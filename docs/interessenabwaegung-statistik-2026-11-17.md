# Interessenabwägung: anonyme Beliebtheits-Zählung der Merklisten (Art. 6 Abs. 1 lit. f DSGVO)

> **Stand 17.11.2026, Entwurf für die anwaltliche Durchsicht (Plan E4, Abschnitt 9.1, Schritt 6).** Erstellt von Claude, kein Rechtsrat. Vor dem Einschalten der Konten vom Auftraggeber freizugeben und abzulegen (Rechenschaftspflicht, Art. 5 Abs. 2 DSGVO).

## 1. Verarbeitung
- **Was:** Zählen, wie oft ein Event in Nutzerkonten gemerkt wurde, dazu erstes und letztes Merk-Datum je Event.
- **Datenbasis:** die Merklisten der Konten (Event-ID, Zeitpunkt des Merkens).
- **Wer sieht das Ergebnis:** nur Admins von dies.das, später im internen Dashboard (Phase 3). Das Ergebnis enthält **keine Nutzer-IDs** und keine Mailadressen, nur Summen je Event.
- **Wie technisch umgesetzt:** Datenbankfunktion `merk_statistik`. Sie läuft nur für Admins, zählt nur Konten mit `analyse_erlaubt = true` und schließt Events aus, die als besonders schützenswert gekennzeichnet sind (Plan 4.5, `database/konten_2026-11-16.sql`). Summen werden nicht gespeichert, sondern bei Bedarf neu gezählt.
- **Verantwortlicher:** Rocktician e. K. (dies.das.düsseldorf).

## 2. Berechtigtes Interesse (Stufe 1)
- Das Programm des Veranstaltungskalenders nach tatsächlichem Interesse ausrichten: welche Arten von Events, Orte und Stadtteile gefragt sind, welche Quellen sich lohnen.
- Beliebte Events auf der Website und in den Social-Media-Beiträgen hervorheben (z. B. „Viel gemerkt diese Woche“).
- Wirtschaftliches Interesse am Betrieb eines kostenlosen, werbearmen Angebots.

Das sind rechtlich anerkannte Interessen (Erwägungsgrund 47: auch wirtschaftliche Interessen). Sie sind klar benannt und bestehen tatsächlich.

## 3. Erforderlichkeit (Stufe 2)
- Ein milderes, gleich wirksames Mittel gibt es nicht. Ohne Zählung wüssten wir nicht, was Nutzer interessiert. Eine Befragung wäre weniger aussagekräftig und aufwendiger für die Nutzer.
- **Datenminimierung:**
  - Gezählt werden nur Summen je Event; keine Profile und keine Verknüpfung mit anderen Daten (keine Verknüpfung mit Google Analytics, kein Newsletter-Abgleich).
  - Es gibt keine eigene Tabelle mit Statistikdaten: Gezählt wird aus den Merklisten, die für das Konto ohnehin gespeichert sind (Art. 6 Abs. 1 lit. b).
  - Löscht jemand das Konto oder ein Event aus der Merkliste, zählt es sofort nicht mehr mit.
- Besonders schützenswerte Events (Art. 9) zählen **nie** mit, auch nicht mit Einwilligung (b).

## 4. Abwägung (Stufe 3)
**Interessen und Erwartungen der Betroffenen:**
- Die Merkliste dient den Nutzern selbst. Dass ein Kalender grob auswertet, was beliebt ist, ist nach unserer Einschätzung im Rahmen dessen, was Nutzer eines solchen Dienstes vernünftigerweise erwarten (Erwägungsgrund 47), zumal sie bei der Einrichtung des Kontos ausdrücklich darauf hingewiesen werden.
- Es betrifft nur Konten von Personen ab 16 Jahren.

**Risiken für die Betroffenen:**
- Rückschluss auf einzelne Personen: gering. Das Ergebnis enthält nur Summen. Bei sehr kleinen Zahlen (z. B. ein Event mit einer einzigen Merkung) könnten Admins theoretisch vermuten, wer es gemerkt hat, wenn sie zusätzliches Wissen haben. Gegenmaßnahme: siehe 5.
- Sensible Rückschlüsse: ausgeschlossen, weil Events nach Art. 9 nie mitzählen.
- Weitergabe: keine. Das Ergebnis bleibt intern; öffentlich gezeigt werden höchstens „viel gemerkte“ Events ohne genaue Zahlen.

**Schutzmaßnahmen:**
- **Gesonderter Hinweis auf das Widerspruchsrecht** (Art. 21 Abs. 4) auf der Abschlussseite, deutlich abgesetzt, mit einem Häkchen „Meine Merkliste nicht mitzählen“, und jederzeit im Konto.
- **Gezählt wird ein Konto erst, nachdem der Hinweis gezeigt wurde** (`analyse_erlaubt` ist bis dahin `false`).
- Widerspruch wirkt sofort und ohne Begründung (Art. 21 Abs. 1 wird großzügig umgesetzt: kein Prüfen „zwingender Gründe“).
- Zugriff nur für Admins; keine Nutzer-IDs im Ergebnis.
- Nachweis der Hinweis-Fassung pro Konto (`einwilligungen`, Art `analyse`).

**Ergebnis:** Die Interessen von dies.das überwiegen. Die Zählung ist geringfügig in die Rechte der Betroffenen eingreifend, transparent, jederzeit widersprechbar und schließt sensible Daten aus.

## 5. Offene Punkte für die Durchsicht
1. Soll das Dashboard Summen unter einer Mindestgröße (z. B. weniger als 3 Merkungen) ausblenden, um Rückschlüsse auf Einzelne bei kleinen Zahlen auszuschließen? Empfehlung: ja, wird mit Phase 3 umgesetzt.
2. Reicht die Formulierung des Hinweises auf der Abschlussseite (siehe `docs/einwilligungstexte-2026-11-17.md`, Abschnitt „analyse“) für Art. 21 Abs. 4 („ausdrücklich, verständlich und von anderen Informationen getrennt“)?
3. Ist die öffentliche Kennzeichnung „viel gemerkt“ ohne Zahlen von dieser Abwägung gedeckt, oder braucht sie eine eigene Prüfung?

**Freigegeben:** vom Anwalt bestätigt („zulässig mit Widerspruch“), vom Auftraggeber übernommen am 17.11.2026.
