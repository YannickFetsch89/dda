# Cursor-Prompt: Prüfung der Nutzerkonten auf live (17.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD geöffnet, Branch `claude/setup-project-structure-5QNOf`).

---

Du prüfst die Nutzerkonten von dies.das.düsseldorf. Sie sind seit Commit `06571c5` auf https://diesdas.events live, mit Schalter `KONTEN_AKTIV=1`. **Ändere keinen Code und keine Datenbank. Schreib nur einen Befundbericht.**

## Grundlagen (bitte zuerst lesen)
- Plan: `docs/plan-nutzerkonten-2026-11-16.md`. Verbindlich sind vor allem die Abschnitte 3 (Sitzung, Cookies, Caching), 4 (Datenmodell, RLS), 5 (Abläufe), 6 (Routen), 11 (Sicherheit) und 16 (Tests). Abschnitt 20 ist die Historie mit allen späteren Entscheidungen, darunter E16 (Vorname, Nachname, Geburtsdatum Pflicht) und die Ansprache per du.
- Diff: `git show 06571c5 --stat` und `git show 06571c5`.
- Server-Code: `web/lib/konto/*`, `web/app/api/konto/**`.
- Oberfläche: `web/components/konto*.tsx`, `web/components/interessen-fragebogen.tsx`, `web/components/merkliste.tsx`, `web/components/client.tsx`, `web/app/konto/**`.
- Rechtstexte: `web/app/datenschutz/page.tsx` und `konto-abschnitt.tsx`, `web/app/nutzungsbedingungen/page.tsx`.
- Deploy: `.github/workflows/deploy.yml` (Variable `KONTEN_AKTIV`).
- SQL (schon ausgeführt): `database/konten_2026-11-16.sql`, `database/konten_stammdaten_2026-11-17.sql`, `database/konten_aufraeumen_2026-11-17.sql`, Tests in `database/konten_tests_2026-11-16.sql`.
- Job: `pipeline/konten_aufraeumen.py` (Aufruf in `main.py`).
- Betrieb: nginx leitet an Next auf `localhost:3847` weiter, mit Host `localhost:3847` und `X-Forwarded-Proto: https`. Deshalb prüft `istLokal` in `web/lib/konto/cookies.ts` zusätzlich die Forwarded-Köpfe.

## Was du live prüfen darfst (nur lesend, schonend)
Mit `curl -i` oder im Browser. **Kein Konto anlegen**, keine echten Mailadressen, insgesamt höchstens rund 30 Anfragen an `/api/konto/*`. Keine Last- oder Brute-Force-Tests.
1. **Abgemeldet:**
   - `GET /api/konto/ich` → 401, `Cache-Control: private, no-store`, kein `Set-Cookie` mit Sitzungsdaten.
   - Ein unbekannter Pfad unter `/api/konto/` → 404.
2. **CSRF/Origin:** `POST /api/konto/anmelden` mit JSON
   - ohne `Origin`,
   - mit `Origin: https://evil.example`,
   - mit `Origin: http://localhost:3847`.

   Erwartet: Ablehnung. Ein Body mit falschem Content-Type → abgelehnt.
3. **Registrieren ohne Wirkung:** `POST /api/konto/registrieren` mit `Origin: https://diesdas.events`, aber **ungültiger** Adresse bzw. zu kurzem Passwort → 400 mit Feldcode. Kein gültiger Datensatz, damit kein Konto entsteht.
4. **Seiten:**
   - `/konto/anmelden`, `/konto`, `/konto/willkommen` → 200 und `X-Robots-Tag: noindex`.
   - `/nutzungsbedingungen` → 200.
   - `/datenschutz` enthält Abschnitt 13 „Nutzerkonto“, dahinter die Nummern 14–18.
   - `/robots.txt` und `/sitemap.xml` enthalten keine `/konto`-Pfade.
5. **Öffentliche Seiten unverändert und weiter cachebar:**
   - Startseite und eine Eventseite haben keine Konto-Daten im HTML.
   - Kein `Set-Cookie` bei normalen Seitenaufrufen.
   - Caching-Köpfe wie vor dem Deploy (Plan 3.5).
6. **Browser, Netzwerk-Tab:** Auf `/konto/anmelden` und einer Eventseite gehen keine Anfragen an Dritte (insbesondere nicht an `supabase.co`). Konto-Anfragen gehen nur an `/api/konto/*`.

## Was du im Code prüfen sollst
- **Sitzung und Cookies:**
  - HttpOnly, Secure (live!), SameSite, Pfade.
  - Erneuern des Tokens und Abmelden.
  - Reset-Sitzung nur für `passwort-setzen`.
- **Jede Route:** Reihenfolge im Wrapper `kontoRoute` (Schalter, Origin/JSON, Größe, Sitzung, Bremslimit, Mindestalter). Ein Fehlerpfad darf keine Fehlertexte von Supabase und keine personenbezogenen Daten in Antwort oder Log geben.
- **Sensibel-Filter (E13):** Eine Kennzeichnung „sensibel“ darf **nirgends** für Nutzer sichtbar sein: nicht in Antworten, nicht im Export, nicht im Browser-Speicher, nicht in Klassen oder Attributen.
- **Einwilligungen:**
  - Die Textversion kommt immer aus `TEXTVERSIONEN`, nie aus dem Body.
  - Ein Nachweis entsteht für jede Angabe.
  - Unter 16: Sperre und keine Speicherung von Name und Datum.
  - Geburtstagsmail nur mit gespeichertem Datum.
- **E16:**
  - Prüfung der Namen in `nameNormal` und in der Datenbank (`name_plausibel`).
  - `onboarding_nur_mit_stammdaten`.
  - Kein direktes Spaltenrecht für `authenticated` auf vorname, nachname, geburtsdatum.
- **Merkliste:**
  - Übernahme ohne Datenverlust (Plan 5.4).
  - Warteschlange und Sperre (Web Locks) mit Ersatzweg.
  - Abmelden löscht lokale Kopien, aber nicht „Nur auf diesem Gerät“.
- **SQL:**
  - RLS-Policies und Spaltenrechte.
  - `SECURITY DEFINER` nur mit `search_path ''` und REVOKE/GRANT wie im Plan 4.5.
  - Trigger-Reihenfolge in `merkliste_vor_insert`.
- **Schalter:**
  - Mit `KONTEN_AKTIV` aus müssen alle Konto-Routen 404 geben und alle Links verschwinden.
  - Die Datenschutzerklärung muss dann exakt der alten entsprechen.
  - Der Deploy schreibt immer ausdrücklich 0 oder 1.
- **Job:**
  - Admins werden nie gelöscht.
  - Die Obergrenze von 200 gilt.
  - Im Log stehen keine vollständigen Nutzer-IDs und keine Mailadressen.
- **Texte:**
  - Konto-Seiten per du, „Button“ statt „Knopf“.
  - Datenschutzerklärung und Nutzungsbedingungen in Sie-Form.
  - Keine offenen Klammern wie „[Prüfpunkt]“ im veröffentlichten Text.

## Bericht
Eine Liste, sortiert nach Schwere (**kritisch / hoch / mittel / gering / Hinweis**). Je Befund:
- Ort (Datei:Zeile oder URL)
- was passiert, mit einem Beispiel oder einer Anfrage zum Nachstellen
- warum es ein Problem ist (Verweis auf den Planabschnitt)
- Vorschlag zur Behebung

Am Ende: eine Zeile „live geprüft“ mit den tatsächlich gestellten Anfragen und Ergebnissen, dazu eine Gesamteinschätzung, ob die Konten so live bleiben können.
