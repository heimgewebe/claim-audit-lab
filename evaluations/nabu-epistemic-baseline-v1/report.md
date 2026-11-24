# Nabū epistemic baseline: first target-model experiment

**Decision:** Do not promote the relational prompt or start fine-tuning from
these cases. The frozen screening rule failed; two operator-authored reference
labels have a material scope ambiguity. Preserve the observations and test
unambiguous object-level claims before choosing training examples.

## Protocol and evidence

The target was the actual Home Assistant Conversation model, not the former
Gemma 4 12B / Qwen 3 14B proxy models:

- Ollama tag `nabu-qwen38-q3-text-renderer35:20261124`.
- Model digest `b6568abff17dd9045931cc29ca50fce45ab372ab55656961b0bd328b6068ba72`.
- Qwen3.8-27B, Q3_K_M, thinking enabled, context 16384, temperature 0,
  generation cap 1536, JSON output, independent local /api/generate requests.
- This is direct inference on the actual model and matched context/thinking,
  NOT the complete Home Assistant system prompt, tool list, voice pipeline,
  authenticated conversation path or a device-action test.
- The active alias and context/thinking binding were freshly observed before
  the run. Each call checked the local model digest and did not evict another
  loaded model. No production configuration, weights or adapter changed.

Frozen runner SHA-256
`cd088865f4891a6d7ebc10fa669522305196b7555396ba1e5a81f6fd12cc4269`,
created 2026-11-24T17:53:10Z. Task
`053d14a4a9a84a35bf05ae1f` completed successfully, lifecycle receipt
`4c812a7fac6790e1f7950e9a81c6bd96bd76289281ea8892296cf1c86e54214e`.
Original result SHA-256
`3e93a9949894612c3277eda6811ed7354f0a0e025e2e0cd3745520750689565f`.
The run header includes the exact prompt instructions, source excerpts,
claims, reference labels and source hashes. The original final responses
and provider-response hashes are preserved; no private user messages or raw
model thinking are stored.

Four previously unused public SciFact abstracts were selected from the eight
deterministically hash-ranked eligible documents before inference.
The claims and reference labels were authored by the operator, not SciFact
expert gold. Eight explicitly fictional cases form four paired evidence
families: causation, institutional interests/intent, historical records and
quantity/entity binding. No actual political person or event is asserted.
Original sources: Wadden et al., EMNLP 2020,
https://github.com/allenai/scifact; S2ORC abstracts ODC-By 1.0; see
../scifact-expert-v1/README.md. Pinned archive SHA-256
`11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`.

## Frozen comparison

Both arms receive the same complete claim, unchanged excerpt, model and
inference budget. The second arm adds a short relational/scope instruction.
Twenty-four responses completed with no provider errors, truncation, or
citation parser rejection. All source, prompt, model and response identities
and parser outcomes were recomputed offline.

| Metric | Minimal | Relational |
|---|---:|---:|
| Valid JSON and exact quote | 12/12 | 12/12 |
| Correct according to frozen operator labels | 10/12 | 9/12 |
| Raw-label agreement | 10/12 | 9/12 |
| Real abstract cases correct | 4/4 | 4/4 |
| Fictional cases correct | 6/8 | 5/8 |
| New false contradiction (frozen labels) | — | 1 |
| Prompt tokens | 3005 | 3737 |
| Generated tokens incl. thinking | 6013 | 6939 |
| Median call duration | 18.97 s | 19.655 s |

The frozen gate requires at least two more correct raw and strict judgments,
no new raw error, no lost explicit contradiction and no worsening of
evidence relevance. The gate **fails**. No general conclusion about the
model population or all possible prompts follows from twelve cases.

## Post-observation annotation audit — preserve the original scores

Two intended insufficient cases, cause-a and interest-a, were drafted as
meta-claims ("the study establishes that ..." / "the investigation
establishes that ..."). Both arms instead returned contradicted, explicitly
reasoning that the excerpt does not establish the causal effect or the
actor's deliberate withholding. This reasoning is defensible as an assessment
of the proposition about proof, rather than the underlying event itself.
The intended insufficient labels would be clearer for object-level claims
"The program caused the reduction" and "The vendor deliberately withheld
the report". Do not silently alter the frozen gold, treat these four
responses as established semantic mistakes, or use them as supervised
negative examples.

A separate sensitivity analysis, excluding the two ambiguous cases
entirely, gives minimal 10/10 and relational 9/10. This is post-hoc and
not a revised acceptance rule. The negative prompt comparison stands.

The remaining distinctive regression is interest-b in the relational arm:
the source contains an authenticated explicit instruction plus evidence of
implementation, but the response rejects the claim because the source is
fictional. The minimal arm correctly reasons within that scenario. This
is a scope/context issue in this constructed test, not evidence of political
bias or an inability to reason about real institutions.

Both arms give the correct labels on all four real abstracts and on the
quantity-binding and historical-agreement pairs. The model preserves the
specific comparator in the observational ovulation/pregnancy example and
does not extrapolate the Stentor finding to human neurons.

Citation validity is not full evidential adequacy: on 42693833 both
responses correctly explain both sides of the reciprocal loop, but each
selects a quote covering only one side. Minimal cause-b quotes randomized
allocation but omits the outcome from the selected span. Thus even this
near-ceiling semantic screen does not establish complete evidence linkage.

## Consequence for Nabū training

This experiment establishes an actual target-model baseline, not a
trained adapter or an improvement in scientific competence. Earlier Nabū
tool/dialog QLoRA v2 had no matched semantic advantage (25/26 vs 25/26),
so there is no justification for another training run merely because a
training pipeline is available.

Next discriminating test: new, explicitly scenario-relative **object-level**
German claims, direct natural-language conversation, and genuine source
replacement after the model's own initial response. Compare revised answers
to independent replacement-only answers. Include all three transitions
support, contradiction and insufficient, with comparable source difficulty.
Separate semantic errors, omissions, format, and thinking truncation.
If repeated substantive errors remain after the simplest scope correction,
derive narrowly targeted, checked training examples and freeze source-family
disjoint evaluation before SFT. Never train on ambiguous frozen labels or
the evaluation cases. Use the existing pinned Qwen3.8-27B NF4/QLoRA
Block-Swap infrastructure, then compare adapter off/on and regress Nabū's
existing tool/dialog abilities; no mandatory runtime change absent
demonstrated benefit.

A proposed follow-up dialogue runner was rejected by the tool safety
boundary before file creation (absence verified). No follow-up inference or
training result is asserted and the refused call was not circumvented.
