# Ungültiger Modelllauf: Codex-Zugriff abgelaufen (21.11.2026)

Diese Dateien sind **kein Ergebnis zur semantischen Modellqualität**.

Das im Git-Commit `fb06a842c03b367b54d9d1dccaa2aa75ecded8b2` vorregistrierte Experiment wurde mit allen 18 festgelegten Aufrufen versucht. Alle 18 CLI-Aufrufe endeten mit Exitcode 1 und **ohne Modellantwort**; die Roh-Prompts, Prompt-SHA-256, Statuscodes und SHA-256 der Standardfehlerausgaben bleiben vollständig in `results.json` erhalten. Es wurden 0 von 18 gültige Antworten erzielt.

Eine isolierte, nachgeschaltete Einzelfall-Gegenprobe belegt die Ursache:

- `codex login status` antwortete mit Exitcode 0 und „Logged in using ChatGPT“; diese Anzeige ist **kein Nachweis eines funktionsfähigen Tokens**.
- Ein echter `codex exec`-Aufruf meldete mehrfach `Failed to refresh token: Your access token could not be refreshed because your refresh token has expired` und `workspace routing discovery unauthorized (401)`.
- Das Modell hat daher **keine** der 18 Aussagen bewertet. Die vom alten Reporter angezeigte 0%-Trefferrate ist **nicht interpretierbar** und darf weder als Widerlegung noch als Erfolg einer semantischen Prüfung verwendet werden.

Die Ursprungsdateien bleiben unverändert; `results.json` hat den SHA-256-Wert `95fbfc108686e3a87e0d1ee98c469d8011b54c13a952a7e48d9e3a2035179b3b`. Der neuere Runner erkennt abgelaufene Authentifizierung und beendet weitere Modellaufrufe nach der ersten fehlgeschlagenen Probe mit sichtbaren „nicht ausgeführt“-Einträgen.

**Offen:** Die Anmeldung muss außerhalb dieses Tests wieder gültig werden. Eine erneute Ausführung benötigt einen **neuen** `--output-dir`. Es gibt keine erzwungene Anmeldung, keinen API-Key-Workaround, keine mehrfachen automatischen Wiederholungsversuche und kein neues Pflichtgate.

Die 18 vorab kuratierten Referenzlabels und der Prompt sind weiterhin unverändert gültig als Testdefinition, aber nicht als nachgewiesene Modellleistung.
