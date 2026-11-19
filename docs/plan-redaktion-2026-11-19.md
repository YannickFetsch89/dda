# Plan: Redaktionelle Inhalte („Magazin“) auf diesdas.events

Stand 19.11.2026 · **siebte Fassung nach sechs Cursor-Prüfungen vom 19.11. · vom Auftraggeber freigegeben am 19.11.2026**.

- **Cursor-Prüfungen** (alle Befunde eingearbeitet, siehe Anhang A–F):
  - Prüfung 1: 14 Befunde, davon 2 kritisch;
  - Prüfung 2: 8 Befunde, keiner kritisch;
  - Prüfung 3: 4 Befunde, keiner kritisch;
  - Prüfung 4: 4 Befunde, keiner kritisch;
  - Prüfung 5: 2 Befunde, keiner kritisch;
  - Prüfung 6: 2 geringe Befunde. Gesamturteil der sechsten Prüfung: freigabefähig.
- **Entscheidungen:** E1, E2, E4, E4a, E5, E7, E12 und die Modellwahl am 19.11. vom Auftraggeber beantwortet (2.2). Autorenkonzept mit redaktionellen Pseudonymen vom Auftraggeber vorgegeben (2.3).
- **Umsetzung:** noch nichts umgesetzt; startet erst auf ausdrückliche Anweisung des Auftraggebers.
- **Umsetzungsstand (19.11.2026):** Schritte 1–4 live (772b756, cc95cf2, b0b2567, 9b4887b), Schalter aus. E15 und E16 entschieden (2.2): fünf Pseudonyme, sieben Rubriken. Cursor-Gesamtprüfung der Schritte 1–4: bereit für Schritt 5; Befunde eingearbeitet.
- **Vor dem Livegang offen:** Profilbilder (erzeugt der Auftraggeber aus den Prompts, danach SQL für `bild`), Schritt 5 (Impressum § 18 Abs. 2 MStV, Text „Unsere Redaktion“, `llms.txt`), Anwalt A1–A3.

**Ziel:** dies.das.düsseldorf bekommt ein Online-Magazin für Düsseldorf. Die Beiträge sollen Google in **Discover**, in der
**normalen Suche** und in **KI-Suchen** ausspielen können (Google AI Overviews/AI Mode, ChatGPT, Perplexity …).
- **Themen:** Events, Freizeit, Gastronomie, Stadtleben und lokale Tipps.
- **Inhalt:** Die Beiträge verbinden unsere Daten (Events, Guides, Orte) mit redaktionellem Mehrwert: Auswahl, Einordnung, Erfahrung.
- **Autoren:** Die Beiträge erscheinen unter mehreren **redaktionellen Pseudonymen**, offen als solche gekennzeichnet.
- **Verantwortung:** Redaktionell verantwortlich ist der Auftraggeber mit echtem Namen.
- **Beispiele des Auftraggebers:**
  - Weihnachtsmärkte mit Links auf unsere Markt-Seiten;
  - Clubs;
  - laufende Rubriken wie „Events kommende Woche“ und „Top-Events im Dezember“.

**Gleiche Regeln wie bei den bisherigen Plänen:**
- nur belegte Angaben;
- Inhalt in der ersten HTML-Antwort;
- echte 404/308 nur im Proxy, kein `rewrite`;
- keine öffentliche Score-Zahl;
- Deploy nur nach OK;
- Datenbank-Änderungen per SQL durch den Auftraggeber;
- Kosten vor jedem KI-/Google-Lauf nennen;
- keine neue Bibliothek ohne Rückfrage;
- Leser-Ansprache ihr/euch (wie die Guides);
- URL-Änderungen nur mit Weiterleitung.

**Grundsatz:** KI-Agenten schreiben Entwürfe, sie veröffentlichen nie selbst. Den Status „veröffentlicht“ kann **technisch nur
der Auftraggeber** setzen, nicht die Pipeline (3.1, Trigger). Das ist die Voraussetzung für Discover, für Googles
Spam-Richtlinien und für das Medienrecht (1.4).

---

## 0. Zeitplan (Vorschlag, Kalender 2026)

| Datum | Ereignis | Folge für den Plan |
|---|---|---|
| Do 19.11. | siebte Fassung (nach Cursor-Prüfungen 1–6), **Freigabe des Plans am 19.11.** | Umsetzung erst auf Anweisung |
| bis Di 24.11. | Auftraggeber: Namen und Schwerpunkte der Pseudonyme (E15), Anwalt-Fragen A1–A3 gestellt | Autorenprofile (Schritt 5) |
| Di 24.–Do 26.11. | Schritt 1 (SQL), Schritt 2 (Website, Schalter aus), Schritt 3 (Entwurfs-Agenten), Profilbilder | Seiten live, aber noindex und unverlinkt (5.9) |
| Fr 27.11. | Die drei Entwürfe aus Schritt 6: „Welcher Weihnachtsmarkt passt zu euch?“ (Saison), „Top-Events im Dezember 2026“ (Monats-Tipps), erste Wochenvorschau 30.11.–06.12. (regulärer Fr-18-Uhr-Lauf, E6) | KI-Kosten vorher nennen (4.4) |
| Sa 28.11. | Prüfung aller drei Entwürfe und Veröffentlichung durch den Auftraggeber (Zeitsteuerung So 8 Uhr) | – |
| **So 29.11.** (1. Advent) | **Livegang Stufe 1:** Schalter an, **die drei Beiträge aus Schritt 6** (inkl. Wochenvorschau), Autorenseiten, „Unsere Redaktion“, Feed, Sitemap, IndexNow | Suchinteresse an Weihnachtsmärkten am höchsten; danach Wochenvorschau wöchentlich (E6) |
| Mo 28.12. | „Silvester in Düsseldorf“ (Saison) + Wochenvorschau | – |
| Do 31.12. | „Top-Events im Januar 2027“ | monatlich |
| ab Januar 2027 | Messung (Abschnitt 9), Stadtleben-Beitrag „Feiern in Düsseldorf“ (E5) | Karneval 2027: Altweiber Do 04.02., Rosenmontag 08.02. |

Ist bis So 29.11. nicht alles geprüft, startet das Magazin später. Ein halbfertiger Beitrag oder ein Autorenprofil ohne Kennzeichnung geht nicht online.

---

## 1. Geprüfte Fakten (Stand 19.11.2026)

### 1.1 Live-Stand diesdas.events (abgerufen am 19.11.)
- Seitenweites robots `max-image-preview:large` steht seit heute im Code (`web/lib/seo.ts:73` `ROBOTS_INDEX`, Layout
  `web/app/layout.tsx:34`), gebaut von der Hauptsession.
  - Seiten mit eigenem `robots` müssen `ROBOTS_INDEX` im indexierbaren Fall selbst setzen (`seo.ts:70–72`).
  - Ein Beitrag ohne eigenes `robots` behält den Layout-Wert.
- `/feed.xml` antwortet 404. Es gibt keinen Feed.
- JSON-LD heute:
  - Startseite: `Organization` (`@id …/#organisation`) und `WebSite` (`web/lib/seo.ts:20,29`);
  - Guides: `FAQPage`, `ItemList`, `BreadcrumbList`;
  - Event-Seiten: `Event` mit `@id` = Seiten-URL (`web/lib/json-ld.ts:57`).
  - Es gibt **kein** `Article`, keine Autoren und keine Autorenseite.
- Standard-Vorschaubild `/og-standard.png` ist 1200×630.

### 1.2 Code-Stand
**Proxy** `web/proxy.ts` und `web/lib/pfad-pruefung.ts`:
- Der Proxy läuft **nur für die Pfade im `matcher`** (`proxy.ts:61–63`): `/event/…`, `/tag/…`, `/reihe/…`, `/guides/:hub/:slug`, `/guides/:hub/stadtteil/:slug`, `/kategorie/…`, `/stadtteil/…`, `/entdecken`.
  - `/magazin/…` und `/feed.xml` stehen dort **nicht**. Eine Erweiterung von `routeVon` allein erreicht sie nie (Befund 2).
- `routeVon` (`pfad-pruefung.ts:48–61`) gibt für unbekannte Präfixe `null` zurück.
- Mit Streaming (cacheComponents) wird `notFound()` in der Seite eine **Soft-404 mit Status 200** (`pfad-pruefung.ts:2–4`). Deshalb kommen 404/308 nur aus dem Proxy, mit statischem `NICHT_GEFUNDEN_HTML` (`proxy.ts:19`) und `Cache-Control: no-store`.
- Zwischenspeicher je Server-Prozess (`pfad-pruefung.ts:69–80`): Treffer 10 min (`TREFFER_MS`), Fehltreffer 2 min (`FEHLT_MS`).

**SEO-Helfer** `seitenMetadaten()` (`web/lib/seo.ts:75`):
- Canonical über `alternates` (Z. 82) oder noindex,follow ohne `alternates`.
- `openGraph.type` ist fest `"website"` (Z. 87).
- Ein gesetztes `alternates` **ersetzt das Layout-Feld komplett** (Next-Metadaten-Auflösung). Ein Feed-Link nur im Layout fehlt deshalb auf allen Seiten mit eigenem `alternates`. Das sind die Startseite (`app/page.tsx:41` über `seitenMetadaten`) und alle Seiten mit `seitenMetadaten` im indexierbaren Zweig. Dazu kommen Seiten mit eigenem `alternates`:
  - `web/app/guides/page.tsx:23`
  - `guides/weihnachtsmaerkte/page.tsx:57`
  - `guides/clubs/page.tsx:46`
  - `guides/clubs/[slug]/page.tsx:60`
  - `guides/kneipen-bars/page.tsx:43`
  - `guides/kneipen-bars/[slug]/page.tsx:44`
  - `guides/spielplaetze/page.tsx:42`
  - `guides/restaurants-cafes/page.tsx:51`
  - `guides/restaurants-cafes/[slug]/page.tsx:32`
  - `reihe/[slug]/page.tsx:26`
  - `event-melden/page.tsx:11`
  - Fundstellen aus der Cursor-Prüfung, Befund 5.
- Der noindex-Test erwartet `alternates === undefined` (`web/tests/seo-a1.test.ts:116`).

**Caching:**
- Daten-Funktionen: `"use cache"` + `cacheLife({ stale: 300, revalidate: 600, expire: 3600 })` (`web/lib/daten.ts:145`).
- `revalidateTag` wird nur in `web/app/ort-foto/[slug]/route.ts:35` aufgerufen (Import Z. 11).

**Interne Links in Texten:**
- `LINK_MUSTER` (`web/lib/guide-texte.ts:529`) erlaubt nur Ziele mit führendem `/`. Damit erlaubt es auch `//fremde-seite.de`, und `https://` gar nicht (Befund 6).
- Der Beitrags-Renderer bekommt eigene, strengere Muster (T2).

**Empfehlungslogik** in `web/lib/ableitungen.ts`:
- `wochenendProgramm()` Z. 328: **nur Fr–So**, also nicht für die Wochenvorschau Mo–So;
- `highlights()` Z. 357: Highlight der Woche, Top-Event des Monats;
- `startPlaetze()` Z. 693;
- `beliebtAuswahl()` Z. 750;
- Stufen `stufenKontext`/`breite`.

**Karten:**
- Event-Karten in `web/components/karten.tsx` mit Symbolbild-Hinweis (`BildImg symbolAlt`).
- `OrtKarte` (`web/components/ort-karten.tsx:85–114`) und `GuideKarte` (`web/components/guide-karte.tsx:387`) zeigen **Google-Foto (`ortBildUrl`) und Google-Bewertung (`google_rating`)**. Beide sind im Magazin tabu (1.4), also eine eigene schmale Ort-Karte (5.2).

**Bild-Proxy** `web/app/bild/event/[id]/route.ts:34–36`: prüft nur eine Event-UUID, keine freien Dateipfade. `sharp` steht in `web/package.json:23`.

**Weitere Bausteine:**
- **Schalter** `web/lib/schalter.ts:10–20`: Muster `…_VERLINKT` steuert Menü, Footer, Kacheln und Startseite. `public/llms.txt` wird von Hand gepflegt.
- **Sitemap** `web/app/sitemap.ts` (Einträge mit `lastModified`, `images`), **robots** `web/app/robots.ts` (alles erlaubt außer `/api/`).
- **IndexNow:** `pipeline/indexnow.py` `melden(urls)`.

**KI-Pipeline** (Python):
- `anthropic==2.4.0` (`requirements.txt:5`);
- `output_config` mit `effort` bereits genutzt (`pipeline/beschreibung_quellen.py:355`);
- Modelle heute: `pipeline/caption_generator.py` claude-sonnet-4-6, `beschreibung_quellen.py` claude-haiku-5-5, Kategorisierung `claude-haiku-4-5-20251001` (`pipeline/categorizer.py:102`).
- Für Bilder ist laut CLAUDE.md DALL-E 3 (OpenAI) im Projekt vorgesehen.

**Bilder** (gemessen am 19.11. mit `sharp`):
- `web/public/fallback/`: 151 Symbolbilder, alle 1200 px breit, alle > 300 000 Pixel.
  - 84 sind mindestens 675 px hoch: 69× 1200×675, 12× 1200×805, 1× 1200×800, 2× 1200×900.
  - 64× 1200×655, 3× 1200×670.
  - **Diese Bilder sind KI-generiert** (Foto-Prompt, `docs/fallback-bilder.md:24–28`).
- `web/public/ort-bilder/`: 16 Dateien, 1254–1600 px breit, alle hoch genug für 16:9.
  - Unter `weihnachtsmaerkte/` sind laut `database/weihnachtsmarkt_bilder_2026-11-18*.sql` 13 Fotos **eigene Fotos des Auftraggebers**.
  - `koe-on-ice.webp` ist ein **Fremdfoto** („Foto: DEG Winterwelt“).
  - Die zwei Dateien unter `events/` haben eine eigene Herkunft (Further, Rennbahn).
  - Als Magazin-Hero nur die 13 eigenen Fotos.

**Konten** sind live (17.11.). Eine Rolle „Redaktion“ gibt es nicht.

**Rechte-Prüfung** `database/konten_rechte_pruefung_2026-11-16.sql:164–176`: Eine View ohne `security_invoker` läuft mit den Rechten des Eigentümers und **umgeht RLS**.

### 1.3 Externe Quellen (Google, abgerufen am 19.11.2026)

| Quelle | Kernaussage | Folge |
|---|---|---|
| Google Search Central „Discover“ | Keine Anmeldung, kein Pflicht-Markup. Bilder ≥ 1200 px breit, > 300 000 Pixel, 16:9, `max-image-preview:large`. Kein Logo, keine textlastigen Bilder. Keine Clickbait-Titel, keine Sensationsmache. „timely“, gut erzählt, eigene Einsichten. Discover-Leistungsbericht (16 Monate, Mindest-Impressionen). Verkehr „less predictable“, also nur Ergänzung | 5.2, 5.11, 6, 9 |
| Google „Article structured data“ | Typen `Article`/`NewsArticle`/`BlogPosting`, keine Pflichtfelder. Empfohlen: `headline`, `image` (16:9, 4:3, 1:1, je ≥ 50 000 Pixel), `datePublished`, `dateModified` (ISO 8601 **mit Zeitzone**), `author` (`Person` oder `Organization`) mit `url`. Alle auf der Seite gezeigten Autoren auszeichnen, nur der Name in `author.name` | 5.4, 2.3 |
| Google „News sitemap“ | Für Nachrichten-Publisher. Nur Artikel der **letzten 2 Tage**, max. 1000 Einträge | keine News-Sitemap (E13) |
| Google „Folgen“ in Discover/Chrome | Die frühere Doku-Seite antwortet 404 (19.11.). Laut Fachpresse (Search Engine Journal, SamMobile) läuft „Folgen“ über einen im `<head>` verlinkten **RSS-/Atom-Feed**. Wichtig sind der Feed-Titel und die Item-Links. „Search profiles“ für Publisher seit 06/2026 nur in den USA | Feed ja (5.6), Nutzen für „Folgen“ unbelegt |
| Google Spam-Richtlinien („scaled content abuse“) | Viele Seiten mit wenig Mehrwert, egal ob von KI oder Mensch, können manuelle Maßnahmen auslösen | Freigabe, begrenzte Frequenz, Mehrwert-Prüfung (R2) |
| Google Qualitäts-Richtlinien (allgemein, nicht in dieser Session nachgelesen) | Irreführende Angaben darüber, wer einen Inhalt erstellt hat, gelten als vertrauensmindernd | Pseudonyme offen kennzeichnen, keine erfundenen Qualifikationen (2.3, R12) |
| IndexNow | Bing, Yandex, Seznam, Naver. **Google nimmt nicht teil**. Eine Meldung löst einen erneuten Abruf aus. Eine 404-URL fällt danach heraus | 5.8 |

### 1.4 Rechtliches (keine Rechtsberatung; Prüfpunkte für den Anwalt in E11)
- **Impressum:**
  - `web/app/impressum/page.tsx:62` nennt „§ 55 Abs. 2 RStV“. Der Rundfunkstaatsvertrag gilt seit 07.11.2020 nicht mehr. Richtig ist **§ 18 Abs. 2 MStV**: verantwortliche Person mit Name und Anschrift für journalistisch-redaktionelle Angebote.
  - Mit dem Magazin gelten die **journalistischen Sorgfaltspflichten (§ 19 MStV)**.
  - Der Auftraggeber wird mit echtem Namen als Verantwortlicher genannt (Vorgabe 2.3). Änderung in Schritt 5; das ist Text, keine URL.
- **Pseudonyme:** Redaktionelle Pseudonyme sind üblich und zulässig, wenn die Verantwortung offengelegt ist (§ 18 Abs. 2 MStV) und keine Irreführung entsteht. Also keine erfundenen Qualifikationen, Lebensläufe oder persönlichen Erlebnisse und eine offene Kennzeichnung (2.3) → A1.
- **KI-Kennzeichnung (EU-KI-Verordnung):**
  - **Texte:** Art. 50 Abs. 4 verlangt die Offenlegung von KI-Texten zu Angelegenheiten von öffentlichem Interesse. Ausgenommen sind menschlich geprüfte Texte mit redaktioneller Verantwortung. Wir kennzeichnen trotzdem (E4).
  - **Bilder:** Die Symbolbilder und die Profilbilder sind KI-generiert. Für realistisch wirkende Bilder, die echte Orte oder Szenen zeigen, kann die Offenlegungspflicht für Deepfakes (Art. 50 Abs. 4) greifen. Art. 50 Abs. 2 betrifft die Anbieter des Modells (maschinenlesbare Markierung). → Kennzeichnung „KI-generiert“ an jedem solchen Bild im Magazin (E7, 2.3). A1 umfasst Texte und Bilder.
- **Bilder, sonstige:**
  - **Google-Places-Fotos:** EEA-Bedingungen (Notiz `google-eea-bedingungen.md`) → **im Magazin keine Google-Fotos und keine Google-Bewertungen**.
  - **Veranstalterbilder:** als Hero nur nach Klärung (A2). In Event-Karten bleiben sie wie heute.
  - **Erkennbare Personen (KUG §§ 22, 23):** im Hero nur ohne erkennbare Einzelpersonen oder mit Einwilligung.
- **Werbung:** Keine bezahlten Beiträge in Stufe 1. Später gilt die Kennzeichnung nach § 22 MStV (eigener Plan).
- **Gegendarstellung (§ 20 MStV)** bei periodischen journalistisch-redaktionellen Texten → A3.

---

## 2. Entscheidungen

### 2.1 Technisch

| Nr. | Entscheidung | Begründung |
|---|---|---|
| T1 | Beiträge und Autoren in **Supabase-Tabellen** (`magazin_beitraege`, `magazin_autoren`, 3.1), nicht als Dateien im Repo | Wöchentliche Rubriken bräuchten mit Repo-Dateien je Ausgabe einen Push mit OK. Mit Tabellen ist die Freigabe ein Datenschritt. Gegenrechnung in 3.2 |
| T2 | Beitragstext als **eingeschränktes Markdown**, gerendert von einem **eigenen Renderer** (keine neue Bibliothek, kein HTML aus der DB). Erlaubt: Überschriften `##`/`###`, Absätze, Listen, `**fett**`, Links, Einbettungen `{{event:…}}`, `{{ort:…}}`, `{{guide:…}}`, `{{tag:…}}` | **Links:** Ziel zuerst einmal dekodieren (`decodeURIComponent`, Fehler → Text), dann die Regeln anwenden (Prüfung 2, Befund 6: sonst schlüpfen `/%2e%2e/` und `/%2f%2ffremd.de` durch). Intern nur `^/(?![/\\])` ohne `..`-Segment; extern nur `^https://` als zweites Muster. Alles andere (auch `//fremd.de`, `javascript:`, `data:`) wird reiner Text. **Einbettungs-IDs:** `event` = UUID, `ort`/`guide` = `^[a-z0-9]+(-[a-z0-9]+)*$`, `tag` = gültiger Tag (`istGueltigerTag`). Passt die ID nicht, wird die Einbettung als Text verworfen. Ausgabe nur über React (Escaping), nie über `dangerouslySetInnerHTML` |
| T3 | **Fakten kommen aus den Daten, nicht aus dem Text.** Datum, Uhrzeit, Ort und Preis stehen in der eingebetteten Karte, die live rendert. Der Fließtext beschreibt und ordnet ein | Ändert sich ein Event oder fällt es aus, stimmt die Karte trotzdem. Die Prüfung 4.2 (b) verbietet Zeiten, Preise und „ausverkauft“ im Fließtext |
| T4 | **Proxy prüft alle Magazin-Pfade.** `matcher` bekommt `/magazin/:path*` und `/feed.xml`. `routeVon` erkennt die Magazin-Routen (5.1); Entscheidung in `pfadPruefen`. Kein `rewrite` | Echte 404/308 statt Soft-404 (Befund 2) |
| T5 | Workflow-Status `entwurf` → `in_pruefung` → `veroeffentlicht` (+ `zurueckgezogen`). Sichtbar nur `veroeffentlicht` **und** `veroeffentlicht_am <= now()` (Zeitsteuerung). **Nur der Auftraggeber** kann `veroeffentlicht` setzen; ein Trigger verweigert das der Rolle `service_role` (Pipeline) und den Rollen `anon`/`authenticated` | Vorgabe des Auftraggebers (2.3 Punkt 4): kein KI-Artikel ohne Freigabe |
| T6 | Job `pipeline/magazin.py` (GitHub Action, `concurrency: magazin`, `cancel-in-progress: false`): Entwürfe nach Zeitplan; stündlich IndexNow für neu sichtbare Beiträge (`gemeldet_am`); täglich Prüflauf (5.12). **Entwürfe** nur mit GitHub-Variable `MAGAZIN_AKTIV=1`. **IndexNow-Meldungen** nur, wenn `https://diesdas.events/magazin/feed.xml` mit 200 antwortet: Der Feed gibt bei `MAGAZIN_VERLINKT = false` 404 (T9), damit folgt die Meldung dem Website-Schalter | Freigabe im Table Editor hat keinen Hook. Prüfung 2, Befund 8: Der Job kann den TS-Schalter nicht lesen; ohne Feed-Abfrage würde er Seiten melden, die noch `noindex` sind. Die `concurrency`-Gruppe verhindert gleichzeitige Läufe (Kostendeckel, 4.4) |
| T7 | **Ressort-Agenten:** je Pseudonym ein eigenes Schreibprofil (Systemprompt mit Ton, Themen, Rubriken) in `pipeline/magazin_profile/<autor>.md`, gleiches Modell | „Verschiedene KI-Agenten“ (2.3) ohne mehrere Modelle oder Dienste. Profile versioniert im Repo |
| T8 | JSON-LD-Typ `Article` für alle Rubriken; kein `NewsArticle` in Stufe 1 | Unsere Beiträge sind Service-Journalismus. `NewsArticle` erst mit Google News (E13) |
| T9 | Schalter `MAGAZIN_VERLINKT` in `web/lib/schalter.ts` steuert **auch Indexierung, Sitemap und Feed**: aus → Magazin-Seiten `noindex,follow`, nicht in Sitemap, Feed 404, kein Feed-Link im `<head>` | Befund 11: ein veröffentlichter Beitrag wäre sonst bei Schalter aus über Sitemap und Feed öffentlich |
| T10 | Magazin-Daten mit **eigenem kurzen `cacheLife`** `{ stale: 60, revalidate: 300, expire: 600 }`. Proxy-Zwischenspeicher für Magazin: Treffer 5 min, Fehltreffer 60 s | Befund 4: normal bis 5 min nach `veroeffentlicht_am` (`revalidate`), spätestens 10 min (`expire`). Ein zurückgezogener Beitrag ist höchstens 10 min noch sichtbar |
| T11 | **Datenauswahl in TypeScript:** interne Route `POST /api/magazin/auswahl` (`{ rubrik, von, bis }` → Kandidaten mit Event-IDs, Highlight/Top). Geschützt mit Header-Schlüssel `MAGAZIN_JOB_SCHLUESSEL`. **Vergleich** (Cursor-Prüfung 4, Befund 1): SHA-256 des gesendeten und des gespeicherten Werts bilden (immer gleich lang), dann `crypto.timingSafeEqual`. Fehlender Header, falscher Wert **oder fehlende Umgebungsvariable** → 404, nie 500. `Cache-Control: no-store`. `/api/` ist in `robots.ts` nur für Crawler gesperrt; der Schutz ist der Header. **Schlüssel auf dem Server:** GitHub-Secret → `deploy.yml` (`env` + `envs`) → wie `SUPABASE_SERVICE_KEY` (`deploy.yml:72–81`) per `grep`/`sed` **nach `web/.env.local` geschrieben, vor `npm run build`**. Nur `envs` reicht nicht: `web/deploy/website.sh:99` startet Next ohne die Variablen der SSH-Sitzung. Derselbe Wert als Secret in der Magazin-Action. **Fehler im Job** (Befund 2): Status ≠ 200, Zeitüberschreitung (30 s), ungültiges JSON oder ein Körper ohne die erwarteten Felder (`rubrik`, `von`, `bis`, `kandidaten[]` mit gültigen UUIDs) → Lauf dieser Rubrik endet: **keine Zeile, kein Modellaufruf, keine Kostenreservierung**, Fehler im Log. Eine echte leere Auswahl (z. B. Woche ohne passende Events) ist ein gültiges Ergebnis: kein Entwurf, Hinweis im Log | Die Stufen- und Highlight-Logik (`ableitungen.ts`) gibt es nur in TypeScript. Ein Nachbau in Python würde mit der Zeit von der Startseite abweichen. Auswahl ohne KI, also ohne Kosten |

### 2.2 Entscheidungen des Auftraggebers

| Nr. | Frage | Stand |
|---|---|---|
| **E1** | Name und URL | **entschieden 19.11.: „Magazin“, `/magazin`** |
| **E2** | Wer ist Autor? | **entschieden 19.11.: mehrere redaktionelle Pseudonyme**, Konzept in 2.3 |
| E3 | Wie wird geprüft und freigegeben? | Empfehlung (gilt, solange nichts anderes gesagt): in Stufe 1 im Supabase-Table-Editor (Status setzen), Korrekturen direkt in `inhalt_md` oder per Chat. Stufe 2: Redaktionsseite `/konto/redaktion` für ein Admin-Konto |
| **E4** | Sichtbarer KI-Hinweis | **entschieden 19.11.:** nur am Ende des Beitrags: „Mit KI-Unterstützung aus unseren Eventdaten erstellt, von der Redaktion geprüft und freigegeben. Redaktionell verantwortlich: Yannick Fetsch.“ Für Beiträge ohne Eventdaten siehe E4a |
| **E4a** | Wortlaut für Beiträge, die nicht (nur) auf Eventdaten beruhen | **entschieden 19.11.:** Die Datenart wird automatisch aus den Einbettungen gewählt. Nur Events → „aus unseren Eventdaten“; nur Orte → „aus unseren Ortsdaten“; beides oder keins → „aus unseren Event- und Ortsdaten“. Der Rest des Satzes bleibt wie E4. Der Weihnachtsmarkt-Beitrag nutzt damit den Ortsdaten- bzw. Event- und Ortsdaten-Satz |
| **E5** | Abgrenzung zu den Guides | **entschieden 19.11.: eigener Blickwinkel.** Titel beginnt nie mit dem Hub-Kopfbegriff („Weihnachtsmärkte in Düsseldorf“, „Clubs in Düsseldorf“). Der Hub behält den kurzen Suchbegriff, der Beitrag verlinkt ihn prominent |
| E6 | Erscheinungstermin Wochenvorschau | Empfehlung: Sonntag 8:00 Uhr (Zeitsteuerung), Entwurf Freitag 18:00, Prüfung bis Samstagabend |
| **E7** | Herkunft der Aufmacherbilder | **entschieden 19.11.: KI-Symbolbilder aus `public/fallback/` in allen Rubriken erlaubt, immer gekennzeichnet** „Symbolbild (KI-generiert)“. Nur die 84 Motive mit mindestens 675 px Höhe. Bevorzugt bleiben eigene Fotos (z. B. `public/ort-bilder/`). Keine Google-Fotos, keine Veranstalterbilder als Hero (bis A2) |
| E8 | Frequenz in Stufe 1 | Empfehlung: Wochenvorschau wöchentlich, Monats-Tipps monatlich, Saison/Anlass 1–2 pro Monat, Stadtleben ca. 1 pro Monat |
| E9 | Startseite | Empfehlung: Box „Aus dem Magazin“ unter den Event-Stufen, Position nach Screenshot |
| E10 | Menü | Empfehlung: „Magazin“ nach „Guides“, auch im Mobilmenü und Footer |
| E11 | Anwalt-Fragen A1–A3 | Empfehlung: vor dem Livegang stellen, Bau parallel |
| **E12** | Abgelaufene Ausgaben | **entschieden 19.11.:** Seite bleibt mit Hinweis auf die aktuelle Ausgabe; **30 Tage nach `gueltig_bis` noindex,follow**, raus aus Sitemap und Feed. Nie löschen, keine Umleitung |
| E13 | Google News / `NewsArticle` | Empfehlung: nein in Stufe 1 |
| E14 | Instagram/Newsletter | nicht Teil dieses Plans |
| **E15** | Namen, Schwerpunkte und Kurzbeschreibungen der Pseudonyme | **entschieden 19.11.: fünf Ressorts** – Lisa Hartwig (Events & Wochenplanung; Rubriken Wochenvorschau, Monats-Tipps), Dan Suttner (Nachtleben & Musik), Nathalie Kirchner (Stadtleben; Rubriken Saison, Stadtleben und alles nicht eindeutig Zuordenbare), Laurenz Weigelt (Genuss: Restaurants, Cafés, Foodmärkte, Tastings), Amelie Glasner (Familie). Namensprüfung per Websuche ohne Treffer auf bekannte Personen. Kurzbeschreibungen von Claude entworfen, vom Auftraggeber zu prüfen (SQL `database/magazin_rubriken_autoren_2026-11-19.sql`). Regeln in 2.3 |
| **E16** | Eigene Rubriken für Nachtleben, Genuss, Familie? | **entschieden 19.11.: ja.** Rubriken jetzt `wochenvorschau`, `monats-tipps`, `saison`, `nachtleben`, `genuss`, `familie`, `stadtleben` (Wert = URL-Segment = CHECK, Plan 3.1). Rubrik-Ersatzbilder der neuen Rubriken: `nacht-der-museen-2`, `sprachcafe-3`, `ostern-3` (ohne erkennbare Gesichter). Je Rubrik genau ein Standard-Autor (`magazin_autoren.rubriken`) |
| **Modell** | Welches Modell schreibt? | **entschieden 19.11.: Claude Opus 5.5** (`claude-opus-5-5`) |

### 2.3 Autorenkonzept (Vorgabe des Auftraggebers vom 19.11., technisch umgesetzt)

**Vorgaben (sinngemäß):**
- Mehrere redaktionelle Pseudonyme mit Name, Profilbild, Kurzbeschreibung und Themenschwerpunkt.
- **Keine erfundenen Qualifikationen oder Lebensläufe.**
- Profilbilder dürfen KI-generiert sein und werden gekennzeichnet. **Stil: illustriert** (entschieden 19.11.), nicht fotorealistisch.
- Beiträge können von verschiedenen KI-Agenten recherchiert und erstellt werden.
- **Jeder Beitrag wird vom Auftraggeber persönlich geprüft und freigegeben.**
- Der Auftraggeber steht mit echtem Namen als Verantwortlicher nach § 18 Abs. 2 MStV im Impressum.
- Autorenseiten erklären offen, dass es sich um redaktionelle Pseudonyme handelt und dass KI-Werkzeuge eingesetzt werden können.
- Eine zentrale Seite „Unsere Redaktion“ erklärt das Konzept.

**Umsetzung:**
1. **Autorenprofile** in `magazin_autoren` (3.1):
   - Name (Pseudonym), Slug, Kurzbeschreibung (nur Themen und Ton, keine Biografie);
   - Schwerpunkt, zugeordnete Rubriken;
   - Profilbild (illustriert, 1:1, ≥ 400 px, `web/public/magazin-autoren/<slug>.webp`), Kennzeichen `bild_ki`.
2. **Regeln für Pseudonyme** (Prüfung durch den Auftraggeber vor Schritt 5):
   - Keine Namen bekannter realer Personen (kurze Websuche je Name).
   - Keine Berufsbezeichnungen, Abschlüsse, Altersangaben oder Wohnorte.
   - Keine Ich-Erlebnisse im Text, die so nicht stattgefunden haben. Erfahrung des Auftraggebers erscheint als „aus der Redaktion“/„unser Tipp“, nicht als erfundene Erinnerung des Pseudonyms.
3. **Zuordnung:** Jeder Beitrag hat genau einen Autor (`autor_slug`, Fremdschlüssel). Laufende Rubriken bekommen den Autor über die Rubrik-Zuordnung, Saison- und Stadtleben-Beiträge über den Schwerpunkt.
4. **Autorenseite** `/magazin/autor/[slug]`:
   - Profilbild mit Unterzeile „KI-generiertes Profilbild“, Name, Kurzbeschreibung, Schwerpunkt;
   - Kasten „Redaktionelles Pseudonym“: „[Name] ist ein redaktionelles Pseudonym von dies.das.düsseldorf. Beiträge unter diesem Namen entstehen mit Unterstützung von KI-Werkzeugen aus unseren Daten und werden vor der Veröffentlichung von Yannick Fetsch geprüft und freigegeben. Er ist redaktionell verantwortlich.“ (Wortlaut in Schritt 5 freigeben);
   - Liste der Beiträge, Link auf „Unsere Redaktion“ und Impressum.
5. **„Unsere Redaktion“** `/magazin/redaktion`. Inhalte:
   - Redaktionskonzept: Wer wir sind, welche Daten wir nutzen.
   - Übersicht der Pseudonyme mit Ressorts.
   - Wie KI eingesetzt wird und wie geprüft wird (Workflow 4.2).
   - Verantwortlicher mit echtem Namen, Korrekturen und Hinweise (Kontakt), Quellenregeln.
   - Kennzeichnung von KI-Bildern.
   - Diese Seite ist `publishingPrinciples` der Organisation (5.4). „So arbeiten wir“ aus der ersten Fassung geht hierin auf; `/ueber` verlinkt sie.
6. **Strukturierte Daten ohne Vortäuschung realer Personen** (Vorgabe 2.3 Punkt 5) → 5.4:
   - `author` = **`Organization`** „Redaktion dies.das.düsseldorf“ (`@id …/magazin/redaktion#redaktion`, `url` `/magazin/redaktion`).
   - Das Pseudonym steht **nur sichtbar** auf der Seite, **nicht im JSON-LD** (Prüfung 2, Befund 4). Google liest bei `Article` nur `Person` oder `Organization` als Autor; `Role`/`Thing` hätte nichts gebracht außer einer möglichen Warnung im Rich-Results-Test.
   - Dazu `accountablePerson` = `Person` „Yannick Fetsch“ (die echte Person, `url` `/impressum`).
   - Autorenseiten bekommen `ProfilePage` **nicht**, sondern `WebPage` + `BreadcrumbList`. `ProfilePage` setzt eine Person oder Organisation als Hauptentität voraus.
   - **Warum:** Ein Pseudonym als `Person` würde eine eigenständige reale Person behaupten. `Organization` als Autor ist von Google ausdrücklich erlaubt.
   - **Sichtbare Autorenzeile im Beitrag:** „von [Pseudonym] (redaktionelles Pseudonym) · Redaktion dies.das.düsseldorf“. Das Wort „Pseudonym“ steht damit schon am Beitrag, nicht erst auf der Autorenseite.
   - Prüfung 2 hat bestätigt, dass dieses Modell schema.org-gültig ist und keine reale Person vortäuscht.
7. `og:article:author` und `<meta name="author">` = „Redaktion dies.das.düsseldorf“, gleiche Logik.
8. **Erwartung (R12):** Pseudonyme bringen weniger E-E-A-T-Signal als eine echte, nachprüfbare Person. Die offene Kennzeichnung verhindert Irreführung, ersetzt aber keine echte Autorschaft. Mehr Vertrauen schaffen: ein Beitrag oder eine Notiz des Verantwortlichen unter echtem Namen auf „Unsere Redaktion“ und echte Fotos.

---

## 3. Datenmodell

SQL in `database/magazin_2026-11-xx.sql`, führt der Auftraggeber aus. Danach die Rechte-Prüfung
`database/konten_rechte_pruefung_2026-11-16.sql` erneut laufen lassen; Ziel: keine „LÜCKE“ bei den neuen Objekten.

### 3.1 Tabellen

**`magazin_autoren`**

| Spalte | Typ | Zweck |
|---|---|---|
| `slug` | text PK, CHECK `^[a-z0-9]+(-[a-z0-9]+)*$` | URL `/magazin/autor/[slug]` |
| `name` | text | Pseudonym |
| `kurzbeschreibung` | text, ≤ 300 Zeichen | ohne Qualifikationen (2.3) |
| `schwerpunkt` | text | Ressort |
| `rubriken` | text[] | Standard-Autor je Rubrik |
| `bild` | text, CHECK `^/magazin-autoren/[a-z0-9-]+\.webp$` | Profilbild |
| `bild_ki` | boolean not null default true | Hinweis „KI-generiertes Profilbild“ |
| `aktiv` | boolean default true | – |

**`magazin_beitraege`**

| Spalte | Typ | Zweck |
|---|---|---|
| `id` | uuid PK | – |
| `slug` | text unique, CHECK `^[a-z0-9]+(-[a-z0-9]+)*$` und nicht in (`rubrik`, `autor`, `vorschau`, `seite`, `redaktion`) | URL |
| `alte_slugs` | text[] default `{}` | 308 im Proxy |
| `rubrik` | text CHECK in (`wochenvorschau`, `monats-tipps`, `saison`, `stadtleben`) | **Wert = URL-Segment** (Befund 9), keine Zuordnungstabelle |
| `autor_slug` | text not null FK → `magazin_autoren.slug` | 2.3 |
| `titel` | text, ≤ 90 Zeichen | H1, `headline` |
| `seo_titel` | text null, ≤ 60 | `<title>` |
| `teaser` | text, 80–160 Zeichen | Meta-Description, Feed |
| `inhalt_md` | text | Text (T2) |
| `kurzfassung` | text[] (3–5) | „Auf einen Blick“ |
| `faq` | jsonb null | `[{frage, antwort}]` |
| `hero_bild` | text, Constraint `magazin_hero_pfad` (Muster und Fremdfoto-Verbot im SQL-Block unten, nicht in dieser Tabelle) | Hero (Befund 3) |
| `hero_alt` | text | Alt-Text |
| `hero_nachweis` | text | z. B. „Foto: dies.das.düsseldorf“ |
| `hero_ki` | boolean not null default false | Hinweis „Symbolbild (KI-generiert)“; Trigger setzt true für `/fallback/…` |
| `status` | text CHECK in (`entwurf`, `in_pruefung`, `veroeffentlicht`, `zurueckgezogen`) | T5 |
| `veroeffentlicht_am` | timestamptz null | sichtbar ab; `datePublished` |
| `aktualisiert_am` | timestamptz null | nur bei inhaltlicher Änderung; `dateModified` |
| `korrektur_hinweis` | text null | sichtbarer Korrekturhinweis (5.12) |
| `gueltig_von`/`gueltig_bis` | date null | Zeitraum der Ausgabe |
| `naechste_pruefung` | date null | Erinnerung Überarbeitung |
| `event_ids` | uuid[] | aus Einbettungen, für Prüfungen und „Erwähnt im Magazin“ |
| `ort_slugs` | text[] | dito |
| `quellen` | jsonb | `[{titel, url, abgerufen_am}]` |
| `ki_entwurf` | jsonb | Modell, Agent/Profil, Prompt-Version, Tokens, **Kosten in USD**, Zeit, Hash der Eingabe |
| `pruefung` | jsonb | Ergebnis 4.2 (3) und Prüflauf |
| `vorschau_hash` | text null | SHA-256 eines Zufallsschlüssels je Entwurf (5.3); wird bei `veroeffentlicht` geleert |
| `freigegeben_von` / `freigegeben_am` | text / timestamptz | – |
| `gemeldet_am` | timestamptz null | IndexNow |
| `erstellt_am` | timestamptz default now() | – |

**`magazin_ki_kosten`** (nur Pipeline, keine Rechte für `anon`/`authenticated`, RLS an ohne Policy)

| Spalte | Typ | Zweck |
|---|---|---|
| `id` | uuid PK | – |
| `zeitpunkt` | timestamptz default now() | Monatssumme |
| `art` | text CHECK in (`reserviert`, `gemessen`) | 4.4 |
| `kosten_usd` | numeric(8,4) | Schätzung bzw. Messung |
| `beitrag_id` | uuid null FK → `magazin_beitraege.id` on delete set null | Zuordnung |
| `modell`, `tokens_ein`, `tokens_aus` | text, int, int | Protokoll |

**Rechte (Befund 3):**

```sql
alter table magazin_beitraege enable row level security;
alter table magazin_autoren   enable row level security;
alter table magazin_ki_kosten enable row level security;  -- keine Policy: nur service_role
revoke all on magazin_beitraege, magazin_autoren, magazin_ki_kosten from public, anon, authenticated;
-- nur öffentliche Spalten, nur für Lesende
grant select (id, slug, rubrik, autor_slug, titel, seo_titel, teaser, inhalt_md, kurzfassung, faq, hero_bild, hero_alt,
              hero_nachweis, hero_ki, veroeffentlicht_am, aktualisiert_am, korrektur_hinweis, gueltig_von, gueltig_bis,
              event_ids, ort_slugs, quellen)
  on magazin_beitraege to anon, authenticated;
create policy magazin_lesen on magazin_beitraege for select to anon, authenticated
  using (status = 'veroeffentlicht' and veroeffentlicht_am <= now());
grant select (slug, name, kurzbeschreibung, schwerpunkt, rubriken, bild, bild_ki) on magazin_autoren to anon, authenticated;
create policy autoren_lesen on magazin_autoren for select to anon, authenticated using (aktiv);
create view magazin_oeffentlich with (security_invoker = true) as
  select id, slug, rubrik, autor_slug, titel, seo_titel, teaser, inhalt_md, kurzfassung, faq, hero_bild, hero_alt, hero_nachweis,
         hero_ki, veroeffentlicht_am, aktualisiert_am, korrektur_hinweis, gueltig_von, gueltig_bis, event_ids, ort_slugs, quellen
  from magazin_beitraege;
grant select on magazin_oeffentlich to anon, authenticated;
-- Hero-Pfad (Prüfung 2, Befund 1): ungeschützte | als Oder; das Fremdfoto als eigenes Verbot
alter table magazin_beitraege add constraint magazin_hero_pfad check (
  hero_bild is null or (
    hero_bild ~ '^/(magazin-bilder/[a-z0-9-]+|fallback|ort-bilder/weihnachtsmaerkte)/[a-z0-9-]+\.(webp|jpg|png)$'
    and hero_bild <> '/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp'
  )
);
```

- Die **Mindesthöhe** (nur 84 von 151 Fallback-Bildern, ≥ 675 px) ist nicht Teil des Musters.
  - Sie steht als feste Liste `ERLAUBTE_FALLBACK_HEROS` in `web/lib/magazin-bilder.ts`, erzeugt einmalig mit `sharp` und per Test gegen die Dateien geprüft.
  - Die Pipeline prüft sie vor dem Speichern (Prüfung 4.2 i). Die Vorschau zeigt einen Verstoß rot; ohne grüne Prüfung lässt der Trigger keine Veröffentlichung zu.
  - Ändert jemand das Bild nach der Veröffentlichung im Table Editor, erlaubt der CHECK auch ein zu flaches Fallback-Bild; die grüne Prüfung lief nur beim Wechsel auf `veroeffentlicht`.
  - Deshalb prüft **die Website selbst beim Rendern** (Cursor-Prüfung 3, Befund 3): Ist `hero_bild` ein `/fallback/`-Pfad, der nicht in `ERLAUBTE_FALLBACK_HEROS` steht, nutzt die Seite das **Rubrik-Ersatzbild**.
    - Das Ersatzbild gilt für `<img>`, `og:image`/Twitter und alle drei JSON-LD-Zuschnitte gleich (eine Funktion `heroFuer(beitrag)` in `web/lib/magazin-bilder.ts`).
    - Bildnachweis „Symbolbild (KI-generiert)“.
    - Der tägliche Prüflauf meldet den Fall zusätzlich im Log.
  - **Rubrik-Ersatzbilder** (alle aus `ERLAUBTE_FALLBACK_HEROS`, Vorschlag; der Auftraggeber sieht sie sich in Schritt 2 an und kann tauschen):

    | Rubrik | Datei | Maße |
    |---|---|---|
    | `wochenvorschau` | `/fallback/theater-1.webp` | 1200×805 |
    | `monats-tipps` | `/fallback/theater-2.webp` | 1200×805 |
    | `saison` | `/fallback/theater-3.webp` | 1200×805 |
    | `stadtleben` | `/fallback/sprachcafe-1.webp` | 1200×805 |

- Die View läuft mit den Rechten der aufrufenden Rolle und greift damit die Policy.
- `ki_entwurf`, `pruefung`, `vorschau_hash`, `freigegeben_von`, `status` und `alte_slugs` sind für `anon` nicht lesbar.
- **Welcher Schlüssel liest was (Prüfung 2, Befund 2):**
  - Der bestehende Proxy liest mit `SUPABASE_KEY` (anon, `web/lib/pfad-pruefung.ts:86–87`). Damit sieht er weder `vorschau_hash` noch `status` noch `alte_slugs`: Vorschau wäre immer 404, alte Slugs 404 statt 308.
  - Die Magazin-Prüfungen im Proxy lesen deshalb mit **`SUPABASE_SERVICE_KEY`**. Das ist derselbe Schlüssel wie `dienstClient()` (`web/lib/supabase-server.ts:26–32`), nur serverseitig; `service_role` umgeht die RLS.
  - Eigene Abfragefunktion `dienstAbfrage()` in `pfad-pruefung.ts`. Abgefragt werden nur `id`, `slug`, `status`, `veroeffentlicht_am`, `alte_slugs`, `vorschau_hash`.
  - Ergebnis des Proxys ist nie Inhalt, nur `weiter`/404/308.
  - Die Seiten selbst (Beitrag, Listen, Feed, Sitemap) lesen weiter mit dem anon-Schlüssel über `magazin_oeffentlich`. Nur die Vorschau-Seite (5.3) liest mit dem Service-Schlüssel.

**Trigger `magazin_status_pruefen` (before insert/update):**
- Wechsel auf `veroeffentlicht` nur, wenn alle Bedingungen erfüllt sind:
  - `current_user` ist nicht `service_role`, `anon` oder `authenticated` (Pipeline und Website dürfen nicht veröffentlichen, T5);
  - vorher `in_pruefung`;
  - `veroeffentlicht_am`, `freigegeben_von`, `hero_bild`, `hero_alt`, `hero_nachweis` gesetzt;
  - `pruefung->>'ergebnis' = 'gruen'`.
  - Sonst Fehler mit deutscher Meldung.
- Die Trigger-Funktion bleibt `SECURITY INVOKER`, sonst wäre `current_user` immer der Eigentümer. Die Pipeline schreibt über PostgREST mit `service_role` und wird abgewiesen; der Table Editor schreibt als `postgres` (Prüfung 2 bestätigt). In Schritt 1 trotzdem nachprüfen. Test: im SQL-Editor `select current_user`, dann eine Statusänderung im Table Editor und eine per Service-Schlüssel (muss scheitern).
- `freigegeben_am` = now() beim Wechsel; `vorschau_hash` = null.
- `hero_ki` = true, wenn `hero_bild` mit `/fallback/` beginnt.
- Geänderter `slug` bei veröffentlichtem Beitrag → alter Slug nach `alte_slugs`.
- **Auslegung bei der Umsetzung (Schritt 1, 19.11.):** Ein veröffentlichter Beitrag darf über `service_role`, `anon` und `authenticated` nur noch in `pruefung` und `gemeldet_am` geändert werden (täglicher Prüflauf, IndexNow). Text, Bild, Status usw. ändert nur der Auftraggeber (Fehler `magazin_veroeffentlicht_gesperrt`). Grund: T5, sonst könnte die Pipeline einen freigegebenen Text nachträglich überschreiben.
- **Ebenfalls Schritt 1:** Slugs und alte Slugs sind über alle Beiträge eindeutig (Fehler `magazin_slug_belegt`), damit die 308 im Proxy nie mehrdeutig ist.

**Indizes:** `(status, veroeffentlicht_am desc)`, `(rubrik, veroeffentlicht_am desc)`, GIN auf `alte_slugs` und `event_ids`.

### 3.2 Gegenrechnung Repo-Dateien

| | Supabase (T1) | Repo-Dateien |
|---|---|---|
| Freigabe ohne Deploy | ja | nein, jede Ausgabe ein Push mit OK |
| Versionsgeschichte | über `ki_entwurf` + manuell | git |
| Entwurf durch Pipeline | direkt | Pipeline müsste committen |
| „Nur Auftraggeber veröffentlicht“ technisch erzwingbar | ja (Trigger) | nur über Deploy-OK |
| Risiko | Rechtefehler → Entwürfe sichtbar (Test 7.3) | keins |

---

## 4. Wie Beiträge entstehen

### 4.1 Rollen

| Rolle | Wer | Aufgabe |
|---|---|---|
| Datenauswahl | Code (deterministisch) | Kandidaten nach festen Regeln. Die KI wählt keine Events aus |
| Ressort-Agent (Entwurf) | Claude Opus 5.5 mit dem Schreibprofil des Pseudonyms (T7) | Text, Gliederung, Kurzfassung, Titelvorschläge **nur** aus unseren Daten |
| Recherche (Saison/Stadtleben) | Claude-Code-Session mit dem Auftraggeber (wie bei den Guide-Texten) | Fakten mit Quellen in die Datenbasis. Eine automatische Web-Recherche ist **nicht** Teil von Stufe 1, das wäre eigener Kostenpunkt |
| Prüfung | Code | 4.2 Schritt 3 |
| Redaktion / Freigabe | Auftraggeber (verantwortlich, § 18 Abs. 2 MStV) | lesen, korrigieren, Bild wählen, **veröffentlichen** (nur er, T5) |
| Technik | Claude Code (Session) | Vorlagen, Profile, Prompts, Fehler |

### 4.2 Ablauf je Beitrag (laufende Rubriken)
1. **Datenauswahl** (Code, TypeScript über die interne Route aus T11):
   - **Zeitraum der Ausgabe:** `gueltig_von`/`gueltig_bis`, nie „heute + n Tage“.
     - Wochenvorschau: Montag bis Sonntag der Zielwoche, z. B. Entwurf am Fr 27.11. → 30.11.–06.12.
     - Monats-Tipps: 1. bis letzter Tag des Zielmonats, z. B. 01.12.–31.12.
   - **Warum (Cursor-Prüfung 3, Befund 1):** `highlights()` rechnet mit `pool.heute` + 6 bzw. + 29 Tagen (`web/lib/ableitungen.ts:362–363`).
     - Am Fr 27.11. sähe es den 27.11.–03.12.: Das „Highlight der Woche“ könnte am 28./29.11. liegen und fehlte in der Vorschau, der 04.–06.12. fehlte ganz.
     - Selbst mit `heute` = 01.12. endet das Monatsfenster am 30.12. und verliert Silvester.
   - **Umsetzung (Cursor-Prüfungen 4 und 5):** `highlights()` bleibt **unverändert** (eigener Kontext mit dem echten `heute`, Wochen- und Monatsfenster, `ohneStamm` vor der Auswahl, Ausschluss der Highlight-ID beim Top, `ableitungen.ts:357–381`).
     - Neu ist nur, dass die bisher innere Regelkette `waehle` (`:364–377`) als Funktion `waehleEvent(liste, flagge, k, ohne?)` herausgezogen wird.
       - **In der Hilfe** (Cursor-Prüfung 6, Befund 1): Die Flagge läuft mit dem Tag des Kontexts, also `flagge(e, k.heute)`. `highlightGilt` und `topGilt` erwarten den Tag als zweites Argument (`:571`, `:580`); ohne ihn wird `tageZwischen` zu `NaN`, und die Flagge gilt nie.
       - Der Vergleich ist `nachEmpfehlung(k)` (`:647`), kein eigener Parameter. `k` trägt `heute`, Serien und Stufen und wird auch von `breite` gelesen.
       - `highlights()` ruft sie genau wie heute auf: `ohneStamm` → `waehleEvent(woche, highlightGilt, k)` → `waehleEvent(monat, topGilt, k, highlight?.id)`.
       - Ein Test „dieselben Daten, dasselbe Ergebnis“ sichert das.
     - **`highlightsImZeitraum(pool, { von, bis }, art)`** mit `art` = `"highlight"` (Wochenvorschau) oder `"top"` (Monats-Tipps) liefert **ein** Event oder `null`. Ablauf:
       - Pool aus der eigenen Lade-Funktion (siehe unten), `heute = von`;
       - `stufenKontext(pool, von)`, Kandidaten per `filtern(…, { von, bis, mitLanglaeufern: true })`, dann `ohneStamm`;
       - `waehleEvent(kandidaten, art === "highlight" ? highlightGilt : topGilt, k)` – **ohne Ausschluss einer Highlight-ID** (Cursor-Prüfung 5, Befund 1).
       - Grund: Sonst würde im Monatslauf das beste Event des Monats als „Highlight“ verbraucht und „Top-Event des Monats“ wäre nur der Zweite. Der Ausschluss gehört nur in `highlights()`, wo Wochen- und Monatsfenster verschieden sind und beide Plätze nebeneinander auf der Startseite stehen.
     - **Eigene Lade-Funktion `magazinPoolLaden(von, bis)`** in `web/lib/daten.ts` (Cursor-Prüfung 5, Befund 2). `eventPoolLaden()` bleibt unverändert (Quelle der Startseite, `"use cache"`, ohne Argument ab heute, `TAGE_VORAUS` = 60 Tage, `daten.ts:108–122`).
       - Gleiche Abfrage wie `eventPoolLaden()` (nicht abgelehnt, `datum >= von` oder `datum_bis >= von`), aber mit `von` statt des echten heutigen Tags. Ende ist **`max(bis, von + 60 Tage)`**.
       - **Gleiche Verarbeitung wie die Startseite** (Cursor-Prüfung 6, Befund 2): dieselbe Seitenschleife, dieselben `SPALTEN_VARIANTEN`, `normalisieren` und danach **`buendeln(alle)`** (`daten.ts:108–136`, `:225`).
         - Ohne `buendeln` würden mehrere Uhrzeiten desselben Tages nicht zu einem Eintrag. Eine Highlight- oder Top-Flagge an nur einer Uhrzeit gälte dann nicht für den Eintrag, während die Startseite am `von` sie sieht.
       - Kein `"use cache"` nötig (Route `no-store`, seltene Läufe). Den Cache-Eintrag von `eventPoolLaden` (`:218`) berührt die Funktion nicht.
       - **Fehler:** Schlägt die Abfrage fehl, **wirft** `magazinPoolLaden`. Die Route antwortet dann mit einem Fehlerstatus, und der Job bricht nach T11 ab.
         - Die Beispieldaten aus dem `catch` von `eventPoolLaden` (`:226–230`) dürfen nie in einen Entwurf gelangen.
       - So sieht der Pool genau aus wie der der Startseite am `von`. Events, die am `von` nicht mehr laufen (z. B. Termine vom 27.–29.11.), sind gar nicht erst drin und können über `serienErkennen` (`:528`, `:561`) nichts deckeln. Spätere Serientermine (z. B. 04., 08., 11.12.) sind drin und deckeln wie auf der Startseite.
       - Läufe, die am `von` noch gehen (`datum_bis >= von`), bleiben, wie bei `findetStatt` (`datum.ts:186–189`).
       - Die Kandidaten schneidet weiter `filtern` auf `von`/`bis`.
     - Flaggen: `highlightGilt` gilt sieben Tage ab Setz-Tag, `topGilt` nur im Kalendermonat von `heute`. Mit `heute = von` entspricht das der Startseite am Montag der Zielwoche bzw. am 1. des Monats. Eine November-Top-Flagge zählt im Dezember nicht; die Auswahl fällt dann auf „Stufe 3 mit Bild“, wie ohne Flagge (Prüfung 4 bestätigt).
   - **Wochenvorschau:** Events im Zeitraum, nicht abgesagt, Auswahl über `stufenKontext`/`breite`/`beliebtAuswahl`, 12–20 Kandidaten.
     - `wochenendProgramm` wird nicht genutzt (nur Fr–So).
     - Mindestens 4 Kategorien, höchstens 3 je Ort, Mehrtages-Events einmal.
     - „Highlight der Woche“ = `highlightsImZeitraum(…, "highlight")`.
   - **Monats-Tipps:** „Top-Event des Monats“ = `highlightsImZeitraum(…, "top")` (bestes Event des ganzen Monats nach der Top-Regel), dazu die stärksten Events je Kalenderwoche des Monats (ohne das Top-Event), 10–15 Einträge, Saison-Guides als Kasten.
   - Die Auswahl wird mit Event-IDs gespeichert.
2. **Entwurf durch den Ressort-Agenten:**
   - Eingabe je Event: Titel, Datum, Uhrzeit, Ort, Stadtteil, Kategorie, Preis, `beschreibung`, interner Pfad. Dazu das Schreibprofil (T7), die Stilregeln (6) und die Rubrik-Vorlage.
   - Ausgabe als strukturiertes JSON (`output_config.format`): `titel_vorschlaege[3]`, `teaser`, `kurzfassung[]`, `abschnitte[{ueberschrift, text_md, event_ids[]}]`, `faq[]`.
   - Einbettungen nur über IDs aus der Auswahl.
   - **Verboten:**
     - nicht belegte Angaben;
     - Uhrzeiten, Daten, Preise und „ausverkauft“/„restlos“ im Fließtext;
     - Superlative ohne Begründung;
     - Google-Bewertungen;
     - Ich-Erlebnisse des Pseudonyms (2.3).
   - Modell `claude-opus-5-5`, adaptives Denken, `effort: medium`. Kosten aus `usage` in `ki_entwurf`.
3. **Automatische Prüfungen** (Code, Ergebnis `pruefung.ergebnis` = `gruen`/`rot` + Liste):
   - (a) Alle `event_ids` existieren, liegen im Zeitraum, sind nicht abgesagt.
   - (b) **Uhrzeiten:** nirgends im Text (`\d{1,2}[.:]\d{2}` und „Uhr“ als ganzes Wort, `\bUhr\b`).
     - **Preise:** nirgends (`€`, `\bEuro\b`, `\bEUR\b`, „kostenlos“, „Eintritt frei“); ganze Wörter, damit „Europa“ nicht anschlägt.
     - **„ausverkauft“/„restlos“:** nirgends.
     - **Datumsangaben** (Tag + Monatsname, `\d{1,2}\.\d{1,2}\.`) sind im Fließtext verboten. Im **Titel, Teaser, in Überschriften und in der Kurzfassung** sind sie erlaubt, wenn **jedes genannte Datum zwischen `gueltig_von` und `gueltig_bis` liegt** (Prüfung 2, Befund 3). Damit geht „Montag, 30. November“ als Tagesüberschrift der Wochenvorschau ebenso durch wie der Saisonzeitraum in „Auf einen Blick“.
     - Ohne `gueltig_von`/`gueltig_bis` (Stadtleben) sind Daten überall verboten.
   - (c) Alle internen Links lösen auf: bekannte Seiten, `routeVon`, Datenbank. Externe Links nur `https://`.
   - (d) Längen: Titel, Teaser, Text 600–1800 Wörter je Rubrik.
   - (e) Verbotsliste Clickbait („unglaublich“, „du wirst nicht glauben“, „Geheimtipp, den keiner kennt“ …) und Ich-Formen des Pseudonyms („ich war“, „mein Lieblings…“).
   - (f) Keine Google-Inhalte.
   - (g) Gleiche Rubrik und gleicher Zeitraum schon vorhanden → Abbruch.
   - (h) Titel beginnt nicht mit einem Hub-Kopfbegriff (E5): „Weihnachtsmärkte in Düsseldorf“, „Clubs in Düsseldorf“, „Restaurants & Cafés“, „Kneipen & Bars“, „Spielplätze in Düsseldorf“.
   - (i) `hero_bild` erfüllt den Constraint und ist bei `/fallback/` in `ERLAUBTE_FALLBACK_HEROS` (≥ 675 px Höhe).
4. **Status:** grün → `in_pruefung`, rot → bleibt `entwurf` (Prüfliste in der Vorschau).
   - Je Entwurf ein Zufallsschlüssel (32 Byte); gespeichert wird nur der Hash (`vorschau_hash`).
   - Der Vorschau-Link mit Schlüssel steht im Lauf-Log der Action. Mail über den eigenen Mailserver erst in Stufe 2.
5. **Redaktion:**
   - Der Auftraggeber liest die Vorschau, wählt einen Titel und das Hero-Bild und korrigiert.
   - Eigene Erfahrung ergänzt er als „aus der Redaktion“ (2.3).
   - Er setzt `veroeffentlicht_am`, `freigegeben_von` und `status = 'veroeffentlicht'` im Table Editor (E3). Der Trigger erzwingt die Pflichtfelder.
6. **Veröffentlichung:**
   - Ab `veroeffentlicht_am` sichtbar, normal nach ca. 1–5 min (T10).
   - Der stündliche Job meldet per IndexNow und setzt `gemeldet_am`. Sitemap und Feed lesen live.
7. **Nachlauf:** täglicher Prüflauf (5.12).

**Saison/Stadtleben:**
- Gliederung gemeinsam in einer Claude-Code-Session. Datenbasis sind Guide-Stammdaten und Notizen mit Quellen.
- Der Ressort-Agent schreibt in Abschnitten, danach eine längere Redaktion.
- Quellen stehen sichtbar unter dem Beitrag.
- Echte Erfahrung des Auftraggebers als „aus der Redaktion“ ist ausdrücklich erwünscht. Sie ist das stärkste Mehrwert-Signal.

### 4.3 Häufigkeit und Aufwand (E8)

| Rubrik | Frequenz | Entwurf | Aufwand Auftraggeber |
|---|---|---|---|
| Wochenvorschau | wöchentlich (So 8 Uhr) | Fr 18 Uhr automatisch | 15–25 min |
| Monats-Tipps | monatlich (letzter Tag des Vormonats) | 3 Tage vorher | 20–30 min |
| Saison/Anlass (Weihnachtsmärkte, Silvester, Karneval, Japan-Tag, Größte Kirmes am Rhein, Open-Air-Sommer) | 1–2 pro Monat | in Session | 45–90 min |
| Stadtleben (Feiern, Brauhäuser, Stadtteil-Porträts, Regentage mit Kindern) | ca. 1 pro Monat | in Session | 1–2 h |

### 4.4 Kosten (Preise laut Anthropic, Stand 03.11.2026, US-Dollar)

Modell **Claude Opus 5.5** (`claude-opus-5-5`, $4 / $20 je 1 Mio. Tokens), entschieden am 19.11.

| Beitrag | Eingabe (geschätzt) | Ausgabe inkl. Denken (geschätzt) | Kosten |
|---|---|---|---|
| Wochenvorschau (15 Events) | ~15 000 Tokens | ~8 000 Tokens | ~$0,22 |
| Monats-Tipps (25 Kandidaten) | ~22 000 | ~10 000 | ~$0,29 |
| Saison/Stadtleben (3 Teil-Entwürfe + 1 Überarbeitung) | ~80 000 gesamt | ~35 000 gesamt | ~$1,02 |

- **Monat:** 4,3 Wochenvorschauen + 1 Monats-Tipps + 2 Saison/Stadtleben ≈ **$3,25**.
- **Deckel $10/Monat** (Befund 14):
  - Der Job liest vor jedem Aufruf die **Kostensumme des laufenden Kalendermonats aus der Datenbank** (`magazin_ki_kosten`, siehe unten), nicht aus einem Zähler im Prozess.
  - Er bricht ab, wenn Summe + geschätzter Aufruf > $10.
  - Denk-Tokens können die Schätzung übersteigen; der Deckel fängt das auf.
  - **Gleichzeitige Läufe (Prüfung 2, Befund 7):** Die Action hat `concurrency: magazin` (T6). Zusätzlich führt der Job eine eigene Kostentabelle `magazin_ki_kosten` (3.1).
    - Vor jedem Aufruf schreibt er eine **Reservierung** (Schätzung) und ersetzt sie danach durch die gemessenen Kosten; bei Abbruch bleibt die Schätzung stehen.
    - Der Deckel summiert **diese Tabelle** im laufenden Kalendermonat, nicht `ki_entwurf`. So zählen auch Läufe ohne gespeicherten Entwurf, und ein zweiter, gleichzeitiger Lauf (z. B. von Hand) sieht die Reservierung.
    - Ein Restfenster von Millisekunden zwischen Lesen und Schreiben bleibt; höchstens ein Aufruf (~$0,22) kann den Deckel überschreiten. Das ist hingenommen.
- **Profilbilder** (einmalig, 3 Pseudonyme, illustriert): mit DALL-E 3 laut OpenAI-Preisliste ca. $0,04–0,08 je Bild. Bei 2–3 Versuchen je Profil höchstens ca. $1 gesamt. Preis vor dem Lauf prüfen und nennen. Alternativ liefert der Auftraggeber die Bilder.
- **Hero-Bilder:** eigene und Symbolbilder ohne Kosten. **Google:** keine Kosten.
- Vor dem ersten echten Lauf werden die Kosten erneut genannt. Gemessen wird mit `messages.count_tokens` und `usage`.

---

## 5. Website

### 5.1 URLs und Proxy

| URL | Inhalt | Index (Schalter an) |
|---|---|---|
| `/magazin` | Übersicht: neuester Beitrag groß, dann chronologisch (30), Rubrik-Links | ja |
| `/magazin/rubrik/[rubrik]` | `wochenvorschau`, `monats-tipps`, `saison`, `stadtleben` | ja |
| `/magazin/[slug]` | Beitrag | ja (Archiv E12) |
| `/magazin/autor/[slug]` | Autorenseite (2.3) | ja |
| `/magazin/redaktion` | „Unsere Redaktion“ (2.3) | ja |
| `/magazin/feed.xml` | RSS 2.0 (5.6) | – |
| `/magazin/vorschau/[id]?s=…` | Entwurfs-Vorschau (5.3) | nein |
| `/feed.xml` | 308 → `/magazin/feed.xml` | – |

**Slugs:**
- Wochenvorschau: `events-duesseldorf-30-november-bis-6-dezember-2026`
- Monats-Tipps: `top-events-duesseldorf-dezember-2026`
- Saison und Stadtleben ohne Jahreszahl, z. B. `welcher-weihnachtsmarkt-passt-zu-euch`. Die Jahreszahl steht im Titel.

**Proxy (Befund 2):**
- `matcher` in `web/proxy.ts` um `"/magazin/:path*"` und `"/feed.xml"` ergänzen. `:path*` erfasst null oder mehr Segmente, also auch `/magazin` selbst; `routeVon("/magazin")` → `magazin-fest` → `weiter`.
- `routeVon` erkennt (rein, ohne Netz):
  - `/feed.xml` → Typ `feed-alt`;
  - `/magazin`, `/magazin/feed.xml`, `/magazin/redaktion` → Typ `magazin-fest`;
  - `/magazin/rubrik/[r]` → `magazin-rubrik`;
  - `/magazin/autor/[s]` → `magazin-autor`;
  - `/magazin/vorschau/[id]` → `magazin-vorschau`;
  - `/magazin/[slug]` → `magazin-beitrag`;
  - **vier oder mehr Pfadteile** (z. B. `/magazin/autor/x/y`) oder drei Pfadteile mit anderem zweiten Teil als `rubrik`/`autor`/`vorschau` (z. B. `/magazin/x/y`) → `ungueltig` → 404.
- `pfadPruefen` entscheidet:

| Typ | Entscheidung |
|---|---|
| `feed-alt` | `umleiten` → `/magazin/feed.xml` (308) |
| `magazin-fest` | `weiter`. Die Route selbst antwortet. Der Feed ist ein Route-Handler mit echtem Status, z. B. 404 bei Schalter aus |
| `magazin-rubrik` | Rubrik in der festen Liste → `weiter`, sonst `fehlt` |
| `magazin-autor` | aktiver Autor in `magazin_autoren` → `weiter`, sonst `fehlt` |
| `magazin-vorschau` | `id` ist UUID **und** `s` gesetzt **und** SHA-256(`s`) = `vorschau_hash` (zeitkonstanter Vergleich) **und** Status `entwurf`/`in_pruefung` → `weiter`, sonst `fehlt` (5.3) |
| `magazin-beitrag` | sichtbarer Beitrag → `weiter`; Slug in `alte_slugs` eines sichtbaren Beitrags → `umleiten` (308); sonst `fehlt` (auch `zurueckgezogen` und Zukunft) |

- Proxy-Antwort bei `fehlt`: das vorhandene statische `NICHT_GEFUNDEN_HTML`, Status 404, `Cache-Control: no-store`. Kein `rewrite`.
- Zwischenspeicher für Magazin-Abfragen: Treffer 5 min, Fehltreffer 60 s (T10). Vorschau-Prüfungen werden **nicht** gemerkt.
- Alle Magazin-Abfragen des Proxys laufen über `dienstAbfrage()` mit `SUPABASE_SERVICE_KEY` (3.1, Prüfung 2, Befund 2). Sichtbar heißt dabei ausdrücklich `status = 'veroeffentlicht' AND veroeffentlicht_am <= now()`, weil der Service-Schlüssel die Policy nicht anwendet. Fehlt der Service-Schlüssel, gilt der Grundsatz „Fehler → weiter“ für Beiträge und „Fehler → 404“ für die Vorschau.
- Grundsatz aus `pfad-pruefung.ts` bleibt: Abfragefehler → `weiter`, nie fälschlich 404. Ausnahme Vorschau: Abfragefehler → `fehlt`. Ein Entwurf darf bei einem Fehler nie ausgeliefert werden.
- Paginierung erst ab > 30 Beiträgen je Liste (`/magazin/seite/2`, eigener Typ und eigene Prüfung).

### 5.2 Seitenaufbau Beitrag
1. Brotkrumen: Start › Magazin › Rubrik (sichtbar und `BreadcrumbList`).
2. Rubrik-Label, **H1**, Teaser.
3. Zeile mit Autorenhinweis:
   - kleines Profilbild + „von [Pseudonym] (redaktionelles Pseudonym) · Redaktion dies.das.düsseldorf“ (Link auf die Autorenseite);
   - „Veröffentlicht am …“, „Aktualisiert am …“ (nur mit `aktualisiert_am`), Lesezeit.
4. **Hero:**
   - 16:9, ≥ 1200×675, `<img>` mit `width`/`height`, `fetchpriority="high"`, Alt-Text.
   - Darunter Bildnachweis. Bei `hero_ki` die Zeile „Symbolbild (KI-generiert)“.
5. Box **„Auf einen Blick“** (`kurzfassung`).
6. **Inhaltsverzeichnis** ab drei `##`-Überschriften.
7. **Fließtext** mit Einbettungen:
   - `{{event:uuid}}` → bestehende Event-Karte aus `karten.tsx`, live. Bild nach heutiger Regel, Symbolbild-Hinweis wie bisher.
   - `{{ort:slug}}` → **eigene schmale Karte `MagazinOrtKarte`**: Name, Typ, Stadtteil, Link auf die Ortsseite. **Ohne Foto, ohne Bewertung.** `OrtKarte` und `GuideKarte` werden im Magazin nicht verwendet (Befund 7).
   - `{{guide:slug}}` → Guide-Kasten mit Link (Text aus `guide-texte.ts`, ohne Karte).
   - `{{tag:YYYY-MM-DD}}` → Link-Kasten „Alles am …“.
8. Optional **FAQ** (sichtbar; `FAQPage`-Markup nur, wenn keine Guide-FAQ gedoppelt wird).
9. **Quellen** mit Abrufdatum.
10. Bei `korrektur_hinweis`: Kasten „Korrektur vom …“.
11. **Hinweis am Ende** (E4/E4a): „Mit KI-Unterstützung aus unseren [Eventdaten | Ortsdaten | Event- und Ortsdaten] erstellt, von der Redaktion geprüft und freigegeben. Redaktionell verantwortlich: Yannick Fetsch.“
    - Die Datenart kommt automatisch aus den Einbettungen (`event_ids`/`ort_slugs`).
    - Mit Link auf „Unsere Redaktion“.
12. **Weiterlesen:** 3 Beiträge + passender Guide.
13. Abgelaufene Ausgabe (E12): Hinweisbox oben „Diese Vorschau ist vorbei → aktuelle Ausgabe“.

Alles serverseitig in der ersten HTML-Antwort. Lesebreite ~68 Zeichen; Bestandsstile aus `globals.css`.

### 5.3 Entwurfs-Vorschau (Befund 1)
- **Zugang wird im Proxy entschieden** (5.1, Typ `magazin-vorschau`). Ohne oder mit falschem Schlüssel kommt eine echte 404 aus dem Proxy, bevor irgendetwas rendert. So kann kein Entwurfstext im HTML einer 200-Antwort landen.
- **Schlüssel:**
  - je Entwurf ein Zufallswert, gespeichert nur als SHA-256 (`vorschau_hash`), Vergleich zeitkonstant (`crypto.timingSafeEqual` auf gleich langen Hashes);
  - wird bei `veroeffentlicht` geleert. Ein geleakter Link öffnet also nur einen einzelnen, noch nicht veröffentlichten Entwurf.
  - Kein globaler Schlüssel in `.env`.
- **Leck-Wege:**
  - Antwort mit `Referrer-Policy: no-referrer` (Links im Entwurf geben den Schlüssel nicht weiter).
  - Query-Parameter landen im nginx-Zugriffslog des eigenen Servers. Hingenommen: Server und Log gehören dem Auftraggeber; Schlüssel je Entwurf, kurzlebig.
- **Seite** `web/app/magazin/vorschau/[id]/page.tsx`:
  - liest `searchParams` und prüft den Hash **zusätzlich** serverseitig (zweite Sicherung). Bei Fehlschlag wird nichts vom Entwurf gerendert.
  - kein `"use cache"`, `robots: { index: false, follow: false }`, `Cache-Control: private, no-store`, nicht in Sitemap und Feed.
  - Liest mit `SUPABASE_SERVICE_KEY` über `dienstClient()` (nur serverseitig), weil Entwürfe für anon unsichtbar sind.

### 5.4 Strukturierte Daten
`Article` (`web/lib/magazin-json-ld.ts`):
- `headline` ≤ 110, `description`;
- `image` [16:9, 4:3, 1:1] (5.11), immer aus `heroFuer(beitrag)` (gespeichertes Hero oder Rubrik-Ersatzbild, 3.1);
- `datePublished`/`dateModified` mit Zeitzone Europe/Berlin;
- `author`: `{ "@type": "Organization", "@id": "…/magazin/redaktion#redaktion", "name": "Redaktion dies.das.düsseldorf", "url": "…/magazin/redaktion" }`;
- **kein** `contributor` und keine andere Angabe zum Pseudonym. Das Pseudonym steht nur sichtbar (2.3 Punkt 6, Prüfung 2, Befund 4);
- `accountablePerson`: `{ "@type": "Person", "name": "Yannick Fetsch", "url": "…/impressum" }`;
- `publisher`: `{ "@id": "…/#organisation" }`;
- `mainEntityOfPage`, `inLanguage` `de-DE`, `isAccessibleForFree` true, `articleSection`.
- `mentions`: `[{ "@id": Event-URL }]` (Event-`@id` vorhanden, `json-ld.ts:57`). **Kein** `Event`-Markup im Beitrag.

Weitere Seiten:
- `BreadcrumbList`; `FAQPage` nach 5.2 Punkt 8.
- Autorenseite: `WebPage` + `BreadcrumbList`, `about` → `#redaktion`. Kein `ProfilePage`, keine `Person` (2.3).
- „Unsere Redaktion“: `AboutPage` mit `mainEntity` `Organization` `#redaktion` (`parentOrganization` → `#organisation`).
- `Organization` (`seo.ts:20`) bekommt `publishingPrinciples` → `/magazin/redaktion`.

### 5.5 Metadaten
- `seitenMetadaten()` bekommt optional `artikel: { veroeffentlicht, aktualisiert, rubrik }`. Ohne `artikel` ändert sich nichts. Mit `artikel` setzt sie **zwei** Felder (Cursor-Prüfung 3, Befund 4):
  - `openGraph.type: "article"` mit `publishedTime`, `modifiedTime`, `section` und `openGraph.authors: ["Redaktion dies.das.düsseldorf"]`. Das erzeugt die Zeile `article:author`.
  - das Seiten-Metadatenfeld `authors: [{ name: "Redaktion dies.das.düsseldorf", url: "/magazin/redaktion" }]`. Das erzeugt `<meta name="author">` (und `<link rel="author">`).
  - Beides ist die Redaktion, nie das Pseudonym (2.3 Punkt 7).
- **`robots`:**
  - Beiträge setzen kein eigenes `robots` → `ROBOTS_INDEX` aus dem Layout (`max-image-preview:large`).
  - Abgelaufen (E12) und Schalter aus (T9) → `{ index: false, follow: true }`.
  - Vorschau → `{ index: false, follow: false }`.
- `og:image` = `heroFuer(beitrag)` (gespeichertes Hero oder Rubrik-Ersatzbild, 3.1) 16:9 mit Alt-Text. Twitter `summary_large_image`.

### 5.6 Feed (RSS 2.0)
- Route-Handler `web/app/magazin/feed.xml/route.ts`:
  - die 20 neuesten sichtbaren, nicht archivierten Beiträge;
  - bei Schalter aus 404 (echter Status, Route-Handler streamt nicht).
- **Wurzelelement mit Namensräumen** (Befund 13): `<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:media="http://search.yahoo.com/mrss/">`.
- Kanal: `title` „dies.das.düsseldorf – Magazin“, `link`, `description`, `language` `de-DE`, `atom:link rel="self"`.
- Items: `title`, `link`, `guid isPermaLink="true"`, `pubDate` (RFC 822), `description` (Teaser), `dc:creator` = Pseudonym, `media:content` (`heroFuer(beitrag)`, 1200 px, `medium="image"`; Cursor-Prüfung 4, Befund 4).
- Alles XML-escaped. `Content-Type: application/rss+xml; charset=utf-8`. Cache wie T10.
- **Feed-Link im `<head>` aller indexierbaren Seiten (Befund 5):**
  - Neue Hilfe `seitenAlternates(canonical?: string)` in `web/lib/seo.ts` liefert `{ canonical, types: { "application/rss+xml": [{ url: "/magazin/feed.xml", title: "dies.das.düsseldorf – Magazin" }] } }`. Bei Schalter aus kommen keine `types`.
  - `seitenMetadaten()` nutzt sie im indexierbaren Zweig; **im noindex-Zweig bleibt `alternates` undefiniert** (bestehender Test `seo-a1.test.ts:116`).
  - Die elf Seiten mit eigenem `alternates` (1.2) stellen auf `seitenAlternates(...)` um. Das Layout bekommt dieselben `types` für Seiten ohne eigenes `alternates`.

### 5.7 Sitemap
- Bei Schalter an: `/magazin`, Rubriken, Autorenseiten, `/magazin/redaktion` und alle sichtbaren, nicht archivierten Beiträge (`lastModified` = `aktualisiert_am ?? veroeffentlicht_am`, `images: [heroFuer(beitrag)]`; Cursor-Prüfung 4, Befund 4).
- Bei Schalter aus: keine Magazin-URL.
- Keine News-Sitemap (E13).

### 5.8 IndexNow und Google
- Job T6 meldet neue und inhaltlich geänderte Beiträge plus `/magazin` und Rubrik-Seite über `melden()`, **nur wenn der Feed mit 200 antwortet** (Schalter an, T6). Das erreicht Bing (davon profitieren Copilot und die ChatGPT-Suche), Yandex, Seznam und Naver.
- **Zurückgezogene Beiträge** werden ebenfalls gemeldet: Bing ruft sie erneut ab, bekommt 404, und die URL fällt heraus (Befund 13).
- Google: Sitemap; bei Saison- und Stadtleben-Beiträgen URL-Prüfung → „Indexierung beantragen“ von Hand. Die Indexing API ist nur für Jobs und Livestreams erlaubt, also nicht nutzen.

### 5.9 Einbaustellen (alle hinter `MAGAZIN_VERLINKT`)

| Stelle | Datei | Inhalt |
|---|---|---|
| Hauptmenü + Mobilmenü | `components/client.tsx`, `components/rahmen.tsx` | „Magazin“ (E10) |
| Footer | `components/rahmen.tsx` | „Magazin“, „Unsere Redaktion“, „Feed“ |
| Startseite | `app/page.tsx` | Box „Aus dem Magazin“ (E9) |
| `/wochenende` | `app/wochenende/page.tsx` | Kasten „Die ganze Woche“ → aktuelle Wochenvorschau |
| Guide-Hubs | `app/guides/*/page.tsx` | „Lesetipp aus dem Magazin“, wenn ein Beitrag den Guide einbettet |
| Event-Seiten | `app/event/[kategorie]/[slug]/page.tsx` | „Erwähnt im Magazin“ über `event_ids` (max. 2) |
| `/ueber` | `app/ueber/page.tsx` | Link auf „Unsere Redaktion“ |
| Impressum | `app/impressum/page.tsx` | § 18 Abs. 2 MStV, Hinweis auf Pseudonyme und Link „Unsere Redaktion“ |
| `public/llms.txt` | von Hand | „## Magazin“ mit `/magazin`, `/magazin/redaktion`, Feed |

### 5.10 Design
- Vorhandene Karten, Farben, Schriften (`globals.css`). Neue Klassen nur für Lesetypografie, „Auf einen Blick“, Inhaltsverzeichnis, Autorenzeile, Bildnachweis, Pseudonym-Kasten.
- Mobil zuerst. Feste Seitenverhältnisse ohne Layout-Sprung.

### 5.11 Bilder
- **Pflicht je Beitrag:**
  - Hero ≥ 1200 px, 16:9, Alt-Text, Nachweis;
  - keine erkennbaren Einzelpersonen ohne Einwilligung;
  - kein Text, kein Logo.
- **Quellen (E7):**
  - (1) eigene Fotos (`web/public/magazin-bilder/<slug>/…`, Deploy nötig; aus `web/public/ort-bilder/weihnachtsmaerkte/` die 13 eigenen Fotos, **nicht** `koe-on-ice.webp`);
  - (2) KI-Symbolbilder aus `web/public/fallback/`, **nur die 84 Motive mit ≥ 675 px Höhe**, immer mit Zeile „Symbolbild (KI-generiert)“ (`hero_ki`, Trigger);
  - (3) lizenzierte Fotos nach Rückfrage.
  - Verboten: Google-Fotos und Veranstalterbilder als Hero (bis A2).
- **Profilbilder** der Pseudonyme: illustriert, 1:1, mit Unterzeile „KI-generiertes Profilbild“.
- **Zuschnitte 16:9 / 4:3 / 1:1** für JSON-LD über die Route `web/app/magazin-bild/[...pfad]/route.ts` mit `sharp` (Befund 8):
  - jedes Segment gegen `^[a-z0-9-]+$` (letztes: `^[a-z0-9-]+\.(webp|jpg|png)$`) prüfen; Prozent-Kodierung vorher dekodieren, damit `%2e%2e` auffällt;
  - Seitenverhältnis nur aus fester Liste (`16x9`, `4x3`, `1x1`);
  - nach `path.resolve` muss der Pfad unter `public/fallback`, `public/magazin-bilder` oder `public/ort-bilder/weihnachtsmaerkte` liegen, sonst 404;
  - Ausgabe webp, Ausschnitt mittig, `Cache-Control: public, max-age=31536000, immutable`.
  - Die Route liegt außerhalb des Proxy-`matcher`; ungültige Pfade beantwortet sie selbst mit 404 (Route-Handler, echter Status).
- **Bestand außerhalb des Magazins:** Event-Karten auf der ganzen Website zeigen KI-Symbolbilder heute nur mit „Symbolbild“. Ob dort „KI-generiert“ ergänzt werden muss, gehört zu A1 und ist nicht Teil dieses Plans.

### 5.12 Veraltete Beiträge

| Typ | Regel |
|---|---|
| Wochenvorschau / Monats-Tipps | Nach `gueltig_bis`: Hinweisbox. Nach 30 Tagen noindex,follow, raus aus Sitemap/Feed. Seite bleibt (E12) |
| Saison | Gleiche URL jedes Jahr. Nach der Saison Box „Saison 2026 vorbei – Termine 2027 folgen“. Bleibt indexiert. Jährliche Überarbeitung (`naechste_pruefung`) |
| Stadtleben | `naechste_pruefung` = +6 Monate |
| Sachlicher Fehler | Korrektur + `aktualisiert_am` + `korrektur_hinweis` (sichtbar, § 19 MStV) |
| Zurückgezogen | `status = 'zurueckgezogen'` → 404 aus dem Proxy (nach Zwischenspeicher ≤ 5 min, Seiten-Cache ≤ 10 min, T10). 308 nur auf inhaltsgleichen Nachfolger (`alte_slugs` beim Nachfolger). Raus aus Sitemap/Feed, IndexNow-Meldung |
| Slug-Änderung | Trigger → `alte_slugs` → 308 |

- `dateModified` ändert sich nur bei inhaltlicher Änderung.
- **Täglicher Prüflauf:** abgesagte oder gelöschte Events in sichtbaren Beiträgen, tote interne Links, fällige `naechste_pruefung`, abgelaufene Ausgaben → `pruefung` + Log.

### 5.13 KI-Suchen (GEO)
- Antwort zuerst („Auf einen Blick“), Fragen als Überschriften, wo passend.
- Fakten in Karten, Quellen und Datum sichtbar, Verantwortung offen („Unsere Redaktion“).
- `llms.txt` ergänzen. `robots.txt` bleibt offen.

---

## 6. Texte und Stil (Vorgaben für Schreibprofile und Redaktion)
- **Ton:** Ansprache ihr/euch, locker, konkret, Düsseldorf-Kenntnis, keine Werbesprache. Jedes Schreibprofil (T7) variiert den Ton innerhalb dieser Regeln.
- **Titel:** 40–70 Zeichen, Ort und Zeitraum drin, **kein Clickbait**, beginnt nie mit dem Hub-Kopfbegriff (E5, Prüfung 4.2 h).
- **Teaser:** sagt, was drinsteht. Superlative nur mit Begründung. Keine öffentlichen Scores.
- **Pseudonyme** sprechen nicht über eigene Erlebnisse, Ausbildung oder Herkunft (2.3). Erfahrung des Auftraggebers als „aus der Redaktion“/„unser Tipp“.
- **Keine erfundenen Fakten** (Prompt + Prüfung 4.2).

**Gliederungen der ersten Beiträge (Entwurf, Titel nach E5):**

1. **„Welcher Weihnachtsmarkt passt zu euch? Unsere Tipps für Düsseldorf 2026“** (Saison, Ressort Stadtleben/Genuss/Familie)
   - Auf einen Blick: Saisonzeitraum, Totensonntag/Heiligabend.
   - Abschnitte „Für den Klassiker“, „Mit Kindern“, „Zum Schlittschuhlaufen“, „Abseits vom Trubel“, „Ausflug nach Neuss/Ratingen“, je 1–3 `{{ort:…}}`.
   - Kasten `{{guide:weihnachtsmaerkte}}` („Welche Märkte heute offen haben“). Kurz-Märkte als Events, FAQ (3).
   - Hero: eigenes Bild aus `public/ort-bilder/weihnachtsmaerkte/`.
   - Slug `welcher-weihnachtsmarkt-passt-zu-euch`.
2. **„Top-Events im Dezember 2026: Unsere Auswahl für Düsseldorf“** (Monats-Tipps, Ressort Events)
   - Top-Event des Monats, Abschnitte je Stimmung, 10–15 Event-Karten.
3. **„Was ist los in Düsseldorf? 30. November bis 6. Dezember 2026“** (Wochenvorschau, Ressort Events)
   - Highlight der Woche, Mo–So mit 2–3 Events je Tag, Kasten `/wochenende`, Kasten Weihnachtsmärkte.
4. **„Feiern in Düsseldorf: Welcher Club an welchem Abend?“** (Stadtleben, Ressort Nachtleben, Januar)
   - Nach Wochentag und Musikrichtung, `{{ort:…}}` (schmale Karte), Link `/guides/clubs`, keine Club-Score-Zahlen.

---

## 7. Tests

### 7.1 Automatisch (Vitest, `web/tests/magazin.test.ts`)

**Renderer (Befund 6):**
- Überschriften, Listen, Links, alle vier Einbettungen.
- `//beispiel.de`, `/../x`, `/%2e%2e/x`, `/%2f%2fbeispiel.de`, `%zz` (kaputte Kodierung), `javascript:`, `data:`, rohes HTML → Text (Prüfung 2, Befund 6).
- `https://…` → Link mit `rel="noopener"`.
- `{{event:<img src=x>}}` und `{{ort:a"b}}` → verworfen, kein `<img`/`"` im Attribut.

**Proxy (Befund 1, 2):**
- `routeVon` für alle Magazin-Typen inkl. `/magazin`, `/feed.xml`, `/magazin/feed.xml`, `/magazin/redaktion`, `/magazin/autor/x`, `/magazin/rubrik/x` (gültig); `/magazin/autor/x/y` (vier Pfadteile) und `/magazin/x/y` → `ungueltig` (Prüfung 2, Befund 8).
- `pfadPruefen`, Datenbank gemockt, Magazin-Abfragen über `dienstAbfrage()` mit Service-Schlüssel (Befund 2 aus Prüfung 2: Test, dass die anon-Abfrage nicht genutzt wird):
  - unbekannter Slug → `fehlt`; alter Slug → `umleiten`; Zukunft und `zurueckgezogen` → `fehlt`;
  - unbekannte Rubrik/Autor → `fehlt`; `feed-alt` → `umleiten`; `magazin-fest` → `weiter`;
  - Vorschau ohne Schlüssel, mit falschem Schlüssel oder für einen veröffentlichten Beitrag → `fehlt`; Abfragefehler bei der Vorschau → `fehlt`.
- `config.matcher` enthält `/magazin/:path*` und `/feed.xml`.

**Auswahl (Cursor-Prüfung 3, Befund 1; T11):**
- `highlightsImZeitraum(pool, { von: "2026-11-30", bis: "2026-12-06" }, "highlight")` mit einem stärkeren Event am 28.11. im Datenbestand → das Highlight liegt in der Zielwoche 30.11.–06.12. Events vom 04.–06.12. sind Kandidaten.
- Monats-Tipps Dezember (`"top"`): ein Top-Kandidat am 31.12. wird gefunden; Events vom 27.–30.11. nie.
- **Monats-Tipps (Cursor-Prüfung 5, Befund 1):** Das beste Event des Monats (Stufe 3 mit Bild, ohne Flagge) wird als Top-Event gewählt, nicht verdrängt. Es gibt im Monatslauf keinen Highlight-Ausschluss.
- `highlights()` (Startseite) liefert mit denselben Daten dasselbe wie vor dem Umbau (Vergleich mit dem alten Ergebnis).
  - Ein Event, das Highlight **und** Top gewinnen würde, erscheint **in `highlights()`** nur als Highlight (Ausschluss bleibt dort).
  - Ein Stamm-Event (`breite < 1`) wird nie gewählt, weder in `highlights()` noch in `highlightsImZeitraum()`.
- `magazinPoolLaden(von, bis)` (Cursor-Prüfung 5, Befund 2):
  - Termine vom 27.–29.11. sind nicht im Pool für `von` = 30.11. und deckeln die Zielwoche nicht.
  - Ein Lauf mit `datum_bis >= von` ist drin.
  - Serientermine am 04., 08. und 11.12. sind drin (Ende `max(bis, von + 60 Tage)`), das Event am 04.12. wird wie auf der Startseite gedeckelt.
  - `eventPoolLaden()` ohne Argument fragt unverändert ab heute 60 Tage ab.
- Auswahl-Route: ohne Header, mit falschem, zu kurzem oder zu langem Schlüssel und ohne gesetzte Umgebungsvariable → 404 (nie 500, Vergleich über SHA-256, Cursor-Prüfung 4, Befund 1); Antwort `no-store`; Zeitraum muss zur Rubrik passen (Mo–So bzw. ganzer Monat), sonst 400.

**Metadaten (Befund 5):**
- `seitenMetadaten` mit `artikel` → `og:type article`. Ohne → unverändert (`seo-a1.test.ts` grün).
- Feed-`types` im indexierbaren Zweig. Noindex-Zweig: `alternates` undefiniert.
- Startseite, Guide-Hub (`guides/clubs`) und eine Club-Seite liefern den Feed-Link (Metadaten-Funktion direkt aufrufen).

**JSON-LD:**
- `author` ist `Organization`; kein `Person`-Objekt außer `accountablePerson`; **der Pseudonym-Name kommt im JSON-LD nicht vor**; `dateModified` mit Zeitzone; drei Bildgrößen; kein `Event`-Markup.
- Autorenzeile im HTML enthält „(redaktionelles Pseudonym)“. Hinweis am Ende wählt „Eventdaten“/„Ortsdaten“/„Event- und Ortsdaten“ richtig (E4a).
- `ERLAUBTE_FALLBACK_HEROS` stimmt mit den Dateien in `web/public/fallback/` mit ≥ 675 px Höhe überein (84).

**Feed (Befund 13):**
- gültiges XML mit Namensräumen `atom`, `dc`, `media`; Sonderzeichen escaped; RFC-822-Daten; ≤ 20 Items; Schalter aus → 404.

**Autor-Metadaten und Ersatzbild (Cursor-Prüfung 3, Befunde 3 und 4):**
- Beitrag rendert `<meta property="article:author">` **und** `<meta name="author" content="Redaktion dies.das.düsseldorf">`; der Pseudonym-Name steht in keinem der beiden.
- `heroFuer()`: gespeichertes Hero `/fallback/<datei unter 675 px>.webp` → Rubrik-Ersatzbild. Dasselbe Bild in `<img>`, `og:image`, allen drei JSON-LD-Zuschnitten, Feed `media:content` und Sitemap `images`; erlaubtes Hero bleibt unverändert.
- Alle vier Rubrik-Ersatzbilder stehen in `ERLAUBTE_FALLBACK_HEROS`.

**Weitere:**
- Sitemap: Schalter an/aus, archivierte fehlen.
- Ort-Einbettung (Befund 7): Beitrags-HTML enthält weder `google_rating`-Werte noch `/ort-foto/`.
- Zuschnitt-Route (Befund 8): `..`, `%2e%2e`, fremde Ordner, falsche Endung, falsches Seitenverhältnis → 404.
- Rubrik-Werte = URL-Segmente (Befund 9).

### 7.2 Automatisch (Python, `tests/test_magazin.py`)
- **Auswahl-Route gemockt** (die Auswahlfälle selbst testet 7.1, die Logik liegt in TypeScript, T11):
  - Status 404/500, Zeitüberschreitung, ungültiges JSON, Körper ohne `kandidaten` oder mit Nicht-UUID → kein Entwurf, kein Modellaufruf, keine Kostenreservierung, Fehler im Log (Cursor-Prüfung 4, Befund 2);
  - leere Kandidatenliste → kein Entwurf, Hinweis im Log, Lauf gilt als erfolgreich.
- Prüfungen 4.2 (a)–(i) mit Beispielen:
  - Uhrzeit, Preis, „ausverkauft“ im Fließtext; „Europa“ und „Uhrwerk“ schlagen **nicht** an;
  - Datum: „Montag, 30. November“ als Überschrift der Wochenvorschau 30.11.–06.12. → grün; „7. Dezember“ in derselben Überschrift → rot; Saisonzeitraum in Kurzfassung/Teaser → grün; Datum im Fließtext → rot;
  - fremde Event-ID, toter Link, `//fremd.de`;
  - Clickbait, Ich-Form, Titel mit Hub-Kopfbegriff;
  - Fallback-Hero unter 675 px Höhe, `koe-on-ice.webp` → rot.
- **Kostendeckel (Befund 14, Prüfung 2 Befund 7):** Monatssumme $10 aus gemockter `magazin_ki_kosten` → kein Aufruf. Zwei Läufe nacheinander addieren sich. Zwei Prüfungen auf derselben Summe: Die Reservierung des ersten ist in der Summe des zweiten enthalten.
- IndexNow: Feed antwortet 404 → keine Meldung (Prüfung 2, Befund 8).
- Pipeline setzt nie `veroeffentlicht`.
- Doppelter Lauf → kein zweiter Entwurf.
- KI-Aufruf gemockt, **kein echter API-Aufruf in Tests**.

### 7.3 Von Hand vor dem Livegang
- Rich-Results-Test und Schema.org-Validator (Beitrag, Autorenseite, Redaktionsseite).
- W3C-Feed-Validator.
- Search Console URL-Prüfung (gerendertes HTML mit Text und Karten).
- Mobil, Lighthouse.
- `curl -I`:
  - unbekannter Slug → 404 (aus dem Proxy, Body `NICHT_GEFUNDEN_HTML`);
  - alter Slug → 308;
  - `/feed.xml` → 308;
  - Vorschau ohne/mit falschem Schlüssel → 404;
  - `/magazin/rubrik/x` → 404.
- **Rechte (Befund 3):**
  - Mit dem Anon-Schlüssel `magazin_beitraege?select=*` → **nur die öffentlichen Spalten veröffentlichter Zeilen**. PostgREST beschränkt `*` auf erlaubte Spalten, ohne Fehler (Prüfung 2, Befund 2).
  - `magazin_beitraege?select=ki_entwurf`, `?select=vorschau_hash`, `?select=status` → Fehler.
  - `magazin_oeffentlich?select=*` → nur veröffentlichte, keine internen Spalten.
  - `magazin_ki_kosten` → Fehler.
  - `magazin_autoren` → nur aktive.
  - Mit dem Service-Schlüssel: Proxy-Abfrage sieht Entwürfe, `alte_slugs` und `vorschau_hash`.
  - Rechte-Prüfung `konten_rechte_pruefung_2026-11-16.sql` ohne „LÜCKE“.
- **Trigger:** `veroeffentlicht` per Service-Schlüssel (PostgREST, `service_role`) → Fehler; im Table Editor (`postgres`) → geht nur mit Pflichtfeldern und grüner Prüfung. Beide Wege werden geprüft.
- **CHECK `magazin_hero_pfad`:** `/fallback/theater-1.webp` und `/ort-bilder/weihnachtsmaerkte/maerchen-markt.webp` → angenommen; `/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp`, `/ort-bilder/events/x.webp`, `/../x.webp` → abgelehnt.

---

## 8. Umsetzungsschritte und Freigaben

| Schritt | Inhalt | Freigabe / Wer |
|---|---|---|
| 1 | SQL `database/magazin_2026-11-xx.sql`: Tabellen, Rechte, View, Policies, Trigger, Indizes; Rechte-Prüfung | Auftraggeber führt aus |
| 2 | Website: Routen 5.1, Proxy-`matcher` + Prüfung, Renderer, Metadaten + `seitenAlternates`, JSON-LD, Feed, Sitemap, Vorschau, Zuschnitt-Route, Autoren- und Redaktionsseite, `waehleEvent()` + `highlightsImZeitraum()` + `magazinPoolLaden()` + Auswahl-Route `/api/magazin/auswahl` (T11, Secret `MAGAZIN_JOB_SCHLUESSEL` in `deploy.yml` und nach `web/.env.local`), `heroFuer()`; `MAGAZIN_VERLINKT = false`; Tests 7.1 | Cursor-Prüfung des Codes, Deploy nach OK; Seiten live, noindex, unverlinkt |
| 3 | `pipeline/magazin.py` (Auswahl über die Route aus T11, Ressort-Agenten, Prüfungen, Kostendeckel, Meldung, Prüflauf), Schreibprofile (T7), GitHub Action mit `MAGAZIN_AKTIV`; Tests 7.2 | Kosten vor erstem Lauf nennen |
| 4 | Profile der Pseudonyme (E15) + illustrierte Profilbilder; eigene Rubriken Nachtleben, Genuss, Familie (E16) | Erledigt 19.11. (9b4887b, SQL ausgeführt) bis auf die Profilbilder: Der Auftraggeber erzeugt sie aus den Prompts, danach SQL für `bild` |
| 5 | Impressum (§ 18 Abs. 2 MStV), „Unsere Redaktion“, Pseudonym-Kasten, `llms.txt` | Texte vom Auftraggeber freigegeben, Anwalt A1–A3 |
| 6 | Erste Entwürfe, genau drei: „Welcher Weihnachtsmarkt passt zu euch?“, „Top-Events im Dezember 2026“, Wochenvorschau 30.11.–06.12. (Gliederungen 1–3 aus Abschnitt 6; Gliederung 4 folgt im Januar) | Auftraggeber prüft und veröffentlicht |
| 7 | Livegang: `MAGAZIN_VERLINKT = true`, `MAGAZIN_AKTIV=1`, Einbaustellen 5.9, Search Console | Deploy nach OK |
| 8 | Nach 4 und 8 Wochen: Messung (9), Anpassung | Auftraggeber |

---

## 9. Messung
- **Search Console:**
  - Bericht „Discover“: erst ab Mindest-Impressionen, kann wochenlang leer sein.
  - „Leistung“ mit Filter „Seite enthält `/magazin/`“.
  - Indexierung.
- **Bing Webmaster Tools.**
- **Weiterklicks:** Es gibt kein Analysewerkzeug im Code. Stufe 1: nginx-Logs nach `Referer: …/magazin/`, wenn Zugriff besteht. Ein Analysewerkzeug wäre ein eigener Plan.
- **KI-Suchen:** Referrer `chatgpt.com`, `perplexity.ai`, `copilot.microsoft.com`, `gemini.google.com` in nginx-Logs.
- **Ziele nach 8 Wochen:** ≥ 80 % indexiert, Discover-Bericht sichtbar, Wochenvorschau mit Impressionen auf „was ist los in düsseldorf“/„events düsseldorf diese woche“, keine manuelle Maßnahme.

---

## 10. Risiken

| Nr. | Risiko | Gegenmaßnahme |
|---|---|---|
| R1 | Kannibalisierung mit Guides | E5, Prüfung 4.2 (h), Hub-Link. Search Console beobachten; Beitrag umschreiben, nie auf den Hub umleiten |
| R2 | „Scaled content abuse“ | Freigabe durch den Auftraggeber (technisch erzwungen), begrenzte Frequenz, Mehrwert, keine Seiten nur für Suchbegriffe |
| R3 | Falsche Fakten | T3, Prüfung 4.2 (b), Prüflauf, Korrekturhinweis |
| R4 | Discover liefert wenig | Als Ergänzung planen; Suche und Wochenvorschau sind der verlässliche Teil |
| R5 | Bildrechte und KI-Kennzeichnung | Nur eigene, KI-Symbol- (gekennzeichnet) und lizenzierte Bilder; Pflichtfelder; A1/A2 |
| R6 | Engpass Freigabe | Ohne Freigabe erscheint nichts (sicherer Ausfall) |
| R7 | Rechtefehler macht Entwürfe öffentlich | Spaltenrechte + Policy + `security_invoker`-View, Test 7.3, Rechte-Prüfung |
| R8 | Cache-Verzögerung | T10: normal bis 5 min, spätestens 10 min |
| R9 | Rechtliche Pflichten | Impressum, Workflow, Anwalt A1–A3 |
| R10 | KI-Kosten | Deckel aus der Datenbank-Summe, $10/Monat |
| R11 | Feed-Link fehlt | `seitenAlternates`, Test 7.1 |
| R12 | Pseudonyme schwächen das Vertrauen (E-E-A-T) oder wirken irreführend | Offene Kennzeichnung (2.3), keine erfundenen Qualifikationen und Erlebnisse, illustrierte und gekennzeichnete Profilbilder, echte Verantwortung sichtbar, kein `Person`-Markup für Pseudonyme |
| R13 | Entwurf im HTML einer 200-Antwort | Vorschau-Zugang im Proxy (5.3), zweite Prüfung in der Seite, Tests |

---

## 11. Abnahme (Stufe 1)
1. `/magazin`, die drei Beiträge aus Schritt 6 (Weihnachtsmärkte, Top-Events Dezember, Wochenvorschau), die Autorenseiten und `/magazin/redaktion` liefern 200 mit Inhalt in der ersten HTML-Antwort.
2. Rich-Results-Test: `Article` ohne Fehler, `author` = Organisation, `accountablePerson` gesetzt, Bilder ≥ 1200 px. `max-image-preview:large` im robots-Meta.
3. Feed validiert. Der Feed-Link steht auf Startseite, Event-Seite, Guide-Hub, Club-Seite und Beitrag.
4. Sitemap enthält die Beiträge. IndexNow-Meldung im Log mit HTTP 200/202.
5. Unbekannter Slug, unbekannte Rubrik, Vorschau ohne Schlüssel → 404 aus dem Proxy; alter Slug und `/feed.xml` → 308.
6. Entwürfe und interne Spalten mit Anon-Schlüssel nicht lesbar. Die Pipeline kann nicht veröffentlichen.
7. Jeder Beitrag hat Bildnachweis, Alt-Text, bei KI-Bild „Symbolbild (KI-generiert)“, Quellen, Hinweis nach E4/E4a mit passender Datenart, Autorenzeile mit „(redaktionelles Pseudonym)“. Jede Autorenseite hat den Pseudonym-Kasten und „KI-generiertes Profilbild“.
8. Impressum nennt § 18 Abs. 2 MStV, den Verantwortlichen und den Hinweis auf Pseudonyme.
9. Alle Tests grün. Cursor-Prüfung des Codes ohne kritischen Befund.
10. Kostenprotokoll des ersten Laufs liegt vor, Abweichung höchstens ±50 % zu 4.4, sonst Schätzung anpassen.

---

## 12. Offene Punkte
- **Profilbilder** der fünf Pseudonyme (E15 entschieden 19.11., Kurzbeschreibungen in der Datenbank; `bild` bis dahin NULL).
- **E3, E6, E8, E9, E10, E13, E14:** gelten mit der Empfehlung, solange nichts anderes gesagt.
- **Anwalt:**
  - **A1:** Pseudonyme mit offengelegter Verantwortung; KI-Kennzeichnung von Texten und Bildern (Art. 50 KI-VO), auch für die KI-Symbolbilder auf der übrigen Website; KI-Profilbilder.
  - **A2:** Veranstalterbilder als Aufmacher.
  - **A3:** § 20 MStV und weitere Impressumsangaben.
- Zugriff auf nginx-Logs (9)?
- Eigene Fotos als Hero (Weihnachtsmärkte vorhanden; Clubs, Stadt)?

---

## Anhang A: Cursor-Prüfung vom 19.11.2026 – Einarbeitung

| Befund | Schwere | Eingearbeitet in |
|---|---|---|
| 1 Vorschau-Prüfung in der Seite → Soft-404, Schlüssel in Logs/Referer | kritisch | 5.3, 5.1 (Typ `magazin-vorschau`), 3.1 (`vorschau_hash` je Entwurf), R13, Tests 7.1/7.3 |
| 2 `matcher` kennt `/magazin` und `/feed.xml` nicht; feste Pfade | kritisch | T4, 5.1 (Typen und Entscheidungstabelle), Tests 7.1 |
| 3 SQL für Rechte fehlt, View ohne `security_invoker`, `hero_bild` ungeprüft | mittel | 3.1 (Rechte-SQL, Trigger, CHECK), 7.3 |
| 4 „höchstens 10 Minuten“ falsch; Proxy-Fehltreffer 2 min | mittel | T10, 4.2 Punkt 6, 5.1, 5.12, R8 |
| 5 Feed-Link fehlt auf Seiten mit eigenem `alternates` | mittel | 1.2, 5.6 (`seitenAlternates`), 7.1 |
| 6 `LINK_MUSTER` erlaubt `//`, kein `https://`; Einbettungs-IDs ungeprüft | mittel | 1.2, T2, 7.1 |
| 7 `OrtKarte`/`GuideKarte` zeigen Google-Foto und -Bewertung | mittel | 1.2, 5.2 (`MagazinOrtKarte`), 7.1 |
| 8 Zuschnitt-Route Pfad-Traversal | mittel | 5.11, 7.1 |
| 9 Rubrik `monats_tipps`/`monats-tipps`; Titel = Hub-Kopf; Preise/„ausverkauft“ ungeprüft | mittel | 3.1 (Rubrik = URL-Segment), 6 (neue Titel), 4.2 (b), (h) |
| 10 Fallback-Bilder sind KI-generiert | mittel | 1.2, 1.4, E7 (Entscheidung), 5.11 |
| 11 Schalter steuert Sitemap/Feed/Index nicht; E2/E4 offen | mittel | T9, 5.5–5.7, E2/E4 entschieden, 2.3 |
| 12 Zeilennummern, `wochenendProgramm` nur Fr–So, Modell-ID, `revalidateTag`-Zeile | gering | 1.2, 4.2 |
| 13 Feed-Namensräume, IndexNow-Satz, `tag` in T2 | gering | 5.6, 5.8, T2, 7.1 |
| 14 Kostendeckel aus Prozesszähler | gering | 4.4, 7.2 |

---

## Anhang B: Cursor-Prüfung 2 vom 19.11.2026 – Einarbeitung

Gesamturteil der Prüfung: kritische Lücken der ersten Fassung geschlossen; nicht freigabefähig, bis CHECK, Service-Schlüssel und
Datumsausnahme im Plan stehen und E4a beantwortet ist. Alle drei Punkte und E4a sind in dieser dritten Fassung erledigt.
E15 blockiert die technische Freigabe nicht (gebraucht in Schritt 4); A1–A3 vor dem Livegang.

| Befund | Schwere | Eingearbeitet in |
|---|---|---|
| 1 CHECK `hero_bild` mit `\|` (wörtlicher Strich), Fremdfoto fällt nicht heraus, Mindesthöhe | mittel | 3.1 (Constraint `magazin_hero_pfad` im SQL-Block, `ERLAUBTE_FALLBACK_HEROS`), 4.2 (i), 7.1, 7.3 |
| 2 Proxy liest mit anon-Schlüssel → Vorschau immer 404, alte Slugs 404; Test erwartet falschen Fehler | mittel | 3.1 („Welcher Schlüssel liest was“, `dienstAbfrage()`), 5.1, 5.3, Trigger `SECURITY INVOKER`, 7.1, 7.3 |
| 3 Datumsausnahme zu eng; Teaser/Kurzfassung; E4-Satz falsch für Ortsdaten; „Euro“/„Uhr“ als Teilwort | mittel | 4.2 (b), E4a (entschieden), 5.2 Punkt 11, 7.1, 7.2 |
| 4 Pseudonym im JSON-LD (`Role`/`Thing`) nutzlos; Wort „Pseudonym“ erst auf der Autorenseite | gering | 2.3 Punkt 6, 5.2 Punkt 3, 5.4, 7.1 |
| 5 „keine harte Obergrenze“ widerspricht `expire` | gering | T10, R8 |
| 6 Prozent-kodierte Linkziele (`/%2e%2e/`, `/%2f%2f…`) | gering | T2, 7.1 |
| 7 Kostendeckel bei gleichzeitigen Läufen | gering | T6 (`concurrency`), 3.1 (`magazin_ki_kosten`), 4.4 (Reservierung), 7.2 |
| 8 IndexNow trotz Schalter aus; Test „drei Segmente“; Zahl der Startbeiträge | gering | T6, 5.8 (Feed-200-Bedingung), 5.1, 7.1, Schritt 6, Abnahme 1 |

---

## Anhang C: Cursor-Prüfung 3 vom 19.11.2026 – Einarbeitung

Gesamturteil der Prüfung: kein kritischer Befund; freigabefähig, sobald der Satz zu `highlights()` in 4.2 steht. Die drei geringen
Punkte sind ebenfalls eingearbeitet (Wunsch des Auftraggebers: alle Befunde lösen).

| Befund | Schwere | Eingearbeitet in |
|---|---|---|
| 1 `highlights()` rechnet mit heute + 6/+ 29 Tagen, nicht mit Kalenderwoche/-monat | mittel | 4.2 Punkt 1 (`highlightsImZeitraum`, Zeitraum = `gueltig_von`/`gueltig_bis`), 7.1 „Auswahl“ |
| 2 Abschnitt 0 zählt zwei Beiträge, Schritt 6 und Abnahme drei | gering | Abschnitt 0 (Fr 27.11., Sa 28.11., So 29.11.) |
| 3 „Standard-Symbolbild der Rubrik“ ohne Datei; zu flaches Bild nach Veröffentlichung; `og:image` nicht abgedeckt | gering | 3.1 (Rubrik-Ersatzbilder, `heroFuer()` beim Rendern), 5.4, 5.5, 7.1 |
| 4 `<meta name="author">` fehlt in 5.5 | gering | 5.5 (Feld `authors` der Seiten-Metadaten), 7.1 |

**Zusätzlich, aus eigener Durchsicht (nicht von Cursor gemeldet):**
- Die Auswahl-Logik (`stufenKontext`, `breite`, `beliebtAuswahl`, `highlights`) gibt es nur in TypeScript, die Pipeline ist Python.
- Deshalb die neue Entscheidung **T11**: Die Auswahl läuft über die geschützte interne Route `POST /api/magazin/auswahl` mit Header-Schlüssel `MAGAZIN_JOB_SCHLUESSEL`.
- Eingearbeitet in Schritt 2 und 3 sowie Tests 7.1.

---

## Anhang D: Cursor-Prüfung 4 vom 19.11.2026 – Einarbeitung

Gesamturteil der Prüfung: kein kritischer Befund; freigabefähig, sobald der Schlüssel in `web/.env.local` steht und ein Fehler der
Auswahl-Route den Entwurf abbricht. Beide Punkte und die zwei geringen Befunde sind eingearbeitet.

| Befund | Schwere | Eingearbeitet in |
|---|---|---|
| 1 `MAGAZIN_JOB_SCHLUESSEL` nur in `envs` erreicht die laufende Website nicht; `timingSafeEqual` wirft bei ungleicher Länge | mittel | T11 (Schreiben nach `web/.env.local` vor dem Build, SHA-256-Vergleich, fehlende Variable → 404), Schritt 2, 7.1 |
| 2 Fehler der Auswahl-Route bricht den Entwurf nicht ab; 7.2 testet Auswahl in Python | mittel | T11 (Abbruch ohne Zeile, Modellaufruf, Reservierung; leere Auswahl gültig), 7.2 (Route gemockt) |
| 3 `highlights()` verliert Stamm-Filter und Highlight-Ausschluss; Vortermine vor `von` verfälschen Serien | gering | 4.2 Punkt 1 (`highlights()` unverändert, gemeinsame Hilfe `waehleHighlightUndTop`, Pool-Kopie ohne Vortermine, eigener Pool bis `bis`), 7.1 |
| 4 Feed `media:content` und Sitemap `images` nutzen das gespeicherte Hero | gering | 5.6, 5.7, 7.1 |

---

## Anhang E: Cursor-Prüfung 5 vom 19.11.2026 – Einarbeitung

Gesamturteil der Prüfung: kein kritischer Befund; freigabefähig, sobald der Monats-Tipp `.top` aus der Monatsliste nimmt, ohne
das beste Event derselben Liste an `.highlight` zu verlieren. Beide Befunde sind eingearbeitet.

| Befund | Schwere | Eingearbeitet in |
|---|---|---|
| 1 Monats-Tipps: Bei „Woche = Monat = Zeitraum“ verbraucht `.highlight` das beste Event, `.top` wird der Zweite | mittel | 4.2 Punkt 1: statt `waehleHighlightUndTop` nur die herausgezogene Regelkette `waehleEvent`; `highlightsImZeitraum(…, art)` wählt **ein** Event (`"highlight"` bzw. `"top"`) ohne Highlight-Ausschluss; der Ausschluss bleibt nur in `highlights()`. Tests 7.1 |
| 2 `eventPoolLaden()` hat kein Ende, ist Quelle der Startseite; Ende = `bis` schneidet spätere Serientermine ab | gering | 4.2 Punkt 1: eigene `magazinPoolLaden(von, bis)` mit Abfrage ab `von` und Ende `max(bis, von + 60 Tage)`; `eventPoolLaden()` unverändert. Schritt 2, Tests 7.1 |

---

## Anhang F: Cursor-Prüfung 6 vom 19.11.2026 – Einarbeitung

Gesamturteil der Prüfung: freigabefähig, kein kritischer oder mittlerer Befund. Beide geringen Punkte sind vor der Freigabe
eingearbeitet.

| Befund | Schwere | Eingearbeitet in |
|---|---|---|
| 1 Aufrufe von `waehleEvent` passen nicht zur Signatur; Flagge braucht den Tag (`flagge(e, k.heute)`), Vergleich ist `nachEmpfehlung(k)` | gering | 4.2 Punkt 1 (Signatur `waehleEvent(liste, flagge, k, ohne?)`, Aufrufe `waehleEvent(woche, highlightGilt, k)` / `waehleEvent(monat, topGilt, k, highlight?.id)`) |
| 2 `magazinPoolLaden` ohne `buendeln`; Fehlerfall und Beispieldaten | gering | 4.2 Punkt 1 (gleiche Schleife, `SPALTEN_VARIANTEN`, `normalisieren`, `buendeln`; wirft bei Fehler, nie Beispieldaten; kein `"use cache"`) |
