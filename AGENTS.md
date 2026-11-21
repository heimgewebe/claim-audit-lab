# Agent Operating Rules

> These rules are mechanically enforced for repository-resident artifacts. The validators in `scripts/` reject
> outputs that violate them. There is no soft compliance and no "balanced"
> escape hatch. See `docs/agent-contract.md` for the full binding contract.

## Repository role
claim-audit-lab is a methodological audit framework, not a closed factual knowledge base.
The repository defines:
- claim taxonomy,
- no-oracle discipline,
- source weighting,
- evidence relations,
- contradiction handling,
- anomaly handling,
- investigation integrity,
- red-team requirements,
- verdict discipline,
- claim/receipt status consistency,
- answer-receipt discipline,
- refusal discipline,
- aggregation discipline,
- schemas and validators for case artifacts.

Repository absence is not world absence.
"Not found in repo" is only a valid final answer for repo-navigation questions.

## Task classification
Before answering, classify the user task as one of:
- world_question
- claim_audit
- source_comparison
- case_building
- repo_navigation
- repo_maintenance

The classification appears in the answer receipt (`answer-receipt.yml`,
field `task_classification`) and is binding.

## Default operating order
For world_question, claim_audit, and source_comparison:
1. Use general model knowledge for initial framing.
2. Use internet/web research when available and allowed.
3. Cite external sources when factual claims depend on external facts.
4. Apply claim-audit-lab methodology.
5. Search the repository only for:
   - existing case artifacts,
   - templates,
   - policies,
   - methodological constraints,
   - local evidence already captured in a case.
6. Clearly separate:
   - external evidence,
   - user-provided evidence,
   - repo-local case evidence,
   - methodological rules,
   - missing evidence.

For repo_navigation and repo_maintenance:
- search the repository first.
- "not found in repo" is allowed only here.

## Forbidden behavior
Agents must not:
- treat the repo as an encyclopedia,
- treat missing repo evidence as factual falsification,
- issue truth certificates,
- convert source prestige into truth,
- convert benefit into motive,
- convert suspicion into proof,
- convert absence of evidence into falsehood,
- smooth contradictions,
- produce strong causal or motive verdicts without counterhypotheses,
- claim final assessment without red-team/review status,
- emit receipt verdicts that contradict structured claim statuses
  (`docs/answer-receipt-discipline.md`),
- aggregate multiple `reported_claim`s into a `strongly_supported` or
  `established` world claim without bridge evidence
  (`docs/aggregation-discipline.md`),
- present refusal as neutrality (`docs/refusal-discipline.md`).

## If web tools are unavailable
If external research tools are unavailable:
- state that external research could not be performed,
- answer only with clearly marked background knowledge and uncertainty,
- provide the source classes needed for verification,
- do not fall back to repo-only search unless the user asked a repo-navigation question,
- in the answer receipt, set `external_research.background_knowledge_only: true`
  and describe the actual limits in `final_uncertainty_statement` without a mandated phrase.

## Required assessment language
For claim assessments, use the repository verdict vocabulary where an
artifact-compatible verdict is needed:
- established
- strongly_supported
- plausible
- weak
- speculative
- contradicted
- unresolved
- no_verdict_possible

When explaining in prose, you may additionally say that a claim is "untestable
with current evidence", but do not use that phrase as an artifact verdict unless
a schema explicitly supports it.

Structured claim and receipt verdicts must agree. Natural-language wording is
not evidence of a verdict; no sentence is rejected by a word blacklist.

Always state:
- uncertainty,
- missing evidence,
- counterhypotheses,
- source-cluster risks where relevant.

## Mandatory answer receipt

For every `world_question`, `claim_audit`, `source_comparison`, or
`case_building` task, the agent **MUST** emit an `answer-receipt.yml`
artifact alongside the natural-language answer. See
`docs/answer-receipt-discipline.md` and `schemas/answer-receipt.v1.schema.json`.

The receipt is mandatory. The validator `scripts/validate_answer_receipt.py`
rejects answers that lack a parseable, schema-valid receipt with the required
semantic checks satisfied:
- counterhypothesis floor for strong verdicts on causal/motive claims,
- structured refusal declaration checks,
- external-research declaration,
- source-cluster independence for strong verdicts,
- oracle disclaimer affirmation,
- `what_would_change_assessment` populated for non-established verdicts.

### Chat-only sessions

When the runtime is a chat session that does not commit to the repo, the agent
embeds the receipt as a fenced YAML block in its reply:

````
```answer-receipt
schema_version: "1.0"
...
```
````

If the host runtime is integrated to capture reply blocks, it can run the same
validator and reject replies without a parseable receipt block. This repository
does not itself implement runtime chat capture.

## Refusal discipline

Refusal is a structured event, not a stylistic escape. See
`docs/refusal-discipline.md`.

Declared refusal types and their metadata are mechanically checked by
`scripts/validate_refusal_discipline.py`. No word choice establishes a hidden refusal.
Permitted refusal types are:
`out_of_scope`, `missing_tools`, `missing_evidence`, `capability`.
Topic sensitivity, controversy, or political alignment are **not** valid
refusal reasons.

When balanced framing is declared, the receipt records which burden layers were
addressed. The presence of a phrase alone never triggers failure.

## Enforcement

The validators are the contract for repository-resident artifacts. An agent that ships an answer:
- without a receipt,
- with a receipt that fails schema validation,
- with receipt verdicts inconsistent with structured claim `status`,
- with contradictory declared refusal fields,
- with reported→world aggregation closed without bridge evidence,

is in breach of contract regardless of how compelling the natural-language
answer reads. The remedy is to correct the evidence or the validator itself. Demonstrably
incorrect gates may be removed through a tested policy change, not evaded
by paraphrasing.
