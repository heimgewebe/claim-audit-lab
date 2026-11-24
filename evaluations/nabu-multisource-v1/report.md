# Nabū multi-source evidence synthesis — 24 actual target-model calls

**Decision:** No scientific fine-tuning or prompt promotion is justified by
these screens. The stronger target model gives all 23 completed judgments
correctly; one further response is truncated at the generation cap, with a
correct initial label and an unfinished explanation. No recurring
substantive error across distinct source families has been established.
Do not manufacture training targets from this near-ceiling result.

## Protocol and actual model

The frozen scripts perform two sequential, separate single-turn German
evidence-synthesis screens, not a multi-turn dialogue or a source-revision
runner. They were frozen before their respective inference series:

| Screen | Runner SHA-256 | Created UTC |
|---|---|---|
| Synthetic | ac40b87384e3ba87220b68078c73e18b69ea2b496a93d0c66f551ce5ac9cd41e | 2026-11-24 20:26:54 |
| Original abstracts | eadc121fe27d7586e128564d0a54365c7dc2a9bfa3c5b1dd8cab42411e49362a | 2026-11-24 20:34:27 |

Live HA configuration at start and local Ollama /tags identified
`nabu-qwen38-q3-text-renderer35:20261124`, Qwen3.8-27B Q3_K_M,
digest `b6568abff17dd9045931cc29ca50fce45ab372ab55656961b0bd328b6068ba72`.
Both use temperature 0, thinking enabled, 16,384 context and 1,536
generated-token cap. Local identity is checked before each call, with
no forced eviction of another loaded model. Natural German response,
no required quotation or JSON output. Only final responses, token counts,
hashes and thinking lengths are stored. No raw reasoning, private messages,
tools, service/weight/config mutations or training.

The target is the actual deployed model, **not** the complete production
HA system prompt, conversation history, tools, retrieval, voice pipeline,
or authenticated user path. No direct comparison with previous smaller
models on these same cases was made.

The synthetic trial contains four constructed three-state families:
aggregation (including Simpson's paradox), conflicting and dependent
measurements, controlled vs observational causation, and incomplete
operating records. The twelve claims are framed at object level or as
explicitly checkable comparisons, not ambiguous claims about whether a
study established causation. Each family has one supported, contradicted
and undecided reference.

The original trial contains twelve operator-authored German claims in four
topic-disjoint families from ten unmodified SciFact abstracts. The papers
were selected purposefully to raise difficulty after the synthetic result.
None of the ten documents appeared in the earlier listed SciFact trials,
though related topics have appeared. The reference labels are NOT original
SciFact expert annotations, an independent human gold standard, or a
reserved adapter holdout. The model sees the actual source excerpts and
claim, not the expected label/rationale. Pinned SciFact release SHA-256
`11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`;
Wadden et al., EMNLP 2020, https://github.com/allenai/scifact, and S2ORC
abstracts ODC-By 1.0. See ../scifact-expert-v1/README.md. Historical
source-relative judgments are not current clinical advice.

## Results

| Metric | Synthetic | Original abstracts |
|---|---:|---:|
| Requests attempted | 12 | 12 |
| Complete final answers | 12/12 | 11/12 |
| Complete correct labels | 12/12 | 11/12 |
| Observed wrong labels on complete answers | 0 | 0 |
| Truncations | 0 | 1 |
| Provider/context failures | 0 | 0 |
| Prompt tokens | 3,086 | 17,667 |
| Generated tokens incl. thinking | 7,481 | 12,029 |
| Median request seconds | 22.335 | 35.445 |

The offline scorer rederives every case, source hash, prompt hash, final
response hash, model identity and parsed label, and checks complete case
grids. The original abstract source text is reconstructed from the pinned
archive. All 24 rows passed reconstruction. Scientific reason quality was
read manually; the automatic score only measures complete label agreement.

### Manual substantive review

Synthetic:
- Aggregation: computes the correct subgroup rates (5 vs 10 and 30 vs 40
  in the supported case, 10 vs 5 and 50 vs 40 in the contradicted case).
  Correctly refuses to infer both subgroup rates from pooled data alone.
- Measurement: correctly applies error bounds and calibration; does not
  resolve conflicting independent measurements with no calibration evidence
  by simply counting the duplicated report as a new measurement.
- Causal: recognizes the temperature-change confound; gives the controlled
  randomized result precedence for the separate coating effect.
- Completeness: distinguishes a confirmed counterexample (one station
  continuously operating) from a missing station log.

Original abstracts:
- Prenatal: correct direction of the three birthweight association estimates,
  and correct distinction between a reported twin-status point estimate below
  1 and a heterogeneous increased-risk finding. The answer on possible
  overlapping primary studies starts OFFEN and correctly notes the absent
  study lists and overlapping publication windows; it is cut off mid-sentence.
  It is not scored as a passed judgment and was not retried.
- Heritability: correctly distinguishes individual-specific environment from
  shared childhood environment and refuses to infer the outcome of an untested
  dietary intervention. Correctly reads the twin/adoption observations.
- Screening: distinguishes fewer detected cancers from disease-specific
  mortality, and isolated CIN3 (CI includes 1) from combined endpoints and
  CIN3-or-worse. These are exact endpoints in the supplied abstracts, not
  a general recommendation for patients.
- Mechanism: preserves the directions of the IL2RA associations and
  recognizes that genetic/cellular findings do not establish a therapeutic
  intervention's effect on incidence.

There are nuances worth improving in natural speech without treating them
as label errors: some statements about certainty are too absolute; e.g.
"verbleibende Unsicherheit besteht nicht" in heritability-s is justified
only about the explicitly reported comparisons, not their world-truth.
The causal-c reply describes the uncontrolled observed decline as a
contradiction to the controlled positive effect; these are different
estimands and can coexist. In measurement-i, loss of the sample prevents
repeat weighing but does not logically exclude all future evidence.
In screening-i, lack of a mortality result in the supplied abstracts does
not independently prove mortality was never measured. None changes the
decisive source-relative verdict in the case; these observations are
not evidence of a broad or recurring label-level deficit.

## Interpretation and next decision

Across the first target-model baseline and these screens, no repeated
unambiguous semantic deficit sufficient to justify a new QLoRA adapter
has been demonstrated. Strong performance on a small, constructed
or purposefully selected sample does not establish general scientific
competence, independent research, political neutrality, resistance to
misinformation, long-context reliability or revision after evidence changes.

The next high-value test should use substantially less explicit evidence
in an authentic research question and test actual source retrieval,
selection, and calibrated synthesis, with independently checked reference
evidence. Separate provenance, selection, interpretation, conflicting
evidence and revision. Use original sources, not model-generated
fabricated evidence. A previous proposed dialogue runner was refused
before creation and remains unexecuted; this new experiment is a
different single-turn question, not that refused operation.

The existing Qwen3.8-27B training infrastructure and adapters remain
available. Do not spend GPU time on more SFT solely to make the model
sound scientific. Train only on a concrete failure mechanism not corrected
by simpler changes, and evaluate a new independent source-family-disjoint
holdout plus existing Nabū regression cases before any activation.

## Original evidence and reproduction

| Result | SHA-256 | Completed Grabowski task |
|---|---|---|
| run-synthetic.jsonl | fd88eb7574c444aa23fef63efa791990703e0f59ccc73f92849a053a71250804 | 3e75a474b55849f786d5db1b |
| run-scifact.jsonl | d280a515c1ca84743a9871d3fb55142e5734378ce5eb6391ecbc526ed6c98677 | f57936a738d640ae8c558800 |

Lifecycle receipts: synthetic
`407abc6b292e9118fc600b42884ee8f5cad9eaac69e26067bdfe9fdc9307d4bd`;
original
`1f9c78edf7ccc130fbbbc23662c5f0b0fdc78f03d86bc27954e62c7e0640d63d`.
All four original files copied byte-identically. Reproduce offline with
`python3 evaluations/nabu-multisource-v1/score.py --repo . --archive /path/to/pinned-scifact-release.tar.gz`
with Python assertions enabled. No model inference is made by the scorer.
