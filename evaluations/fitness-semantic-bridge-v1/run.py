#!/usr/bin/env python3
"""Optional bridge from the original fitness canaries to source/claim shadow review.

Pre-registered oracle:
- two original evidence contradictions must be marked contradicted;
- rhetorical certainty is *not warranted* by a merely plausible verdict:
  the status does not establish absolute certainty, without logically proving
  the opposite proposition;
- three paired supported controls must be accepted.

Neither script changes the original fitness cases, their metrics or CI gates.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import yaml

ROOT = Path(__file__).resolve().parents[2]
SHADOW_DIR = ROOT / "evaluations" / "source-claim-shadow-v1"
FITNESS_DIR = ROOT / "evaluations" / "lab-fitness-20261121"
SEED = 20261122
PROTOCOL = "claim-audit-lab.original-fitness-semantic-bridge.v1"
DEFAULT_MODELS = ("qwen3:14b", "gemma4:12b")


def load_local(name: str, file: Path):
    spec = importlib.util.spec_from_file_location(name, file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fitness = load_local("fitness_bridge_original", FITNESS_DIR / "run.py")
shadow = load_local("fitness_bridge_shadow", SHADOW_DIR / "run.py")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def extract_from_original_cases() -> list[dict]:
    """Read live data from exact, already committed original fitness mutations."""
    rows = []
    originals = (
        "contradictory_event_time",
        "contradictory_count",
        "rhetorical_certainty_laundering",
    )
    with tempfile.TemporaryDirectory(prefix="lab-fitness-bridge-") as tmp:
        for name in originals:
            original = next(c for c in fitness.CHALLENGES if c.name == name)
            folder = Path(tmp) / name
            shutil.copytree(fitness.BASE, folder)
            original.mutation(folder)
            data_claim = yaml.safe_load((folder / "claims.yml").read_text())["claims"][0]
            data_evidence = yaml.safe_load((folder / "evidence-pack.yml").read_text())["evidence"][0]
            receipt = yaml.safe_load((folder / "answer-receipt.yml").read_text())

            if name == "contradictory_event_time":
                excerpt = data_evidence["verbatim_or_ref"] + "\n" + data_evidence["summary"]
                proposition = data_claim["statement"]
                control = "Event A occurred at 11:00 UTC on 2026-01-01."
                gold = "contradicted"
                rationale = "The same event is recorded at 11:00 rather than 10:00 UTC."
                field = "claims.yml:statement ↔ evidence-pack.yml:verbatim_or_ref"
            elif name == "contradictory_count":
                excerpt = data_evidence["verbatim_or_ref"] + "\n" + data_evidence["summary"]
                proposition = data_claim["statement"]
                control = "The same participant register contains three distinct people."
                gold = "contradicted"
                rationale = "The same register names three individuals, not exactly two."
                field = "claims.yml:statement ↔ evidence-pack.yml:verbatim_or_ref"
            else:
                status = data_claim["status"]
                assert status == "plausible"
                excerpt = (
                    f"Structured verdict for this claim: {status}.\n"
                    f"Claim statement: {data_claim['statement']}"
                )
                proposition = receipt["answer_summary"]
                control = f"The structured verdict for this claim is {status}."
                gold = "insufficient"
                rationale = (
                    "The recorded plausible status does not establish the "
                    "answer's claim of conclusive proof. It also does not prove "
                    "that the underlying proposition is false."
                )
                field = "answer-receipt.yml:answer_summary ↔ claims.yml:status"

            sources = {
                n: digest((folder / n).read_bytes())
                for n in ("claims.yml", "evidence-pack.yml", "answer-receipt.yml")
            }
            for kind, claim, expected, why in (
                ("canary", proposition, gold, rationale),
                ("control", control, "supported", "Directly entailed by the given record."),
            ):
                rows.append({
                    "id": name + "-" + kind,
                    "source_fitness_case": name,
                    "lane": kind,
                    "origin_fields": field,
                    "source_excerpt": excerpt,
                    "claim": claim,
                    "gold_label": expected,
                    "gold_rationale": why,
                    "mutated_fixture_sha256": sources,
                })
    assert len(rows) == 6
    random.Random(SEED).shuffle(rows)
    return rows


def assignments(cases: list[dict]) -> list[dict]:
    rows = []
    for i, c in enumerate(cases):
        prompt = shadow.prompt_for(c)
        rows.append({
            "id": c["id"],
            "lane": c["lane"],
            "order": i,
            "prompt": prompt,
            "prompt_sha256": shadow.sha(prompt),
        })
    return rows


def metrics(cases: list[dict], results: list[dict]) -> dict:
    lookup = {r["id"]: r for r in results}
    if len(lookup) != len(cases) or set(lookup) != {c["id"] for c in cases}:
        raise ValueError("Missing or duplicate case result")
    out = {}
    for lane in ("canary", "control"):
        items = [c for c in cases if c["lane"] == lane]
        valid = sum(lookup[c["id"]].get("status") == "valid" for c in items)
        correct = sum(
            lookup[c["id"]].get("judgment", {}).get("label") == c["gold_label"]
            for c in items
        )
        out[lane] = {
            "total": len(items),
            "valid": valid,
            "correct_exact": correct,
            "wrong_or_missing": len(items) - correct,
        }
    out["invalid"] = sum(r.get("status") != "valid" for r in results)
    out["false_positive_controls"] = sum(
        lookup[c["id"]].get("judgment", {}).get("label") not in (None, "supported")
        for c in cases if c["lane"] == "control"
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--model", default="gemma4:12b",
                        help="Already installed Ollama model name")
    parser.add_argument("--output-dir", type=Path)
    opts = parser.parse_args()
    cases = extract_from_original_cases()
    samples = assignments(cases)
    prereg = {
        "protocol": PROTOCOL, "seed": SEED,
        "source_fitness_main_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "original_fitness_results_sha256": digest((FITNESS_DIR / "results.json").read_bytes()),
        "case_definition_sha256": digest(Path(__file__).read_bytes()),
        "cases": cases,
    }
    if not opts.execute:
        print(json.dumps({
            "protocol": PROTOCOL,
            "samples": [
                {k: r[k] for k in ("id", "lane", "order", "prompt_sha256")}
                for r in samples
            ],
            "prereg_sha256": digest(json.dumps(
                prereg, ensure_ascii=False, sort_keys=True
            ).encode("utf-8")),
        }, ensure_ascii=False, indent=2))
        return
    if opts.output_dir is None:
        raise SystemExit("Provide a new --output-dir")
    out = opts.output_dir.expanduser().resolve()
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise SystemExit("Output directory exists; do not overwrite earlier measurements")

    results = [
        shadow.run_ollama_one(item, cases[next(
            i for i, c in enumerate(cases) if c["id"] == item["id"]
        )]["source_excerpt"], opts.model)
        for item in samples
    ]
    scores = metrics(cases, results)
    data = {
        **prereg, "model": opts.model, "backend": "ollama",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "metrics": scores, "results": results,
    }
    p = out / "results.json"
    staged = out / "results.json.tmp"
    staged.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    staged.replace(p)
    print(json.dumps(scores, sort_keys=True))
    if scores["invalid"]:
        raise SystemExit("Incomplete model trial; raw failures retained")


if __name__ == "__main__":
    main()
