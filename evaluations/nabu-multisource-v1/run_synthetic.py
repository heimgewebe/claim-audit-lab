#!/usr/bin/env python3
"""Nabu epistemic multi-source screen v1, frozen before inference.
A new single-turn German evidence-synthesis experiment; not a dialogue
replay or source-revision runner. All examples are explicitly constructed,
not actual findings. No tools, devices, personal information, or training.
Four families, each supported/contradicted/undecided. Claims concern
the described facts rather than assertions about their proof. The same
minimal task instruction, active model digest, temperature, context and
thinking setting throughout. The model sees only claim and sources.
Judge label AND decisive reasoning manually; no quote-format gate.
A first substantive-error screen, not independent human annotation,
a general accuracy estimate or an adapter holdout. If an actual error
recurs in distinct families, investigate the mechanism and a small
prompt alternative before preparing new supervised data. If no such
errors, do not infer a need for fine-tuning. Preserve every response.
"""
import argparse,hashlib,json,pathlib,random,re,runpy,sys,time,urllib.request
from datetime import datetime,timezone

MODEL="nabu-qwen38-q3-text-renderer35:20261124"
DIGEST="b6568abff17dd9045931cc29ca50fce45ab372ab55656961b0bd328b6068ba72"
OPTIONS={"temperature":0,"num_predict":1536,"num_ctx":16384}
INSTRUCTION=("Alle folgenden Quellen beschreiben ein fiktives Untersuchungsbeispiel. "
"Beurteile die Behauptung innerhalb dieses Beispiels ausschließlich anhand der verfügbaren Quellen. "
"Antworte zuerst mit BELEGT, WIDERLEGT oder OFFEN. BELEGT: Die Quellen tragen die Behauptung. "
"WIDERLEGT: Die Quellen zeigen einen mit ihr unvereinbaren Sachverhalt. "
"OFFEN: Die Quellen entscheiden sie nicht. Begründe dein Urteil in zwei bis vier natürlichen deutschen Sätzen; "
"nenne die entscheidenden Ergebnisse und gegebenenfalls die verbleibende Unsicherheit.")
# family, variant, object claim, sources, expected label, decisive reason.
CASES=[
 ("aggregation","s","Mit dem neuen Prüfverfahren war die Fehlerquote innerhalb beider Belastungsgruppen niedriger als mit dem alten Verfahren.",
 ["Quelle A: Gesamtbericht: Beim neuen Prüfverfahren gab es 21 Fehler unter 220 Prüfungen, beim alten 76 Fehler unter 220 Prüfungen. Die Gruppen waren unterschiedlich zusammengesetzt.",
 "Quelle B: Geprüfte Einzeltabelle. Geringe Belastung: neu 9 Fehler unter 180 Prüfungen, alt 4 unter 40. Hohe Belastung: neu 12 unter 40, alt 72 unter 180. Die Gruppen umfassen alle Prüfungen."],
 "BELEGT","Geringe Belastung 5% vs 10%; hohe 30% vs 40%. Beide innerhalb der Gruppe niedriger."),
 ("aggregation","c","Mit dem neuen Prüfverfahren war die Fehlerquote innerhalb beider Belastungsgruppen niedriger als mit dem alten Verfahren.",
 ["Quelle A: Gesamtbericht: Beim neuen Prüfverfahren gab es 38 Fehler unter 220 Prüfungen, beim alten 74 Fehler unter 220 Prüfungen. Die Gruppen waren unterschiedlich zusammengesetzt.",
 "Quelle B: Geprüfte Einzeltabelle. Geringe Belastung: neu 18 Fehler unter 180 Prüfungen, alt 2 unter 40. Hohe Belastung: neu 20 unter 40, alt 72 unter 180. Die Gruppen umfassen alle Prüfungen."],
 "WIDERLEGT","Geringe Belastung 10% vs 5%; hohe 50% vs 40%. Die günstigere Gesamtrate ist kein Nachweis für die Gruppenbehauptung."),
 ("aggregation","i","Mit dem neuen Prüfverfahren war die Fehlerquote innerhalb beider Belastungsgruppen niedriger als mit dem alten Verfahren.",
 ["Quelle A: Gesamtbericht: Beim neuen Prüfverfahren gab es 38 Fehler unter 220 Prüfungen, beim alten 74 unter 220. Die Einzeldaten sind nicht erhalten.",
 "Quelle B: Die 220 Prüfungen je Verfahren verteilen sich auf zwei Belastungsgruppen. Die Gruppengrößen und gruppenspezifischen Fehlerzahlen sind nicht bekannt. Keine weitere Messung liegt vor."],
 "OFFEN","Gesamtraten entscheiden die einzelnen Gruppenraten nicht; Zusammensetzung und gruppenspezifische Zahlen fehlen."),
 ("measurement","s","Die Masse der Probe beim dokumentierten Wiegevorgang lag bei mindestens 50 Kilogramm.",
 ["Quelle A: Zeitgleiches Waagenprotokoll A: 52 kg. Die unabhängige Kalibrierprüfung begrenzt den absoluten Messfehler auf 1 kg.",
 "Quelle B: Der zusammenfassende Bericht übernimmt lediglich den Wert aus A; keine neue Messung.",
 "Quelle C: Eine unabhängig kalibrierte Referenzwaage maß dieselbe unveränderte Probe beim gleichen Vorgang mit 51,5 kg; maximaler absoluter Messfehler 0,5 kg."],
 "BELEGT","Beide unabhängigen kalibrierten Messintervalle liegen vollständig oberhalb 50; B ist keine weitere Bestätigung."),
 ("measurement","c","Die Masse der Probe beim dokumentierten Wiegevorgang lag bei mindestens 50 Kilogramm.",
 ["Quelle A: Zeitgleiches Waagenprotokoll A: 52 kg.",
 "Quelle B: Der zusammenfassende Bericht übernimmt lediglich den Wert aus A; keine neue Messung.",
 "Quelle C: Die nachgewiesene Fehlkalibrierung der Waage A betrug plus 5 kg bei diesem Vorgang. Das korrigierte Ergebnis 47 kg hat einen maximalen absoluten Messfehler von 1 kg. Eine unabhängig kalibrierte Referenzwaage bestätigte 47 kg mit maximal 1 kg Messfehler."],
 "WIDERLEGT","Korrigierte und unabhängige Intervalle 46–48 kg; B dupliziert den falschen Rohwert."),
 ("measurement","i","Die Masse der Probe beim dokumentierten Wiegevorgang lag bei mindestens 50 Kilogramm.",
 ["Quelle A: Zeitgleiches Waagenprotokoll A: 52 kg.",
 "Quelle B: Der zusammenfassende Bericht übernimmt lediglich den Wert aus A; keine neue Messung.",
 "Quelle C: Eine unabhängige Waage protokollierte für dieselbe Probe beim selben Vorgang 47 kg. Für keine der Waagen sind Kalibrierungsdaten erhalten; die Prüfung konnte nicht feststellen, welcher Messwert zuverlässig ist. Die Probe wurde später zerstört."],
 "OFFEN","Unaufgelöster Konflikt zweier unabhängiger Messungen; B zählt nicht zusätzlich und keine Messung ist verifiziert überlegen."),
 ("causal","s","Die neue Beschichtung verringerte im untersuchten Prozess die mittlere Ausschussquote gegenüber der alten Beschichtung.",
 ["Quelle A: Im Vorher-nachher-Bericht ging die mittlere Ausschussquote von 8 auf 4 Prozent zurück; zugleich wurde die Temperaturregelung erneuert.",
 "Quelle B: Eine anschließende randomisierte Vergleichsstudie bei identischer Temperaturregelung ermittelte für die neue gegenüber der alten Beschichtung eine kausale Differenz von minus 3 Prozentpunkten (95%-Konfidenzintervall minus 4 bis minus 2). Die Auswertung war vollständig, keine weiteren Prozessänderungen."],
 "BELEGT","Der kontrollierte randomisierte Vergleich trennt die Beschichtung von der Temperaturregelung und ergibt eine Verringerung."),
 ("causal","c","Die neue Beschichtung verringerte im untersuchten Prozess die mittlere Ausschussquote gegenüber der alten Beschichtung.",
 ["Quelle A: Im Vorher-nachher-Bericht ging die mittlere Ausschussquote von 8 auf 4 Prozent zurück; zugleich wurde die Temperaturregelung erneuert.",
 "Quelle B: Eine anschließende randomisierte Vergleichsstudie im selben Prozess bei identischer Temperaturregelung ermittelte für die neue gegenüber der alten Beschichtung eine kausale Differenz von plus 3 Prozentpunkten (95%-Konfidenzintervall plus 2 bis plus 4). Die Auswertung war vollständig, keine weiteren Prozessänderungen."],
 "WIDERLEGT","Die kontrollierte kausale Differenz ist eine Erhöhung; die unkontrollierte frühere Verbesserung kann durch Temperatur erklärt sein."),
 ("causal","i","Die neue Beschichtung verringerte im untersuchten Prozess die mittlere Ausschussquote gegenüber der alten Beschichtung.",
 ["Quelle A: Im Vorher-nachher-Bericht ging die mittlere Ausschussquote von 8 auf 4 Prozent zurück; zugleich wurde die Temperaturregelung erneuert.",
 "Quelle B: Die nachträgliche Prüfung bestätigte beide Änderungen und die Rohzahlen. Es gab keine unabhängige Vergleichsgruppe oder Variation der beiden Maßnahmen. Der Effekt der Beschichtung wurde nicht getrennt gemessen."],
 "OFFEN","Rückgang belegt, aber Beschichtungseffekt nicht identifiziert; Temperatur als alternative Erklärung."),
 ("completeness","s","Alle vier Messstationen waren im Zeitraum von 10 bis 11 Uhr mindestens einmal außer Betrieb.",
 ["Quelle A: Die vorläufige Meldung spricht von vier betroffenen Stationen und beruht nur auf telefonischen Hinweisen.",
 "Quelle B: Die abschließende Prüfung der vollständigen, authentifizierten Betriebsprotokolle dokumentiert in diesem Zeitraum Ausfälle bei A, B, C und D. Die vier Stationen sind der gesamte Bestand."],
 "BELEGT","Vollständige verifizierte Protokolle bestätigen jede der vier Stationen."),
 ("completeness","c","Alle vier Messstationen waren im Zeitraum von 10 bis 11 Uhr mindestens einmal außer Betrieb.",
 ["Quelle A: Die vorläufige Meldung spricht von vier betroffenen Stationen und beruht nur auf telefonischen Hinweisen.",
 "Quelle B: Die abschließende Prüfung der vollständigen, authentifizierten Betriebsprotokolle dokumentiert in diesem Zeitraum Ausfälle bei A, B und C. Station D war nachweislich durchgehend betriebsbereit. Die vorläufige Meldung ist in diesem Punkt korrigiert."],
 "WIDERLEGT","D durchgehend betriebsbereit; die All-Aussage ist falsch, auch wenn drei Ausfälle gesichert sind."),
 ("completeness","i","Alle vier Messstationen waren im Zeitraum von 10 bis 11 Uhr mindestens einmal außer Betrieb.",
 ["Quelle A: Die vorläufige Meldung spricht von vier betroffenen Stationen und beruht nur auf telefonischen Hinweisen.",
 "Quelle B: Die abschließende Prüfung der authentifizierten Betriebsprotokolle dokumentiert in diesem Zeitraum Ausfälle bei A, B und C. Für Station D fehlt das Protokoll. Der telefonische Hinweis zu D war keinem eindeutigen Zeitraum zuzuordnen und wurde als nicht belastbar zurückgezogen."],
 "OFFEN","D unbekannt; weder ein Ausfall bei D noch durchgehende Betriebsbereitschaft nachgewiesen.")
]
def sha(t):return hashlib.sha256(t.encode()).hexdigest()
def prompt_for(c):return INSTRUCTION+"\n\nBehauptung: "+c["claim"]+"\n\n"+"\n\n".join(c["sources"])
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--repo",type=pathlib.Path,required=True)
 p.add_argument("--output",type=pathlib.Path,required=True)
 a=p.parse_args()
 sci=runpy.run_path(str(a.repo/"evaluations/scifact-expert-v1/run.py"))
 shadow=sci["load_shadow"]();shadow.OLLAMA_NUM_CTX=16384
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 def request(endpoint,payload=None,timeout=10):
  req=urllib.request.Request("http://127.0.0.1:11434/api/"+endpoint,data=None if payload is None else json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
  with opener.open(req,timeout=timeout) as f:raw=f.read()
  return json.loads(raw),hashlib.sha256(raw).hexdigest()
 def check():
  p=shadow.verify_local_ollama_model(opener,MODEL)
  if p.get("model_digest")!=DIGEST or p.get("error"):raise RuntimeError("model identity changed")
  ps,_=request("ps")
  if any(m.get("name")!=MODEL for m in ps.get("models",[])):raise RuntimeError("another model loaded")
 cases=[{"id":f+"-"+v,"family":f,"claim":c,"sources":s,"source_hashes":[sha(x) for x in s],"gold":g,"decisive_reason":why} for f,v,c,s,g,why in CASES]
 random.Random(2026112421).shuffle(cases)
 check()
 with a.output.open("x",encoding="utf-8") as f:
  def save(x):f.write(json.dumps(x,ensure_ascii=False)+"\n");f.flush()
  save({"kind":"protocol","created":datetime.now(timezone.utc).isoformat(),"runner_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),"model":MODEL,"digest":DIGEST,"options":OPTIONS,"think":True,"instruction":INSTRUCTION,"cases":cases})
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
