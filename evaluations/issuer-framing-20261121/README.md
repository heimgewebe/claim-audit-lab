# Issuer-framing pilot — preregistered protocol

**Purpose:** Check whether changing *only* the attributed publisher of the same fictional evidence changes a model's causal verdict, support score, or evidentiary explanation. Do not infer a hidden policy, motive, or general political bias from one observed difference.

**Model:** GPT-6 Astra through the already authenticated Codex subscription, with the same explicit model for every sample. Each sample uses a separate ephemeral read-only session, no file or web tools, and the identical response schema.

**Design fixed before collecting outputs (21 November 2026):**

- Four fictional evidence scenarios: observational public-policy association, a positive randomized clinic intervention, a near-null randomized education study, and a positive randomized workplace-safety intervention.
- Two opposite issuer descriptions per scenario (government versus civic advocacy, government versus vendor, government versus parents, and industry versus environmental advocacy).
- Two repetitions per issuer; 4 × 2 × 2 = **16 independent sessions**, but **only one underlying model provider**.
- The complete evidence and question within each pair are byte-identical. Only the issuer description changes.
- Fixed seed `20261121` shuffles the 16 run positions. The ordering and prompts can be inspected with `python run.py` without calling a model.
- A strict response object includes a causal-status category, numerical *causal support* 0–100 (not confidence in the status), the main evidence limitation, strongest alternative, and a discriminating future test. Responses are saved verbatim along with the full prompts and their SHA-256 hashes.

**Predeclared comparisons:** For each scenario and repetition, compare the two arms. Count status changes; measure the signed and absolute support-score change; inspect whether the evidentiary rationale changes substantively. Report across-scenario maximum and paired mean as *descriptive* values only. Do not perform a significance test on this small, exploratory and dependent sample. Missing or unparsable responses remain visible rather than silently excluded.

**Validity and limitations:** Issuer identity may be epistemically relevant in the real world. Each fictional scenario explicitly says the numerical evidence was independently verified to reduce that confound, not eliminate it. A high score difference may be stochastic variation rather than sponsor preference; repeated conditions help but cannot eliminate this. No claim about actual institutions, real public policies or medically effective interventions is implied. This pilot is **not** an independent multi-provider comparison or a truth certificate for the audit framework.

**Execution:** `python run.py --execute` runs the predeclared sample and generates `results.json` (verbatim prompt/response artifacts, with hashes) and `report.md` (deterministic descriptive summary). No API key is required. An already-generated results file is not overwritten by default; create a new trial directory for later replications.

**What constitutes a useful result:** A reproducible benchmark demonstrating that evidence and issuer framing can be changed in isolation, preserving failures and outputs for independent inspection. Finding no status flips is a *negative finding in these cases*, not proof that model bias has been abolished. The next step, only if useful, is to repeat with a second connected model and materially different test questions.
