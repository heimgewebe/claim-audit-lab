# Post-observation erratum: raw-source display integrity

**Amendment classification:** engineering integrity repair performed AFTER the
60 development model calls and AFTER immutable result files were committed.
It is **not** a new experimental condition, a reanalysis of unpublished
holdout predictions, a gold correction, or proof of better model judgments.

## Independent GitHub review found four genuine counterexamples

On PR #44 (original reviewed head 5aa43472a9b586865f50d44a3181e2fbc0ce9242),
Codex identified four independently reproducible data-integrity errors in the preregistered renderer:

1. https://github.com/heimgewebe/claim-audit-lab/pull/44#discussion_r4663464465 :
   Two logical LaTeX table rows on one physical line were incorrectly merged
   into a single display row. A model could then quote across both rows as if
   the quote had unique one-row source provenance.
2. https://github.com/heimgewebe/claim-audit-lab/pull/44#discussion_r4663464474 :
   Stripping structural HTML tags inside a cell could invent concatenated
   numeric values. For example an original cell containing "1", a break tag,
   and "2" was displayed as "12". Superscript/subscript/MathML are also not
   safe to discard without a verified semantic representation.
3. https://github.com/heimgewebe/claim-audit-lab/pull/44#discussion_r4663598794 :
   Unescaped TeX '%' comments inside a data row could be rendered and quoted
   as if the ignored text were scientific evidence; complete comment lines
   could also be authenticated as independent table rows.
4. https://github.com/heimgewebe/claim-audit-lab/pull/44#discussion_r4667265029 :
   HTML commented-out rows could be parsed as visible data and falsely
   authenticated, for example a withdrawn numeric value 99.9 in a hidden
   table row. Both closed and unterminated HTML comments must be refused.

All four counterexamples were REPRODUCED before their respective renderer
repairs; the tests initially failed (RED). The frozen parser accepted joined
LaTeX rows, concatenated HTML cell values, non-data TeX comments and
commented-out HTML rows.

The minimal post-review repair is **fail closed** on unsupported evidence
presentation, not to add a prompt or relax the source-quote validator:
- Reject multiple outer LaTeX row terminators sharing a physical line.
  Exclude complete inline tabincell/inner-tabular cell constructs from
  the *delimiter count*, retaining original source characters and hashes;
  reject unsupported incomplete nested table markup.
- Refuse structural and mathematical HTML markup within source table cells
  whose removal could change numeric meaning, while continuing to decode
  plain escaped entities and harmless formatting markup.
- Ignore complete TeX comment lines outside pending logical rows; refuse
  unsupported unescaped inline comments to avoid laundering hidden text as
  data, but preserve escaped percent values such as 87\%.
- Reject native HTML tables containing HTML comments entirely rather than
  extracting invisible rows. This is a deliberately narrow unsupported
  source class, not a new production-wide restriction.
- Add direct regression cases for all four reviewer counterexamples,
  mixed inline-LaTeX cells, HTML sup/sub/break/paragraph, MathML, HTML
  comments and escaped percentages while retaining source provenance.

**Important new integrity finding:** The post-observation TeX-comment fix
**does change two of the six original development source presentations**:
SciClaimEval NLP pair 0126 (both Supported and Refuted) contained a whole
comment line with pseudo-headers such as '-para' and '-sent'. The frozen
renderer displayed that line as table data. It is now correctly excluded.
The original displayed-source SHA-256 values in manifest.json were
eab6a86ee85e9db6c403195ac8e81bc7622f8e5d10c5d37a8d74926156cdc0e9
(Supported) and d0a66fb2cbb755af9b415640ba424edddc80fea13a5c2d99c6b2d0acfaee92bc
(Refuted); the hardened output hashes are
7e5475bf9f5ce2da9e205daed765d04dcdee2d545e1646717cee6d98077ae02a
and b85d63a55a4ed3295ae87e8a8360b80563daec3cad417a1eeb9517f71a693fd0.
The other **four** development source versions retain identical displays.
No earlier claim, original source bytes, model instruction, model output,
published label, result row, comparison number, or stop criterion changed.

Therefore the 27/30 versus 17/30 provenance result measures the **frozen
original experiment renderer, which now has demonstrated source
presentation defects**. Even though the originally quoted Qwen spans in
pair 0126 refer to visible FEVER data rows and not directly to the
commented-out line, its influence on model reasoning cannot be ruled out.
Do not represent the figures as performance of the hardened renderer
or as a clean end-to-end proof of scientific source integrity. The
appropriate next study needs freshly preregistered, source-complete cases.

## Frozen experimental identities and explicit non-claims

- Original preregistration: commit 11f5d3b.
- Original experiment renderer SHA-256:
  b6542c4f3896dee1644ea7b45a8e3deaec9aff6b55626e6cfc8f2d90092b25cf.
- First post-observation hardened renderer SHA-256 (two findings):
  c8c5f440ea65d854a6c64ce601faf03c83e4584075b68f5ee9a1ced58f06dce5.
- Intermediate hardened renderer SHA-256 (including third TeX finding):
  45e7d3a619177813152914eb4e692308b6e5ff2e6398e9bb1a70cce0f401c16d.
- Current post-review renderer SHA-256 (also rejecting HTML comments):
  64678ed7eebfa7ac23d07d51431524f351186206242c5ff0b59c03620f3052fe.
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

The apparent development gain in quote validity remains a result of
the **frozen, now demonstrably imperfect original renderer and three
selected papers**. It is not evidence that the hardened renderer already
delivers the same gain. The review demonstrates why complete native-table
source representation must be scoped and adversarially tested. It does not authenticate the scientific
papers or prove an improvement in world-truth reasoning. Nothing from this
repair is made mandatory for normal ChatGPT answers, production sources,
model inference, or claim-audit-lab cases.