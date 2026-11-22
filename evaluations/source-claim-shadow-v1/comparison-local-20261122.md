# Shadow-Pilot mit zwei lokalen Modellfamilien – 22. November 2026

**Beobachtung, keine Freigabeentscheidung.** Dieselben 18 vorregistrierten Quelle→Behauptung-Prompts aus PR #35 wurden in zwei getrennten, bereits installierten Offline-Modellen verarbeitet. Alle Referenzlabels, Quellenauszüge, Falldefinitionen, die Reihenfolge und die Metrikfunktionen blieben unverändert.

| Kennzahl | Qwen3 14B | Gemma4 12B |
|---|---:|---:|
| Auswertbare Antworten | 18/18 | 18/18 |
| Übereinstimmung mit vorregistriertem Gold | 17/18 | 18/18 |
| Quellgetrennter Holdout | 8/9 | 9/9 |
| Gestützte Claims erkannt | 6/6 | 6/6 |
| Widersprochene Claims erkannt | 6/6 | 6/6 |
| Aus dem Auszug nicht entscheidbare Claims erkannt | 5/6 | 6/6 |
| Falsche Widerspruchsvorwürfe unter 12 Nicht-Widersprüchen | 1 | 0 |
| Ungültige JSON-/Zitierformate | 0 | 0 |

## Einziger Modellkonflikt

**Fall `earthquake-magnitude-i`, USGS:** Der Beleg erklärt, dass ein Anstieg der Erdbebenmagnitude um eine ganze Einheit eine **Verzehnfachung der gemessenen seismischen Amplitude** bedeutet. Der Claim behauptet hingegen eine **Verzehnfachung der freigesetzten Energie**. Der vorgelegte Auszug enthält keine entsprechende Aussage über den Energiefaktor.

- **Vorregistriertes Referenzurteil:** `insufficient`, weil aus dem Auszug die Energiemenge nicht hervorgeht.
- **Qwen3:** `contradicted`. Seine Begründung „The excerpt refers to a tenfold increase in amplitude, not energy“ deutet bloß fehlende Aussage über Energie als inhaltliche Widerlegung.
- **Gemma4:** `insufficient`. Auch hier lautet die Begründung, der Auszug spreche von Amplitude statt Energie, ohne daraus eine Gegenbehauptung zu machen.

Das ist ein **belegbarer Fehlalarmtyp**: *Eine Quelle, die eine konkrete Aussage nicht enthält, widerlegt diese Aussage nicht automatisch.* Der Fehler liegt nicht in einem fehlenden Zitat; Qwen3 nannte eine tatsächlich vorkommende Quellenstelle, interpretierte aber ihre Reichweite falsch.

## Reproduzierbarkeit

- Identische 18 Prompt-SHA-256 in beiden Resultdateien und identischer Referenzdatensatz SHA-256 `8927332ab32f061676bc0676805816d102a3d73678fe2d0aec0b44b175ebfa64`.
- Backend: vorhandener Ollama-Server **0.40.16**, ohne externe API-Schlüssel, ohne Modelldownload, ohne neuen Dienst.
- Qwen3 `qwen3:14b` (Q4_K_M), Modell-Digest `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.
- Gemma4 `gemma4:12b` (Q4_K_M), Modell-Digest `6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b`.
- Qwen-Rohresultat SHA-256 `1b05ffc672f0c09554dec1487bbde070de853ff9a8c6fe6595fc8a78fffb4285`.
- Gemma-Rohresultat SHA-256 `7a1bd826ceaf977e518080d26ade81af9e8f30c105286b8fb16513448685f9df`.
- 36 von 36 Prompt- und Antwort-Hashes nachgerechnet, Modellurteile wurden nicht umklassifiziert oder erneut erzeugt.

**P2-Transportkorrektur nach diesen Rohmessungen:** Ein echter Codex-Reviewer wies darauf hin, dass Standard-`urllib` bei gesetztem `HTTP_PROXY` den angeblich lokalen Request umleiten könnte. Beim anschließenden Live-Check waren keine HTTP(S)-Proxy-Einstellungen gesetzt; das ist kein vollständiger historischer Netzwerkbeweis. Der Runner verwendet deshalb nun einen ausdrücklich proxyfreien lokalen Opener. Ein synthetischer, echter Gemma4-Test mit absichtlich ungültigem `HTTP_PROXY` erreichte weiterhin die Loopback-API und erhielt eine gültige JSON-Antwort. Die ursprünglichen 36 Rohurteile wurden **nicht** regeneriert.

## Grenzen und Entscheidung

Eine perfekt erfüllte kleine Testreihe bedeutet nicht, dass das Modell alle politischen, historischen, wissenschaftlichen und sprachlichen Widersprüche erkennt. Die sechs kurzen Quellen sind relativ eindeutige Beispiele; die Goldlabels stammen von einem einzelnen Operator, nicht von unabhängig annotierenden Experten. Der Entwicklungs-/Holdout-Split trennt Quellen, aber nicht den auswählenden Menschen oder die allgemeine Schwierigkeitsstufe.

Dies ist **keine direkte A/B-Verbesserungsquote gegenüber den drei ursprünglichen Fitness-Kanarien**: Die Modellprobe hat andere Quellenausschnitte verwendet. Ein falscher Widerspruch bei Qwen3 zeigt jedoch unmittelbar, welche Kategorien künftig gemessen werden sollten.

**Nutzwert jetzt:** Das Lab besitzt einen echten funktionsfähigen, freiwilligen Quelleninhalt-vs.-Claim-Vergleich sowie zwei vollständig nachvollziehbare Modellbaselines. **Nicht sinnvoll:** daraus jetzt einen verpflichtenden automatischen Wahrheitsrichter, neue Wortfilter oder weitere Freigabegates zu machen. Für eine belastbare Produktiventscheidung braucht es deutlich schwierigere, unabhängig annotierte und unveränderte Fälle.
