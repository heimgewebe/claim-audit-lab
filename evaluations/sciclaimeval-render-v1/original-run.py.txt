#!/usr/bin/env python3
"""Opt-in scientific claim/table evaluation: raw markup vs source-backed rows."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "sciclaimeval-revision-v1" / "run.py"
OLD_MANIFEST = ROOT.parent / "sciclaimeval-revision-v1" / "manifest.json"
RENDERER = ROOT / "render.py"
SHADOW = ROOT.parent / "source-claim-shadow-v1" / "run.py"
MANIFEST = ROOT / "manifest.json"
CACHE = Path("/tmp/claim-audit-sciclaimeval-render-v1")
SEED = "20261123-source-row-v1"
MODES = ("raw", "rendered")
# After excluding PR43 papers there are ZERO additional eligible numeric ML papers.
# Freeze two numeric-bearing domains: four distinct NLP and two distinct PeerJ papers.
QUOTAS = {"nlp": 4, "peerj": 2}
RELEASE = "data/dev_task1_release.json"
# Source is pinned at a fixed commit and a whole-release SHA:
PIN = "55ec80b427d9b4eaff8ed9b537a1ea6cb5d665d7"
RELEASE_SHA = "cbf0db967f285875b7b283ed56f4fed93bf4627f84d8e7f3c39489bc56f289ab"


def prior() -> dict:
    return runpy.run_path(str(OLD))


def rendered() -> dict:
    return runpy.run_path(str(RENDERER))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base_url(path: str) -> str:
    if path != RELEASE and not (
        path.startswith("data/tables/dev/") and
        path.endswith((".tex", ".html")) and
        "/" not in path[len("data/tables/dev/"):]
    ):
        raise ValueError("Only the pinned SciClaimEval release/table paths may be fetched")
    return ("https://huggingface.co/datasets/alabnii/sciclaimeval-shared-task/"
            "resolve/" + PIN + "/" + path)


def fetch(url: str, cap: int) -> bytes:
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with op.open(url, timeout=25) as response:
        raw = response.read(cap + 1)
    if len(raw) > cap:
        raise ValueError("Source exceeds bounded file size")
    return raw


def store(path: str, raw: bytes) -> None:
    target = CACHE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != raw:
            raise ValueError("Cached source conflict; no overwrite allowed")
    else:
        with target.open("xb") as fp:
            fp.write(raw)


def cached(path: str, digest: str) -> bytes:
    raw = (CACHE / path).read_bytes()
    if sha(raw) != digest:
        raise ValueError("Pinned dataset cache SHA-256 mismatch: " + path)
    return raw


def prep() -> None:
    if MANIFEST.exists():
        raise ValueError("Preregistered manifest already exists; no re-selection")
    old = prior()
    r = rendered()
    release_raw = fetch(base_url(RELEASE), 1_200_000)
    if sha(release_raw) != RELEASE_SHA:
        raise ValueError("Official SciClaimEval source revision SHA-256 mismatch")
    store(RELEASE, release_raw)
    release = json.loads(release_raw)
    if not isinstance(release, list) or len(release) < 700:
        raise ValueError("Official SciClaimEval source dataset malformed")
    tree_url = ("https://huggingface.co/api/datasets/alabnii/sciclaimeval-shared-task/"
                "tree/" + PIN + "/data/tables/dev?expand=false")
    listing = fetch(tree_url, 300_000)
    sizes = {x["path"]: x["size"] for x in json.loads(listing)
             if x.get("type") == "file"}
    old_manifest = json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))
    excluded = {c["paper_id"] for c in old_manifest["samples"]}
    used = set(excluded)
    pools = old["pair_pool"](release, sizes)
    samples = []
    for domain, quota in QUOTAS.items():
        choices = sorted(
            pools[domain],
            key=lambda pair: sha(
                (SEED + "/" + domain + "/" + pair[0]["paper_id"] +
                 "/" + pair[0]["claim_id_pair"]).encode()
            ),
        )
        selected = 0
        for members in choices:
            if members[0]["paper_id"] in used:
                continue
            by_label = {row["label"]: row for row in members}
            bodies, views = {}, {}
            renderable = True
            for label in old["LABELS"]:
                file = "data/" + by_label[label]["evi_path_original"]
                raw = fetch(base_url(file), 6200)
                if len(raw) != sizes[file]:
                    raise ValueError("Pinned source file size changed unexpectedly")
                try:
                    view = r["render_table"](raw.decode("utf-8"))
                except (ValueError, UnicodeError):
                    # Structural ineligibility, determined before any inference;
                    # never replace or silently re-label a gold sample.
                    renderable = False
                    break
                bodies[label] = raw
                views[label] = view
            if not renderable:
                continue
            if (bodies["Supported"] == bodies["Refuted"]
                or views["Supported"]["rendered_source"] ==
                   views["Refuted"]["rendered_source"]):
                continue  # no experimentally visible evidence substitution
            for label in old["LABELS"]:
                store("data/" + by_label[label]["evi_path_original"], bodies[label])
            item = {
                "pair_id": str(members[0]["claim_id_pair"]),
                "paper_id": str(members[0]["paper_id"]),
                "domain": domain, "split": ("development" if selected < quota // 2
                                              else "holdout"),
                "claim_sha256": sha(members[0]["claim"].encode()),
                "caption_sha256": sha(members[0]["caption"].encode()),
                "license_name": members[0]["license_name"],
                "license_url": members[0]["license_url"],
                "sources": {
                    label: {
                        "claim_id": by_label[label]["claim_id"],
                        "path": "data/" + by_label[label]["evi_path_original"],
                        "sha256": sha(bodies[label]),
                        "bytes": len(bodies[label]),
                        "display_sha256": views[label]["rendered_sha256"],
                        "row_count": len(views[label]["rows"]),
                    } for label in old["LABELS"]
                },
            }
            used.add(item["paper_id"])
            samples.append(item)
            selected += 1
            if selected == quota:
                break
        if selected != quota:
            raise ValueError("Insufficient source-disjoint renderable cases for " + domain)
    samples.sort(key=lambda c: (c["split"], c["domain"]))
    manifest = {
        "schema_version": "claim-audit-lab.sciclaimeval-render-manifest-v1",
        "dataset_revision": PIN, "release_sha256": RELEASE_SHA,
        "selection_seed": SEED, "old_manifest_sha256": sha(OLD_MANIFEST.read_bytes()),
        "catalog_listing_sha256": sha(listing),
        "selection": (
            "SciClaimEval prior-pilot pair_pool filter, exclude all six prior "
            "papers; SHA-sort by 20261123-source-row-v1/domain/paper/pair, "
            "4 new distinct-paper NLP pairs and 2 new distinct-paper PeerJ pairs; "
            "source versions must differ in raw bytes and rendered rows; "
            "first 2 NLP and 1 PeerJ development, next 2 NLP and 1 PeerJ holdout. "
            "All prior PR43 paper IDs are excluded; ML quota zero because all "
            "remaining eligible numeric ML paper identities belonged to PR43"
        ),
        "source_relative_gold_only": True,
        "modified_sources_are_not_independent_world_evidence": True,
        "samples": samples,
    }
    with MANIFEST.open("x", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2, ensure_ascii=False)
        fp.write("\n")
    print(json.dumps({
        "manifest_sha256": sha(MANIFEST.read_bytes()),
        "samples": [(s["split"], s["domain"], s["pair_id"], s["paper_id"])
                    for s in samples],
    }), flush=True)


def locked():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if (manifest["schema_version"] != "claim-audit-lab.sciclaimeval-render-manifest-v1"
        or manifest["dataset_revision"] != PIN or manifest["release_sha256"] != RELEASE_SHA
        or manifest["selection_seed"] != SEED
        or manifest["old_manifest_sha256"] != sha(OLD_MANIFEST.read_bytes())):
        raise ValueError("Preregistered experiment manifest identity invalid")
    release = json.loads(cached(RELEASE, RELEASE_SHA))
    old = prior()
    r = rendered()
    old_manifest = json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))
    known_old_papers = {x["paper_id"] for x in old_manifest["samples"]}
    index = {x["claim_id"]: x for x in release}
    ids, papers = set(), set()
    quota = Counter()
    for sample in manifest["samples"]:
        if (sample["pair_id"] in ids or sample["paper_id"] in papers
            or sample["paper_id"] in known_old_papers):
            raise ValueError("Data leakage across selected source papers")
        ids.add(sample["pair_id"])
        papers.add(sample["paper_id"])
        quota[(sample["split"], sample["domain"])] += 1
        for label in old["LABELS"]:
            part = sample["sources"][label]
            item = index[part["claim_id"]]
            if (
                item["claim_id_pair"] != sample["pair_id"] or
                item["paper_id"] != sample["paper_id"] or
                item["domain"] != sample["domain"] or
                item["label"] != label or
                item["license_name"] != sample["license_name"] or
                item["license_url"] != sample["license_url"] or
                sha(item["claim"].encode()) != sample["claim_sha256"] or
                sha(item["caption"].encode()) != sample["caption_sha256"] or
                "data/" + item["evi_path_original"] != part["path"]
            ):
                raise ValueError("Published claim/source/label binding changed")
            body = cached(part["path"], part["sha256"])
            if (len(body) != part["bytes"] or
                r["render_table"](body.decode("utf-8"))["rendered_sha256"] !=
                    part["display_sha256"]):
                raise ValueError("Original or displayed evidence hash invalid")
    if (len(manifest["samples"]) != 6 or
        any(quota[(s, d)] != count // 2
            for d, count in QUOTAS.items() for s in old["SPLITS"])):
        raise ValueError("Frozen paper-disjoint development/holdout quota failed")
    return manifest, index


def hydrate() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw = fetch(base_url(RELEASE), 1_200_000)
    if sha(raw) != RELEASE_SHA:
        raise ValueError("Official dataset release source SHA changed")
    store(RELEASE, raw)
    for sample in manifest["samples"]:
        for part in sample["sources"].values():
            body = fetch(base_url(part["path"]), 6200)
            if sha(body) != part["sha256"]:
                raise ValueError("Source bytes changed from original commit")
            store(part["path"], body)
    locked()
    print(json.dumps({"cache_faithful": True,
                      "manifest_sha256": sha(MANIFEST.read_bytes())}))


def proof_for(result: dict, condition: str, raw: str, view: dict | None) -> dict:
    if result.get("status") != "valid":
        return result
    span = result["evidence_span"]
    if condition == "rendered":
        try:
            result["provenance"] = rendered()["prove_quote"](raw, view, span)
        except ValueError as exc:
            result["status"] = "error"
            result["error"] = "rendered_evidence_unbound"
            result["provenance_error"] = str(exc)
    else:
        if span and span not in raw:
            raise ValueError("Existing raw-source quote parser returned an invalid proof")
        result["provenance"] = {
            "kind": "raw-verbatim", "source_sha256": sha(raw.encode()),
            "source_quote_byte_verbatim": True,
        } if span else None
    return result


def sample_steps(shadow: dict, old: dict, model: str,
                 mode: str, sample: dict, index: dict) -> dict:
    refs = {}
    raw = {}
    for label, part in sample["sources"].items():
        raw[label] = cached(part["path"], part["sha256"]).decode("utf-8")
        refs[label] = rendered()["render_table"](raw[label]) if mode == "rendered" else None
    texts = {
        label: refs[label]["rendered_source"] if mode == "rendered" else raw[label]
        for label in old["LABELS"]
    }
    record = index[sample["sources"]["Supported"]["claim_id"]]
    claim, caption = record["claim"], record["caption"]
    steps = {}
    order = [
        ("initial_supported", "Supported", None),
        ("initial_refuted", "Refuted", None),
        ("revision_to_refuted", "Refuted", "Supported"),
        ("revision_to_supported", "Supported", "Refuted"),
        ("unchanged_control", "Supported", "Supported"),
    ]
    for tag, target, previous in order:
        if previous is None:
            messages = old["make_messages"](shadow["INSTRUCTION"],
                                             claim, caption, texts[target])
        else:
            first_tag = "initial_supported" if previous == "Supported" else "initial_refuted"
            messages = old["make_messages"](shadow["INSTRUCTION"],
                                             claim, caption, texts[previous])
            followup = (
                old["unchanged_prompt"](claim) if tag == "unchanged_control"
                else old["updated_prompt"](claim, caption, texts[target])
            )
            messages.extend([
                {"role": "assistant", "content": steps[first_tag].get("raw_response") or ""},
                {"role": "user", "content": followup},
            ])
        original = old["call"](shadow, model, messages, texts[target])
        original = proof_for(original, mode, raw[target], refs[target])
        row = old["classify_result"](tag, original, target)
        row["provenance"] = original.get("provenance")
        row["provenance_error"] = original.get("provenance_error")
        row["source_sha256"] = sample["sources"][target]["sha256"]
        row["source_display_sha256"] = (
            refs[target]["rendered_sha256"] if refs[target]
            else sample["sources"][target]["sha256"]
        )
        steps[tag] = row
        print(json.dumps({"pair": sample["pair_id"], "mode": mode, "stage": tag,
                          "status": row["status"], "label": row.get("label"),
                          "error": row.get("error")}), flush=True)
        if row["status"] != "valid" and row["error"] not in (
                "invalid_output", "rendered_evidence_unbound"):
            break
    return steps


def measurements(rows: list[dict]) -> dict:
    tally = Counter({"invalid_evidence_quotes": 0, "provider_or_context_failure": 0,
                     "control_label_changed": 0, "anchored_wrong": 0,
                     "valid_expert_revision": 0, "valid_expert_independent": 0})
    seconds = 0.0
    for sample in rows:
        steps = sample["steps"]
        for tag, row in steps.items():
            tally[tag + "_attempted"] += 1
            good = row["status"] == "valid"
            expected = "supported" if row["expected_expert_relation"] == "Supported" else "contradicted"
            tally[tag + "_valid"] += good
            tally[tag + "_expert_match"] += good and row["label"] == expected
            if tag.startswith("revision_"):
                tally["valid_expert_revision"] += good and row["label"] == expected
                tally["missed_contradictions"] += good and expected == "contradicted" and row["label"] != expected
                tally["false_contradictions"] += good and expected == "supported" and row["label"] == "contradicted"
            if tag.startswith("initial_"):
                tally["valid_expert_independent"] += good and row["label"] == expected
            tally["invalid_evidence_quotes"] += row.get("error") in (
                "invalid_output", "rendered_evidence_unbound")
            tally["provider_or_context_failure"] += (
                not good and row.get("error") not in
                ("invalid_output", "rendered_evidence_unbound")
            )
            seconds += row.get("duration_seconds") or 0
        if "unchanged_control" in steps and "initial_supported" in steps:
            control = steps["unchanged_control"]
            early = steps["initial_supported"]
            if early["status"] == control["status"] == "valid":
                tally["controls_with_valid_pair"] += 1
                tally["control_label_changed"] += early["label"] != control["label"]
        for initial, final in (("initial_supported","revision_to_refuted"),
                               ("initial_refuted","revision_to_supported")):
            if initial in steps and final in steps:
                a,b = steps[initial],steps[final]
                if a["status"] == b["status"] == "valid":
                    tally["valid_revision_pairs"] += 1
                    tally["anchored_wrong"] += a["label"] == b["label"] and (
                        b["label"] != ("supported" if final=="revision_to_supported"
                                     else "contradicted"))
    tally["total_calls"] = sum(len(r["steps"]) for r in rows)
    tally["duration_seconds_total"] = round(seconds, 2)
    return dict(tally)


def trial(split: str, model: str, mode: str) -> None:
    result_path = ROOT / ("run-" + split + "-" + model.replace(":","-") +
                          "-" + mode + ".json")
    if result_path.exists():
        raise ValueError("Immutable model output already exists: no overwrite/retry")
    manifest, index = locked()
    old = prior()
    shadow = runpy.run_path(str(SHADOW))
    preflight = old["local_preflight"](shadow, model)
    samples = [s for s in manifest["samples"] if s["split"] == split]
    rows = []
    for sample in samples:
        steps = sample_steps(shadow, old, model, mode, sample, index)
        rows.append({"pair_id": sample["pair_id"],
                     "paper_id": sample["paper_id"],
                     "domain": sample["domain"], "steps": steps})
        if any(
            r["status"] != "valid" and r.get("error") not in
            ("invalid_output","rendered_evidence_unbound")
            for r in steps.values()
        ):
            break
    result = {
        "schema_version": "claim-audit-lab.sciclaimeval-render-results-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha(MANIFEST.read_bytes()),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "renderer_sha256": sha(RENDERER.read_bytes()),
        "original_prior_runner_sha256": sha(OLD.read_bytes()),
        "original_shadow_sha256": sha(SHADOW.read_bytes()),
        "instruction_sha256": sha(shadow["INSTRUCTION"].encode()),
        "source_gold_is_published_not_world_truth": True,
        "condition": mode, "split": split, "model": model,
        "model_digest": preflight["model_digest"],
        "metrics": measurements(rows), "rows": rows,
    }
    with result_path.open("x", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)
        fp.write("\n")
    print("SUMMARY", json.dumps({"path": str(result_path),
                                  "metrics": result["metrics"]}), flush=True)
    if (len(rows) != len(samples) or
        result["metrics"]["provider_or_context_failure"]):
        raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("prepare")
    actions.add_parser("hydrate-cache")
    t = actions.add_parser("trial")
    t.add_argument("--split", choices=("development","holdout"), required=True)
    t.add_argument("--model", choices=("qwen3:14b","gemma4:12b"), required=True)
    t.add_argument("--condition", choices=MODES, required=True)
    args = parser.parse_args()
    if args.action == "prepare":
        prep()
    elif args.action == "hydrate-cache":
        hydrate()
    else:
        trial(args.split, args.model, args.condition)


if __name__ == "__main__":
    main()