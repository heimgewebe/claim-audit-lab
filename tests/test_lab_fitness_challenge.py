"""Independent no-network self-tests for the Lab adversarial challenge harness."""
from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path
import shutil

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "evaluations" / "lab-fitness-20261121" / "run.py"
spec = importlib.util.spec_from_file_location("lab_fitness", FILE)
fitness = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = fitness
spec.loader.exec_module(fitness)


def test_predeclared_case_matrix_not_posthoc():
    cases = fitness.CHALLENGES
    assert len(cases) == 16
    assert len({case.name for case in cases}) == len(cases)
    assert Counter(case.lane for case in cases) == {
        "valid_control": 4, "structural_fault": 9, "semantic_canary": 3,
    }
    assert all(case.expected == "reject" for case in cases
               if case.lane != "valid_control")
    assert all(case.expected == "accept" for case in cases
               if case.lane == "valid_control")
    assert len(fitness.validator_commands()) >= 30


@pytest.mark.parametrize("scenario_id,relative,needle", [
    ("contradictory_event_time", "claims.yml", "10:00 UTC"),
    ("contradictory_count", "claims.yml", "exactly two people"),
    ("rhetorical_certainty_laundering", "answer-receipt.yml", "conclusively proven"),
])
def test_semantic_mutations_have_explicit_distinct_oracles(
    scenario_id, relative, needle, tmp_path
):
    case = tmp_path / "case"
    shutil.copytree(fitness.BASE, case)
    scenario = next(x for x in fitness.CHALLENGES if x.name == scenario_id)
    scenario.mutation(case)
    payload = yaml.safe_load((case / relative).read_text(encoding="utf-8"))
    assert needle in str(payload)
    # Control inputs remain valid YAML with the same elementary IDs.
    assert yaml.safe_load((case / "claims.yml").read_text())["claims"][0]["claim_id"] == "c001"


def test_score_does_not_promote_semantic_misses_to_success():
    rows = [
        {"id": case.name, "lane": case.lane,
         "expected": case.expected,
         "observed": (
             "accept" if case.lane in {"valid_control", "semantic_canary"}
             else "reject"
         )}
        for case in fitness.CHALLENGES
    ]
    result = fitness.summarize(rows)
    assert result["structural_detection_rate"] == 1
    assert result["benign_false_alarm_rate"] == 0
    assert result["semantic_canary_detection_rate"] == 0
    assert result["semantic_canary"]["met_expectation"] == 0


def test_score_counts_crashes_separately_from_rejection():
    rows = [
        {"id": case.name, "lane": case.lane,
         "expected": case.expected,
         "observed": "error" if case.name == "orphan_claim_source"
         else case.expected}
        for case in fitness.CHALLENGES
    ]
    result = fitness.summarize(rows)
    assert result["structural_fault"]["errors"] == 1
    assert result["structural_detection_rate"] < 1
    assert result["case_errors"] == 1


def test_actual_baseline_is_accepted_by_production_validator_chain():
    known_good = fitness.CHALLENGES[0]
    record = fitness.execute_case(known_good, fitness.validator_commands())
    assert record["id"] == "valid_baseline"
    assert record["observed"] == "accept", record["failures"] + record["crashes"]
    assert record["changed_files"] == []


def test_mutated_reference_is_rejected_by_real_production_validators():
    case = next(x for x in fitness.CHALLENGES if x.name == "orphan_claim_source")
    record = fitness.execute_case(case, fitness.validator_commands())
    assert record["observed"] == "reject", record["failures"] + record["crashes"]
    assert any("case_references" in name or "source" in name
               for name in record["rejecting_validators"]), record



def test_repeated_run_uses_fresh_directory_and_preserves_prior_results(tmp_path):
    first = fitness.output_directory(tmp_path / "first")
    assert first.exists()
    original = b'{"first_run":true}\n'
    (first / "results.json").write_bytes(original)

    with pytest.raises(SystemExit, match="choose a fresh --output-dir"):
        fitness.output_directory(first)
    assert (first / "results.json").read_bytes() == original

    second = fitness.output_directory(tmp_path / "second")
    assert second.is_dir()
    assert second != first
    assert (first / "results.json").read_bytes() == original


def test_existing_report_alone_is_never_overwritten(tmp_path):
    directory = tmp_path / "partial"
    directory.mkdir()
    report = directory / "report.md"
    report.write_text("Earlier trial, not to be overwritten", encoding="utf-8")

    with pytest.raises(SystemExit):
        fitness.output_directory(directory)
    assert report.read_text(encoding="utf-8") == "Earlier trial, not to be overwritten"
