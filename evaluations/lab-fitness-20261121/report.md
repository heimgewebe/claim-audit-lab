# Claim-Audit-Lab adversarial fitness test

Source commit: 017b644b07f7cb193e80f8d79f58062ff139ba6f
Production validators per case: 33

| Lane | Detected / passed desired outcome | Cases | Rejected | Accepted | Errors |
|---|---:|---:|---:|---:|---:|
| valid_control | 4 | 4 | 0 | 4 | 0 |
| structural_fault | 9 | 9 | 9 | 0 | 0 |
| semantic_canary | 0 | 3 | 0 | 3 | 0 |

| Case | Expected | Observed | Rejecting validators |
|---|---|---|---:|
| valid_baseline | accept | accept | 0 |
| valid_quoted_consensus | accept | accept | 0 |
| valid_absence_negation | accept | accept | 0 |
| valid_source_relabel | accept | accept | 0 |
| orphan_claim_source | reject | reject | 1 |
| orphan_claim_evidence | reject | reject | 2 |
| orphan_evidence_source | reject | reject | 2 |
| orphan_evidence_claim | reject | reject | 2 |
| orphan_relation_claim | reject | reject | 1 |
| missing_weight_audit | reject | reject | 1 |
| premature_established | reject | reject | 2 |
| receipt_status_mismatch | reject | reject | 2 |
| missing_redteam | reject | reject | 1 |
| contradictory_event_time | reject | accept | 0 |
| contradictory_count | reject | accept | 0 |
| rhetorical_certainty_laundering | reject | accept | 0 |

Structural controls measure reference and artifact integrity, not factual truth.
Semantic canaries have predeclared elementary contradictions or overclaiming. An accepted semantic canary is a measured limitation, not a hidden success.
Benign controls measure false alarms due to wording. Do not add word blacklists or a mandatory quality gate based on this exploratory test.
