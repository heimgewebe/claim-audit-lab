"""No-network contract tests for the original fitness-to-shadow bridge."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evaluations" / "fitness-semantic-bridge-v1" / "run.py"
spec = importlib.util.spec_from_file_location("fitness_bridge_tests", SCRIPT)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)


def test_exact_original_canaries_and_paired_source_identical():
    cases = bridge.extract_from_original_cases()
    assert len(cases) == 6
    assert len({c["id"] for c in cases}) == 6
    assert {c["source_fitness_case"] for c in cases} == {
        "contradictory_event_time",
        "contradictory_count",
        "rhetorical_certainty_laundering",
    }
    assert all(c["source_fitness_case"] in c["id"] for c in cases)
    for origin in {c["source_fitness_case"] for c in cases}:
        pair = {c["lane"]: c for c in cases if c["source_fitness_case"] == origin}
        assert set(pair) == {"canary", "control"}
        assert pair["canary"]["source_excerpt"] == pair["control"]["source_excerpt"]
        assert pair["control"]["gold_label"] == "supported"
        assert pair["canary"]["gold_label"] in {"contradicted", "insufficient"}
        assert pair["canary"]["mutated_fixture_sha256"] == pair["control"]["mutated_fixture_sha256"]


def test_oracles_are_independent_of_model_output():
    cases = bridge.extract_from_original_cases()
    assert {
        c["source_fitness_case"]: c["gold_label"]
        for c in cases if c["lane"] == "canary"
    } == {
        "contradictory_event_time": "contradicted",
        "contradictory_count": "contradicted",
        "rhetorical_certainty_laundering": "insufficient",
    }
    statements = {c["source_fitness_case"]: c for c in cases if c["lane"] == "canary"}
    assert "10:00 UTC" in statements["contradictory_event_time"]["claim"]
    assert "11:00 UTC" in statements["contradictory_event_time"]["source_excerpt"]
    assert "exactly two people" in statements["contradictory_count"]["claim"]
    assert "three distinct people" in statements["contradictory_count"]["source_excerpt"]
    assert "conclusively proven" in statements["rhetorical_certainty_laundering"]["claim"]
    assert "plausible" in statements["rhetorical_certainty_laundering"]["source_excerpt"]


def test_frozen_prompt_does_not_include_gold_or_authority_fields():
    cases = bridge.extract_from_original_cases()
    samples = bridge.assignments(cases)
    assert [r["order"] for r in samples] == list(range(6))
    assert samples == bridge.assignments(bridge.extract_from_original_cases())
    for case, sample in zip(cases, samples):
        assert sample["prompt"] == bridge.shadow.prompt_for(case)
        assert sample["prompt_sha256"] == bridge.shadow.sha(sample["prompt"])
        altered = {**case, "gold_label": "SECRET", "gold_rationale": "SECRET"}
        assert bridge.shadow.prompt_for(case) == bridge.shadow.prompt_for(altered)


def test_missed_canaries_not_counted_as_semantic_success():
    cases = bridge.extract_from_original_cases()
    rows = [
        {"id": c["id"], "status": "valid",
         "judgment": {"label": "supported"}}
        for c in cases
    ]
    metrics = bridge.metrics(cases, rows)
    assert metrics["control"]["correct_exact"] == 3
    assert metrics["canary"]["correct_exact"] == 0
    assert metrics["invalid"] == 0
    assert metrics["false_positive_controls"] == 0


def test_false_rejection_of_valid_control_is_measured():
    cases = bridge.extract_from_original_cases()
    rows = [
        {"id": c["id"], "status": "valid",
         "judgment": {"label": c["gold_label"]}}
        for c in cases
    ]
    row = next(row for row in rows if row["id"].endswith("-control"))
    row["judgment"]["label"] = "contradicted"
    metrics = bridge.metrics(cases, rows)
    assert metrics["canary"]["correct_exact"] == 3
    assert metrics["control"]["correct_exact"] == 2
    assert metrics["false_positive_controls"] == 1


def test_missing_model_output_is_invalid_not_false_positive():
    cases = bridge.extract_from_original_cases()
    results = [
        {"id": c["id"], "error": "local_provider_unreachable"}
        for c in cases
    ]
    scores = bridge.metrics(cases, results)
    assert scores["invalid"] == 6
    assert scores["control"]["valid"] == 0
    assert scores["canary"]["correct_exact"] == 0
    assert scores["false_positive_controls"] == 0


def test_results_directory_cannot_be_overwritten(monkeypatch, tmp_path):
    cases = bridge.extract_from_original_cases()
    preexisting = tmp_path / "prior"
    preexisting.mkdir()
    (preexisting / "results.json").write_text('{"archive":"untouched"}')
    monkeypatch.setattr(sys, "argv", [
        "run.py", "--execute", "--output-dir", str(preexisting)
    ])
    with pytest.raises(SystemExit, match="exists"):
        bridge.main()
    assert json.loads((preexisting / "results.json").read_text()) == {"archive": "untouched"}
