"""No-network row-display/source-provenance tests for a scientific source pilot."""
import hashlib
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
R = runpy.run_path(str(ROOT / "evaluations" / "sciclaimeval-render-v1" / "render.py"))
RUNNER = ROOT / "evaluations" / "sciclaimeval-render-v1" / "run.py"


class DisplayProofTests(unittest.TestCase):
    def test_latex_cell_numbers_have_source_backing(self):
        original = (
            r"\begin{tabular}{lrr}" + "\n"
            + r"Model & Noisy & Clean \\" + "\n"
            + r"Human & 69.13 & 86.57\\ \midrule" + "\n"
            + r"Transformer & 64.0 & 81.0 \\" + "\n"
            + r"\end{tabular}" + "\n"
        )
        view = R["render_table"](original)
        self.assertEqual(view["representation"], "latex")
        self.assertIn("Human | 69.13 | 86.57", view["rendered_source"])
        proof = R["prove_quote"](original, view, "Human | 69.13 | 86.57")
        self.assertEqual(proof["original_source_sha256"], hashlib.sha256(original.encode()).hexdigest())
        self.assertFalse(proof["display_quote_is_raw_verbatim"])
        start, end = proof["original_source_chars"]
        self.assertIn("69.13", original[start:end])
        with self.assertRaises(ValueError):
            R["prove_quote"](original, view, "Human | 69.13 | 99.99")
        with self.assertRaises(ValueError):
            R["prove_quote"](original.replace("86.57", "86.58"), view, "Human | 69.13")

    def test_html_decoded_entity_is_mapped_not_raw_quote(self):
        original = (
            "<html><table><tr><th>Field</th><th>P value</th></tr>\n"
            "<tr><td>Weekly PA</td><td>&lt;0.001</td></tr>\n"
            "<tr><td>Gender</td><td>0.202</td></tr></table></html>"
        )
        view = R["render_table"](original)
        self.assertIn("Weekly PA | <0.001", view["rendered_source"])
        proof = R["prove_quote"](original, view, "Weekly PA | <0.001")
        self.assertFalse(proof["display_quote_is_raw_verbatim"])
        start, end = proof["original_source_chars"]
        self.assertIn("&lt;0.001", original[start:end])
        with self.assertRaises(ValueError):
            R["prove_quote"](original, view, "Weekly PA | <0.001\nGender | 0.202")

    def test_ambiguous_and_invented_display_quotes_are_not_authenticated(self):
        original = (
            "<table><tr><td>Alpha</td><td>0.202</td></tr>"
            "<tr><td>Beta</td><td>0.202</td></tr></table>"
        )
        view = R["render_table"](original)
        with self.assertRaises(ValueError):
            R["prove_quote"](original, view, "0.202")
        with self.assertRaises(ValueError):
            R["prove_quote"](original, view, "99.99")
        self.assertIsNone(R["prove_quote"](original, view, ""))

    def test_original_raw_src_is_never_modified_by_render(self):
        text = (
            "\\begin{tabular}{ll}\n"
            "Human & 69.13\\\\\n"
            "Other & 70.00\\\\\n"
            "\\end{tabular}\n"
        )
        first = R["render_table"](text)
        self.assertEqual(first, R["render_table"](text))
        self.assertEqual(first["source_sha256"], hashlib.sha256(text.encode()).hexdigest())
        self.assertGreater(len(text), len(first["rendered_source"]))

    def test_multiline_latex_cells_remain_one_contiguous_source_row(self):
        source = (
            "\\begin{tabular}{lrrrr}\n"
            "Model & Noisy & Clean \\\\\n"
            "Human &\n"
            "69.13 &\n"
            "86.57 \\\\\n"
            "AI & 64 & 81 \\\\\n"
            "\\end{tabular}\n"
        )
        view = R["render_table"](source)
        self.assertEqual(len(view["rows"]), 3)
        quote = "Human | 69.13 | 86.57"
        self.assertIn(quote, view["rendered_source"])
        proof = R["prove_quote"](source, view, quote)
        start, end = proof["original_source_chars"]
        self.assertIn("Human &\n69.13 &\n86.57", source[start:end])
        self.assertEqual(proof["quoted_display_sha256"],
                         hashlib.sha256(quote.encode()).hexdigest())

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
        renderer_sha = hashlib.sha256((directory / "render.py").read_bytes()).hexdigest()
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

    def test_unknown_format_and_wrong_length_rejected(self):
        with self.assertRaises(ValueError):
            R["render_table"]("not a table")
        with self.assertRaises(ValueError):
            R["render_table"]("A" * 7100)


if __name__ == "__main__":
    unittest.main()