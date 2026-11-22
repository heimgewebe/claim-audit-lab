# Direkter Anschluss-Test: ursprüngliche Fitness-Kanarien mit zwei Offline-Modellen

**Messung am 22. November 2026.** Die sechs Testfragen wurden vor der lokalen Inferenz auf dem Branch `eval/fitness-semantic-bridge-v1` im Präregistrierungscommit `1e7ebc1429ea993ef7adc43119959f03387061d3` fixiert. Das Skript leitet sie aus den **originalen gemergten Fitness-Mutationen** ab. Die drei bekannten Negativbeispiele wurden nicht nach Modellantworten umetikettiert oder neu formuliert.

| Originalfall | Vorab erwartetes Urteil | Qwen3 14B | Gemma4 12B |
|---|---|---|---|
| Ereignis: Behauptung 10:00, Beleg 11:00 | `contradicted` | `contradicted` | `contradicted` |
| Register: behauptet exakt 2, Beleg enthält 3 | `contradicted` | `contradicted` | `contradicted` |
| Antwort behauptet zweifelsfreie Gewissheit, strukturierter Status nur `plausible` | `insufficient` | `contradicted` | `contradicted` |

Die **drei passenden Positivkontrollen** mit denselben jeweiligen Belegen wurden in beiden Modellfamilien jeweils korrekt als `supported` beurteilt: **3/3 pro Modell, 0/3 Fehlalarme**.

## Was wurde tatsächlich verbessert?

Die ursprünglichen **33 rein strukturellen Validatoren akzeptierten alle drei semantisch problematischen Fälle** (0/3 erkannt). Mit dem bereits vorhandenen freiwilligen semantischen Prüfer und einem expliziten Brückentest wurden jetzt **beide ursprünglichen inhaltlichen Evidenz/Claim-Widersprüche** von Qwen und Gemma **jeweils korrekt** erkannt (2/2), ohne die drei gespiegelten gültigen Behauptungen abzulehnen.

Die dritte Abweichung ist **kein harter Modellbeweisfehler**: Beide Modelle verwerfen die überzogene Gewissheitsbehauptung als nicht gestützt, wählen aber `contradicted` statt des vorab festgelegten `insufficient`. Ein nur plausibler Status bietet keinen Beweis absoluter Gewissheit; ob er diese selbst widerlegt, hängt davon ab, ob `plausible` im verwendeten Urteilssystem als zur stärkeren Statusbehauptung unvereinbar definiert ist. Die vorab festgelegte Klassifikation `insufficient` ist epistemisch vorsichtiger. **Die Messzahl bleibt 2/3 exakt**, während alle drei überzogenen Negativfälle auf der groben Ebene „nicht unterstützt“ markiert wurden.

**Keine automatische Produktionserkennung behaupten:** Der Bridge-Test extrahiert gezielt Text und Status aus den drei bestehenden synthetischen Fitnessakten. Im regulären Lab-Prozess wurde damit **noch kein verpflichtender inhaltlicher Prüfschritt aktiviert** und kein Quellensystem automatisch erschlossen. Es ist ein getesteter Proof of Usefulness der optionalen Shadow-Methode und keine neue allgemeine Trefferquote.

## Rohdaten und Reproduzierbarkeit

- Qwen3 `qwen3:14b`: 6/6 gültige Antworten, 2/3 kanariengenau, 3/3 Positivkontrollen; `results.json` SHA-256 `e84763c36524af6b78a03b8ac58842661153e9523cda65c71e2d7fc1c199481e`.
- Gemma4 `gemma4:12b`: 6/6 gültige Antworten, 2/3 kanariengenau, 3/3 Positivkontrollen; SHA-256 `766c98f4d4165367a969f8dd88212c3475f6779d6ec401ecd84fa237cba9932a`.
- Alle 12 Original-Prompts und Rohantworten sind in den beiden Datensätzen enthalten, einschließlich SHA-256. Beide Modelle erhielten pro Fall bytegleiche Prompts, identische Mutatoren-Ausgaben und identische Sollklassen.
- Die Quelle ist eine **synthetische, eigens konstruierte Testakte** mit vorab deklarierten Urteilen, keine extern unabhängig annotierte Primärquelle. Der dritte Fall betrifft die metakognitive Aussage über den Verdict-Status und sollte nicht mit einer empirischen Quellenwiderlegung gleichgesetzt werden.
- Kein neues Modell installiert, keine Daten an Cloudanbieter geschickt, kein Sprachfilter, kein zusätzlicher Dienst und kein automatisches Freigabegate.

## Nächste sachliche Grenze

Der unmittelbare technische Nutzen ist jetzt auf **denselben zwei konkret bestätigten Evidenzfehlern** demonstriert. Für einen Einsatz auf längeren, mehrdeutigen realen Belegen braucht es unabhängig menschlich bewertete Fallakten, Quellencharakter und echte Gegenbelege. Ein automatischer Wahrheitsrichter wäre aufgrund dieser kleinen Stichprobe nicht gerechtfertigt.
