"""SciFact reference quality, provenance and no-leak tests."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "evaluations/scifact-expert-v1/run.py"
spec = importlib.util.spec_from_file_location("scifact_expert_runner_test", SCRIPT)
bench = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bench
spec.loader.exec_module(bench)


def _artificial_inputs():
    claims, docs = [], {}
    for group, label in enumerate(bench.STRATA):
        for n in range(11):
            did, cid = 1000 + group * 100 + n, 100 + group * 100 + n
            docs[did] = {
                "doc_id": did, "title": f"Paper {did}",
                "abstract": [
                    f"Experiment {did} measured one observed scientific outcome and discussed a particular controlled intervention.",
                    "It gave relevant observations and reported methodological limitations for the experimental procedure.",
                ],
            }
            claims.append({
                "id": cid, "claim": f"Experimental claim about record {cid} and the observed scientific outcome.",
                "evidence": {} if label == bench.STRATA[2] else {
                    str(did): [{"label": label, "sentences": [0]}]},
                "cited_doc_ids": [did],
            })
    return claims, docs


def test_selection_precommitted_disjoint_and_balanced():
    claims, docs = _artificial_inputs()
    a = bench.choose_manifest(claims, docs)
    assert a == bench.choose_manifest(claims, docs)
    assert a["sample_count"] == 30
    assert len({v["claim_id"] for v in a["samples"]}) == 30
    assert len({v["doc_id"] for v in a["samples"]}) == 30
    for split in bench.SPLITS:
        for label in bench.STRATA:
            items = [x for x in a["samples"] if x["split"] == split and x["reference_label"] == label]
            assert len(items) == 5
            assert all(x["rationale_sentence_indices"] == ([] if label == bench.STRATA[2] else [0]) for x in items)
    assert "NOT an expert NEI gold label" in a["gold_semantics"][bench.STRATA[2]]


def test_weak_negative_has_no_false_nei_accuracy_claim():
    samples = [{"id": "a", "reference_label": "SUPPORT"},
               {"id": "b", "reference_label": "CONTRADICT"},
               {"id": "c", "reference_label": bench.STRATA[2]}]
    rows = [{"id": "a", "status": "valid", "label": "supported"},
            {"id": "b", "status": "valid", "label": "insufficient"},
            {"id": "c", "status": "valid", "label": "contradicted"}]
    score = bench.measurements(rows, samples)
    assert score["expert_expected"] == score["expert_valid"] == 2
    assert score["expert_correct"] == 1
    assert score["missed_expert_refute"] == 1
    assert score["unannotated_cited_contradicted"] == 1
    assert "nei_correct" not in score and "false_nei_contradiction" not in score


def test_invalid_output_never_counts_as_model_mistake():
    score = bench.measurements(
        [{"id": "a", "status": "error", "label": None}],
        [{"id": "a", "reference_label": "CONTRADICT"}],
    )
    assert score["valid"] == score["expert_valid"] == score["expert_correct"] == 0
    assert score["invalid_or_unattempted"] == 1


def test_comparator_uses_existing_frozen_minimal_prompt():
    shadow = bench.load_shadow()
    original = shadow.INSTRUCTION
    bench.select_instruction(shadow, "minimal")
    frozen = json.loads(bench.MINIMAL_PROMPT.read_text(encoding="utf-8"))
    assert shadow.INSTRUCTION == frozen["treatments"]["minimal"]
    assert original != shadow.INSTRUCTION
    prompt = shadow.prompt_for({"claim": "A scientific claim", "source_excerpt": "The abstract text."})
    assert "A scientific claim" in prompt and "The abstract text." in prompt
    assert "gold_label" not in prompt


def test_invalid_archive_checksum_fails_before_parse(tmp_path):
    p = tmp_path / "untrusted.tar.gz"
    p.write_bytes(b"invalid corpus")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        bench.load_release(p)


def test_create_only_run_refuses_overwrite_without_generation(monkeypatch, tmp_path):
    p = tmp_path / "run-development-qwen3-14b-lab.json"
    p.write_text("original receipt", encoding="utf-8")
    monkeypatch.setattr(bench, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "run.py", "trial", "--archive", str(tmp_path / "absent.tar.gz"),
        "--split", "development", "--model", "qwen3:14b", "--condition", "lab",
    ])
    with pytest.raises(SystemExit) as error:
        bench.main()
    assert error.value.code == 2
    assert p.read_text() == "original receipt"


def test_committed_manifest_contains_hashes_not_copyrighted_abstracts():
    p = bench.ROOT / "manifest.json"
    if not p.exists():
        pytest.skip("No manifest committed yet")
    manifest = json.loads(p.read_text(encoding="utf-8"))
    assert manifest["sample_count"] == 30
    assert manifest["release_sha256"] == bench.RELEASE_SHA256
    assert len({s["claim_id"] for s in manifest["samples"]}) == 30
    assert len({s["doc_id"] for s in manifest["samples"]}) == 30
    expected_keys = {"id", "claim_id", "doc_id", "reference_label",
                     "claim_sha256", "abstract_sha256", "rationale_sentence_indices",
                     "paper_title", "split"}
    for sample in manifest["samples"]:
        assert set(sample) == expected_keys
        assert len(sample["abstract_sha256"]) == len(sample["claim_sha256"]) == 64


def test_continue_only_verbatim_quote_format_failure_with_bound_original_result():
    shadow = bench.load_shadow()
    by_claim = {1: "The original study measured a specific treatment effect."}
    doc = {
        2: {"abstract": [
            "The study measured an outcome in trial A and found a clearly reported result.",
            "It did not evaluate the proposed treatment effect in the final analysis.",
        ]}
    }
    excerpt = bench.source_text(doc[2])
    prompt = shadow.prompt_for({"claim": by_claim[1], "source_excerpt": excerpt})
    raw = json.dumps({"label": "contradicted", "evidence_span": "a fabricated quote",
                      "reason": "Unsupported citation."})
    row = {
        "id": "1:2", "status": "error", "error": "invalid_output",
        "label": None, "evidence_span": None, "raw_response": raw,
        "prompt_sha256": shadow.sha(prompt), "response_sha256": bench.sha(raw.encode()),
    }
    selected = [{"id": "1:2", "claim_id": 1, "doc_id": 2},
                {"id": "4:5", "claim_id": 4, "doc_id": 5}]
    previous = {
        "release_sha256": bench.RELEASE_SHA256, "manifest_sha256": "m" * 64,
        "split": "development", "model": "qwen3:14b", "condition": "lab",
        "backend_sha256": bench.sha(bench.SHADOW.read_bytes()),
        "instruction_sha256": shadow.sha(shadow.INSTRUCTION),
        "rows": [row],
    }
    accepted = bench.verified_resume_prefix(
        previous, "m" * 64, "development", "qwen3:14b", "lab",
        selected, by_claim, doc, shadow,
    )
    assert accepted == [row]
    tampered = json.loads(json.dumps(previous))
    tampered["rows"][0]["response_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        bench.verified_resume_prefix(
            tampered, "m" * 64, "development", "qwen3:14b", "lab",
            selected, by_claim, doc, shadow,
        )
    tampered = json.loads(json.dumps(previous))
    tampered["condition"] = "minimal"
    with pytest.raises(ValueError, match="identity"):
        bench.verified_resume_prefix(
            tampered, "m" * 64, "development", "qwen3:14b", "lab",
            selected, by_claim, doc, shadow,
        )


def test_saved_trial_responses_are_sha_bound_and_gold_is_scored_separately():
    import random

    manifest_path = bench.ROOT / "manifest.json"
    if not manifest_path.exists():
        pytest.skip("No externally derived sample manifest")
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    manifest_sha = bench.sha(raw)
    for file in sorted(bench.ROOT.glob("run-*.json")):
        saved = json.loads(file.read_text(encoding="utf-8"))
        assert saved["release_sha256"] == bench.RELEASE_SHA256
        assert saved["manifest_sha256"] == manifest_sha
        assert saved["expert_labels_only_for_annotated_pairs"] is True
        assert saved["cited_unannotated_is_not_nei_gold"] is True
        samples = [s for s in manifest["samples"] if s["split"] == saved["split"]]
        random.Random(bench.SEED).shuffle(samples)
        rows = saved["rows"]
        assert [r["id"] for r in rows] == [s["id"] for s in samples[:len(rows)]]
        for row in rows:
            assert isinstance(row["raw_response"], str)
            assert bench.sha(row["raw_response"].encode()) == row["response_sha256"]
            assert isinstance(row["prompt_sha256"], str) and len(row["prompt_sha256"]) == 64
        assert saved["metrics"] == bench.measurements(rows, samples)


def test_resumed_trial_preserves_original_invalid_citation_without_relabeling():
    old = bench.ROOT / "run-development-qwen3-14b-lab.json"
    resumed = bench.ROOT / "run-development-qwen3-14b-lab-resumed.json"
    if not resumed.exists():
        pytest.skip("No completed continuation yet")
    a, b = json.loads(old.read_text()), json.loads(resumed.read_text())
    assert b["continuation_from_sha256"] == bench.sha(old.read_bytes())
    assert b["rows"][:len(a["rows"])] == a["rows"]
    assert len(b["rows"]) == 15
    assert b["metrics"]["invalid_or_unattempted"] == 1
    assert b["metrics"]["expert_expected"] == 10
    assert b["metrics"]["expert_valid"] == 9


def test_report_expert_scores_and_invalid_denominators_match_original_files():
    root = bench.ROOT
    report = root / "report.md"
    if not report.exists():
        pytest.skip("Final report not yet compiled")
    body = report.read_text(encoding="utf-8")
    totals = {"minimal": 0, "lab": 0}
    for split in ("development", "holdout"):
        for model in ("qwen3:14b", "gemma4:12b"):
            metrics = {}
            for variant in ("minimal", "lab"):
                suffix = "-resumed" if split == "development" and model == "qwen3:14b" and variant == "lab" else ""
                name = f"run-{split}-{model.replace(':', '-')}-{variant}{suffix}.json"
                score = json.loads((root / name).read_text(encoding="utf-8"))["metrics"]
                assert score["expert_expected"] == 10
                metrics[variant] = score
                totals[variant] += score["expert_correct"]
            a, b = metrics["minimal"], metrics["lab"]
            row = (
                f"| {split} | {model} | {a['expert_correct']}/10 | {b['expert_correct']}/10 "
                f"| {10 - a['expert_valid']} / {10 - b['expert_valid']} | "
                f"{a['missed_expert_refute']} / {b['missed_expert_refute']} |"
            )
            assert row in body
    assert totals == {"minimal": 34, "lab": 31}
    assert "34/40" in body and "31/40" in body
    assert "descriptive controls" in body
    assert "**not** expert-labeled NOT_ENOUGH_INFO gold" in body
