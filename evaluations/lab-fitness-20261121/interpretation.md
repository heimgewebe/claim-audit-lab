# Interpretation der adversarialen Lab-Fitness-Messung

**Status:** Ergebnis eines korrigierten und vorregistrierten Funktionstests. Die 16 Sollreaktionen waren bereits im Commit `a4889a38c7b9633ab89a80677689cfb1624214dd` festgelegt. Die notwendige Aufrufkorrektur liegt separat im Commit `017b644b07f7cb193e80f8d79f58062ff139ba6f`; sie veränderte keine Herausforderungen und keine erwarteten Antworten.

## Gemessene Ergebnisse

| Kategorie | Beobachtung | Interpretation |
|---|---:|---|
| Gültige Kontrollen | 4/4 akzeptiert | Keine Fehlalarme für diese vier kontrollierten Änderungen |
| Bekannte strukturelle Fehler | 9/9 abgewiesen | Die geprüften Referenz-, Provenienz- und Receipt-Konsistenzfehler werden erkannt |
| Bekannte semantische Täuschungen | 0/3 erkannt | Formal korrekt verknüpfte, aber inhaltlich falsche oder übertriebene Aussagen bleiben unbeanstandet |
| Technische Laufzeitfehler | 0/16 Fälle | Die korrigierte Prüfroutine konnte die Fälle tatsächlich durchlaufen |

Insgesamt wurden pro Testfall die **33 produktiven Makefile-Validatoren** auf einer isolierten Kopie des gültigen Sandbox-Falls aufgerufen. Der Ergebnisdatensatz enthält die Hashes der tatsächlich manipulierten Artefakte, die vollständigen Validatornamen bei Ablehnungen sowie deren begrenzte Diagnosen.

### Welche Täuschungen wurden übersehen?

1. **Zeitlicher Widerspruch:** Der Claim behauptet, dass ein Ereignis um 10:00 UTC stattgefunden habe. Die unmittelbar dafür angegebene Evidenz sagt: dasselbe Ereignis um 11:00 UTC. Alle Validatoren akzeptierten die Akte.
2. **Zählwiderspruch:** Der Claim behauptet genau zwei Personen in einem Register; der als Beleg verknüpfte Registerauszug nennt drei. Alle Validatoren akzeptierten die Akte.
3. **Rhetorische Aufwertung:** Die freie Antwortprosa bezeichnet einen Claim als endgültig und zweifelsfrei bewiesen, während das strukturierte Urteil weiterhin nur `plausible` lautet. Alle Validatoren akzeptierten die Akte.

Das sind **vorab festgelegte semantische Negativkontrollen**. Die drei Fälle wurden nicht nachträglich passend zum Verhalten der Validatoren ausgewählt.

## Was das Lab nachweislich leistet

Das Lab prüft in dieser Stichprobe **strukturelle Integrität** gut: ungültige referenzierte Quellen und Evidenzen, fehlende Red-Team-Akten, fehlende Quelle-Gewichtungsbelege, voreilige Statusaufwertung und Widerspruch zwischen strukturiertem Claim und strukturiertem Answer-Receipt werden erkannt. Die harmlosen Zitate und Negationen werden nicht wegen ihrer Wörter gesperrt.

**Das ist nicht dasselbe wie Tatsachenprüfung.** Das Lab verifiziert nicht, ob ein zitierter Quelleninhalt die behauptete Aussage logisch und empirisch trägt. Auch der Abgleich von freier Prosa mit strukturiertem Urteil ist gegenwärtig nicht semantisch zuverlässig.

## Vorläufige Entscheidung

**Keine neue Wortzensur und keine zusätzliche verpflichtende Freigabearchitektur einführen.** Die nächsten Verbesserungen sollten anhand echter, unabhängig annotierter Primärquellen zeigen, ob eine getrennte semantische Gegenprüfung einen messbaren Zusatznutzen liefert. Sie sollte nicht bloß mit mehr Schlüsselwörtern die drei synthetischen Fälle erkennen und andere Formulierungen weiterhin übersehen.

Dies ist ein gezielter Fitness-Test, keine populationsweite Fehlerrate des gesamten Labs oder aller denkbaren Claimtypen. Die drei semantischen Fälle liegen derzeit außerhalb der starken, mechanisch prüfbaren Garantien der vorhandenen Validatoren; sie zeigen eine **Produktgrenze**, nicht notwendigerweise einen Implementierungsfehler in einem bestimmten Schema.

## Prüfbarkeit

- Gültige Rohmessung: `results.json`, SHA-256 `aefcd8b10cadd0c9041ec10a1344577d137369192f287026a88a1b44ca9a8296`.
- Nachgewiesener Test-Harness-Fehler im ersten Durchlauf: `diagnostic-v0-skipped-case.json`, **ungültig**, SHA-256 `04262b4c994dcf184a94cbfac7eb45059877a2a414017bdeb6ff7794a99d8e63`.
- Alle 16 Fälle und Erwartungen sind im vorab festgelegten Python-Code reproduzierbar.
