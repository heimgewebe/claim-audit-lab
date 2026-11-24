# Post-hoc context-preservation diagnostic (not independent holdout)

After the compound pilot's failed holdout, freeze a new small diagnostic
on four already exposed sources. Script SHA-256
13646288b436e9da610ea37ed36bf9f04746b66de2182418b3d1a668ef993563,
created 2026-11-24T12:32:14Z before the diagnostic calls. Original 72
responses, protocol, and holdout decision remain unchanged.

Both arms use the same minimal instruction plus target-focus clarification,
same exact source and target B. Isolated context repeats target B; full
context presents A and B. 16 fresh model requests, eight per model.
No retries, provider/context errors, or new sources. Cases already seen
during original pilot; not new independent evidence.

| Model | Strict correct isolated | Strict correct full | Raw label isolated/full | Valid isolated/full |
|---|---:|---:|---:|---:|
| Gemma 4 12B | 3/4 | 3/4 | 3/4, 3/4 | 3/4, 4/4 |
| Qwen 3 14B | 3/4 | 3/4 | 3/4, 3/4 | 4/4, 4/4 |

Both models again incorrectly supported the CD34(low/-) 3.5-fold claim
(doc 40234452) in both arms. Gemma's isolated response also included
an ellipsis, invalid under the existing quote parser. The other three
targets (insufficient CRP intervention evidence, insufficient inherited
genetic explanation of familial reflux, and contradicted GU-rich element
location) were all correct in both arms. Thus the specified strong
mechanistic criterion FAILED. Adding the full statement merely as context
while focusing on a single atom was insufficient to restore the correct
relationship. This does not prove that context has no effect, nor that
any explicit relational comparison would fail. Distinguish actual
entity-to-measure assignment from simply quoting the correct source.

Do not enable oracle splitting or this context-focus variant. No prompt
or product change. A future diagnostic can target explicit comparison
of entity/value pairs, with new sources and equal-budget control;
separately test source sentence references and verbatim reconstruction.
Do not reuse these exposed cases as a new holdout.

Original outputs:
- context-diagnostic-gemma4-12b.jsonl SHA256 6cdae147346f9bfbcfc5a1cb7f8226257d0c8b914307364da9303036837237ac, task 2fff05cc9f254f55827a4706 (completed).
- context-diagnostic-qwen3-14b.jsonl SHA256 631711c1e135a34bb2ca4de28e19ff344fb2f68ff0451774da4fb412c1f70bb3, task a9544854f212436998beee68 (completed).
