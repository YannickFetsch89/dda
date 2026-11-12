# Plan: Guide „Spielplätze“ (`/guides/spielplaetze`)

Stand 12.11.2026 · Gegenprüfung (Cursor) und zweite Durchsicht (Claude, Abschnitt 0.3) eingearbeitet · noch nichts umgesetzt

Ziel: Eltern finden den passenden städtischen Spielplatz nach Alter, Ausstattung, Stadtteil und Nähe. Dieselben Qualitätsregeln wie bei den anderen Guides: nur belegte Angaben, eine URL pro Ort, Inhalt in der ersten HTML-Antwort, SEO-Text mit fünf FAQs, Deploy nur nach OK. SQL führt der Auftraggeber aus.

Die Entscheidungen S1–S9 sind damit getroffen. Abweichungen stehen in Abschnitt 0 und gelten vor dem ursprünglichen Entwurf.

---

## 0. Verbindlich nach der Gegenprüfung

### 0.1 Daten, die der Entwurf falsch beschreibt

Geprüft an der Datei der Stadt (Open Data Düsseldorf, Datensatz „Notfallnummern auf städtischen Spielplätzen“, Lizenz auf dem Portal: Datenlizenz Deutschland – Zero – Version 2.0):

| Behauptung im Entwurf | Befund |
|---|---|
| Datei vom 11.11.2026, monatliches Diff | Die Ressourcen (CSV, GeoJSON) sind seit **25.09.2020** unverändert. Das Portal nennt das Intervall **jährlich**. Der Datensatz-Stempel 09.06.2026 ist nur Metadaten. Kein monatlicher Abgleich. |
| 413 Leerzeilen | Stimmt für das **GeoJSON**: 846 Features, davon 413 ohne Eigenschaften und 433 Punkte. Die CSV hat 433 Datenzeilen und keine Leerzeilen. |
| Filter auf Objektart-Codes `336`, `536`, `337` | Der Wert ist Text: `336 Kinderspielplatz`, `536 Waldkinderspielplatz`, `337 Wasserspielplatz`, dazu `338 Bolzplatz` (71), `538 Waldbolzplatz` (5), `335 Skateranlage` (3), `333 Freizeitanlage` (3). Ein Zahlenvergleich trifft nichts. |
| Koordinaten aus CSV oder aus `latitude`/`xkoord` | In der CSV sind Breite und Länge durch Tausenderpunkte zerstört (`5.123.280.449` statt `51.23280449`). Im GeoJSON sind `xkoord`/`ykoord` ebenfalls unbrauchbar. **Einzige Quelle: `geometry.coordinates` der WGS84-Datei.** Jeder Punkt muss in 6,6–7,0 °O und 51,1–51,4 °N liegen, sonst Abbruch. |
| Größe als Zahl | `groesse` ist ein Text mit Komma (`664,1`). |

Lizenzfrage: maßgeblich ist das Portal der Stadt, nicht der NRW-Spiegel. Die FAQ der Stadt erlaubt die kommerzielle Nutzung unter dl-de/zero-2.0. Vor dem Import die URL und den Lizenznamen in `extras.spielplatz.lizenz` festhalten. Den Import nicht auf eine Rückfrage an den NRW-Spiegel warten lassen.

ODbL: Die Koordinate bleibt die der Stadt. OSM liefert nur Eigenschaften. Auf jeder Seite mit OSM-Angaben „Ausstattung: © OpenStreetMap-Mitwirkende“. Den OSM-Rohauszug nicht veröffentlichen und kein öffentliches API, das diese Felder ausliefert. Einzelne Tags anzuzeigen ist damit ein Produced Work und reicht.

### 0.2 Was der Code heute noch nicht kann

`/guides/spielplaetze/…` ist absichtlich noch keine Route: `routeVon` gibt `null` zurück, die Tests in `seo-a1.test.ts` und `seo-b.test.ts` halten das fest. `GuideHub` kennt den Hub nicht. `orteLaden` und `ortLaden` verlangen `qualitaets_score >= 7`. Der Foto-Proxy lädt über `ortLaden` und danach nur Clubs. Wer den Spielplatz-Score in `qualitaets_score` schreibt, lässt die Plätze in anderen Abfragen auftauchen oder, wenn der Score unter 7 liegt, unsichtbar bleiben. Der Score bleibt in `extras.spielplatz.score`.

Stadtteilseiten, Sitemap und die Links auf Event- und Stadtteilseiten hängen an `GUIDE_HUBS` und `hubOrte`. Der neue Hub muss dort einen Zweig bekommen, sonst zieht ein Eintrag in `GUIDE_HUBS` die falschen Orte. Die Karten auf Stadtteilseiten sind Restaurant-Karten. Für Spielplätze eine eigene, schmale Karte (Name, Typ, Altersangabe), nicht die Restaurant-Karte.

`instant = false` auf Hub, Detail und Stadtteilseite, sonst fehlt der Inhalt in der ersten HTML-Antwort. Unbekannte Slugs mit einer direkten 404 im Proxy beantworten, nicht mit `notFound()` in der Seite und nicht mit Rewrite.

Der Handoff-Ordner liegt **außerhalb des Repos**, aber lokal vor: `C:\Claude_DDD\design_v2\ddd_handoff_v2\14_spielplaetze\`
(`README.md` mit Ansicht 23/25, `data/spielplaetze.json` mit Altersfarben, Ausstattungs-Icons und Extras). Er ist die
Design-Vorlage; ergänzend `DESIGN_PROMPTS_GUIDES.md` (Repo), Abschnitt 10. Korrekturen gegenüber beiden: MapLibre statt
Leaflet, Anrede **ihr/euch** wie die anderen Guides (Hero-Subline nicht „finde den perfekten für dein Kind“), kein
Hero-Foto mit Kindern, Zahl im Hero aus den Daten (nicht „230“).

### 0.3 Zweite Durchsicht (Claude, 12.11.2026) – geprüft an Daten und Code

| Punkt | Befund | Folge für den Plan |
|---|---|---|
| Stadtteilflächen | Datensatz **„Stadtteilgrenzen Düsseldorf 2025“** (Open Data, dl-de/zero-2.0) existiert; dazu „Zuordnung der Stadtteile zu den Stadtbezirken“ (dl-de/zero-2.0) | Quelle für 3.1 Schritt 4. Plausibilitätsprüfung: Stadtbezirk aus dem Punkt-in-Polygon muss zum Feld `stadtbezirk` der Spielplatzdatei passen, sonst Prüf-CSV |
| Notfallnummern | Alle 351 Plätze haben eine Nummer, aber **8 Nummern sind doppelt** vergeben | Doppelte nur anzeigen, wenn beide Plätze im selben Park liegen (≤ 150 m); sonst Prüf-CSV und Zeile weglassen, bis geklärt. Eine falsche Notruf-Angabe ist schlimmer als keine. Text: „Die Nummer steht auch auf dem Schild am Spielplatz.“ |
| Mehrere Plätze je Park | Hofgarten, Rheinpark, Zoopark, Volksgarten, Alter Gerresheimer Friedhof u. a. haben je 3+ Plätze | Name „Spielplatz Hofgarten (Oederallee)“; auf der Detailseite zuerst „Weitere Spielplätze im Hofgarten“, dann die nächsten. Überlappende Pins: bei 351 DOM-Markern ohne Clustering akzeptabel; Clustering erst, wenn es im Browser stört |
| Unklare Abkürzungen | Präfix **„GW“** (z. B. „GW RATH/ELLER“, „GW TANNENHOF“, „GW GARATH SW“) | Bedeutung nicht raten → Frage an den Auftraggeber bzw. Stadt; bis dahin Name ohne Präfix aus dem Teil nach dem Komma bilden und in die Prüf-CSV |
| Typ vs. Name | „VOR DEM DEICH, Ksp 'Wind,Wasser,Sonne'“ ist als Wasserspielplatz geführt | Typ immer aus `objektart`, nie aus dem Namen |
| Auswahl für Google/Profile | 9 Wasser, 20 Wald, 86 Plätze ≥ 3.000 m², 171 ≥ 1.500 m² | Erste Runde: Wasser + Wald + ≥ 3.000 m² (≈ 110 Plätze); 1.500–3.000 m² erst nach Bericht. Damit bleiben Google und KI deutlich unter S9 |
| Wasserspielplätze saisonal | Die Stadt schaltet das Wasser per Pressemitteilung frei und bei Trockenheit auch ab | Feld `saison` nur mit Beleg („laut Stadt in der Regel Mai bis September“), sonst Hinweis „Wasser nur in der warmen Jahreszeit, Betrieb kann ruhen“. Eine FAQ dazu |
| Eigene Icons | Handoff verlangt eigene SVGs für Schaukel, Rutsche, Sandkasten | In 4.6 aufgenommen (Outline, 2 px, 24er Raster, mit Label) |
| Typ-Illustrationen (S5) | Für Plätze ohne freigegebenes Foto | Drei Motive (Spielplatz, Waldspielplatz, Wasserspielplatz) ohne Personen; Bild-Prompts liefern wie bei „Über uns“, der Auftraggeber erzeugt die Bilder |
| Dunkles Design | Heller Hero `#FFF6E6` ist nur hell definiert | Farben als Tokens mit Dark-Variante, Pins/Legende in beiden Modi prüfen |
| Datenschutz | „In der Nähe“ nutzt die Standortfreigabe des Browsers (nur lokal) | Ein Satz in der Datenschutzerklärung (Text vom Auftraggeber freigeben) |
| Interne Links | Familien-Events haben Stadtteil, aber keine Koordinate | Event-Seiten der Kategorie Familie verlinken „Spielplätze in {Stadtteil}“, sobald die Stadtteilseite existiert (über `stadtteileImHub`, neuer Zweig `zaehltFuerIndex` = alle sichtbaren) |
| Haftung | Geräte werden gesperrt/umgebaut | Fuß der Detailseite: „Angaben ohne Gewähr, Stand …; vor Ort kann es Abweichungen geben.“ |
| Erfolgsmessung | – | Nach 4 Wochen Suchanfragen in Bing/Google prüfen (Spielplatz + Stadtteil, Wasserspielplatz, Waldspielplatz) und die FAQ danach nachschärfen |

**Entscheidungen des Auftraggebers (12.11.2026):**
1. **„GW“ ist unbekannt.** Regel: Präfix „GW“ entfällt im Anzeigenamen, der Rest wird normal gebildet
   („GW TANNENHOF, Wsp Tannenhof“ → „Wasserspielplatz Tannenhof“; „GW RATH/ELLER, Ksp Gutenbergstr.“ → „Spielplatz
   Gutenbergstraße (Rath/Eller)“). 43 Einträge der Datei tragen „GW“; abgekürzte Straßen wie „Fritz./Mörsenb.“ nicht
   auflösen, sondern in die Prüf-CSV. `objektbezeichnung` bleibt unverändert in `extras.spielplatz.stadt_name`. Alle GW-Fälle
   stehen in der Prüf-CSV; keine Deutung des Kürzels im Text.
2. **Typ-Illustrationen** erzeugt der Auftraggeber selbst; die Prompts stehen in Abschnitt 10.
3. **Datenschutz-Satz freigegeben** (Wortlaut in Abschnitt 11); Einbau in `/datenschutz` zusammen mit dem Livegang.
4. **Filter „Rollstuhlgerecht“** (Extras-Zeile) erscheint, sobald mindestens fünf sichtbare Plätze das belegt haben
   (OSM `wheelchair=yes` oder Zitat). „Teilweise“ (`wheelchair=limited`) zählt nicht für den Filter, steht aber auf der
   Detailseite.

---

## 1. Ausgangslage

### 1.1 Daten

| Quelle | Was sie trägt | Nutzung |
|---|---|---|
| Stadt Düsseldorf, GeoJSON WGS84, dl-de/zero-2.0, Dateistand 25.09.2020 | 322 Kinderspielplätze, 20 Waldkinderspielplätze, 9 Wasserspielplätze, plus Bolz-, Skater- und Freizeitanlagen | Rückgrat. Koordinate, Name, Stadtbezirk, Größe, Notfallnummer, Objektschlüssel. Keine Ausstattung, kein Alter, keine Fotos. |
| OpenStreetMap `leisure=playground` | Geräte, `min_age`/`max_age`, Belag, Rollstuhl, Eintritt | Nur Eigenschaften, Zuordnung über die Stadt-Koordinate. Plätze nur in OSM (neu seit 2020, Abenteuerspielplätze) in eine Prüf-CSV, nicht automatisch anlegen. |
| Google Places, Typ `playground` | Bewertung, Fotos | Nur für die Profil-Auswahl, über den vorhandenen Places-Client. Kein flächiges Gitter. |
| Neuss, Ratingen | PDF 2023 bzw. keine offenen Daten | Nicht in dieser Runde. |

Abenteuerspielplätze des Jugendamts stehen nicht in der Gartenamt-Datei. Eine kurze manuelle Liste (Name, Koordinate, Quelle) kommt vor dem Livegang dazu, sonst fehlen die Plätze, die Eltern dem Namen nach suchen. Das blockiert den Import der 351 städtischen Plätze nicht.

### 1.2 Wiederverwenden

Karte (MapLibre, PMTiles, `GuideKarteLazy`, `/api/guide-karte`), Filterchips, `GuideEinleitung` / `GuideSeoText`, Stadtteil-Mechanik, Sitemap, IndexNow, Foto-Proxy. Die Event-Kategorie Familie für den Block auf der Detailseite.

---

## 2. Entscheidungen

| Nr. | Entscheidung |
|---|---|
| S1 | Kinderspielplätze, Waldkinderspielplätze, Wasserspielplätze (351). Bolzplätze, Waldbolzplätze, Skateranlagen und Freizeitanlagen nicht. Keine Indoor- oder kommerziellen Spielplätze. Der Einleitungssatz sagt das, damit die Karte nicht vollständig wirkt, wo sie es nicht ist. |
| S2 | Jeder Platz aus S1 mit gültiger Koordinate kommt auf die Karte. `aktiv=true` nach einer Stichprobe der Namen-CSV, nicht nach einer Einzel-Freigabe wie bei Clubs. `NICHT_IM_HUB` nur für Schulhöfe ohne öffentlichen Zugang, Dubletten und nachweislich abgebaute Plätze. Der interne Score steht nicht in `qualitaets_score`. |
| S3 | Düsseldorf. Neuss und Ratingen später. |
| S4 | Ausstattung nur belegt: OSM-Tag oder wörtliches Zitat. Ohne Beleg „keine Angabe“, nie „fehlt“. „Fehlt“ nur bei belegter Abwesenheit. Alter aus der Ausstattung ist „vermutlich“ und zählt nicht als Beleg für die Indexierung. |
| S5 | Keine Fotos mit erkennbaren Kindern. Google-Fotos nur nach Sichtprüfung (`foto_manuell`). Sonst eine Illustration je Typ. Kein Street View. |
| S6 | Notfallnummer als Hinweis: „Bei einem Notruf (112) die Nummer 9601 angeben.“ Kein `tel:`-Link. Fehlt die Nummer, entfällt die Zeile. Die drei Skateranlagen haben laut Stadt keine Nummer; sie sind ohnehin nicht im Hub. |
| S7 | Karte ist die Standardansicht, Liste daneben. Keine Grid-Ansicht. |
| S8 | „In der Nähe“ nur nach Klick, nur im Browser, nichts speichern oder senden. Ohne Standortfreigabe bleibt die Standardsortierung und ein Satz sagt das. Nicht still auf die Stadtmitte springen. |
| S9 | Bis etwa 40 $ für den Erstaufbau, über den vorhandenen Places-Client. Kosten vor dem Google-Lauf nennen. |

---

## 3. Pipeline (`scraper/spielplaetze/`)

Muster wie die Club-Skripte: `--dry-run`, Logs auf Deutsch, Pause vor fremden Websites, robots.txt.

### 3.1 Stadt-Import

1. Nur das WGS84-GeoJSON. Features ohne `objektart` verwerfen. S1 über den Text der Objektart, nicht über eine nackte Zahl.
2. Größe mit Komma-Dezimaltrenner. Koordinate ausschließlich aus `geometry`.
3. Namen als reine, getestete Funktion: `Ksp` → Spielplatz, `Waldksp` → Waldspielplatz, `Wsp` → Wasserspielplatz, Großschreibung, Apostroph in `SPEE'SCHER GRABEN`. Unklare Namen in die Prüf-CSV, nicht raten.
4. Stadtteil per Punkt-in-Polygon gegen „Stadtteilgrenzen Düsseldorf 2025“ (Open Data, dl-de/zero-2.0); Stadtbezirk zur Kontrolle gegen das Feld `stadtbezirk`. Reines Python, Ray-Casting, Multipolygone und Löcher. Keine neue Bibliothek. Grenzlage: der kleinere Treffer, und die Zeile in die Prüf-CSV. Ergebnis auf die Namen in `web/lib/stadtteile.ts` abbilden, Anzeige „Hafen“ bleibt „Medienhafen“. Flingern-Nord und Flingern-Süd nicht zu „Flingern“ zusammenziehen; beide haben eine eigene Seite.
5. Adresse aus `strasse_hausnr`. Für die **78 der 351 Plätze ohne Adresse** die nächste Hausadresse aus der städtischen
   „Adressliste Düsseldorf“ (Open Data, dl-de/zero-2.0, lokal, ≤ 150 m) als „nahe Musterstraße 12“ – kein Nominatim.
   Ohne Treffer bleibt die Adresse leer. „Route planen“ immer aus der Koordinate.
6. Speichern: `typ='spielplatz'`, Slug aus Name und Stadtteil, bei Kollision `slug_mit_suffix`. Identität ist `objektschluessel`. Ein erneuter Import ändert nur Stadtfelder und mischt `extras` (`extras_mergen`), er ersetzt weder Profil noch Foto noch `aktiv`.

### 3.2 OSM

Eine Overpass-Abfrage, Zwischenspeicher `data/spielplaetze/osm.json` (gitignored), Wiederholung mit Pause. Zuordnung bis 60 m oder wenn die Stadt-Koordinate in der OSM-Fläche liegt. Mehrdeutiges in die CSV. Übernehmen: `playground`, `min_age`/`max_age`, `surface`, `wheelchair`, `fee`, `access`, jeweils mit Quelle `osm`. Mapping-Tabelle mit Tests. Plätze nur in OSM nicht anlegen, sondern auflisten (Kandidaten für die Zeit nach 2020 und für Abenteuerspielplätze).

### 3.3 Google

Nur Wasser-, Wald- und große Plätze (ab etwa 1.500 m²), Umkreis 80 m, Typ `playground`. Bewertung nur intern für den Score. Fotos als Kandidaten, Freigabe per SQL und `foto_manuell`, nur ohne erkennbare Kinder.

### 3.4 Profil

Zuerst zehn Plätze, Bericht, dann der Rest der Auswahl (Wasser, Wald, groß, plus die manuelle Abenteuer-Liste). Quellen: duesseldorf.de, Vorlagen der Bezirksvertretung, Pressemitteilungen. Portale nur als Fakt mit Zitat, nichts übernehmen. Je Platz: belegte Ausstattung, Altersgruppe, Extras (Schatten, WC, Zaun, Picknick, rollstuhlgerecht) mit ja/nein/teilweise und Notiz, zwei bis vier eigene Sätze, Highlight, `stand`. Jede Aussage mit wörtlichem Beleg, Prüfung wie bei den Clubs. Eine aus den Stadtfeldern gebaute Schablone („Spielplatz X in Y, Z m²“) ist keine Beschreibung.

### 3.5 Score und Badge

Intern, keine Zahl auf der Seite. Gewichte wie vorgeschlagen (Ausstattung 35, Größe 20, Besonderheit 20, Google 15, Extras 10). Ohne Google bleibt Beliebtheit neutral, der Platz wird nicht abgewertet. „Top-Spielplatz“ nur für Profile mit Belegen, die im obersten Fünftel dieses Scores liegen. Nicht auf dünnen Seiten.

### 3.6 Aktualisierung

Die Stadtdatei ist jährlich und seit 2020 unverändert. Ein monatlicher Job lohnt nicht. Beim nächsten veröffentlichten Stand: Diff, fehlende Objektschlüssel als `stadt_fehlt_seit` markieren, nicht sofort abschalten. OSM-only-Liste ist der Weg für neuere Plätze. Profile neu nur bei Hinweis oder Umbau.

---

## 4. Website

### 4.1 Logik

`web/lib/spielplaetze.ts`: Profil nur aus bekannten Werten. Filter `alter` (eine Altersgruppe), `geraet` (UND, nur „belegt vorhanden“), `extra`, `stadtteil`, `sort`. Plätze mit Altersgruppe „alle“ passen zu jedem Altersfilter (Handoff). Ohne Altersangabe erscheint ein Platz bei „Alle Alter“, nicht bei 0–3, 3–6 oder 6–12. Unbekannt bekommt einen neutralen Pin, nicht die Farbe von „alle“. Chips für Geräte erst, wenn mindestens ein Platz das Gerät belegt hat. Leere Filterlage erklärt, dass die Ausstattung noch nicht überall erfasst ist.

`web/lib/spielplaetze-daten.ts`: `"use cache"`, seitenweise, `aktiv=true`, `typ=spielplatz`, **ohne** die Score-Schwelle von `orteLaden`. Sichtbar ist, was S1 entspricht und nicht auf der Ausschlussliste steht.

Sortierung standardmäßig nach Score, dann Name. „In der Nähe“ ist kein URL-Parameter: die Koordinate bleibt im Browser (Haversine).

### 4.2 Hub

Heller Hero, eine H1 „Spielplätze in Düsseldorf“, Zahl aus den Daten, Einleitung mit zwei bis drei Sätzen und dem Satz, was nicht im Hub ist. Karte und Liste, Pins nach Alter plus neutral, Legende mit Text, nicht nur Farbe. Punkte über `/api/guide-karte?hub=spielplaetze`. Darunter `OrtLinkListe`, damit die Links im ersten HTML stehen. Unten SEO-Text und fünf FAQs. Brotkrumen: Start / Düsseldorf entdecken / Spielplätze.

Filter-URLs: `noindex, follow`, Canonical auf `/guides/spielplaetze`, wie die anderen Hubs.

### 4.3 Detail

Brotkrumen bis zum Namen, Bild oder Typ-Illustration, H1, Stadtteil, Adresse falls vorhanden, Alters-Badge mit dem Zusatz „vermutlich“, wenn abgeleitet. Ausstattung: belegt, keine Angabe, oder belegt fehlend. Extras, Notfallnummer, Größe als „1.200 m² laut Stadt“, Stand, Quellen. Mini-Karte, „Route planen“ als normaler Google-Maps-Link aus der Koordinate.

„Weitere Spielplätze“: die drei nächsten mit Koordinate. Cafés: bis zu zwei aus dem Restaurant-Guide, Typ Café, höchstens 1 km, kanonische URL; der Block entfällt, wenn keiner in der Nähe liegt. Familien-Events: Überschrift „Familien-Events in {Stadtteil}“, nicht „in der Nähe“, weil Events keine Koordinate haben.

JSON-LD `Playground` mit `geo` und `address`. `isAccessibleForFree` nur, wenn OSM nicht `fee=yes` sagt. Kein `aggregateRating`. BreadcrumbList aus derselben Kette wie die sichtbaren Brotkrumen.

### 4.4 Indexierung

- Hub indexierbar.
- Detail indexierbar nur mit eigener Profil-Beschreibung **und** mindestens zwei belegten Ausstattungsmerkmalen. Wasser- und Waldspielplätze zusätzlich nur mit dieser Beschreibung, nicht allein wegen des Typs. Abgeleitetes Alter zählt nicht. Sonst `noindex, follow`, nicht in der Sitemap.
- Stadtteilseiten ab fünf **sichtbaren** Plätzen indexierbar. Hier zählen auch die dünnen mit, weil die Seite die vollständige Liste des Viertels ist. Die verlinkte URL ist die Spielplatz-URL.
- Sitemap: `lastModified` aus `aktualisiert_am`, nicht aus der Uhrzeit des Abrufs.
- Nach dem Livegang einmal IndexNow. `llms.txt`, die Kachel auf `/guides`, der Footer und die FAQ „Welche Guides kommen noch dazu?“ werden mitgezogen.

### 4.5 Foto-Proxy

`/ort-foto/[slug]` muss einen aktiven Spielplatz auch ohne `qualitaets_score` finden. Sonst bleiben freigegebene Fotos unsichtbar.

### 4.6 Barrierefreiheit

Farbpunkte mit Text, Icons mit `title`, Liste als Alternative zur Karte, Touch-Ziele mindestens 44 px, bei 375 px kein horizontales Scrollen. Pin-Kontrast auf der hellen und der dunklen Karte, der gewählte Pin mit einem Ring, der auf der dunklen Karte hell ist. Eigene Outline-SVGs für Schaukel, Rutsche und Sandkasten (2 px Strich, 24er Raster, immer mit Text-Label). Farben des hellen Heros als Tokens mit Dark-Variante.

### 4.7 Tests

Python: Namen, Komma-Größe, Ablehnung von Koordinaten außerhalb des Rechtecks, Objektart-Text, Ray-Casting inklusive Loch, OSM-Mapping, Belegprüfung, Score, „vermutlich“ zählt nicht als Beleg.

Web: Filter (UND, „alle“, unbekannte Altersgruppe), Sichtbarkeit ohne Qualitäts-Score, Indexregel, JSON-LD ohne `aggregateRating`, Pfadentscheidung inklusive der bisher auf `null` festgelegten Tests, fünf FAQs, nur interne Links, keine Score-Zahl, Anrede ihr/euch.

---

## 5. Ablauf

| Schritt | Ergebnis |
|---|---|
| 0 | Entscheidungen aus 0.3 sind getroffen; Illustrationen (Abschnitt 10) vom Auftraggeber anfordern |
| 1 | Import der 351 Plätze, inaktiv, Prüf-CSV für Namen, Grenz-Stadtteile, Bezirks-Abweichungen, doppelte Notfallnummern und Adressen „nahe …“ |
| 2 | OSM-Bericht: wie viele haben Geräte, Liste der OSM-Plätze ohne Stadt-Treffer |
| 3 | Manuelle Abenteuer-Liste, soweit öffentlich belegbar |
| 4 | Google nur für die Auswahl, Kosten vorher, Foto-SQL |
| 5 | Zehn Profile zum Gegenlesen, dann der Rest |
| 6 | Score, Stichprobe, `aktiv=true` für den sauberen Bestand |
| 7 | Website, Cursor-Check |
| 8 | Tests, Build, Browser Desktop und Mobil, hell und dunkel |
| 9 | IndexNow und Sitemap-Kontrolle |

Eine Melde-Funktion für falsche Angaben ist nicht Teil dieser Runde. Bis dahin reicht der bestehende Kontakt.

---

## 6. Kosten

Stadt, OSM, Stadtteilflächen und Adressliste kosten nichts. Erste Runde (≈ 110 Plätze, siehe 0.3): Google-Umkreissuche + Foto-Sichtung grob 3–6 $, Profile (KI + Websuche, 0,05–0,10 $ je Platz) grob 6–11 $. Zusammen deutlich unter S9 (40 $); den genauen Google-Satz des vorhandenen Places-Clients vor dem Lauf nennen.

---

## 7. Risiken, die bleiben

- Die Stadtliste ist von 2020. Neuere Plätze fehlen, bis die OSM-only-Liste oder ein neuer Stadtstand sie nachzieht.
- Fotos mit Kindern bleiben draußen, auch wenn der alte Design-Prompt ein Kinderfoto im Hero vorsieht.
- Ausstattung veraltet. Deshalb Stand der Angaben, und keine Gewähr im Fuß der Detailseite.
- Dünne Detailseiten bleiben noindex. Eine Schablone aus Name und Größe macht sie nicht indexierbar.
- „Fehlt“ nur bei Beleg. Keine öffentliche Score-Zahl.

---

## 8. Abnahme

- Die 351 Plätze aus S1 mit gültiger Koordinate sind importiert; auf der Karte stehen die, die nicht ausgeschlossen wurden. Stadtteil stimmt in der Stichprobe.
- Alle Wasser- und Waldspielplätze haben ein Profil. Mindestens 60 Plätze haben belegte Ausstattung und eine Altersangabe.
- Kein Foto mit erkennbaren Kindern. Jedes Foto mit Urheber.
- Hub, Detail und Stadtteilseiten liefern den Inhalt in der ersten HTML-Antwort. Canonical und noindex wie in 4.4. JSON-LD ohne Google-Bewertung.
- Filter und Karte funktionieren mobil ohne horizontales Scrollen.
- Tests grün. Deploy erst, wenn die Gegenprüfung keine kritischen oder mittleren Befunde mehr hat.

---

## 10. Bild-Prompts (Auftraggeber erzeugt die Bilder)

Gemeinsame Regeln: **keine Personen, keine Kinder, keine Gesichter, keine Logos oder Schriftzüge**, keine erkennbaren
Marken-Spielgeräte. Freundlich und hell, natürliches Licht, leicht warmer Ton passend zu `#FFF6E6`. Fotorealistisch wie
die übrigen Guide-Bilder (`/guides/*.webp`). Ablage als WebP in `web/public/guides/`.

| Datei | Format | Prompt (englisch, für den Bildgenerator) |
|---|---|---|
| `spielplaetze.webp` (Hero, rechts 46 %, läuft nach links aus) | 16:9, mind. 1600 × 900 | *Empty modern public playground in a leafy city park in Düsseldorf on a sunny late-summer morning, wooden climbing tower with a slide, swings and a sandpit with a few colourful buckets, soft golden light through tall plane trees, fresh green lawn, calm and inviting atmosphere, no people, no children, no text, no logos, photorealistic, shallow depth of field, main subject placed on the right third, left side calm and slightly blurred for text overlay* |
| `spielplatz-typ-kinder.webp` (Ersatzbild Kinderspielplatz) | 4:3, mind. 1200 × 900 | *Close-up of an empty colourful city playground: a red slide, a rope climbing net and a sandpit with small toy shovels, sunny afternoon, green bushes in the background, cheerful but natural colours, no people, no children, no text, no logos, photorealistic* |
| `spielplatz-typ-wald.webp` (Ersatzbild Waldspielplatz) | 4:3, mind. 1200 × 900 | *Empty natural forest playground made of raw tree trunks and wooden balancing beams, a log climbing structure and a rope bridge between oak trees, dappled sunlight on the forest floor with leaves, peaceful and adventurous mood, no people, no children, no text, no logos, photorealistic* |
| `spielplatz-typ-wasser.webp` (Ersatzbild Wasserspielplatz) | 4:3, mind. 1200 × 900 | *Empty water playground in a city park on a hot summer day, water pump and small wooden channels with water running into a sandy play area, sparkling water droplets in the sunlight, splash pad stones, green trees around, no people, no children, no text, no logos, photorealistic* |

Prüfung vor dem Einbau: keine Person im Bild (auch nicht im Hintergrund), keine Schrift, Bildausschnitt funktioniert bei
4:3 und als 80 × 80-Thumb.

## 11. Datenschutz-Satz (freigegeben am 12.11.2026)

Einbau in `/datenschutz`, Abschnitt zu Funktionen der Website:

Die Datenschutzerklärung spricht die Leser mit „Sie“ an; der Satz folgt dieser Anrede (die Guides bleiben bei ihr/euch).

> **Standortfunktion im Spielplatz-Guide.** Wenn Sie im Spielplatz-Guide auf „In der Nähe“ tippen, fragt Ihr Browser,
> ob die Website Ihren Standort verwenden darf. Nur wenn Sie zustimmen, berechnet der Browser auf Ihrem Gerät die
> Entfernung zu den Spielplätzen. Ihr Standort wird dabei nicht an uns oder Dritte übertragen und nicht gespeichert.
> Die Freigabe können Sie jederzeit in den Einstellungen Ihres Browsers widerrufen.

