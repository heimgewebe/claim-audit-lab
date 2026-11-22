# Pre-amendment development run: preserve an evidence-format failure

Scientific source: AllenAI SciFact dev claims and abstracts, verified archive SHA-256 11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be. The deterministic 30-pair manifest was committed *before* all model calls in c1146cf; manifest SHA-256 727fed187d5d925d3c94ca640c7525cc2df73bb343053b656cc86e16a330e6be.

Original development arms (10 annotated expert gold pairs plus 5 unannotated cited controls per arm):
- Qwen3 14B minimal: 15/15 valid, 9/10 expert matches; five weak controls yielded insufficient (not a measured NEI accuracy).
- Gemma4 12B lab: 15/15 valid, 8/10 expert matches; five weak controls insufficient.
- Gemma4 12B minimal: 15/15 valid, 9/10 expert matches; five weak controls insufficient.
- Qwen3 14B lab: **7 attempted, 6 valid, 8 never attempted**. On expert CONTRADICT pair 42:18174210 the model emitted a plausible contradicted judgment but joined two genuine evidence sentences with an ellipsis in a single alleged verbatim span. The strict contiguous-quote parser correctly rejected this fabricated composite quote as invalid_output. This is **not** a zero-percent model reasoning result, and the trial remains incomplete.

Small *post-observation process amendment proposed*, not a gold or prompt change: continue subsequent claims after an invalid_output response and count all such invalid citations explicitly; abort only on non-parser backend errors. Resume the incomplete Qwen lab run from its immutable prefix, without rerunning previously observed cases. Persist resumed output separately, linked by exact SHA, and do not pretend the continuation was a first untouched trial. Only after committing this amendment should the untouched holdout be evaluated.

All original output JSON files are preserved create-only, with response and prompt hashes. No prompts, gold labels, source excerpts, or core checker rules are modified.
