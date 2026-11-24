#!/usr/bin/env python3
"""Post-hoc diagnostic, NOT independent evidence, after failed compound pilot.

Question: did removing the companion clause contribute to the HES-1
entity/value error? Four already exposed documents: 40234452 (target B,
both models missed explicit mismatch), 21287352 and 20767776 (target B,
missing causal evidence), 35448676 (target B, explicit upstream/downstream
contradiction). No new claims, reference labels or sources. Both arms use
same minimal instruction plus same focus clarification. Only context
field differs: isolated repeats B; full includes A and B. Target and source
are unchanged. Fresh requests in seeded random order, no retry.
Strong mechanistic signal requires reproducing the error in isolated
arm on 40234452 for both models, both corrected to C under full context,
with all other targets correct in full and no validity regression. Raw
labels and exact-span validity separately. Even success does not establish
causality of token count or general efficacy; these cases are exposed.
Freeze this script before new calls. No production change.
"""
import argparse, hashlib, json, pathlib, random, runpy, sys
from datetime import datetime, timezone

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--repo",type=pathlib.Path,required=True)
 p.add_argument("--archive",type=pathlib.Path,required=True)
 p.add_argument("--model",choices=["gemma4:12b","qwen3:14b"],required=True)
 p.add_argument("--output",type=pathlib.Path,required=True)
 a=p.parse_args()
 root=a.repo/"evaluations"
 original=runpy.run_path(str(root/"scifact-compound-pilot-v1/run.py"))
 sci=runpy.run_path(str(root/"scifact-expert-v1/run.py"))
 _,corp=sci["load_release"](a.archive)
 shadow=sci["load_shadow"]()
 base=json.loads((root/"evidence-switch-v1/protocol.json").read_text())["treatments"]["minimal"]
 instruction=base+" Evaluate only the target claim. The original statement is provided only to preserve its context, not as a separate target."
 cases={d:atoms for d,sp,atoms in original["CASES"] if d in (40234452,21287352,20767776,35448676)}
 schedule=[(doc,arm) for doc in cases for arm in ("isolated","full")]
 random.Random(2026112403 if a.model=="gemma4:12b" else 2026112404).shuffle(schedule)
 with a.output.open("x",encoding="utf-8") as f:
  def save(x):
   f.write(json.dumps(x,ensure_ascii=False)+"\n")
   f.flush()
  save({"kind":"protocol","timestamp":datetime.now(timezone.utc).isoformat(),"runner_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),"original_runner_sha256":hashlib.sha256((root/"scifact-compound-pilot-v1/run.py").read_bytes()).hexdigest(),"archive_sha256":sci["RELEASE_SHA256"],"instruction":instruction,"model":a.model,"exposed_cases":True,"gold":{d:atoms[1][1] for d,atoms in cases.items()}})
  for doc,arm in schedule:
   atoms=cases[doc]
   excerpt=sci["source_text"](corp[doc])
   target=atoms[1][0]+"."
   context=atoms[0][0]+". Additionally, "+target if arm=="full" else target
   prompt=instruction+"\n\n[BEGIN SOURCE EXCERPT]\n"+excerpt+"\n[END SOURCE EXCERPT]\n\n[ORIGINAL STATEMENT]\n"+context+"\n\n[TARGET CLAIM]\n"+target
   out=shadow.run_ollama_one({"id":f"{doc}:{arm}","prompt":prompt,"prompt_sha256":shadow.sha(prompt)},excerpt,a.model)
   out.pop("prompt",None)
   row={"kind":"response","doc_id":doc,"arm":arm,"target":target,"context":context,"reference":atoms[1][1],"source_sha256":shadow.sha(excerpt),**out}
   save(row)
   print(json.dumps({"id":row["id"],"label":row.get("judgment",{}).get("label"),"reference":row["reference"],"error":row.get("error")}),flush=True)
   if row.get("error") not in (None,"invalid_output","generation_truncated"):
    return 2
 return 0

if __name__=="__main__":
 sys.exit(main())
