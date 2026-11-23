# SciClaimEval native-table rendering: bound citations improved, scientific gate did not pass

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
The three-paper development sample and lack of independent reannotation
are far too small for generalized scientific truth or mandatory runtime
enforcement.

## Immutable input and original output identities

- Before-inference finalized manifest SHA-256:
  c5f91e3ed9240cd41ad4dd270e01dfd86944953ce3a1d015c25765283b2d863a.
- Aborted, never model-tested pretrial manifest SHA-256:
  375b79d7082f84829c25b220cd6150d2af7c8aa78c31ddfef91f20e4cf4ae497.
- Qwen RAW: run-development-qwen3-14b-raw.json,
  SHA-256 41ac1ec42ad5ccc202cc694d567e645e00f7f60625892c58e2f4e34935483dad.
- Qwen RENDERED: run-development-qwen3-14b-rendered.json,
  SHA-256 c33fd2e74524d57173b21981dc2dd5bcdc20996a930e7e12ff634db026cea005.
- Gemma RAW: run-development-gemma4-12b-raw.json,
  SHA-256 34aab99dd9da972d5379f470d10b09bc363fbb7563c857e429c04b25beacbd1d.
- Gemma RENDERED: run-development-gemma4-12b-rendered.json,
  SHA-256 5d1ec499338959d3f9862d50e4bd9b2116b61e2c2af6af698c287081baa0a998.

All 60 original responses were read back with a second verifier. It
reconstructed each real chat turn and compared its SHA-256, checked
per-row source and display identities against the pinned original file,
re-applied the existing strict output parser, and confirmed each valid
rendered quote had the same unique original-row provenance. All
reported invalid quote failures were reproduced; holdout output count
was zero. This is a verified reproducibility result, not independent
human annotation.

**Decision:** retain source-bound row rendering as an experimental,
opt-in research method only; do not modify the existing single-source
verifier, global prompt, quality gate, services or regular chat flow.
