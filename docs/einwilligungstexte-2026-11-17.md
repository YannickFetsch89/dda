# Einwilligungstexte der Nutzerkonten (Entwurf zur Freigabe)

> **Stand 17.11.2026, vom Anwalt freigegeben** („in Ordnung wie vorgeschlagen“, Mitteilung des Auftraggebers vom 17.11.2026). Plan Abschnitte 4.4, 5.3, Schritt 6.
> - Das sind die Wortlaute, die die Website heute anzeigt (Quelle im Code: `web/lib/konto/texte.ts`; Registrierungsformular in `web/components/konto-zugang.tsx`).
> - Erklärtexte duzen (Entscheidung des Auftraggebers vom 17.11.2026). Die Häkchen-Sätze stehen in der Ich-Form der erklärenden Person.
> - **Nach der Freigabe:** Jeder Wortlaut kommt unverändert als Zeile in `public.einwilligungstexte`, mit der Versionskennung aus der Tabelle (per SQL-Datei, die der Auftraggeber ausführt). Erst danach können Registrierung, Abschlussseite und Schalter Nachweise speichern.
> - Ändert sich ein Wortlaut später, bekommt er eine neue Version (z. B. `interessen-2026-12`). Die alte Zeile bleibt als Nachweis erhalten.

| Art | Version | Wo gezeigt | Handlung im Nachweis |
|---|---|---|---|
| mindestalter | `mindestalter-2026-11` | Registrierungsformular; ersatzweise `/konto/willkommen` | `registrierung` bzw. `abschlussseite`; bei Sperre unter 16: `altersgrenze` |
| nutzungsbedingungen | `nutzungsbedingungen-2026-11` | Registrierungsformular | `registrierung` |
| personalisierung (a) | `interessen-2026-11` | Abschlussseite, Konto, „Interessen ändern“ | `abschlussseite`, `konto_schalter`, `interessen_aendern` |
| sensible_events (b) | `sensible-events-2026-11` | Abschlussseite, Konto | `abschlussseite`, `konto_schalter` |
| analyse (c, Hinweis und Widerspruch) | `analyse-hinweis-2026-11` | Abschlussseite, Konto | `abschlussseite`, `konto_schalter` |
| geburtstagsmail (d) | `geburtstagsmail-2026-11` | Abschlussseite, Konto, Abmeldelink | `abschlussseite`, `konto_schalter`, `abmeldelink` |

> **Hinweis zur Version der Nutzungsbedingungen:** Die Kennung `nutzungsbedingungen-2026-11` bezeichnet die Fassung der Nutzungsbedingungen, die bei der Registrierung gilt. Ändert der Anwalt den Text oder geht er erst im Dezember online, wird die Kennung angepasst (z. B. `nutzungsbedingungen-2026-12`), und zwar gleich auf der Seite `/nutzungsbedingungen`, im Code und in der Tabelle.

---

## mindestalter · `mindestalter-2026-11`
**Häkchen (Pflicht, nicht vorangekreuzt):**
> Ich bin mindestens 16 Jahre alt.

## nutzungsbedingungen · `nutzungsbedingungen-2026-11`
**Satz über dem Button „Konto anlegen“ (mit Links):**
> Mit „Konto anlegen“ akzeptierst du unsere Nutzungsbedingungen (mit Widerrufsbelehrung). Wie wir deine Daten verarbeiten, steht in der Datenschutzerklärung.

**Darunter (Hinweis nach Art. 13 DSGVO, kein Nachweis):**
> Wir nutzen deine Adresse für die Anmeldung und dein Konto. Mehr dazu in der Datenschutzerklärung.

## personalisierung (a) · `interessen-2026-11`
**Einleitung über dem Fragebogen (kein Nachweis):**
> **Was interessiert dich?** Ein paar kurze Fragen, damit wir dir passende Events vorschlagen können. Am Ende entscheidest du, ob wir deine Antworten speichern.

**Häkchen auf der Abschlussseite (nur sichtbar, wenn Antworten vorliegen; nicht vorangekreuzt):**
> Ich willige ein, dass dies.das meine Antworten in meinem Konto speichert und zusammen mit meiner Merkliste nutzt, um mir passende Events vorzuschlagen. Sensible Events (siehe unten) fließen nie in Empfehlungen ein. Ich kann das jederzeit im Konto widerrufen. Dann werden meine Antworten sofort gelöscht.

## sensible_events (b) · `sensible-events-2026-11`
**Erklärtext (immer sichtbar):**
> **Datenschutz ist uns hier besonders wichtig.** Manche Events lassen Rückschlüsse auf sehr persönliche Dinge zu: Gesundheit, Religion oder Weltanschauung, sexuelle Orientierung oder geschlechtliche Identität, politische Meinung, Gewerkschaftszugehörigkeit oder ethnische Herkunft. Merkst du dir solche Events, speichern wir sie ohne deine ausdrückliche Einwilligung nur auf dem Gerät, auf dem du sie gemerkt hast, und nicht in deinem Konto. Auf anderen Geräten siehst du sie dann nicht. Für Empfehlungen und Statistiken nutzen wir sie nie, auch nicht mit Einwilligung.

**Häkchen (ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a DSGVO, nicht vorangekreuzt):**
> Ich willige ausdrücklich ein, dass dies.das auch solche Events, die ich mir merke, in meinem Konto speichert, damit sie auf allen meinen Geräten verfügbar sind. Ich kann das jederzeit im Konto widerrufen. Dann werden sie aus meinem Konto entfernt.

**Rückfrage beim Widerruf im Konto (kein eigener Nachweis):**
> Sensible Events entfernen wir aus deinem Konto. Auf diesem Gerät bleiben sie gemerkt, auf deinen anderen Geräten verschwinden sie.

## analyse (c) · `analyse-hinweis-2026-11`
**Gesonderter Hinweis auf das Widerspruchsrecht (Art. 21 Abs. 4 DSGVO), abgesetzter Kasten:**
> **Dein Widerspruchsrecht:** Wir zählen anonym, wie oft Events gemerkt werden, um zu sehen, was in Düsseldorf beliebt ist (berechtigtes Interesse, Art. 6 Abs. 1 lit. f DSGVO). Wer was gemerkt hat, sieht dabei niemand, und sensible Events zählen nie mit. Du kannst dem jederzeit widersprechen:
> ☐ Meine Merkliste nicht mitzählen. (Auch später im Konto.)

Der Nachweis hält fest, dass der Hinweis gezeigt wurde, und ob widersprochen wurde (`erteilt = false` heißt Widerspruch).

## geburtstagsmail (d) · `geburtstagsmail-2026-11-2` (seit 17.11.2026, E16)
**Kein eigenes Feld mehr:** Das Geburtsdatum ist seit E16 Pflichtangabe im Schritt „Noch kurz zu dir“ (zusammen mit Vor- und Nachname). Die Geburtstagsmail bleibt eine freiwillige Einwilligung.

**Häkchen (Einwilligung nach Art. 6 Abs. 1 lit. a DSGVO und § 7 Abs. 2 UWG, nicht vorangekreuzt):**
> Ich möchte an meinem Geburtstag eine Mail von dies.das bekommen, mit Glückwünschen und Event-Tipps für den Tag. Dafür nutzt dies.das mein Geburtsdatum aus meinem Konto. Ich kann das jederzeit im Konto oder über den Abmeldelink in jeder Mail widerrufen.

Der Widerruf schaltet nur die Mail ab, das Datum bleibt als Pflichtangabe. SQL: `database/einwilligungstexte_2026-11-17-2.sql`. Schriftliche Freigabe des Anwalts holt der Auftraggeber ein.

Vorherige Fassung `geburtstagsmail-2026-11` (bleibt als Nachweis in der Datenbank): „… Dafür speichert dies.das mein Geburtsdatum. Ich kann das jederzeit im Konto oder über den Abmeldelink in jeder Mail widerrufen. Dann wird mein Geburtsdatum gelöscht.“

**Hinweis zu den Pflichtangaben (Art. 13 DSGVO, kein Häkchen), im Schritt „Noch kurz zu dir“ und im Konto:**
> Name und Geburtsdatum sind Pflichtangaben für dein Konto. Mit dem Geburtsdatum prüfen wir, ob du mindestens 16 Jahre alt bist. Deinen Namen brauchen wir für Ticketkäufe über dein Konto. Ändern kannst du beides jederzeit im Konto.
