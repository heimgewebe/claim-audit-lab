# Development decision — STOP; holdout not opened

Pretrial code, both manifest versions, methodology and source mapping tests
were committed before model calls as 11f5d3b. Final manifest SHA-256:
c5f91e3ed9240cd41ad4dd270e01dfd86944953ce3a1d015c25765283b2d863a.
The aborted earlier unscored manifest was preserved separately and is not
included in scored data. Only the final six new paper-disjoint pairs were
eligible. Three development papers were used (NLP 0126 and 0152, PeerJ 0281);
three independent paper IDs were held out without model inference.

Both locally available models actually completed all 5 planned responses per
development paper, in each condition, totaling **60/60 model calls**. All
source IDs, raw response SHA-256, conversation message hashes, original-source
SHA, rendered-source SHA and returned evidence/provenance were rechecked.
There were no provider or context errors.

| Metric | RAW (30 calls) | RENDERED (30 calls) |
|---|---:|---:|
| Fully valid quoted source judgments | 17 | 27 |
| Invalid citations or bound rendered quote | 13 | 3 |
| Fully valid expert-matching revised judgments | 1/12 | 4/12 |
| Missed annotated refutations among valid revised outputs | 3 | 3 |
| False refutations of expert-supported revised sources | 0 | 0 |
| Unchanged-evidence control label changed (valid pair) | 0 | 1 |

By model, fully valid expert-matching revised judgments: Qwen3 RAW 1/6,
RENDERED 2/6; Gemma4 RAW 0/6, RENDERED 2/6. All four 15-call attempts
completed; no retries or overwritten outputs.

**Primary +3 criterion met, but full preregistered improvement criterion
FAILED**: one Gemma4 case changed its verdict when the table remained
unchanged and the added note was unrelated. This is an observed control
*change*, not by itself a demonstrated erroneous change. In the affected
published expert-SUPPORT case 0152 the original answer was supported,
but the second answer was insufficient because the supplied table gave
an Archer score and no Spider test-set score, despite the claim asserting
both. The later answer may be more epistemically justified than the
published source-relative gold; independent human adjudication is absent.
Our **predeclared no-control-change gate nevertheless fails**, and we
must not redefine that criterion after seeing the result.

**Decision:** Do not open the 3-paper holdout. Do not install a mandatory
source renderer, default prompt, extra model reviewer or chat interception.
Preserve exact positive provenance and citation signal alongside the
failed complete decision criterion; do not claim scientific E2E gain.

The treatment both shortens the prompt (68,791 RAW versus 34,417 RENDERED
prompt-evaluation tokens for both models combined) and changes its format.
The two effects are confounded. This selected public three-paper
development set cannot yield population error estimates and may have
appeared in model pretraining.

The correct next hypothesis would require an independently reannotated
paper-disjoint set and an explicit distinction between an unjustified
reaction to irrelevant context and a legitimate correction of a previously
overconfident answer. It must also separate display/token-length effects.
That work remains open, not retrospectively incorporated here.
