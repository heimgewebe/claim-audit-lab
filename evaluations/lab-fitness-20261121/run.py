#!/usr/bin/env python3
"""Measure Claim-Audit-Lab detection, false alarms and semantic blind spots.

Expected outcomes and controlled mutations are fixed before execution.
All production validators run against isolated copies of one known-valid case.
This is a measurement, not a release gate or an automatic truth certificate.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "cases" / "sandbox" / "minimal-valid-case"
OUTPUT = Path(__file__).resolve().parent / "results.json"
PROTOCOL = "claim-audit-lab.fitness-challenge.v1"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def mutate_yaml(case: Path, file: str, change: Callable[[dict], None]) -> None:
    path = case / file
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    change(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def field(obj: dict, key: str, value) -> None:
    obj[key] = value


def claim(case: Path, fn: Callable[[dict], None]) -> None:
    mutate_yaml(case, "claims.yml", lambda d: fn(d["claims"][0]))


def evidence(case: Path, fn: Callable[[dict], None]) -> None:
    mutate_yaml(case, "evidence-pack.yml", lambda d: fn(d["evidence"][0]))


def source(case: Path, fn: Callable[[dict], None]) -> None:
    mutate_yaml(case, "sources.yml", lambda d: fn(d["sources"][0]))


def relation(case: Path, fn: Callable[[dict], None]) -> None:
    mutate_yaml(case, "evidence-relations.yml", lambda d: fn(d["relations"][0]))


def baseline(case: Path) -> None:
    pass


def scientific_quote(case: Path) -> None:
    p = case / "assessment.md"
    p.write_text(p.read_text(encoding="utf-8") +
        "\nDer zitierte Ausdruck „wissenschaftlicher Konsens“ ist kein Wahrheitsbeweis.\n",
        encoding="utf-8")


def absence_negation(case: Path) -> None:
    evidence(case, lambda e: field(e, "notes",
        "Keine Evidenz ist kein Beweis für die Falschheit der These."))


def same_source_new_label(case: Path) -> None:
    source(case, lambda s: field(s, "label",
        "Another display label for the very same recorded source"))


def unknown_claim_source(case: Path) -> None:
    claim(case, lambda c: field(c, "source_refs", ["s999"]))


def unknown_claim_evidence(case: Path) -> None:
    claim(case, lambda c: field(c, "evidence_refs", ["e999"]))


def unknown_evidence_source(case: Path) -> None:
    evidence(case, lambda e: field(e, "source_ref", "s999"))


def unknown_evidence_claim(case: Path) -> None:
    evidence(case, lambda e: field(e, "claim_refs", ["c999"]))


def unknown_relation_claim(case: Path) -> None:
    relation(case, lambda r: field(r, "claim_ref", "c999"))


def missing_source_weight_audit(case: Path) -> None:
    (case / "source-weight-audit.yml").unlink()


def premature_established(case: Path) -> None:
    claim(case, lambda c: field(c, "status", "established"))


def false_receipt_status(case: Path) -> None:
    mutate_yaml(case, "answer-receipt.yml", lambda r: field(
        r, "verdicts_used", [{
            "claim_id": "c001",
            "statement": "Synthetic proposition under evaluation.",
            "status": "established",
        }]))


def missing_redteam(case: Path) -> None:
    mutate_yaml(case, "lifecycle.yml", lambda d: field(
        d, "redteam_ref", "missing-redteam.yml"))


def wrong_event_time(case: Path) -> None:
    claim(case, lambda c: field(c, "statement",
        "Event A occurred at 10:00 UTC on 2026-01-01."))
    evidence(case, lambda e: field(e, "summary",
        "The same Event A occurred at 11:00 UTC on 2026-01-01, not at 10:00."))
    evidence(case, lambda e: field(e, "verbatim_or_ref",
        "Original event ledger: Event A at 11:00 UTC on 2026-01-01."))


def wrong_participant_count(case: Path) -> None:
    claim(case, lambda c: field(c, "statement",
        "The single verified participant register contains exactly two people."))
    evidence(case, lambda e: field(e, "summary",
        "The same participant register contains three distinct people."))
    evidence(case, lambda e: field(e, "verbatim_or_ref",
        "Original register entries: participant 1, participant 2, participant 3."))


def overclaim_answer(case: Path) -> None:
    mutate_yaml(case, "answer-receipt.yml", lambda d: field(d,
        "answer_summary",
        "The proposition is conclusively proven beyond all doubt, although its "
        "structured claim status remains merely plausible."))


@dataclass(frozen=True)
class Challenge:
    name: str
    lane: str
    expected: str
    purpose: str
    mutation: Callable[[Path], None]


CHALLENGES = (
    Challenge("valid_baseline", "valid_control", "accept",
              "Known-valid fixture unchanged", baseline),
    Challenge("valid_quoted_consensus", "valid_control", "accept",
              "A scientific-consensus quotation is not a truth certificate", scientific_quote),
    Challenge("valid_absence_negation", "valid_control", "accept",
              "Absence-of-evidence negation is not a forbidden phrase", absence_negation),
    Challenge("valid_source_relabel", "valid_control", "accept",
              "A display label is not independent corroboration", same_source_new_label),
    Challenge("orphan_claim_source", "structural_fault", "reject",
              "Claim references missing source", unknown_claim_source),
    Challenge("orphan_claim_evidence", "structural_fault", "reject",
              "Claim references missing evidence", unknown_claim_evidence),
    Challenge("orphan_evidence_source", "structural_fault", "reject",
              "Evidence references missing source", unknown_evidence_source),
    Challenge("orphan_evidence_claim", "structural_fault", "reject",
              "Evidence references missing claim", unknown_evidence_claim),
    Challenge("orphan_relation_claim", "structural_fault", "reject",
              "Typed relation references missing claim", unknown_relation_claim),
    Challenge("missing_weight_audit", "structural_fault", "reject",
              "Weighted source has no source-weight audit", missing_source_weight_audit),
    Challenge("premature_established", "structural_fault", "reject",
              "Established verdict is declared without strong proof chain", premature_established),
    Challenge("receipt_status_mismatch", "structural_fault", "reject",
              "Answer receipt overstates the structured verdict", false_receipt_status),
    Challenge("missing_redteam", "structural_fault", "reject",
              "Lifecycle points to missing red-team file", missing_redteam),
    Challenge("contradictory_event_time", "semantic_canary", "reject",
              "The cited event time directly contradicts the claim", wrong_event_time),
    Challenge("contradictory_count", "semantic_canary", "reject",
              "Source states three people while claim says exactly two", wrong_participant_count),
    Challenge("rhetorical_certainty_laundering", "semantic_canary", "reject",
              "Answer asserts certainty while structured claim is plausible", overclaim_answer),
)
assert len({case.name for case in CHALLENGES}) == len(CHALLENGES)


def validator_commands() -> tuple[tuple[str, bool], ...]:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    block = text.split("\nvalidate:\n", 1)[1].split("\ntest:\n", 1)[0]
    pat = re.compile(
        r"^\s*\$\(PYTHONPATH_ENV\) \$\(PYTHON\) "
        r"(scripts/[A-Za-z0-9_.-]+\.py) cases(\s+--check)?\s*$",
        re.MULTILINE,
    )
    commands = tuple((name, bool(check)) for name, check in pat.findall(block))
    if len(commands) < 30:
        raise ValueError("Unexpectedly short real validator chain")
    return commands


def tree_hashes(folder: Path) -> dict[str, str]:
    return {
        str(p.relative_to(folder)): digest(p.read_bytes())
        for p in sorted(folder.rglob("*")) if p.is_file()
    }


def execute_case(case: Challenge, commands: tuple[tuple[str, bool], ...]) -> dict:
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="lab-fitness-") as temp:
        folder = Path(temp) / "cases" / "sandbox" / "minimal-valid-case"
        folder.parent.mkdir(parents=True)
        shutil.copytree(BASE, folder)
        before = tree_hashes(folder)
        case.mutation(folder)
        after = tree_hashes(folder)
        failures, crashes = [], []
        for filename, check in commands:
            # Most production CLIs discover case *children* below a root.
            # Passing the case directory itself silently skips some validators.
            argv = [sys.executable, str(ROOT / filename), str(folder.parent)]
            if check:
                argv.append("--check")
            try:
                result = subprocess.run(
                    argv, cwd=ROOT, stdin=subprocess.DEVNULL,
                    capture_output=True, text=True, timeout=20, check=False
                )
                # Probe case enumeration explicitly. A vacuous 0 exit must
                # not masquerade as acceptance of a challenge.
                if filename == "scripts/validate_case_references.py" and str(folder) not in result.stdout:
                    crashes.append({"validator": filename,
                                    "error": "target_case_not_discovered",
                                    "diagnostic": result.stdout[-300:]})
                if "No case directories found" in result.stdout:
                    crashes.append({"validator": filename,
                                    "error": "empty_discovery",
                                    "diagnostic": result.stdout[-300:]})
                if result.returncode:
                    raw = (result.stdout + "\n" + result.stderr).strip()
                    entry = {
                        "validator": filename, "exit": result.returncode,
                        "diagnostic": raw[-550:],
                    }
                    if "Traceback (most recent call last)" in raw:
                        crashes.append(entry)
                    else:
                        failures.append(entry)
            except (subprocess.TimeoutExpired, OSError) as error:
                crashes.append({"validator": filename, "error": type(error).__name__})
        observed = "error" if crashes else ("reject" if failures else "accept")
        return {
            "id": case.name, "lane": case.lane, "expected": case.expected,
            "purpose": case.purpose, "observed": observed,
            "changed_files": sorted(
                k for k in before.keys() | after.keys()
                if before.get(k) != after.get(k)
            ),
            "mutated_file_hashes": after,
            "rejecting_validators": [x["validator"] for x in failures],
            "failures": failures, "crashes": crashes,
            "seconds": round(time.monotonic() - start, 2),
        }


def summarize(cases: list[dict]) -> dict:
    if {c["id"] for c in cases} != {c.name for c in CHALLENGES}:
        raise ValueError("Case results are incomplete or duplicated")
    result = {"total": len(cases)}
    for lane in ("valid_control", "structural_fault", "semantic_canary"):
        rows = [row for row in cases if row["lane"] == lane]
        result[lane] = {
            "total": len(rows),
            "accepted": sum(x["observed"] == "accept" for x in rows),
            "rejected": sum(x["observed"] == "reject" for x in rows),
            "errors": sum(x["observed"] == "error" for x in rows),
            "met_expectation": sum(x["observed"] == x["expected"] for x in rows),
        }
    result["structural_detection_rate"] = round(
        result["structural_fault"]["rejected"] /
        result["structural_fault"]["total"], 3
    )
    result["benign_false_alarm_rate"] = round(
        result["valid_control"]["rejected"] /
        result["valid_control"]["total"], 3
    )
    result["semantic_canary_detection_rate"] = round(
        result["semantic_canary"]["rejected"] /
        result["semantic_canary"]["total"], 3
    )
    result["case_errors"] = sum(x["observed"] == "error" for x in cases)
    return result


def report(data: dict) -> str:
    summary = data["summary"]
    text = [
        "# Claim-Audit-Lab adversarial fitness test",
        "",
        "Source commit: " + data["source_commit"],
        "Production validators per case: " + str(len(data["validators"])),
        "",
        "| Lane | Detected / passed desired outcome | Cases | Rejected | Accepted | Errors |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for lane in ("valid_control", "structural_fault", "semantic_canary"):
        row = summary[lane]
        text.append(
            f"| {lane} | {row['met_expectation']} | {row['total']} | "
            f"{row['rejected']} | {row['accepted']} | {row['errors']} |"
        )
    text += ["", "| Case | Expected | Observed | Rejecting validators |",
             "|---|---|---|---:|"]
    for row in data["cases"]:
        text.append(f"| {row['id']} | {row['expected']} | "
                    f"{row['observed']} | {len(row['rejecting_validators'])} |")
    text += [
        "",
        "Structural controls measure reference and artifact integrity, not factual truth.",
        "Semantic canaries have predeclared elementary contradictions or overclaiming. "
        "An accepted semantic canary is a measured limitation, not a hidden success.",
        "Benign controls measure false alarms due to wording. Do not add word blacklists "
        "or a mandatory quality gate based on this exploratory test.",
        "",
    ]
    return "\n".join(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    commands = validator_commands()
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if not args.execute:
        print(json.dumps({
            "protocol": PROTOCOL, "source_commit": source_commit,
            "validators": len(commands),
            "cases": [{"id": x.name, "lane": x.lane, "expected": x.expected,
                       "purpose": x.purpose} for x in CHALLENGES],
        }, ensure_ascii=False, indent=2))
        return
    output_path = Path(__file__).resolve().parent / "results.json"
    if output_path.exists():
        raise SystemExit("Results already exist. Original evidence must not be overwritten.")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(lambda c: execute_case(c, commands), CHALLENGES))
    payload = {
        "protocol": PROTOCOL, "source_commit": source_commit,
        "fixture": str(BASE.relative_to(ROOT)),
        "fixture_claims_sha256": digest((BASE / "claims.yml").read_bytes()),
        "validators": [{"name": n, "check": c} for n, c in commands],
        "summary": summarize(records),
        "cases": records,
    }
    for file, data in (
        ("results.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n"),
        ("report.md", report(payload))
    ):
        target = output_path.parent / file
        temp = target.with_suffix(target.suffix + ".tmp")
        temp.write_text(data, encoding="utf-8")
        temp.replace(target)
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    if payload["summary"]["case_errors"]:
        raise SystemExit("Validator crashes/timeouts occurred; inspect recorded failures.")


if __name__ == "__main__":
    main()