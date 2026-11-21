"""Tests for scripts/validate_overclosure.py."""

import pathlib

import validate_overclosure

FIXTURE_ROOT = pathlib.Path(__file__).parent / "fixtures" / "overclosure"


def fixture_errors(kind: str, name: str) -> list[str]:
    return validate_overclosure.validate_case(FIXTURE_ROOT / kind / name)


def test_invalid_causal_chain_contradicted_without_required_chain_fails():
    errors = fixture_errors("invalid", "causal_chain_contradicted_without_required_chain")
    assert any("requires non-empty required_chain" in error for error in errors), errors


def test_invalid_claim_kind_causal_chain_without_required_chain_fails():
    errors = fixture_errors("invalid", "claim_kind_causal_chain_without_required_chain")
    assert any("requires non-empty required_chain" in error for error in errors), errors


def test_invalid_contradicted_with_unresolved_high_materiality_anomaly_fails():
    errors = fixture_errors("invalid", "contradicted_with_unresolved_high_materiality_anomaly")
    assert any("residual-path-closure" in error for error in errors), errors


def test_non_tested_path_uses_affected_claims_to_target_negative_closure(tmp_path):
    import yaml

    (tmp_path / "claims.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "claims": [
            {
                "schema_version": "1.0",
                "claim_id": "c001",
                "claim_type": "causal_claim",
                "claim_kind": "causal_claim",
                "statement": "Affected causal claim.",
                "status": "contradicted",
                "source_refs": ["s001"],
                "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
                "uncertainty": {"score": 0.2, "causes": []},
                "interpolation": {"score": 0.1, "assumptions": []},
            },
            {
                "schema_version": "1.0",
                "claim_id": "c002",
                "claim_type": "causal_claim",
                "claim_kind": "causal_claim",
                "statement": "Unaffected causal claim.",
                "status": "contradicted",
                "source_refs": ["s001"],
                "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
                "uncertainty": {"score": 0.2, "causes": []},
                "interpolation": {"score": 0.1, "assumptions": []},
            },
        ],
    }), encoding="utf-8")
    (tmp_path / "investigation-integrity.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "case_ref": "cases/test",
        "investigations": [{
            "investigation_id": "inv001",
            "source_cluster_refs": ["s001"],
            "lead_institution": "Test institution",
            "report_role": "primary_investigation",
            "politically_sensitive": False,
            "financially_sensitive": False,
            "institutional_interest_risk": 0.0,
            "hypothesis_space_declared": ["main"],
            "hypothesis_space_gaps": ["gap"],
            "non_tested_material_paths": [{
                "path_id": "nt001",
                "expected_test": "Test affected path.",
                "justification_present": "partial",
                "justification_quality": 0.4,
                "materiality": 0.8,
                "affected_claims": ["c001"],
            }],
            "adversarial_review": {"present": "unknown", "notes": "Unknown."},
            "integrity_verdict": "insufficient_information",
            "downstream_constraints": ["No overclosure."],
        }],
    }), encoding="utf-8")

    errors = validate_overclosure.validate_case(tmp_path)

    assert any("claim 'c001'" in error and "nt001" in error for error in errors), errors
    assert not any("claim 'c002'" in error and "nt001" in error for error in errors), errors


def test_non_tested_path_closed_residual_path_allows_negative_closure(tmp_path):
    import yaml

    (tmp_path / "claims.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "claims": [{
            "schema_version": "1.0",
            "claim_id": "c001",
            "claim_type": "causal_claim",
            "claim_kind": "causal_claim",
            "statement": "Affected causal claim.",
            "status": "contradicted",
            "source_refs": ["s001"],
            "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
            "uncertainty": {"score": 0.2, "causes": []},
            "interpolation": {"score": 0.1, "assumptions": []},
        }],
    }), encoding="utf-8")
    (tmp_path / "investigation-integrity.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "case_ref": "cases/test",
        "investigations": [{
            "investigation_id": "inv001",
            "source_cluster_refs": ["s001"],
            "lead_institution": "Test institution",
            "report_role": "primary_investigation",
            "politically_sensitive": False,
            "financially_sensitive": False,
            "institutional_interest_risk": 0.0,
            "hypothesis_space_declared": ["main"],
            "hypothesis_space_gaps": ["gap"],
            "non_tested_material_paths": [{
                "path_id": "nt001",
                "expected_test": "Test affected path.",
                "justification_present": "partial",
                "justification_quality": 0.4,
                "materiality": 0.8,
                "affected_claims": ["c001"],
                "residual_path_closure": {
                    "status": "closed",
                    "rationale": "Direct temporal exclusion closes this path.",
                    "evidence_refs": ["e001"],
                },
            }],
            "adversarial_review": {"present": "unknown", "notes": "Unknown."},
            "integrity_verdict": "insufficient_information",
            "downstream_constraints": ["No overclosure."],
        }],
    }), encoding="utf-8")

    (tmp_path / "evidence-pack.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "evidence": [{"evidence_id": "e001", "source_ref": "s001", "claim_refs": ["c001"]}],
    }), encoding="utf-8")

    assert validate_overclosure.validate_case(tmp_path) == []


def test_non_tested_path_unknown_affected_claim_fails(tmp_path):
    import yaml

    (tmp_path / "claims.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "claims": [{
            "schema_version": "1.0",
            "claim_id": "c001",
            "claim_type": "causal_claim",
            "claim_kind": "causal_claim",
            "statement": "Affected causal claim.",
            "status": "contradicted",
            "source_refs": ["s001"],
            "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
            "uncertainty": {"score": 0.2, "causes": []},
            "interpolation": {"score": 0.1, "assumptions": []},
        }],
    }), encoding="utf-8")
    (tmp_path / "investigation-integrity.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "case_ref": "cases/test",
        "investigations": [{
            "investigation_id": "inv001",
            "source_cluster_refs": ["s001"],
            "lead_institution": "Test institution",
            "report_role": "primary_investigation",
            "politically_sensitive": False,
            "financially_sensitive": False,
            "institutional_interest_risk": 0.0,
            "hypothesis_space_declared": ["main"],
            "hypothesis_space_gaps": ["gap"],
            "non_tested_material_paths": [{
                "path_id": "nt001",
                "expected_test": "Test affected path.",
                "justification_present": "partial",
                "justification_quality": 0.4,
                "materiality": 0.8,
                "affected_claims": ["c001-typo"],
            }],
            "adversarial_review": {"present": "unknown", "notes": "Unknown."},
            "integrity_verdict": "insufficient_information",
            "downstream_constraints": ["No overclosure."],
        }],
    }), encoding="utf-8")

    errors = validate_overclosure.validate_case(tmp_path)

    assert any("unknown affected_claim 'c001-typo'" in error for error in errors), errors


def test_non_tested_path_closed_unknown_affected_claim_still_fails(tmp_path):
    import yaml

    (tmp_path / "claims.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "claims": [{
            "schema_version": "1.0",
            "claim_id": "c001",
            "claim_type": "causal_claim",
            "claim_kind": "causal_claim",
            "statement": "Affected causal claim.",
            "status": "contradicted",
            "source_refs": ["s001"],
            "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
            "uncertainty": {"score": 0.2, "causes": []},
            "interpolation": {"score": 0.1, "assumptions": []},
        }],
    }), encoding="utf-8")
    (tmp_path / "evidence-pack.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "evidence": [{"evidence_id": "e001", "source_ref": "s001", "claim_refs": ["c001"]}],
    }), encoding="utf-8")
    (tmp_path / "investigation-integrity.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "case_ref": "cases/test",
        "investigations": [{
            "investigation_id": "inv001",
            "source_cluster_refs": ["s001"],
            "lead_institution": "Test institution",
            "report_role": "primary_investigation",
            "politically_sensitive": False,
            "financially_sensitive": False,
            "institutional_interest_risk": 0.0,
            "hypothesis_space_declared": ["main"],
            "hypothesis_space_gaps": ["gap"],
            "non_tested_material_paths": [{
                "path_id": "nt001",
                "expected_test": "Test affected path.",
                "justification_present": "partial",
                "justification_quality": 0.4,
                "materiality": 0.8,
                "affected_claims": ["c001-typo"],
                "residual_path_closure": {
                    "status": "closed",
                    "rationale": "Direct temporal exclusion closes this path.",
                    "evidence_refs": ["e001"],
                },
            }],
            "adversarial_review": {"present": "unknown", "notes": "Unknown."},
            "integrity_verdict": "insufficient_information",
            "downstream_constraints": ["No overclosure."],
        }],
    }), encoding="utf-8")

    errors = validate_overclosure.validate_case(tmp_path)

    assert any("unknown affected_claim 'c001-typo'" in error for error in errors), errors


def test_closed_residual_path_unknown_evidence_ref_fails(tmp_path):
    import yaml

    (tmp_path / "claims.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "claims": [{
            "schema_version": "1.0",
            "claim_id": "c001",
            "claim_type": "causal_claim",
            "claim_kind": "causal_claim",
            "statement": "Affected causal claim.",
            "status": "contradicted",
            "source_refs": ["s001"],
            "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
            "uncertainty": {"score": 0.2, "causes": []},
            "interpolation": {"score": 0.1, "assumptions": []},
        }],
    }), encoding="utf-8")
    (tmp_path / "evidence-pack.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "evidence": [{"evidence_id": "e001", "source_ref": "s001", "claim_refs": ["c001"]}],
    }), encoding="utf-8")
    (tmp_path / "investigation-integrity.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "case_ref": "cases/test",
        "investigations": [{
            "investigation_id": "inv001",
            "source_cluster_refs": ["s001"],
            "lead_institution": "Test institution",
            "report_role": "primary_investigation",
            "politically_sensitive": False,
            "financially_sensitive": False,
            "institutional_interest_risk": 0.0,
            "hypothesis_space_declared": ["main"],
            "hypothesis_space_gaps": ["gap"],
            "non_tested_material_paths": [{
                "path_id": "nt001",
                "expected_test": "Test affected path.",
                "justification_present": "partial",
                "justification_quality": 0.4,
                "materiality": 0.8,
                "affected_claims": ["c001"],
                "residual_path_closure": {
                    "status": "closed",
                    "rationale": "Direct temporal exclusion closes this path.",
                    "evidence_refs": ["e999"],
                },
            }],
            "adversarial_review": {"present": "unknown", "notes": "Unknown."},
            "integrity_verdict": "insufficient_information",
            "downstream_constraints": ["No overclosure."],
        }],
    }), encoding="utf-8")

    errors = validate_overclosure.validate_case(tmp_path)

    assert any("unknown evidence_ref 'e999'" in error for error in errors), errors


def test_non_tested_path_closed_without_evidence_refs_still_blocks(tmp_path):
    import yaml

    (tmp_path / "claims.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "claims": [{
            "schema_version": "1.0",
            "claim_id": "c001",
            "claim_type": "causal_claim",
            "claim_kind": "causal_claim",
            "statement": "Affected causal claim.",
            "status": "contradicted",
            "source_refs": ["s001"],
            "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
            "uncertainty": {"score": 0.2, "causes": []},
            "interpolation": {"score": 0.1, "assumptions": []},
        }],
    }), encoding="utf-8")
    (tmp_path / "investigation-integrity.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "case_ref": "cases/test",
        "investigations": [{
            "investigation_id": "inv001",
            "source_cluster_refs": ["s001"],
            "lead_institution": "Test institution",
            "report_role": "primary_investigation",
            "politically_sensitive": False,
            "financially_sensitive": False,
            "institutional_interest_risk": 0.0,
            "hypothesis_space_declared": ["main"],
            "hypothesis_space_gaps": ["gap"],
            "non_tested_material_paths": [{
                "path_id": "nt001",
                "expected_test": "Test affected path.",
                "justification_present": "partial",
                "justification_quality": 0.4,
                "materiality": 0.8,
                "affected_claims": ["c001"],
                "residual_path_closure": {"status": "closed", "rationale": "Direct temporal exclusion closes this path."},
            }],
            "adversarial_review": {"present": "unknown", "notes": "Unknown."},
            "integrity_verdict": "insufficient_information",
            "downstream_constraints": ["No overclosure."],
        }],
    }), encoding="utf-8")

    errors = validate_overclosure.validate_case(tmp_path)

    assert any("claim 'c001'" in error and "nt001" in error for error in errors), errors


def test_non_tested_path_closed_without_rationale_still_blocks(tmp_path):
    import yaml

    (tmp_path / "claims.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "claims": [{
            "schema_version": "1.0",
            "claim_id": "c001",
            "claim_type": "causal_claim",
            "claim_kind": "causal_claim",
            "statement": "Affected causal claim.",
            "status": "contradicted",
            "source_refs": ["s001"],
            "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
            "uncertainty": {"score": 0.2, "causes": []},
            "interpolation": {"score": 0.1, "assumptions": []},
        }],
    }), encoding="utf-8")
    (tmp_path / "investigation-integrity.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "case_ref": "cases/test",
        "investigations": [{
            "investigation_id": "inv001",
            "source_cluster_refs": ["s001"],
            "lead_institution": "Test institution",
            "report_role": "primary_investigation",
            "politically_sensitive": False,
            "financially_sensitive": False,
            "institutional_interest_risk": 0.0,
            "hypothesis_space_declared": ["main"],
            "hypothesis_space_gaps": ["gap"],
            "non_tested_material_paths": [{
                "path_id": "nt001",
                "expected_test": "Test affected path.",
                "justification_present": "partial",
                "justification_quality": 0.4,
                "materiality": 0.8,
                "affected_claims": ["c001"],
                "residual_path_closure": {"status": "closed", "rationale": " ", "evidence_refs": ["e001"]},
            }],
            "adversarial_review": {"present": "unknown", "notes": "Unknown."},
            "integrity_verdict": "insufficient_information",
            "downstream_constraints": ["No overclosure."],
        }],
    }), encoding="utf-8")

    errors = validate_overclosure.validate_case(tmp_path)

    assert any("claim 'c001'" in error and "nt001" in error for error in errors), errors


def test_non_tested_path_open_residual_path_blocks_negative_closure(tmp_path):
    import yaml

    (tmp_path / "claims.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "claims": [{
            "schema_version": "1.0",
            "claim_id": "c001",
            "claim_type": "causal_claim",
            "claim_kind": "causal_claim",
            "statement": "Affected causal claim.",
            "status": "contradicted",
            "source_refs": ["s001"],
            "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
            "uncertainty": {"score": 0.2, "causes": []},
            "interpolation": {"score": 0.1, "assumptions": []},
        }],
    }), encoding="utf-8")
    (tmp_path / "investigation-integrity.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "case_ref": "cases/test",
        "investigations": [{
            "investigation_id": "inv001",
            "source_cluster_refs": ["s001"],
            "lead_institution": "Test institution",
            "report_role": "primary_investigation",
            "politically_sensitive": False,
            "financially_sensitive": False,
            "institutional_interest_risk": 0.0,
            "hypothesis_space_declared": ["main"],
            "hypothesis_space_gaps": ["gap"],
            "non_tested_material_paths": [{
                "path_id": "nt001",
                "expected_test": "Test affected path.",
                "justification_present": "partial",
                "justification_quality": 0.4,
                "materiality": 0.8,
                "affected_claims": ["c001"],
                "residual_path_closure": {"status": "open", "rationale": "Still unclosed.", "evidence_refs": ["e001"]},
            }],
            "adversarial_review": {"present": "unknown", "notes": "Unknown."},
            "integrity_verdict": "insufficient_information",
            "downstream_constraints": ["No overclosure."],
        }],
    }), encoding="utf-8")

    errors = validate_overclosure.validate_case(tmp_path)

    assert any("claim 'c001'" in error and "nt001" in error for error in errors), errors


def test_non_tested_path_low_materiality_still_validates_references(tmp_path):
    import yaml

    (tmp_path / "claims.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "claims": [{
            "schema_version": "1.0",
            "claim_id": "c001",
            "claim_type": "causal_claim",
            "claim_kind": "causal_claim",
            "statement": "Affected causal claim.",
            "status": "contradicted",
            "source_refs": ["s001"],
            "direct_incompatibility_basis": "Temporal exclusion rules out the required link.",
            "uncertainty": {"score": 0.2, "causes": []},
            "interpolation": {"score": 0.1, "assumptions": []},
        }],
    }), encoding="utf-8")
    (tmp_path / "evidence-pack.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "evidence": [{"evidence_id": "e001", "source_ref": "s001", "claim_refs": ["c001"]}],
    }), encoding="utf-8")
    (tmp_path / "investigation-integrity.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "case_ref": "cases/test",
        "investigations": [{
            "investigation_id": "inv001",
            "source_cluster_refs": ["s001"],
            "lead_institution": "Test institution",
            "report_role": "primary_investigation",
            "politically_sensitive": False,
            "financially_sensitive": False,
            "institutional_interest_risk": 0.0,
            "hypothesis_space_declared": ["main"],
            "hypothesis_space_gaps": ["gap"],
            "non_tested_material_paths": [{
                "path_id": "nt-low",
                "expected_test": "Low-materiality path still needs valid references.",
                "justification_present": "yes",
                "justification_quality": 1.0,
                "materiality": 0.1,
                "affected_claims": ["c999"],
                "residual_path_closure": {
                    "status": "open",
                    "rationale": "Reference-integrity check only.",
                    "evidence_refs": ["e999"],
                },
            }],
            "adversarial_review": {"present": "unknown", "notes": "Unknown."},
            "integrity_verdict": "insufficient_information",
            "downstream_constraints": ["No overclosure."],
        }],
    }), encoding="utf-8")

    errors = validate_overclosure.validate_case(tmp_path)

    assert any("unknown affected_claim 'c999'" in error for error in errors), errors
    assert any("unknown evidence_ref 'e999'" in error for error in errors), errors
    assert not any("claim 'c001'" in error and "nt-low" in error for error in errors), errors


def test_timestamp_based_direct_incompatibility_needs_no_keyword(tmp_path):
    import shutil
    import yaml

    copied = tmp_path / "real_time_contradiction"
    shutil.copytree(
        FIXTURE_ROOT / "valid" / "causal_temporal_exclusion_contradiction",
        copied,
    )
    relation_path = copied / "evidence-relations.yml"
    doc = yaml.safe_load(relation_path.read_text(encoding="utf-8"))
    doc["relations"][0]["explanation"] = (
        "Event B occurred at 12:00 UTC; the earliest recorded occurrence of A was 13:00 UTC."
    )
    doc["relations"][0]["incompatible_proposition"] = (
        "The causal chain requires A before B, but A started one hour after B."
    )
    relation_path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    assert validate_overclosure.validate_case(copied) == []


def test_quoted_absence_and_explicit_direct_relation_are_not_word_gates(tmp_path):
    import shutil
    import yaml

    copied = tmp_path / "quoted_statement"
    shutil.copytree(
        FIXTURE_ROOT / "valid" / "causal_temporal_exclusion_contradiction",
        copied,
    )
    relation_path = copied / "evidence-relations.yml"
    doc = yaml.safe_load(relation_path.read_text(encoding="utf-8"))
    doc["relations"][0]["explanation"] = (
        'The report states "absence of evidence is not proof"; it also establishes '
        'B at 12:00 and A only at 13:00.'
    )
    doc["relations"][0]["incompatible_proposition"] = (
        "The required sequence depends on A preceding B, but the source timestamps reverse it."
    )
    relation_path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    assert validate_overclosure.validate_case(copied) == []


def test_valid_causal_temporal_exclusion_contradiction_passes():
    assert fixture_errors("valid", "causal_temporal_exclusion_contradiction") == []


def test_valid_co_causation_downgraded_to_weak_passes():
    assert fixture_errors("valid", "co_causation_downgraded_to_weak") == []


def test_valid_reported_source_report_established_passes():
    assert fixture_errors("valid", "reported_source_report_established") == []


def test_cli_reports_invalid_fixture(capsys):
    exit_code = validate_overclosure.main(str(FIXTURE_ROOT / "invalid" / "causal_chain_contradicted_without_required_chain"))
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "FAIL" in captured.out
