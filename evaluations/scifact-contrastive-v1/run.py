#!/usr/bin/env python3
"""Opt-in comparison of one specific claim-relation prompt against SciFact expert labels.

Scientific evidence tests only the relationship of a supplied abstract to a claim.
No paper truth, third-party source authenticity, or ordinary-chat enforcement is inferred.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import runpy
import sys

ROOT = Path(__file__).resolve().parent
SCIFACT = ROOT.parent / "scifact-expert-v1" / "run.py"
OLD_MANIFEST = ROOT.parent / "scifact-expert-v1" / "manifest.json"
MINIMAL_PROTOCOL = ROOT.parent / "evidence-switch-v1" / "protocol.json"
MANIFEST = ROOT / "manifest.json"
SEED = 2026112202
PER_CLASS_PER_SPLIT = 4
CLASSES = ("SUPPORT", "CONTRADICT")
SPLITS = ("development", "holdout")
MODELS = ("qwen3:14b", "gemma4:12b")
CONDITIONS = ("minimal", "contrast")
EXTRA_INSTRUCTION = (
    "Before labeling, check the claim's precise subject, predicate, negation, "
    "and comparison direction against the excerpt. Mentioning the same topic "
    "or an effect on a related outcome is not by itself support."
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def science():
    return runpy.run_path(str(SCIFACT))


def protocol_text(condition: str) -> str:
    base = json.loads(MINIMAL_PROTOCOL.read_text(encoding="utf-8"))["treatments"]["minimal"]
    return base if condition == "minimal" else base + " " + EXTRA_INSTRUCTION


def expected_manifest(claims: list[dict], corpus: dict[int, dict], sci: dict) -> dict:
    old = json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))
    occupied_claims = {s["claim_id"] for s in old["samples"]}
    occupied_docs = {s["doc_id"] for s in old["samples"]}
    pools = sci["candidate_pairs"](claims, corpus)
    samples = []
    for label in CLASSES:
        ordered = sorted(
            pools[label],
            key=lambda x: (
                digest(f"{SEED}/{label}/{x['claim_id']}/{x['doc_id']}".encode()),
                x["claim_id"], x["doc_id"],
            ),
        )
        selected = []
        for item in ordered:
            if item["claim_id"] in occupied_claims or item["doc_id"] in occupied_docs:
                continue
            occupied_claims.add(item["claim_id"])
            occupied_docs.add(item["doc_id"])
            selected.append(item)
            if len(selected) == PER_CLASS_PER_SPLIT * len(SPLITS):
                break
        if len(selected) != PER_CLASS_PER_SPLIT * len(SPLITS):
            raise ValueError(f"Not enough disjoint expert-annotated pairs: {label}")
        for i, item in enumerate(selected):
            samples.append({**item, "split": SPLITS[i // PER_CLASS_PER_SPLIT]})
    samples.sort(key=lambda x: (x["split"], x["reference_label"], x["id"]))
    return {
        "schema_version": "claim-audit-lab.scifact-contrast-manifest-v1",
        "seed": SEED,
        "original_scifact_release_sha256": sci["RELEASE_SHA256"],
        "original_scifact_manifest_sha256": digest(OLD_MANIFEST.read_bytes()),
        "selection": "SHA-sort unused published expert SUPPORT/CONTRADICT, no reused claims/docs versus SciFact v1",
        "per_class_per_split": PER_CLASS_PER_SPLIT,
        "samples": samples,
    }


def load_locked(archive: Path, sci: dict):
    claims, corpus = sci["load_release"](archive)
    candidate = expected_manifest(claims, corpus, sci)
    raw = MANIFEST.read_bytes()
    frozen = json.loads(raw)
    if frozen != candidate:
        raise ValueError("Manifest does not match checksum-verified source and frozen algorithm")
    return frozen, digest(raw), claims, corpus


def evaluate(archive: Path, split: str, model: str, condition: str):
    sci = science()
    frozen, manifest_sha, claims, corpus = load_locked(archive, sci)
    shadow = sci["load_shadow"]()
    shadow.INSTRUCTION = protocol_text(condition)
    by_claim = {x["id"]: x["claim"] for x in claims}
    selected = [x for x in frozen["samples"] if x["split"] == split]
    random.Random(SEED).shuffle(selected)
    rows = []
    for sample in selected:
        claim = by_claim[sample["claim_id"]]
        excerpt = sci["source_text"](corpus[sample["doc_id"]])
        if digest(claim.encode()) != sample["claim_sha256"] or digest(excerpt.encode()) != sample["abstract_sha256"]:
            raise ValueError("Source identity mismatch before model call")
        prompt = shadow.prompt_for({"claim": claim, "source_excerpt": excerpt})
        outcome = shadow.run_ollama_one(
            {"id": sample["id"], "prompt": prompt, "prompt_sha256": shadow.sha(prompt)},
            excerpt, model,
        )
        prediction = outcome.get("judgment") or {}
        row = {
            "id": sample["id"], "reference": sample["reference_label"],
            "status": outcome.get("status", "error"), "error": outcome.get("error"),
            "label": prediction.get("label"), "evidence_span": prediction.get("evidence_span"),
            "reason": prediction.get("reason"), "raw_response": outcome.get("raw_response"),
            "prompt_sha256": shadow.sha(prompt), "response_sha256": outcome.get("response_sha256"),
            "model_digest": outcome.get("model_digest"),
            "duration_seconds": outcome.get("duration_seconds"),
            "prompt_eval_count": outcome.get("prompt_eval_count"),
        }
        rows.append(row)
        print(json.dumps({"id": row["id"], "condition": condition,
            "status": row["status"], "label": row["label"], "reference": row["reference"],
            "error": row["error"]}), flush=True)
        # Invalid quotes are faults, not a reason to hide remaining fixed cases.
        # Provider/context failures are a different category; do not score them as semantics.
        if row["status"] != "valid" and row["error"] != "invalid_output":
            break
    metrics = {
        "expected": len(selected), "attempted": len(rows),
        "valid": sum(r["status"] == "valid" for r in rows),
        "correct_expert_labels": sum(
            r["label"] == ("supported" if r["reference"] == "SUPPORT" else "contradicted")
            for r in rows if r["status"] == "valid"
        ),
        "missed_expert_support": sum(
            r["reference"] == "SUPPORT" and r["status"] == "valid" and r["label"] != "supported"
            for r in rows
        ),
        "missed_expert_contradiction": sum(
            r["reference"] == "CONTRADICT" and r["status"] == "valid" and r["label"] != "contradicted"
            for r in rows
        ),
        "false_contradiction_of_expert_support": sum(
            r["reference"] == "SUPPORT" and r["label"] == "contradicted"
            for r in rows if r["status"] == "valid"
        ),
        "false_support_of_expert_contradiction": sum(
            r["reference"] == "CONTRADICT" and r["label"] == "supported"
            for r in rows if r["status"] == "valid"
        ),
        "invalid_citations_or_schema": sum(r["error"] == "invalid_output" for r in rows),
        "provider_or_context_errors": sum(
            r["status"] != "valid" and r["error"] != "invalid_output" for r in rows
        ),
        "duration_seconds_total": round(sum(r["duration_seconds"] or 0 for r in rows), 2),
        "prompt_eval_tokens": sum(r["prompt_eval_count"] or 0 for r in rows),
    }
    return {
        "schema_version": "claim-audit-lab.scifact-contrast-results-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_sha256": sci["RELEASE_SHA256"],
        "manifest_sha256": manifest_sha,
        "runner_sha256": digest(Path(__file__).read_bytes()),
        "backend_sha256": digest(Path(sci["SHADOW"]).read_bytes()),
        "prompt_sha256": digest(shadow.INSTRUCTION.encode()),
        "split": split, "model": model, "condition": condition,
        "expert_annotation_not_world_truth": True,
        "metrics": metrics, "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--archive", type=Path, required=True)
    trial = sub.add_parser("trial")
    trial.add_argument("--archive", type=Path, required=True)
    trial.add_argument("--split", required=True, choices=SPLITS)
    trial.add_argument("--model", required=True, choices=MODELS)
    trial.add_argument("--condition", required=True, choices=CONDITIONS)
    args = ap.parse_args()
    sci = science()
    if args.action == "prepare":
        claims, corpus = sci["load_release"](args.archive)
        output = expected_manifest(claims, corpus, sci)
        with MANIFEST.open("x", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(json.dumps({"manifest": str(MANIFEST), "sha256": digest(MANIFEST.read_bytes()),
                          "cases": len(output["samples"])}))
        return
    filename = f"run-{args.split}-{args.model.replace(':', '-')}-{args.condition}.json"
    output_path = ROOT / filename
    if output_path.exists():
        ap.error("Original model trial exists; no overwrite or hidden retry")
    output = evaluate(args.archive, args.split, args.model, args.condition)
    with output_path.open("x", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("SUMMARY", json.dumps({"file": str(output_path), "metrics": output["metrics"]}), flush=True)
    if output["metrics"]["valid"] != output["metrics"]["expected"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
