# Plan: Saison-Guide „Weihnachtsmärkte“ (`/guides/weihnachtsmaerkte`)

Stand 17.11.2026 · **vierte Fassung nach Cursor-Prüfung 3 · vom Auftraggeber freigegeben am 17.11.2026** · Produktentscheidungen W1–W7 am 17.11. vom Auftraggeber beantwortet (2.2) ·
noch nichts umgesetzt.

**Ziel:** Wer in Düsseldorf, Neuss oder Ratingen auf einen Weihnachtsmarkt will, findet auf einer Seite alle Märkte der Saison:
wo sie liegen, **ob sie heute (bzw. an einem gewählten Tag) offen haben**, was es dort gibt (Eisbahn, Riesenrad, Kindereisenbahn,
Kinderprogramm …), wie man hinkommt und welche fünf Märkte die Redaktion empfiehlt. Die ersten Märkte öffnen am 19.11.2026 –
deshalb eine **schlanke Stufe 1a**, die vor dem Totensonntag (Ziel Sa 21.11.) live ist, ein Ausbau **1b** bis spätestens Fr 27.11.
(vor dem 1. Advent) und spätere Ausbaustufen.

Gleiche Regeln wie bei den anderen Guides: nur belegte Angaben (Quelle + Stand je Angabe), eine URL pro Ort, Inhalt in der
ersten HTML-Antwort, SEO-Text mit fünf FAQs, **keine öffentliche Score-Zahl**, Deploy nur nach OK, Datenbank-Änderungen per SQL
durch den Auftraggeber, Kosten vor jedem Google-/KI-Lauf nennen, robots.txt respektieren (≥ 2 s Pause), Texte mit ihr/euch.

---

## 0. Zeitplan (Kalender 2026)

| Datum | Ereignis | Folge für den Plan |
|---|---|---|
| Di 17.11. | Plan, Cursor-Prüfung | Freigabe des Plans |
| Mi 18.11. | SQL Schritt 1, Toubiz-Lesen + Recherche (Schritt 2), Auftraggeber liest Neuss/Ratingen | Stammdaten |
| Do 19.11. | Innenstadt-Markt, Bilk, Nordstraße öffnen (1.3); Eröffnung 17:30 Marktplatz | Suchvolumen steigt stark |
| Do 19.–Fr 20.11. | Website Stufe 1a (Kern), Tests, Cursor-Check | Abschnitt 8 |
| bis Fr 27.11. | Stufe 1b (Filter, Pin-Farben, Kurz-Markt-Liste, Event-Links, Google-Lauf, Top 5) | Abschnitt 8 |
| Fr 20.11. | Winter Village, Roncalli-Promenade (laut Toubiz-Terminen, Widerspruch 1.3), Benrath öffnen | – |
| So 22.11. | **Totensonntag** – Innenstadt, Bilk, Benrath, Kö on Ice **geschlossen** (belegt); Riesenrad ungeklärt | Sonderzeiten vor dem Livegang belegt |
| Ziel **Sa 21.11.** | Livegang Stufe 1a | vor dem Totensonntag |
| spätestens **Fr 27.11.** | Livegang Stufe 1b | vor dem 1. Advent (So 29.11., verkaufsoffener Sonntag Innenstadt) |
| Do 24.12. | Heiligabend: Innenstadt 11–15 Uhr, Kö on Ice und Riesenrad zu | FAQ 3, Kontrolle 23.12. |
| Fr 25.12. / Sa 26.12. | Innenstadt 25.12. zu, 26.12. 14–21 Uhr; Bilk an beiden Tagen zu | Sonderzeiten |
| Mi 30.12. | Ende Innenstadt und Bilk; Kö on Ice bis 10.01.2027, Riesenrad bis 03.01.2027 | Zustand „Saison vorbei“ je Eintrag (5.8) |
| Sa 02.01.2027 | Commit: Schalter aus (Menü, Startseite, Kachel-Platz 1) | Seiten bleiben (E10) |

---

## 1. Geprüfte Fakten (Stand 17.11.2026)

### 1.1 Eigene Eventdaten (Supabase, lesend abgefragt am 17.11.)
Abfrage `events` mit Titel-Mustern `weihnachtsmarkt|winterwelt|adventsmarkt|christkind|weihnachtsdorf|wintermarkt|winterzauber|
lichterzauber|eisbahn` (ab 01.11.): **19 Treffer**; Kontrolle mit `weihnacht|advent|winter`: 112 Treffer.

| Befund | Beispiel | Folge |
|---|---|---|
| Der große Markt steht als **ein Event an einem Tag**, ohne `datum_bis` | „Düsseldorfer Weihnachtsmarkt“ (VisitDüsseldorf), `datum` 19.11., `datum_bis` NULL; die eigene Beschreibung sagt „Vom 19. November bis 30. Dezember 2026“ | Ab 20.11. fehlt der Markt in Heute/Morgen/Entdecken. Ursache: `scraper/tier1/visitduesseldorf.py` setzt `datum_bis` immer `None` (Z. 146) |
| Mehrwöchige Märkte aus anderen Quellen ebenfalls eintägig | „Weihnachtszauber auf dem Areal Böhler“ (Rausgegangen), `datum` 24.11., Text „bis zum 20. Dezember“ | wie oben |
| Kategorien uneinheitlich | `food/maerkte` (2), `family/ausfluege`, `sonstiges` (6), `kultur`, `community`, `nightlife`, `musik` | Eine Kategorie-Seite allein findet die Märkte nicht |
| Rauschen | Meetup-Gruppe „GoFreizeitGO“ (Ort = Gruppenname), „Gertrudenhof Hundeweihnachtsmarkt“ (Hürth), „Leipziger Weihnachtsmarkt 2026“ (PRINZ, Leipzig, fälschlich Stadtteil Altstadt), Spieleabend bei Starbucks | Event-Treffer nie ungeprüft übernehmen |
| Echte **Kurz-Märkte** (1–2 Tage) | Bücherweihnachtsmarkt FFT (05.12., Dublette bereits per `event_seo_entscheidungen` weitergeleitet), „1. Alternativer Weihnachtsmarkt“ zakk (06.12.), veganer „Veihnachtsmarkt“ Jugendkirche (28.11.), „BULLE WINTERMARKT“ (04.12.), Handmade-Markt (13.12.) | Liste im Hub (4.5), keine eigenen Seiten (Ausnahme W7) |
| Events haben keine Koordinate und keinen Bezug zu `orte` | – | Zuordnung Event ↔ Markt nur über gepflegte Muster (3.3) |

**Schluss:** Die Eventtabelle kann den Guide nicht tragen (keine Zeiträume, keine Öffnungszeiten, keine Merkmale, Rauschen).
Der Guide bekommt eigene, belegte Stammdaten je Markt; Events bleiben für Einzeltermine.

### 1.2 Code-Stand
- `orte.typ` hat einen CHECK (`database/orte_typ_imbiss_2026-11-05.sql`: restaurant, imbiss, cafe, kneipe, club, spielplatz,
  ausflug, wochenendtipp) – **`weihnachtsmarkt` fehlt → SQL nötig** (Schritt 1).
- `web/lib/pfad-pruefung.ts`: `OrtHub`/`HUBS` (Z. 35–36) kennen den Hub nicht; `ortLaden` liest `freigeschaltet_am` nur aus
  `extras->spielplatz` (Z. 134).
- `web/lib/landing.ts` `GUIDE_HUBS` (Z. 64) steuert automatisch Stadtteil-Guideseiten, deren Sitemap-Einträge (`app/sitemap.ts:160`),
  Links auf `/stadtteil/[slug]` (Z. 71) und den Block „Vorher oder nachher“ auf **jeder Event-Seite**
  (`app/event/[kategorie]/[slug]/page.tsx:104`). Bei rund 15–20 Märkten wären Stadtteilseiten dünn → **nicht in `GUIDE_HUBS`** (E9).
  `GUIDE_NACHBARSTAEDTE = ["Neuss", "Ratingen"]` (Z. 15) gibt es schon (Stadtteilwert für die Nachbarstädte).
- Wiederverwendbar: Spielplatz-Guide (`web/lib/spielplaetze*.ts`, `web/app/guides/spielplaetze/`), Karte
  `web/components/guide-karte.tsx` (`KartenOrt` mit hub-eigenen Feldern; Pins ohne `transform` am Marker), `/api/guide-karte`
  (Zweig je Hub), `/ort-foto/[slug]` (Zweig je Hub, `extras.google_foto`, `extras.bild_fokus`), Schalter `web/lib/schalter.ts`,
  Freischalt-/Abschalt-Logik mit `freigeschaltet_am` und 308 statt 404 (Spielplatz-Plan 5.5), Toubiz-Leser
  `scraper/tier1/visitduesseldorf_fuehrungen.py` (`_event_lesen`, Zwischenspeicher, 2 s Pause).
- `web/lib/symbolbild.ts:63`: Motiv `advent-weihnachtsmarkt` gilt nur **15.11.–23.12.**; die Innenstadt läuft bis 30.12. → Fenster bis
  `12-30` (Test in `symbolbild.test.ts`).
- `web/lib/unterkategorien.json`: `food/maerkte` nennt Weihnachtsmärkte ausdrücklich (Querverweis 5.6).
- Startseite (`web/app/page.tsx`) liest `searchParams` und rendert dynamisch → datumsabhängige Saison-Box möglich. Menü
  (`GUIDE_LINKS` in `components/client.tsx:313`, `rahmen.tsx`) ist statisch → **Schalter statt Datum**.
- Icon-Schrift ist die volle Material Symbols Rounded (lokal): `ice_skating`, `attractions`, `train`, `child_care`, `accessible`,
  `storefront`, `schedule`, `directions_transit` vorhanden. Eigene Icons wie `sp:` über `globals.css` (`.icon[data-icon^="sp:"]`).

### 1.3 Externe Quellen (geprüft am 17.11.2026; Bericht mit allen URLs: Notizordner der Sitzung, `weihnachtsmaerkte-quellen.md`)

**Innenstadt 2026** (visitduesseldorf.de Hub `/erleben/veranstaltungen/weihnachten-in-duesseldorf`, FAQ und Toubiz-Termine; belegt):
Do 19.11.–Mi 30.12.2026, So–Do 11–20 Uhr, Fr/Sa 11–21 Uhr (Händler dürfen bis 22 Uhr verlängern), Heiligabend 11–15 Uhr,
2. Weihnachtstag 14–21 Uhr, **geschlossen Totensonntag 22.11. und 25.12.**, Eintritt frei, Eröffnung 19.11. Marktplatz
(Text 17:15, Termin 17:30). Anfahrt: Haltestelle Heinrich-Heine-Allee; P+R-Kombiticket Flughafen P13 und P7 Arena; Provinzial-Parkhaus
Hohensandweg an den Dezember-Samstagen kostenlos.

| Eintrag | Lage | Zeitraum 2026 | Zeiten | Belegte Besonderheiten | Beleg 2026 |
|---|---|---|---|---|---|
| Altstadt-Markt | Flinger Str./Marktstraße | 19.11.–30.12. | Innenstadt | Hütten im Stil alter Bürgerhäuser | ✔ Toubiz |
| Märchen-Markt | Schadowplatz | 19.11.–30.12. | Innenstadt | rund 15.000 LEDs, Kinderkarussell | ✔ |
| Schadow-Markt | Schadowstraße | 19.11.–30.12. | Innenstadt | – | ✔ |
| The Winter Village | Kö, Corneliusplatz bis Girardetbrücke | **20.11.**–30.12. (Termine) | Innenstadt | kuratiert von der IG Kö, Glascontainer | ✔, Starttag widersprüchlich |
| Weihnachtspromenade (Roncalli) | Rheinufer, Burgplatz bis Alter Hafen | **20.11.**–30.12. (Termine) | Innenstadt | Verkaufswagen, Glaspavillons | ✔, Starttag widersprüchlich |
| Kö on Ice (DEG Winterwelt), **Eisbahn** | Corneliusplatz | 06.11.2026–10.01.2027 | bis 31.12. So–Do 11–21, Fr/Sa 11–22; 22.11. und 24.12. zu; 25./26.12. 13–18; 31.12. 11–18 | Eintritt 9 €/Kinder 6 €, Eisstock | ✔ deg-winterwelt.de |
| Riesenrad „Wheel of Vision“ | Burgplatz | 23.10.2026–03.01.2027 | So–Do 11–21, Fr/Sa 11–22; 24.12. zu; 25./26.12. 13–19 | 55 m, 42 Gondeln; **Totensonntag ungeklärt** | ✔ Toubiz-POI |
| Handwerker-Markt (Rathaus), Kö-Bogen-Markt | Marktplatz / Kö-Bogen | – | – | 2026 kein eigenes Event | nur 2025 |
| „Engelchenmarkt“, „Sternchenmarkt“ | – | – | – | alte Namen, 2025/2026 nicht geführt | ✘ |

**Stadtteile, Neuss, Ratingen:**

| Eintrag | Lage | Zeitraum 2026 | Zeiten | Besonderheiten | Beleg 2026 |
|---|---|---|---|---|---|
| Weihnachtsmarkt Schloss Benrath | Benrather Schloßallee 102 | 20.11.–20.12., **nur Fr–So** | Fr 14–21, Sa 11–21, So 11–20; Totensonntag zu | Kunsthandwerk, **Kindereisenbahn**, Eintritt frei; U72 „Schloss Benrath“, S „Benrath“ | ✔ schloss-benrath.de + Toubiz |
| Weihnachtszauber Areal Böhler | Hansaallee 321 (Heerdt) | 24.11.–20.12. | Di–Fr 16–22, Sa 13–22, So 13–20, Mo zu | Live-Musik, Puppenbühne, Kinderschminken | ✔ areal-boehler.de |
| Weihnachtsmarkt Bilk | Düsseldorf Arcaden, Friedrichstr. 133 | 19.11.–30.12. | Mo–Sa 11–21, So 12–20; 24.12. 11–15; zu 22.11., 25.12., **26.12.** | – | ✔ Toubiz |
| Weihnachtszeit Nordstraße | Nordstraße (Pempelfort) | 19.11.–23.12. | täglich 11:30–20:30 (22.11. fehlt in der Terminliste) | Kinder-Sonntag, montags Kasperle | ✔ Toubiz |
| Kaiserswerther Nikolausmarkt | Kaiserswerther Markt | 2026 **nicht veröffentlicht** (2025: 6./7.12.) | – | – | nur 2025 |
| Angermunder Nikolausmarkt / Oberbilker Lichterzauber / Wohltätiger Weihnachtsmarkt | – | 28.11. / 21.11. / 06.12. | 12–20 / 14–18 / 12–16 | Eintagesmärkte | ✔ Toubiz |
| Gerresheim, Schloss Eller, Kalkum, Lorettostraße, Medienhafen | – | – | – | nichts gefunden | ✘ |
| Neusser Weihnachtsmarkt | Münsterplatz/Freithof | widersprüchlich (18.11. oder 25.11. bis 23.12.) | Snippet: Mo–Do 11–20, Fr/Sa 11–21, So 12–20:30 | 15-m-Pyramide | nur Snippet (robots, s. u.) |
| Quirinus-Adventsmarkt Neuss | – | 29.11. (Snippet) | – | – | nur Snippet |
| Ratinger Weihnachtsmarkt | Marktplatz | Aggregator: 21.11.–22.12. (nachweislich fehlerhaft) | – | – | ✘ |

Nirgends belegt: Stände-Anzahl, Glühweintasse/Pfand, Glühweinpreis, Barrierefreiheit je Markt (Toubiz hat nur leere Vorlagen).
→ Diese Merkmale nur über Sichtung des Auftraggebers (`merkmale.csv`) oder später belegte Zitate.

**Quellen-Status:**

| Quelle | robots.txt | Bedingungen | Strukturiert | Nutzung im Guide |
|---|---|---|---|---|
| visitduesseldorf.de | `*` gesperrt nur `/neos/`, Warenkorb, `/duesseldorf/offer`; `/event/`, `/erleben/`, `/attraktionen/` erlaubt | Impressum: alle Rechte vorbehalten; Toubiz-Datensätze meist `cc-by-sa`, Fotos teils `none` mit Fremd-Copyright | Toubiz-JSON in `data-tb-detail-event` (`dates[]` mit startAt/endAt/closed, `dateIntervals`, Geo, Adresse, `price.freeEntry`, `updatedAt`); Sitemap (~800 `/event/`) | **Primärquelle für Fakten** (Skript 4.1); Texte selbst schreiben; **keine Fotos** übernehmen; Toubiz-Widget-API mit öffentlichem Token **nicht** nutzen |
| Veranstalter: schloss-benrath.de, areal-boehler.de, deg-winterwelt.de, d-live.de, kaiserswerth.de | offen (nur Admin-Pfade gesperrt; areal-boehler ohne robots.txt) | nicht geprüft | nein | Gegenprüfen von Hand, Zitat als Beleg |
| duesseldorf.de | `*`: `Disallow: /`; freigegeben nur benannte Bots (u. a. Googlebot, ClaudeBot, Claude-User) | – | – | **kein Skript**; Einzelabruf zum Gegenlesen nur als „Claude-User“ bzw. durch den Auftraggeber |
| neuss-marketing.de | `*`: `Disallow: /` | – | – | **nicht abrufen**; Auftraggeber liest selbst (W2) |
| ratingen-marketing.de / neuss.de | erlaubt | nicht geprüft | nein | bisher keine 2026-Seite |
| weihnachten-in-duesseldorf.de (u. a. `lage-der-weihnachtsmaerkte-in-duesseldorf.php`, 14 Standorte mit Unterseiten) | erlaubt | privates Projekt (rimVERLAG), alle Rechte vorbehalten, Fotos teils KI, Zeiten nur pauschal und für Roncalli/Winter Village abweichend von Toubiz | – | **nur Hinweisgeber für Kandidaten** (z. B. Rathaus, Kö-Bogen I/II, Burgplatz), **nie Beleg**: jeder Kandidat wird bei Visit Düsseldorf/D.LIVE/Veranstalter belegt oder bleibt draußen; keine Texte/Fotos übernehmen |
| OpenStreetMap (Overpass, taginfo) | `/api/` für `*` gesperrt | ODbL | Schema `xmas:feature=market` (de facto) | **nicht nötig**: Koordinaten aus Toubiz-Geo bzw. Google-place_id; keine Overpass-Abfrage für diesen Guide |
| Google Places API (New) | API | **nur `place_id` dauerhaft speicherbar; Koordinaten max. 30 Tage; Bewertungen, Öffnungszeiten, Namen usw. nicht speichern**; Autor-Attribution bei Fotos; **EEA-Bedingungen für deutsche Rechnungsadresse noch nicht gelesen** | – | Score-Eingang zur Laufzeit (4.6), Fotos nach Sichtung (4.4) |
| rausgegangen.de, wz.de, rp-online.de | nicht abgerufen bzw. KI-Bots gesperrt, RP mit TDM-Vorbehalt § 44b UrhG | – | – | nicht nutzen |

**Widersprüche, vor dem Livegang zu klären:** (1) Starttag Winter Village/Roncalli 19. oder 20.11. – Termindaten gelten (20.11.),
Hinweis in `pruefung.csv`, Gegenlesen bei D.LIVE; (2) eigene Zeiten Kö on Ice, Riesenrad, Benrath, Böhler, Bilk – nie die
Innenstadt-Zeiten pauschal übernehmen; (3) Riesenrad am Totensonntag ungeklärt → „nicht veröffentlicht“; (4) Nordstraße 22.11. nur
als Lücke in der Terminliste → nur nach Beleg „zu“.

### 1.4 Rechtliches zu Öffnungszeiten
Totensonntag ist in NRW ein stiller Feiertag. Der Guide zeigt **nur belegte Sonderzeiten**; fehlt der Beleg, steht dort
„Ob der Markt am Totensonntag öffnet, hat der Veranstalter nicht veröffentlicht“ (Regel 4.3).

---

## 2. Entscheidungen

### 2.1 Technisch (von Claude, Cursor prüft)
| Nr. | Entscheidung |
|---|---|
| E1 | **Ein Eintrag = eine Zeile in `orte`** mit neuem Typ `weihnachtsmarkt` (CHECK erweitern). Karte, Foto-Proxy, Pfadprüfung, Sitemap und Freischaltung funktionieren wie bei den Spielplätzen. Kein Jahr in der URL. |
| E2 | **Saisondaten je Jahr** unter `extras.weihnachtsmarkt.saisons["2026"]`. 2027 kommt als neuer Schlüssel dazu; Zeile, Slug und URL bleiben. |
| E3 | **Pflege über eingecheckte CSV-Dateien** (3.2) und zwei kleine Skripte (Python, `--dry-run`, keine neue Bibliothek): `toubiz_lesen.py` erzeugt aus den Visit-Düsseldorf-Eventseiten einen **Entwurf** der Saisondaten, `import_maerkte.py` schreibt die geprüften CSV-Zeilen nach `orte`. Merkmale und Beschreibungen recherchiert Claude von Hand mit Beleg-URL und Zitat (für rund 15–20 Einträge schneller als ein KI-Profil-Skript); das automatische Profil folgt 2027 (Schritt 11). |
| E4 | **Öffnungszeiten nur belegt.** Ohne belegte Wochenzeit: „Öffnungszeiten noch nicht veröffentlicht“, kein „heute geöffnet“. Sonderzeit schlägt Wochenzeit. Vor dem `von` ist der Zustand `vor_saison`, nach dem `bis` `nach_saison`; `zu` gibt es nur innerhalb des Zeitraums. Eine Lücke in einer Terminliste ist weder Beleg für „zu“ noch für „offen“; an Feiertagen ohne Sonderzeile gilt „nicht veröffentlicht“ (4.3 Schritt 4). |
| E5 | **„Heute geöffnet“ rechnet nur der Browser** (Europe/Berlin) aus den Zeiten im ersten HTML. Server und Cache enthalten **nie** einen fertig gerechneten Zustand: Zustandszeile und Pin-Farbe rendern auf dem Server einen neutralen Platzhalter (gleich beim Hydrieren, kein Mismatch), danach rechnet eine Client-Insel. Die Karten-API (`public`, bis zu 1 h alt) liefert nur Zeiten, keinen Zustand. Der Server liefert die vollständige Zeitentabelle (crawlbar). Der Datumsfilter `?tag=YYYY-MM-DD` rechnet der Server **nur innerhalb der Suspense-Grenze** wie beim Spielplatz-Hub (`app/guides/spielplaetze/page.tsx:253`: ungefilterte Ansicht als Fallback außerhalb, nur die gefilterte Ansicht wartet auf `searchParams`); Datums-URLs `noindex, follow`, Canonical auf den Hub. Die Startseiten-Box liest `heuteBerlin()` im dynamischen Teil der Seite, **nicht** `pool.heute` (Cache bis 1 h, `web/lib/daten.ts:217`). |
| E6 | **Innenstadt als Gruppe:** eine Gruppenzeile „Düsseldorfer Weihnachtsmarkt in der Innenstadt“ (eigene Detailseite, kein eigener Pin) plus je eine Zeile für die fünf 2026 belegten Teilmärkte (Altstadt-Markt, Märchen-Markt, Schadow-Markt, The Winter Village, Weihnachtspromenade) und die zwei **Attraktionen** Kö on Ice (Eisbahn) und Riesenrad. Teilmärkte erben Zeitraum und Zeiten der Gruppe, solange sie keine eigenen haben; Attraktionen haben immer eigene. Handwerker-Markt und Kö-Bogen-Markt nur, wenn 2026 belegt. |
| E7 | **Attraktionen** (`attraktion: true`) zählen nicht als „Markt“ (Hero-Zahl „{n} Märkte, dazu Eisbahn und Riesenrad“), bekommen keinen Score und keinen Top-5-Platz; ihre Merkmale (Eisbahn, Riesenrad) gelten als Badge der Gruppe. |
| E8 | **Keine öffentliche Zahl, keine Google-Sterne** (W3a). Score nur intern für die Sortierung „Empfohlen“ und als Vorschlag für die Top 5 (4.6). |
| E9 | **Nicht in `GUIDE_HUBS`**: keine Stadtteil-Guideseiten, kein automatischer Link auf jeder Event-Seite. Eigene Konstante `SAISON_GUIDES` in `web/lib/landing.ts`; `/guides/weihnachtsmaerkte/stadtteil/*` → 404 (Proxy). |
| E10 | **Saisonende ohne 410/noindex:** Hub und Detailseiten bleiben das ganze Jahr erreichbar und indexierbar (5.8). Ein Eintrag, der nicht wiederkommt, wird abgeschaltet → 308 auf den Hub. Nie 404/410 für eine einmal freigeschaltete URL. |
| E11 | Fotos: Google Places nach Sichtung durch den Auftraggeber; **Menschen nur klein, fern oder unscharf, keine erkennbaren Gesichter** (W4); sonst Illustration. Struktur wie Spielplatz (`google_foto`, `foto_manuell`, `foto_version`, `bild_fokus`). Keine Fotos von Visit Düsseldorf/Veranstaltern ohne schriftliche Erlaubnis. |
| E12 | **Google-Bedingungen:** in `orte` nur `google_place_id`; **keine** Bewertung, Anzahl, Öffnungszeiten oder Google-Koordinate speichern (Koordinate kommt aus Toubiz/Veranstalter). Rohwerte nur im lokalen, nicht eingecheckten Prüfbericht, der nach der Score-Freigabe gelöscht wird. Vor dem ersten Google-Lauf liest Claude die EEA-Bedingungen (Schritt 7a). **Ergänzend:** (a) `score.teile.beliebtheit` ist ein aus Google-Bewertungen abgeleiteter Wert und fällt unter Schritt 7a – bis dahin kein Google-Lauf; 7a entscheidet, ob `score` mit `teile.beliebtheit` gespeichert werden darf oder nur `score_manuell` und `top5_rang` (der Auftraggeber setzt dann den Score von Hand anhand des Berichts). (b) Der Foto-Ressourcenname mit Autor bleibt wie bei den Spielplätzen in `extras.google_foto`; Bildbytes werden nie gespeichert. (c) Im Weihnachtsmarkt-Zweig von `/ort-foto` verfällt die gemerkte Bildadresse nach **höchstens 30 Tagen** (`expire` ≤ 30 Tage statt 45 wie heute, `app/ort-foto/[slug]/route.ts:104`); die übrigen Hubs sind ein Folgepunkt (13). |
| E13 | Budget Google + KI für Stufe 1 und 2: **15 $** (Schätzung Abschnitt 9: unter 5 $). Konkrete Kosten vor jedem Lauf nennen. |

### 2.2 Vom Auftraggeber entschieden (17.11.2026)
| Nr. | Frage | Antwort |
|---|---|---|
| W1 | Umfang Stufe 1 | **Düsseldorf + Neuss + Ratingen.** Ausflugsziele (Köln, Aachen …) nicht in diesem Guide |
| W2 | Neuss/Ratingen, wenn die Quelle Bots sperrt | **Auftraggeber liest selbst** (neuss-marketing.de u. a.) und gibt Claude die Angaben; Beleg = URL + Lesedatum + `quelle: auftraggeber`. Ohne Angaben bleiben die Einträge inaktiv und kommen per Freischalt-SQL nach (kein Deploy) |
| W3 | Bewertung/Ranking | **Score aus zugänglichen Daten, v. a. Google-Bewertungen** (4.6), vom Auftraggeber **vor der Freigabe von Hand geprüft**; **nicht öffentlich**, nur Sortierung. Dazu **redaktionelle Top 5** und **Badges** („Für Familien“, „Mit Eisbahn“ usw., 4.7) |
| W4 | Fotos mit Menschenmengen | **erlaubt, wenn fern/unscharf**, keine erkennbaren Gesichter |
| W5 | Einbau während der Saison | **alle vier:** Menü + Footer, Startseiten-Box, `/guides`-Kachel an erster Stelle, Event- und Kategorie-Seiten |
| W6 | Score sichtbar? | **Nein, nur Sortierung** |
| W7 | Kurz-Märkte (1–3 Tage) | **Ab 4 Öffnungstagen eigene Seite; kürzere nur in der Liste „Kleine Weihnachtsmärkte“ – Ausnahme: jährlich wiederkehrende Märkte mit eigener Suchnachfrage** (Kaiserswerther Nikolausmarkt, Quirinus-Adventsmarkt Neuss) bekommen eine Seite (`immer_im_guide`) |

**Auslegung (bitte bestätigen oder korrigieren):** Die Antwort zu W3 nennt „mit eisenbahn“. Gelesen als **zwei** Badges:
„Mit Eisbahn“ (Kö on Ice) **und** „Mit Kindereisenbahn“ (Schloss Benrath, belegt). Beide stehen in 4.7.

---

## 3. Datenmodell

### 3.1 Tabelle `orte`
- Spalten: `typ='weihnachtsmarkt'`, `name` (ohne Jahr, z. B. „The Winter Village“), `slug` (Name + Stadtteil, bestehende
  Slug-Funktion, **fest ab der ersten Freischaltung**), `stadtteil` (Katalogwert bzw. „Neuss“/„Ratingen“), `adresse`,
  `latitude`/`longitude` (aus Toubiz-Geo, Veranstalter oder Sichtung – **nie** aus Google), `webseite`, `google_place_id`
  (einzige Google-Angabe, E12), `aktiv`, `qualitaets_score = NULL`, `bild_url = NULL`, `bild_attribution` (nur bei Foto),
  `beschreibung` (2–4 eigene Sätze aus Belegen).
- `extras.weihnachtsmarkt`:
  ```
  { schluessel: "<kurz>",                 // stabile Identität aus maerkte.csv, z. B. "winter-village"
    gruppe: "innenstadt" | null,          // Teilmarkt bzw. Attraktion einer Gruppe (E6)
    ist_gruppe: bool,                     // Gruppenzeile: Detailseite, kein Pin, Liste zeigt die Teile
    attraktion: bool,                     // Kö on Ice, Riesenrad (E7)
    immer_im_guide: bool,                 // W7-Ausnahme für kurze, traditionelle Märkte
    art: ["klassisch" | "mittelalter" | "kunsthandwerk" | "alternativ" | "schloss" | "eisbahn" | "riesenrad"],
    veranstalter?, quelle_url, toubiz_url?,
    lage: "draussen" | "drinnen" | "beides" | null,
    eintritt: { wert: "frei" | "kostenpflichtig", notiz?, beleg, url, stand } | null,
    anfahrt: { haltestellen: [{ name, linien? }], parken?, beleg, url, stand } | null,
    merkmale: { <merkmal>: { wert: "ja" | "nein" | "teilweise", notiz?, quelle: "zitat" | "sichtung" | "auftraggeber", beleg, url?, stand } },
        // <merkmal>: eisbahn, riesenrad, karussell, kindereisenbahn, kinderprogramm, puppenbuehne, buehnenprogramm,
        //            kunsthandwerk, krippe, tassenpfand (notiz = Betrag), barrierefrei (auch "teilweise"), wc, ueberdacht
        // „nein“ nur mit Beleg der Abwesenheit; ohne Beleg → keine Angabe, keine Kachel
    staende: { anzahl, beleg, url, stand } | null,
    saisons: { "2026": {
        von, bis,                                        // YYYY-MM-DD
        zeiten: [{ tage: ["mo",…], von: "HH:MM", bis: "HH:MM" }],   // leer = nicht belegt
        sonder: [{ datum, geschlossen: true } | { datum, von, bis }],
        nur_tage?: [YYYY-MM-DD],                         // z. B. Benrath nur Fr–So: als Wochenzeiten, nicht hier
        geerbt_von?: "innenstadt", geerbt: ["von" | "bis" | "zeiten" | "sonder"],   // feldweise Erbung (3.2)
        quelle: "toubiz" | "veranstalter" | "auftraggeber", beleg, url, stand } },
    event_muster?: [{ titel: "<regex>", ort?: "<regex>" }],   // 3.3
    score?: { wert: 0–10, teile: { beliebtheit, angebot, nutzwert, erreichbarkeit }, google_bezug: "markt" | "ort" | "kein",
              stand, manuell?: 0–10 },                // KEINE Google-Rohwerte (E12)
    top5_rang?: 1–5,                                   // redaktionell (4.6)
    highlight?, profil_stand?,
    freigeschaltet_am: YYYY-MM-DD | null, ausgeschlossen: "<grund>" | null }
  ```
- Foto: `extras.google_foto = { name, breite, hoehe, autor, autor_url }`, `extras.foto_manuell`, `extras.foto_version`,
  optional `extras.bild_fokus`; `bild_attribution = autor`.
- Begriffe wie Spielplatz-Plan 3.1: *nie freigeschaltet*, *freigeschaltet*, *abgeschaltet*.

### 3.2 Eingecheckte Pflegedateien `data/weihnachtsmaerkte/`
| Datei | Spalten | Pflege |
|---|---|---|
| `maerkte.csv` | `schluessel`, `name`, `gruppe`, `ist_gruppe`, `attraktion`, `immer_im_guide`, `art`, `stadtteil`, `adresse`, `lat`, `lng`, `koord_quelle` (`toubiz` \| `veranstalter` \| `sichtung`), `webseite`, `toubiz_url`, `veranstalter`, `lage`, `eintritt`, `eintritt_beleg`, `anfahrt_haltestellen`, `anfahrt_beleg`, `staende`, `staende_beleg`, `beschreibung`, `event_muster`, `top5_rang`, `score_manuell`, `quelle_url`, `ausschliessen`, `grund` | Claude recherchiert, Auftraggeber prüft; `top5_rang` und `score_manuell` nur Auftraggeber |
| `saison-2026.csv` | `schluessel`, `von`, `bis`, `zeiten` (Kurzschrift `Mo-Do 11:00-20:00; Fr-Sa 11:00-21:00; So 11:00-20:00`), `sonder` (`2026-11-22 zu; 2026-12-24 11:00-15:00`), `quelle`, `beleg`, `url`, `stand` | aus dem Toubiz-Entwurf, von Claude geprüft; Neuss/Ratingen vom Auftraggeber |
| `merkmale.csv` | `schluessel`, `merkmal`, `wert`, `notiz`, `quelle`, `beleg`, `url`, `stand` | Claude (Zitat), Auftraggeber (Sichtung) |
| `event_ausschluss.csv` | `quelle_url`, `grund` | Rauschen aus der Kurz-Markt-Liste nehmen (4.5) |
| `saison-2026-entwurf.csv`, `toubiz.json`, `score_bericht.md` | Ausgaben | **gitignored**; `score_bericht.md` nach der Score-Freigabe löschen (E12) |

**`toubiz_lesen.py`** (nur Lesen, nichts in die DB): für jede `toubiz_url` aus `maerkte.csv` die Eventseite laden (≥ 2 s Pause,
generischer User-Agent wie `STANDARD_HEADERS`, Zwischenspeicher `toubiz.json` mit `updatedAt` – unveränderte Seiten nicht neu laden),
`data-tb-detail-event` (bei POIs `data-tb-detail-article`) parsen, aus `dates[]` Zeitraum, Wochenzeiten (je Wochentag die häufigste
Zeit) und Abweichungen (andere Zeit oder `closed`) ableiten. **Fehlende Tage innerhalb des Zeitraums** schreibt das Skript nicht als
„zu“, sondern als Hinweis „Lücke im Terminplan“. Dazu Geo, Adresse, `price.freeEntry`. Ausgabe `saison-2026-entwurf.csv` +
Abweichungsliste gegen `saison-2026.csv` (für spätere Läufe: geänderte Zeiten der Veranstalter erkennen). Der Code lehnt sich an
`visitduesseldorf_fuehrungen.py` an (gemeinsame Hilfsfunktion statt Kopie, wenn ohne Umbau des alten Scrapers möglich).

**`import_maerkte.py`** (schreibt `orte`):
- Pflichtfelder `schluessel`, `name`, `stadtteil` (Katalogwert oder Neuss/Ratingen), Koordinate im Rechteck 6,55–7,00 °O /
  51,08–51,40 °N (Kartenausschnitt). Fehler → Log-Fehler, Zeile nicht angelegt bzw. unverändert.
- `zeiten`/`sonder` über eine **reine, getestete Parser-Funktion**; nicht lesbar, `von > bis`, Sonderdatum außerhalb des Zeitraums
  oder Zeit über Mitternacht → Log-Fehler, Saison für diese Zeile **nicht** geschrieben (lieber keine Zeit als eine falsche).
- **Gruppen-Erbung feldweise:** Ein Teilmarkt übernimmt `von`, `bis`, `zeiten` und `sonder` **einzeln** von der Gruppe, wenn die
  jeweilige Zelle in seiner Zeile von `saison-2026.csv` leer ist (fehlt die Zeile ganz, sind alle vier leer). Beispiel Winter Village:
  eigenes `von` 20.11., Zeiten und Sonderzeiten geerbt. Gespeichert werden die aufgelösten Werte plus `geerbt_von` und `geerbt`
  (Liste der übernommenen Felder). Attraktionen erben nie. Eine Lücke in der Toubiz-Terminliste wird **keine** fehlende
  Wochentagszeile, sondern ein Hinweis in `pruefung.csv`.
- Neue Zeilen `aktiv=false`; der Import ändert `aktiv` und `freigeschaltet_am` nie; `ausgeschlossen` wie Spielplatz 3.1; Wiederholung
  über `schluessel`; Slug nur bei nie freigeschalteten Zeilen neu, Kollisionen gegen die ganze Tabelle `orte`.
- Schreibweg direkt per Skript (Service-Key) wie beim Spielplatz-Import – **Freigabe des Schreibwegs vor dem ersten Lauf**.
- Ausgabe `pruefung.csv`: je Eintrag Zeitraum, Zeiten, Sonderzeiten, Quelle, fehlende Belege, Zustand an vier Stichtagen
  (22.11., 24.12., 26.12., 31.12., 01.01.) zum Gegenlesen.

### 3.3 Zuordnung Event ↔ Eintrag
`event_muster` je Eintrag (Titel-/Ort-Regex, Spalte in `maerkte.csv`, getestet). In **Stufe 1b** nur für zwei Zwecke: (a) Events, die
einen Guide-Eintrag meinen, fallen aus der Kurz-Markt-Liste (z. B. Kaiserswerther Nikolausmarkt); (b) ihre Event-Seite zeigt den
Kasten „Alle Infos zum Markt: Öffnungszeiten, Anfahrt, Besonderheiten → {Name}“. In **Stufe 2**: Abschnitt „Termine auf dem Markt“
auf der Detailseite (Events, die nicht den ganzen Markt meinen: Konzert, Nikolaus, Eröffnung). Event-Seiten der großen Märkte
bleiben bestehen (Kalender „heute“), **keine Weiterleitung** auf den Guide (Vorschlag, Einspruch möglich – Abschnitt 13).

---

## 4. Daten beschaffen

### 4.1 Einträge Stufe 1 (Kandidaten; freigeschaltet wird nur, was belegt ist)
Rolle nur über `ist_gruppe`, `gruppe`, `attraktion`, `immer_im_guide`; `art` bleibt die Aufzählung aus 3.1 (oder leer, solange nicht belegt).

| # | Schlüssel | Name | Stadtteil | Rolle | `art` (nur belegt) | Quelle Zeiten |
|---|---|---|---|---|---|---|
| 1 | `innenstadt` | Düsseldorfer Weihnachtsmarkt in der Innenstadt | Altstadt | `ist_gruppe` | klassisch | Toubiz Sammel-Event + Hub-FAQ |
| 2 | `altstadt-markt` | Altstadt-Markt | Altstadt | `gruppe=innenstadt` | klassisch | erbt alles |
| 3 | `maerchen-markt` | Märchen-Markt | Stadtmitte | `gruppe=innenstadt` | klassisch | erbt alles |
| 4 | `schadow-markt` | Schadow-Markt | Stadtmitte | `gruppe=innenstadt` | – | erbt alles |
| 5 | `winter-village` | The Winter Village | Stadtmitte | `gruppe=innenstadt` | – | eigenes `von` 20.11., Rest erbt |
| 6 | `weihnachtspromenade` | Weihnachtspromenade am Rhein | Altstadt | `gruppe=innenstadt` | – | eigenes `von` 20.11., Rest erbt |
| 7 | `koe-on-ice` | Kö on Ice (DEG Winterwelt) | Stadtmitte | `gruppe=innenstadt`, `attraktion` | eisbahn | deg-winterwelt.de (eigene) |
| 8 | `riesenrad` | Riesenrad „Wheel of Vision“ | Altstadt | `gruppe=innenstadt`, `attraktion` | riesenrad | Toubiz-POI (eigene) |
| 9 | `schloss-benrath` | Weihnachtsmarkt Schloss Benrath | Benrath | – | schloss, kunsthandwerk | schloss-benrath.de |
| 10 | `areal-boehler` | Weihnachtszauber Areal Böhler | Heerdt | – | klassisch | areal-boehler.de |
| 11 | `bilk-arcaden` | Weihnachtsmarkt Bilk (Düsseldorf Arcaden) | Bilk | – | klassisch | Toubiz |
| 12 | `nordstrasse` | Weihnachtszeit Nordstraße | Pempelfort | – | klassisch | Toubiz |
| 13 | `kaiserswerth` | Kaiserswerther Nikolausmarkt | Kaiserswerth | `immer_im_guide` | – | 2026 offen → aktiv erst mit Beleg |
| 14 | `neuss` | Neusser Weihnachtsmarkt | Neuss | – | klassisch | Auftraggeber (W2) |
| 15 | `quirinus-neuss` | Quirinus-Adventsmarkt | Neuss | `immer_im_guide` | – | Auftraggeber (W2) |
| 16 | `ratingen` | Ratinger Weihnachtsmarkt | Ratingen | – | klassisch | Auftraggeber (W2) |
(`klassisch` nur, wenn die Quelle den Markt so beschreibt; sonst leer.)
Weitere Kandidaten nur mit Beleg (Schritt 2 sucht noch einmal): Handwerker-Markt am Rathaus (Marktplatz), Kö-Bogen-Markt I,
Kö-Bogen II (Gustaf-Gründgens-Platz), Markt am Burgplatz (neben dem Riesenrad), Gerresheim, weitere Neuss/Ratingen. Die ersten vier
führt die Privatseite weihnachten-in-duesseldorf.de als eigene Standorte 2026; Visit Düsseldorf hat 2026 dafür kein eigenes Event
(Stand 17.11.). Werden sie bei D.LIVE oder Visit Düsseldorf belegt, kommen sie als Teilmärkte der Gruppe Innenstadt dazu (erben die
Zeiten); sonst nennt die Gruppenseite nur die belegten Teile.
Die Stadtteile 10–12 prüft Claude per Polygon wie beim Spielplatz-Import (Hansaallee 321 → Heerdt, Friedrichstr. 133 → Bilk).
Eintagesmärkte (Angermund, Oberbilk, Wohltätiger Markt) bleiben in der Kurz-Markt-Liste (W7).

### 4.2 Reihenfolge der Quellen je Angabe
| Angabe | 1. Wahl | 2. Wahl | nie |
|---|---|---|---|
| Zeitraum, Wochen-, Sonderzeiten | Veranstalterseite bzw. Toubiz-Termine (`toubiz_lesen.py`) | Auftraggeber liest gesperrte Seiten (W2) | Google-Öffnungszeiten, Privatseiten, Aggregatoren, Presse ohne Jahr |
| Lage/Koordinate | Toubiz-Geo | Veranstalter-Adresse + Kontrolle auf der Karte | Google-Koordinate (E12) |
| Merkmale | Veranstalter-Zitat 2026 | Toubiz-Text 2026 | Bewertungstexte, Annahmen |
| Tassenpfand, WC, Barrierefreiheit, Stände | Veranstalter-Zitat | Sichtung des Auftraggebers | Schätzung |
| Anfahrt | Veranstalter/Visit Düsseldorf | Haltestelle und Linien aus dem Rheinbahn-/VRR-Netzplan (Name + Linien, ohne Fußweg-Minuten, wenn nicht belegt) | – |
| Foto | Google Places nach Sichtung (W4) | Foto des Auftraggebers | Fotos von Visit Düsseldorf/Veranstaltern |

Jede Angabe trägt `beleg` (wörtliches Zitat, Prüfung wie Club-Profil: Wortstamm/Zahl im Zitat), `url` und `stand`. Nur für 2025
belegte Angaben kommen nicht in `saison-2026`, sondern als Hinweis in `pruefung.csv`.

### 4.3 Öffnungs-Logik (reine Funktion, Python und TypeScript mit gemeinsamer Fixture)
`oeffnungAm(eintrag, datum, uhrzeit?) → { zustand: "vor_saison" | "nach_saison" | "zu" | "offen" | "unbekannt", von?, bis?, grund? }`
1. **Saison wählen:** die Saison, deren `von`–`bis` das Datum enthält – **nicht** der Schlüssel des Kalenderjahrs (Kö on Ice liegt unter
   `saisons["2026"]` und läuft bis 10.01.2027). Enthält keine Saison das Datum: liegt es vor dem frühesten `von` aller Saisons mit Daten
   → `vor_saison` (gegen diese Saison), sonst → `nach_saison` (gegen die Saison mit dem spätesten `bis` davor).
2. Gewählte Saison ohne belegte `zeiten` → `unbekannt` („Öffnungszeiten noch nicht veröffentlicht“).
3. Sonderzeile für das Datum → `zu` mit Grund bzw. deren Zeiten. Sie schlägt alles Folgende.
4. **Feiertag ohne Sonderzeile → `unbekannt`** („nicht veröffentlicht“), auch wenn die Wochenzeit den Wochentag enthält. Feiertage:
   **Totensonntag (Sonntag vor dem 1. Advent, berechnet – 2026 der 22.11., 2027 der 21.11.)**, 24.12., 25.12., 26.12., 31.12., 01.01.
   (Grund: eine Lücke in der Terminliste ist weder Beleg für „zu“ noch für „offen“; die Nordstraße und das Riesenrad zeigen am 22.11.
   deshalb „nicht veröffentlicht“.)
5. Sonst Wochenzeit des Wochentags; der Wochentag hat keine Zeile → `zu` (z. B. Benrath Mo–Do – belegt durch die Wochenzeiten selbst).
6. Mit Uhrzeit: „jetzt offen bis …“ / „öffnet um …“ / „heute schon geschlossen“.
Datum und Uhrzeit immer in Europe/Berlin über die vorhandenen Helfer `heuteBerlin()`/`minutenBerlin()` (`web/lib/datum.ts:10/15`),
auch wenn der Server in UTC läuft. Anzeige: „Heute 11–21 Uhr“, „Heute geschlossen (Totensonntag)“, „Am Totensonntag: nicht
veröffentlicht“, „Öffnet am Fr, 20.11.“, „Saison 2026 beendet“, „Öffnungszeiten noch nicht veröffentlicht“.
`aktuelleSaison(eintraege)` = die Saison mit dem spätesten `bis`, **die Zeitraum und Wochenzeiten hat** (ein neuer, noch leerer
Schlüssel `saisons["2027"]` ändert nichts).

### 4.4 Google: place_id und Fotos
- Text Search (New) je Eintrag (ohne Attraktionen nur für Fotos/Score; Gruppe und Teilmärkte einzeln) mit Name + Ort; Treffer nur
  bei Namensähnlichkeit **und** ≤ 300 m zur gespeicherten Koordinate, sonst Prüf-Hinweis. Gespeichert wird nur `google_place_id`.
- `google_bezug` je Treffer: `markt` (Eintrag ist der Markt selbst), `ort` (Eintrag ist der Ort, z. B. Schloss Benrath oder die
  Arcaden – Bewertungen meinen nicht den Markt), `kein`. Claude schlägt vor, der Auftraggeber bestätigt im Score-Bericht.
- Fotos: bis zu 10 Kandidaten je Eintrag (auch für `ort`-Treffer zulässig, wenn das Foto den Markt zeigt) → Sichtung (W4) →
  Foto-SQL wie Spielplatz Runde 2.

### 4.5 Kurz-Markt-Liste aus der Eventtabelle
Ein Event zählt, wenn alles gilt: Titel passt auf `weihnachtsmarkt|adventsmarkt|wintermarkt|christkindl|weihnachtsbasar|
adventsbasar|veihnachtsmarkt|nikolausmarkt|lichterzauber` (getestet); `datum` oder `datum_bis` zwischen heute und 31.12.; nicht
abgesagt/abgelehnt; Stadtteil ist ein Katalogwert **oder** die Adresse hat eine PLZ aus Düsseldorf (40210–40629), Neuss
(41460–41472) oder Ratingen (40878–40885); `quelle_name` ≠ Meetup.com; nicht in `event_ausschluss.csv`; passt auf kein
`event_muster` eines aktiven Guide-Eintrags; Titel+Datum+Ort-Dubletten (bestehende Normalisierung) nur einmal. Höchstens 12,
nach Datum. Test-Fehltreffer: Leipziger Weihnachtsmarkt (Ausschlussliste), Gertrudenhof (Hürth), Secret-Hitler-Abend (Meetup).
Test-Treffer: Bücherweihnachtsmarkt (einmal), zakk, Jugendkirche, Bulle.

### 4.6 Score und Top 5 (W3, intern)
**Score 0–10** (`score.py`, reine Funktion, nur Märkte und Gruppe, keine Attraktionen):
| Teil | Gewicht | Berechnung |
|---|---|---|
| Beliebtheit | 45 % | Nur bei `google_bezug = markt`: Bayes-Mittel `B = (n·R + m·C)/(n + m)` mit `m = 100`, `C` = Mittel aller Markt-Treffer; Teilwert `(B − 3,5)/1,5` auf 0–1 begrenzt (30 %) plus Reichweite `log10(n+1)/log10(n_max+1)` (15 %). Bei `ort`/`kein`: beide Teilwerte neutral 0,5, Hinweis im Bericht |
| Angebot | 25 % | Zahl belegter Merkmale aus {eisbahn, riesenrad, karussell, kindereisenbahn, kinderprogramm, puppenbuehne, buehnenprogramm, kunsthandwerk, krippe} / 4, begrenzt auf 1. Gruppe: Merkmale der Teile und Attraktionen zählen mit |
| Nutzwert | 15 % | Öffnungstage der Saison / 35, begrenzt auf 1 (10 %); Eintritt frei belegt = 1, kostenpflichtig = 0, unbekannt = 0,5 (5 %) |
| Erreichbarkeit | 15 % | Haltestelle mit Zitat/Netzplan genannt = 1, sonst 0,5 |
**Skala:** gewichtete Summe der Teilwerte (0–1) **× 10**, auf eine Nachkommastelle gerundet, begrenzt auf 0–10 – dieselbe Skala wie
`score_manuell`. `score_manuell` gewinnt, **wenn es gesetzt ist** (auch `0`); leer = Rechenwert. **Randfälle:** Gibt es keinen einzigen
Treffer mit `google_bezug = markt`, ist die Beliebtheit für alle 0,5 und die Reichweite entfällt (ihr Gewicht geht an den Bayes-Teil;
`C` und `n_max` werden dann nicht gebildet). Gibt es Markt-Treffer, aber `n_max = 0` (alle ohne Bewertung), ist die Reichweite für
alle 0 und `C` wird nicht gebildet (Bayes-Teil dann 0,5). Beim Angebot zählt `teilweise` als halbes Merkmal, `nein` und „keine Angabe“ nicht.
`n` und `R` (Anzahl/Sterne) holt der Lauf live (Text Search Enterprise, Felder `rating`, `userRatingCount`) und schreibt sie **nur**
in `score_bericht.md` (gitignored); in die DB kommt nur `score` mit Teilwerten, `google_bezug` und `stand` (E12).
**Händische Prüfung:** Der Auftraggeber liest `score_bericht.md` (Rohwerte, Teilwerte, Rangliste) und setzt bei Bedarf
`score_manuell` in `maerkte.csv` (gewinnt immer). Erst danach Freigabe der Sortierung. Neuer Lauf frühestens nach Zeitänderungen
oder im Dezember (Freikontingent).
**Top 5:** Claude schlägt fünf Einträge vor (Score, Vielfalt: höchstens zwei aus der Gruppe Innenstadt – **die Gruppenzeile zählt als
einer dieser zwei Plätze** –, mindestens ein
Stadtteil-Markt, mindestens einer für Familien), der Auftraggeber trägt `top5_rang` 1–5 ein. Kandidaten nur mit belegtem Zeitraum und
belegten Zeiten der aktuellen Saison. Je Top-Eintrag ein Begründungssatz aus belegten Angaben („Kindereisenbahn und Kunsthandwerk vor
der Schlosskulisse, nur an den Adventswochenenden“). Ohne fünf Einträge mit `top5_rang` entfällt der Block (kein Auffüllen).

### 4.7 Badges (aus Daten, keine Handvergabe)
| Badge | Regel | Icon |
|---|---|---|
| Unser Tipp | `top5_rang` gesetzt | `star` |
| Für Familien | belegt `kinderprogramm` oder `karussell` oder `kindereisenbahn` oder `puppenbuehne` | `child_care` |
| Mit Eisbahn | Merkmal `eisbahn`, bei der Gruppe über die Attraktion | `ice_skating` |
| Mit Riesenrad | Merkmal `riesenrad`, bei der Gruppe über die Attraktion | `attractions` |
| Mit Kindereisenbahn | Merkmal `kindereisenbahn` | `train` |
| Kunsthandwerk | Merkmal `kunsthandwerk` oder `art` enthält `kunsthandwerk` | `palette` |
| Schlosskulisse | `art` enthält `schloss` | `castle` |
| Lange offen | eine belegte Wochenzeit bis ≥ 22:00 | `nightlight` |
| Nur am Wochenende | Wochenzeiten nur Fr/Sa/So (Hinweis, kein Filter) | `event` |
Karte: höchstens drei Badges (Reihenfolge der Tabelle). Filter-Chips (UND) für Für Familien, Eisbahn, Riesenrad, Kindereisenbahn,
Kunsthandwerk, Lange offen; ein Chip erscheint ab **2** sichtbaren Einträgen mit dem Badge (bei Eisbahn/Riesenrad/Kindereisenbahn
ab 1, weil es dort die Antwort auf eine Suchfrage ist).

### 4.8 Scraper-Korrektur `datum_bis` (Stufe 2)
`visitduesseldorf.py` liest bei Teasern mit Zeitraum `datum_bis` (bzw. das Toubiz-JSON wie `visitduesseldorf_fuehrungen.py`). Vorher
prüfen, ob der Upsert ein gesetztes `datum_bis` später mit `NULL` überschreibt. Die Empfehlungs-Regel „Tipp-Flagge ab 8 Tagen Laufzeit
nur am Fokustag“ verhindert sechs Wochen Weihnachtsmarkt als Tipp des Tages.

---

## 5. Website

### 5.1 Daten und Logik
- `web/lib/weihnachtsmaerkte-daten.ts`: eigener Lader `weihnachtsmaerkteLaden()` wie `spielplaetzeLaden` – `"use cache"`, seitenweise,
  nur `typ='weihnachtsmarkt'` und `aktiv=true`, **ohne Score-Schwelle** (`orteLaden` verlangt `qualitaets_score ≥ 7`,
  `web/lib/orte.ts:183`, und fiele aus). Dafür `"weihnachtsmarkt"` in `EXTRAS_FELDER` (`web/lib/orte.ts:19`, sonst lädt
  `SPALTEN_MIT_EXTRAS` das Feld nicht) und in `OrtTyp` (`web/lib/typen.ts:52`).
- `web/lib/weihnachtsmaerkte.ts`: Profil nur aus bekannten Werten; `oeffnungAm` und `aktuelleSaison` (4.3); `badges` (4.7); Filter `tag`, `badge` (UND), `gebiet` (Innenstadt / Düsseldorfer Stadtteile / Neuss / Ratingen),
  `sort` (`empfohlen` = Top-5-Rang, dann `score.manuell ?? score.wert`, dann Name; `name`); `istIndexierbar` (5.4).
- `SAISON_GUIDES` in `web/lib/landing.ts` (E9), Schalter `WEIHNACHTSMAERKTE_VERLINKT` in `web/lib/schalter.ts` mit Liste aller
  Stellen im Kommentar (wie `SPIELPLAETZE_VERLINKT`).

### 5.2 Hub `/guides/weihnachtsmaerkte` (`instant = false`)
Reihenfolge:
1. Hero (heller Grund, Dark-Variante), H1 „Weihnachtsmärkte in Düsseldorf {saison}“, Unterzeile „{n} Märkte in Düsseldorf, Neuss und
   Ratingen vom {von} bis {bis}, dazu Eisbahn und Riesenrad“, Brotkrumen, „Stand der Angaben: {jüngstes stand}“.
   `{n}` zählt Teilmärkte und Märkte außerhalb der Gruppe – **nicht die Gruppenzeile und nicht die Attraktionen**. `{von}`/`{bis}` nur
   aus diesen Märkten (2026: 19.11. bis 30.12.), nicht aus den Attraktionen (Eisbahn ab 06.11.).
2. **Tagesleiste**: Heute (Standard), Morgen, nächster Samstag, Totensonntag, Heiligabend, 2. Weihnachtstag, „Datum wählen“ (`?tag=`).
3. **Unsere Top 5** (4.6, Stufe 1b) als Karten mit Begründungssatz.
4. **Karte + Liste** (Karte Standard, Liste daneben bzw. darunter mobil) über `/api/guide-karte?hub=weihnachtsmaerkte`, eigene
   Punktfunktion: id, Name, Gruppe, Stadtteil, Koordinate, URL, Thumb, Badges, kompakte Zeiten (für die Pin-Farbe im Browser).
   **Keine Bewertung, kein Score.** Pin-Farbe (Stufe 1b; in 1a einfarbig, Zustand nur in der Liste) mit Legende und Text, im Browser gerechnet: heute offen (Gold) / heute zu (Grau) / vor bzw. nach Saison (hell) /
   unbekannt (neutral). Gruppenzeile ohne Pin; in der Liste eine Gruppenkarte mit den Teilen. Pins ohne `transform` am Marker.
   Filter (Stufe 1b): Badges, Gebiet, „nur heute geöffnet“, Sortierung.
5. **Sonderzeiten auf einen Blick**: Tabelle Eintrag × (Totensonntag, Heiligabend, 1. und 2. Weihnachtstag, Silvester, Neujahr) plus
   Spalte „letzter Tag“ – Einträge, deren Zeitraum den Tag nicht enthält, zeigen „–“; sonst nur
   belegt, sonst „nicht veröffentlicht“.
6. **Kleine Weihnachtsmärkte an einzelnen Tagen** (4.5, Stufe 1b), Links auf die Event-Seiten; entfällt ohne Treffer.
7. `OrtLinkListe` mit allen Einträgen, `GuideSeoText` mit fünf FAQs (6.2), Quellen-Fuß (Veranstalter, Visit Düsseldorf,
   „Kartendaten © OpenStreetMap-Mitwirkende“), Haftungssatz (6.4).
Filter-/Datums-URLs `noindex, follow`, Canonical immer `/guides/weihnachtsmaerkte` (Seite setzt es selbst wie `guides/clubs/page.tsx`,
nicht über `seitenMetadaten({ noindex: true })`). JSON-LD: BreadcrumbList + ItemList (nur indexierbare).

### 5.3 Detail `/guides/weihnachtsmaerkte/[slug]` (`instant = false`)
- Brotkrumen; Bild (Foto mit Urheber oder Illustration); H1; Badges; Stadtteil, Adresse.
- **Zustandszeile** (Browser, `aria-live="polite"`) über der **vollständigen Zeitentabelle** (Server, `<table>` mit `<th scope>`):
  Zeitraum, Wochenzeiten, Sonderzeiten mit Feiertagsnamen, „laut {Quelle}, Stand {stand}“ mit Link; bei Erbung „gleiche Zeiten wie
  der Weihnachtsmarkt in der Innenstadt“; bei „Händler dürfen bis 22 Uhr verlängern“ der Satz als Hinweis.
- Beschreibung, Merkmal-Kacheln (nur belegt), Eintritt (Kö on Ice mit Preisen, belegt), Anfahrt (Haltestellen, Parken, P+R),
  „Route planen“ (Google-Maps-Link aus der Koordinate, öffnet erst nach Klick).
- Gruppe: Liste der Teile mit Mini-Karte; Teilmarkt: „Weitere Märkte in der Innenstadt“; sonst die drei nächsten Einträge.
- „In der Nähe“ (Stufe 1b): bis zu 2 Cafés und 2 Kneipen aus den Guides (≤ 800 m, kanonische URL).
- Event-Kasten-Gegenstück: Stufe 2 „Termine auf dem Markt“ (3.3).
- JSON-LD während der Saison: `Event` (`name` „{Name} {Jahr}“, `startDate`/`endDate`, `eventStatus` Scheduled,
  `eventAttendanceMode` Offline, `location` Place mit `geo`/`address`, `isAccessibleForFree` nur bei belegtem Eintritt, `organizer`
  nur belegt, `image` nur bei Foto) + BreadcrumbList; nach der Saison nur `Place`. Kein `aggregateRating`.
- Title „{Name} {Jahr}: Öffnungszeiten, Anfahrt & Infos“ (nach der Saison ohne Jahr), Description aus Zeitraum + zwei Badges.

### 5.4 Indexierung
- Hub immer indexierbar.
- Detail indexierbar, sobald **irgendeine** Saison Zeitraum **und** Wochenzeiten hat **und** die Zeile eine Beschreibung hat; sonst
  `noindex, follow`, ohne Canonical, nicht in der Sitemap. Ein neuer, noch leerer Saison-Schlüssel ändert daran nichts – eine einmal
  indexierbare Seite bleibt es auch nach der Saison und beim Jahreswechsel.
- Sitemap: Hub + indexierbare Details, `lastModified` aus `aktualisiert_am`.
- IndexNow beim Livegang (Hub, `/guides`, indexierbare Details), nach Zeitänderungen und nach Freischaltungen (Slugs aus dem
  `RETURNING` der SQL).

### 5.5 Proxy, Foto-Proxy, Karten-API
- `pfad-pruefung.ts`: `OrtHub`/`HUBS` + `weihnachtsmaerkte`; `ortLaden` liest zusätzlich
  `wm_freigeschaltet_am:extras->weihnachtsmarkt->>freigeschaltet_am`; `weihnachtsmarktEntscheidung`: aktiv und Typ → weiter;
  nie freigeschaltet/unbekannt → 404; abgeschaltet → **308 auf `/guides/weihnachtsmaerkte`**. In `ortEntscheidung` steht der Aufruf
  **ganz oben** neben dem Spielplatz-Zweig, **vor** jedem Zugriff auf `HUB_TYPEN` (sonst wirft `HUB_TYPEN[hub]` für den neuen Hub).
- **Stadtteil-Unterpfad:** Mit dem Eintrag in `HUBS` wird `/guides/weihnachtsmaerkte/stadtteil/<slug>` eine erkannte Route, und der
  heutige Zweig `guide-stadtteil` (`pfad-pruefung.ts:230`) ließe jeden gültigen Stadtteil durch (`WEITER`) – eine Seite gibt es nicht,
  `notFound()` wäre mit cacheComponents ein Soft-404 mit Status 200. Deshalb: im Zweig `guide-stadtteil` für `weihnachtsmaerkte`
  **immer `fehlt`**, auch bei gültigem Slug. Tests in `seo-a1`/`seo-b`.
- `/ort-foto/[slug]`: Zweig für aktive Einträge, inaktiv → 404.
- `/api/guide-karte`: Zweig `hub=weihnachtsmaerkte`.

| Stelle | nie freigeschaltet | aktiv | abgeschaltet | wieder freigeschaltet |
|---|---|---|---|---|
| Proxy Detail | 404 | 200 | 308 → Hub | 200 (gleicher Slug) |
| Sitemap | nein | ja, wenn indexierbar | nein | ja, wenn indexierbar |
| `/ort-foto` | 404 | Foto bzw. 404 | 404 | Foto bzw. 404 |
| Karte, Liste, Sonderzeiten-Tabelle, Zahlen | nein | ja | nein | ja |
| Top 5, Startseiten-Box | nein | ja, **zusätzlich** nach 5.6 (Schalter, Datumsfenster 15.11.–30.12.) und 5.8 (Top 5 nur mit fünf Rängen und nur bis zum 30.12.; ab dem 31.12. entfällt der Block) | nein | wie aktiv |

### 5.6 Einbaustellen (W5: alle während der Saison)
| Stelle | Inhalt | Steuerung |
|---|---|---|
| `/guides`-Kachel (`app/guides/page.tsx`) | an **erster** Stelle, Einheit „Märkte“, Bild `weihnachtsmaerkte.webp` | Schalter |
| Menü/Mobilmenü (`GUIDE_LINKS`, `rahmen.tsx`), Footer-Spalte und Markenabsatz | „Weihnachtsmärkte“ als erster Guide-Eintrag | Schalter |
| Startseite: Box „Weihnachtsmärkte heute geöffnet“ (nach Tipp/Picks) | bis zu 4 heute offene Einträge (Top 5 zuerst) mit Zeit, Link zum Hub; ohne belegt offenen Eintrag „Heute ist kein Markt als geöffnet belegt. In der Übersicht seht ihr, wo die Zeiten fehlen und wann es weitergeht.“ | Schalter **und** Datum 15.11.–30.12. |
| Kategorie `food` und `familie` (`EXTRA_LINKS`, `app/kategorie/[slug]/page.tsx:29`) | **ergänzen, nicht ersetzen**: `food` behält „Restaurants & Cafés“ und bekommt „Weihnachtsmärkte“; `familie` bekommt „Weihnachtsmärkte für Familien“ (→ `?badge=familien`, ab Stufe 1b) neben den Spielplätzen | Schalter |
| Unterkategorie `food/maerkte` (Stufe 1b; `app/kategorie/[slug]/[unter]/page.tsx`, hat keine `EXTRA_LINKS`) | eigener Link „Alle Weihnachtsmärkte im Überblick“ | Schalter |
| Event-Seiten (Stufe 1b) | Titel passt auf das Muster aus 4.5: Link „Alle Weihnachtsmärkte in Düsseldorf“; passt auf `event_muster`: Markt-Kasten (3.3) | Schalter |
| Symbolbild-Zeitfenster `advent-weihnachtsmarkt` bis 30.12. | – | – |
| `public/llms.txt` (Abschnitt „Guides“) | Zeile „Weihnachtsmärkte“ | von Hand |
| FAQ „Welche Guides kommen noch dazu?“ (`lib/guide-texte.ts`) | Satz zum Weihnachtsmarkt-Guide | Schalter |
| Datenschutz | Google-Maps-Absatz um „Route planen“ im Weihnachtsmarkt-Guide ergänzen (kein Standort-Knopf in Stufe 1) | – |
Am 02.01.2027 stellt ein Commit den Schalter auf `false` (Erinnerung im Kalender des Auftraggebers); Seiten bleiben erreichbar.

### 5.7 Design, Barrierefreiheit, Mobil
Bestehende `gd-*`-Tokens, heller Hero mit Dark-Variante; Zustandsfarben immer mit Text; Badges mit Icon **und** Text; Touch-Ziele
≥ 44 px; 375 px ohne Querscrollen; hell/dunkel geprüft; Liste als Alternative zur Karte; Sonderzeiten-Tabelle mobil als Karten je
Eintrag statt breiter Tabelle.

### 5.8 Nach der Saison und 2027
| Zeitpunkt | Hub | Detail | Links |
|---|---|---|---|
| vor dem ersten `von` | „öffnet am …“ | Zeitentabelle | Schalter an |
| Saison | Tageszustand | Tageszustand | an |
| nach dem `bis` eines Eintrags | Eintrag „Saison beendet“ (Attraktionen laufen länger) | Tabelle bleibt, Zustand „beendet“ | an bis 02.01. |
| 31.12. bis zum spätesten `bis` (2026/27: Kö on Ice 10.01.) | Märkte als „Saison beendet“, oben die noch laufenden Attraktionen („Eisbahn und Riesenrad laufen noch bis …“), keine Top 5, keine Kurz-Markt-Liste | Märkte „beendet“, Attraktionen Tageszustand | aus ab Commit 02.01. |
| nach dem spätesten `bis` aller Einträge | Hinweis „Die Saison {Jahr} ist vorbei. Die Termine für {Jahr+1} tragen wir ein, sobald die Veranstalter sie veröffentlichen.“ Liste mit „So war es {Jahr}“, keine Top 5, keine Kurz-Markt-Liste | „So war es {Jahr}“, kein `Event`-JSON-LD, Title ohne Jahr | aus (Commit 02.01.) |
| neue Saison eingetragen (Herbst 2027) | Jahr aus `aktuelleSaison`, neue Top 5 | neue Zeiten | Schalter an (Commit im Oktober) |
| Eintrag kommt nicht wieder | – | abschalten → 308 Hub | – |
Kein 410, kein noindex wegen Saisonende: Wer im Oktober „Weihnachtsmarkt Düsseldorf 2027“ sucht, landet auf derselben URL, die
seit 2026 Verlinkungen sammelt. Score und Top 5 gelten je Saison (2027 neu prüfen).

### 5.9 SEO
- Wichtigste Anfragen (Stufe 3 misst sie): „weihnachtsmarkt düsseldorf (2026)“, „… öffnungszeiten“, „… totensonntag“, „… heiligabend
  geöffnet“, „weihnachtsmarkt düsseldorf eisbahn“, „kö on ice“, „riesenrad düsseldorf“, „winter village düsseldorf“, „weihnachtsmarkt
  benrath“, „weihnachtsmarkt kaiserswerth“, „areal böhler weihnachtsmarkt“, „weihnachtsmarkt neuss“, „weihnachtsmarkt ratingen“.
- Antworten stehen im ersten HTML (Zeitentabellen, Sonderzeiten-Tabelle, FAQ); Datum „Stand“ sichtbar; Titel mit Jahr nur während
  der Saison; interne Links aus Startseite, Menü, Kategorien, Event-Seiten, `/guides`, `llms.txt`.
- Keine Keyword-Seiten ohne Inhalt (keine „Weihnachtsmarkt {Stadtteil}“-Seiten ohne Markt).

### 5.10 Piktogramm und Bilder
- Eigenes Outline-Icon `wm:markt` (Marktbude mit Giebeldach und Stern, 2 px, 24er Raster) als `public/guides/icons/wm-markt.svg`,
  eingebunden wie `sp:` (`globals.css`); Vorschlag: Claude zeichnet einen ersten Entwurf, der Auftraggeber ersetzt ihn bei Bedarf.
  Bis dahin Material `storefront`.
- Hero/Kachel `web/public/guides/weihnachtsmaerkte.webp` (Auftraggeber erzeugt, Prompt Abschnitt 11). Einträge ohne Foto bekommen
  dasselbe Bild verkleinert (eine Illustration reicht für Stufe 1).

---

## 6. Texte (Entwürfe zur Freigabe)

### 6.1 Einleitung (Hub)
„Hier findet ihr alle {n} Weihnachtsmärkte in Düsseldorf, Neuss und Ratingen – vom großen Markt in der Innenstadt mit Eisbahn und
Riesenrad bis zu den Märkten in Benrath, Bilk und auf dem Areal Böhler. Auf einen Blick seht ihr, wer heute geöffnet hat, was es dort
gibt und wie ihr hinkommt. Die Zeiten stammen von den Veranstaltern; Sonderzeiten an Totensonntag und Weihnachten stehen extra
dabei.“ (Ortsnamen nach der finalen Liste.)

### 6.2 Fünf FAQs (feste Satzmuster, Namen und Zeiten aus den Daten, interne Links)
1. „Wann öffnen die Weihnachtsmärkte in Düsseldorf {saison}?“
2. „Haben die Weihnachtsmärkte am Totensonntag geöffnet?“
3. „Welche Weihnachtsmärkte haben an Heiligabend, an den Weihnachtstagen, an Silvester und an Neujahr geöffnet?“
4. „Wo gibt es in Düsseldorf eine Eisbahn oder ein Riesenrad?“
5. „Welcher Weihnachtsmarkt eignet sich für Familien mit Kindern?“ (Link in Stufe 1a auf den Hub ohne Parameter, ab 1b auf `?badge=familien`)
Die Satzmuster werden einmal freigegeben; 2027 muss nichts umgeschrieben werden. Nicht belegte Sonderzeiten heißen „nicht veröffentlicht“.

### 6.3 Beschreibungen und Top-5-Begründungen
2–4 eigene Sätze je Eintrag bzw. ein Satz je Top-5-Platz, nur aus belegten Angaben, keine Werbesprache, keine Übernahme von
Veranstaltertext.

### 6.4 Haftung (Fuß von Hub und Detail)
„Angaben ohne Gewähr, Stand {stand}. Die Veranstalter können Zeiten kurzfristig ändern, etwa bei Sturm – im Zweifel vorher auf der
Seite des Veranstalters nachsehen.“ (mit Link)

---

## 7. Tests
Zwei Listen: **1a** muss vor dem Deploy von Stufe 1a grün sein (Schritt 5), **1b** vor dem Deploy von Stufe 1b (Schritt 6b).
Tests für 1b-Bausteine entstehen mit diesen Bausteinen und blockieren 1a nicht.

### 7.1 Stufe 1a
**Python:** Zeiten-/Sonderzeiten-Parser (Kurzschrift, `Mo-Do`, Einzeltage, `zu`, ungültig/`von > bis`/über Mitternacht/Sonderdatum
außerhalb → Fehler, Saison nicht geschrieben); Toubiz-Ableitung (Wochenzeit = häufigste Zeit je Wochentag, `closed` → Sonderzeit „zu“,
**fehlender Tag → nur Hinweis, nie „zu“**, Fixture aus einer gespeicherten Toubiz-Antwort); **feldweise Erbung** (leere Zelle übernimmt
das Feld der Gruppe, gesetzte Zelle nicht; Winter Village behält `von` 20.11. und erbt Zeiten und Sonderzeiten; Zeile fehlt ganz → alle
vier Felder geerbt; Attraktion erbt nie; `geerbt` listet die übernommenen Felder, `geerbt_von` die Gruppe); Pflichtfelder,
Koordinaten-Rechteck, Stadtteil-Katalog inkl. Neuss/Ratingen; Wiederholungsimport über `schluessel`; Import schreibt
`aktiv`/`freigeschaltet_am` nie; Slug fest ab Freischaltung; `ausgeschlossen`; Freischalt-SQL-Textprüfung (`COALESCE`, `RETURNING`,
Filter auf alten `aktiv`-Wert, Bedingung „Zeitraum und Wochenzeiten“); Belegprüfung.

**Web (vitest):** `oeffnungAm` gegen die gemeinsame Fixture (vor/nach Saison mit `vor_saison`/`nach_saison`, `zu` nur innerhalb des
Zeitraums, Sonderzeit schlägt Wochenzeit, Totensonntag zu mit Grund, **22.11. ohne Sonderzeile → `unbekannt`, nicht offen** (Nordstraße,
Riesenrad), Totensonntag 2027 = 21.11. berechnet, Heiligabend verkürzt, **31.12. und 01.01. ohne Sonderzeile → `unbekannt`**, Benrath
Mo–Do zu, keine Zeiten → unbekannt, **05.01.2027 Kö on Ice offen laut Wochenzeit aus `saisons["2026"]`, 11.01.2027 `nach_saison`**,
Server in UTC um 23:30 bzw. 00:30, Uhrzeit „öffnet um“/„schon geschlossen“); **feldweise Erbung** (Winter Village am 19.11.
`vor_saison`, am 22.11. zu); `aktuelleSaison` (leerer Schlüssel 2027 ändert nichts, Indexierbarkeit bleibt); **Platzhalter**:
Server-HTML und Karten-API enthalten keinen Zustand „offen/zu“; `?tag=` (gültig → Server rechnet, ungültig → ignoriert, Canonical auf
den Hub, `noindex`); Sonderzeiten-Tabelle (sechs Spalten inkl. Silvester/Neujahr, nicht belegt → „nicht veröffentlicht“);
Startseiten-Box (`heuteBerlin()`, nur im Datumsfenster und mit Schalter, Satz ohne belegt offenen Markt); Hero-Zahl ohne Gruppenzeile
und Attraktionen, Zeitraum 19.11.–30.12.; Hinweis „Saison vorbei“ erst nach dem spätesten `bis` (Kö on Ice 10.01.); Badges je Regel
(Gruppe erbt Eisbahn/Riesenrad über Attraktion); Karten-Punkte ohne Bewertung/Score; JSON-LD (`Event` nur in der Saison, kein
`aggregateRating`); Indexierbarkeit; Pfadentscheidungen (404/308; **Stadtteil-Unterpfad mit gültigem Stadtteil `altstadt` → `fehlt`,
nicht `WEITER`**; `ortEntscheidung("weihnachtsmaerkte", …)` wirft nicht); `EXTRA_LINKS.food` enthält weiterhin „Restaurants &
Cafés“; Sitemap; Schalter aus → keine Links; Symbolbild bis 30.12.; Texte (5 FAQs, FAQ 5 verlinkt in 1a den Hub ohne Parameter,
ihr/euch, keine Score-Zahl, keine Google-Sterne).

**Browser:** Desktop und 375 px, hell/dunkel; Hub (Liste, einfarbige Karte), Detail; Uhr auf 10:59 / 11:00 / 21:01 gestellt;
`?tag=2026-11-22` und `?tag=2026-12-24`; Startseiten-Box; kein Hydration-Fehler in der Konsole.

### 7.2 Stufe 1b
**Python:** Score (Bayes, Grenzen 0/1, neutral bei `ort`/`kein`, kein Markt-Treffer → Beliebtheit 0,5 ohne Reichweite, **`n_max = 0`
→ Reichweite 0**, Skala ×10, `score_manuell` gewinnt auch bei 0, `teilweise` = halbes Merkmal, Attraktion ohne Score);
**Score-Schreiben enthält keine Rohwerte** (JSON-Schlüssel `rating`/`userRatingCount` fehlen).
**Web (vitest):** Filter (UND, Chip-Schwellen 2 bzw. 1, `?badge=familien`); Sortierung (Top-5-Rang, dann `score_manuell ?? score.wert`,
dann Name); Top-5-Block entfällt ohne fünf Ränge und ab dem 31.12.; Pin-Farben im Browser; Kurz-Markt-Muster (Fehl- und
Treffer aus 4.5, Ausschluss über `event_muster`); Event-Kasten; Links `food/maerkte` und `familie`; FAQ 5 verlinkt ab 1b
`?badge=familien`; Foto-Proxy-Zweig (`expire` ≤ 30 Tage, inaktiv → 404).
**Browser:** Filter mobil, Pin-Legende hell/dunkel, Event-Seite mit Kasten.

---

## 8. Ablauf und Freigaben
| Schritt | Stufe | Inhalt | Freigabe / Ergebnis |
|---|---|---|---|
| 0 | – | Plan, Cursor-Prüfung, Auslegung „Eisbahn/Kindereisenbahn“ bestätigen | Freigabe des Plans |
| 1 | 1a | SQL `database/orte_typ_weihnachtsmarkt_2026-11-17.sql`: `DROP CONSTRAINT IF EXISTS orte_typ_check` und neu anlegen mit **genau der Liste aus `database/orte_typ_imbiss_2026-11-05.sql`** (restaurant, imbiss, cafe, kneipe, club, spielplatz, ausflug, wochenendtipp) **plus** `weihnachtsmarkt` – fehlt ein alter Typ, lehnt die Datenbank bestehende Zeilen ab; vorher `SELECT DISTINCT typ FROM orte` in einem `DO`-Block: jeder Wert, der nicht in der neuen Liste steht, bricht die Migration mit `RAISE EXCEPTION` ab (die Imbiss-Datei hat diese Prüfung nicht); danach die Kontrollabfrage der Imbiss-Datei | Auftraggeber führt aus |
| 2 | 1a | `toubiz_lesen.py` (kostenlos) → Entwurf; Claude prüft gegen Veranstalterseiten, schreibt `maerkte.csv`, `saison-2026.csv`, `merkmale.csv`; **Auftraggeber liest Neuss/Ratingen** (W2) und gibt Zeitraum, Zeiten, Sonderzeiten, URL | Auftraggeber + Cursor lesen `pruefung.csv` gegen |
| 3 | 1a | Import (inaktiv) – **Freigabe des Schreibwegs** vorher; Freischalt-SQL `database/weihnachtsmaerkte_freischalten.sql`: nur Einträge, deren Saison **Zeitraum und Wochenzeiten** hat (Gruppenzeile und erbende Teilmärkte nach der Erbung), ohne `ausgeschlossen`; `COALESCE`, Filter auf alten `aktiv`-Wert, `RETURNING slug` wie Spielplatz Schritt 6 | Auftraggeber führt SQL aus |
| 4 | 1a | Website-Kern (Umfang Stufe 1a unten), Texte 6.1–6.4, Tests | Texte zur Freigabe |
| 5 | 1a | Tests 7.1, Build, Browser; Abnahme 12.1; Cursor-Check | Deploy nur nach OK |
| 6 | 1a | Deploy, Live-Kontrolle (`curl -I`: Hub 200, Detail 200, unbekannt 404, Stadtteil-Unterpfad mit gültigem Stadtteil 404), IndexNow als **manueller Lauf** mit den Guide-URLs wie beim Spielplatz-Livegang (`pipeline/indexnow.py` meldet von sich aus nur Event-URLs) | Bericht |
| 6b | 1b | Website-Ausbau bis spätestens Fr 27.11. (Umfang Stufe 1b unten), Tests 7.2, Abnahme 12.2, Cursor-Check | Deploy nur nach OK |
| 7a | 1b | EEA-Bedingungen der Google Maps Platform lesen (Speicherung, Anzeige) – Ergebnis in Abschnitt 10 nachtragen | vor jedem Google-Lauf |
| 7b | 1b | Google-Lauf (place_id, Rohwerte nur im Bericht, Foto-Kandidaten): **Kosten vorher nennen** → Score-Bericht → Auftraggeber prüft Score, setzt `score_manuell`/`top5_rang` → Import → Top 5 + Sortierung live (kein Deploy, nur Daten) | Auftraggeber |
| 7c | 1b | Foto-Sichtung (W4) → Foto-SQL | Auftraggeber sichtet und führt aus |
| 8 | 2 | Event ↔ Eintrag „Termine auf dem Markt“ (3.3), Scraper `datum_bis` (4.8), Sichtungen (Tassenpfand, WC, Barrierefreiheit) | Deploy nach OK |
| 9 | 2 | Bis 30.12.: `toubiz_lesen.py` zweimal pro Woche (Abweichungsliste), Kontrolle der Sonderzeiten am 21.11. und 23.12. | – |
| 10 | 3 | 02.01.2027 Schalter aus; Januar: Suchanfragen auswerten, FAQ nachschärfen; `score_bericht.md` gelöscht? | Bericht |
| 11 | 3 | Herbst 2027: `saison-2027.csv` (Toubiz + Profil-Skript mit KI/Websuche und Belegprüfung), Score/Top 5 neu, Schalter an | Kosten vorher nennen |

**Umfang Stufe 1a (Livegang Ziel Sa 21.11., vor dem Totensonntag):** belegte Zeiten (Schritt 2), Hub mit Tagesleiste, **Liste** mit
Badges auf den Karten, Karte mit **einfarbigen** Pins (Zustand nur in der Liste), Gruppenkarte Innenstadt, **Sonderzeiten-Tabelle**,
Detailseiten mit Zeitentabelle und Zustandszeile (Browser), Anfahrt, FAQ, Proxy-Statuscodes (404/308, Stadtteil-Unterpfad 404),
Sitemap, Schalter mit Menü/Footer, `/guides`-Kachel vorne, Startseiten-Box, `EXTRA_LINKS` `food`, Symbolbild-Fenster, `llms.txt`,
JSON-LD. Icon: Material `storefront`.
**Umfang Stufe 1b (bis spätestens Fr 27.11., vor dem 1. Advent):** Filter (Badges, Gebiet, „nur heute geöffnet“) und Sortierung,
Pin-Farben nach Zustand, Kurz-Markt-Liste (4.5), Event-Seiten-Links und Markt-Kasten (3.3), Link auf `food/maerkte` und `familie`,
„In der Nähe“ (Cafés/Kneipen), eigenes Icon `wm:markt`, Google-Lauf mit Score, Top 5 und Fotos (7a–7c).
Die Top 5 und die Score-Sortierung brauchen Schritt 7b; ohne Ränge entfällt der Top-5-Block, sortiert wird nach Name.
**Rückfallebene:** Livegang mit den Einträgen, deren Zeiten belegt sind; der Rest bleibt inaktiv und kommt per Freischalt-SQL nach.
Nicht in Stufe 1: „Termine auf dem Markt“, Scraper-Änderung, Standort-Knopf, Stadtteilseiten, Ausflugsziele, Meldefunktion.

## 9. Kosten (Schätzung, vor jedem Lauf konkret nennen)
Preise laut Google-Preisseite (Stand 11.11.2026, USD je 1.000 Aufrufe, Freikontingent je SKU und Monat):
| Posten | Menge | Preis | Schätzung |
|---|---|---|---|
| Toubiz/Veranstalter lesen | ~15 Seiten | – | 0 $ |
| Text Search Enterprise (`rating`, `userRatingCount`, `photos`) | ~16 Einträge × 1–2 = ≤ 32 | 35 $/1.000, 1.000 frei | 0 $ (im Freikontingent, sofern im Monat nicht anders verbraucht), höchstens 1,15 $ |
| Fotos (Place Photos) | ≤ 16 × 10 = 160 | 7 $/1.000, 1.000 frei | Freikontingent November ist durch die Spielplatz-Fotos vermutlich verbraucht → ≈ 1,10 $; im Dezember 0 $ |
| KI | Beschreibungen schreibt Claude in der Sitzung (kein API-Lauf) | – | 0 $ |
| Score-Neulauf Dezember | ≤ 32 | Freikontingent | 0 $ |
**Summe Stufe 1+2: unter 3 $**, Rahmen E13 (15 $). Profil-Skript 2027: ~16 × 0,10–0,20 $ ≈ 2–3 $ (dann neu nennen).

## 10. Risiken und Gegenmaßnahmen
| Risiko | Gegenmaßnahme |
|---|---|
| Falsche Öffnungszeit (Totensonntag, Heiligabend, eigene Zeiten der Attraktionen) | Nur belegt (E4), Quelle + Stand sichtbar, Stichtage in `pruefung.csv`, Kontrolle 21.11. und 23.12., Toubiz-Abweichungsliste zweimal pro Woche |
| Widersprüchliche Quellen (Starttag Winter Village/Roncalli) | Termindaten gelten, Hinweis in `pruefung.csv`, Gegenlesen beim Veranstalter |
| Kurzfristige Schließung (Sturm, Sicherheitslage) | Haftungssatz; Sonderzeit per CSV + Import in Minuten (kein Deploy) |
| „Heute geöffnet“ veraltet durch Cache | Browser rechnet (E5); Stammdaten-Cache 10 Min. |
| Zeitzone | Europe/Berlin fest, Tests mit UTC-Uhr |
| **Google-Bedingungen** (Speicherverbot außer place_id, Koordinate 30 Tage) | E12: nur place_id in der DB, Score ohne Rohwerte, Bericht gitignored und gelöscht, Koordinaten nie aus Google |
| **EEA-Bedingungen ungelesen** | Schritt 7a vor jedem Google-Lauf |
| Bestehende Guides speichern `google_rating`/`google_bewertungen_anzahl` in `orte` | **außerhalb dieses Plans**; als eigener Folgepunkt gemeldet (Abschnitt 13) |
| Google-Bewertung meint den Ort, nicht den Markt (Schloss, Arcaden) | `google_bezug`, neutral bei `ort`, händische Prüfung (W3) |
| Score wirkt willkürlich | nicht öffentlich (W6), `score_manuell`, Top 5 redaktionell |
| Urheberrecht Texte/Fotos (Visit Düsseldorf: alle Rechte vorbehalten, Fotos teils fremd) | Eigene Sätze, Zitate nur intern, keine Fremdfotos (E11) |
| Personen auf Fotos | W4: nur fern/unscharf, Sichtung |
| robots.txt (neuss-marketing.de, duesseldorf.de, Overpass/taginfo-API) | kein Abruf durch Skripte; Neuss über den Auftraggeber (W2); OSM nicht nötig |
| Dünne Detailseiten | Indexregel 5.4 |
| Dubletten Guide ↔ Events | Kurz-Märkte nur Events (W7), große Märkte Guide + Event mit Kasten (3.3), `event_muster` hält die Kurz-Liste sauber |
| Rauschen in der Kurz-Markt-Liste | Muster + PLZ/Katalog + Meetup-Ausschluss + Ausschlussliste (4.5) |
| Zeitdruck | Stufe 1a schlank bis 21.11., Ausbau 1b bis 27.11., Livegang ohne 7b möglich, Rückfallebene (Abschnitt 8) |
| Menü-Link bleibt nach der Saison | Commit 02.01.2027, Erinnerung |

## 11. Bild-Prompts (Auftraggeber erzeugt, WebP nach `web/public/guides/`)
Gemeinsam wie Spielplatz Abschnitt 11: keine erkennbaren Personen, keine Schrift, keine Logos/Marken, kein nachgebautes Wahrzeichen,
fotorealistisch, warmes Licht.

| Datei | Format | Prompt |
|---|---|---|
| `weihnachtsmaerkte.webp` (Hero + `/guides`-Kachel + Ersatzbild; Motiv rechts, Maske nach links) | 16:9, ≥ 1600 × 900 | *Evening photo of a cosy German Christmas market: two or three wooden market stalls with warm fairy lights and fir garlands in the right third of the frame, glowing softly, cobblestones, blurred bokeh lights in the background. The left half is calm: dusk-blue sky and soft out-of-focus lights, suitable for overlaying text. No people, no faces, no text, no signs, no logos, no recognisable landmark, photorealistic.* |

Prüfung vor dem Einbau: keine Person, keine Schrift, als 80 × 80-Quadrat erkennbar, Hero-Text hell und dunkel lesbar.

## 12. Abnahmekriterien

### 12.1 Stufe 1a (vor dem Deploy, Ziel 21.11.)
- Jeder freigeschaltete Eintrag hat Zeitraum, Wochenzeiten, Lage, Stadtteil und Beleg-Link mit Stand; Stichprobe **aller** Einträge
  gegen die Quelle für 22.11., 24.12., 26.12. und 31.12. ohne Abweichung; Attraktionen mit eigenen Zeiten; Winter Village und
  Weihnachtspromenade öffnen am 20.11. mit den Innenstadt-Zeiten.
- „Heute geöffnet“ stimmt im Browser zu drei Uhrzeiten; `?tag=2026-11-22` und `?tag=2026-12-24` korrekt; am 22.11. zeigen Einträge ohne
  belegte Totensonntag-Zeile „nicht veröffentlicht“, keiner „geöffnet“; Sonderzeiten-Tabelle mit Silvester/Neujahr.
- Hub/Detail: Inhalt im ersten HTML, Index-/Canonical-Regeln 5.4, JSON-LD valide, Proxy 404/308 wie 5.5 (Stadtteil-Unterpfad mit
  gültigem Stadtteil 404), Karten-API ohne Bewertung und ohne Zustand.
- Desktop, 375 px, hell/dunkel, keine Hydration-Fehler; Menü/Kachel/Startseiten-Box nur bei Schalter an (Startseite zusätzlich
  Datumsfenster); `food` zeigt beide Links.
- Tests 7.1 grün; Cursor-Check ohne kritische/mittlere Befunde; Deploy nach OK; IndexNow (manueller Lauf) gemeldet.

### 12.2 Stufe 1b (vor dem Deploy, spätestens 27.11.)
- In der DB keine Google-Rohwerte bei Weihnachtsmärkten – Prüfung **nur über JSON-Schlüssel**, nicht über Text (sonst schlägt
  „Ratingen“ an): `SELECT slug FROM orte WHERE typ='weihnachtsmarkt' AND (extras->'weihnachtsmarkt'->'score' ? 'rating' OR
  extras->'weihnachtsmarkt'->'score' ? 'userRatingCount' OR extras ? 'google_rating' OR google_rating IS NOT NULL OR
  google_bewertungen_anzahl IS NOT NULL)` liefert keine Zeile; `score_bericht.md` nicht im Git; der RSC-Payload von Hub und Detail
  (`curl` der Seite) enthält weder `score` noch `rating`-Schlüssel; der Weihnachtsmarkt-Zweig von `/ort-foto` hat `expire` ≤ 30 Tage.
- Top 5 erst nach Eintrag der Ränge durch den Auftraggeber; Badges nur aus belegten Merkmalen; Filter und Pin-Farben stimmen mit der
  Liste überein.
- Kurz-Markt-Liste ohne die bekannten Fehltreffer; Event-Kasten auf zugeordneten Event-Seiten.
- Tests 7.2 grün; Cursor-Check ohne kritische/mittlere Befunde; Deploy nach OK.

### 12.3 Eigene Haken (nicht vorab prüfbar)
Hydration im echten Browser (Schritt 5), EEA-Bedingungen (7a), Neuss/Ratingen (nach den Angaben des Auftraggebers).

## 13. Offene Punkte
- **Bestätigen:** Auslegung „mit eisenbahn“ = Badges „Mit Eisbahn“ **und** „Mit Kindereisenbahn“ (2.2).
- **Bestätigen (Vorschlag):** Event-Seiten der großen Märkte bleiben bestehen und bekommen den Markt-Kasten, keine Weiterleitung (3.3).
- **Auftraggeber liefert:** Neuss/Ratingen-Angaben (W2); `top5_rang` und ggf. `score_manuell` nach dem Score-Bericht; Hero-Bild.
- **Folgepunkt außerhalb dieses Plans:** Die bestehenden Guides speichern Google-Bewertungen in `orte` (`google_rating`,
  `google_bewertungen_anzahl`, Spielplatz `extras.spielplatz.google`) – nach den Places-Bedingungen nicht erlaubt; eigener Prüfauftrag.
- **Folgepunkt außerhalb dieses Plans:** `/ort-foto` merkt sich Google-Bildadressen bei den übrigen Hubs bis 45 Tage
  (`app/ort-foto/[slug]/route.ts:104`); mit dem Prüfauftrag zu den gespeicherten Bewertungen klären.
- Vor dem Livegang zur Freigabe: Texte 6.1–6.4, Top-5-Begründungen.

## 14. Prüfhistorie
- Entwurf 17.11.2026 (Claude): Eventdaten (Supabase, lesend) und Code geprüft, externe Quellen recherchiert (Visit Düsseldorf/Toubiz,
  Veranstalter, duesseldorf.de, neuss-marketing.de, OSM, Google-Preise und -Bedingungen); Produktentscheidungen W1–W7 vom Auftraggeber
  am 17.11. beantwortet und eingearbeitet; weihnachten-in-duesseldorf.de als Hinweisgeber für vier weitere Innenstadt-Kandidaten.
- Cursor-Prüfung 1 (17.11., eingearbeitet, alle Code-Angaben nachgeprüft): (1 kritisch) Feiertag ohne Sonderzeile → `unbekannt`,
  Totensonntag berechnet; (2) Stadtteil-Unterpfad im Proxy immer `fehlt`, Weihnachtsmarkt-Zweig vor `HUB_TYPEN`; (3) feldweise
  Erbung; (4) Saison über `von`/`bis` statt Kalenderjahr, `aktuelleSaison` = spätestes `bis` mit Daten; (5) `EXTRAS_FELDER`, `OrtTyp`,
  eigener Lader ohne Score-Schwelle; (6) Score-Skala ×10, Randfälle, `teilweise`; (7) Zustand nur im Browser, Platzhalter auf dem Server,
  Karten-API nur Zeiten, `?tag=` in der Suspense-Grenze, Startseite mit `heuteBerlin()`; (8) E12 um abgeleiteten Score, Fotonamen und
  Bild-Cache ≤ 30 Tage ergänzt; (9) Stufe 1 geteilt in 1a (21.11.) und 1b (27.11.); (10) Hero-Zahl und -Zeitraum, Rollen statt
  `art`-Werten, Gruppenzeile zählt in der Top 5; (11) Indexierbarkeit bleibt über den Saisonwechsel, `EXTRA_LINKS` ergänzen,
  `food/maerkte` eigener Link, Freischalten nur mit Wochenzeiten; (12) CHECK mit vollständiger Typliste neu anlegen. Tests,
  Abnahme und IndexNow (manueller Lauf) nachgezogen.
- Cursor-Prüfung 2 (17.11., eingearbeitet): Befunde aus Runde 1 bestätigt. (1) Python-Test zur Erbung auf feldweise umgestellt;
  (2) Tests und Abnahme in Stufe 1a (7.1, 12.1) und 1b (7.2, 12.2) geteilt, 1b-Bausteine in 5.2/5.3/5.6 markiert, Einleitung auf
  21.11./27.11.; (3) E4: `vor_saison`/`nach_saison` statt „zu“ außerhalb des Zeitraums; (4) Startseiten-Box-Satz „kein Markt als
  geöffnet belegt“, FAQ 5 in 1a ohne Parameter; (5) Saisonende-Hinweis erst nach dem spätesten `bis` (Kö on Ice 10.01.), Zeile für die
  laufenden Attraktionen, Zustandstabelle 5.5 geteilt; (6) Sonderzeiten-Tabelle und FAQ 3 um Silvester/Neujahr; (7) `n_max = 0` →
  Reichweite 0; (8) Vorab-Prüfung `SELECT DISTINCT typ` mit Abbruch neu beschrieben (die Imbiss-Datei hat sie nicht); (9) Abnahme
  prüft JSON-Schlüssel statt `ILIKE '%rating%'` (Ratingen).
- Cursor-Prüfung 3 (17.11.): keine kritischen/mittleren Befunde, „freigabereif“. Zwei geringe eingearbeitet: Top 5 nur bis 30.12.
  (5.5, 7.2, passend zu 5.8); `pruefung.csv` rechnet 22.11., 24.12., 26.12., 31.12., 01.01. **Plan vom Auftraggeber am 17.11.2026
  freigegeben**, Umsetzung beginnt. Die Auslegung „Mit Eisbahn“ + „Mit Kindereisenbahn“ gilt mit der Freigabe als bestätigt.
- Umsetzung 17.11. (lokal, nichts committet): Schritt 1 SQL geschrieben (`database/orte_typ_weihnachtsmarkt_2026-11-17.sql`, nicht ausgeführt);
  Schritt 2 erledigt – `toubiz_lesen.py` las 12 Visit-Düsseldorf-Seiten, geprüfte Pflegedateien `data/weihnachtsmaerkte/`
  (12 Düsseldorfer Einträge, Belege von Visit-Düsseldorf-FAQ, schloss-benrath.de, areal-boehler.de, deg-winterwelt.de; Neuss/Ratingen fehlen
  noch, W2); Schritt 3 vorbereitet – `import_maerkte.py` (Dry-Run: 12 neu, Stichtage plausibel), `database/weihnachtsmaerkte_freischalten.sql`;
  Schreibweg-Freigabe steht aus. Schritt 4 Website-Kern 1a gebaut (Hub, Detail, Pfadprüfung, Karten-API, Foto-Proxy ≤ 30 Tage, Sitemap,
  Schalter, Menü/Footer/Kachel/Startseiten-Box/Food-Link, Symbolbild bis 30.12., llms.txt, Datenschutz). Tests: Python 301, vitest 391 grün;
  Build kompiliert, bricht aber am Ende wegen einer npm-Sicherheitsmeldung zur installierten Next.js-Version ab (nicht durch diese Änderung).
  Hinweis aus den Daten: Areal Böhler hat im Toubiz-Terminplan eine Lücke am Sa 12.12. (Veranstalterseite nennt samstags 13–22 Uhr) – vor dem 12.12. prüfen.
