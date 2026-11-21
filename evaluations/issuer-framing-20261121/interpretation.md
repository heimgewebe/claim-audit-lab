# Interpretation after observing the responses

This note was written **after** the preregistered model runs. The original hypotheses, model prompts, output format and sampling order were committed first (protocol commit `abbe49decc53591d883919c60c59d12385d6e62e`).

## Measured result

- All **16/16** sessions returned valid structured answers.
- **8/8** matched issuer pairs have complete, independently generated responses.
- **1/8** matched pairs changed the categorical causal verdict.
- Largest paired numerical support difference: **10 points** on the 0–100 causal-support scale.
- Pooled signed issuer-A-minus-B difference: **−0.25 points**. This is merely descriptive: "A" represents different kinds of institutions in different scenarios.
- All strong randomized positive cases remained `strongly_supported` with scores between 95 and 96. All randomized near-null cases remained `unsupported` with scores between 5 and 8.
- The only category change occurred in the nonrandom waiting-time scenario: government issuer `unsupported` / 20 versus civic issuer `plausible` / 30 in the first repetition. Both answers gave essentially the **same** causal caveat: nonrandom allocation, unknown selection, unknown prior trends and confounding. In the second repetition, both issuers received `plausible` (government / 30, civic / 25).

The **government-labeled arm itself changed category between repetitions**, so the single flip cannot responsibly be assigned to issuer identity. It is also consistent with categorical threshold or sampling variability. The score differences do not show a consistent direction across repeated pairings.

## What can and cannot be concluded

**Supported:** In these fictional cases, GPT-6 Astra distinguished randomized positive evidence from randomized near-null data, and its explanatory cautions remained similar under different issuer labels. Its classification was less stable around the nonrandom evidence boundary.

**Not supported:** A claim that government sources are systematically favored, opposition sources are systematically suppressed, there is zero institutional bias, or that the model's outputs are empirically calibrated truth probabilities.

These are synthetic prompts from **one model provider**, with two repetitions per label and no live source verification. Numeric scores were explicitly defined as *support for causality*, not confidence in an unsupported label. The A/B attribution is exact within each pair, but random sampling and subtle real-world institutional credibility effects remain unresolved.

## Practical next decision

The pilot produced a usable, audited negative result for a broad claim of obvious issuer effects, together with a small classification-instability finding. **Do not activate a new mandatory bias gate** on this basis. A later test should include an independent provider and larger counterbalanced sample if the objective is to identify more subtle or systematic shifts. Until that is possible, source-aware review remains more useful than adding automated language rules.

Raw prompts, verbatim answers, run order, parsed scores, success/failure outcomes and their SHA-256 values are in `results.json`. The file SHA-256 is `7192e5256b5e5bc466cff676705674c47d9b5def836213690849a19f746dfbb9` (calculated locally after the pilot).


## Review corrections after data collection

GitHub code review identified two exception-handling defects in the experiment
runner: non-string status values could crash parsing, and timed-out processes
could lose already captured partial output. Those **failure-path** cases were
repaired with no-network regression tests **after** the 16 completed sessions.
The original preregistration is retained as commit
`abbe49decc53591d883919c60c59d12385d6e62e`, and the first outcome
commit remains `dc0c9847f82bb28766b7aac118b5dd9de60cf080`.
No prompts, model answers, run order, scoring scheme or result objects were
regenerated or silently changed by these follow-up corrections.
