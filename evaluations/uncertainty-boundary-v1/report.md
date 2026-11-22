# Epistemic uncertainty boundary: preregistered experiment

Goal: distinguish an untested or unsupported world claim from a claim actually contradicted by the provided text. This synthetic short-excerpt test neither certifies truth nor authenticates external sources.

- Gold corpus SHA-256: c05be1632fbb888ff4bfd6689ed88700d367fbd8a231b1cdb2432cd9169c8de8 (frozen before any inference in commit f6beb4c)
- Selection frozen in commit 377da19 before evaluating holdout.
- 18 source families, 9 development and 9 holdout; supported/contradicted/insufficient each 3 per split.
- All reference labels were authored by one operator, not independently annotated.

## Paired model outcomes

| Split | Model | Baseline correct | V1 correct | Baseline false contradictions | V1 false contradictions |
|---|---|---:|---:|---:|---:|
| development | qwen3:14b | 6/9 | 7/9 | 3 | 2 |
| development | gemma4:12b | 9/9 | 9/9 | 0 | 0 |
| holdout | qwen3:14b | 8/9 | 8/9 | 1 | 1 |
| holdout | gemma4:12b | 9/9 | 9/9 | 0 | 0 |

Alternative v2 on Qwen development: 7/9 correct, 2 false contradictions; no gain over v1.

## Observed failures and interpretation

- Qwen3 falsely classifies explicitly uninvestigated causality as contradicted, although no counter-fact is given.
- Qwen3 also treats an increase in electricity production as contradicting a decrease in emissions: different variables without a demonstrated relation.
- On holdout, Qwen3 declares an uninvestigated payment influence on voting contradicted under both prompts; Gemma4 calls it insufficient.
- V1 improves one Qwen development classification but zero holdout classifications. It does not warrant replacing the default prompt. Gemma4 is 9/9 under both in both splits.
- An earlier valid INSUFFICIENT response with a literal evidence limitation quote was wrongly rejected by the former parser's empty-span-only rule. The narrow repair accepts exact source limitations and rejects invented spans.

Decision: keep the default prompt unchanged. Keep the grounded-limitation-span parser fix. Treat V1 and V2 prompt tweaks as unsuccessful exploratory evidence. No keyword filter, new mandatory gate or extra service.

Next hypothesis (not independently tested here): a second independent local model might flag false contradictions without sacrificing genuine contradiction detections. These 18 cases were observed while forming that hypothesis and cannot independently validate it.

## Raw artifacts and SHA-256

- baseline-development-gemma4-12b.json SHA-256: 9306e182462fd26d0bb35b8864a2764b749bc035132b533102e78e02cf5a9b28
- baseline-development-qwen3-14b.json SHA-256: 09ccf1688b28e77367f1469f69f55837e0584daa1472e7624a0374b2b7e9758a
- candidate-after-span-fix-development-gemma4-12b.json SHA-256: 8ec368c8ce1edbb6be6a5d2cb8a1a1c72da2c6ac02edfd05601dd6caf6d47c0f
- candidate-after-span-fix-development-qwen3-14b.json SHA-256: 4e41dd1016f4100ede5f01d26037b2eb9c62c478cf90d80938211f4f9b42fc16
- candidate-development-gemma4-12b.json SHA-256: 4323930c507728e08a30b6be0caaa68e9baa49aadebff34319809cdef1c64188
- run-baseline-holdout-gemma4-12b.json SHA-256: c63ca1adf8369ae958691adfcb8b87dddcc6ff37f0870cf07b5645956aee8544
- run-baseline-holdout-qwen3-14b.json SHA-256: 0fc7c546be6e0ddf4efdd61ebe240d3eb73109046dd7b41aa2c6b83234e6f87a
- run-v1-holdout-gemma4-12b.json SHA-256: 785c3820f7dc0744e3628316dcb9734207a15cc6c470462cd6c7c4a7cc7995a1
- run-v1-holdout-qwen3-14b.json SHA-256: acda1fc32d7d510d82f6639ebfa8f2700b46b729e34cb7438bdeab696c2e767c
- run-v2-development-qwen3-14b.json SHA-256: 8279e378831b4991bbddd8b5ac8bf7b3aa55acd35ce2e759d4ebe9c063c1d553
