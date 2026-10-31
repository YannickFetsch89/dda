# DiesDasDüsseldorf – Konzept: Guide-Hubs

## Übersicht

Erweiterung der Website um permanente, kuratierte Stadtguides als eigenständige Hub-Seiten. Jeder Guide bekommt ein auf seinen Content-Typ optimiertes Layout. Die Startseite bleibt Event-fokussiert mit einem kompakten Teaser-Bereich zu den Guides.

### Integrationsansatz: Hub-Seiten (Konzept C)

- Startseite = täglicher Wiederkehrwert (Events)
- Guides = zeitlose Empfehlungen mit eigenen Hub-Seiten
- Verbindung: Querverweise zwischen Events und Orten (Events in der Nähe, Restaurants vor/nach dem Event)
- Navigation: Header bekommt zwei Dropdown-Bereiche (Events | Guides)

### Design-Prinzipien

- **Gleiche Brand Identity**: Navy/Gold, DM Serif Display, Inter – über alle Hubs einheitlich
- **Typ-gerechtes Layout**: Jeder Hub bekommt das Layout das sein Content braucht
- **Subtile Differenzierung**: Clubs/Kneipen etwas dunkler, Spielplätze heller, Ausflüge großzügiger
- **Mobile First**: Alle Hubs funktionieren auf dem Smartphone genauso gut wie am Desktop

---

## Navigation

```
Header:
  dies.das.düsseldorf    [Suche]    Events ▾    Guides ▾    Event melden

  Events ▾                          Guides ▾
  ├── Heute                         ├── Restaurants & Cafés
  ├── Dieses Wochenende             ├── Kneipen & Bars
  ├── Alle Events                   ├── Clubs
  ├── Kategorien                    ├── Spielplätze
  └── Stadtteile & Karte            ├── Ausflüge (< 1h)
                                    └── Wochenendtipps
```

---

## Hub 1: `/restaurants` – Restaurants & Cafés

### Übersichtsseite

**Hero-Bereich**
- Headline: "Restaurants & Cafés in Düsseldorf"
- Subline: Anzahl kuratierter Orte, z.B. "127 Empfehlungen – handverlesen für dich"
- Hintergrundbild: stimmungsvolles Food-Foto (rotierend oder saisonal)

**Filter-Leiste (sticky beim Scrollen)**
- Typ: Alle | Restaurants | Cafés
- Stadtteil: Dropdown oder Chips (Altstadt, Flingern, Bilk, Pempelfort …)
- Küche: Japanisch, Italienisch, Deutsch, Asiatisch, Brunch …
- Preisniveau: € | €€ | €€€
- Tags: Terrasse, Romantisch, Brunch, Vegan, Familienfreundlich
- Sortierung: Empfohlen | Bewertung | Neu hinzugefügt

**Ansichten (Toggle)**
- Grid-Ansicht (Standard): Karten mit Foto, Name, Typ-Icon, Stadtteil, Rating, 1-2 Tags
- Kartenansicht: Leaflet/OSM mit Pins, beim Klick Mini-Card mit Bild + Name

**Stadtteil-Quicklinks**
- Horizontale Leiste: "Flingern (23) · Altstadt (18) · Bilk (15) · Pempelfort (12) …"
- Klick scrollt/filtert

### Detailseite `/restaurants/[slug]`

- Hero-Bild (16:9, volle Breite)
- Name, Typ-Badge, Preisniveau, Stadtteil
- Highlight-Zitat (goldener Balken, kursiv – der eine Satz warum dieser Ort besonders ist)
- Beschreibungstext (150-300 Zeichen, DDA-Ton)
- Tags als Chips
- Sidebar: Adresse, Öffnungszeiten, Telefon, Website-Link, Instagram, Google Maps Link, Rating
- Foto-Attribution (Google-Pflicht)
- Block: "Events in der Nähe" (Radius-Query aus Event-DB)
- Block: "Das könnte dir auch gefallen" (gleicher Stadtteil oder gleiche Küche)

---

## Hub 2: `/kneipen` – Kneipen & Bars

### Übersichtsseite

**Hero-Bereich**
- Headline: "Kneipen & Bars in Düsseldorf"
- Dunklere Farbgebung als Restaurants (Navy-Töne, gedämpftes Gold)
- Optional: abendliche Stimmung im Hintergrundbild

**Filter-Leiste**
- Stadtteil
- Spezialität: Craft Beer, Cocktails, Altbier, Wein, Whisky
- Vibe: Gemütlich, Laut & Gesellig, Draußen sitzen, Sportsbar, Studikneipe
- Happy Hour: Ja/Nein
- Raucherbereich: Ja/Nein

**Karten-Grid**
- Wie Restaurants, aber visuell etwas dunkler gehalten
- Karte zeigt zusätzlich: Spezialität, Happy Hour Zeiten wenn vorhanden

### Detailseite `/kneipen/[slug]`

- Gleicher Aufbau wie Restaurant-Detail
- Extras: Spezialität, Happy Hour Zeiten, Raucherbereich Ja/Nein
- "Events in der Nähe" (besonders Nightlife + Musik)

---

## Hub 3: `/clubs` – Clubguide

### Übersichtsseite

**Hero-Bereich**
- Headline: "Clubs in Düsseldorf"
- Dunkles Design, ggf. subtile Gradient-Animation oder Lichteffekt
- Stärkste visuelle Abgrenzung von allen Hubs

**Filter-Leiste**
- Musikrichtung: Techno, House, Hip-Hop, R&B, Mixed, Live
- Dresscode: Casual, Schick, Egal
- Eintritt: Frei, bis 10€, bis 20€, 20€+
- Stadtteil

**Karten-Grid**
- Dunkleres Card-Design
- Karte zeigt: Musikrichtung prominent, Eintritt, nächste Events

### Detailseite `/clubs/[slug]`

- Hero-Bild
- Musikrichtung als großer Badge
- Beschreibung (Atmosphäre, Publikum, Sound)
- Extras: Dresscode, Eintritt ab, Kapazität
- Block: "Nächste Events hier" (Events aus der Event-DB gefiltert nach diesem Venue)
- Block: "Ähnliche Clubs"

---

## Hub 4: `/spielplaetze` – Spielplatz-Guide

### Übersichtsseite

**Hero-Bereich**
- Headline: "Spielplätze in Düsseldorf"
- Freundlich, hell, Familien-Tonalität
- Subline: "Finde den perfekten Spielplatz für dein Kind"

**Karte als Primär-Ansicht (nicht Grid)**
- Große Leaflet-Karte, nimmt 60% der Seite ein
- Farbige Pins nach Altersgruppe (Kleinkind = Gelb, Schulkind = Blau, Alle = Grün)
- Klick auf Pin: Mini-Popup mit Bild, Name, Ausstattungs-Icons
- Daneben oder darunter: scrollbare Liste

**Filter-Leiste**
- Altersgruppe: 0-3, 3-6, 6-12, Alle
- Ausstattung: Sandkasten, Schaukel, Rutsche, Kletterwand, Wasserspiel, Seilbahn
- Extras: Schatten vorhanden, WC vorhanden, Eingezäunt, Picknick möglich
- Stadtteil
- Sortierung: Nähe (Standort-Abfrage) | Bewertung | Ausstattung

**Listen-Ansicht (Toggle)**
- Kompakte Karten: Bild, Name, Stadtteil, Alters-Badge, Ausstattungs-Icons in einer Reihe

### Detailseite `/spielplaetze/[slug]`

- Bild (Street View oder Google Places Foto)
- Name, Stadtteil, Adresse
- Altersgruppen-Badge
- Ausstattungs-Liste mit Icons (Sandkasten ✓, Schaukel ✓, Rutsche ✓, WC ✗ …)
- Schatten: Ja/Nein/Teilweise
- Karte mit Pin (kleines Leaflet-Widget)
- "In der Nähe": andere Spielplätze + Cafés + Familienevents

---

## Hub 5: `/ausfluege` – Ausflugstipps (< 1 Stunde)

### Übersichtsseite

**Hero-Bereich**
- Headline: "Ausflüge ab Düsseldorf"
- Subline: "Raus aus der Stadt – alles unter einer Stunde erreichbar"
- Großes, inspirierendes Landschaftsbild

**Magazin-Layout (kein Grid)**
- Große Karten (1 pro Reihe auf Desktop, volle Breite)
- Jede Karte: großes Foto links (40%), Text rechts (60%)
- Text: Name, Entfernung, Anreise-Art (Auto/Zug/Rad), kurze Beschreibung
- Badge: Saison (Ganzjährig, Frühling-Herbst, Nur Sommer …)

**Filter-Leiste**
- Anreise: Auto, Bahn, Fahrrad, Alles
- Dauer: bis 30 Min, bis 45 Min, bis 60 Min
- Art: Natur, Stadt, See/Wasser, Burg/Schloss, Wandern, Radtour
- Saison: Ganzjährig, Aktuell passend (automatisch nach Monat)

### Detailseite `/ausfluege/[slug]`

- Großes Hero-Bild (Landschaft, volle Breite)
- Name, Entfernungs-Badge, Anreise-Badge
- Ausführlicher Text (500-800 Zeichen, Storytelling-Stil – "Warum sich die Fahrt lohnt")
- Info-Box: Entfernung, Anreise, Dauer vor Ort, beste Saison, Kosten
- Karte mit Route ab Düsseldorf HBF
- "Unterwegs einkehren": Restaurant/Café-Empfehlung am Zielort (wenn vorhanden)
- "Ähnliche Ausflüge"

---

## Hub 6: `/wochenendtipps` – Wochenendtrips (< 4 Stunden)

### Übersichtsseite

**Hero-Bereich**
- Headline: "Wochenendtrips ab Düsseldorf"
- Subline: "Ein Wochenende raus – unter 4 Stunden Anfahrt"
- Reise-Magazin-Feeling, großes Bild

**Editorial-Layout (wie ein Reisemagazin)**
- Feature-Story oben: Ein Trip groß hervorgehoben (saisonal rotierend)
- Darunter: 2er-Grid mit großen Karten
- Jede Karte: Foto, Name, Entfernung, Dauer in Tagen, kurzer Teaser

**Filter-Leiste**
- Dauer: 1 Nacht, 2 Nächte, Tagestrip möglich
- Art: Städtetrip, Natur, Wellness, Kultur, Aktiv
- Anreise: Auto, Bahn
- Budget: Günstig, Mittel, Gehoben

### Detailseite `/wochenendtipps/[slug]`

- Großes Hero-Bild
- Name, Entfernung, Anreise, Dauer
- Langer Text (800-1200 Zeichen, Reisebericht-Stil)
- Info-Box: Entfernung, Anreise, Übernachtung (Preisrahmen), beste Saison
- Optional: 2-3 "Highlights vor Ort" als Mini-Karten
- Optional: Karte mit Route
- "Ähnliche Trips"

---

## Querschnitts-Elemente

### `/guides` – Übersichtsseite

- Headline: "Düsseldorf entdecken"
- 6 große Kacheln (2x3 Grid), je eine pro Hub
- Jede Kachel: Stimmungsbild, Hub-Name, Anzahl Einträge, kurzer Teaser
- Dient als Einstiegspunkt für alle die "stöbern" wollen

### Startseiten-Teaser

**Position**: nach dem "Highlights der Woche" Block, vor dem Footer
- Headline: "Düsseldorf entdecken"
- 3-6 kompakte Kacheln nebeneinander (horizontal scrollbar auf Mobile)
- Jede Kachel: Icon + Name + Anzahl + "Entdecken →"
- Dezent, nicht zu groß – Events bleiben der Star der Startseite

### Querverweise

- Restaurant-Detail → "Events in der Nähe"
- Event-Detail → "Restaurants in der Nähe"
- Stadtteil-Seite → Events + Orte gemischt
- Club-Detail → "Nächste Events hier" (Venue-Match)

---

## Technische Basis

- **Datenbank**: Supabase `orte`-Tabelle (bereits angelegt)
- **Datenzugriff**: `web/lib/orte.ts` (bereits implementiert)
- **Bildquelle**: Google Places Photos API (Attribution-Pflicht)
- **Karten**: Leaflet + OpenStreetMap (kostenlos, kein API Key nötig)
- **Geo-Queries**: PostGIS-Extension in Supabase für "in der Nähe"-Abfragen
