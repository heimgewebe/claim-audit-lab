#!/usr/bin/env python3
"""Verify and score the two frozen multisource screens, without inference.

Labels are operator annotations. Scientific adequacy of the reasons is
separate manual review in report.md; label score does not prove entailment.
"""
import argparse
import hashlib
import json
import pathlib
import re
import runpy
import statistics

def sha(x):
    return hashlib.sha256(x.encode()).hexdigest()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=pathlib.Path, required=True)
    p.add_argument("--archive", type=pathlib.Path, required=True)
    a = p.parse_args()
    root = a.repo / "evaluations"
    here = root / "nabu-multisource-v1"
    sci = runpy.run_path(str(root / "scifact-expert-v1/run.py"))
    _, corpus = sci["load_release"](a.archive)
    for real, script, result in [
        (False, "run_synthetic.py", "run-synthetic.jsonl"),
        (True, "run_scifact.py", "run-scifact.jsonl"),
    ]:
        m = runpy.run_path(str(here / script))
        expected = {}
        if real:
            for k, family, claim, gold, reason in m["CASES"]:
                pairs = m["FAMILIES"][family]
                sources = [sci["source_text"](corpus[d]) for d, _ in pairs]
                hashes = [h for _, h in pairs]
                assert list(map(sha, sources)) == hashes
                expected[k] = {"id": k, "family": family, "claim": claim,
                    "doc_ids": [d for d, _ in pairs], "sources": sources,
                    "source_hashes": hashes, "gold": gold, "decisive_reason": reason}
        else:
            for family, v, claim, sources, gold, reason in m["CASES"]:
                k = family + "-" + v
                expected[k] = {"id": k, "family": family, "claim": claim,
                    "sources": sources, "source_hashes": list(map(sha, sources)),
                    "gold": gold, "decisive_reason": reason}
        path = here / result
        header, *rows = map(json.loads, path.read_text().splitlines())
        assert header["runner_sha256"] == digest(here / script)
        assert header["model"] == m["MODEL"] and header["digest"] == m["DIGEST"]
        assert header["options"] == m["OPTIONS"] and header["think"] is True
        assert header["instruction"] == m["INSTRUCTION"]
        if real:
            assert header["archive_sha256"] == sci["RELEASE_SHA256"]
        hcases = {c["id"]: c for c in header["cases"]}
        assert len(header["cases"]) == len(hcases) == len(expected) == 12
        assert hcases == {k: {a: b for a, b in c.items() if not real or a != "sources"}
                          for k, c in expected.items()}
        assert len(rows) == 12 and {r["case_id"] for r in rows} == set(expected)
        correct = 0
        for r in rows:
            c = expected[r["case_id"]]
            assert sha(m["prompt_for"](c)) == r["prompt_sha256"]
            assert r["model_used"] == m["MODEL"] and r["model_digest"] == m["DIGEST"]
            raw = r["raw_response"]
            assert isinstance(raw, str) and sha(raw) == r["response_sha256"]
            assert type(r["prompt_eval_count"]) is int and 1 <= r["prompt_eval_count"] < 14336
            if r.get("error"):
                assert r["error"] == "generation_truncated" and r["done_reason"] == "length"
                continue
            assert r["status"] == "complete" and raw.strip()
            match = re.match(r"^\s*(?:\*\*)?(BELEGT|WIDERLEGT|OFFEN)\b", raw, re.I)
            label = match.group(1).upper() if match else None
            assert r["label"] == label
            correct += label == c["gold"]
            print(result, r["case_id"], "expected", c["gold"], "observed", label)
        print(json.dumps({"file": result, "sha256": digest(path), "n": len(rows),
            "correct_labels": correct, "complete": sum(r.get("status") == "complete" for r in rows),
            "errors": [r["case_id"] for r in rows if r.get("error")],
            "median_seconds": statistics.median(r["duration_seconds"] for r in rows),
            "prompt_tokens": sum(r["prompt_eval_count"] for r in rows),
            "generated_tokens": sum(r["eval_count"] for r in rows)}))
    print("Both original case grids, sources, instructions, model identity, prompts and responses verified.")
if __name__ == "__main__":
    main()
