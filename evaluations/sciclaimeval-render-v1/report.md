# SciClaimEval native-table rendering: bound citations improved, scientific gate did not pass

**Post-observation qualification:** A subsequent independent Codex review
demonstrated four source-presentation defects in the original experimental
renderer; one affected the displayed input of an actually model-tested
development paper (pair 0126). The original 60 model outputs and all
numbers below are preserved as historical evidence, **not** re-scored
under the hardened renderer. The primary-source fidelity of the original
treatment is therefore compromised. See
[post-observation-erratum.md](post-observation-erratum.md) for exact changed
display hashes, reproducible counterexamples and the unchanged holdout.
No claim of improvement by the current hardened renderer follows.



## Scientific purpose and methodology

Test whether an intact scientific table, transformed from native LaTeX or
HTML into compact human-readable rows **with a deterministic proof of each
quoted row's location in the original source**, helps a local model make
more provenance-valid and expert-matching judgments, including genuine
two-turn source-replacement revisions.

This remains a voluntary lab evaluation, not a quality-certified ordinary
ChatGPT response path. See protocol.md and the first before-inference
commit 11f5d3b, containing the renderer, unchanged golden selection,
preregistered go/no-go criteria, source hashes and exact code. The
attempted initial selection was recorded before any model inference in
aborted-pretrial-manifest.json because a physically multiline LaTeX
table was initially rendered as incomplete data. The repaired renderer
assembles logical rows, preserves a contiguous original-source character
span for each row, and binds SHA-256 of source, row, display and quote.

Sources: Ho et al., SciClaimEval, LREC 2026:
https://huggingface.co/datasets/alabnii/sciclaimeval-shared-task
Pinned dataset commit 55ec80b427d9b4eaff8ed9b537a1ea6cb5d665d7,
Task-1 JSON SHA-256
cbf0db967f285875b7b283ed56f4fed93bf4627f84d8e7f3c39489bc56f289ab.
Selected native source tables have individual CC BY 4.0 metadata recorded
in manifest.json; complete scientific table files remain pinned by SHA-256
outside the git repository. The selected six papers share none of the six
PR43 papers. **Published Supported/Refuted labels are only
source-relative expert annotations, not independently established world
truth.** The refuting table is deliberately modified, not a second paper.

The model sees the same claim and caption with either original native
markup (RAW) or a deterministic, source-backed row presentation
(RENDERED). Both arms use the unchanged existing scientific semantic
instruction, real locally installed Qwen3 14B/Gemma4 12B, zero temperature,
proxy-free Ollama API, and no model downloads. Each of the three
development pairs per model/condition is tried as independent support,
independent refutation, two opposite genuine two-turn source replacements
and an unchanged-evidence control. All outputs are create-only original
receipts; holdout is conditionally unused.

## Exact development results

| Model | Condition | Fully valid/15 | Invalid quotes | Valid expert-matching revisions/6 | Missed expert contradictions | False expert-support refutations | Unchanged-control changes |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3 14B | RAW | 9 | 6 | 1 | 2 | 0 | 0 |
| Qwen3 14B | RENDERED | 13 | 2 | 2 | 2 | 0 | 0 |
| Gemma4 12B | RAW | 8 | 7 | 0 | 1 | 0 | 0 |
| Gemma4 12B | RENDERED | 14 | 1 | 2 | 1 | 0 | 1 |
| **Total** | **RAW** | **17/30** | **13** | **1/12** | **3** | **0** | **0** |
| **Total** | **RENDERED** | **27/30** | **3** | **4/12** | **3** | **0** | **1** |

All **60/60 scheduled development calls** were attempted and produced a
saved model result. **44/60** passed the strict original/derived-source
citation check; **14** raw/model quotations failed the documented
contiguous quote schema and **2** rendered quotes could not be uniquely
bound to one original source row. There were zero provider/context
failures or clipped generations. On exactly these selected development
cases, a faithful row display increased valid source-bounded outputs
from 17/30 to 27/30. It did **not** independently demonstrate that the
underlying scientific claim judgments are more correct in general.

An important source-specific distinction: the display proof validates a
quote against a **deterministically transformed** row (e.g. decoded
HTML entity or collapsed LaTeX row), with the row's unchanged raw-source
location and SHA. It is **not** a misleading assertion that the displayed
quote is a byte-for-byte substring of the raw HTML/LaTeX file. Quotes
that combine multiple rows or have ambiguous provenance are rejected.
This mechanism makes a better *audit trail*, not a world-truth oracle,
and does not prove every omitted style element is semantically irrelevant.

## Why no holdout and no default integration

The predeclared development threshold required at least +3 fully valid
expert-matching revised answers across both models with no increased
missed real expert refutations, false refutations, invalid citations,
provider errors **or changes on irrelevant control information**.
The revised judgments improved by exactly +3; quote errors decreased
by ten; missed/false refutations were not increased. However one
otherwise valid Gemma4 answer changed on unchanged evidence, so the
full go criterion **failed**. The holdout was not opened.

The changed-control case is NLP 0152 (a claim combining Archer 6.73%
and Spider 85.3% scores). Initial Gemma4 RENDERED response said
supported; after an unrelated note it said insufficient, explicitly
because the table did not include the Spider comparator. This is a
**label change** but could be an epistemically warranted reassessment,
not a proven error. The published expert annotation and source hash
were left unchanged. Its epistemic status requires independent
adjudication; we did not change the preregistered rule to rescue the
experiment after observation.

The time and prompt budget also changed with display size. RAW used
68,791 prompt-evaluated tokens across both models, RENDERED used
34,417. Total measured local generation time was 54.76 seconds RAW
versus 46.58 seconds RENDERED; chronological order and model warmup
differ, so no causal latency claim follows. This experiment does not
identify whether a future improvement came from rendering, removal of
stylistic noise, shorter contexts or genuine better scientific reasoning.