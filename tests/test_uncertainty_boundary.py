"""Regression tests for the preregistered, non-blocking semantic holdout."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "evaluations" / "uncertainty-boundary-v1" / "run.py"
spec = importlib.util.spec_from_file_location("uncertainty_boundary_evaluation_test", SCRIPT)
evaluation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = evaluation
spec.loader.exec_module(evaluation)


def test_gold_file_frozen_and_source_families_disjoint():
    data, digest = evaluation.load_cases()
    assert digest == evaluation.FROZEN_CASES_SHA256
    cases = data["cases"]
    assert len(cases) == 18
    assert len({c["id"] for c in cases}) == len({c["family"] for c in cases}) == 18
    for split in ("development", "holdout"):
        selected = [c for c in cases if c["split"] == split]
        assert len(selected) == 9
        assert {c["gold_label"] for c in selected} == {
            "supported", "contradicted", "insufficient",
        }


def test_relabeling_precommitted_cases_requires_new_version(tmp_path, monkeypatch):
    data, _ = evaluation.load_cases()
    data["cases"][0]["gold_label"] = "contradicted"
    (tmp_path / "cases.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(evaluation, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="preregistered gold file changed"):
        evaluation.load_cases()


def test_prompt_never_receives_precommitted_answer_or_source_metadata():
    data, _ = evaluation.load_cases()
    source = evaluation.model_module()
    case = data["cases"][0]
    changed = {**case, "gold_label": "SECRET_GOLD",
               "gold_rationale": "SECRET_REASON", "family": "SECRET_SOURCE"}
    assert source.prompt_for(case) == source.prompt_for(changed)
    assert case["claim"] in source.prompt_for(case)
    assert case["source_excerpt"] in source.prompt_for(case)


def test_existing_output_is_not_overwritten_or_reexecuted(tmp_path, monkeypatch):
    destination = tmp_path / "run-baseline-development-gemma4-12b.json"
    destination.write_text("existing evidence", encoding="utf-8")
    monkeypatch.setattr(evaluation, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["run.py", "--split", "development",
                                      "--profile", "baseline", "--model", "gemma4:12b"])
    with pytest.raises(SystemExit) as exc:
        evaluation.main()
    assert exc.value.code == 2
    assert destination.read_text(encoding="utf-8") == "existing evidence"


def test_holdout_response_hashes_and_metrics():
    """Check published holdout rows against frozen gold and exact prompt/response bytes."""
    data, case_digest = evaluation.load_cases()
    holdout = {c["id"]: c for c in data["cases"] if c["split"] == "holdout"}
    for profile in ("baseline", "v1"):
        model_module = evaluation.model_module()
        if profile == "v1":
            rule = (evaluation.ROOT / "candidate-rule-v1.txt").read_text(encoding="utf-8").strip()
            model_module.INSTRUCTION += " " + rule
        for model in ("qwen3:14b", "gemma4:12b"):
            name = f"run-{profile}-holdout-{model.replace(':', '-')}.json"
            saved = json.loads((evaluation.ROOT / name).read_text(encoding="utf-8"))
            assert saved["case_sha256"] == case_digest
            assert saved["expected"] == saved["valid"] == len(holdout)
            rows = saved["results"]
            assert len(rows) == len(holdout)
            assert {r["id"] for r in rows} == set(holdout)
            for row in rows:
                assert row["status"] == "valid"
                assert isinstance(row["raw_response"], str)
                assert hashlib.sha256(row["raw_response"].encode()).hexdigest() == row["response_sha256"]
                prompt = model_module.prompt_for(holdout[row["id"]])
                assert model_module.sha(prompt) == row["prompt_sha256"]
            assert saved["correct"] == sum(r["label"] == holdout[r["id"]]["gold_label"] for r in rows)
            assert saved["false_contradictions"] == sum(
                r["label"] == "contradicted" and holdout[r["id"]]["gold_label"] != "contradicted"
                for r in rows
            )
