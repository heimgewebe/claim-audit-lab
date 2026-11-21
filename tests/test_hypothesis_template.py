"""Regression test for case hypothesis scaffold integrity."""

from pathlib import Path

import yaml


def test_hypothesis_template_preserves_distinct_linked_record():
    template = Path(__file__).resolve().parent.parent / "cases" / "_template" / "hypotheses.yml"
    data = yaml.safe_load(template.read_text(encoding="utf-8"))
    hypotheses = data["hypotheses"]
    assert [entry["id"] for entry in hypotheses] == [
        "h1", "h2", "h3", "h4", "h_example_linked"
    ]
    assert hypotheses[3]["label"] == "coordinated_intentionality"
    assert hypotheses[3]["description"] == ""
    assert "claim_refs" not in hypotheses[3]
    assert hypotheses[4]["label"] == "alternative_causal_explanation"
    assert hypotheses[4]["claim_refs"] == ["c001"]
