# Für den Anwalt: Newsletter mit Double-Opt-in

Stand 23.11.2026. Erstellt von Claude für die schriftliche Freigabe, die der Auftraggeber einholt. Kein Rechtsrat. Gehört zu Stufe 4 des Plans `docs/plan-admin-dashboard-2026-11-23.md` (Abschnitt 4.9).

**Stand der Technik:** Die Website und der Versandjob sind gebaut. Der Versand der Bestätigungsmails ist aber **ausgeschaltet**, bis diese Freigabe vorliegt (GitHub-Variable `NEWSLETTER_AKTIV`). Bis dahin nimmt die Website Anmeldungen an, verschickt aber nichts. Der Versand des eigentlichen Newsletters („Zehn Tipps“ am Donnerstag) ist **nicht** Teil dieser Freigabe; er kommt mit einem eigenen Plan.

## Was passiert

1. **Anmeldung** auf der Startseite (Feld „E-Mail“). Gespeichert werden die E-Mail-Adresse, die Quelle („website“) und der Zeitpunkt der Anmeldung. **Keine IP-Adresse.** Ob eine Adresse schon angemeldet ist, verrät die Website nicht (immer dieselbe Antwort).
2. **Bestätigungsmail** innerhalb von etwa 15 Minuten, über den Mailserver unseres Hosting-Anbieters (derselbe wie für die Konto-Mails). Inhalt: nur die Bitte um Bestätigung, ein Button „Anmeldung bestätigen“ und ein Link „Sofort löschen“. Keine Werbung, keine Event-Tipps. Gespeichert werden der Zeitpunkt der Mail und die Anzahl der Mails.
3. **Bestätigung:** Der Link führt auf eine Seite mit einem Button. Erst der Klick bestätigt (Programme, die Links in Mails vorab öffnen, lösen nichts aus). Gespeichert wird der Zeitpunkt der Bestätigung – das ist der Nachweis der Einwilligung.
4. **Keine Bestätigung:** Die Adresse wird **30 Tage nach der Bestätigungsmail** gelöscht.
5. **Erneute Anmeldung** derselben Adresse ohne Bestätigung: frühestens nach 24 Stunden eine neue Mail, insgesamt höchstens **drei** Bestätigungsmails je Adresse (Schutz davor, dass jemand fremde Adressen wiederholt einträgt).
6. **Abmelden:** Link in jeder Mail und One-Click-Abmeldung nach RFC 8058 (Kopfzeile `List-Unsubscribe`). Die Abmeldung **löscht die Adresse sofort** – keine Sperrliste. So steht es schon heute in der Datenschutzerklärung.
7. **Bestehende Anmeldungen** (vor dem Double-Opt-in, ohne Bestätigung): Sie bekommen nach dem Einschalten **einmal** die Bestätigungsmail – so kündigt es die heutige Datenschutzerklärung an („Bevor die erste Ausgabe verschickt wird, bitten wir Sie per E-Mail, Ihre Anmeldung zu bestätigen“). Ohne Bestätigung werden sie nach 30 Tagen gelöscht.
8. **Im Admin-Bereich:** Liste, Export nur der bestätigten Adressen, Löschen auf Anfrage. Export und Löschen werden protokolliert, ohne die Adresse selbst im Protokoll.

## Fragen

1. Ist die Bestätigungsmail an die **bestehenden** Anmeldungen (Punkt 7) zulässig?
2. Reicht der Zeitpunkt der Bestätigung als Nachweis, oder sollen wir zusätzlich etwas speichern (z. B. den Text der Anmeldung zum Zeitpunkt der Anmeldung)? Eine IP-Adresse speichern wir bewusst nicht.
3. Passt die sofortige Löschung bei Abmeldung ohne Sperrliste?
4. Braucht das Anmeldeformular auf der Startseite einen Hinweistext? Vorschlag unten.

## Vorschlag: Hinweis unter dem Anmeldefeld

> Mit der Anmeldung bekommst du eine Mail mit Bestätigungslink. Erst danach schicken wir dir donnerstags unseren Newsletter. Abmelden kannst du dich jederzeit über den Link in jeder Mail. Mehr in der [Datenschutzerklärung](/datenschutz#newsletter).

## Vorschlag: Datenschutzerklärung, Abschnitt 11 „Newsletter“ (ersetzt den heutigen Text)

> Wenn Sie unseren Newsletter abonnieren, speichern wir Ihre E-Mail-Adresse und den Zeitpunkt der Anmeldung (Supabase, siehe Abschnitt 9). Anschließend schicken wir Ihnen eine E-Mail mit einem Bestätigungslink (Double-Opt-in). Erst wenn Sie den Link aufrufen und die Anmeldung bestätigen, erhalten Sie den Newsletter; wir speichern dann zusätzlich den Zeitpunkt der Bestätigung als Nachweis Ihrer Einwilligung. Bestätigen Sie die Anmeldung nicht, löschen wir Ihre E-Mail-Adresse 30 Tage nach der Bestätigungs-E-Mail. Die E-Mails versenden wir über den Mailserver unseres Hosting-Anbieters, der dabei Ihre E-Mail-Adresse und den Inhalt der E-Mail in unserem Auftrag verarbeitet.
>
> Rechtsgrundlage ist Art. 6 Abs. 1 lit. a DSGVO (Einwilligung). Sie können Ihre Einwilligung jederzeit widerrufen – über den Abmeldelink in jeder E-Mail oder per E-Mail an hallo@diesdas.events. Mit der Abmeldung löschen wir Ihre E-Mail-Adresse sofort.

Dazu: Der Satz zum Mailserver in Abschnitt 3 („Über den Mailserver unseres Hosting-Anbieters versenden wir außerdem die E-Mails zum Nutzerkonto“) erscheint heute nur, wenn die Nutzerkonten eingeschaltet sind. Er würde um „und zum Newsletter (Abschnitt 11)“ ergänzt und immer angezeigt.
