#!/usr/bin/env python3
"""Post-hoc diagnostic on six EXPOSED compound cases, not an independent holdout.

Question: do source sentence references solve the actual quote transport
failures observed on compound claims? Use unchanged full claims from
scifact-compound-pilot-v1, never split them. Four prior citation failures
(28419824, 17333231, 34747208, 42404093), correlation/causality boundary
21287352 and entity/value control 40234452. Three fresh paired one-call
arms identical to the sentence-reference pilot (plain, numbered quote,
reference). Source identities unchanged, no selective retries.
Strong diagnostic signal requires baseline plain at least two invalid
responses across twelve model/case pairs, reference at least two more
strict correct labels than both quote arms, no new raw-label error,
no loss of previously recognized contradiction, and actual relevant
reconstructed evidence. No promotion on exposed cases, even if passes.
No holdout from the failed single-claim experiment is accessed.
"""
import argparse, hashlib, json, pathlib, random, runpy, sys
from datetime import datetime, timezone

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--repo",type=pathlib.Path,required=True)
 p.add_argument("--archive",type=pathlib.Path,required=True)
 p.add_argument("--model",choices=["gemma4:12b","qwen3:14b"],required=True)
 p.add_argument("--output",type=pathlib.Path,required=True)
 a=p.parse_args();root=a.repo/"evaluations"
 pilot=runpy.run_path(str(root/"scifact-sentence-reference-v1/run.py"))
 compound=runpy.run_path(str(root/"scifact-compound-pilot-v1/run.py"))
 sci=runpy.run_path(str(root/"scifact-expert-v1/run.py"))
 _,corp=sci["load_release"](a.archive)
 shadow=sci["load_shadow"]();orig=shadow.parse_response
 base=json.loads((root/"evidence-switch-v1/protocol.json").read_text())["treatments"]["minimal"]
 instructions={"plain":base,"numbered_quote":base+pilot["NUMBERED_NOTE"]+" Quote only original source text, omit labels; preserve the original sentence separators.","reference":pilot["REF_INSTRUCTION"]}
 wanted={28419824,17333231,34747208,42404093,21287352,40234452}
 cases=[]
 for d,split,atoms in compound["CASES"]:
  if d in wanted:
   claim=atoms[0][0]+". Additionally, "+atoms[1][0]+"."
   cases.append({"id":str(d),"doc_id":d,"claim":claim,"source_sha256":pilot["sha"](sci["source_text"](corp[d])),"operator":compound["aggregate"]([x[1] for x in atoms]),"atoms":atoms})
 if len(cases)!=6:raise ValueError("wrong diagnostic cases")
 schedule=[(c,arm) for c in cases for arm in pilot["ARMS"]]
 random.Random(2026112407 if a.model=="gemma4:12b" else 2026112408).shuffle(schedule)
 with a.output.open("x",encoding="utf-8") as f:
  def save(x):
   f.write(json.dumps(x,ensure_ascii=False)+"\n");f.flush()
  save({"kind":"protocol","created":datetime.now(timezone.utc).isoformat(),"runner_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),"reference_pilot_sha256":hashlib.sha256((root/"scifact-sentence-reference-v1/run.py").read_bytes()).hexdigest(),"original_compound_sha256":hashlib.sha256((root/"scifact-compound-pilot-v1/run.py").read_bytes()).hexdigest(),"archive_sha256":sci["RELEASE_SHA256"],"model":a.model,"exposed_cases":True,"instructions":instructions,"cases":cases})
  for c,arm in schedule:
   ex=sci["source_text"](corp[c["doc_id"]]);spans=pilot["source_spans"](corp[c["doc_id"]]["abstract"])
   if pilot["sha"](ex)!=c["source_sha256"] or any(ex[s["start"]:s["end"]]!=s["text"] for s in spans):raise ValueError("source identity")
   display=ex if arm=="plain" else "\n".join(f"[S{s['id']}] "+s["text"] for s in spans)
   shadow.INSTRUCTION=instructions[arm]
   shadow.parse_response=(lambda raw,source:pilot["reference_parse"](raw,source,spans)) if arm=="reference" else orig
   prompt=shadow.prompt_for({"claim":c["claim"],"source_excerpt":display})
   out=shadow.run_ollama_one({"id":c["id"]+":"+arm,"prompt":prompt,"prompt_sha256":shadow.sha(prompt)},ex,a.model)
   out.pop("prompt",None)
   j=out.get("judgment")
   ids=(j["evidence_ids"] if arm=="reference" else pilot["quote_ids"](j["evidence_span"],ex,spans)) if j else None
   row={"kind":"response","case_id":c["id"],"arm":arm,"source_sha256":pilot["sha"](ex),"display_sha256":pilot["sha"](display),"localized_ids":ids,**out}
   save(row)
   print(json.dumps({"id":row["id"],"label":(j or {}).get("label"),"operator":c["operator"],"ids":ids,"error":row.get("error")}),flush=True)
   if row.get("error") not in (None,"invalid_output","generation_truncated"):return 2
 return 0
if __name__=="__main__":sys.exit(main())
