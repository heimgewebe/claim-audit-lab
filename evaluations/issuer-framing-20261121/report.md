# Issuer-framing paired pilot

This is an exploratory synthetic, **single-model** comparison. The prompts are identical within each pair except for the named report issuer. Runs use separate ephemeral sessions and a fixed order seed.

- Model: gpt-6-astra; seed: 20261121; repetitions per frame: 2
- Valid responses: 16/16
- Valid pairs: 8/8
- Paired categorical status changes: 1/8
- Largest within-pair support-score difference: 10

| Scenario | Mean support A | Mean support B | Flips | Max score gap |
|---|---:|---:|---:|---:|
| waiting_nonrandom | 25 | 27.5 | 1 | 10 |
| clinic_randomized | 96 | 95.5 | 0 | 1 |
| classroom_null_randomized | 6.5 | 5 | 0 | 3 |
| workplace_randomized | 95 | 95.5 | 0 | 1 |

The raw answers and complete prompts are stored in results.json, including the hash of each. Score differences alone do not prove institutional bias. Repeated runs from one model are not independent providers or a representative sample; only an observed sensitivity of this model on these synthetic questions can be inferred.
