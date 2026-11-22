# Erste funktionsfähige semantische Shadow-Auswertung – Qwen3 14B

**Gemessen am 22. November 2026.** Die 18 Eingaben, drei Goldklassen und der quellgetrennte Entwicklungs-/Holdout-Split waren bereits im PR #35 (`fb06a842c03b367b54d9d1dccaa2aa75ecded8b2`) festgelegt. Das Ollama-Backend wurde als separater Commit `3fe8aa7820a2a7617c12a53697a2562a54758ac1` **vor der lokalen Modellmessung** veröffentlicht. Die Testdaten, Textauszüge und Prompts blieben unverändert.

## Beobachtete Ergebnisse

- **18/18** unabhängige Modellaufrufe ergaben formal gültige dreiklassige Urteile mit den geforderten Belegstellen.
- **17/18** Urteile stimmen mit den vorab von einem Operator kuratierten Goldlabels überein (94,4 %).
- **8/9** der quellgetrennten Holdout-Fälle stimmen überein (88,9 %), Entwicklung **9/9**.
- `supported`: **6/6**; `contradicted`: **6/6**; `insufficient`: **5/6** korrekte Einordnung.
- **Ein falscher Widerspruch** in zwölf nicht-widersprochenen Fällen (8,3 %). Die gemessene Precision von `contradicted` beträgt 6/7.

**Wichtiger Gegenfall:** `earthquake-magnitude-i` (USGS) sagt, dass eine ganze Magnitudenstufe die **gemessene Amplitude** verzehnfacht. Die zu bewertende Behauptung spricht von der **freigesetzten Energie**. Das Modell klassifizierte `contradicted` und zitierte die Amplitudenstelle. Das vorab annotierte Urteil ist `insufficient`: Der sichtbare Auszug enthält keinen Faktor für die Energieabgabe. Diese Fehlklassifizierung illustriert gerade, warum eine korrekte wörtliche Quellenstelle noch keine korrekte logische Folgerung garantiert.

## Technische Reproduzierbarkeit

- Bereits installierter Ollama-Server: **0.40.16**, ausschließlich lokaler Endpoint `127.0.0.1:11434`.
- Modell: **`qwen3:14b`**, installierter Digest `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`, Quantisierung **Q4_K_M**.
- Temperatur **0**, maximal 256 Antworttokens, kein Reasoning-Modus, JSON-Ausgabe.
- `results.json` SHA-256: `1b05ffc672f0c09554dec1487bbde070de853ff9a8c6fe6595fc8a78fffb4285`. Alle 18 Prompt- und Antwort-Hashes wurden unabhängig nachgerechnet; Goldbasis SHA-256 `8927332ab32f061676bc0676805816d102a3d73678fe2d0aec0b44b175ebfa64`.
- Kein Cloud-Login, keine API-Schlüssel, kein neues Modell heruntergeladen, kein neuer Dienst eingerichtet und kein verpflichtender Validator verändert.

## Methodische Grenzen

Die sechs Quellenauszüge sind kurz und relativ eindeutig; sie testen **Textentailment**, nicht die Echtheit, Aktualität oder Vollständigkeit einer Primärquelle. Ein Vorab-Label eines einzelnen Operators ist nicht unabhängige Mehrpersonen-Annotation. Auch der NIST-Auszug ist eine ausdrücklich ältere SI-Definition und darf nicht als Beweis der aktuell gültigen Definition behandelt werden. Eine Stichprobe von nur 18 Fällen ist zu klein für verallgemeinerbare Erfolgsversprechen.

Vor allem wurde auf diesem Qwen-Pilot **nicht dieselbe Menge wie bei den drei semantischen Fitness-Kanarien** getestet. Die 17/18 sind damit kein direkter Nachweis einer Verbesserung um 17/18 gegenüber den 33 strukturellen Validatoren. Der sinnvolle Folgeschritt ist ein weiterer unveränderter Modellvergleich und eine spätere unabhängige Quell-/Claim-Annotation, weiterhin **Shadow-only**.
