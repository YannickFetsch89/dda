# Plan: Guide „Spielplätze“ (`/guides/spielplaetze`)

Stand 13.11.2026 · **konsolidierte Fassung** nach acht Cursor-Prüfungen und acht eigenen Durchsichten · **vom Auftraggeber freigegeben am 13.11.2026**, ergänzt um Tischtennis und `ausstattung.csv` (13.11.) · noch nichts umgesetzt.
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
- `4stellige_nr` (Notfallnummer) bei allen 351 vorhanden; **7 Nummern verteilen sich auf 15 Einträge**. Sechs Gruppen liegen auf
  demselben Punkt (San-Remo-Straße, Am Angerbach, Stadtwerkepark, Naturpark Flingern ×3, Gerresheimer Friedhof, Auf'm Rott).
  Hanielpark (9754) liegt **127 m** auseinander: Rollerbahn 5.308 m² und „gegenüber Sohnstraße“ 734 m². Auf'm Rott (9861) ist
  707 m² Wasser plus 11.472 m² Kinderfläche. Zusätzlich teilen sich 35 Kinderspielplätze die Nummer mit einem Bolzplatz
  (nicht im Hub, zählt nicht mit).
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
| E1 | Im Hub: Kinder-, Wald- und Wasserspielplätze der Stadt (351 Einträge → **344 Spielplätze** nach Zusammenführung, 4.1) plus die kurze manuelle Liste betreuter Abenteuerspielplätze (4.6, nicht in den 344). Keine Bolz-, Skater-, Freizeit-, Indoor- oder kommerziellen Anlagen. Die Einleitung sagt das. |
| E2 | Auf Karte, Liste und in den Zahlen steht jede Zeile mit `aktiv=true`. Neue Plätze aus E1 mit gültiger Koordinate kommen über die Freischalt-SQL dazu, nur ohne Ausschluss und ohne sperrenden Prüf-Code (Schritt 6); ein später hinzukommender sperrender Code nimmt eine aktive Zeile nicht heraus. Freischaltung nach Stichprobe der Prüf-CSV, nicht Einzel-Freigabe. Ausschlüsse stehen in `data/spielplaetze/korrekturen.csv` (Schlüssel → Grund, 3.1) und nur für: nicht öffentlich, Dublette, nachweislich abgebaut, unauflösbarer Name. |
| E3 | Nur Düsseldorf. Neuss/Ratingen später. |
| E4 | Ausstattung nur belegt (OSM-Tag, wörtliches Zitat oder Sichtung des Auftraggebers über `ausstattung.csv`, 3.2). Ohne Beleg „keine Angabe“, nie „fehlt“; „fehlt/nein“ nur bei belegter Abwesenheit. |
| E5 | Alter: **belegt** (OSM `min_age`/`max_age`, Zitat, Stadtname „Kleinkind/Schulkind“) oder **vermutlich** (Formel 4.5, erste zutreffende Zeile). Vermutlich zählt für Filter und Pin-Farbe, wird überall als „vermutlich“ gekennzeichnet und zählt **nicht** für die Indexierung: es ersetzt die zwei Geräte nicht und blockiert eine sonst indexierbare Seite nicht. |
| E6 | Fotos: keine erkennbaren Kinder/Personen. Google-Fotos nur nach Sichtprüfung, gespeichert als `extras.google_foto`, geschützt durch `foto_manuell` (4.4), sonst Typ-Illustration (Abschnitt 11). Kein Street View. |
| E7 | Notfallnummer als Hinweis, kein `tel:`-Link (Regel 4.1, Wortlaut 6.3). |
| E8 | „In der Nähe“ nur nach Klick, nur im Browser (Haversine), nichts gespeichert oder gesendet, kein URL-Parameter. Ohne Freigabe bleibt die Standardsortierung, ein Satz erklärt es. |
| E9 | Karte ist Standard, Liste daneben; keine Grid-Ansicht. |
| E10 | „GW“-Präfix entfällt im Anzeigenamen. |
| E11 | Filter „Rollstuhlgerecht“ ab 5 sichtbaren Plätzen mit Beleg (`wheelchair=yes` oder Zitat); `limited` nur auf der Detailseite („teilweise“). Dieselbe Schwelle (5) für jeden Geräte-Chip. |
| E12 | Typ-Illustrationen erzeugt der Auftraggeber (Prompts Abschnitt 11). |
| E13 | Datenschutz-Satz freigegeben (Wortlaut 6.4). |
| E14 | Budget Google + KI bis 40 $; konkrete Kosten vor jedem Google-Lauf nennen. |
| E15 | Score nur intern (`extras.spielplatz.score`), **nie** in `qualitaets_score`; öffentlich höchstens Badge „Top-Spielplatz“. |
| E16 | Link „Spielplätze {inStadtteil}“ auf Event-Seiten **nur bei Kategorie Familie** und nur, wenn diese Stadtteilseite mindestens 5 aktive Spielplätze hat (Zustandstabelle 5.5). Andere Hubs bleiben wie bisher. |

---

## 3. Datenmodell

Tabelle `orte` (Typ `spielplatz` ist im CHECK-Constraint schon erlaubt):
- Spalten: `typ='spielplatz'`, `name` (Anzeigename), `slug`, `stadtteil` (Katalogwert, 4.2), `adresse` (nur `strasse_hausnr` +
  „Düsseldorf“, sonst `NULL`), `latitude`/`longitude` (Stadt), `aktiv`, `qualitaets_score = NULL`, `bild_url = NULL`,
  `bild_attribution` (nur bei freigegebenem Foto).
- `extras.spielplatz`:
  ```
  { quelle: "stadt-duesseldorf" | "abenteuer", lizenz: "dl-de/zero-2.0", quelle_url, datenstand: "2020-09-25",
    // lizenz und datenstand nur bei quelle stadt-duesseldorf. Abenteuer: quelle "abenteuer", quelle_url aus abenteuer.csv,
    // dazu schluessel: "abenteuer:<kurz>" (Identität für Wiederholungsimport und ausstattung.csv)
    teile: [{ objektschluessel, stadt_name, objektart, groesse_m2, latitude, longitude }],   // 1–3 Teilflächen (4.1)
    typ: "kinder" | "wald" | "wasser" | "abenteuer",   // abenteuer nur aus der manuellen Liste (4.6)
    name_quelle: "stadt" | "korrektur",   // Anzeigename aus der Normalisierung oder aus korrekturen.csv
    pruefung: ["name_unklar" | "kein_stadtteil" | "access_private" | "bezirk_abweichend" | "gruppe_gemischt" | "zuordnung_mehrdeutig"],
    bestaetigt: ["access_private" | "gruppe_gemischt"],   // aus korrekturen.csv bzw. abenteuer.csv (dort nur access_private): diese Codes sperren nicht
              // Sperrend: name_unklar, kein_stadtteil, access_private, gruppe_gemischt. bestaetigt hebt nur access_private und
              // gruppe_gemischt auf. name_unklar verschwindet nur über anzeigename, kein_stadtteil nur über einen Katalog-stadtteil (3.1).
              // name_unklar gibt es nur an nie freigeschalteten Zeilen (4.1 Schritt 4).
              // Warnung, sperrt nie: bezirk_abweichend, zuordnung_mehrdeutig.
              // Sperrende Codes wirken nur bei der Freischaltung: Eine aktive Zeile, die später einen sperrenden Code bekommt
              // (z. B. access_private aus einem neuen OSM-Abgleich), bleibt aktiv und steht als Warnung in der Prüf-CSV.
              // Abgeschaltet wird sie nur über ausschliessen + Abschalt-SQL (Schritt 6).
              // Stadt-Codes schreibt nur der Stadt-Import, OSM-Codes nur der OSM-Abgleich. Ein Lauf löscht die Codes der anderen Quelle nicht.
              // Jeder Lauf setzt seine eigenen Codes neu (entfällt der Grund, entfällt der Code). pruefung und bestaetigt sind immer
              // ein Array, auch leer ([]), damit die Freischalt-SQL nie auf NULL prüft.
    ausgeschlossen: "<grund>" | null,   // jeder Import setzt es neu: Grund bei ausschliessen=ja, sonst null (3.1, 4.6). Leerer Grund ist ein Log-Fehler. Die SQL filtert darauf.
    freigeschaltet_am: "YYYY-MM-DD" | null,   // setzt die Freischalt-SQL beim ersten aktiv=true; Grundlage der Weiterleitung nach dem Abschalten (5.5)
    notfallnummer: "9601" | null,  groesse_m2,  stadtbezirk_stadt: 1–10 | null,
    eintritt: "ja" | "nein" | null,   // Städtisch: OSM fee; null = kein Treffer, der Platz gilt als frei. OSM schreibt ihn nur bei quelle stadt-duesseldorf.
              // Abenteuer: Pflicht ja|nein aus abenteuer.csv; eine Zeile ohne gültigen Wert legt der Import nicht an (4.6).
    fehlende_teile: [{ objektschluessel, seit }],   // Schlüssel aus einem späteren Stadtstand verschwunden
    stadt_fehlt_seit?: "YYYY-MM-DD",   // nur wenn kein Schlüssel der Zeile mehr in der Datei steht
    ausstattung: { <geraet>: { wert: "ja"|"nein", quelle: "osm"|"zitat"|"stadt"|"sichtung", beleg?, url?, stand? } },
              // <geraet>: sandkasten, schaukel, rutsche, klettern, wasserspiel, seilbahn, tischtennis, fussball, basketball (Filter);
              // federwippe, wippe, karussell, balancierbalken, volleyball, skaten (Nebengeräte, nur Detailseite).
              // quelle "sichtung" nur aus 3.2.
    alter: { wert: "0-3"|"3-6"|"6-12"|"alle", art: "belegt"|"vermutlich", beleg? } | null,
    extras: { schatten|wc|eingezaeunt|picknick|rollstuhl: { wert: "ja"|"nein"|"teilweise", notiz?, quelle, beleg? } },
    traeger?: string,   // nur Abenteuer, aus abenteuer.csv; die Detailseite zeigt ihn, wenn er gesetzt ist
    beschreibung?, highlight?, profil_stand?, saison?: { text, beleg, url },
    osm: { id, tags_stand, zuordnung, min_age?, max_age?, geraete_roh: [], sport_roh: [] } | null, google: { place_id, rating, anzahl } (intern), score, top: bool }
  ```
- `extras.google_foto` = `{ name, breite, hoehe, autor, autor_url }` nach der Sichtung (4.4) – dieselbe Struktur wie bei Clubs und
  Restaurants; `autor_url` braucht `ortBildAutorUrl` (`web/lib/orte.ts`) für den Urheber-Link. Dazu Spalte `bild_attribution = autor`.
  `extras.foto_manuell` (nicht leer, z. B. Datum der Sichtung) verhindert, dass ein späterer Google-Lauf das Foto ersetzt.
  `bild_url` bleibt `null`. `extras.foto_version` ist 1, wenn das Feld leer ist, sonst der alte Wert plus 1 (Cache der Bildadresse).
- Öffnungszeiten (nur Abenteuerplätze) in der vorhandenen Spalte `oeffnungszeiten`.

### 3.1 Korrekturdatei `data/spielplaetze/korrekturen.csv` (eingecheckt, vom Auftraggeber gepflegt)
Spalten: `schluessel` (Objektschlüssel der Stadt), `anzeigename`, `ausschliessen` (leer/ja), `grund`, `stadtteil`
(Katalogwert; **hat immer Vorrang vor dem Polygon**, bei aktiven wie inaktiven Zeilen, und löst `kein_stadtteil` auf – so lässt
sich auch ein falscher Grenz-Treffer korrigieren; ein Nicht-Katalogwert ist ein Log-Fehler, die Spalte bleibt wie gespeichert (bei einer neuen Zeile leer), das Polygon gilt für diese Zeile nicht, und die Zeile bekommt `kein_stadtteil` – dieselbe Regel wie in `abenteuer.csv` (4.6). Das Polygon gilt nur bei leerer Zelle), `bestaetigt`
(kommagetrennte Prüf-Codes, die für diesen Schlüssel nicht sperren).
Abenteuerplätze stehen nicht hier, sondern in `abenteuer.csv` (4.6). Fehlt `korrekturen.csv`, gilt das als keine Korrekturen, der Import läuft.
Der Import wendet die Datei **vor** Namensbildung, Slug und Freischalt-Prüfung an: steht ein `anzeigename`, entfällt die Namensbildung
(`name_quelle: "korrektur"`, `name_unklar` wird nicht gesetzt, auch wenn der Rohzusatz unklar wäre), ein gesetzter Katalog-`stadtteil` ersetzt `kein_stadtteil`.
Jeder Import setzt `ausgeschlossen` neu aus der Datei: `ausschliessen = ja` mit gesetztem `grund` schreibt `ausgeschlossen = <grund>`
(Schlüssel, nicht Name – Namen ändern sich durch die Normalisierung). Ist `ausschliessen` leer oder fehlt der Schlüssel in
`korrekturen.csv`, wird `ausgeschlossen` auf `null` gesetzt. Fehlt die Datei ganz, bleibt `ausgeschlossen` unverändert (keine Korrekturen). Ein leerer `grund` bei `ausschliessen = ja` ist ein Log-Fehler, das Feld
bleibt unverändert. Eine inaktive Zeile bleibt inaktiv, solange `ausgeschlossen` gesetzt ist oder ein sperrender Code steht.
Eine **aktive** Zeile, die später einen sperrenden Code bekommt, bleibt aktiv (Warnung in der Prüf-CSV); sperrende Codes wirken nur
bei der Freischaltung, abgeschaltet wird nur über `ausschliessen`.
Ist der Ausschluss aufgehoben und kein sperrender Code mehr da, setzt die nächste Freischalt-SQL wieder `aktiv=true`;
`freigeschaltet_am` bleibt der erste Tag, der Slug bleibt. Eine schon freigeschaltete Zeile mit gesetztem `ausgeschlossen` schaltet
erst die Abschalt-SQL in Schritt 6 ab – der Import ändert `aktiv` und `freigeschaltet_am` nie. `bestaetigt` hebt nur
`access_private` und `gruppe_gemischt` auf, wenn der nächste Import sie neu setzt; der Code bleibt in `pruefung` und in der Prüf-CSV
sichtbar. `name_unklar` verschwindet nur über `anzeigename`, `kein_stadtteil` nur über `stadtteil` (sonst entstünden Slug aus dem
Rohnamen bzw. ein Platz ohne Stadtteil, Titel und Stadtteilseite). Steht einer dieser beiden Codes unter `bestaetigt`, wird das
ignoriert und im Log als Fehler gemeldet.
Bei zusammengeführten Plätzen gilt der Eintrag für den **kleinsten** Objektschlüssel der Gruppe. Ein Schlüssel, der zur Gruppe gehört,
aber nicht der kleinste ist, wird nicht angewendet und im Log als Fehler gemeldet.
Ablauf: Import → Prüf-CSV → Auftraggeber trägt Entscheidungen in `korrekturen.csv` ein → Import erneut (Stadtfelder,
Name und Slug, solange die Zeile nie freigeschaltet war, `bestaetigt`) → Freischalt-SQL.

**Begriffe (gelten im ganzen Plan):** *nie freigeschaltet* = `freigeschaltet_am` leer. *Freigeschaltet* = `freigeschaltet_am` gesetzt,
egal ob die Zeile gerade aktiv oder abgeschaltet ist. *Abgeschaltet* = `aktiv=false` und `freigeschaltet_am` gesetzt. Name aus der
Normalisierung und Slug ändern sich **nur bei nie freigeschalteten Zeilen**; ab der ersten Freischaltung ist der Slug für immer fest
(auch nach dem Abschalten, sonst fände die Weiterleitung aus 5.5 die alte URL nicht mehr), der Name ändert sich dann nur über
`anzeigename` (Abenteuer: Spalte `name` in `abenteuer.csv`). Deshalb setzt der Import `name_unklar` nur bei nie freigeschalteten
Zeilen; bei freigeschalteten Zeilen steht ein geänderter Stadtname als „Stadtname neu“ in der Prüf-CSV, ohne Code.
### 3.2 Ausstattung von Hand: `data/spielplaetze/ausstattung.csv` (eingecheckt, vom Auftraggeber gepflegt)
Für Ausstattung, die der Auftraggeber selbst gesehen hat (vor Ort oder eindeutig auf einem Luftbild/Kartenbild).
Spalten: `schluessel` (kleinster Objektschlüssel wie in 3.1, oder `abenteuer:<kurz>`), `merkmal`, `wert`, `beleg`, `stand`.
- `merkmal`: ein Gerät aus §3 (`sandkasten` … `basketball`, Nebengeräte) oder ein Extra (`schatten`, `wc`, `eingezaeunt`,
  `picknick`, `rollstuhl`). `wert`: `ja` oder `nein`, bei `rollstuhl` auch `teilweise`. `beleg`: kurzer Text, wie die Angabe
  gesichert ist (z. B. „vor Ort gesehen“), Pflicht. `stand`: Datum `YYYY-MM-DD`, Pflicht.
- `ausstattung_import.py` schreibt jede gültige Zeile als `{ wert, quelle: "sichtung", beleg, stand }` nach
  `extras.spielplatz.ausstattung` bzw. `extras.spielplatz.extras`. Ungültige Zeile (unbekannter Schlüssel oder Merkmal, falscher
  Wert, leerer Beleg, Datum ungültig, Schlüssel nicht der kleinste der Gruppe, doppelte Zeile): Log-Fehler, nichts geschrieben.
- **Vorrang:** Eine Sichtung gewinnt gegen OSM und Zitat. OSM-Abgleich (4.2) und Profil (4.3) überschreiben ein Merkmal mit
  `quelle: "sichtung"` nie; ein abweichender OSM- oder Zitat-Wert kommt nur in die Prüf-CSV.
- Fehlt eine Zeile, die vorher in der Datei stand, entfernt der nächste Lauf dieses Merkmal (nur Einträge mit `quelle: "sichtung"`);
  der nächste OSM-Abgleich bzw. das Profil kann es wieder füllen. Fehlt die Datei ganz, ändert der Lauf nichts.
- Der Lauf ändert nur Ausstattung und Extras, nie `aktiv`, Name, Slug, Stadtteil oder Prüf-Codes. Er kann jederzeit laufen,
  auch nach dem Livegang; die Seite zeigt die Änderung nach dem nächsten Cache-Ablauf.
- Die Detailseite nennt die Quelle als „vor Ort geprüft ({stand})“ in „Stand der Angaben“ (5.3).

- Wiederholungsimport findet die Zeile über die **Schnittmenge** der `objektschluessel` (4.7), nicht über die exakte Liste.
  Die sortierte Liste bleibt der gespeicherte Stand der aktuellen Teilflächen.

---

## 4. Pipeline `scraper/spielplaetze/` (Python, Logs Deutsch, `--dry-run`, keine neue Bibliothek)

### 4.1 Stadt-Import (`stadt_import.py`)
1. GeoJSON WGS84 laden; Features ohne Geometrie verwerfen; Filter über den **Text** der Objektart (E1).
2. Koordinate nur aus `geometry`; jeder Punkt muss in 6,6–7,0 °O / 51,1–51,4 °N liegen, sonst **Abbruch** (falsche Datei/Projektion).
3. **Zusammenführung**, nur innerhalb des Hubs (Bolzplätze zählen nicht):
   - Alle Teile derselben Nummer ≤ **30 m**: **ein** Spielplatz. Koordinate = die der größten Teilfläche, bei gleicher
     Größe der kleinste `objektschluessel`. Größe = Summe. Typ = Wasser vor Wald vor Kinder. Jede Teilfläche in `teile`
     **mit eigener Koordinate und eigenem Namen**.
   - Dieselbe Nummer, Abstand über 30 m und bis 150 m: **nicht** zusammenführen, Nummer **behalten** (Hanielpark, 127 m).
   - Dieselbe Nummer, irgendein Paar > 150 m: nicht zusammenführen, Nummer bei allen unterdrücken (`notfallnummer = null`),
     Plätze behalten, Prüf-CSV.
   - **Gemischte Gruppe** (einige Teile ≤ 30 m, andere weiter weg): Teile, die über Abstände ≤ 30 m verbunden sind, bilden
     je eine Teilgruppe (ein Platz je Teilgruppe); Nummer nach den Regeln oben für die ganze Gruppe; Code `gruppe_gemischt`
     in der Prüf-CSV. Der Code sperrt die Freischaltung, bis `korrekturen.csv` ihn unter `bestaetigt` führt; die automatische
     Teilung bleibt. Kommt heute nicht vor, kann mit einem neuen Stadtstand kommen.
   - Heute: sechs Gruppen auf einem Punkt werden je ein Platz, Hanielpark bleibt zwei. **351 → 344.**
4. **Name** (reine, getestete Funktion): „GW “-Präfix weg (E10); Teil vor dem Komma = Ort/Park, danach Zusatz.
   `Ksp/KSP` → Spielplatz, `Wsp/WSP` → Wasserspielplatz, `Waldksp` → Waldspielplatz; Schreibweise normalisieren
   („HOFGARTEN“ → „Hofgarten“, „SPEE`SCHER GRABEN“ → „Spee'scher Graben“, „Str.“ → „straße“ nur bei eindeutigem Wortende).
   Muster: „Spielplatz Hofgarten (Oederallee)“, „Wasserspielplatz Volksgarten“. Bei zusammengeführten Teilflächen den
   gemeinsamen Stamm („Spielplatz San-Remo-Straße“); die Zusätze stehen als Bereiche auf der Detailseite („Bereich für
   Kleinkinder und für Schulkinder“). Ein unklarer Zusatz blockiert den zusammengeführten Platz nicht, der Stamm ist der
   Anzeigename. Bei einem nicht zusammengeführten Platz gehört der Zusatz zum Anzeigenamen. Sichere Auflösungen,
   geschlossen: `Str.` am Wortende → „straße“, `a.d.` → „an der“, `ggü.` → „gegenüber“. Damit heißen die zwei
   Hanielpark-Plätze „Spielplatz Hanielpark (an der Rollerbahn)“ und „Spielplatz Hanielpark (gegenüber Sohnstraße)“.
   Lässt sich der Zusatz einer **nie freigeschalteten** Zeile nicht auflösen („Fritz./Mörsenb.“), bekommt sie `name_unklar` und bleibt
   **inaktiv**, bis `korrekturen.csv` einen Anzeigenamen hat. Steht dort ein `anzeigename`, entfällt diese Namensbildung und
   `name_unklar` wird nicht gesetzt (3.1). Bei freigeschalteten Zeilen (aktiv oder abgeschaltet) setzt der Import `name_unklar` nicht –
   ihr Name kommt nie aus der Normalisierung –; ein geänderter Stadtname steht als „Stadtname neu“ in der Prüf-CSV. Der Import setzt
   `aktiv` nie (Schritt 8). Typ immer aus `objektart`, nie aus dem Namen.
5. **Stadtteil** per Ray-Casting gegen jedes Teilpolygon der WGS84-Stadtteildatei (keine Löcher vorhanden; Code kann sie trotzdem).
   Katalog-Mapping: „Flingern Nord“ → `Flingern-Nord`, „Flingern Süd“ → `Flingern-Süd`, sonst Name 1:1; `Hafen` bleibt
   Datenbankwert (Anzeige „Medienhafen“ über die bestehende Logik). **Reihenfolge:** Katalogwert aus `korrekturen.csv` (3.1) vor
   Polygon-Treffer. Ein Nicht-Katalogwert in der CSV ist ein Log-Fehler, lässt die Spalte wie gespeichert (neue Zeile: leer), fällt nicht auf das Polygon zurück und setzt `kein_stadtteil` (3.1). Ohne Katalogwert und ohne Polygon-Treffer → `kein_stadtteil`, Prüf-CSV: eine nie freigeschaltete Zeile hat keinen Stadtteil und bleibt inaktiv;
   eine freigeschaltete Zeile (aktiv oder abgeschaltet) behält ihren gespeicherten Stadtteil, der Code ist eine Warnung (eine abgeschaltete
   Zeile wird mit dem Code nicht wieder freigeschaltet).
   **Kontrolle Bezirk** (nur bei Polygon-Treffer; kommt der Stadtteil aus `korrekturen.csv`, entfällt sie): Bezirk = `int(Nummer[:2])`; nur ein **gesetzter**, abweichender `stadtbezirk` der Spielplatzdatei kommt
   als `bezirk_abweichend` in die Prüf-CSV (sperrt die Freischaltung nicht), leer ist kein Widerspruch (Polygon gewinnt).
6. **Adresse** nur aus `strasse_hausnr`; sonst leer. Kein Geocoding, keine Adressliste. „Route planen“ aus der Koordinate.
7. **Slug** = Anzeigename + Stadtteil (bestehende Slug-Funktion), Kollision → `slug_mit_suffix`. Solange die Zeile **nie
   freigeschaltet** war (`freigeschaltet_am` leer), bildet jeder Import den Slug aus dem aktuellen Anzeigenamen neu (so verschwindet ein
   Rohname wie „…-fritz-moersenb-…“, sobald `korrekturen.csv` einen Namen hat). **Ab der ersten Freischaltung ist der Slug für immer
   fest** – auch nach dem Abschalten (die Weiterleitung aus 5.5 sucht die Zeile über den Slug); spätere Namensänderungen ändern nur `name`.
   Kollisionen prüft der Import gegen die ganze Tabelle `orte` (städtische und Abenteuer-Zeilen, alle Typen) und löst sie in fester
   Reihenfolge auf: Slugs freigeschalteter Zeilen sind zuerst reserviert, danach bekommen nie freigeschaltete Zeilen ihren Slug nach
   kleinstem Schlüssel (Objektschlüssel bzw. `abenteuer:`-Schlüssel). Ein Wiederholungsimport ohne Namensänderung ergibt dieselben Slugs.
8. Schreiben über das Skript (wie der Club-Import). **Neu angelegte** Zeilen mit `aktiv=false`, `extras.spielplatz.quelle` gesetzt,
   `pruefung` und `bestaetigt` als Array (auch leer). Bei bestehenden Zeilen steht `aktiv` nicht in der Schreibliste.
   Rücknahme **nur vor der Freischaltung** und nur für nie freigeschaltete Zeilen: `DELETE … WHERE typ='spielplatz' AND aktiv=false AND extras->'spielplatz'->>'freigeschaltet_am' IS NULL AND extras->'spielplatz'->>'quelle'='stadt-duesseldorf'`.
   Wiederholter Import findet die Zeile nach 4.7 und ändert nur Stadtfelder (`extras_mergen`): `teile`, Größe, Koordinate, Typ,
   Notfallnummer, Adresse, die Stadt-Codes in `pruefung` (`name_unklar`, `kein_stadtteil`, `bezirk_abweichend`, `gruppe_gemischt`)
   und `bestaetigt` aus der CSV. `stadtteil` nach Schritt 5: Katalogwert aus `korrekturen.csv`, sonst Polygon-Treffer; ohne beides bleibt
   bei einer freigeschalteten Zeile der gespeicherte Wert (Warnung `kein_stadtteil`), eine nie freigeschaltete Zeile bleibt ohne Stadtteil.
   Bei einer freigeschalteten Zeile ändert ein Polygon-Treffer den gespeicherten Stadtteil nur, wenn die Zelle `stadtteil` in
   `korrekturen.csv` leer ist und der Treffer sich vom gespeicherten unterscheidet; die Änderung steht in der Prüf-CSV. Ein
   Nicht-Katalogwert lässt den gespeicherten Stadtteil unverändert und setzt `kein_stadtteil` (Schritt 5). `eintritt` und die OSM-Codes
   (`access_private`, `zuordnung_mehrdeutig`) schreibt nur der OSM-Abgleich; ein Stadt-Import lässt sie stehen. Bei **nie freigeschalteten**
   Zeilen auch Name und Slug. Dazu `ausgeschlossen` aus der CSV nach 3.1 (gesetzt oder wieder `null`). Nie Profil, Foto, `aktiv`,
   `freigeschaltet_am`, und bei freigeschalteten Zeilen (aktiv oder abgeschaltet) nie Name aus der Normalisierung (nur aus
   `korrekturen.csv`) oder Slug.
   Abschalten nur über die Abschalt-SQL (Schritt 6).
9. Ausgabe: `data/spielplaetze/pruefung.csv` (Schlüssel, Name alt/neu, Stadtteil, Prüf-Codes aus `pruefung`, zusammengeführt,
   Nummer unterdrückt, GW, keine Adresse) und Zusammenfassung im Log. Die Prüf-CSV ist eine Ausgabe; Entscheidungen gehen nur über
   `korrekturen.csv` zurück.

### 4.2 OSM-Abgleich (`osm_abgleich.py`)
- Eine Overpass-Abfrage `nwr[leisure=playground]` + Geräte-Objekte `playground=*` im Stadtgebiet, generischer User-Agent,
  Wiederholung mit Pause, Zwischenspeicher `data/spielplaetze/osm.json` (gitignored, nie veröffentlicht).
- Zuordnung: Liegt der Stadt-Punkt in genau einer OSM-Spielplatzfläche, ist das der Treffer. Liegt er in keiner, zählt ein OSM-Spielplatz
  (Fläche oder Punkt), dessen Mittelpunkt ≤ 60 m entfernt ist, wenn es genau einer ist. Mehrere Kandidaten (zwei Flächen um den Punkt
  oder mehrere in 60 m) → Code `zuordnung_mehrdeutig`, Prüf-CSV, nichts übernehmen.
- **Geräte des Treffers:** Objekte mit `playground=*` (Punkt oder Fläche, Mittelpunkt zählt) innerhalb der getroffenen Fläche; bei
  einem OSM-Punkt die Geräte ≤ 30 m um diesen Punkt. Werte mit `;` werden getrennt. Rohwerte bleiben in `osm.geraete_roh` (für die
  Altersregel 4.5), `min_age`/`max_age` in `osm`; die Altersregel rechnet in Schritt 6.
- **Sportflächen** (Tischtennis, Fußball, Basketball, Volleyball, Skaten): `leisure=pitch` mit passendem `sport` sowie `sport=table_tennis`
  an einem Punkt, wenn das Objekt ≤ 40 m vom Stadt-Punkt bzw. der Abenteuer-Koordinate **oder** von der getroffenen
  Spielplatzfläche entfernt ist (Abstand der nächsten Punkte; drinnen = 0). Unabhängig davon, ob ein Spielplatz-Treffer besteht.
  Nicht bei `access=private`/`no`/`customers` (z. B. Schulhof, Vereinsplatz). `sport=multi` wird nicht zugeordnet, nur gezählt.
- Übernahme mit `quelle: "osm"` (nie über ein Merkmal mit `quelle: "sichtung"` oder `"zitat"`; ein abweichender Wert steht nur in der Prüf-CSV): Jeder Lauf ersetzt die bisherigen OSM-Einträge; Geräte (Mapping-Tabelle, 4.5), `min_age`/`max_age`, `wheelchair`, `fee` → `eintritt`
  (`yes` → `ja`, `no` → `nein`, sonst `null`; **nur bei `quelle: "stadt-duesseldorf"`** – bei Abenteuerplätzen bleibt `eintritt` aus
  `abenteuer.csv`, ein abweichendes `fee` steht nur in der Prüf-CSV), `access`
  (`access=private` → Code `access_private`, Prüf-CSV, sperrt die Freischaltung, bis `korrekturen.csv` ihn unter `bestaetigt` führt
  oder der Platz mit `ausschliessen` draußen bleibt).
  Mehrere OSM-Kandidaten → Code `zuordnung_mehrdeutig` (sperrt nicht, es wird nur nichts übernommen).
  Jeder Lauf setzt die OSM-Codes neu: Ist `access=private` weg, entfällt `access_private`.
- **Abenteuer:** dieselbe Zuordnung über die Koordinate aus `abenteuer.csv`, nach dem Anlegen in Schritt 3 und vor den Profilen.
  Übernommen werden Geräte, Alter, `wheelchair` und `access`, **nie `eintritt`**. Ohne OSM-Treffer bleibt die Zeile, wie sie ist.
  `access=private` (auch `customers`) setzt auch hier `access_private`; betreute Plätze sind in OSM öfter so markiert. Aufheben über die
  Spalte `bestaetigt` in `abenteuer.csv` (4.6), wenn die Anlage laut Quelle öffentlich zugänglich ist.
- **Bericht** (`data/spielplaetze/osm_bericht.md`, Prüf-Liste `osm_pruefung.csv`): Anteil der Plätze mit ≥ 1 / ≥ 2 OSM-Geräten, städtisch und Abenteuer getrennt, dazu Zählung je Gerät und Sportart. Ein OSM-Platz ohne Treffer auf einen
  Stadt-Punkt und ohne Treffer auf eine Abenteuer-Koordinate wird nur aufgelistet, nicht angelegt – Kandidat für einen neueren Platz
  oder eine fehlende Zeile in `abenteuer.csv`.

### 4.3 Profil (`profil.py`, KI + Websuche, wie Club-Profil)
- **Runde 1 (108 Spielplätze, nach der Zusammenführung gezählt):** alle Wasser (9) + alle Wald (20) + Kinderspielplätze
  mit **summierter** Größe ≥ 3.000 m² (79). Die frühere Rechnung 9 + 20 + 86 − 6 = 109 zählte Einträge vor der
  Zusammenführung; Auf'm Rott fällt mit der Kinderfläche in die 9 Wasser und wird nicht noch einmal als großer
  Kinderspielplatz gezählt. **Dazu alle Abenteuerplätze aus `abenteuer.csv`** (zusätzlich zu den 108; Eltern suchen sie
  namentlich). Indexierbar wird die Seite mit Profil-Beschreibung und mindestens zwei belegten Geräten (5.4). Geräte mit Beleg
  aus dem Profil (`quelle: "zitat"`) zählen dafür, auch ohne OSM-Treffer. Erst **Probe mit 10**, Bericht zum Gegenlesen, dann der Rest. Runde 2 (**74** Kinderspielplätze
  mit Summe 1.500 bis unter 3.000 m²) nur nach Bericht und Freigabe. Dieselbe Zählung an den Roh-Einträgen ist ebenfalls 74:
  die sechs Zusammenführungen verschieben keinen Platz in oder aus diesem Band. Am Angerbach (712 m² Kleinkind plus 1.635 m²
  Schulkind) wird ein Platz, Alter belegt „alle“, und bleibt in Runde 2. Die früher genannte 85 war keine Vorher-Zählung
  dieser Definition. Profil erst, wenn Schritt 3 von 4.1 gelaufen ist.
- Quellen: duesseldorf.de, Pressemitteilungen der Stadt, Vorlagen der Bezirksvertretungen, lokale Presse; Spielplatz-Portale nur als
  Fakt mit Zitat. robots.txt, ≥ 2 s Pause, keine Rausgegangen-Seiten.
- Ergebnis je Platz: Geräte, Extras (inkl. Rollstuhl), Alter, `saison` (nur mit Beleg; bei Typ Wasser für den Platz,
  bei einer größeren Kinder-Teilfläche nur für den Wasserbereich formulieren), Beschreibung 2–4 eigene Sätze,
  Highlight, `profil_stand` = Datum der jüngsten Quelle. **Jede Aussage mit wörtlichem Beleg**, Prüfung wie bei den Clubs
  (Wortstamm/Zahl im Zitat). Eine Schablone aus Stadtfeldern („Spielplatz X in Y, Z m²“) ist keine Beschreibung.
- Widerspruch OSM ↔ Zitat: jüngere Quelle gewinnt, beide in der Prüf-CSV. Ein Merkmal mit `quelle: "sichtung"` (3.2) bleibt immer.

### 4.4 Google (`google_abgleich.py`, nur Runde-1-Plätze)
- Umkreissuche 80 m, Typ `playground`, über den vorhandenen Places-Client; Treffer nur bei Namensähnlichkeit oder einzigem Treffer,
  sonst Prüf-CSV. Bewertung nur intern (Score). Foto-Kandidaten → Sichtung (nur ohne erkennbare Personen) → Foto-SQL wie bei den Club-Fotos: `extras.google_foto` = `{ name, breite, hoehe, autor, autor_url }`, `bild_attribution = autor`,
  `foto_manuell` = Datum der Sichtung, `foto_version` ist 1, wenn das Feld leer ist, sonst der alte Wert plus 1, `bild_url` bleibt `null`.
- Kosten vorher nennen (E14); Schätzung Abschnitt 9.

### 4.5 Regeln (reine Funktionen, getestet)
- **Geräte-Mapping OSM → Liste:** `sandpit`→Sandkasten, `swing`/`basketswing`/`baby_swing`→Schaukel, `slide`→Rutsche,
  `climbingwall`/`climbingframe`/`climbing_net`→Klettern, `water`/`pump`/`splash_pad`→Wasserspiel, `zipwire`→Seilbahn;
  **Sportflächen** nach 4.2: `sport=table_tennis`→Tischtennis, `soccer`→Fußball, `basketball`→Basketball (Filter-Geräte),
  `volleyball`/`beachvolleyball`→Volleyball, `skateboard`→Skaten (Nebengeräte); weitere (`springy`→Federwippe, `seesaw`→Wippe,
  `roundabout`→Karussell, `balancebeam`→Balancierbalken) als Nebengeräte (Detailseite, kein Filter). Tischtennis, Fußball und
  Basketball sind Filter-Geräte wie die übrigen sechs (Chip ab 5 sichtbaren Plätzen, E11), zählen für die zwei Geräte der
  Indexierung, für „X von Y“ und für den Score, aber nicht für das Alter.
- **Alter.** Erst ein belegter Wert, sonst die Ableitung. Belegt (dann nicht weiter ableiten): OSM `min_age`/`max_age`,
  wörtliches Zitat oder Stadtname. „Kleinkind“ und „Schulkind“ an zusammengeführten Teilen, oder eine Spanne über mehr
  als ein Band: „alle“. Nur „Kleinkind“ oder `max_age` ≤ 3: „0-3“. Nur „Schulkind“ oder `min_age` ≥ 6: „6-12“. Sonst das
  Band aus dem Zitat. Widerspruch OSM gegen Zitat: die jüngere Quelle; der Stadtname zählt mit dem Dateistand 2020-09-25.
  Ohne Beleg, erste zutreffende Zeile. Gezählt werden die gemappten Geräte plus die Rohwerte `baby_swing` und `springy`
  (Filter: Babyschaukel bleibt Schaukel, Federwippe ein Nebengerät). Kleinkindgerät = Sandkasten, Federwippe, Babyschaukel.
  Großkindgerät = Klettern, Seilbahn.
  1. Weniger als zwei Geräte: kein Alter.
  2. Kleinkindgerät und Großkindgerät: „alle“.
  3. Nur Sandkasten, Federwippe, Babyschaukel: „0-3“.
  4. Klettern oder Seilbahn, ohne Kleinkindgerät: „6-12“.
  5. Sandkasten, Rutsche oder Schaukel, ohne Klettern und ohne Seilbahn: „3-6“.
  6. Sonst kein Alter.
  Leeres Alter: neutraler Pin, nur unter „Alle Alter“. „alle“ hat eine eigene Farbe und passt zu jedem Altersfilter.
  „Vermutlich“ zählt für Filter und Pin, ersetzt bei der Indexierung keine Geräte und sperrt eine Seite mit Beschreibung
  und mindestens zwei Geräten nicht.
- **Score (intern, 0–1):** gewichtete Summe aus Teilwerten, jeder Teilwert 0–1:
  Ausstattung 35 % (Anzahl belegter Filter-Geräte inkl. Tischtennis / 6, höchstens 1), Größe 20 % (Perzentil-Rang der summierten Größe. Die Menge ist bei jedem Schritt 6, gerechnet vor der Freischalt-SQL, die Vereinigung aus den nicht ausgeschlossenen **städtischen** Plätzen ohne sperrenden Prüf-Code (nach `bestaetigt`, also wie `freischaltbar()` in Schritt 6) und den bereits aktiven städtischen Plätzen, auch mit Warn-Code. Ein ausgeschlossener Platz gehört nicht dazu, auch wenn er noch aktiv ist. Liegt ein städtischer Platz außerhalb der Menge, ist sein Größen-Teilwert 0,5. Abenteuerplätze haben keine Größe, ihr Teilwert ist 0,5 = neutral,
  und sie gehen nicht in die Perzentil-Menge ein), Besonderheit 20 % (Wasser 1, Wald 1, Abenteuer 1, rollstuhlgerecht belegt +0,5, höchstens 1; sonst 0),
  Google 15 % (Bayes-Mittel wie beim Club-Score auf 0–1; ohne Google 0,5 = neutral), Extras 10 % (Anteil belegter „ja“ unter
  Schatten, WC, eingezäunt, Picknick). Sortierung „Empfohlen“ = Score absteigend, dann Name.
  „Top-Spielplatz“ = die besten 20 % nach Score (mindestens 1, aufgerundet) unter den Plätzen, die **indexierbar** (5.4), nicht
  ausgeschlossen und nach diesem Lauf aktiv sind (schon aktiv oder `freischaltbar()`, Schritt 6); städtisch und Abenteuer zusammen.
  Alle übrigen Zeilen bekommen `top: false`.
  Score und Top werden bei **jedem** Durchlauf von Schritt 6 neu berechnet (nach neuen Profilen, Freischaltungen oder Ausschlüssen).
  Es schreibt `score.py` per `extras_mergen` (`extras.spielplatz.score`, `top`) – derselbe freigegebene Schreibweg wie Schritt 1.
  `istIndexierbar` gibt es in Python (Top) und TypeScript (5.1); beide prüfen gegen dieselbe Fixture
  `tests/fixtures/spielplatz_indexierbar.json` (pytest und vitest).

### 4.6 Abenteuer-/Bauspielplätze
Eigene Datei `data/spielplaetze/abenteuer.csv` (eingecheckt, vom Auftraggeber gepflegt), nicht `korrekturen.csv`.
Spalten: `schluessel` (`abenteuer:<kurz>`), `name`, `traeger`, `adresse`, `latitude`, `longitude`, `stadtteil` (Katalogwert),
`oeffnungszeiten`, `eintritt` (`ja` oder `nein`, Pflicht; nur dieser Import schreibt ihn, nie der OSM-Abgleich), `quelle_url`, optional `ausschliessen` (leer/ja), `grund` und
`bestaetigt` (nur `access_private`; andere Codes werden ignoriert und im Log als Fehler gemeldet).
`abenteuer_import.py` legt daraus Zeilen an und blockiert
den Stadt-Import nicht. Nur öffentlich belegte, öffentlich zugängliche Anlagen. `typ: "abenteuer"`, `quelle: "abenteuer"`,
Öffnungszeiten in der Spalte `oeffnungszeiten`, Ersatzbild = Kinder-Motiv, eigener Typ-Text „betreuter Abenteuerspielplatz –
Öffnungszeiten beachten“. Die Detailseite zeigt die Öffnungszeiten. Keine Notfallnummer (nicht städtisch), Score-Besonderheit 1.
Der Stadt-DELETE aus 4.1 und der Stadt-Diff treffen `quelle = "abenteuer"` nicht; der eigene DELETE steht unten. Eigene Identität (manueller Schlüssel), nicht die
Objektschlüssel der Stadt.

Regeln von `abenteuer_import.py` (reine Funktionen, getestet):
- **Pflichtfelder:** `schluessel` (Muster `abenteuer:[a-z0-9-]+`, eindeutig), `name`, `latitude`/`longitude` (im Rechteck aus 4.1
  Schritt 2), `eintritt` (`ja` oder `nein`), `quelle_url`. Fehlt eines oder ist es ungültig: Zeile wird **nicht** angelegt, Log-Fehler.
  Eine Zeile ohne Eintritt gibt es damit in der Datenbank nicht. **Bei einer bestehenden Zeile** (Wiederholungsimport) bleibt die
  Datenbankzeile bei einer ungültigen CSV-Zeile vollständig unverändert – kein teilweises Überschreiben –, Log-Fehler. Das gilt für
  fehlende/ungültige Pflichtfelder und für `ausschliessen = ja` ohne `grund`.
- **Stadtteil:** muss ein Katalogwert sein (dieselbe Regel wie `korrekturen.csv`, 3.1). Sonst Log-Fehler, Code `kein_stadtteil`, und die Spalte `stadtteil` behält den ungültigen Text nicht: eine neue Zeile bleibt leer, eine bestehende behält den alten Wert. Auflösen nur durch einen Katalogwert in `abenteuer.csv`. An einer nie freigeschalteten oder abgeschalteten Zeile sperrt der Code die Freischaltung, an einer aktiven Zeile ist er eine Warnung.
- **Anlegen** mit `aktiv=false`, `pruefung` und `bestaetigt` als Array (auch leer); bei bestehenden Zeilen steht `aktiv` nicht in der Schreibliste. `ausgeschlossen`: bei `ausschliessen = ja` und gesetztem `grund` der Grund, sonst `null`. Ein leerer
  `grund` bei `ausschliessen = ja` ist ein Log-Fehler, die Zeile wird nicht angelegt (bestehende Zeile: unverändert, siehe oben).
  `bestaetigt` aus der CSV (nur `access_private`). Freischaltung und Abschalten über dieselbe SQL
  wie bei den städtischen Plätzen (Schritt 6).
- **Wiederholungsimport** findet die Zeile über `schluessel`: aktualisiert Name (den Slug nur, solange die Zeile nie freigeschaltet war), Träger, Adresse,
  Koordinate, Stadtteil, Öffnungszeiten, Eintritt, Quelle, `bestaetigt` und `ausgeschlossen` (gesetzt oder wieder `null`, gleiche
  Regel wie beim Anlegen) – nur wenn die CSV-Zeile gültig ist. Ein Katalog-Stadtteil schreibt die Spalte und entfernt `kein_stadtteil`. Ein Nicht-Katalogwert schreibt die Spalte nicht. `traeger` liegt in `extras.spielplatz.traeger`. Nie Profil, Foto, `aktiv`, `freigeschaltet_am`. Ein aus der CSV
  gelöschter Schlüssel ändert nichts (weder `aktiv` noch `ausgeschlossen`) und erscheint im Log; Abschalten nur über `ausschliessen`,
  solange der Schlüssel in der Datei steht, plus Abschalt-SQL.
- **Slug** wie 4.1 Schritt 7 (Name + Stadtteil, `slug_mit_suffix`, fest ab der ersten Freischaltung, auch nach dem Abschalten).
- **Rücknahme** nur vor der Freischaltung und nur für nie freigeschaltete Zeilen: `DELETE … WHERE typ='spielplatz' AND aktiv=false AND extras->'spielplatz'->>'freigeschaltet_am' IS NULL AND extras->'spielplatz'->>'quelle'='abenteuer'`.

### 4.7 Aktualisierung
Stadtdatei jährlich prüfen (Last-Modified). Bei neuem Stand die Gruppen nach 4.1 neu bilden und so zuordnen:
- Schnittmenge der Objektschlüssel mit genau einer bestehenden Zeile: diese Zeile. Stadtfelder neu rechnen (Größe, Koordinate
  der größten verbliebenen Teilfläche, Typ, Nummer, Stadt-Codes in `pruefung`, `stadtteil` nach 4.1 Schritt 8). `eintritt` und OSM-Codes bleiben.
  Nie freigeschaltet (`freigeschaltet_am` leer): Name und Slug aus dem aktuellen Anzeigenamen neu. Freigeschaltet (aktiv oder
  abgeschaltet): Slug fest; `name` nur, wenn `korrekturen.csv` einen `anzeigename` für den kleinsten Schlüssel setzt. Profil, Foto, `aktiv` und `freigeschaltet_am` bleiben in beiden Fällen. `ausgeschlossen` folgt 3.1 (gesetzt oder wieder `null`).
- Ein Schlüssel fehlt, andere der Zeile stehen noch in der Datei: Schlüssel aus `teile` nach `fehlende_teile` (mit Datum),
  Zeile nicht deaktivieren.
- Kein Schlüssel der Zeile steht noch in der Datei: `stadt_fehlt_seit` setzen, nicht sofort deaktivieren. Die Zeile steht in der
  Prüf-CSV; bestätigt der Auftraggeber den Abbau, trägt er `ausschliessen = ja` (Grund „abgebaut“) in `korrekturen.csv` ein, der
  nächste Import setzt `ausgeschlossen`, die Abschalt-SQL (Schritt 6) setzt `aktiv=false`, die alte URL leitet weiter (5.5).
- Eine neue Gruppe trifft keine Zeile: neue inaktive Zeile.
- Eine Gruppe trifft mehrere Zeilen, oder eine Zeile trifft mehrere Gruppen: nichts automatisch teilen oder verschmelzen,
  Prüf-CSV.
OSM halbjährlich neu abgleichen (nur `quelle: "osm"`-Felder). Profile nur bei Hinweis oder Umbau.

---

## 5. Website

### 5.1 Daten und Logik
- `web/lib/spielplaetze-daten.ts`: eigene Abfrage (`"use cache"`, seitenweise), `typ='spielplatz'`, `aktiv=true`,
  **mit** `extras` (nicht die Spaltenliste aus `orte.ts`), **ohne** Score-Schwelle.
- `web/lib/spielplaetze.ts`: Profil nur aus bekannten Werten lesen; Konstanten (Altersfarben/Labels aus dem Handoff, Geräte, Extras);
  Filter `alter` (Einzelauswahl; „alle“ passt zu jedem Alter; unbekannt nur bei „Alle Alter“), `geraet` (UND, nur „ja“; Sandkasten, Schaukel, Rutsche, Klettern, Wasserspiel, Seilbahn, Tischtennis, Fußball, Basketball),
  `extra` (UND), `typ` (Wasser, Wald, Abenteuer; Mehrfach, ODER; aus Stadtdaten bzw. Liste belegt, daher ohne Schwelle – ein
  Chip erscheint, sobald mindestens ein sichtbarer Platz den Typ hat), `stadtteil` (Mehrfach, ODER), `sort` (`empfohlen` = Score, dann Name; `ausstattung` = Anzahl belegter Geräte);
  `istIndexierbar` (5.4); Chip-Schwelle 5 (E11). „In der Nähe“ ist kein URL-Parameter.
- `GuideHub`/`GUIDE_HUBS` um `spielplaetze` erweitern (Name „Spielplätze“, Mehrzahl „Spielplätze“, Icon `toys`);
  `hubOrte("spielplaetze")` → Spielplätze laden (expliziter Zweig, kein Fallback auf Clubs).

### 5.2 Hub `/guides/spielplaetze` (`instant = false`)
- Heller Hero (Tokens mit Dark-Variante): Bild `web/public/guides/spielplaetze.webp` rechts auf 46 %, im hellen Theme mit
  Ausblendung nach links in den hellen Grund. Die dunkle Darstellung nutzt die dunklen Flächentokens und diese helle Maske nicht;
  der Text bleibt lesbar (5.7). H1 „Spielplätze in Düsseldorf“, Zahl aus den Daten, Brotkrumen Start / Düsseldorf entdecken /
  Spielplätze. Darunter **Einleitung** (2–3 Sätze: öffentliche städtische Spielplätze, dazu wenige betreute Abenteuerspielplätze).
- Filter: Alter (groß, Farbpunkt + Text), Typ (Wasser/Wald/Abenteuer), Ausstattung, Extras inkl. Rollstuhl (E11), Stadtteil, Sortierung; „In der Nähe“-Knopf (E8,
  nur dieser Knopf fragt den Standort ab). Leere Ergebnisse erklären: „Die Ausstattung ist noch nicht für alle Spielplätze erfasst.“
  Sichtbarer Hinweis über der Liste: „Ausstattung für X von Y Spielplätzen erfasst“. X = Spielplätze mit mindestens einem
  belegten Gerät, Y = sichtbare Spielplätze. Die Chip-Schwelle 5 bleibt.
- **Karte (Standard) + Liste:** Punkte über `/api/guide-karte?hub=spielplaetze` mit **eigener** Punktfunktion: id, Name, Typ, Alter
  (+ „vermutlich“), Stadtteil, Koordinate, URL, Thumb – **keine Bewertung, keine OSM-Tags**. Pins in Altersfarbe, unbekannt neutral,
  Legende mit Text, gewählter Pin mit hellem Ring auf dunkler Karte, Hover-Puls.
- Unter der Karte `OrtLinkListe` mit **allen** Spielplätzen (Parameter `max` erhöhen), damit alle Links im ersten HTML stehen.
- Unten `GuideSeoText` mit fünf FAQs (6.2). **Kein** Block „… nach Stadtteil“ unten (wie Clubs/Kneipen).
- Filter-URLs `noindex, follow`, Canonical immer `/guides/spielplaetze`. Das setzt die Seite selbst, wie
  `web/app/guides/clubs/page.tsx`: Canonical auch bei Filtern, `robots` nur dann. Nicht über `seitenMetadaten({ noindex: true })`,
  denn der Helfer streicht dabei den Canonical (`web/lib/seo.ts`). JSON-LD BreadcrumbList + ItemList (nur indexierbare, max. 30).
- Fuß: „Kartendaten und Ausstattung teils © OpenStreetMap-Mitwirkende · Spielplatzdaten: Landeshauptstadt Düsseldorf (dl-de/zero-2.0)“.

### 5.3 Detail `/guides/spielplaetze/[slug]` (`instant = false`)
- Brotkrumen bis zum Namen; Bild (freigegebenes Foto mit Urheber) oder Typ-Illustration; H1; Stadtteil (Anzeige wie überall,
  „Medienhafen“); Adresse falls vorhanden; Alters-Badge (+ „vermutlich“).
- Beschreibung (nur aus Profil); zusammengeführte Teilflächen als Bereiche („Bereich für Kleinkinder und für Schulkinder“);
  Ausstattung: ja (grün) / keine Angabe (neutral) / nein (rot, nur belegt); Extras mit Notiz; Größe „ca. 1.200 m² laut Stadt“
  (Summe der Teilflächen); bei `typ: "abenteuer"` die Öffnungszeiten aus `oeffnungszeiten` und, wenn gesetzt, den Träger; Saison-Hinweis nur für den Wasserbereich, wenn eine Kinder-Teilfläche größer ist, sonst bei Typ Wasser;
  **Notfallnummer** (6.3); „Stand der Angaben“ (bei Sichtung „vor Ort geprüft ({stand})“, 3.2), Quellen, OSM-Namensnennung, Haftungssatz (6.5).
- Rechts: Mini-Karte, „Route planen“ (Google-Maps-Link aus der Koordinate, öffnet erst nach Klick), Anker „In der Nähe“
  (scrollt nur, fragt den Standort nicht ab).
- „In der Nähe“: (1) „Weitere Spielplätze in {Park}“ = andere Spielplätze mit demselben Namensstamm. Stamm = Anzeigename ohne das
  führende Typwort („Spielplatz“, „Wasserspielplatz“, „Waldspielplatz“, „Abenteuerspielplatz“) und ohne Klammerzusatz, also der Park
  bzw. Ort: „Spielplatz Hanielpark (an der Rollerbahn)“ → „Hanielpark“, „Wasserspielplatz Volksgarten“ und „Spielplatz Volksgarten
  (…)“ → beide „Volksgarten“. Gruppiert wird bei gleichem, nicht leerem Stamm (Groß-/Kleinschreibung egal). Ohne Partner gibt es keine
  Park-Gruppe, sondern die 3 nächsten. Zusammengeführte Bereiche eines Platzes sind keine Nachbarn;
  (2) bis zu 2 Cafés aus dem Restaurant-Guide (Typ Café, ≤ 1 km, kanonische URL) – Block entfällt, wenn keins;
  (3) „Familien-Events {inStadtteil}“ (Kategorie Familie, gleicher Stadtteil; Events haben keine Koordinate).
- JSON-LD `Playground` mit `geo`, `address` (falls vorhanden). `isAccessibleForFree`: bei städtischen Plätzen falsch nur wenn
  `eintritt` = `ja`, sonst wahr (fehlendes OSM-`fee` lässt den Platz frei). Bei Abenteuerplätzen aus dem Pflichtfeld: `ja` → falsch,
  `nein` → wahr (ohne gültigen Wert gibt es die Zeile nicht, 4.6). Kein `aggregateRating`;
  BreadcrumbList aus derselben Kette wie die sichtbaren Brotkrumen.
- Title/Description: „{Name} {inStadtteil}“ ohne Gedankenstrich, z. B. „Spielplatz Hofgarten (Oederallee) in Pempelfort“,
  „Wasserspielplatz Volksgarten in Oberbilk“ (der Name trägt den Typ schon). Description aus Profil, sonst
  „{Typ} {inStadtteil}: Lage, Größe, Notfallnummer“. Dünnes Detail: Metadaten mit `noindex` und ohne Canonical, wie Stufe C
  in `web/app/guides/clubs/[slug]/page.tsx`. `seitenMetadaten({ noindex: true })` leistet das.

### 5.4 Indexierung
- Hub indexierbar.
- **Detail indexierbar nur mit** Profil-Beschreibung **und** ≥ 2 belegten Geräten (`quelle` `osm`, `zitat` oder `sichtung`, mit Beleg). Geräte aus dem Profil zählen mit, auch ohne OSM-Treffer. Vermutetes Alter ersetzt diese zwei Geräte
  nicht und macht eine Seite, die beides hat, nicht zu noindex. Typ Wasser/Wald allein reicht nicht. Sonst `noindex, follow`,
  ohne Canonical, nicht in der Sitemap, aber erreichbar und in Hub/Liste verlinkt.
- **Stadtteilseiten** `/guides/spielplaetze/stadtteil/{slug}` (`instant = false`) ab 5 **sichtbaren** Spielplätzen indexierbar.
  Dünne zählen mit. `zaehltFuerIndex` bleibt der Default (jeder sichtbare Ort) und darf nicht auf `istIndexierbar` umgebogen
  werden, sonst würden dünne Seiten die Schwelle nicht mehr füllen. Unter 5: `noindex, follow`, ohne Canonical, nicht in der
  Sitemap; `guideStadtteilMetadaten` macht das, weil `seitenMetadaten` bei noindex keinen Canonical setzt.
  Eigene schmale Spielplatz-Karte in `guide-stadtteil.tsx` (Name, Typ, Alter, Größe) statt Restaurant-Karte. Die sichtbare
  Liste enthält alle Spielplätze des Viertels. Die ItemList nur die indexierbaren (max. 30), URL = Spielplatz-URL.
  Schwelle und ItemList sind zwei Listen; `indexOrte` der bestehenden Komponente darf nicht beides sein.
- **Sitemap:** eigene Liste indexierbarer Detailseiten, `lastModified` aus `aktualisiert_am`; Stadtteilseiten über `GUIDE_HUBS`. Abgeschaltete URLs (inaktiv und `freigeschaltet_am` gesetzt) stehen nicht darin; ihre Antwort ist der 308 aus 5.5. Nie freigeschaltete Zeilen stehen ebenfalls nicht darin.

### 5.5 Proxy, Foto-Proxy, Karten-API
- `pfad-pruefung.ts`: `OrtHub`/`HUBS` + `spielplaetze`; `ortEntscheidung("spielplaetze")`: sichtbar = `aktiv && typ === "spielplatz"`,
  **ohne** Score; unbekannt oder nie freigeschaltet → direkte 404 im Proxy. **Abgeschaltet** (inaktiv **und** `freigeschaltet_am`
  gesetzt): dauerhafte Weiterleitung (Proxy-„umleiten“, 308) auf `/guides/spielplaetze/stadtteil/{slug}`. Der Slug ist
  `stadtteilSlug` aus `web/lib/landing.ts` (Anzeigename, gespeichertes `Hafen` → `medienhafen`), und nur wenn `kanonischerStadtteil`
  einen Treffer hat. Sonst auf `/guides/spielplaetze`. Eine einmal indexierte URL endet nie in einer 404. Tests in `seo-a1`/`seo-b` von `null` auf
  die neuen Entscheidungen umstellen. `OrtKopf` lädt dafür zusätzlich `stadtteil` und `extras->spielplatz->>freigeschaltet_am`.
- `/ort-foto/[slug]`: aktiver Spielplatz auch ohne `qualitaets_score` (eigener Zweig). Die Bildquelle ist `extras.google_foto` (Struktur aus §3), wie `ortBildUrl` bei den übrigen Orten, Urheber-Link über `autor_url`; `bild_url` bleibt leer. Ein inaktiver Slug, auch mit gesetztem `freigeschaltet_am`, antwortet 404 und leitet nicht weiter.
- `/api/guide-karte`: Zweig `hub=spielplaetze` mit eigener Punktfunktion (5.2).

**Zustände eines Platzes – was jede Stelle tut** (verbindliche Übersicht für den Bau):

| Stelle | nie freigeschaltet | aktiv | abgeschaltet | wieder freigeschaltet |
|---|---|---|---|---|
| Proxy `/guides/spielplaetze/<slug>` | 404 | 200 | 308 → Stadtteilseite (`stadtteilSlug`), ohne gültigen Stadtteil → Hub | 200 (gleicher Slug) |
| Sitemap | nein | ja, wenn indexierbar (5.4) | nein | ja, wenn indexierbar |
| `/ort-foto/<slug>` | 404 | Foto bzw. 404 ohne Foto | 404 | Foto bzw. 404 ohne Foto |
| Karte / Liste / `OrtLinkListe` / „In der Nähe“ | nein | ja | nein | ja |
| ItemList (Hub und Stadtteil) | nein | nur indexierbare, max. 30 | nein | nur indexierbare, max. 30 |
| Stadtteilseite (Liste, Schwelle 5) | zählt nicht | zählt | zählt nicht | zählt |
| Zahlen (Hero, `/guides`-Kachel, „X von Y“, Anzahl auf `/stadtteil/[slug]`) | zählt nicht | zählt | zählt nicht | zählt |
| IndexNow (Slugs aus dem `RETURNING` der SQL, Schritt 6) | – | beim Livegang, nur wenn indexierbar (Schritt 9) | alte URL einmal melden | URL einmal melden, nur wenn indexierbar |
| Event-Link „Spielplätze {inStadtteil}“ | über die Stadtteilseite, nur wenn sie ≥ 5 aktive Plätze hat (E16) | ← | ← | ← |
| Slug / Name aus Normalisierung | ändert sich | fest / nur über `anzeigename` | fest / nur über `anzeigename` | fest / nur über `anzeigename` |

Eine abgeschaltete Zeile mit sperrendem Code bleibt in der Spalte „abgeschaltet“, auch wenn `ausgeschlossen` null ist (Schritt 6).
Maßgeblich für die Spalten „aktiv“ und „wieder freigeschaltet“ ist allein `aktiv=true`: ein sperrender Code an einer aktiven Zeile ändert keine Zeile der Tabelle.

### 5.6 Einbaustellen außerhalb des Hubs
`/guides`-Kachel `fertig: true` (Zahl aus den Daten), `GUIDE_LINKS`, Popover-/Mobilmenü, Footer-Spalte Guides **und** der Markenabsatz
im Footer (`web/components/rahmen.tsx`, heute „Restaurants, Cafés, Kneipen, Bars und Clubs“), `EXTRA_LINKS.familie`
= „Spielplätze“, Event-Seite (E16, Linktext `Spielplätze ${inStadtteil(st)}`, nur wenn diese Stadtteilseite mindestens 5 aktive Spielplätze hat), `/stadtteil/[slug]` (automatisch über `GUIDE_HUBS`),
`llms.txt` (Abschnitt umbenennen in „Guides“ + Spielplätze-Zeile), Guide-Übersichtstext + FAQ „Welche Guides kommen noch dazu?“
(neue Antwort: „Neu ist der Spielplatz-Guide … in Arbeit sind Ausflüge und Wochenend-Trips“), Datenschutz (6.4).

### 5.7 Design, Barrierefreiheit, Mobil
Altersfarben aus dem Handoff mit Text; eigene Outline-SVGs für Schaukel, Rutsche, Sandkasten (2 px, 24er Raster, mit Label);
Icons mit `title`; Touch-Ziele ≥ 44 px; 375 px ohne horizontales Scrollen; Liste als Alternative zur Karte; hell und dunkel geprüft.
Der dunkle Hero nutzt die dunklen Flächentokens. Die helle Bildmaske aus Abschnitt 11 gilt nur für den hellen Hero.

---

## 6. Texte

### 6.1 Einleitung (Hub, Entwurf zur Freigabe)
„Hier findet ihr {anzahl} öffentliche Spielplätze in Düsseldorf – vom kleinen Sandkasten im Viertel bis zum Wasser- und
Waldspielplatz, dazu wenige betreute Abenteuerspielplätze mit festen Öffnungszeiten. Filtert nach Alter, Ausstattung und
Stadtteil oder lasst euch zeigen, was in eurer Nähe liegt. Bolzplätze, Skateanlagen und Indoor-Spielplätze sind nicht dabei.“

### 6.2 Fünf FAQs (Entwurf, Antworten mit internen Links, Texte vor dem Livegang zur Freigabe)
1. „Wo gibt es Wasserspielplätze in Düsseldorf?“ (inkl. Saison-Hinweis – keine sechste FAQ)
2. „Welcher Spielplatz eignet sich für Kleinkinder?“
3. „Wo finde ich Waldspielplätze?“
4. „Was bedeutet die Nummer auf dem Spielplatzschild?“
5. „Gibt es rollstuhlgerechte Spielplätze?“ – oder „Welche Spielplätze haben eine Toilette in der Nähe?“. Die Wahl fällt **einmal
   beim Festschreiben der Texte** nach dem OSM-Bericht (Schritt 2): FAQ-Texte sind Konstanten, keine Laufzeit-Bedingung.
FAQ 1 und 3 verlinken auf den Typ-Filter (`?typ=wasser` bzw. `?typ=wald`, noindex mit Canonical auf den Hub – zulässig).

### 6.3 Notfallnummer (Detailseite)
„**Notfallnummer 9601** – das ist keine Telefonnummer. Im Notfall die 112 wählen und diese Nummer nennen; sie steht auch auf dem
Schild am Spielplatz.“ Quelle: Stadt Düsseldorf. Fehlt die Nummer (4.1 Schritt 3), entfällt die Zeile.

### 6.4 Datenschutz (freigegeben, korrigierter Wortlaut)
In `/datenschutz` neuer Punkt:
> **Standortfunktion im Spielplatz-Guide.** Wenn Sie auf der Übersichtsseite des Spielplatz-Guides bei der Sortierung auf
> „In der Nähe“ tippen, fragt Ihr Browser, ob die Website Ihren Standort verwenden darf. Nur wenn Sie zustimmen, berechnet
> Ihr Browser auf Ihrem Gerät die Entfernung zu den Spielplätzen. Die Website erhält Ihren Standort dabei nicht und speichert
> ihn nicht. Die Freigabe können Sie jederzeit in den Einstellungen Ihres Browsers widerrufen. Der Link „In der Nähe“ auf
> einer Spielplatz-Seite springt nur zu den schon geladenen Angaben weiter unten und fragt den Standort nicht ab.

Zusätzlich im bestehenden Google-Maps-Absatz: „… und der Knopf ‚Route planen‘ im Spielplatz-Guide …“ ergänzen.

### 6.5 Haftung (Fuß der Detailseite)
„Angaben ohne Gewähr, Stand {profil_stand bzw. Datenstand der Stadt}. Geräte können umgebaut oder gesperrt sein.“

---

## 7. Tests

**Python:** WGS84-Pflicht/Koordinaten-Rechteck (Abbruch), Objektart-Text, Komma-Größe, Leerzeilen; Zusammenführung (9777 ×3 am selben
Punkt → 1; konstruierter Fall 40 m → 2 Plätze, Nummer behalten; Hanielpark 127 m → 2 Plätze, Nummer behalten; konstruierter Fall
> 150 m → 2 Plätze, Nummer unterdrückt; Bolzplatz mit gleicher Nummer zählt nicht; gleiche Größe → kleinerer Objektschlüssel);
Namen (GW mit Komma, Ksp/Wsp/Waldksp, Apostroph, „Str.“, `a.d.` → „an der“, `ggü.` → „gegenüber“, „Fritz./Mörsenb.“ → `name_unklar`, nie freigeschaltete Zeile bleibt inaktiv; freigeschaltete Zeile mit neuem unklarem Stadtnamen → kein `name_unklar`, Hinweis „Stadtname neu“);
Wiederholungsimport (Schnittmenge trifft eine Zeile; ein Schlüssel fehlt → `fehlende_teile`, die Zeile bleibt, der Slug bleibt, sobald sie einmal freigeschaltet war; Schlüssel wechseln die
Gruppe → Prüf-CSV, nichts automatisch teilen); gemischte Gruppe (10 m + 100 m → Teilgruppe + Einzelplatz, Code `gruppe_gemischt`);
`korrekturen.csv` (Anzeigename ersetzt Normalisierung und löscht `name_unklar`; Stadtteil löscht `kein_stadtteil`; `ausschliessen` hält inaktiv; `bestaetigt` hebt `access_private` und `gruppe_gemischt` auf, der Code bleibt in der Prüf-CSV; Eintrag am kleinsten
Schlüssel einer Gruppe, ein anderer Schlüssel derselben Gruppe ist ein Log-Fehler und wird nicht angewendet; fehlende Datei = keine Korrekturen; `abenteuer:`-Zeilen gehören nicht hierher); Slug ändert sich bei nie freigeschalteter Zeile mit neuem Namen, bei aktiver **und bei abgeschalteter** Zeile nicht (abgeschaltete Zeile + neuer Name → Slug bleibt, Weiterleitung greift); Name einer freigeschalteten Zeile nur aus `korrekturen.csv`;
Prüf-Codes (sperrend: `name_unklar`, `kein_stadtteil`, `access_private`, `gruppe_gemischt`; `bezirk_abweichend` und `zuordnung_mehrdeutig` sperren nicht; an einer schon aktiven Zeile bleiben sie Warnung, `aktiv` wird nicht falsch); Stadt-Import lässt `eintritt` und OSM-Codes stehen; `stadtteil`: Katalogwert aus `korrekturen.csv` vor Polygon (aktiv wie inaktiv, korrigiert auch einen Grenz-Treffer), Nicht-Katalogwert in `korrekturen.csv` → Log-Fehler, gespeicherter Stadtteil bleibt (neue Zeile: leer), Polygon gilt nicht, Code `kein_stadtteil`; Bezirkskontrolle nur bei Polygon-Treffer; Polygon-Fehltreffer lässt bei freigeschalteter Zeile den gespeicherten Stadtteil stehen, nie freigeschaltete Zeile ohne Treffer bleibt ohne Stadtteil und inaktiv; abgeschaltete Zeile mit sperrendem Code wird nicht wieder freigeschaltet; Score-Teilwerte, Größen-Perzentil als Vereinigung aus nicht ausgeschlossenen städtischen Plätzen ohne Sperr-Code und bereits aktiven städtischen Plätzen (auch mit Warn-Code), außerhalb dieser Menge Größen-Teilwert 0,5, Top = 20 % der indexierbaren, nicht ausgeschlossenen, danach aktiven Plätze; Ray-Casting (MultiPolygon, Loch, Rand);
`ausgeschlossen` aus der CSV gesetzt und bei leerem `ausschliessen` oder fehlendem Schlüssel wieder `null` (fehlende Datei lässt es stehen; leerer `grund` ist Log-Fehler und lässt das Feld stehen), Import ändert `aktiv` und `freigeschaltet_am` nie; `bestaetigt` mit `name_unklar` bzw.
`kein_stadtteil` wird ignoriert (Log-Fehler); `anzeigename` gesetzt und Rohzusatz unklar → `name_unklar` bleibt weg, Name aus `anzeigename`, bei nie freigeschalteter Zeile Slug daraus, sonst Slug unverändert; `stadt_fehlt_seit` → erst über `ausschliessen` ausgeschlossen;
`abenteuer_import` (Pflichtfelder, ungültiger Eintritt → nicht angelegt, Koordinate außerhalb → nicht angelegt, Stadtteil kein
Katalogwert → `kein_stadtteil` und die Spalte bleibt leer bzw. behält den alten Wert, Katalogwert beim Wiederholungsimport schreibt die Spalte und entfernt den Code, Träger nach `extras.spielplatz.traeger`, Wiederholungsimport über `schluessel`, `ausgeschlossen` gesetzt oder wieder `null`, Slug fest ab der ersten Freischaltung, auch nach dem Abschalten, gelöschter Schlüssel ändert weder `aktiv` noch `ausgeschlossen`,
DELETE nur bei `freigeschaltet_am` leer, städtisch wie `quelle='abenteuer'`; ungültige CSV-Zeile (fehlender Eintritt, Koordinate
außerhalb, `ausschliessen` ohne Grund) bei bestehender Zeile → Datenbankzeile unverändert; `bestaetigt` = `access_private` hebt den
OSM-Code auf, andere Codes in `bestaetigt` → Log-Fehler); aktive Zeile bekommt durch neuen OSM-Abgleich `access_private` → bleibt aktiv,
Warnung in der Prüf-CSV und bleibt in der Perzentil-Menge; Ausschluss aufgehoben und kein sperrender Code → Freischalt-Regel setzt `aktiv=true`, `freigeschaltet_am` bleibt der erste Tag; Score und Top bei erneutem Schritt 6 neu berechnet; Größen-Teilwert Abenteuer = 0,5 und nicht in der Perzentil-Menge;
`freischaltbar()` (nie freigeschaltet ohne Code → ja; `ausgeschlossen` gesetzt → nein; `name_unklar` bzw. `kein_stadtteil` → nein, auch
mit `bestaetigt`; `access_private` bzw. `gruppe_gemischt` → nein, mit `bestaetigt` → ja; nur Warn-Codes → ja; abgeschaltet, Ausschluss
aufgehoben, ohne Sperrcode → ja, `freigeschaltet_am` bleibt; abgeschaltet mit Sperrcode → nein; fehlendes `pruefung`/`bestaetigt` → wie
leer); Vorschau mit zwei Listen (Anschalten, Abschalten) und SQL-Datei nutzen dieselbe Bedingung (Text-Test auf `COALESCE`, `RETURNING` und den Filter auf den alten `aktiv`-Wert); zweiter Lauf ohne Änderung → beide Listen leer; DELETE-Bedingung mit
`freigeschaltet_am IS NULL` (Text-Test); neuer Platz → `aktiv=false`, Slug aus Name und Stadtteil, `pruefung`/`bestaetigt` als Array;
Wiederholungsimport schreibt `aktiv` nicht; Slug-Kollision in fester Reihenfolge (freigeschaltete zuerst, dann kleinster Schlüssel;
zweiter Import ohne Änderung → gleiche Slugs; Kollision mit Abenteuer- und anderen `orte`-Zeilen); Top = 20 % der indexierbaren, nicht
ausgeschlossenen, danach aktiven Plätze, alle anderen `top: false`;
Flingern Nord/Süd-Mapping; Bezirk aus `Nummer[:2]` (leer = kein Fehler, abweichend = Prüf-CSV); Adresse bleibt leer ohne `strasse_hausnr`;
OSM-Mapping inkl. `fee` → `eintritt` (nur städtisch; Abenteuer + OSM ohne `fee` → `eintritt` bleibt, abweichendes `fee` → nur Prüf-CSV), Zuordnung auch über die Abenteuer-Koordinate, Abenteuer ohne OSM-Treffer → `eintritt` bleibt, keine OSM-Codes; OSM-Lauf entfernt `access_private`, wenn das Tag weg ist; zwei Geräte mit Beleg aus dem Profil zählen ohne OSM-Treffer; Alter in der Reihenfolge von 4.5 (weniger als zwei Geräte → keins; Kleinkind und Schulkind im
Namen → belegt „alle“; vermutet ersetzt keine Geräte); Belegprüfung; Score; `ausstattung_import` (gültige Zeile schreibt `quelle: "sichtung"`; unbekannter Schlüssel/Merkmal, falscher Wert, leerer Beleg, ungültiges Datum, nicht kleinster Schlüssel, Dublette → Log-Fehler und nichts geschrieben; entfernte Zeile entfernt nur Sichtungs-Einträge; fehlende Datei ändert nichts; OSM und Profil überschreiben keine Sichtung); OSM-Zuordnung (Punkt in genau einer Fläche; keine Fläche → genau ein Kandidat ≤ 60 m; zwei Flächen oder mehrere Kandidaten → `zuordnung_mehrdeutig`, nichts übernommen), Geräte in der Fläche bzw. ≤ 30 m um einen OSM-Punkt, `;`-Werte getrennt; Sportflächen ≤ 40 m vom Punkt oder der Fläche, `access=private` ausgenommen, `sport=multi` nicht zugeordnet; Tischtennis/Fußball/Basketball zählen für Filter, Indexierung und Score, nicht fürs Alter; OSM-Lauf ersetzt alte OSM-Einträge, nie Sichtung oder Zitat; Top-Badge nur bei indexierbar; `istIndexierbar` gegen die gemeinsame Fixture (auch in vitest).

**Web (vitest):** Filter (UND, „alle“, unbekanntes Alter, Chip-Schwelle 4/5, Rollstuhl `limited` zählt nicht, X = mindestens ein
Gerät, Typ-Filter ODER inkl. Abenteuer), Titel „{Name} {inStadtteil}“, Sichtbarkeit ohne Qualitäts-Score, `istIndexierbar` (Beschreibung + 2 Geräte + vermutetes Alter → indexierbar; Geräte aus dem Profil mit Beleg zählen ohne OSM-Treffer;
Beschreibung + vermutetes Alter + 1 Gerät → nicht), Karten-Punkte ohne Bewertung/OSM-Tags, JSON-LD ohne `aggregateRating`,
`isAccessibleForFree` (städtisch: nur `eintritt=ja` setzt es auf falsch; Abenteuer: `ja` → falsch, `nein` → wahr), Foto (`google_foto` mit `autor_url`, Urheber-Link und `bild_attribution` vorhanden; `foto_manuell` verhindert Ersetzen); Zustandstabelle aus 5.5 je Zeile; Pfadentscheidungen (neue Fälle statt `null`; nie freigeschaltet → 404; abgeschaltet mit `freigeschaltet_am` → 308 über `stadtteilSlug`, gespeichertes `Hafen` → `medienhafen`, ohne gültigen Stadtteil auf den Hub; wieder freigeschaltet → 200, Sitemap und Karte führen die URL wieder), Sitemap ohne abgeschaltete URL, Foto-Proxy liest `google_foto` und antwortet 404 für einen inaktiven Slug, Trägerzeile nur wenn gesetzt,
Stadtteilseite ab 5 sichtbaren inklusive dünner, dünnes Detail ohne Canonical, Filter-URL mit Canonical auf den Hub,
Event-Link nur bei Familie mit `inStadtteil` und mindestens 5 aktiven Spielplätzen der Stadtteilseite, Saison-Hinweis nur für den Wasserbereich, Notfallnummer-Zeile entfällt ohne Nummer,
Öffnungszeiten nur bei Abenteuer, Namensstamm ohne Typwort und Klammer („Wasserspielplatz Volksgarten“ + „Spielplatz Volksgarten (…)“ gruppieren; ohne Partner → drei nächste),
Texte (5 FAQs, nur interne Links, keine Score-Zahl, ihr/euch).

---

## 8. Ablauf und Freigaben

| Schritt | Inhalt | Freigabe / Ergebnis |
|---|---|---|
| 1 | Stadt-Import (inaktiv) direkt per Skript wie beim Club-Import – **Freigabe des Auftraggebers für diesen Schreibweg vor dem ersten Lauf**; Prüf-CSV | Auftraggeber trägt Entscheidungen in `korrekturen.csv` ein; Import erneut |
| 2 | OSM-Abgleich + Bericht (Abdeckung) | Entscheidung, ob Runde 2 der Profile nötig ist |
| 3 | Abenteuer-Liste in `abenteuer.csv` (`abenteuer_import.py`, Zeilen inaktiv), danach OSM-Abgleich dieser Koordinaten (4.2) | Auftraggeber bestätigt Name, Koordinate, Öffnungszeiten, Eintritt; die Plätze laufen in Schritt 4/5 mit (Runde 1) |
| 4 | Google Runde 1 (Kosten vorher) + Foto-Sichtung | Foto-SQL |
| 5 | Profile: Probe 10 → Bericht → Rest Runde 1 | Gegenlesen |
| 6 | Score und Top-Badge (`score.py`, 4.5), **Freischalt-SQL** (städtisch und Abenteuer; feste Datei `database/spielplaetze_freischalten.sql`, Bedingung mit `COALESCE(…, '[]')` auf `pruefung` und `bestaetigt`, endet mit `RETURNING slug, aktiv`; vorher zeigt `freischalt_vorschau.py` lesend zwei Listen: **Anschalten** = `aktiv=false` und `freischaltbar(zeile)` (getestete reine Funktion), **Abschalten** = `aktiv=true` und `ausgeschlossen` gesetzt. Beide UPDATE filtern auf den alten Wert (`WHERE aktiv=false …` bzw. `WHERE aktiv=true …`), damit `RETURNING` nur Zeilen liefert, deren `aktiv` sich ändert): `aktiv=true` und `freigeschaltet_am` (falls leer) nur für Zeilen mit `ausgeschlossen IS NULL` und ohne sperrenden Prüf-Code – `name_unklar` und `kein_stadtteil` sperren immer, `access_private` und `gruppe_gemischt` nur, wenn sie nicht in `bestaetigt` stehen; `bezirk_abweichend` und `zuordnung_mehrdeutig` sperren nicht. Sperrende Codes wirken nur hier: eine schon aktive Zeile mit neuem sperrendem Code bleibt aktiv (Warnung in der Prüf-CSV). Score und Top bei jedem Durchlauf neu, Perzentil-Menge nach 4.5. Eine zuvor abgeschaltete Zeile wird nur wieder aktiv, wenn `ausgeschlossen` null ist und kein sperrender Code steht (`name_unklar` und `kein_stadtteil` sperren immer, `access_private` und `gruppe_gemischt` nur ohne `bestaetigt`); `freigeschaltet_am` bleibt der erste Tag, der Slug bleibt. **Abschalt-SQL** (in derselben Datei, ebenfalls mit `RETURNING slug`) im selben Schritt und bei jeder späteren Aktualisierung: `aktiv=false` für aktive Zeilen mit gesetztem `ausgeschlossen` (die URL leitet danach weiter, 5.5). Das Rücknahme-DELETE verlangt zusätzlich `freigeschaltet_am IS NULL` (4.1, 4.6) | Auftraggeber führt SQL aus |
| 7 | Website, Texte (6.1/6.2 zur Freigabe), Illustrationen eingebaut | Cursor-Check |
| 8 | Tests, Build, Browser (Desktop/Mobil, hell/dunkel) | Deploy nur nach OK |
| 9 | IndexNow (Hub, Stadtteilseiten, indexierbare Details), Sitemap-Kontrolle. Die Detail-Slugs kommen aus dem `RETURNING` der SQL (Schritt 6): `aktiv=true` nur melden, wenn die Seite nach 5.4 indexierbar ist; `aktiv=false` als alte URL. Nach einer späteren Abschalt-SQL die alte Detail-URL einmal melden, damit der 308 gelesen wird; eine wieder freigeschaltete URL einmal melden, wenn sie nach 5.4 indexierbar ist | Bericht |
| 10 | Nach 4 Wochen: Suchanfragen (Bing/Google) auswerten, FAQ nachschärfen | Bericht |

Nicht in dieser Runde: Meldefunktion für Nutzer, Neuss/Ratingen, Bolzplätze/Skaten, Indoor-Spielplätze, Clustering der Karte.

## 9. Kosten (Schätzung, vor dem Lauf konkret nennen)
Stadt, Stadtteilgrenzen, OSM: 0 $. Google Runde 1 und die Profile gelten für die 108 städtischen Plätze und jede Zeile aus `abenteuer.csv`. Für die 108: Umkreissuche grob 2–4 $, Foto-Sichtung ≈ 60 Plätze × 10 Fotos grob 4 $, Profile 108 × 0,05–0,10 $ ≈ 6–11 $, zusammen ≈ 12–19 $. Die Abenteuerplätze kommen in derselben Größenordnung je Platz dazu; ihre Zahl und die Summe nennt der Lauf vorher (E14). Runde 2 (74 Plätze) zusätzlich ≈ 4–8 $. Rahmen E14: 40 $.

## 10. Risiken und Gegenmaßnahmen
| Risiko | Gegenmaßnahme |
|---|---|
| Stadtdaten von 2020, neuere Plätze fehlen | OSM-only-Liste, Abenteuer-Liste, „Datenstand“ sichtbar |
| OSM-Abdeckung gering → kaum Geräte | Bericht in Schritt 2; Profile Runde 2; ehrliche „X von Y erfasst“-Anzeige |
| Viele „keine Angabe“ wirken leer | Chip-Schwelle 5, Hinweis über der Liste, Illustrationen, Detailseiten noindex |
| Falsche Notruf-Info | Zusammenführung + Unterdrückung bei > 150 m, Wortlaut 6.3, Quelle |
| Kinder auf Fotos | nur Sichtprüfung, sonst Illustration |
| Falscher Stadtteil | Punkt-in-Polygon mit Prüf-CSV, Korrektur über einen Katalogwert in `korrekturen.csv` |
| Abenteuer-Eintritt von OSM überschrieben | OSM schreibt `eintritt` nur bei städtischen Plätzen (4.2) |
| Freischalt-SQL schaltet still nicht frei | `pruefung`/`bestaetigt` immer als Array, `COALESCE`, Vorschau und `RETURNING` (Schritt 6) |
| Name falsch aufgelöst | Prüf-CSV, nie freigeschaltete Plätze bleiben mit `name_unklar` inaktiv, `anzeigename` entfernt den Code und lässt die Namensbildung aus; freigeschaltete Plätze behalten ihren Namen (kein Code, nur Hinweis „Stadtname neu“), Korrektur über `korrekturen.csv` (Schlüssel statt Name) |
| Slug-Änderung nach Livegang | Ab der ersten Freischaltung ist der Slug für immer fest, auch nach dem Abschalten. Davor bildet jeder Import ihn aus dem aktuellen Anzeigenamen neu |
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
- 344 städtische Spielplätze (bzw. Zahl nach Ausschlüssen) korrekt importiert, dazu die Zeilen aus `abenteuer.csv`; Stichprobe von 30: Name, Stadtteil, Notfallnummer stimmen.
  Hanielpark ist zwei Plätze, die sechs Gruppen auf einem Punkt sind je einer.
- Alle Wasser-, Wald- und Abenteuerspielplätze mit Profil; ≥ 60 Plätze mit ≥ 2 belegten Geräten und Altersangabe (belegt oder vermutlich).
- Abschalten getestet: eine abgeschaltete Testzeile leitet dauerhaft auf ihre Stadtteilseite weiter (`stadtteilSlug`, gespeichertes `Hafen` → `/guides/spielplaetze/stadtteil/medienhafen`), ohne gültigen Stadtteil auf den Hub; eine nie freigeschaltete liefert 404. Die abgeschaltete URL fehlt in der Sitemap, `/ort-foto` für denselben Slug liefert 404.
- Wiederfreischaltung getestet: Ausschluss aufheben, Freischalt-SQL → 200 unter demselben Slug, wieder in Sitemap (wenn indexierbar)
  und Karte, `freigeschaltet_am` unverändert.
- Keine Fotos mit Personen; jedes Foto mit Urheber; Illustrationen eingebaut.
- Hub, Detail, Stadtteilseiten: Inhalt im ersten HTML; Index-/Canonical-Regeln wie 5.4; JSON-LD valide, ohne Bewertungen; Proxy 404 für
  unbekannte Slugs; Karten-API ohne Bewertung/OSM-Tags.
- Filter/Karte/„In der Nähe“ funktionieren (Desktop, 375 px, hell/dunkel); Datenschutz- und Footer-/Menü-Links ergänzt.
- Alle Tests grün; Cursor-Check ohne kritische/mittlere Befunde; Deploy nach OK; IndexNow gemeldet.

## 13. Offene Punkte
Keine offenen Produktentscheidungen. Vor dem Livegang liegen zur Freigabe vor: die Texte 6.1/6.2 (FAQ 5 wird dabei einmal gewählt, nach dem OSM-Bericht) und die Zeilen in `abenteuer.csv`.

## 14. Prüfhistorie
- Entwurf 12.11. → Cursor-Prüfung 1: Dateistand 2020, Objektart als Text, Koordinaten nur aus `geometry`, Score nicht in
  `qualitaets_score`, Foto-Proxy, Proxy-Route, `instant = false`, Indexregel, Abenteuerspielplätze, kein stiller Standort-Fallback.
- Zweite Durchsicht (Claude): Stadtteilgrenzen-Datensatz, Notfallnummer-Dubletten, Parks, GW, Saison, Icons, Illustrationen, Dark Mode,
  Datenschutz, Event-Links, Haftung, Erfolgsmessung.
- Cursor-Prüfung 2: Adressliste ohne Koordinaten (→ keine „nahe“-Adresse), nur WGS84-Stadtteildatei, Proxy-Zweig ohne Score,
  Notfallnummer-Statistik, Bezirk aus `Nummer[:2]`, Google-Umfang 109, eigene Sitemap-Liste, eigene Karten-Punkte, Event-Link nur
  Familie mit `inStadtteil`, Handoff-Abweichungen (Stadtmitte, WC-Kreuz), Datenschutz-Wortlaut + Maps-Absatz, Tests, Bild-Prompts,
  weitere Einbaustellen, `extras` laden.
- Konsolidierung (Claude, 12.11.): Dubletten sind Teilflächen → Zusammenführung 351 → 343 bei 150 m; vermutetes Alter für Filter/Pin;
  Chip-Schwelle 5; Slugs vor Freischaltung fest; Rücknahme-Weg; Datenmodell; Titel/Description-Muster; Hinweis „X von Y erfasst“;
  `OrtLinkListe` mit allen; kein Stadtteil-Block unten; Quellen-Fuß; Ablauf mit Freigaben; Abnahme-Stichprobe.
- Cursor-Prüfung 3: 150 m fasst Hanielpark (127 m) zu weit → Zusammenführung nur ≤ 30 m, **351 → 344**, Nummer dort behalten;
  Runde 1 an den zusammengeführten Plätzen = **108** (9 + 20 + 79), nicht 109; Altersformel mit fester Reihenfolge; Wiederholungsimport
  über Schlüssel-Schnittmenge; `eintritt`, Koordinate je Teil, `fehlende_teile`; Freischalt-SQL mit Ausschlüssen; DELETE nur vor der
  Freischaltung; Filter-Canonical nicht über `seitenMetadaten`; Stadtteil-ItemList nur indexierbar; X/Y definiert; Datenschutz-Satz nur
  für den Sortier-Knopf; Titel „{Name} – {inStadtteil}“; Footer-Markenabsatz; Tests nachgezogen.
- Vierte Durchsicht (Claude, 12.11.): Runde 2 = **74** Kinderspielplätze (die frühere 85 zählte alle Typen im Größenband; Kinder
  allein sind roh wie zusammengeführt 74 – Korrektur nach Cursor-Prüfung 4); Rückweg der Prüf-CSV über eingecheckte
  `korrekturen.csv` (Schlüssel statt Name, ersetzt `NICHT_IM_HUB`), Slug bis zur Freischaltung neu, danach fest; Prüf-Codes
  `extras.spielplatz.pruefung` als Grundlage der Freischalt-SQL; Typ `abenteuer` mit Öffnungszeiten; Typ-Filter Wasser/Wald/Abenteuer;
  gemischte Gruppen; Score-Formel und Top-Grundmenge; FAQ 5 beim Festschreiben; Titel ohne Gedankenstrich; Freigabe des Schreibwegs.
- Cursor-Prüfung 4 (12.11., eingearbeitet): Sperr-Codes sind genau vier, `bestaetigt` hebt sie auf; 4.7 folgt der Namensregel aus 4.1;
  Abenteuer in eigener CSV mit Pflicht-`eintritt` und Öffnungszeiten auf der Detailseite; Stadt-Import lässt OSM-Felder stehen;
  Größen-Perzentil über die freischaltbare Menge; Namensstamm vor der Klammer; Runde 2 ist roh und nach Zusammenführung 74.
- Fünfte Durchsicht (Claude, 13.11.): Ausschluss als Datenbankfeld `ausgeschlossen` (die SQL kann keine CSV lesen); Abschalt-SQL und
  `freigeschaltet_am`, abgeschaltete Plätze leiten dauerhaft auf die Stadtteilseite bzw. den Hub weiter statt 404; `stadt_fehlt_seit`
  endet über `ausschliessen`; Abenteuerplätze inaktiv angelegt, gleiche Freischaltung, in Runde 1 (Profil, Google, Fotos), Import-Regeln
  (Pflichtfelder, Eintritt Pflicht ohne Weglassen-Fall, Katalog-Stadtteil, Wiederholungsimport, Slug, eigener DELETE); `bestaetigt` nur
  für `access_private`/`gruppe_gemischt`; Größen-Teilwert Abenteuer neutral; Namensstamm ohne Typwort und Klammer; Tests und Abnahme
  nachgezogen.
- Cursor-Prüfung 5 (13.11., eingearbeitet): `ausgeschlossen` setzt jeder Import neu (`null`, wenn der Ausschluss entfällt; fehlende Datei lässt es stehen; leerer Grund ist ein Log-Fehler). Beide DELETE verlangen `freigeschaltet_am IS NULL`, damit eine abgeschaltete Zeile den 308 behält. OSM-Abgleich auch über die Abenteuer-Koordinate, nach Schritt 3 und vor den Profilen; Geräte mit Beleg aus dem Profil zählen für die zwei Geräte der Indexierung. Abgeschaltete URLs fehlen in der Sitemap, der Foto-Proxy antwortet 404, IndexNow meldet die alte URL einmal. Weiterleitungsziel ist `stadtteilSlug` (`Hafen` → `medienhafen`), sonst der Hub. Kosten in Abschnitt 9 nennen die Abenteuerplätze zusätzlich zu den 108.
- Sechste Durchsicht (Claude, 13.11.): Sperrende Codes wirken nur bei der Freischaltung (aktive Zeile bleibt aktiv, Warnung);
  `abenteuer.csv` mit `bestaetigt` für `access_private`; ungültige CSV-Zeile lässt eine bestehende Abenteuerzeile unverändert;
  IndexNow auch bei Wiederfreischaltung; Score/Top bei jedem Schritt 6 neu; Tests dazu.
- Cursor-Prüfung 6 (13.11., eingearbeitet): Perzentil-Menge umfasst auch bereits aktive städtische Plätze mit Warn-Code; ausgeschlossene Plätze zählen nicht mit. `stadtteil` schreibt der Wiederholungsimport: inaktiv aus Polygon oder CSV, aktiv nur aus einem Katalogwert der CSV, ein Fehltreffer lässt den gespeicherten Wert stehen; ein Nicht-Katalogwert aus `abenteuer.csv` schreibt die Spalte nicht. „Bleibt inaktiv“ gilt nur für noch nie aktive Zeilen. Test für die Wiederfreischaltung (200, Sitemap, Karte, `freigeschaltet_am` bleibt). Gewähltes Foto nach `extras.google_foto`, geschützt durch `foto_manuell`. Doppelten Historienabsatz entfernt. Feld `traeger`.
- Siebte Durchsicht (Claude, 13.11.): **Slug-Regel an `freigeschaltet_am` statt an `aktiv`** – vorher hätte ein Import den Slug einer
  abgeschalteten Zeile neu gebildet und damit die Weiterleitung und die zugesagte Wiederfreischaltung mit gleichem Slug gebrochen
  (Begriffe in 3.1: nie freigeschaltet / freigeschaltet / abgeschaltet); Stadtteil aus `korrekturen.csv` hat immer Vorrang vor dem Polygon
  (vorher widersprachen „nur bei kein_stadtteil“ in 3.1 und die Regel in 4.1), Nicht-Katalogwert dort Log-Fehler; Foto-Struktur wie bei
  Clubs inkl. `autor_url` und `bild_attribution`; abgeschaltete Zeile mit sperrendem Code wird nicht wieder freigeschaltet;
  Zustandstabelle in 5.5; Tests nachgezogen.
- Cursor-Prüfung 7 (13.11., eingearbeitet): Steht `anzeigename`, entfällt die Namensbildung und `name_unklar` wird nicht gesetzt. Eine abgeschaltete Zeile wird nur wieder aktiv, wenn `ausgeschlossen` null ist und kein sperrender Code steht. Ein Nicht-Katalogwert in `korrekturen.csv` lässt den gespeicherten Stadtteil stehen, das Polygon gilt dann nicht. Abenteuer-Slug fest ab der ersten Freischaltung. Event-Link nur ab 5 aktiven Plätzen der Stadtteilseite. `foto_version` startet bei 1. Zustandstabelle um ItemList, „In der Nähe“ und den Fall „abgeschaltet mit Sperr-Code“ ergänzt.
- Achte Durchsicht (Claude, 13.11., nach Cursor-Prüfung 7): OSM schreibt `eintritt` nur bei städtischen Plätzen (vorher konnte ein
  OSM-Lauf den Pflicht-Eintritt eines Abenteuerplatzes auf `null` setzen); der Import schreibt `aktiv` nur beim Anlegen; `pruefung` und
  `bestaetigt` immer als Array, Freischalt-SQL als feste Datei mit `COALESCE`, Vorschau, `RETURNING` und getesteter Funktion
  `freischaltbar()`; `name_unklar` nur an nie freigeschalteten Zeilen; Nicht-Katalog-Stadtteil in beiden CSV-Dateien gleich (Log-Fehler,
  Spalte bleibt, `kein_stadtteil`); Top-Grundmenge, `score.py` und gemeinsame Fixture für `istIndexierbar`; feste Slug-Reihenfolge bei
  Kollisionen; Zustandstabelle um Zahlen und `RETURNING`-Listen ergänzt; Wiederfreischaltung in der Abnahme; Satzbau 3.1, E2, Perzentil
  nach `bestaetigt`, Bezirkskontrolle nur bei Polygon-Treffer, OSM-Codes je Lauf neu.
- Cursor-Prüfung 8 (13.11., eingearbeitet): E2 an `aktiv=true` geknüpft (eine aktive Zeile mit neuem sperrendem Code bleibt auf Karte,
  Liste und in den Zahlen); Vorschau mit zwei Listen, beide UPDATE filtern auf den alten `aktiv`-Wert, `RETURNING` liefert nur
  Änderungen, IndexNow meldet daraus `aktiv=true` nur indexierbar und `aktiv=false` als alte URL; Top-Wortlaut in §7 angeglichen.
- Ergänzung nach Freigabe (Auftraggeber, 13.11.): Tischtennis, Fußball und Basketball als Filter-Geräte, Volleyball und Skaten als
  Nebengeräte (OSM-Sportflächen ≤ 40 m, 4.2); OSM-Zuordnung „Fläche zuerst“ und Geräte-Zuordnung präzisiert;
  Ausstattung von Hand über `ausstattung.csv` (3.2) mit `quelle: "sichtung"`, die OSM und Profil nie überschreiben.
