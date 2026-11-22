#!/usr/bin/env python3
"""Precommitted source/claim boundary evaluation; advisory, never a truth gate."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SHADOW_PATH = ROOT.parents[1] / "evaluations" / "source-claim-shadow-v1" / "run.py"
SCHEMA = "claim-audit-lab.uncertainty-boundary-v1"
LABELS = {"supported", "contradicted", "insufficient"}


def load_cases() -> tuple[dict, str]:
    raw = (ROOT / "cases.json").read_bytes()
    data = json.loads(raw)
    if data.get("schema_version") != SCHEMA:
        raise ValueError("Wrong case schema")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != 18:
        raise ValueError("The preregistered 18 cases changed")
    for split in ("development", "holdout"):
        rows = [c for c in cases if c.get("split") == split]
        if len(rows) != 9 or Counter(c.get("gold_label") for c in rows) != Counter({
            "supported": 3, "contradicted": 3, "insufficient": 3,
        }):
            raise ValueError("Unbalanced or changed precommit split")
    if len({c.get("id") for c in cases}) != 18 or len({c.get("family") for c in cases}) != 18:
        raise ValueError("Duplicate id or source family")
    for c in cases:
        if not all(isinstance(c.get(k), str) and c[k].strip()
                   for k in ("claim", "source_excerpt", "gold_rationale", "family")):
            raise ValueError("Missing source, claim, rationale or family")
    return data, hashlib.sha256(raw).hexdigest()


def model_module():
    spec = importlib.util.spec_from_file_location("uncertainty_source_shadow", SHADOW_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Existing shadow backend unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(split: str, profile: str, model_name: str) -> dict:
    data, cases_sha = load_cases()
    source = model_module()
    source_sha = hashlib.sha256(SHADOW_PATH.read_bytes()).hexdigest()
    rule_sha = None
    if profile != "baseline":
        rule_file = ROOT / f"candidate-rule-{profile}.txt"
        raw = rule_file.read_bytes()
        rule_sha = hashlib.sha256(raw).hexdigest()
        source.INSTRUCTION += " " + raw.decode("utf-8").strip()
    cases = [c for c in data["cases"] if c["split"] == split]
    rows = []
    for case in cases:
        # Never send the predeclared label or source family to the reviewer.
        prompt = source.prompt_for(case)
        sample = {"id": case["id"], "prompt": prompt, "prompt_sha256": source.sha(prompt)}
        result = source.run_ollama_one(sample, case["source_excerpt"], model_name)
        verdict = result.get("judgment") or {}
        row = {
            "id": case["id"], "status": result.get("status", "error"),
            "label": verdict.get("label"), "evidence_span": verdict.get("evidence_span"),
            "reason": verdict.get("reason"), "error": result.get("error"),
            "raw_response": result.get("raw_response"), "response_sha256": result.get("response_sha256"),
            "prompt_sha256": sample["prompt_sha256"], "model_digest": result.get("model_digest"),
            "duration_seconds": result.get("duration_seconds"),
        }
        rows.append(row)
        print(json.dumps({"id": case["id"], "model": model_name,
                          "gold": case["gold_label"], "observed": row["label"],
                          "error": row["error"]}, ensure_ascii=False), flush=True)
        if row["status"] != "valid":
            break  # A provider failure is never a semantic score.
    outcome = {
        "schema_version": "claim-audit-lab.uncertainty-boundary-results-v1",
        "created_at": datetime.now(timezone.utc).isoformat(), "case_sha256": cases_sha,
        "runner_sha256": source_sha, "rule_sha256": rule_sha,
        "instruction_sha256": source.sha(source.INSTRUCTION),
        "split": split, "profile": profile, "model": model_name,
        "expected": len(cases), "attempted": len(rows),
        "valid": sum(r["status"] == "valid" for r in rows),
        "correct": sum(r["label"] == c["gold_label"] for r, c in zip(rows, cases)),
        "false_contradictions": sum(r["label"] == "contradicted" and c["gold_label"] != "contradicted"
                                    for r, c in zip(rows, cases)),
        "results": rows, "source_authenticity_verified": False, "advisory_only": True,
    }
    return outcome


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "holdout"), required=True)
    parser.add_argument("--profile", choices=("baseline", "v1", "v2"), required=True)
    parser.add_argument("--model", choices=("qwen3:14b", "gemma4:12b"), required=True)
    args = parser.parse_args()
    destination = ROOT / f"run-{args.profile}-{args.split}-{args.model.replace(':', '-')}.json"
    if destination.exists():
        parser.error(f"Refusing to overwrite existing evidence: {destination}")
    result = run(args.split, args.profile, args.model)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(destination), "correct": result["correct"], "valid": result["valid"],
                      "total": result["expected"], "false_contradictions": result["false_contradictions"]},
                     ensure_ascii=False), flush=True)
    if result["valid"] != result["expected"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
