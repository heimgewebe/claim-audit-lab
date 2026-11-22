# Evidence-switch: wissenschaftliche Reaktion auf wechselnde Belege

Ziel: ein unveränderter Claim wird jeweils mit drei Belegzuständen konfrontiert: unterstützt, explizit widersprochen, nicht entscheidbar. Für jede Gruppe wird geprüft, ob eine KI ihr Urteil bei geändertem Beleg entsprechend ändert. Ein bloß ausgefülltes Prüfprotokoll reicht nicht.

12 synthetische Quellenfamilien, jeweils 3 Varianten, getrennt in 6 Development und 6 Holdout. Pro Familie ist der Claim byteidentisch. Die Belege sind bewusst konstruiert und keine authentischen Originalquellen. Die Goldlabels stammen allein vom Operator; keine unabhängige menschliche Annotation, kein allgemein gültiger Accuracy-Nachweis.

Erfolgskriterien vor dem ersten Modellaufruf: alle 36 gültigen Modellantworten pro Modell; 3/3 korrekte Zustandswechsel pro Familie; Falsch-Widersprüche unter den 12 insufficient-Zuständen getrennt; echte explizite Widersprüche bleiben erkennbar. Ausfälle des Providers nicht als semantische Fehler zählen.

Messung mit bestehenden lokalen Gemma4 12B und Qwen3 14B in unverändertem Prompt, ohne neue CI- oder Release-Gates. Gesonderte Holdout-Familien werden vorerst nicht geöffnet. Die Messung prüft Quellenreaktivität, nicht die Echtheit der Quellen oder allgemeine Erkenntnisfähigkeit.