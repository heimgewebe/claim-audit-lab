# Compound claim oracle-splitting pilot — negative confirmation

**Decision:** Do not enable isolated atom verification as a default. The
development screen passed, but the frozen holdout non-regression rule
failed. No changes to the ordinary shadow CLI, validator or chat runtime.

## Protocol and evidence

See the pre-inference protocol and operator-authored cases in the unchanged
run.py, SHA-256 cd6b82e3fc15654d5655775523c867be936296a19f52975d599434ba23f76de3
(created 2026-11-24T12:04:23Z). See decision-before-holdout.md for the frozen
development decision (created 2026-11-24T12:10:24Z). The holdout rule was
specified after development but before any holdout inference, using the
same non-regression criterion as development.

The twelve distinct abstracts were deterministically selected from the
original SHA-verified SciFact archive, excluding both earlier SciFact
manifests and smoke document 13734012. Original sources and exact prompt
can be reconstructed from the pinned archive and runner. The claims,
atomic components and reference labels are newly operator-authored;
not the published SciFact expert gold. No independent human annotation.
Every case is source-relative, not a judgment of ultimate world truth.
Source attribution and license: Wadden et al. (EMNLP 2020),
https://github.com/allenai/scifact ; S2ORC abstracts ODC-By 1.0, see
../scifact-expert-v1/README.md. No original source rendering.

Both conditions use the same minimal instruction and unchanged local
backend. The direct claim presents both clauses in adjacent sentences
with "Additionally,"; the treatment independently evaluates each
operator-given clause and aggregates C > I > S. The treatment does not
automatically discover clauses. All 72 requested inferences returned
model text; no provider/context errors or retries. All 72 original rows
and per-run header hashes remain intact.

| Split | Model | Strict correct direct | Strict correct split | Valid direct | Valid split | False C direct/split | Missed C direct/split |
|---|---|---:|---:|---:|---:|---:|---:|
| Development | Gemma 4 12B | 3/6 | 6/6 | 4/6 | 6/6 | 0/0 | 1/0 |
| Development | Qwen 3 14B | 4/6 | 5/6 | 4/6 | 5/6 | 0/0 | 0/0 |
| Holdout | Gemma 4 12B | 3/6 | 5/6 | 4/6 | 6/6 | 1/0 | 0/1 |
| Holdout | Qwen 3 14B | 3/6 | 4/6 | 3/6 | 5/6 | 0/0 | 0/1 |

Strict means the existing JSON/exact contiguous quote parser accepts the
response (both responses for atom aggregation), plus reference label
agreement. Invalid responses count as not correct; missed C includes
invalid outputs on reference-C cases. Validity does not by itself
establish that the quotation actually supports the label. All raw reasons
were read against the selected sources. Fully correct strict atom pairs:
11/12 development and 9/12 holdout; valid individual atomic answers
23/24 development and 23/24 holdout; correct individual atomic answers
23/24 development and 21/24 holdout.
Across both models and splits there were 24 direct calls and 48 atom calls.

### Separating semantics from quote transport

As a **post-hoc diagnostic only**, all raw label JSONs could be parsed
even when a quote was rejected. Raw-label accuracy ignoring quote validity
was 10/12 -> 12/12 on development, but **11/12 -> 10/12 on holdout**.
Thus increased end-to-end strict accuracy on holdout (6/12 -> 9/12)
does not mean improved semantic accuracy. Of eleven rejected individual
responses, six become contiguous after replacing all whitespace runs
with one space (a diagnostic, NOT a change in accepted source identity),
and five do not. Direct quote invalid: 9/24; isolated atom quote invalid:
2/48. The original exact-source requirement stays unchanged.
Total prompt tokens: direct 9,993 vs isolated atoms 18,927 (+89.4%).
Different per-claim call count and token budget remain confounds.

## Three decisive source-relative examples

- **21287352 (development, both models):** the direct raw judgments
  incorrectly supported a conjunction of CRP association with FEV(1)
  decline and a CRP-lowering intervention slowing decline. The abstract
  reports inverse correlation, not a causal intervention. Both isolated
  B judgments correctly said insufficient. Qwen's A citation remained
  invalid. The gain in semantic reasoning is real on this example,
  but the method is not uniformly superior.
- **20767776 (holdout, Gemma):** the direct judgment treated "has not
  been established" as a refutation of genetic causation. The abstract
  reports a family questionnaire, not an identified genetic mechanism.
  The isolated B judgment correctly said insufficient. Qwen direct raw
  judgment was already insufficient, but its quote was invalid.
- **40234452 (holdout, both models):** the source reports two different
  ratios for side-population and CD34(low/-) progeny, 3.5-fold and 7.8-fold,
  in that order. The conjunction falsely assigns 3.5 to both. Both direct
  models identified the mismatch correctly. Both isolated B judgments
  accepted 3.5 for CD34(low/-) despite quoting the sentence containing
  both numbers. This is an observed missed contradiction introduced by
  the treatment; exact quotes and correct aggregation cannot repair it.
  Loss of comparison context is a plausible causal explanation, not yet
  established by a controlled ablation.

## Decision

Development passed. Holdout failed because both models newly missed an
explicit contradiction; do not relax the rule after seeing the data.
No ordinary answer gate or automatic decomposition implemented. Next
scientific question: preserve the whole claim and compare specific
entity-to-value relationships instead of hiding the comparison context
from each local check. Separately, test source sentence references with
verbatim reconstruction as a way to reduce quote transport errors
without lossy source transformation. Any exploratory reuse of these
cases is diagnosis, never an independent confirmation. Confirm only
on genuinely new source-disjoint cases with comparable inference budgets.
The dataset is public and may have been seen in pretraining. Samples
are small, and operator-authored claims are not independent annotations.

## Original evidence

| File | SHA-256 | Grabowski task |
|---|---|---|
| run-development-gemma4-12b.jsonl | f8a650c2584c3a354960b1c82c56c9a13a316319602d58ec6b97948e5eca4e03 | d6b64ec06a384a318b2c4356 |
| run-development-qwen3-14b.jsonl | d2435309b3ca8df52e065d9ceb9cf0f5d5b2fb3c1c6e9fa54dffe7f54fbcd6c4 | d2470a7f365c4db28a270a11 |
| run-holdout-gemma4-12b.jsonl | 7db2ae6da71e2ed7166190405581492ce1474a7c16c9fdf395b1dfa8b4d6806c | 0401bf96887b4342af930d6b |
| run-holdout-qwen3-14b.jsonl | 5c02b601730e12d314cc3a99fe1f7baf26f00fe7b1f57c365d6508d75fb2a329 | 01395299c2f7437cadc87fe7 |

Each task completed, with local model digests Gemma
6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b
and Qwen bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8.
No new service or production policy.
