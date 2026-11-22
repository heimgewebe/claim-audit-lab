# Vorregistrierte Holdout-Entscheidung – 2026-11-22

Goldlabels und source-disjunkte Splits: Commit f6beb4c. Jede Klasse je Split: 3/9. Die Labels wurden vor Modellaufrufen festgelegt und werden nicht verändert.

Development / Gemma4 12B: Original 9/9, Candidate v1 nach Parserkorrektur 9/9 (0 falsche Widersprüche).
Development / Qwen3 14B: Original 6/9 (3 falsche Widersprüche), Candidate v1 7/9 (2 falsche Widersprüche), Candidate v2 7/9 (2 falsche Widersprüche).

Der erste v1-Probelauf wurde nach einer gültigen inhaltlichen INSUFFICIENT-Antwort formal abgewiesen, weil das Modell eine wörtliche Belegstelle für die fehlende Kausalitätsuntersuchung zitierte. Diese zusätzliche Schema-Sperre wurde minimal repariert; der ursprüngliche Fehlversuch bleibt separat erhalten.

**Auswahl vor Öffnung des Holdouts:** Candidate v1 gegen unveränderte Originalinstruktion auf denselben 9 Holdoutfällen und beiden Modellen vergleichen. V2 bringt im Development keinen Zusatznutzen und wird nicht weiterverfolgt. Eine Verbesserung im kleinen Holdout ist nur ein Hinweis, kein allgemeiner Wissenschaftlichkeitsnachweis. Keine automatische Freigabe durch diesen Vergleich.

Prüfziele: echte Widersprüche weiter erkennen, unzureichende Evidenz nicht fälschlich widerlegt nennen, Formfehler von Semantikfehlern trennen. Unabhängige menschliche Goldannotatoren fehlen weiterhin.
