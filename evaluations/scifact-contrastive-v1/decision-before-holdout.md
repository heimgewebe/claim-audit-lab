# Development decision: STOP before running holdout

The protocol, deterministic manifest and runner were committed as
324964f before the first model inference. The unchanged local Qwen3 14B and
Gemma4 12B implementations each evaluated 8 development pairs under
the minimal and contrast instruction (32 completed, valid replies).

| Model | Minimal expert matches | Contrast expert matches | Missed expert refutations (both) | False refutations of expert support (both) |
|---|---:|---:|---:|---:|
| qwen3:14b | 6/8 | 6/8 | 0 | 1 |
| gemma4:12b | 6/8 | 6/8 | 0 | 1 |

All four arms have 8/8 formally valid citations and no provider/context errors.
Every individual label remained identical between the minimal and contrast
conditions, for both models. Contrast raised total input tokens per model
(4089 to 4409 Qwen, 3966 to 4286 Gemma). Wall-clock timings cannot be
compared causally because model warmup/cache differs between consecutive runs.

**Preregistered development success criterion not met.**
Do not run the holdout, do not modify either default prompt, and do not add
a validator, retry loop, mandatory second opinion or runtime gate.

The 8 separately selected and source-disjoint holdout items are frozen
in manifest.json but **no holdout model trial was executed**. Their published
rationale snippets were inspected manually for reference quality after
the hypothesis and selection had been frozen; they are therefore not
strictly unseen by the operator, although no gold was changed and no
model prediction was observed.

Two important development observations are not interchangeable:
- Expert SUPPORT case 597:12779444 asserts incidence decreased, but its
  designated rationale is about **mortality** decline. Both models returned
  insufficient, which is defensible for the supplied text. Without
  independent adjudication this is a candidate annotation-to-excerpt
  discrepancy, not a proven correction to SciFact's official reference.
- Expert SUPPORT case 636:24294572 addresses PTEN converting PI(3,4)P2
  to PI4P. Both models instead said contradicted. Gemma even claimed
  a 3-phosphatase would leave PI(3,4)P, chemically retaining the very
  3-position phosphate it supposedly removed. See report.md for an
  independent published experimental confirmation of the correct product.

This is a negative result for exactly this one prompt intervention on a
small preselected development subset; not a finding that semantic
verification or scientific reasoning cannot be improved.
