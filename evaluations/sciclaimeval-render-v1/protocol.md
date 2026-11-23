# Preregistered SciClaimEval native-table presentation experiment

## Motivation and falsifiable hypothesis

PR #43 attempted 26 genuine local Qwen3/Gemma4 model calls with scientific
claims and raw HTML/LaTeX table evidence. Only 11 produced valid contiguous
source quotations; 14 produced invalid literal citations and one response
was truncated. On an explicitly weaker post-hoc reading of the labels, there
was a possible updating signal but no validated scientific benefit.

**Hypothesis (not yet established):** Representing the SAME native
scientific table as deterministic, readable rows with verifiable links to
unchanged original source spans will increase the fraction of fully valid,
expert-label-matching source judgments and two-turn revisions, without
increasing actual false refutations, missed refutations or inappropriate
changes on irrelevant information.

This is a test of **scientific source/provenance fidelity combined with
semantic evidence interpretation**, not of absolute world truth or independent
corroboration. The intentionally modified SciClaimEval Refuted table is
a counterfactual replacement of a source, not an authentic second paper.

## Sources, license and strict independence boundary

- Published data: SciClaimEval (Ho et al., LREC 2026),
  https://huggingface.co/datasets/alabnii/sciclaimeval-shared-task
- Fixed revision: 55ec80b427d9b4eaff8ed9b537a1ea6cb5d665d7
- Original Task1 release SHA-256:
  cbf0db967f285875b7b283ed56f4fed93bf4627f84d8e7f3c39489bc56f289ab
- Individual files restricted to native .tex/.html table sources
  with their own explicit CC BY 4.0 source metadata; the archive, license,
  paper/claim IDs, original-source SHA-256 and derived display hashes must
  match before model inference. Original tables remain outside Git, exact
  source IDs/hashes are in manifest.json. No original source rewriting.
- Prior PR43's six science papers are **excluded entirely**, not used for
  a second holdout. PR43 samples can be used only as already observed
  offline renderer-development fixtures, not scored as blind outcomes.
- **Pre-inference selection amendment (no manifest or model trial existed):**
  The original 2 ML + 2 NLP + 2 PeerJ plan could not select any further
  eligible numeric ML paper: all such ML identities were already used in
  PR43's six-pair experiment. That initial prepare call exited with a
  selection error and no manifest was created. Do not weaken the published
  gold or reuse a source family to force that stratum.
- Instead select 4 new NLP pairs and 2 new medical (PeerJ) pairs by
  deterministic SHA ordering using seed 20261123-source-row-v1. The
  SciClaimEval numeric-claim eligibility is unchanged. Each pair must
  have two published source-relative expert labels, unchanged claim and
  caption, differing raw AND rendered source contents, a new paper,
  bounded source lengths and CC BY 4.0 attribution.
  First two NLP and first one PeerJ = development; next two NLP and one
  PeerJ = untouched model holdout. No pair/paper crosses splits. This
  narrower domain mix reduces external generalizability.
- **Second pre-inference correction, also without model calls:** An initial
  six-pair candidate manifest (SHA-256
  375b79d7082f84829c25b220cd6150d2af7c8aa78c31ddfef91f20e4cf4ae497)
  was generated but its row renderer split **logical** LaTeX rows across
  multiple physical lines, losing table semantics. It is retained
  verbatim as aborted-pretrial-manifest.json, explicitly **not** a
  model-scored manifest. The renderer was repaired to join full logical
  rows and map their continuous original source character spans. A valid
  final table row may omit a trailing LaTeX row-break. Structurally
  unrenderable candidates are excluded *before inference*, without
  editing any published expert label. The final pre-inference manifest
  is SHA-256 c5f91e3ed9240cd41ad4dd270e01dfd86944953ce3a1d015c25765283b2d863a.
  Only that final manifest can be used for model trials. No model ran on
  either preliminary selection attempt, and no gold answer was changed.
- Commit manifest, renderer, runner, methodology and tests **before**
  first model call; original raw outputs are create-only, never retried.

## Paired trial

Use the existing local Qwen3 14B and Gemma4 12B digests, temperature 0,
8192 context, no source truncation, no HTTP proxy/cloud inference, and the
**unchanged** scientific semantic instruction and JSON response contract.

For every new pair and each model, compare exactly two treatments:

- RAW (baseline): the previously established original native table
  excerpt, unchanged quote validation against raw source bytes.
- RENDERED: same underlying source transformed to plain-text rows by a
  deterministic display that strips markup and decodes HTML entities.
  The evidence quote must occur in exactly one display row. Re-running
  the renderer against the SHA-verified original is mandatory, and its
  row original-source character offsets and SHA-256 must map the quoted display
  back to that exact source row. A synthetic composition spanning multiple
  displayed rows or an ambiguous quote must not be accepted. The displayed
  quote is **not** falsely advertised as a literal substring of raw HTML
  or LaTeX; the proof explicitly states whether it is raw-verbatim.

In each condition perform:
1. Independent judgment against the supporting source version.
2. Independent judgment against the deliberately refuting version.
3. Genuine sequential chat: earlier supporting judgment, then replacement
   with refuting version.
4. Genuine sequential chat: earlier refuted judgment, then replacement
   with supporting version.
5. Unchanged-evidence control with irrelevant administrative information.

The result files bind original source sha, displayed source sha,
prompt/conversation hashes, original model responses, model digest,
citation validity/provenance, errors, token counts and durations.
No reported success from invalid citations, clipped generations or a
provider outage.

Counterbalance trial order: Qwen3 RAW then RENDERED; Gemma4 RENDERED
then RAW. Development first; holdout only after a frozen decision.
This small design cannot eliminate model/warmup/ordering confounding
or pretraining contamination; report raw paired counts, not population
accuracy estimates.

## Predeclared metrics and go/no-go

Primary: **fully valid and expert-matching revised answers** across
the two replacement directions, 3 development papers (2 NLP + 1 PeerJ) x
2 models x 2 directions = 12 opportunities per condition. Secondary: provenance-
verified quote rate over all 30 responses per condition; separate missed
expert contradictions and false expert contradictions, extra irrelevant
control changes, incomplete generations, time and prompt-token burden.

Open the holdout only if, on development:
- RENDERED obtains at least 3 MORE fully valid expert-matching revisions
  than RAW across both models; neither model loses correct revised cases;
- no increase in fully valid false contradictions of expert-supported
  evidence or missed genuine published refutations;
- no increase in invalid source-provenance or irrelevant-evidence changes,
  and no new provider/context errors.

A holdout success would require **at least 3 additional fully valid and
expert-matching revised answers without regression**, and at least one
specific independently corroborated semantic/provenance gain on a new
source family. The tiny fixed sample still cannot establish world truth
or justify mandatory chat interception, more rules, a new service, or a
production gate. In the absence of that evidence, document the negative
trial, leave the default verifier unchanged and preserve all artifacts.

If development fails, STOP without opening holdout, without retrying
invalid output on the same cases, and without adjusting the hypothesis.
A technically defective renderer is a separate engineering fault, not
license to count model/experiment failures as scientific accuracy.