# Source excerpt → claim semantic shadow assessment

One model; precommitted editor-curated labels, **not independent expert annotations**.
No web access was granted to the reviewer and these judgments do not certify
the authenticity of the cited web pages or factual claims outside each excerpt.

- Model: gpt-6-astra; seed: 20261121
- Valid responses: 0/18
- Accuracy across all cases: 0.0
- Blind holdout accuracy: 0.0
- False contradiction calls among noncontradictions: 0/12

| Label | True positives | Gold cases | Recall | Precision |
|---|---:|---:|---:|---:|
| supported | 0 | 6 | 0.0 | None |
| contradicted | 0 | 6 | 0.0 | None |
| insufficient | 0 | 6 | 0.0 | None |

| Case | Split | Gold | Observed | Span bound |
|---|---|---|---|---|
| moon-distance-s | development | supported | model_or_cli_failure | no |
| moon-distance-c | development | contradicted | model_or_cli_failure | no |
| moon-distance-i | development | insufficient | model_or_cli_failure | no |
| ocean-cover-s | development | supported | model_or_cli_failure | no |
| ocean-cover-c | development | contradicted | model_or_cli_failure | no |
| ocean-cover-i | development | insufficient | model_or_cli_failure | no |
| census-2020-s | development | supported | model_or_cli_failure | no |
| census-2020-c | development | contradicted | model_or_cli_failure | no |
| census-2020-i | development | insufficient | model_or_cli_failure | no |
| earthquake-magnitude-s | holdout | supported | model_or_cli_failure | no |
| earthquake-magnitude-c | holdout | contradicted | model_or_cli_failure | no |
| earthquake-magnitude-i | holdout | insufficient | model_or_cli_failure | no |
| si-second-s | holdout | supported | model_or_cli_failure | no |
| si-second-c | holdout | contradicted | model_or_cli_failure | no |
| si-second-i | holdout | insufficient | model_or_cli_failure | no |
| moon-life-s | holdout | supported | model_or_cli_failure | no |
| moon-life-c | holdout | contradicted | model_or_cli_failure | no |
| moon-life-i | holdout | insufficient | model_or_cli_failure | no |

Original prompts, verbatim model outputs and source URLs are in results.json.
The reference labels were committed **before** model execution.
A small dataset and a single model are not proof of general semantic reliability.
No automatic blocking of Claim-Audit-Lab answers has been enabled.
