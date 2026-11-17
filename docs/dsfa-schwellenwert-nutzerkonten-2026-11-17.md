# Schwellenwertprüfung Datenschutz-Folgenabschätzung (Art. 35 DSGVO): Nutzerkonten

> **Stand 17.11.2026, Entwurf für die anwaltliche Durchsicht (Plan Abschnitt 9.1, Schritt 6).** Erstellt von Claude, kein Rechtsrat. Ergibt die Prüfung eine Pflicht zur vollständigen Datenschutz-Folgenabschätzung, werden die Konten nicht eingeschaltet, sondern es wird neu entschieden (Plan 9.1).

## 1. Verarbeitung im Überblick
Freiwillige Nutzerkonten auf diesdas.events (Plan `docs/plan-nutzerkonten-2026-11-16.md`):
- Anmeldung mit Mail und Passwort, Merkliste geräteübergreifend
- freiwillige Interessen für persönliche Vorschläge (Einwilligung)
- anonyme Beliebtheits-Zählung (berechtigtes Interesse, Widerspruch)
- freiwilliges Geburtsdatum für Geburtstagsmails (Einwilligung)
- Mindestalter 16

Erwarteter Umfang im ersten Jahr: 500 bis 1.000 Konten (Schätzung des Auftraggebers, 17.11.2026), regional (Düsseldorf).

## 2. Prüfung nach den Kriterien der Leitlinien WP 248 rev.01 (vom EDSA bestätigt)
Faustregel der Leitlinien: Treffen **zwei oder mehr** Kriterien zu, ist in der Regel eine DSFA durchzuführen. Die Aufsichtsbehörde kann im Einzelfall abweichen.

| Nr. | Kriterium | Trifft zu? | Begründung |
|---|---|---|---|
| 1 | Bewerten oder Einstufen (Scoring, Profiling) | **teilweise** | Persönliche Vorschläge aus Interessen und Merkliste (Phase 2), nur mit Einwilligung. Kein Scoring mit Folgen für die Person, keine Vorhersage von Verhalten oder Eigenschaften über Event-Vorlieben hinaus. Sensible Events fließen nie ein. |
| 2 | Automatisierte Entscheidung mit Rechtswirkung | nein | Keine Entscheidungen über Personen. Die Sperre bei einem Geburtsdatum unter 16 folgt einer Angabe der Person selbst und vertraglichen Regeln. |
| 3 | Systematische Überwachung | nein | Kein Tracking über Seiten hinweg, keine Standortdaten, keine Überwachung öffentlich zugänglicher Bereiche. |
| 4 | Sensible Daten (Art. 9) oder höchstpersönliche Daten | **teilweise** | Aus Merkungen bestimmter Events lassen sich Art.-9-Daten ableiten. Gegenmaßnahmen: automatische Kennzeichnung im Backend, ohne ausdrückliche Einwilligung keine Speicherung im Konto, nie in Vorschlägen oder Statistik (Plan E13, 4.8, 5.8). |
| 5 | Datenverarbeitung in großem Umfang | nein | Regionales Angebot, wenige Datenarten je Person. |
| 6 | Abgleichen oder Zusammenführen von Datensätzen | nein | Keine Verknüpfung mit anderen Quellen (kein Abgleich mit Google Analytics, Newsletter oder sozialen Netzwerken). |
| 7 | Daten schutzbedürftiger Betroffener | **gering** | Konten ab 16 Jahren; 16- und 17-Jährige sind möglich. Keine Kinder unter 16 (Sperre und Löschung). Keine Abhängigkeitsverhältnisse. |
| 8 | Innovative Nutzung neuer Technologien | nein | Übliche Konto- und Datenbanktechnik. |
| 9 | Hindert an der Ausübung eines Rechts oder an der Nutzung einer Leistung | nein | Die Website bleibt ohne Konto voll nutzbar. |

**Zwischenergebnis:** Zwei Kriterien treffen teilweise zu (1 und 4), eines nur gering (7). Für die sensiblen Daten (4) sind die wesentlichen Risiken durch die Gestaltung bereits gemindert: Ohne ausdrückliche Einwilligung werden sie gar nicht im Konto gespeichert, und sie werden nie ausgewertet. Das Profiling (1) beschränkt sich auf freiwillige, eingewilligte Event-Vorschläge.

## 3. Abgleich mit der Muss-Liste der Datenschutzkonferenz (DSK)
Die deutsche „Liste der Verarbeitungstätigkeiten, für die eine DSFA durchzuführen ist“ (Art. 35 Abs. 4 DSGVO) nennt typische Fälle wie umfangreiche Verarbeitung von Standort- oder Bewegungsdaten, Bonitäts-Scoring, umfangreiche Verarbeitung von Gesundheitsdaten oder Überwachung von Beschäftigten. **Nach unserer Durchsicht passt keiner dieser Fälle**, insbesondere gibt es keine umfangreiche Verarbeitung sensibler Daten. **[Abgleich mit der aktuell gültigen Fassung der Liste durch den Anwalt.]**

## 4. Ergebnis (Vorschlag)
Eine vollständige DSFA ist nach unserer Einschätzung **nicht erforderlich**. Die Gründe:
- keine Verarbeitung in großem Umfang, keine systematische Überwachung, kein Fall der DSK-Muss-Liste;
- sensible Ableitungen werden durch Gestaltung vermieden bzw. nur mit ausdrücklicher Einwilligung gespeichert und nie ausgewertet;
- Profiling nur als freiwillige, eingewilligte Vorschläge ohne Rechtsfolgen.

Weil zwei Kriterien teilweise berührt sind, wird diese Prüfung dokumentiert und überprüft, sobald sich etwas Wesentliches ändert, etwa:
- persönliche Vorschläge (Phase 2) mit KI oder zusätzlichen Datenquellen,
- deutlich mehr Konten als erwartet,
- eine App mit Push oder Standort,
- neue Kategorien von Daten.

## 5. Offene Punkte für die Durchsicht
1. Teilen Sie die Einschätzung, dass Kriterium 4 durch die Gestaltung (keine Speicherung ohne ausdrückliche Einwilligung, nie Auswertung) nicht voll zählt?
2. Abgleich mit der aktuellen DSK-Muss-Liste.
3. Soll für Phase 2 (persönliche Vorschläge) vorab eine eigene Schwellenwertprüfung erfolgen? Empfehlung: ja.

**Entscheidung:** Der Anwalt sieht keine zwingende Notwendigkeit einer DSFA. Der Auftraggeber hat am 17.11.2026 entschieden, die Konten ohne vollständige DSFA umzusetzen (eigene Verantwortung). · Nächste Überprüfung: vor Phase 2
