# SciFact expert benchmark: development readback and holdout decision

Official SciFact release SHA-256 11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be, source-disjoint, 5 expert SUPPORT + 5 expert CONTRADICT + 5 cited/unannotated pairs per split, manifest SHA-256 727fed187d5d925d3c94ca640c7525cc2df73bb343053b656cc86e16a330e6be. All selection and original trial code were committed before model inference (c1146cf).

Development, published expert labels only:
- Gemma4 12B minimal: 9/10 gold matches, 10 valid expert outputs, 5/5 weak controls yielded insufficient.
- Gemma4 12B lab: 8/10 matches, 10 valid expert outputs, 5/5 weak controls yielded insufficient.
- Qwen3 14B minimal: 9/10 matches, 10 valid expert outputs, 5/5 weak controls yielded insufficient.
- Qwen3 14B lab: 8/9 matches **among 9 valid annotated outputs**, with one invalid verbatim quote among the 10 expert cases; 5/5 weak controls yielded insufficient. The original 7-row incomplete trial is preserved and its unchanged SHA-verified prefix was continued to 15 attempts after a documented *process-only* amendment. The valid expert denominator is 9, not 10, and the invalid quote is an observable separate model fault.

These development observations do not show any benefit from the longer lab prompt; no threshold/guard/prompt is changed. Cited unannotated samples are **not** expert-labeled NEI and cannot be counted as correct or incorrect neutral judgments.

**Pre-holdout decision:** evaluate the same unchanged minimal and lab prompts under both existing local models on all 15 disjoint holdout SciFact claim/doc pairs. Allow invalid model citation-format outputs to be counted and subsequent cases tried, but stop for provider errors; do not retry or overwrite any output. Only expert SUPPORT/CONTRADICT scores are evaluated as gold. Report raw counts with denominators, invalid outputs, support incorrectly refuted, missed explicit expert refutations and descriptive unannotated-citation outcomes.

Limits: SciFact expert judgments are not guarantees about the world; released corpus may have been encountered during training; 5 expert samples per class per split are too small to establish generalization; no source-authenticity or human reannotation claim.
