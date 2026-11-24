#!/usr/bin/env python3
"""Reproduce the completed target-model baseline offline; no inference."""
import argparse
import hashlib
import json
import pathlib
import runpy
import statistics

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=pathlib.Path, required=True)
    p.add_argument("--archive", type=pathlib.Path, required=True)
    a = p.parse_args()
    root = a.repo / "evaluations"
    here = root / "nabu-epistemic-baseline-v1"
    sci = runpy.run_path(str(root / "scifact-expert-v1/run.py"))
    _, corpus = sci["load_release"](a.archive)
    original = runpy.run_path(str(here / "run.py"))
    shadow = sci["load_shadow"]()
    results = here / "run-thinking.jsonl"
    assert digest(results) == "3e93a9949894612c3277eda6811ed7354f0a0e025e2e0cd3745520750689565f"
    header, *rows = map(json.loads, results.read_text().splitlines())
    assert header["runner_sha256"] == digest(here / "run.py")
    assert header["archive_sha256"] == sci["RELEASE_SHA256"]
    assert header["model"] == original["MODEL"] and header["digest"] == original["DIGEST"]
    assert header["think"] is True and header["options"] == original["OPTIONS"]
    base = json.loads((root / "evidence-switch-v1/protocol.json").read_text())["treatments"]["minimal"]
    assert header["instructions"] == {"minimal": base, "relations": base + original["RULE"]}
    cases = {c["id"]: c for c in header["cases"]}
    expected = {}
    for d, h, claim, gold, why in original["REAL"]:
        ex = sci["source_text"](corpus[d])
        assert shadow.sha(ex) == h
        expected[str(d)] = ("scifact-original", str(d), ex, claim, gold, why)
    for k, family, ex, claim, gold, why in original["SYNTH"]:
        expected[k] = ("fictional", family, ex, claim, gold, why)
    assert set(cases) == set(expected)
    for k, c in cases.items():
        assert tuple(c[x] for x in ("kind", "family", "source_excerpt", "claim", "gold", "gold_reason")) == expected[k]
        assert shadow.sha(c["source_excerpt"]) == c["source_sha256"]
    assert len(rows) == 24
    assert {(r["case_id"], r["arm"]) for r in rows} == {(k, arm) for k in cases for arm in header["instructions"]}
    for r in rows:
        c = cases[r["case_id"]]
        assert r["source_sha256"] == c["source_sha256"]
        shadow.INSTRUCTION = header["instructions"][r["arm"]]
        assert shadow.sha(shadow.prompt_for(c)) == r["prompt_sha256"]
        assert shadow.sha(r["raw_response"]) == r["response_sha256"]
        assert r["model_digest"] == header["digest"] and r["model_used"] == header["model"]
        assert r["status"] == "valid" and shadow.parse_response(r["raw_response"], c["source_excerpt"]) == r["judgment"]
    for arm in header["instructions"]:
        rr = [r for r in rows if r["arm"] == arm]
        def right(r):
            return r["judgment"]["label"] == cases[r["case_id"]]["gold"]
        print(arm, json.dumps({
            "n": len(rr), "valid": len(rr), "correct_frozen": sum(map(right, rr)),
            "real_correct": sum(right(r) for r in rr if cases[r["case_id"]]["kind"] == "scifact-original"),
            "posthoc_excluding_ambiguous_correct": sum(right(r) for r in rr if r["case_id"] not in {"cause-a", "interest-a"}),
            "posthoc_n": 10, "prompt_tokens": sum(r["prompt_eval_count"] for r in rr),
            "generated_tokens": sum(r["eval_count"] for r in rr),
            "median_seconds": statistics.median(r["duration_seconds"] for r in rr),
            "errors_frozen": [r["case_id"] for r in rr if not right(r)],
        }))
    print("Verified all 24 original rows, frozen case definitions, source/prompt/response digests, model identity and parser outcomes.")
if __name__ == "__main__":
    main()
