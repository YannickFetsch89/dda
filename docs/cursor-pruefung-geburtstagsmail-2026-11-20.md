# Cursor-Prompt: Prüfung der Umsetzung „Geburtstagsmail“ (20.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD geöffnet, Branch `claude/setup-project-structure-5QNOf`).

---

Du prüfst die **Umsetzung** des freigegebenen Plans `docs/plan-geburtstagsmail-2026-11-20.md` (Kontenplan Schritt 9a). Claude Code hat alles gebaut. Der Stand ist **lokal und nicht committet**; nichts ist deployt, kein SQL ist ausgeführt, kein Secret angelegt.

**Wichtig:**
- **Du änderst keinen Code und keine Datei außer deinem Bericht.** Im selben Ordner arbeiten andere Sitzungen. Claude Code behebt deine Befunde danach.
- Fremde, nicht committete Änderungen anderer Vorhaben prüfst du nicht (Ortsseiten, Magazin, Rausgegangen-Scraper, `data/**`).
- Keine Mails verschicken, keine Anfragen an `diesdas.events/api/konto/*` oder `/api/intern/*`, keine Verbindung zum Mailserver.
- Erfinde keine Befunde. Jeder Befund braucht Datei:Zeile und ein konkretes Szenario.
- Die Entscheidungen G1–G9 stehen fest. Stell sie nur in Frage, wenn etwas rechtlich oder technisch unhaltbar ist.

## Lies zuerst
- Plan: `docs/plan-geburtstagsmail-2026-11-20.md` (G1–G9, Abschnitte 3–6, Prüfhistorie mit den Abweichungen).
- Hintergrund: `docs/plan-nutzerkonten-2026-11-16.md`, Abschnitte 13a, 4.5 (Rechte, `SECURITY DEFINER`), E15/E16 in Abschnitt 20.
- Vorlage: `docs/geburtstagsmail/entwurf-geburtstag.html` (freigegeben) und `pipeline/vorlagen/geburtstag.html` (daraus abgeleitet).

## Dateien
- **SQL:** `database/geburtstagsmail_2026-11-20.sql` (vergleiche `einwilligung_setzen` Zeile für Zeile mit `database/konten_stammdaten_2026-11-17.sql`; nur der Zweig `geburtstagsmail` darf sich unterscheiden).
- **Website:**
  - `web/lib/konto/geburtstag.ts`
  - `web/lib/konto/geburtstag-tipps.ts`
  - `web/lib/konto/mein-bereich.ts` (neu `eingabeAusProfil`)
  - `web/app/api/konto/geburtstag-abmelden/route.ts` und `.../[token]/route.ts`
  - `web/app/api/intern/geburtstag-tipps/route.ts`
  - `web/app/konto/geburtstag-abmelden/page.tsx`, `web/components/geburtstag-abmelden.tsx`
- **Pipeline:** `pipeline/geburtstag_mails.py`, `pipeline/vorlagen/geburtstag.html`
- **Workflows:** `.github/workflows/geburtstag.yml`, `.github/workflows/deploy.yml` (Block für die zwei Schlüssel)
- **Tests:** `web/tests/geburtstag.test.ts`, `tests/test_geburtstag_mails.py`

## Was du prüfst

**Recht und Datenschutz**
- § 7 UWG / Art. 7 DSGVO: Gehen Mails nur an Konten mit Einwilligung (d), nicht gesperrt, Mindestalter bestätigt? Kann eine Mail nach einem Widerruf noch rausgehen (Reihenfolge Empfänger → Beanspruchen → Versand)?
- Abmelden: Link auf jeder Mail, One-Click nach RFC 8058 (`List-Unsubscribe` + `List-Unsubscribe-Post`, POST ohne Anmeldung, GET 405). Abmeldung ruft `einwilligung_setzen(false, 'abmeldelink')` mit der aktuellen Textversion; das Geburtsdatum bleibt (E16); `geburtstagsmail_zuletzt` wird geleert (G5, stimmt mit der Datenschutzerklärung `web/app/datenschutz/konto-abschnitt.tsx` überein?).
- E13: Können sensible Events in die Tipps kommen (persönlich, Ersatz, allgemein)? Verrät die Antwort der internen Route Interessen, Begründungen, Merkliste oder Mailadressen?
- Logs (Job und Routen): keine Mailadressen, keine Nutzer-IDs, keine Tokens.
- Keine Bilder von fremden Servern, kein Zählpixel, keine Tracking-Parameter in der Mail.

**Sicherheit**
- Token: HMAC korrekt, Vergleich in konstanter Zeit, nur für diesen Zweck, Python und TypeScript gleich (Testvektor). Kann ein Token für eine andere Nutzer-ID gebaut werden?
- One-Click-Route ohne Origin-Prüfung: Ist das vertretbar (kann nur die Geburtstagsmail abbestellen)? CSRF-Folgen?
- Interne Route: 404 ohne/mit falschem Schlüssel, Vergleich wie `schluesselOk`, Obergrenze 200 Nutzer, keine Daten ohne Schalter.
- SQL: `SECURITY DEFINER` mit `search_path = ''`, `REVOKE … FROM PUBLIC, anon, authenticated`, `GRANT … TO service_role`. Ist `geburtstag_beanspruchen` gegen zwei gleichzeitige Läufe sicher (`FOR UPDATE`)? Setzt `geburtstag_freigeben` nur zurück, wenn noch der beanspruchte Tag drinsteht?
- `deploy.yml`: Funktioniert der Block in einer `sh`-Shell? Landen die Schlüssel nie im Log?
- `geburtstag.yml`: Kann eine Workflow-Eingabe Befehle einschleusen? Verschickt „senden“ ohne `GEBURTSTAG_AKTIV=1` irgendetwas?

**Korrektheit**
- 29. Februar, Jahreswechsel, Zeitzone (Europe/Berlin vs. UTC-Cron 08:00), Tipps eines anderen Tages werden verworfen.
- Doppelversand: paralleler Lauf, erneuter Lauf am selben Tag, Sendefehler mit Freigabe, fehlende Mailadresse.
- Tipps: persönlich nur mit (a); Ersatz „Beliebt“; ohne (a) Tipp und Picks des Tages; gemerkte Events fallen raus; höchstens drei; ohne Tipps entfällt der Block in HTML und Text.
- Mail: `multipart/alternative`, Kopfzeilen (From, Reply-To, Message-ID, Date, Auto-Submitted), HTML-Maskierung von Titeln, Links absolut.
- Seite `/konto/geburtstag-abmelden`: liest das Token nur aus dem Fragment, sendet erst beim Klick, statisch, noindex.
- `eingabeAusProfil`: verhält sich `eingabeBauen` exakt wie vorher (Stufe 1 „Mein dies.das“ darf sich nicht ändern)?

**Tests**
- Im Ordner `web`: `npx vitest run` und `npx tsc --noEmit -p .` (Stand Claude: 568 grün, TypeScript ohne Befund).
- Python: `pytest tests/test_geburtstag_mails.py`, falls pytest bei dir installiert ist (Claude hatte lokal kein pytest und einen Ersatz-Runner; 19 grün).
- Welche Fälle aus Plan Abschnitt 5 fehlen?

## Bericht (in der Antwort)
1. **Befunde nach Schwere** (kritisch / hoch / mittel / gering / Hinweis): Datei:Zeile, Problem, Szenario, Beleg, Vorschlag.
2. **Abweichungen** in der Prüfhistorie des Plans: je „in Ordnung“ oder „ändern“ mit Grund.
3. **Fehlende Tests.**
4. **Gesamteinschätzung:** „bereit für SQL, Secrets und Deploy nach Behebung“, „bereit“ oder „überarbeiten“. Wenn du nichts findest, sag das ausdrücklich.
