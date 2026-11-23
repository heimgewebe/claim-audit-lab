# Decision before holdout: STOP

This file records the decision *after* the development attempts and *before*
any holdout inference. The six-pair paper-disjoint selection and exact method
were committed in d7d49d9 before either model was called.

## Observation under the preregistered, strict source-span validator

- Qwen3 14B: 3/3 development pairs attempted, 15 inference calls,
  8 valid, 7 invalid_output due to nonverbatim/noncontiguous source spans,
  no provider/context failures.
- Gemma4 12B: 2 complete pairs and an attempted first turn for the third,
  11 inference calls, 3 valid, 7 invalid_output due to source spans,
  1 generation_truncated (a runaway line-break sequence, not an evidence
  classification and not a cloud-provider failure). No remaining calls
  after that termination.
- Across both models: 26 actual calls, 11 fully valid responses,
  14 invalid evidence quotations, 1 incomplete generation. The exact
  model-generated responses and hashes are retained without retry.
- Among the ten paired baseline-versus-revision comparisons with both
  calls attempted, only 4 fresh baseline judgments and 3 sequential
  revised judgments were *fully valid and expert-matching*. Those raw
  counts do not establish a scientific benefit.

**The preregistered development success criterion (>=2 additional
fully valid, expert-matching revised answers with no extra false
refutations, invalid quotes, or inappropriate control changes) FAILED.**

Holdout trials were **not started**. The three holdout pairs remain frozen
but unscored by models. No core citation parser, default prompt, merge gate,
service, or required ChatGPT receipt is changed.

## Explicitly post-hoc descriptive analysis, not a new success metric

For the ten fully attempted revision directions, the raw JSON fields
contained the correct *label* in 10/10 revised answers versus 8/10
fresh independent answers, despite the majority of revised evidence_span
fields failing exact provenance. This is a narrow exploratory observation
and must NOT be described as the preregistered 10/10 scientific success.

One Qwen control changed its raw label from supported to insufficient
with unchanged evidence and an irrelevant administrative note (its first
answer had a quote-format failure). This is a warning about unnecessary
opinion changes; it cannot be erased from the evidence.

Invalid quotes are not all fabricated claims: with native LaTeX and HTML
tables, rendered human-readable text can differ literally from source
markup, including HTML entity encoding, line-break commands, and joined
rows. Strict byte-bound citation rejection was correct by the existing
contract, but formal validity by that contract and semantic correctness
must remain separate. A correct future benchmark should bind a faithful
display/normalization mapping to original source bytes and test it
separately, not silently loosen the old checker.

**Scientific inference:** There may be a signal of source-sensitive
semantic revision in raw labels; reliable source-quoted output and a
scientifically justified general effect have NOT been demonstrated.
A further experiment on genuinely new papers with an independently
audited presentation is needed before practical use.
