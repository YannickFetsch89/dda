# Datenschutzerklärung – Ergänzungen für Nutzerkonten (Entwurf)

> **Vom Anwalt freigegeben (Mitteilung des Auftraggebers vom 17.11.2026).** Wird mit dem Einschalten der Konten in `web/app/datenschutz/page.tsx` übernommen. Ursprünglich: Arbeitsfassung vom 17.11.2026. Erstellt von Claude für die anwaltliche Durchsicht (Plan `docs/plan-nutzerkonten-2026-11-16.md`, Abschnitt 9.4, Schritt 6). Kein Rechtsrat.
> - **Nachtrag 17.11.2026 (E16, Entscheidung des Auftraggebers): Vorname, Nachname und Geburtsdatum sind Pflichtangaben.** Geänderte Stellen: Einleitung, Tabelle (neue Zeile „Name und Geburtsdatum“, Zeile „Geburtstagsmail“), „Registrierung und Mindestalter“, „Geburtstagsmail“. Die schriftliche Freigabe dieser Änderungen holt der Auftraggeber beim Anwalt ein.
> - Grundlage ist die geltende Erklärung `web/app/datenschutz/page.tsx` (Stand Oktober 2026). Sie bleibt bis zur Freigabe unverändert.
> - Die Erklärung bleibt in der **Sie-Form** (Entscheidung des Auftraggebers vom 17.11.2026). Die Konto-Seiten selbst sprechen mit du an.
> - Stellen in **[eckigen Klammern]** sind vor der Veröffentlichung auszufüllen. Die Werte kommen aus den Supabase-Unterlagen (Checkliste Schritt 2, Teil H).
> - Abschnittsnummern: Der neue Abschnitt „Nutzerkonto“ kommt als **13** nach „Event melden“ (12). Die bisherigen Abschnitte 13–17 werden zu 14–18. Querverweise sind unten schon angepasst.

---

## A. Neuer Abschnitt 13 „Nutzerkonto“ (Anker `#konto`)

### 13. Nutzerkonto

Sie können die Website ohne Konto nutzen. Mit einem kostenlosen Nutzerkonto steht Ihre Merkliste auf mehreren Geräten zur Verfügung. Für das Konto brauchen wir Ihre E-Mail-Adresse, Ihren Vor- und Nachnamen und Ihr Geburtsdatum. Optional können Sie Interessen angeben und Geburtstagsmails erhalten. Für das Konto gelten zusätzlich unsere [Nutzungsbedingungen](/nutzungsbedingungen).

**Welche Daten wir verarbeiten und wozu**

| Zweck | Daten | Rechtsgrundlage | Speicherdauer |
|---|---|---|---|
| Konto führen, Anmeldung | E-Mail-Adresse, Passwort (nur als verschlüsselter Hash bei Supabase, nie im Klartext bei uns), Zeitpunkte von Anlage und Anmeldung, Sitzungen | Art. 6 Abs. 1 lit. b DSGVO (Nutzungsvertrag) | bis zur Löschung des Kontos; ohne Nutzung höchstens 24 Monate (siehe „Löschung“) |
| Name und Geburtsdatum (Pflichtangaben) | Vorname, Nachname, Geburtsdatum | Art. 6 Abs. 1 lit. b DSGVO (Nutzungsvertrag): Geburtsdatum zur Prüfung des Mindestalters von 16 Jahren, Name für Ticketkäufe über das Konto | bis zur Löschung des Kontos |
| Merkliste im Konto | IDs der gemerkten Events, Zeitpunkt des Merkens | Art. 6 Abs. 1 lit. b DSGVO | wie das Konto |
| Merkungen besonders schützenswerter Events | IDs solcher Events, Zeitpunkt (siehe „Besonders schützenswerte Events“) | Art. 9 Abs. 2 lit. a i. V. m. Art. 6 Abs. 1 lit. a DSGVO (ausdrückliche Einwilligung) | bis zum Widerruf, spätestens mit dem Konto |
| Interessen und persönliche Vorschläge | Ihre Angaben im Fragebogen (Kategorien, Stadtteile, Vorlieben) und die Auswertung Ihrer Merkliste für Vorschläge | Art. 6 Abs. 1 lit. a DSGVO (Einwilligung) | bis zum Widerruf, dann sofort gelöscht; spätestens mit dem Konto |
| Anonyme Beliebtheits-Zählung | Anzahl der Merkungen je Event, ohne Bezug zu einzelnen Personen im Ergebnis | Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse), Widerspruch jederzeit möglich | es werden keine Summen gespeichert; sie werden bei Bedarf aus den Merklisten gezählt |
| Geburtstagsmail | Ihr Geburtsdatum aus dem Konto, Datum der letzten Geburtstagsmail | Art. 6 Abs. 1 lit. a DSGVO und § 7 Abs. 2 UWG (Einwilligung) | bis zum Widerruf (das Datum der letzten Mail wird dann gelöscht, das Geburtsdatum bleibt als Pflichtangabe im Konto); spätestens mit dem Konto |
| Altersbestätigung, Nutzungsbedingungen, Nachweis Ihrer Einwilligungen | Zeitpunkt, Art der Erklärung, Fassung des angezeigten Textes | Art. 6 Abs. 1 lit. b und c DSGVO, Art. 7 Abs. 1 DSGVO (Nachweispflicht) | wie das Konto [Prüfpunkt: längere Aufbewahrung nach Löschung?] |
| Schutz vor Missbrauch | IP-Adresse und eine verschlüsselte (gehashte) Form der E-Mail-Adresse, um Anmelde- und Registrierungsversuche zu begrenzen | Art. 6 Abs. 1 lit. f DSGVO | nur im Arbeitsspeicher, rund eine Stunde |
| Anmeldeprotokoll beim Dienstleister | Nutzer-ID, E-Mail-Adresse, IP-Adresse, Zeitpunkt in den Protokollen von Supabase | Art. 6 Abs. 1 lit. f DSGVO (Sicherheit des Dienstes) | 7 Tage |

**Registrierung und Mindestalter.** Ein Konto können Personen ab 16 Jahren anlegen. Das bestätigen Sie bei der Registrierung mit einem Häkchen. Nach der Registrierung schicken wir Ihnen eine E-Mail mit einem Bestätigungslink. Erst mit der Bestätigung ist das Konto nutzbar. Danach fragen wir Ihren Vor- und Nachnamen und Ihr Geburtsdatum ab. Ergibt sich aus dem Geburtsdatum ein Alter unter 16 Jahren, speichern wir weder Namen noch Datum, sperren das Konto sofort und löschen es innerhalb von drei Tagen.

**Interessen und persönliche Vorschläge.** Nach der Bestätigung können Sie in einem kurzen Fragebogen Interessen angeben oder ihn überspringen. Ihre Antworten bleiben zunächst nur in Ihrem Browser. Gespeichert werden sie erst, wenn Sie am Ende ausdrücklich einwilligen. Sie können die Einwilligung jederzeit im Konto widerrufen. Dann löschen wir Ihre Antworten sofort.

**Besonders schützenswerte Events.** Aus der Merkung mancher Events lassen sich Rückschlüsse auf sehr persönliche Dinge ziehen: Gesundheit, Religion oder Weltanschauung, sexuelle Orientierung oder geschlechtliche Identität, politische Meinung, Gewerkschaftszugehörigkeit oder ethnische Herkunft (Art. 9 DSGVO).
- Solche Events erkennen wir automatisch anhand von Stichwörtern in Titel, Ort und Beschreibung. Die Kennzeichnung betrifft nur das Event, nicht Sie.
- Ohne Ihre ausdrückliche Einwilligung speichern wir Merkungen solcher Events **nicht in Ihrem Konto**, sondern nur in Ihrem Browser auf dem Gerät, auf dem Sie sie gemerkt haben.
- Mit Einwilligung speichern wir sie in Ihrem Konto, damit sie auf allen Ihren Geräten verfügbar sind.
- Für persönliche Vorschläge und für die Beliebtheits-Zählung nutzen wir sie **nie**, auch nicht mit Einwilligung.
- Sie können die Einwilligung jederzeit im Konto widerrufen. Dann entfernen wir diese Merkungen aus Ihrem Konto. Auf dem Gerät, auf dem Sie widerrufen, bleiben sie gemerkt, auf Ihren anderen Geräten verschwinden sie.
- Wird ein Event erst nachträglich als besonders schützenswert erkannt, entfernen wir seine Merkung aus Konten ohne diese Einwilligung.

**Anonyme Beliebtheits-Zählung und Ihr Widerspruchsrecht.** Wir zählen, wie oft Events gemerkt werden, um zu sehen, was in Düsseldorf beliebt ist, und unser Programm danach auszurichten. Dabei sehen wir nur Summen je Event, nie, wer was gemerkt hat. Besonders schützenswerte Events zählen nie mit. Grundlage ist unser berechtigtes Interesse (Art. 6 Abs. 1 lit. f DSGVO). Gezählt werden Konten erst, nachdem Sie diesen Hinweis bei der Einrichtung des Kontos gesehen haben.

> **Ihr Widerspruchsrecht (Art. 21 DSGVO):** Sie können der Zählung jederzeit widersprechen, mit einem Häkchen bei der Einrichtung des Kontos oder später in Ihrem Konto. Ihre Merkliste zählt dann nicht mehr mit.

**Geburtstagsmail.** Freiwillig können Sie einwilligen, dass wir Ihnen zum Geburtstag eine E-Mail mit Glückwünschen und Event-Tipps schicken. Dafür nutzen wir das Geburtsdatum aus Ihrem Konto. Sie können die Einwilligung jederzeit im Konto oder über den Abmeldelink in jeder Geburtstagsmail widerrufen. Das Geburtsdatum bleibt dann als Pflichtangabe im Konto gespeichert, wird aber nicht mehr für Mails genutzt.

**E-Mails zum Konto.** Wir senden Ihnen E-Mails, die für das Konto nötig sind: Bestätigung der Adresse, Link zum Zurücksetzen des Passworts, gegebenenfalls einen Bestätigungscode und einen Hinweis vor der Löschung eines ungenutzten Kontos. Sie werden von Supabase ausgelöst und über den Mailserver unseres Hosting-Anbieters versendet (Abschnitt 3). Die E-Mails enthalten keine Zählpixel und keine Klick-Verfolgung.

**Löschung.**
- Sie können Ihr Konto jederzeit selbst im Bereich „Konto“ löschen. Dabei löschen wir Ihre Merkliste, Ihre Angaben und die Nachweise Ihrer Einwilligungen [Prüfpunkt Aufbewahrung].
- Konten, deren E-Mail-Adresse nicht bestätigt wurde, löschen wir nach 48 Stunden. Weil der Löschlauf alle drei Tage stattfindet, geschieht das spätestens nach fünf Tagen.
- Bestätigte Konten ohne Altersbestätigung löschen wir nach 7 Tagen, spätestens nach 10 Tagen.
- Konten, die wegen eines Alters unter 16 Jahren gesperrt sind, löschen wir innerhalb von drei Tagen.
- Konten, die 24 Monate lang nicht genutzt wurden, löschen wir. Als Nutzung zählt jede Anmeldung und jede Aktion im Konto, zum Beispiel das Merken eines Events. Wurde ein Konto nie genutzt, zählt die Frist ab der Anlage. Einen Monat vor der Löschung erhalten Sie eine E-Mail.
- Gelöschte Daten können noch bis zu 7 Tage in den Datensicherungen unseres Dienstleisters Supabase enthalten sein und werden dort danach überschrieben. Eine Wiederherstellung aus einer Sicherung führt nicht dazu, dass ein gelöschtes Konto wieder nutzbar wird.

**Ihre Daten herunterladen.** Im Konto können Sie Ihre Kontodaten, Interessen, Einwilligungen und Ihre Merkliste als Datei herunterladen (Art. 20 DSGVO). Der Download ersetzt nicht Ihr Recht auf Auskunft nach Art. 15 DSGVO. Eine vollständige Auskunft erhalten Sie per E-Mail an [moin@rocktician.com](mailto:moin@rocktician.com).

**Empfänger und Drittland.** Die Kontodaten speichern wir bei Supabase (Abschnitt 9) in der EU (AWS, Frankfurt). Ein Zugriff durch Supabase, Inc. oder deren Unterauftragsverarbeiter aus Drittländern ist nicht ausgeschlossen. Grundlage dafür sind die Standardvertragsklauseln der EU-Kommission (Art. 46 Abs. 2 lit. c DSGVO). Mit Supabase und unserem Hosting-Anbieter bestehen Verträge zur Auftragsverarbeitung (Art. 28 DSGVO).

---

## B. Änderungen an bestehenden Abschnitten

### Abschnitt 3 „Hosting und Server-Logfiles“ – neuer Absatz am Ende
> Über den Mailserver unseres Hosting-Anbieters versenden wir außerdem die E-Mails zum Nutzerkonto (Abschnitt 13). Dabei verarbeitet der Anbieter Ihre E-Mail-Adresse und den Inhalt der jeweiligen E-Mail in unserem Auftrag.

### Abschnitt 5 „Cookies“ – Ergänzung im Punkt „Technisch notwendige Cookies“
> Wenn Sie sich in Ihrem Nutzerkonto anmelden, setzen wir zwei weitere technisch notwendige Cookies:
> - **ddd_sitzung** enthält die Anmeldedaten Ihrer Sitzung. Es ist für Skripte auf der Seite nicht lesbar (HttpOnly) und wird nur an die Konto-Funktionen unseres Servers geschickt, nicht bei normalen Seitenaufrufen. Laufzeit: 30 Tage, verlängert bei Nutzung. Nach einem Klick auf „Passwort vergessen“ gilt es nur eine Stunde.
> - **ddd_konto** enthält nur „0“ oder „1“ und sagt der Seite, ob Sie angemeldet sind. So zeigt die Seite Ihre Merkliste im richtigen Zustand an, ohne Ihre Anmeldedaten bei jedem Seitenaufruf mitzuschicken. Laufzeit wie die Sitzung, gelöscht beim Abmelden.
>
> Beide Cookies sind unbedingt erforderlich, damit eine von Ihnen gewünschte Anmeldung über mehrere Seiten hinweg bestehen bleibt (§ 25 Abs. 2 Nr. 2 TDDDG). Sie werden nur gesetzt, wenn Sie sich anmelden.

### Abschnitt 7 „Lokale Speicherung (localStorage)“
Liste ergänzen:
> - wenn Sie angemeldet sind: eine Kopie Ihrer Konto-Merkliste und noch nicht übertragene Änderungen, damit die Merkliste auch bei schlechter Verbindung sofort reagiert
> - Merkungen, die nur auf diesem Gerät gespeichert werden dürfen (Abschnitt 13, „Besonders schützenswerte Events“)
> - ein Merker, dass Sie den Hinweis auf das Nutzerkonto nach dem ersten Merken schon gesehen haben

Den letzten Absatz ersetzen durch:
> Ohne Nutzerkonto werden diese Daten ausschließlich lokal in Ihrem Browser gespeichert und nicht an uns oder Dritte übermittelt. Wenn Sie angemeldet sind, wird Ihre Merkliste in Ihrem Konto gespeichert (Abschnitt 13). Auf dem Gerät liegt dann nur eine Kopie, die beim Abmelden gelöscht wird. Beim ersten Anmelden übernehmen wir die bisher nur auf dem Gerät gespeicherte Merkliste in Ihr Konto, wenn Ihr Konto noch keine Merkliste hatte; sonst fragen wir vorher nach. Sie können die lokal gespeicherten Daten jederzeit über die Browser-Einstellungen löschen.

### Abschnitt 9 „Externe Inhalte und Drittanbieter“, Punkt „Supabase“
Den Satz „Neben Event-Daten speichern wir dort …“ ergänzen:
> Neben Event-Daten speichern wir dort Newsletter-Anmeldungen (Abschnitt 11), über „Event melden“ eingereichte Angaben und Bilder (Abschnitt 12) **sowie Nutzerkonten und Merklisten (Abschnitt 13)**. Supabase stellt außerdem die Anmeldung für Nutzerkonten bereit.

Der Satz „Ihr Browser verbindet sich dabei nicht direkt mit Supabase …“ bleibt, er gilt auch für das Konto.

### Abschnitt 15 (bisher 14) „Ihre Rechte“ – neuer Absatz nach der Liste
> Wenn Sie ein Nutzerkonto haben, können Sie viele dieser Rechte direkt im Konto ausüben: Einwilligungen widerrufen, der Beliebtheits-Zählung widersprechen, Ihre Daten herunterladen und Ihr Konto löschen.

### Abschnitt 16 (bisher 15) „Keine Weitergabe an Dritte“ – neuer Satz am Ende
> Keine Weitergabe in diesem Sinne ist die Verarbeitung durch Dienstleister, die Daten in unserem Auftrag und nach unseren Weisungen verarbeiten (Auftragsverarbeiter nach Art. 28 DSGVO), insbesondere unser Hosting-Anbieter (einschließlich E-Mail-Versand) und Supabase.

### Abschnitt 18 (bisher 17) „Aktualität“ und Kopfzeile
> „Stand“ auf den Monat des Einschaltens der Konten setzen: **[Monat 2026]**.

---

## C. Offene Angaben vor der Veröffentlichung
1. Aufbewahrungsdauer der Supabase-Protokolle und Inhalt der Auth-Logs: [X Tage], [Felder] (Checkliste Schritt 2, Teil H).
2. Aufbewahrung der Supabase-Datensicherungen: [X Tage].
3. Ob Supabase Inc. unter dem EU-US Data Privacy Framework zertifiziert ist.
4. Ob Einwilligungsnachweise nach der Kontolöschung länger aufbewahrt werden (Prüfpunkt für den Anwalt).
5. Monat für „Stand“.
