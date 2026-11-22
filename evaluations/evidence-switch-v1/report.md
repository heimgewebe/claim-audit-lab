# Evidence-switch: scientific discipline under counterfactual source changes

The exact same claim was tested with supporting, explicitly contradicting and insufficient synthetic excerpts. Gold labels and prompt treatments were frozen in Git before local inference. Six development and six holdout families are disjoint. Models were stateless between inputs, so this measures evidence responsiveness, not durable belief revision.

- Frozen case SHA-256: 19995409ae52c5de4495f6431a9816a3b9b3575eaa09d9bec850703d6dbabd5c; protocol SHA-256: 3ae254ae5bb1e47284c4e80cead4a42eff7099b47993b286dd0b66aed1c306a2.
- All 144 local model generations completed with valid JSON, source-span validation and SHA-256-bound prompts and responses.
- Single operator-authored synthetic cases; no independent human gold annotator, source authenticity or claims of real-world accuracy.
- The minimal prompt kept the output format and local backend; only the scientific discipline instruction differed.

## Reviewer-discovered gold errors and post-hoc sensitivity

Two original gold labels were semantically wrong; the immutable 36-case corpus and all 144 original model replies are retained. d05-political-payment-purpose--insufficient asks whether the note expressly names a motive, but the excerpt explicitly states that the note names no purpose. h06-radiology--insufficient asks what the evaluated CT image identified, but the excerpt says the CT did not image that bone. These CONTRADICT the document/image-content claims; they do not disprove the corresponding real-world motive or patient condition.

The following **post-hoc** sensitivity analysis excludes the entire affected 3-state family in each split, rather than relabeling original gold after seeing the outputs. It is NOT a new blind holdout, and the original 18-case numbers below are historical and invalid as unqualified performance estimates.

| Split | Model | Minimal correct | Lab correct | False contradictions minimal to lab | 3/3 families minimal to lab |
|---|---|---:|---:|---:|---:|
| development | gemma4:12b | 10/15 | 14/15 | 5 to 1 | 0/5 to 4/5 |
| development | qwen3:14b | 11/15 | 13/15 | 4 to 2 | 1/5 to 3/5 |
| holdout | gemma4:12b | 13/15 | 13/15 | 2 to 2 | 3/5 to 3/5 |
| holdout | qwen3:14b | 11/15 | 11/15 | 4 to 4 | 1/5 to 1/5 |

After removing the contaminated full families, the lab instructions still show improvement only in development, not holdout. Remaining jointly wrong labels cannot be cured by a mere model-agreement rule. Original prompt/response files and original labels are preserved for forensic reproducibility. Independent human gold annotation remains missing.

Review origin: https://github.com/heimgewebe/claim-audit-lab/pull/40 ; authoritative correction description: erratum-v1.json ; original cases SHA-256: 19995409ae52c5de4495f6431a9816a3b9b3575eaa09d9bec850703d6dbabd5c


## Original preregistered metrics (contaminated by gold errors)

| Split | Model | Minimal correct | Lab correct | False contradictions minimal to lab | Correct 3-state families minimal to lab |
|---|---|---:|---:|---:|---:|
| development | gemma4:12b | 12/18 | 16/18 | 6 to 2 | 0/6 to 4/6 |
| development | qwen3:14b | 13/18 | 15/18 | 5 to 3 | 1/6 to 3/6 |
| holdout | gemma4:12b | 15/18 | 15/18 | 3 to 3 | 3/6 to 3/6 |
| holdout | qwen3:14b | 13/18 | 13/18 | 5 to 5 | 1/6 to 1/6 |

Both models and prompts recognized all six explicit contradictions per split. The measured weakness is frequently calling an undeciding excerpt contradicted.

Interpretation: Lab instructions improved development performance for both models but produced zero label improvements on the disjoint holdout. This does not demonstrate a transferable benefit from more prompt instructions, nor prove they are useless on other tasks. No new prompt expansion or mandatory gate is justified.

## Original exploratory disagreement (includes two wrong gold labels; do not use as accuracy evidence)

- development: models disagreed on 1/18; Qwen-only mistakes 1, shared mistakes 2.
- Shared mistakes: d03-publisher-conclusion--insufficient, d05-political-payment-purpose--insufficient.
- holdout: models disagreed on 2/18; Qwen-only mistakes 2, shared mistakes 3.
- Shared mistakes: h02-education-budget--insufficient, h03-railway-departure--insufficient, h06-radiology--insufficient.

The disagreement diagnostic is post hoc and cannot itself validate a second-model adjudicator. When both models misclassify the same evidence, agreement would falsely reassure.

## Next falsifiable scientific test

- Use naturally occurring source excerpts independently annotated by multiple people and bound to source snapshots. Do not generate reference labels from the evaluated models.
- Before running, preregister whether an optional independent model-disagreement alert detects false contradictions without increasing false alarms on actual contradictions; measure additional latency and cost.
- Source authenticity, genuine world truth and changes of belief across a continuous conversation are not tested by this experiment.

## Hashes for all raw results

- run-development-gemma4-12b-minimal.json SHA256 f96707a03ad574797cc4a638d34d80f185f102f99090e9333475a71e874bedd6
- run-development-gemma4-12b-lab.json SHA256 a10d01bf4bfa17b84784a64e71ef3bcac738895daf4c8ff7f029b1443cb58f94
- run-development-qwen3-14b-minimal.json SHA256 79605a18d3c76bd971c3b5e7e0d52fc635f6bdcecac8f8ad8581153499ccbefb
- run-development-qwen3-14b-lab.json SHA256 a5891907adba0a7d5b0b88f6531c968cde9987c0792be979025cb666f075447f
- run-holdout-gemma4-12b-minimal.json SHA256 2574981c4640797a0af958b766d3af220d1ebd397470a38e07f7b9a3d752e160
- run-holdout-gemma4-12b-lab.json SHA256 5657d1c976a272ed9dc04a7f96f91cb3c3bb98c7b24e4b9b76109b60ad46ec7c
- run-holdout-qwen3-14b-minimal.json SHA256 621fcadd22a6410924fbb601adda2bb82e2c5759c1c7606ba7d43c04da7ec0b4
- run-holdout-qwen3-14b-lab.json SHA256 b0bdca780d91e3e856d1024a7b4251ce1791b88eef3b8f0e722f0c74ff866415
