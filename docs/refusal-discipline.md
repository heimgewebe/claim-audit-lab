# Refusal Discipline

## Principle

**Refusal is not neutrality.** A refusal or inability to assess a claim must be
made explicit in the structured answer receipt, with its actual scope and reason.

An answer's words cannot establish whether the model refused, why it refused,
or whether an argument is well supported. There are **no banned phrases** and
no topic- or politics-triggered automatic failure.

## Structured declaration

The `refusal_check` field records `refused` and, when relevant,
`refusal_type`. Supported types:

- `out_of_scope`: a repository-navigation/maintenance task, not a world claim.
- `missing_tools`: a provisional answer without the needed external tools;
  `refused=false` and `external_research.tools_used=[]`.
- `missing_evidence`: an unresolved or `no_verdict_possible` claim;
  `refused=false` and a matching verdict.
- `capability`: an actual capability limit, declared as `refused=true`
  if the relevant operation could not be performed.

If `balanced_framing_present=true`, the receipt records which burden layers
have been addressed; the value is not inferred from idioms or word choice.

## What the validator checks

`scripts/validate_refusal_discipline.py` verifies the declared type and
`refused` consistency, unresolved verdicts for missing-evidence assessments,
missing-tools declarations, and the structured burden-layer requirement.
It does **not** search answers for prohibited expressions or infer intent
from words like "political", "controversial", or "cannot evaluate".

Misclassified, undisclosed, or selectively treated refusals remain substantive
audit questions for an independent reviewer. Passing the structural validator
is **not** a guarantee that an answer was candid or unbiased.
