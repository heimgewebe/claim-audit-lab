# Ungültiger erster Testlauf – nicht als Lab-Messung verwenden

Die erste Harness-Version übergab den Fallordner selbst an die CLI. Mindestens `validate_case_references.py` durchsucht jedoch nur Unterordner und meldete deshalb bei einem manipulierten Quellverweis fälschlich Erfolg ohne Prüfung (`No case directories found`). Die ursprüngliche JSON-Ausgabe bleibt als Fehlerbeleg erhalten, zählt aber **nicht** zur gültigen Auswertung. Der korrigierte Runner verwendet den Elternordner und prüft die tatsächliche Fallentdeckung. Die vorregistrierten Mutationen und Erwartungen wurden nicht geändert.

---

# Claim-Audit-Lab adversarial fitness test

Source commit: a4889a38c7b9633ab89a80677689cfb1624214dd
Production validators per case: 33

| Lane | Detected / passed desired outcome | Cases | Rejected | Accepted | Errors |
|---|---:|---:|---:|---:|---:|
| valid_control | 4 | 4 | 0 | 4 | 0 |
| structural_fault | 7 | 9 | 7 | 2 | 0 |
| semantic_canary | 0 | 3 | 0 | 3 | 0 |

| Case | Expected | Observed | Rejecting validators |
|---|---|---|---:|
| valid_baseline | accept | accept | 0 |
| valid_quoted_consensus | accept | accept | 0 |
| valid_absence_negation | accept | accept | 0 |
| valid_source_relabel | accept | accept | 0 |
| orphan_claim_source | reject | accept | 0 |
| orphan_claim_evidence | reject | reject | 1 |
| orphan_evidence_source | reject | reject | 1 |
| orphan_evidence_claim | reject | reject | 1 |
| orphan_relation_claim | reject | reject | 1 |
| missing_weight_audit | reject | reject | 1 |
| premature_established | reject | reject | 2 |
| receipt_status_mismatch | reject | reject | 2 |
| missing_redteam | reject | accept | 0 |
| contradictory_event_time | reject | accept | 0 |
| contradictory_count | reject | accept | 0 |
| rhetorical_certainty_laundering | reject | accept | 0 |

Structural controls measure reference and artifact integrity, not factual truth.
Semantic canaries have predeclared elementary contradictions or overclaiming. An accepted semantic canary is a measured limitation, not a hidden success.
Benign controls measure false alarms due to wording. Do not add word blacklists or a mandatory quality gate based on this exploratory test.