# Plan: Quellen-Ausbau – Venues direkt, Rausgegangen zuletzt, Ticketing mit Vorlauf – dritte Fassung, **freigegeben 24.11.2026**

Status: **Freigegeben vom Auftraggeber am 24.11.2026 (dritte Fassung).** Die Vorschläge Q1–Q22 gelten damit als entschieden. Gebaut wird erst nach Freigabe, schrittweise und jeweils mit OK des Auftraggebers.
Jeder Push ist ein Live-Deploy; SQL führt der Auftraggeber im Supabase-SQL-Editor aus.

Drei Ziele des Auftraggebers:
1. **Möglichst alle einzelnen Venues** in Düsseldorf (plus Neuss/Ratingen) direkt abfragen.
2. **Rausgegangen nur noch als letzte Quelle:** von dort nur, was wir nirgends sonst finden; ein direkter Link hat immer Vorrang.
3. **Ticketmaster, Eventim, Songkick** anbinden und große Events mit bis zu 12 Monaten Vorlauf zeigen; Zeitraum je Quelle statt der globalen 60 Tage.

---

## 1. Ausgangslage (geprüft am 23.11.2026)

### 1.1 Zahlen

Sichtbare künftige Events (anon-Schlüssel der Website, `abgelehnt = false` per RLS): **1.647**, davon 1.307 in den Tagen 0–29 und 340 in den Tagen 30–59. Nach Tag 60 nichts, weil jeder Scraper bei `heute + SCRAPER_VORSCHAU_TAGE` (60) abschneidet.

Künftige Events je Quelle (Auszug, Tage 0–29 / 30–59):

| Quelle | 0–29 | 30–59 |
|---|---:|---:|
| VisitDüsseldorf (Kalender + Führungen) | 122 | 123 |
| Stadtbüchereien | 165 | 6 |
| Düsseldorfer Schauspielhaus | 118 | 46 |
| **Rausgegangen** | **161** | **0** |
| zakk | 85 | 19 |
| Kunstpalast | 91 | 7 |
| PRINZ.de | 88 | 2 |
| Meetup.com | 83 | 0 |
| AllEvents.in | 65 | 7 |
| d-live | 38 | 21 |
| Kom(m)ödchen | 33 | 24 |
| Deutsche Oper am Rhein | 25 | 19 |
| Pitcher | 19 | 14 |
| Tonhalle | 15 | 11 |
| Capitol Theater | 9 | 10 |

Rausgegangen in den letzten 120 Tagen: **2.094 von 5.034 Events (42 %)** stammten (noch) von Rausgegangen, verteilt auf **381 Orte**. Ein Teil davon ist inzwischen auf andere Quellen umgehängt (die Vorrang-Regel greift schon, siehe 1.3).

### 1.2 Scraper-Lauf vom 21.11.2026 (GitHub Actions, 3 h 7 min)

| Schritt | Dauer |
|---|---:|
| 1 Scraper (alle 47 Quellen) | **10 min** |
| 1e2 Adressen ergänzen | 2 min |
| 2 Speichern (1.829 Events, je Event bis zu 3 Abfragen) | 8 min |
| 3 Kategorisierung (Limit 300) | 8,5 min |
| 3a Unterkategorien | 1,5 min |
| **3b Beschreibungen aus Veranstalter-Quellen** | **2 h 28 min** |
| 4 Captions | 6 min |

Folgerung: **Die Scraper selbst sind nicht der Engpass**, sondern die Beschreibungen (Schritt 3b). Mehr Quellen und mehr Vorlauf kosten vor allem dort Zeit (Abschnitt 5.3).

Auffälligkeiten im selben Lauf (nicht Teil dieses Plans, aber relevant):
- **Ticketmaster: 0 Events** – `TICKETMASTER_API_KEY ist nicht gesetzt`. **Songkick: 0 Events** – `SONGKICK_API_KEY nicht gesetzt`. Beide Scraper existieren (`scraper/tier1/ticketmaster.py`, `songkick.py`), im Workflow `scrape.yml` fehlen die Secrets ganz.
- **Kulturportal Düsseldorf: 0 Events** (Playwright-Timeout bei `networkidle`) – wird schon von der Rausgegangen-Session beobachtet (Lauf 24.11.).
- **VisitDüsseldorf-Kalender: nur 10 Events** aus 21 Teasern der ersten Seite. Die Sitemap hat rund 880 `/event/`-Seiten mit vollständigem JSON (Toubiz, alle Termine); der Führungs-Scraper nutzt das schon, aber nur für Führungen.
- Kunstsammlung NRW: nur 4 Events (der Scraper liest nur Ausstellungen), während Rausgegangen für K20/K21 in 120 Tagen 94 Events (Führungen, Veranstaltungen) lieferte.

### 1.3 Was beim Vorrang schon funktioniert

- `pipeline/deduplication.py` `_events_mergen()`: Trifft ein Rausgegangen-Eintrag auf dasselbe Event aus einer anderen Quelle, wird die andere Quelle zur Basis.
- `database/client.py` `_anreicherungs_update_bauen()`: Ein **gespeichertes** Rausgegangen-Event wechselt zur anderen Quelle (`quelle_name`, `quelle_url`, Bild, Beschreibung, Preis, Adresse), der Slug bleibt; im Lauf vom 21.11. 17-mal geschehen. Geschützt bleiben `beschreibung_quelle` und `redaktion_felder` (Admin-Plan 4.4).
- `main.py`: Rausgegangen läuft als letzte Quelle.
- `pipeline/rausgegangen_nachziehen.py`: einmaliges Umhängen des Bestands (gibt es schon).

**Lücken:**
- Die Regel kennt nur „Rausgegangen gegen den Rest“. Zwischen allen anderen Quellen gilt „wer zuerst kommt“: Ticketmaster läuft als erste Quelle, VisitDüsseldorf vor den Häusern. Liefern Ticketmaster und d.live dasselbe Konzert, wird Ticketmaster die Basis; ist ein PRINZ-Event gespeichert und das Haus liefert es später, bleibt PRINZ die Quelle.
- `ist_aggregator()` ist nur ein Ja/Nein (für die Uhrzeit), keine Rangfolge.
- Es wird nur **eine** Quelle je Event gespeichert. Welche Events nur Rausgegangen kennt, lässt sich nicht messen, und ein zusätzlicher Ticket-Link geht verloren.
- Die Dubletten-Vorschläge (`pipeline/dubletten_sql.py` `paare_finden`, `pipeline/vorschlaege.py`) behalten „Nicht-Aggregator vor Aggregator, dann den älteren Eintrag“.

### 1.4 Wo die 60 Tage stehen

Python: `config.py` `SCRAPER_VORSCHAU_TAGE = 60`, genutzt in **47 Scraper-Dateien** (davon 5 deaktiviert) und `scraper/utils/` (`enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)`). Ohne Fenster: R25, Salon des Amateurs, Parkrun, Kleine Weihnachtsmärkte.

Website:
- `web/lib/daten.ts:34` `TAGE_VORAUS = 60` → `eventPoolLaden()` lädt alles bis heute + 60. Davon leben Startseite, `/entdecken`, Kategorie-, Stadtteil-, Wochenend-, Kostenlos-, Tagesseiten, Guides, Konto-Bereich, Sitemap, `/api/events`.
- `web/lib/datum.ts:129` `MAX_ZEITRAUM_TAGE = 60` (eigener Zeitraum auf /entdecken), `:167` Schlüssel „alle“ = 60 Tage, `:178` „kostenlos in 60 Tagen“, `:39` Tagesleiste (60, bei fernem Tag bis 366).
- `web/lib/admin/empfehlungen.ts:51` `TAGE_VORAUS = 59`.
- `web/app/event/[kategorie]/[slug]/page.tsx:83` „mehr am Ort“ in 59 Tagen.
- **Schon ohne Grenze:** Die Eventseite lädt ein Event außerhalb des Pools einzeln nach (`eventLaden()`, `daten.ts:266`), die **Ortsseiten** laden ihr Programm über `events.ort_id` ohne Pool (`web/lib/spielstaetten-daten.ts:3`).

---

## 2. Entscheidungen (Vorschläge von Claude, zur Bestätigung)

| Nr. | Frage | Vorschlag | Abschnitt |
|---|---|---|---|
| Q1 | Rangfolge der Quellen | Haus 1 · Ticketverkauf 2 · offizielle Portale 3 · Aggregatoren 4 · Rausgegangen 5; besserer Rang wird Hauptquelle, auch nachträglich | 4.1, 4.2 |
| Q2 | Alle Quellen eines Events speichern (`events.quellen`) | ja | 4.3 |
| Q3 | Events, die nur Rausgegangen kennt | behalten; Knopf weiter auf Rausgegangen, zusätzlich „Website von <Ort>“ (a) | 4.4 |
| Q4 | Rausgegangen-Event an einem Ort mit eigenem Scraper, ohne Treffer | behalten und als Lücke melden (a) | 4.5 |
| Q5 | Wann Rausgegangen abschalten? | nicht in diesem Plan; Kennzahl „nur Rausgegangen < 5 % über drei Läufe“ als Signal | 4.6 |
| Q6 | Ticketing | Ticketmaster, Eventim, Reservix, ADticket, Stagedates ja; Songkick nein (**Auftraggeber 24.11.: alle Partner-Anbieter anbinden**) | 5.1, 5.5 |
| Q7 | Zeitraum je Quelle | große Häuser + Ticketing 365, kleine Häuser 120, VisitDüsseldorf 120, Aggregatoren/Rausgegangen 60 | 5.2 |
| Q8 | 60-Tage-Pool der Website | bleibt; zweiter Fernpool für Tag 61–365 | 6.1 |
| Q9 | Neue Liste für spätere Events | eigene Seite **„Ausblick“ unter `/ausblick`** (zweite Runde, 24.11.; erste Vorschläge abgelehnt) | 6.4 |
| Q10 | Startseiten-Box mit großen Events der nächsten Monate | ja, 6 Einträge, verlinkt auf den Ausblick | 6.1 |
| Q11 | Label für Events > 60 Tage | Monat und Jahr groß („MÄRZ 2027“) statt „Vorverkauf“ | 6.2, 6.4 |
| Q12 | Partner-Links | **ja** (Auftraggeber 24.11.); Schalter `PARTNERLINKS_AKTIV`, live erst nach Anmeldung beim Programm und Anwalts-Freigabe von Kennzeichnung und Datenschutz | 5.5 |
| Q13 | Kategorisierungs-Limit beim Start | zwei Wochen 1.500 statt 300 (≈ 2–3 € einmalig) | 5.3 |
| Q14 | Beschreibungen für ferne Events | nur bis Tag 60, plus 100 Fern-Events (Rang 1–2) je Lauf | 5.3 |
| Q15 | Welle A der Venues | siehe 3.2 | 3.2 |
| Q16 | Workshops/Kurse mit festen Terminen (Keramik-, Kreativstudios) | ja, als `community`, aber erst Welle B | 3.2 |
| Q17 | Normales Kinoprogramm (Filmkunstkinos, UFA) | nein, nur Sonderveranstaltungen | 3.2 |
| Q18 | Monatsseiten des Ausblicks (`/ausblick/2027-03`) | später, wenn genug Fern-Events da sind | 6.4 |
| Q19 | Welche Partner? | **alle genannten:** Ticketmaster, Eventim, Reservix, ADticket, Tiqets, GetYourGuide (Auftraggeber 24.11.) | 5.5 |
| Q20 | Welcher Ticket-Button bei mehreren Anbietern? | einer je Event, nach Offiziellkeit (Link des Hauses vor Rang-2-Quelle), nie nach Provision | 5.5.3 |
| Q21 | Tiqets/GetYourGuide | als Angebote auf Ortsseiten und im Stadtführungs-Guide, nicht als Events | 5.5.4 |
| Q22 | Partner-Links im Magazin | nein, nur Event- und Ortsseiten und Ausblick | 5.5.3 |

---

## 3. Ziel 1: Venues direkt abfragen

### 3.1 Was wir heute direkt abfragen

**Tier 2 (23 Häuser, aktiv):** Tonhalle, zakk, Deutsche Oper am Rhein, Düsseldorfer Schauspielhaus, d.live (Merkur Spiel-Arena, PSD Bank Dome …), Kunstpalast (inkl. Robert-Schumann-Saal), Kunstsammlung NRW (nur Ausstellungen), NRW-Forum, FFT, Stahlwerk, Rudas Studios, Mitsubishi Electric HALLE, Kulturschlachthof R25 (über RA), Salon des Amateurs (über RA), Pitcher (WP-REST), Kunsthalle, Filmmuseum/Black Box, Stadtbüchereien (inkl. KAP1), Tanzhaus NRW, Jazz-Schmiede, Capitol Theater, Kom(m)ödchen (über unseren Server), STARTPLATZ.

**Tier 3 (14 aktiv):** Parkrun, Sport im Park, Fortuna, DEG, Messe, EKŌ-Haus, Classic Remise, Stadtstrand/KLONKK, IHK, StartupDorf, Street Food Thursday, Kasematten, Auf ins Viertel, Kleine Weihnachtsmärkte.

**Deaktiviert:** Bandsintown, meinestadt, Eventbrite, Eventfinder, Spontacts (jeweils Bot-Schutz oder Login).

### 3.2 Kandidaten und Machbarkeit

Grundlage: (a) Orte mit den meisten Rausgegangen-Events der letzten 120 Tage (je Ort gezählt, auch über `ort_id`), (b) Spielstätten/Clubs aus `orte` (241 Spielstätten, 31 Clubs), (c) bekannte Häuser in Neuss/Ratingen. Für 65 Websites wurde am 23.11. automatisch geprüft (je Seite höchstens 4 Abrufe, 2 s Pause, robots.txt beachtet): robots.txt, WordPress / „The Events Calendar“-REST-API, JSON-LD `Event`, iCal-Links, eingebundene Ticket-Plattformen, Zahl der Datumsangaben auf der Programmseite.

**Was die Prüfung zeigt:** Kein geprüftes Haus hat auf der Programm-Übersicht JSON-LD-Events; nur eines bietet die „The Events Calendar“-API (Insel Hombroich) und nur eines einen echten iCal-Link (The Vinyl Room). Die iCal-Erkennung der Prüfung war zu grob (Treffer auf Wörter wie „Musical“) und ist nicht gewertet. JSON-LD kann trotzdem auf den Detailseiten stehen (nicht geprüft, um die Abrufe klein zu halten). Fast alle Häuser brauchen also einen **kleinen HTML-Parser**. Der Aufwand ist trotzdem meist gering, weil die Termine als Liste mit Datum im HTML stehen (Spalte „Daten“ = Zahl der Datumsangaben auf Start-/Programmseite). Zahlreiche Kleinst-Orte (Bars, Cafés, Workshop-Studios) haben **gar kein Programm auf der Website** – dort bleibt Rausgegangen die einzige Quelle; genau das ist Ziel 2.

Spalten: **RG** = Rausgegangen-Events dieses Ortes in 120 Tagen · **andere** = Events aus anderen Quellen am selben Ort (gleiche `ort_id`) · **Aufwand** S = eine Listen-Seite, M = Monats-/Detailseiten oder Sonderfall, L = JavaScript/Playwright · **Fenster** nach Q7.

#### Welle A (V0/V1) – große Wirkung, machbar

| Haus | RG | andere | Website-Befund | robots.txt | Aufwand | Fenster |
|---|---:|---:|---|---|---|---|
| **Kunstsammlung NRW (K20/K21)** – vorhandenen Scraper erweitern | 94 | 4 | Scraper liest nur Ausstellungen; Führungen/Veranstaltungen fehlen | erlaubt | M | 365 |
| **VisitDüsseldorf komplett** – Führungs-Scraper verallgemeinern | – | 245 | Sitemap ≈ 880 `/event/`-Seiten mit Toubiz-JSON (alle Termine) | erlaubt (`/event/`, Sitemap) | M | 120 |
| Theatermuseum (duesseldorf.de) | 46 | 0 | gleiche CMS-Familie wie Filmmuseum/Stadtbüchereien | erlaubt (nur `?tx_*`, `?cHash*` gesperrt) | S | 120 |
| Gerhart-Hauptmann-Haus | 43 | 0 | Monatsseiten `/veranstaltung/2026/november` | erlaubt | M | 120 |
| Goethe-Museum | 28 | 0 | Drupal, Veranstaltungsliste (34 Daten) | erlaubt, **Crawl-delay 10** | S | 120 |
| Comedy Club Düsseldorf | 27 | 21 | `/shows`, 195 Daten; Tickets fienta/Eventim | keine robots.txt (404 = erlaubt) | S | 120 |
| Schloss Benrath | 25 | 0 | `/veranstaltungs-liste`, Details je Event | erlaubt | M | 365 |
| Maxhaus | 24 | 1 | WordPress, `/veranstaltung/` (57 Daten) | erlaubt | S | 120 |
| Theater an der Luegallee | 18 | 10 | Zertifikat passt nicht zu `www.` → ohne `www` prüfen | – | M | 365 |
| KaBARett FLiN | 16 | 0 | Wix, Spielplan im HTML (52 Daten) | erlaubt, Crawl-delay 10 | M | 365 |
| KIT – Kunst im Tunnel | 16 | 0 | WordPress, `/programm/kalender/` | erlaubt | S | 120 |
| Roncalli's Apollo Varieté | 14 | 14 | WordPress, Shows mit Laufzeit | erlaubt | S | 365 |
| Bilker Bunker + Schleuse Zwei | 28 | 8 | Drupal, Programm auf der Startseite (39 Daten) | erlaubt | S | 120 |
| Theater an der Kö | – | 7 | `/spielplan`, 177 Daten | erlaubt | S | 365 |
| Savoy Theater | 9 | 15 | WordPress, wenige Daten im HTML (Tickets extern) | erlaubt | M | 365 |
| Tor 3 | 3 | 3 | 184 Daten; Tickets Stagedates/Eventim/ticket.io | erlaubt | S | 120 |
| Nachtresidenz | 2 | 7 | WordPress, `/events/` | erlaubt | S | 120 |
| Ampere | 3 | 0 | WordPress, `/programm/` (48 Daten) | erlaubt | S | 120 |
| Stagedates (Plattform) | – | – | siehe 5.1 | erlaubt | S | 365 |

#### Welle B (V2) – kleiner oder aufwendiger

| Haus | RG | andere | Befund | Aufwand |
|---|---:|---:|---|---|
| Robert Schumann Hochschule (viele freie Konzerte) | 4 | 0 | `/veranstaltungen`, Details je Termin | M |
| Haus der Universität | 10 | 0 | `/programm` | S |
| Sammlung Philara | 9 | 0 | `/de/programm` (150 Daten), Tickets Reservix | S |
| Aquazoo Löbbecke | 4 | 23 | `/veranstaltungen` | S |
| Hetjens-Museum | 7 | 0 | Werkstatt-/Programmseiten | S |
| Event-Theater Schwanenhöfe | 2 | 10 | WordPress | S |
| Filmwerkstatt | 5 | 3 | WordPress (Tickets xceed) | S |
| Ratinger Hof | 11 | 11 | Seite rendert per JavaScript, keine Daten im HTML | L |
| Düsseldorfer Marionetten-Theater | 8 | 0 | Zertifikatskette unvollständig (httpx lehnt ab) | M |
| Komödie Düsseldorf | – | – | Weiterleitungsschleife unter der geprüften Adresse – richtige URL klären | M |
| Kloster Flingern, Boston Club, Klub Kulb (Wix) | 2–3 | 1–6 | Termine im HTML | S |
| The Vinyl Room | 4 | 0 | echter iCal-Feed (`plattenparty.ics`) | S |
| The Craft Studio, Eigenlob Keramik (Workshops, Buchung über etermin) | 18 / 17 | 0 | Termine im HTML (103 / 52 Daten) | S – **Q16:** Workshops/Kurse aufnehmen? |
| Filmkunstkinos (Metropol, Bambi, Cinema) | 7 | 4 | reines Kinoprogramm (814 Daten) | S – **Q17:** normales Kinoprogramm aufnehmen? Vorschlag nein, nur Sonderveranstaltungen |

#### Bleibt bei Rausgegangen (keine brauchbare eigene Quelle)

| Ort | RG | Grund |
|---|---:|---|
| Theater der Klänge | 12 | robots.txt sperrt alles (`Disallow: /`) |
| Areal Böhler | 15 | Eventkalender ist ein eingebettetes **Rausgegangen-Widget** |
| Bar Lola, Isla de Cuba, The Old Irish Pub, Ghorban, BrauArt, Klanghaus | 1–31 | kein Programm auf der Website (Instagram) |
| zentrum plus Holthausen (ASB) | 37 | kein Programm auf der Website |
| Ashtanga Yoga, Spontan Theater (Kurse), Volkshochschule | 3–30 | regelmäßige Kurse, keine Einzel-Events |
| Heine Haus | 4 | Programm nur als PDF |
| BBK Kunstforum | 7 | Server bricht die Verbindung ab |
| HofArt Studio, TanzStudio HopSpot, glazed., Wilma Wunder … | 14–28 | keine Website in `orte` bzw. nur Social Media |
| Plätze und Straßen (Altstadt, Carlstor, Schadowplatz, Krimi-Trails …) | 9–59 | keine Venue; Veranstalter verschieden |

#### Neuss und Ratingen

| Haus | Befund | robots.txt | Aufwand | Welle |
|---|---|---|---|---|
| **Insel Hombroich / Raketenstation** | WordPress mit **„The Events Calendar“-API**: `/wp-json/tribe/events/v1/events` meldet 418 Einträge | erlaubt | S (Baustein 2) | A |
| **Stadt Ratingen – Veranstaltungskalender** (`stadt-ratingen.de/veranstaltungskalender`, 97 Daten) | städtischer Kalender für ganz Ratingen (Stadttheater, Museum, Märkte) – deckt mehrere Häuser auf einmal ab | erlaubt | M | A |
| Theater am Schlachthof (TaS) Neuss | WordPress, `/spielplan/` (103 Daten) | erlaubt | S | A |
| Oberschlesisches Landesmuseum Ratingen | WordPress mit Kalender-Plugin, 210 Daten | erlaubt | S | B |
| Globe Neuss / Shakespeare-Festival (Kulturamt Neuss) | Programmseite, nur Festivalzeit (Juni/Juli) | erlaubt | S | B |
| Rheinisches Landestheater Neuss | Startseite 12 Daten, Spielplan-Link der Startseite führt auf 404 – richtige Spielplan-URL klären | erlaubt | M | B |
| Gare du Neuss, Stadthalle/Zeughaus Neuss, LVR-Industriemuseum Cromford | keine Termine im HTML bzw. geprüfte Adresse 404 – erst richtige Kalender-URL suchen | – | M | B |

Weitere Häuser in Düsseldorf aus der Prüfung: **Weltkunstzimmer** (WordPress, `/programm/` mit 217 Daten → Welle A, S), **D'haus/Junges Schauspiel** (deckt der Schauspielhaus-Scraper), **Ev. Kirche Düsseldorf** (`evdus.de/kalender`, Kirchenkonzerte; Termine per JavaScript → Welle B, L).

Nebenbefund **Kulturportal Düsseldorf:** Die Seite antwortet per httpx sofort (200, Termine im HTML), der Playwright-Scraper scheitert am Warten auf `networkidle`. Umstellung auf httpx wäre ein kleiner Fix – liegt aber bei der Rausgegangen-Session, die den Lauf vom 24.11. auswertet; hier nur der Hinweis.

**Erwartung:** Welle A deckt nach den Rausgegangen-Zahlen ≈ 400 der 2.094 Rausgegangen-Events aus 120 Tagen ab (≈ 100 je Monat), dazu längeren Vorlauf bei Apollo, Theater an der Kö, Schloss Benrath, Luegallee, FLiN, Savoy. Der größte Einzelhebel ist **VisitDüsseldorf komplett** (Toubiz enthält auch Termine vieler kleiner Häuser, Märkte und Stadtfeste mit Monaten Vorlauf).

### 3.3 Bausteine statt Einzel-Scraper

Damit 20–40 neue Häuser nicht 20–40 eigene Dateien mit eigenem Parser werden, kommen drei gemeinsame Bausteine nach dem Muster von `scraper/utils/bookingkit.py` und `scraper/utils/ra_venue.py`:

1. **`scraper/utils/jsonld_events.py`** – liest schema.org-`Event` aus `application/ld+json` einer oder mehrerer Seiten (inkl. `@graph`, `subEvent`, `eventSchedule` als Einzeltermine), Felder: Titel, Start, Ort/Adresse, Bild, Preis (`offers`), URL. Abbruch bei 0 Treffern mit Warnung (Struktur geändert).
2. **`scraper/utils/wp_tribe.py`** – WordPress „The Events Calendar“: `/wp-json/tribe/events/v1/events?start_date=…&end_date=…&per_page=50`, seitenweise. Pitcher nutzt schon die WP-REST-API (eigener Code, wird nicht umgebaut).
3. **`scraper/utils/ical.py`** – iCal-Feeds (`.ics`) mit einem kleinen eigenen Parser für `VEVENT` (DTSTART, SUMMARY, LOCATION, URL, DESCRIPTION; RRULE nur `FREQ=WEEKLY/MONTHLY` mit `UNTIL`/`COUNT`). **Keine neue Bibliothek** – falls RRULE-Vielfalt das nötig macht, wird vorher gefragt.

Dazu **`scraper/tier2/venues.py`**: eine Tabelle `VENUES = [{name, quelle_name, methode, url, ort, adresse, kategorie_standard, vorschau, ...}]` und eine `scrape()`-Funktion, die je Eintrag den passenden Baustein ruft. Jeder Eintrag erscheint im Lauf-Report als eigene Quelle (Anzeigename), damit Warnregeln W1–W5 je Haus greifen. Häuser mit eigenem HTML brauchen weiter eine eigene Datei in `scraper/tier2/`.

Regeln je neuer Quelle (wie bisher): robots.txt prüfen (im Code als Kommentar mit Datum festhalten), 2 s Pause, Backoff, realistischer User-Agent, `ort` exakt in der Schreibweise der Ortstabelle (damit `ort_zuordnung` trifft), Test mit gespeicherter Beispielseite in `tests/fixtures/`.

---

## 4. Ziel 2: Rausgegangen nur als letzte Quelle

### 4.1 Rangfolge der Quellen (Q1)

Neue Datei `pipeline/quellen_rang.py` mit **einer** Funktion `quellen_rang(event) -> int` (kleiner = besser). Grundlage ist eine feste Tabelle nach `quelle_name` (so wie heute in `main.py` `QUELLEN` benannt), Rausgegangen zusätzlich über die URL erkannt (wie `ist_rausgegangen()`):

| Rang | Gruppe | Quellen |
|---:|---|---|
| 1 | **Veranstalter / Haus** | alle Tier-2- und Tier-3-Scraper und die neuen Venue-Scraper (Abschnitt 3); Meetup-Gruppenseiten der Veranstalter (StartupDorf) |
| 2 | **Offizieller Ticketverkauf** | Eventim, Ticketmaster, (später) Reservix |
| 3 | **Offizielle Portale** | VisitDüsseldorf (+ Führungen), Kulturportal Düsseldorf, Meetup.com, Resident Advisor |
| 4 | **Aggregatoren** | PRINZ.de, AllEvents.in, Songkick, Eventfinder, meinestadt |
| 5 | **Rausgegangen** | nur, wenn sonst nichts |

Unbekannte `quelle_name` (neuer Scraper ohne Eintrag) → Rang 1, wenn der Scraper in `QUELLEN` Tier 2/3 hat, sonst 4; ein Test sorgt dafür, dass jeder Name aus `QUELLEN` in der Tabelle steht.

`ist_aggregator()` bleibt für die Uhrzeit-Regel bestehen, wird aber aus dem Rang abgeleitet (Rang ≥ 2 = „gibt Termine nur weiter“), damit es nur noch eine Liste gibt. Die Uhrzeit-Regel ist dann: bei Abweichung gilt die Zeit der Quelle mit dem **besseren Rang**, wenn dieser 1 ist (wie heute).

### 4.2 Wo der Rang greift

1. **In-Memory-Deduplizierung** (`_events_mergen`): Statt „Rausgegangen gegen den Rest“ wird die Quelle mit dem besseren Rang zur Basis. Gleicher Rang → wie heute die zuerst gekommene. Die Reihenfolge in `QUELLEN` wird damit egal (bleibt aber: Rausgegangen zuletzt).
2. **Speichern** (`_anreicherungs_update_bauen`): Der Quellenwechsel gilt für jeden **besseren Rang**, nicht nur ab Rausgegangen. Übernommen werden wie heute `quelle_name`, `quelle_url` und die Vorrang-Felder Bild, Preis, Adresse, Beschreibung – Beschreibung nicht, wenn `beschreibung_quelle` gesetzt ist; nichts, was in `redaktion_felder` steht (Admin-Plan 4.4, E7). Bild: ein Bild der besseren Quelle ersetzt das bisherige nur, wenn das bisherige von Rang ≥ 4 stammt (Ticketing-Bilder von Rang 2 sind oft gute Pressebilder und sollen von einem Haus-Scraper ohne Bild nicht gelöscht werden – leere Werte überschreiben nie).
3. **Dubletten-Vorschläge** (`dubletten_sql.paare_finden`, `vorschlaege.py`): Sortierung „Status-Zusatz, Rang, älterer Eintrag“ statt „Status-Zusatz, Aggregator, älterer Eintrag“. Behalten wird also der Eintrag mit dem besseren Rang.
4. **Einmaliges Nachziehen** (`rausgegangen_nachziehen.py`): wird auf den Rang umgestellt und heißt dann `pipeline/quellen_nachziehen.py` (altes Modul bleibt als dünner Aufruf, damit Doku-Verweise stimmen). Lauf nach jedem größeren Schritt in Abschnitt 7, erst als Probelauf (Bericht), dann `--schreiben` mit OK.

Abstimmung mit dem Admin-Plan: `database/client.py` und `pipeline/vorschlaege.py` sind dort gerade in Arbeit (Stufen 1d/2). Schritt R1 (Abschnitt 7) wird erst begonnen, wenn die laufende Admin-Stufe gepusht ist, und baut auf dem dann aktuellen Stand auf.

### 4.3 Alle Quellen eines Events merken (Q2)

Neue Spalte `events.quellen jsonb` (Liste `[{"name", "url", "rang", "zuletzt"}]`, höchstens eine Zeile je Quellenname). Gefüllt beim Speichern: neues Event mit seiner Quelle; bei einem Duplikat wird die Quelle des eingehenden Events ergänzt bzw. `zuletzt` aktualisiert. Die Hauptquelle bleibt in `quelle_name`/`quelle_url` (keine Änderung für Website, Admin, Sitemap).

Wofür:
- **Messbar machen**, wie viele Events nur Rausgegangen kennt (Kennzahl im Lauf-Report und im Admin-Cockpit: „nur Rausgegangen: n von m“), und an welchen Orten.
- **Ticket-Link:** Ist die Hauptquelle ein Haus (Rang 1) und kennt eine Rang-2-Quelle dasselbe Event, zeigt die Eventseite zusätzlich „Tickets bei Eventim/Ticketmaster“ (Abschnitt 6.3).
- **Abdeckungsprüfung:** Rausgegangen-Events an Orten, die wir direkt abfragen, ohne Treffer der Direktquelle → Hinweis auf eine Lücke im Venue-Scraper (Abschnitt 4.5).

SQL (`database/quellen_spalte_<datum>.sql`, führt der Auftraggeber **vor** dem Deploy von R2 aus): Spalte, kein Index nötig. Die Pipeline liest die Spalte wie `redaktion_felder` in `_ABGLEICH_SPALTEN` mit; die Website liest sie nur auf der Eventseite und lädt notfalls ohne sie (`SPALTEN_VARIANTEN` in `web/lib/daten.ts`). Bestehende Events bekommen beim ersten Lauf ihre aktuelle Quelle eingetragen (SQL-Vorbelegung aus `quelle_name`/`quelle_url`).

### 4.4 Was mit Events passiert, die nur Rausgegangen kennt (Q3)

Vorschlag: **behalten**, aber
- Der Hauptknopf „Zum Termin“ zeigt weiter auf die Rausgegangen-Seite (sie ist die einzige Seite mit Ticket-/Detailinfos zu genau diesem Termin). **Zusätzlich**, wenn der Ort in `orte` eine `webseite` hat: Link „Website von <Ort>“ über dem Quellenhinweis.
- Alternative Q3-b: Hauptknopf auf die Website des Ortes, Rausgegangen nur als kleiner Hinweis „gefunden bei Rausgegangen“. Nachteil: Die Ortswebsite nennt den Termin oft nicht; Nutzer finden nichts.

### 4.5 Rausgegangen-Events an Orten mit eigener Quelle (Q4)

Liefert Rausgegangen ein Event an einem Ort, dessen Haus wir direkt abfragen (Rang-1-Scraper mit derselben `ort_id`/`_haus_id`), und die Direktquelle hat an dem Tag nichts Passendes:
- **Vorschlag Q4-a:** Event trotzdem speichern (sonst fehlen Termine, die unser Scraper übersieht – z. B. Kunstsammlung: Führungen fehlen), aber im Lauf-Report als „Lücke im Venue-Scraper“ je Ort zählen. Mehr als 3 Lücken an einem Ort in einem Lauf → gelbe Warnung im Admin-Scraper-Tab (neue Regel neben W1–W5).
- Q4-b: verwerfen. Sauberer im Sinne „Rausgegangen nur zuletzt“, aber riskant, solange Venue-Scraper Lücken haben.

### 4.6 Rausgegangen-Scraper selbst

Bleibt unverändert: nur die Startseite, ein Abruf je Lauf (C4 aus dem Club-Plan). Keine weiteren Rausgegangen-Seiten. Mittelfristig soll der Anteil so weit sinken, dass ein Abschalten möglich ist (Kennzahl aus 4.3). Ziel-Kennzahl für die Freigabe zum Abschalten: Vorschlag Q5 – „nur Rausgegangen“ unter 5 % der künftigen Events über drei Läufe.

---

## 5. Ziel 3: Ticketing und Zeitraum je Quelle

### 5.1 Ticketing-Anbieter

Recherche vom 23.11.2026 (Dokumentation und Bedingungen der Anbieter gelesen, robots.txt geprüft; kein Konto angelegt):

| Anbieter | Stand bei uns | Zugang | Bedingungen / Haken | Vorschlag |
|---|---|---|---|---|
| **Ticketmaster** | Scraper fertig (`tier1/ticketmaster.py`), läuft leer: **kein Secret** im Workflow | Discovery API v2, Schlüssel sofort nach Registrierung; 5.000 Abfragen/Tag, mit 2/s planen; Blättern nur bis 1.000 Treffer → Abfrage in Monatsfenster teilen; `countryCode=DE`, `city`/`geoPoint`+`radius` | Kein Nachbau von Ticketmaster; Inhalte nur „angemessen lange“ zwischenspeichern; auf Verlangen binnen 24 h entfernen; Ticketmaster nicht als Bild-Host; Team-/Liga-Logos nicht frei. **Einnahmen „aus der Nutzung der API“ sind ausgeschlossen** (Ausnahme nicht auffindbar) → Q6-a | **Ja, zuerst** (T1): Auftraggeber registriert sich, Secret `TICKETMASTER_API_KEY`, Workflow-`env` ergänzen. Wie viele Düsseldorfer Events Ticketmaster DE liefert, zeigt erst der erste Lauf (Eventim dominiert in DE) |
| **Eventim** | nichts (Umsetzung: 5.5) | Keine öffentliche API. Partnerprogramm über Awin (Programm „eventim DE“) mit Deeplinks; ob es einen **Event-Datenfeed** gibt und ob man daraus Eventseiten bauen darf, ist nur im Awin-Konto bzw. auf Anfrage zu klären | eventim.de blockt automatisierte Abrufe technisch (Akamai; jede Anfrage lief in einen Timeout) – **kein Scraping** | **Ja** über Awin (5.5): Ticket-Links der Häuser als Partner-Links (P1/P2), Eventdaten nur, falls Awin einen Feed liefert (T2) |
| **Songkick** | Scraper fertig, kein Secret | API nur noch als **bezahlte Lizenz** mit Partnervertrag, keine Hobby-/Kleinprojekte | Metro-Seite hätte JSON-LD (50 Konzerte/Seite), aber die Nutzungsbedingungen verbieten Scraper ohne schriftliche Zustimmung und kommerzielle Nutzung | **Nein.** Scraper bleibt im Code, aber aus `QUELLEN` raus (wie Bandsintown), CLAUDE.md-Tabelle anpassen |
| **Stagedates** | nur indirekt (Rudas Studios) | `sitemap-events.xml` (≈ 830 URLs), Eventseiten mit JSON-LD `Event`/`Offer`; robots.txt erlaubt alles | Nutzungsbedingungen noch zu lesen | **Ja** (mit Welle A): Sitemap filtern auf Düsseldorf/Neuss/Ratingen, JSON-LD-Baustein (3.3) |
| Reservix / ADticket | nichts | Affiliate über Awin; Reservix nennt eine API für Partner; robots.txt antwortet 403 (Bot-Schutz) – kein Scraping | – | **Ja** über Awin + Reservix-API (5.5) |
| Tixforgigs | nichts | keine API; robots.txt erlaubt Eventseiten | strukturierte Daten ungeprüft | Später prüfen |
| Bandsintown, Dice, Eventbrite-Suche, Pretix | Bandsintown/Eventbrite deaktiviert | nur für Künstler / eigene Partner-Events / abgeschaltet / Token je Veranstalter | – | Nein (Eventbrite höchstens je bekanntem Veranstalter über `/v3/venues/{id}/events/`) |

Rang (4.1): Ticketmaster und später Eventim Rang 2, Stagedates Rang 2 (Verkaufsplattform des Veranstalters).

Ticketmaster-Abfrage: ein Durchlauf je Monat bis 12 Monate voraus, `countryCode=DE`, `geoPoint` Düsseldorf + `radius=25`, `unit=km`, danach `pipeline/gebiet.py`. 12 Monate × wenige Seiten ≈ 30 Abfragen je Lauf – weit unter dem Tageslimit.

### 5.2 Zeitraum je Quelle (Q7)

`config.py` bekommt statt der einen Zahl eine kleine Tabelle und eine Hilfsfunktion:

```python
SCRAPER_VORSCHAU_TAGE = 60          # Standard (Aggregatoren, kleine Häuser) – Name bleibt für Altcode
VORSCHAU_TAGE_LANG = 365            # große Häuser und Ticketing
VORSCHAU_TAGE_JE_QUELLE = {         # Schlüssel = Anzeigename aus main.py QUELLEN
    "Ticketmaster": 365, "Eventim": 365,
    "d-live": 365, "Mitsubishi Electric HALLE": 365, "Capitol Theater Düsseldorf": 365,
    "Tonhalle Düsseldorf": 365, "Deutsche Oper am Rhein": 365, "Düsseldorfer Schauspielhaus": 365,
    "Kom(m)ödchen Düsseldorf": 365, "Messe Düsseldorf": 365, "Fortuna Düsseldorf": 365,
    "DEG Eishockey Düsseldorf": 365,
    # neue Häuser aus Abschnitt 3 mit Kennzeichen „lang“
}
def vorschau_ende(quelle: str, heute: date) -> date: ...
```

- Jeder Scraper ersetzt `heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)` durch `vorschau_ende(QUELLE_NAME, heute)`. Mechanisch, aber 47 Dateien – deshalb in einem eigenen Schritt (Z1) mit Test „jeder Scraper nutzt `vorschau_ende`“ (Quelltext-Prüfung wie bei anderen Struktur-Tests).
- **Aggregatoren bleiben bei 60**, ebenso Rausgegangen (liefert ohnehin nur die Startseite), Meetup, RA, VisitDüsseldorf-Kalender (Q7-b: VisitDüsseldorf/Toubiz hätte Termine bis weit ins nächste Jahr – Vorschlag 120 Tage).
- **Kleine Häuser** (Clubs, Kneipen, Kleinkunst): 120 Tage als Mittelweg (Q7-c) – deren Programme reichen selten weiter, und so ist das Fenster für den Rang-Abgleich mit Ticketing (365) nicht zu kurz.
- **Seiten-Grenzen prüfen:** Ein längeres Fenster hilft nur, wenn der Scraper auch weiter blättert. Je Langzeit-Scraper wird geprüft und ggf. erweitert: Oper (`MONATE_VORAUS`, Monatsseiten), Schauspielhaus, Tonhalle (Saison-Spielplan), Capitol, d.live, Mitsubishi-Halle, Kom(m)ödchen (Spielplan über unseren Server), Fortuna/DEG (Saison-Spielpläne). Ergebnis je Scraper im Umsetzungsnotiz-Anhang.

### 5.3 Folgen für die Pipeline

- **Speichern:** heute 8 min für 1.829 Events (bis zu 3 Abfragen je Event). Mit +2.000–4.000 Fern-Terminen etwa +10–20 min. Vertretbar; Optimierung (Tagesbestand vorab laden) nur, wenn der Lauf über 4 h kommt.
- **Kategorisierung** (`categorizer.kategorisieren(limit=300)`, nach Datum sortiert): Ferne Events kommen erst dran, wenn die nahen fertig sind. Beim ersten Lauf mit 12 Monaten entsteht ein Rückstand von 2.000+ Events → **Q13:** Limit für zwei Wochen auf 1.500 anheben (Haiku, ≈ 0,1–0,2 Cent je Event, also ≈ 2–3 € einmalig), danach zurück auf 300. Der Fernpool (6.1) lädt deshalb nur Events mit Kategorie (`kategorie is not null`), damit unfertige Einträge nicht im Ausblick landen.
- **Unterkategorien** (limit 600): gleiche Logik, unkritisch.
- **Beschreibungen (Schritt 3b, heute 2,5 h):** Hier liegt das eigentliche Risiko (Job-Grenze 6 h, Workflow-Timeout 240 min). **Q14, Vorschlag:** Beschreibungen nur für Events bis Tag 60 wie bisher; Fern-Events bekommen ihre Beschreibung, sobald sie ins 60-Tage-Fenster rutschen. Ausnahme: höchstens 100 Fern-Events je Lauf mit Rang 1–2 (für den Ausblick und die Sitemap), nach Datum. Umsetzung: zusätzlicher Datumsfilter `datum <= heute + 60` in den Abfragen von `beschreibungen_nachziehen()` und `veranstalter_nachziehen()` (`pipeline/beschreibung_quellen.py:461`, `:604`, `:631`) plus der kleine Fern-Block.
- **IndexNow, Reihen, Club-Scores:** laufen über alle künftigen Events; mehr Events, aber ohne KI. Club-Scores nutzen nur die nahen Termine (Programm-Wert) – prüfen, dass ein Club mit vielen Fern-Terminen nicht künstlich steigt (`scraper/orte/clubs_profil.py`, Fenster festschreiben auf 60 Tage).
- **Instagram/Captions:** unverändert (nur nahe Events).
- **Gebietsfilter:** Ticketing liefert Region (Köln, Essen …) – `pipeline/gebiet.py` filtert schon nach Düsseldorf/Neuss/Ratingen; Ticketmaster-Abfrage zusätzlich per Ort/Radius eingrenzen.

### 5.4 Provision: Partnerprogramme mit Eventdaten (Recherche 24.11.2026, Rückfrage des Auftraggebers)

Recherche in Programmseiten, Awin-Profilen und Entwickler-Dokumentation; kein Konto angelegt. Die tatsächlichen Sätze für Deutschland stehen bei mehreren Anbietern erst nach der Anmeldung im jeweiligen Netzwerk fest.

| Anbieter | Eventdaten | Provision (soweit öffentlich) | Netzwerk | Haken | Einschätzung |
|---|---|---|---|---|---|
| **Ticketmaster** | Discovery API (frei); Discovery Feed (JSON/CSV) für freigegebene Partner | DE-Satz nicht öffentlich (Dritte: ≈ 0,8–1,6 %) | Impact, ein Programm für 25 Märkte **inkl. Deutschland**, Bewerbung mit Prüfung | Keine Provision im Presale und in den ersten 24 h nach Vorverkaufsstart. API-Bedingungen verbieten Einnahmen aus der API-Nutzung; die FAQ verweist auf genau dieses Affiliate-Programm, und die Impact-ID lässt sich im Entwicklerkonto eintragen → gewollt, aber **schriftlich bestätigen lassen** (affiliatepartners@ticketmaster.com) | einzige belegte Kombination API + Provision |
| **Eventim** | Partnerseite nennt „Zugriff auf Events der Datenbank“ + Deeplink-Generator; Feed/API **nicht belegt** | 20 % der Netto-Vorverkaufsgebühr ≈ 1,6–2 % vom Ticketpreis (Ø 1,55 € je Bestellung) | Awin (11388) | **Cookie nur 1 Tag**; kein Preisvergleich, keine Suchmaschinen-Anzeigen; einzelne Events ausgeschlossen | größte Abdeckung in DE; Daten nur auf Anfrage |
| **Reservix / ADticket** | Reservix nennt „Integration über API-Schnittstelle“ | Reservix ≈ 25 % der Vorverkaufsgebühr + 2,5 % vom Warenkorb (≈ 5 %); ADticket 2,5 %; Cookie 30 Tage | Awin (31293, 18490) oder direkt | verlangt „reichweitenstarke Website“ | **beste Rate**, stark bei Kleinkunst und NRW-Veranstaltern (Philara, viele Kleinkunstbühnen verkaufen dort) |
| ticket.io | kein Feed genannt | ≈ 10 % vom Netto-Ticketumsatz, Cookie 30 Tage | Awin | Angebot in Düsseldorf unbekannt (Tor 3, Nachtresidenz verlinken ticket.io) | nur als Link |
| Fever (Candlelight) | Feed/API nur für Partner mit viel Traffic | nicht öffentlich (US: 8–10 %) | wohl Impact | ohne Daten nur Links | später |
| **Tiqets** | **Partner-API für Affiliates offen** (Inhalte, Preise, Verfügbarkeit) | nicht öffentlich (Dritte: ≈ 8 %), Cookie 30 Tage | eigenes Portal, Awin | Bilder nur auf Antrag | passt zu Museen/Attraktionen |
| **GetYourGuide** | Partner-API (Token von GYG, Kriterien unbekannt) | ≈ 7–8 %, Cookie 30 Tage | eigenes Portal, Awin | Rate-Limit, Abrufe im Verhältnis zu Buchungen überwacht | passt zu Stadtführungen |
| Viator | Basis-Zugang sofort | Satz nicht genannt | eigenes Portal | überschneidet sich mit GYG | optional |
| myticket.de | unbekannt | ≈ 1 % | Daisycon | – | nein |
| Eventfrog | öffentliche API | keine Provision | – | – | nur als Datenquelle (Schweiz-lastig) |
| Ticketino, Eventbrite, Stagedates, Tixforgigs, Dice | – | kein Käufer-Affiliate gefunden | – | – | nein |

**Rechtliches (allgemein, Anwalt vor Livegang):** Affiliate-Links sind Werbung und müssen direkt am Button erkennbar sein (§ 6 DDG, § 5a Abs. 4 UWG); „Empfehlung“ oder nur ein Warenkorb-Symbol reichten Gerichten nicht. Üblich: „Tickets*“ mit Hinweis „*Affiliate-Link – bei einem Kauf erhalten wir eine Provision, der Preis bleibt gleich“ plus Erklärseite. Tracking-Cookies setzt erst der Anbieter nach dem Klick; trotzdem Datenschutzerklärung ergänzen (Art. 26 DSGVO wird diskutiert).

Die Umsetzung steht in 5.5 (Entscheidung des Auftraggebers vom 24.11.: alle diese Anbieter anbinden).

### 5.5 Partner-Anbindung (Entscheidung des Auftraggebers 24.11.2026)

**Umfang:** Ticketmaster (Impact), Eventim (Awin 11388), Reservix (Awin 31293), ADticket (Awin 18490), Tiqets, GetYourGuide. Nicht beauftragt, später möglich: ticket.io, Fever, Viator. Damit ist die Antwort „Eventim/Reservix vorerst nicht“ vom selben Tag überholt; T2 ist wieder aktiv.

#### 5.5.1 Anmeldungen (macht der Auftraggeber – Claude legt keine Konten an)

| Anbieter | Anmeldung | Was danach in GitHub kommt |
|---|---|---|
| Eventim, Reservix, ADticket | **ein** Awin-Publisher-Konto, darin Bewerbung bei den drei Programmen (Website-Prüfung durch den Anbieter; Reservix verlangt „Reichweite“) | Variable `AWIN_PUBLISHER_ID` (steht ohnehin in jedem Link, also kein Geheimnis); Secret `AWIN_API_TOKEN`, falls Awin für ein Programm einen Produkt-/Eventfeed anbietet |
| Reservix (Daten) | zusätzlich Anfrage an affiliate@reservix.de nach der genannten API-Schnittstelle | Secret `RESERVIX_API_KEY` (Name je nach Antwort) |
| Eventim (Daten) | nach Freigabe im Awin-Konto prüfen, ob „Zugriff auf die Event-Datenbank“ ein Feed/eine API ist | ggf. Feed-URL als Secret |
| Ticketmaster | Impact-Konto, Ticketmaster-Programm (Deutschland), Impact-ID im Ticketmaster-Entwicklerkonto eintragen; **schriftliche Bestätigung**, dass API-Daten + Affiliate-Links zusammen erlaubt sind | Secret `TICKETMASTER_API_KEY` |
| Tiqets | Partner-Portal, API-Token dort selbst erzeugen | Secrets `TIQETS_API_TOKEN`, Variable `TIQETS_PARTNER_ID` |
| GetYourGuide | Partner-Programm, API-Zugang beantragen | Secret `GYG_API_TOKEN`, Variable `GYG_PARTNER_ID` |

Claude legt die Texte für die Ticketmaster-Bestätigung und die Reservix-Anfrage in `docs/partner-anfragen-2026-11-24.md` ab; senden muss der Auftraggeber. Jeder Teil unten funktioniert auch, solange einzelne Freigaben fehlen (fehlende Variable = normaler Link bzw. Quelle wird übersprungen, wie heute bei Ticketmaster).

**Hinweis außerhalb des Plans:** Provisionen sind Einnahmen – Gewerbe/Umsatzsteuer mit dem Steuerberater klären.

#### 5.5.2 Zwei Wege zur Provision

1. **Daten vom Anbieter** (Rang 2): Ticketmaster-API, Reservix-API, Eventim-Feed (falls es ihn gibt) liefern Events mit Ticket-Link; neue Scraper `scraper/tier1/reservix.py`, `scraper/tier1/eventim.py`, bestehender `ticketmaster.py`. Zeitraum 365 Tage, Gebietsfilter wie gehabt.
2. **Ticket-Link aus der Haus-Quelle** (größter Hebel, wirkt auch ohne Datenfeed): Viele Häuser verlinken ihren Ticketverkauf bei Eventim, Reservix, ADticket oder Ticketmaster (in der Prüfung z. B. Comedy Club, Tor 3 und Nachtresidenz → Eventim, Philara → Reservix). Venue-Scraper speichern diesen Link künftig in einer **neuen Spalte `events.ticket_url`** (der DEG-Scraper liest ihn heute schon intern). Die Website macht daraus bei bekanntem Anbieter einen Partner-Link, bei Awin als Deeplink `https://www.awin1.com/cread.php?awinmid=<Programm>&awinaffid=<Publisher-ID>&ued=<Ziel-URL>`.

SQL (vor dem Deploy von P1): `events.ticket_url text`. Beim Rangwechsel (4.2) bleibt ein vorhandener `ticket_url` stehen, wenn die neue Quelle keinen hat; der Admin-Bereich bekommt das Feld in die Bearbeiten-Whitelist (Abstimmung mit dem Admin-Plan).

#### 5.5.3 Welcher Ticket-Button? (Q20)

- **Ein** Ticket-Button je Event, nie mehrere Anbieter mit Preisen nebeneinander (Awin-Bedingung „kein Preisvergleich“; außerdem übersichtlicher).
- Auswahl nach **Offiziellkeit, nicht nach Provision:** zuerst der Ticket-Link, den das Haus selbst nennt (`ticket_url`), sonst der Link der Rang-2-Quelle aus `quellen` (4.3). Das hält die Seite redaktionell unabhängig (Magazin und Impressum nach § 18 MStV).
- Ist die Hauptquelle selbst ein Ticketanbieter, ist „Zum Termin“ schon der Ticket-Link; dann kein zweiter Button.
- **Keine Partner-Links im Magazin-Text** (Q22), nur auf Event- und Ortsseiten sowie im Ausblick.

#### 5.5.4 Tiqets und GetYourGuide: Angebote statt Events (Q21)

Beide verkaufen Eintrittskarten und Touren mit täglicher Verfügbarkeit, keine Einzeltermine. Als Events würden sie den Kalender fluten. Vorschlag:
- Neue Tabelle `partner_angebote` (Anbieter, externe ID, Titel, URL, Bild, „ab“-Preis, Bewertung, `ort_id`, aktualisiert_am), gefüllt einmal je Scraper-Lauf über die APIs (nur Düsseldorf/Neuss/Ratingen).
- **Ortsseiten** von Museen und Attraktionen (Kunstpalast, K20/K21, Aquazoo, Rheinturm …): Button „Tickets“, wenn ein Angebot dem Ort zugeordnet ist. Zuordnung über Name + Adresse als **Vorschlag im Admin-Bereich** (wie die Orte-Vorschläge aus Stufe 3c), erst die Bestätigung schaltet den Button frei.
- **Stadtführungen** (Kategorie `stadtfuehrung`, Guide-Seite): Block „Führungen buchen“ mit bis zu 6 GetYourGuide-/Tiqets-Touren in Düsseldorf, nach Bewertung.
- Bilder aus den APIs nur, wenn die Bedingungen das erlauben (Tiqets: Bilder nur auf Antrag) – sonst ohne Bild.

#### 5.5.5 Website

- **`web/lib/tickets.ts`:** erkennt den Anbieter an der Domain (eventim.de, reservix.de, adticket.de, ticketmaster.de, tiqets.com, getyourguide.de) und baut den Partner-Link aus den Variablen. Schalter **`PARTNERLINKS_AKTIV`** als GitHub-Variable wie `KONTEN_AKTIV` (wirkt mit dem nächsten Deploy; der Admin-Bereich zeigt ihn an). Aus = normale Links ohne Partner-Kennung.
- **Kennzeichnung** direkt am Button: „Tickets*“ und darunter klein „*Partner-Link: Kaufst du darüber, bekommen wir eine Provision. Der Preis bleibt gleich.“ (du-Ansprache wie auf den Konto-Seiten). Dazu ein Abschnitt „Partner-Links“ auf `/ueber` (Anker `#partner-links`).
- Links mit `rel="sponsored noopener"` (Vorgabe von Google für Affiliate-Links).
- **Kein eigenes Klick-Tracking**, keine Cookies bei uns; Auswertung in den Netzwerk-Konten (Awin, Impact, Tiqets, GetYourGuide).
- **Datenschutzerklärung** (Sie-Form): neuer Abschnitt zu den Partnerprogrammen; Entwurf von Claude, Freigabe durch den Anwalt **vor** `PARTNERLINKS_AKTIV=1`. Kennzeichnungstext ebenfalls zum Anwalt.

---

## 6. Website: wo der längere Zeitraum sichtbar wird

### 6.1 Grundsatz (Q8)

Der bestehende Pool `eventPoolLaden()` bleibt bei **60 Tagen**. Alles, was „was ist bald los“ zeigt, ändert sich nicht. Für den längeren Zeitraum kommt ein **zweiter, schlanker Pool** dazu: `fernPoolLaden()` in `web/lib/daten.ts` – Tage 60 bis 365, gleiche Abfrage und `normalisieren()`, eigenes `"use cache"` mit `cacheTag(EVENTS_CACHE_TAG)` (der Admin-Bereich leert ihn mit). Erwartete Größe nach dem Ausbau: 2.000–4.000 Termine, also 2–4 Seiten à 1.000.

| Stelle | Zeitraum | Änderung |
|---|---|---|
| Startseite, Tagesleiste, Wochenende, Kostenlos, Kategorie-/Stadtteilseiten, Tagesplaner | **60 Tage** | keine |
| Empfehlungen (Admin, Fokustag, Top/Highlight) | **60 Tage** | keine (`admin/empfehlungen.ts:51` bleibt) |
| Magazin-Pool | wie heute | keine |
| **Eventseite** | **unbegrenzt** | funktioniert schon (`eventLaden()` lädt einzeln nach); neu: Monats-Label („MÄRZ 2027“) bei Events > 60 Tage, Ticket-Link (6.3) |
| **Ortsseiten** (`/orte/…`, Clubs, Kneipen) | **unbegrenzt** | lädt schon über `ort_id`; neu: Liste nach Monat gruppiert, ab Tag 61 eingeklappt „Ausblick (n)“ |
| **/entdecken – Suche** (`?q=`) | **12 Monate** | Treffer aus dem Fernpool als eigener Block „Ausblick“ unter den normalen Treffern |
| **/entdecken – eigener Zeitraum** | **12 Monate** | `MAX_ZEITRAUM_TAGE` 60 → 366; liegt der Zeitraum ganz oder teilweise hinter Tag 60, kommen die Events aus dem Fernpool dazu |
| **Neue Seite „Ausblick“** (Q9, `/ausblick`) | **Tag 61–365** | Liste nach Monaten, Filter Kategorie; nur Quellen Rang 1–2 und Orte mit Ortsseite (keine Kleinst-Events) |
| Startseite – neue Box | Teaser | Q10: kleine Box „Große Events später im Jahr“ (6 Einträge, Rang 1–2, nach Datum) mit Link auf die neue Seite |
| **Sitemap** | **12 Monate** | Eventseiten aus dem Fernpool aufnehmen (sonst findet Google die fernen Events nicht); Tagesseiten bleiben bei 60 |
| `/api/events`, Konto (Merkliste, „Für dich“), Geburtstags-Tipps | 60 Tage | keine; die Merkliste lädt gemerkte Events schon einzeln |

Nicht geändert wird die Tagesleiste: Sie springt heute schon bis 366 Tage, wenn ein ferner Tag gewählt ist (`datum.ts:39`) – die Tagesseite `/tag/<datum>` hinter Tag 60 bleibt aber leer, solange sie den 60-Tage-Pool nutzt. Vorschlag: `/tag/<datum>` > Tag 60 nutzt den Fernpool; in der Sitemap stehen Tagesseiten weiter nur bis Tag 60 (heute ist eine ferne Tagesseite indexierbar, aber leer – `app/tag/[datum]/page.tsx:17` setzt `noindex` nur für vergangene Tage).

### 6.2 Kennzeichnung

Events > 60 Tage zeigen auf Karten und Eventseite ein kleines Label mit Monat und Jahr (**„MÄRZ 2027“**, Q11), damit niemand sie für morgen hält.

### 6.3 Quell-Link auf der Eventseite (`web/app/event/[kategorie]/[slug]/page.tsx:282–300`)

- Hauptknopf „Zum Termin“ → `quelle_url` (ist nach Abschnitt 4 immer die beste Quelle).
- **Neu:** zweiter Button „Tickets“ nach den Regeln in 5.5.3 (`ticket_url` des Hauses, sonst Rang-2-Quelle aus `quellen`). Ohne beide Angaben entfällt der Button.
- Rausgegangen-Events: siehe 4.4.
- „Quelle: …“ bleibt wie heute die Hauptquelle.
- Partner-Links, Kennzeichnung und Datenschutz: 5.5.5.

### 6.4 Name der neuen Seite (Q9, zweite Runde)

Die bestehenden Adressen sind kurze deutsche Zeitwörter: `/heute`, `/morgen`, `/wochenende`, `/kostenlos`. Die neue Seite sollte in diese Reihe passen und nicht mit vorhandenen Begriffen kollidieren („Merkliste“, Magazin-„Wochenvorschau“, Admin-„Vorschau“). Alle folgenden Adressen sind frei.

| Vorschlag | Adresse | Seitentitel (SEO) | Für | Gegen |
|---|---|---|---|---|
| **Ausblick** (Empfehlung) | `/ausblick` | „Ausblick: Große Events in Düsseldorf bis <Monat Jahr>“ | kurz, neutral, passt zu heute/morgen/wochenende; sagt „weiter weg“ ohne Kaufdruck | etwas nüchtern |
| Vormerken | `/vormerken` | „Jetzt vormerken: Konzerte, Shows und Highlights in Düsseldorf“ | Handlungsaufforderung, passt zum Merken-Button | Verwechslung mit der Merkliste möglich |
| Demnächst | `/demnaechst` | „Demnächst in Düsseldorf“ | geläufig (Kino-Sprache) | klingt nach „bald“, gemeint sind Monate |
| Jahresvorschau | `/jahresvorschau` | „Jahresvorschau Düsseldorf: die großen Events der nächsten 12 Monate“ | eindeutig, gute Suchbegriffe | lang; „Vorschau“ gibt es schon im Magazin |
| Save the Date | `/save-the-date` | „Save the Date: Düsseldorfs große Events“ | bekannt, locker | englisch, die übrigen Adressen sind deutsch |
| Highlights | `/highlights` | „Highlights in Düsseldorf: was die nächsten Monate bringen“ | griffig | Highlight ist schon eine Empfehlungsstufe auf der Startseite |

Ergänzend für Google (unabhängig vom Namen): Unterseiten je Monat (`/ausblick/2027-03`, Titel „Events in Düsseldorf im März 2027“) – danach wird viel gesucht. Vorschlag: erst die Hauptseite, Monatsseiten nach einigen Wochen, wenn genug Fern-Events da sind (Q18).

Label auf Karten (Q11) passt sich an: bei „Ausblick“ statt „Vorverkauf“ einfach das Monatskürzel groß („MÄRZ 2027“) – das erklärt sich selbst.

---

## 7. Umsetzungsschritte und Freigaben

Jeder Schritt: lokal bauen und testen → Zusammenfassung → OK des Auftraggebers → Push aus einem temporären Worktree, der von `origin/claude/setup-project-structure-5QNOf` abzweigt → nächster Scraper-Lauf im Admin-Scraper-Tab bzw. Log prüfen. SQL jeweils **vor** dem Deploy des Schritts.

| Nr. | Inhalt | SQL | Prüfung nach Deploy |
|---|---|---|---|
| **A1** | **Auftraggeber:** Anmeldungen bei Awin (Eventim, Reservix, ADticket), Impact (Ticketmaster), Tiqets, GetYourGuide; Anfragen an Ticketmaster und Reservix senden (Texte von Claude) – läuft parallel ab Freigabe | – | Variablen/Secrets in GitHub |
| **R1** | Rangfolge `pipeline/quellen_rang.py`; Deduplizierung, Speichern, Dubletten-Vorschläge auf Rang umstellen (4.1, 4.2) | – | Lauf-Log: „Quelle gewechselt: A → B“ jetzt auch zwischen Nicht-Rausgegangen-Quellen; Stichprobe 10 Events |
| **R2** | Spalte `events.quellen`, Kennzahlen „nur Rausgegangen“ und „Lücken je Ort“ im Lauf-Report (4.3, 4.5) | `quellen_spalte_<datum>.sql` | Kennzahlen im Report plausibel |
| **Z1** | Zeitraum je Quelle (`vorschau_ende`), Seiten-Grenzen der Langzeit-Scraper, Beschreibungen auf Tag ≤ 60 + Fern-Block 100, Kategorisierungs-Limit befristet 1.500 (5.2, 5.3) | – | Laufzeit je Schritt, Events > 60 Tage je Quelle, keine Zeitüberschreitung |
| **T1** | Ticketing (5.1): Ticketmaster (Secret vom Auftraggeber, Workflow-`env`, Monatsfenster bis 12 Monate), Songkick aus `QUELLEN` nehmen, Stagedates über Sitemap + JSON-LD | – | Events je Quelle, Gebietsfilter, Dubletten zu d.live/Mitsubishi/Capitol |
| **W1** | Website: Fernpool, Suche und eigener Zeitraum bis 12 Monate, Ortsseiten nach Monaten, Monats-Label, Sitemap, `/tag` > 60 (6.1, 6.2) | – | Seiten im Browser, Sitemap-Größe, Ladezeit Startseite unverändert |
| **V0** | Bestehende Quellen mit großer Wirkung reparieren/erweitern: Kunstsammlung (Führungen/Veranstaltungen), VisitDüsseldorf komplett über Sitemap/Toubiz (3.4) | – | Events je Quelle vorher/nachher |
| **V1** | Bausteine (3.3) + Welle A der Venues (3.2) | – | je Haus Eventzahl > 0, Ortszuordnung trifft |
| **P1** | `events.ticket_url`: Venue-Scraper erfassen den Ticket-Link des Hauses (bestehende + Welle A), Rangwechsel behält ihn (5.5.2) | `ticket_url_<datum>.sql` | Anteil Events mit Ticket-Link je Anbieter |
| **N1** | `quellen_nachziehen.py`: Bestand auf Rang umhängen – Probelauf, dann `--schreiben` | – (Sicherung im Skript) | Bericht |
| **W2** | Seite „Ausblick“ (`/ausblick`), Startseiten-Box, Ticket-Button (Partner-Link vorbereitet, aus), Link „Website von <Ort>“ (6.1, 6.3, 4.4) | – | Seiten im Browser |
| **P2** | Partner-Links: `web/lib/tickets.ts`, Kennzeichnung, Abschnitt auf `/ueber`, Datenschutz-Entwurf → Anwalt → Variable `PARTNERLINKS_AKTIV=1` + Deploy (5.5.5) | – | Links im Browser (Partner-Kennung, `rel=sponsored`), Netzwerk-Konten zeigen Klicks |
| **T2** | Reservix-API und Eventim-Feed als Rang-2-Quellen – sobald A1 Zugang liefert (5.5.2) | – | Events je Quelle, Dubletten |
| **T3** | Tiqets/GetYourGuide: Tabelle `partner_angebote`, Abruf je Lauf, Zuordnungs-Vorschläge im Admin, Buttons auf Ortsseiten, Block im Stadtführungs-Guide (5.5.4) | `partner_angebote_<datum>.sql` | Angebote je Ort, Vorschläge |
| **V2** | Welle B (Düsseldorf, Neuss, Ratingen; 3.2) | – | wie V1 |

Cursor-Prüfungen: Plan (Anhang A) vor der Freigabe; Umsetzung nach R1+R2 (Pipeline-Kern), nach W1+W2 (Website) und nach P2 (Partner-Links, vor dem Einschalten).

Parallel möglich: V0/V1 (neue Scraper-Dateien) berühren andere Dateien als R1/R2 (Pipeline-Kern) und W1/W2 (Website). Z1 fasst alle Scraper-Dateien an und läuft deshalb **nicht** parallel zu V0/V1. A1 (Anmeldungen des Auftraggebers) läuft ab Freigabe nebenher; T1, T2, T3 und das Einschalten von P2 warten jeweils auf den passenden Zugang. P1 baut auf V1 auf (dieselben Scraper-Dateien), P2 auf W2 (Ticket-Button).

---

## 8. Tests

Python mit `unittest` (wie bisher; pytest kommt nicht dazu), Website mit dem bestehenden Test-Runner in `web/tests/`.

- **Rang (R1):** jeder Anzeigename aus `main.py` `QUELLEN` hat einen Rang; Rausgegangen per Name und per URL Rang 5; Tier 2/3 ohne Eintrag → 1.
- **Merge (R1):** Paare Haus/Ticketmaster, Ticketmaster/PRINZ, PRINZ/Rausgegangen, Haus/Rausgegangen in beiden Reihenfolgen → Basis ist immer der bessere Rang; gleicher Rang → erste Quelle; Uhrzeit des Hauses gewinnt; leere Werte überschreiben nie; Bild der Rang-2-Quelle bleibt, wenn das Haus keines hat.
- **Speichern (R1):** `_anreicherungs_update_bauen` mit gespeichertem PRINZ-Event und eingehendem Haus-Event → Quellenwechsel; umgekehrt keiner; `redaktion_felder` und `beschreibung_quelle` bleiben geschützt (bestehende Tests erweitern).
- **Dubletten (R1):** `paare_finden` behält den besseren Rang.
- **Quellenliste (R2):** neue Quelle wird angehängt, gleiche Quelle aktualisiert `zuletzt`, höchstens ein Eintrag je Name.
- **Zeitraum (Z1):** `vorschau_ende` je Gruppe; Struktur-Test: kein Scraper rechnet mehr selbst mit `SCRAPER_VORSCHAU_TAGE`.
- **Bausteine (V1):** JSON-LD mit `@graph`, `subEvent`, fehlender Uhrzeit, Zeitzone; Tribe-API-Antwort mit zwei Seiten; iCal mit Ganztags-Termin und wöchentlicher RRULE. Beispieldateien unter `tests/fixtures/`.
- Bestehende Tests, die angepasst werden: `tests/test_rausgegangen_vorrang.py`, `test_dedup_aehnlich.py`, `test_dedup_toleranz.py`, `test_redaktion_feldschutz.py`, `test_lauf_report_kennzahlen.py`.
- **Website (W1/W2):** Zeitraum > 60 Tage wird nicht mehr auf 60 gekürzt, aber auf 366; Suche findet ein Fern-Event im eigenen Block; Startseite enthält kein Event > 60 Tage außer in der neuen Box; Monats-Label ab Tag 61.
- **Ticket-Link (P1):** Rangwechsel ohne `ticket_url` der neuen Quelle behält den alten; Venue-Fixtures liefern den Ticket-Link.
- **Partner-Links (P2, `web/tests/`):** je Anbieter-Domain der richtige Partner-Link (Awin-Deeplink mit korrekt kodierter Ziel-URL, Ticketmaster/Tiqets/GetYourGuide mit Partner-Kennung); unbekannte Domain bleibt unverändert; Schalter aus oder fehlende ID → normaler Link; jeder Partner-Link hat `rel="sponsored noopener"` und den Hinweistext; Ticket-Button-Auswahl nach 5.5.3 (Haus-Link vor Rang-2-Quelle, nie zwei Buttons); keine Partner-Links in Magazin-Beiträgen.
- **Partner-Angebote (T3):** Abruf mit Beispielantworten aus `tests/fixtures/`; nur bestätigte Zuordnungen erzeugen einen Button.

---

## 9. Risiken

- **Mehr Dubletten** durch Ticketing (andere Titel-Schreibweisen: „KÜNSTLER – Tour 2027 – Düsseldorf, Halle“). Gegenmittel: `_bandname_enthalten` deckt viele Fälle; Prüfung nach T1; Dubletten-Vorschläge im Admin-Bereich.
- **Laufzeit:** Beschreibungen sind schon heute bei 2,5 h. Ohne das Datumsfenster (Q14) würde der Lauf das Workflow-Timeout reißen.
- **Venue-Scraper veralten** (Relaunch, neue Struktur): Bausteine warnen bei 0 Treffern; Warnregeln W1/W2 im Admin-Scraper-Tab.
- **Rechtliches:** Nur öffentlich frei zugängliche Termindaten, robots.txt beachtet; Beschreibungen werden wie bisher in eigenen Worten geschrieben, Bilder nur aus der Quelle mit Herkunft. Ticketing-Bedingungen (Attribution, Bildnutzung, Speicherdauer) je Anbieter beachten (5.1).
- **Falsche Rangfolge in Einzelfällen** (z. B. ein Haus-Scraper mit schlechteren Daten als Ticketmaster): leere Felder überschreiben nie; Redaktion kann Felder im Admin-Bereich festsetzen (`redaktion_felder`).
- **Öffentliches Repository:** Zugangsdaten nur als GitHub-Secrets; Ortslisten und Venue-Tabellen sind unkritisch.
- **Partner-Links abmahnfähig:** falsche oder fehlende Kennzeichnung ist ein Wettbewerbsverstoß. Gegenmittel: Kennzeichnung direkt am Button, Erklärseite, Anwalts-Freigabe vor `PARTNERLINKS_AKTIV=1`.
- **Ticketmaster-Bedingungen:** ohne schriftliche Bestätigung (5.5.1) keine Partner-Links auf Ticketmaster-Daten; dann bleibt der Ticketmaster-Link ein normaler Link.
- **Awin-Bedingungen:** kein Preisvergleich, keine Suchmaschinen-Anzeigen auf die Marke; Eventim zahlt nur bei Kauf am selben Tag (Cookie 1 Tag) – Erwartung an die Einnahmen niedrig halten.
- **Glaubwürdigkeit:** Button-Auswahl nach Offiziellkeit (Q20), keine Partner-Links im Magazin (Q22), keine Empfehlung wegen Provision (Empfehlungs-Logik bleibt unverändert).

---

## 10. Offene Fragen an den Auftraggeber

Antworten des Auftraggebers vom 24.11.2026:

1. **Einnahmen / Provision (Q6-a):** Rückfrage des Auftraggebers – bei welchen Anbietern lassen sich über ein Partnerprogramm Provisionen erzielen? → Recherche in 5.4.
2. **Ticketmaster-Schlüssel:** reicht der Auftraggeber nach. Bis dahin bleibt T1 für Ticketmaster offen; Stagedates und die Songkick-Abschaltung gehen ohne Schlüssel.
3. **Eventim/Reservix-Anfrage (Q6-b):** zunächst „vorerst nicht“, dann (24.11., zweite Antwort): **alle genannten Partner anbinden** → 5.5, Schritte A1, P1, T2, T3, P2.
4. **Name der neuen Seite (Q9):** „Später im Jahr“ und „Vorverkauf“ gefallen nicht → neue Vorschläge in 6.4.
5. **Prioritäten bei den Häusern (Q15, Neuss/Ratingen):** keine besonderen Wünsche; Auswahl und Reihenfolge wie in 3.2 vorgeschlagen.

---

## Anhang A: Cursor-Prüf-Prompt (dritte Fassung des Plans)

```
Prüfe den Plan `docs/plan-quellen-ausbau-2026-11-23.md` (Quellen-Ausbau: Venues direkt, Rausgegangen zuletzt,
Ticketing mit bis zu 12 Monaten Vorlauf, Partner-Links mit Provision) gegen den tatsächlichen Code im Repo. Ändere keinen Code und keinen
Plan – nur Befunde.

Prüfe bitte:
1. Abschnitt 1.3/4.2: Stimmt die Beschreibung des heutigen Vorrangs (pipeline/deduplication.py `_events_mergen`,
   database/client.py `_anreicherungs_update_bauen`, pipeline/dubletten_sql.py `paare_finden`,
   pipeline/vorschlaege.py, pipeline/rausgegangen_nachziehen.py)? Gibt es weitere Stellen, die Quellen
   vergleichen oder `ist_rausgegangen`/`ist_aggregator`/`quelle_name` auswerten und auf den Rang umgestellt werden
   müssen (auch beschreibung_quellen.py, adressen_ergaenzen.py, ort_zuordnung.py, reihen_zuordnen.py,
   lauf_report.py, web/)? Bricht die Rang-Regel etwas am Feldschutz `redaktion_felder` oder an `beschreibung_quelle`?
2. Abschnitt 4.2 Punkt 2: Ist „Quellenwechsel bei jedem besseren Rang“ im Zusammenspiel mit dem Slug-Abgleich
   (`_slug_pruefen`), dem Redaktions-Abgleich (`_abgleich_redaktion`) und dem Tagesbestand-Cache sicher? Kann ein
   Event zwischen zwei Quellen hin- und herspringen?
3. Abschnitt 4.3: Reicht `events.quellen jsonb` mit Vorbelegung per SQL? Welche Lese-/Schreibstellen
   (`_ABGLEICH_SPALTEN`, Inserts, `_NICHT_IN_DB`, Admin-Bereich) müssen sie kennen, damit nichts bricht, wenn die
   Spalte noch fehlt bzw. schon da ist?
4. Abschnitt 5.2/5.3: Liste alle Stellen, die SCRAPER_VORSCHAU_TAGE oder ein eigenes Zeitfenster nutzen (auch
   MONATE_VORAUS o. Ä. in einzelnen Scrapern). Welche KI-Schritte (categorizer, unterkategorien,
   beschreibung_quellen, caption_generator, clubs_profil, magazin) würden durch Events bis 365 Tage teurer oder
   langsamer, und reichen die vorgeschlagenen Datumsfenster? Workflow-Timeout `.github/workflows/scrape.yml`.
5. Abschnitt 6.1: Stimmt die Tabelle, welche Seiten `eventPoolLaden()` nutzen und welche ohne Pool laden
   (`eventLaden`, `web/lib/spielstaetten-daten.ts`)? Fehlen Stellen mit eigener 60-/59-Tage-Grenze? Folgen eines
   zweiten Pools für Cache (`cacheTag(EVENTS_CACHE_TAG)`), Sitemap-Größe und Speicher.
6. Abschnitt 3.3: Passen die Bausteine (JSON-LD, WP-Tribe, iCal ohne neue Bibliothek) zu bestehenden Mustern
   (`scraper/utils/bookingkit.py`, `ra_venue.py`, `http_client.py`) und zum Lauf-Report je Quelle
   (`pipeline/lauf_report.py`, Warnregeln in `pipeline/lauf_warnungen.py`), wenn mehrere Häuser aus einer Datei
   `scraper/tier2/venues.py` kommen?
7. Abschnitt 5.5 (Partner-Links): Wo muss `events.ticket_url` überall bekannt sein (Inserts, `_ABGLEICH_SPALTEN`,
   Rangwechsel in `_anreicherungs_update_bauen`, Admin-Whitelist, `web/lib/daten.ts` Spaltenvarianten)? Reicht
   `PARTNERLINKS_AKTIV` als GitHub-Variable (Wirkung erst mit Deploy wie `KONTEN_AKTIV`)? Ist die Button-Auswahl
   (5.5.3) eindeutig, und gibt es Stellen außer der Eventseite, die `quelle_url` als Kauf-Link zeigen (Karten,
   Merkliste, Konto, Mails, Magazin), an denen Partner-Links ungewollt auftauchen oder fehlen?
8. Widersprüche zwischen den Abschnitten, fehlende Tests, Reihenfolge der Schritte in Abschnitt 7 (insbesondere
   Konflikte mit dem laufenden Admin-Plan docs/plan-admin-dashboard-2026-11-23.md, der dieselben Dateien ändert).

Ausgabe je Befund: Schweregrad (kritisch / mittel / gering) · Fundstelle (Plan-Abschnitt + Datei:Zeile) · Befund ·
Vorschlag. Nach Schweregrad sortiert. Am Ende: Gesamturteil (freigabefähig ja/nein). Die Entscheidungen Q1–Q22
trifft der Auftraggeber; sie sind nicht Gegenstand der Prüfung, wohl aber ihre technische Umsetzbarkeit.
```

## Prüfhistorie

- 23.11.2026: erste Fassung (Claude), Datenstand 23.11., Lauf vom 21.11.
- 24.11.2026: Antworten des Auftraggebers eingearbeitet (10), Provisions-Recherche (5.4), Namensvorschläge (6.4), Q18–Q19 neu
- 24.11.2026: dritte Fassung – Auftraggeber: alle Partner-Anbieter anbinden → 5.5, Q19–Q22, Schritte A1/P1/T2/T3/P2, Tests, Risiken
- 24.11.2026: dritte Fassung vom Auftraggeber freigegeben. Cursor-Prüfung (Anhang A) steht noch aus; Empfehlung: vor Schritt R1.
