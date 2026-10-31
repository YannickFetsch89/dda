# DiesDasDüsseldorf – Design-Prompts für Guide-Seiten

Jeder Prompt ist eigenständig und kann direkt in Claude Design eingegeben werden.
Die Brand Identity wird in jedem Prompt mitgegeben, damit die Ergebnisse konsistent sind.

---

## Brand Identity (Referenz für alle Prompts)

```
Marke: dies.das.düsseldorf (DDA)
Ton: Locker, einladend, urban, jung – nicht werblich, nicht clickbaity
Farben:
  - Navy: #1b2540 (Primär, Header, Buttons)
  - Gold: #c9a84c (Akzent, Highlights, CTAs)
  - Background: #f7f8fa (Light), #0d1117 (Dark)
  - Surface: #ffffff (Light), #161b26 (Dark)
  - Text: #1b2540 (Light), #f7f8fa (Dark)
  - Muted: #718096
Fonts:
  - Headlines: DM Serif Display (Serif)
  - Body: Inter (Sans-serif)
Radien: Cards 20px, Badges 10px, Pills 999px
Schatten: Subtil (0 6px 16px -4px rgba(27,37,64,0.12))
Icons: Google Material Symbols (Outlined)
```

---

## 1. Navigation – Header mit Dropdown-Menüs

```
Erstelle ein Desktop- und Mobil-Design für den Header einer Event- und Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa
Fonts: DM Serif Display (Logo/Headlines), Inter (Body)

Desktop-Header (1344px max-width):
- Links: Wortmarke "dies.das.düsseldorf" (DM Serif Display, die Punkte in Gold)
- Mitte: Suchleiste mit Lupe-Icon und Datums-Dropdown
- Rechts: Zwei Dropdown-Links "Events" und "Guides", danach Theme-Toggle, Merkliste-Icon, Button "Event melden" (Gold)

Dropdown "Events" enthält: Heute, Dieses Wochenende, Alle Events, Kategorien, Stadtteile & Karte
Dropdown "Guides" enthält: Restaurants & Cafés, Kneipen & Bars, Clubs, Spielplätze, Ausflüge, Wochenendtipps

Dropdown-Stil: Weißes Panel mit Schatten, Links untereinander, Hover zeigt Gold-Akzent.

Mobil-Header:
- Wortmarke links, Lupe und Hamburger rechts
- Hamburger öffnet Vollbild-Menü mit beiden Bereichen (Events / Guides) als aufklappbare Gruppen

Zeige beide Zustände (Desktop + Mobil) und den offenen Dropdown-Zustand.
```

---

## 2. Startseiten-Teaser "Düsseldorf entdecken"

```
Erstelle einen Teaser-Bereich für die Startseite einer Event-Website, der auf kuratierte Stadtguides verlinkt.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)
Radien: Cards 20px

Position: Zwischen dem letzten Event-Block und dem Footer.

Aufbau:
- Section-Headline: "Düsseldorf entdecken" (DM Serif Display, 24px)
- Darunter 6 kompakte Kacheln in einem 3x2 Grid (Desktop) / horizontal scrollbar (Mobile)

Jede Kachel enthält:
- Material Symbol Icon (z.B. restaurant, local_cafe, sports_bar, nightlife, toys, hiking)
- Hub-Name (z.B. "Restaurants & Cafés")
- Anzahl Einträge (z.B. "127 Tipps")
- Dezenter Pfeil "→"

Die Kacheln haben weißen Hintergrund, feinen Border, beim Hover leichter Gold-Akzent.
Der gesamte Bereich soll dezent sein – Events sind der Star der Startseite, nicht die Guides.

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 3. `/guides` – Übersichtsseite

```
Erstelle das Layout für eine Übersichtsseite "Düsseldorf entdecken" – die zentrale Einstiegsseite zu allen Stadtguides.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)
Radien: Cards 20px

Aufbau:
- Hero: Keine großes Bild, stattdessen cleaner typografischer Header
  - Headline: "Düsseldorf entdecken" (DM Serif Display, groß)
  - Subline: "Kuratierte Tipps für Restaurants, Cafés, Kneipen, Clubs, Spielplätze und Ausflüge – von uns für euch."

- Darunter: 6 große Kacheln in einem 2x3 Grid (Desktop) / 1-spaltig (Mobile)
  Jede Kachel:
  - Großes Stimmungsbild (16:9 Aspect Ratio, abgerundete Ecken oben)
  - Hub-Name als Overlay unten im Bild (weißer Text auf dunklem Gradient)
  - Darunter: Kurzer Teaser-Text (1 Satz) + Anzahl Einträge
  - Hover: Bild zoomt leicht, Schatten verstärkt sich

Die 6 Kacheln sind:
1. "Restaurants & Cafés" – Food-Foto – "Die besten Adressen zum Essen und Kaffeetrinken" – 127 Tipps
2. "Kneipen & Bars" – Abendstimmung – "Altbier, Cocktails und gemütliche Ecken" – 45 Tipps
3. "Clubs" – Club-Atmosphäre – "Düsseldorfs Nachtleben von Techno bis Hip-Hop" – 18 Tipps
4. "Spielplätze" – Kinder spielen – "Der perfekte Spielplatz für jedes Alter" – 230 Plätze
5. "Ausflüge" – Landschaft – "Raus aus der Stadt – unter einer Stunde erreichbar" – 30 Ziele
6. "Wochenendtipps" – Reise – "Ein Wochenende weg – unter 4 Stunden Anfahrt" – 20 Trips

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 4. `/restaurants` – Übersichtsseite

```
Erstelle das Layout für eine Restaurant- und Café-Übersichtsseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff, Muted #718096
Fonts: DM Serif Display (Headlines), Inter (Body)
Radien: Cards 20px, Chips/Badges 999px
Icons: Google Material Symbols (Outlined)

Aufbau:

1. Hero-Bereich:
   - Headline: "Restaurants & Cafés" (DM Serif Display, weiß)
   - Subline: "127 Empfehlungen – handverlesen für Düsseldorf" (Inter, weiß/muted)
   - Hintergrund: stimmungsvolles Food-Foto mit dunklem Overlay
   - Höhe: ca. 280px Desktop, 200px Mobile

2. Filter-Leiste (wird sticky beim Scrollen):
   - Zeile 1: Typ-Tabs: "Alle" | "Restaurants" (mit Icon restaurant) | "Cafés" (mit Icon local_cafe)
   - Zeile 2: Stadtteil-Chips horizontal scrollbar: Altstadt (18), Flingern (23), Bilk (15), Pempelfort (12), Unterbilk (9), Stadtmitte (14), Friedrichstadt (7), ...
   - Zeile 3: Filter-Chips: Küche (Dropdown), Preis (€/€€/€€€), Tags (Terrasse, Brunch, Vegan...)
   - Zeile 4: Sortierung (Dropdown: Empfohlen, Bewertung, Neu) + Ansicht-Toggle (Grid/Karte)
   - Aktiver Filter: Navy-Hintergrund mit weißem Text
   - Inaktiver Filter: Heller Hintergrund (#e3edf3) mit dunklem Text
   - Filter-Status unter der Leiste: "23 Ergebnisse in Flingern" (klein, muted)

3. Grid-Ansicht (Standard):
   - 3 Spalten Desktop, 2 Tablet, 1 Mobile
   - Jede Card:
     - Bild oben (4:3 Aspect Ratio)
     - Preis-Badge oben rechts im Bild (Navy: "€€")
     - Typ-Label unter dem Bild: Icon + "Restaurant" oder "Café" (Gold, 12px, uppercase)
     - Name (DM Serif Display, 18px, max 2 Zeilen)
     - Untertitel (Inter, 14px, muted: z.B. "Japanisch · Flingern · €€")
     - Zeile: Pin-Icon + Stadtteil | Stern-Icon + Rating (z.B. "4.7 (1931)")
     - Tags: max. 3 kleine Chips (z.B. "Terrasse", "Brunch")
   - Hover: Card hebt sich leicht, Schatten verstärkt sich

4. Kartenansicht (Toggle):
   - Linke Hälfte: scrollbare Kartenliste (kompakt, nur Bild+Name+Rating)
   - Rechte Hälfte: Leaflet-Karte mit Pins
   - Pin-Klick zeigt Mini-Popup: Bild, Name, Rating, "Details →"

Zeige: Desktop Grid-Ansicht (1344px), Desktop Kartenansicht, Mobile Grid (375px), und den Sticky-Filter-Zustand.
```

---

## 5. `/restaurants/[slug]` – Restaurant-Detailseite

```
Erstelle das Layout für eine Restaurant-Detailseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)
Radien: Cards 20px, Panels 24px
Icons: Google Material Symbols (Outlined)

Beispieldaten:
- Name: "Takumi"
- Typ: Restaurant
- Küche: Japanisch (Ramen)
- Preis: €€
- Stadtteil: Stadtmitte
- Rating: 4.5 (8901 Bewertungen)
- Highlight: "Die wohl besten Ramen in NRW – Warteschlange gehört zum Erlebnis"
- Beschreibung: "Authentische japanische Ramen in minimalistischem Ambiente. Das Takumi ist eine Düsseldorfer Institution an der Immermannstraße und zieht Ramen-Fans aus ganz Deutschland an."
- Tags: Ramen, Japanisch, Immermannstraße, Kult
- Adresse: Immermannstraße 28, 40210 Düsseldorf
- Öffnungszeiten: Mo-Sa 12:00-15:00, 17:30-22:00 | So geschlossen
- Telefon: 0211 1234567
- Website: takumi.de
- Instagram: @takumi.dus

Aufbau:

1. Breadcrumb: Start / Restaurants & Cafés / Takumi (13px, muted, Links in Gold beim Hover)

2. Hero-Bild:
   - Volle Breite, 16:9, max-height 480px, abgerundete Ecken (20px)
   - Kleiner Foto-Credit unten rechts: "Foto: Google" (11px, halbtransparent)

3. Zwei-Spalten-Layout (Desktop: 60/40, Mobile: einspaltig)

   Linke Spalte (Hauptinhalt):
   - Typ-Zeile: Restaurant-Icon + "Restaurant · €€ · Stadtmitte" (Gold, 13px, uppercase)
   - Name: "Takumi" (DM Serif Display, 36px)
   - Highlight-Zitat: Goldener Balken links (3px), kursiver Text, Gold-Farbe, 18px
   - Beschreibungstext (Inter, 15px, Zeilenhöhe 1.7)
   - Tags als Chips (klein, heller Hintergrund)
   - Details-Sektion mit Überschrift:
     - Küche: Japanisch (Ramen)
     - Highlight-Gericht: Tantanmen

   Rechte Spalte (Sidebar):
   - Info-Panel (Surface-Farbe, 24px Radius, Schatten):
     - Überschrift "Infos" (16px, fett)
     - Zeilen mit Icons: location_on Adresse, schedule Öffnungszeiten, phone Telefon, star Rating, payments Preis
     - Icons in Gold, Text in Body-Farbe
   - Darunter: Link-Buttons (volle Breite):
     - "Website" (Navy-Button mit language-Icon)
     - "Instagram" (Outline-Button)
     - "Google Maps" (Outline-Button mit map-Icon)

4. Block "Events in der Nähe" (volle Breite):
   - Section-Headline (DM Serif Display)
   - Horizontal scrollbare Event-Cards (gleicher Stil wie auf der Startseite)

5. Block "Das könnte dir auch gefallen" (volle Breite):
   - Section-Headline
   - 4er Grid mit Restaurant-Cards (gleicher Card-Stil wie Übersichtsseite)

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 6. `/kneipen` – Übersichtsseite

```
Erstelle das Layout für eine Kneipen- und Bar-Übersichtsseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c (hier gedämpfter einsetzen), Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)
Icons: Google Material Symbols (Outlined)

Diese Seite soll eine leicht dunklere, abendliche Stimmung haben als die Restaurant-Seite –
aber KEIN Dark-Mode. Subtile Unterschiede: Hero-Bild dunkler, Cards können einen minimal
dunkleren Rand haben.

Aufbau:

1. Hero-Bereich:
   - Headline: "Kneipen & Bars" (DM Serif Display, weiß)
   - Subline: "45 Empfehlungen – von der Altbier-Kneipe bis zur Cocktailbar"
   - Hintergrund: Abendstimmung, Bar-Tresen, warmes Licht, dunkler Overlay
   - Höhe: ca. 280px

2. Filter-Leiste:
   - Stadtteil-Chips
   - Spezialität: Craft Beer, Cocktails, Altbier, Wein, Whisky
   - Vibe: Gemütlich, Gesellig, Draußen sitzen, Sportsbar
   - Toggles: "Happy Hour" (Ja/Nein), "Raucherbereich" (Ja/Nein)

3. Grid (3 Spalten Desktop):
   - Card-Aufbau wie Restaurants, aber:
     - Typ-Label: Icon sports_bar + "Kneipe" oder "Bar"
     - Zusätzlich angezeigt: Spezialität (z.B. "Craft Beer · Altbier")
     - Happy Hour Badge: kleines Tag "Happy Hour 17-19h" in Gold

4. Beispiel-Cards:
   - "Uerige" – Altstadt – Altbier – ★4.3 – Gemütlich
   - "Craft.s" – Flingern – Craft Beer – ★4.6 – Lässig
   - "Bar Olio" – Bilk – Cocktails – ★4.7 – Romantisch

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 7. `/kneipen/[slug]` – Kneipen-Detailseite

```
Erstelle das Layout für eine Kneipen-Detailseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)

Beispieldaten:
- Name: "Uerige"
- Typ: Kneipe
- Spezialität: Altbier
- Stadtteil: Altstadt
- Rating: 4.3 (12782 Bewertungen)
- Highlight: "Das Original – Düsseldorfs berühmteste Brauerei seit 1862"
- Beschreibung: "Im Uerige wird das Altbier noch selbst gebraut und vom Köbes an den Tisch gebracht. Die urige Atmosphäre im Herzen der Altstadt zieht Touristen wie Einheimische gleichermaßen an."
- Tags: Altbier, Brauerei, Tradition, Biergarten
- Happy Hour: Nein
- Raucherbereich: Ja (Außenbereich)

Aufbau: Gleiche Struktur wie Restaurant-Detail, aber:
- Typ-Zeile zeigt: sports_bar Icon + "Kneipe · Altstadt"
- Info-Panel enthält zusätzlich: Spezialität, Happy Hour (wenn vorhanden), Raucherbereich
- "Events in der Nähe" zeigt bevorzugt Nightlife- und Musik-Events
- "Ähnliche Kneipen" statt "Das könnte dir auch gefallen"

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 8. `/clubs` – Übersichtsseite

```
Erstelle das Layout für einen Clubguide einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)
Icons: Google Material Symbols (Outlined)

Diese Seite hat die stärkste visuelle Abgrenzung aller Guides. Der Hero-Bereich ist dunkel
und atmosphärisch. Die Cards zeigen die Musikrichtung prominent.

Aufbau:

1. Hero-Bereich:
   - Headline: "Clubs in Düsseldorf" (DM Serif Display, weiß, groß)
   - Subline: "18 Clubs – von Techno bis Hip-Hop"
   - Hintergrund: Dunkle Club-Atmosphäre, Lichteffekte, starker Overlay
   - Optional: subtiler Gradient von Navy zu Schwarz
   - Höhe: ca. 320px (etwas größer als andere Hubs)

2. Filter-Leiste:
   - Musikrichtung-Chips (prominent, größer als bei anderen Hubs):
     Techno, House, Hip-Hop, R&B, Mixed, Live
   - Dresscode: Casual, Schick, Egal
   - Eintritt: Frei, bis 10€, bis 20€, 20€+
   - Stadtteil

3. Grid (3 Spalten Desktop, 2 Mobile):
   - Card-Design:
     - Bild oben (4:3)
     - Musikrichtung als prominentes Badge oben links IM Bild (z.B. "TECHNO" in Gold auf Navy)
     - Eintritts-Badge oben rechts (z.B. "ab 10€")
     - Name (DM Serif Display, 18px)
     - Stadtteil
     - Zeile: "Nächstes Event: Fr 31.10. – Resident Night" (klein, verlinkt zur Event-Seite)
   - Hover: Deutlicherer Schatten als bei Restaurants

4. Beispiel-Cards:
   - "Salon des Amateurs" – Altstadt – Techno/Experimental – ab 8€
   - "Rudas Studios" – Stadtmitte – House/Techno – ab 15€
   - "Sub" – Friedrichstadt – Techno – ab 10€

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 9. `/clubs/[slug]` – Club-Detailseite

```
Erstelle das Layout für eine Club-Detailseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)

Beispieldaten:
- Name: "Salon des Amateurs"
- Typ: Club
- Musikrichtung: Techno, Experimental, Avant-Garde
- Stadtteil: Altstadt
- Rating: 4.5 (1200 Bewertungen)
- Highlight: "Düsseldorfs Kultclub für elektronische Musik – klein, verschwitzt, legendär"
- Beschreibung: "Der Salon des Amateurs im Kunstpalast ist einer der besten Clubs Europas für experimentelle elektronische Musik. Kleine Tanzfläche, großer Sound, keine VIP-Areas – hier zählt nur die Musik."
- Tags: Techno, Experimental, Kunstpalast, Underground
- Dresscode: Casual
- Eintritt: ab 8€
- Kapazität: ca. 200

Aufbau:
- Hero-Bild (dunkel, Club-Atmosphäre)
- Musikrichtung als großer Badge neben dem Namen (Gold auf Navy, z.B. "TECHNO · EXPERIMENTAL")
- Name (DM Serif Display, 36px)
- Highlight-Zitat
- Beschreibung

Besonderheiten gegenüber Restaurant-Detail:
- Info-Panel enthält: Musikrichtung, Dresscode, Eintritt ab, Kapazität, Adresse
- Block "Nächste Events hier": Events aus der Event-DB gefiltert nach diesem Venue-Namen
  - Mini-Event-Cards mit Datum, Event-Name, DJ/Künstler
  - Maximal 5 Events, Button "Alle Events →"
- Block "Ähnliche Clubs"

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 10. `/spielplaetze` – Übersichtsseite

```
Erstelle das Layout für einen Spielplatz-Guide einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)
Icons: Google Material Symbols (Outlined)

Diese Seite richtet sich an Eltern und Familien. Helle, freundliche Tonalität.
Die Karte ist die Primär-Ansicht (nicht das Grid).

Aufbau:

1. Hero-Bereich:
   - Headline: "Spielplätze in Düsseldorf" (DM Serif Display)
   - Subline: "230 Spielplätze – finde den perfekten für dein Kind"
   - Heller, freundlicher Hintergrund (Illustration oder Foto spielender Kinder, dezent)
   - Höhe: ca. 200px (kompakter als andere Hubs)

2. Filter-Leiste:
   - Altersgruppe-Chips (prominent): 0-3 Jahre, 3-6 Jahre, 6-12 Jahre, Alle Alter
   - Ausstattung (Multi-Select): Sandkasten, Schaukel, Rutsche, Kletterwand, Wasserspiel, Seilbahn
   - Extras (Toggles): Schatten ☀️, WC 🚻, Eingezäunt 🔒, Picknick 🧺
   - Stadtteil
   - Sortierung: In der Nähe (Standort), Beste Ausstattung

3. Karte + Liste Layout:
   - Desktop: Linke Seite (55%) = Leaflet-Karte, Rechte Seite (45%) = scrollbare Liste
   - Mobile: Karte oben (50vh), Liste darunter

   Karte:
   - OpenStreetMap mit Pins
   - Pins farblich nach Altersgruppe: Gelb (0-3), Blau (3-6), Grün (6-12), Grau (Alle)
   - Pin-Klick zeigt Popup: Name, Stadtteil, 3-4 Ausstattungs-Icons, "Details →"

   Liste:
   - Kompakte Cards (horizontal, nicht quadratisch):
     - Kleines Bild links (1:1, 80px)
     - Name, Stadtteil
     - Alters-Badge (farbig, z.B. "3-6 J." in Blau)
     - Ausstattungs-Icons in einer Reihe (schaukel, rutsche, sandkasten als Material Icons)
     - Schatten-Icon (wb_sunny oder cloud), WC-Icon (wc)
   - Hover: Card wird hervorgehoben, Pin auf Karte blinkt

4. Beispiel-Einträge:
   - "Spielplatz Zoopark" – Düsseltal – 3-6 J. – Schaukel, Rutsche, Sandkasten, Schatten ✓, WC ✗
   - "Abenteuerspielplatz Eller" – Eller – 6-12 J. – Kletterwand, Seilbahn, Schatten ✓, WC ✓
   - "Kleinkindspielplatz Hofgarten" – Pempelfort – 0-3 J. – Sandkasten, Schaukel, Eingezäunt ✓

Zeige: Desktop Karte+Liste (1344px), Mobile Karte oben (375px).
```

---

## 11. `/spielplaetze/[slug]` – Spielplatz-Detailseite

```
Erstelle das Layout für eine Spielplatz-Detailseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)

Beispieldaten:
- Name: "Spielplatz Zoopark"
- Stadtteil: Düsseltal
- Adresse: Brehmstraße 30, 40239 Düsseldorf
- Altersgruppe: 3-6 Jahre
- Ausstattung: Sandkasten ✓, Schaukel ✓, Rutsche ✓, Kletterwand ✗, Wasserspiel ✗, Seilbahn ✗
- Schatten: Ja (große Bäume)
- WC: Nein
- Eingezäunt: Teilweise
- Picknick: Ja (Bänke und Wiese)
- Beschreibung: "Beliebter Spielplatz im grünen Zoopark mit viel Platz zum Toben. Durch die großen Bäume gibt es auch im Sommer genug Schatten."

Aufbau:

1. Breadcrumb: Start / Spielplätze / Spielplatz Zoopark

2. Bild (Google Street View oder Places Foto, 16:9)

3. Zwei-Spalten-Layout:

   Links (Hauptinhalt):
   - Name (DM Serif Display, 32px)
   - Stadtteil + Adresse (Inter, muted)
   - Altersgruppen-Badge (farbig, groß: "3-6 Jahre" in Blau, mit Emoji 👶)
   - Beschreibungstext

   - Ausstattungs-Checkliste (visuell prominent):
     Zweispaltige Liste mit Icons:
     ✅ Sandkasten     ✅ Schaukel
     ✅ Rutsche        ❌ Kletterwand
     ❌ Wasserspiel    ❌ Seilbahn
     (Grüner Haken = vorhanden, Roter Kreis = nicht vorhanden)

   - Extras-Info:
     ☀️ Schatten: Ja (große Bäume)
     🚻 WC: Nein
     🔒 Eingezäunt: Teilweise
     🧺 Picknick: Ja

   Rechts (Sidebar):
   - Kleine Karte (Leaflet, 300x200px) mit Pin
   - Button "Route planen" (verlinkt zu Google Maps)
   - Button "In der Nähe" (scrollt zu Block unten)

4. Block "In der Nähe":
   - Andere Spielplätze (max. 3 Cards)
   - Cafés in der Nähe (max. 2 Cards, z.B. "Perfekt für einen Kaffee danach")
   - Familien-Events in der Nähe (max. 3 Event-Cards)

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 12. `/ausfluege` – Übersichtsseite

```
Erstelle das Layout für eine Ausflugstipps-Übersichtsseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)
Icons: Google Material Symbols (Outlined)

Diese Seite hat ein Magazin-Layout mit großen, inspirierenden Bildern.
Kein Grid mit vielen kleinen Cards – stattdessen jeder Ausflug als große,
einladende Karte.

Aufbau:

1. Hero-Bereich:
   - Headline: "Ausflüge ab Düsseldorf" (DM Serif Display, weiß, groß)
   - Subline: "Raus aus der Stadt – 30 Ziele unter einer Stunde erreichbar"
   - Hintergrund: Panorama-Landschaftsbild (z.B. Siebengebirge, Drachenfels, Neandertal)
   - Höhe: ca. 360px (größer als andere Hubs – inspirierend)

2. Filter-Leiste (dezenter als bei Restaurants):
   - Anreise: Alle, Auto, Bahn, Fahrrad
   - Entfernung: bis 30 Min, bis 45 Min, bis 60 Min
   - Art: Natur, Stadt, See/Wasser, Burg/Schloss, Wandern, Radtour
   - Saison: Ganzjährig, Aktuell passend

3. Magazin-Cards (1 pro Reihe auf Desktop):
   - Jede Card ist horizontal: Bild links (40%), Text rechts (60%)
   - Card-Höhe: ca. 240px
   - Bild: Landscape-Foto, 16:9 innerhalb der Card, abgerundete Ecken links
   - Text-Bereich:
     - Badges oben: "45 Min · Auto + Bahn" (kleine Chips mit Icons directions_car, train)
     - Saison-Badge: "Ganzjährig" oder "April – Oktober" (dezent, muted)
     - Name (DM Serif Display, 22px)
     - Kurze Beschreibung (Inter, 15px, 2-3 Zeilen, muted)
     - Art-Chips: "Natur", "Wandern" (klein)
     - "Mehr erfahren →" Link in Gold

   - Mobile: Cards werden vertikal (Bild oben, Text unten)

4. Beispiel-Cards:
   - "Drachenfels & Königswinter" – 45 Min · Bahn · Natur/Burg – "Rheinblick, Burgruine und die älteste Zahnradbahn Deutschlands"
   - "Neandertal" – 20 Min · Auto · Natur/Museum – "Auf den Spuren der Neandertaler – Museum und Wanderwege im Tal"
   - "Schloss Benrath" – 15 Min · Bahn · Schloss/Park – "Barockes Lustschloss mit weitläufigem Park direkt in Düsseldorf"
   - "Baldeneysee (Essen)" – 35 Min · Bahn · See/Wandern – "Baden, Segeln, Wandern – das Naherholungsgebiet im Ruhrgebiet"

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 13. `/ausfluege/[slug]` – Ausflug-Detailseite

```
Erstelle das Layout für eine Ausflug-Detailseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)

Beispieldaten:
- Name: "Drachenfels & Königswinter"
- Entfernung: 45 Minuten
- Anreise: Bahn (RE/RB ab Düsseldorf Hbf nach Königswinter, dann Fußweg)
- Dauer vor Ort: 3-5 Stunden
- Saison: Ganzjährig (Zahnradbahn April-Oktober)
- Art: Natur, Burg/Schloss
- Kosten: Zahnradbahn 10€ Erwachsene, Eintritt Schloss Drachenburg 8€
- Beschreibung: "Der Drachenfels am Rhein gehört zu den meistbesuchten Ausflugszielen in NRW – und das zu Recht. Die Wanderung vom Rheinufer zur Burgruine dauert etwa 30 Minuten und belohnt mit einem atemberaubenden Panoramablick über das Rheintal. Wer es bequemer mag, nimmt die historische Zahnradbahn. Auf halbem Weg liegt das neugotische Schloss Drachenburg, das allein schon den Ausflug wert ist."

Aufbau:

1. Hero-Bild (volle Breite, max-height 500px – größer als bei Restaurants!)
   Panorama-Landschaft, Foto-Credit unten rechts

2. Hauptbereich (einspaltig auf Desktop, max-width 800px, zentriert):
   - Badges-Zeile: "45 Min" (mit Icon train) · "Ganzjährig" (mit Icon calendar_today) · "Natur" · "Burg"
   - Name (DM Serif Display, 40px – größer als bei Restaurants)
   - Ausführlicher Text (Inter, 16px, Zeilenhöhe 1.8 – mehr Luft als bei Restaurants)
     Storytelling-Stil, nicht nur Fakten

3. Info-Box (volle Breite, Surface-Hintergrund, abgerundete Ecken):
   Zwei-Spalten-Grid innerhalb der Box:
   - Entfernung: 45 Minuten ab Düsseldorf
   - Anreise: Bahn (RE/RB ab Hbf)
   - Dauer vor Ort: 3-5 Stunden
   - Beste Saison: Ganzjährig
   - Kosten: Zahnradbahn 10€, Schloss 8€
   - Geeignet für: Paare, Familien, Solo

4. Karte (Leaflet, volle Breite, 300px Höhe):
   - Zeigt Zielort mit Pin
   - Optional: Route von Düsseldorf Hbf andeuten

5. Block "Unterwegs einkehren":
   - 2-3 Restaurant/Café-Cards am Zielort (wenn in der DB vorhanden)
   - Ansonsten: "Tipp: In Königswinter gibt es zahlreiche Cafés am Rheinufer"

6. Block "Ähnliche Ausflüge":
   - 3 horizontale Magazin-Cards (gleicher Stil wie Übersichtsseite)

Zeige Desktop (1344px, zentrierter Content) und Mobile (375px).
```

---

## 14. `/wochenendtipps` – Übersichtsseite

```
Erstelle das Layout für eine Wochenendtipp-Übersichtsseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)
Icons: Google Material Symbols (Outlined)

Diese Seite hat ein Reise-Magazin-Feeling mit einem Feature-Artikel oben
und einem Editorial-Grid darunter.

Aufbau:

1. Hero-Bereich:
   - Headline: "Wochenendtrips ab Düsseldorf" (DM Serif Display, weiß, groß)
   - Subline: "Ein Wochenende raus – 20 Ziele unter 4 Stunden Anfahrt"
   - Hintergrund: Stimmungsvolles Reisebild (z.B. Brügge, Amsterdam, Moseltal)
   - Höhe: ca. 400px (der größte Hero aller Hubs – Reise-Magazin-Feeling)

2. Feature-Story (direkt unter Hero):
   - Volle Breite, großes Bild links (50%), Text rechts (50%)
   - Badge: "EMPFEHLUNG" in Gold
   - Name: z.B. "Amsterdam" (DM Serif Display, 28px)
   - Kurzer Teaser (3-4 Zeilen)
   - "2 Nächte · Bahn · ab 89€/Nacht"
   - Button "Mehr erfahren →"
   - Wechselt saisonal (z.B. Weihnachtsmärkte im Dezember)

3. Filter-Leiste (minimal):
   - Dauer: 1 Nacht, 2 Nächte, Tagestrip möglich
   - Art: Städtetrip, Natur, Wellness, Kultur, Aktiv
   - Anreise: Auto, Bahn
   - Budget: Günstig, Mittel, Gehoben

4. Editorial-Grid (2 Spalten Desktop, 1 Mobile):
   - Größere Cards als bei Restaurants (mehr Bild, mehr Luft):
     - Bild oben (16:9, volle Card-Breite)
     - Name (DM Serif Display, 20px)
     - Badges: "3h · Bahn · 1-2 Nächte"
     - Teaser-Text (2 Zeilen)
     - Art-Chips: "Städtetrip", "Kultur"

5. Beispiel-Cards:
   - "Brügge" – 3h · Bahn · Städtetrip – "Mittelalterliche Gassen, Schokolade und Kanäle"
   - "Moseltal" – 2h · Auto · Natur/Wein – "Weinberge, Burgen und die schönsten Dörfer"
   - "Köln" – 30 Min · Bahn · Städtetrip – "Mehr als nur der Dom – Belgisches Viertel, Ehrenfeld, Street Art"
   - "Eifel" – 1.5h · Auto · Natur/Wandern – "Vulkanseen, Wildnis und die Milchstraße bei Nacht"

Zeige Desktop (1344px) und Mobile (375px).
```

---

## 15. `/wochenendtipps/[slug]` – Wochenendtipp-Detailseite

```
Erstelle das Layout für eine Wochenendtipp-Detailseite einer Stadtguide-Website.

Marke: dies.das.düsseldorf
Farben: Navy #1b2540, Gold #c9a84c, Hintergrund #f7f8fa, Surface #ffffff
Fonts: DM Serif Display (Headlines), Inter (Body)

Beispieldaten:
- Name: "Brügge"
- Entfernung: 3 Stunden
- Anreise: Bahn (ICE nach Brüssel, dann IC nach Brügge) oder Auto (A44/E40)
- Dauer: 1-2 Nächte
- Übernachtung: ab 89€/Nacht (Boutique-Hotels im Zentrum)
- Beste Saison: Ganzjährig (besonders schön: Frühling + Weihnachtszeit)
- Art: Städtetrip, Kultur
- Beschreibung (lang, Reisebericht-Stil): "Brügge ist wie eine Zeitreise ins Mittelalter – nur mit besserer Schokolade. Die gesamte Altstadt gehört zum UNESCO-Weltkulturerbe, und es fühlt sich an, als wäre man in ein Gemälde von Jan van Eyck spaziert. Nehmt euch Zeit für eine Bootsfahrt auf den Kanälen, steigt auf den Belfried für den Panoramablick, und probiert unbedingt die Fritten bei Chez Albert am Marktplatz. Abends wird es ruhig in den Gassen – dann gehört die Stadt euch."

Aufbau:

1. Hero-Bild (volle Breite, max-height 500px, Panorama)

2. Hauptbereich (einspaltig, max-width 800px, zentriert – Reise-Magazin-Stil):
   - Badges: "3h Bahn" · "1-2 Nächte" · "Städtetrip" · "Ganzjährig"
   - Name (DM Serif Display, 40px)
   - Langer Beschreibungstext (Inter, 16px, Zeilenhöhe 1.8)
     Persönlicher, erzählender Stil – wie ein Reiseblog

3. Info-Box:
   - Entfernung: 3 Stunden
   - Anreise: Bahn oder Auto
   - Dauer: 1-2 Nächte empfohlen
   - Übernachtung: ab 89€/Nacht
   - Beste Saison: Ganzjährig
   - Budget-Einschätzung: Mittel

4. Optional: "3 Highlights vor Ort" (3 Mini-Cards nebeneinander):
   - "Bootsfahrt auf den Kanälen" – Icon: rowing – 12€
   - "Belfried besteigen" – Icon: castle – 14€
   - "Schokoladen-Museum" – Icon: cake – 8€

5. Karte (Leaflet, Zielort markiert)

6. Block "Ähnliche Trips":
   - 2-3 Cards im Editorial-Stil

Zeige Desktop (1344px) und Mobile (375px).
```
