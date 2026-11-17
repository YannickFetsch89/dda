# Bitte um datenschutzrechtliche Prüfung: Nutzerkonten auf diesdas.events

> **Archivstand: Fragen vom 16.11.2026, vor der siebten Fassung des Plans.** Der unten beschriebene Ablauf ist **nicht mehr aktuell**: Alters-Häkchen nach der Mail, „Ohne Interessen fortfahren“, „Fertig“ als Einwilligung, Zählung nur mit Häkchen, Löschung nach 30 Tagen. Die rechtliche Einschätzung dazu liegt nur als Zusammenfassung vor (nicht im Repo) und ist im Plan `docs/plan-nutzerkonten-2026-11-16.md` eingearbeitet: Abschnitt 2 (E4, E6, E12a, E13–E15), 4.4, 5.3, 5.8 und 9.1–9.4. Maßgeblich ist allein der Plan. Die Altersbestätigung per Häkchen ab 16 hat der Anwalt am 16.11.2026 freigegeben.

Stand: 16.11.2026 · Verantwortlicher: Rocktician e. K., Inhaber Yannick Fetsch, Erkrather Str. 401, 40231 Düsseldorf

Sehr geehrte Damen und Herren,

wir betreiben mit diesdas.events („dies.das.düsseldorf“) einen kostenlosen Veranstaltungskalender für Düsseldorf. Bisher gibt es keine Nutzerkonten. Besucher können Events mit einem Herz „merken“, diese Merkliste liegt nur lokal im Browser (localStorage) und wird nicht an uns übertragen.

Wir möchten freiwillige Nutzerkonten einführen und bitten Sie, die unten beschriebene Gestaltung zu prüfen und die nummerierten Fragen zu beantworten. Die Umsetzung startet erst nach Ihrer Rückmeldung.

## 1. Was geplant ist

**Konto (freiwillig).** Registrierung mit Mailadresse und Passwort. Die Adresse wird per Bestätigungslink verifiziert, und es gibt „Passwort vergessen“. Ohne Konto bleibt die Website voll nutzbar, auch das lokale Merken.

**Daten im Konto:**
- Mailadresse, Passwort (nur als Hash beim Dienstleister Supabase), Zeitpunkte der Anmeldung;
- die Merkliste: welche Events jemand gemerkt hat, mit Zeitpunkt;
- Interessen: Kategorien (z. B. Musik, Kultur, Familie, Dating, Nightlife), Unterkategorien, bevorzugte Stadtteile, Merkmale wie „gern kostenlos“, „mit Kindern unterwegs“, „eher abends“;
- Bestätigung „mindestens 16 Jahre alt“ (Pflicht-Häkchen);
- ein Protokoll aller Einwilligungen und Widerrufe mit Zeitpunkt und Textversion.

**Ablauf beim Anlegen.** Nach der Bestätigung der Mailadresse folgen unmittelbar:
1. das Pflicht-Häkchen „Ich bin mindestens 16 Jahre alt“;
2. ein freiwilliges, nicht vorangekreuztes Häkchen zur anonymen Zählung (siehe Zweck c);
3. ein kurzer Fragebogen zu den Interessen. Darüber steht: „Damit wir euch passende Tipps geben können: Erzählt uns, was euch interessiert. Wir speichern eure Auswahl in eurem Konto und berücksichtigen dafür auch, was ihr euch merkt. Ihr könnt das jederzeit im Konto ändern oder abschalten.“ Auf jeder Seite des Fragebogens gibt es gut sichtbar „Ohne Interessen fortfahren“. Wer das wählt, für den speichern wir keine Interessen und bilden keine Empfehlungen. Am Ende steht der Knopf „Fertig“. Auch „Fertig“ ohne jede Auswahl werten wir als Einwilligung. Gespeichert wird dann eine leere Auswahl, und Empfehlungen stützen sich nur auf die Merkliste.

**Zwecke:**
- a) Konto und geräteübergreifende Merkliste (Kernfunktion). Wir stützen das auf Art. 6 Abs. 1 lit. b DSGVO.
- b) Persönliche Empfehlungen aus Interessen und Merkliste, z. B. eine Zeile „Für euch“. Es ist eine automatisierte Auswahl von Event-Vorschlägen ohne rechtliche oder ähnlich erhebliche Wirkung. Geplant ist eine Einwilligung durch das Ausfüllen des Fragebogens (siehe Frage 2), widerrufbar im Konto. Beim Widerruf löschen wir die Interessen sofort.
- c) Interne Statistik „welche Events sind beliebt“. Wir zählen nur, wie oft ein Event gemerkt wurde. Ergebnis sind Summen je Event ohne Personenbezug, sichtbar nur für unsere Admins. Es gibt keine Auswertung einzelner Personen, keine Zielgruppen, keine Weitergabe an Veranstalter und keine Werbung. Bis zu Ihrer Prüfung zählen nur Konten mit dem freiwilligen Häkchen.

**Was wir ausdrücklich nicht tun:** keine Werbung oder Werbemails aus den Kontodaten, keine Verknüpfung mit Google Analytics (dort nur mit Cookie-Einwilligung und getrennt), keine Weitergabe an Veranstalter oder Dritte, keine Ableitung oder Speicherung von Merkmalen wie „queer“ oder „religiös“.

**Dienstleister:**
- Supabase Inc. (Singapur/USA) als Datenbank und Anmeldedienst, Server in der EU (AWS Frankfurt). Ein AV-Vertrag wird abgeschlossen, Grundlage der Übermittlung sind Standardvertragsklauseln.
- Unser Hoster (deutscher Webhoster) für Website und Mailversand der Kontomails über unseren eigenen Mailserver.
- Der Browser der Nutzer verbindet sich nur mit unserem Server, nicht mit Supabase.

**Speicherdauer:**
- Konto bis zur Löschung durch die Person (im Konto per Knopf, mit Passwort);
- automatische Löschung nach 24 Monaten ohne Nutzung, mit Hinweismail einen Monat vorher;
- unbestätigte Registrierungen nach 48 Stunden; weil der Löschlauf nur alle drei Tage läuft, spätestens nach fünf Tagen;
- bestätigte Konten, bei denen das Alters-Häkchen nie gesetzt wurde, nach 30 Tagen, spätestens nach 33 Tagen;
- Datenexport als Datei im Konto (Art. 15, 20 DSGVO).

**Technisch notwendige Cookies:** ein Anmelde-Cookie (HttpOnly, nur für unsere Konto-Schnittstelle) und ein Anzeige-Cookie ohne personenbezogenen Inhalt („1“ bzw. „0“), je 30 Tage. Wir stützen sie auf § 25 Abs. 2 Nr. 2 TDDDG, ohne Banner-Einwilligung.

## 2. Fragen

1. **Besondere Kategorien (Art. 9 DSGVO).** Unter den Events sind z. B. CSD- und queere Veranstaltungen, religiöse Veranstaltungen, Selbsthilfegruppen und Dating-Events. Aus einer Merkliste oder den Interessen (z. B. Kategorie „Dating“) könnten Rückschlüsse auf sexuelle Orientierung, Religion oder Gesundheit möglich sein, auch wenn wir sie nie ziehen.
   - a) Ist die Speicherung der Merkliste im Konto (Zweck a) deshalb eine Verarbeitung besonderer Kategorien?
   - b) Falls ja: Reicht dafür Art. 9 Abs. 2 lit. a (ausdrückliche Einwilligung), oder gibt es eine andere tragfähige Grundlage, z. B. lit. e, weil die Person die Daten selbst bewusst angibt?
   - c) Müssen wir die Gestaltung ändern, z. B. sensible Kategorien vom Zählen ausnehmen?

2. **Einwilligung durch Ausfüllen des Fragebogens (Zweck b).** Wir möchten kein eigenes Häkchen, sondern das aktive Ausfüllen nach dem oben zitierten Hinweistext als Einwilligung werten. Opt-out ist „Ohne Interessen fortfahren“ auf jeder Seite. Der Fragebogen erscheint bei jedem neuen Konto automatisch.
   - a) Ist das eine wirksame, freiwillige und informierte Einwilligung im Sinne von Art. 4 Nr. 11 und Art. 7 DSGVO, auch wenn „Fertig“ ohne jede Auswahl gedrückt wird? Reicht sie, falls Frage 1 die Annahme besonderer Kategorien ergibt, auch als „ausdrückliche“ Einwilligung nach Art. 9 Abs. 2 lit. a?
   - b) Wäre stattdessen Art. 6 Abs. 1 lit. b tragfähig, weil Empfehlungen Teil des Kontoangebots sind?
   - c) Was muss der Hinweistext mindestens enthalten?

3. **Anonyme Zählung (Zweck c).** Wir möchten die Summen am liebsten auf berechtigtes Interesse stützen (Art. 6 Abs. 1 lit. f) und im Konto einen Widerspruch per Schalter anbieten.
   - a) Ist das zulässig, oder braucht es eine Einwilligung (vorerst so umgesetzt)?
   - b) Spielt Frage 1 dabei eine Rolle, weil die Ausgangsdaten (wer hat was gemerkt) personenbezogen sind, auch wenn das Ergebnis es nicht ist?

4. **Mindestalter 16.** Reicht ein Pflicht-Häkchen „Ich bin mindestens 16 Jahre alt“ als Absicherung für Art. 8 DSGVO, gerade weil es Dating- und Nightlife-Inhalte gibt? Oder sollten wir für Konten 18 Jahre verlangen?

5. **Anmeldeprotokolle beim Dienstleister.** Supabase protokolliert Anmeldungen (Nutzer-ID, Mailadresse, IP, Zeitpunkt). Wir versuchen, diese Einträge bei einer Kontolöschung mit zu löschen. Falls technisch nicht möglich: Dürfen sie bis zum Ablauf der Aufbewahrungsfrist von Supabase bestehen bleiben (Sicherheit des Dienstes, Art. 6 Abs. 1 lit. f), wenn wir die Frist in der Datenschutzerklärung nennen?

6. **Speicherfristen.** Sind diese Fristen angemessen: 24 Monate Inaktivität; unbestätigte Registrierungen nach 48 Stunden, wegen des Drei-Tage-Laufs spätestens nach fünf Tagen; unvollständige Registrierungen (Alter nie bestätigt) nach 30, spätestens 33 Tagen? Reicht es, in der Datenschutzerklärung die jeweils späteste Frist zu nennen?

7. **Dienstleister und Drittland.** Reichen AV-Vertrag und Standardvertragsklauseln mit Supabase (Server in Frankfurt, Unternehmen in Singapur/USA) aus? Müssen wir zusätzlich auf das EU-US Data Privacy Framework verweisen? Deckt unser bestehender AV-Vertrag mit dem Hoster den Mailversand ab, oder braucht es eine Ergänzung?

8. **Nachweis der Einwilligung.** Reicht unser Protokoll (Art der Einwilligung, erteilt oder widerrufen, Zeitpunkt, Kennung der angezeigten Textfassung) als Nachweis nach Art. 7 Abs. 1 DSGVO?

9. **Nutzungsbedingungen.** Brauchen wir für kostenlose Konten eigene Nutzungsbedingungen (AGB), z. B. zu Kontolöschung, Missbrauch und Haftung? Wenn ja, was sollten sie mindestens regeln?

10. **Datenschutz-Folgenabschätzung.** Ist nach Art. 35 DSGVO eine DSFA nötig? Wir gehen bisher davon aus, dass nicht: keine umfangreiche Verarbeitung besonderer Kategorien, kein systematisches Monitoring, keine Entscheidungen mit Rechtswirkung.

11. **Datenschutzerklärung.** Wir schicken Ihnen den Entwurf der neuen Abschnitte (Nutzerkonto, Cookies, lokale Speicherung, Dienstleister) separat. Bitte prüfen Sie ihn auf Vollständigkeit nach Art. 13 DSGVO.

## 3. Was wir von Ihnen brauchen

- Antworten auf die Fragen 1 bis 10, besonders 1 bis 3, weil davon der Aufbau des Anmeldeablaufs abhängt;
- konkrete Formulierungsvorschläge, wo Hinweistexte oder Häkchen nicht ausreichen;
- die Prüfung des Entwurfs zur Datenschutzerklärung (Frage 11).

Für Rückfragen stehe ich gern zur Verfügung.

Mit freundlichen Grüßen
Yannick Fetsch
Rocktician e. K.
