# Schritt 2 – Checkliste: Mailversand, Supabase-Einstellungen, Unterlagen

Stand: 16.11.2026 · gehört zu `docs/plan-nutzerkonten-2026-11-16.md`, Schritt 2 in Abschnitt 15 (Details in 9.2, 10.1–10.3, 4.6).
Ausführung: Auftraggeber. Claude liefert diese Liste und die Texte:
- `docs/konto-mails-2026-11-16.md`: Mailvorlagen für Supabase, zur Freigabe
- `docs/supabase-unterlagen-vorlagen-2026-11-16.md`: Vorlagen für die TIA und den Eintrag ins Verarbeitungsverzeichnis

**Ziel von Schritt 2:**
- Eine Testmail über Supabase kommt bei Gmail, GMX/Web.de und Outlook.com an, mit `spf=pass`, `dkim=pass` und `dmarc=pass`, und landet nicht im Spam.
- Die Supabase-Einstellungen stehen wie in 10.2.
- Die Unterlagen aus 9.2 sind abgelegt.

**Die Registrierung bleibt während des ganzen Schritts aus.** Am Website-Code ändert sich nichts.

**Nie an Claude schicken:** Passwörter, SMTP-Zugangsdaten, private DKIM-Schlüssel und unterschriebene Verträge. Gebraucht werden nur die Ergebnisse, siehe Teil J.

---

## A. Supabase: Ist-Stand festhalten, Registrierung aus (zuerst, 5 Minuten)

Supabase-Dashboard, Projekt DDA (`dqckcszxoyaxiwwcgxxk`):

- [ ] **Authentication → Sign In / Providers** (je nach Dashboard-Version auch „Settings“): „Allow new users to sign up“ ablesen.
  - Ist es **an**, sofort ausschalten.
  - Danach unter Authentication → Users nachsehen, ob es Konten gibt, die keine Admins sind. Zahl und Anlagedatum an Claude geben, keine Adressen.
- [ ] Dieselbe Seite: „Confirm email“, „Secure email change“ und „Secure password change“ ablesen und notieren (Ist-Stand).
- [ ] **Authentication → URL Configuration:** die heutige **Site URL** und die **Redirect URLs** notieren, damit sie sich wiederherstellen lassen.
- [ ] **Organization → Billing:** den Tarif notieren (Free, Pro, Team …).

## B. Fragen an den Hoster (meinserver.io)

Text zum Abschicken (Sie-Form). In eckigen Klammern steht, was ihr vor dem Versand ergänzt.

> Betreff: Mailversand über unseren Server k49q02.meinserver.io – Fragen vor dem Start
>
> Guten Tag,
>
> wir möchten über unseren Server k49q02.meinserver.io künftig Systemmails versenden (Bestätigungs- und Passwort-Mails für Nutzerkonten auf diesdas.events). Die Mails werden von unserem Dienstleister Supabase (Rechenzentrum AWS Frankfurt) per SMTP-Anmeldung über ein Postfach auf unserem Server eingeliefert, also von einer IP-Adresse außerhalb Ihres Netzes. Dazu haben wir folgende Fragen:
>
> 1. Ist die SMTP-Einlieferung mit Anmeldung von außen erlaubt, und über welche Ports (587 mit STARTTLS und/oder 465 mit TLS)? Werden fremde Absender-IPs gefiltert?
> 2. Gibt es ein Limit für ausgehende Mails pro Stunde oder Tag, je Postfach oder je Server?
> 3. Welcher Hostname ist für SMTP zu verwenden, und passt das TLS-Zertifikat genau zu diesem Namen?
> 4. Passt der Reverse-DNS-Eintrag (PTR) der Server-IP zum Hostnamen des Mailservers? Versendet der Server auch über IPv6? Wenn ja: Hat die IPv6-Adresse ebenfalls einen passenden PTR-Eintrag, oder lässt sich der Versand auf IPv4 beschränken?
> 5. Bleibt der Envelope-Absender (Return-Path) bei der Absenderadresse @diesdas.events, oder wird er auf den Servernamen umgeschrieben?
> 6. Unterstützt der Server DKIM-Signaturen für diesdas.events (ISPConfig), und wird mit d=diesdas.events signiert?
> 7. Steht die IP-Adresse des Servers derzeit auf einer Sperrliste (z. B. Spamhaus)?
> 8. Deckt unser bestehender Vertrag zur Auftragsverarbeitung auch den Mailversand und die Postfächer ab, oder benötigen wir eine Ergänzung?
>
> Vielen Dank und freundliche Grüße
> [Name]
> Rocktician e. K.
> [Kundennummer]

- [ ] Abgeschickt am: ____ · Antwort erhalten am: ____

## C. Postfach anlegen (ISPConfig)

- [ ] Prüfen, ob `diesdas.events` als Mail-Domain in ISPConfig angelegt ist, sonst anlegen.
- [ ] Postfach `konto@diesdas.events` anlegen.
  - Eigenes, langes Zufallspasswort (mindestens 24 Zeichen), nur für den Versand.
  - Ablage im Passwortmanager, nirgends sonst.
  - Kleine Quota reicht. Weiterleitung nicht nötig, Antworten gehen per „Antwort an“ zu `moin@rocktician.com`.
- [ ] Alias `dmarc@diesdas.events` anlegen, mit Weiterleitung an eine Adresse, die ihr lest. Dort kommen die DMARC-Berichte an (Teil D).
- [ ] **MX von `diesdas.events` prüfen** (z. B. `nslookup -type=mx diesdas.events`).
  - Zeigt er auf unseren Server: gut.
  - Zeigt er woandershin oder fehlt er: Unzustellbar-Meldungen an `@diesdas.events` kommen nicht im Postfach an. Das ist kein Hindernis für den Start, aber notieren und an Claude geben.
  - `hallo@diesdas.events` aus dem Seitenfuß ist laut Plan noch ungeprüft. Das hängt am selben MX.

## D. DNS für `diesdas.events`

Wer den DNS verwaltet (Hoster, Registrar, Cloudflare …), steht noch offen (Plan 19, Punkt 6). Einträge dort setzen, wo die Domain verwaltet wird.

- [ ] **SPF**, TXT-Eintrag auf `diesdas.events`.
  - **Es darf nur einen SPF-Eintrag geben.** Gibt es schon einen (beginnt mit `v=spf1`), wird er ergänzt, nicht ein zweiter angelegt.
  - Vorlage je nach Antwort des Hosters (Teil B, Frage 4). Die IPs nennt der Hoster bzw. ISPConfig.
    - **Versand nur über IPv4:** `v=spf1 ip4:[IPv4 des Servers] ~all`
    - **Versand auch über IPv6:** `v=spf1 ip4:[IPv4 des Servers] ip6:[IPv6 des Servers] ~all`
  - Bewusst ohne `a:k49q02.meinserver.io` und ohne `mx`: Beide gelten auch für die IPv6-Adresse (AAAA) des Hosts. Bei Versand nur über IPv4 würden sie eine Adresse freigeben, die gar nicht senden soll. Ist der Versand später über IPv6 gewollt, reicht das `ip6:` oben.
  - Gibt es schon einen SPF-Eintrag mit weiteren Absendern (z. B. für `hallo@diesdas.events` bei einem anderen Anbieter), bleiben deren Teile (`include:` …) erhalten. Nur die eigene IP kommt dazu.
  - Zum Start `~all`. Auf `-all` erst, wenn die DMARC-Berichte zwei Wochen sauber sind.
- [ ] **DKIM:**
  - In ISPConfig unter Email → Domain → `diesdas.events` → Reiter DKIM einschalten, Schlüssel erzeugen und den Selektor notieren (oft `default`).
  - Den öffentlichen Schlüssel als TXT-Eintrag `[selektor]._domainkey.diesdas.events` setzen (`v=DKIM1; t=s; p=…`).
  - Verwaltet ISPConfig den DNS selbst, legt es den Eintrag automatisch an.
- [ ] **DMARC**, TXT-Eintrag auf `_dmarc.diesdas.events`: `v=DMARC1; p=none; rua=mailto:dmarc@diesdas.events; adkim=r; aspf=r; fo=1`
  - Nach zwei Wochen sauberer Berichte auf `p=quarantine` umstellen (Plan 10.1). Termin eintragen: ____
- [ ] **PTR (Reverse-DNS):** setzt der Hoster (Teil B, Frage 4). Nur prüfen, nicht selbst setzen.
- [ ] Sperrliste prüfen: Die Server-IP auf einer Blacklist-Prüfseite eingeben (z. B. MXToolbox „Blacklist Check“). Ergebnis notieren.

## E. Erste Testmail ohne Supabase (Postfach direkt)

So zeigt sich, ob Postfach, DNS und Zertifikat stimmen, bevor Supabase dazukommt.

- [ ] In einem Mailprogramm (z. B. Thunderbird) das Postfach `konto@diesdas.events` einrichten: SMTP-Host laut Hoster, Port 587 STARTTLS oder 465 TLS, Anmeldung mit vollem Mailnamen.
  - Ein Fehler wie „Zertifikat passt nicht zum Host“ heißt: In Supabase würde es auch scheitern (Plan 10.1). Dann zuerst mit dem Hoster klären.
- [ ] Je eine Testmail an ein Gmail-, ein GMX- oder Web.de- und ein Outlook.com-Postfach.
- [ ] In Gmail die Mail öffnen → ⋮ → „Original anzeigen“ und Folgendes ablesen:
  - SPF, DKIM, DMARC: jeweils `PASS`?
  - Zeile `Return-Path:`: endet sie auf `@diesdas.events` oder auf den Servernamen?
  - Zeile `DKIM-Signature:`: steht dort `d=diesdas.events`?
  - Zeile `Received: from …`: kommt die Mail über IPv4 oder IPv6?
- [ ] In GMX/Web.de und Outlook.com: Posteingang oder Spam?

Ist eines davon nicht in Ordnung, die Kopfzeilen **ohne die Empfängeradresse** an Claude geben.

## F. Supabase: SMTP und Auth-Einstellungen (nach bestandenem Teil E)

**Authentication → Emails → SMTP Settings** („Enable Custom SMTP“):

| Feld | Wert |
|---|---|
| Sender email | `konto@diesdas.events` |
| Sender name | `dies.das.düsseldorf` (im Test prüfen, ob das ü richtig ankommt; sonst `dies.das.duesseldorf`) |
| Host | SMTP-Hostname laut Hoster (passend zum Zertifikat) |
| Port | 587 (oder 465, laut Hoster) |
| Username | `konto@diesdas.events` |
| Password | Postfach-Passwort aus dem Passwortmanager |
| Minimum interval between emails | Standard lassen (60 Sekunden) |

**Weitere Einstellungen (Plan 10.2):**

| Bereich | Einstellung | Wert |
|---|---|---|
| Sign In / Providers | Allow new users to sign up | **aus** (erst in Schritt 8 an) |
| Sign In / Providers → Email | Email provider | an |
| | Confirm email | an |
| | Secure email change | an |
| | Secure password change | an |
| | Minimum password length | 10 |
| | Password requirements | keine Zeichenklassen-Pflicht |
| | Leaked password protection | an, **falls der Tarif sie anbietet** (sonst notieren, Plan 19 Punkt 13) |
| | Email OTP length | 6 |
| | Email OTP expiration | 3600 Sekunden (gilt für alle Mail-Token; getrennte Werte gibt es nach unserem Kenntnisstand nicht – falls doch: Bestätigung 86400, Reset 3600) |
| URL Configuration | Site URL | `https://diesdas.events` |
| | Redirect URLs | `https://diesdas.events/konto/bestaetigen`, `http://localhost:3100/konto/bestaetigen`, `http://localhost:3200/konto/bestaetigen` |
| Rate Limits | Rate limit for sending emails | **20 pro Stunde** |
| | Rate limit for token verifications | unverändert lassen und den Wert notieren (Vorversuch in Schritt 4) |
| Sessions / JWT | JWT expiry | 3600 Sekunden |
| | Detect and revoke compromised refresh tokens (Rotation) | an |
| | Refresh token reuse interval | 10 Sekunden |
| Auth-Protokolle (falls es den Schalter gibt) | Auth-Protokolle zusätzlich in die Datenbank schreiben | **aus** (Plan 4.6) |

- [ ] **Vorher prüfen:** Das Admin-Dashboard meldet sich nur mit Mail und Passwort an (`dashboard/auth.py`). Site URL, JWT-Werte und „Confirm email“ ändern daran nichts. Nach dem Speichern einmal im Dashboard ab- und wieder anmelden.
- [ ] **Testmail über Supabase (nur SMTP und Zustellung):**
  - Authentication → Users → ein **eigenes** Admin-Konto → „Send password recovery“. Nur diesen Weg nutzen.
  - Hier zählt nur, dass die Mail über unseren Server kommt: In „Original anzeigen“ wieder SPF, DKIM und DMARC prüfen.
  - Ob schon die alte Supabase-Vorlage oder schon unsere kommt, ist hier egal. Den Link prüft Teil G.

**Bis Schritt 8 im Supabase-Dashboard nicht verwenden:**
- „Invite user“ und „Send magic link“: Unsere Vorlagen dafür haben absichtlich keinen Link. Eine Einladung legt trotzdem ein Konto an, das sich nie anmelden kann.
- Neue Admins nur über „Add user“ mit „Auto Confirm User“ anlegen (wie in `database/auth_rollen.sql`).
- Hat ein Admin sein Passwort vergessen: bis Schritt 5 im Supabase-Dashboard direkt neu setzen (Authentication → Users → Konto → Passwort ändern), nicht per Reset-Mail. `/konto/bestaetigen` gibt es bis dahin noch nicht.

## G. Mailvorlagen

- [ ] `docs/konto-mails-2026-11-16.md` lesen und freigeben (oder Änderungen an Claude).
- [ ] Nach der Freigabe in **Authentication → Emails → Templates** eintragen: je Vorlage Betreff und HTML-Text aus der Datei kopieren.
- [ ] **Linktest, nur über „Send password recovery“** an ein eigenes Admin-Konto (nicht über Magic Link, dessen Vorlage hat absichtlich keinen Link):
  - Betreff „Neues Passwort für dies.das“?
  - Umlaute korrekt?
  - Der Knopf ist ein Link auf `https://diesdas.events/konto/bestaetigen#token_hash=…&art=reset`?
  - Kein `supabase.co` im Link?
  - Bis Schritt 5 führt der Link ins Leere, weil es `/konto/bestaetigen` noch nicht gibt. Das ist erwartet. Den Link nicht weiterverwenden; er verfällt nach einer Stunde von selbst.

## H. Supabase-Unterlagen (Plan 9.2, 4.6)

Unterschriebene Verträge **nicht ins Repo**, sondern in den Firmenordner für Verträge. Ins Repo kommt höchstens ein Vermerk „abgelegt am …“.

- [ ] **DPA (Data Processing Addendum):**
  - Im Dashboard unter Organization → Settings → **Legal Documents** (bzw. „Documents“) anfordern bzw. unterschreiben.
  - Prüfen: Abschlussdatum, Vertragspartner (Supabase Inc.), Verweis auf die Standardvertragsklauseln.
- [ ] **Standardvertragsklauseln:** im DPA enthalten? Modul 2 (Verantwortlicher an Auftragsverarbeiter)? Seite bzw. Anhang notieren.
- [ ] **Unterauftragsverarbeiter:** aktuelle Liste von Supabase (Seite „Subprocessors“ unter supabase.com/legal) als PDF sichern, mit Datum.
- [ ] **TIA (Transfer-Folgenabschätzung):**
  - Stellt Supabase eine eigene TIA bereit (Legal Documents), diese ablegen.
  - Zusätzlich oder sonst die Vorlage aus `docs/supabase-unterlagen-vorlagen-2026-11-16.md` ausfüllen.
- [ ] **EU-US Data Privacy Framework:** Prüfen, ob Supabase Inc. auf der DPF-Liste (dataprivacyframework.gov) steht. Nur wenn ja, darf die Erklärung darauf verweisen (Plan 9.2). Ergebnis notieren.
- [ ] **Aufbewahrung der Logs:**
  - Laut Supabase-Preisseite bzw. Tarifbeschreibung: Wie lange werden Logs gespeichert (Log retention), insbesondere die Auth-Logs?
  - Wie lange werden Backups aufbewahrt (Daily backups / PITR)?
  - Beide Zahlen für euren Tarif notieren. Sie kommen in die Datenschutzerklärung (Plan 4.6, 9.4).
  - **Inhalt der Auth-Logs:** Unter Logs → Auth einen Eintrag einer eigenen Admin-Anmeldung öffnen. Notieren, welche Angaben darin stehen (IP-Adresse, Mailadresse, Nutzer-ID, Browser), **ohne die Werte selbst**. Schritt 1 hat nur belegt, dass die Protokolle nicht in der Datenbank-Tabelle stehen (Plan 4.6).
- [ ] **Hoster:** Antwort auf Teil B, Frage 8 (AV-Vertrag deckt Mail ab, sonst Ergänzung anfordern).
- [ ] **Verzeichnis der Verarbeitungstätigkeiten:** Eintrag „Nutzerkonten“ aus der Vorlagen-Datei übernehmen.

## J. Rückmeldung an Claude

Bitte diese Liste ausgefüllt zurückgeben, **ohne Passwörter und ohne Mailadressen von Personen**:

```
A  Signup war: an/aus · andere Konten als Admins: Zahl, Anlagedaten
   Confirm email / Secure email change / Secure password change vorher: …
   Site URL vorher: …
   Tarif: …
B  Hoster: Port(s) …, Limit …, SMTP-Host …, Zertifikat passt: ja/nein,
   PTR IPv4 ok: ja/nein, IPv6-Versand: ja/nein (PTR ok: ja/nein),
   Return-Path: @diesdas.events / umgeschrieben, DKIM d=diesdas.events: ja/nein,
   Sperrliste: ja/nein, AV-Vertrag deckt Mail: ja/nein/Ergänzung angefordert
C  MX zeigt auf: unseren Server / anderswohin / fehlt
D  SPF gesetzt: …  DKIM-Selektor: …  DMARC gesetzt: ja/nein
E  Gmail: SPF … DKIM … DMARC …, Return-Path-Domain …, d= …, IPv4/IPv6
   GMX/Web.de: Posteingang/Spam · Outlook.com: Posteingang/Spam
F  Supabase-Testmail: SPF … DKIM … DMARC …
   Leaked password protection verfügbar: ja/nein
   Getrennte OTP-Gültigkeit möglich: ja/nein
   Verify-Rate-Limit (Wert): …
   Schalter „Auth-Protokolle in Datenbank“ gefunden: ja (aus)/nein
G  Vorlagen freigegeben und eingetragen: ja/nein, Umlaute ok: ja/nein
H  DPA abgeschlossen am …, SCC Modul 2: ja/nein, Subprocessor-Liste vom …,
   TIA: von Supabase/eigene, DPF-Liste: ja/nein,
   Log retention: … Tage, Backups: … Tage
   Auth-Logs enthalten: IP ja/nein, Mail ja/nein, Nutzer-ID ja/nein, Browser ja/nein
```

Damit trägt Claude die Werte in den Plan ein (10.1, 10.2, 4.6, 9.4) und bereitet Schritt 3 vor (Migration `database/konten_<datum>.sql`).
