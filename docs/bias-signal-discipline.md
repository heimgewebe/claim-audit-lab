# Bias-Signal Discipline

## Why this exists

Bias cannot be eliminated, and a self-declared bias confession (`bias-residue.yml`
style) is cheap: an author simply writes "I acknowledge possible bias" and the
gate opens. Worse, an agent can learn to *write so that no confession seems
necessary*.

This discipline does not claim to prevent bias. It makes bias **more expensive**.
Every one-sided relevance ordering, every threshold nudge, every finalizing
sentence on top of weak evidence leaves an *explanation-bearing signal* that the
author must answer before a case can be finalized.

The shift in axis: not "how do we make agents honest?" but "how do we build a
system where dishonesty leaves more artifact traces than honesty?"

## Invariants

1. **Generated before confessed.** Bias signals are derived mechanically from
   case artifacts first (`scripts/generate_bias_signals.py`). The author does
   not get to decide which signals exist.
2. **Signal is not guilt.** A bias signal is not proof of distortion; it is a
   declared *need to explain*.
3. **Response is not acquittal.** A response counts only when it points at
   concrete artifacts.
4. **`acknowledged` is not enough.** The response vocabulary deliberately
   excludes `acknowledged`, `noted`, `seen`, `handled`. These are methodological
   throw-pillows: comfortable, load-bearing of nothing.
5. **Finalization needs signal coverage.** No case finalizes while severe
   signals are unanswered or only rhetorically answered.
6. **Assessment language may not outrank evidence status.** Prose may not
   silently upgrade a claim above its structured `status`.

## Two artifacts, two roles

```
case artifacts
  -> _generated/bias-signals.yml      (machine-derived, never hand-edited)
  -> bias-response.yml                (manual answer, must cite artifacts)
  -> validator gate before finalization
```

### `_generated/bias-signals.yml`

A **derived** artifact. It lives under `_generated/` precisely so that nobody is
tempted to "just quickly fix" it. Generated files are like breadcrumbs in the
fairy tale: useful for finding the way, but you should not eat them yourself.

Produced by:

```
python scripts/generate_bias_signals.py cases --write
```

Committing it is optional. If it is committed, `--check` verifies it is current.
If it is absent, the response validator regenerates signals in memory.

Each signal carries a deterministic id:

```
bs_<sha256(case_ref + signal_type + affected_refs + observation)[:12]>
```

so a response stays attached to a signal as long as the signal means the same
thing.

### `bias-response.yml`

The **manual** answer artifact, one entry per signal the author chooses (or is
required) to answer.

Permitted `response_status` values:

| status | meaning | requires |
|---|---|---|
| `mitigated` | the underlying issue was changed | `mitigation_refs` (existing artifacts) |
| `accepted_with_constraint` | the issue stands but is bounded | `residual_risk` + `constraint_statement` + artifact ref |
| `false_positive` | the signal does not apply | rationale + at least one artifact ref |
| `escalated_to_redteam` | handed to adversarial review | `redteam_ref` to an existing red-team artifact |

Forbidden (rejected by schema): `acknowledged`, `noted`, `seen`, `handled`.

## Signal types (MVP set)

The generator starts with a small set of hard signal types.

| type | severity | fires when |
|---|---:|---|
| `relation_threshold_proximity` | 0.50 | a directional relation's numeric strength is within ±0.03 of a verdict threshold |
| `source_weight_asymmetry` | 0.60 | extreme source-weight asymmetry is not supported by a source-weight audit |
| `reported_claim_world_pressure` | 0.78 | reported evidence is used to support a world claim without argument-provenance |
| `redteam_pending_with_final_language` | 0.85 | structured lifecycle status is final while independent red-team verdict is pending |

Only structured indicators create mandatory signals. The historic schema retains
old lexical signal names so archived records remain readable, but the generator
does not produce `assessment_verdict_mismatch`, `comparative_claim_underframed`
or `counterhypothesis_understeelman` from words in prose.

An unsubstantiated strong claim can still be rhetorically misleading without
a mechanical signal. Structural validation is not a substitute for independent
substantive review.
## Validator gate

`scripts/validate_bias_response.py` runs in two modes, keyed off `lifecycle.yml`
`status`.

### Draft mode (`draft`, `contested`, `provisional_under_uncertainty`, `reopened`, ...)

- A missing `bias-response.yml` is allowed.
- A malformed `bias-response.yml` still fails (schema is binding everywhere).
- Generated signals are reported but do not block.
- A response to an unknown signal is a warning, not a failure.

Draft cases may carry open bias signals. That is the point: drafting is where
the work happens.

### Final mode (`assessed`, `final_under_uncertainty`)

1. Every `required_response: true` signal has a response.
2. Every response references an existing signal.
3. `mitigated` needs at least one existing `mitigation_refs` artifact.
4. `accepted_with_constraint` needs `residual_risk`, a `constraint_statement`,
   and an existing artifact ref.
5. `false_positive` needs a rationale and at least one existing artifact ref.
6. `escalated_to_redteam` needs an existing `redteam_ref`.
7. **Severe signals (`severity >= 0.75`) may not be merely accepted.** They must
   be `mitigated`, declared `false_positive`, or `escalated_to_redteam`;
   `accepted_with_constraint` is insufficient. A satisfied bias response does not
   by itself license finalization.

## What this does not do

- It does not certify the absence of bias.
- It does not re-score any case verdict.
- It does not replace the harder future path (blind-pair assessment, where
  different agents build the case, score relations blind, and write the
  assessment without source labels). Bias-signal discipline is the cheaper
  repo-MVP; blind-pair assessment remains the later, stronger path.
