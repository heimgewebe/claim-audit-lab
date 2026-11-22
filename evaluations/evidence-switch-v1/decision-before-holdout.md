# Development observation and holdout decision (written before holdout)

All four development runs are complete. Both conditions were fixed in Git before inference. This note fixes the decision to run **both** conditions in the blind holdout, regardless of development results. No prompt modifications or case relabeling.

| Model | Minimal correct | Lab correct | Minimal false contradictions | Lab false contradictions | Complete families minimal to lab |
|---|---:|---:|---:|---:|---:|
| qwen3:14b | 13/18 | 15/18 | 5 | 3 | 1/6 to 3/6 |
| gemma4:12b | 12/18 | 16/18 | 6 | 2 | 0/6 to 4/6 |

Do not adopt or widen enforcement on development evidence. On holdout, count false contradictions separately and preserve detection of actual contradictions. These are operator-authored synthetic sources, not independently annotated or authenticated.
