# Fitness → Semantic Shadow: direkter Anschluss-Test

## Fragestellung

Die ursprüngliche Fitness-Messung auf dem Claim-Audit-Lab fand 9/9 strukturelle Fehler, aber **0/3 semantische Fehler**. Die anschließende Textentailment-Stichprobe aus sechs öffentlichen Kurzquellen erreichte lokal 17/18 (Qwen3) beziehungsweise 18/18 (Gemma4). Das waren **andere Testfälle**. Die entscheidende noch fehlende Messung ist daher, ob die semantische Prüfmethode aus den **ursprünglichen drei Fehlerfällen selbst** zusätzliche Information gewinnt.

Dieses Skript bildet genau jene bestehenden Fitness-Mutationen auf die vorhandene dreiklassige semantische Shadow-Schnittstelle ab, ohne den ursprünglichen Test, seine 33 Validatoren oder seine Messdaten zu verändern.

## Vorab fixierte, unabhängig vom Modell definierte Fälle

Jeder der drei ursprünglichen Kanarien erhält eine **inhaltlich passende akzeptable Kontrolle** mit exakt demselben Quellenausschnitt. Das Modell sieht nur diesen Ausschnitt und die jeweilige Behauptung, nicht Ursprung, Erwartungslabel oder Metadaten.

| Mutationsfall aus dem Original | Semantisches Soll | Kontrolle |
|---|---|---|
| Dasselbe Ereignis: Behauptung 10:00, Beleg 11:00 | `contradicted` | Ereignis um 11:00: `supported` |
| Dasselbe Teilnehmerregister: behauptet 2, Beleg nennt 3 | `contradicted` | 3 Personen: `supported` |
| Antworttext behauptet zweifelsfreie Gewissheit, strukturiertes Urteil ist nur `plausible` | `insufficient` | Strukturiertes Urteil lautet `plausible`: `supported` |

**Wichtige Unterscheidung beim dritten Fall:** Aus einem bloß plausiblen Status ergibt sich keine Gewissheit. Der Status beweist aber auch nicht automatisch, dass die zugrunde liegende Aussage falsch ist. Das korrekte Schattenurteil über die behauptete Gewissheit ist deshalb `insufficient`, nicht pauschal `contradicted`. Zudem wird hier der **Answer-Receipt gegen die strukturierte Statusangabe** geprüft, nicht ein externer Primärquelleninhalt gegen eine Weltbehauptung. Diese Ebene bleibt getrennt ausgewiesen.

Die sechs Sollurteile sind im Skript vor den Modellaufrufen definiert. Die zu vergleichenden Akten entstehen reproduzierbar aus den bereits gemergten Originalmutatoren. Der Test speichert die SHA-256 der veränderten Claim-, Evidenz- und Receipt-Dateien. Dies sind **synthetische, vom gleichen Entwickler kuratierte Fälle** und keine unabhängige Expertenannotation.

## Erfolg und Grenzen

Es werden **Treffer bei den drei vorregistrierten Kanarien**, **Fehlalarme unter den drei gültigen Kontrollen** und **technische Ausfälle** getrennt angegeben. Ein bloßes syntaktisch korrektes Zitat zählt nicht als inhaltlich richtiges Urteil.

Der Vergleich ist keine Validierung realer historischer oder wissenschaftlicher Belege. Die zwei Evidenz-Fälle testen direkte Aussagen über ein und dasselbe künstliche Ereignis bzw. Register. Der Receipt-Fall prüft eine andere Informationsschicht (Gewissheitsbehauptung versus strukturiertem Status). Jede direkte Übertragung der Zahlen auf Politik oder allgemeine Wahrheitsqualität wäre unbegründet.

Die Shadow-Messung bleibt **optional und nicht blockierend**. Keine der 33 Regeln wird ersetzt; weder ein Sprachfilter noch eine neue Reviewpflicht wird eingeführt.

## Durchführung

```bash
python evaluations/fitness-semantic-bridge-v1/run.py
python evaluations/fitness-semantic-bridge-v1/run.py --execute --model qwen3:14b --output-dir /tmp/fitness-bridge-qwen3-v1
python evaluations/fitness-semantic-bridge-v1/run.py --execute --model gemma4:12b --output-dir /tmp/fitness-bridge-gemma4-v1
```

Die realen Modellaufrufe verwenden die bereits vorhandene Ollama-Schnittstelle auf `127.0.0.1:11434` mit dem proxyfreien Opener aus PR #36. Für jeden neuen Versuch ist ein frisches Ausgabeverzeichnis nötig. Originalantworten und Prompt-Hashes bleiben zur Gegenprüfung erhalten.

**Ziel dieses Schritts:** Die bisher nur indirekt behauptete Brücke zwischen struktureller Prüfung und semantischem Zusatznutzen mit den **identischen ursprünglichen Fehlerarten** sichtbar, reproduzierbar und falsifizierbar machen.
