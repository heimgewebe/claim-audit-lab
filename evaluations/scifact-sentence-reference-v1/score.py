#!/usr/bin/env python3
"""Offline scoring/reconstruction for the frozen sentence-reference pilot.

No inference; no changed reference labels. Strict score uses original parser
acceptance plus label match. Raw-label accuracy is a diagnostic separate
from valid output. Sentence coverage is NOT proof of semantic entailment.
"""
import argparse,hashlib,json,pathlib,runpy,sys
from collections import Counter

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--repo",type=pathlib.Path,required=True)
 p.add_argument("--archive",type=pathlib.Path,required=True)
 p.add_argument("--runner",type=pathlib.Path,required=True)
 p.add_argument("results",type=pathlib.Path,nargs="+")
 a=p.parse_args()
 s=runpy.run_path(str(a.repo/"evaluations/scifact-expert-v1/run.py"))
 _,corpus=s["load_release"](a.archive); shadow=s["load_shadow"](); orig=shadow.parse_response
 runner=runpy.run_path(str(a.runner));sha=runner["sha"];arms=runner["ARMS"]
 S,I,C=runner["S"],runner["I"],runner["C"]
 expected_hash=hashlib.sha256(a.runner.read_bytes()).hexdigest()
 for f in a.results:
  rows=[json.loads(x) for x in f.read_text().splitlines()]
  h=rows[0]; assert h["runner_sha256"]==expected_hash
  assert h["archive_sha256"]==s["RELEASE_SHA256"]
  cases={c["id"]:c for c in h["cases"]}; idx={}
  for r in rows[1:]:
   c=cases[r["case_id"]];arm=r["arm"];doc=corpus[c["doc_id"]]
   excerpt=s["source_text"](doc);spans=runner["source_spans"](doc["abstract"])
   display=excerpt if arm=="plain" else "\n".join(f"[S{x['id']}] "+x["text"] for x in spans)
   assert sha(excerpt)==c["source_sha256"]==r["source_sha256"]
   assert sha(display)==r["display_sha256"]
   shadow.INSTRUCTION=h["instructions"][arm]
   assert sha(shadow.prompt_for({"claim":c["claim"],"source_excerpt":display}))==r["prompt_sha256"]
   assert (c["id"],arm) not in idx
   raw=r.get("raw_response")
   raw_label=None
   if isinstance(raw,str):
    assert sha(raw)==r["response_sha256"]
    try:
     d=json.loads(raw);raw_label=d.get("label") if isinstance(d,dict) else None
    except ValueError:pass
   if r.get("status")=="valid" or r.get("error")=="invalid_output":
    try:j=runner["reference_parse"](raw,excerpt,spans) if arm=="reference" else orig(raw,excerpt)
    except ValueError:assert r["error"]=="invalid_output"
    else:
     assert r["status"]=="valid" and r["judgment"]==j
     ids=j["evidence_ids"] if arm=="reference" else runner["quote_ids"](j["evidence_span"],excerpt,spans)
     assert ids==r["localized_ids"]
   strict=r.get("judgment",{}).get("label") if r.get("status")=="valid" else None
   selected=set(r.get("localized_ids") or [])
   idx[c["id"],arm]={"case":c,"strict":strict,"raw":raw_label,"ids":r.get("localized_ids"),"expert_coverage":any(set(x)<=selected for x in c["expert_sets"]),"operator_coverage":any(set(x)<=selected for x in c["operator_sets"]),"error":r.get("error"),"reason":r.get("judgment",{}).get("reason"),"raw_response":raw,"prompt_tokens":r.get("prompt_eval_count",0),"output_tokens":r.get("eval_count",0)}
  print(f.name,"sha256",hashlib.sha256(f.read_bytes()).hexdigest(),"completed",len(idx),"expected",len(cases)*len(arms))
  for arm in arms:
   rr=[v for (cid,aa),v in idx.items() if aa==arm]
   print(arm,json.dumps({"attempted":len(rr),"valid":sum(r["strict"] is not None for r in rr),"raw_operator":sum(r["raw"]==r["case"]["operator"] for r in rr),"strict_operator":sum(r["strict"]==r["case"]["operator"] for r in rr),"raw_expert":sum(r["raw"]==r["case"]["expert"] for r in rr),"strict_expert":sum(r["strict"]==r["case"]["expert"] for r in rr),"false_support_raw":sum(r["raw"]==S and r["case"]["operator"]!=S for r in rr),"false_refutation_raw":sum(r["raw"]==C and r["case"]["operator"]!=C for r in rr),"missed_C_raw":sum(r["raw"]!=C and r["case"]["operator"]==C for r in rr),"expert_coverage":sum(r["expert_coverage"] for r in rr),"operator_SC_coverage":sum(r["operator_coverage"] for r in rr),"prompt_tokens":sum(r["prompt_tokens"] or 0 for r in rr),"output_tokens":sum(r["output_tokens"] or 0 for r in rr),"errors":dict(Counter(r["error"] or "none" for r in rr))}))
  for cid,c in cases.items():
   print(cid,"operator",c["operator"],"expert",c["expert"])
   for arm in arms:
    r=idx.get((cid,arm))
    if r: print(" ",arm,r["strict"],r["raw"],r["ids"],"expertcov",r["expert_coverage"],"opcov",r["operator_coverage"],r["error"],r["reason"])
  for base in ("plain","numbered_quote"):
   new=[]
   for cid,c in cases.items():
    b=idx.get((cid,base));t=idx.get((cid,"reference"))
    if not b or not t:continue
    g=c["operator"]
    if (t["raw"]==S and g!=S and b["raw"]!=S) or (t["raw"]==C and g!=C and b["raw"]!=C) or (g==C and b["raw"]==C and t["raw"]!=C):
     new.append(cid)
   print("new raw semantic errors against",base,new)
if __name__=="__main__":main()
