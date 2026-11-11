# Plan: Guide-Hub „Clubs“ (`/guides/clubs`)

Stand 11.11.2026. Design-Vorlage: `design_v2/ddd_handoff_v2/13_clubs` (Ansichten 22 und 24).
Muster: Hub „Kneipen & Bars“ (`docs/plan-kneipen-bars-2026-11-07.md`).

## 1. Entscheidungen (Auftraggeber, 11.11.2026)

| Nr. | Frage | Entscheidung |
|---|---|---|
| C1 | Umfang | Drei Unterarten mit eigenem Label und Filter: **Club**, **Kulturhaus** (Konzert-/Kulturhäuser mit regelmäßigen Partys, z. B. zakk, Stahlwerk, R25), **Partylocation** (z. B. Oberbayern, Kuhstall, Schlager Cafe). Immer ausgeschlossen: Erotik-, Swinger- und Saunaclubs, Bordelle, Shisha-Lounges, reine Karaoke-Bars, DJ-Dienstleister. |
| C2 | Bewertung | Eigener **Club-Score 1–10 aus Daten** (Teilwerte sichtbar); Website zeigt Score ≥ 7. Google-Sterne nur schwach gewichtet (Türsteher-Beschwerden verzerren). |
| C3 | Gebiet | Düsseldorf + Neuss + Ratingen (wie Restaurants und Bars). |
| C4 | Rausgegangen | robots.txt sperrt seit Kurzem alle unbekannten Crawler. Der tägliche Scraper läuft vorerst weiter; der Club-Guide nutzt nur Daten, die schon in unserer DB stehen. Rausgegangen-Location-Seiten werden **nicht** abgerufen. Dauerhafte Lösung später. |

## 2. Datengrundlage

### 2.1 Kandidaten (`scraper/orte/clubs.py`)
1. **Zwischenspeicher** `data/orte/flaechensuche_clubs.json` (171 Treffer der Flächensuche `night_club`) – gefiltert nach C1/C3.
2. **Startliste** bekannter Clubs, Kulturhäuser und Partylocations (Namen aus Recherche und unserem Eventkalender), per Google **Text Search** aufgelöst.
3. **Eigene Events:** Orte mit mehreren Nightlife-Events im Kalender als Hinweis auf fehlende Kandidaten.

Ausschluss per Regeln (Name/Typ: Erotik, Sauna, Swinger, Bordell, Massage, Shisha, Karaoke …) und `businessStatus`.
Schon vorhandene Orte (Pitcher, Konvex, zakk, Schlager Cafe …) werden **nicht umgetypt**, sondern bekommen `extras.auch_club = true` (wie E1 bei Bars).

### 2.2 Import
Place Details wie bei Bars (inkl. `liveMusic`, `servesCocktails`, `goodForGroups`), `typ = 'club'`, `aktiv = false`,
`extras.hub = 'clubs'`, `extras.unterart` (club | kulturhaus | partylocation, Regel + KI).

### 2.3 Club-Profil (`scraper/orte/clubs_profil.py`) – Kern des Hubs
Quellen, nur mit robots.txt-Prüfung und ≥ 2 s Abstand:
- Website des Clubs (Start-, Über-uns-, Programmseiten),
- Resident-Advisor-Club-Seite (falls vorhanden, `ra.co/clubs/…` erlaubt),
- weitere Seiten aus einer Claude-Websuche (Presse, Stadtmagazine; gesperrt: Rausgegangen, Social Media),
- **unsere Events** an diesem Ort (Titel, Beschreibungen, Kategorien, letzte 6 Monate + kommende),
- Google-Kurzbeschreibung und Bewertungstexte.

Claude ordnet ein (festes JSON-Schema), **jede Angabe mit wörtlichem Zitat**, der Code prüft das Zitat gegen die
geladenen Texte (`belegt()` aus `bars_einordnen.py`). Ohne Beleg wird die Angabe verworfen.
Gespeichert in `extras.club`:
- `genres` (Haupt, feste Liste: Techno, House, Hip-Hop, R&B, Reggaeton/Latin, Pop/Charts, Schlager, 80er/90er/2000er,
  Rock/Indie, Metal/Punk, Elektro/Experimental, Drum & Bass, Afrobeats, Jazz/Soul/Funk, Mixed),
  `genres_neben` (gelegentlich), mit Beleg,
- `formate`: wiederkehrende Partyreihen (Name, Rhythmus, Musik),
- `zusatz_events`: was sonst passiert (Konzerte, Comedy, Lesungen, Flohmarkt, Public Viewing, Workshops …) mit Beispielen,
- `oeffnungstage`, `eintritt` (typische Spanne), `dresscode` (Casual | Schick | Egal) + Türpolitik,
  `alter` (z. B. ab 18, Ü30), `kapazitaet`, `floors`, `publikum` (feste Werte), `ausstattung`
  (Außenbereich, Raucherbereich, barrierefrei …), Links (Website, Instagram, Resident Advisor),
- `event_orte`: Schreibweisen des Orts in unserem Eventkalender (für „Nächste Events“),
- `belege`, `quellen`, `profil_datum`.
Dazu `beschreibung` (gegliedert wie bei den Event-Texten) und `highlight`.

### 2.4 Club-Score (C2)
Teilwerte 0–10, gewichtet, gerundet auf 1–10, gespeichert in `extras.club_score`:
- **Programm 35 %** – Events in unserem Kalender (letzte 90 + nächste 60 Tage), Regelmäßigkeit,
- **Szene 25 %** – Resident Advisor, kuratierte Reihen/Line-ups, Kulturhaus-Programm,
- **Profil 20 %** – belegte Musikrichtungen und Formate,
- **Beliebtheit 20 %** – Google (Bayes-Mittel, Anzahl Bewertungen).
Kalibrierung nach dem ersten Lauf; Zielbild: alle bekannten Szene-Clubs ≥ 7.

## 3. Website
- `/guides/clubs`: dunkler Hero mit Lichtflecken, Genre-Chips (Mehrfachauswahl, ODER), Unterart, Stadtteil, Eintritt;
  Karten mit Genre-Badge, Eintritts-Badge, „Nächstes Event“ aus dem Kalender.
- `/guides/clubs/[slug]`: Name + Genre-Pill, Highlight, Beschreibung, Info-Panel (Musik, Öffnung, Eintritt, Dresscode,
  Alter, Kapazität, Adresse), **Partyreihen**, **Was sonst passiert**, **Nächste Events hier**, Club-Score mit Teilwerten,
  ähnliche Clubs.
- SEO wie Kneipen (Canonical, `noindex` bei Filtern, JSON-LD `NightClub`, Sitemap, `/guides`-Kachel).

## 4. Ablauf
1. Kandidaten + Import (Kosten: Text Search ≈ 0,032 $/Anfrage, Details ≈ 0,025 $ – zusammen ca. 3–5 $, Nov.-Freikontingent ist verbraucht).
2. Profile (Claude + Websuche ≈ 0,05–0,10 $/Club → ca. 5–10 $).
3. Score, Sichtprüfung (CSV), Freischaltung.
4. Website, Tests, Browser-Prüfung → Deploy nur mit OK.
5. Später: Profil-Aktualisierung (Events/Genres) im täglichen Lauf.
