"""Pure, no-network checks for the opt-in SciClaimEval revision pilot."""
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1] / "evaluations" / "sciclaimeval-revision-v1"
PILOT = runpy.run_path(str(ROOT / "run.py"))


class SciClaimEvalRevisionTests(unittest.TestCase):
    def test_frozen_manifest_has_paper_disjoint_expert_pairs(self):
        data = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(data["dataset_revision"], PILOT["REVISION"])
        self.assertEqual(data["release_sha256"], PILOT["RELEASE_SHA256"])
        self.assertEqual(data["selection_rule"], PILOT["SELECTION_RULE"])
        self.assertEqual(len(data["samples"]), 6)
        self.assertEqual(
            {(item["split"], item["domain"]) for item in data["samples"]},
            {(s, d) for s in PILOT["SPLITS"] for d in PILOT["DOMAINS"]},
        )
        self.assertEqual(len({item["pair_id"] for item in data["samples"]}), 6)
        self.assertEqual(len({item["paper_id"] for item in data["samples"]}), 6)
        for sample in data["samples"]:
            self.assertEqual(set(sample["sources"]), set(PILOT["LABELS"]))
            self.assertEqual(sample["license_name"], "CC BY 4.0")
            self.assertEqual(len(sample["claim_sha256"]), 64)
            for evidence in sample["sources"].values():
                self.assertEqual(len(evidence["sha256"]), 64)
                self.assertTrue(350 <= evidence["bytes"] <= 6000)

    def test_only_numbers_in_claim_not_references(self):
        self.assertFalse(PILOT["numeric_claim"]("Table 4 in Smith (2024) summarizes results."))
        self.assertTrue(PILOT["numeric_claim"]("The average is 0.61 versus 0.63 in Table 1."))

    def test_source_paths_are_not_general_network_urls(self):
        with self.assertRaises(ValueError):
            PILOT["source_url"]("data/tables/dev/../../test.tex")
        with self.assertRaises(ValueError):
            PILOT["source_url"]("data/papers/dev/foo.json")
        self.assertIn(PILOT["REVISION"], PILOT["source_url"]("data/tables/dev/t.tex"))

    def test_updated_prompt_does_not_assert_world_truth(self):
        text = PILOT["updated_prompt"]("X is 10.", "Table", "X & 5")
        self.assertIn("alternative version", text)
        self.assertIn("Do not assume newer means true", text)
        self.assertNotIn("Refuted", text)
        self.assertNotIn("Supported", text)

    def test_scores_revisions_and_unjustified_changes_separately(self):
        def one(expected, label):
            return {
                "expected_expert_relation": expected, "label": label,
                "status": "valid", "error": None, "duration_seconds": 1.0,
            }
        rows = [{
            "steps": {
                "initial_supported": one("Supported", "supported"),
                "initial_refuted": one("Refuted", "contradicted"),
                "revision_to_refuted": one("Refuted", "contradicted"),
                "revision_to_supported": one("Supported", "supported"),
                "unchanged_control": one("Supported", "supported"),
            }
        }]
        m = PILOT["score"](rows)
        self.assertEqual(m["revision_appropriate_flip"], 2)
        self.assertEqual(m["anchored_wrong_on_revision"], 0)
        self.assertEqual(m["control_label_changed"], 0)
        self.assertEqual(m["total_model_calls"], 5)
        rows[0]["steps"]["unchanged_control"]["label"] = "contradicted"
        self.assertEqual(PILOT["score"](rows)["control_label_changed"], 1)


if __name__ == "__main__":
    unittest.main()
