# DiesDasDüsseldorf – Plan: Statische Inhalte + Chatbot

## Übersicht

Erweiterung der Website um permanente, KI-recherchierte Inhalte als Mehrwert gegenüber reinen Event-Aggregatoren. Inhalte werden vollautomatisch recherchiert und aufbereitet – manuelle Kuration nur als letzter Schritt.

---

## Content-Typen (nach Priorität)

| Prio | Typ | Route | Beschreibung |
|------|-----|-------|-------------|
| A | Restaurants & Cafés | `/restaurants` | Ausgewählte, stylische Adressen à la Mister Düsseldorf |
| B | Ausflugstipps | `/ausfluege` | Tagesausflüge innerhalb von 1 Stunde ab Düsseldorf |
| C | Spielplatz-Guide | `/spielplaetze` | Kartenansicht, Ausstattung, Altersgruppen, Schatten |
| C | Kneipenguide | `/kneipen` | Kuratierte Bar-Empfehlungen |
| C | Clubguide | `/clubs` | Clubbing-Empfehlungen mit Musikrichtung |
| D | Wochenendtipps | `/wochenendtipps` | Trips bis max. 4 Stunden ab Düsseldorf |
| A/B | AI-Chatbot | `/chat` | "Was machen wir heute?" – personalisierte Tipps |

---

## Datenmodell – Tabelle `orte`

```sql
CREATE TABLE orte (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE,
  typ TEXT NOT NULL CHECK (typ IN ('restaurant', 'cafe', 'kneipe', 'club', 'spielplatz', 'ausflug', 'wochenendtipp')),
  untertitel TEXT,
  beschreibung TEXT,
  highlight TEXT,
  adresse TEXT,
  stadtteil TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  bild_url TEXT,
  bild_attribution TEXT,
  tags TEXT[],
  preis_niveau TEXT CHECK (preis_niveau IN ('€', '€€', '€€€')),
  oeffnungszeiten TEXT,
  webseite TEXT,
  instagram TEXT,
  google_place_id TEXT,
  google_rating NUMERIC(2,1),
  google_bewertungen_anzahl INTEGER,
  qualitaets_score INTEGER CHECK (qualitaets_score BETWEEN 1 AND 10),
  extras JSONB DEFAULT '{}',
  sortierung INTEGER DEFAULT 0,
  aktiv BOOLEAN DEFAULT false,
  erstellt_am TIMESTAMPTZ DEFAULT now(),
  aktualisiert_am TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_orte_typ ON orte (typ);
CREATE INDEX idx_orte_stadtteil ON orte (stadtteil);
CREATE INDEX idx_orte_aktiv ON orte (aktiv) WHERE aktiv = true;
```

### `extras` (JSONB) je Typ

| Typ | Felder |
|-----|--------|
| restaurant / cafe | `kueche`, `reservierung_url`, `highlight_gericht`, `terrasse` |
| spielplatz | `altersgruppe`, `schatten`, `ausstattung[]`, `wc_vorhanden` |
| kneipe | `spezialitaet`, `happy_hour`, `raucherbereich` |
| club | `musikrichtung`, `dresscode`, `eintritt_ab` |
| ausflug | `entfernung_min`, `anreise`, `dauer_h`, `saison` |
| wochenendtipp | `entfernung_min`, `anreise`, `uebernachtung`, `dauer_tage` |

---

## Research-Pipeline (4 Stufen)

### Stufe 1: Discovery

**Restaurants/Cafés/Kneipen/Clubs** – Google Places API (Nearby Search):
- Suchradius: Düsseldorf Stadtgebiet (51.2277° N, 6.7735° E, r=10km)
- Suchbegriffe pro Typ: `restaurant`, `cafe`, `bar`, `night_club`
- Filter: Mindestens 4.0 Sterne, mindestens 30 Bewertungen
- Erwartetes Ergebnis: ~300-500 Restaurants, ~100-150 Cafés, ~80-120 Kneipen, ~20-40 Clubs

**Spielplätze** – OpenStreetMap Overpass API:
- Query: `leisure=playground` im Stadtgebiet Düsseldorf
- Liefert: Koordinaten, Ausstattungs-Tags (sandbox, swing, slide, etc.)
- Erwartetes Ergebnis: ~200-300 Spielplätze

**Ausflüge/Wochenendtipps** – Claude-Recherche:
- Claude erstellt kuratierte Liste basierend auf Wissen + Web-Recherche
- Google Places API für Details + Fotos zu jedem Ziel
- Erwartetes Ergebnis: ~30 Ausflüge (< 1h), ~20 Wochenendtipps (< 4h)

### Stufe 2: Enrichment

Pro Ort via Google Places Details API:
- Name, Adresse, Koordinaten, Stadtteil (via bestehender Stadtteil-Mapper-Logik)
- Öffnungszeiten, Webseite, Telefon
- Preisniveau (€/€€/€€€)
- Bis zu 5 echte Fotos (User-/Inhaber-Fotos)
- Bewertungen: Durchschnitt + ausgewählte Reviews als Input für Claude

### Stufe 3: KI-Aufbereitung (Claude)

Claude bekommt pro Ort alle Rohdaten + die 3-5 besten Google-Bewertungen.

Output pro Ort:
- `beschreibung` (150-300 Zeichen, authentischer Empfehlungston)
- `untertitel` (z.B. "Japanisch · Flingern · €€")
- `tags[]` (z.B. ["romantisch", "terrasse", "brunch"])
- `highlight` (ein Satz, warum dieser Ort besonders ist)
- `qualitaets_score` (1-10, basierend auf Bewertungen + Einzigartigkeit)
- Spielplatz-spezifisch: `altersgruppe`, `schatten`, Ausstattungsliste

### Stufe 4: Kuration (Dashboard)

Erweiterung des Streamlit-Dashboards:
- Neue Seite "Orte kuratieren"
- Tabellarische Ansicht aller neuen Vorschläge
- Pro Ort: Foto-Vorschau, Claude-Beschreibung, Score, Tags
- Aktionen: Genehmigen / Bearbeiten / Verwerfen
- Bulk-Aktionen: "Alle mit Score ≥ 8 genehmigen"
- Erst nach Genehmigung erscheint der Ort auf der Website

---

## Datenquellen pro Typ

| Typ | Primärquelle | Fotos | Ergänzend |
|-----|-------------|-------|-----------|
| Restaurants & Cafés | Google Places API | Google Places Photos | TripAdvisor, Instagram |
| Kneipen | Google Places API | Google Places Photos | Foursquare |
| Clubs | Google Places API + Resident Advisor | Google Places Photos | RA-Fotos |
| Spielplätze | OpenStreetMap Overpass API | Google Places Photos + Street View | Düsseldorf Open Data |
| Ausflüge | Claude-Recherche + Google Places | Wikimedia Commons + Google Places | Tourismus-Portale NRW |
| Wochenendtipps | Claude-Recherche + Google Places | Wikimedia Commons + Google Places | Tourismus-Portale |

---

## Foto-Strategie

- Google Places Photos API liefert echte Nutzer-/Inhaber-Fotos
- Attributions müssen angezeigt werden (Google-Pflicht) → kleiner Credit unter jedem Bild
- Fotos werden in Supabase Storage gespeichert (nicht hotlinked)
- Fallback: Kein gutes Foto → Ort wird markiert, manuelles Foto hinterlegbar
- Für Ausflüge: Wikimedia Commons (CC-lizenziert) als zusätzliche Quelle

---

## Frontend-Routen

```
/restaurants                    ← Restaurant & Café Guide
/restaurants/[slug]             ← Detail-Seite
/ausfluege                      ← Ausflüge (< 1h)
/ausfluege/[slug]               ← Detail-Seite
/spielplaetze                   ← Spielplatz-Guide (Karte + Liste)
/spielplaetze/[slug]            ← Detail-Seite
/kneipen                        ← Kneipenguide
/kneipen/[slug]                 ← Detail-Seite
/clubs                          ← Clubguide
/clubs/[slug]                   ← Detail-Seite
/wochenendtipps                 ← Wochenendtipps (< 4h)
/wochenendtipps/[slug]          ← Detail-Seite
/chat                           ← AI-Chatbot
```

---

## Projektstruktur (neue Dateien)

```
scraper/
├── orte/
│   ├── google_places.py           ← Discovery + Enrichment
│   ├── overpass_spielplaetze.py   ← Spielplatz-Daten von OSM
│   ├── ausflug_recherche.py       ← Claude-gestützte Recherche
│   └── foto_downloader.py         ← Fotos → Supabase Storage

pipeline/
├── orte_aufbereitung.py           ← Claude-Beschreibungen generieren
├── orte_slug_generator.py         ← Slug-Generierung für Orte
└── orte_importer.py               ← In Supabase importieren

database/
├── schema_orte.sql                ← Tabelle + Indizes

dashboard/
├── pages/
│   └── orte_kuratieren.py         ← Streamlit-Kurationsseite
```

---

## Kosten-Schätzung

| Service | Nutzung | Einmalig | Monatlich |
|---------|---------|----------|-----------|
| Google Places API | ~800 Detail-Requests + Fotos | ~$20 | ~$5 (Updates) |
| Claude API | ~800 Beschreibungen | ~$3 | ~$1 |
| Overpass API (OSM) | Spielplatz-Daten | kostenlos | kostenlos |
| Supabase Storage | Foto-Speicherung | – | im Free Tier |
| **Gesamt** | | **~$25** | **~$6** |

---

## Voraussetzung

Google Places API Key benötigt:
1. Google Cloud Console → Projekt erstellen
2. Places API (New) aktivieren
3. API Key erstellen → in `.env` als `GOOGLE_PLACES_API_KEY`

---

## Zeitplan

| Phase | Was | Dauer |
|-------|-----|-------|
| 1 | DB-Schema + Google Places Discovery-Script | 1 Tag |
| 2 | Enrichment + Foto-Download + Claude-Aufbereitung | 1-2 Tage |
| 3 | Dashboard-Kuration | 1 Tag |
| 4 | Frontend: `/restaurants` + Detail-Seite | 2 Tage |
| 5 | Spielplatz-Pipeline (OSM) + Frontend | 1-2 Tage |
| 6 | Kneipen/Clubs/Ausflüge (gleiche Pipeline, andere Filter) | 1-2 Tage |
| 7 | AI-Chatbot | 3-4 Tage |

---

## AI-Chatbot (Phase 7)

- Route: `/chat`
- Backend: API-Route `/api/chat` mit Claude API (Streaming via SSE)
- Ablauf:
  1. User fragt "Was machen wir heute?"
  2. Bot stellt 2-3 Rückfragen (Wer? Budget? Interessen? Drinnen/draußen?)
  3. Bot durchsucht Events + Orte in Supabase
  4. Gibt 3-5 personalisierte Tipps mit Links zu den Detail-Seiten
- System-Prompt mit DDA-Tonalität und Kontext über Düsseldorf
- Modell: Claude claude-sonnet-4-6 (schnell, günstig, gutes Deutsch)
