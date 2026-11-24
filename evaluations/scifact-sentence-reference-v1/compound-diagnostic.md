# Exposed-case compound diagnostic — citation transport is not entailment

**Decision: FAIL the frozen diagnostic gate. No production promotion.**

This is a post-hoc mechanism diagnosis on six deliberately selected,
previously exposed compound cases from scifact-compound-pilot-v1, not an
independent holdout or population estimate. The original full compound
claims, operator labels and source abstracts are unchanged. The runner
was frozen before inference (15:10:58 UTC, 2026-11-24; SHA-256
`6b1875caaa344bf6072e9853f7da0507889f36fd80857e8f082a2c629f271348`).
Its gate requires at least two invalid plain responses, at least two
additional strict correct labels over EACH quote arm, no new raw-label
error, no loss of a previously recognized contradiction, and relevant
reconstructed evidence. All conditions must hold.

Both models finished 18 calls each. No selective retries; no single-claim
reserved holdout was accessed. The original claims and labels, runner,
archive, source, numbered display, prompt and response hashes and parser
results were checked again offline for all 36 responses.

| Model | Arm | Valid | Strict correct | Raw-label correct |
|---|---|---:|---:|---:|
| Gemma4 12B | plain | 2/6 | 1/6 | 5/6 |
| Gemma4 12B | numbered_quote | 2/6 | 1/6 | 5/6 |
| Gemma4 12B | reference | 6/6 | 5/6 | 5/6 |
| Qwen3 14B | plain | 2/6 | 2/6 | 5/6 |
| Qwen3 14B | numbered_quote | 2/6 | 2/6 | 5/6 |
| Qwen3 14B | reference | 6/6 | 4/6 | 4/6 |
| Both | plain | 4/12 | 3/12 | 10/12 |
| Both | numbered_quote | 4/12 | 3/12 | 10/12 |
| Both | reference | 12/12 | 9/12 | 9/12 |

Strict means parser-valid and correct operator label. Raw-label correctness
ignores citation rejection. Labels concern excerpt entailment, not clinical
or scientific truth beyond the excerpt. These are operator-authored labels.

The reference arm resolves all eight invalid outputs in each quote arm
but loses one correctly recognized contradiction in Qwen (40234452).
The original S3 sentence reports distinct progeny ratios, 3.5-fold and
7.8-fold, respectively. The reference response conflates them as a range
and labels the full claim supported, despite selecting precisely S3.
Gemma preserves the contradiction. Numbering alone did not cause this
observed error: both numbered-quote responses correctly contradict it.
This does not establish a general causal mechanism or population effect.

Both reference models still wrongly support 21287352: the reported
inverse CRP/FEV(1) association does not establish that lowering CRP
slows decline. Both select correlational evidence. That error already
exists in the raw labels of both quote arms.

For 28419824, 17333231, 34747208 and 42404093, the reference arm
selects the relevant separated source sentences and preserves correct
compound labels. The Qwen numbered-quote output for 42404093 is an
additional caution: it is parser-valid and labels the claim contradicted
but selects S13 (support for the first clause), not the decisive contrary
ordering/administration evidence in S15. The strict metric does not
independently establish evidence relevance.

Token totals (prompt/output) are plain 5164/1277, numbered quote
6107/1276, reference 6377/905. Validity improvement is genuine within
this exposed-case test, but is not a gain in scientific discrimination.
It cannot override the no-new-semantic-error condition. Do not activate
sentence references as a default or infer a successful holdout.

## Reproduction

Run the diagnostic with the original pinned archive and models, choosing
new output paths; offline verification (no inference):

```sh
python3 evaluations/scifact-sentence-reference-v1/score_compound.py \
  --repo . --archive /path/to/scifact-release.tar.gz \
  evaluations/scifact-sentence-reference-v1/compound-diagnostic-gemma4-12b.jsonl \
  evaluations/scifact-sentence-reference-v1/compound-diagnostic-qwen3-14b.jsonl
```

Run with assertions enabled. The archive SHA-256 is
`11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`.
Original files are byte-identical to task outputs:
Gemma SHA `4283aa2cee62354b5029ad5a3508a8bfca53a0803cffd1fbe8eb0be6125cb1d7`,
task 6837a4ab7e7c4156ba5f8970; Qwen SHA
`335a225174d120242ad0379ea5d1c821a6dbb89e969ce3f3948c4f54d25a6fb3`,
task 7160fbc0a48745baadf09ed5.

## Scientific implication

Further work should test relation-sensitive interpretation of the evidence
itself (entity, value, comparator, direction, causal vs observational
relation), against the unchanged minimal full-claim baseline, on fresh
source-disjoint cases. Do not treat successful transport, formal receipts
or more elaborate output schemas as a proxy for entailment. Preserve
the existing normal answer runtime until a fresh preregistered holdout
shows improvement without new false supports or missed contradictions.
