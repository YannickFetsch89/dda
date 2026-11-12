# Plan: Guide „Spielplätze“ (`/guides/spielplaetze`)

Stand 12.11.2026 · **konsolidierte Fassung** nach zwei Cursor-Prüfungen und zwei eigenen Durchsichten · noch nichts umgesetzt.
Diese Fassung ersetzt alle früheren Abschnitte (0, 0.3 usw.); die Prüfhistorie steht in Abschnitt 14.

**Ziel:** Eltern finden den passenden öffentlichen Spielplatz in Düsseldorf – nach Alter, Ausstattung, Stadtteil und Nähe.
Gleiche Regeln wie bei den anderen Guides: nur belegte Angaben, eine URL pro Ort, Inhalt in der ersten HTML-Antwort,
SEO-Text mit fünf FAQs, keine öffentliche Score-Zahl, Deploy nur nach OK, Datenbank-Freischaltungen per SQL durch den Auftraggeber.

---

## 1. Geprüfte Fakten (Daten und Code, Stand 12.11.2026)

### 1.1 Spielplatzdatei der Stadt
Open Data Düsseldorf, Datensatz „Notfallnummern auf städtischen Spielplätzen“, Lizenz laut Stadtportal **Datenlizenz
Deutschland – Zero – Version 2.0** (kommerzielle Nutzung erlaubt; der NRW-Spiegel zeigt fälschlich „geschlossene Lizenz“ –
maßgeblich ist das Stadtportal). Dateistand der Ressourcen **25.09.2020** (HTTP Last-Modified), Intervall laut Portal jährlich.

- **Nur** `…/Spielplätze mit Notfallnummern WGS84.geojson` verwenden. 846 Features, davon 413 ohne Geometrie/Eigenschaften
  (verwerfen) und 433 Punkte. Die CSV ist unbrauchbar (Koordinaten durch Tausenderpunkte zerstört), `xkoord`/`ykoord` im GeoJSON ebenso –
  **einzige Koordinate ist `geometry.coordinates`**.
- `objektart` ist Text: `336 Kinderspielplatz` (322), `536 Waldkinderspielplatz` (20), `337 Wasserspielplatz` (9) → **351 Einträge
  im Hub**. Nicht im Hub: `338 Bolzplatz` (71), `538 Waldbolzplatz` (5), `335 Skateranlage` (3), `333 Freizeitanlage` (3).
- `groesse` ist Text mit Komma (`664,1`); `stadtbezirk` ist bei allen 20 Waldspielplätzen leer; `strasse_hausnr` fehlt bei 78 der 351.
- `4stellige_nr` (Notfallnummer) bei allen 351 vorhanden; **7 Nummern verteilen sich auf 15 Einträge**. Alle Gruppen liegen am selben
  Punkt, nur Hanielpark 127 m auseinander. Es sind **Teilflächen eines Spielplatzes** (z. B. „SAN-REMO-STR., KSP Kleinkinder“ +
  „… Schulkinder“, „AUF' M ROTT, WSP“ + „… KSP“, „GRAFENTAL, Naturpark Flingern“ ×3). Zusätzlich teilen sich 35 Kinderspielplätze
  die Nummer mit einem Bolzplatz (nicht im Hub, irrelevant).
- 33 Hub-Einträge beginnen mit „GW“ (Bedeutung unbekannt, Auftraggeber: weglassen), alle mit Komma.

### 1.2 Weitere Datenquellen
| Quelle | Inhalt | Lizenz | Nutzung |
|---|---|---|---|
| „Stadtteilgrenzen Düsseldorf 2025“, **nur** `Stadtteile_2025_WGS84_EPSG4326_1.geojson` | 50 MultiPolygone, Felder `Name`, `Nummer` (z. B. `033` Hafen; Bezirk = Zahl der ersten zwei Stellen) | dl-de/zero-2.0 | Stadtteil per Punkt-in-Polygon. Die ETRS89-Datei (EPSG:4647, Meter) **nicht** verwenden |
| „Adressliste Düsseldorf“ | Straße, Hausnummer, Stadtteil, PLZ – **keine Koordinaten** | dl-de/zero-2.0 | **Nicht** für Adressen nutzbar. Fehlende Adressen bleiben leer |
| OpenStreetMap `leisure=playground` | Geräte (`playground=*`), `min_age`/`max_age`, `surface`, `wheelchair`, `fee`, `access` | ODbL | Nur Eigenschaften. Abdeckung in Düsseldorf noch unbekannt (Overpass beim Test überlastet) → Schritt 2 misst sie |
| Google Places, Typ `playground` | Bewertung, Fotos | Google-Bedingungen | Nur Auswahl (Abschnitt 4.4), intern + Foto-Kandidaten |
| Abenteuer-/Bauspielplätze (Jugendhilfe) | nicht in der Gartenamt-Datei | – | kurze manuelle Liste mit öffentlicher Quelle (Abschnitt 4.6) |
| Neuss, Ratingen | PDF 2023 bzw. keine offenen Daten | – | nicht in dieser Runde |

### 1.3 Code-Stand (was heute fehlt)
- `web/lib/pfad-pruefung.ts`: `OrtHub`/`HUBS` kennen `spielplaetze` nicht; `routeVon("/guides/spielplaetze/…")` → `null`
  (festgehalten in `seo-a1.test.ts`, `seo-b.test.ts`); `ortEntscheidung` verlangt `HUB_TYPEN` + `qualitaets_score ≥ 7`.
- `web/lib/orte.ts`: `orteLaden`/`ortLaden` verlangen `qualitaets_score ≥ 7`; die Spaltenliste lädt `extras` nur feldweise
  (kein `extras.spielplatz`).
- `/ort-foto/[slug]`: findet nur Orte über `ortLaden` (Score ≥ 7) oder Clubs.
- `web/app/sitemap.ts`: Detail-URLs nur aus `orteLaden`, Kneipen, Clubs. Stadtteilseiten über `GUIDE_HUBS`/`hubOrte`.
- `web/lib/landing.ts` `GUIDE_HUBS` / `GuideHub`; `web/lib/guide-stadtteile.ts` `hubOrte` (Fallback ist `clubsLaden()`!),
  `zaehltFuerIndex` (für Nicht-Club-Hubs schon „jeder sichtbare Ort“ – so lassen).
- `web/components/guide-stadtteil.tsx`: zeigt Restaurant-Karten (`OrtKartenGrid`) bzw. Club-Karten.
- `/api/guide-karte`: unbekannter Hub → 400; `kartenOrte` hängt Google-Sterne an.
- Event-Seite „Vorher oder nachher“ hängt Guide-Stadtteil-Links aller `GUIDE_HUBS` an jedes Event.
- Weitere Einbaustellen: `GUIDE_LINKS` (`components/client.tsx`), Mobil-/Popover-Menü (`components/rahmen.tsx`), Footer,
  `EXTRA_LINKS` der Kategorie-Seite (`app/kategorie/[slug]/page.tsx`), `/guides`-Kachel (`fertig: false`), FAQ „Welche Guides
  kommen noch dazu?“ (`lib/guide-texte.ts`), `public/llms.txt` (Abschnitt „Guides: Essen und Ausgehen“), Datenschutz-Absatz zu Google Maps.

### 1.4 Design
Handoff lokal außerhalb des Repos: `C:\Claude_DDD\design_v2\ddd_handoff_v2\14_spielplaetze\` (`README.md`, `data/spielplaetze.json`),
ergänzend `DESIGN_PROMPTS_GUIDES.md` Abschnitt 10 (Repo). **Abweichungen vom Handoff (verbindlich):**
1. MapLibre + eigene PMTiles statt Leaflet/OSM-Kacheln.
2. Anrede ihr/euch; Hero-Zahl aus den Daten (nicht „230“); kein Hero-Foto mit Kindern.
3. **Kein stiller Sprung auf die Stadtmitte** ohne Standortfreigabe (Handoff Z. 16) – siehe E8.
4. **Kein graues Kreuz für „WC nein“ ohne Beleg** (Handoff Z. 26): unbekannte Extras bekommen keine Kachel; Rot/„nein“ nur bei belegter Abwesenheit.
5. Unbekanntes Alter: neutraler Pin, nicht die Farbe von „alle“.

---

## 2. Entscheidungen (alle getroffen)

| Nr. | Entscheidung |
|---|---|
| E1 | Im Hub: Kinder-, Wald- und Wasserspielplätze der Stadt (351 Einträge → **343 Spielplätze** nach Zusammenführung, 4.1). Keine Bolz-, Skater-, Freizeit-, Indoor- oder kommerziellen Anlagen. Die Einleitung sagt das. |
| E2 | Alle Spielplätze aus E1 mit gültiger Koordinate kommen auf die Karte. Freischaltung nach Stichprobe der Prüf-CSV, nicht Einzel-Freigabe. Ausschlussliste `NICHT_IM_HUB` (mit Grund) nur für: nicht öffentlich, Dublette, nachweislich abgebaut, unauflösbarer Name. |
| E3 | Nur Düsseldorf. Neuss/Ratingen später. |
| E4 | Ausstattung nur belegt (OSM-Tag oder wörtliches Zitat). Ohne Beleg „keine Angabe“, nie „fehlt“; „fehlt/nein“ nur bei belegter Abwesenheit. |
| E5 | Alter: **belegt** (OSM `min_age`/`max_age`, Zitat, Stadtname „Kleinkind/Schulkind“) oder **vermutlich** (aus belegten Geräten abgeleitet, Regel 4.5). Vermutlich zählt für Filter und Pin-Farbe, wird überall als „vermutlich“ gekennzeichnet und zählt **nicht** für die Indexierung. |
| E6 | Fotos: keine erkennbaren Kinder/Personen. Google-Fotos nur nach Sichtprüfung (`foto_manuell`), sonst Typ-Illustration (Abschnitt 11). Kein Street View. |
| E7 | Notfallnummer als Hinweis, kein `tel:`-Link (Regel 4.1, Wortlaut 6.3). |
| E8 | „In der Nähe“ nur nach Klick, nur im Browser (Haversine), nichts gespeichert oder gesendet, kein URL-Parameter. Ohne Freigabe bleibt die Standardsortierung, ein Satz erklärt es. |
| E9 | Karte ist Standard, Liste daneben; keine Grid-Ansicht. |
| E10 | „GW“-Präfix entfällt im Anzeigenamen. |
| E11 | Filter „Rollstuhlgerecht“ ab 5 sichtbaren Plätzen mit Beleg (`wheelchair=yes` oder Zitat); `limited` nur auf der Detailseite („teilweise“). Dieselbe Schwelle (5) für jeden Geräte-Chip. |
| E12 | Typ-Illustrationen erzeugt der Auftraggeber (Prompts Abschnitt 11). |
| E13 | Datenschutz-Satz freigegeben (Wortlaut 6.4). |
| E14 | Budget Google + KI bis 40 $; konkrete Kosten vor jedem Google-Lauf nennen. |
| E15 | Score nur intern (`extras.spielplatz.score`), **nie** in `qualitaets_score`; öffentlich höchstens Badge „Top-Spielplatz“. |
| E16 | Link „Spielplätze {inStadtteil}“ auf Event-Seiten **nur bei Kategorie Familie** (andere Hubs bleiben wie bisher). |

---

## 3. Datenmodell

Tabelle `orte` (Typ `spielplatz` ist im CHECK-Constraint schon erlaubt):
- Spalten: `typ='spielplatz'`, `name` (Anzeigename), `slug`, `stadtteil` (Katalogwert, 4.2), `adresse` (nur `strasse_hausnr` +
  „Düsseldorf“, sonst `NULL`), `latitude`/`longitude` (Stadt), `aktiv`, `qualitaets_score = NULL`, `bild_url = NULL`,
  `bild_attribution` (nur bei freigegebenem Foto).
- `extras.spielplatz`:
  ```
  { quelle: "stadt-duesseldorf", lizenz: "dl-de/zero-2.0", quelle_url, datenstand: "2020-09-25",
    teile: [{ objektschluessel, stadt_name, objektart, groesse_m2 }],   // 1–3 Teilflächen (4.1)
    typ: "kinder" | "wald" | "wasser",
    notfallnummer: "9601" | null,  groesse_m2,  stadtbezirk_stadt: 1–10 | null,
    ausstattung: { <geraet>: { wert: "ja"|"nein", quelle: "osm"|"zitat"|"stadt", beleg?, url? } },
    alter: { wert: "0-3"|"3-6"|"6-12"|"alle", art: "belegt"|"vermutlich", beleg? } | null,
    extras: { schatten|wc|eingezaeunt|picknick|rollstuhl: { wert: "ja"|"nein"|"teilweise", notiz?, quelle, beleg? } },
    beschreibung?, highlight?, profil_stand?, saison?: { text, beleg, url },
    osm: { id, tags_stand }, google: { place_id, rating, anzahl } (intern), score, top: bool }
  ```
- `extras.foto_manuell`, `extras.google_foto`, `extras.foto_version` wie bei den Clubs.
- `NICHT_IM_HUB` als Konstante im Skript (Name → Grund), wie bei den Clubs.
- Identität für Wiederholungsimporte: sortierte Liste der `objektschluessel` der Teilflächen.

---

## 4. Pipeline `scraper/spielplaetze/` (Python, Logs Deutsch, `--dry-run`, keine neue Bibliothek)

### 4.1 Stadt-Import (`stadt_import.py`)
1. GeoJSON WGS84 laden; Features ohne Geometrie verwerfen; Filter über den **Text** der Objektart (E1).
2. Koordinate nur aus `geometry`; jeder Punkt muss in 6,6–7,0 °O / 51,1–51,4 °N liegen, sonst **Abbruch** (falsche Datei/Projektion).
3. **Zusammenführung:** Einträge mit gleicher Notfallnummer, die alle ≤ 150 m auseinanderliegen, sind **ein** Spielplatz
   (Koordinate = die der größten Teilfläche, Größe = Summe, Typ = Wasser vor Wald vor Kinder, Teilflächen in `teile`).
   Ergebnis 351 → 343. Gleiche Nummer > 150 m: nicht zusammenführen, Nummer bei beiden unterdrücken (`notfallnummer = null`),
   Plätze behalten, Prüf-CSV. Vergleich nur innerhalb des Hubs (Bolzplätze zählen nicht).
4. **Name** (reine, getestete Funktion): „GW “-Präfix weg (E10); Teil vor dem Komma = Ort/Park, danach Zusatz.
   `Ksp/KSP` → Spielplatz, `Wsp/WSP` → Wasserspielplatz, `Waldksp` → Waldspielplatz; Schreibweise normalisieren
   („HOFGARTEN“ → „Hofgarten“, „SPEE`SCHER GRABEN“ → „Spee'scher Graben“, „Str.“ → „straße“ nur bei eindeutigem Wortende).
   Muster: „Spielplatz Hofgarten (Oederallee)“, „Wasserspielplatz Volksgarten“. Bei zusammengeführten Teilflächen ohne
   Zusatz den gemeinsamen Teil („Spielplatz San-Remo-Straße“), Teilflächen auf der Detailseite nennen („Bereich für Kleinkinder
   und für Schulkinder“). Abkürzungen, die sich nicht sicher auflösen lassen („Fritz./Mörsenb.“, „a.d.“), → Prüf-CSV, Platz
   bleibt **inaktiv**, bis dort ein Anzeigename steht. Typ immer aus `objektart`, nie aus dem Namen.
5. **Stadtteil** per Ray-Casting gegen jedes Teilpolygon der WGS84-Stadtteildatei (keine Löcher vorhanden; Code kann sie trotzdem).
   Katalog-Mapping: „Flingern Nord“ → `Flingern-Nord`, „Flingern Süd“ → `Flingern-Süd`, sonst Name 1:1; `Hafen` bleibt
   Datenbankwert (Anzeige „Medienhafen“ über die bestehende Logik). Kein Treffer → Prüf-CSV, Platz inaktiv.
   **Kontrolle Bezirk:** Bezirk = `int(Nummer[:2])`; nur ein **gesetzter**, abweichender `stadtbezirk` der Spielplatzdatei kommt
   in die Prüf-CSV, leer ist kein Widerspruch (Polygon gewinnt).
6. **Adresse** nur aus `strasse_hausnr`; sonst leer. Kein Geocoding, keine Adressliste. „Route planen“ aus der Koordinate.
7. **Slug** = Anzeigename + Stadtteil (bestehende Slug-Funktion), Kollision → `slug_mit_suffix`. **Slugs werden vor der
   Freischaltung festgezogen** und danach nicht mehr geändert (Namensänderungen ändern nur `name`).
8. Schreiben über das Skript (wie der Club-Import), alle Zeilen `aktiv=false`, `extras.spielplatz.quelle` gesetzt
   (Rücknahme: `DELETE … WHERE typ='spielplatz' AND extras->'spielplatz'->>'quelle'='stadt-duesseldorf'`).
   Wiederholter Import ändert nur Stadtfelder (`extras_mergen`), nie Profil, Foto, Name nach Freigabe oder `aktiv`.
9. Ausgabe: `data/spielplaetze/pruefung.csv` (Name alt/neu, Stadtteil, Bezirk-Abweichung, zusammengeführt, Nummer unterdrückt,
   GW, unklare Abkürzung, keine Adresse) und Zusammenfassung im Log.

### 4.2 OSM-Abgleich (`osm_abgleich.py`)
- Eine Overpass-Abfrage `nwr[leisure=playground]` + Geräte-Objekte `playground=*` im Stadtgebiet, generischer User-Agent,
  Wiederholung mit Pause, Zwischenspeicher `data/spielplaetze/osm.json` (gitignored, nie veröffentlicht).
- Zuordnung: Stadt-Punkt liegt in der OSM-Fläche **oder** OSM-Mittelpunkt ≤ 60 m; mehrere Kandidaten → Prüf-CSV, nichts übernehmen.
- Übernahme mit `quelle: "osm"`: Geräte (Mapping-Tabelle, 4.5), `min_age`/`max_age`, `wheelchair`, `fee`, `access`
  (`access=private` → Prüf-CSV, Kandidat für `NICHT_IM_HUB`).
- **Bericht:** Anteil der Plätze mit ≥ 1 / ≥ 2 OSM-Geräten. OSM-Plätze ohne Stadt-Treffer nur auflisten (nicht anlegen) – Kandidaten
  für neuere Plätze und Abenteuerspielplätze.

### 4.3 Profil (`profil.py`, KI + Websuche, wie Club-Profil)
- **Runde 1 (109 Plätze):** alle Wasser (9) + Wald (20) + Kinderspielplätze ≥ 3.000 m² (86), Überschneidungen 6.
  Erst **Probe mit 10**, Bericht zum Gegenlesen, dann der Rest. Runde 2 (85 Plätze 1.500–3.000 m²) nur nach Bericht und Freigabe.
- Quellen: duesseldorf.de, Pressemitteilungen der Stadt, Vorlagen der Bezirksvertretungen, lokale Presse; Spielplatz-Portale nur als
  Fakt mit Zitat. robots.txt, ≥ 2 s Pause, keine Rausgegangen-Seiten.
- Ergebnis je Platz: Geräte, Extras (inkl. Rollstuhl), Alter, `saison` (nur Wasser, nur mit Beleg), Beschreibung 2–4 eigene Sätze,
  Highlight, `profil_stand` = Datum der jüngsten Quelle. **Jede Aussage mit wörtlichem Beleg**, Prüfung wie bei den Clubs
  (Wortstamm/Zahl im Zitat). Eine Schablone aus Stadtfeldern („Spielplatz X in Y, Z m²“) ist keine Beschreibung.
- Widerspruch OSM ↔ Zitat: jüngere Quelle gewinnt, beide in der Prüf-CSV.

### 4.4 Google (`google_abgleich.py`, nur Runde-1-Plätze)
- Umkreissuche 80 m, Typ `playground`, über den vorhandenen Places-Client; Treffer nur bei Namensähnlichkeit oder einzigem Treffer,
  sonst Prüf-CSV. Bewertung nur intern (Score). Foto-Kandidaten → Sichtung (nur ohne erkennbare Personen) → SQL mit `foto_manuell`.
- Kosten vorher nennen (E14); Schätzung Abschnitt 9.

### 4.5 Regeln (reine Funktionen, getestet)
- **Geräte-Mapping OSM → Liste:** `sandpit`→Sandkasten, `swing`/`basketswing`/`baby_swing`→Schaukel, `slide`→Rutsche,
  `climbingwall`/`climbingframe`/`climbing_net`→Klettern, `water`/`pump`/`splash_pad`→Wasserspiel, `zipwire`→Seilbahn;
  weitere (`springy`, `seesaw`, `roundabout`, `balancebeam`) als Nebengeräte (Detailseite, kein Filter).
- **Alter vermutlich:** nur Sandkasten/Federwippe/Babyschaukel → „0-3“; Sandkasten/Rutsche/Schaukel ohne Klettern/Seilbahn → „3-6“;
  Klettern oder Seilbahn ohne Kleinkindgeräte → „6-12“; Kleinkind- **und** Großkind-Geräte → „alle“; < 2 belegte Geräte → kein Alter.
- **Score (intern):** Ausstattung 35 %, Größe 20 %, Besonderheit (Wasser, Wald, Inklusion) 20 %, Google 15 % (fehlend = neutral),
  Extras 10 %. „Top-Spielplatz“ = oberstes Fünftel **und** indexierbar (5.4).

### 4.6 Abenteuer-/Bauspielplätze
Manuelle Liste (Name, Träger, Adresse, Koordinate aus OSM oder vom Auftraggeber bestätigt, Quelle-URL) vor dem Livegang,
nur öffentlich belegte, öffentlich zugängliche Anlagen; eigener Typ-Text „betreuter Abenteuerspielplatz – Öffnungszeiten beachten“.
Blockiert den Import der städtischen Plätze nicht.

### 4.7 Aktualisierung
Stadtdatei jährlich prüfen (Last-Modified). Bei neuem Stand: Diff; fehlende Objektschlüssel → `stadt_fehlt_seit` + Prüf-CSV,
nicht sofort deaktivieren. OSM halbjährlich neu abgleichen (nur `quelle: "osm"`-Felder). Profile nur bei Hinweis/Umbau.

---

## 5. Website

### 5.1 Daten und Logik
- `web/lib/spielplaetze-daten.ts`: eigene Abfrage (`"use cache"`, seitenweise), `typ='spielplatz'`, `aktiv=true`,
  **mit** `extras` (nicht die Spaltenliste aus `orte.ts`), **ohne** Score-Schwelle.
- `web/lib/spielplaetze.ts`: Profil nur aus bekannten Werten lesen; Konstanten (Altersfarben/Labels aus dem Handoff, Geräte, Extras);
  Filter `alter` (Einzelauswahl; „alle“ passt zu jedem Alter; unbekannt nur bei „Alle Alter“), `geraet` (UND, nur „ja“),
  `extra` (UND), `stadtteil` (Mehrfach, ODER), `sort` (`empfohlen` = Score, dann Name; `ausstattung` = Anzahl belegter Geräte);
  `istIndexierbar` (5.4); Chip-Schwelle 5 (E11). „In der Nähe“ ist kein URL-Parameter.
- `GuideHub`/`GUIDE_HUBS` um `spielplaetze` erweitern (Name „Spielplätze“, Mehrzahl „Spielplätze“, Icon `toys`);
  `hubOrte("spielplaetze")` → Spielplätze laden (expliziter Zweig, kein Fallback auf Clubs).

### 5.2 Hub `/guides/spielplaetze` (`instant = false`)
- Heller Hero (Tokens mit Dark-Variante), H1 „Spielplätze in Düsseldorf“, Zahl aus den Daten, Brotkrumen Start / Düsseldorf entdecken /
  Spielplätze. Darunter **Einleitung** (2–3 Sätze inkl. „nur öffentliche städtische Spielplätze“).
- Filter: Alter (groß, Farbpunkt + Text), Ausstattung, Extras inkl. Rollstuhl (E11), Stadtteil, Sortierung; „In der Nähe“-Knopf (E8).
  Leere Ergebnisse erklären: „Die Ausstattung ist noch nicht für alle Spielplätze erfasst.“ Sichtbarer Hinweis über der Liste:
  „Ausstattung für X von Y Spielplätzen erfasst“.
- **Karte (Standard) + Liste:** Punkte über `/api/guide-karte?hub=spielplaetze` mit **eigener** Punktfunktion: id, Name, Typ, Alter
  (+ „vermutlich“), Stadtteil, Koordinate, URL, Thumb – **keine Bewertung, keine OSM-Tags**. Pins in Altersfarbe, unbekannt neutral,
  Legende mit Text, gewählter Pin mit hellem Ring auf dunkler Karte, Hover-Puls.
- Unter der Karte `OrtLinkListe` mit **allen** Spielplätzen (Parameter `max` erhöhen), damit alle Links im ersten HTML stehen.
- Unten `GuideSeoText` mit fünf FAQs (6.2). **Kein** Block „… nach Stadtteil“ unten (wie Clubs/Kneipen).
- Filter-URLs `noindex, follow`, Canonical `/guides/spielplaetze`. JSON-LD BreadcrumbList + ItemList (nur indexierbare, max. 30).
- Fuß: „Kartendaten und Ausstattung teils © OpenStreetMap-Mitwirkende · Spielplatzdaten: Landeshauptstadt Düsseldorf (dl-de/zero-2.0)“.

### 5.3 Detail `/guides/spielplaetze/[slug]` (`instant = false`)
- Brotkrumen bis zum Namen; Bild (freigegebenes Foto mit Urheber) oder Typ-Illustration; H1; Stadtteil (Anzeige wie überall,
  „Medienhafen“); Adresse falls vorhanden; Alters-Badge (+ „vermutlich“).
- Beschreibung (nur aus Profil); Teilflächen („Bereich für Kleinkinder und für Schulkinder“); Ausstattung: ja (grün) / keine Angabe
  (neutral) / nein (rot, nur belegt); Extras mit Notiz; Größe „ca. 1.200 m² laut Stadt“; Saison-Hinweis bei Wasser; **Notfallnummer** (6.3);
  „Stand der Angaben“, Quellen, OSM-Namensnennung, Haftungssatz (6.5).
- Rechts: Mini-Karte, „Route planen“ (Google-Maps-Link aus der Koordinate, öffnet erst nach Klick), „In der Nähe“-Anker.
- „In der Nähe“: (1) „Weitere Spielplätze in {Park}“ bei Teilflächen desselben Parks/Namensstamms, sonst die 3 nächsten;
  (2) bis zu 2 Cafés aus dem Restaurant-Guide (Typ Café, ≤ 1 km, kanonische URL) – Block entfällt, wenn keins;
  (3) „Familien-Events {inStadtteil}“ (Kategorie Familie, gleicher Stadtteil; Events haben keine Koordinate).
- JSON-LD `Playground` mit `geo`, `address` (falls vorhanden), `isAccessibleForFree` nur ohne OSM `fee=yes`; kein `aggregateRating`;
  BreadcrumbList aus derselben Kette wie die sichtbaren Brotkrumen.
- Title/Description: „{Name} – Spielplatz {inStadtteil}“, Description aus Profil, sonst „{Typ} {inStadtteil}: Lage, Größe, Notfallnummer“.

### 5.4 Indexierung
- Hub indexierbar.
- **Detail indexierbar nur mit** Profil-Beschreibung **und** ≥ 2 belegten Geräten (vermutetes Alter zählt nicht; Typ Wasser/Wald allein
  reicht nicht). Sonst `noindex, follow`, ohne Canonical, nicht in der Sitemap, aber erreichbar und in Hub/Liste verlinkt.
- **Stadtteilseiten** `/guides/spielplaetze/stadtteil/{slug}` ab 5 sichtbaren Spielplätzen (dünne zählen mit; `zaehltFuerIndex`-Default).
  Eigene schmale Spielplatz-Karte in `guide-stadtteil.tsx` (Name, Typ, Alter, Größe) statt Restaurant-Karte; ItemList-URL = Spielplatz-URL.
- **Sitemap:** eigene Liste indexierbarer Detailseiten, `lastModified` aus `aktualisiert_am`; Stadtteilseiten über `GUIDE_HUBS`.

### 5.5 Proxy, Foto-Proxy, Karten-API
- `pfad-pruefung.ts`: `OrtHub`/`HUBS` + `spielplaetze`; `ortEntscheidung("spielplaetze")`: sichtbar = `aktiv && typ === "spielplatz"`,
  **ohne** Score; unbekannt/inaktiv → direkte 404 im Proxy. Tests in `seo-a1`/`seo-b` von `null` auf die neue Entscheidung umstellen.
  `OrtKopf` lädt dafür `typ`, `aktiv` (vorhanden).
- `/ort-foto/[slug]`: aktiver Spielplatz auch ohne `qualitaets_score` (eigener Zweig, wie Clubs).
- `/api/guide-karte`: Zweig `hub=spielplaetze` mit eigener Punktfunktion (5.2).

### 5.6 Einbaustellen außerhalb des Hubs
`/guides`-Kachel `fertig: true` (Zahl aus den Daten), `GUIDE_LINKS`, Popover-/Mobilmenü, Footer (Spalte Guides), `EXTRA_LINKS.familie`
= „Spielplätze“, Event-Seite (E16, Linktext `Spielplätze ${inStadtteil(st)}`), `/stadtteil/[slug]` (automatisch über `GUIDE_HUBS`),
`llms.txt` (Abschnitt umbenennen in „Guides“ + Spielplätze-Zeile), Guide-Übersichtstext + FAQ „Welche Guides kommen noch dazu?“
(neue Antwort: „Neu ist der Spielplatz-Guide … in Arbeit sind Ausflüge und Wochenend-Trips“), Datenschutz (6.4).

### 5.7 Design, Barrierefreiheit, Mobil
Altersfarben aus dem Handoff mit Text; eigene Outline-SVGs für Schaukel, Rutsche, Sandkasten (2 px, 24er Raster, mit Label);
Icons mit `title`; Touch-Ziele ≥ 44 px; 375 px ohne horizontales Scrollen; Liste als Alternative zur Karte; hell und dunkel geprüft.

---

## 6. Texte

### 6.1 Einleitung (Hub, Entwurf zur Freigabe)
„Hier findet ihr {anzahl} öffentliche Spielplätze in Düsseldorf – vom kleinen Sandkasten im Viertel bis zum Wasser- und
Waldspielplatz. Filtert nach Alter, Ausstattung und Stadtteil oder lasst euch zeigen, was in eurer Nähe liegt. Bolzplätze,
Skateanlagen und Indoor-Spielplätze sind nicht dabei.“

### 6.2 Fünf FAQs (Entwurf, Antworten mit internen Links, Texte vor dem Livegang zur Freigabe)
1. „Wo gibt es Wasserspielplätze in Düsseldorf?“ (inkl. Saison-Hinweis – keine sechste FAQ)
2. „Welcher Spielplatz eignet sich für Kleinkinder?“
3. „Wo finde ich Waldspielplätze?“
4. „Was bedeutet die Nummer auf dem Spielplatzschild?“
5. „Gibt es rollstuhlgerechte Spielplätze?“ (nur wenn E11 greift; sonst „Welche Spielplätze haben eine Toilette in der Nähe?“)

### 6.3 Notfallnummer (Detailseite)
„**Notfallnummer 9601** – das ist keine Telefonnummer. Im Notfall die 112 wählen und diese Nummer nennen; sie steht auch auf dem
Schild am Spielplatz.“ Quelle: Stadt Düsseldorf. Fehlt die Nummer (4.1 Schritt 3), entfällt die Zeile.

### 6.4 Datenschutz (freigegeben, korrigierter Wortlaut)
In `/datenschutz` neuer Punkt:
> **Standortfunktion im Spielplatz-Guide.** Wenn Sie im Spielplatz-Guide auf „In der Nähe“ tippen, fragt Ihr Browser, ob die
> Website Ihren Standort verwenden darf. Nur wenn Sie zustimmen, berechnet Ihr Browser auf Ihrem Gerät die Entfernung zu den
> Spielplätzen. Die Website erhält Ihren Standort dabei nicht und speichert ihn nicht. Die Freigabe können Sie jederzeit in den
> Einstellungen Ihres Browsers widerrufen.

Zusätzlich im bestehenden Google-Maps-Absatz: „… und der Knopf ‚Route planen‘ im Spielplatz-Guide …“ ergänzen.

### 6.5 Haftung (Fuß der Detailseite)
„Angaben ohne Gewähr, Stand {profil_stand bzw. Datenstand der Stadt}. Geräte können umgebaut oder gesperrt sein.“

---

## 7. Tests

**Python:** WGS84-Pflicht/Koordinaten-Rechteck (Abbruch), Objektart-Text, Komma-Größe, Leerzeilen; Zusammenführung (9777 ×3 am selben
Punkt → 1; Hanielpark 127 m → 1; konstruierter Fall > 150 m → 2 Plätze, Nummer unterdrückt; Bolzplatz mit gleicher Nummer zählt nicht);
Namen (GW mit Komma, Ksp/Wsp/Waldksp, Apostroph, „Str.“, unauflösbare Abkürzung → inaktiv); Ray-Casting (MultiPolygon, Loch, Rand);
Flingern Nord/Süd-Mapping; Bezirk aus `Nummer[:2]` (leer = kein Fehler, abweichend = Prüf-CSV); Adresse bleibt leer ohne `strasse_hausnr`;
OSM-Mapping; Alter vermutlich (alle Regeln, < 2 Geräte → keins); Belegprüfung; Score; Top-Badge nur bei indexierbar.

**Web (vitest):** Filter (UND, „alle“, unbekanntes Alter, Chip-Schwelle 4/5, Rollstuhl `limited` zählt nicht), Sichtbarkeit ohne
Qualitäts-Score, `istIndexierbar`, Karten-Punkte ohne Bewertung/OSM-Tags, JSON-LD ohne `aggregateRating`, `isAccessibleForFree`,
Pfadentscheidungen (neue Fälle statt `null`), Sitemap-Liste, Event-Link nur bei Familie mit `inStadtteil`, Saison-Hinweis nur bei Wasser
mit Beleg, Notfallnummer-Zeile entfällt ohne Nummer, Texte (5 FAQs, nur interne Links, keine Score-Zahl, ihr/euch).

---

## 8. Ablauf und Freigaben

| Schritt | Inhalt | Freigabe / Ergebnis |
|---|---|---|
| 1 | Stadt-Import (inaktiv), Prüf-CSV | Auftraggeber sichtet CSV (Namen, Abkürzungen, Grenzfälle) |
| 2 | OSM-Abgleich + Bericht (Abdeckung) | Entscheidung, ob Runde 2 der Profile nötig ist |
| 3 | Abenteuer-Liste | Auftraggeber bestätigt |
| 4 | Google Runde 1 (Kosten vorher) + Foto-Sichtung | Foto-SQL |
| 5 | Profile: Probe 10 → Bericht → Rest Runde 1 | Gegenlesen |
| 6 | Score, Top-Badge, Freischaltungs-SQL (`aktiv=true`, Slugs fest) | Auftraggeber führt SQL aus |
| 7 | Website, Texte (6.1/6.2 zur Freigabe), Illustrationen eingebaut | Cursor-Check |
| 8 | Tests, Build, Browser (Desktop/Mobil, hell/dunkel) | Deploy nur nach OK |
| 9 | IndexNow (Hub, Stadtteilseiten, indexierbare Details), Sitemap-Kontrolle | Bericht |
| 10 | Nach 4 Wochen: Suchanfragen (Bing/Google) auswerten, FAQ nachschärfen | Bericht |

Nicht in dieser Runde: Meldefunktion für Nutzer, Neuss/Ratingen, Bolzplätze/Skaten, Indoor-Spielplätze, Clustering der Karte.

## 9. Kosten (Schätzung, vor dem Lauf konkret nennen)
Stadt, Stadtteilgrenzen, OSM: 0 $. Google Runde 1: Umkreissuche 109 × Places-Satz (grob 2–4 $) + Foto-Sichtung (≈ 60 Plätze × 10 Fotos,
grob 4 $). Profile: 109 × 0,05–0,10 $ ≈ 6–11 $. **Gesamt ≈ 12–19 $**, Runde 2 (85 Plätze) zusätzlich ≈ 5–9 $. Rahmen E14: 40 $.

## 10. Risiken und Gegenmaßnahmen
| Risiko | Gegenmaßnahme |
|---|---|
| Stadtdaten von 2020, neuere Plätze fehlen | OSM-only-Liste, Abenteuer-Liste, „Datenstand“ sichtbar |
| OSM-Abdeckung gering → kaum Geräte | Bericht in Schritt 2; Profile Runde 2; ehrliche „X von Y erfasst“-Anzeige |
| Viele „keine Angabe“ wirken leer | Chip-Schwelle 5, Hinweis über der Liste, Illustrationen, Detailseiten noindex |
| Falsche Notruf-Info | Zusammenführung + Unterdrückung bei > 150 m, Wortlaut 6.3, Quelle |
| Kinder auf Fotos | nur Sichtprüfung, sonst Illustration |
| Falscher Stadtteil | Punkt-in-Polygon mit Prüf-CSV |
| Name falsch aufgelöst | Prüf-CSV, unklare Plätze inaktiv |
| Slug-Änderung nach Livegang | Slugs vor Freischaltung fest |
| Abmahnrisiko durch Wertungen | keine Score-Zahl, „nein“ nur belegt, Haftungssatz |
| ODbL | Nur Eigenschaften, Namensnennung, Rohdaten/Karten-API ohne OSM-Tags |

## 11. Bild-Prompts (Auftraggeber erzeugt, WebP nach `web/public/guides/`)
Gemeinsam: **keine Personen, keine Kinder, keine Gesichter, keine Schrift, keine Logos/Marken**; fotorealistisch wie die übrigen
Guide-Bilder; helles, natürliches Licht, warmer Ton passend zu `#FFF6E6`; **keine dunkle Vignette**.

| Datei | Format | Prompt |
|---|---|---|
| `spielplaetze.webp` (Hero: Bild rechts 46 %, Maske nach links in `#FFF6E6`; mobil Überschrift unten) | 16:9, ≥ 1600 × 900 | *Bright, airy photo of an empty public playground in a leafy Düsseldorf city park on a sunny morning. The main subject – a wooden climbing tower with a slide – sits in the right third of the frame. The left half and the bottom quarter are calm and light: soft pale sky, light lawn and gentle out-of-focus greenery, suitable for overlaying dark navy text. No people, no children, no faces, no text, no logos, no dark vignette, photorealistic, natural warm light.* |
| `spielplatz-typ-kinder.webp` | 4:3, ≥ 1200 × 900 | *One single bright red playground slide, centred, photographed from the front so it is still recognisable as a small square thumbnail, with a soft sandpit and green bushes blurred behind it, sunny afternoon, light background, no people, no children, no text, no logos, photorealistic.* |
| `spielplatz-typ-wald.webp` | 4:3, ≥ 1200 × 900 | *One single natural wooden climbing structure made of raw tree trunks, centred in the frame, in a light beech forest with dappled sunlight, light and friendly mood, simple uncluttered background, no people, no children, no text, no logos, photorealistic.* |
| `spielplatz-typ-wasser.webp` | 4:3, ≥ 1200 × 900 | *One single hand water pump with sparkling water flowing into a small wooden channel, centred in the frame, sunny summer day, bright sand and green trees softly blurred behind, no people, no children, no text, no logos, photorealistic.* |

Prüfung vor dem Einbau: keine Person (auch nicht im Hintergrund), keine Schrift; Motiv als 80 × 80-Quadrat erkennbar; Hero-Text
links/unten lesbar (hell und dunkel).

## 12. Abnahmekriterien
- 343 Spielplätze (bzw. Zahl nach Ausschlüssen) korrekt importiert; Stichprobe von 30: Name, Stadtteil, Notfallnummer stimmen.
- Alle Wasser- und Waldspielplätze mit Profil; ≥ 60 Plätze mit ≥ 2 belegten Geräten und Altersangabe (belegt oder vermutlich).
- Keine Fotos mit Personen; jedes Foto mit Urheber; Illustrationen eingebaut.
- Hub, Detail, Stadtteilseiten: Inhalt im ersten HTML; Index-/Canonical-Regeln wie 5.4; JSON-LD valide, ohne Bewertungen; Proxy 404 für
  unbekannte Slugs; Karten-API ohne Bewertung/OSM-Tags.
- Filter/Karte/„In der Nähe“ funktionieren (Desktop, 375 px, hell/dunkel); Datenschutz- und Footer-/Menü-Links ergänzt.
- Alle Tests grün; Cursor-Check ohne kritische/mittlere Befunde; Deploy nach OK; IndexNow gemeldet.

## 13. Offene Punkte
Keine offenen Entscheidungen. Texte 6.1/6.2 und die Abenteuer-Liste werden vor dem Livegang zur Freigabe vorgelegt.

## 14. Prüfhistorie
- Entwurf 12.11. → Cursor-Prüfung 1: Dateistand 2020, Objektart als Text, Koordinaten nur aus `geometry`, Score nicht in
  `qualitaets_score`, Foto-Proxy, Proxy-Route, `instant = false`, Indexregel, Abenteuerspielplätze, kein stiller Standort-Fallback.
- Zweite Durchsicht (Claude): Stadtteilgrenzen-Datensatz, Notfallnummer-Dubletten, Parks, GW, Saison, Icons, Illustrationen, Dark Mode,
  Datenschutz, Event-Links, Haftung, Erfolgsmessung.
- Cursor-Prüfung 2: Adressliste ohne Koordinaten (→ keine „nahe“-Adresse), nur WGS84-Stadtteildatei, Proxy-Zweig ohne Score,
  Notfallnummer-Statistik, Bezirk aus `Nummer[:2]`, Google-Umfang 109, eigene Sitemap-Liste, eigene Karten-Punkte, Event-Link nur
  Familie mit `inStadtteil`, Handoff-Abweichungen (Stadtmitte, WC-Kreuz), Datenschutz-Wortlaut + Maps-Absatz, Tests, Bild-Prompts,
  weitere Einbaustellen, `extras` laden.
- Konsolidierung (Claude, 12.11.): Dubletten sind Teilflächen → **Zusammenführung 351 → 343**; vermutetes Alter für Filter/Pin;
  Chip-Schwelle 5; Slugs vor Freischaltung fest; Rücknahme-Weg; Datenmodell; Titel/Description-Muster; Hinweis „X von Y erfasst“;
  `OrtLinkListe` mit allen; kein Stadtteil-Block unten; Quellen-Fuß; Ablauf mit Freigaben; Abnahme-Stichprobe.
