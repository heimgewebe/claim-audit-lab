# SciFact contrastive interpretation: preregistered bounded experiment

**Purpose:** Test whether one precise clarification of subject, predicate, negation and comparison direction reduces demonstrably missed expert contradictions without promoting unsupported claims or false refutations. This is an **opt-in experiment**, not a new default instruction, validator, gate or claim of world truth.

**Observed development motivation (already seen, not new holdout):**
- SciFact 1088:37549932: an intervention *removes* BCL-2 and causes leukemic cells to disappear, while the claim ambiguously credits its *silencing* with tumor maintenance. Some local judgments mistakenly treat BCL-2 necessity as support for silencing promoting growth.
- SciFact 759:1805641: the claim compares ACT with nongametocytocidal drugs; one model cited a favorable ACT result and overlooked the abstract's more favorable long-prophylaxis comparator.
- SciFact 343:5884524: the claim concerns *bleeding events*, but the expert-cited abstract sentence reports mortality and cardiovascular outcomes instead. SOURCE-TO-CLAIM SUPPORT is not established by that sentence. The canonical expert label is retained; this is a disputed source-level reference, not permission to overwrite gold.
- SciFact 1337:20231138: the published rationale mentions PCNA ubiquitination, UBC13 and K63-linked chains but not the claim's site-specific PCNA K164 statement. This is another plausible expert-reference entailment gap. Neither case is a ground-truth correction.

**Intervention (frozen before model calls):** Same published minimal prompt and same structured source-span validator, plus exactly:
> Before labeling, check the claim's precise subject, predicate, negation, and comparison direction against the excerpt. Mentioning the same topic or an effect on a related outcome is not by itself support.

**Dataset and provenance:** Official SciFact release, SHA-256 11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be. The runner selects 4 expert SUPPORT + 4 expert CONTRADICT pairs for development, and the same for holdout. Selection uses deterministic SHA ordering with seed 2026112202, excludes **all 30** previous SciFact v1 claim and document identities and enforces unique claim and document identities within this new sample. Commit manifest, protocol and code **before** any model inference. No missing annotations are treated as expert NEI gold. Source and model prompt/response hashes are recorded.

**Procedure:** Same Qwen3 14B and Gemma4 12B local Ollama backends at temperature 0, with explicit proxy exclusion, native model/digest verification, no context truncation and exact contiguous citation checking. Randomized source order fixed across the two prompt arms, separate files per model/split/arm. Development for all four conditions first; record decision before untouched holdout. Failed model responses stay separate from semantic disagreements, and no overwritten/retried trials.

**Development criterion:** Proceed to holdout only if contrast corrects at least one additional published expert label across the two models without increasing false contradictions, missed contradictions or invalid quotations. Otherwise stop; record negative evidence and do not change defaults.

**Holdout criterion:** A plausible *candidate* requires a net gain of at least 2 correct expert judgments across both models (16 comparisons per arm), with no increased missed annotated refutations, false refutations or invalid citations. A tiny selected sample cannot warrant mandatory use even if it passes; a second independent replication or real user-level A/B evidence would still be needed.

**Limits:** Published expert labels are source-level annotations, not verified world truth; some source/annotation mismatches have already been observed. SciFact is public and may be in model pretraining. This experiment neither measures sequential belief revision nor validates ordinary ChatGPT capture. Time and token costs count against practical value.
