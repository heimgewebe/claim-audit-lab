# SciFact: targeted claim-relation instruction failed development screening

**Scope:** Direct, opt-in source-excerpt semantic evaluator only; no mandatory
artifact or chat enforcement. Original SciFact release SHA-256
11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be,
licensed and attributed as described in ../scifact-expert-v1/README.md.
Preregistered branch commit: 324964f. New source-disjoint manifest SHA-256:
accf2a23fa26fc3bd8f38b73cafa99d826f06b2386d91dc5f7d9b2b362796be7.
16 pairs, 8 development and 8 never used for model inference in holdout;
each split balances 4 published expert SUPPORT and 4 CONTRADICT.

## What was tested

Unmodified minimal SciFact source prompt versus exactly one added clarification:
resolve the claim's subject, predicate, negation and comparison direction,
rather than treating shared topic or a related effect as sufficient.
Both prompts used the existing strict contiguous-span parser and
running local models with no cloud access, transparent model identity
and no context truncation. Provider errors were scored separately.
No model was shown a gold label or published rationale.

| Model | Minimal development | Contrast development | Valid responses each | Missed expert contradictions each | Contradicted expert supports each |
|---|---:|---:|---:|---:|---:|
| Qwen3 14B | 6/8 | 6/8 | 8/8 | 0 | 1 |
| Gemma4 12B | 6/8 | 6/8 | 8/8 | 0 | 1 |

Original pairwise labels did not change in **any of 16 model/case
comparisons**. The extra clarification consumed 640 more prompt tokens
across the two local models (+8.0% relative to the minimal condition);
runtime times varied with model warmup, not a reliable performance test.
No citations were invented or malformed in these 32 responses.

The preregistered development criterion failed: **holdout inference was
not run**. Raw completed model outputs remain create-only in four
run-development-*.json files. This is negative evidence for the **exact**
intervention, not proof that all semantic interventions fail.

## Two distinct evidence problems

**A. Published labels sometimes overstate what the supplied abstract says.**
Case 597:12779444 is labeled expert SUPPORT for a claim about decreasing
cervical-cancer *incidence*. Its published rationale describes falling
cervical-cancer *mortality* and models mortality trends, not incidence.
Both models judged the given excerpt insufficient. Treating those replies
as unambiguously erroneous conflates two distinct epidemiological
quantities. This is a documented *suspected source-to-claim reference
gap*, not an authorized change to published expert annotations.

Previously examined SciFact v1 case 343:5884524 is similarly labeled
SUPPORT for diabetic bleeding events, although the rationale enumerates
mortality, myocardial infarction, stroke and heart failure without
mentioning bleeding events. Case 1337:20231138 names a specific
ubiquitination site (PCNA K164) not actually spelled out in its published
rationale. The strength of any implicit entailment must be reviewed;
neither old gold label has been rewritten.

**B. A model can reject an actual biochemical implication.**
Case 636:24294572 is expert-labeled SUPPORT for PTEN converting
PI(3,4)P2 into PI4P. The designated source says PTEN is a PI(3,4)P2
**3-phosphatase**. By removing the phosphate at position 3, the
remaining phosphate is at position 4, giving PI4P.
Both local models classified this as CONTRADICTED under both prompts.
One model's recorded rationale specifically claimed the enzymatic
product would still contain the removed 3-position phosphate.

This biochemical inference has **external empirical corroboration**:
Goulden et al., *Journal of Cell Biology* (2019),
https://pmc.ncbi.nlm.nih.gov/articles/PMC6400549/
(figure 4 C/D directly tests PTEN-mediated PI(3,4)P2 conversion to PI4P).
Original source Malek et al., *Molecular Cell* (2017),
https://doi.org/10.1016/j.molcel.2017.09.024 .
These references make the observed local semantic error substantially
better supported than a mere model-vs-gold disagreement, without
certifying every claim in the dataset as world truth.

## Source identity and raw receipts

- Development Qwen minimal: run-development-qwen3-14b-minimal.json;
  SHA-256 62bbf3cfc5e6b1e9bb1d76dc215a1bb66011981e216e3fea222daae4fa3b822d.
- Development Qwen contrast: run-development-qwen3-14b-contrast.json;
  SHA-256 bb3061d87ef08651fcc72edcfb7d0e934288682eab48d207691b0cfedf68d25b.
- Development Gemma minimal: run-development-gemma4-12b-minimal.json;
  SHA-256 a055545b340506af2fb8bf9af51e2329c8199104f6228a63095d441f7deff30e.
- Development Gemma contrast: run-development-gemma4-12b-contrast.json;
  SHA-256 7c67f786762b9e0ad7ccf0a75ab9fbe91f209c4725c5ec42303eb69421e93b98.

Qwen digest bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8.
Gemma digest 6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b.
All original trial rows preserve the exact generated text, quoted span,
rationale, prompt/result hashes, token counts, duration and error status.

## Decision and limitations

1. **Do not ship this prompt addition** as a default or mandatory check.
2. Do not mistake the discrepancy in case 597 for a discovered model
   failure or unilaterally correct official external expert gold.
3. Preserve case 636 as an independently corroborated, small but concrete
   scientific reasoning fault to target in future source-disjoint tests.
4. A future useful test should distinguish published expert agreement
   from separately reviewed *excerpt entailment*, especially where
   source omissions, causal claims or biochemical transformations matter.
   It should measure erroneous refutation and missed refutation separately.
5. No normal ChatGPT interception/integration exists in this repository;
   this experiment made no claim to enforce ordinary chat answers.

This experiment is not a population performance estimate. The original
SciFact release is publicly available and may have been seen during model
pretraining; only 8 development items per model were evaluated.
The holdout was source-inspected by the operator but not model-tested.
No independent human reannotation was performed.
