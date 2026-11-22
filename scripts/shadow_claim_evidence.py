#!/usr/bin/env python3
"""Opt-in local source excerpt vs claim review; never a truth certificate or gate."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SHADOW = ROOT / "evaluations" / "source-claim-shadow-v1" / "run.py"
MAX_EXCERPT_CHARS = 12000
SCHEMA = "claim-audit-lab.single-source-shadow.v1"


def get_shadow_module():
    spec = importlib.util.spec_from_file_location(
        "claim_audit_single_source_shadow", SHADOW
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Existing source-claim shadow evaluator missing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


shadow = get_shadow_module()


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evaluate(claim: str, excerpt: str, model: str) -> dict:
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("A nonempty claim is required")
    if not isinstance(excerpt, str) or not excerpt.strip():
        raise ValueError("A nonempty source excerpt is required")
    if len(excerpt) > MAX_EXCERPT_CHARS:
        raise ValueError(
            "Excerpt is longer than the documented comparison window; "
            "choose a bounded, relevant quotation rather than silently truncating"
        )
    if not model or not model.strip():
        raise ValueError("An installed local model tag is required")
    payload = {"claim": claim, "source_excerpt": excerpt}
    prompt = shadow.prompt_for(payload)
    sample = {"id": "single-source-claim", "prompt": prompt,
              "prompt_sha256": digest(prompt)}
    result = shadow.run_ollama_one(sample, excerpt, model)
    outcome = {
        "schema_version": SCHEMA,
        "mode": "advisory_only",
        "source_authenticity_verified": False,
        "inference": "from_supplied_excerpt_only",
        "model": model,
        "model_digest": result.get("model_digest"),
        "model_native_context_tokens": result.get("model_native_context_tokens"),
        "prompt_eval_count": result.get("prompt_eval_count"),
        "context_window_tokens": shadow.OLLAMA_NUM_CTX,
        "claim": claim,
        "source_excerpt": excerpt,
        "claim_sha256": digest(claim),
        "source_excerpt_sha256": digest(excerpt),
        "prompt_sha256": digest(prompt),
        "status": result.get("status", "error"),
        "verdict": result.get("judgment"),
        "error": result.get("error"),
        "raw_response": result.get("raw_response"),
        "raw_response_sha256": result.get("response_sha256"),
        "provider_response_sha256": result.get("provider_response_sha256"),
    }
    return outcome


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", required=True,
                        help="Claim to assess against the supplied excerpt")
    parser.add_argument("--excerpt-file", type=Path, required=True,
                        help="UTF-8 file containing the exact source quotation")
    parser.add_argument("--model", default="gemma4:12b",
                        help="Already installed local Ollama model")
    args = parser.parse_args()
    try:
        # Bound decoding before input validation: a mistaken huge file must not exhaust RAM.
        with args.excerpt_file.open("r", encoding="utf-8") as stream:
            excerpt = stream.read(MAX_EXCERPT_CHARS + 1)
        output = evaluate(args.claim, excerpt, args.model)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if output["status"] != "valid":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
