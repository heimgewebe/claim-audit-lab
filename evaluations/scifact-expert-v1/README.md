# SciFact: independently annotated scientific evidence benchmark

The purpose is to compare the existing claim-audit-lab instructions to the existing frozen minimal prompt against *published expert annotations*, not another single-operator synthetic gold corpus.

## Source, license, provenance

David Wadden, Shanchuan Lin, Kyle Lo, Lucy Lu Wang, Madeleine van Zuylen, Arman Cohan and Hannaneh Hajishirzi, *Fact or Fiction: Verifying Scientific Claims* (EMNLP 2020). Official dataset: https://github.com/allenai/scifact . Original archive: https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz . Claim and rationale annotations: CC BY 4.0. Original S2ORC scientific abstracts: ODC-By 1.0. License details: https://github.com/allenai/scifact/blob/master/LICENSE.md . No author endorsement is implied.

Pin: SHA-256 11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be, as published in dataset distribution metadata. The runner checks every byte, reads only the two named archive files, never extracts them or downloads models, and requires the original archive explicitly at runtime. The committed manifest contains identifiers, titles, rationale indices and hashes, not full abstracts or claims.

## Gold-label and negative-control boundaries

Only expert-annotated SUPPORT and CONTRADICT labels score accuracy or false refutations. A cited abstract without a published annotated rationale is NOT expert-labeled NEI. Such weak negative controls have descriptive counts only; the tool does not assume silence is disproof or that lack of annotation proves an insufficient claim.

A deterministic, before-inference selection picks five SUPPORT, five CONTRADICT, and five cited-but-unannotated pairs for each of the development and holdout splits. Claim and paper IDs cannot repeat, including across splits. Abstract length is bounded (120 to 3200 characters) to limit local context clipping. The result is a small, source-disjoint convenience sample, not an unbiased estimate of scientific model accuracy.

## Usage (opt in)

Save the official archive outside the repo and verify its hash, then run:

    python evaluations/scifact-expert-v1/run.py build-manifest --archive /path/to/verified-data.tar.gz
    python evaluations/scifact-expert-v1/run.py trial --archive /path/to/verified-data.tar.gz --split development --model gemma4:12b --condition lab

Run both existing locally installed models, each with both unchanged prompt variants, on development first. Freeze a comparison before opening the holdout. Each result is create-only, records prompt and response hashes and distinguishes provider and schema failures from semantic mistakes. A trial now continues after model-authored invalid_output citation formatting instead of hiding subsequent cases, while it still terminates on backend/provider failures. This is an explicitly post-development process amendment prompted by a Qwen response that joined two verbatim source sentences with a noncontiguous ellipsis: the core citation validator correctly refused that composite quote. For the original incomplete trial, supply --resume-from /path/to/original-run.json; the script verifies original prompt/response hashes and creates a separate -resumed.json without rerunning those cases. The original partial output is preserved as evidence of the initial procedure. No new service, CI gate, global prompt requirement or cloud inference is involved.

Limitations: release provenance does not prove the underlying scientific articles are true; expert labels are judgments about abstracts and claims, not incontrovertible world facts; SciFact is public and may have been encountered in model pretraining. This benchmark does not establish live chat enforcement, source authenticity or durable correction of beliefs.