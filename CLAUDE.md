# DiesDasDüsseldorf – Projekt CLAUDE.md

## Was dieses Projekt ist
DiesDasDüsseldorf ist ein vollautomatisiertes Event-Aggregations- und Publishing-System für Düsseldorf. Es sammelt täglich Events und Aktivitäten aus der Stadt, bereitet sie mit KI auf und veröffentlicht sie als Instagram-Posts. Langfristig wird daraus eine App und ein täglicher Stadtguide.

## Aktueller Entwicklungsstand
**Phase 1:** Instagram-Pipeline + Supabase Datenbank
- Scraper und API-Anbindungen für alle Datenquellen
- KI-basierte Aufbereitung und Kategorisierung der Events
- Automatisches Erstellen von Instagram-Captions (Feed-Posts & Reels)
- Visuelle Pipeline: Canva-Templates + Python/Pillow Overlay + DALL-E 3 Fallback
- Brand Identity wird auf jedem Post automatisch angewendet
- Speicherung aller Events in Supabase
- Automatisches Posting direkt via Instagram Graph API (kein Drittanbieter)

## Tech Stack
- **Sprache:** Python 3.11
- **Datenbank:** Supabase (PostgreSQL)
- **KI Text:** Claude API (claude-sonnet-4-6) für Caption-Erstellung und Kategorisierung
- **KI Bild:** OpenAI API (DALL-E 3) als Fallback-Bildgenerierung wenn kein Event-Bild vorhanden
- **Scraping:** Playwright (für dynamische Seiten), httpx + BeautifulSoup (für statische Seiten)
- **Bildverarbeitung:** Pillow – Brand-Overlay auf Canva-Templates (Logo, Farben, Kategorie-Badge)
- **Video (Reels):** ffmpeg (Systemabhängigkeit) für Reel-Rendering
- **Design-Templates:** Canva Pro – einmalige Gestaltung der Vorlagen, Export als PNG/SVG
- **Scheduling:** APScheduler oder cron (täglich 06:00 Uhr)
- **Posting:** Instagram Graph API (direkt – Feed-Posts & Reels, kein Drittanbieter)
- **Hosting:** Railway oder Render
- **Versionskontrolle:** GitHub

## Output-Sprache
Ausschließlich Deutsch. Alle generierten Texte, Captions, Beschreibungen und Logs auf Deutsch.

## Datenstruktur – Event-Objekt (Pflichtfelder)
```json
{
  "id": "uuid",
  "titel": "string",
  "datum": "ISO 8601 (YYYY-MM-DD)",
  "uhrzeit": "HH:MM oder null",
  "ort": "string (Venue-Name)",
  "adresse": "string oder null",
  "kategorie": "enum (siehe unten)",
  "beschreibung": "string (max. 300 Zeichen)",
  "preis": "string oder null (z.B. 'kostenlos', 'ab 12€')",
  "quelle_name": "string (z.B. 'Rausgegangen')",
  "quelle_url": "string (Original-URL des Events)",
  "bild_url": "string oder null",
  "bild_generiert": "boolean (true = DALL-E generiert, false = Original vom Veranstalter)",
  "post_typ": "enum: feed | reel",
  "instagram_caption": "string oder null (wird von KI befüllt)",
  "instagram_location_id": "string oder null (Facebook Location ID für Standort-Tag)",
  "status": "enum: neu | aufbereitet | gepostet | fehler",
  "erstellt_am": "ISO 8601 timestamp",
  "gepostet_am": "ISO 8601 timestamp oder null"
}
```

## Kategorien (enum)
- `kultur` – Ausstellungen, Theater, Oper, Literatur, Film
- `musik` – Konzerte, DJ-Sets, Live-Musik, Clubbing
- `food` – Food Events, Märkte, Tastings, Restaurant-Events
- `sport` – Sportevents, Outdoor-Fitness, Laufen, Klettern
- `outdoor` – Natur, Parks, Spaziergänge, saisonale Aktivitäten
- `community` – Meetups, Networking, Workshops, Mitmachevents
- `nightlife` – Partys, Clubs, Late-Night-Events
- `family` – Kinder- und Familienevents
- `dating` – Speed Dating, Singles Events, Flirt-Abende
- `sonstiges` – Alles was nicht passt

---

## Datenquellen

### TIER 1 – Primärquellen (Pflicht, täglich)

#### Aggregatoren mit Scraping
| Name | URL | Methode |
|---|---|---|
| Rausgegangen | rausgegangen.de/duesseldorf | Playwright Scraper |
| visitduesseldorf.de | visitduesseldorf.de/erleben/veranstaltungen | Playwright Scraper |
| Kulturportal Düsseldorf | kulturportal-duesseldorf.de | Playwright Scraper |
| meinestadt.de | veranstaltungen.meinestadt.de/duesseldorf | Playwright Scraper |
| eventfinder.de | eventfinder.de/veranstaltungen-duesseldorf | Playwright Scraper |
| PRINZ.de Düsseldorf | prinz.de/duesseldorf/events | HTML Scraper (täglich) |
| AllEvents.in | allevents.in/dusseldorf | HTML Scraper (täglich) |

#### APIs (kostenlos, strukturiert)
| Name | API-Docs | Auth |
|---|---|---|
| Ticketmaster | developer.ticketmaster.com | API Key |
| Eventbrite | eventbrite.com/platform/api | OAuth Token |
| Meetup.com | meetup.com/api | API Key |
| Resident Advisor (RA) | ra.co/api (inoffiziell) | Scraping-Fallback |
| Songkick | songkick.com/developer (Metro Area ID: 28470) | API Key (SONGKICK_API_KEY) |
| Bandsintown | bandsintown.com/c/dusseldorf-germany | HTML Scraper (kein Key nötig) |

---

### TIER 2 – Venue-eigene Kalender (direkte Scraper)

#### Musik & Nightlife
| Venue | URL |
|---|---|
| Stahlwerk Düsseldorf | stahlwerk-duesseldorf.de |
| Tonhalle Düsseldorf | tonhalle.de/programm |
| zakk | zakk.de/programm |
| Rudas Studios | rudas-studios.de |
| Kulturschlachthof R25 | kulturschlachthof.de |
| Salon des Amateurs | salonamateurs.de |
| Pitcher Rock HQ | pitcher.de |
| Jazz-Schmiede Düsseldorf | jazz-schmiede.de/veranstaltungen |

#### Große Venues / Arenen
| Venue | URL |
|---|---|
| d.live (Merkur Arena + PSD BANK DOME) | d-live.de/events |
| Mitsubishi Electric HALLE | mitsubishi-electric-halle.de |
| Capitol Theater Düsseldorf | capitol-theater.de/programm-tickets |

#### Kultur & Theater
| Institution | URL |
|---|---|
| Deutsche Oper am Rhein | operamrhein.de/spielplan |
| Düsseldorfer Schauspielhaus | dhaus.de/spielplan |
| FFT Düsseldorf | fft-duesseldorf.de/programm |
| Kunstpalast | kunstpalast.de/de/programm |
| Kunstsammlung NRW (K20/K21) | kunstsammlung.de/programm |
| NRW-Forum | nrw-forum.de/veranstaltungen |
| Kunsthalle Düsseldorf | kunsthalle-duesseldorf.de |
| Filmmuseum / Black Box Kino | duesseldorf.de/filmmuseum |
| Stadtbüchereien Düsseldorf | duesseldorf.de/stadtbuechereien/veranstaltungen |
| Tanzhaus NRW | tanzhaus-nrw.de/calendar |
| Kom(m)ödchen | kommoedchen.de/spielplan |

#### Community & Business
| Institution | URL |
|---|---|
| STARTPLATZ Düsseldorf | startplatz.de/events |

---

### TIER 3 – Nischen & Spezialquellen (wöchentlich)

| Quelle | Typ | Methode |
|---|---|---|
| Parkrun Düsseldorf (Volksgarten) | Sport, jeden Sa. 9 Uhr | Statischer Eintrag |
| Sport im Park Düsseldorf | Outdoor-Fitness, kostenlos | duesseldorf.de/sportamt Scraper |
| Fortuna Düsseldorf | Fußball Heimspiele | fortuna-duesseldorf.de |
| DEG (Eishockey) | Heimspiele | deg-hockey.de |
| Messe Düsseldorf | Leitmessen | messe-duesseldorf.de/events |
| Japan Center Düsseldorf | Japanische Kulturevents | japan-duesseldorf.de |
| Classic Remise | Oldtimer + Kulturevents | classic-remise.de |
| Stadtstrand Düsseldorf | Saisonale Events (ab Frühjahr) | stadtstrand-duesseldorf.de |
| Spontacts Düsseldorf | Freizeitaktivitäten | spontacts.de |
| IHK Düsseldorf | Business-Events | duesseldorf.ihk.de/veranstaltungen |
| StartupDorf (Meetup) | Startup-Community | meetup.com/startupdorf |
| Street Food Thursday | Food-Event, monatlich (Stahlwerk, 2. Do. im Monat) | Statisch + Scraping-Fallback |

---

### TIER 4 – Social & Community (wöchentlich manuell prüfen)
- Instagram Hashtags: #düsseldorf #düsseldorftoday #dusevents #diesunddas
- Facebook Events Düsseldorf (via Apify wenn nötig)
- Google Events SERP (Suche: "Events Düsseldorf [Datum]")

---

## Projektstruktur
```
diesdasduesseldorf/
│
├── CLAUDE.md                        ← Diese Datei
│
├── agents/
│   ├── architect/CLAUDE.md
│   ├── developer/CLAUDE.md
│   ├── qa/CLAUDE.md
│   ├── refactor/CLAUDE.md
│   └── orchestrator/CLAUDE.md
│
├── scraper/
│   ├── tier1/                       ← Täglich laufende Scraper
│   ├── tier2/                       ← Venue-eigene Scraper
│   └── tier3/                       ← Nischen-Quellen
│
├── pipeline/
│   ├── deduplication.py             ← Duplikate entfernen
│   ├── categorizer.py               ← KI-Kategorisierung
│   ├── caption_generator.py         ← Instagram-Captions generieren (Claude API)
│   └── publisher.py                 ← Instagram Graph API – Feed-Posts & Reels
│
├── visual/
│   ├── brand.py                     ← Brand Identity (Farben, Fonts, Logo-Pfad)
│   ├── image_renderer.py            ← Pillow: Canva-Template + Event-Bild + Brand-Overlay
│   ├── image_generator.py           ← DALL-E 3: KI-Bild generieren wenn kein Bild vorhanden
│   └── reel_renderer.py             ← ffmpeg: Standbild-Reel aus fertigem Bild erstellen
│
├── assets/
│   ├── templates/                   ← Canva-Exporte (PNG/SVG Rohdateien, einmalig erstellt)
│   │   ├── feed_template.png        ← Feed-Post Template (1080x1080px)
│   │   └── reel_template.png        ← Reel Template (1080x1920px)
│   └── logo/
│       └── dda_logo.png             ← DDA Logo für Overlay
│
├── database/
│   ├── schema.sql                   ← Supabase Tabellenstruktur
│   └── client.py                    ← Supabase-Verbindung
│
├── tests/                           ← QA Agent legt Tests hier ab
│
├── logs/                            ← Tägliche Run-Logs
│
├── config.py                        ← Konfiguration (keine Secrets!)
├── .env.example                     ← Vorlage für Umgebungsvariablen
├── requirements.txt
└── main.py                          ← Einstiegspunkt, startet Pipeline
```

---

## Globale Regeln für alle Agents

### Code-Qualität
- Alle Kommentare und Docstrings auf **Deutsch**
- Alle Log-Ausgaben auf **Deutsch**
- Fehlerbehandlung bei JEDER externen Anfrage (try/except)
- Niemals Secrets oder API Keys im Code – immer über `.env`
- Keine Bibliotheken ohne explizite Rückfrage installieren

### Scraping-Regeln
- Rate Limiting: mindestens 2 Sekunden zwischen Requests
- User-Agent setzen (realistischer Browser-String)
- Bei HTTP 429 (Too Many Requests): exponentielles Backoff
- Robots.txt respektieren – bei Unklarheit den Architect fragen

### Daten-Regeln
- Pflichtfelder müssen immer befüllt sein (kein None bei titel, datum, ort, kategorie)
- Datum immer als ISO 8601 speichern
- Duplikate anhand von titel + datum + ort erkennen
- Events die älter als heute sind werden nicht gespeichert

### Output-Regeln

#### Captions (Feed & Reels)
- Instagram Captions: max. 2200 Zeichen
- Ton: locker, einladend, keine Werbsprache, kein Clickbait
- Immer mit Datum, Uhrzeit und Ort beginnen
- Mindestens 5 relevante Hashtags am Ende
- Verlinkungen: Venue-Account per @Mention taggen wenn bekannt
- Kein Klick-Link in der Caption (Instagram sperrt das) – stattdessen "Link in Bio"

#### Bilder & Visuals
- Jeder Post bekommt ein Bild: entweder vom Veranstalter oder DALL-E 3 generiert
- Jedes Bild bekommt den Brand-Overlay (Logo, Kategorie-Badge, Farbstreifen)
- Brand-Farben, Fonts und Logo sind in `visual/brand.py` definiert – nie hardcoden
- Canva-Templates werden nur manuell angepasst (nicht automatisch) – bei Bedarf Architect fragen

#### Reels
- Format: 1080x1920px, MP4, mind. 3 Sekunden, max. 90 Sekunden
- Phase 1: Standbild-Reel (ein Bild als kurzes Video via ffmpeg)
- Standort-Tag via `instagram_location_id` im Graph API Request setzen wenn vorhanden

### Kommunikation
- Bei Unklarheiten **immer fragen**, nie raten
- Nach jedem abgeschlossenen Task kurze Zusammenfassung ausgeben
- Fehler vollständig mit Ursache und Lösungsvorschlag dokumentieren
