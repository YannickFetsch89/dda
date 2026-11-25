# Plan: Quellen-Ausbau – Venues direkt, Rausgegangen zuletzt, Ticketing mit Vorlauf – dritte Fassung, **freigegeben 24.11.2026**

Status: **Freigegeben vom Auftraggeber am 24.11.2026 (dritte Fassung).** Die Vorschläge Q1–Q22 gelten damit als entschieden und werden nicht still geändert. Gebaut wird schrittweise (Abschnitt 7), jeder Schritt mit eigenem OK des Auftraggebers.
Jeder Push ist ein Live-Deploy; SQL führt der Auftraggeber im Supabase-SQL-Editor aus.
Runde 1 (Cursor, 24.11.2026) hat den Plan gegen den Code geprüft und die Befunde unten eingearbeitet. Runde 2 hat die Claude-Befunde 19 und 20 geprüft. Runde 3 hat Nr. 25–33 geprüft. Runde 4 hat Nr. 34 geprüft. Runde 5 hat Nr. 35 und 36 gegen den ganzen Plan gehalten und keine kritischen oder mittleren Befunde mehr gefunden. Protokoll: Anhang B.

Drei Ziele des Auftraggebers:
1. **Möglichst alle einzelnen Venues** in Düsseldorf (plus Neuss/Ratingen) direkt abfragen.
2. **Rausgegangen nur noch als letzte Quelle:** von dort nur, was wir nirgends sonst finden; ein direkter Link hat immer Vorrang.
3. **Ticketmaster und Eventim** anbinden und große Events mit bis zu 12 Monaten Vorlauf zeigen; Zeitraum je Quelle statt der globalen 60 Tage. **Songkick bleibt draußen** (Q6).

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

Python: `config.py:83` `SCRAPER_VORSCHAU_TAGE = 60`. Die Konstante steht in **48 Dateien** unter `scraper/` (Zählung 24.11.). Die **47** sind die Länge von `main.py` `QUELLEN` (Zeile 86–139), nicht die Zahl der Dateien. Die Konstante nutzen auch die deaktivierten Dateien `eventbrite.py`, `eventfinder.py`, `bandsintown.py` und `spontacts.py`. `meinestadt.py` ist deaktiviert und nutzt sie nicht. `scraper/utils/ra_venue.py:113` setzt das Fenster für Kulturschlachthof R25 und Salon des Amateurs (höchstens 5 Seiten, `ra_venue.py:122`). Wirklich ohne dieses Fenster: Parkrun (nächster Samstag) und Kleine Weihnachtsmärkte (feste Einträge).

Website:
- `web/lib/daten.ts:34` `TAGE_VORAUS = 60` → `eventPoolLaden()` lädt alles bis heute + 60. Davon leben Startseite, `/entdecken`, Kategorie-, Stadtteil-, Wochenend-, Kostenlos-, Tagesseiten, Guides, Konto-Bereich, Sitemap, `/api/events`.
- `web/lib/datum.ts:129` `MAX_ZEITRAUM_TAGE = 60` (eigener Zeitraum auf /entdecken), `:167` Schlüssel „alle“ = 60 Tage, `:178` „kostenlos in 60 Tagen“, `:39` Tagesleiste (60, bei fernem Tag bis 366).
- `web/lib/admin/empfehlungen.ts:51` `TAGE_VORAUS = 59`.
- `web/app/event/[kategorie]/[slug]/page.tsx:83` „mehr am Ort“ in 59 Tagen.
- **Schon ohne Grenze:** Die Eventseite lädt ein Event außerhalb des Pools einzeln nach (`eventLaden()`, `daten.ts:266`), die **Ortsseiten** laden ihr Programm über `events.ort_id` ohne Pool (`web/lib/spielstaetten-daten.ts:3`).

---

## 2. Entscheidungen (Q1–Q22, am 24.11.2026 freigegeben)

| Nr. | Frage | Entscheidung | Abschnitt |
|---|---|---|---|
| Q1 | Rangfolge der Quellen | Haus 1 · Ticketverkauf 2 · offizielle Portale 3 · Aggregatoren 4 · Rausgegangen 5; besserer Rang wird Hauptquelle, auch nachträglich | 4.1, 4.2 |
| Q2 | Alle Quellen eines Events speichern (`events.quellen`) | ja | 4.3 |
| Q3 | Events, die nur Rausgegangen kennt | behalten; Button weiter auf Rausgegangen, zusätzlich „Website von <Ort>“ (a) | 4.4 |
| Q4 | Rausgegangen-Event an einem Ort mit eigenem Scraper, ohne Treffer | behalten und als Lücke melden (a) | 4.5 |
| Q5 | Wann Rausgegangen abschalten? | nicht in diesem Plan; Kennzahl „nur Rausgegangen < 5 % über drei Läufe“ als Signal | 4.6 |
| Q6 | Ticketing | Ticketmaster, Eventim, Reservix, ADticket, Stagedates ja; **Songkick nein** (bleibt dabei). Die Partner-Anbieter aus 5.5 bindet der Auftraggeber alle an (24.11.) – das hebt Songkick nicht auf | 5.1, 5.5 |
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
| The Craft Studio, Eigenlob Keramik (Workshops, Buchung über etermin) | 18 / 17 | 0 | Termine im HTML (103 / 52 Daten) | S – **Q16 entschieden: ja**, als `community`, erst in dieser Welle |
| Filmkunstkinos (Metropol, Bambi, Cinema) | 7 | 4 | reines Kinoprogramm (814 Daten) | S – **Q17 entschieden: nein**; nur Sonderveranstaltungen, nicht der normale Spielplan |

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

Das gemeinsame Modul darf **nicht** als eine Zeile in `QUELLEN` laufen. `pipeline/lauf_report.py:148–165` schreibt je Aufruf von `scraper_ausfuehren` genau einen Quellnamen (`SCRAPER_FELD`) und einen Status. Eine gemeinsame `scrape()` für 20 Häuser wäre im Report, in den Warnregeln und in „neu je Quelle“ ein einziger Topf: ein leeres Haus versteckt sich, ein Absturz trifft alle. Deshalb bekommt **jedes Haus eine eigene Zeile** in `main.py` `QUELLEN` (dünner Aufruf mit demselben Baustein und dem Anzeigenamen). Der Anzeigename ist zugleich `quelle_name`. Häuser mit eigenem HTML brauchen weiter eine eigene Datei in `scraper/tier2/`.

Regeln je neuer Quelle (wie bisher): robots.txt prüfen (im Code als Kommentar mit Datum festhalten), Pause = das **größere** aus 2 Sekunden und dem Crawl-delay (Goethe-Museum und KaBARett FLiN: 10), Backoff bei 429, realistischer User-Agent, Test mit gespeicherter Beispielseite in `tests/fixtures/`. Saisonale Häuser (Globe Neuss, nur Juni/Juli) melden den bestehenden Status `saisonal`, sonst feuert W2 bei jedem Lauf außerhalb der Saison.

`ort_zuordnung` vergleicht nicht den Anzeigenamen der Ortstabelle, sondern `schluessel(ort)` mit `event_orte` einer aktiven Zeile (`pipeline/ort_zuordnung.py:8–9`, `schluessel` bei `:86–92`). Der Scraper setzt `ort` auf eine Schreibweise, die dort schon steht, oder V1 trägt diese Schreibweise in `event_orte` ein, bevor die Prüfung „Ortszuordnung trifft“ grün sein kann. Ohne `ort_id` bleiben „Website von <Ort>“, die Ortsseite und W7 (Lücken je Ort) blind.

`kategorie` nur mit einem Wert aus der bestehenden Liste (`scraper/tier3/kleine_weihnachtsmaerkte.py:22`, dort `family`, nicht `familie`). `uhrzeit` ist `HH:MM` oder leer, `preis` Freitext (freier Eintritt wird beim Speichern vereinheitlicht, `database/client.py:322–323`). `bild_url` nur `https://…` oder ein lokaler Pfad wie in `kleine_weihnachtsmaerkte.py:40`. Leere Felder überschreiben nie (4.2).

Beschreibung: Venue-Scraper lassen `beschreibung` leer. Schritt 3b holt den Text von `quelle_url` (`veranstalter_nachziehen`). Das Zeitbudget ist `max_sekunden=5400` (`main.py:305`); ist es aufgebraucht, bricht die Schleife ab und der Rest bleibt offen (`pipeline/beschreibung_quellen.py:709–711`). V0 und V1 erhöhen dieses Budget nicht. Die 100 Fern-Events von Q14 laufen **in** diesem Budget, nicht danach. Setzt ein Scraper schon eine Beschreibung, lässt der Kategorisierer das Event aus (`pipeline/categorizer.py:186`, nur `beschreibung` leer).

---

## 4. Ziel 2: Rausgegangen nur als letzte Quelle

### 4.1 Rangfolge der Quellen (Q1)

Neue Datei `pipeline/quellen_rang.py` mit **einer** Funktion `quellen_rang(event) -> int` (kleiner = besser). Grundlage ist eine feste Tabelle nach `quelle_name`, exakt die Anzeigenamen aus `main.py` `QUELLEN` (Zeile 86–139). Rausgegangen wird zusätzlich über die URL erkannt (wie `ist_rausgegangen()`, `deduplication.py:370–374`). **Nicht** über die Domain in `quelle_url`: ein Haus, das auf eventim.de oder ticketmaster.de verlinkt, bleibt Rang 1. Das heutige `ist_aggregator` sucht die Domain im Namen **und** in der URL (`deduplication.py:193–196`) – diese URL-Suche darf der Rang nicht übernehmen, sonst springt ein Haus mit Ticket-Link auf Rang 2.

| Rang | Gruppe | Quellen (Anzeigenamen) |
|---:|---|---|
| 1 | **Veranstalter / Haus** | alle Tier-2- und Tier-3-Zeilen in `QUELLEN` und die neuen Venue-Zeilen (Abschnitt 3), inklusive `StartupDorf Meetup` |
| 2 | **Offizieller Ticketverkauf** | `Ticketmaster`, Eventim, Reservix, ADticket, Stagedates (Q6, Q19, Abschnitt 5.1 – nicht „später“) |
| 3 | **Offizielle Portale** | `VisitDüsseldorf`, `VisitDüsseldorf Führungen`, `Kulturportal Düsseldorf`, `Meetup.com`, `Resident Advisor` |
| 4 | **Aggregatoren** | `PRINZ.de Düsseldorf`, `AllEvents.in Düsseldorf`, `Songkick` (bis T1 die Zeile entfernt), Eventfinder, meinestadt (beide heute nicht in `QUELLEN`, nur für alte Zeilen) |
| 5 | **Rausgegangen** | `Rausgegangen`, und jede URL mit `rausgegangen.de` |

Unbekannter **Anzeigename** im Lauf: Rang 1, wenn die Zeile in `QUELLEN` Tier 2 oder 3 hat, sonst Rang 4. Das gilt nur für den Rang aus `_scraper`, nicht für gespeicherte Namen (dafür die zweite Tabelle unten, unbekannter gespeicherter Name = Rang 3). Ein Test verlangt, dass **jeder** heutige Anzeigename aus `QUELLEN` ausdrücklich in der Tabelle steht, damit Ticketmaster nicht versehentlich Rang 4 wird.

**Anzeigename ≠ gespeicherter `quelle_name` (Claude, Runde 1):** Bei vier Zeilen schreibt der Scraper einen anderen `quelle_name` als den Anzeigenamen: `VisitDüsseldorf Führungen` → `VisitDüsseldorf` (`scraper/tier1/visitduesseldorf_fuehrungen.py:40`), `Classic Remise Düsseldorf` → `Classic Remise`, `Street Food Thursday` → `Street Food Thursday Düsseldorf`, `Kleine Weihnachtsmärkte` → `Kleine Weihnachtsmärkte (Redaktion)` bzw. der Name aus der CSV-Spalte `quelle_name` („Stadt Neuss“, „neuss feiert“ …, `scraper/tier3/kleine_weihnachtsmaerkte.py:57`). Gespeicherte Zeilen kennen nur `quelle_name`. Deshalb:
- **Im Lauf** zählt der Anzeigename aus `_scraper` (`SCRAPER_FELD`, gesetzt in `pipeline/lauf_report.py:148–149`). Weil `events_speichern` alle `_`-Felder vor `_anreicherungs_update_bauen` entfernt (`database/client.py`, Aufbau von `datensatz`), wird der Rang **vorher** berechnet und als Argument übergeben (wie heute `kategorie_fest`).
- **Für gespeicherte Zeilen** gilt eine zweite Tabelle `quelle_name → Rang`, gebaut aus den Anzeigenamen **und** den `QUELLE_NAME`-Konstanten der Module. Unbekannter gespeicherter Name (z. B. CSV-Namen der kleinen Märkte) → **Rang 3**. Rang 1 (Haus) und Rang 2 (Ticketverkauf) lösen ihn ab, Rang 4 und 5 nicht. **Entschieden (Claude, Runde 2, technische Detailfrage ohne Rückfrage):** Die CSV-Namen der kleinen Märkte bleiben Rang 3. Dass eine Ticketverkaufs-Quelle einen solchen Eintrag ablöst, ist gewollt: Sie bringt dann einen Kauf-Link, die Redaktionsangaben (Text, Bild aus `redaktion_felder`) bleiben geschützt. Die CSV-Namen stehen nicht als Konstante im Modul; der Struktur-Test sieht sie deshalb nicht und erzwingt sie nicht.
- Test: Für jede Zeile in `QUELLEN` werden die `QUELLE_NAME`-Werte des Moduls gesammelt; jeder muss in der zweiten Tabelle stehen und denselben Rang haben wie der Anzeigename.

`ist_aggregator()` bleibt für die Uhrzeit-Regel bestehen und wird aus dem Rang abgeleitet (Rang ≥ 2). Dieselbe Ableitung ersetzt die Kopie `AGGREGATOR` in `web/lib/admin/events.ts:164–165` (Dubletten-Uhrzeit im Admin). Die Uhrzeit-Regel: bei Abweichung gilt die Zeit der Quelle mit dem besseren Rang, wenn dieser 1 ist. Gleicher Rang ändert die Uhrzeit nicht.

### 4.2 Wo der Rang greift

1. **In-Memory-Deduplizierung** (`_events_mergen`, heute nur Tausch wenn die Basis Rausgegangen ist, `deduplication.py:393–398`): die Quelle mit dem **strikt besseren** Rang wird Basis. Gleicher Rang → die zuerst gekommene bleibt, auch wenn sie später noch einmal hereinkommt. Die Reihenfolge in `QUELLEN` wird damit egal (bleibt aber: Rausgegangen zuletzt, `main.py:136–138`).
2. **Speichern** (`_anreicherungs_update_bauen`, heute nur Wechsel weg von Rausgegangen und nur mit `quelle_url`, `client.py:128–135`): Der Quellenwechsel gilt für jeden **strikt besseren** Rang, und nur wenn das neue Event eine `quelle_url` hat. Ohne URL werden leere Felder aufgefüllt, `quelle_name`/`quelle_url` bleiben. So verliert ein gespeicherter Ticket-Link nicht den Button, und zwei Quellen können nicht hin- und herspringen: der schlechtere Rang schreibt die Quelle nie zurück, gleicher Rang auch nicht. Übernommen werden wie heute `quelle_name`, `quelle_url` und die Vorrang-Felder Bild, Preis, Adresse, Beschreibung – Beschreibung nicht, wenn `beschreibung_quelle` gesetzt ist; nichts, was in `redaktion_felder` steht (der Filter sitzt am Ende und gilt für alle vier Blöcke, `client.py:137–142`). Bild: ein Bild der besseren Quelle ersetzt das bisherige nur, wenn das bisherige von Rang ≥ 4 stammt (Ticketing-Bilder von Rang 2 bleiben, auch wenn das Haus kein eigenes Bild hat – leere Werte überschreiben nie). `ticket_url` (ab P1) bleibt stehen, wenn die neue Quelle keinen Ticket-Link hat. `ort_id` wird beim Rangwechsel nicht ersetzt und nicht geleert: sie wird nur ergänzt, wenn sie fehlt (`database/client.py:100–103`). Slug und `abgleich_*` bleiben unangetastet (`_slug_pruefen`, `_abgleich_redaktion` finden die Zeile, sie wechseln die Quelle nicht).
3. **Dubletten-Vorschläge** (`dubletten_sql.paare_finden`, `vorschlaege.py`): Sortierung „Status-Zusatz, Rang, älterer Eintrag“ statt „Status-Zusatz, Aggregator, älterer Eintrag“. Behalten wird also der Eintrag mit dem besseren Rang.
4. **Einmaliges Nachziehen** (`rausgegangen_nachziehen.py`): wird auf den Rang umgestellt und heißt dann `pipeline/quellen_nachziehen.py` (altes Modul bleibt als dünner Aufruf, damit Doku-Verweise stimmen). Dieselben Grenzen wie beim Speichern: nur strikt besserer Rang, nur mit URL der besseren Quelle, `redaktion_felder` und `beschreibung_quelle` bleiben, vorhandene `ticket_url` und `quellen` werden nicht geleert. **Ein** Lauf, Schritt N1, nach P1: die Spalte `ticket_url` muss schon existieren. Vorher kein Nachziehen. Ablauf: Probelauf (Bericht), dann `--schreiben` mit OK.

Abstimmung mit dem Admin-Plan: Der Admin-Plan ist seit 24.11. komplett live (Stufe 6, `3f6a7ab`). Er hat `database/client.py` (Feldschutz `redaktion_felder`), `pipeline/vorschlaege.py` (Dubletten-, Gebiets- und Orte-Vorschläge) und „Quellen an/aus“ (Stufe 5b, `3333855`) eingeführt. R1 baut auf diesem Stand auf und muss alle drei berücksichtigen.

### 4.3 Alle Quellen eines Events merken (Q2)

Neue Spalte `events.quellen jsonb` (Liste `[{"name", "url", "rang", "zuletzt"}]`, höchstens eine Zeile je Quellenname). Gefüllt beim Speichern: neues Event mit seiner Quelle; bei einem Duplikat wird die Quelle des eingehenden Events ergänzt bzw. `zuletzt` aktualisiert. Die Hauptquelle bleibt in `quelle_name`/`quelle_url` (keine Änderung für Website, Admin, Sitemap).

Wofür:
- **Messbar machen**, wie viele Events nur Rausgegangen kennt (Kennzahl im Lauf-Report und im Admin-Cockpit: „nur Rausgegangen: n von m“), und an welchen Orten.
- **Ticket-Link:** Ist die Hauptquelle ein Haus (Rang 1) und kennt eine Rang-2-Quelle dasselbe Event, zeigt die Eventseite einen zweiten Button. Der Text ist „Tickets*“ (6.3 und 5.5.5).
- **Abdeckungsprüfung:** Rausgegangen-Events an Orten, die wir direkt abfragen, ohne Treffer der Direktquelle → Hinweis auf eine Lücke im Venue-Scraper (Abschnitt 4.5).

SQL (`database/quellen_spalte_<datum>.sql`, führt der Auftraggeber **vor** dem Deploy von R2 aus): Spalte `jsonb`, kein Index nötig. Vorbelegung aus `quelle_name`/`quelle_url`. Neue Spalten auf `events` erben die Policy „Events lesen“ (`database/auth_rollen.sql:147–149`, `abgelehnt = false` für anon). R1 liest und schreibt die Spalte nicht. Ab R2 hängt sie an `_ABGLEICH_SPALTEN` (`client.py:61`). Fehlt sie, schlägt jede Abgleich-Abfrage fehl, nicht nur der Eventseiten-Select.

Die Website hängt neue Spalten an die **erste** Zeile von `SPALTEN_VARIANTEN` (`web/lib/daten.ts:17–26`). Diese Liste gilt für den ganzen Pool, nicht nur für die Eventseite. Fehlt die Spalte, fällt der Pool auf die nächste Variante zurück und verliert damit auch `nicht_empfehlen`. Deshalb zuerst SQL, dann Deploy. `quellen` ist klein und darf im Pool mitkommen.

Die Kennzahl „nur Rausgegangen“ steht im Lauf-Report. **Speicherort (Claude, Runde 1, in Runde 2 präzisiert):** Kennzahlen des Laufs sind Spalten von `scraper_laeufe`; eine neue braucht erst eine Spalte (`main.py:299`, `pipeline/lauf_report.py:186–188`). Das SQL von R2 legt deshalb zusätzlich `scraper_laeufe.kuenftige_events int`, `scraper_laeufe.nur_rausgegangen int` und `scraper_laeufe.luecken jsonb` (`{Ort: Anzahl}` für W7) an und endet mit `NOTIFY pgrst, 'reload schema'` (wie `database/scraper_laeufe_ort_kennzahlen_2026-11-20.sql:16`). Sonst kennt PostgREST die Spalten im ersten Lauf danach noch nicht.

W7 liest `luecken` nur, wenn die Abfrage die Spalte holt. `scraperDatenLaden` und das Cockpit nennen die Spalten ausdrücklich (`web/lib/admin/scraper.ts:40`, `web/lib/admin/cockpit.ts:45`). `warnungenBerechnen` bekommt heute nur Läufe und Ergebnisse (`web/lib/admin/warnregeln.ts:51`). R2 erweitert beide Selects, `LaufAnzeige` und die Funktion um `luecken`, und das Cockpit zusätzlich um `nur_rausgegangen` und `kuenftige_events`. Fehlt eine dieser Spalten, entfällt nicht nur W7: `abschliessen` schreibt alle Kennzahlen in einem Update (`pipeline/lauf_report.py:200–207`) und fällt bei einem Fehler auf Status, Ende und Fehlermeldung zurück (`:208–213`). Deshalb SQL vor dem Deploy. Das Cockpit zeigt die Kennzahl des letzten Laufs. Es zählt sie nicht aus `eventPoolLaden()` nach (`web/lib/admin/cockpit.ts:5` und `:97` laden nur 60 Tage).

### 4.4 Was mit Events passiert, die nur Rausgegangen kennt (Q3)

**Entschieden (Q3-a):** behalten.
- Der Haupt-Button zeigt weiter auf die Rausgegangen-Seite (sie ist die einzige Seite mit Ticket-/Detailinfos zu genau diesem Termin). Heute heißt er „Zum Termin um … Uhr“, wenn diese Uhrzeit einen eigenen Link hat, sonst „Zur Veranstalter-Seite“ (`web/app/event/[kategorie]/[slug]/page.tsx:74–75` und `:282–286`). Die Texte bleiben. **Zusätzlich**, wenn die zugeordnete Zeile in `orte` (über `ort_id`, nicht über eine Namenssuche) eine `webseite` hat: Link „Website von <Ort>“ über dem Quellenhinweis.
- Q3-b (Haupt-Button auf die Ortswebsite) ist verworfen: die Ortswebsite nennt den Termin oft nicht.

### 4.5 Rausgegangen-Events an Orten mit eigener Quelle (Q4)

**Entschieden (Q4-a).** Liefert Rausgegangen ein Event an einem Ort, dessen Haus wir direkt abfragen (Rang-1-Zeile in `QUELLEN` mit derselben `ort_id`/`_haus_id`), und die Direktquelle hat an dem Tag nichts Passendes:
- Event trotzdem speichern (sonst fehlen Termine, die unser Scraper übersieht – z. B. Kunstsammlung: Führungen fehlen), aber im Lauf-Report als „Lücke im Venue-Scraper“ je Ort zählen. Mehr als 3 Lücken an einem Ort in einem Lauf → gelbe Warnung **W7** im Admin-Scraper-Tab. Die Regeln heißen heute W1–W6 (`pipeline/lauf_warnungen.py:3`, dieselbe Liste in `web/lib/admin/warnregeln.ts:24`). Die Mail geht bei W1, W2, W4 und W6 raus (`lauf_warnungen.py:25–26`). W7 ist gelb und steht **nicht** in `MAIL_REGELN`, wie W3. Beide Seiten (Python und TypeScript) und `tests/fixtures/lauf_warnungen.json` bekommen die Regel.
- Nicht mitzählen: die Rang-1-Quelle ist im Admin abgeschaltet (`pipeline/quellen.py:21`, Status `uebersprungen`) oder der Lauf hat sie als `saisonal` gemeldet. Sonst warnt jedes abgeschaltete Haus und jedes Festival außerhalb der Saison.
- Q4-b (verwerfen) ist verworfen: Venue-Scraper haben am Anfang Lücken.

### 4.6 Rausgegangen-Scraper selbst

Bleibt unverändert: nur die Startseite, ein Abruf je Lauf (C4 aus dem Club-Plan). Keine weiteren Rausgegangen-Seiten. **Q5 entschieden:** in diesem Plan nicht abschalten. Die Kennzahl aus 4.3 ist das Signal: „nur Rausgegangen“ unter 5 % der künftigen Events über drei Läufe. Abgeschaltet wird erst in einem späteren Plan.

---

## 5. Ziel 3: Ticketing und Zeitraum je Quelle

### 5.1 Ticketing-Anbieter

Recherche vom 23.11.2026 (Dokumentation und Bedingungen der Anbieter gelesen, robots.txt geprüft; kein Konto angelegt):

| Anbieter | Stand bei uns | Zugang | Bedingungen / Haken | Vorschlag |
|---|---|---|---|---|
| **Ticketmaster** | Scraper vorhanden (`tier1/ticketmaster.py`), läuft leer: **kein Secret** im Workflow (`scrape.yml` setzt `TICKETMASTER_API_KEY` nicht). Heute **eine** Abfrage, `size=50`, `city=Düsseldorf`, ohne Blättern (`ticketmaster.py:287–294`), danach Schnitt bei 60 Tagen (`:340–342`) | Discovery API v2, Schlüssel sofort nach Registrierung; 5.000 Abfragen/Tag, mit 2/s planen; Blättern nur bis 1.000 Treffer → Abfrage in Monatsfenster teilen; `countryCode=DE`, `city`/`geoPoint`+`radius` | Kein Nachbau von Ticketmaster; Inhalte nur „angemessen lange“ zwischenspeichern; auf Verlangen binnen 24 h entfernen; Ticketmaster nicht als Bild-Host; Team-/Liga-Logos nicht frei. **Einnahmen „aus der Nutzung der API“ sind ausgeschlossen** (Ausnahme nicht auffindbar; in Runde 1 nicht erneut auf der Anbieterseite geprüft) → Q6-a | **Ja, zuerst** (T1): Auftraggeber registriert sich, Secret `TICKETMASTER_API_KEY`, Workflow-`env` ergänzen, **und** der Scraper bekommt Monatsfenster bis 12 Monate plus Blättern. Der Schlüssel allein liefert höchstens 50 Events. Wie viele Düsseldorfer Events Ticketmaster DE hat, zeigt erst der erste Lauf (Eventim dominiert in DE) |
| **Eventim** | nichts (Umsetzung: 5.5) | Keine öffentliche API. Partnerprogramm über Awin (Programm „eventim DE“) mit Deeplinks; ob es einen **Event-Datenfeed** gibt und ob man daraus Eventseiten bauen darf, ist nur im Awin-Konto bzw. auf Anfrage zu klären | eventim.de blockt automatisierte Abrufe technisch (Akamai; jede Anfrage lief in einen Timeout) – **kein Scraping** | **Ja** über Awin (5.5): Ticket-Links der Häuser als Partner-Links (P1/P2), Eventdaten nur, falls Awin einen Feed liefert (T2) |
| **Songkick** | Scraper fertig, kein Secret | API nur noch als **bezahlte Lizenz** mit Partnervertrag, keine Hobby-/Kleinprojekte | Metro-Seite hätte JSON-LD (50 Konzerte/Seite), aber die Nutzungsbedingungen verbieten Scraper ohne schriftliche Zustimmung und kommerzielle Nutzung | **Nein.** Scraper bleibt im Code, aber aus `QUELLEN` raus (wie Bandsintown), CLAUDE.md-Tabelle anpassen |
| **Stagedates** | nur indirekt (Rudas Studios) | `sitemap-events.xml` (≈ 830 URLs), Eventseiten mit JSON-LD `Event`/`Offer`; robots.txt erlaubt alles | Nutzungsbedingungen noch zu lesen | **Ja** (mit Welle A): Sitemap filtern auf Düsseldorf/Neuss/Ratingen, JSON-LD-Baustein (3.3) |
| Reservix / ADticket | nichts | Affiliate über Awin; Reservix nennt eine API für Partner; robots.txt antwortet 403 (Bot-Schutz) – kein Scraping | – | **Ja** über Awin + Reservix-API (5.5) |
| Tixforgigs | nichts | keine API; robots.txt erlaubt Eventseiten | strukturierte Daten ungeprüft | Später prüfen |
| Bandsintown, Dice, Eventbrite-Suche, Pretix | Bandsintown/Eventbrite deaktiviert | nur für Künstler / eigene Partner-Events / abgeschaltet / Token je Veranstalter | – | Nein (Eventbrite höchstens je bekanntem Veranstalter über `/v3/venues/{id}/events/`) |

Rang (4.1): Ticketmaster, Eventim (ab T2) und Stagedates sind Rang 2. „Später“ meint nur den Schritt, nicht den Rang.

Ticketmaster-Abfrage: ein Durchlauf je Monat bis 12 Monate voraus, `countryCode=DE`, `geoPoint` Düsseldorf + `radius=25`, `unit=km`, danach `pipeline/gebiet.py`. 12 Monate × wenige Seiten ≈ 30 Abfragen je Lauf – weit unter dem Tageslimit.

### 5.2 Zeitraum je Quelle (Q7)

`config.py` bekommt statt der einen Zahl eine kleine Tabelle und eine Hilfsfunktion:

```python
SCRAPER_VORSCHAU_TAGE = 60  # Fallback: Aggregatoren und Rausgegangen. Name bleibt für Altcode.
def vorschau_ende(quelle: str, heute: date) -> date:
    """Tage aus VORSCHAU_TAGE, sonst 120 für Tier 2/3 und 60 für Tier 1."""
```

`VORSCHAU_TAGE` schlüsselt auf den **Anzeigenamen** in `QUELLEN`. Maßgeblich ist Q7, nicht eine unvollständige Skizze:

- **365:** `Ticketmaster`, Eventim, Reservix, ADticket, Stagedates, `d-live`, `Mitsubishi Electric HALLE`, `Capitol Theater Düsseldorf`, `Tonhalle Düsseldorf`, `Deutsche Oper am Rhein`, `Düsseldorfer Schauspielhaus`, `Kom(m)ödchen Düsseldorf`, `Messe Düsseldorf`, `Fortuna Düsseldorf`, `DEG Eishockey Düsseldorf`, `Kunstsammlung NRW (K20/K21)`, und jedes neue Haus, dessen Spalte „Fenster“ in 3.2 **365** ist. In der Neuss/Ratingen-Tabelle fehlt die Spalte: Haus-Spielplan 365 (TaS, Rheinisches Landestheater, Globe nur in der Festivalzeit), städtischer Kalender 120 (`Stadt Ratingen`).
- **120:** `VisitDüsseldorf`, `VisitDüsseldorf Führungen` (Q7, entschieden – nicht mehr „Vorschlag“), und jedes andere Tier-2-/Tier-3-Haus ohne 365-Eintrag (zakk, Stadtbüchereien, Pitcher, …). Ein neues Tier-2-/Tier-3-Haus ohne Eintrag bekommt 120, nicht 60.
- **60:** die übrigen Tier-1-Namen, inklusive `Rausgegangen`, `Meetup.com`, `Resident Advisor`, `PRINZ.de Düsseldorf`, `AllEvents.in Düsseldorf`.

- Jeder Scraper ersetzt `heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)` durch `vorschau_ende` mit dem **Anzeigenamen** der `QUELLEN`-Zeile (derselbe String wie `_scraper`), nicht mit `QUELLE_NAME`, wenn die beiden auseinanderfallen. `VORSCHAU_TAGE` enthält zusätzlich jede abweichende `QUELLE_NAME` mit **demselben** Fenster: `VisitDüsseldorf` (der Führungs-Scraper, `visitduesseldorf_fuehrungen.py:40`) 120 wie `VisitDüsseldorf Führungen`, `Classic Remise` 120 wie `Classic Remise Düsseldorf`, `Street Food Thursday Düsseldorf` 120 wie `Street Food Thursday`. Sonst bekäme ein unbekannter Name das Tier-1-Fenster von 60 Tagen. Kleine Weihnachtsmärkte nutzen das Fenster nicht (1.4). Das sind die 48 Dateien aus 1.4, deshalb ein eigener Schritt (Z1) mit Test „kein Scraper rechnet das Fenster mehr selbst“ (Quelltext-Prüfung) und demselben Struktur-Test wie bei der zweiten Rangtabelle. `config.py:83` verliert den Kommentar „Website zeigt ebenfalls 60“.
- **Seiten-Grenzen sind Teil von Z1, nicht optional.** Ein längeres Fenster hilft nur, wenn der Scraper auch weiter liest. Heute stehen Oper auf 2 Monaten (`oper_am_rhein.py:33`) und das Schauspielhaus auf 6 (`schauspielhaus.py:47`). Beide Häuser haben Fenster 365, also zieht Z1 `MONATE_VORAUS` so weit, dass diese 365 Tage gelesen werden. RA-Häuser bleiben bei höchstens 5 Seiten (`ra_venue.py:122`). Ticketmaster bleibt in Z1 bei einer Seite à 50; Monatsfenster und Blättern liegen in T1 (5.1). Tonhalle, Capitol, d.live, Mitsubishi-Halle, Kom(m)ödchen, Fortuna und DEG werden im selben Schritt gelesen und, wo der Spielplan kürzer ist als das Fenster, erweitert. Ergebnis je Scraper in der Umsetzungsnotiz.

### 5.3 Folgen für die Pipeline

- **Speichern:** heute 8 min für 1.829 Events (bis zu 3 Abfragen je Event). Mit +2.000–4.000 Fern-Terminen etwa +10–20 min. Vertretbar. Eine Optimierung (Tagesbestand vorab laden) ist nicht Teil dieses Plans. Der Job endet bei 240 Minuten (`scrape.yml:44`). Die Abnahme steht in Abschnitt 7.
- **Kategorisierung** (`categorizer.kategorisieren(limit=300)`, nach Datum sortiert): Ferne Events kommen erst dran, wenn die nahen fertig sind. Beim ersten Lauf mit 12 Monaten entsteht ein Rückstand von 2.000+ Events → **Q13:** Limit für zwei Wochen auf 1.500 anheben (Haiku, ≈ 0,1–0,2 Cent je Event, also ≈ 2–3 € einmalig), danach zurück auf 300. Der Fernpool (6.1) lädt deshalb nur Events mit Kategorie (`kategorie is not null`), damit unfertige Einträge nicht im Ausblick landen.
- **Unterkategorien** (limit 600): gleiche Logik, unkritisch.
- **Beschreibungen (Schritt 3b, im Lauf vom 21.11. 2 h 28 min):** Hier liegt das eigentliche Risiko. Das Workflow-Timeout ist **240 Minuten** (`.github/workflows/scrape.yml:44`), nicht 6 Stunden. GitHub ließe 360 zu, der Job ist aber auf 240 gesetzt. Nach einem Lauf von 3 h 7 min bleiben rund 50 Minuten. **Q14, entschieden:** Beschreibungen nur für Events bis Tag 60 wie bisher; Fern-Events bekommen ihre Beschreibung, sobald sie ins 60-Tage-Fenster rutschen. Ausnahme: höchstens 100 Fern-Events je Lauf mit Rang 1–2 (für den Ausblick und die Sitemap), nach Datum. Umsetzung: oberes Datum `datum <= heute + 60` in `offene_rausgegangen_events` (`pipeline/beschreibung_quellen.py:461`) und `offene_veranstalter_events` (`:604`). Der Fern-Block von höchstens 100 Events mit Rang 1–2 ist eine zweite, begrenzte Abfrage und zählt auf dasselbe `max_sekunden`. `alle_event_seiten` (`:623–631`) sammelt nur Pfade, um Kalenderseiten zu erkennen, und schreibt keine Beschreibung; dort kein Datumsfenster.
- **IndexNow** meldet nur Events, die **dieser Lauf** angelegt hat (`pipeline/indexnow.py:167–175`), nicht den ganzen künftigen Bestand. Ein erster Lauf mit Tausenden neuen Fern-Events kann trotzdem viele URLs auf einmal schicken. Ob das Tageskontingent von IndexNow reicht, ist offen (nicht geprüft). Die Meldung bleibt auf neue Events beschränkt; sie wird nicht auf alle Fern-Events ausgedehnt.
- **Reihen** laden schon alle Events ab heute minus 365 Tage, ohne oberes Datum (`pipeline/reihen_zuordnen.py:24` und `:116–119`). Mehr Zeilen, keine KI. Kein neues Fenster nötig.
- **Club-Scores:** der Zahlenwert „Programm“ zählt schon nur heute−90 bis heute+60 (`clubs_profil.py:663–664`). `kalender_laden` holt aber alle kommenden Events ohne Obergrenze (`:294–298`), und `kalender_quelle` behält von der nach Datum sortierten Liste die **letzten** 60 Zeilen (`:379–385`) – das wären die fernsten Termine, nicht die nächsten. Z1 begrenzt diese Quelle auf heute+60, bevor der Prompt gebaut wird.
- **Instagram/Captions:** sollen nah bleiben, tun das im Code aber nicht. `caption_generator.py:208–216` lädt `status = neu` mit Beschreibung **ohne** Datumsfilter (Limit 50). `publisher.py:281–290` postet `status = aufbereitet` ohne Datumsfilter, die nächsten zuerst, Top/Highlight/Tipp vorgezogen. Sobald Q14 einem Fern-Event eine Beschreibung gibt, kann es eine Caption bekommen und später gepostet werden. Z1 setzt in beiden Abfragen `datum <= heute + 60`. Top/Highlight/Tipp eines Fern-Events postet der Publisher erst, wenn das Event in diesem Fenster liegt.
- **Gebietsfilter:** Ticketing liefert Region (Köln, Essen …) – `pipeline/gebiet.py` filtert schon nach Düsseldorf/Neuss/Ratingen; Ticketmaster-Abfrage zusätzlich per Ort/Radius eingrenzen.

### 5.4 Provision: Partnerprogramme mit Eventdaten (Recherche 24.11.2026, Rückfrage des Auftraggebers)

Recherche in Programmseiten, Awin-Profilen und Entwickler-Dokumentation; kein Konto angelegt. Die tatsächlichen Sätze für Deutschland stehen bei mehreren Anbietern erst nach der Anmeldung im jeweiligen Netzwerk fest. **Runde 1 und Runde 3 haben diese Anbieterseiten nicht erneut abgerufen** – Sätze, Cookie-Fristen und API-Zusagen in dieser Tabelle bleiben offen/ungeprüft, Stand 24.11.2026. Das blockiert den Plan nicht. Gebaut wird trotzdem. `PARTNERLINKS_AKTIV` geht erst auf 1, wenn die Anmeldung da ist und der Anwalt Kennzeichnung und Datenschutz freigegeben hat (Q12, 5.5.5, Schritt P2). Bis dahin bleiben die Links normal.

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
2. **Ticket-Link aus der Haus-Quelle** (größter Hebel, wirkt auch ohne Datenfeed): Viele Häuser verlinken ihren Ticketverkauf bei Eventim, Reservix, ADticket oder Ticketmaster (in der Prüfung z. B. Comedy Club, Tor 3 und Nachtresidenz → Eventim, Philara → Reservix). Venue-Scraper speichern diesen Link künftig in einer **neuen Spalte `events.ticket_url`**. Der DEG-Scraper liest den Link heute nur intern (`scraper/tier3/deg.py:255–257`) und schreibt ihn **nicht** ins Event (`:316–331`). P1 übernimmt ihn dort. Die Website macht daraus bei bekanntem Anbieter einen Partner-Link, bei Awin als Deeplink `https://www.awin1.com/cread.php?awinmid=<Programm>&awinaffid=<Publisher-ID>&ued=<Ziel-URL>`.

SQL (vor dem Deploy von P1, Datei `database/ticket_url_<datum>.sql`): `events.ticket_url text`, am Ende `NOTIFY pgrst, 'reload schema'` (wie `database/scraper_laeufe_ort_kennzahlen_2026-11-20.sql:16`). Ohne `NOTIFY` kennt PostgREST die Spalte im ersten Lauf danach nicht, und ein Insert mit `ticket_url` scheitert. Dieselbe Policy wie bei `quellen` (4.3): die Spalte erbt „Events lesen“. Beim Rangwechsel (4.2) bleibt ein vorhandener `ticket_url` stehen, wenn die neue Quelle keinen hat. `ticket_url` kommt in `BEARBEITBAR` (`web/lib/admin/events.ts:7–24`) und in die erste `SPALTEN_VARIANTEN`-Zeile, analog zu `quellen`. `quelle_url` bleibt die Hauptquelle und ist kein Ersatz für `ticket_url`.

#### 5.5.3 Welcher Ticket-Button? (Q20)

- **Ein** Ticket-Button je Event, nie mehrere Anbieter mit Preisen nebeneinander (Awin-Bedingung „kein Preisvergleich“; außerdem übersichtlicher).
- Auswahl nach **Offiziellkeit, nicht nach Provision:** zuerst der Ticket-Link, den das Haus selbst nennt (`ticket_url`), sonst der Link der Rang-2-Quelle aus `quellen` (4.3). Das hält die Seite redaktionell unabhängig (Magazin und Impressum nach § 18 MStV).
- Ist die Hauptquelle selbst ein Ticketanbieter (Rang 2), ist der Haupt-Button schon der Ticket-Link; dann kein zweiter Button. Der Button-Text bleibt der heutige (6.3), nicht pauschal „Zum Termin“.
- **Keine Partner-Links im Magazin-Text** (Q22), nur auf Event- und Ortsseiten sowie im Ausblick.

#### 5.5.4 Tiqets und GetYourGuide: Angebote statt Events (Q21)

Beide verkaufen Eintrittskarten und Touren mit täglicher Verfügbarkeit, keine Einzeltermine. Als Events würden sie den Kalender fluten. **Umsetzung (Q21, entschieden):**
- Neue Tabelle `partner_angebote` (Anbieter, externe ID, Titel, URL, Bild, „ab“-Preis, Bewertung, `ort_id`, `bestaetigt`, aktualisiert_am), gefüllt einmal je Scraper-Lauf über die APIs (nur Düsseldorf/Neuss/Ratingen). SQL legt RLS und Grants an, nach dem Muster von `database/auth_rollen.sql:147` und `database/admin_quellen_2026-11-24.sql:24–37`: anon liest nur Zeilen mit `bestaetigt = true`; `authenticated` liest und bestätigt über die Admin-Prüfung `ist_admin()`; Schreiben aus der Pipeline nur mit `service_role`. Ohne Policy wäre die Tabelle für die Website unsichtbar oder für jeden lesbar.
- **Ortsseiten** von Museen und Attraktionen (Kunstpalast, K20/K21, Aquazoo, Rheinturm …): Button „Tickets“, wenn ein Angebot dem Ort zugeordnet ist. Zuordnung über Name + Adresse als **Vorschlag im Admin-Bereich**, erst die Bestätigung schaltet den Button frei. Ablauf: Die Pipeline schreibt eine Zeile in `admin_vorschlaege` mit `art = 'partner_angebot'`, `schluessel` `anbieter:externe_id` (eindeutig über `UNIQUE (art, schluessel)`, `database/admin_grundlagen_2026-11-23.sql:63`) und im JSON `angebot_id`, vorgeschlagenes `ort_id`, Name und Adresse. Annehmen setzt `partner_angebote.ort_id` und `bestaetigt = true`. Ablehnen nutzt die bestehende Funktion `admin_vorschlag_ablehnen` und lässt `bestaetigt` falsch. Der Button erscheint nur bei `bestaetigt` und gesetzter `ort_id`. Eine unbekannte `art` wirft `admin_vorschlag_art_unbekannt` (`database/admin_vorschlaege_orte_2026-11-23.sql:136–137`). T3 ergänzt in `admin_vorschlag_annehmen` den Zweig `partner_angebot` (CREATE OR REPLACE, die Zweige dublette, gebiet, ortsname, ort_id und adresse bleiben) und einen Eintrag in `VORSCHLAG_ARTEN` (`web/lib/admin/vorschlaege.ts:3–9`).

- SQL `partner_angebote_<datum>.sql`, in derselben Datei wie der Funktionszweig: Spalten `id uuid`, `anbieter text`, `externe_id text`, `titel text`, `url text`, `bild_url text`, `preis_ab text`, `bewertung numeric`, `ort_id uuid`, `bestaetigt boolean default false`, `aktualisiert_am timestamptz`; `UNIQUE (anbieter, externe_id)`; Index auf `ort_id` nur wo `bestaetigt`; RLS und Grants wie oben; am Ende `NOTIFY pgrst, 'reload schema'`.
- **Stadtführungen** (Kategorie `stadtfuehrung`, Guide-Seite): Block „Führungen buchen“ mit bis zu 6 GetYourGuide-/Tiqets-Touren in Düsseldorf, nach Bewertung.
- Bilder aus den APIs nur, wenn die Bedingungen das erlauben – sonst ohne Bild, und keine Kopie unter `web/public`. Tiqets: Bilder nur auf Antrag (5.4), bis zur schriftlichen Freigabe `bild_url` leer. GetYourGuide genauso, solange die Bildregel ungeprüft ist (5.4). Ticketmaster setzt `bild_url` nicht, solange die schriftliche Bestätigung aus 5.5.1 die Bildnutzung nicht ausdrücklich einschließt (die Bedingungen verbieten, Ticketmaster als Bild-Host zu nutzen, 5.1; unser Bild-Proxy `web/app/bild` holt und liefert Bilder aus). Die Anfrage in `docs/partner-anfragen-2026-11-24.md` fragt deshalb gezielt danach. **Achtung:** `scraper/tier1/ticketmaster.py` setzt heute `bild_url` (`_bild_url_ermitteln`, ab `:32`); T1 stellt das ab, bis die Bestätigung da ist.

#### 5.5.5 Website

- **`web/lib/tickets.ts`:** erkennt den Anbieter an der Domain (eventim.de, reservix.de, adticket.de, ticketmaster.de, tiqets.com, getyourguide.de) und baut den Partner-Link aus den Variablen. Schalter **`PARTNERLINKS_AKTIV`** als GitHub-Variable wie `KONTEN_AKTIV` (wirkt mit dem nächsten Deploy). Der Admin zeigt Schalter nur aus der festen Liste `SCHALTER` (`web/lib/admin/github.ts:92`) mit Texten in `web/app/admin/technik/ansicht.tsx:19–25`. P2 trägt `PARTNERLINKS_AKTIV` dort ein, sonst erscheint er nicht. Aus oder fehlende Variable = normale Links ohne Partner-Kennung. **Ticketmaster bleibt zusätzlich außen vor**, bis die schriftliche Bestätigung aus 5.5.1 da ist (eigene Variable `TICKETMASTER_PARTNER_OK` oder eine Domänen-Allowlist, Standard aus). Ein globaler Schalter allein würde Ticketmaster-Links zu früh umbauen (Abschnitt 9).
- **Kennzeichnung** direkt am Button: „Tickets*“ und darunter klein „*Partner-Link: Kaufst du darüber, bekommen wir eine Provision. Der Preis bleibt gleich.“ (du-Ansprache wie auf den Konto-Seiten). Dazu ein Abschnitt „Partner-Links“ auf `/ueber` (Anker `#partner-links`).
- Partner-Links mit `rel="sponsored noopener"`. Der heutige Haupt-Button hat nur `rel="noopener"` (`page.tsx:283`). JSON-LD behält die echte URL ohne Partner-Umleitung: `offers.url` ist heute `quelle_url` (`web/lib/json-ld.ts:109–113`) und wird, wenn vorhanden, die rohe `ticket_url`. Die Partner-URL steht nur im Button.
- **Kein eigenes Klick-Tracking**, keine Cookies bei uns; Auswertung in den Netzwerk-Konten (Awin, Impact, Tiqets, GetYourGuide).
- **Datenschutzerklärung** (Sie-Form, Datei `web/app/datenschutz/page.tsx`): neuer Abschnitt zu den Partnerprogrammen (wer den Link setzt, dass der Anbieter nach dem Klick selbst Cookies setzen kann, keine eigenen Tracking-Cookies bei uns). Entwurf von Claude, Freigabe durch den Anwalt **vor** `PARTNERLINKS_AKTIV=1`. Kennzeichnungstext ebenfalls zum Anwalt. Das Impressum benennt die redaktionelle Verantwortung schon (`web/app/impressum/page.tsx:78`, § 18 Abs. 2 MStV) und bekommt keinen Partner-Abschnitt. Die Kennzeichnung sitzt am Button, auf `/ueber` (`#partner-links`) und in der Datenschutzerklärung. Die Button-Auswahl nach Offiziellität (5.5.3) bleibt die redaktionelle Regel und hängt nicht an der Provision.

---

## 6. Website: wo der längere Zeitraum sichtbar wird

### 6.1 Grundsatz (Q8)

Der bestehende Pool `eventPoolLaden()` bleibt bei **60 Tagen**. Alles, was „was ist bald los“ zeigt, ändert sich nicht. Für den längeren Zeitraum kommt ein **zweiter, schlanker Pool** dazu: `fernPoolLaden()` in `web/lib/daten.ts` – **Tag 61 bis 365** (Tag 60 bleibt nur im Nah-Pool), gleiche Spalten und `normalisieren()`, dazu `kategorie is not null` (5.3, unfertige Einträge nicht im Ausblick), eigenes `"use cache"` mit `cacheTag(EVENTS_CACHE_TAG)` (der Admin-Bereich leert ihn mit). Erwartete Größe nach dem Ausbau: 2.000–4.000 Termine, also 2–4 Seiten à 1.000. Die Seite `/ausblick` und die Startbox filtern daraus zusätzlich Rang 1–2 und Orte mit Ortsseite. Die Suche auf `/entdecken` nutzt den Fernpool ohne diesen Rang-Filter.

| Stelle | Zeitraum | Änderung |
|---|---|---|
| Startseite, Tagesleiste, Wochenende, Kostenlos, Kategorie-/Stadtteilseiten, Tagesplaner | **60 Tage** | keine |
| Empfehlungen (Admin, Fokustag, Top/Highlight) | **60 Tage** | keine (`admin/empfehlungen.ts:51` bleibt) |
| Magazin-Pool | wie heute | keine |
| **Eventseite** | **unbegrenzt** | `eventLaden()` lädt das Event einzeln nach; neu: Monats-Label („MÄRZ 2027“) bei Events > 60 Tage, Ticket-Link (6.3). „Weitere Events an diesem Ort“ und „ähnliche Events“ lesen heute nur den 60-Tage-Pool (`page.tsx:81–88`). Liegt das Event hinter Tag 60, kommen diese beiden Blöcke aus dem Fernpool, sonst bliebe die Seite ohne Nachbarn. |
| **Ortsseiten** (`/orte/…`, Clubs, Kneipen) | **unbegrenzt** | lädt schon über `ort_id`; neu: Liste nach Monat gruppiert, ab Tag 61 eingeklappt „Ausblick (n)“. Die Ortsseite zeigt heute höchstens 60 Karten und zählt den Rest nur (`web/app/orte/[slug]/page.tsx:175–180`). Der Guide-Block `OrtProgramm` zeigt 10 (`web/components/ort-programm.tsx:12`). Die 60 bzw. 10 gelten für die nahen Termine; der Ausblick ist der eingeklappte Rest und wird nicht von der Kappung verschluckt. |
| **/entdecken – Suche** (`?q=`) | **12 Monate** | Treffer aus dem Fernpool als eigener Block „Ausblick“ unter den normalen Treffern |
| **/entdecken – eigener Zeitraum** | **12 Monate** | `MAX_ZEITRAUM_TAGE` 60 → 366 (`web/lib/datum.ts:129`); liegt der Zeitraum ganz oder teilweise hinter Tag 60, kommen die Events aus dem Fernpool dazu. Der Preset „alle“ bleibt „60 Tage“ (`datum.ts:166–167`) und wird nicht mitgezogen. |
| **Neue Seite „Ausblick“** (Q9, `/ausblick`) | **Tag 61–365** | Liste nach Monaten, Filter Kategorie; nur Quellen Rang 1–2 und Orte mit Ortsseite (keine Kleinst-Events) |
| Startseite – neue Box | Teaser | Q10: kleine Box „Große Events später im Jahr“ (6 Einträge, Rang 1–2, nach Datum) mit Link auf die neue Seite |
| **Sitemap** | **12 Monate** | Eventseiten aus dem Fernpool aufnehmen (sonst findet Google die fernen Events nicht). Tagesseiten in der Sitemap sind heute **14**, nicht 60 (`web/app/sitemap.ts:93–96`). Das bleibt. Der Fernpool hängt am selben `cacheTag(EVENTS_CACHE_TAG)` (`daten.ts:12`, `eventPoolLaden` bei `:239`), damit der Admin beide Pools leert. Einige Tausend Event-URLs bleiben unter der Sitemap-Grenze von 50.000. |
| `/api/events`, Konto (Merkliste, „Für dich“), Geburtstags-Tipps | 60 Tage | keine; die Merkliste lädt gemerkte Events schon einzeln |

Nicht geändert wird die Tagesleiste: Sie springt heute schon bis 366 Tage, wenn ein ferner Tag gewählt ist (`datum.ts:37–39`, höchstens 366). Die Tagesseite `/tag/<datum>` hinter Tag 60 bleibt leer, solange sie den 60-Tage-Pool nutzt. **Entschieden mit Q8:** `/tag/<datum>` hinter Tag 60 nutzt den Fernpool. In der Sitemap stehen Tagesseiten weiter nur die nächsten 14 (`sitemap.ts:93`). Eine ferne Tagesseite, die jemand verlinkt, ist heute indexierbar und leer: `app/tag/[datum]/page.tsx:17` setzt `noindex` nur für vergangene Tage. Sobald der Fernpool Termine für den Tag hat, ist die Seite zu Recht indexierbar; ohne Termine setzt sie `noindex`. `/ausblick` braucht keinen 404 oder 308 aus dem Proxy. Die Bremse gegen Massenabrufe gilt heute nur für `/guides` (`web/proxy.ts:67`; der Ausfall vom 23.11. ist in `web/lib/bremse.ts:1–3` und `proxy.ts:65–66` beschrieben). Ein Eintrag nur im Matcher (`proxy.ts:146–156`) bremst die Seite nicht. W2 nimmt `/ausblick` in dieselbe Bedingung auf. Der Fernpool hat eigenes `"use cache"`. Schlägt das Laden fehl, liefert `fernPoolLaden()` eine leere Liste und keinen Beispielbestand: `eventPoolLaden()` fällt bei einem Fehler auf Beispieldaten zurück (`web/lib/daten.ts:247–251`), der Ausblick und die Sitemap dürfen das nicht. Die Seite ruft `seitenMetadaten` mit Pfad `/ausblick` auf (`web/lib/seo.ts:109`, Canonical über `seitenAlternates`, solange nicht `noindex`). Die Sitemap nimmt `/ausblick` in die festen Seiten auf (`web/app/sitemap.ts:81–91`). Der Link steht bei den Event-Links in `web/components/rahmen.tsx:66–67`, nicht nur im Fließtext. Monatsseiten (Q18) kommen später und dann mit eigener Regel, inklusive Bremse. Im Admin-Plan steht zum Jail „ohne `ps`“ (`docs/plan-admin-dashboard-2026-11-23.md:14`). Eine Speichergrenze oder ein `/proc`-Verbot steht im Website-Code nicht; deshalb keine Byte-Zahl für den Fernpool, sondern schlanke Spalten, eigener Cache und die Bremse.

### 6.2 Kennzeichnung

Events > 60 Tage zeigen auf Karten und Eventseite ein kleines Label mit Monat und Jahr (**„MÄRZ 2027“**, Q11), damit niemand sie für morgen hält.

### 6.3 Quell-Link auf der Eventseite (`web/app/event/[kategorie]/[slug]/page.tsx:282–300`)

- Haupt-Button → `quelle_url` (ist nach Abschnitt 4 immer die beste Quelle). Text wie heute: „Zum Termin um … Uhr“ oder „Zur Veranstalter-Seite“ (`page.tsx:282–286`), bei abgelaufenen Events der schlichte Link (`:289–292`).
- **Neu:** zweiter Button „Tickets*“ nach den Regeln in 5.5.3 (`ticket_url` des Hauses, sonst Rang-2-Quelle aus `quellen`). Ohne beide Angaben entfällt der Button. Karten, Merkliste, Konto, Geburtstagsmail und Magazin verlinken auf die Eventseite (`eventPfad`), nicht auf `quelle_url`. Partner-Links entstehen dort nicht. Einzige weitere Kauf-URL ist `offers.url` im JSON-LD (5.5.5), und die bleibt ohne Partner-Umleitung.
- Rausgegangen-Events: siehe 4.4.
- „Quelle: …“ bleibt wie heute die Hauptquelle.
- Partner-Links, Kennzeichnung und Datenschutz: 5.5.5.

### 6.4 Name der neuen Seite (Q9, zweite Runde)

Die bestehenden Adressen sind kurze deutsche Zeitwörter: `/heute`, `/morgen`, `/wochenende`, `/kostenlos`. **Q9 ist entschieden: „Ausblick“ unter `/ausblick`.** Die übrigen Zeilen sind die verworfenen Vorschläge der zweiten Runde und werden nicht gebaut. Alle genannten Adressen waren am 24.11. frei; vor W2 wird das noch einmal im Repo geprüft (`/vormerken`, `/highlights` und die anderen dürfen bis dahin nicht belegt worden sein).

| Vorschlag | Adresse | Seitentitel (SEO) | Für | Gegen |
|---|---|---|---|---|
| **Ausblick** (entschieden) | `/ausblick` | „Ausblick: Große Events in Düsseldorf bis <Monat Jahr>“ | kurz, neutral, passt zu heute/morgen/wochenende; sagt „weiter weg“ ohne Kaufdruck | etwas nüchtern |
| Vormerken | `/vormerken` | „Jetzt vormerken: Konzerte, Shows und Highlights in Düsseldorf“ | Handlungsaufforderung, passt zum Merken-Button | Verwechslung mit der Merkliste möglich |
| Demnächst | `/demnaechst` | „Demnächst in Düsseldorf“ | geläufig (Kino-Sprache) | klingt nach „bald“, gemeint sind Monate |
| Jahresvorschau | `/jahresvorschau` | „Jahresvorschau Düsseldorf: die großen Events der nächsten 12 Monate“ | eindeutig, gute Suchbegriffe | lang; „Vorschau“ gibt es schon im Magazin |
| Save the Date | `/save-the-date` | „Save the Date: Düsseldorfs große Events“ | bekannt, locker | englisch, die übrigen Adressen sind deutsch |
| Highlights | `/highlights` | „Highlights in Düsseldorf: was die nächsten Monate bringen“ | griffig | Highlight ist schon eine Empfehlungsstufe auf der Startseite |

Ergänzend für Google (unabhängig vom Namen): Unterseiten je Monat (`/ausblick/2027-03`, Titel „Events in Düsseldorf im März 2027“) – danach wird viel gesucht. **Q18 entschieden:** erst die Hauptseite, Monatsseiten später, wenn genug Fern-Events da sind.

Label auf Karten (Q11) passt sich an: bei „Ausblick“ statt „Vorverkauf“ einfach das Monatskürzel groß („MÄRZ 2027“) – das erklärt sich selbst.

---

## 7. Umsetzungsschritte und Freigaben

Jeder Schritt: lokal bauen und testen → Zusammenfassung → OK des Auftraggebers → Push aus einem temporären Worktree, der von `origin/claude/setup-project-structure-5QNOf` abzweigt → nächster Scraper-Lauf im Admin-Scraper-Tab bzw. Log prüfen. SQL jeweils **vor** dem Deploy des Schritts.

| Nr. | Inhalt | SQL | Prüfung nach Deploy |
|---|---|---|---|
| **A1** | **Auftraggeber:** Anmeldungen bei Awin (Eventim, Reservix, ADticket), Impact (Ticketmaster), Tiqets, GetYourGuide; Anfragen an Ticketmaster und Reservix senden (Texte von Claude) – läuft parallel ab Freigabe | – | Variablen/Secrets in GitHub |
| **R1** | Rangfolge `pipeline/quellen_rang.py`; Deduplizierung, Speichern, Dubletten-Vorschläge auf Rang umstellen (4.1, 4.2) | – | Lauf-Log: „Quelle gewechselt: A → B“ jetzt auch zwischen Nicht-Rausgegangen-Quellen; Stichprobe 10 Events |
| **R2** | Spalte `events.quellen`, Kennzahlen „nur Rausgegangen“ und „Lücken je Ort“ im Lauf-Report, W7 (4.3, 4.5) | `quellen_spalte_<datum>.sql` (inkl. drei Spalten in `scraper_laeufe`) | Kennzahlen im Report plausibel |
| **Z1** | Zeitraum je Quelle (`vorschau_ende`, 5.2). Oper und Schauspielhaus lesen heute 2 bzw. 6 Monate; Z1 zieht sie auf das 365-Tage-Fenster. RA bleibt bei 5 Seiten. Ticketmaster-Blättern ist T1. Dazu Beschreibungen auf Tag ≤ 60 + Fern-Block 100, Kategorisierungs-Limit befristet 1.500, Captions und Publisher auf Tag ≤ 60, Club-Prompt auf +60 (5.3). `VORSCHAU_NOTAUS` in den Workflow (Rückweg) | – | Abnahme Laufzeit unten: Dauer unter 240 Minuten. Events > 60 Tage je Quelle, kein Instagram-Post eines Fern-Events |
| **T1** | Ticketing (5.1): Ticketmaster (Secret vom Auftraggeber, Workflow-`env`, Monatsfenster bis 12 Monate), Songkick aus `QUELLEN` nehmen, Stagedates über Sitemap + JSON-LD. Ticketmaster ohne `bild_url` bis zur Bild-Bestätigung (5.5.4). Stagedates erst in `QUELLEN`, nachdem die Nutzungsbedingungen gelesen sind; widersprechen sie dem Abruf, Rückfrage, nicht still weglassen (Q6 bleibt ja) | – | Events je Quelle, Gebietsfilter, Dubletten zu d.live/Mitsubishi/Capitol, Stichprobe `bild_url` leer |
| **W1** | Website: Fernpool, Suche und eigener Zeitraum bis 12 Monate, Ortsseiten nach Monaten, Monats-Label, Sitemap, `/tag` > 60 (6.1, 6.2) | – | Seiten im Browser, Sitemap-Größe, Ladezeit Startseite unverändert |
| **V0** | Bestehende Quellen mit großer Wirkung reparieren/erweitern: Kunstsammlung (Führungen/Veranstaltungen), VisitDüsseldorf komplett über Sitemap/Toubiz (3.2, nicht ein eigener Abschnitt 3.4) | – | Events je Quelle vorher/nachher |
| **V1** | Bausteine (3.3) + Welle A der Venues (3.2) | – | je Haus Eventzahl > 0, Ortszuordnung trifft, und dieselbe Laufzeit-Abnahme wie Z1 |
| **P1** | `events.ticket_url`: Venue-Scraper erfassen den Ticket-Link des Hauses (bestehende + Welle A), Rangwechsel behält ihn (5.5.2) | `ticket_url_<datum>.sql` | Anteil Events mit Ticket-Link je Anbieter |
| **N1** | `quellen_nachziehen.py`: Bestand auf Rang umhängen – Probelauf, dann `--schreiben` | – (Sicherung im Skript) | Bericht |
| **W2** | Seite „Ausblick“ (`/ausblick`), Startseiten-Box, Ticket-Button (Partner-Link vorbereitet, aus), Link „Website von <Ort>“ (6.1, 6.3, 4.4) | – | Seiten im Browser |
| **P2** | Partner-Links: `web/lib/tickets.ts`, Kennzeichnung, Abschnitt auf `/ueber`, Datenschutz-Entwurf → Anwalt → Variable `PARTNERLINKS_AKTIV=1` + Deploy (5.5.5). Ticketmaster-Domain erst mit der schriftlichen Bestätigung. Schalter in `SCHALTER` und in der Technik-Ansicht | – | Links im Browser (Partner-Kennung, `rel=sponsored`), Ticketmaster-Link ohne Bestätigung noch ohne Partner-Kennung, Netzwerk-Konten zeigen Klicks |
| **T2** | Reservix-API und Eventim-Feed als Rang-2-Quellen – sobald A1 Zugang liefert (5.5.2) | – | Events je Quelle, Dubletten |
| **T3** | Tiqets/GetYourGuide: Tabelle `partner_angebote`, Abruf je Lauf, Zuordnungs-Vorschläge im Admin, Buttons auf Ortsseiten, Block im Stadtführungs-Guide (5.5.4) | `partner_angebote_<datum>.sql` | Angebote je Ort, Vorschläge |
| **V2** | Welle B (Düsseldorf, Neuss, Ratingen; 3.2) | – | wie V1 |

Cursor-Prüfungen: Plan (Anhang A) vor der Freigabe; Umsetzung nach R1+R2 (Pipeline-Kern), nach W1+W2 (Website) und nach P2 (Partner-Links, vor dem Einschalten).

Parallel möglich: V0/V1 (neue Scraper-Dateien) berühren andere Dateien als R1/R2 (Pipeline-Kern) und W1/W2 (Website). Z1 fasst alle Scraper-Dateien an und läuft deshalb **nicht** parallel zu V0/V1. A1 (Anmeldungen des Auftraggebers) läuft ab Freigabe nebenher; T1, T2, T3 und das Einschalten von P2 warten jeweils auf den passenden Zugang. P1 baut auf V1 auf (dieselben Scraper-Dateien), P2 auf W2 (Ticket-Button).

### SQL vor dem Deploy

Nur diese drei Dateien. Jede endet mit `NOTIFY pgrst, 'reload schema'`. Der Auftraggeber führt sie im SQL-Editor aus, bevor der zugehörige Schritt deployed wird.

| Schritt | Datei | Inhalt |
|---|---|---|
| **R2** | `database/quellen_spalte_<datum>.sql` | `events.quellen jsonb` plus Vorbelegung; `scraper_laeufe.kuenftige_events`, `nur_rausgegangen`, `luecken` (4.3) |
| **P1** | `database/ticket_url_<datum>.sql` | `events.ticket_url text` (5.5.2) |
| **T3** | `database/partner_angebote_<datum>.sql` | Tabelle, Unique, Index, RLS, Grants und der Zweig `partner_angebot` in `admin_vorschlag_annehmen` (5.5.4) |

R1, Z1, T1, W1, V0, V1, N1, W2, P2, T2 und V2 haben kein SQL. Eine neue Quelle braucht keine Zeile in `quellen_einstellungen`, solange sie an bleiben soll.

### Abnahme der Laufzeit (Z1 und V1)

Das ist die Abnahme der beiden Schritte, nicht ein Kriterium für die Freigabe dieses Plans.

Gemessen wird `beendet_am` minus `gestartet_am` in `scraper_laeufe` (`database/scraper_report.sql:16–17`). Die Schrittzeiten, vor allem Schritt 3b, stehen im Workflow-Log, nicht als eigene Spalte. Bestanden ist die Abnahme, wenn `status = erfolgreich` ist und die Dauer **unter 240 Minuten** liegt. Der Job bricht bei `timeout-minutes: 240` ab (`scrape.yml:44`). Das Timeout wird in diesem Plan nicht angehoben.

Reißt es (der Job wird abgebrochen, `beendet_am` bleibt leer, `status` bleibt `laeuft`): `VORSCHAU_NOTAUS=1` setzen und keine weitere Venue-Welle starten, bis ein Lauf wieder unter 240 Minuten mit `erfolgreich` endet.

W5 „läuft seit über 90 Minuten“ (`web/lib/admin/warnregeln.ts:38`, Meldung `:61–62`) leuchtet während eines gesunden langen Laufs mit, weil der Status bis zum Schluss `laeuft` ist. Das ist nicht die Abnahme.

### Rückweg

SQL-Spalten bleiben liegen; abgeschaltet wird der Code, der sie füllt oder zeigt.

- **Neue Quelle:** im Admin unter „Quellen an/aus“, Schlüssel ist der Anzeigename (`pipeline/quellen.py:21`). Der Lauf schreibt dann `uebersprungen` und startet den Scraper nicht.
- **R1** hat keinen Schalter. Rückweg ist der Commit zurück. Bis dahin schreibt der Rang. `ort_id` wird dabei nicht ersetzt (4.2).
- **Z1:** Die Variable `VORSCHAU_NOTAUS=1` lässt `vorschau_ende` für alle Quellen bei Tag 60 aufhören. Nicht gesetzt oder ein anderer Wert ist aus. Damit sie im Lauf ankommt, trägt Z1 sie in `.github/workflows/scrape.yml` in den `env`-Block des Schritts „Pipeline ausführen“ ein (`VORSCHAU_NOTAUS: ${{ vars.VORSCHAU_NOTAUS }}`, wie `ORTSSEITEN_MELDEN` in `scrape.yml:100`). `web/lib/admin/github.ts` nimmt sie in `SCHALTER` auf (`:92`), und `web/app/admin/technik/ansicht.tsx` bekommt einen Text in `SCHALTER_TEXT` (`:19–25`). Ohne den Text zeigt das Panel den Roh-Namen, weil der Fallback nur der Variablenname ist (`:87`). Ohne Eintrag im Workflow wäre der Notaus wirkungslos. Wirksam wird er beim nächsten Pipeline-Lauf, nicht beim Deploy der Website. Captions, Publisher und der Club-Prompt bleiben ohnehin bei Tag 60.
- **W1 und W2:** Fernpool und `/ausblick` sind eigener Code. Rückweg ist der Commit zurück. Die Startseite liest den Fernpool nur in der Box aus W2.
- **P2:** `PARTNERLINKS_AKTIV` fehlt oder ist 0, und `TICKETMASTER_PARTNER_OK` fehlt. Dann sind die Links normal, die Spalte `ticket_url` bleibt.
- **Kommt ein Partner-Zugang nie:** T1 überspringt Ticketmaster ohne Secret, wie heute. T2 und T3 werden nicht gebaut. P2 bleibt aus. P1 speichert den Ticket-Link des Hauses weiter als normalen Link. V0, V1, R1, R2, Z1, W1 und W2 warten nicht auf A1.

---

## 8. Tests

Python mit `unittest` (wie bisher; pytest kommt nicht dazu), Website mit dem bestehenden Test-Runner in `web/tests/`.

- **Rang (R1):** jeder Anzeigename aus `main.py` `QUELLEN` hat einen Rang; Rausgegangen per Name und per URL Rang 5; Tier 2/3 ohne Eintrag → 1. Jede `QUELLE_NAME`-Konstante steht in der zweiten Tabelle mit demselben Rang wie der Anzeigename. Ein gespeicherter Name, der in keiner der beiden Tabellen steht, hat Rang 3. Der Rang fürs Speichern wird vor dem Entfernen der `_`-Felder berechnet und als Argument übergeben; `datensatz` enthält `_scraper` nicht (`database/client.py:316–320` und `:391–392`).
- **Merge (R1):** Paare Haus/Ticketmaster, Ticketmaster/PRINZ, PRINZ/Rausgegangen, Haus/Rausgegangen in beiden Reihenfolgen → Basis ist immer der bessere Rang; gleicher Rang → erste Quelle; Uhrzeit des Hauses gewinnt; leere Werte überschreiben nie; Bild der Rang-2-Quelle bleibt, wenn das Haus keines hat.
- **Speichern (R1):** `_anreicherungs_update_bauen` mit gespeichertem PRINZ-Event und eingehendem Haus-Event → Quellenwechsel; umgekehrt keiner; `redaktion_felder` und `beschreibung_quelle` bleiben geschützt (bestehende Tests erweitern).
- **Dubletten (R1):** `paare_finden` behält den besseren Rang.
- **Quellenliste (R2):** neue Quelle wird angehängt, gleiche Quelle aktualisiert `zuletzt`, höchstens ein Eintrag je Name. W7 zählt eine Lücke nicht, wenn die Rang-1-Quelle abgeschaltet oder saisonal ist. Die Fixture `tests/fixtures/lauf_warnungen.json` enthält `luecken`; ohne die Spalte im Select entsteht keine W7-Warnung.
- **Zeitraum (Z1):** `vorschau_ende` je Gruppe (365 / 120 / 60, unbekannter Tier-2-Name = 120). `Classic Remise` und `Street Food Thursday Düsseldorf` haben dasselbe Fenster wie der Anzeigename. Struktur-Test: kein Scraper rechnet das Fenster mehr selbst. `VORSCHAU_NOTAUS=1` liefert für jede Quelle Tag 60; fehlt die Zeile im `env`-Block von `scrape.yml`, gilt der Test als fehlgeschlagen. Captions und Publisher lassen ein Event hinter Tag 60 aus. Der Club-Prompt enthält keine Zeile hinter Tag 60.
- **Bausteine (V1):** JSON-LD mit `@graph`, `subEvent`, fehlender Uhrzeit, Zeitzone; Tribe-API-Antwort mit zwei Seiten; iCal mit Ganztags-Termin und wöchentlicher RRULE. Beispieldateien unter `tests/fixtures/`.
- Bestehende Tests, die angepasst werden: `tests/test_rausgegangen_vorrang.py`, `test_dedup_aehnlich.py`, `test_dedup_toleranz.py`, `test_redaktion_feldschutz.py`, `test_lauf_report_kennzahlen.py`.
- **Website (W1/W2):** Zeitraum > 60 Tage wird nicht mehr auf 60 gekürzt, aber auf 366; der Preset „alle“ heißt weiter „60 Tage“. Der Fernpool beginnt bei Tag 61 und lässt `kategorie is null` weg. Suche findet ein Fern-Event im eigenen Block; Startseite enthält kein Event > 60 Tage außer in der neuen Box; Monats-Label ab Tag 61. Der Ticket-Button heißt „Tickets*“. Ortsseite und `OrtProgramm` kappen nur die nahen Termine, der Ausblick bleibt. Eine Tagesseite hinter Tag 60 ohne Termine ist `noindex`. Sitemap-Tage bleiben 14, `/ausblick` steht bei den festen Seiten, Event-URLs kommen aus dem Fernpool. `seitenMetadaten` für `/ausblick` setzt einen Canonical auf `/ausblick`. Ein Ladefehler des Fernpools liefert eine leere Liste, keine Beispieldaten. Die Bremse in `proxy.ts` gilt auch für `/ausblick`.
- **Ticket-Link (P1):** Rangwechsel ohne `ticket_url` der neuen Quelle behält den alten; Venue-Fixtures liefern den Ticket-Link.
- **Partner-Links (P2, `web/tests/`):** je Anbieter-Domain der richtige Partner-Link (Awin-Deeplink mit korrekt kodierter Ziel-URL, Tiqets/GetYourGuide mit Partner-Kennung); unbekannte Domain bleibt unverändert; Schalter aus oder fehlende ID → normaler Link; Ticketmaster ohne `TICKETMASTER_PARTNER_OK` bleibt ein normaler Link, auch wenn `PARTNERLINKS_AKTIV=1`; jeder Partner-Link hat `rel="sponsored noopener"` und den Hinweistext; JSON-LD `offers.url` enthält die Partner-URL nicht; Ticket-Button-Auswahl nach 5.5.3 (Haus-Link vor Rang-2-Quelle, nie zwei Buttons); keine Partner-Links in Magazin-Beiträgen, Karten, Merkliste und Mails.
- **Partner-Angebote (T3):** Abruf mit Beispielantworten aus `tests/fixtures/`; nur bestätigte Zuordnungen mit `ort_id` erzeugen einen Button. `admin_vorschlag_annehmen` mit `art = 'partner_angebot'` setzt `bestaetigt`; eine unbekannte Art wirft weiter.
- **Ticketmaster (T1):** eine Beispielantwort mit Bildern ergibt `bild_url` leer, solange die schriftliche Bild-Bestätigung fehlt (`scraper/tier1/ticketmaster.py:32` und `:202` setzen sie heute). Songkick steht danach nicht mehr in `QUELLEN`.

---

## 9. Risiken

- **Mehr Dubletten** durch Ticketing (andere Titel-Schreibweisen: „KÜNSTLER – Tour 2027 – Düsseldorf, Halle“). Gegenmittel: `_bandname_enthalten` deckt viele Fälle; Prüfung nach T1; Dubletten-Vorschläge im Admin-Bereich.
- **Laufzeit:** Beschreibungen waren im Lauf vom 21.11. bei 2 h 28 min. Das Timeout steht auf 240 Minuten (`scrape.yml:44`). Ohne das Datumsfenster (Q14) und ohne die Datumsgrenze bei Captions und Publisher würde der Lauf das Timeout reißen oder ferne Events auf Instagram posten. Die 100 Fern-Beschreibungen liegen im bestehenden Budget von 5400 Sekunden (5.3), V0 und V1 erhöhen es nicht.
- **Kennzahlen-Update:** Eine fehlende Spalte verwirft alle Kennzahlen des Laufs, nicht nur die neue (`pipeline/lauf_report.py:208–213`). Das SQL von R2 inklusive `NOTIFY` läuft vor dem Deploy (4.3).
- **Fernpool:** `/ausblick` liegt heute nicht unter der Guide-Bremse (`web/proxy.ts:67`). W2 nimmt die Seite dort auf. Bei einem Ladefehler keine Beispieldaten (6.1).
- **Venue-Scraper veralten** (Relaunch, neue Struktur): Bausteine warnen bei 0 Treffern; Warnregeln W1/W2 im Admin-Scraper-Tab.
- **Rechtliches:** Nur öffentlich frei zugängliche Termindaten, robots.txt beachtet; Beschreibungen werden wie bisher in eigenen Worten geschrieben, Bilder nur aus der Quelle mit Herkunft. Ticketing-Bedingungen (Attribution, Bildnutzung, Speicherdauer) je Anbieter beachten (5.1).
- **Falsche Rangfolge in Einzelfällen** (z. B. ein Haus-Scraper mit schlechteren Daten als Ticketmaster): leere Felder überschreiben nie; Redaktion kann Felder im Admin-Bereich festsetzen (`redaktion_felder`).
- **Öffentliches Repository:** Zugangsdaten nur als GitHub-Secrets; Ortslisten und Venue-Tabellen sind unkritisch.
- **Partner-Links abmahnfähig:** falsche oder fehlende Kennzeichnung ist ein Wettbewerbsverstoß. Gegenmittel: Kennzeichnung direkt am Button, Erklärseite, Anwalts-Freigabe vor `PARTNERLINKS_AKTIV=1`.
- **Ticketmaster-Bedingungen:** ohne schriftliche Bestätigung (5.5.1) keine Partner-Links auf Ticketmaster-Daten, auch nicht wenn `PARTNERLINKS_AKTIV` schon 1 ist. Der Ticketmaster-Link bleibt dann ein normaler Link. Die API-Formulierung zu Einnahmen ist in Runde 1 nicht erneut gelesen.
- **Awin-Bedingungen:** kein Preisvergleich, keine Suchmaschinen-Anzeigen auf die Marke; Eventim zahlt nur bei Kauf am selben Tag (Cookie 1 Tag) – Erwartung an die Einnahmen niedrig halten.
- **Glaubwürdigkeit:** Button-Auswahl nach Offiziellkeit (Q20), keine Partner-Links im Magazin (Q22), keine Empfehlung wegen Provision (Empfehlungs-Logik bleibt unverändert).

---

## 10. Offene Fragen an den Auftraggeber

Antworten des Auftraggebers vom 24.11.2026:

1. **Einnahmen / Provision (Q6-a):** Rückfrage des Auftraggebers – bei welchen Anbietern lassen sich über ein Partnerprogramm Provisionen erzielen? → Recherche in 5.4.
2. **Ticketmaster-Schlüssel:** reicht der Auftraggeber nach. Bis dahin bleibt T1 für Ticketmaster offen; Stagedates und die Songkick-Abschaltung gehen ohne Schlüssel.
3. **Eventim/Reservix-Anfrage (Q6-b):** zunächst „vorerst nicht“, dann (24.11., zweite Antwort): **alle genannten Partner anbinden** → 5.5, Schritte A1, P1, T2, T3, P2.
4. **Name der neuen Seite (Q9):** „Später im Jahr“ und „Vorverkauf“ gefallen nicht. Entschieden ist **Ausblick** `/ausblick` (6.4). Die anderen Namen dort sind die verworfene Liste, keine offene Wahl.
5. **Prioritäten bei den Häusern (Q15, Neuss/Ratingen):** keine besonderen Wünsche; Auswahl und Reihenfolge wie in 3.2 vorgeschlagen.

---

## Anhang A: Prüfliste für die Cursor-Runden

Die Prüfschleife steht in Anhang B. Diese Liste ist der Mindestumfang der ersten Runde.

```
Prüfe mindestens:
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
   Zusammenspiel mit dem inzwischen kompletten Admin-Bereich docs/plan-admin-dashboard-2026-11-23.md:
   Feldschutz, Vorschläge, „Quellen an/aus“ aus Stufe 5b).

```

## Anhang B: Prüfschleife Cursor ↔ Claude (ab 24.11.2026)

Ablauf (Wunsch des Auftraggebers vom 24.11.): Cursor prüft den kompletten Plan kritisch gegen den Code und **ändert den Plan selbst**. Danach meldet Cursor die Änderungen, der Auftraggeber gibt die Meldung an Claude weiter, Claude prüft jede Änderung gegen den Code und nimmt sie an, passt sie an oder nimmt sie mit Begründung zurück. Das geht hin und her, bis eine Runde keine kritischen und keine mittleren Befunde mehr ergibt und beide Seiten zustimmen.

Regeln für beide Seiten:
- Arbeitsordner ist der Worktree `C:\Claude_DDD\DD-quellen` (Branch `claude/plan-quellen-ausbau`, auf dem Stand von origin). Den Hauptordner `C:\Claude_DDD\DD` nicht anfassen; dort liegen offene Änderungen anderer Sessions.
- Geändert werden nur diese Plan-Datei und `docs/partner-anfragen-2026-11-24.md`. Kein Code, kein SQL ausführen, kein Commit, kein Push. Claude committet nach seiner Prüfung, gepusht wird erst mit OK des Auftraggebers.
- Die Entscheidungen Q1–Q22 hat der Auftraggeber getroffen. Sie werden nicht still geändert. Trägt eine technisch nicht, kommt sie als „Rückfrage an den Auftraggeber“ in die Runde.
- Jede Tatsachenbehauptung über den Code mit `Datei:Zeile` belegen. Keine Zahlen erfinden; Unbekanntes als offen kennzeichnen.
- Sprache: Deutsch, Projektbegriffe wie im Plan, „Button“ statt „Knopf“, Nutzertexte per du, Datenschutzerklärung per Sie.

Protokoll je Runde (wird unten angehängt):

| Runde | Wer | Nr. | Schweregrad | Abschnitt | Befund | Änderung im Plan | Status |
|---|---|---|---|---|---|---|---|

Status-Werte: `geändert` (Cursor) · `angenommen` / `angepasst` / `zurückgenommen` (Claude, mit Begründung) · `Rückfrage Auftraggeber`.

### Runden

| Runde | Wer | Nr. | Schweregrad | Abschnitt | Befund | Änderung im Plan | Status |
|---|---|---|---|---|---|---|---|
| 1 | Cursor | 1 | kritisch | 3.3 | Eine gemeinsame `scrape()` ist im Lauf-Report eine Quelle. `scraper_ausfuehren` setzt einen Namen und einen Status (`pipeline/lauf_report.py:148–165`). Warnregeln und „neu je Quelle“ sähen 20 Häuser nicht. | Jedes Haus eine eigene Zeile in `QUELLEN`, gemeinsames Modul dahinter. Saisonale Häuser melden `saisonal`. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 2 | kritisch | 5.3 | Captions und Publisher filtern nicht nach Datum (`pipeline/caption_generator.py:208–216`, `pipeline/publisher.py:281–290`). Q14 würde ferne Events caption-fähig machen. Der Plan sagte „nur nahe Events“. | Z1 setzt in beiden Abfragen `datum <= heute + 60`. Top/Highlight/Tipp eines Fern-Events wartet bis dahin. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 3 | kritisch | 4.1 | Die Rangtabelle nannte Reservix „später“ und ließ ADticket und Stagedates weg. Ein unbekannter Tier-1-Name würde Rang 4. `ist_aggregator` sucht die Domain auch in der URL (`pipeline/deduplication.py:193–196`). | Rang 2 = Ticketmaster, Eventim, Reservix, ADticket, Stagedates. Rang nur über `quelle_name`, Rausgegangen zusätzlich über die URL. Q6-Zelle stellt klar: Songkick bleibt nein. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 4 | mittel | 5.2 | Die Dict-Skizze kennt weder 120 Tage noch VisitDüsseldorf noch die Kunstsammlung. Oper liest 2 Monate (`scraper/tier2/oper_am_rhein.py:33`), Schauspielhaus 6 (`schauspielhaus.py:47`), RA höchstens 5 Seiten (`scraper/utils/ra_venue.py:122`). | Regel 365/120/60 nach Q7 und Spalte „Fenster“. Seiten-Grenzen sind Pflicht in Z1, nicht „ggf.“. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 5 | mittel | 1.4 | „47 Dateien, davon 5 deaktiviert“ und „R25/Salon ohne Fenster“ stimmen nicht. 48 Dateien enthalten die Konstante. R25 und Salon laufen über `ra_venue.py:113`. `QUELLEN` hat 47 Zeilen (`main.py:86–139`). | Absatz auf die Zählung vom 24.11. korrigiert. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 6 | mittel | 5.3, 9 | Als Job-Grenze standen 6 Stunden. Gesetzt sind 240 Minuten (`.github/workflows/scrape.yml:44`). | Timeout-Angabe korrigiert. Nach dem Lauf vom 21.11. (3 h 7 min) bleiben rund 50 Minuten. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 7 | mittel | 4.5 | Die Warnregeln heißen W1–W6 (`pipeline/lauf_warnungen.py:3`, `web/lib/admin/warnregeln.ts:24`). Die Mail geht bei W1, W2, W4, W6 (`lauf_warnungen.py:25–26`). Abgeschaltete Quellen stehen in `pipeline/quellen.py:21`. | Neue Lückenregel ist W7, gelb, keine Mail. Abgeschaltete und saisonale Quellen zählen nicht. Q4-a als entschieden markiert. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 8 | mittel | 4.2 | Ein Rang über die Ticket-Domain oder ein Wechsel bei gleichem Rang ließe die Quelle springen. Heute wechselt die Quelle nur weg von Rausgegangen und nur mit URL (`database/client.py:128–135`). Der Admin dupliziert das Aggregator-Muster (`web/lib/admin/events.ts:164`). | Wechsel nur bei strikt besserem Rang und mit `quelle_url`. Dieselbe Ableitung im Admin. Nachziehen leert `ticket_url` und `quellen` nicht. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 9 | mittel | 4.3, 5.5 | `SPALTEN_VARIANTEN` gilt für den ganzen Pool (`web/lib/daten.ts:17–26`). `BEARBEITBAR` hat kein `ticket_url` (`web/lib/admin/events.ts:7–24`). `SCHALTER` hat kein `PARTNERLINKS_AKTIV` (`web/lib/admin/github.ts:92`, `web/app/admin/technik/ansicht.tsx:19–25`). Das Cockpit lädt den 60-Tage-Pool (`web/lib/admin/cockpit.ts:5`, `:97`). | Neue Spalten in die erste Variante, SQL davor, R1 fasst sie nicht an. `ticket_url` in die Whitelist, Schalter in beide Listen. Kennzahl aus dem Lauf-Report, nicht aus dem Pool. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 10 | mittel | 5.5.4 | `partner_angebote` war ohne RLS und Grants beschrieben. Anon liest `events` nur über „Events lesen“ (`database/auth_rollen.sql:147–149`). | SQL: anon nur `bestaetigt`, Admin über `ist_admin()`, Schreiben nur `service_role`. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 11 | mittel | 6.1, 6.3 | Sitemap-Tage sind 14 (`web/app/sitemap.ts:93–96`). Die Ortsseite kappt bei 60 Karten (`web/app/orte/[slug]/page.tsx:175–180`), `OrtProgramm` bei 10 (`web/components/ort-programm.tsx:12`). Ähnliche Events kommen aus dem 60-Tage-Pool (`page.tsx:81–88`). Der Button heißt nicht immer „Zum Termin“ (`page.tsx:282–286`). `offers.url` ist `quelle_url` (`web/lib/json-ld.ts:109–113`). | Kappung nur für nahe Termine. Fernpool für Nachbarn hinter Tag 60. Ferne Tagesseite ohne Termine `noindex`. Partner-URL nicht ins JSON-LD. Karten, Merkliste, Mails verlinken die Eventseite. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 12 | mittel | 5.3 | `kalender_laden` hat keine Obergrenze (`scraper/orte/clubs_profil.py:294–298`). `kalender_quelle` behält die letzten 60 Zeilen der Datumssortierung (`:379–385`), also die fernsten. IndexNow meldet nur neue Events des Laufs (`pipeline/indexnow.py:167–175`), nicht alle künftigen. | Club-Prompt auf heute+60. IndexNow-Satz korrigiert. Kontingent von IndexNow offen. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 13 | mittel | 5.1 | Ticketmaster holt eine Seite à 50 und schneidet bei 60 Tagen (`scraper/tier1/ticketmaster.py:287–294`, `:340–342`). Der Workflow setzt den Schlüssel nicht (`scrape.yml:93–109`). | T1 baut Monatsfenster und Blättern. Der Schlüssel allein reicht nicht. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 14 | mittel | 3.2, 4.4, 4.6, 5.5.4, 6.4, 7 | Q3, Q4, Q5, Q9, Q16, Q17, Q18 und Q21 sind entschieden, der Text fragte oder sagte „Vorschlag“. Schritt V0 verwies auf Abschnitt 3.4, den es nicht gibt. | Als entschieden markiert. V0 verweist auf 3.2. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 15 | mittel | 5.5.5, 9 | Ein globaler Schalter würde Ticketmaster-Links vor der schriftlichen Bestätigung zu Partner-Links machen. | Ticketmaster-Domain bleibt außen vor, bis `TICKETMASTER_PARTNER_OK` gesetzt ist. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 16 | gering | 3.3 | Goethe-Museum und KaBARett FLiN haben Crawl-delay 10. Die Baustein-Regel nannte nur 2 Sekunden. | Pause = das größere aus 2 Sekunden und Crawl-delay. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 17 | gering | 5.5.2 | Der DEG-Scraper legt `ticket_url` nur intern ab (`scraper/tier3/deg.py:255–257`) und nicht ins Event (`:316–331`). | P1 übernimmt das Feld ins Event. | angenommen (Claude: Belege geprüft) |
| 1 | Cursor | 18 | gering | 1.1, 5.4 | Die Zahlen vom 23.11. und die Anbieterbedingungen (Sätze, Cookies, API-Formulierung) sind in dieser Runde nicht erneut abgerufen. | In 5.4 als offen/ungeprüft gekennzeichnet. Keine Zahl geändert. | angenommen (Claude: Belege geprüft) |
| 1 | Claude | 19 | mittel | 4.1 | Rangtabelle nach Anzeigenamen trifft gespeicherte `quelle_name` nicht (4 Abweichungen + CSV-Namen der kleinen Märkte); `_scraper` fehlt in `_anreicherungs_update_bauen`, weil `_`-Felder vorher entfernt werden | Lauf: Rang aus `_scraper`, vorab berechnet und übergeben; DB: zweite Tabelle aus Anzeigenamen + `QUELLE_NAME`, unbekannt = Rang 3; Struktur-Test | angenommen |
| 1 | Claude | 20 | mittel | 4.3, 7 | Neue Kennzahlen (nur Rausgegangen, Lücken je Ort) haben keinen Speicherort: Kennzahlen sind Spalten in `scraper_laeufe` (`main.py:299`) | R2-SQL um `kuenftige_events`, `nur_rausgegangen`, `luecken jsonb` ergänzt; W7 in TS liest `luecken` | angenommen |
| 2 | Cursor | 19 | gering | 4.1 | Bestätigt: die vier Paare stimmen (`visitduesseldorf_fuehrungen.py:40`, `classic_remise.py:49`, `street_food_thursday.py:39`, `kleine_weihnachtsmaerkte.py:20` und CSV-Spalte `:57`). `_scraper` wird vor `_anreicherungs_update_bauen` entfernt (`database/client.py:316–320`, Aufruf mit `datensatz` bei `:391–392`). Gegenbefund: der Satz „unbekannter Name = Rang 1 oder 4“ galt danach auch für gespeicherte CSV-Namen und widersprach Rang 3. Rang 2 (Ticketverkauf) löst Rang 3 ab, nicht nur ein Haus. | Unbekannter Anzeigename im Lauf und unbekannter gespeicherter Name getrennt. CSV-Namen bleiben Rang 3 und stehen nicht im Struktur-Test. | angenommen (Claude: Belege geprüft) |
| 2 | Cursor | 20 | mittel | 4.3 | Die drei Spalten stimmen mit `kennzahl()` (`pipeline/lauf_report.py:186–207`). Gegenbefund: „fehlt die Spalte, entfällt W7 still“ ist falsch. Ein fehlender Schlüssel verwirft alle Kennzahlen (`:208–213`). Die Admin-Abfragen nennen die Spalten ausdrücklich und holen `luecken` nicht (`web/lib/admin/scraper.ts:40`, `cockpit.ts:45`); `warnungenBerechnen` hat kein `luecken` (`warnregeln.ts:51`). PostgREST braucht `NOTIFY` (`scraper_laeufe_ort_kennzahlen_2026-11-20.sql:16`). | Selects, Funktion und Cockpit erweitert; SQL endet mit `NOTIFY`. | angenommen (Claude: Belege geprüft) |
| 2 | Cursor | 21 | mittel | 3.3, 5.3 | `ort_zuordnung` trifft `event_orte` über `schluessel`, nicht den Anzeigenamen (`pipeline/ort_zuordnung.py:8–9`, `:86–92`). Ohne Eintrag keine `ort_id`, dann bleiben Ortsseite, „Website von <Ort>“ und W7 blind. Eine gesetzte Beschreibung lässt den Kategorisierer aus (`categorizer.py:186`). `:631` ist `alle_event_seiten` und schreibt keine Beschreibung. Die 100 Fern-Texte müssen im Budget von 5400 s liegen (`beschreibung_quellen.py:709–711`, `main.py:305`). | Ort über `event_orte`. Kategorie, Uhrzeit, Preis, Bild an bestehende Felder gebunden. Beschreibung leer lassen. Datumsfenster nur in den beiden offenen Abfragen. | angenommen (Claude: Belege geprüft) |
| 2 | Cursor | 22 | mittel | 5.5.4 | „Wie die Orte-Vorschläge“ reicht nicht: `admin_vorschlag_annehmen` wirft bei unbekannter `art` (`database/admin_vorschlaege_orte_2026-11-23.sql:136–137`). `VORSCHLAG_ARTEN` hat keinen Partner-Eintrag (`web/lib/admin/vorschlaege.ts:3–9`). | Art `partner_angebot`, Zweig in der Funktion, Schlüssel `anbieter:externe_id`, Button nur bei `bestaetigt` und `ort_id`. SQL mit Spalten, Unique, Index, RLS, `NOTIFY`. | angenommen (Claude: Belege geprüft) |
| 2 | Cursor | 23 | mittel | 6.1, 6.4 | Die Bremse gilt nur für `/guides` (`web/proxy.ts:67`); ein Matcher-Eintrag allein bremst nicht. Der Ausfall vom 23.11. steht in `bremse.ts:1–3`. `eventPoolLaden` fällt auf Beispieldaten zurück (`daten.ts:247–251`). `/ausblick` fehlt in den festen Sitemap-Seiten (`sitemap.ts:81–91`) und in der Navigation (`rahmen.tsx:66–67`). Canonical kommt nur über `seitenMetadaten` (`seo.ts:109`). Der Preset „alle“ ist „60 Tage“ (`datum.ts:166–167`), getrennt von `MAX_ZEITRAUM_TAGE` (`:129`). Ein `/proc`-Verbot steht im Website-Code nicht; der Admin-Plan nennt das Jail „ohne ps“ (`plan-admin-dashboard-2026-11-23.md:14`). | `/ausblick` in die Brems-Bedingung, Metadaten, Sitemap und Navigation. Fernpool-Fehler ohne Beispieldaten. Preset „alle“ bleibt 60 Tage. | angenommen (Claude: Belege geprüft) |
| 2 | Cursor | 24 | mittel | 4.2, 7 | Beim Rangwechsel darf `ort_id` nicht ersetzt werden (`database/client.py:100–103`). Abschnitt 7 sagte nicht, wie man jeden Schritt abschaltet, und nicht, was bleibt, wenn ein Partner-Zugang nie kommt. | `ort_id` ausdrücklich ausgenommen. Rückweg je Schritt, inklusive `VORSCHAU_NOTAUS` und „Quellen an/aus“ (`pipeline/quellen.py:21`). Ohne Zugang: T2/T3/P2 aus, P1 bleibt ein normaler Link. | angenommen (Claude: Belege geprüft) |
| 2 | Claude | 25 | gering | 7 (Rückweg), Z1 | `VORSCHAU_NOTAUS` wirkt nur, wenn der Workflow die Variable an den Lauf gibt; `scrape.yml` reicht Variablen einzeln durch (`:100`) | Z1 ergänzt: Eintrag im `env`-Block, Anzeige über `SCHALTER` | angenommen |
| 2 | Claude | 26 | – | 4.1 | Rückfrage Cursor zu den CSV-Namen der kleinen Märkte (Rang 3) | als technische Detailfrage entschieden: Rang 3 bleibt, Ablösung durch Ticketverkauf gewollt, Redaktionsfelder geschützt; keine Rückfrage an den Auftraggeber | angenommen |
| 3 | Cursor | 25 | gering | 7 | Bestätigt: `ORTSSEITEN_MELDEN` steht im `env`-Block des Schritts „Pipeline ausführen“ (`scrape.yml:100`), `SCHALTER` ist die Liste (`web/lib/admin/github.ts:92`). Ergänzung: ohne Eintrag in `SCHALTER_TEXT` zeigt das Panel den Roh-Namen (`web/app/admin/technik/ansicht.tsx:87`, Texte `:19–25`). Wirksam beim nächsten Pipeline-Lauf, nicht beim Website-Deploy. Nicht gesetzt ist aus. | Text in `SCHALTER_TEXT`, Wirkung und Default im Rückweg Z1. | geändert → angenommen (Claude: Belege geprüft) |
| 3 | Cursor | 26 | – | 4.1 | Bestätigt. Rang 3 bleibt. `redaktion_felder` filtert am Ende jedes Updates (`database/client.py:137–142`). Ein Bild wird nur ersetzt, wenn das bisherige von Rang ≥ 4 stammt (4.2). Die Zeilenangabe `:42` war die Sitemap; `QUELLE_NAME` steht in `visitduesseldorf_fuehrungen.py:40`. Keine Rückfrage an den Auftraggeber. | Zeilennummer korrigiert. Entscheidung unverändert. | bestätigt → angenommen (Claude: Belege geprüft) |
| 3 | Cursor | 27 | mittel | 1, 2, 5.1, 6.4 | Ziel 3 nannte Songkick noch als Anschluss, Q6 sagt nein. Abschnitt 2 hieß „zur Bestätigung“, die Qs sind freigegeben. „später Eventim“ las sich wie ein offener Rang. Die Ausblick-Zeile hieß noch „Empfehlung“. | Ziel 3 ohne Songkick. Abschnitt 2 als entschieden. Eventim ab T2, Rang 2. Ausblick als entschieden. | geändert → angenommen (Claude: Belege geprüft) |
| 3 | Cursor | 28 | mittel | 4.3, 6.3 | 4.3 schrieb den Button-Text „Tickets bei Eventim/Ticketmaster“, 6.3 und 5.5.5 schreiben „Tickets*“. | 4.3 verweist auf „Tickets*“. | geändert → angenommen (Claude: Belege geprüft) |
| 3 | Cursor | 29 | mittel | 5.2 | `vorschau_ende` sollte `QUELLE_NAME` bekommen, die Tabelle schlüsselt auf den Anzeigenamen. `Classic Remise` und `Street Food Thursday Düsseldorf` träfen dann keinen Eintrag (`classic_remise.py:49`, `street_food_thursday.py:39`). | Aufruf mit dem Anzeigenamen; abweichende `QUELLE_NAME` mit demselben Fenster in der Tabelle. | geändert → angenommen (Claude: Belege geprüft) |
| 3 | Cursor | 30 | mittel | 5.3, 7 | „Optimierung, wenn der Lauf über 4 h kommt“ ist unerreichbar: der Job endet bei 240 Minuten (`scrape.yml:44`). Z1 und V1 hatten keine messbare Abnahme. | Abnahme: `beendet_am - gestartet_am` unter 240 Minuten und `status = erfolgreich` (`scraper_report.sql:16–17`). Bei Abbruch `VORSCHAU_NOTAUS=1`, keine weitere Welle. W5 nach 90 Minuten (`warnregeln.ts:38`, `:61–62`) ist nicht die Abnahme. | geändert → angenommen (Claude: Belege geprüft) |
| 3 | Cursor | 31 | mittel | 5.3, 6.1 | 5.3 lässt den Fernpool nur Events mit Kategorie laden. 6.1 sagte „Tage 60 bis 365, gleiche Abfrage“ und hätte Tag 60 doppelt und unfertige Events mitgenommen. | Fernpool Tag 61–365 und `kategorie is not null`. Rang 1–2 nur auf `/ausblick` und in der Startbox. | geändert → angenommen (Claude: Belege geprüft) |
| 3 | Cursor | 32 | mittel | 5.5.2, 7 | `ticket_url` fehlte `NOTIFY`. Dieselbe Lücke hat am 20.11. den Lauf-Report gekippt (`scraper_laeufe_ort_kennzahlen_2026-11-20.sql:16`). Die drei SQL-Dateien standen nicht an einer Stelle. | `NOTIFY` in der P1-Datei. Tabelle „SQL vor dem Deploy“ mit R2, P1 und T3. | geändert → angenommen (Claude: Belege geprüft) |
| 3 | Cursor | 33 | gering | 5.4, 5.5.4, 5.5.5, 7 | Ungeprüfte Sätze in 5.4 lasen sich wie eine Sperre. Datenschutz-Datei und Impressum waren nicht genannt. Bildregeln für Ticketmaster und GetYourGuide nicht als Feld `bild_url`. Stagedates: „Nutzungsbedingungen noch zu lesen“, T1 aber ohne Halt. | 5.4 blockiert nicht; P2 erst nach Anmeldung und Anwalt. Datenschutz `web/app/datenschutz/page.tsx`, Impressum `web/app/impressum/page.tsx:78` bleibt. `bild_url` leer, bis die Bildfreigabe da ist. Stagedates erst nach gelesenen Bedingungen in `QUELLEN`. | geändert → angenommen (Claude: Belege geprüft) |
| 3 | Claude | 34 | gering | 5.5.4, T1, Anfragen | Bildverzicht bei Ticketmaster widerspricht dem heutigen Code (`ticketmaster.py:32` ff. setzt `bild_url`) und war nicht an eine Klärung gebunden | T1 stellt `bild_url` ab, bis die Ticketmaster-Bestätigung die Bildnutzung einschließt; Anfrage-Entwurf fragt ausdrücklich nach Bildern über unseren Bild-Proxy | angenommen |
| 4 | Cursor | 34 | – | 5.5.4, T1, Anfragen | Bestätigt. `_bild_url_ermitteln` steht in `scraper/tier1/ticketmaster.py:32`, das Event bekommt `bild_url` in `:202`. Der Proxy holt diese Adresse (`web/app/bild/event/[id]/route.ts:43`, Verkleinern in `web/lib/bild-proxy.ts:213`). Die Anfrage fragt die Bildnutzung. Ergänzung: die Aufzählung „planned use“ nannte das Bild schon als fest, die Frage danach wirkte nur noch nachgeschoben. | „image“ aus der festen Aufzählung genommen. Die Frage bleibt. | geändert → angenommen (Claude: Belege geprüft) |
| 4 | Cursor | 35 | mittel | 5.2, 7 | Die Klammer in Z1 las sich als Ziel (Oper 2 Monate, Schauspielhaus 6, Ticketmaster eine Seite). 5.2 meint damit den heutigen Code (`oper_am_rhein.py:33`, `schauspielhaus.py:47`). Beide Häuser haben Fenster 365. Ticketmaster-Blättern ist T1. RA bleibt bei 5 Seiten (`ra_venue.py:122`). | Z1 zieht Oper und Schauspielhaus auf 365 Tage. RA-Grenze bleibt. Ticketmaster-Blättern bleibt in T1. | geändert → angenommen (Claude: Belege geprüft) |
| 4 | Cursor | 36 | mittel | 4.2, 7 | „Nach jedem größeren Schritt“ und „erst N1 nach P1“ widersprechen sich. Ein Lauf vor der Spalte `ticket_url` würde das Nachziehen an dieser Spalte scheitern lassen. | Ein Lauf N1, nach P1, vorher keiner. | geändert → angenommen (Claude: Belege geprüft) |
| 4 | Cursor | 37 | gering | 8, 7 | Abschnitt 8 nannte T1 nicht. Die Abnahme von T1 prüfte `bild_url` nicht. | Test: Beispielantwort mit Bildern ergibt `bild_url` leer. Abnahme: Stichprobe `bild_url` leer. | geändert → angenommen (Claude: Belege geprüft) |
| 5 | Cursor | – | – | gesamt | keine kritischen oder mittleren Befunde | – | bestätigt |
| 5 | Claude | – | – | gesamt | Gegenprüfung: keine alten Sätze zu Nr. 35/36 übrig, Schrittfolge A1 R1 R2 Z1 T1 W1 V0 V1 P1 N1 W2 P2 T2 T3 V2 und SQL-Tabelle stimmig | – | bestätigt – **Prüfschleife abgeschlossen** |

## Anhang C: Umsetzungsnotizen

### R1 – Rangfolge der Quellen (24.11.2026, lokal gebaut)

Gebaut wie 4.1/4.2, Punkte 1–3 (Punkt 4 Nachziehen = N1, später):
- `pipeline/quellen_rang.py`: `RANG_ANZEIGE` (alle 47 Zeilen aus `QUELLEN`), `RANG_GESPEICHERT` (dazu die abweichenden
  `QUELLE_NAME`-Werte, `Event-Meldung` aus `web/app/api/admin/meldungen/route.ts:18` als Rang 1 und die Namen der
  deaktivierten Scraper für alte Zeilen), `quellen_rang(event)`, `rang_gespeichert(...)`, `rang_anzeige(name, tier)`.
- `pipeline/lauf_report.py`: setzt neben `_scraper` auch `_tier` (für den Rang eines Anzeigenamens ohne Tabelleneintrag,
  Tier 2/3 → 1, sonst 4). Wird wie alle `_`-Felder vor dem Speichern entfernt.
- `pipeline/deduplication.py`: `_events_mergen` tauscht zur Quelle mit strikt besserem Rang. **Abweichung vom
  Wortlaut von 4.2 Punkt 1:** auch hier nur, wenn die bessere Quelle eine `quelle_url` hat – wie beim Speichern
  (Punkt 2); sonst verlöre das Event seinen Link. Die Uhrzeit des Hauses gilt dann trotzdem. `ist_aggregator` =
  Rang ≥ 2; `_AGGREGATOR_MUSTER` entfällt (die URL-Suche nach Ticket-Domains damit auch).
- `database/client.py`: `_anreicherungs_update_bauen(..., rang_neu)`; `events_speichern` rechnet den Rang vor dem
  Entfernen der `_`-Felder. Quellenwechsel nur bei strikt besserem Rang mit Link; Bild nur ersetzt, wenn die alte
  Quelle Rang ≥ 4 hat; `beschreibung_quelle`, `redaktion_felder`, `ort_id` bleiben. Log: „Quelle gewechselt: A → B“.
- `pipeline/dubletten_sql.py` `paare_finden`: Sortierung nach Rang (damit auch `vorschlaege.py`).
- `web/lib/quellen-rang.ts` (neue Datei, Tabelle der gespeicherten Namen) und `web/lib/admin/events.ts`
  (`istAggregator` = Rang ≥ 2 statt eigenem Muster).
- Gemeinsame Prüfdaten `tests/fixtures/quellen_rang.json`; Tests `tests/test_quellen_rang.py` (20) und
  `web/tests/quellen-rang.test.ts` (4). `tests/test_dedup_toleranz.py`: Meetup.com gilt jetzt als Sammelquelle
  (Rang 3, Q1).
- Ergebnis: Python 548 Tests ok, Website 703 Tests ok. `tsc` meldet im Worktree nur die bekannten fehlenden
  `PageProps`-Typen (entstehen erst beim Next-Build), keine Fehler in den geänderten Dateien.
- Verhaltensänderungen im Lauf: PRINZ, AllEvents, VisitDüsseldorf usw. werden jetzt von einem Haus abgelöst (bisher
  nur Rausgegangen); Ticketmaster wird von einem Haus abgelöst; Uhrzeit-Regel unverändert, aber Meetup.com zählt als
  Sammelquelle. Rückweg: Commit zurücknehmen (kein Schalter, kein SQL).

### R2 – Quellenliste, Kennzahlen, W7 (24.11.2026, lokal gebaut)

- SQL `database/quellen_spalte_2026-11-24.sql` (vor dem Deploy): `events.quellen jsonb` mit Vorbelegung (Rang per CASE
  aus derselben Tabelle wie `pipeline/quellen_rang.py`, erzeugt aus `RANG_GESPEICHERT`), `scraper_laeufe.kuenftige_events`,
  `nur_rausgegangen`, `luecken jsonb`, `NOTIFY pgrst`, zwei Kontrollabfragen.
- `pipeline/quellen_rang.py`: `QUELLEN_FELD` (`_quellen`), `quellen_eintrag`, `quellen_vereinigen` (je Name ein Eintrag;
  meldet eine Änderung nur bei neuer Quelle, anderem Link/Rang oder `zuletzt` älter als 7 Tage – sonst gäbe jedes Duplikat
  in jedem Lauf ein Update), `quellen_der_zeile` (alte Zeilen ohne Liste), `nur_rausgegangen`.
- `pipeline/deduplication.py`: jedes Event startet mit seiner eigenen Quelle, `_events_mergen` vereinigt die Listen.
- `database/client.py`: `quellen` in `_ABGLEICH_SPALTEN`; Insert schreibt die Liste; `_anreicherungs_update_bauen`
  ergänzt sie (Feldschutz gilt wie für alle Felder).
- `pipeline/quellen_kennzahlen.py`: `luecken_berechnen` (Haus = `_haus_id` bzw. `ort_id`; „direkt abgefragt“ = eine
  Rang-1-Quelle hat in diesem Lauf Events an dem Haus geliefert – abgeschaltete und saisonal leere Quellen liefern
  keine und zählen deshalb nicht; Lücke = Event nur mit Rausgegangen an einem solchen Haus an einem Tag ohne Event der
  Direktquelle), `bestand_zaehlen` (künftige sichtbare Events, davon nur Rausgegangen). `main.py` schreibt beides nach
  Schritt 2 als Kennzahlen; Fehler werden nur geloggt.
- W7 in `pipeline/lauf_warnungen.py` und `web/lib/admin/warnregeln.ts` (gelb, nicht in `MAIL_REGELN`, Grenze > 3),
  zwei neue Fälle in `tests/fixtures/lauf_warnungen.json`. Die Python-Mail-Abfrage holt `luecken` nicht (W7 löst keine
  Mail aus).
- Admin: `scraper.ts` und `cockpit.ts` holen `kuenftige_events`, `nur_rausgegangen`, `luecken`; das Cockpit zeigt
  „nur bei Rausgegangen (von n künftigen)“ des letzten beendeten Laufs.
- **Abweichung:** Die Website lädt `quellen` noch nicht in den Pool (`SPALTEN_VARIANTEN`); das braucht erst der
  Ticket-Button in W2 und kommt dort dazu.
- Tests: `tests/test_quellen_liste.py` (13); Python gesamt 562 ok, Website 708 ok.
- Rückweg: Commit zurücknehmen; die Spalten bleiben liegen und stören nicht.

### Z1 – Zeitraum je Quelle (24.11.2026, lokal gebaut)

- `config.py`: `VORSCHAU_TAGE` (Anzeigenamen und abweichende `QUELLE_NAME`, 365/120/60 nach Q7), `vorschau_tage(quelle,
  tier)`, `vorschau_ende(quelle, heute, tier)`; Notaus über `VORSCHAU_NOTAUS=1` (jede Quelle höchstens 60 Tage).
- Alle 48 Scraper-Dateien rufen `vorschau_ende(QUELLE_NAME, heute)` (`ra_venue.py` mit dem übergebenen `quelle_name`);
  `SCRAPER_VORSCHAU_TAGE` kommt in `scraper/` nicht mehr vor. Die Tabelle enthält jeden `QUELLE_NAME` mit demselben
  Fenster wie sein Anzeigename (Test), deshalb reicht der Modulname.
- Seiten-Grenzen: Oper `MONATE_VORAUS` 2 → `vorschau_tage // 30` (12 Zusatzmonate, mit Startseite 14), Schauspielhaus
  6 → `vorschau_tage // 30 + 1` (13); beide folgen dem Notaus. Ohne Änderung, weil sie schon das ganze Programm laden:
  d.live und Mitsubishi-Halle (`total=9999`), Tonhalle (Webshop-Liste), Capitol (Übersichtsseite), Kom(m)ödchen
  (Spielplan-Seite über unseren Server), Fortuna/DEG (Saison-Spielplan), Messe (Messeliste), Kunstsammlung
  (Ausstellungen; Führungen folgen in V0). RA-Häuser bleiben bei 5 Seiten, Ticketmaster bei einer Seite (T1).
- Beschreibungen (`pipeline/beschreibung_quellen.py`): `BESCHREIBUNG_TAGE = 60` als Obergrenze in
  `offene_rausgegangen_events` und `offene_veranstalter_events`; Fern-Block `offene_veranstalter_events(db, fern=True)`
  ab Tag 61, nur Rang 1–2, höchstens `FERN_BESCHREIBUNGEN = 100`, nach den nahen Stücken im selben Zeitbudget.
- Captions und Publisher: `INSTAGRAM_TAGE = 60` als Obergrenze in beiden Abfragen. Club-Prompt: `kalender_quelle`
  nimmt nur Termine bis heute + 60 (`PROMPT_TAGE`).
- Kategorisierung: 1.500 statt 300 bis einschließlich 09.12.2026 (`KATEGORIEN_RUECKSTAND_BIS` in `main.py`), danach
  automatisch wieder 300.
- `VORSCHAU_NOTAUS` im `env` von `scrape.yml`, in `SCHALTER` (`web/lib/admin/github.ts`) und mit Text im Technik-Panel.
- Tests: `tests/test_vorschau.py` (12); Python gesamt 574 ok, Website 708 ok.
- Sichtbar schon vor W1: Eventseiten ferner Events (einzeln über `eventLaden`) und die Ortsseiten (laden über `ort_id`
  ohne Datumsgrenze, zeigen die nächsten 60 Termine). Noch nicht kategorisierte ferne Events erscheinen dort bis zur
  Kategorisierung als „sonstiges“ – betrifft nur Häuser, deren nächste 60 Termine schon über Tag 60 hinausreichen.
- Abnahme (Abschnitt 7): nächster Lauf `status = erfolgreich` und unter 240 Minuten. Reißt es: GitHub-Variable
  `VORSCHAU_NOTAUS=1` setzen (wirkt ab dem nächsten Lauf, kein Deploy nötig).

### T1 – Ticketing (24.11.2026, lokal gebaut)

- `scraper/tier1/ticketmaster.py`: ein Abruf je Kalendermonat bis `vorschau_ende` (365 Tage, 13 Fenster), `countryCode=DE`,
  `geoPoint` Düsseldorf (Geohash `u1hg6jsq`) + 25 km, je Fenster geblättert (200 je Seite, höchstens 1.000 Treffer – sonst
  Warnung im Log), 2 s zwischen Anfragen. `bild_url` nur mit `TICKETMASTER_BILDER_OK=1` (GitHub-Variable, im
  Technik-Panel sichtbar), sonst leer. Ohne `TICKETMASTER_API_KEY` wird die Quelle wie bisher übersprungen.
- `scrape.yml`: `TICKETMASTER_API_KEY` (Secret) und `TICKETMASTER_BILDER_OK` (Variable) im `env`.
- Songkick aus `main.py` `QUELLEN` entfernt (Modul bleibt), CLAUDE.md-Tabelle angepasst.
- **Stagedates zurückgestellt (Rückfrage an den Auftraggeber):** robots.txt erlaubt alles, die Sitemap hat 835 Events
  bundesweit, Eventseiten tragen JSON-LD. Aber (1) die Nutzungsbedingungen (`/terms`) sind nur per JavaScript lesbar und
  deshalb ungelesen – der Plan verlangt sie vor der Aufnahme; (2) nur **1** der 835 URLs ist am Namen als Düsseldorf
  erkennbar. Für den Ort müsste man jede Eventseite laden (erster Lauf ≈ 28 min, danach nur neue URLs). Rudas Studios
  läuft schon über einen eigenen Scraper. Vorschlag: Stagedates erst mit V1 (JSON-LD-Baustein und Zwischenspeicher
  wie bei VisitDüsseldorf), nachdem jemand die Bedingungen im Browser gelesen hat.
  **Auftraggeber 24.11.2026: einverstanden** – Stagedates kommt mit V1.
- Tests: `tests/test_ticketmaster.py` (7); Python gesamt 581 ok, Website 708 ok.
- Rückweg: Commit zurücknehmen; Ticketmaster ohne Secret ist ohnehin aus.

### Cursor-Prüfung der Umsetzung R1–T1 (24.11.2026) – Einarbeitung

Urteil Cursor: R1 und R2 in Ordnung, Z1 und T1 nicht (je ein mittlerer Befund), dazu fünf geringe. Eingearbeitet:
- **Z1, mittel – Oper las nur verlinkte Monate:** `scraper/tier2/oper_am_rhein.py` rechnet die Monats-URLs jetzt selbst
  (`_monate_ab`, insgesamt `MONATE_VORAUS + 2` ab dem laufenden Monat), verlinkte Monate kommen dazu. Eine fehlende
  oder leere Monatsseite zählt als leerer Monat; nach `LEERE_MONATE_STOPP = 2` leeren Monaten in Folge endet der Abruf.
- **T1, mittel – ein API-Fehler verwarf alle Monate:** Ein fehlgeschlagenes Fenster wird übersprungen, die übrigen
  bleiben; Warnung „Teilergebnis“ mit den Monaten. Nach `ABBRUCH_NACH_FEHLERN = 3` gestörten Fenstern in Folge endet
  der Abruf (sonst kostet jedes Fenster drei Timeouts). Der Lauf-Report zeigt dann „ok“ mit der Warnung als Meldung –
  ein eigener Status „Teilmenge“ wäre eine Änderung am Lauf-Report und ist nicht Teil von T1.
- **T1, gering – Zeitzone:** Das erste Fenster beginnt am Vortag 22:00 UTC (Events kurz nach Mitternacht Ortszeit).
- **Z1/T1, gering – Tests:** Oper ohne Navigationslinks, Stopp nach leeren Monaten, Notaus senkt `MONATE_VORAUS` beim
  frischen Import (Oper und Schauspielhaus), Ticketmaster-Fehler in einem Fenster, Abbruch nach Fehlern in Folge.
- **R1, gering – `rausgegangen_nachziehen.py` übergibt keinen Rang und keine Quellenliste:** bewusst nicht geändert,
  das Skript läuft erst in N1; N1 übergibt Rang und Liste, bevor die „_“-Felder entfallen.
- **Z1, gering – Laufzeit des ersten Laufs:** wird beobachtet; Notaus statt höherem Zeitlimit.
- Python gesamt 585 Tests ok (Website unverändert, 708 ok).

### V0 – VisitDüsseldorf komplett und Kunstsammlung-Kalender (24.11.2026, lokal gebaut)

- **VisitDüsseldorf:** `scraper/tier1/visitduesseldorf.py` neu – statt Playwright auf der ersten Kalenderseite
  (≈ 10 Events je Lauf) alle ≈ 780 Eventseiten der Sitemap mit Toubiz-JSON. Abruf und Zwischenspeicher teilt es mit dem
  Führungs-Scraper: `visitduesseldorf_fuehrungen.seiten_laden()` lädt je Lauf nur geänderte Seiten, neueste zuerst,
  höchstens `MAX_NEU_JE_LAUF = 200` (je Seite ≈ 1,5 MB; der erste Vollbestand verteilt sich so auf mehrere Läufe), und
  nur einmal je Prozess. Kategorie aus den Toubiz-Kategorien (`KATEGORIE_MAP`), Ort/Adresse wie bei den Führungen,
  Beschreibung leer (Schritt 3b). Ausgelassen: Führungen (liefert der Führungs-Scraper bzw. die Museen; „Aufführung“
  zählt nicht als Führung) und buchbare Tagesangebote (`AUSSCHLUSS`: Aktivität, Schifffahrt, Bustour – im Probelauf
  82 Termine „Panoramafahrt auf dem Rhein“). Probelauf mit 12 Seiten: 241 Termine, davon 104 Schiffsfahrten → jetzt raus.
- **Kunstsammlung NRW:** zusätzlich `/de/calendar/` (serverseitig, je Termin `div.card[data-date]` mit Haus, Art,
  Zielgruppe, freiem Eintritt) – 133 Termine bis Juli 2027 (Führungen, Workshops, Aktionen, Talks). Ort „K20 Grabbeplatz“
  bzw. „K21 Ständehaus“ wie in der Ortstabelle, Familie/Kinder → `family`, Workshop/Aktionen → `community`, sonst
  `kultur`. Ein Fehler im Kalender kostet nur die Termine, nicht die Ausstellungen.
- Tests: `tests/test_visitduesseldorf_kalender.py` (3), `tests/test_kunstsammlung_kalender.py` (3) mit Auszug
  `tests/fixtures/kunstsammlung_kalender.html`; Python gesamt 592 ok.
- CLAUDE.md-Tabellen angepasst. Rückweg: im Admin unter „Quellen an/aus“ abschalten oder Commit zurücknehmen.

### V1 – Bausteine und Welle A (24.11.2026, lokal gebaut)

- **Bausteine:** `scraper/utils/jsonld_events.py` (schema.org-Events inkl. `@graph`, `subEvent`, Zeitzonen → Ortszeit,
  Angebote, abgesagt), `scraper/utils/wp_tribe.py` (The Events Calendar, seitenweise), `scraper/utils/ical.py` (ohne
  Bibliothek: gefaltete Zeilen, ganztägig, UTC → Ortszeit, RRULE DAILY/WEEKLY/MONTHLY mit INTERVAL/UNTIL/COUNT, EXDATE,
  CANCELLED). Tests `tests/test_bausteine.py`.
- **Stagedates** (`scraper/tier1/stagedates.py`, Rang 2, 365 Tage): Sitemap, Datum aus dem Slug, nur noch nicht
  gelesene Seiten (höchstens 150 je Lauf, Zwischenspeicher `data/stagedates/` per `actions/cache` im Workflow), JSON-LD,
  nur Düsseldorf/Neuss/Ratingen. Nutzungsbedingungen am 24.11. im Browser gelesen (AGB Ticketkäufer, kein Verbot).
- **Welle A, 19 Häuser** (je eine Zeile in `QUELLEN`, Rang 1, Fenster in `config.VORSCHAU_TAGE`), gebaut von vier
  Unteragenten nach gemeinsamer Vorgabe, von Claude geprüft und eingebunden. Live-Proben 24.11. (teils mit 60/120 Tagen):
  Theater an der Kö 167 · Theater an der Luegallee 68 · KaBARett FLiN 124 (über den eingebetteten Spielplan von
  neanderticket.de) · Savoy 28 bei 6 Seiten (Liste per admin-ajax-POST, robots erlaubt; `MAX_SEITEN` 35 für 365 Tage) ·
  Apollo 17 (Spielzeiten als `datum_bis`, Einzelvorstellungen nur im gesperrten Ticketshop) · Theatermuseum 36 (Quelle
  theater-museum.de, die städtische Seite ist leer) · Gerhart Hauptmann Haus 7 (Website zeigt nur ≈ 3 Monate) ·
  Goethe-Museum 4 · Schloss Benrath 127 (ohne 280 Ticket-Zeitfenster) · KIT 28 (WP-REST) · Comedy Club 83 · Bilker
  Bunker/Schleuse Zwei 9 · Tor 3 3 · Nachtresidenz 11 · Ampere 12 · Weltkunstzimmer 4 · Insel Hombroich 2 (Winter;
  Tribe-API, ohne englische Doppel und Ausstellungstage) · Stadt Ratingen 59 (ohne Wochenmärkte, Crawl-delay 10) ·
  TaS Neuss 29.
- **Nicht gebaut: Maxhaus** – Termindatum nur auf jeder Detailseite (REST liefert nur das Veröffentlichungsdatum),
  Liste per JetEngine-POST. Möglich später: Detailseiten mit höherer Grenze oder Anfrage beim Haus.
- Bekannte Grenzfälle: Poetry Slam 04.12. bei Theatermuseum und Goethe-Museum mit abweichender Uhrzeit (Dublette
  möglich, Dubletten-Vorschläge im Admin); Schloss Benrath „Die Leuchtenden Gärten“ 52 Einzeltermine; Comedy-Club-Bilder
  als AVIF (Bild-Proxy prüfen).
- Tests: 116 neue in `tests/test_<haus>.py`; Python gesamt 716 ok, Website 712 ok.
- Rückweg: einzelne Häuser im Admin unter „Quellen an/aus“ abschalten; sonst Commit zurücknehmen.

### Cursor-Prüfung Fix/V0/V1 (24.11.2026) – Einarbeitung

Cursor: V1 deploybar, ein mittlerer und sechs geringe Befunde. Alle sieben eingearbeitet:
- **Stagedates (mittel):** Eine Seite ohne lesbaren Termin (leere Hülle, Bot-Seite) galt als gelesen und wurde nie
  wieder geladen. Jetzt zählt nur eine Seite mit Termin als gelesen; leere Seiten werden bis `MAX_FEHLVERSUCHE = 2`
  erneut versucht. Bei 0 Events im Gebiet steht eine Warnung im Log. Test `test_leere_seite_wird_nachgeholt`.
- **iCal:** COUNT zählt nur echte Termine (ein ausgelassener 31. in kürzeren Monaten zählt nicht mit);
  ganztägiges DTEND ist exklusiv (RFC 5545) und wird als letzter Tag minus eins gespeichert. Zwei Tests neu.
- **JSON-LD:** Scheitert die Umrechnung der Zeitzone (z. B. fehlende tzdata), steht eine Warnung im Log statt still
  die UTC-Uhrzeit zu übernehmen. Test für Sommerzeit.
- **VisitDüsseldorf:** Führungen werden über ganze Wörter der Kategorienamen erkannt (Menge `FUEHRUNG`), nicht über
  Teilstrings. Im Bestand stehen auch „Vorführung“ und „Filmvorführung“ – die wären sonst als Führung aussortiert
  worden. Test erweitert.
- **Spaltenprobe `events.quellen`:** Nur eine wirklich fehlende Spalte (42703, PGRST204, „does not exist“) schaltet
  die Quellenliste ab; ein kurzer Netzfehler nicht mehr. Test `test_netzfehler_schaltet_quellenliste_nicht_ab`; der
  bestehende Test setzt den Schalter im `finally` zurück.
- **Admin Scraper-Seite:** Fehlen die Kennzahl-Spalten, lädt die Seite die Läufe ohne sie statt mit Fehler.

Tests: Python 720 ok, Web 712 ok, tsc nur die bekannten generierten Typen.

### P1 – Ticket-Link des Hauses (24.11.2026, lokal gebaut)

- **SQL** `database/ticket_url_2026-11-24.sql`: `events.ticket_url text` + `NOTIFY pgrst`. Vor dem Deploy ausführen und
  die Spalte danach per anon-Abfrage prüfen (Lehre aus R2).
- **Baustein** `scraper/utils/ticket_link.py`: `ticket_link(url, basis)`, `ticket_link_aus(element, basis)`,
  `anbieter(url)`. Erkennt Anbieter an der Domain (Eventim inkl. Eventim Light, Reservix, ADticket, Ticketmaster,
  ticket.io, Neanderticket, YesTicket, Stagedates, Eventbrite, pretix, vivenu, Fienta, Rodrigue …) und eigene Shops
  am Host (`tickets.`, `karten.`, `shop.`). Rausgegangen, PayPal, mailto/javascript zählen nie.
- **Speichern** (`database/client.py`): Spaltenprobe wie bei `quellen` (`_TICKET_SPALTE`, ohne Spalte wird ohne
  Ticket-Link gespeichert). `ticket_url` wird ergänzt, wenn er fehlt; ein vorhandener bleibt, wenn die neue Quelle
  keinen hat; ersetzt wird er nur beim Quellenwechsel zu einem besseren Rang oder von der Quelle, die schon
  Hauptquelle ist (das Haus hat den Link geändert). `redaktion_felder` schützt ihn wie jedes andere Feld.
- **Deduplizierung**: `ticket_url` ist anreicherbar (die bessere Quelle zuerst, sonst ergänzt).
- **Kennzahl**: Log-Zeile „Ticket-Links: n von m Events (x %) – Eventim …, eigener Shop …“ je Lauf
  (`pipeline/quellen_kennzahlen.ticket_links_zaehlen`). Keine neue Spalte in `scraper_laeufe`.
- **Admin**: `ticket_url` in `BEARBEITBAR` (nur vollständige http(s)-Adresse), im Event-Editor und in der Admin-API.
  **Website**: neue erste `SPALTEN_VARIANTEN`-Zeile mit `ticket_url` (Fallback ohne, `spaltenFehlt` kennt die Spalte),
  Feld `DddEvent.ticket_url`. Angezeigt wird er erst mit W2.
- **Welle A** (Live-Probe 24.11.): Theater an der Kö 161/167 (Rodrigue-Shop), TaS Neuss 63/84 (karten.tas-neuss.de),
  Nachtresidenz 7/11 (ticket.io, Eventim Light, vivenu), Tor 3 1/3 (Eventim Light; PayPal-/Anmelde-Links zählen
  nicht), dazu laut Fixtures Savoy (Eventim-Button je Termin), Bilker Bunker (Eventim), KaBARett FLiN (Eventseite
  bei Neanderticket `neanderticket.de/<Nr>`, der Kauf-Button selbst ist JavaScript), Apollo (tickets.apollo-variete.com –
  nur verlinkt, robots sperrt den Shop für Abrufe), Stadt Ratingen (`a.event-ticketlink` der Detailseite, nur für die
  Reihe dieser Detailseite), Comedy Club (nur `external_url`, z. B. Fienta – sonst verkauft der Club auf der
  Show-Seite, die schon `quelle_url` ist). DEG schreibt den Game-Center-Button jetzt ins Event.
- **Bestehende Häuser** (Hilfsagent, je Website höchstens 1–2 Kontrollabrufe, kein zusätzlicher Abruf im Scraper):
  mit Ticket-Link Kom(m)ödchen (tickets.kommoedchen.de), Kunstsammlung (nur Kalender, shop.kunstsammlung.de), Oper
  (webshop.operamrhein.de; ausverkauft/„Info“ → keiner), Schauspielhaus (ticket.dhaus.de, live 85/137), Tanzhaus
  (Reservix, ticket.io; „Anfrage“ → keiner), d.live und Mitsubishi (API-Button „tickets-conversion“, VIP/Parken
  zählen nicht), Tonhalle (Webshop, gleich `quelle_url`), Pitcher (`external_ticket_url`), Rudas (Stagedates-Teil),
  NRW-Forum (Kunstpalast-Shop-Pfad `/shop/`), Fortuna (tickets.f95.de, über das Datum der Spielkarte). Ohne Link in
  den geladenen Daten: Capitol (nur Detailseite), FFT (Links nur zu Rausgegangen), Filmmuseum, Jazz-Schmiede,
  Stahlwerk, STARTPLATZ, Stadtstrand, Kasematten, EKŌ-Haus, Kunsthalle/Kunstpalast (nur allgemeiner Shop),
  Stadtbüchereien, zakk (nur Detailseite), R25/Salon (nur über RA), Classic Remise, Messe (Infoseite, kein Shop).
  Anbieterliste um Live Nation, KölnTicket, ATG Tickets u. a. ergänzt.
- **Nicht übernommen:** Theater an der Luegallee – der einzige Link je Termin ist „merken“
  (`theaterkarten/hinzufuegen/?mode=notepad_add`), ein Warenkorb-Eintrag, kein Kauflink. Übrige Welle-A-Häuser
  (Museen, Schloss Benrath, KIT, Ampere, Weltkunstzimmer, Insel Hombroich, Gerhart Hauptmann Haus, Theatermuseum,
  Goethe-Museum) nennen keinen Ticket-Link in den geladenen Seiten.
- **Für P2 merken:** Manche Häuser hängen eigene Partner-Kennungen an (Savoy: `?affiliate=SAV&utm_…`). `tickets.ts`
  muss beim Bau des Partner-Links fremde Kennungen ersetzen, nicht doppelt anhängen.

### N1 – Bestand auf Rang umhängen (24.11.2026, lokal gebaut)

- `pipeline/quellen_nachziehen.py` (Nachfolger von `rausgegangen_nachziehen.py`, das als dünner Aufruf bleibt und
  `_rausgegangen_eintraege` für `beschreibung_quellen.stichprobe` behält).
- Scrapt alle Quellen außer Rausgegangen und den im Admin abgeschalteten über den Lauf-Report (ohne `starten()`,
  also ohne Zeile in `scraper_laeufe`), damit jedes Event `_scraper`/`_tier` und damit seinen Rang trägt. Danach
  Gebietsfilter und Deduplizierung wie im täglichen Lauf.
- Lädt alle künftigen Zeilen mit Rang ≥ 2 (mit `quellen` und `ticket_url`), sucht je Zeile die passenden gescrapten
  Events (Titel+Ort, Slug oder ähnlich, gleiche/fehlende Uhrzeit) und nimmt das mit dem besten Rang. Die Änderung
  baut `_anreicherungs_update_bauen` mit Rang und Quellenliste – also dieselben Grenzen wie beim Speichern. Ein
  Sicherheitsnetz verwirft leere Werte im Update.
- Ohne Spalte `ticket_url` bricht das Skript ab (N1 erst nach P1).
- `--schreiben` sichert vorher alle geänderten Felder; `--zuruecksetzen <Sicherung>` spielt sie zurück.
- Hinweis: Seit R1 hängt auch jeder tägliche Lauf die Events um, die er wieder findet. Der Lauf am 24.11. hat wegen
  der fehlenden Spalte nichts gespeichert, deshalb wirkt N1 jetzt drei Tage früher als der Lauf am 27.11.
- **Ausgeführt 24.11.2026** (OK des Auftraggebers): Probelauf 651 künftige Zeilen mit Rang ≥ 2 (3: 350, 4: 155,
  5: 146), 55 Quellenwechsel (43 aufs Haus), 301 Zeilen mit Änderungen. `--schreiben`: 300 geschrieben, 1 Fehler –
  „MOTORJESUS“ 02.01.2027 (AllEvents, 18:00) kollidiert mit der vorhandenen Pitcher-Zeile (19:00) am Unique-Index
  `titel, datum, ort, uhrzeit`; das ist eine Dublette für die Dubletten-Vorschläge im Admin, kein Fehler im Skript.
  Sicherung `data/quellen_nachziehen/sicherung_20261124_215537.json` (lokal im Worktree DD-quellen). Danach je Rang
  (künftig, nicht abgelehnt): 1: 991, 3: 350, 4: 129, 5: 128.

### W2 – Ausblick, Startseiten-Box, Ticket-Button, Ortswebsite (24.11.2026, lokal gebaut, Browser-Prüfung offen)

- `/ausblick` war im Repo noch frei (geprüft 24.11.). `web/lib/ausblick.ts`: Fernpool (Tag 61–365) gefiltert auf Rang
  1–2 (`rangGespeichert` ≤ `TICKETVERKAUF`), Orte mit Ortsseite (aktive Spielstätten über `ort_id`), ohne Absagen,
  nach Datum. `web/app/ausblick/page.tsx`: Liste nach Monaten, Filter-Chips je Kategorie (`?kategorie=`, dann noindex;
  leere Seite ebenfalls noindex), Titel „Ausblick: Große Events in Düsseldorf bis <Monat Jahr>“, JSON-LD-Liste.
- `ort_id` steht jetzt in `SPALTEN_BASIS` und in `normalisieren()` (bisher nur im Ortsprogramm geladen).
- Startseite: `AusblickStartBox` (6 Einträge, eigene Suspense-Grenze, ohne Einträge nichts) über dem Magazin.
- Navigation (Menü bei den Event-Links), Sitemap (feste Seiten), Proxy: `/ausblick` in Matcher **und** Bremse.
- Eventseite: zweiter Button „Tickets“ (`web/lib/ticket-button.ts`, `ticketZiel`): `ticket_url` des Hauses, sonst
  Rang-2-Quelle aus `quellen` (eigene gecachte Abfrage nur, wenn kein `ticket_url`); kein Button, wenn die Hauptquelle
  selbst Rang 2 ist oder das Ziel gleich dem Haupt-Button wäre; nur kommende, nicht abgesagte Events. `rel="noopener"`,
  ohne Stern – Partner-Kennung, „Tickets*“ und `rel="sponsored"` kommen mit P2.
- „Website von <Ort>“ (4.4): nur bei Hauptquelle Rang 5 (Rausgegangen) und `orte.webseite` über `ort_id`, über dem
  Quellenhinweis.
- JSON-LD `offers.url`: `ticket_url`, sonst `quelle_url` – immer die echte URL.
- Tests `web/tests/ausblick-tickets.test.ts`. Browser-Prüfung zusammen mit W1 nach dem Lauf am 27.11. (Turbopack läuft
  im Worktree nicht mit dem verlinkten node_modules; außerdem fehlen bis dahin die fernen Events).

### P2 – Partner-Links (24.11.2026, lokal gebaut, Schalter aus)

- `web/lib/tickets.ts`: Anbieter nur an den Hauptdomains (eventim.de, reservix.de, adticket.de, ticketmaster.de,
  tiqets.com, getyourguide.de/.com). Shops auf Subdomains, Eventim Light und Webshops der Häuser bleiben normale Links.
  Awin-Deeplink mit den Programmen 11388/31293/18490 und `AWIN_PUBLISHER_ID`. Ticketmaster nur mit
  `TICKETMASTER_PARTNER_OK=1` **und** einer Impact-Vorlage `TICKETMASTER_PARTNER_VORLAGE` (mit `{url}`). Tiqets
  `partner=`, GetYourGuide `partner_id=`. Fremde Kennungen des Hauses (`affiliate`, `utm_*`, `ref` …) werden vor dem
  Partner-Link entfernt. Ohne `PARTNERLINKS_AKTIV=1` oder ohne Kennung: normaler Link.
- Eventseite: Ticket-Button und – wenn die Hauptquelle selbst Rang 2 ist – der Haupt-Button laufen über
  `partnerLink`. Partner-Link → Text mit „*“, `rel="sponsored noopener"`, darunter der Hinweis mit Link auf
  `/ueber#partner-links`. JSON-LD bleibt die echte URL.
- `/ueber` (Abschnitt „Partner-Links“, du) und Datenschutzerklärung (Punkt in Abschnitt 9, Sie, ohne Umnummerierung)
  erscheinen nur, wenn ein Programm wirklich Links umbaut, und nennen nur diese Programme
  (`web/components/partner-links.tsx`). Texte zur Freigabe: `docs/partner-links-texte-2026-11-24.md`.
- Deploy schreibt `PARTNERLINKS_AKTIV`, `TICKETMASTER_PARTNER_OK`, `AWIN_PUBLISHER_ID`, `TICKETMASTER_PARTNER_VORLAGE`,
  `TIQETS_PARTNER_ID`, `GYG_PARTNER_ID` bei jedem Deploy ausdrücklich in `web/.env.local` (ohne sed). Admin → Technik
  zeigt `PARTNERLINKS_AKTIV` und `TICKETMASTER_PARTNER_OK`.
- Reihenfolge zum Einschalten: Anwalt gibt die Texte frei → Kennungen setzen → `PARTNERLINKS_AKTIV=1` → Deploy.
- **25.11.2026:** Texte für /ueber und Datenschutz vom Anwalt freigegeben (Mitteilung des Auftraggebers). Kennzeichnung
  am Button auf Wunsch des Auftraggebers geändert (er trägt das Risiko): kein Sternchen mehr, darunter nur
  „Partnerlink“ mit „i“-Tooltip (`PartnerHinweis` in `web/components/partner-links.tsx`, `<details>` ohne JavaScript,
  auf Geräten mit Maus auch beim Darüberfahren). Im Browser geprüft (lokal mit Testkennung).

### Cursor-Prüfung der Scraper-Neubauten (24.11.2026, nach T1-Fixes) – Einarbeitung

Cursor: 776 Tests grün, nicht abnahmefähig wegen zwei mittlerer Befunde; dazu drei geringe. Alle fünf eingearbeitet:
1. **mittel – Ticketmaster-Schlüssel im Log:** httpx-Fehlermeldungen enthalten die URL mit `?apikey=`. Jetzt loggt
   der HTTP-Fehler nur den Status, alle anderen Fehlermeldungen laufen durch `ohne_schluessel()`, und ein Filter am
   Logger `httpx` ersetzt den Schlüssel auch in den „HTTP Request“-Zeilen durch `***`.
2. **mittel – Zeitbudget Schritt 3b:** `beschreibungen_nachziehen` hat jetzt `max_sekunden` (2.400 s), Veranstalter
   4.200 s statt 5.400 s. Rechnung: Scraper inkl. neuer Quellen ~60 min, KI/Speichern ~30 min, Beschreibungen
   40 + 70 min → unter 200 der 240 Workflow-Minuten. Das Workflow-Limit bleibt.
3. **gering – Rückfall bei Ticket-Links:** neuer Baustein `ticket_link_haus()` (scraper/utils/ticket_link.py) für
   Felder/Buttons, die das Haus selbst als Ticketverkauf kennzeichnet: bekannte Anbieter wie bisher, andere
   http(s)-Hosts nur ohne Sperrliste (Rausgegangen, PayPal, Facebook/Instagram, WhatsApp, Google-Formulare,
   mailto/javascript), unbekannte Hosts im Debug-Log. Genutzt von Stadt Ratingen, Comedy Club, d.live, Mitsubishi,
   Pitcher, NRW-Forum und DEG.
4. **gering – Stagedates „Neusser Straße“:** `ist_im_gebiet` nutzt `pipeline.gebiet.adresse_im_gebiet`: eine PLZ
   entscheidet, sonst die Stadt als ganzes Wort (`stadt_im_gebiet`).
5. **gering – Ticketmaster ohne Stadt:** Fehlt `venue.city`, bleibt ein Event nur mit PLZ im Gebiet
   (`plz_im_gebiet`); die Stadtprüfung nutzt ebenfalls das ganze Wort.

Tests: `tests/test_cursor_scraper_2026_11_24.py` (9), Python gesamt 785 ok.

Nachprüfung durch Cursor (24.11.2026): alle fünf Befunde geschlossen, deploybar. Ein neuer geringer Befund – Stadtteile
mit Bindestrich („Düsseldorf-Benrath“, „Neuss-Holzheim“) fielen heraus, und jede fünfstellige Zahl galt als PLZ –
behoben: `stadt_im_gebiet` lässt einen Bindestrich nach dem Stadtnamen zu, `adresse_im_gebiet` wertet nur „PLZ Stadt“
am Anfang eines Adressabschnitts als PLZ, Ticketmaster behält ein Event mit PLZ im Gebiet unabhängig von der
Schreibweise der Stadt. Zwei Tests dazu, Python gesamt 787 ok.

### V2 – Welle B (25.11.2026, lokal gebaut)

Drei Hilfsagenten je Gruppe (Auftrag wie V1, ergänzt um `ticket_url`, `ticket_link_haus`, `adresse_im_gebiet`), Einbindung
durch Claude (main.py QUELLEN je Haus eine Zeile, config.VORSCHAU_TAGE, Rangtabelle Python/TS/Fixture, CLAUDE.md).

| Haus | Modul | Methode | Fenster | Ticket-Link |
|---|---|---|---|---|
| Robert Schumann Hochschule | rsh_hochschule | Liste + Details, fremde Orte mit eigener Adresse, Wuppertal/Radio weg | 120 | ja |
| Haus der Universität | haus_der_universitaet | Kalender + Details, Crawl-delay 10 | 120 | ja (selten) |
| Sammlung Philara | philara | Programmseite, Freitext-Daten | 120 | ja (Reservix) |
| Aquazoo Löbbecke Museum | aquazoo | JSON-API, Tagungen weg | 120 | nein |
| Hetjens-Museum | hetjens | JSON-API (gleiches CMS), Dauer-Suchspiel weg | 120 | nein |
| Filmwerkstatt Düsseldorf | filmwerkstatt | Startseite + Beitragsseiten | 120 | ja (xceed, Anbieter ergänzt) |
| Ratinger Hof | ratinger_hof | concertteam.de JSON + Details (Betreiber des Hauses) | 120 | ja |
| Boston Club | boston_club | handgepflegte Seite | 120 | nein |
| The Craft Studio | craft_studio | Playwright, Wix-Buchungskalender, community | 120 | ja (eigene Buchung) |
| Oberschlesisches Landesmuseum | oberschlesisches_landesmuseum | iCal (MEC), Termine außer Haus weg | 120 | nein |
| Rheinisches Landestheater Neuss | rheinisches_landestheater | Spielplan monatsweise, Gastspiele/Gruppenvorstellungen weg | 365 | ja (derticketservice, Anbieter ergänzt) |
| Globe Neuss | globe_neuss | Festival-Programm, nur Spielort Globe, sonst „saisonal“ | 365 | ja |
| LVR-Industriemuseum Cromford | lvr_cromford | Kalender-JSON, nur Standort Ratingen | 120 | Shop-Startseite |

Nicht gebaut (Gründe in den Berichten): Event-Theater Schwanenhöfe, Kloster Flingern, KLUB KULB, Gare du Neuss (keine
Termine); Düsseldorfer Marionetten-Theater (unvollständige Zertifikatskette, kein `verify=False`); Komödie Düsseldorf
(Domain übernommen, kein Spielplan); The Vinyl Room (iCal nur YouTube-Livestream); Eigenlob Keramik (nur offene Kurse);
Stadthalle/Zeughaus Neuss (neuss-marketing.de sperrt alle Bots). Möglicher Ersatz später: Kalender Kulturamt Neuss
(ZeughausKonzerte, ~4 je Spielzeit).

Live-Probe 25.11. mit den richtigen Fenstern: 392 Termine (RSH 61, HdU 29, Philara 4, Aquazoo 11, Hetjens 13,
Filmwerkstatt 6, Ratinger Hof 20, Boston Club 3, Craft Studio 73, OSLM 21, RLT 145, Globe 0 = außerhalb der Saison,
LVR 6), davon 167 mit Ticket-Link; Laufzeit zusammen 11,9 Minuten (HdU 5,6 min wegen Crawl-delay, RSH 3 min). Deshalb
Veranstalter-Beschreibungen 3.600 statt 4.200 s (main.py), damit der Lauf unter 200 Minuten bleibt.

Adresse Globe Neuss (Hammer Landstraße 2) vom Auftraggeber bestätigt (25.11.). Bilder des LVR von lvr.gomus.de
(Ticketsystem des LVR) und des Ratinger Hofs von concertteam.de (Betreiber) gelten als Website des Hauses.

Cursor-Prüfung V2 (25.11.2026): deploybar, drei geringe Befunde, alle behoben – Haus der Universität nimmt nur Termine
mit gelesener Detailseite (sonst bekäme ein Campus-Termin die Adresse am Schadowplatz; `MAX_DETAILS` begrenzt nur die
Abrufe); LVR Cromford ohne `ticket_url` (nur Shop-Startseite, kein Link je Termin); RSH wertet nur eigene Säle,
„Schumann-Hochschule“ und Fischerstraße als Haus, nicht das bloße Wort „Hochschule“. Tests
`tests/test_cursor_v2_2026_11_25.py`. Tests
876 Python ok.

### Welle C – Auswertung (25.11.2026, nur Prüfung, noch nicht gebaut)

- **Lücken nach N1:** nur noch 110 von 1.529 künftigen Events ausschließlich bei Rausgegangen (7 %), verteilt auf viele
  kleine Orte (höchstens 6 je Ort: hi sunny, UFA-Palast, Maxhaus, BrauArt, Cuvée …). Daraus lohnt keine eigene Welle.
- **Spielstätten ohne kommende Termine:** 109 von 241 (viele Welle-A/B-Häuser darunter, deren erster Lauf erst am 27.11.
  kommt). 15 Kandidaten nur lesend geprüft (je ≤ 4 Abrufe, robots beachtet). Lohnend:
  1. **Bürgerhaus Reisholz** – `duesseldorf.de/buergerhaeuser/reisholz/veranstaltungen`, ~10 Termine/4 Wochen, HTML, S;
     vermutlich gleiche Vorlage für die anderen städtischen Bürgerhäuser (ungeprüft).
  2. **Comedy für Freunde** – wöchentliche Profi-Testbühne (Mo 20 Uhr, Lupin Gin Bar), JSON-LD, S; nur der nächste
     Termin sichtbar.
  3. **Heine Haus Literaturhaus** – Startseite HTML, ~3–5 Termine/Monat, S (iCal unvollständig, nicht nutzen).
  4. optional **NRW-Akademie der Wissenschaften und der Künste** – S, aber nur ~3–4 öffentliche Termine.
- **Nein:** Niemandsland, Leica Galerie, ZERO foundation, reinraum, b41 (zu wenig/Freitext – eher von Hand);
  Storage Museum (robots.txt HTTP 500 = gesperrt); Einstein Boulderhalle (Kalender bei vertical-life, robots sperrt);
  Das Dazwischen, Sponk, ausARTen, Studio Brick (keine datierten Termine/nur JS); ASG-Bildungsforum (Kursprogramm);
  Berger Kirche, Henkel-Saal (keine eigene Programmseite).

## Prüfhistorie

- 23.11.2026: erste Fassung (Claude), Datenstand 23.11., Lauf vom 21.11.
- 24.11.2026: Antworten des Auftraggebers eingearbeitet (10), Provisions-Recherche (5.4), Namensvorschläge (6.4), Q18–Q19 neu
- 24.11.2026: dritte Fassung – Auftraggeber: alle Partner-Anbieter anbinden → 5.5, Q19–Q22, Schritte A1/P1/T2/T3/P2, Tests, Risiken
- 24.11.2026: dritte Fassung vom Auftraggeber freigegeben. Cursor-Prüfung (Anhang A) steht noch aus; Empfehlung: vor Schritt R1.
- 24.11.2026: Worktree auf origin (3f6a7ab, Admin-Plan komplett) gesetzt; Anhang A zur Prüfliste, Anhang B Prüfschleife Cursor ↔ Claude; „Knopf“ → „Button“
- 24.11.2026: Runde 1 – Cursor 18 Befunde (3 kritisch, 12 mittel, 3 gering), alle von Claude geprüft und angenommen; Claude 2 weitere (mittel), eingearbeitet
- 24.11.2026: Runde 2 – Cursor: Nr. 19 bestätigt mit geringem Gegenbefund, Nr. 20 mit mittlerem Gegenbefund; dazu Nr. 21–24 (mittel). Q1–Q22 unverändert.
- 24.11.2026: Runde 2 – Claude: alle 6 Cursor-Änderungen gegen den Code geprüft und angenommen; Nr. 25 (gering) ergänzt, Rückfrage Nr. 26 technisch entschieden
- 24.11.2026: Runde 3 – Cursor: Nr. 25 bestätigt mit Ergänzung (gering), Nr. 26 bestätigt. Dazu Nr. 27–32 (mittel) und Nr. 33 (gering). Q1–Q22 unverändert.
- 24.11.2026: Runde 3 – Claude: alle Änderungen gegen den Code geprüft und angenommen; Nr. 34 (gering, Ticketmaster-Bilder) ergänzt
- 24.11.2026: Runde 4 – Cursor: Nr. 34 bestätigt, Anfrage-Aufzählung korrigiert. Nr. 35 und 36 mittel (Z1-Seitengrenzen, ein Nachziehen N1). Nr. 37 gering (Test für leeres Ticketmaster-Bild). Q1–Q22 unverändert.
- 24.11.2026: Runde 4 – Claude: alle 4 Änderungen gegen den Code geprüft (`ticketmaster.py:202`, `web/app/bild/event/[id]/route.ts:43`, `web/lib/bild-proxy.ts:213`) und angenommen; keine eigenen Befunde.
- 24.11.2026: Runde 5 – Cursor: Nr. 35 und 36 sind in 4.2, 5.2, Abschnitt 7, Rückweg, Abnahme und Tests ohne widersprechenden Satz. Keine kritischen oder mittleren Befunde.
- 24.11.2026: Runde 5 – Claude bestätigt. **Prüfschleife Cursor ↔ Claude abgeschlossen** (5 Runden, 37 Befunde eingearbeitet). Der Plan ist baufertig; gebaut wird schrittweise nach Abschnitt 7 mit OK je Schritt.
