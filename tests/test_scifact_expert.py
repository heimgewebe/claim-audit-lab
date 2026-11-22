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
