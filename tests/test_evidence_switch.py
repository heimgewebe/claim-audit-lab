"""Effect and scientific-fitness boundaries for the evidence-switch benchmark."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "evaluations" / "evidence-switch-v1" / "run.py"
spec = importlib.util.spec_from_file_location("evidence_switch_runner", SCRIPT)
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def test_precommitted_source_swap_is_one_constant_claim_with_three_gold_states():
    protocol, cases = runner.read_protocol()
    assert protocol["schema_version"] == "claim-audit-lab.evidence-switch-protocol.v1"
    assert len(cases) == 36
    assert {c["split"] for c in cases} == {"development", "holdout"}
    for family in {c["family"] for c in cases}:
        group = [c for c in cases if c["family"] == family]
        assert len(group) == 3
        assert {c["gold_label"] for c in group} == set(runner.LABELS)
        assert len({c["claim"] for c in group}) == 1
        assert len({c["source_excerpt"] for c in group}) == 3


def test_only_evidence_and_claim_pass_to_both_model_treatments():
    protocol, cases = runner.read_protocol()
    case = cases[0]
    for treatment in runner.CONDITIONS:
        reviewer = runner.reviewer_module(treatment, protocol)
        scrubbed = {**case, "gold_label": "SECRET_GOLD", "gold_rationale": "SECRET_REASON",
                    "family": "SECRET_FAMILY", "split": "SECRET_SPLIT"}
        assert reviewer.prompt_for(case) == reviewer.prompt_for(scrubbed)
        prompt = reviewer.prompt_for(case)
        assert "SECRET_" not in prompt
        assert case["claim"] in prompt and case["source_excerpt"] in prompt


def test_metrics_count_false_accusations_and_complete_evidence_families():
    _, cases = runner.read_protocol()
    selected = [case for case in cases if case["split"] == "development"]
    baseline = [{"id": c["id"], "status": "valid", "label": c["gold_label"]} for c in selected]
    good = runner.summarize(baseline, selected)
    assert good["correct"] == 18
    assert good["complete_three_state_families"] == 6
    assert good["false_contradictions"] == good["missed_explicit_contradictions"] == 0
    one = next(c for c in selected if c["gold_label"] == "insufficient")
    for record in baseline:
        if record["id"] == one["id"]:
            record["label"] = "contradicted"
    bad = runner.summarize(baseline, selected)
    assert bad["correct"] == 17
    assert bad["false_contradictions"] == 1
    assert bad["complete_three_state_families"] == 5


def test_changed_gold_or_protocol_is_rejected(monkeypatch, tmp_path):
    protocol, cases = runner.read_protocol()
    (tmp_path / "cases.json").write_text(json.dumps({"cases": cases}, ensure_ascii=False))
    (tmp_path / "protocol.json").write_text(json.dumps(protocol, ensure_ascii=False))
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Prerecorded gold/protocol changed"):
        runner.read_protocol()


def test_second_run_refuses_overwrite_without_model_call(monkeypatch, tmp_path):
    destination = tmp_path / "run-development-gemma4-12b-lab.json"
    destination.write_text("immutable", encoding="utf-8")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["run.py", "--split", "development",
                                     "--model", "gemma4:12b", "--condition", "lab"])
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    assert destination.read_text() == "immutable"
