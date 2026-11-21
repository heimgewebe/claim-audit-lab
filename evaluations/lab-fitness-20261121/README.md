# Claim-Audit-Lab: adversarialer Funktionstest

## Fragestellung

**Prüft das Lab echte Belegbeziehungen, oder bestätigt es vor allem die Form seiner eigenen YAML-Dateien?**

Dieser Test richtet sich gegen das Lab selbst, nicht gegen ein Sprachmodell. Er braucht keine API-Zugangsdaten und verwendet keine realen Personen, Institutionen oder strittigen Weltbehauptungen.

## Versuchsaufbau (vor dem ersten Lauf festgelegt)

Ausgangspunkt ist die bereits gültige Testakte `cases/sandbox/minimal-valid-case`. Für jede Herausforderung wird eine neue temporäre Kopie angelegt. Die **tatsächlich im Makefile eingetragenen produktiven Validatoren** laufen unverändert über jede Kopie. Es gibt keinen Dummy-Validator und keinen gesonderten Freigabepfad.

Drei voneinander getrennte Klassen von Gegenproben:

1. **Gültige Kontrollen**: unveränderte Akte sowie harmlose Umbenennung, Negation und ein Zitat zum wissenschaftlichen Konsens. Erwartung: Annahme ohne Fehlalarm.
2. **Strukturelle Fälschungen**: nicht vorhandene Quell- und Evidenz-IDs, kaputte Relationsziele, fehlender Quellengewichtungs-Audit, ein vorzeitig starkes Urteil, nicht übereinstimmender Answer-Receipt und fehlendes Red-Team-Dokument. Erwartung: Abweisung durch mindestens einen produktiven Validator.
3. **Semantische Täuschungen**: eine Zeitangabe, die der unmittelbar zugeordneten Evidenz widerspricht; eine Anzahl, die der Evidenz widerspricht; eine endgültig behauptete Gewissheit bei bloß plausibler Statusdeklaration. Erwartung an einen **idealen inhaltlichen Prüfer**: Abweisung. Diese Erwartung ist bewusst *keine* Behauptung, dass das aktuelle Lab dazu technisch fähig ist.

Insgesamt **16 Akten** (vier gültige Kontrollen, neun strukturelle Fehler und drei semantische Kanarien). Für die Fehlerklassen wird die gewünschte Reaktion **vor dem Testlauf im Code fixiert**, nicht nach den Ergebnissen angepasst.

## Messwerte

- **Strukturelle Erkennungsquote** = abgewiesene strukturelle Fehler / neun vorgegebene Fehler.
- **Fehlalarmquote** = abgewiesene gültige Kontrollen / vier Kontrollen.
- **Semantische Erkennungsquote** = abgewiesene semantische Kanarien / drei Fälle. Hier kann eine niedrige Quote die Grenze der automatischen Prüfung aufzeigen, ohne einen Validator-Programmierfehler zu beweisen.
- Laufzeitfehler und Timeouts zählen als **technische Fehler**, weder als korrekte Ablehnung noch als Erfolg.

Die Fälle enthalten die manipulierten Dateihashes, den erwarteten und tatsächlich beobachteten Status sowie die konkreten ablehnenden Validatoren und begrenzten Fehlerdiagnosen. Das Lab kann also nicht nachträglich behaupten, eine Täuschung erkannt zu haben, wenn alle produktiven Validatoren den Fall akzeptierten.

## Durchführung

```bash
python evaluations/lab-fitness-20261121/run.py
python evaluations/lab-fitness-20261121/run.py --execute --output-dir /tmp/claim-audit-lab-fitness-repeat-1
```

Der erste Aufruf ist ein kostenfreier Dry-Run mit allen festgelegten Erwartungen. Der zweite arbeitet ausschließlich auf temporären Kopien und schreibt nach allen Prüfungen `results.json` und `report.md` **in den neuen Ausgabeordner**. Ein neuer Durchlauf erhält einen neuen `--output-dir`; vorhandene Messdaten werden weder ersetzt noch stillschweigend gelöscht. Es sind keine neuen Gates, Dienste oder Abhängigkeiten jenseits der vorhandenen YAML- und Python-Testumgebung nötig.

## Erkenntnisgrenze

Eine korrekt verkettete Belegreferenz beweist **nicht**, dass der Inhalt der referenzierten Quelle die behauptete Schlussfolgerung trägt. Zwei formal kompatible Akten können gegensätzliche Tatsachen behaupten. Ein rein struktureller Validator kann diesen Widerspruch übersehen, ohne seinen dokumentierten Vertrag zu verletzen.

Deshalb werden Struktur- und Wahrheitskontrollen **niemals zu einer einzigen irreführenden Erfolgsquote addiert**. Der Test soll blinde Flecken sichtbar machen, nicht neue Sprachverbote erfinden. Die nächste empirische Ausbaustufe wäre eine kleine, extern annotierte Sammlung echter Primärquellen mit unabhängigen menschlichen Gegenbewertungen.

## Transparenz über einen Test-Harness-Fehler

Der erste Lauf lieferte ein irreführendes Teilresultat, weil bei mindestens einem produktiven Validator der Fall selbst statt seines übergeordneten Suchordners übergeben wurde. Die originale Messung ist unter `diagnostic-v0-skipped-case.json` gesondert erhalten und ausdrücklich **ungültig**. Der korrigierte Runner übergibt den Elternordner und wertet eine ausbleibende Fallentdeckung als technischen Fehler. Die ursprünglichen 16 Sollfälle und ihre erwarteten Reaktionen blieben unverändert.