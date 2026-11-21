#!/usr/bin/env python3
"""Derive bias signals from case artifacts.

Bias signals are generated, not confessed. Each signal is an explanation-bearing
observation about a case artifact pattern; it is not proof of distortion. See
docs/bias-signal-discipline.md.

Usage:
    python scripts/generate_bias_signals.py cases
    python scripts/generate_bias_signals.py cases --write
    python scripts/generate_bias_signals.py cases --check
    python scripts/generate_bias_signals.py cases --case cases/critical-inquiry/example
    python scripts/generate_bias_signals.py cases --format json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

import yaml

from case_compat import find_cases_root
from jsonschema_compat import jsonschema
import validate_reported_claim_world_effect as provenance

GENERATED_BY = "scripts/generate_bias_signals.py"
GENERATED_SUBDIR = "_generated"
GENERATED_FILENAME = "bias-signals.yml"
SIGNALS_SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "schemas" / "bias-signals.v1.schema.json"

# Strong-effect relation types, kept in sync with STRONG_EFFECT_RELATIONS in
# validate_reported_claim_world_effect.py. The bare forms "supports",
# "contradicts", and "contradicts_indirectly" are legacy aliases not present in
# evidence-relation.v1.schema.json's enum; they are recognised here so a relation
# cannot dodge the gate by relabelling to a non-canonical type.
DIRECTIONAL_RELATION_TYPES = {
    "supports",  # legacy alias (not in schema enum)
    "supports_directly",
    "supports_indirectly",
    "weakens",
    "undercuts",
    "contradicts",  # legacy alias (not in schema enum)
    "contradicts_directly",
    "contradicts_conditionally",
    "contradicts_indirectly",  # legacy alias (not in schema enum)
    "alternative_explanation",
    "method_challenge",
}
THRESHOLD_GATES = (0.60, 0.75)
THRESHOLD_WINDOW = 0.03

PENDING_REDTEAM_VERDICTS = {"pending", "pending_independent_review"}
FINAL_LIFECYCLE_STATUSES = {"assessed", "final_under_uncertainty"}

def _load_yaml(path: pathlib.Path) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def relative_case_ref(case_dir: pathlib.Path) -> str:
    root = find_cases_root(case_dir)
    if root is not None:
        rel = case_dir.relative_to(root).as_posix()
        return f"cases/{rel}" if rel != "." else "cases"
    return case_dir.as_posix()


def _signal_id(case_ref: str, signal_type: str, affected_refs: list[str], observation: str) -> str:
    payload = "|".join(
        [case_ref, signal_type, ",".join(sorted(affected_refs)), observation]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"bs_{digest[:12]}"


class CaseContext:
    def __init__(self, case_dir: pathlib.Path):
        self.case_dir = case_dir
        self.case_ref = relative_case_ref(case_dir)
        claims_doc = _load_yaml(case_dir / "claims.yml")
        self.claims = _as_list(claims_doc, "claims")
        relations_doc = _load_yaml(case_dir / "evidence-relations.yml")
        self.relations = _as_list(relations_doc, "relations")
        sources_doc = _load_yaml(case_dir / "sources.yml")
        self.sources = _as_list(sources_doc, "sources")
        swa_doc = _load_yaml(case_dir / "source-weight-audit.yml")
        self.source_audit = _as_list(swa_doc, "records")
        self.redteam = _load_yaml(case_dir / "redteam.yml")
        self.lifecycle = _load_yaml(case_dir / "lifecycle.yml")
        self.assessment_text = _read_text(case_dir / "assessment.md")
        argument_doc = _load_yaml(case_dir / "argument-provenance.yml")
        self.argument_provenance = argument_doc if isinstance(argument_doc, dict) else {}
        inference_doc = _load_yaml(case_dir / "inference-ledger.yml")
        self.inference_ledger = inference_doc if isinstance(inference_doc, dict) else {}
        hypotheses_doc = _load_yaml(case_dir / "hypotheses.yml")
        self.hypotheses = _as_list(hypotheses_doc, "hypotheses")
        evidence_pack_doc = _load_yaml(case_dir / "evidence-pack.yml")
        self.evidence_pack = _as_list(evidence_pack_doc, "evidence")


def _as_list(doc: Any, key: str) -> list[dict]:
    if isinstance(doc, dict) and isinstance(doc.get(key), list):
        return [item for item in doc[key] if isinstance(item, dict)]
    return []


def _read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _get_evidence_refs_from_relation(relation: dict) -> list[str]:
    """Collect all evidence refs from a relation (singular and plural fields)."""
    refs: list[str] = []
    singular = relation.get("evidence_ref")
    if isinstance(singular, str) and singular:
        refs.append(singular)
    plural = relation.get("evidence_refs") or []
    if isinstance(plural, list):
        refs.extend(r for r in plural if isinstance(r, str) and r)
    return list(dict.fromkeys(refs))


def _load_signals_schema() -> dict | None:
    try:
        with open(SIGNALS_SCHEMA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _schema_errors_for_document(document: dict, schema: dict) -> list[str]:
    validator = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    return [
        f"Schema error at {list(e.absolute_path)}: {e.message}"
        for e in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    ]


def detect_relation_threshold_proximity(ctx: CaseContext) -> list[dict]:
    signals: list[dict] = []
    for relation in ctx.relations:
        rtype = relation.get("relation_type", "")
        strength = relation.get("strength")
        relation_id = relation.get("relation_id")
        claim_ref = relation.get("claim_ref")
        if rtype not in DIRECTIONAL_RELATION_TYPES:
            continue
        if not isinstance(strength, (int, float)) or isinstance(strength, bool):
            continue
        near = next(
            (gate for gate in THRESHOLD_GATES if abs(strength - gate) <= THRESHOLD_WINDOW + 1e-9),
            None,
        )
        if near is None or not relation_id:
            continue
        observation = (
            f"relation {relation_id} ({rtype}) strength {strength} sits within "
            f"±{THRESHOLD_WINDOW} of gate {near}; a small numeric move crosses a verdict gate."
        )
        affected = [claim_ref] if isinstance(claim_ref, str) and claim_ref else []
        signals.append(
            _build(
                ctx,
                signal_type="relation_threshold_proximity",
                severity=0.50,
                affected_claims=affected,
                detected_from=[f"evidence-relations.yml#{relation_id}"],
                observation=observation,
            )
        )
    return signals


def _composite_trust(source_weight: dict) -> float | None:
    positive = ("primary_proximity", "method_transparency", "reproducibility",
                "source_cluster_independence", "historical_track_record")
    risk = ("institutional_interest_risk", "update_latency_risk")
    values: list[float] = []
    for key in positive:
        v = source_weight.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            values.append(float(v))
    for key in risk:
        v = source_weight.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            values.append(1.0 - float(v))
    if len(values) < 5:
        return None
    return sum(values) / len(values)


def detect_source_weight_asymmetry(ctx: CaseContext) -> list[dict]:
    signals: list[dict] = []
    composites: dict[str, float] = {}
    for source in ctx.sources:
        sid = source.get("source_id")
        weight = source.get("source_weight")
        if not isinstance(sid, str) or not isinstance(weight, dict):
            continue
        comp = _composite_trust(weight)
        if comp is not None:
            composites[sid] = comp
    if len(composites) < 2:
        return signals
    values = list(composites.values())
    spread = max(values) - min(values)
    if spread < 0.4:
        return signals
    mean = sum(values) / len(values)

    audit_notes: dict[str, str] = {}
    for record in ctx.source_audit:
        ref = record.get("source_ref")
        if isinstance(ref, str):
            audit_notes[ref] = str(record.get("notes", "") or "")

    claims_by_source: dict[str, list[str]] = {}
    for claim in ctx.claims:
        cid = claim.get("claim_id")
        if not isinstance(cid, str):
            continue
        for ref in claim.get("source_refs", []) or []:
            if isinstance(ref, str):
                claims_by_source.setdefault(ref, []).append(cid)

    for sid, comp in sorted(composites.items()):
        if abs(comp - mean) < 0.25:
            continue
        justified = len(audit_notes.get(sid, "").strip()) >= 40
        if justified:
            continue
        direction = "above" if comp > mean else "below"
        observation = (
            f"source {sid} composite trust {round(comp, 3)} is far {direction} the case "
            f"mean {round(mean, 3)} (spread {round(spread, 3)}) without a justification in "
            f"source-weight-audit.yml."
        )
        signals.append(
            _build(
                ctx,
                signal_type="source_weight_asymmetry",
                severity=0.60,
                affected_claims=sorted(set(claims_by_source.get(sid, []))),
                detected_from=[f"sources.yml#{sid}", "source-weight-audit.yml"],
                observation=observation,
            )
        )
    return signals


def _has_report_to_world_provenance(
    ctx: CaseContext,
    reported_claim_id: str,
    world_claim_id: str,
    *,
    relation_type: str = "supports_indirectly",
    strength: float = 0.6,
    origin_source_refs: set[str] | None = None,
) -> bool:
    """Reuse the canonical evidence validator's per-claim provenance checks."""
    token = (reported_claim_id, None)
    sources = provenance.get_sources_by_id({"sources": ctx.sources})
    origins = set(origin_source_refs or ())
    return provenance.has_inference_provenance(
        ctx.inference_ledger, world_claim_id, token, relation_type,
        strength, sources, origins,
    ) or provenance.has_argument_provenance(
        ctx.argument_provenance, world_claim_id, token, relation_type,
        strength, sources, origins,
    )


def detect_reported_claim_world_pressure(ctx: CaseContext) -> list[dict]:
    signals: list[dict] = []
    claims_by_id = {
        claim["claim_id"]: claim for claim in ctx.claims
        if isinstance(claim.get("claim_id"), str)
    }
    reported_claim_ids = {
        cid for cid, claim in claims_by_id.items()
        if claim.get("claim_kind") == "reported_claim"
        or claim.get("burden_profile") == "source_report"
    }

    covered_pairs: set[tuple[str, str]] = set()

    # For actual strong report-derived evidence relations, rely on the
    # same source- and effect-aware matching contract as the canonical
    # validate_reported_claim_world_effect validator. Filename existence
    # alone, unrelated arguments and weak relations cannot release a signal.
    evidence_by_id = {
        evidence["evidence_id"]: evidence for evidence in ctx.evidence_pack
        if isinstance(evidence.get("evidence_id"), str)
    }
    for relation in ctx.relations:
        rtype = relation.get("relation_type")
        target = relation.get("claim_ref")
        strength = relation.get("strength")
        if (
            rtype not in provenance.STRONG_EFFECT_RELATIONS
            or not isinstance(target, str)
            or not provenance.is_world_claim(claims_by_id, target)
            or isinstance(strength, bool)
            or not isinstance(strength, (int, float))
            or strength < provenance.STRENGTH_THRESHOLD
        ):
            continue
        evidence_ids = _get_evidence_refs_from_relation(relation)
        involved: set[str] = set()
        origin_sources: set[str] = set()
        for eid in evidence_ids:
            evidence = evidence_by_id.get(eid)
            if evidence is None:
                continue
            linked = {
                ref for ref in (evidence.get("claim_refs") or [])
                if isinstance(ref, str) and ref in reported_claim_ids
            }
            if linked:
                involved.update(linked)
                origin_sources.update(provenance.evidence_origin_sources(evidence))
        if not involved:
            continue
        covered_pairs.update((reported_id, target) for reported_id in involved)
        missing = [
            reported_id for reported_id in sorted(involved)
            if not _has_report_to_world_provenance(
                ctx, reported_id, target, relation_type=rtype,
                strength=float(strength), origin_source_refs=origin_sources,
            )
        ]
        if not missing:
            continue
        relation_id = relation.get("relation_id", "?")
        signals.append(_build(
            ctx,
            signal_type="reported_claim_world_pressure",
            severity=0.78,
            affected_claims=sorted({target, *missing}),
            detected_from=[
                f"evidence-relations.yml#{relation_id}",
                "argument-provenance.yml / inference-ledger.yml",
            ],
            observation=(
                f"relation {relation_id} uses report-derived evidence "
                f"{sorted(evidence_ids)} toward world claim {target} with "
                f"effect {rtype} at strength {strength}, but no matching "
                f"provenance for reported claim(s) {missing}."
            ),
        ))
    # Explicit report-to-world links are an early-warning signal even before
    # a strong evidence relation is present. Merely mentioning a report in
    # assessment prose is not evidence of such a world argument.
    for reported_id in sorted(reported_claim_ids):
        claim = claims_by_id[reported_id]
        world_refs = [
            ref for ref in (claim.get("world_claim_refs") or [])
            if isinstance(ref, str)
        ]
        missing = [
            ref for ref in world_refs
            if (reported_id, ref) not in covered_pairs
            and not _has_report_to_world_provenance(ctx, reported_id, ref)
        ]
        if not missing:
            continue
        signals.append(_build(
            ctx,
            signal_type="reported_claim_world_pressure",
            severity=0.78,
            affected_claims=sorted({reported_id, *missing}),
            detected_from=[
                f"claims.yml#{reported_id}",
                "argument-provenance.yml / inference-ledger.yml",
            ],
            observation=(
                f"reported_claim {reported_id} references world claim(s) "
                f"{sorted(set(missing))} without a matching premise/target "
                "and reported_to_world check in either provenance artifact."
            ),
        ))

    return signals


def detect_redteam_pending_with_final_language(ctx: CaseContext) -> list[dict]:
    if not isinstance(ctx.redteam, dict):
        return []
    verdict = ""
    if isinstance(ctx.redteam.get("verdict"), dict):
        verdict = str(ctx.redteam["verdict"].get("status", ""))
    if verdict not in PENDING_REDTEAM_VERDICTS:
        return []
    lifecycle_status = ""
    if isinstance(ctx.lifecycle, dict):
        lifecycle_status = str(ctx.lifecycle.get("status", ""))
    if lifecycle_status not in FINAL_LIFECYCLE_STATUSES:
        return []
    observation = (
        f"red-team verdict is '{verdict}' while lifecycle status "
        f"is '{lifecycle_status}'."
    )
    return [
        _build(
            ctx,
            signal_type="redteam_pending_with_final_language",
            severity=0.85,
            affected_claims=[],
            detected_from=["redteam.yml", "lifecycle.yml"],
            observation=observation,
        )
    ]


DETECTORS = (
    detect_relation_threshold_proximity,
    detect_source_weight_asymmetry,
    detect_reported_claim_world_pressure,
    detect_redteam_pending_with_final_language,
)


def _build(
    ctx: CaseContext,
    *,
    signal_type: str,
    severity: float,
    affected_claims: list[str],
    detected_from: list[str],
    observation: str,
) -> dict:
    affected_refs = [*affected_claims, *detected_from]
    signal_id = _signal_id(ctx.case_ref, signal_type, affected_refs, observation)
    return {
        "signal_id": signal_id,
        "signal_type": signal_type,
        "severity": severity,
        "affected_claims": affected_claims,
        "detected_from": detected_from,
        "observation": observation,
        "required_response": True,
    }


def generate_for_case(case_dir: pathlib.Path) -> list[dict]:
    ctx = CaseContext(case_dir)
    signals: list[dict] = []
    for detector in DETECTORS:
        signals.extend(detector(ctx))
    signals.sort(key=lambda s: (s["signal_type"], s["signal_id"]))
    return signals


def build_document(case_ref: str, signals: list[dict]) -> dict:
    return {
        "schema_version": "1.0",
        "case_ref": case_ref,
        "generated_by": GENERATED_BY,
        "signals": signals,
    }


def discover_case_dirs(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(
        {
            marker.parent
            for marker in root.rglob("claims.yml")
            if "_template" not in marker.parts and GENERATED_SUBDIR not in marker.parts
        }
    )


def _generated_path(case_dir: pathlib.Path) -> pathlib.Path:
    return case_dir / GENERATED_SUBDIR / GENERATED_FILENAME


def _write_document(case_dir: pathlib.Path, document: dict) -> pathlib.Path:
    out_path = _generated_path(case_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(document, f, sort_keys=False, allow_unicode=True)
    return out_path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Derive bias signals from case artifacts.")
    parser.add_argument("cases_dir")
    parser.add_argument("--write", action="store_true", help="write _generated/bias-signals.yml per case")
    parser.add_argument("--check", action="store_true", help="fail if a committed generated file is stale")
    parser.add_argument("--case", help="limit to a single case directory")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.cases_dir)
    if args.case:
        case_dirs = [pathlib.Path(args.case)]
    else:
        if not root.is_dir():
            print(f"ERROR: {root} is not a directory", file=sys.stderr)
            return 1
        case_dirs = discover_case_dirs(root)

    if not case_dirs:
        print(f"No case directories found under {root}")
        return 0

    signals_schema = _load_signals_schema()

    json_payload: list[dict] = []
    drift = 0
    for case_dir in case_dirs:
        signals = generate_for_case(case_dir)
        document = build_document(relative_case_ref(case_dir), signals)

        if signals_schema:
            schema_errs = _schema_errors_for_document(document, signals_schema)
            if schema_errs:
                for err in schema_errs:
                    print(f"SCHEMA ERROR {case_dir}: {err}", file=sys.stderr)
                return 1

        if args.check:
            committed = _generated_path(case_dir)
            if committed.exists():
                existing = _load_yaml(committed)
                existing_signals = existing.get("signals") if isinstance(existing, dict) else None
                if existing_signals != signals:
                    print(f"DRIFT {committed}: committed signals are stale; re-run with --write.")
                    drift += 1
                else:
                    print(f"OK    {committed}")
            else:
                print(f"OK    {case_dir} (no committed signals; generated in memory)")
            continue

        if args.write:
            out_path = _write_document(case_dir, document)
            print(f"WROTE {out_path} ({len(signals)} signal(s))")
            continue

        if args.format == "json":
            json_payload.append(document)
        else:
            print(f"{document['case_ref']}: {len(signals)} signal(s)")
            for signal in signals:
                print(
                    f"  [{signal['signal_type']}] {signal['signal_id']} "
                    f"severity={signal['severity']} affects={signal['affected_claims']}"
                )
                print(f"    {signal['observation']}")

    if args.check:
        if drift:
            print(f"\n{drift} stale generated file(s).")
            return 1
        print("\nAll committed bias-signal files current.")
        return 0

    if args.format == "json" and not args.write:
        print(json.dumps(json_payload, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
