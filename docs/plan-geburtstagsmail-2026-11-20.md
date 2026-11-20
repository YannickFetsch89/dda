# Plan: Geburtstagsmail (Kontenplan Schritt 9a) – erste Fassung, 20.11.2026

**Status:** FREIGEGEBEN 20.11.2026 (G1–G9 und Vorlage wie vorgeschlagen). Gebaut lokal, nicht committet, nicht deployt.
**Grundlage:** `docs/plan-nutzerkonten-2026-11-16.md`, Abschnitt 13a (Geburtstagsmails) und Schritt 9a („eigener Mini-Plan, eigene Freigabe, Vorlage zur Freigabe“). Dieser Plan ersetzt 13a dort, wo sich seitdem etwas geändert hat (Abschnitt 1).
**Mailvorlage (Entwurf):** `docs/geburtstagsmail/entwurf-geburtstag.html`

## 1. Ausgangslage und was sich seit 13a geändert hat

- Die Einwilligung (d) „Geburtstagsmail“ wird seit dem 17.11.2026 live eingeholt (aktuelle Fassung `geburtstagsmail-2026-11-3`). **Verschickt wird bisher nichts.** Wer eingewilligt hat, erwartet die Mail.
- Datenbank (vorhanden): `profiles.geburtstagsmail`, `profiles.geburtsdatum` (seit E16 Pflichtangabe), `profiles.geburtstagsmail_zuletzt`, `einwilligungen.handlung` kennt schon `'abmeldelink'`.
- **Geändert seit 13a:**
  1. **E16:** Das Geburtsdatum ist Pflichtangabe. Der Widerruf löscht es **nicht** mehr, er setzt nur `geburtstagsmail = false`. 13a sagte noch „löschen damit das Geburtsdatum“.
  2. **Ansprache per du** (nicht „ihr“).
  3. **Vorschläge** rechnet inzwischen `web/lib/fuer-dich.ts` (TypeScript, „Mein dies.das“ Stufe 1). 13a ging von einer Rechnung im Python-Job aus.
  4. **Kontaktadresse** ist `hallo@diesdas.events` (seit 546fe6b), nicht mehr `moin@rocktician.com`.
  5. **Anrede mit Vornamen** ist freigegeben, aber laut Datenschutzerklärung nur „auf der Website und in der App“ (Mein dies.das S3). Für Mails fehlt dieser Zweck (G3).
- **Gefundene Abweichung:** Die Datenschutzerklärung sagt in der Tabelle zur Geburtstagsmail: „bis zum Widerruf (das Datum der letzten Mail wird dann gelöscht …)“. `einwilligung_setzen` (`database/konten_stammdaten_2026-11-17.sql`, Zweig `geburtstagsmail`) setzt aber nur `geburtstagsmail`, `geburtstagsmail_zuletzt` bleibt stehen (G5).

## 2. Entscheidungen (Vorschläge von Claude, zur Bestätigung)

| Nr. | Frage | Vorschlag |
|---|---|---|
| G1 | Wie wird verschickt? | **Python-Job** `pipeline/geburtstag_mails.py` mit `smtplib` (Standardbibliothek, keine neue Bibliothek) über das Postfach `hallo@diesdas.events` auf unserem Mailserver (Mitteilung des Auftraggebers vom 20.11.2026; zuerst war `konto@` vorgesehen, das Supabase für die Konto-Mails nutzt; DKIM/DMARC gelten für die ganze Domain). Eigener Workflow `.github/workflows/geburtstag.yml`, **täglich 08:00 UTC** (= 9 Uhr im Winter, 10 Uhr im Sommer). Schalter: GitHub-Variable `GEBURTSTAG_AKTIV` (ohne `1` läuft der Job nicht). Absender „dies.das.düsseldorf <hallo@diesdas.events>“, Antwort-An `hallo@diesdas.events`. |
| G2 | Welche Event-Tipps? | **Bis zu drei Events für den Geburtstag selbst**, gerechnet in TypeScript über eine **interne Route** `POST /api/intern/geburtstag-tipps` mit Job-Schlüssel (Muster wie das Magazin, `MAGAZIN_JOB_SCHLUESSEL`). Mit Einwilligung (a): die persönlichen Vorschläge für diesen Tag (`startVorschlaege`, Fenster `tag`, inklusive Ersatz „Beliebt“). Ohne (a): Tipp und Picks des Tages wie auf der Startseite (`startPlaetze`). Nie sensible, abgesagte oder schon gemerkte Events. Gibt es an dem Tag nichts, entfällt der Tipp-Block, die Glückwünsche gehen trotzdem raus. **Alternative:** für alle nur Tipp und Picks (einfacher, keine Interessen in der Mail). |
| G3 | Vorname in der Mail? | **Zunächst ohne Namen** („Alles Gute zum Geburtstag!“). Mit Namen bräuchte es den Zusatz „… und in E-Mails“ beim Zweck der Anrede in Datenschutzerklärung, Hinweis „Über dich“ und Art.-15-Auskunft. Das kann später als kleine Textänderung nachkommen, wenn der Anwalt zustimmt. |
| G4 | Abmeldung | Wie 13a: Link `https://diesdas.events/konto/geburtstag-abmelden#t=<Token>` (statische Seite, Button „Keine Geburtstagsmails mehr“, erst der Klick schickt `POST /api/konto/geburtstag-abmelden`), dazu **One-Click nach RFC 8058**: Kopfzeilen `List-Unsubscribe: <https://diesdas.events/api/konto/geburtstag-abmelden/<Token>>` und `List-Unsubscribe-Post: List-Unsubscribe=One-Click`, `GET` → 405. Beide rufen `einwilligung_setzen('geburtstagsmail', false, …, 'abmeldelink')` mit der aktuellen Textversion. **Das Datum bleibt (E16).** Token: `<nutzer-id>.<HMAC-SHA256(GEBURTSTAG_TOKEN_SCHLUESSEL, "geburtstag:" + nutzer-id), base64url>`, ohne Ablauf, nur für diesen Zweck. Erzeugt in Python, geprüft in TypeScript; ein fester Testvektor sichert, dass beide gleich rechnen. |
| G5 | Widerruf und `geburtstagsmail_zuletzt` | **SQL anpassen**, damit die Datenschutzerklärung stimmt: Der Zweig `geburtstagsmail` setzt beim Widerruf zusätzlich `geburtstagsmail_zuletzt = NULL`. Hingenommen: Wer am Geburtstag nach der Mail widerruft und sofort neu einwilligt, bekäme am selben Tag eine zweite Mail. **Alternative:** Text der Datenschutzerklärung ändern („bleibt bis zum Jahresende gegen doppelten Versand“). |
| G6 | 29. Februar | In Nicht-Schaltjahren am 28. Februar (wie 13a). |
| G7 | Doppelversand | Wie 13a: vor dem Versand per `UPDATE … SET geburtstagsmail_zuletzt = heute WHERE … AND (geburtstagsmail_zuletzt IS NULL OR geburtstagsmail_zuletzt < Jahresbeginn) RETURNING id` beanspruchen; nur bei einer Zeile senden; schlägt der Versand fehl, den alten Wert zurückschreiben. |
| G8 | Probelauf und Testmail | `--probe`: zählt nur die Empfänger von heute, schreibt nichts, schickt nichts. `--test-an <adresse> [--nutzer <id>]`: schickt eine Beispielmail mit echten Tipps an eine Testadresse, schreibt nichts. Erst danach `GEBURTSTAG_AKTIV=1`. |
| G9 | Mailformat | `multipart/alternative` mit Text- und HTML-Teil, Gestaltung wie die Konto-Mails (`docs/konto-mails/`), keine Bilder von fremden Servern (Event-Bilder entfallen), kein Zählpixel, keine Links mit Tracking-Parametern. |

## 3. Bauteile

**Datenbank** (SQL, führt der Auftraggeber aus, vor dem Deploy):
- `database/geburtstagsmail_2026-11-20.sql`: `einwilligung_setzen` neu, nur der Zweig `geburtstagsmail` ändert sich (G5). Alles andere wörtlich wie in `konten_stammdaten_2026-11-17.sql`. Kontrollabfrage am Ende.
- Lesend braucht der Job: Empfänger mit `geburtstagsmail = true`, `unter16_gesperrt_am IS NULL`, `mindestalter_bestaetigt_am IS NOT NULL`, Geburtstag heute (Europe/Berlin), `geburtstagsmail_zuletzt` nicht in diesem Jahr, plus die Mailadresse aus `auth.users` (Dienst-Client, `auth.admin.getUserById`).

**Website** (`web/`):
- `lib/konto/geburtstag-token.ts`: Token erzeugen und prüfen (Zeitkonstanter Vergleich), Schlüssel aus `GEBURTSTAG_TOKEN_SCHLUESSEL`.
- `app/konto/geburtstag-abmelden/page.tsx`: statische Hülle (`KontoRahmen`, `KONTO_ROBOTS`), liest das Token aus dem Fragment, Button, Erfolg „Du bekommst keine Geburtstagsmails mehr. Ändern kannst du das jederzeit im Konto.“
- `app/api/konto/geburtstag-abmelden/route.ts` (POST, Token im Body) und `app/api/konto/geburtstag-abmelden/[token]/route.ts` (POST One-Click, GET → 405): ohne Anmeldung, Bremslimit 30 je IP und Stunde, 404 bei ausgeschaltetem `KONTEN_AKTIV`. Antwort immer gleich (auch bei schon abgemeldet), ohne Rückschluss auf das Konto. Ungültiges Token → 400.
- `app/api/intern/geburtstag-tipps/route.ts` (POST, Kopf `x-job-schluessel` = `GEBURTSTAG_JOB_SCHLUESSEL`): bekommt `{ datum, nutzer: [id, …] }` (höchstens 200), liefert je Nutzer bis zu drei Events (`titel`, `ort`, `uhrzeit`, `url`). Ohne gültigen Schlüssel 404 (verrät die Route nicht). Keine Mailadressen, keine Interessen in der Antwort. Sensibel-Menge wie in Stufe 1 über `kontoDienstClient()`. Ist sie nicht lesbar, liefert die Route 503, und der Job verschickt die Mail **ohne** Tipp-Block (keine Tipps ohne Sensibel-Prüfung).
- `deploy.yml`: die zwei neuen Secrets in `web/.env.local` schreiben (wie `MAGAZIN_JOB_SCHLUESSEL`).

**Pipeline:**
- `pipeline/geburtstag_mails.py`: Empfänger lesen, je Empfänger beanspruchen (G7), Tipps holen (G2), Mail bauen (Vorlage `pipeline/vorlagen/geburtstag.html` und `.txt`), über SMTP (STARTTLS, Port 587) senden. Log nur mit Zahlen (gefunden, gesendet, fehlgeschlagen), keine Adressen, keine IDs. `--probe`, `--test-an` (G8).
- `.github/workflows/geburtstag.yml`: täglich 08:00 UTC und manuell, `if: vars.GEBURTSTAG_AKTIV == '1'` (manueller Probelauf auch ohne Schalter), Secrets `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_BENUTZER`, `SMTP_PASSWORT`, `GEBURTSTAG_TOKEN_SCHLUESSEL`, `GEBURTSTAG_JOB_SCHLUESSEL`.

**Texte:**
- Mailvorlage (Entwurf beiliegend). Betreff: „Alles Gute zum Geburtstag!“, Vorschautext: „Wir haben dir ein paar Events für heute herausgesucht.“
- Datenschutzerklärung: keine Änderung nötig, wenn G5 wie vorgeschlagen (SQL statt Text).

## 4. Ablauf

1. **Freigabe** dieses Plans (G1–G9) und der Vorlage.
2. Claude baut lokal: SQL, Website-Teile, Job, Workflow, Tests. Kein Deploy.
3. Cursor-Prüfung der Umsetzung, Befunde beheben.
4. Auftraggeber: SQL ausführen; Secrets in GitHub anlegen (SMTP-Zugang des Postfachs `hallo@`, zwei neue zufällige Schlüssel); `GEBURTSTAG_AKTIV` bleibt aus.
5. Deploy der Website (nach OK). Live prüfen: Abmeldeseite, One-Click-Route (405 bei GET), interne Route ohne Schlüssel 404.
6. Workflow manuell: `--probe` (Zahl der Empfänger heute), dann `--test-an` an eine Adresse des Auftraggebers. Abnahme der Mail im Postfach (Darstellung hell/dunkel, Abmeldelink, One-Click-Knopf im Mailprogramm, Kopfzeilen DKIM/DMARC).
7. `GEBURTSTAG_AKTIV=1`. Nach dem ersten echten Lauf das Log prüfen.

## 5. Tests

- **Python:** Empfängerauswahl (heute, 29.2. → 28.2. in Nicht-Schaltjahren, gesperrt und ohne Mindestalter ausgeschlossen, schon in diesem Jahr gesendet ausgeschlossen), Beanspruchen und Zurücksetzen bei Sendefehler, Token gleich dem Testvektor, Mail enthält `List-Unsubscribe`-Kopfzeilen und beide Teile, kein Tipp-Block bei 503, Log ohne Adressen.
- **Website:** Token fälschungssicher (falsches HMAC, fremde ID, anderer Zweck), Abmeldung ruft `einwilligung_setzen(false, 'abmeldelink')` mit aktueller Textversion, Datum bleibt, gleiche Antwort für schon abgemeldet, GET auf One-Click → 405, Bremslimit, 404 ohne Schalter; interne Route: 404 ohne Schlüssel, keine sensiblen Events, höchstens drei, keine Interessen oder Adressen in der Antwort, 503 ohne Sensibel-Menge.
- **SQL:** Widerruf setzt `geburtstagsmail_zuletzt = NULL`, Datum bleibt.

## 6. Risiken

- **Zustellbarkeit:** Werbemails aus demselben Postfach wie die Konto-Mails. Bei wenigen Mails am Tag unkritisch; DMARC steht noch auf `none` (Umstellung auf `quarantine` Anfang Dezember geplant). Die Testmail prüft DKIM/DMARC.
- **SMTP aus GitHub Actions:** Supabase (AWS) sendet schon von außen über das Postfach. Sperrt der Hoster GitHub-IPs, zeigt das der Probelauf mit `--test-an`. Ausweichweg: den Job per SSH auf unserem Server starten (wie der Deploy).
- **Token im nginx-Log** (One-Click-Pfad): bewusst hingenommen (13a), kann nur die Geburtstagsmail abbestellen.

## 7. Prüfhistorie
- 20.11.2026: erste Fassung (Claude), auf Wunsch des Auftraggebers („Geburtstagsmail zuerst“).
- 20.11.2026: **Vom Auftraggeber freigegeben** („Ja, so umsetzen“), G1–G9 und Vorlage wie vorgeschlagen.
- 20.11.2026: **Gebaut** (lokal, nicht committet):
  - SQL `database/geburtstagsmail_2026-11-20.sql`: `einwilligung_setzen` mit G5; dazu (Abweichung: statt direkter Abfragen und `UPDATE … RETURNING` aus dem Job) vier Funktionen nur für `service_role`: `geburtstag_heute` (29.2.-Regel, in der Kontrollabfrage mit sieben Fällen geprüft), `geburtstag_empfaenger`, `geburtstag_beanspruchen` (gibt den alten Wert zurück) und `geburtstag_freigeben` (setzt nur zurück, wenn noch der beanspruchte Tag drinsteht). So bleibt Beanspruchen atomar, und der Job braucht keine Datumsrechnung.
  - Website: `lib/konto/geburtstag.ts` (Token, Abmeldung), `lib/konto/geburtstag-tipps.ts` (Tipps, rein), Routen `api/konto/geburtstag-abmelden` (Seite, JSON, Origin) und `api/konto/geburtstag-abmelden/[token]` (One-Click ohne Origin, GET 405), interne Route `api/intern/geburtstag-tipps` (Header `x-geburtstag-schluessel`; die Route nimmt den Tag aus dem Pool und gibt ihn mit, der Job verwirft Tipps eines anderen Tages), Seite `/konto/geburtstag-abmelden`, `eingabeAusProfil` in `lib/konto/mein-bereich.ts` (eingabeBauen nutzt es).
  - Pipeline: `pipeline/geburtstag_mails.py` (senden/probe/test; Absender seit 20.11. `hallo@diesdas.events`, das SMTP-Postfach), Vorlage `pipeline/vorlagen/geburtstag.html` aus dem freigegebenen Entwurf, Workflow `.github/workflows/geburtstag.yml`, `deploy.yml` schreibt die zwei Schlüssel nach `web/.env.local`.
  - Tests: `web/tests/geburtstag.test.ts` (12), `tests/test_geburtstag_mails.py` (19, gemeinsamer Token-Testvektor mit TypeScript). Website-Suite 568/568, TypeScript und ESLint ohne Befund. Die Python-Tests liefen lokal mit einem kleinen Ersatz-Runner, weil pytest hier nicht installiert ist.
  - Hinweis zum Workflow: Die Testadresse bei „test“ steht in den Eingaben des Laufs (in der Actions-Oberfläche sichtbar), nicht im Log.
- 20.11.2026: **SQL ausgeführt** (`database/geburtstagsmail_2026-11-20.sql`), Kontrolle 15× „ok“ (29.2.-Regel, Rechte, Widerruf).
- 20.11.2026: **Cursor-Prüfung der Umsetzung** (`docs/cursor-pruefung-geburtstagsmail-2026-11-20.md`): „bereit für SQL, Secrets und Deploy nach Behebung“, alle Abweichungen in Ordnung. Behoben (lokal, nicht committet):
  - **hoch:** Bei einem Ladefehler liefert `eventPoolLaden` Beispieldaten mit heutigem Datum; die hätten als Tipps in der Mail landen können. Die interne Route antwortet jetzt 503, wenn `quelle !== "supabase"`; der Job schickt dann ohne Tipps.
  - **gering:** Merkliste je Person einzeln laden (höchstens 1000 Zeilen, volle Antwort → 503), statt einer Sammelabfrage, die Supabase still kürzen könnte.
  - **Hinweis:** Das Fehler-Log im Wrapper maskiert Pfadteile über 40 Zeichen (`pfadFuerLog`), damit kein One-Click-Token im Anwendungslog landet.
  - **Tests ergänzt:** Beispielpool → 503, Schalter aus an interner und One-Click-Route → 404, gemerktes Event bei (a), Merkliste je Person, Merkliste-Fehler → 503, Log-Maskierung, Kopfzeilen Auto-Submitted/Message-ID/Date. Web 18 + Python 19 grün; Gesamtsuite 573/574 (ein bekannter Zeitüberschreiter in `seo-c.test.ts`, Guides).
- 20.11.2026: **LIVE** (580c3b9, Push aus temporärem Worktree auf 836fbf2, Fast-Forward). Testmail an den Auftraggeber funktioniert.
- 20.11.2026: **Änderungen nach der Testmail** (Wunsch des Auftraggebers): Anrede „Hallo <Vorname>,“ statt „Hallo!“ (danach „heute ist dein Tag …“ klein), Satz über den Tipps „Hier haben wir ein paar ausgewählte Tipps, falls du heute noch was unternehmen willst:“. **G3 geändert:** Vorname jetzt auch in der Mail; dafür nennt die Datenschutzerklärung beim Zweck der Anrede zusätzlich „in E-Mails“ (`web/app/datenschutz/konto-abschnitt.tsx`). Der Hinweis „Über dich“ („um dich persönlich anzusprechen“) und die Art.-15-Auskunft („persönliche Anrede“) decken das schon ab. Ohne Vornamen lautet die Anrede „Hallo,“. Python-Tests 21/21.
