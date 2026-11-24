# Sentence-reference pilot — no advantage over the original minimal baseline

**Decision:** The frozen development screening criterion FAILED. Do not run
the eight reserved holdout cases, change the default prompt/validator, or
introduce a compulsory sentence-reference layer.

## Frozen protocol and scope

See run.py, SHA-256
5a4ef7bbe0168942e419a361419ee27dd1c6d5bf8e0355af4af8614c6251278f,
created 2026-11-24T15:05:34Z before inference. Sixteen published SciFact
claim/document pairs were deterministically selected, with distinct source
and claim IDs and excluding the prior SciFact and compound trials; eight
development, eight reserved. The source archive is the unchanged pinned
SciFact release (SHA-256
11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be).
The public release and attribution are described in
../scifact-expert-v1/README.md. Published expert labels are preserved.
Additional source-relative operator annotations were frozen before model
calls and are not independently validated human expert annotations.
One attack-related source was excluded as outside the method's scope
before any inference; the next ranked eligible case was selected.

Three paired one-call arms with identical models, settings, cases and
original source sentences: plain unchanged minimal prompt, numbered source
with quote generation, and numbered source with 1–3 exact sentence
references (zero allowed for insufficient). The displayed sentence
numbers are metadata. The reference parser rejects invalid, repeated,
unordered, boolean or out-of-range IDs, then resolves exact original
source offsets and text. Multiple references remain separate spans, not
a fabricated continuous quote. This is an opt-in experiment only.
Fifteen pre-inference positive/negative assertions on ID and span
reconstruction passed. No source or model downloads, new runtime gate
or default behavior.

## Observed results

All 48 planned requests completed (24 per model), no provider/context
errors. The only rejected response was a generated quote in the
numbered-quote arm: Qwen capitalized a word within the original sentence,
so the existing exact-contiguous-span parser correctly refused it.

| Model | Arm | Valid | Strict operator correct | Raw operator correct | Raw expert agreement | Complete expert rationale coverage |
|---|---|---:|---:|---:|---:|---:|
| Gemma4 12B | plain | 8/8 | 6/8 | 6/8 | 6/8 | 5/8 |
| Gemma4 12B | numbered quote | 8/8 | 6/8 | 6/8 | 6/8 | 5/8 |
| Gemma4 12B | reference | 8/8 | 6/8 | 6/8 | 6/8 | 5/8 |
| Qwen3 14B | plain | 8/8 | 6/8 | 6/8 | 6/8 | 5/8 |
| Qwen3 14B | numbered quote | 7/8 | 5/8 | 6/8 | 6/8 | 4/8 |
| Qwen3 14B | reference | 8/8 | 6/8 | 6/8 | 6/8 | 5/8 |

Strict correctness requires parser validity and label agreement.
All raw label vectors are identical across arms and both models.
Across both models, each arm contains two false supports and two false
refutations relative to the predeclared operator annotations, no missed
operator-explicit contradiction. Published expert agreement also remains
12/16 raw in every arm. Complete operator rationale coverage on the
eight clear support/contradiction model/case pairs is 6/8 plain, 5/8
numbered quote, 6/8 reference. Coverage is sentence localization, not
proof that a quote or sentence entails the claim.

| Arm | Prompt tokens | Output tokens |
|---|---:|---:|
| plain | 8,347 | 1,296 |
| numbered quote | 9,606 | 1,292 |
| reference | 9,966 | 1,034 |

Reference reduces generated tokens but uses 1,619 more prompt tokens
than the plain baseline. No runtime superiority claim: total tokens
increase from 9,643 to 11,000, and timing is confounded by model warmup.

### Scientific boundary

The models all supported claim 521 although the excerpt discusses time
between symptom onset and presentation, not the claim's time before
injury. All treated the different drug combination in claim 1359 as a
direct contradiction despite the source not testing nicotine replacement
therapy. Conversely all judged 1132 and 728 insufficient despite
published support/contradict annotations: the excerpts address CD3
conformational change and inflammatory recruitment rather than the
specific synapse/microdomain requirement and inflammatory capacity.
These are source-relative operator assessments and suspected reference
gaps, not corrections of the published expert corpus. The negative
treatment comparison is unchanged regardless of which label set is
used. For 619 all arms cite the outcome sentence while the operator
rationale additionally requests the intervention sentence; label
agreement alone is not sufficient evidence localization.

The actual unchanged plain baseline had **zero transport errors** on
these simple claims. Sentence references therefore have no demonstrated
benefit over the existing workflow in this sample, despite one better
result compared with numbered quote. No claim that this technique is
useless for all evidence tasks. The prior compound experiment had a
different failure distribution (nine rejected direct quotes), so a
separate exposed-case diagnostic can test that concrete problem;
it must not be called a new independent holdout.

## Reproduction and original evidence

Invoke the frozen run.py with --repo, --archive, --model, --split and a
new --output filename. Use score.py with --repo, --archive, --runner and
the stored result files. The offline score reconstructs original source
and numbered displays, matches source/prompt/response hashes and reruns
the applicable parser, without model calls. All 48 stored outputs were
successfully reconstructed and checked. Do not use optimized Python
assertion stripping for the offline check.

| Original result | SHA-256 | Completed Grabowski task |
|---|---|---|
| run-development-gemma4-12b.jsonl | 711886b168475e31e3a63e5c916ba49460238e1186d3e1d6c59cbb24ab592379 | 676a63d1cf594a86bb50fcd1 |
| run-development-qwen3-14b.jsonl | 055ac4dd8b1bf5b4779dcca1d8e53e9cf4aef5a2556b749bdd258dbaae032fed | 8a418a1b6c4c43c3b593f4c0 |

Model digests: Gemma
6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b,
Qwen bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8.
No reserved-holdout inference or normal ChatGPT interception.
