# Cursor-Prompt: Komplettprüfung „Ortsseiten“, Schritte 1, 2, 2a und 3 (20.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD, Branch `claude/setup-project-structure-5QNOf`).

---

Du prüfst den **gesamten aktuellen Stand** der Ortsseiten für die Website dies.das.düsseldorf (diesdas.events): den freigegebenen Plan `docs/plan-locations-2026-11-18.md` (elfte Fassung) gegen alles, was bisher gebaut ist. Das umfasst die Schritte 1 und 2 (live), den Bücherei-Teilschritt 2a und die Seiten unter `/orte` (Schritt 3). Schritt 2a und Schritt 3 sind gebaut, aber noch nicht deployt.

**Ändere keine Dateien und keine Datenbank. Schreib nur einen Befundbericht.**

## Stand
- **Live (gepusht):**
  - `b1570ff` (Schritt 1), `f33890f` (Schritt 2), `0d58755` (weitere 73 Orte, Kamp-Lintfort)
  - `c6085db`: Befunde deiner letzten Umsetzungsprüfung (`docs/cursor-pruefung-locations-umsetzung-2026-11-19.md`), unter anderem Bambi und Holocafé zusammengelegt, Flow umbenannt, keine Google-Fotos
  - `66fc482`: Geo 2 (198 Adressen mit Koordinaten), Gertrudenhof (Hürth) raus
- **Nur lokal committet, nicht deployt:**
  - `c610438`: Adressen für ausARTen, b41, Pialana, MS RheinFantasie
  - `b602a1a`: Schritt 3 (Seiten, Proxy, Sitemap, IndexNow, Links)
  - `42a8cd3`: weitere Pflicht-Tests, `.gitignore`-Ausnahmen
  - Schritt 2a (Bücherei-Filialen) als eigener Commit; siehe `git log`
- **Vom Auftraggeber im Supabase-SQL-Editor ausgeführt:**
  - alle SQL-Dateien vom 19.11. zu den Ortsseiten
  - `orte_korrekturen_2026-11-19.sql`, `orte_spielstaetten_geo_2026-11-20.sql`, `orte_gertrudenhof_weglassen_2026-11-20.sql`, `gebiet_bereinigung_2026-11-20.sql`
  - Stand: rund 226 Spielstätten, 198 mit Adresse und Koordinaten, rund 3.229 kommende Events mit `ort_id`
- **Noch nicht ausgeführt:**
  - `database/orte_spielstaetten_geo_2026-11-20_2.sql` (4 Adressen)
  - `database/stadtbuechereien_filialen_2026-11-20.sql`. Sie muss **vor** dem Deploy des neuen Bücherei-Scrapers laufen, sonst entstehen Doppel-Einträge.
- **Schalter:** `ORTSSEITEN_MELDEN` (GitHub-Variable) steht auf 0. Die IndexNow-Erstmeldung (`python -m pipeline.indexnow --orte-erstmeldung`) folgt erst nach dem Deploy.
- **Entscheidungen des Auftraggebers außerhalb des Plantexts:**
  - neue Arten: Laden, Freizeit/Erlebnis, Ausflugsziel/Sehenswürdigkeit, dazu Öffentliches Gebäude und Gastronomie/Eventlocation
  - Areal Böhler bleibt
  - die VHS ist umgezogen (Yorckstraße 23)
  - Theater an der Kö (eigene Seite) ist noch offen

## Was du lesen sollst
1. **Den Plan:** `docs/plan-locations-2026-11-18.md`, Abschnitt 3 (maßgeblich) und 4 (Schritte, Deploy-Reihenfolge, Pflicht-Tests), dazu 7.2 und 9.
2. **Deinen letzten Bericht** und was daraus geworden ist: `docs/cursor-pruefung-locations-umsetzung-2026-11-19.md`, Commit `c6085db`.
3. **Schritt 1 und 2:**
   - `scraper/orte/spielstaetten_kandidaten.py`, `scraper/orte/spielstaetten_import.py`, `scraper/orte/spielstaetten_geo.py`
   - `pipeline/ort_zuordnung.py`, `pipeline/deduplication.py`, `database/client.py`, `pipeline/dubletten_sql.py`, `main.py` (Schritte 1d bis 1f)
   - `scraper/orte/clubs_profil.py`, `pipeline/gebiet.py`, `pipeline/ortsnamen.py`, `scraper/tier2/schauspielhaus.py`, `scraper/orte/google_places.py`
   - die SQL-Dateien in `database/` vom 19. und 20.11. mit `orte_`, `ort_id_`, `gebiet_` oder `ortsnamen` im Namen
4. **Schritt 2a:**
   - `scraper/tier2/stadtbuechereien.py`: `filiale_aus_text`, `FILIAL_ADRESSEN`, `filialen_zuordnen`, `nachtrag_sql`
   - `tests/test_stadtbuechereien_filiale.py`, `database/stadtbuechereien_filialen_2026-11-20.sql`
5. **Schritt 3 (Website `web/`):**
   - **Seiten:** `app/orte/page.tsx`, `app/orte/[slug]/page.tsx`
   - **Bibliotheken:** `lib/spielstaetten.ts`, `lib/spielstaetten-daten.ts`, `lib/spielstaetten-json-ld.ts`
   - **Proxy:** `lib/pfad-pruefung.ts` (Teil „Ortsseiten“), `proxy.ts`
   - **Karte und Sitemap:** `app/api/guide-karte/route.ts` (`hub=orte`), `app/sitemap.ts`
   - **Programm-Block:** `components/ort-programm.tsx`, eingebunden in `app/guides/clubs/[slug]/page.tsx`, `app/guides/kneipen-bars/[slug]/page.tsx` und `app/guides/restaurants-cafes/[slug]/page.tsx`
   - **Eventseite:** `app/event/[kategorie]/[slug]/page.tsx` (`eventOrtLink`)
   - **Links:** `app/stadtteil/[slug]/page.tsx`, `components/rahmen.tsx`, `app/entdecken/page.tsx`
   - **Stile:** `app/globals.css` (`.os-*`)
   - **Tests:** `tests/ortsseiten.test.ts`, `tests/sitemap.test.ts`
   - **IndexNow:** `pipeline/indexnow.py` (`ort_indexierbar`, `ortsseiten_urls`, `orte_erstmeldung`, `nach_lauf_melden`), `tests/test_indexnow_orte.py`, `tests/fixtures/ort_indexierbar.json`

## Regeln des Projekts (Verstöße sind Befunde)
- **Eine URL je Ort.** Echte 404 und 308 nur im Proxy, nie `NextResponse.rewrite`.
- **Der Proxy liest mit dem anonymen Schlüssel** und sieht nur `aktiv = true`. Bei Abfragefehlern gilt „weiter“, nie ein falscher 308 oder 404.
- **Next.js 16 mit `cacheComponents`:**
  - `"use cache"` mit `cacheLife`; bei Fehlern nur `KURZ`
  - `searchParams` nur in Suspense
  - keine Beispieldaten auf Ortsseiten (kein `eventPoolLaden`)
- **Keine Google-Fotos und keine Google-Koordinaten**, nur die `place_id`. Bilder nur lokal (`lokalesBild`).
- **Automatische Läufe schreiben nie `NULL` über eine vorhandene `ort_id`.** `event_orte` der Clubs wächst nur.
- **Scraping:** mindestens 2 Sekunden Pause, Backoff bei 429, robots.txt.
- **SQL** nur als Datei in `database/`. Abfragen auf `orte` und `events` seitenweise.
- Keine neue Bibliothek ohne Rückfrage. Texte, Kommentare und Logs auf Deutsch, Ansprache auf der Website per du.

## Worauf du besonders achten sollst
1. **Plan gegen Code, Schritt 3:** Setzt der Code die Abschnitte 3.1, 3.2, 3.6, 3.8 bis 3.14 und „Schritt 3 im Einzelnen“ aus Abschnitt 4 wörtlich um? Nenn jede Abweichung, auch begründete.
2. **Pflicht-Tests aus Abschnitt 4:** Geh die Liste Punkt für Punkt durch und nenn jeden fehlenden oder zu schwachen Test. Bekannte Lücken, bitte bestätigen oder widerlegen:
   - Zielabfrage-Timeout → „weiter“: `spielstaettePruefen` hat keinen eigenen Test.
   - „K20 und K21 sind zwei Seiten“: nur über Daten geprüft.
   - Saal-Filter „Haus allgemein“ und „Events eines Saals erscheinen nicht auf einem anderen Haus“: kein Komponententest.
3. **Proxy (`spielstaetteEntscheidung`, `guideZiel`, `spielstaettePruefen`):**
   - alle Fälle aus Abschnitt 3.10
   - Weiterleitungen über `ziel_ort_id` mit unsichtbarem, inaktivem oder gelöschtem Ziel
   - Guide-Slugs (Club, Bar und Club, Spielplatz, Weihnachtsmarkt, Ausflug)
   - zusammengelegte Märkte
   - `/orte/a/b`
   - Caching über `gemerkt`: Kann ein vorübergehender Fehler als „fehlt“ hängen bleiben?
4. **Indexierung:**
   - Ist die Regel in `lib/spielstaetten.ts` (`indexierbar`, `indexierbareOrte`), in `generateMetadata` der Ortsseite, in `app/sitemap.ts` und in `pipeline/indexnow.py` wirklich dieselbe?
   - Säle erben die Adresse, das Haus zählt die Events seiner Kinder.
   - Sind gefilterte `/orte`-Ansichten `noindex` mit Canonical `/orte`?
   - Was passiert in der Sitemap, wenn `kommendeJeOrt` scheitert?
5. **Ortsseite `/orte/<slug>`:**
   - Programm über `programmLaden` (Haus plus Kinder, seitenweise, abgesagte, mehrtägige „Läuft gerade“)
   - Saal-Chips mit `?saal=` (ungültige Werte, Saalseiten)
   - „Ort nicht gefunden“ und „Gerade nicht verfügbar“ mit `noindex`
   - Titel (Stadt nicht doppelt)
   - Route-Link ohne eingebetteten Google-Rahmen
   - JSON-LD: Typ je Art, `containedInPlace` auf die kanonische Haus-URL, `addressLocality` = Stadt
   - „Weitere Orte“: Säle nutzen die Koordinaten des Hauses
6. **Übersicht `/orte`:**
   - Filter Art, Stadt, Stadtteil und Suche (Neuss und Ratingen ohne Stadtteil)
   - Die Suspense-Vorabversion zeigt die ungefilterte Liste: Ist das für Nutzer und Suchmaschinen in Ordnung?
   - A–Z-Gruppen, Säle unter dem Haus
   - Leer- und Fehlerzustand
7. **Karte (`/api/guide-karte?hub=orte`):**
   - `nahe=<slug>` mit `lat`/`lng` als Rückfall für Säle: nur im Gebiet, Eingaben prüfen
   - nur lokale Bilder
   - Cache-Header
8. **Guide-Seiten mit `OrtProgramm`:**
   - Club-Seite des zakk: Programm aus `ort_id`, nicht aus dem Pool; „nicht im zakk“ erscheint nicht; Saal-Filter
   - Kneipen- und Restaurantseiten ohne `ort_id`-Events: Bleibt der Block weg?
   - Doppelte Blöcke?
9. **Eventseite:**
   - `eventOrtLink`: kanonischer Pfad nach den Hub-Regeln, sonst der alte Suchlink
   - Zusammenspiel mit dem bisherigen Club-Treffer
   - Cache bei Fehlern
10. **IndexNow (`pipeline/indexnow.py`):**
    - nur indexierbare URLs
    - Schalter `ORTSSEITEN_MELDEN`
    - Erstmeldung
    - Abfragen seitenweise
    - Fehlerbehandlung
    - keine Meldung von 404- oder 308-URLs
11. **Schritt 2a (Bücherei):**
    - `filiale_aus_text`: Wertet er nur das Seitenende aus? Fälle FFT, Zentralbibliothek, Kinderbücherei. Ist `FILIAL_ADRESSEN` vollständig und richtig?
    - `filialen_zuordnen`: Pausen, Fehler beim Abruf, Rückfall über den Titel
    - Nachtrag-SQL:
      - nur kommende Events mit `ort = 'Stadtbüchereien Düsseldorf'`
      - Reihen-Schlüssel nur, wenn eindeutig und frei
      - Wiederholbarkeit
      - Reihenfolge „SQL vor Deploy“
    - Passt das zu Plan 3.15? Die Filialzeilen selbst gibt es noch nicht. Sie entstehen erst mit der nächsten Kandidatenliste.
12. **Zusammenspiel mit der Pipeline:** Setzt `ort_zuordnen` nach dem Bücherei-Deploy die `ort_id` für Filialen richtig, sobald es Filialzeilen gibt? Bis dahin: Gehen Events ohne Treffer sauber durch die Kennzahlen?
13. **Sicherheit und Leistung:**
    - Eingaben aus `searchParams` und Slugs (Encoding, Abfrage-Injection in PostgREST-Filtern)
    - Anzahl der Supabase-Abfragen je Seitenaufruf
    - Cache-Schlüssel (`programmLaden(ids)` mit sortierten IDs)
14. **Datenqualität** (nur lesen, falls du Zugriff hast; sonst aus SQL und CSV schließen):
    - Spielstätten ohne Art
    - Säle ohne `parent_id`
    - Häuser ohne Adresse
    - Weiterleitungen auf inaktive Zeilen
    - Orte mit kommenden Events, aber ohne Seite
15. **Deploy-Reihenfolge:** Was muss vor dem Deploy noch passieren? Welche SQL zuerst, welche Schalter, welche `curl -I`-Prüfungen?

## Bericht
Eine Liste, sortiert nach Schwere (**kritisch / hoch / mittel / gering / Hinweis**). Je Befund:
- Ort (Datei:Zeile)
- was falsch ist, mit einem konkreten Beispiel (Eingabe → falsches Ergebnis)
- warum es ein Problem ist
- Vorschlag

Am Ende:
- eine Gesamteinschätzung, ob Schritt 2a und 3 so deployt werden können
- welche Befunde vor dem Deploy behoben sein müssen
- eine Prüfliste für den Live-Test nach dem Deploy
