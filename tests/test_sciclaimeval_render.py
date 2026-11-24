"""Integrity tests for a retired historical scientific pilot; no inference."""
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RetiredPilotArchiveTests(unittest.TestCase):
    def test_new_manifest_excludes_old_papers_and_has_paper_disjoint_holdout(self):
        import json
        base = ROOT / "evaluations"
        current = json.loads((base / "sciclaimeval-render-v1" / "manifest.json").read_text())
        previous = json.loads((base / "sciclaimeval-revision-v1" / "manifest.json").read_text())
        old_papers = {c["paper_id"] for c in previous["samples"]}
        items = current["samples"]
        self.assertEqual(current["schema_version"],
                         "claim-audit-lab.sciclaimeval-render-manifest-v1")
        self.assertEqual(len(items), 6)
        self.assertEqual(len({i["pair_id"] for i in items}), 6)
        self.assertEqual(len({i["paper_id"] for i in items}), 6)
        self.assertFalse(old_papers & {i["paper_id"] for i in items})
        from collections import Counter
        tally = Counter((i["split"], i["domain"]) for i in items)
        self.assertEqual(dict(tally), {
            ("development", "nlp"): 2, ("development", "peerj"): 1,
            ("holdout", "nlp"): 2, ("holdout", "peerj"): 1,
        })
        for item in items:
            self.assertEqual(item["license_name"], "CC BY 4.0")
            self.assertEqual(set(item["sources"]), {"Supported", "Refuted"})
            self.assertEqual(len(item["claim_sha256"]), 64)
            for part in item["sources"].values():
                self.assertEqual(len(part["sha256"]), 64)
                self.assertEqual(len(part["display_sha256"]), 64)
                self.assertGreaterEqual(part["row_count"], 2)

    def test_original_model_receipts_unchanged_and_no_holdout_inference(self):
        import json
        directory = ROOT / "evaluations" / "sciclaimeval-render-v1"
        fixed = {
            "run-development-qwen3-14b-raw.json":
                "41ac1ec42ad5ccc202cc694d567e645e00f7f60625892c58e2f4e34935483dad",
            "run-development-qwen3-14b-rendered.json":
                "c33fd2e74524d57173b21981dc2dd5bcdc20996a930e7e12ff634db026cea005",
            "run-development-gemma4-12b-raw.json":
                "34aab99dd9da972d5379f470d10b09bc363fbb7563c857e429c04b25beacbd1d",
            "run-development-gemma4-12b-rendered.json":
                "5d1ec499338959d3f9862d50e4bd9b2116b61e2c2af6af698c287081baa0a998",
        }
        self.assertEqual(
            {f.name for f in directory.glob("run-development-*.json")},
            set(fixed),
        )
        self.assertFalse(list(directory.glob("run-holdout-*.json")))
        manifest_sha = hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()
        # Results are immutable evidence from the preregistered pre-review
        # renderer. Post-observation guards must not rewrite that origin.
        renderer_sha = (
            "b6542c4f3896dee1644ea7b45a8e3deaec9aff6b55626e6cfc8f2d90092b25cf"
        )
        calls = 0
        for name, expected_sha in fixed.items():
            raw = (directory / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected_sha)
            result = json.loads(raw)
            self.assertEqual(result["manifest_sha256"], manifest_sha)
            self.assertEqual(result["renderer_sha256"], renderer_sha)
            self.assertEqual(result["split"], "development")
            self.assertEqual(result["metrics"]["total_calls"], 15)
            for pair in result["rows"]:
                for row in pair["steps"].values():
                    text = row.get("raw_response")
                    if text is not None:
                        self.assertEqual(
                            hashlib.sha256(text.encode()).hexdigest(),
                            row["response_sha256"],
                        )
                    calls += 1
        self.assertEqual(calls, 60)

    def test_original_code_archived_but_not_active(self):
        directory = ROOT / "evaluations" / "sciclaimeval-render-v1"
        for filename, digest in (
            ("original-render.py.txt", "b6542c4f3896dee1644ea7b45a8e3deaec9aff6b55626e6cfc8f2d90092b25cf"),
            ("original-run.py.txt", "4fd816dd0202d67b3ee9bebced2d727ca3f47ef5b55d1c26739bf5a8ce3546b9"),
        ):
            self.assertEqual(hashlib.sha256((directory / filename).read_bytes()).hexdigest(), digest)
        self.assertFalse((directory / "render.py").exists())
        self.assertFalse((directory / "run.py").exists())
