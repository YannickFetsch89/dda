# Anwalt-Vorlage: E-Mail an Melder nach der Veröffentlichung (24.11.2026)

**Worum es geht:** Über das Formular „Event melden“ (diesdas.events/event-melden) schlagen Veranstalter und Besucher Events vor. Die E-Mail-Adresse ist Pflicht und bisher laut Datenschutzerklärung „nur für Rückfragen“ gedacht. Ab jetzt bekommt jeder Melder **einmalig** eine E-Mail, sobald wir sein Event veröffentlicht haben.

**Stand:** Auf Wunsch des Auftraggebers geht die Mail **sofort mit dem Konto-Hinweis** live (Entscheidung 24.11.2026, Risiko bewusst getragen). Abschalten ist jederzeit ohne Deploy möglich (GitHub-Variable `MELDUNG_MAIL_AKTIV`). Mit dieser Vorlage soll das im Nachhinein geprüft werden.

## Inhalt der Mail (Absender hallo@diesdas.events, Ansprache du)

> **Betreff:** Dein Event ist online: ‹Titel›
>
> Hallo ‹Name aus der Meldung›, *(ohne Namen: „Hallo,“)*
>
> danke, dass du uns dein Event geschickt hast! Wir haben es angeschaut und jetzt veröffentlicht:
>
> **‹Titel›** – ‹Datum, Uhrzeit› · ‹Ort› – [Zum Event]
>
> Teil den Link gern mit allen, die vorbeikommen sollen. Und wenn dein nächstes Event ansteht: Du kannst es jederzeit hier melden: diesdas.events/event-melden
>
> Übrigens: Mit einem kostenlosen Konto bei dies.das merkst du dir Events, bekommst Tipps, die zu dir passen, und hast deine Favoriten auf jedem Gerät dabei: [Kostenloses Konto anlegen]
>
> Danke, dass du dies.das nutzt. So wird der Kalender für Düsseldorf jeden Tag ein bisschen vollständiger.
>
> Viele Grüße, dein Team von dies.das
>
> *Fußzeile:* Du bekommst diese Mail einmalig, weil du über „Event melden“ ein Event bei uns eingereicht hast. · Anbieterangaben · Links zu Impressum und Datenschutz (Abschnitt 12)

Wer ein fremdes Event als Besucher gemeldet hat, liest „dieses Event“ bzw. „Das von dir gemeldete Event ist online“ und statt des Satzes zum nächsten eigenen Event: „Und wenn du wieder ein Event entdeckst, das bei uns noch fehlt …“.

## Geänderte Texte auf der Website

**Formular, Danke-Meldung nach dem Absenden:** „… Sobald dein Event online ist, schicken wir dir den Link per E-Mail; bei Rückfragen melden wir uns ebenfalls per E-Mail.“
**Formular, Kontaktfeld:** „Wird nicht veröffentlicht. An diese Adresse schicken wir dir auch den Link, sobald dein Event online ist.“

**Datenschutzerklärung, Abschnitt 12 (neu):** „Die Kontaktdaten nutzen wir für Rückfragen zu Ihrer Meldung und für eine einmalige E-Mail, sobald das Event veröffentlicht ist und noch bevorsteht (mit dem Link zum Event und einem Hinweis auf unser kostenloses Nutzerkonto); sie werden nicht veröffentlicht. Diese E-Mail versenden wir über den Mailserver unseres Hosting-Anbieters (Abschnitt 3).“ (bisher: „Die Kontaktdaten nutzen wir nur für Rückfragen zu Ihrer Meldung; sie werden nicht veröffentlicht.“)

**Datenschutzerklärung, Abschnitt 3 (Mailserver), ergänzt:** „… sowie die Mitteilung, dass ein von Ihnen gemeldetes Event veröffentlicht ist (Abschnitt 12).“

Rechtsgrundlage in Abschnitt 12 unverändert: Art. 6 Abs. 1 lit. a bzw. lit. f DSGVO. Die Meldung samt Kontaktdaten wird weiterhin sechs Monate nach dem Event-Tag gelöscht.

## Fragen

1. **Konto-Hinweis als Werbung (§ 7 Abs. 2 Nr. 2 UWG):** Ist der Absatz „Übrigens: Mit einem kostenlosen Konto …“ in einer sonst rein informierenden Mail zulässig, obwohl der Melder nicht in Werbung eingewilligt hat (vgl. BGH, Urt. v. 15.12.2015 – VI ZR 134/15, Werbezusatz in Bestätigungsmail)? Falls nein: Reicht ein freiwilliges Häkchen im Formular („Ja, schickt mir auch einen Hinweis auf euer kostenloses Konto“), oder sollte der Absatz ganz entfallen?
2. **Hinweis aufs nächste Melden** („Du kannst es jederzeit hier melden“) – ebenfalls Werbung oder als Teil der Dankesmail unbedenklich?
3. **Rechtsgrundlage der Mail selbst:** Genügt Art. 6 Abs. 1 lit. f DSGVO (Information über das Ergebnis der eigenen Meldung), und reicht die geänderte Formulierung in Abschnitt 12 samt Hinweis im Formular?
4. **Ältere Meldungen:** Melder, deren Event vor dem 24.11.2026 freigegeben wurde, bekommen keine Mail. Einverstanden?
