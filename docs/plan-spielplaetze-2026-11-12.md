# Plan: Guide „Spielplätze“ (`/guides/spielplaetze`)

Stand 12.11.2026 · Entwurf zur Gegenprüfung (Cursor) · noch nichts umgesetzt

Ziel: Eltern finden schnell den passenden Spielplatz – nach Alter des Kindes, Ausstattung, Stadtteil und Nähe –
mit ehrlichen, belegten Angaben. Gleiche Qualitätsregeln wie bei Restaurants, Kneipen und Clubs: nur belegte Daten,
eine URL pro Ort, erste HTML-Antwort mit Inhalt, SEO-/GEO-Texte, Deploy nur mit OK, SQL führt der Auftraggeber aus.

---

## 1. Ausgangslage (geprüft am 12.11.2026)

### 1.1 Daten, die es schon gibt
| Quelle | Inhalt | Lizenz | Bewertung |
|---|---|---|---|
| **Stadt Düsseldorf, Open Data** „Notfallnummern auf städtischen Spielplätzen“ (Garten-, Friedhofs- und Forstamt), CSV/GeoJSON (WGS84 + ETRS89)/KML, aktualisiert 11.11.2026 | **433 Anlagen** mit Punktkoordinaten: 322 Kinderspielplätze, 20 Waldkinderspielplätze, 9 Wasserspielplätze, 71 Bolzplätze, 5 Waldbolzplätze, 3 Skateranlagen, 3 Freizeitanlagen. Felder: `objektbezeichnung` (z. B. „HOFGARTEN, Ksp Oederallee“), `strasse_hausnr` (oft leer), `stadtbezirk` (1–10), `objektart`, `groesse` (m²), `4stellige_nr` (Notfallnummer), `objektschluessel` | Portal: **Datenlizenz Deutschland – Zero 2.0** (dl-de/zero-2-0). Achtung: der NRW-Spiegel (ckan.open.nrw) zeigt „Andere geschlossene Lizenz“ → vor dem Import klären (s. Risiken) | Rückgrat des Guides: vollständig, amtlich, kostenlos. **Keine** Ausstattung, kein Alter, keine Fotos. 413 Leerzeilen in der Datei (beim Import verwerfen) |
| **OpenStreetMap** `leisure=playground` | Teilweise Ausstattung (`playground=swing/slide/sandpit/climbingframe/zipwire/water…`), `min_age`/`max_age`, `surface`, `wheelchair`, Name | ODbL – Namensnennung „© OpenStreetMap-Mitwirkende“ (haben wir an der Karte schon) | Ergänzung für Ausstattung. Abdeckung in Düsseldorf noch prüfen (Overpass war beim Test überlastet) |
| **Google Places** (Typ `playground`) | Bewertung, Anzahl Bewertungen, Fotos, teils Öffnungszeiten | Google-Bedingungen, Fotos nur über API mit Urhebernennung | Für „Beliebtheit“ und Fotos; viele kleine Plätze fehlen bei Google. Kostet Geld |
| Neuss: Liste aller Kinderspielplätze (PDF, Stand 11/2023) und NRW-Datensatz „Stadt Neuss: Kinderspielplätze“ (kuratierte Auswahl) | Namen/Standorte | prüfen | Für C3 (Neuss) |
| Ratingen | keine offenen Geodaten gefunden | – | nur OSM/Google |

### 1.2 Website – vorhanden und wiederverwendbar
- Typ `spielplatz` ist in der Tabelle `orte` (CHECK-Constraint) und in `OrtTyp` schon vorgesehen.
- Kachel „Spielplätze“ auf `/guides` (noch `fertig: false`), Text „In Arbeit …“ in den Guide-FAQs.
- Bausteine aus den anderen Hubs: Karte (MapLibre + eigene PMTiles, `GuideKarteLazy`, `/api/guide-karte`), Filter-Chips (`gd-zeile`),
  Guide-Stadtteilseiten (`/guides/{hub}/stadtteil/{slug}`), `GuideEinleitung`/`GuideSeoText` mit 5 FAQs, Proxy-Prüfung
  (`pfad-pruefung.ts`), Sitemap, IndexNow, Foto-Proxy `/ort-foto/[slug]` inkl. `foto_manuell`.
- Event-Kategorie „Familie“ für „Familien-Events in der Nähe“.

### 1.3 Design (Handoff `design_v2/ddd_handoff_v2/14_spielplaetze`, Ansichten 23 + 25)
- Hell und freundlich (Hero `#FFF6E6`), **Karte ist die Hauptansicht** (Grid 55/45 Karte/Liste, mobil Karte oben).
- Altersgruppen 0–3 / 3–6 / 6–12 / alle mit festen Farben; Ausstattung (Sandkasten, Schaukel, Rutsche, Kletterwand,
  Wasserspiel, Seilbahn) mit UND-Filter; Extras Schatten / WC / eingezäunt / Picknick; Sortierung „In der Nähe“ (Geolocation)
  und „Beste Ausstattung“.
- Detail: Alters-Badge, Ausstattung vorhanden/fehlt, Extras ja/nein/teilweise, Mini-Karte, „Route planen“,
  „In der Nähe“ (weitere Spielplätze, Cafés, Familien-Events).
- Eigene SVG-Icons nötig für Schaukel, Rutsche, Sandkasten (keine passenden Material-Icons).

---

## 2. Entscheidungen (vom Auftraggeber zu treffen – Vorschlag fett)

| Nr. | Frage | Vorschlag |
|---|---|---|
| **S1** | Welche Anlagen? | **Kinderspielplätze, Waldspielplätze, Wasserspielplätze** der Stadt. Bolzplätze/Skateranlagen erst später (eigener Filter „Bolzen & Skaten“), Indoor-Spielplätze (kommerziell) **nicht** in diesem Hub |
| **S2** | Alle zeigen oder nur Empfehlungen? | **Alle Spielplätze mit Koordinaten zeigen** (die Karte lebt von Vollständigkeit), dazu eine sichtbare Stufe **„Top-Spielplatz“** (wie bei Clubs, aber ohne Erklärung der Einteilung). Detailseiten indexierbar nur mit genug Inhalt (s. 4.4) |
| **S3** | Gebiet | **Düsseldorf zuerst**; Neuss/Ratingen in Phase 2, wenn die Datenlage es trägt |
| **S4** | Woher kommen Ausstattung und Alter? | **Kombination**: OSM-Tags → belegtes KI-Profil aus öffentlichen Quellen (Stadt, Presse, Spielplatz-Portale; nur Fakten mit Zitat, wie bei Clubs) → später Meldungen von Nutzern („Angabe falsch / ergänzen“). Was nicht belegt ist, heißt „noch keine Angaben“ – nie „fehlt“ |
| **S5** | Fotos | **Nur Fotos ohne erkennbare Kinder** (Persönlichkeitsrechte, Kinder sind auf Spielplatzfotos fast immer drauf). Google-Fotos nur nach Sichtprüfung (wie Club-Fotos, `foto_manuell`), sonst freundliches Illustrations-Motiv je Typ (Wald/Wasser/Spielplatz). **Kein Street View** (Kosten, oft unbrauchbar) |
| **S6** | Notfallnummer anzeigen? | **Ja**, auf der Detailseite als Infozeile: „Notfallnummer 9601 – bei einem Notruf (112) angeben“. Echter Mehrwert für Eltern, amtliche Angabe |
| **S7** | Standardansicht | **Karte** (laut Design), Liste daneben; „Grid“-Ansicht nicht nötig |
| **S8** | Geolocation „In der Nähe“ | **Nur auf Klick**, nur im Browser berechnet, nichts gespeichert oder gesendet; ohne Freigabe Fallback Stadtmitte |
| **S9** | Budget Google + KI | **bis ca. 40 $** für den Erstaufbau (Details s. Abschnitt 7) |

---

## 3. Datengrundlage und Pipeline

Neues Paket `scraper/spielplaetze/` (Muster wie `scraper/orte/clubs*.py`), alles mit `--dry-run`, Logs auf Deutsch,
Rate-Limit ≥ 2 s für Websites, robots.txt beachten.

### 3.1 Import Stadt (`stadt_import.py`)
1. GeoJSON (WGS84) laden, Leerzeilen verwerfen, nach S1 filtern (`objektart` 336, 536, 337).
2. **Name normalisieren**: „HOFGARTEN, Ksp Oederallee“ → „Spielplatz Hofgarten (Oederallee)“, „Wsp“ → Wasserspielplatz,
   „Waldksp“ → Waldspielplatz; Großschreibung, Apostrophe („SPEE`SCHER GRABEN“). Regeln als reine Funktion mit Tests;
   unklare Namen in eine CSV zur Sichtprüfung.
3. **Stadtteil per Punkt-in-Polygon** mit den offiziellen Stadtteilgrenzen (Open Data Düsseldorf, dl-de/zero) – neue
   reine Funktion `stadtteil_aus_koordinate()`, Abgleich mit unseren kanonischen Stadtteilnamen (`ortsnamen`/`stadtteile.ts`).
4. **Adresse**: `strasse_hausnr`, sonst Reverse-Geocoding nur bei Bedarf (Nominatim, 1 req/s, eigener User-Agent ohne
   persönliche Daten) oder „nahe <Straße aus dem Namen>“.
5. Speichern in `orte`: `typ='spielplatz'`, `aktiv=false` (Freischaltung nach Sichtprüfung), `slug` = Name + Stadtteil,
   `latitude/longitude`, `extras.spielplatz = { quelle:'stadt', objektschluessel, notfallnummer, objektart, groesse_m2, stadtbezirk }`.
   Eindeutigkeit über `objektschluessel` (wiederholbarer Import, ändert nur Stadtfelder).

### 3.2 OSM-Abgleich (`osm_abgleich.py`)
- Overpass-Abfrage `leisure=playground` im Stadtgebiet (einmal, Zwischenspeicher `data/spielplaetze/osm.json`, gitignored).
- Zuordnung Stadt ↔ OSM über Distanz (≤ 60 m, Fläche enthält Punkt) – Mehrdeutigkeiten in die Prüf-CSV.
- Übernehmen: `playground=*` (auch `playground:*`-Unterobjekte im Umkreis), `min_age`/`max_age`, `surface`, `wheelchair`,
  `fee`, `lit`, `access`. Mapping auf unsere Ausstattungsliste (Tabelle im Code, getestet).

### 3.3 Google (optional, `google_abgleich.py`)
- Nur für Plätze ab z. B. 1.500 m² und Wasser-/Waldspielplätze (die „Ausflugsziele“), Nearby Search Typ `playground`
  im Umkreis 80 m um die Koordinate → Bewertung, Anzahl, Foto-Kandidaten. Kein Flächengitter über die ganze Stadt.
- Fotos: Kandidaten wie bei den Clubs sichten, **nur ohne Kinder**; Auswahl per SQL mit `foto_manuell`.

### 3.4 Profil (`profil.py`, KI + Websuche, wie Club-Profil)
- Für Top-Kandidaten (Wasser-/Wald-/große Spielplätze, Google-Bewertungen) Quellen suchen: duesseldorf.de, Pressemitteilungen
  (Neugestaltungen nennen oft Geräte und Altersgruppe), Bezirksvertretungs-Vorlagen, Spielplatz-Portale (nur Fakten, nichts kopieren).
- Ergebnis je Platz: `ausstattung[]`, `altersgruppe` (0–3/3–6/6–12/alle), `extras` (schatten/wc/eingezaeunt/picknick, je ja/nein/teilweise
  + Notiz), `beschreibung` (eigene Worte, 2–4 Sätze), `highlight`. **Jede Angabe mit wörtlichem Beleg** (Code prüft wie bei Clubs),
  `stand` = Datum der Quelle (Spielplätze werden umgebaut!).
- Altersgruppe ohne Beleg: aus der Ausstattung **ableiten** (Sandkasten/Babyschaukel/Federwippe → 0–3 bzw. 3–6; Kletterturm/Seilbahn → 6–12;
  beides → „alle“) und als „abgeleitet“ markieren; im Text „geeignet vor allem für …“.

### 3.5 Spielplatz-Score (intern, für Sortierung und „Top-Spielplatz“)
Nicht als Note anzeigen (Abmahnrisiko, siehe Club-Score) – höchstens „Top-Spielplatz“-Badge.
- Ausstattung (Anzahl belegter Geräte, Vielfalt) 35 %
- Größe (m² aus Stadtdaten) 20 %
- Besonderheit (Wasser, Wald, Thema, Inklusion/rollstuhlgerecht) 20 %
- Beliebtheit (Google, Bayes-Mittel; ohne Google neutral) 15 %
- Extras (WC, Schatten, Picknick in der Nähe) 10 %

### 3.6 Kuration und Freischaltung
CSV zur Sichtprüfung (Name, Stadtteil, Typ, Größe, Ausstattung + Belege, Altersgruppe, Score, Foto) →
`--freigeben`/`--freischalten` wie bei Clubs. Unpassende Einträge (Schulhof, nicht öffentlich, abgerissen) über eine
Ausschlussliste `NICHT_IM_HUB` mit Grund.

### 3.7 Aktualisierung
- Stadtdaten monatlich (Datei ändert sich, z. B. neue Notfallnummern) – Diff-Protokoll, keine Löschung ohne Prüfung.
- OSM vierteljährlich; Profile nur bei Hinweis/Umbau neu.

---

## 4. Website

### 4.1 Daten- und Logikschicht
- `web/lib/spielplaetze.ts`: Profil aus `extras.spielplatz` lesen (nur bekannte Werte), Altersgruppen/Ausstattung/Extras
  als Konstanten (Farben aus dem Handoff), Filter lesen/schreiben (`alter`, `geraet` (UND), `extra`, `stadtteil`, `sort`),
  Sortierung „Beste Ausstattung“/„In der Nähe“ (Haversine im Browser), `istSichtbarerSpielplatz`.
- `web/lib/spielplaetze-daten.ts`: Laden mit `"use cache"` (wie `clubOrteLaden`, paginiert).

### 4.2 Hub `/guides/spielplaetze` (Ansicht 23)
- Heller Hero mit Zahl aus den Daten, darunter **Einleitung** (2–3 Sätze, `GuideEinleitung`).
- Filter: Altersgruppe (groß, Einzelauswahl, Farbpunkte), Ausstattung (UND), Extras (Schalter), Stadtteil, Sortierung.
- **Karte + Liste** (Karte Standard): Pins in Altersfarbe, Legende, Hover-Puls, „Mein Standort“ (nur auf Klick, S8).
  Kartenpunkte über `/api/guide-karte?hub=spielplaetze` (erste HTML-Antwort bleibt klein); darunter `OrtLinkListe` für Crawler.
- Liste mit kompakten Cards (Thumb 80×80, Alters-Badge, Ausstattungs-Icons mit `title`, Schatten/WC/Zaun).
- Unten **SEO-Text + 5 FAQs** (FAQPage-JSON-LD), eigene Texte (z. B. „Wo gibt es Wasserspielplätze in Düsseldorf?“,
  „Welcher Spielplatz eignet sich für Kleinkinder?“, „Gibt es Spielplätze mit Toilette?“, „Was bedeutet die Notfallnummer
  am Spielplatz?“, „Wo finde ich Waldspielplätze?“).
- Filter-URLs `noindex, follow`, Canonical auf den Hub (wie die anderen Hubs).

### 4.3 Detail `/guides/spielplaetze/[slug]` (Ansicht 25)
- Brotkrumen, Bild (oder Typ-Illustration), H1, Stadtteil + Adresse, Alters-Badge, Beschreibung.
- **Ausstattung**: vorhanden (grün) – **nicht belegt** (neutral „keine Angabe“ statt rot „fehlt“, Lehre aus dem Club-Score);
  „fehlt“ in Rot nur bei belegter Abwesenheit.
- Extras mit Ja/Nein/Teilweise + Notiz, **Notfallnummer** (S6), Größe („ca. 3.800 m²“), „Stand der Angaben: …“, Quellen.
- Rechts sticky: Mini-Karte, Adresse, „Route planen“ (Google-Maps-Link ohne API), „In der Nähe“.
- **In der Nähe**: 3 weitere Spielplätze (Haversine), 2 Cafés aus dem Restaurant-Guide (Typ café, Haversine ≤ 1 km),
  3 Familien-Events (Kategorie Familie, gleicher Stadtteil/Nachbarstadtteile – Events haben keine Koordinaten).
- JSON-LD `Playground` (schema.org, CivicStructure) mit `geo`, `address`, `isAccessibleForFree: true`, BreadcrumbList.
  Kein `aggregateRating` aus Google.

### 4.4 Indexierung
- Hub und Guide-Stadtteilseiten (`/guides/spielplaetze/stadtteil/{slug}`, ab 5 Spielplätzen) indexierbar.
- Detailseiten indexierbar nur mit **eigenem Inhalt** (Beschreibung + mind. 2 belegte Ausstattungsmerkmale oder Typ
  Wasser/Wald); sonst `noindex, follow` und nicht in der Sitemap (sonst Hunderte dünne Seiten → Qualitätssignal leidet).
- Proxy (`pfad-pruefung.ts`): Hub `spielplaetze` in `routeVon`/`ortEntscheidung`, 404 für unbekannte/inaktive Slugs.
- Sitemap, IndexNow (einmalige Meldung nach Livegang), `llms.txt`, `/guides`-Kachel `fertig: true`, Footer-Link,
  Guide-Übersichtstext und FAQ „Welche Guides kommen noch dazu?“ anpassen.

### 4.5 Barrierefreiheit und Mobil
Farbpunkte immer mit Text (nicht nur Farbe), Icons mit Label/`title`, Karte mit Liste als Alternative,
Touch-Ziele ≥ 44 px, kein horizontales Scrollen bei 375 px.

### 4.6 Tests
- Python: Namensnormalisierung, Stadtteil aus Koordinate, OSM-Mapping, Belegprüfung, Score, Altersableitung.
- Web (vitest): Filter (UND-Logik, „alle“ passt zu jedem Alter), Sortierung/Haversine, Sichtbarkeit/Indexierbarkeit,
  JSON-LD, Pfadentscheidungen, Texte (5 FAQs, nur interne Links, keine Score-Erklärung).

---

## 5. Ablauf und Meilensteine

| Schritt | Inhalt | Ergebnis / Freigabe |
|---|---|---|
| 0 | Entscheidungen S1–S9, Lizenzfrage Stadtdaten klären | Freigabe Auftraggeber |
| 1 | Stadt-Import + Namen + Stadtteile (inaktiv) | SQL/Import, Prüf-CSV „Namen & Stadtteile“ |
| 2 | OSM-Abgleich | Abdeckungsbericht: wie viele Plätze haben Ausstattung aus OSM? |
| 3 | Google-Abgleich (nur Auswahl) + Foto-Sichtung | Kosten vorher nennen, Foto-SQL |
| 4 | KI-Profile für Top-Kandidaten (Probelauf 10 → Bericht → Rest) | Probe-Bericht zum Gegenlesen |
| 5 | Score, Sichtprüfung, Freischaltung | Freigabe-CSV |
| 6 | Website (Hub, Detail, Karte, Filter, Stadtteilseiten, Texte) | Cursor-Check |
| 7 | Tests, Build, Browser-Prüfung (Desktop/Mobil, hell/dunkel) | Deploy nur mit OK |
| 8 | IndexNow, Sitemap-Kontrolle, Bing/Google | Bericht |

---

## 6. SEO/GEO-Chancen
- Suchanfragen mit klarer Absicht: „Spielplatz Düsseldorf“, „Wasserspielplatz Düsseldorf“, „Waldspielplatz Düsseldorf“,
  „Spielplatz Kleinkinder Düsseldorf“, „Spielplatz <Stadtteil>“, „Spielplatz mit Toilette Düsseldorf“.
- Eigene Stadtteilseiten je Viertel; interne Links aus Familien-Events (Event-Seite „Vorher oder nachher“) und aus
  Café-Seiten („Spielplatz in der Nähe“).
- FAQ-Antworten in kurzen, zitierfähigen Sätzen (KI-Suchen).

## 7. Kosten (Schätzung)
| Posten | Menge | Kosten |
|---|---|---|
| Stadt-Open-Data, OSM, Nominatim | – | 0 $ |
| Google Nearby (Umkreis je Platz, nur Auswahl ~120) | ~120 × 0,032 $ | ~4 $ |
| Google Fotos zur Sichtung (~60 Plätze × 10) | ~600 × 0,007 $ | ~4 $ |
| KI-Profile (Claude + Websuche, ~150 Top-Kandidaten) | 150 × 0,05–0,10 $ | 8–15 $ |
| **Summe** | | **ca. 16–25 $** (Puffer bis 40 $, S9) |

## 8. Risiken
- **Lizenz der Stadtdaten**: Portal sagt dl-de/zero-2-0, NRW-Spiegel „geschlossene Lizenz“ → vor Import beim
  Open-Data-Team bestätigen lassen bzw. Portalangabe dokumentieren.
- **Kinder auf Fotos** (Persönlichkeitsrecht) → strikte Foto-Regel S5.
- **Veraltete Ausstattung** (Umbauten, gesperrte Geräte) → „Stand der Angaben“, Meldefunktion, keine Gewähr-Hinweis.
- **Dünne Detailseiten** → Indexierungsregel 4.4.
- **Falsche Stadtteile** bei Grenzlagen → Punkt-in-Polygon statt Adress-Raten; Prüf-CSV.
- **Overpass-Auslastung** → Zwischenspeicher, Wiederholung mit Pause.
- **„Fehlt“-Darstellung** als Tatsachenbehauptung → nur bei belegter Abwesenheit.
- Bewertungen als Note → kein öffentlicher Score (nur „Top-Spielplatz“).

## 9. Abnahmekriterien
- Mindestens 300 Düsseldorfer Spielplätze auf der Karte, korrekt im Stadtteil.
- Mindestens 60 Spielplätze mit belegter Ausstattung und Altersgruppe; alle Wasser- und Waldspielplätze mit Profil.
- Keine Fotos mit erkennbaren Kindern; jedes Foto mit Urheber.
- Hub, Detail, Stadtteilseiten: erste HTML-Antwort mit Inhalt, Canonical/noindex-Regeln wie oben, JSON-LD valide.
- Filter (Alter, Ausstattung UND, Extras, Stadtteil, Nähe) funktionieren in Karte und Liste, mobil ohne horizontales Scrollen.
- Tests grün, Cursor-Check ohne kritische/mittlere Befunde, Deploy nach OK.

## 10. Offene Fragen an Cursor (Gegenprüfung)
1. Reicht dl-de/zero-2-0 laut Portal, oder muss der Widerspruch zum NRW-Spiegel vorher geklärt sein?
2. Ist die Indexierungsregel für Detailseiten (4.4) streng genug / zu streng?
3. Punkt-in-Polygon: eigene Implementierung (Shapely ist nicht installiert – keine neue Bibliothek ohne Freigabe) vs. Ray-Casting
   in reinem Python – genügt das für ~350 Punkte?
4. ODbL: Ist die Übernahme einzelner OSM-Tags in unsere Datenbank und die Anzeige als „Produced Work“ mit Namensnennung ausreichend?
5. Fehlt eine Datenquelle (z. B. Abenteuer-/Bauspielplätze der Jugendhilfe, die nicht beim Gartenamt geführt werden)?
