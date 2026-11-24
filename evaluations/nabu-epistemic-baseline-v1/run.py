#!/usr/bin/env python3
"""First target-model scientific baseline, frozen before inference, 2026-11-24.

Target: actual installed Nabū Qwen3.8-27B Q3_K_M text alias; exact digest.
NOT the normal HA conversation path, no devices/tools, no runtime change.
Match active HA thinking=True and context=16384 in both arms; temperature 0,
1536 max generated tokens (including thinking), independent requests, no retry.
Minimal full-claim prompt vs same + focused semantic comparison instruction.
No evidence representation change or atom decomposition. Test the cheapest
intervention first. Provider error/truncation is not semantic disagreement.
Keep all raw final responses; provider response hash, thinking length and
token counts, no private chat text or raw reasoning retained.
Four previously unused real SciFact abstracts (original source bytes, pinned
archive; selected before outcomes from first eight hash-ranked eligible docs
as non-pathogen method/comparison cases; not original SciFact gold labels).
Eight deliberately fictional English excerpt cases, four evidence pairs
(causality, institutional interests, archival provenance, quantity binding).
Operator-authored labels, no independent annotator. All claims source-relative.
All 24 planned calls must complete for the comparative screen. Strict score
= exact quote/JSON validator passes and gold label agrees; raw label separately;
inspect decisive evidence and reason (not mere substring presence).
A prompt is worth further testing only if at least two more raw correct
and at least two more strict correct out of 12, with no new raw label error,
no lost explicit contradiction and no degradation in evidence relevance.
Otherwise no promotion. Neither a positive nor a negative pilot decides
training efficacy. Training candidates should target recurring actual
semantic errors that simpler methods do not correct, not citation formatting
or artificially truncated thinking. A future source-family-disjoint holdout
and existing Nabū tool/dialog regression tests must precede adapter adoption.
No automatic training, merge or product switch follows this pilot.
"""
import argparse,hashlib,json,pathlib,random,runpy,sys,time,urllib.request,urllib.error
from datetime import datetime,timezone

MODEL="nabu-qwen38-q3-text-renderer35:20261124"
DIGEST="b6568abff17dd9045931cc29ca50fce45ab372ab55656961b0bd328b6068ba72"
S,I,C="supported","insufficient","contradicted"
OPTIONS={"temperature":0,"num_predict":1536,"num_ctx":16384}
RULE=" Before deciding, compare the actual relation in each part of the claim with the source: the same entities, quantities, comparator, time and causal direction. Distinguish an explicitly incompatible finding from missing evidence; support a conjunction only if all its parts follow. Assess the evidence independently of the author's institutional role."
# doc, source hash, full claim, label, rationale; scope explicitly relative to historical excerpt
REAL=[
 (4530659,"c8f72378cef571230d166f0199e244db02e4ad8f631ff28f3eb8bea31328ca2c","The review reports approved therapies for wet AMD and also reports approved treatments for dry AMD.",C,"The review explicitly says there were no approved treatments for dry AMD at the time of writing."),
 (12030318,"b96dbc0e64b6b3a4ab1c85403e90040bdcac254e7cfc6d066a0aa9ea02b334c4","The study identifies Mob1 as required for global patterning during development and regeneration in Stentor, and establishes that inhibiting Mob1 improves regeneration in human neurons.",I,"The Stentor result is explicit. The proposed human neuronal intervention is not studied."),
 (42693833,"a45633810a5cb7a440c919ec3bd1a367abcb41a7a7e869b7145f453c1cf7e1f4","The reported mouse findings link Foxp3-positive T cells to diversification of gut microbiota, and describe a reciprocal regulatory loop in which diversified microbiota facilitate expansion of those T cells.",S,"The second and fourth sentences establish both directions."),
 (24323369,"6c531594f2863bf78a0807eee29b778f22b2aa72a6a96bfdb1af23dbaced4f63","In the reported observational study, metformin alone had a higher ovulation rate than clomiphene alone and a higher pregnancy rate than clomiphene alone.",C,"75.4 versus 50 percent refers to ovulation; pregnancy rates were equivalent.")
]
# Fictional excerpts, author-created and matched within family. No actual events, named persons, companies or political groups.
SYNTH=[
 ("cause-a","causality","In a fictional district, participation in a new after-school program was voluntary. During the semester, average absence days in participating schools fell from 8 to 5. Other schools were not monitored, and the program began at the same time as a district-wide transport improvement. The evaluator reported the decline but did not estimate the effect of the program separately.","The study establishes that the new after-school program caused the reported reduction in average absence days.",I,"No comparator and concurrent transport change; the decline does not identify the program's effect."),
 ("cause-b","causality","In a fictional district, schools were randomly allocated to the new after-school program or usual provision. All schools received the same transport improvement. The prespecified analysis found a mean 3-day reduction in absence attributable to the program compared with usual provision, with a 95% confidence interval of 2 to 4 days. Attrition was negligible and balanced.","The study establishes that the new after-school program caused the reported reduction in average absence days.",S,"Randomized comparison and reported difference isolate the program in the study."),
 ("interest-a","institutional-evidence","In a fictional public records audit, a vendor had a financial interest in renewal. Archived access logs show that its report was uploaded two days after the scheduled committee review. The report's author said the delay was accidental. No instruction to withhold it was found; the investigation did not establish who decided the upload date.","The investigation establishes that the vendor deliberately withheld the report until after the committee review.",I,"Timing and financial interest are compatible with deliberate withholding but do not establish intent."),
 ("interest-b","institutional-evidence","In a fictional public records audit, a vendor had a financial interest in renewal. Archived access logs show that its report was uploaded two days after the scheduled committee review. Two independently retained copies of an authenticated instruction from the vendor's authorized director read: 'Do not release the completed report until the committee review is over.' The recipient confirmed carrying out that instruction.","The investigation establishes that the vendor deliberately withheld the report until after the committee review.",S,"Authenticated directive plus implementation evidence establish deliberate withholding."),
 ("archive-a","historical-provenance","In a fictional historical archive, an independently dated municipal ledger records a bridge closure on 18 May 1904. A contemporary maintenance diary records a closure on 20 May 1904. The researchers verified that the dates refer to the same bridge but could not reconcile the two accounts.","The two contemporary records agree that the bridge closed on 18 May 1904.",C,"Two records give different dates; agreement is explicitly absent."),
 ("archive-b","historical-provenance","In a fictional historical archive, an independently dated municipal ledger records a bridge closure on 18 May 1904. A contemporary maintenance diary independently records a closure on 18 May 1904. Researchers verified that both dates refer to the same bridge, but neither record establishes why it closed.","The two contemporary records agree that the bridge closed on 18 May 1904.",S,"Both independently record the same date; agreement is not a claim about cause."),
 ("binding-a","relation-binding","A fictional factory tested two changes. The reduction in energy consumption was 12% for press A and 30% for press B, respectively, relative to each press's own baseline. Output per hour was unchanged for both. The reductions were not an interval estimate.","The report records a 12% energy reduction for both presses and unchanged output per hour for both.",C,"Press B had a 30% reduction, not 12%; unchanged output does not rescue the conjunction."),
 ("binding-b","relation-binding","A fictional factory tested two changes. The reduction in energy consumption was 12% for press A and 12% for press B, respectively, relative to each press's own baseline. Output per hour was unchanged for both. The reductions were not an interval estimate.","The report records a 12% energy reduction for both presses and unchanged output per hour for both.",S,"Both reductions are 12%, and the output statement is explicit.")
]
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--repo",type=pathlib.Path,required=True)
 p.add_argument("--archive",type=pathlib.Path,required=True)
 p.add_argument("--output",type=pathlib.Path,required=True)
 p.add_argument("--think",choices=["true","false"],default="true")
 a=p.parse_args()
 root=a.repo/"evaluations"; sci=runpy.run_path(str(root/"scifact-expert-v1/run.py"))
 _,corp=sci["load_release"](a.archive)
 used={13734012,33872649}
 for name in ("scifact-expert-v1","scifact-contrastive-v1"):
  used.update(x["doc_id"] for x in json.loads((root/name/"manifest.json").read_text())["samples"])
 used.update(d for d,_,_ in runpy.run_path(str(root/"scifact-compound-pilot-v1/run.py"))["CASES"])
 used.update(d for _,d,*_ in runpy.run_path(str(root/"scifact-sentence-reference-v1/run.py"))["CASES"])
 pool=[d for d in corp if d not in used and 800<=len(sci["source_text"](corp[d]))<=1800]
 ranked=sorted(pool,key=lambda d:sha(f"nabu-epistemic-20261124/{d}"))[:8]
 if ranked!=[4530659,12030318,42693833,798152,21257564,27270151,24323369,5511240]:raise ValueError("source ranking drift")
 cases=[]
 for d,h,c,g,why in REAL:
  ex=sci["source_text"](corp[d])
  if sha(ex)!=h:raise ValueError("source digest mismatch")
  cases.append({"id":str(d),"kind":"scifact-original","family":str(d),"doc_id":d,"source_excerpt":ex,"source_sha256":h,"claim":c,"gold":g,"gold_reason":why})
 for k,f,ex,c,g,why in SYNTH:
  cases.append({"id":k,"kind":"fictional","family":f,"source_excerpt":ex,"source_sha256":sha(ex),"claim":c,"gold":g,"gold_reason":why})
 shadow=sci["load_shadow"]();shadow.OLLAMA_NUM_CTX=OPTIONS["num_ctx"]
 base=json.loads((root/"evidence-switch-v1/protocol.json").read_text())["treatments"]["minimal"]
 instructions={"minimal":base,"relations":base+RULE}
 schedule=[(c,arm) for c in cases for arm in instructions]
 random.Random(2026112419).shuffle(schedule)
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 def get_json(path,payload=None,timeout=10):
  req=urllib.request.Request("http://127.0.0.1:11434/api/"+path,data=None if payload is None else json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
  with opener.open(req,timeout=timeout) as res:raw=res.read()
  return json.loads(raw),hashlib.sha256(raw).hexdigest()
 def check():
  pre=shadow.verify_local_ollama_model(opener,MODEL)
  if pre.get("error") or pre.get("model_digest")!=DIGEST:raise RuntimeError("model identity unavailable or changed")
  ps,_=get_json("ps")
  if any(m.get("name")!=MODEL for m in ps.get("models",[])):raise RuntimeError("other model loaded; stop rather than evict")
  return pre
 check()
 with a.output.open("x",encoding="utf-8") as f:
  def save(r):f.write(json.dumps(r,ensure_ascii=False)+"\n");f.flush()
  save({"kind":"protocol","created":datetime.now(timezone.utc).isoformat(),"runner_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),"archive_sha256":sci["RELEASE_SHA256"],"model":MODEL,"digest":DIGEST,"think":a.think=="true","options":OPTIONS,"instructions":instructions,"cases":cases,"seed":2026112419})
  for c,arm in schedule:
   t=time.monotonic()
   row={"kind":"response","case_id":c["id"],"arm":arm,"source_sha256":c["source_sha256"],"model_digest":DIGEST}
   try:
    check();shadow.INSTRUCTION=instructions[arm];prompt=shadow.prompt_for(c);row["prompt_sha256"]=sha(prompt)
    payload={"model":MODEL,"prompt":prompt,"stream":False,"think":a.think=="true","format":"json","options":OPTIONS,"keep_alive":"3m","truncate":False,"shift":False}
    data,rawhash=get_json("generate",payload,timeout=210)
    row.update({"provider_response_sha256":rawhash,"model_used":data.get("model"),"raw_response":data.get("response"),"thinking_chars":len(data.get("thinking") or ""),"prompt_eval_count":data.get("prompt_eval_count"),"eval_count":data.get("eval_count"),"done_reason":data.get("done_reason")})
    if isinstance(row["raw_response"],str):row["response_sha256"]=sha(row["raw_response"])
    if data.get("model")!=MODEL or data.get("done") is not True:row["error"]="model_identity_or_completion"
    elif type(data.get("prompt_eval_count")) is not int or not 1<=data["prompt_eval_count"]<OPTIONS["num_ctx"]-2048:row["error"]="prompt_coverage_unverified"
    elif data.get("done_reason")=="length":row["error"]="generation_truncated"
    elif not isinstance(row["raw_response"],str):row["error"]="invalid_local_response"
    else:
     try:row["judgment"]=shadow.parse_response(row["raw_response"],c["source_excerpt"]);row["status"]="valid"
     except ValueError as e:row["error"]="invalid_output";row["parser_error"]=str(e)
   except (urllib.error.URLError,TimeoutError,OSError,RuntimeError,ValueError) as e:
    row["error"]="provider_or_preflight_error";row["error_type"]=type(e).__name__;row["error_detail"]=str(e)[:200]
   row["duration_seconds"]=round(time.monotonic()-t,2);save(row)
   print(json.dumps({k:row.get(k) for k in ("case_id","arm","status","error","duration_seconds","thinking_chars","eval_count")}|{"label":row.get("judgment",{}).get("label"),"gold":c["gold"]}),flush=True)
   if row.get("error") not in (None,"invalid_output","generation_truncated"):return 2
 return 0
if __name__=="__main__":sys.exit(main())
