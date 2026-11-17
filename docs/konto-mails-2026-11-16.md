# Mailvorlagen für Supabase Auth – zur Freigabe

Stand: 17.11.2026 · dritte Fassung (dies.das-Design, du-Form) · Endfassung zu Plan 10.3 (`docs/plan-nutzerkonten-2026-11-16.md`), Schritt 2.

Die Vorlagen liegen als fertige HTML-Dateien in **`docs/konto-mails/`**. Erzeugt werden sie aus `web/scripts/konto-mails.mjs` (Aufruf im Ordner `web`: `node scripts/konto-mails.mjs`). Änderungen nur im Skript, dann neu erzeugen.
- **Ansehen:** `docs/konto-mails/vorschau.html` im Browser öffnen. Sie zeigt alle sechs Vorlagen mit Beispielwerten.
- **Eintragen:** Supabase → Authentication → Emails → Templates. Je Vorlage den Betreff in „Subject“ setzen und den **gesamten Inhalt** der HTML-Datei in „Message body“ kopieren.

| Supabase-Vorlage | Betreff | Datei |
|---|---|---|
| Confirm signup | Bitte bestätige deine Mailadresse für dies.das | `1-confirm-signup.html` |
| Reset Password | Neues Passwort für dies.das | `2-reset-password.html` |
| Reauthentication | Dein Bestätigungscode für dies.das | `3-reauthentication.html` |
| Change Email Address | Änderung deiner Mailadresse bei dies.das | `4-change-email.html` |
| Magic Link | Anmeldung bei dies.das | `5-magic-link.html` |
| Invite user | Einladung zu dies.das | `6-invite-user.html` |

**Gestaltung:**
- Wortmarke „dies.das.düsseldorf“ als Text (Georgia kursiv, goldene Punkte).
- Weiße Karte mit goldenem Strich oben, Navy-Button, Hinweiskasten in Sand mit goldenem Rand.
- Fuß mit Anschrift wie im Impressum und Links auf Impressum und Datenschutz.
- Tabellen-Layout mit Inline-Styles für Outlook, Gmail und Apple Mail.
- Ein Vorschautext für die Posteingangsliste.
- Dunkler Modus für Apple Mail und andere Programme, die ihn unterstützen (dort ist der Button golden).
- Ohne CSS bleibt alles als Text lesbar.

**Regeln (Plan 5.2, 10.1, 10.3):**
- Nie `{{ .ConfirmationURL }}`. Links bauen wir selbst aus `{{ .SiteURL }}`, der Token steht im Fragment (`#`), nicht in der Query.
- Keine Bilder, keine Schriften oder Dateien von fremden Servern, kein Tracking. Die Wortmarke ist Text, nicht Bild.
- Ansprache **du** (Wunsch des Auftraggebers vom 17.11.2026; abweichend von der ihr-Form der Website-Texte im Plan). Für Bedienelemente steht „Button“, nicht „Knopf“.
- Neu in dieser Fassung: Unter dem Button steht der Link noch einmal als Text zum Kopieren, falls der Button in einem Mailprogramm nicht funktioniert.
- Neu in dieser Fassung: Die Bestätigungsmail sagt, dass ein Link auf einem anderen Gerät dort anmeldet (Plan 5.2).

**Offen bis zum Vorversuch (Schritt 4):** Die Bestätigungsmail bekommt die Zeile mit dem Ersatz-Code (`{{ .Token }}`) nur, wenn der Vorversuch ein Verify-Limit **je Adresse** zeigt (Plan 5.1 Schritt 13, 5.2). Der fertige Block liegt in `docs/konto-mails/ersatz-code-block.html`. Er kommt dann in `1-confirm-signup.html` direkt unter den Button, aber **nie vorab als HTML-Kommentar**: Supabase würde den Code sonst trotzdem in den Quelltext schreiben.

**Abweichung zum Plan (freigegeben mit dieser Datei):** „Change Email Address“, „Magic Link“ und „Invite user“ enthalten **keinen Token-Link**.
- Der Plan sah für „Change Email Address“ eine Vorlage „für später“ vor.
- Eine Mailänderung bieten wir in dieser Runde aber nicht an (Plan 19, Punkt 4), Magic Link und Einladung nutzen wir nie.
- Ohne Token-Link lässt sich auch dann nichts bestätigen, wenn jemand diese Mails mit seinem eigenen Token direkt bei Supabase auslöst.
- Magic Link und Einladung verweisen nur auf `/konto/anmelden`.
- Kommt die Mailänderung später, bekommt die Vorlage mit jener Freigabe ihren Link.
- Folge für das Supabase-Dashboard: „Invite user“ und „Send magic link“ nicht verwenden. Neue Admins nur über „Add user“ mit Auto-Confirm (Checkliste Teil F).

**Reset Password** gilt auch für die Admin-Konten des Dashboards (Plan 5.1 Schritt 11). Bis Schritt 5 live ist, gibt es `/konto/bestaetigen` dort noch nicht. Ein Admin, der vorher sein Passwort vergisst, bekommt es im Supabase-Dashboard neu gesetzt.

---

## Prüfung nach dem Eintragen
- Testmail „Send password recovery“ an ein eigenes Admin-Konto. Prüfen:
  - Betreff „Neues Passwort für dies.das“, Umlaute korrekt, Wortmarke und Button wie in der Vorschau.
  - Der Link beginnt mit `https://diesdas.events/konto/bestaetigen#token_hash=` und endet auf `&art=reset`. Kein `supabase.co` in der Mail.
  - Den Link **nicht anklicken**, solange `/konto/bestaetigen` noch nicht live ist.
- In Gmail unter „Original anzeigen“: SPF, DKIM und DMARC `PASS`, sobald die DNS-Einträge stehen.
- Darstellung in Gmail (Web und App), Outlook.com und GMX/Web.de kurz ansehen. Apple Mail im dunklen Modus, falls vorhanden.
