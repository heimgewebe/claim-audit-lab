"""Absence claims are typed and evidenced, never inferred from word lists."""

import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_claims


def _claim(**updates):
    with (ROOT / "tests" / "fixtures" / "valid_claim.yml").open(encoding="utf-8") as f:
        claim = yaml.safe_load(f)
    claim.update(updates)
    return claim


def _errors(claim):
    with (ROOT / "schemas" / "claim.v1.schema.json").open(encoding="utf-8") as f:
        schema = json.load(f)
    return validate_claims.validate_claim(claim, schema)


def test_quoted_or_negated_absence_language_is_not_a_claim_type():
    claim = _claim(
        statement="Die Quelle sagt 'keine Evidenz', aber dieses Zitat ist kein Beweis.",
        notes="Keine Evidenz ist kein Beweis für die Falschheit der These.",
    )
    assert _errors(claim) == []


def test_absence_claim_needs_explicit_scope_even_when_statement_mentions_dataset():
    claim = _claim(
        claim_kind="absence_claim",
        statement="Within dataset Y there is no record matching X.",
    )
    assert any("bounded scope" in error for error in _errors(claim))


def test_absence_claim_requires_upgrade_check_independent_of_wording():
    claim = _claim(
        claim_kind="absence_claim",
        absence_scope="Archive A, records 1939–1945",
        forbidden_upgrades=[],
        statement="Results were negative within this archive.",
    )
    assert any("absence_of_evidence_to_falsehood" in error for error in _errors(claim))


def test_strong_absence_claim_uses_actual_evidence_refs_not_magic_exhaustivity_words():
    claim = _claim(
        claim_kind="absence_claim",
        absence_scope="Archive A, records 1939–1945",
        statement="No matching entry was found in the named records.",
        status="established",
        source_refs=["s001"],
        evidence_refs=["e001"],
    )
    assert _errors(claim) == []


def test_strong_absence_claim_without_evidence_fails_even_if_scope_says_exhaustive():
    claim = _claim(
        claim_kind="absence_claim",
        absence_scope="Exhaustive search, fully verified, every document checked",
        status="established",
        source_refs=[],
        evidence_refs=[],
    )
    errors = _errors(claim)
    assert any("source_refs" in error for error in errors)
    assert any("evidence_refs" in error for error in errors)
