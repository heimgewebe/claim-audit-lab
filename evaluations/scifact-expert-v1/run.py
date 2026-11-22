#!/usr/bin/env python3
"""Opt-in SciFact expert-evidence benchmark. No network, extra model or CI gate."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
SHADOW = ROOT.parents[1] / "evaluations" / "source-claim-shadow-v1" / "run.py"
MINIMAL_PROMPT = ROOT.parents[1] / "evaluations" / "evidence-switch-v1" / "protocol.json"
RELEASE_URL = "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz"
RELEASE_SHA256 = "11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be"
SEED = 20261122
PER_CLASS_PER_SPLIT = 5
STRATA = ("SUPPORT", "CONTRADICT", "CITED_NO_ANNOTATED_RATIONALE")
SPLITS = ("development", "holdout")
MODELS = ("gemma4:12b", "qwen3:14b")
CONDITIONS = ("minimal", "lab")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def source_text(document: dict) -> str:
    abstract = document.get("abstract")
    if not isinstance(abstract, list) or len(abstract) < 2:
        raise ValueError("Missing scientific abstract")
    if any(not isinstance(sentence, str) or not sentence.strip() for sentence in abstract):
        raise ValueError("Malformed scientific abstract")
    return "\n".join(abstract)


def load_release(path: Path) -> tuple[list[dict], dict[int, dict]]:
    """Read exact two known members; never extract the archive to disk."""
    raw = path.read_bytes()
    if sha(raw) != RELEASE_SHA256:
        raise ValueError("SciFact original release SHA-256 mismatch")
    with tarfile.open(path, mode="r:gz") as archive:
        def rows(name: str) -> list[dict]:
            member = archive.getmember(name)
            if not member.isfile() or member.size > 9_000_000:
                raise ValueError("Unexpected original release member")
            fp = archive.extractfile(member)
            if fp is None:
                raise ValueError("Missing original release member")
            return [json.loads(line) for line in fp if line.strip()]
        claims = rows("data/claims_dev.jsonl")
        docs = rows("data/corpus.jsonl")
    corpus = {row["doc_id"]: row for row in docs}
    if len(corpus) != len(docs) or len(claims) < 200:
        raise ValueError("Unexpected SciFact dev/corpus size")
    return claims, corpus


def candidate_pairs(claims: list[dict], corpus: dict[int, dict]) -> dict[str, list[dict]]:
    pools: dict[str, list[dict]] = {label: [] for label in STRATA}
    for claim in claims:
        statement = claim["claim"]
        claim_id = claim["id"]
        if not isinstance(statement, str) or not 12 <= len(statement) <= 400:
            continue
        positive = claim.get("evidence", {})
        if not isinstance(positive, dict):
            raise ValueError("SciFact evidence structure invalid")
        for doc_id, rationales in positive.items():
            document = corpus.get(int(doc_id))
            if document is None:
                continue
            excerpt = source_text(document)
            if not 120 <= len(excerpt) <= 3200:
                continue
            labels = {r["label"] for r in rationales}
            if len(labels) != 1 or not labels.issubset({"SUPPORT", "CONTRADICT"}):
                continue
            label = next(iter(labels))
            indices = sorted({idx for rationale in rationales for idx in rationale["sentences"]})
            if not indices or any(type(idx) is not int or idx < 0 or idx >= len(document["abstract"]) for idx in indices):
                raise ValueError("Invalid expert rationale sentence index")
            pools[label].append(make_candidate(claim_id, document, statement, label, indices))
        for doc_id in claim.get("cited_doc_ids", []):
            if str(doc_id) in positive:
                continue
            document = corpus.get(int(doc_id))
            if document is None:
                continue
            excerpt = source_text(document)
            if 120 <= len(excerpt) <= 3200:
                pools["CITED_NO_ANNOTATED_RATIONALE"].append(make_candidate(
                    claim_id, document, statement, "CITED_NO_ANNOTATED_RATIONALE", []
                ))
    return pools


def make_candidate(claim_id: int, document: dict, claim: str, label: str, indices: list[int]) -> dict:
    text = source_text(document)
    return {
        "id": f"{claim_id}:{document['doc_id']}", "claim_id": claim_id,
        "doc_id": document["doc_id"], "reference_label": label,
        "claim_sha256": sha(claim.encode()), "abstract_sha256": sha(text.encode()),
        "rationale_sentence_indices": indices,
        "paper_title": document["title"],
    }


def choose_manifest(claims: list[dict], corpus: dict[int, dict]) -> dict:
    pools = candidate_pairs(claims, corpus)
    used_claims: set[int] = set()
    used_docs: set[int] = set()
    samples: list[dict] = []
    for label in STRATA:
        order = sorted(pools[label], key=lambda c: (
            sha(f"{SEED}/{label}/{c['claim_id']}/{c['doc_id']}".encode()),
            c["claim_id"], c["doc_id"],
        ))
        selected = []
        for candidate in order:
            if candidate["claim_id"] in used_claims or candidate["doc_id"] in used_docs:
                continue
            selected.append(candidate)
            used_claims.add(candidate["claim_id"])
            used_docs.add(candidate["doc_id"])
            if len(selected) == PER_CLASS_PER_SPLIT * len(SPLITS):
                break
        if len(selected) != PER_CLASS_PER_SPLIT * len(SPLITS):
            raise ValueError(f"Insufficient disjoint SciFact pairs for {label}")
        for index, sample in enumerate(selected):
            samples.append({**sample, "split": SPLITS[index // PER_CLASS_PER_SPLIT]})
    samples.sort(key=lambda s: (s["split"], s["reference_label"], s["claim_id"], s["doc_id"]))
    return {
        "schema_version": "claim-audit-lab.scifact-expert-manifest-v1",
        "release_url": RELEASE_URL, "release_sha256": RELEASE_SHA256,
        "provenance": "allenai/scifact claims_dev.jsonl + corpus.jsonl",
        "seed": SEED, "samples_per_class_per_split": PER_CLASS_PER_SPLIT,
        "gold_semantics": {
            "SUPPORT": "Expert-annotated source abstract supports claim",
            "CONTRADICT": "Expert-annotated source abstract contradicts claim",
            "CITED_NO_ANNOTATED_RATIONALE": "No published positive annotation in this cited abstract: exploratory only, NOT an expert NEI gold label",
        },
        "sample_count": len(samples), "samples": samples,
    }


def locked_manifest(claims: list[dict], corpus: dict[int, dict]) -> tuple[dict, str]:
    path = ROOT / "manifest.json"
    raw = path.read_bytes()
    manifest = json.loads(raw)
    expected = choose_manifest(claims, corpus)
    if manifest != expected or canonical(manifest) != canonical(expected):
        raise ValueError("Committed expert-reference manifest differs from release-derived preselection")
    if manifest["sample_count"] != 30:
        raise ValueError("Wrong preselected manifest size")
    return manifest, sha(raw)


def load_shadow():
    spec = importlib.util.spec_from_file_location("scifact_expert_shadow", SHADOW)
    if spec is None or spec.loader is None:
        raise RuntimeError("Existing local semantic backend unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def select_instruction(shadow, condition: str) -> None:
    if condition == "minimal":
        protocol = json.loads(MINIMAL_PROMPT.read_text(encoding="utf-8"))
        shadow.INSTRUCTION = protocol["treatments"]["minimal"]


def verified_resume_prefix(
    previous: dict, manifest_hash: str, split: str, model: str,
    condition: str, selected: list[dict], by_claim: dict[int, str],
    corpus: dict[int, dict], shadow,
) -> list[dict]:
    if any(previous.get(key) != value for key, value in {
        "release_sha256": RELEASE_SHA256, "manifest_sha256": manifest_hash,
        "split": split, "model": model, "condition": condition,
        "backend_sha256": sha(SHADOW.read_bytes()),
        "instruction_sha256": shadow.sha(shadow.INSTRUCTION),
    }.items()):
        raise ValueError("Original trial identity does not match current source and prompt")
    rows = previous.get("rows")
    if not isinstance(rows, list) or not 0 < len(rows) < len(selected):
        raise ValueError("Original trial is not a nonempty incomplete prefix")
    if rows[-1].get("error") != "invalid_output":
        raise ValueError("Only a model citation/format failure may be continued")
    for index, row in enumerate(rows):
        sample = selected[index]
        if row.get("id") != sample["id"]:
            raise ValueError("Earlier model inputs do not match frozen order")
        excerpt = source_text(corpus[sample["doc_id"]])
        prompt = shadow.prompt_for({
            "claim": by_claim[sample["claim_id"]], "source_excerpt": excerpt,
        })
        raw = row.get("raw_response")
        if (row.get("prompt_sha256") != shadow.sha(prompt)
            or not isinstance(raw, str)
            or row.get("response_sha256") != sha(raw.encode())):
            raise ValueError("Earlier model input or output hash is not valid")
        if row.get("status") == "valid":
            parsed = shadow.parse_response(raw, excerpt)
            if (parsed["label"] != row.get("label")
                or parsed["evidence_span"] != row.get("evidence_span")):
                raise ValueError("Earlier valid result is inconsistent")
        elif index != len(rows) - 1 or row.get("error") != "invalid_output":
            raise ValueError("Only the final saved row may have a format error")
        else:
            try:
                shadow.parse_response(raw, excerpt)
            except ValueError:
                pass
            else:
                raise ValueError("Claimed format failure parses as valid")
    return rows


def evaluate_split(
    archive: Path, split: str, model: str, condition: str,
    resume_from: Path | None = None,
) -> dict:
    claims, corpus = load_release(archive)
    manifest, manifest_hash = locked_manifest(claims, corpus)
    by_claim = {claim["id"]: claim["claim"] for claim in claims}
    shadow = load_shadow()
    select_instruction(shadow, condition)
    selected = [sample for sample in manifest["samples"] if sample["split"] == split]
    random.Random(SEED).shuffle(selected)
    original_sha = None
    rows: list[dict] = []
    if resume_from is not None:
        raw = resume_from.read_bytes()
        previous = json.loads(raw)
        rows = verified_resume_prefix(
            previous, manifest_hash, split, model, condition,
            selected, by_claim, corpus, shadow,
        ).copy()
        original_sha = sha(raw)
    for sample in selected[len(rows):]:
        claim = by_claim[sample["claim_id"]]
        excerpt = source_text(corpus[sample["doc_id"]])
        if sha(claim.encode()) != sample["claim_sha256"] or sha(excerpt.encode()) != sample["abstract_sha256"]:
            raise ValueError("Release content differs from sampled manifest hash")
        prompt = shadow.prompt_for({"claim": claim, "source_excerpt": excerpt})
        result = shadow.run_ollama_one({
            "id": sample["id"], "prompt": prompt, "prompt_sha256": shadow.sha(prompt),
        }, excerpt, model)
        judgment = result.get("judgment") or {}
        row = {
            "id": sample["id"], "status": result.get("status", "error"),
            "label": judgment.get("label"), "evidence_span": judgment.get("evidence_span"),
            "reason": judgment.get("reason"), "error": result.get("error"),
            "prompt_sha256": shadow.sha(prompt), "response_sha256": result.get("response_sha256"),
            "raw_response": result.get("raw_response"), "model_digest": result.get("model_digest"),
            "prompt_eval_count": result.get("prompt_eval_count"), "duration_seconds": result.get("duration_seconds"),
        }
        rows.append(row)
        print(json.dumps({"id": sample["id"], "status": row["status"],
                          "label": row["label"], "error": row["error"]}), flush=True)
        # Citation formatting is a measurable model fault, not a provider outage.
        # Continue the fixed sample sequence without silently accepting the quote.
        if row["status"] != "valid" and row["error"] != "invalid_output":
            break
    metrics = measurements(rows, selected)
    return {
        "schema_version": "claim-audit-lab.scifact-expert-results-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "release_sha256": RELEASE_SHA256, "manifest_sha256": manifest_hash,
        "runner_sha256": sha(Path(__file__).read_bytes()), "backend_sha256": sha(SHADOW.read_bytes()),
        "instruction_sha256": shadow.sha(shadow.INSTRUCTION),
        "split": split, "model": model, "condition": condition,
        "expert_labels_only_for_annotated_pairs": True,
        "cited_unannotated_is_not_nei_gold": True,
        "underlying_paper_truth_verified": False,
        "continuation_from_sha256": original_sha,
        "methods_amended_after_development_format_failure": True,
        "metrics": metrics, "rows": rows,
    }


def measurements(rows: list[dict], samples: list[dict]) -> dict:
    by_id = {s["id"]: s for s in samples}
    if len({r["id"] for r in rows}) != len(rows) or not {r["id"] for r in rows}.issubset(by_id):
        raise ValueError("Unknown or duplicate sample")
    rows_valid = [row for row in rows if row["status"] == "valid"]
    expert = [row for row in rows_valid if by_id[row["id"]]["reference_label"] in {"SUPPORT", "CONTRADICT"}]
    correct = sum((r["label"] == "supported" if by_id[r["id"]]["reference_label"] == "SUPPORT"
                   else r["label"] == "contradicted") for r in expert)
    weak = [r for r in rows_valid if by_id[r["id"]]["reference_label"] == "CITED_NO_ANNOTATED_RATIONALE"]
    return {
        "expected": len(samples), "attempted": len(rows), "valid": len(rows_valid),
        "invalid_or_unattempted": len(samples) - len(rows_valid),
        "expert_expected": sum(s["reference_label"] in {"SUPPORT", "CONTRADICT"} for s in samples),
        "expert_valid": len(expert), "expert_correct": correct,
        "false_refute_of_expert_support": sum(
            r["label"] == "contradicted" and by_id[r["id"]]["reference_label"] == "SUPPORT" for r in expert),
        "missed_expert_refute": sum(
            r["label"] != "contradicted" and by_id[r["id"]]["reference_label"] == "CONTRADICT" for r in expert),
        "unannotated_cited_valid": len(weak),
        "unannotated_cited_contradicted": sum(r["label"] == "contradicted" for r in weak),
        "unannotated_cited_insufficient": sum(r["label"] == "insufficient" for r in weak),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build-manifest")
    build.add_argument("--archive", type=Path, required=True)
    trial = sub.add_parser("trial")
    trial.add_argument("--archive", type=Path, required=True)
    trial.add_argument("--split", choices=SPLITS, required=True)
    trial.add_argument("--model", choices=MODELS, required=True)
    trial.add_argument("--condition", choices=CONDITIONS, required=True)
    trial.add_argument("--resume-from", type=Path)
    args = parser.parse_args()
    if args.command == "build-manifest":
        path = ROOT / "manifest.json"
        if path.exists():
            parser.error("Manifest already exists; cannot rewrite reference selection")
        claims, corpus = load_release(args.archive)
        manifest = choose_manifest(claims, corpus)
        with path.open("x", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(json.dumps({"manifest": str(path), "sha256": sha(path.read_bytes()),
                          "samples": manifest["sample_count"]}), flush=True)
    else:
        suffix = "-resumed" if args.resume_from is not None else ""
        path = ROOT / f"run-{args.split}-{args.model.replace(':','-')}-{args.condition}{suffix}.json"
        if path.exists():
            parser.error(f"Existing trial evidence cannot be overwritten: {path}")
        output = evaluate_split(
            args.archive, args.split, args.model, args.condition,
            resume_from=args.resume_from,
        )
        with path.open("x", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("SUMMARY", json.dumps({"result": str(path), "metrics": output["metrics"]}), flush=True)
        if output["metrics"]["valid"] != output["metrics"]["expected"]:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
