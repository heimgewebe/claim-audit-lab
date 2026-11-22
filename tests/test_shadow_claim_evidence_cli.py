"""No-network tests for the optional single-source shadow CLI."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "shadow_claim_evidence.py"
spec = importlib.util.spec_from_file_location("single_claim_shadow_test", SCRIPT)
cli = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cli
spec.loader.exec_module(cli)


def test_correct_quote_and_prompt_reuse(monkeypatch):
    evidence = "Original ledger: Event A occurred at 11:00 UTC."
    claim = "Event A occurred at 10:00 UTC."
    seen = []

    def fake_ollama(sample, excerpt, model):
        seen.append((sample, excerpt, model))
        return {
            "status": "valid",
            "judgment": {
                "label": "contradicted",
                "evidence_span": "Event A occurred at 11:00 UTC.",
                "reason": "The one event has a different timestamp in the source.",
            },
            "raw_response": '{"label":"contradicted"}',
            "response_sha256": cli.digest('{"label":"contradicted"}'),
            "provider_response_sha256": "local-response-digest",
            "prompt_eval_count": 120,
        }

    monkeypatch.setattr(cli.shadow, "run_ollama_one", fake_ollama)
    result = cli.evaluate(claim, evidence, "gemma4:12b")
    assert result["status"] == "valid"
    assert result["verdict"]["label"] == "contradicted"
    assert result["mode"] == "advisory_only"
    assert result["source_authenticity_verified"] is False
    assert result["claim_sha256"] == hashlib.sha256(claim.encode()).hexdigest()
    assert result["source_excerpt_sha256"] == hashlib.sha256(evidence.encode()).hexdigest()
    sample, excerpt, model = seen[0]
    assert model == "gemma4:12b" and excerpt == evidence
    assert sample["prompt"] == cli.shadow.prompt_for(
        {"claim": claim, "source_excerpt": evidence}
    )
    assert result["prompt_sha256"] == cli.digest(sample["prompt"])
    assert result["provider_response_sha256"] == "local-response-digest"
    assert result["prompt_eval_count"] == 120
    assert result["context_window_tokens"] == cli.shadow.OLLAMA_NUM_CTX


def test_absent_model_does_not_fabricate_semantic_label(monkeypatch):
    def unavailable(sample, excerpt, model):
        return {"error": "local_provider_unreachable"}

    monkeypatch.setattr(cli.shadow, "run_ollama_one", unavailable)
    result = cli.evaluate("Claim X", "Excerpt Y", "gemma4:12b")
    assert result["status"] == "error"
    assert result["verdict"] is None
    assert result["error"] == "local_provider_unreachable"
    assert result["raw_response"] is None


@pytest.mark.parametrize("claim,excerpt", [
    ("", "Nonempty excerpt"),
    ("Claim X", ""),
    ("  ", "Source excerpt"),
    ("Claim X", "\n \t"),
])
def test_blank_input_never_calls_model(monkeypatch, claim, excerpt):
    def unexpected(*args, **kwargs):
        raise AssertionError("Model called for a blank input")

    monkeypatch.setattr(cli.shadow, "run_ollama_one", unexpected)
    with pytest.raises(ValueError):
        cli.evaluate(claim, excerpt, "gemma4:12b")


def test_too_long_excerpt_is_not_silently_truncated():
    with pytest.raises(ValueError, match="choose a bounded"):
        cli.evaluate("Example", "A" * (cli.MAX_EXCERPT_CHARS + 1), "gemma4:12b")


def test_cli_prints_one_explicitly_advisory_json_result(tmp_path, monkeypatch, capsys):
    excerpt = "Observed item count: three."
    file = tmp_path / "source.txt"
    file.write_text(excerpt, encoding="utf-8")

    def fake_ollama(sample, actual_excerpt, model):
        assert actual_excerpt == excerpt
        return {
            "status": "valid",
            "judgment": {"label": "insufficient", "evidence_span": "",
                         "reason": "The excerpt says nothing about dates."},
            "raw_response": '{"label":"insufficient"}',
            "response_sha256": cli.digest('{"label":"insufficient"}'),
        }

    monkeypatch.setattr(cli.shadow, "run_ollama_one", fake_ollama)
    monkeypatch.setattr(sys, "argv", [
        "shadow_claim_evidence.py", "--claim", "The item was found yesterday.",
        "--excerpt-file", str(file), "--model", "gemma4:12b",
    ])
    cli.main()
    output = json.loads(capsys.readouterr().out)
    assert output["verdict"]["label"] == "insufficient"
    assert output["source_excerpt"] == excerpt
    assert output["source_authenticity_verified"] is False
    assert not (tmp_path / "results.json").exists()


def test_cli_reports_provider_error_and_nonzero_exit(tmp_path, monkeypatch, capsys):
    file = tmp_path / "source.txt"
    file.write_text("A measured fact", encoding="utf-8")
    monkeypatch.setattr(cli.shadow, "run_ollama_one",
                        lambda *args: {"error": "local_provider_unreachable"})
    monkeypatch.setattr(sys, "argv", [
        "shadow_claim_evidence.py", "--claim", "Some claim",
        "--excerpt-file", str(file),
    ])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert json.loads(capsys.readouterr().out)["verdict"] is None

def test_cli_bounds_input_read_before_rejecting_oversized_file(tmp_path, monkeypatch, capsys):
    file = tmp_path / "oversized.txt"
    file.write_text("A" * (cli.MAX_EXCERPT_CHARS + 100), encoding="utf-8")

    def must_not_use_unbounded_reader(*args, **kwargs):
        raise AssertionError("Unbounded Path.read_text was called")

    monkeypatch.setattr(Path, "read_text", must_not_use_unbounded_reader)
    monkeypatch.setattr(cli.shadow, "run_ollama_one",
                        lambda *args: (_ for _ in ()).throw(
                            AssertionError("model called for oversized input")))
    monkeypatch.setattr(sys, "argv", [
        "shadow_claim_evidence.py", "--claim", "Claim X",
        "--excerpt-file", str(file),
    ])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert "choose a bounded" in capsys.readouterr().err
