#!/usr/bin/env python3
"""Compound SciFact pilot: frozen before inference, source-relative, operator-authored annotations.

Protocol (2026-11-24): first 12 SHA-ordered unused SciFact corpus abstracts
with 700 < len(abstract) < 2200, excluding both prior SciFact manifests
and smoke doc 13734012. First six development, next six reserved. Each
split has two supported, two insufficient, two contradicted conjunctions.
Sources are original abstracts from the SHA-pinned SciFact archive
(Wadden et al. EMNLP 2020; S2ORC abstract data ODC-By 1.0; attribution
https://github.com/allenai/scifact and previous scifact-expert-v1/README.md).
Claims and atom annotations below are operator-created, NOT SciFact gold.
Never interpret missing evidence as world refutation.

Control: existing minimal prompt on full conjunction. Treatment: the same
minimal prompt independently on each operator-provided atomic clause, then
C if either C, S if both S, otherwise I. Both atom responses must pass
the existing exact-span parser. No source rendering, extra prompting,
external retrieval, model downloads, or user-runtime changes.
Test is an oracle-segmentation diagnostic, not automatic decomposition.
Treatment gets two calls instead of one; if positive, a separate frozen
equal-budget control and automatic-segmentation test are necessary.
Prompts contain no gold or split; random order of all individual calls per
model, fresh independent requests. Save every returned raw output; never
overwrite. No selective retry. Provider/context errors are separately
reported; all 18 planned calls per model have to complete for screening.
Report label accuracy, valid counts, fully correct atom pairs, false
refutations, missed contradictions, and token cost. Inspect rationales and
evidence meaning manually, separately from syntactic validity.
Advance to reserved holdout only if on development (both models) aggregate
correct improves by >=2 of 12, at least one model improves, neither loses
accuracy or increases false contradictions/missed contradictions, and no
atom-pair validity is lost relative to direct. An observed failure is a
screening stop, not proof of no possible benefit. Any gain is exploratory.
No human independent annotation or estimate of population accuracy.
"""
import argparse
import hashlib
import json
import pathlib
import random
import runpy
import sys
from datetime import datetime, timezone

S, I, C = "supported", "insufficient", "contradicted"
CASES = [
 (21287352, "development", [
  ("Higher serum CRP was associated with faster FEV(1) decline in the COPD patients studied", S, "Inverse correlation with annual FEV(1) change."),
  ("Lowering serum CRP slows that decline", I, "No CRP-lowering intervention or causal result reported.")]),
 (42404093, "development", [
  ("Life-threatening and serious adverse drug events were more often judged preventable than significant events", S, "42% versus 18%."),
  ("Errors were more likely to be intercepted at the administration stage than at the ordering stage", C, "0% versus 48%.")]),
 (30543439, "development", [
  ("Depleting NUDT15 had no effect on incorporation of 8-oxo-dGTP into DNA in the reported experiments", S, "Explicit no-effect result."),
  ("Depleting NUDT15 did not affect survival in the cancer cell lines tested", S, "Explicit no-effect result in tested lines.")]),
 (28419824, "development", [
  ("Discontinuing daily symptomatic medication improved headache in the reported study", S, "Conclusion 2."),
  ("Discontinuing daily symptomatic medication enhanced the benefit of prophylactic medication in the reported study", S, "Conclusion 4.")]),
 (16839245, "development", [
  ("Inhibiting CDKs increases five-year survival in human cancer patients", I, "Potential therapeutic benefits but no such survival result."),
  ("The major cell-division regulatory mechanisms originally identified in yeast are not conserved in mammals", C, "Explicit statement that major mechanisms are conserved.")]),
 (2159648, "development", [
  ("Vascular calcification shares mineral composition features with bone development", S, "Explicit common features."),
  ("Vitamin D supplementation has been shown to reduce vascular calcification incidence in older adults", I, "Vitamin D named as a biomarker, but no supplementation incidence result.")]),
 (40234452, "holdout", [
  ("In recipient mice, HES-1-transduced 34-KSL cells produced side-population progeny at 3.5 times the ratio produced by nontransduced competitors", S, "First reported ratio 3.5-fold."),
  ("In recipient mice, HES-1-transduced 34-KSL cells produced CD34(low/-) progeny at 3.5 times the ratio produced by nontransduced competitors", C, "Second reported ratio 7.8-fold.")]),
 (20767776, "holdout", [
  ("Among relatives of patients with Barrett's esophagus, 30% had frequent reflux symptoms", S, "Explicit prevalence."),
  ("The excess prevalence in those relatives was attributable to inherited genetic variants", I, "Familial clustering from a questionnaire does not establish genetic causation.")]),
 (17333231, "holdout", [
  ("Deleting ADAM10 in forebrain neurons shortened incubation times after prion infection in the mice studied", S, "Explicit decrease in incubation time."),
  ("The absence of ADAM10-mediated shedding impaired spread of prion pathology in the mice studied", S, "Explicit impaired spread.")]),
 (3773719, "holdout", [
  ("Human pluripotent stem cells can form tumors in immunocompromised individuals if introduced in their pluripotent state", S, "Explicit capability."),
  ("The incidence of tumors after transplantation of differentiated human pluripotent stem cell derivatives is below one percent", I, "No quantitative incidence provided.")]),
 (34747208, "holdout", [
  ("The cryptic splice site in lamin A constitutively activated in HGPS is sporadically used in healthy individuals", S, "Explicit mechanism."),
  ("Inhibiting this splice site reverses the reported age-related nuclear defects", S, "Explicit reversal.")]),
 (35448676, "holdout", [
  ("In mammalian cells, pre-mRNA 3'-end processing depends on the AAUAAA sequence upstream of the cleavage site", S, "Explicit sequence location."),
  ("In mammalian cells, the GU-rich sequence element involved in pre-mRNA 3'-end processing is upstream of the cleavage site", C, "Explicit downstream location.")]),
]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def aggregate(labels):
    if len(labels) != 2 or any(x not in (S,I,C) for x in labels):
        return None
    return C if C in labels else S if labels == [S,S] else I

def lower_initial(s):
    # Avoid lowercasing proper names/abbreviations: clause after semicolon
    # is written as a distinct sentence, not altered.
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=pathlib.Path, required=True)
    p.add_argument("--archive", type=pathlib.Path, required=True)
    p.add_argument("--model", choices=["gemma4:12b","qwen3:14b"], required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--split", choices=["development","holdout"], default="development")
    a=p.parse_args()
    root=a.repo/"evaluations"
    sci=runpy.run_path(str(root/"scifact-expert-v1/run.py"))
    _,corpus=sci["load_release"](a.archive)
    used={13734012}
    for name in ("scifact-expert-v1","scifact-contrastive-v1"):
        used.update(x["doc_id"] for x in json.loads((root/name/"manifest.json").read_text())["samples"])
    pool=[k for k,v in corpus.items() if k not in used and 700<len(sci["source_text"](v))<2200]
    ranked=sorted(pool,key=lambda k:sha(f"compound-20261124/{k}".encode()))[:12]
    assert ranked==[x[0] for x in CASES], "Source selection mismatch"
    assert all(sorted(aggregate([x[1] for x in atoms]) for _,sp,atoms in CASES if sp==split)==sorted([S,S,C,C,I,I]) for split in ("development","holdout"))
    shadow=sci["load_shadow"]()
    instruction=json.loads((root/"evidence-switch-v1/protocol.json").read_text())["treatments"]["minimal"]
    shadow.INSTRUCTION=instruction
    selected=[(d,atoms) for d,sp,atoms in CASES if sp==a.split]
    schedule=[]
    for doc,atoms in selected:
        full=atoms[0][0]+". Additionally, "+atoms[1][0]+"."
        for arm,claim in (("direct",full),("a",atoms[0][0]+"."),("b",atoms[1][0]+".")):
            schedule.append((doc,arm,claim))
    random.Random(2026112401 if a.model=="gemma4:12b" else 2026112402).shuffle(schedule)
    with a.output.open("x",encoding="utf-8") as f:
        def save(row):
            f.write(json.dumps(row,ensure_ascii=False)+"\n")
            f.flush()
        save({"kind":"protocol","created":datetime.now(timezone.utc).isoformat(),"runner_sha256":sha(pathlib.Path(__file__).read_bytes()),"source_archive_sha256":sci["RELEASE_SHA256"],"backend_sha256":sha(pathlib.Path(sci["SHADOW"]).read_bytes()),"instruction":instruction,"split":a.split,"model":a.model,"cases":[{"doc_id":doc,"source_sha256":sha(sci["source_text"](corpus[doc]).encode()),"atoms":atoms,"gold":aggregate([x[1] for x in atoms])} for doc,atoms in selected]})
        for doc,arm,claim in schedule:
            excerpt=sci["source_text"](corpus[doc])
            prompt=shadow.prompt_for({"claim":claim,"source_excerpt":excerpt})
            out=shadow.run_ollama_one({"id":f"{doc}:{arm}","prompt":prompt,"prompt_sha256":shadow.sha(prompt)},excerpt,a.model)
            # Excerpts are reconstructible from the pinned archive, don't duplicate.
            out.pop("prompt",None)
            row={"kind":"response","doc_id":doc,"arm":arm,"claim":claim,**out}
            save(row)
            print(json.dumps({"id":row["id"],"status":row.get("status"),"label":row.get("judgment",{}).get("label"),"error":row.get("error")}),flush=True)
            if row.get("error") not in (None,"invalid_output","generation_truncated"):
                print("Stopped on provider/context failure; no hidden retry.",flush=True)
                return 2
    return 0

if __name__=="__main__":
    sys.exit(main())
