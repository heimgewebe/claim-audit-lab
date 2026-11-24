#!/usr/bin/env python3
"""Sentence-reference pilot, frozen before inference on 2026-11-24.

Question: can a model select original source sentences rather than generate
quotations, reducing transport errors without degrading semantic judgment?

Three paired one-call arms on the SAME claim and source:
plain: unchanged minimal prompt and original abstract.
numbered_quote: same numbered source as reference arm, minimal quote prompt
plus instructions that numbering is display metadata, not source text.
reference: numbered source, exact original sentences resolved from 1-based
integer IDs by the program, at most three unique IDs. No generated quote.
All use existing local Ollama backend, same parameters and independent requests.
Numbering inserts metadata only; no source sentence is rewritten. Noncontiguous
references stay separate; never concatenate them into a fabricated quote.
Gold, reference annotations and split never enter the prompt.

Source selection: SHA-sort published expert SUPPORT and CONTRADICT pairs from
the pinned SciFact dev release, 4 of each per split; exclude previous SciFact
manifests, all compound pilot documents and smoke 13734012. Exclude source
33872649 from this biomedical-method experiment as out of scope (attack-related).
Filter published rationale union <=3 indices. Distinct source/claim IDs.
Exact selection and human-readable operator source-relative judgments frozen
below. Published labels remain unchanged. Operator annotations are NOT
independent expert gold, and explicitly mark reference gaps where warranted.

Metrics: full-schema validity; raw label accuracy separately (even if citation
invalid); strict correct label; false support, false refutation, missed C for
operator source-relative labels; separately published expert agreement; any
complete published rationale set covered by selected source sentences; operator
rationale coverage for clear S/C. Quote mapping may cover only fragments, so
coverage is descriptive, not semantic entailment; ambiguous occurrence not
counted as localized. Review actual reasons/selected spans manually. For I,
do not treat an empty evidence list as proof of world absence.
Provider/context errors separate. All 24 planned calls per model must finish;
no selective retries. All raw rows saved create-only.

Development and holdout screening rule fixed now: reference must have at least
two additional strict correct operator labels (aggregate 16 comparisons) versus
EACH quote arm; neither model may lose raw operator-label accuracy, add false
support or false contradiction, or miss a previously identified explicit C
on reference versus either quote arm. Reference format validity must be no
worse per model. Published expert raw agreement and rationale coverage reported
separately; any substantial worsening of evidence relevance in manual review
blocks promotion. If development fails, do not run holdout. If holdout passes,
only consider an optional prototype after inspecting practical usefulness.
No mandatory runtime mechanism; public corpus, small source-disjoint sample,
operator annotations, changed formatting and sentence selection granularity
limit inference. No general scientific efficacy or external source authenticity
claim. Attribution Wadden et al., EMNLP 2020, https://github.com/allenai/scifact
(CC BY 4.0 claim/rationale; S2ORC ODC-By 1.0 abstract data).
"""
import argparse, hashlib, json, pathlib, random, runpy, sys
from datetime import datetime, timezone

S,I,C="supported","insufficient","contradicted"
# claim ID, document ID, split, independently operator-assessed excerpt label,
# reason, acceptable decisive 1-based sentence sets for clear S/C.
CASES=[
 (521,34873974,"development",I,"Timing in the claim is relative to injury, not presentation; the abstract limits triage after symptom onset, not timing before injury.",[]),
 (1086,39281140,"development",S,"Explicit improved erectile function in men with SRI-associated dysfunction.",[[8],[10]]),
 (380,19005293,"development",S,"Memory T cell enhancement of cytokines and chemokines led to early influenza control.",[[3]]),
 (1132,33499189,"development",I,"Multivalent engagement and CD3 conformational change required; immunologic synapse or TCR microdomains not established.",[]),
 (1259,24341590,"holdout",S,"Genotype-linked CYP2D6 metabolism and clinical outcomes associated in the cohort, not a universal causal guarantee.",[[14],[7,8,12],[7,8,13]]),
 (1185,16737210,"holdout",S,"Simulation explicitly estimates conditional savings at the stated participation level.",[[11]]),
 (1089,17628888,"holdout",S,"Conclusion links Smc5/6 ATP binding, remodeling and SUMO ligase function.",[[9],[5,6,8]]),
 (1216,24142891,"holdout",I,"Cleavage in beta cells is stated, but the supplied abstract does not establish specifically human cells.",[]),
 (1359,11614737,"development",I,"Trial compares varenicline plus bupropion, not nicotine replacement therapies; distinction between prolonged abstinence and point prevalence.",[]),
 (903,10648422,"development",C,"PD-1 triggering induces rather than reduces IL-10 production.",[[5],[6]]),
 (728,36444198,"development",I,"Recruitment and immature monocyte frequency are measured, not a general inflammatory capacity comparison.",[]),
 (619,20888849,"development",C,"In the reported mouse model stromal depletion and higher vascular density improved delivery and produced transient stabilization, opposite the asserted direction; not universal.",[[3,4]]),
 (1336,27910499,"holdout",I,"Six-month cord blood recipients approximate healthy diversity; no baseline comparison demonstrating reduction or absence of reduction after transplantation.",[]),
 (171,12670680,"holdout",I,"Mouse causal effects and human association do not directly establish whether basophils counteract disease development in patients.",[]),
 (1382,17755060,"holdout",C,"PKC-zeta loss enhances tumorigenesis; the enzyme is described as a tumor suppressor.",[[2,4],[4,6],[6]]),
 (452,464511,"holdout",I,"Phenotypic variation among genetically identical cells is shown; the claim specifically concerns appreciable gene-expression variation, not measured explicitly.",[]),
]
ARMS=("plain","numbered_quote","reference")
NUMBERED_NOTE=" The source is prefixed with sentence numbers [S1], [S2], etc.; they are metadata, not part of the original text."
REF_INSTRUCTION=("Assess whether the supplied source excerpt supports, contradicts, or does not decide the claim. Return ONLY JSON with exactly these keys: label ('supported', 'contradicted', or 'insufficient'), evidence_ids (a list of at most three distinct integer sentence numbers from the supplied source, in increasing order; use an empty list if none is decisive), and reason (one concise sentence). For supported or contradicted, select at least one relevant sentence. Do not add any other keys. The source is prefixed with sentence numbers [S1], [S2], etc.; they are metadata, not part of the original text. Select original sentence numbers, never reproduce or rewrite a quotation.")
def sha(text): return hashlib.sha256(text.encode()).hexdigest()
def source_spans(sentences):
    spans=[];pos=0
    for i,t in enumerate(sentences,1):
        spans.append({"id":i,"start":pos,"end":pos+len(t),"text":t,"sha256":sha(t)})
        pos+=len(t)+1
    return spans
def reference_parse(raw,excerpt,spans):
    j=json.loads(raw.strip())
    if not isinstance(j,dict) or set(j)!={"label","evidence_ids","reason"}: raise ValueError("bad keys")
    if j["label"] not in (S,I,C): raise ValueError("bad label")
    ids=j["evidence_ids"];reason=j["reason"]
    if not isinstance(ids,list) or len(ids)>3 or any(type(x) is not int or not 1<=x<=len(spans) for x in ids) or ids!=sorted(set(ids)): raise ValueError("bad sentence IDs")
    if j["label"]!=I and not ids: raise ValueError("non-insufficient needs evidence")
    if not isinstance(reason,str) or not reason.strip() or len(reason)>500: raise ValueError("bad reason")
    picked=[spans[x-1] for x in ids]
    for s in picked:
        if excerpt[s["start"]:s["end"]]!=s["text"] or sha(s["text"])!=s["sha256"]: raise ValueError("source mapping mismatch")
    return {**j,"evidence_spans":picked}
def quote_ids(quote,excerpt,spans):
    if not quote: return []
    matches=[];pos=0
    while True:
        i=excerpt.find(quote,pos)
        if i<0:break
        ids=[s["id"] for s in spans if s["start"]<i+len(quote) and s["end"]>i]
        matches.append(ids);pos=i+1
    if not matches or any(x!=matches[0] for x in matches[1:]): return None
    return matches[0]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=pathlib.Path,required=True)
    p.add_argument("--archive",type=pathlib.Path,required=True)
    p.add_argument("--model",choices=["gemma4:12b","qwen3:14b"],required=True)
    p.add_argument("--split",choices=["development","holdout"],default="development")
    p.add_argument("--output",type=pathlib.Path,required=True)
    a=p.parse_args()
    root=a.repo/"evaluations"
    sci=runpy.run_path(str(root/"scifact-expert-v1/run.py"))
    claims,corp=sci["load_release"](a.archive)
    used_d={13734012,33872649};used_c=set()
    for name in ("scifact-expert-v1","scifact-contrastive-v1"):
        for x in json.loads((root/name/"manifest.json").read_text())["samples"]:
            used_d.add(x["doc_id"]);used_c.add(x["claim_id"])
    used_d.update(d for d,_,_ in runpy.run_path(str(root/"scifact-compound-pilot-v1/run.py"))["CASES"])
    pools=sci["candidate_pairs"](claims,corp)
    selected=[]
    for label in ("SUPPORT","CONTRADICT"):
        n=0
        for x in sorted(pools[label],key=lambda x:sha(f"sentence-reference-20261124/{label}/{x['claim_id']}/{x['doc_id']}")):
            if x["doc_id"] in used_d or x["claim_id"] in used_c or len(x["rationale_sentence_indices"])>3: continue
            used_d.add(x["doc_id"]);used_c.add(x["claim_id"]);n+=1
            selected.append((x["claim_id"],x["doc_id"],"development" if n<=4 else "holdout",label))
            if n==8:break
        if n!=8:raise ValueError("selection incomplete")
    if [x[:3] for x in CASES]!=[x[:3] for x in selected]:raise ValueError("selection mismatch")
    by={x["id"]:x for x in claims}
    cases=[]
    for (cid,d,split,operator,why,sets),(_,_,_,label) in zip(CASES,selected):
        if split!=a.split:continue
        c=by[cid];excerpt=sci["source_text"](corp[d])
        expert_sets=[[i+1 for i in r["sentences"]] for r in c["evidence"][str(d)] if r["label"]==label]
        cases.append({"id":f"{cid}:{d}","claim_id":cid,"doc_id":d,"claim":c["claim"],"source_sha256":sha(excerpt),"expert":S if label=="SUPPORT" else C,"expert_sets":expert_sets,"operator":operator,"operator_reason":why,"operator_sets":sets})
    shadow=sci["load_shadow"]();original_parser=shadow.parse_response
    base=json.loads((root/"evidence-switch-v1/protocol.json").read_text())["treatments"]["minimal"]
    instructions={"plain":base,"numbered_quote":base+NUMBERED_NOTE+" Quote only original source text, omit labels; preserve the original sentence separators.","reference":REF_INSTRUCTION}
    schedule=[(c,arm) for c in cases for arm in ARMS]
    random.Random(2026112405 if a.model=="gemma4:12b" else 2026112406).shuffle(schedule)
    with a.output.open("x",encoding="utf-8") as f:
        def save(x):
            f.write(json.dumps(x,ensure_ascii=False)+"\n");f.flush()
        save({"kind":"protocol","created":datetime.now(timezone.utc).isoformat(),"runner_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),"archive_sha256":sci["RELEASE_SHA256"],"backend_sha256":hashlib.sha256(pathlib.Path(sci["SHADOW"]).read_bytes()).hexdigest(),"model":a.model,"split":a.split,"instructions":instructions,"cases":cases})
        for c,arm in schedule:
            sentences=corp[c["doc_id"]]["abstract"];excerpt=sci["source_text"](corp[c["doc_id"]]);spans=source_spans(sentences)
            if sha(excerpt)!=c["source_sha256"] or any(excerpt[s["start"]:s["end"]]!=s["text"] for s in spans):raise ValueError("source identity")
            display=excerpt if arm=="plain" else "\n".join(f"[S{s['id']}] "+s["text"] for s in spans)
            shadow.INSTRUCTION=instructions[arm]
            shadow.parse_response=(lambda raw,ex:reference_parse(raw,ex,spans)) if arm=="reference" else original_parser
            prompt=shadow.prompt_for({"claim":c["claim"],"source_excerpt":display})
            out=shadow.run_ollama_one({"id":c["id"]+":"+arm,"prompt":prompt,"prompt_sha256":shadow.sha(prompt)},excerpt,a.model)
            out.pop("prompt",None)
            judgment=out.get("judgment")
            ids=(judgment["evidence_ids"] if arm=="reference" else quote_ids(judgment["evidence_span"],excerpt,spans)) if judgment else None
            row={"kind":"response","case_id":c["id"],"arm":arm,"source_sha256":sha(excerpt),"display_sha256":sha(display),"localized_ids":ids,**out}
            save(row)
            print(json.dumps({"id":row["id"],"label":(judgment or {}).get("label"),"operator":c["operator"],"expert":c["expert"],"ids":ids,"error":row.get("error")}),flush=True)
            if row.get("error") not in (None,"invalid_output","generation_truncated"):return 2
    return 0
if __name__=="__main__":sys.exit(main())
