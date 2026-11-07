# SEO- und GEO-Analyse diesdas.events

**Stand:** 06.11.2026 · **Status:** Analyse, noch nichts umgesetzt

GEO = Generative Engine Optimization, also die Lesbarkeit für KI-Systeme wie ChatGPT, Claude oder Perplexity.

**Geprüft wurden** 10 Anfragen an die Live-Website:

- Startseite, `/heute`, `/entdecken?kategorie=musik`
- ein kommendes und ein abgelaufenes Event, eine Reihe, eine Guide-Seite (Restaurant)
- `robots.txt`, `sitemap.xml`, `llms.txt`

Dazu kam die Ursachenprüfung im Code (`web/`).

**Nicht geprüft:**

- Core Web Vitals (echte Ladezeiten)
- Search-Console-Daten (Indexierung, Rankings)
- mobile Darstellung im Detail

## Kurzfazit

Die technische Grundlage passt: Seiten liefern 200, `lang="de"` ist gesetzt, es gibt saubere Seitentitel und Beschreibungen, eine aktuelle Sitemap (3.513 URLs), eine offene `robots.txt` und Event-JSON-LD auf den Eventseiten.

Bei der **KI-Lesbarkeit** gibt es eine große Lücke: Der Hauptinhalt steckt in versteckten Streaming-Blöcken. Bei **Alt-Texten, Canonicals und Vorschaubildern** gibt es einfache, schnell lösbare Defizite. Der größte Reichweiten-Hebel für SEO sind **feste Landingpages für Kategorien und Stadtteile**.

## Empfohlene Reihenfolge

| Schritt | Paket | Punkte | Aufwand |
|---|---|---|---|
| 1 | Quick Wins | Alt-Texte (2), Canonicals/noindex (3), Open Graph (4), llms.txt (8) | ca. ½ Tag |
| 2 | Streaming-Fix | Inhalte in die erste HTML-Antwort (1), doppelte H1 (9) | mittel |
| 3 | Strukturierte Daten und Icons | JSON-LD erweitern (5), Icon-Text entfernen (7) | mittel |
| 4 | Landingpages | Kategorie- und Stadtteil-Seiten (6) | mittel bis groß, braucht Texte |
| 5 | Feinschliff | Titelbereinigung (10), Über-uns (11), Seitengewicht (12), HSTS (13) | klein bis mittel |

---

## Hohe Priorität

### 1. Hauptinhalt steckt in versteckten Streaming-Blöcken (GEO-Kernproblem)

**Befund:** Fast alle Seiten laden ihren Inhalt über React Suspense „gestreamt“. In der ersten HTML-Antwort steht der Inhalt in Containern mit dem Attribut `hidden`; erst JavaScript schiebt ihn an die richtige Stelle. Gemessen (Text ohne Skripte):

| Seite | sichtbarer Text | Text in `hidden`-Containern |
|---|---|---|
| Startseite | ca. 1.000 Zeichen | ca. 7.000 Zeichen |
| `/heute` | 961 Zeichen | 27.567 Zeichen |
| Eventseite | ca. 1.000 Zeichen | ca. 1.500–1.800 Zeichen |
| Reihenseite | ca. 980 Zeichen | ca. 420 Zeichen |

`<Suspense>` steckt in: `app/page.tsx`, `app/heute`, `app/entdecken`, `app/wochenende`, `app/stadtteile`, `app/tag/[datum]`, `app/event/[kategorie]/[slug]`, `app/reihe/[slug]`, `app/guides/…`.

**Folge:**

- Google rendert JavaScript und sieht alles.
- KI-Crawler (GPTBot, ClaudeBot, PerplexityBot) führen in der Regel **kein JavaScript** aus, und viele Text-Extraktoren verwerfen versteckte Elemente. Für sie besteht die Seite im Wesentlichen aus Menü und Ladegerüst.

**Vorschlag:**

- Inhalte, die ohnehin per `"use cache"` zwischengespeichert sind, direkt in die erste HTML-Antwort (statische Hülle) rendern. Das betrifft Event, Reihe, Guide-Ort und Tageslisten.
- Suspense-Grenzen nur noch um wirklich anfragebezogene Teile (Suchfilter, `searchParams`).
- Anfangen mit Eventseiten, Reihen und Guide-Orten, danach Listen.
- Vorher die Next-16-Doku zu Cache Components und Partial Prerendering lesen (`web/node_modules/next/dist/docs/`).

**Prüfen nach Umsetzung:** `curl` auf eine Eventseite; Titel und Beschreibung des Events müssen außerhalb von `hidden`-Containern im HTML stehen.

### 2. Alt-Texte der Bilder sind leer

**Befund:**

- Startseite: 41 von 41 Bildern mit `alt=""`.
- `/heute`: 251 leer, der Rest nur `alt="Symbolbild"`.
- Eventseiten: alle leer.
- Guide-Seite: nur das Hauptbild hat einen Alt-Text (Restaurantname).

**Code:** `components/karten.tsx` (Komponente `Bild`: `alt=""`), `components/client.tsx` (`BildImg`: `alt={istSymbol ? "Symbolbild" : alt}`), `components/zeitleiste.tsx`, `components/ort-karten.tsx`, `app/guides/page.tsx`, `app/guides/restaurants-cafes/page.tsx`.

**Folge:**

- Keine Sichtbarkeit in der Google-Bildersuche.
- KI-Systeme erfahren nichts über die Bilder.
- Das Hauptbild der Eventseite ist für Screenreader unsichtbar.

**Vorschlag:**

- Echte Event-Bilder: Alt-Text = Event-Titel plus Ort (z.B. „Comedian Harmonists – Best of, Opernhaus Düsseldorf“).
- Symbolbilder: `alt=""` (dekorativ) statt „Symbolbild“, alternativ „Symbolbild Musik“.
- In Kartenlisten (Titel steht daneben) einen kurzen Alt-Text oder bewusst leer lassen.
- Hauptbild der Eventseite immer mit Alt-Text.

### 3. Canonical-Angaben fehlen auf den meisten Seiten

**Befund:**

- Kein `<link rel="canonical">` auf Startseite, `/heute`, `/wochenende`, `/stadtteile`, `/tag/…` und allen Eventseiten.
- Ebenso keins auf `/entdecken` mit sämtlichen Filterkombinationen (`?kategorie=`, `?q=`, `?stadtteil=`, `?datum=` …).
- Vorhanden ist es nur bei Reihen, Guides und „Event melden“.

**Folge:**

- Google kann unzählige Filterkombinationen als eigene Seiten werten (doppelte Inhalte, verschwendetes Crawl-Budget).
- Die alten UUID-Adressen der Events (`/event/<uuid>`, leiten weiter) konkurrieren mit den neuen.

**Vorschlag:**

- Canonical auf jeder Seite über `alternates.canonical` (`metadataBase` ist im Layout schon gesetzt).
- Eventseiten: Canonical = `/event/<kategorie>/<slug>`.
- Entdecken mit Filtern oder Suche: `robots: { index: false, follow: true }` oder Canonical auf `/entdecken`. Ihre Rolle übernehmen später die Landingpages (Punkt 6).

### 4. Vorschaubilder und Open Graph sind unvollständig

**Befund:**

- Startseite, `/heute`, Entdecken und Reihen ohne `og:image`. Geteilte Links (WhatsApp, Instagram-Bio, iMessage) erscheinen ohne Bild.
- Eventseiten und Guide-Seiten setzen ein eigenes `openGraph`-Objekt. Next.js ersetzt das Layout-Objekt komplett, dadurch fehlen dort `og:site_name`, `og:locale` und `og:type` (geprüft: Eventseite und Guide-Seite ohne `og:site_name`).
  - Code: `app/event/[kategorie]/[slug]/page.tsx` Zeile 32, `app/guides/restaurants-cafes/[slug]/page.tsx` Zeile 31.
- `og:url` fehlt überall.
- Listenseiten haben nur `twitter:card = summary`.

**Vorschlag:**

- Standard-Vorschaubild im Markendesign, z.B. `app/opengraph-image.tsx`. Next.js kann pro Seite automatisch Bilder erzeugen, z.B. für Reihen und Kategorien.
- In Seiten die Grundangaben mitgeben (`siteName`, `locale`, `type`) oder eine gemeinsame Hilfsfunktion nutzen.
- `og:url` = Canonical-URL.
- `twitter:card = summary_large_image`, wo ein Bild vorhanden ist.

---

## Mittlere Priorität

### 5. Strukturierte Daten (JSON-LD) erweitern

**Befund:** JSON-LD gibt es nur als `Event` auf Eventseiten (`lib/json-ld.ts`). Reihe, Guide, Listen und Startseite haben keins.

**Vorschlag:**

- **Global (Layout):**
  - `WebSite` mit `SearchAction` (Suche über `/entdecken?q=`).
  - `Organization` mit Name, Logo und `sameAs` (Instagram).
- **Brotkrumen:** `BreadcrumbList` auf Event-, Reihen- und Guide-Seiten. Sichtbare Brotkrumen gibt es teils schon (`.gd-krumen`).
- **Reihenseite:** `EventSeries` mit `subEvent` (kommende Termine). Die Eventseiten verweisen bereits per `superEvent` darauf.
- **Listen** (`/heute`, `/tag/…`, `/wochenende`): `ItemList` mit den Events.
- **Guide-Seiten:** `Restaurant` bzw. `CafeOrBakery` / `LocalBusiness` mit Adresse, Koordinaten (`geo`), Öffnungszeiten, Küche (`servesCuisine`), Website und Telefon.
  - **Achtung:** Google-Sternebewertungen nicht als `aggregateRating` auszeichnen (Bewertungen Dritter, verstößt gegen Googles Richtlinien).

### 6. Landingpages für Kategorien und Stadtteile (größter SEO-Hebel)

**Befund:** Kategorien und Stadtteile gibt es nur als Filter-Parameter (`/entdecken?kategorie=musik`). Feste, beschreibende Adressen fehlen. Achtung: `/event/<kategorie>` ist keine Kategorieseite, sondern ein Legacy-Redirect für UUIDs.

**Vorschlag:**

- Feste Seiten, z.B. `/kategorie/musik` (oder sprechend `/konzerte-duesseldorf`) und `/stadtteil/flingern`.
- Jede Seite mit:
  - eigener H1 und kurzem Einleitungstext (2–4 Sätze, gern redaktionell),
  - aktuellen Events,
  - Links zu Unterthemen, Nachbar-Stadtteilen und Reihen,
  - `ItemList` und `BreadcrumbList`.
- Optional ein kurzer FAQ-Block („Was ist heute in Flingern los?“). Das ist auch gutes Futter für KI-Antworten.
- In die Sitemap aufnehmen und intern verlinken (Navigation, Eventseiten).
- Zielt auf Suchanfragen wie „Konzerte Düsseldorf heute“, „Events Flingern“ oder „Kostenlose Events Düsseldorf“.

### 7. Icon-Namen landen als Text auf der Seite

**Befund:**

- Die Icons sind Schrift-Ligaturen (Material Symbols, `Icon` in `components/karten.tsx`).
- Im reinen Text steht daher z.B. „search Suche calendar_today Heute expand_more …“, oft ganz am Anfang.
- Für Screenreader ist das per `aria-hidden` ausgeblendet, Text-Extraktoren von Suchmaschinen und KI lesen es aber mit.

**Vorschlag:** Icons über CSS (`::before` mit `content: attr(data-icon)`) oder als Inline-SVG einbinden, damit die Namen nicht als Text im HTML stehen.

### 8. Keine `llms.txt`

**Befund:** `/llms.txt` liefert 404.

**Vorschlag:** Kurze Datei unter `web/public/llms.txt` (oder als Route) mit:

- was die Seite ist,
- welche Bereiche es gibt (Events, Reihen, Guides),
- wie aktuell die Daten sind,
- Quellenhinweis und Link zur Sitemap.

Der Nutzen ist heute noch begrenzt, der Aufwand fast null.

### 9. Doppelte H1

**Befund:** Startseite (`app/page.tsx` Zeilen 90 und 395) und Entdecken (`app/entdecken/page.tsx` Zeilen 52 und 102) haben je zwei H1: eine im Ladegerüst (Fallback), eine im Inhalt.

**Vorschlag:** Erledigt sich weitgehend mit Punkt 1. Sonst im Ladegerüst keine H1 verwenden.

---

## Niedrige Priorität

### 10. Rohe Titel und kurze Beschreibungen aus den Scrapern

**Beispiele:**

- Titel: „the biggest Problem in the world • Düsseldorf • Stand up Comedy in English with Victor Patrascan“
- Beschreibung: „Die Goldenen Zwanziger in Concert“

**Vorschlag:**

- Für `<title>` und H1 eine Bereinigung: erster Buchstabe groß, „• Düsseldorf •“ und Doppelungen entfernen, Länge auf ca. 60 Zeichen begrenzen.
- Sehr kurze Beschreibungen automatisch um Datum, Uhrzeit und Ort ergänzen.

### 11. Über-uns-Seite mit Fakten (Vertrauenssignale, E-E-A-T)

**Vorschlag:** Eine Seite mit nachprüfbaren Fakten, z.B.:

- „Wir sammeln täglich Events aus über 40 Quellen“
- Auswahlkriterien für die Guides (Qualitäts-Score)
- Wer dahintersteht, Kontakt

KI-Systeme zitieren solche klaren Aussagen gern. Das Impressum ist vorhanden.

### 12. Seitengewicht und Ladezeit

**Befund:**

- `/heute` ist 571 KB HTML mit 276 Bildern.
- Start- und Eventseiten liefern `Cache-Control: private, no-store`; kein Zwischenspeicher (CDN) kann helfen.

**Vorschlag:**

- `/heute` paginieren oder Bilder erst beim Scrollen laden (Lazy Loading ist teilweise schon aktiv).
- Core Web Vitals mit PageSpeed Insights bzw. der Search Console messen.

### 13. Sicherheits-Header

**Befund:** `Strict-Transport-Security` (HSTS) fehlt.

**Vorschlag:** In nginx ergänzen (ISPConfig). Kein direkter Ranking-Faktor, aber gut für Sicherheit und Vertrauen.

---

## Was schon gut ist

- **`robots.txt`:** erlaubt alle Crawler inklusive KI-Bots, sperrt nur `/api/` und verweist auf die Sitemap. Das passt zum GEO-Ziel.
- **Sitemap:** aktuell, mit `lastmod`, ohne abgelaufene Events. Enthält Reihen mit kommenden Terminen (418) und Guides (684).
- **Seitentitel und Beschreibungen:** auf allen geprüften Seiten vorhanden, sinnvoll und mit einheitlichem Titel-Muster.
- **Eventseiten:**
  - `Event`-JSON-LD mit echtem Datum (inkl. Berliner Zeitzone), Ort, Status (auch `EventCancelled`) und Verweis auf die Reihe.
  - Abgelaufene Events bleiben online (HTTP 200), zeigen einen Hinweis und kommende Events.
- **Guide-Seiten:** Canonical, Vorschaubild, guter Titel („DHABA – Indian Food – Restaurant in Unterbilk“), Alt-Text am Hauptbild.
- **Reihenseiten:** Canonical, sprechende Beschreibung mit nächstem Termin.
- **Grundlagen:** `lang="de"`, gzip-Komprimierung, HTTPS.

---

## Messpunkte für später

Vorher und nachher vergleichen:

- **Search Console:** indexierte Seiten, Impressionen und Klicks für „Events Düsseldorf“, „Konzerte Düsseldorf“ und Stadtteil-Suchen; Ergebnisse des Rich-Results-Tests für Event, Restaurant und Breadcrumbs.
- **KI-Sichtbarkeit:** In ChatGPT, Perplexity und Claude Fragen stellen wie „Was ist heute in Düsseldorf los?“ oder „Gute indische Restaurants in Unterbilk?“ und prüfen, ob diesdas.events genannt oder verlinkt wird.
- **Rohes HTML:** `curl https://diesdas.events/event/…`. Steht der Event-Inhalt außerhalb von `hidden`-Containern?
