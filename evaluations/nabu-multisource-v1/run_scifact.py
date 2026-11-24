#!/usr/bin/env python3
"""Nabu original multi-document scientific screen, frozen before inference.
Twelve German claims over four selected topic-disjoint sets of unchanged
public SciFact abstracts. Deliberate harder exploratory cases, not a random
sample or independent human gold. All documents are new to this project’s
model trials; related topics may have appeared before. Source-relative
judgment, not contemporary clinical advice or world-truth verification.
Use the actual Q3 Nabū model, natural German answer, thinking on, same
settings as the fictional multi-source screen. No private data, tools,
training or production mutation. Require correct substantive explanation,
not just label. Any proposed recurring deficit must be supported by at
least two independent families or a separately frozen replication; do not
train on a single ambiguous mistake. No selective retries.
"""
import argparse, hashlib, json, pathlib, random, re, runpy, sys, time, urllib.request
from datetime import datetime, timezone
MODEL="nabu-qwen38-q3-text-renderer35:20261124"
DIGEST="b6568abff17dd9045931cc29ca50fce45ab372ab55656961b0bd328b6068ba72"
OPTIONS={"temperature":0,"num_predict":1536,"num_ctx":16384}
INSTRUCTION=("Beurteile die Behauptung ausschließlich anhand der angegebenen historischen wissenschaftlichen "
"Quellenauszüge. Es geht um deren Aussagekraft, nicht um eine aktuelle medizinische Empfehlung. "
"Antworte zuerst mit BELEGT, WIDERLEGT oder OFFEN. BELEGT: Die Quellen tragen die Behauptung. "
"WIDERLEGT: Die Quellen zeigen einen mit ihr unvereinbaren Sachverhalt. OFFEN: Die Quellen entscheiden "
"sie nicht. Begründe dein Urteil in zwei bis vier natürlichen deutschen Sätzen; nenne die entscheidenden "
"Ergebnisse und gegebenenfalls die verbleibende Unsicherheit.")
FAMILIES={
 "prenatal": [(27123743,"6ccbcc310242760a4933d6512175cc3accfd654f951af73f4156af65b2b6c10e"),
 (23557241,"203aa73e1dad357a808ccd9b9bf9bbd402b976a2f6795f9241811589b9846296"),
 (17450673,"15631861cfcaa34311530399c3a7afca28698058185a7bd1c255ec7b5447b5be")],
 "heritability": [(19307912,"4149d8dd39dd7883f2fcdbb40b2aadce79c379be076825f0f985ba23630a1091"),
 (27393799,"b4c8c3eb813252e4dca7d5447a3a2833fc584ce834bd22bb5d9018ebc4e3916d"),
 (29025270,"9bc3198b22dca547b90e19af20942d068ded5359fdfac3f22d2301dd840d3e61")],
 "screening": [(27873158,"c0f58ad557cba325a727414aac513430b223a60c582b29d1f01dc890b23e9409"),
 (9764256,"b5583ec8b1d2c9a20b2241eeb583a43bff6aba0e4afd4163871c7076f0a6b131")],
 "mechanism": [(13940200,"627872a1eb79501eb20329ea4504da7fd5d8b21e0c7fed85211aa8ff37818414"),
 (11899391,"b30a0a6929c4c9cc9ee96b6647ee91f9fe5194f8da28511996f7b0482a52971c")]
}
# id, family, claim, gold, decisive rationale. Authored claims, not SciFact gold.
CASES=[
 ("prenatal-s","prenatal","Alle drei Übersichtsarbeiten berichten einen positiven Zusammenhang zwischen höherem Geburtsgewicht und dem späteren Brustkrebsrisiko in mindestens einem untersuchten Vergleich.","BELEGT","A combined RR 1.23; B RR 1.15; C positive OR across categories. Not universal across menopausal groups or causality."),
 ("prenatal-c","prenatal","Die Übersichtsarbeiten B und C berichten für Zwillingsstatus übereinstimmend einen erhöhten Punktschätzer des Brustkrebsrisikos.","WIDERLEGT","B reports RR 0.93; C reports some increased risk with heterogeneity. Do not conflate estimates with significant effect."),
 ("prenatal-i","prenatal","Die in den drei Übersichtsarbeiten berücksichtigten Primärstudien sind vollständig voneinander verschieden; keine Primärstudie ging in mehr als eine Übersicht ein.","OFFEN","Publication intervals and topics overlap; exact included-study lists and overlap are not provided."),
 ("heritability-s","heritability","In der Zwillingsstudie war der BMI getrennt aufgewachsener eineiiger Zwillinge positiv korreliert; in der Adoptionsstudie war das Körpergewicht der Adoptierten mit dem BMI ihrer biologischen, nicht aber ihrer Adoptiveltern verbunden.","BELEGT","B correlations 0.70/0.66; C strong biological-parent and no adoptive-parent association. Do not infer the relative influence on a particular individual."),
 ("heritability-c","heritability","In der Zwillingsstudie entfielen die genannten etwa 30 Prozent der BMI-Varianz auf die gemeinsame familiäre Kindheitsumwelt der Zwillinge.","WIDERLEGT","B attributes about 30% to individual-specific rather than shared environmental factors."),
 ("heritability-i","heritability","Eine gezielte Veränderung der Ernährung hätte bei den erwachsenen Studienteilnehmern keine Veränderung ihres durchschnittlichen BMI bewirkt.","OFFEN","Observational family/twin/adoption associations do not establish the result of a dietary intervention."),
 ("screening-s","screening","In beiden randomisierten Studien wurden in der zweiten Screeningrunde in der HPV-Interventionsgruppe weniger Zervixkarzinome festgestellt als in der jeweiligen Kontrollgruppe.","BELEGT","A 0 vs 9 invasive cancers; B 4 vs 14 cervical cancers. Detection/incidence is not mortality."),
 ("screening-c","screening","Die italienische Studie berichtet in der Altersgruppe von 35 bis 60 Jahren in der zweiten Runde für isoliertes CIN3 einen statistisch signifikant niedrigeren Nachweis unter HPV-Screening; die niederländische Studie berichtet in Runde zwei einen signifikant niedrigeren CIN3-oder-schlimmer-Nachweis.","WIDERLEGT","A CIN3 RR 0.48 CI 0.21–1.11 includes 1; B CIN3+ RR .73 CI .55–.96. Distinguish isolated CIN3 vs CIN3+ and combined CIN2/3."),
 ("screening-i","screening","Das HPV-basierte Screening verringerte in den Beobachtungszeiträumen beider Studien die zervixkarzinombedingte Sterblichkeit.","OFFEN","Both assess detection/diagnoses; no disease-specific mortality endpoint/result in either excerpt."),
 ("mechanism-s","mechanism","In den beiden Studien war ein IL2RA-bezogenes Typ-1-Diabetes-Risiko mit geringerer Immunantwort verbunden: in A niedrigere lösliche IL-2RA-Spiegel und in B verminderte IL-2-Responsivität sowie verminderte suppressive Treg-Funktion.","BELEGT","A risk genotypes associated with lower soluble IL2RA; B disease-associated haplotype with diminished responsiveness and Treg suppression in healthy people."),
 ("mechanism-c","mechanism","In der zweiten Studie war der untersuchte Autoimmunerkrankungs-Risikohaplotyp mit stärkerer IL-2-Responsivität und stärkerer suppressiver Funktion regulatorischer T-Zellen verbunden.","WIDERLEGT","B expressly reports diminished responsiveness and reduced suppressive capacity."),
 ("mechanism-i","mechanism","Eine therapeutische Erhöhung der IL-2-Responsivität würde bei den genetisch gefährdeten Studienteilnehmern die Neuerkrankungsrate an Typ-1-Diabetes senken.","OFFEN","Genetic associations and cellular function, no clinical intervention or incidence comparison of this treatment.")
]
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def prompt_for(c):
 return INSTRUCTION+"\n\nBehauptung: "+c["claim"]+"\n\n"+"\n\n".join("Quelle "+chr(65+i)+":\n"+t for i,t in enumerate(c["sources"]))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--repo",type=pathlib.Path,required=True);p.add_argument("--archive",type=pathlib.Path,required=True);p.add_argument("--output",type=pathlib.Path,required=True);a=p.parse_args()
 root=a.repo/"evaluations";sci=runpy.run_path(str(root/"scifact-expert-v1/run.py"));_,corp=sci["load_release"](a.archive)
 used={13734012,33872649}
 for name in ("scifact-expert-v1","scifact-contrastive-v1"):
  used.update(x["doc_id"] for x in json.loads((root/name/"manifest.json").read_text())["samples"])
 used.update(d for d,_,_ in runpy.run_path(str(root/"scifact-compound-pilot-v1/run.py"))["CASES"])
 used.update(d for _,d,*_ in runpy.run_path(str(root/"scifact-sentence-reference-v1/run.py"))["CASES"])
 used.update(d for d,*_ in runpy.run_path(str(root/"nabu-epistemic-baseline-v1/run.py"))["REAL"])
 docs=[d for fam in FAMILIES.values() for d,_ in fam]
 if len(docs)!=len(set(docs)) or set(docs)&used:raise ValueError("source overlap")
 sources={}
 for f,pairs in FAMILIES.items():
  src=[]
  for d,h in pairs:
   ex=sci["source_text"](corp[d])
   if sha(ex)!=h:raise ValueError("source mismatch")
   src.append(ex)
  sources[f]=src
 cases=[{"id":k,"family":f,"claim":c,"doc_ids":[d for d,_ in FAMILIES[f]],"source_hashes":[h for _,h in FAMILIES[f]],"sources":sources[f],"gold":g,"decisive_reason":why} for k,f,c,g,why in CASES]
 random.Random(2026112422).shuffle(cases)
 shadow=sci["load_shadow"]();shadow.OLLAMA_NUM_CTX=16384
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 def request(endpoint,payload=None,timeout=10):
  req=urllib.request.Request("http://127.0.0.1:11434/api/"+endpoint,data=None if payload is None else json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
  with opener.open(req,timeout=timeout) as f:raw=f.read()
  return json.loads(raw),hashlib.sha256(raw).hexdigest()
 def check():
  pre=shadow.verify_local_ollama_model(opener,MODEL)
  if pre.get("model_digest")!=DIGEST or pre.get("error"):raise RuntimeError("model identity changed")
  ps,_=request("ps")
  if any(m.get("name")!=MODEL for m in ps.get("models",[])):raise RuntimeError("another model loaded")
 check()
 with a.output.open("x",encoding="utf-8") as f:
  def save(x):f.write(json.dumps(x,ensure_ascii=False)+"\n");f.flush()
  save({"kind":"protocol","created":datetime.now(timezone.utc).isoformat(),"runner_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),"archive_sha256":sci["RELEASE_SHA256"],"model":MODEL,"digest":DIGEST,"options":OPTIONS,"think":True,"instruction":INSTRUCTION,"cases":[{k:v for k,v in c.items() if k!="sources"} for c in cases]})
  for c in cases:
   check();prompt=prompt_for(c);t=time.monotonic()
   data,h=request("generate",{"model":MODEL,"prompt":prompt,"stream":False,"think":True,"options":OPTIONS,"keep_alive":"3m","truncate":False,"shift":False},210)
   raw=data.get("response")
   row={"kind":"response","case_id":c["id"],"prompt_sha256":sha(prompt),"model_used":data.get("model"),"model_digest":DIGEST,"provider_response_sha256":h,"raw_response":raw,"response_sha256":sha(raw) if isinstance(raw,str) else None,"thinking_chars":len(data.get("thinking") or ""),"prompt_eval_count":data.get("prompt_eval_count"),"eval_count":data.get("eval_count"),"done_reason":data.get("done_reason"),"duration_seconds":round(time.monotonic()-t,2)}
   if data.get("model")!=MODEL or data.get("done") is not True:row["error"]="incomplete_or_wrong_model"
   elif type(data.get("prompt_eval_count")) is not int or not 1<=data["prompt_eval_count"]<14336:row["error"]="prompt_coverage_unverified"
   elif data.get("done_reason")=="length":row["error"]="generation_truncated"
   elif not isinstance(raw,str) or not raw.strip():row["error"]="empty_final"
   else:
    m=re.match(r"^\s*(?:\*\*)?(BELEGT|WIDERLEGT|OFFEN)\b",raw,re.I)
    row["label"]=m.group(1).upper() if m else None
    row["status"]="complete"
   save(row)
   print(json.dumps({"id":c["id"],"gold":c["gold"],"label":row.get("label"),"error":row.get("error"),"seconds":row["duration_seconds"]},ensure_ascii=False),flush=True)
   if row.get("error") not in (None,"generation_truncated"):return 2
 return 0
if __name__=="__main__":sys.exit(main())
