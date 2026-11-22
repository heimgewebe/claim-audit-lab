# Source excerpt → claim semantic shadow assessment

One model; precommitted editor-curated labels, **not independent expert annotations**.
No web access was granted to the reviewer and these judgments do not certify
the authenticity of the cited web pages or factual claims outside each excerpt.

- Model: gemma4:12b; seed: 20261121
- Valid responses: 18/18
- Model calls actually attempted: 18
- Accuracy among valid responses (not measurable if none): 1.0
- Blind holdout accuracy: 1.0
- False contradiction calls among noncontradictions: 0/12

| Label | True positives | Gold cases | Recall | Precision |
|---|---:|---:|---:|---:|
| supported | 6 | 6 | 1.0 | 1.0 |
| contradicted | 6 | 6 | 1.0 | 1.0 |
| insufficient | 6 | 6 | 1.0 | 1.0 |

| Case | Split | Gold | Observed | Span bound |
|---|---|---|---|---|
| moon-distance-s | development | supported | supported | yes |
| moon-distance-c | development | contradicted | contradicted | yes |
| moon-distance-i | development | insufficient | insufficient | yes |
| ocean-cover-s | development | supported | supported | yes |
| ocean-cover-c | development | contradicted | contradicted | yes |
| ocean-cover-i | development | insufficient | insufficient | yes |
| census-2020-s | development | supported | supported | yes |
| census-2020-c | development | contradicted | contradicted | yes |
| census-2020-i | development | insufficient | insufficient | yes |
| earthquake-magnitude-s | holdout | supported | supported | yes |
| earthquake-magnitude-c | holdout | contradicted | contradicted | yes |
| earthquake-magnitude-i | holdout | insufficient | insufficient | yes |
| si-second-s | holdout | supported | supported | yes |
| si-second-c | holdout | contradicted | contradicted | yes |
| si-second-i | holdout | insufficient | insufficient | yes |
| moon-life-s | holdout | supported | supported | yes |
| moon-life-c | holdout | contradicted | contradicted | yes |
| moon-life-i | holdout | insufficient | insufficient | yes |

Original prompts, verbatim model outputs and source URLs are in results.json.
The reference labels were committed **before** model execution.
A small dataset and a single model are not proof of general semantic reliability.
No automatic blocking of Claim-Audit-Lab answers has been enabled.
