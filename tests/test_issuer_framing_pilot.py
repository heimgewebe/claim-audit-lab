"""No-network unit tests for the preregistered issuer framing pilot."""
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "evaluations" / "issuer-framing-20261121" / "run.py"
)
spec = importlib.util.spec_from_file_location("issuer_framing_pilot", SCRIPT)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def test_fixed_protocol_is_paired_and_deterministic():
    runs = pilot.assignments()
    assert len(runs) == 16
    assert runs == pilot.assignments()
    assert sorted(r["order_index"] for r in runs) == list(range(16))
    for case in pilot.SCENARIOS:
        for repetition in range(1, pilot.REPEATS + 1):
            pair = {
                r["arm"]: r for r in runs
                if r["scenario_id"] == case["id"] and r["repeat"] == repetition
            }
            assert set(pair) == {"a", "b"}
            # Issuer is the only changed text; numerical evidence is invariant.
            assert (
                pair["a"]["prompt"].replace(case["issuer_a"], "__ISSUER__")
                == pair["b"]["prompt"].replace(case["issuer_b"], "__ISSUER__")
            )


def test_response_parser_rejects_confidence_shortcuts_and_extra_fields():
    valid = {
        "causal_status": "plausible",
        "causal_support_0_100": 50,
        "main_evidence_limit": "not randomized",
        "strongest_alternative": "selection",
        "deciding_future_test": "randomized trial",
    }
    assert pilot.parse_response(json.dumps(valid)) == valid
    with pytest.raises(ValueError):
        pilot.parse_response(json.dumps({**valid, "causal_support_0_100": True}))
    with pytest.raises(ValueError):
        pilot.parse_response(json.dumps({**valid, "additional_policy_verdict": "approved"}))
    with pytest.raises(ValueError):
        pilot.parse_response(json.dumps({**valid, "causal_status": "proven"}))


def test_summary_reports_pair_flips_without_claiming_statistical_significance():
    pair = pilot.assignments()
    samples = []
    for run in pair:
        # Two opposing labels in the first scenario differ on this synthetic
        # test fixture; all other pairs are stable.
        status = (
            "plausible"
            if run["scenario_id"] == "waiting_nonrandom" and run["arm"] == "a"
            else "unsupported"
        )
        samples.append({
            **run,
            "status": "valid",
            "response": {
                "causal_status": status,
                "causal_support_0_100": 70 if status == "plausible" else 30,
                "main_evidence_limit": "fictional evidence",
                "strongest_alternative": "selection",
                "deciding_future_test": "randomize",
            },
        })
    summary, report = pilot.summarize(samples)
    assert summary["valid_runs"] == 16
    assert summary["complete_pairs"] == 8
    assert summary["total_status_flips"] == 2
    assert summary["max_absolute_support_delta"] == 40
    assert "single-model" in report
