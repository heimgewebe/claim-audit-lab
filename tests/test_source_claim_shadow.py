"""No-network checks for the opt-in source excerpt → claim shadow reviewer."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "evaluations" / "source-claim-shadow-v1" / "run.py"
)
spec = importlib.util.spec_from_file_location("source_claim_shadow", SCRIPT)
shadow = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = shadow
spec.loader.exec_module(shadow)


def test_gold_is_predeclared_balanced_and_split_by_source():
    cases = shadow.load_cases()
    assert len(cases) == 18
    assert len({x["id"] for x in cases}) == 18
    assert {x["split"] for x in cases} == {"development", "holdout"}
    for label in shadow.LABELS:
        assert sum(x["gold_label"] == label for x in cases) == 6
    for split in ("development", "holdout"):
        assert sum(x["split"] == split for x in cases) == 9
    assert len({x["source_url"] for x in cases}) == 6


def test_prompt_and_order_never_expose_gold_or_authority_metadata():
    cases = shadow.load_cases()
    assert shadow.assignments(cases) == shadow.assignments(cases)
    for case in cases:
        altered = {
            **case,
            "gold_label": "SECRET_GOLD",
            "gold_rationale": "SECRET_RATIONALE",
            "source_url": "https://secret.invalid/",
            "publisher": "SECRET_AUTHORITY",
            "split": "SECRET_SPLIT",
        }
        assert shadow.prompt_for(case) == shadow.prompt_for(altered)
        prompt = shadow.prompt_for(case)
        assert case["claim"] in prompt
        assert case["source_excerpt"] in prompt
        assert "SECRET_" not in prompt
    assert [x["order"] for x in shadow.assignments(cases)] == list(range(18))


def test_verbatim_span_and_missing_evidence_enforced():
    excerpt = "A report states a tenfold increase in measured amplitude."
    correct = {
        "label": "supported",
        "evidence_span": "tenfold increase in measured amplitude",
        "reason": "The excerpt states the claimed effect.",
    }
    assert shadow.parse_response(json.dumps(correct), excerpt) == correct
    with pytest.raises(ValueError, match="verbatim"):
        shadow.parse_response(
            json.dumps({**correct, "evidence_span": "ten times greater"}),
            excerpt,
        )
    with pytest.raises(ValueError, match="should not fabricate"):
        shadow.parse_response(
            json.dumps({**correct, "label": "insufficient"}),
            excerpt,
        )
    assert shadow.parse_response(json.dumps({
        **correct, "label": "insufficient", "evidence_span": ""
    }), excerpt)["label"] == "insufficient"
    with pytest.raises(ValueError):
        shadow.parse_response(json.dumps({**correct, "label": []}), excerpt)
    with pytest.raises(ValueError):
        shadow.parse_response(json.dumps({**correct, "other": "value"}), excerpt)


def test_three_class_metrics_and_false_accusations_are_distinct():
    cases = shadow.load_cases()
    rows = [
        {"id": case["id"], "status": "valid",
         "judgment": {"label": case["gold_label"]}}
        for case in cases
    ]
    perfect = shadow.measurements(cases, rows)
    assert perfect["split_metrics"]["holdout"]["accuracy"] == 1.0
    assert perfect["false_contradiction_count"] == 0
    assert perfect["invalid"] == 0

    supported = next(c for c in cases if c["gold_label"] == "supported")
    contradicted = next(c for c in cases if c["gold_label"] == "contradicted")
    for row in rows:
        if row["id"] == supported["id"]:
            row["judgment"]["label"] = "contradicted"
        if row["id"] == contradicted["id"]:
            row["judgment"]["label"] = "insufficient"
    imperfect = shadow.measurements(cases, rows)
    assert imperfect["split_metrics"]["all"]["correct"] == 16
    assert imperfect["false_contradiction_count"] == 1
    assert imperfect["per_class"]["contradicted"]["recall_all_cases"] < 1.0


def test_failed_response_is_retained_and_does_not_fake_accuracy(monkeypatch):
    case = shadow.load_cases()[0]
    sample = shadow.assignments([case])[0]
    raw = "not JSON"

    def fake_exec(args, **kwargs):
        assert "--sandbox" in args and "read-only" in args
        assert "--ignore-user-config" in args
        assert "--ephemeral" in args
        assert case["gold_rationale"] not in args[-1]
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=raw, stderr="")

    monkeypatch.setattr(shadow.subprocess, "run", fake_exec)
    result = shadow.run_one(sample, case["source_excerpt"])
    assert result["error"] == "invalid_output"
    assert result["raw_response"] == raw
    assert result["response_sha256"] == shadow.sha(raw)
    assert "judgment" not in result
    assembled = [
        {"id": item["id"], "error": "no_model_execution"}
        for item in shadow.load_cases()
    ]
    metrics = shadow.measurements(shadow.load_cases(), assembled)
    assert metrics["valid"] == 0
    assert metrics["split_metrics"]["all"]["accuracy"] is None
    assert metrics["split_metrics"]["all"]["accuracy_over_all_inputs"] == 0
    assert metrics["per_class"]["supported"]["recall_all_cases"] == 0

def test_expired_auth_failure_is_classified_without_leaking_stderr(monkeypatch):
    sample = shadow.assignments(shadow.load_cases())[0]
    stderr = "Failed to refresh token: your refresh token has expired; unauthorized (401)"

    def fake_exec(args, **kwargs):
        return subprocess.CompletedProcess(
            args=args, returncode=1, stdout="", stderr=stderr
        )

    monkeypatch.setattr(shadow.subprocess, "run", fake_exec)
    result = shadow.run_one(sample, "Any arbitrary excerpt")
    assert result["error"] == "authentication_expired"
    assert result["stderr_sha256"] == shadow.sha(stderr)
    assert "stderr" not in result
    assert "judgment" not in result


def test_first_cli_failure_aborts_remaining_17_without_false_accuracy(monkeypatch, tmp_path):
    import json

    seen = []

    def fake_one(sample, excerpt):
        seen.append(sample["id"])
        return {**sample, "exit_code": 1, "error": "authentication_expired"}

    monkeypatch.setattr(shadow, "run_one", fake_one)
    monkeypatch.setattr(
        sys, "argv",
        ["run.py", "--execute", "--output-dir", str(tmp_path / "failed-run")],
    )
    with pytest.raises(SystemExit, match="Incomplete model run"):
        shadow.main()
    assert len(seen) == 1
    result = json.loads((tmp_path / "failed-run" / "results.json").read_text())
    assert result["metrics"]["attempted_calls"] == 1
    assert result["metrics"]["valid"] == 0
    assert result["metrics"]["invalid"] == 18
    assert result["metrics"]["split_metrics"]["holdout"]["accuracy"] is None
    assert sum(r["error"] == "not_run_after_provider_failure" for r in result["runs"]) == 17
    assert "UNUSABLE MODEL TRIAL" in (tmp_path / "failed-run" / "report.md").read_text()


def test_local_ollama_response_preserves_original_prompt_and_verbatim_quote(monkeypatch):
    import io

    case = shadow.load_cases()[0]
    sample = shadow.assignments([case])[0]
    quoted = case["source_excerpt"][:25]
    model_response = json.dumps({
        "label": "supported",
        "evidence_span": quoted,
        "reason": "The quoted source passage directly provides this evidence.",
    })
    raw_api = json.dumps({
        "model": "qwen3:14b",
        "response": model_response,
        "done": True,
        "eval_count": 44,
    })
    observed = []

    def fake_urlopen(request, timeout=None):
        observed.append((request.full_url, timeout, json.loads(request.data)))
        return io.BytesIO(raw_api.encode("utf-8"))

    monkeypatch.setattr(shadow.urllib.request, "urlopen", fake_urlopen)
    output = shadow.run_ollama_one(sample, case["source_excerpt"], "qwen3:14b")
    assert output["status"] == "valid"
    assert output["judgment"]["label"] == "supported"
    assert output["response_sha256"] == shadow.sha(model_response)
    assert output["provider_response_sha256"] == shadow.sha(raw_api)
    url, timeout, payload = observed[0]
    assert url == "http://127.0.0.1:11434/api/generate"
    assert payload["prompt"] == sample["prompt"]
    assert payload["model"] == "qwen3:14b"
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["options"]["temperature"] == 0
    assert len(observed) == 1


def test_local_unavailable_model_returns_explicit_error(monkeypatch):
    from urllib.error import URLError

    def refused(request, timeout=None):
        raise URLError("connection refused")

    monkeypatch.setattr(shadow.urllib.request, "urlopen", refused)
    case = shadow.load_cases()[0]
    sample = shadow.assignments([case])[0]
    result = shadow.run_ollama_one(sample, case["source_excerpt"], "qwen3:14b")
    assert result["error"] == "local_provider_unreachable"
    assert "judgment" not in result
    assert "raw_response" not in result


def test_local_backend_driver_never_leaks_gold_or_reuses_old_output(monkeypatch, tmp_path):
    observed = []

    def local_model(sample, excerpt, model_name):
        observed.append((sample["id"], model_name))
        return {**sample, "error": "local_provider_unreachable"}

    monkeypatch.setattr(shadow, "run_ollama_one", local_model)
    output_dir = tmp_path / "ollama-failed"
    monkeypatch.setattr(sys, "argv", [
        "run.py", "--execute", "--backend", "ollama",
        "--local-model", "qwen3:14b", "--output-dir", str(output_dir),
    ])
    with pytest.raises(SystemExit, match="Incomplete model run"):
        shadow.main()
    assert len(observed) == 1
    assert observed[0][1] == "qwen3:14b"
    recorded = json.loads((output_dir / "results.json").read_text())
    assert recorded["backend"] == "ollama"
    assert recorded["model"] == "qwen3:14b"
    assert recorded["metrics"]["attempted_calls"] == 1
    assert recorded["metrics"]["split_metrics"]["holdout"]["accuracy"] is None
    assert sum(x["error"] == "not_run_after_provider_failure" for x in recorded["runs"]) == 17
    with pytest.raises(SystemExit, match="exists"):
        shadow.main()
