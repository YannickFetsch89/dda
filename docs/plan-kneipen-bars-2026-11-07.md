# Plan: Guide-Hub „Kneipen & Bars“

**Stand:** 07.11.2026, Version 2 (Cursor-Review eingearbeitet, siehe Abschnitt 9) · **Status:** Plan, noch nichts umgesetzt

**Ziel:** Neuer Hub `/guides/kneipen-bars` mit Übersicht (Design-Ansichten 18/19) und Detailseite (20/21) laut Handoff `12_kneipen-bars`. Er baut auf dem Restaurant-Hub (`11_restaurants-cafes`) auf. Die Datengrundlage kommt wie bei den Restaurants aus Google Places (Flächensuche → Vorab-Score → Details → Kuration), ergänzt um eine Einordnung in Kneipe oder Bar, Spezialitäten und Vibes.

---

## 1. Ausgangslage (geprüft, von Cursor bestätigt)

### Daten

- **`typ = 'kneipe'`** ist im CHECK-Constraint schon erlaubt (`database/schema_orte.sql:11`). Für den Typ ist **keine Migration nötig**. Heute gibt es **0** Orte mit `typ = 'kneipe'` (Restaurants 472, Cafés 135, Imbiss 76).
- **Altbier-Brauhäuser fehlen ganz:** Uerige, Füchschen, Schumacher, Schlüssel und Kürzer stehen nicht in der DB. Die Restaurant-Suche nimmt nur Restaurant- und Café-Typen auf; `brewpub` und `gastropub` gelten dort als Restaurant (`flaechensuche.py:96-101`).
- **Bereits im Restaurant-Hub:** 2 `brewpub` (Brauhaus Alter Bahnhof, Ratinger Brauhaus) und 4 `gastropub` (z.B. Froschkönig, Hamtorkrug), siehe E1.
- **Zwischenspeicher der Restaurant-Suche** (`data/orte/flaechensuche.json`, 3.926 Kandidaten): Nur ca. 93 haben einen Bar-Primärtyp. **Folge:** Es braucht eine **eigene Flächensuche mit Bar-Typen**.
- **Aufbau des Zwischenspeichers:** eine Datei mit `orte` (Schlüssel = Place-ID), `warteschlange`, `erledigt`, `gesaettigt_min`. Die Zellenschlüssel (`Stufe:Zeile:Spalte`, `flaechensuche.py:204-208`) enthalten keinen Hub. Deshalb **muss jeder Hub eine eigene Datei** haben, sonst gelten erledigte Restaurant-Zellen auch für Bars als fertig.
- **Kandidatenfilter sind auf Restaurants festgelegt:**
  - `ort_typ()` und `ist_kandidat()` verwerfen alles, was kein Restaurant oder Café ist (`flaechensuche.py:294-313`), und `importieren` nimmt nur diese Kandidaten (`flaechensuche.py:564`).
  - `ort_aus_place()` wirft jeden Treffer mit `hotel` in `types` weg (`google_places.py:263-264`).
  - **Ohne Anpassung bliebe ein Bar-Import leer** (siehe 3.1).
- **Mindestwerte:** Rating ≥ 4,0 und ≥ 30 Bewertungen (`config.py:27-28`). Sichtbar wird ein Ort nur mit `aktiv` **und** Score ≥ 7 (`web/lib/orte.ts:31`).

### Website

- Für `kneipe` sind schon angelegt: Route `/guides/kneipen-bars` (`ort-karten.tsx:16-17`), Icon und Label (`:40`, `:56`) und die Kachel auf `/guides` (`fertig: false`, `app/guides/page.tsx:30`). Eine Seite unter `app/guides/kneipen-bars/` gibt es noch nicht.
- **Wiederverwendbar:**
  - `lib/guide-filter.ts` (Paging, Zählen, Sortierung)
  - `components/ort-karten.tsx`, `components/guide-sticky.tsx`
  - `lib/orte.ts`: `EXTRAS_FELDER` ist eine Positivliste, geladen als `x_<feld>:extras-><feld>`.
  - Foto-Proxy `/ort-foto/<slug>`
  - `gd-*`-Styles
- **Restaurant-Übersicht:** Hero und Liste stehen in einer Suspense-Grenze, die `searchParams` abwartet (`restaurants-cafes/page.tsx:79-81`, `258-272`). Die erste HTML-Antwort ist deshalb der Ladezustand, nicht die Orte.
- **Restaurant-Detailseite:**
  - Name, Beschreibung und Adresse stehen schon außerhalb der Suspense-Grenze (`[slug]/page.tsx:202-227`).
  - „Events in der Nähe“ filtert nach gleichem Stadtteil und sortiert nach Datum (`:107-113`). **Events haben keine Koordinaten**, eine Entfernung lässt sich nicht berechnen.
- **Eine Detail-URL pro Ort:** `ortPfad` baut die URL aus `ort.typ` (`ort-karten.tsx:33`). Die Restaurant-Detailseite antwortet für andere Typen mit 404 (`[slug]/page.tsx:160`). Die Sitemap nutzt ebenfalls `ortPfad` (`sitemap.ts:47-57`).

### Design (Handoff `12_kneipen-bars`)

**Stimmung:** abendlicher, aber kein Dark Mode.
- Hero dunkler mit Gold-Schimmer.
- Card-Border `#D9DEE7`.
- Gold gedämpft `#9C8346` für Typ-Label und Stern.

**Übersicht:**
- Hero „Kneipen & Bars“ mit Unterzeile „N Empfehlungen – von der Altbier-Kneipe bis zur Cocktailbar“.
- **Filter:**
  - Stadtteil (Einzelauswahl)
  - Spezialität (Mehrfachauswahl: Craft Beer, Cocktails, Altbier, Wein, Whisky)
  - Vibe (Mehrfachauswahl: Gemütlich, Gesellig, Draußen sitzen, Sportsbar)
  - Schalter „Happy Hour“ und „Raucherbereich“
  - Sortierung
  - Kein Typ-Tab Kneipe/Bar, keine Kartenansicht im Design.
- **Card:**
  - Typ-Label „KNEIPE“ bzw. „BAR“
  - Spezialitäten-Zeile
  - Happy-Hour-Badge, dann max. 2 Vibe-Chips (ohne Badge max. 3)

**Detail:**
- Typ-Zeile „KNEIPE · ALTSTADT“.
- Details-Tabelle mit Spezialität und Atmosphäre.
- Info-Panel zusätzlich mit Spezialität, Happy Hour und Raucherbereich.
- „Events in der Nähe“ bevorzugt Nightlife und Musik.
- „Ähnliche Kneipen“ als 4er-Grid.
- **Achtung:** Adresse, Öffnungszeiten und Telefon im Design sind Platzhalter.

---

## 2. Entscheidungen

**Beschlossen am 07.11.2026 durch den Auftraggeber** (gilt vor den Empfehlungen in der Tabelle darunter):

| Nr. | Entscheidung |
|---|---|
| E1 | Brauhäuser auch im Kneipen-Hub anzeigen (Empfehlung übernommen). |
| E2 | Keine Shisha-Bars. |
| E3 | Hotelbars aufnehmen. |
| E4 | Clubs gleich mitsuchen, aber **strikt getrennt** für den eigenen Club-Hub vorbereiten: eigener Zwischenspeicher, keine Vermischung mit dem Kneipen-Hub. |
| E5 | Google-Suche **sofort**, Kosten sind in Ordnung. |
| E6 | Happy Hour und Raucherbereich **nur mit Textbeleg**; eine manuelle Bestätigung ist **nicht** nötig. Ein belegter Wert darf angezeigt werden. |
| E7 | Mindest-Score 7. Wie bei den Restaurants **alle** Ergebnisse in die DB importieren; was im Frontend erscheint, filtern wir später. |
| E8 | Guides-Menü im Header **noch nicht** freischalten. |
| E9 | Beschreibungen von der KI schreiben lassen. |

Folgen für den Plan:
- E4: getrennte Zwischenspeicher-Dateien für `bars` und `clubs` (getrennte Suchläufe).
- E6: `bestaetigt` entfällt als Anzeige-Bedingung. Angezeigt wird, was eine Regel oder ein im Code geprüfter Textbeleg stützt.
- E7: Import mit `--min-score 1`.

**Ursprüngliche Empfehlungen** (zur Nachvollziehbarkeit):

| Nr. | Frage | Empfehlung |
|---|---|---|
| E1 | Brauhäuser und Gastropubs: Restaurant-Hub, Kneipen-Hub oder beide? | **Ein Ort, ein Haupt-Hub, eine Detail-URL.** Hausbrauereien und Brauhäuser → `typ = 'kneipe'`. Mit `extras.auch_restaurant = true` erscheinen sie **zusätzlich als Karte in der Restaurant-Liste**; die Karte verlinkt auf die Kneipen-URL (`ortPfad`). Keine zweite Detailroute, in der Sitemap nur einmal. Die 6 bestehenden Einträge (2 `brewpub`, 4 `gastropub`) einzeln entscheiden. |
| E2 | Shisha-Bars aufnehmen? | **Nein.** Aussortieren über Primärtyp `hookah_bar` **und** über `types` (eine Suche nach `bar` liefert Shisha-Bars mit). |
| E3 | Hotelbars aufnehmen? | **Ja**, wenn der Primärtyp ein Bar-Typ ist (`bar`, `cocktail_bar`, `wine_bar`, `lounge_bar`). Nicht über `excludedTypes: ["hotel"]` filtern: Hotelbars tragen oft beide Typen. |
| E4 | Clubs (`night_club`) gleich mitsuchen? | **Ja, nur in den Zwischenspeicher** (für den späteren Club-Hub 13), nicht importieren. |
| E5 | Wann die Google-Suche? | **Ab 01.12.2026** (Freikontingent je 1.000 Such- und Detail-Abrufe pro Monat). Im November ist es mit 1.111 Suchen schon aufgebraucht; sofort kostet es grob 20–40 $ (siehe 6). |
| E6 | Happy Hour und Raucherbereich | Google liefert beides nicht. Nur aus **wörtlich belegten** Stellen in Bewertungen oder Google-Zusammenfassung (Prüfung im Code, siehe 3.3). **Auf der Website nur, wenn manuell bestätigt.** Filter-Chips erst ab ≥ 8 bestätigten sichtbaren Orten. **Kein** „Raucherbereich außen“ aus `outdoorSeating`: ein Sitzplatz draußen ist kein Raucherbereich. |
| E7 | Mindest-Score für Sichtbarkeit | **7 wie bei Restaurants.** Bei weniger als 60 sichtbaren Orten für diesen Hub auf 6 senken. |
| E8 | Navigation (Guides im Header) jetzt freischalten? | Mit diesem zweiten Hub das Guides-Menü freischalten. |
| E9 | KI-Texte (Beschreibung, Highlight-Satz) | **Ja**, mit `claude-haiku`. Kosten ca. 1–2 $ für 400 Orte. Texte manuell prüfbar. |

---

## 3. Datengrundlage

### 3.1 Flächensuche „Bars“ (Google Places, Nearby Search)

**Hub-Parameter** in `scraper/orte/flaechensuche.py`, Standardwert `restaurants` = heutiges Verhalten unverändert:

- `--hub restaurants|bars` bestimmt:
  - die Datei des Zwischenspeichers (**vor** `speicher_laden()`; `restaurants` → `flaechensuche.json` wie bisher, `bars` → `flaechensuche_bars.json`, gitignored),
  - die Suchtypen,
  - die Typ-Zuordnung (`ort_typ`),
  - den Kandidatenfilter (`ist_kandidat`) und die Ausschlüsse.
- **Typ-Zuordnung Bars:** Bar-Primärtyp → `kneipe`, sonst `None`. `night_club` → nur Zwischenspeicher (E4), nicht Kandidat.
- **Kandidatenfilter Bars:**
  - Hotels nur ausschließen, wenn der Primärtyp kein Bar-Typ ist (E3).
  - Shisha-Bars nach Primärtyp und `types` ausschließen (E2).
  - Sonst wie Restaurants: geöffnet, Stadt Düsseldorf/Neuss/Ratingen, Mindest-Rating, Mindest-Bewertungen.
- **`ort_aus_place()` in `google_places.py`** bekommt den Hub bzw. eine erlaubte Ausnahme für Hotelbars, damit sie beim Import nicht ein zweites Mal herausfallen. `typ_verfeinern` (Imbiss-Regeln) ändert nur `restaurant` und lässt `kneipe` stehen.
- **Suchtypen Bars** (alle in Places Table A; mehrere in einem `includedTypes` sind erlaubt, Oder-Verknüpfung):
  - `bar`, `pub`, `irish_pub`, `brewpub`, `brewery`, `beer_garden`, `cocktail_bar`, `wine_bar`, `lounge_bar`, `sports_bar`
  - mit E4 zusätzlich `night_club`
  - **Nicht** `beer_hall`: kein gültiger Typ. Ein unbekannter Wert macht die ganze Anfrage zu HTTP 400, und `suchen` bricht nach der ersten Zelle ab.
- **Typ-Nachzug für volle Kleinstzellen:** Alle Bar-Typen teilen sich das Limit von 20 Treffern pro Anfrage. In dichten Vierteln (Altstadt) verdrängen bekannte Bars sonst Pubs und Biergärten. Die vorhandene Logik `--je-typ` / `_typ_nachzuege` (`flaechensuche.py:226-232`, `449-450`) für den Bar-Hub nutzen: volle Kleinstzellen einzeln je Typgruppe nachfragen (z.B. Kneipen-Typen | Bar-Typen | Biergarten).
- **Ketten-Erkennung** für Bars ergänzen (z.B. Sausalitos, Alex, Hard Rock Cafe, Irish-Pub-Ketten). Ketten-Score auf max. 3.
- **Kosten deckeln:** `--max-anfragen`, vorher `auswertung` (kostenlos).

### 3.2 Import mit Details

- `importieren --hub bars --min-score N` lädt Place Details (dieselbe Enterprise- und Atmosphere-Stufe wie bei Restaurants) und speichert mit `typ = 'kneipe'`, **`aktiv = false`**.
- **Zusätzliche boolesche Felder** (gleiche SKU, keine Mehrkosten): `servesBeer`, `servesWine`, `servesCocktails`, `goodForWatchingSports`, `liveMusic`, `goodForGroups`. `outdoorSeating` ist schon dabei.
- **Unterart** `extras.unterart`:
  - `pub`, `irish_pub`, `brewpub`, `brewery`, `beer_garden`, `sports_bar` → **kneipe**
  - `bar`, `cocktail_bar`, `wine_bar`, `lounge_bar` → **bar**
- **Dubletten:** Bekannte `google_place_id` werden heute still übersprungen (`flaechensuche.py:560-564`). Für den Bar-Hub stattdessen eine **E1-Liste ausgeben**: Name, heutiger Typ, Primärtyp, Score. Sie dient als Grundlage für die Entscheidung und eine spätere Umtypung.

### 3.3 Einordnung: Spezialitäten, Vibes, Happy Hour, Raucher

Erst feste Regeln aus Google-Signalen, dann KI für das, was Google nicht liefert. Alles in `extras`, mit Quelle.

| Merkmal | Regel (Google) | KI-Ergänzung |
|---|---|---|
| Spezialität **Cocktails** | `cocktail_bar` oder `servesCocktails` | Bestätigen oder verwerfen |
| **Wein** | `wine_bar` | Nur bei klarer Weinbar-Ausrichtung (`servesWine` fast überall wahr → kein Signal) |
| **Craft Beer** | `brewpub` | Nur mit Textbeleg |
| **Altbier** | Liste Düsseldorfer Hausbrauereien | Ausgesprochene Altbier-Kneipe, nur mit Textbeleg |
| **Whisky** | – | Nur mit Textbeleg |
| Vibe **Draußen sitzen** | `outdoorSeating` oder `beer_garden` | – |
| **Sportsbar** | `sports_bar` oder `goodForWatchingSports` | – |
| **Gesellig** | `goodForGroups`, `liveMusic` | Bestätigen |
| **Gemütlich** | – | Nur mit Textbeleg |
| **Happy Hour** | – | Nur mit Textbeleg (inkl. Uhrzeit) |
| **Raucherbereich** | – (kein Schluss aus `outdoorSeating`) | Nur mit Textbeleg („Raucherkneipe“, „hier darf geraucht werden“) |

**Textbeleg-Pflicht (im Code geprüft, nicht nur im Prompt):**
- Die KI liefert zu jeder Angabe aus Happy Hour, Raucher, Gemütlich, Craft Beer, Altbier und Whisky ein **wörtliches Zitat**.
- Der Code prüft, dass das Zitat (normalisiert: Groß-/Kleinschreibung, Leerraum) **wirklich in den Eingabetexten vorkommt**.
- Bei Happy Hour muss die angegebene Uhrzeit im Zitat stehen.
- Fehlt der Beleg, wird das Feld verworfen und protokolliert.

**Speicherformat (`extras`):**

- `unterart`: `"kneipe" | "bar"`
- `spezialitaeten`, `vibes`: Listen aus festen Werten
- `happy_hour`: `{ "text": "17–19 Uhr", "beleg": "…", "quelle": "ki" | "manuell", "bestaetigt": false }`
- `raucher`: `{ "wert": "innen" | "aussen", "beleg": "…", "quelle": "ki" | "manuell", "bestaetigt": false }`
- `ki_einordnung`: `{ "modell", "datum", "begruendung" }` (nur Kuration; **nicht** in `EXTRAS_FELDER`, ebenso `google_bewertungen`)

**KI-Schritt** in `scraper/orte/bars_einordnen.py`:
- wiederholbar, `--dry-run`
- festes JSON-Schema
- nur feste Werte
- nur Orte ohne `ki_einordnung`

### 3.4 Kuration und Freischaltung (Reihenfolge wichtig)

1. CSV zur Sichtprüfung (Name, Stadtteil, Unterart, Spezialitäten, Vibes, Happy Hour + Beleg, Raucher + Beleg, Score, Kette).
2. Korrekturen und Bestätigungen (`bestaetigt = true`) per Dashboard oder SQL.
3. **Erst danach** `aktiv = true` für Score ≥ Mindestwert (E7).
4. E1 umsetzen (Umtypung bzw. `auch_restaurant`) nach der E1-Liste aus 3.2.

**Optional:** Dashboard-Tab „Orte“ (Bestätigen und Korrigieren von Unterart, Spezialitäten, Vibes, Happy Hour, Raucher, aktiv). Auch für weitere Hubs nutzbar.

### 3.5 SQL

Keine nötig: `typ = 'kneipe'` ist erlaubt, `extras` ist JSONB.

---

## 4. Website

### 4.1 Bausteine (bewusst klein gehalten)

- **Keine** Generalisierung der Restaurant-Filter und **kein** Zerlegen der Restaurant-Detailseite in Slots. Beides würde den Restaurant-Hub ändern, ohne spätere Hubs (Spielplätze, Ausflüge, Trips mit ganz anderen Filtern) wirklich zu vereinheitlichen.
- **Gemeinsam genutzt bzw. herausgelöst:** Stadtteil-Chips, Zählen, Paging („Weitere laden“), Sticky-Leiste, `OrtKarte` mit optionalen Zusätzen (Typ-Label, Zusatzzeile, Badge, max. Chips).
- **Eigene Filterdatei** `lib/kneipen-filter.ts` für Kneipen & Bars, so angelegt, dass Clubs (Hub 13) sie später mitnutzen können.
- **Restaurant-Hub bleibt unverändert**, abgesehen von E1 (`auch_restaurant`-Karten). Prüfung:
  - Vitest vergleicht **Reihenfolge und Anzahl** der Restaurant-Liste bei Stichproben-Filtern vor und nach der Änderung (inkl. „Empfohlen“, das Imbisse nach hinten stellt, `guide-filter.ts:114-117`).
  - Gewollte Abweichungen durch E1 werden im Test ausdrücklich erwartet.

### 4.2 Hub `/guides/kneipen-bars`

**Übersicht** (`app/guides/kneipen-bars/page.tsx`):
- **Erste HTML-Antwort mit Inhalt:** Hero und die **ungefilterte** Liste (aus `orteLaden`, `"use cache"`) stehen **außerhalb** jeder Suspense-Grenze, also im statischen Shell. Nur die filterabhängige Leiste und die gefilterte Liste warten in `<Suspense>` auf `searchParams`.
- Hero dunkel (`.gd--abend`: Card-Border `#D9DEE7`, Gold `#9C8346`), Unterzeile mit echter Anzahl.
- **Filter:**
  - Stadtteil-Chips mit Anzahl
  - Spezialität und Vibe (Mehrfachauswahl, mit Anzahl)
  - Schalter Happy Hour und Raucherbereich (nur bei ≥ 8 bestätigten Orten, E6)
  - Sortierung Empfohlen / Bewertung / Neu
  - Status „N Ergebnisse“, „Filter zurücksetzen“
- Sticky-Leiste, 9 pro Seite, „Weitere N laden“, Leerzustand „Keine Bar mit diesen Filtern“.

**Card:**
- Typ-Label „KNEIPE“ / „BAR“
- Name, Spezialitäten-Zeile
- Stadtteil, Stern, Bewertungen
- Happy-Hour-Badge **nur bestätigt**
- Vibe-Chips (max. 2 bzw. 3)
- Preis-Badge

**Detail** (`app/guides/kneipen-bars/[slug]/page.tsx`, Aufbau wie die Restaurant-Detailseite: Name, Beschreibung, Adresse außerhalb der Suspense; Öffnungszeiten weiter mit `connection()`):
- Typ-Zeile „KNEIPE · ALTSTADT“.
- Highlight und Beschreibung.
- Details-Tabelle (Spezialität, Atmosphäre).
- Info-Panel: Adresse, Öffnungszeiten, Telefon, Website, Google-Maps-Link, Spezialität, Happy Hour und Raucherbereich **nur bestätigt**.
- Foto mit Attribution.
- **„Events in der Nähe“:** gleicher Stadtteil wie heute; Nightlife und Musik zuerst (`e.kategorie`), danach nach Datum. **Keine Entfernung** (Events haben keine Koordinaten).
- „Ähnliche Kneipen“ (4er-Grid: gleicher Stadtteil oder gleiche Spezialität).
- Antwortet für Orte anderen Typs mit 404 (wie die Restaurant-Seite).

**Daten:**
- `lib/orte.ts`: `EXTRAS_FELDER` um `unterart`, `spezialitaeten`, `vibes`, `happy_hour`, `raucher`, `auch_restaurant` erweitern.
- `DddOrt` bekommt typisierte, normalisierte Felder (nur feste Werte, Happy Hour und Raucher nur mit `bestaetigt`).

**E1 auf der Website:**
- Restaurant-Liste lädt zusätzlich Orte mit `auch_restaurant`; die Karte verlinkt über `ortPfad` auf die Kneipen-URL.
- Die `/guides`-Kachel zählt Kneipen **separat** (heute zählt sie nur Restaurant, Imbiss und Café, `app/guides/page.tsx:97`).

### 4.3 SEO und GEO (Lehren aus `docs/seo-geo-analyse-2026-11-06.md`)

- **Inhalt in der ersten HTML-Antwort:** siehe 4.2.
- **Canonical:** Hub-URL ohne Query, Detail-URL ohne Query.
- **`noindex, follow`** für **jede** URL mit Filter-, Sortier- oder `anzahl`-Parameter. Umsetzung über `generateMetadata`, das `searchParams` liest. Unter `cacheComponents` braucht das einen dynamischen Marker (`<Suspense>` plus `connection()`), sonst meldet der Build einen Fehler; vorher in der Next-16-Doku prüfen.
- **Open Graph** vollständig (`siteName`, `locale`, `type`, `url`); Vorschaubild = Ortsfoto bzw. Hub-Bild.
- **Alt-Texte:** Ortsname plus Stadtteil am Hauptbild, kurze Alt-Texte an Card-Bildern.
- **JSON-LD:**
  - `BarOrPub` mit `name`, Adresse, `geo`, Telefon, Website
  - `openingHoursSpecification` aus den strukturierten Google-Öffnungszeiten, **nicht** aus dem deutschen Freitext. Falls nur der Freitext gespeichert ist: beim Import zusätzlich die strukturierte Form speichern.
  - `BreadcrumbList`, auf der Übersicht `ItemList`
  - **Keine** `aggregateRating` aus Google-Daten.
- **Sitemap:** Übersicht und alle sichtbaren Detailseiten, jede URL **genau einmal** (über `ortPfad`). `/guides`-Kachel `fertig: true` mit echter Anzahl.

### 4.4 Tests

**Vitest:**
- Kneipen-Filterlogik
- Restaurant-Liste unverändert (**Reihenfolge** und Anzahl; E1 als gewollte Abweichung)
- Normalisierung der Extras (unbekannte Werte und unbestätigte Happy-Hour- bzw. Raucher-Angaben ausblenden)
- „Events in der Nähe“ (Stadtteil, Kategorie vor Datum)
- JSON-LD `BarOrPub` (Pflichtfelder, `OpeningHoursSpecification`, keine Bewertung)
- `noindex` bei Filter-URLs

**Python (`unittest`):**
- Hub-spezifische Typ-Zuordnung und Kandidatenfilter (Bars durch, Hotelbar durch, Shisha raus, Restaurant-Hub unverändert)
- Suchtypen ohne `beer_hall`
- Unterart, Spezialitäten- und Vibe-Regeln
- **Belegprüfung der KI-Antwort** (Zitat nicht im Eingabetext → Feld verworfen)
- Ketten-Erkennung
- E1-Liste

---

## 5. Ablauf und Meilensteine

| Schritt | Inhalt | Ergebnis | Freigabe nötig |
|---|---|---|---|
| 0 | Entscheidungen E1–E9 | Antworten | Auftraggeber |
| 1 | Pipeline: Hub-Parameter, eigene Zwischenspeicher-Datei, Bar-Typen, Kandidatenfilter, Hotel-/Shisha-Regeln, Typ-Nachzug, Ketten, E1-Liste; Tests | Code, `--dry-run` ohne Kosten | – |
| 2 | Flächensuche Bars (E5) | Zwischenspeicher, `auswertung` | Kosten-OK |
| 3 | Import mit Details | `orte` mit `typ = 'kneipe'`, `aktiv = false`, E1-Liste | Kosten-OK |
| 4 | Einordnung Regeln + KI mit Belegprüfung | `extras` befüllt, CSV | – |
| 5 | Sichtprüfung, Bestätigungen, **dann** Freischaltung, E1-Umtypung | sichtbare Orte | Auftraggeber prüft CSV |
| 6 | Website-Bausteine (klein, Restaurant-Hub unverändert) | Tests grün | – |
| 7 | Hub Kneipen & Bars (Übersicht, Detail, SEO) | live, noch ohne Navigation | Deploy-OK |
| 8 | Navigation und `/guides`-Kachel (E8), Cursor-Review, Live-Test | fertig | Deploy-OK |

Die Schritte 1 und 6 teilen sich keine Dateien und können parallel laufen. Die Website (6/7) lässt sich mit Beispieldaten aus dem Handoff entwickeln, bevor echte Daten da sind.

---

## 6. Kosten (Schätzung)

| Posten | Menge | Ab 01.12. (Freikontingent) | Sofort (November) |
|---|---|---|---|
| Nearby Search (eine Anfrage pro Zelle) | 300–600 | 0 $ | ca. 10–21 $ |
| Typ-Nachzug für volle Kleinstzellen | geschätzt +50–150 | 0 $ (wenn insgesamt < 1.000) | ca. 2–5 $ |
| Place Details (Enterprise + Atmosphere) | 300–450 | 0 $ | ca. 8–11 $ |
| KI-Einordnung (Haiku) | ca. 400 Orte | ca. 1–2 $ | ca. 1–2 $ |
| Fotos (laufend, je Seitenaufruf über `/ort-foto`) | abhängig vom Traffic | 1.000/Monat frei, danach ca. 7 $/1.000 | gleich |

`PREIS_SUCHE = 35`, `PREIS_DETAILS = 25` $ pro 1.000 (`flaechensuche.py:85-86`). Vor dem Livegang den Foto-Verbrauch prüfen und ggf. ein Budget-Limit in der Google Cloud Console setzen.

---

## 7. Risiken

- **Import bleibt leer:** wenn Kandidatenfilter, Typ-Zuordnung oder Hotel-Ausschluss nicht hub-spezifisch geöffnet werden (siehe 3.1). Abgesichert durch Tests und einen Dry-Run mit Zählung vor dem bezahlten Import.
- **Happy Hour und Raucher bleiben dünn:** gewollt, lieber leer als erfunden (E6, Belegpflicht, Bestätigung).
- **Altbier-Etikett zu breit:** nur Hausbrauereien und belegte Altbier-Kneipen; Sichtprüfung.
- **Überschneidung mit Restaurants:** E1 mit einer URL pro Ort und gewollter, getesteter Abweichung im Restaurant-Hub.
- **Seltene Bar-Typen fehlen in dichten Vierteln:** Typ-Nachzug.
- **Google-Kosten:** Deckel per `--max-anfragen` und `--max`, `auswertung` vor jedem bezahlten Schritt, Zeitpunkt E5.

## 8. Abnahmekriterien

- Übersicht und Detail entsprechen den Ansichten 18–21 (Desktop/Mobil); Filterkombinationen plausibel; Leerzustand funktioniert.
- **Der Import legt Bars wirklich an** (Zählung nach Import > 0, Stichprobe Uerige, Füchschen, Schumacher).
- Hotelbars nach E3 bleiben erhalten, Shisha-Bars nach E2 fehlen.
- Die Suchanfrage enthält nur gültige Places-Typen (kein `beer_hall`).
- Happy Hour und Raucherbereich erscheinen nur mit Textbeleg **und** Bestätigung; keine Design-Platzhalter auf der Website.
- **Jeder Ort hat genau eine Detail-URL**, und sie steht genau einmal in der Sitemap.
- Restaurant-Hub: Reihenfolge und Anzahl unverändert, abgesehen von den gewollten E1-Abweichungen.
- Im rohen HTML stehen Name, Beschreibung und Adresse (Detail) bzw. die ungefilterte Liste (Übersicht) außerhalb von `hidden`-Containern. Canonical, `noindex` bei Filter-URLs, Open Graph, `BarOrPub`-JSON-LD und Alt-Texte sind vorhanden.
- Google-Kosten wie geschätzt bzw. im Freikontingent.

---

## 9. Cursor-Review vom 07.11.2026 – eingearbeitet

| Befund | Bewertung | Wo eingearbeitet |
|---|---|---|
| `ist_kandidat` / `ort_typ` / Hotel-Ausschluss in `ort_aus_place` verwerfen Bars → Import leer (kritisch) | berechtigt, am Code bestätigt | 1, 3.1, 7, 8 |
| `beer_hall` kein gültiger Places-Typ → HTTP 400 | berechtigt | 3.1, 8 |
| Shisha-Bars kommen über `bar` mit | berechtigt | E2, 3.1 |
| Typ-Nachzug für volle Kleinstzellen fehlt | berechtigt | 3.1, 6 |
| Bekannte Place-IDs still übersprungen, keine E1-Liste | berechtigt | 3.2 |
| `raucher = außen` aus `outdoorSeating` falsch | berechtigt | E6, 3.3 |
| KI-Angaben ohne Belegprüfung im Code | berechtigt | 3.3, 4.4 |
| `aktiv` vor Sichtprüfung, Anzeige ohne `bestaetigt` | berechtigt | 3.4, 4.2 |
| E1: zweite Detail-URL, Sitemap, Kachelzahl | berechtigt | E1, 4.2, 4.3 |
| Prüfkriterium Restaurant-Hub muss Reihenfolge vergleichen (Imbiss-Sortierung) | berechtigt | 4.1, 4.4 |
| Übersicht: ungefilterte Liste außerhalb der `searchParams`-Suspense | berechtigt | 4.2 |
| `noindex` für alle Filterparameter, dynamischer Marker nötig | berechtigt | 4.3 |
| Events haben keine Koordinaten → keine Entfernung | berechtigt, am Code bestätigt | 1, 4.2 |
| Zweite Filterdatei statt Generalisierung, kein Slot-Umbau | übernommen | 4.1 |
| `OpeningHoursSpecification` statt Freitext, `name` im JSON-LD | übernommen | 4.3 |
