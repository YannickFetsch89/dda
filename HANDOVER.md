# DiesDasDüsseldorf – Handover-Dokument

**Stand:** 27. Oktober 2026  
**Branch:** `claude/setup-project-structure-5QNOf`  
**Letzter Commit:** `370dbe9` – Stadtteil-Mapper erweitert  
**Repository:** https://github.com/YannickFetsch89/dda

---

## 1. Projektstatus – Was bereits fertig ist

### Scraper-System (45 Scraper, ~29 funktionsfähig)
Die komplette Scraper-Infrastruktur für 3 Tiers steht und liefert aktuell **~930+ Events** pro Lauf.

**Tier 1 – Aggregatoren (10 Scraper):**
| Scraper | Status | Events | Methode |
|---|---|---|---|
| Rausgegangen | OK (Parser-Bug bei "© Eventim") | ~375 | Playwright |
| Kulturportal | OK | ~12 | Playwright |
| VisitDüsseldorf | OK | variabel | Playwright |
| Meetup | OK | variabel | API |
| Resident Advisor | OK | variabel | httpx |
| PRINZ.de | OK | ~98 | httpx |
| AllEvents.in | OK | ~40 | Playwright |
| Bandsintown | KAPUTT (Cloudflare-Block) | 0 | – |
| Ticketmaster | DEAKTIVIERT (kein API Key) | – | – |
| Songkick | DEAKTIVIERT (kein API Key) | – | – |

**Tier 2 – Venue-Scraper (23 Scraper):**
| Scraper | Status | Events |
|---|---|---|
| Tonhalle | OK | variabel |
| zakk | OK | variabel |
| Oper am Rhein | OK | variabel |
| Schauspielhaus | OK | variabel |
| d.live | OK | variabel |
| Kunstpalast | OK | ~31 |
| Kunstsammlung NRW | OK | ~3 |
| NRW-Forum | OK | ~6 (Lit Shadow DOM) |
| FFT Düsseldorf | OK | ~19 |
| Stahlwerk | OK | ~3 |
| Kunsthalle | OK | ~8 |
| Filmmuseum | OK | ~15 |
| Stadtbüchereien | OK | ~87 |
| Tanzhaus NRW | OK | ~9 |
| Capitol Theater | OK | ~11 |
| Kom(m)ödchen | OK | ~14 (Playwright, Sucuri WAF) |
| STARTPLATZ | OK | variabel |
| Jazz-Schmiede | OK | variabel |
| Rudas Studios | KAPUTT (502 Server offline) | 0 |
| Mitsubishi Electric HALLE | OK | variabel |
| Kulturschlachthof R25 | OK | variabel |
| Salon des Amateurs | OK | variabel |
| Pitcher | KAPUTT (503 offline) | 0 |

**Tier 3 – Nischen (12 Scraper):**
| Scraper | Status | Notiz |
|---|---|---|
| Parkrun | OK | Statischer Eintrag, jeden Sa. |
| Street Food Thursday | SAISONAL | März–Oktober |
| Sport im Park | SAISONAL | Sommer |
| Fortuna Düsseldorf | OK | ~1 Event |
| DEG Eishockey | OK | variabel |
| Messe Düsseldorf | OK | ~4 (60-Tage-Fenster) |
| IHK Düsseldorf | OK | ~10 |
| StartupDorf | OK | variabel |
| Stadtstrand | SAISONAL | Mai–September |
| Japan Center | KAPUTT (503 offline) | 0 |
| Classic Remise | KAPUTT (503 offline) | 0 |
| Spontacts | KAPUTT (Plattform eingestellt) | 0 |

### Pipeline
- **Deduplication** (`pipeline/deduplication.py`) – Fuzzy Matching über Titel+Datum+Ort
- **Kategorisierung** (`pipeline/categorizer.py`) – Claude API (claude-sonnet-4-6)
- **Caption Generator** (`pipeline/caption_generator.py`) – Claude API
- **Stadtteil-Zuordnung** (`pipeline/stadtteil_mapper.py`) – 4-stufig: Quelle → Venue-Name → PLZ → Straße
- **Publisher** (`pipeline/publisher.py`) – Instagram Graph API (noch nicht konfiguriert)

### Datenbank (Supabase)
- **Projekt-ID:** `dqckcszxoyaxiwwcgxxk`
- **URL:** `https://dqckcszxoyaxiwwcgxxk.supabase.co`
- **WICHTIG:** Das Projekt ist NICHT mit dem Supabase MCP verknüpft – DDL-Änderungen müssen über das Supabase Dashboard (SQL Editor) gemacht werden
- **Aktuell:** ~1236 Events in DB, davon 761 mit Stadtteil-Zuordnung (61%)
- **Schema:** Siehe `database/schema.sql` – alle Migrationen sind applied

Spalten der `events`-Tabelle:
```
id, titel, datum, uhrzeit, ort, adresse, kategorie, beschreibung, preis,
quelle_name, quelle_url, bild_url, instagram_caption, datum_bis,
ist_wiederkehrend, status, erstellt_am, gepostet_am,
instagram_location_id, abgelehnt, tipp_des_tages, highlight_der_woche,
top_event_des_monats, stadtteil
```

### Dashboard (Admin-Backend)
- **URL:** https://admin.diesdas.events (Streamlit, Port 8502 hinter nginx)
- **Datei:** `dashboard/app.py`
- **Features:** Event-Liste mit Filter (Kategorie, Stadtteil, Datum), Opt-out (ablehnen), Featured-Tiers (Tipp des Tages etc.)
- **Eigene Requirements:** `dashboard/requirements.txt`

### Server-Deployment
- **Server:** Timme Hosting Managed VServer (`k49q02.meinserver.io`)
- **User:** `dies_das_duesseldorfadmin`
- **ISPConfig:** admin.diesdas.events als eigene Website mit nginx Reverse Proxy
- **Python:** 3.11 via `uv` (kein root, daher nicht via apt)
- **Workaround:** `libutil.so.1` Symlink auf `libc.so.6` (Debian 12)
- **LD_LIBRARY_PATH:** `/home/dies_das_duesseldorfadmin/.local/lib`
- **Prozess-Management:** `disown` (kein nohup/screen/tmux verfügbar)
- **Cronjob:** via ISPConfig Web-Interface (nicht crontab)
- **Pfad auf Server:** `/home/dies_das_duesseldorfadmin/dda`

### GitHub Actions
- **Datei:** `.github/workflows/deploy.yml`
- **Trigger:** Push auf `claude/setup-project-structure-5QNOf`
- **NOCH NICHT AKTIV** – GitHub Secrets fehlen noch:
  - `SERVER_HOST` → `k49q02.meinserver.io`
  - `SERVER_USER` → `dies_das_duesseldorfadmin`
  - `SERVER_SSH_KEY` → SSH Private Key (muss noch generiert werden)

---

## 2. Was noch NICHT fertig ist (Offene Aufgaben)

### Priorität 1 – Sofort nötig
1. **Website-Frontend** – Der User hat ein Brand Identity Briefing als ZIP-Datei (`DiesDasDüsseldorf Brand Identity.zip`) auf seinem lokalen Rechner. Das muss eingelesen und als Basis für die Website-Umsetzung verwendet werden. → **Das war der aktuelle Task als die Session endete.**

2. **Visual Pipeline fehlt komplett** – Das gesamte `visual/`-Verzeichnis existiert noch nicht:
   - `visual/brand.py` – Brand Identity (Farben, Fonts, Logo-Pfad)
   - `visual/image_renderer.py` – Pillow: Event-Bild + Brand-Overlay
   - `visual/image_generator.py` – DALL-E 3: KI-Bild wenn kein Bild vorhanden
   - `visual/reel_renderer.py` – ffmpeg: Standbild-Reel
   - `assets/templates/` – Canva-Export-Templates
   - `assets/logo/` – DDA-Logo

3. **Anthropic API Credits aufladen** – Caption-Generierung schlägt fehl ("credit balance is too low")

### Priorität 2 – Konfiguration
4. **GitHub Actions Secrets** einrichten (SERVER_HOST, SERVER_USER, SERVER_SSH_KEY)
5. **SSH Deploy Key** auf Server generieren und zu GitHub hinzufügen
6. **Instagram Graph API Token** konfigurieren (noch nicht eingerichtet)
7. **SSL/Let's Encrypt** für admin.diesdas.events (zeigt "Nicht sicher")
8. **Playwright System-Libs** auf Server (libnss3 etc.) – Timme Support kontaktieren

### Priorität 3 – Verbesserungen
9. **Rausgegangen-Scraper** – Parser-Bug: ~73 Events haben "© Eventim" oder "© EventimAbgesagt" als Ort-Wert statt echtem Venue-Namen
10. **Meetup-Scraper** – Venue-Adresse aus API-Daten extrahieren für bessere Stadtteil-Zuordnung
11. **Stadtteil-Mapping erweitern** – Aktuell 61% Trefferquote, Rest sind Müll-Daten oder unbekannte Venues

---

## 3. Wichtige technische Details

### Playwright Sync/Async-Konflikt
`main.py` ist `async` (`asyncio.run()`). Scraper die Playwright Sync API nutzen (rausgegangen, kulturportal, allevents, bandsintown, nrw_forum, pitcher, kommoedchen) werden mit `await asyncio.to_thread(module.scrape)` aufgerufen.

### Supabase Client (database/client.py)
- Singleton-Pattern
- Intelligentes Upsert: Duplikat-Erkennung über Titel+Datum+Ort
- Anreicherung: fehlende Felder werden bei Duplikaten ergänzt
- Rausgegangen-Bilder werden durch bessere Quellen ersetzt
- `_NICHT_IN_DB`-Set filtert Spalten raus die noch nicht in der DB existieren

### Stadtteil-Mapper (pipeline/stadtteil_mapper.py)
4-stufige Zuordnung:
1. **Venue-Name** (~110 Mappings) – Substring-Match, längster Key zuerst
2. **Quelle** (26 Mappings) – Tier-2-Scraper = Venue bekannt
3. **PLZ** (~30 Mappings) – Regex `40xxx` aus Adresse
4. **Straßenname** (~25 Mappings) – bekannte Düsseldorfer Straßen

### Scraper-Struktur
- Alle Scraper haben `def scrape()` oder `async def scrape()` als Einstiegspunkt
- Rückgabe: `list[dict]` im DDD Event-Format (siehe CLAUDE.md)
- Pflichtfelder: titel, datum, ort, kategorie, quelle_name, quelle_url

---

## 4. Dateistruktur (aktuell)

```
dda/
├── CLAUDE.md                     ← Projekt-Anweisungen (sehr ausführlich!)
├── HANDOVER.md                   ← Diese Datei
├── main.py                       ← Pipeline-Einstiegspunkt (async)
├── config.py                     ← Konfiguration
├── requirements.txt
├── .env.example
├── .github/workflows/deploy.yml  ← Auto-Deploy (noch nicht aktiv)
│
├── agents/                       ← Agent-Anweisungen
│   ├── architect/CLAUDE.md
│   ├── developer/CLAUDE.md
│   ├── qa/CLAUDE.md
│   ├── refactor/CLAUDE.md
│   └── orchestrator/CLAUDE.md
│
├── scraper/
│   ├── tier1/                    ← 15 Dateien (10 aktiv)
│   ├── tier2/                    ← 23 Dateien
│   └── tier3/                    ← 12 Dateien
│
├── pipeline/
│   ├── deduplication.py
│   ├── categorizer.py
│   ├── caption_generator.py
│   ├── publisher.py
│   ├── stadtteil_mapper.py       ← NEU: 4-stufiges Mapping
│   └── stadtteil_backfill.py     ← NEU: Backfill-Skript
│
├── database/
│   ├── schema.sql                ← Alle Migrationen enthalten
│   └── client.py                 ← Supabase-Verbindung + Upsert-Logik
│
├── dashboard/
│   ├── app.py                    ← Streamlit Admin-Dashboard
│   └── requirements.txt
│
├── visual/                       ← EXISTIERT NOCH NICHT
├── assets/                       ← EXISTIERT NOCH NICHT
├── tests/                        ← Leer
└── logs/
```

---

## 5. Umgebungsvariablen (.env)

```env
SUPABASE_URL=https://dqckcszxoyaxiwwcgxxk.supabase.co
SUPABASE_KEY=<anon key vorhanden>
ANTHROPIC_API_KEY=<vorhanden, aber Credits aufgebraucht>
OPENAI_API_KEY=<Status unbekannt>
INSTAGRAM_ACCESS_TOKEN=<nicht konfiguriert>
INSTAGRAM_ACCOUNT_ID=<nicht konfiguriert>
TICKETMASTER_API_KEY=<nicht konfiguriert>
MEETUP_API_KEY=<vorhanden>
SONGKICK_API_KEY=<nicht konfiguriert>
LOG_LEVEL=INFO
```

---

## 6. Aktueller Task / Nächster Schritt

**Der User möchte die Website (Frontend) für diesdas.events bauen.**

Er hat ein Brand Identity Briefing als ZIP-Datei auf seinem lokalen Rechner:
`C:\Users\YannickFetsch\Downloads\DiesDasDüsseldorf Brand Identity.zip`

Diese Datei enthält das Corporate Design / die Brand Identity, die als Grundlage für das Website-Design dienen soll. Der User hat die Session gewechselt, weil er die ZIP-Datei lokal öffnen/teilen muss.

**Schritte:**
1. Brand Identity ZIP einlesen und analysieren
2. Website-Frontend konzipieren und umsetzen (basierend auf dem Briefing)
3. Events aus Supabase auf der Website anzeigen
4. Stadtteil-Clustering auf der Website integrieren
5. Design gemäß Brand Identity anwenden

---

## 7. Bekannte Workarounds & Fallstricke

- **Server hat kein root** – alles über uv/pip im venv, keine apt-Pakete
- **kein nohup/screen/tmux** – Prozesse mit `command & disown $!` backgrounden
- **kein crontab** – Cronjobs über ISPConfig Web-Interface
- **Supabase pausiert bei Inaktivität** – manuell im Dashboard reaktivieren
- **Playwright braucht System-Libs** – auf dem Server fehlen libnss3 etc., daher laufen Playwright-Scraper dort nur eingeschränkt
- **Rausgegangen "© Eventim" Bug** – Scraper parst gelegentlich Sponsor-Text statt Venue-Name
