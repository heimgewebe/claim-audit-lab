# SciClaimEval paired-table revision pilot (preregistered)

## Why

Previous Claim-Audit-Lab PRs #39, #40, #41 and #42 found no reproducible
scientific-accuracy benefit from longer or slightly more precise prompts.
Prior source-switch comparisons used independent single-turn inference,
which does *not* measure how an agent handles an earlier answer when a
source changes. The present test evaluates a genuine two-message local
Ollama chat with the earlier answer supplied as the assistant's first turn.

**Scope:** Does the assistant correctly reconsider a fixed claim relative to
the **currently supplied source text**, and does previous output anchor it
incorrectly when the evidence changes? Not model belief about world truth,
not independent sources contradicting each other, not a repaired real-world
paper. The refuting SciClaimEval tables are *deliberately manipulated* versions
of the supporting evidence. They must never be represented as independent
scientific replications, true later corrections or verified world facts.

## Source and license

- Ho et al., *SciClaimEval: Cross-modal Claim Verification in Scientific
  Papers*, LREC 2026, https://aclanthology.org/2026.lrec-1.864/
- Official data: https://huggingface.co/datasets/alabnii/sciclaimeval-shared-task
- Fixed dataset commit: 55ec80b427d9b4eaff8ed9b537a1ea6cb5d665d7
- Official Task-1 JSON SHA-256:
  cbf0db967f285875b7b283ed56f4fed93bf4627f84d8e7f3c39489bc56f289ab
- Dataset license CC BY 4.0; **each selected table** declares CC BY 4.0.
  Original/modified table bytes are cached outside this repo, verified
  against per-file SHA-256, rather than re-published here. Individual
  source license metadata is bound in the locked manifest.

The published Supported/Refuted labels are expert-curated
**source-relative annotations**. They are neither proof of world truth nor
a separately human-reannotated gold corpus. Captions and table texts are
untrusted data, never model instructions.

## Fixed selection, before any model inference

The committed runner deterministically SHA-sorts eligible pairs with seed
20261123-v1. It selects *exactly one development and one holdout* pair
from each of ML, NLP and medicine (peerj), with distinct papers across
splits and pairs, giving six pairs / twelve labeled source versions.

Filter only public metadata and original bytes, not model outcomes:
one fixed claim with one Supported and one Refuted table;
use_context=no, exact CC BY 4.0, original .tex/.html table source
between 350 and 6000 bytes, a non-bibliographic numeric element in the
claim, and differing original/altered source content. Refer to the
source selection code for the complete deterministic predicate.

The paper list, claim/source IDs, input hashes and licenses are frozen
in manifest.json and committed **before** trial calls. No case or published
gold can be changed silently, and re-fetches must match exact source
hashes. A caption, independent paper ID and claim are paired unchanged.

**This is a small convenience sample of already publicly exposed data.**
It can be present in model training. Paper-disjoint internal holdout is
not proof of true model out-of-distribution generalization. The operator
has already examined source metadata and some table diffs before
pre-registration; untouched means unseen by the local trial, not
untouched by a human.

## Conditions and measurements

For **each** pair and both existing local models (Gemma4 12B and Qwen3 14B),
with identical settings and no new model downloads:

1. Fresh single-turn answer from the original supporting table.
2. Fresh single-turn answer from the manipulated refuting table.
3. Two-turn revision: supported-table answer becomes part of a real Ollama
   chat, followed by an alternative refuting table. The first table is
   explicitly *replaced*, not supplemented by an independent source.
4. Two-turn revision in the opposite refuted-to-supported direction.
5. Unchanged-evidence control: previous supporting-table answer is
   followed by one explicitly unrelated administrative sentence; the
   source table remains unchanged.

The previous answer is fed into the second message as an actual
assistant chat turn. Models see no gold labels, sample IDs, "original"
versus "tampered" labels, pair relationships or modification operations.
The final claim is checked only against the currently designated table.

**Primary:** final expert-label match for revised versus fresh independent
answers to the same table across both directions, including missed
contradictions and false contradictions separately.

**Secondary:** whether a correctly grounded first judgment flips correctly
when the table flips, whether the correct answer is retained when the
evidence does not change, invalid/non-contiguous citations, incomplete
context, source-identity provenance, inference time and token burden.

The existing strict literal substring parser is reused, unchanged.
insufficient is permitted: its disagreement with the binary SciClaimEval
reference is reported as a disagreement, not forcibly mapped to Refuted.
Provider/context failures are never counted as wrong semantic judgments.
All model responses, prompts by hash, exact quotes and model digests are
preserved create-only; no retry or overwriting changes a result.

## Decision bound before development

Development is evaluated first. Run the reserved holdout **only if** the
two-turn final answers improve by at least **2 correct labels** relative to
the fresh-source baseline across the 12 development final judgments
(3 pairs × 2 update directions × 2 models), without any new false expert
contradictions, lost expert refutations, invalid quotes or inappropriate
label changes on unchanged-evidence controls. Otherwise stop after
development and preserve the negative result; do not tune the prompt and
retry on this same holdout.

Even passing the development gate, then passing an equivalent held-out
comparison, would be a small pilot signal: **do not install a mandatory
answer gate or chat interception** without a separate independent
replication and real-user benefit measurement. This trial creates no
service, mandatory QA check, additional reviewer, runtime dependency or
source-authenticity claim.

This experiment cannot decide if a model would revise a belief after
independent contradictory *world evidence*. Its direct target is
source-relative epistemic updating when a cited artifact changes.
