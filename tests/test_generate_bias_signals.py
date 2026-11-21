#!/usr/bin/env python3
"""Tests for generate_bias_signals.py."""

from pathlib import Path

import pytest
import yaml

import generate_bias_signals as gbs


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def make_case(tmp_path: Path, name: str = "example") -> Path:
    case_dir = tmp_path / "cases" / name
    case_dir.mkdir(parents=True)
    return case_dir


def claim(claim_id, status="plausible", **extra):
    base = {
        "claim_id": claim_id,
        "claim_type": extra.pop("claim_type", "factual_event_claim"),
        "statement": extra.pop("statement", f"Statement for {claim_id}"),
        "status": status,
    }
    base.update(extra)
    return base


def types_of(signals):
    return {s["signal_type"] for s in signals}


class TestRelationThresholdProximity:
    def test_strength_near_gate_fires(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001")]})
        write(case / "evidence-relations.yml", {
            "relations": [{
                "relation_id": "r001",
                "evidence_ref": "e001",
                "claim_ref": "c001",
                "relation_type": "supports_directly",
                "strength": 0.76,
                "explanation": "near the 0.75 gate",
            }]
        })
        signals = gbs.generate_for_case(case)
        assert "relation_threshold_proximity" in types_of(signals)

    def test_strength_far_from_gate_does_not_fire(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001")]})
        write(case / "evidence-relations.yml", {
            "relations": [{
                "relation_id": "r001",
                "evidence_ref": "e001",
                "claim_ref": "c001",
                "relation_type": "supports_directly",
                "strength": 0.50,
                "explanation": "comfortably away from any gate",
            }]
        })
        signals = gbs.generate_for_case(case)
        assert "relation_threshold_proximity" not in types_of(signals)

    def test_strength_near_gate_with_supports_fires(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001")]})
        write(case / "evidence-relations.yml", {
            "relations": [{
                "relation_id": "r001",
                "evidence_ref": "e001",
                "claim_ref": "c001",
                "relation_type": "supports",
                "strength": 0.76,
                "explanation": "near the 0.75 gate via supports",
            }]
        })
        signals = gbs.generate_for_case(case)
        assert "relation_threshold_proximity" in types_of(signals)

    def test_strength_near_gate_with_contradicts_fires(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001")]})
        write(case / "evidence-relations.yml", {
            "relations": [{
                "relation_id": "r001",
                "evidence_ref": "e001",
                "claim_ref": "c001",
                "relation_type": "contradicts",
                "strength": 0.76,
                "explanation": "near the 0.75 gate via contradicts",
            }]
        })
        signals = gbs.generate_for_case(case)
        assert "relation_threshold_proximity" in types_of(signals)


class TestRedteamPendingWithFinalLanguage:
    def test_pending_redteam_with_final_lifecycle_fires(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001")]})
        write(case / "redteam.yml", {"verdict": {"status": "pending"}})
        write(case / "lifecycle.yml", {"status": "final_under_uncertainty"})
        signals = gbs.generate_for_case(case)
        assert "redteam_pending_with_final_language" in types_of(signals)

    def test_assessment_prose_is_not_a_lifecycle_gate(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001")]})
        write(case / "redteam.yml", {"verdict": {"status": "pending"}})
        write(case / "lifecycle.yml", {"status": "draft"})
        write(case / "assessment.md", "**Status: final_under_uncertainty**")
        assert "redteam_pending_with_final_language" not in types_of(gbs.generate_for_case(case))

    def test_pending_redteam_with_draft_lifecycle_does_not_fire(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001")]})
        write(case / "redteam.yml", {"verdict": {"status": "pending"}})
        write(case / "lifecycle.yml", {"status": "draft"})
        signals = gbs.generate_for_case(case)
        assert "redteam_pending_with_final_language" not in types_of(signals)


class TestSourceWeightAsymmetry:
    def _weight(self, level):
        return {
            "primary_proximity": level,
            "method_transparency": level,
            "reproducibility": level,
            "source_cluster_independence": level,
            "historical_track_record": level,
            "institutional_interest_risk": 1.0 - level,
            "update_latency_risk": 1.0 - level,
        }

    def test_asymmetry_with_justification_does_not_fire(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001", source_refs=["s001", "s002"])]})
        write(case / "sources.yml", {"sources": [
            {"source_id": "s001", "source_weight": self._weight(0.95)},
            {"source_id": "s002", "source_weight": self._weight(0.15)},
        ]})
        long_reason = "Detailed justification for this weighting decision spanning many words."
        write(case / "source-weight-audit.yml", {"records": [
            {"source_ref": "s001", "notes": long_reason},
            {"source_ref": "s002", "notes": long_reason},
        ]})
        signals = gbs.generate_for_case(case)
        assert "source_weight_asymmetry" not in types_of(signals)

    def test_asymmetry_without_justification_fires(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001", source_refs=["s001", "s002"])]})
        write(case / "sources.yml", {"sources": [
            {"source_id": "s001", "source_weight": self._weight(0.95)},
            {"source_id": "s002", "source_weight": self._weight(0.15)},
        ]})
        write(case / "source-weight-audit.yml", {"records": [
            {"source_ref": "s001", "notes": "ok"},
            {"source_ref": "s002", "notes": ""},
        ]})
        signals = gbs.generate_for_case(case)
        assert "source_weight_asymmetry" in types_of(signals)


class TestReportedClaimWorldPressure:
    def test_reported_claim_only_reporting_does_not_fire(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim", statement="Outlet X reported Y.")
        ]})
        write(case / "argument-provenance.yml", {"provenance": []})
        signals = gbs.generate_for_case(case)
        assert "reported_claim_world_pressure" not in types_of(signals)

    def test_reported_claim_used_as_world_argument_fires(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim", statement="Outlet X reported Y.",
                  world_claim_refs=["c002"]),
            claim("c002", claim_type="causal_claim", status="weak"),
        ]})
        # no argument-provenance.yml -> inference path undeclared
        signals = gbs.generate_for_case(case)
        sig_types = types_of(signals)
        assert "reported_claim_world_pressure" in sig_types
        sig = next(s for s in signals if s["signal_type"] == "reported_claim_world_pressure")
        assert "c001" in sig["affected_claims"] and "c002" in sig["affected_claims"]

    def test_evidence_pack_path_fires_when_directional_relation(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim", statement="Outlet X reported Y."),
            claim("c002", claim_type="causal_claim", status="weak"),
        ]})
        write(case / "evidence-pack.yml", {"evidence": [{
            "evidence_id": "e001",
            "claim_refs": ["c001"],
        }]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001",
            "evidence_ref": "e001",
            "claim_ref": "c002",
            "relation_type": "supports_directly",
            "strength": 0.70,
            "explanation": "reported evidence used to support world claim",
        }]})
        # no argument-provenance.yml -> inference path undeclared
        signals = gbs.generate_for_case(case)
        assert "reported_claim_world_pressure" in types_of(signals)
        sig = next(s for s in signals if s["signal_type"] == "reported_claim_world_pressure")
        assert "c001" in sig["affected_claims"]
        assert "c002" in sig["affected_claims"]

    def test_evidence_pack_safe_relation_does_not_fire(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim", statement="Outlet X reported Y."),
            claim("c002", claim_type="causal_claim", status="weak"),
        ]})
        write(case / "evidence-pack.yml", {"evidence": [{
            "evidence_id": "e001",
            "claim_refs": ["c001"],
        }]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001",
            "evidence_ref": "e001",
            "claim_ref": "c002",
            "relation_type": "reports",  # safe relation: contextualizes/reports
            "strength": 0.70,
            "explanation": "only contextualizes, no strong world effect",
        }]})
        # no argument-provenance.yml, but safe relation type -> no severe signal
        signals = gbs.generate_for_case(case)
        assert "reported_claim_world_pressure" not in types_of(signals)


    def test_empty_provenance_file_does_not_suppress_world_link(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim", world_claim_refs=["c002"]),
            claim("c002", claim_type="causal_claim"),
        ]})
        write(case / "argument-provenance.yml", "")
        assert "reported_claim_world_pressure" in types_of(gbs.generate_for_case(case))

    def test_unrelated_provenance_does_not_suppress_world_link(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim", world_claim_refs=["c002"]),
            claim("c002", claim_type="causal_claim"),
        ]})
        write(case / "argument-provenance.yml", {"arguments": [{
            "target_claim_ref": "c999",
            "premise_claim_refs": ["c001"],
            "forbidden_upgrades_checked": ["reported_to_world"],
            "allowed_effect": "non_decisive",
        }]})
        assert "reported_claim_world_pressure" in types_of(gbs.generate_for_case(case))

    def test_matching_argument_provenance_is_sufficient_for_world_link(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim", world_claim_refs=["c002"]),
            claim("c002", claim_type="causal_claim"),
        ]})
        write(case / "argument-provenance.yml", {"arguments": [{
            "argument_id": "arg001",
            "target_claim_ref": "c002",
            "premise_claim_refs": ["c001"],
            "forbidden_upgrades_checked": ["reported_to_world"],
            "allowed_effect": "non_decisive",
        }]})
        assert "reported_claim_world_pressure" not in types_of(gbs.generate_for_case(case))

    def test_matching_inference_ledger_is_valid_alternative(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim", world_claim_refs=["c002"]),
            claim("c002", claim_type="causal_claim"),
        ]})
        write(case / "inference-ledger.yml", {"inferences": [{
            "claim_ref": "c002",
            "premise_claim_refs": ["c001"],
            "forbidden_upgrades_checked": ["reported_to_world"],
            "inference_type": "direct_premise",
        }]})
        assert "reported_claim_world_pressure" not in types_of(gbs.generate_for_case(case))

    def test_ordinary_mention_does_not_claim_world_effect(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim"),
        ]})
        write(case / "assessment.md", "The source describes c001 as a report.")
        assert "reported_claim_world_pressure" not in types_of(gbs.generate_for_case(case))

    def test_relation_requires_matching_provenance_not_filename(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim"),
            claim("c002", claim_type="causal_claim"),
        ]})
        write(case / "evidence-pack.yml", {"evidence": [{
            "evidence_id": "e001", "claim_refs": ["c001"], "source_ref": "s001",
        }]})
        write(case / "sources.yml", {"sources": [{"source_id": "s001"}]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001", "evidence_ref": "e001", "claim_ref": "c002",
            "relation_type": "supports_directly", "strength": 0.70,
        }]})
        write(case / "argument-provenance.yml", {"arguments": []})
        assert "reported_claim_world_pressure" in types_of(gbs.generate_for_case(case))
        write(case / "argument-provenance.yml", {"arguments": [{
            "target_claim_ref": "c002",
            "premise_claim_refs": ["c001"],
            "forbidden_upgrades_checked": ["reported_to_world"],
            "allowed_effect": "non_decisive",
        }]})
        assert "reported_claim_world_pressure" not in types_of(gbs.generate_for_case(case))

    def test_major_effect_needs_independent_support_not_just_provenance(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim"),
            claim("c002", claim_type="causal_claim"),
        ]})
        write(case / "evidence-pack.yml", {"evidence": [{
            "evidence_id": "e001", "claim_refs": ["c001"], "source_ref": "s001",
        }]})
        write(case / "sources.yml", {"sources": [{"source_id": "s001"}]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001", "evidence_ref": "e001", "claim_ref": "c002",
            "relation_type": "supports_directly", "strength": 0.85,
        }]})
        write(case / "argument-provenance.yml", {"arguments": [{
            "target_claim_ref": "c002", "premise_claim_refs": ["c001"],
            "forbidden_upgrades_checked": ["reported_to_world"],
            "allowed_effect": "non_decisive",
        }]})
        assert "reported_claim_world_pressure" in types_of(gbs.generate_for_case(case))

    def test_weak_relation_does_not_require_world_provenance(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="reported_claim"),
            claim("c002", claim_type="causal_claim"),
        ]})
        write(case / "evidence-pack.yml", {"evidence": [{
            "evidence_id": "e001", "claim_refs": ["c001"],
        }]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001", "evidence_ref": "e001", "claim_ref": "c002",
            "relation_type": "supports_indirectly", "strength": 0.35,
        }]})
        assert "reported_claim_world_pressure" not in types_of(gbs.generate_for_case(case))


import json
import pathlib
from jsonschema_compat import jsonschema as _jsonschema


class TestLexicalNonVeto:
    def test_words_do_not_generate_mandatory_bias_signals(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001", status="weak")]})
        write(case / "assessment.md", "Ein wissenschaftlicher Konsens ist kein Wahrheitsbeweis. "
              "This clearly proves c001. No magical wording decides credibility.")
        assert gbs.generate_for_case(case) == []

    def test_comparative_wording_does_not_make_evidence(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [
            claim("c001", claim_kind="comparative_claim", notes="base rate"),
        ]})
        assert gbs.generate_for_case(case) == []


class TestDeterminismAndDocument:
    def test_signal_ids_are_stable(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001", status="weak")]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001", "evidence_ref": "e001",
            "claim_ref": "c001", "relation_type": "supports_directly",
            "strength": 0.76,
        }]})
        first = gbs.generate_for_case(case)
        second = gbs.generate_for_case(case)
        assert [s["signal_id"] for s in first] == [s["signal_id"] for s in second]
        assert all(s["signal_id"].startswith("bs_") and len(s["signal_id"]) == 15 for s in first)

    def test_write_produces_loadable_generated_file(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001", status="weak")]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001", "evidence_ref": "e001",
            "claim_ref": "c001", "relation_type": "supports_directly",
            "strength": 0.76,
        }]})
        rc = gbs.main([str(tmp_path / "cases"), "--write"])
        assert rc == 0
        out = case / "_generated" / "bias-signals.yml"
        assert out.exists()
        loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
        assert loaded["schema_version"] == "1.0"
        assert loaded["signals"]

    def test_check_detects_drift(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001", status="weak")]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001", "evidence_ref": "e001",
            "claim_ref": "c001", "relation_type": "supports_directly",
            "strength": 0.76,
        }]})
        gbs.main([str(tmp_path / "cases"), "--write"])
        # Only the structured relation changes; prose cannot change the signal.
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001", "evidence_ref": "e001",
            "claim_ref": "c001", "relation_type": "supports_directly",
            "strength": 0.50,
        }]})
        rc = gbs.main([str(tmp_path / "cases"), "--check"])
        assert rc == 1

    def test_check_passes_when_no_committed_file(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001", status="weak")]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001", "evidence_ref": "e001",
            "claim_ref": "c001", "relation_type": "supports_directly",
            "strength": 0.76,
        }]})
        rc = gbs.main([str(tmp_path / "cases"), "--check"])
        assert rc == 0

    def test_build_document_is_schema_valid(self, tmp_path):
        case = make_case(tmp_path)
        write(case / "claims.yml", {"claims": [claim("c001", status="weak")]})
        write(case / "evidence-relations.yml", {"relations": [{
            "relation_id": "r001", "evidence_ref": "e001",
            "claim_ref": "c001", "relation_type": "supports_directly",
            "strength": 0.76,
        }]})
        signals = gbs.generate_for_case(case)
        doc = gbs.build_document(gbs.relative_case_ref(case), signals)
        schema_path = pathlib.Path(gbs.__file__).parent.parent / "schemas" / "bias-signals.v1.schema.json"
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
        validator = _jsonschema.Draft7Validator(schema, format_checker=_jsonschema.FormatChecker())
        errors = list(validator.iter_errors(doc))
        assert errors == []
