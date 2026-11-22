# SciFact: expert scientific evidence versus a minimal prompt

**Source and attribution:** Wadden et al. (EMNLP 2020), SciFact: https://github.com/allenai/scifact . Author-annotated claims and rationales CC BY 4.0; S2ORC original abstracts ODC-By 1.0 (https://github.com/allenai/scifact/blob/master/LICENSE.md). Original archive SHA-256 11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be. No full abstracts or claim texts are committed.

**Provenance:** A deterministic, claim-and-document-disjoint 30-pair manifest (SHA-256 727fed187d5d925d3c94ca640c7525cc2df73bb343053b656cc86e16a330e6be) was committed before model calls in c1146cf. Every original abstract, claim, input hash, prompt hash, raw response hash, quoted span and metric was rechecked against the official verified archive. The holdout was opened only after development results and original malformed citation were preserved in git.

Only expert-annotated SciFact SUPPORT/CONTRADICT pairs contribute to reference accuracy. Five cited-but-unannotated source pairs per split are descriptive controls, **not** expert-labeled NOT_ENOUGH_INFO gold. No absence-of-annotation is taken as a scientific negative conclusion.

## Source-grounded outcomes

| Split | Model | Minimal matches / 10 expert pairs | Lab matches / 10 expert pairs | Invalid expert quotes: minimal / lab | Missed expert refutations: minimal / lab |
|---|---|---:|---:|---:|---:|
| development | qwen3:14b | 9/10 | 8/10 | 0 / 1 | 0 / 0 |
| development | gemma4:12b | 9/10 | 8/10 | 0 / 0 | 0 / 0 |
| holdout | qwen3:14b | 8/10 | 7/10 | 0 / 0 | 1 / 2 |
| holdout | gemma4:12b | 8/10 | 8/10 | 0 / 0 | 1 / 0 |

All four holdout conditions attempted all 15 pairs. Qwen3 lab development initially stopped on a scientifically sensible CONTRADICTED label accompanied by a **noncontiguous synthetic quotation** with an ellipsis. The strict citation parser correctly counted that reply as invalid_output. All seven original responses remain immutable; a checksum-bound continuation collected the remaining eight examples without revisiting those seven. Consequently Qwen3 development lab had 8/10 correct expert inputs with **one invalid quoted source span** (8 correct among 9 valid), not a misleading 8/9 success rate. This process amendment was disclosed and committed before opening holdout; prompts and expert annotations were never changed.

Across 40 expert-annotated model/input pairs per prompt condition, the minimal instruction obtained **34/40 matches** and the longer lab instruction **31/40 matches** (including the citation failure as not correct). On holdout Qwen3 dropped from 8/10 to 7/10, Gemma4 remained 8/10. This narrow experiment does not justify more prompt text or gates.

No model contradicted an expert-supported source in these trials. The principal remaining errors concern insufficient responses when the published evidence annotated a real supporting/refuting abstract. All eight complete conditions returned insufficient on their five cited-but-unannotated controls, but these **are not 40 correct neutral gold judgments**. Source absence and unannotated evidence remain epistemically distinct.

## Limits and decisions

- Expert-annotated abstract-level claims are a stronger reference than our original single-operator synthetic corpus, but are not absolute scientific truth. Source-release SHA is provenance of published data, not verification of all underlying papers.
- The dataset is public and may be present in model pretraining; 5 cases per expert label per split is a small, selected sample with no generalization claim.
- This tests only a claim-versus-excerpt prompt and an exact citation parser. It does not measure the entire red-team, counterhypothesis and answer-receipt mechanism or real ChatGPT response capture.
- No additional default prompt, mandatory external review, model gate, service or word filter was added. Separate evidence quote failures from expert-label disagreements.

## Original result artifacts (SHA-256)

- run-development-gemma4-12b-lab.json: b5881363b25254f1b64152cac7c6fce744fd791623037bb9ea2faabab1a57698
- run-development-gemma4-12b-minimal.json: 273cea6383400b419cb1b13b52763081e34e7b82d9db46864b3d50e81ba7c21e
- run-development-qwen3-14b-lab-resumed.json: 44f0a0c90199dd4b342d32c5a65ce93a8af6583f4c00001502af79b5180d1129
- run-development-qwen3-14b-lab.json: 425e5d30870e0072d8e40e1d0c5e599480ad1b8bb9b14926732cf7ff87dbc8c9
- run-development-qwen3-14b-minimal.json: 262d9779a5e11a7a40ff95114db4c70d8b4f37e0bd39e1c59e29bdf52a269fc7
- run-holdout-gemma4-12b-lab.json: 04971b320329476d39fcdc1979cce34031d54c10e49f940c1f6f669f0375514d
- run-holdout-gemma4-12b-minimal.json: 5df94bfa0cf5ba0af9a70f317edf66be3eb3f3913ece81da10636d83d27f079f
- run-holdout-qwen3-14b-lab.json: 655c0b529d1b240efd4ceeb1858f8a94605b42097d9c5d56a203b0c1b94216db
- run-holdout-qwen3-14b-minimal.json: 266cce93dbb251918ccec11bfe31fab5bb5c1eacefea00688c027286a7657d7c
