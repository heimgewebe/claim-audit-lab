# Published SciClaimEval tables: true two-turn local revision pilot

This is an **opt-in research finding**, not a factual truth certificate
or an enforced property of ordinary ChatGPT chats.

## Source provenance

Ho et al., *SciClaimEval: Cross-modal Claim Verification in Scientific
Papers* (LREC 2026), https://aclanthology.org/2026.lrec-1.864/.
Official release: https://huggingface.co/datasets/alabnii/sciclaimeval-shared-task
commit 55ec80b427d9b4eaff8ed9b537a1ea6cb5d665d7.
Task-1 data SHA-256:
cbf0db967f285875b7b283ed56f4fed93bf4627f84d8e7f3c39489bc56f289ab.
The selected source files are CC BY 4.0 according to original metadata;
see the exact per-file license and SHA-256 in manifest.json. Full source
tables remain in an unmodified, SHA-verified external cache. No source
or model download is needed during inference once the cache is prepared.

Frozen preregistration git commit: d7d49d9. Manifest SHA-256:
76cc43e2ca9a9f0820be1ccd499654dadbd6ccdbc61330393d45f4b5743de805.

The deterministic six source pairs (two per domain) are from six distinct
papers and the original claims are unchanged within each supporting/refuting
pair. Development used pair 0023 (ML: LoRA memory), 0120 (NLP: human EM
score), and 0265 (medicine: colds/activity p-value). Held-out pair 0002
(ML), 0209 (NLP), and 0298 (medicine) are **not** scored by any model.

One partner in each pair is a **deliberately altered evidence table**;
this tests revised reasoning relative to the supplied artifact, not
revising a lasting world belief in response to genuinely independent
contradictory publications. Published labels are stronger references
than homemade labels but not infallible world truth.

## Genuine chat turns versus independent baseline

For each source pair the model independently answered from the
supporting and refuting source tables, then received an actual two-turn
Ollama chat history containing its own first answer and the alternative
replacing source. Replacements were tested in both directions. An
unchanged-evidence follow-up with irrelevant administrative text tested
whether a model changed its answer without new relevant evidence.

Qwen3 14B and Gemma4 12B were the already locally installed models;
no cloud inference. They used the existing strict exact-contiguous
citation parser, truncation and context shifting explicitly disabled in the request,
and original plain-text LaTeX/HTML table bytes. Provider token
accounting is not an independent proof that every table token was read. A provider or incomplete-generation failure
is **not** a semantic wrong label.

## Strict original results

| Model | Development pairs complete | Calls | Fully valid source-grounded | Invalid output citations | Incomplete generation |
|---|---:|---:|---:|---:|---:|
| Qwen3 14B | 3/3 | 15 | 8 | 7 | 0 |
| Gemma4 12B | 2/3 | 11 | 3 | 7 | 1 |
| **Total** | | **26** | **11** | **14** | **1** |

On the ten source-replacement comparisons for which both initial and
revised calls were attempted, there were **4 fully valid expert-matching
fresh judgments and 3 fully valid expert-matching revised judgments**.
Those small counts do not support a practical improvement claim.
The preregistered >=2 gain criterion was **not met**; the held-out cases
were never run. Independent human reannotation of these selected tables
was **not** performed. No population accuracy estimate follows.

## What the raw answers reveal (post-hoc, explicitly weaker)

All ten fully attempted revision replies contained a raw JSON label
matching SciClaimEval's published source-relative label, compared with
eight of ten initial independent replies. In this post-hoc label-only
analysis, **10/10 revised versus 8/10 independent** is a *signal worth
further investigation*, **not** an externally validated scientific
improvement: many corresponding evidence spans failed literal
authentication, and the sample is tiny, public and selected.

For an unchanged-evidence follow-up, Qwen changed an initial raw
supported label to insufficient once without a relevant source change;
the earlier initial quote was invalid. This illustrates the risk of
unnecessary revision even when the final labels appear promising.
It was not counted as a fully source-grounded failure because the
preregistered gate requires valid original citations.

## Observable error mechanism

The two models often produced **semantic-looking but not literal**
citations from the raw LaTeX/HTML source, for example joining
noncontiguous table rows, dropping LaTeX row separators, or replacing
an HTML-escaped comparison with its rendered characters.

The existing strict parser correctly refused such generated strings
as noncontiguous byte-level quotations. Calling every one of those
failures a scientific misunderstanding would conflate *citation
serialization* with *evidence reasoning*; forgiving all of them
would risk fabricated citations. Gemma also generated a runaway
sequence of escaped line breaks and was conservatively classified as
generation_truncated, without retry.

The likely functional issue is a **representation mismatch**:
the models reason about human-rendered tables while the validator
demands a contiguous substring of raw markup. A possible follow-up
is to present a faithfully rendered, integrity-bound human-readable
table and keep an auditable link back to the original source before
changing citation policy. That hypothesis is **not yet tested**.
Adding more generic scientific prompt text or bypassing the quote gate
is not justified by this pilot.

## Integrity and reproducibility

- Original result files (immutable, create-only):
  run-development-qwen3-14b.json and
  run-development-gemma4-12b.json.
- Model tags, digests, full JSON model text, message SHA-256,
  response SHA-256, token counts, per-call duration, per-source hashes,
  gold boundaries and error categories are preserved.
- The failed development attempt and incomplete third Gemma pair are
  kept, with no retry or reported zero semantic accuracy.
- The entire 26-call sequence was read back against original source
  bytes and reconstructed exact chat message hashes. Every accepted
  quote was re-parsed and every rejected quote verified to be rejected;
  holdout result count was zero.
- There is no new default prompt, required double-check, CI gate,
  service, policy or chat capture integration.

**Decision:** Stop. Do not activate this method in ordinary responses.
Document both the small post-hoc source-sensitive label signal and the
larger formal citation defect. Future improvements require new,
paper-disjoint sources, robust presentation provenance, and a separate
holdout demonstrating better *fully valid* decisions.
