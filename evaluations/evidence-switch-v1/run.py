#!/usr/bin/env python3
"""Reproducible, opt-in evidence-switch benchmark. No release or truth gate."""
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

ROOT = Path(__file__).resolve().parent
SHADOW = ROOT.parents[1] / "evaluations" / "source-claim-shadow-v1" / "run.py"
CASES_SHA256 = "19995409ae52c5de4495f6431a9816a3b9b3575eaa09d9bec850703d6dbabd5c"
PROTOCOL_SHA256 = "3ae254ae5bb1e47284c4e80cead4a42eff7099b47993b286dd0b66aed1c306a2"
LABELS = ("supported", "contradicted", "insufficient")
MODELS = ("gemma4:12b", "qwen3:14b")
CONDITIONS = ("minimal", "lab")
SPLITS = ("development", "holdout")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_protocol() -> tuple[dict, list[dict]]:
    raw = (ROOT / "cases.json").read_bytes()
    protocol_raw = (ROOT / "protocol.json").read_bytes()
    if sha(raw) != CASES_SHA256 or sha(protocol_raw) != PROTOCOL_SHA256:
        raise ValueError("Prerecorded gold/protocol changed; use a new version")
    cases = json.loads(raw)["cases"]
    protocol = json.loads(protocol_raw)
    if len(cases) != 36 or len(protocol["models"]) != 2:
        raise ValueError("Incomplete precommitted experiment")
    ids = {case["id"] for case in cases}
    if len(ids) != 36:
        raise ValueError("Duplicate case id")
    for split in SPLITS:
        for family in {case["family"] for case in cases if case["split"] == split}:
            group = [case for case in cases if case["family"] == family]
            if len(group) != 3 or {case["gold_label"] for case in group} != set(LABELS):
                raise ValueError("A counterfactual family is incomplete")
            if len({case["claim"] for case in group}) != 1:
                raise ValueError("The scientific claim changed across evidence variants")
        if sum(case["split"] == split for case in cases) != 18:
            raise ValueError("Precommitted split is not 18/18")
    return protocol, cases


def reviewer_module(condition: str, protocol: dict):
    spec = importlib.util.spec_from_file_location("evidence_switch_shadow", SHADOW)
    if spec is None or spec.loader is None:
        raise RuntimeError("Existing local source reviewer unavailable")
    reviewer = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = reviewer
    spec.loader.exec_module(reviewer)
    if condition == "minimal":
        reviewer.INSTRUCTION = protocol["treatments"]["minimal"]
    return reviewer


def summarize(rows: list[dict], cases: list[dict]) -> dict:
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows) or not set(by_id).issubset({c["id"] for c in cases}):
        raise ValueError("Duplicate or foreign result IDs")
    index = {c["id"]: c for c in cases}
    valid = [r for r in rows if r["status"] == "valid"]
    correct = sum(r["label"] == index[r["id"]]["gold_label"] for r in valid)
    false_contradictions = sum(
        r["label"] == "contradicted" and index[r["id"]]["gold_label"] != "contradicted"
        for r in valid
    )
    missed_contradictions = sum(
        r["label"] != "contradicted" and index[r["id"]]["gold_label"] == "contradicted"
        for r in valid
    )
    families = {c["family"] for c in cases}
    complete_families = 0
    for family in families:
        items = [c for c in cases if c["family"] == family]
        if all(c["id"] in by_id and by_id[c["id"]]["status"] == "valid"
               and by_id[c["id"]]["label"] == c["gold_label"] for c in items):
            complete_families += 1
    return {
        "expected": len(cases), "attempted": len(rows),
        "valid": len(valid), "invalid_or_unattempted": len(cases) - len(valid),
        "correct": correct, "false_contradictions": false_contradictions,
        "missed_explicit_contradictions": missed_contradictions,
        "complete_three_state_families": complete_families,
        "total_families": len(families),
    }


def run(split: str, model: str, condition: str) -> dict:
    protocol, all_cases = read_protocol()
    reviewer = reviewer_module(condition, protocol)
    cases = [case for case in all_cases if case["split"] == split]
    order = list(cases)
    random.Random(protocol["random_seed"]).shuffle(order)
    rows = []
    for case in order:
        # Gold labels, split, family, rationale and treatment identity are not model inputs.
        prompt = reviewer.prompt_for(case)
        sample = {"id": case["id"], "prompt": prompt, "prompt_sha256": reviewer.sha(prompt)}
        output = reviewer.run_ollama_one(sample, case["source_excerpt"], model)
        verdict = output.get("judgment") or {}
        row = {
            "id": case["id"], "status": output.get("status", "error"),
            "label": verdict.get("label"), "evidence_span": verdict.get("evidence_span"),
            "reason": verdict.get("reason"), "error": output.get("error"),
            "prompt_sha256": sample["prompt_sha256"], "raw_response": output.get("raw_response"),
            "response_sha256": output.get("response_sha256"), "model_digest": output.get("model_digest"),
            "prompt_eval_count": output.get("prompt_eval_count"), "duration_seconds": output.get("duration_seconds"),
        }
        rows.append(row)
        print(json.dumps({"id": case["id"], "model": model, "condition": condition,
                          "status": row["status"], "label": row["label"],
                          "error": row["error"]}, ensure_ascii=False), flush=True)
        if row["status"] != "valid":
            break  # Provider/parse failures are never reinterpreted as reasoning errors.
    return {
        "schema_version": "claim-audit-lab.evidence-switch-results-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cases_sha256": CASES_SHA256, "protocol_sha256": PROTOCOL_SHA256,
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "reviewer_sha256": sha(SHADOW.read_bytes()),
        "instruction_sha256": reviewer.sha(reviewer.INSTRUCTION),
        "model": model, "condition": condition, "split": split,
        "source_authenticity_verified": False, "advisory_only": True,
        "metrics": summarize(rows, cases), "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=SPLITS, required=True)
    parser.add_argument("--model", choices=MODELS, required=True)
    parser.add_argument("--condition", choices=CONDITIONS, required=True)
    args = parser.parse_args()
    destination = ROOT / f"run-{args.split}-{args.model.replace(':', '-')}-{args.condition}.json"
    if destination.exists():
        parser.error(f"Existing evidence cannot be overwritten: {destination}")
    result = run(args.split, args.model, args.condition)
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("SUMMARY", json.dumps({
        "file": str(destination), **result["metrics"],
    }), flush=True)
    if result["metrics"]["valid"] != result["metrics"]["expected"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
