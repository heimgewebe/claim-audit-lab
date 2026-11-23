# Post-observation erratum: raw-source display integrity

**Amendment classification:** engineering integrity repair performed AFTER the
60 development model calls and AFTER immutable result files were committed.
It is **not** a new experimental condition, a reanalysis of unpublished
holdout predictions, a gold correction, or proof of better model judgments.

## Independent GitHub review found two genuine counterexamples

On PR #44 (original reviewed head 5aa43472a9b586865f50d44a3181e2fbc0ce9242),
Codex pointed out two data-integrity errors in the preregistered renderer:

1. https://github.com/heimgewebe/claim-audit-lab/pull/44#discussion_r4663464465 :
   Two logical LaTeX table rows on one physical line were incorrectly merged
   into a single display row. A model could then quote across both rows as if
   the quote had unique one-row source provenance.
2. https://github.com/heimgewebe/claim-audit-lab/pull/44#discussion_r4663464474 :
   Stripping structural HTML tags inside a cell could invent concatenated
   numeric values. For example an original cell containing "1", a break tag,
   and "2" was displayed as "12". Superscript/subscript/MathML are also not
   safe to discard without a verified semantic representation.

Both minimal counterexamples were REPRODUCED before changing the renderer;
the regression tests initially failed (RED). The original parser accepted
joined LaTeX rows and displayed concatenated HTML cell values.

The minimal post-review repair is **fail closed** on unsupported evidence
presentation, not to add a prompt or relax the source-quote validator:
- Reject multiple outer LaTeX row terminators sharing a physical line.
  Exclude complete inline tabincell/inner-tabular cell constructs from
  the *delimiter count*, retaining original source characters and hashes;
  reject unsupported incomplete nested table markup.
- Refuse structural and mathematical HTML markup within source table cells
  whose removal could change numeric meaning, while continuing to decode
  plain escaped entities and harmless formatting markup.
- Add direct regression cases for both exact reviewer counterexamples,
  mixed inline-LaTeX cells, HTML sup/sub/break/paragraph and MathML,
  while preserving the existing single-row source-offset and quotation
  proofs.

The existing original PR44 development-source presentations for all
**six source versions** (three papers × Supported/Refuted) have unchanged
rendered-source SHA-256 under the hardened renderer. This was rechecked
against the frozen manifest with original SHA-verified source files.
No earlier claim, source text, model instruction, model output, published
reference label, result row, comparison number, or stop criterion changed.

## Frozen experimental identities and explicit non-claims

- Original preregistration: commit 11f5d3b.
- Original experiment renderer SHA-256:
  b6542c4f3896dee1644ea7b45a8e3deaec9aff6b55626e6cfc8f2d90092b25cf.
- Hardened **post-observation** renderer SHA-256:
  c8c5f440ea65d854a6c64ce601faf03c83e4584075b68f5ee9a1ced58f06dce5.
- Immutable four original result JSON files retain the ORIGINAL renderer
  hash and exact response/model/source/prompt hashes. Their integrity tests
  correctly bind to the frozen origin, not a later working-tree hash.
- The final manifest remains unchanged, SHA-256
  c5f91e3ed9240cd41ad4dd270e01dfd86944953ce3a1d015c25765283b2d863a.
- The original development outcome still fails the preregistered no-control-
  change criterion. Holdout remains 0 model inferences.
- A structural-only recheck of the untested holdout exposed native MathML
  inside paper 18589 (SciClaimEval pair 0296). The original renderer would
  erase that markup. The hardened renderer correctly **rejects** that
  source as unsupported instead of claiming semantically faithful display.
  This freezes the original holdout as historical, unrun trial input; it
  is **not usable with the hardened renderer**, and no replacement paper,
  changed manifest or new "clean" holdout has been selected post-observation.
  Any fresh trial must preregister its own supported source set before
  model inference.

The previous development gain in quote validity remains an observation
on the **frozen experimental renderer and three selected papers**. The
review demonstrates why complete native-table source representation must
be scoped and adversarially tested. It does not authenticate the scientific
papers or prove an improvement in world-truth reasoning. Nothing from this
repair is made mandatory for normal ChatGPT answers, production sources,
model inference, or claim-audit-lab cases.
