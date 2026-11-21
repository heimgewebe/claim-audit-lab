# Semantische Gegenprüfung: Beleg → Behauptung (Shadow-Pilot v1)

## Ziel

Das Claim-Audit-Lab erkannte im adversarialen Fitness-Test 9 von 9 strukturellen Fehlern, aber keinen der 3 elementaren inhaltlichen Widersprüche. Dieses Experiment prüft deshalb **nur**, ob ein zusätzliches Sprachmodell aus einem vorgegebenen Belegauszug beurteilen kann, ob eine Behauptung durch den Auszug gestützt, widerlegt oder nicht entschieden wird.

Es ist **kein neuer Validator und kein Freigabegate**. Die 33 aktiven Lab-Validatoren, die CI-Pipeline und die Produktionsfälle werden nicht verändert.

## Vorregistriertes Referenzmaterial

`cases.json` enthält 18 Fälle aus sechs öffentlich zugänglichen US-Primärquellen:

- NASA JPL: durchschnittliche Entfernung zwischen Erde und Mond
- NOAA: Bedeckung der Erdoberfläche durch die Ozeane
- U.S. Census Bureau: Einwohnerzahl gemäß Volkszählung 2020
- USGS: Magnitude und gemessene Erdbebenamplitude
- NIST: historische Definition der Sekunde
- NASA Moon Facts: fehlende gefundene Belege für eigenes Leben auf dem Mond

Jeder Auszug besitzt genau drei unterschiedlich formulierte Behauptungen: eine **gestützte**, eine **widersprochene** und eine, über die **der konkret gegebene Auszug nicht entscheidet**. Insbesondere sind *fehlender Nachweis* und *Nachweis des Nichtvorhandenseins* zu unterscheiden. Die Entwicklungshälfte und die unangetastete Holdout-Hälfte bestehen aus je drei **verschiedenen Quellen** mit neun Fällen. Dieselbe Quelle kommt nicht in beiden Hälften vor.

**Wichtige Einschränkung:** Die Referenzlabels wurden vorab von einem einzigen Operator anhand der offiziellen Ausgangstexte kuratiert. Sie sind **keine unabhängig von mehreren Menschen annotierten Expertenurteile**. URLs und kurze Originalauszüge ermöglichen die Nachprüfung; die CLI holt die Quellen nicht selbst ab und bestätigt daher weder den Live-Webseitenstand noch die Authentizität einer Behauptung jenseits des Auszugs.

## Blindtest und Messung

Der Modellaufruf erhält ausschließlich die jeweilige Behauptung und den sichtbaren Textauszug. Er erhält ausdrücklich **nicht** das Referenzurteil, dessen Begründung, den Herausgeber, die URL oder die Zugehörigkeit zur Holdout-Gruppe. Die 18 Aufrufe laufen in separaten temporären, read-only Codex-Sessions mit dem vorhandenen Subscription-Modell GPT-6 Astra; kein API-Schlüssel oder neuer Dienst wird eingeführt.

Das Antwortobjekt enthält:

```json
{"label":"supported|contradicted|insufficient","evidence_span":"exakter Textabschnitt oder leer","reason":"kurze Begründung"}
```

Ein positives oder widersprechendes Urteil ohne wörtlich aus dem Auszug übernommene Belegstelle wird als **ungültiger Modell-Output**, nicht als Erfolg gezählt. Bei unzureichender Evidenz muss `evidence_span` leer sein. Auch Timeouts und defekte Antworten bleiben als Fehler mit Prompt- und Antwort-Hashes erhalten.

Gemessen werden Drei-Klassen-Trefferrate, getrennte Entwicklungs-/Holdout-Trefferrate, Precision und Recall je Klasse, fehlgeschlagene Aufrufe sowie **falsche Widerspruchsvorwürfe** bei tatsächlich gestützten oder unentscheidbaren Behauptungen. Diese Werte sind deskriptiv und erlauben keine populationsweite Unvoreingenommenheits- oder Wahrheitsaussage.

## Aufruf

```bash
python evaluations/source-claim-shadow-v1/run.py
python evaluations/source-claim-shadow-v1/run.py --execute --output-dir /tmp/claim-shadow-pilot-001
```

Der erste Aufruf zeigt nur die deterministisch gemischten 18 Fallkennungen, Splits und Prompt-Hashes. Die zweite Variante startet Abonnement-CLI-Aufrufe im vorhandenen Kontingent und schreibt `results.json` und `report.md` unter ein **neues** Verzeichnis. Ein bereits bestehendes Verzeichnis wird nicht überschrieben. Zur Wiederholung muss ein neuer Ausgabeort gewählt werden.

*Die CLI verwendet das bestehende Abonnement. Ob daraus zusätzliche Kosten, Nutzungslimits oder Provider-Sperren entstehen, richtet sich nach dem jeweiligen Kontingent.*

## Erkenntnisgrenzen und Entscheidungskriterium

1. **Quellenvertrauen** ist nicht dasselbe wie Quelleninhalt. Ein wörtlicher Textausschnitt kann falsch oder aus dem Zusammenhang gerissen sein.
2. **Exaktes Zitieren** garantiert keine korrekte logische Folgerung. Auch das Modell darf irren; die Referenzlabels müssen unabhängig nachprüfbar bleiben.
3. Ein hoher Wert auf sechs einfachen Auszügen beweist keine allgemeine Eignung bei langen Primärquellen, mehrdeutigen Aussagen, Argumentationsketten oder kontroverser Politik.
4. Es erfolgt keine automatische Integration in Produktions-Validatoren. Ein weiteres, unabhängig menschlich gegengeprüftes und umfangreicheres Holdout wäre die Voraussetzung, um einen dauerhaften semantischen Prüfdienst oder blockierende Ergebnisse überhaupt zu erwägen.

**Erfolg dieses Piloten:** Die bisherige Strukturprüfung erhält eine **getrennte messbare inhaltliche Versuchsspur**, die sich nicht hinter Wortverboten, optionalen Erklärungen oder bloß grüner CI versteckt.
