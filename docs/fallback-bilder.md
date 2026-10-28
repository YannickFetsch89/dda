# Fallback-Bilder für Events ohne Foto

Stand: 28.10.2026 · Grundlage: alle 912 kommenden Events in Supabase, davon **341 ohne Bild** (37 %).

Die Bilder werden **nur** genutzt, wenn ein Event kein eigenes Bild hat. Pro Motiv gibt es mehrere Varianten;
welche ein Event bekommt, wird aus seiner ID abgeleitet (zufällig verteilt, aber stabil – dasselbe Event zeigt
immer dasselbe Bild, auch nach einem Reload).

Woher die Lücken kommen: Meetup.com (107), Stadtbüchereien (89), Schauspielhaus (41), Kunstpalast (29),
AllEvents (25), Filmmuseum (15), Oper am Rhein (12), Tanzhaus NRW (10).

---

## Technische Vorgaben für alle Bilder

| | |
|---|---|
| **Format** | 3:2 quer, mind. 1536 × 1024 px. Die Website schneidet je nach Ansicht auf 1:1, 4:3, 16:10 oder 16:7 zu → Hauptmotiv **mittig**, nichts Wichtiges an den Rändern |
| **Kein Text** | keine Schrift, Plakate, Schilder, Logos, Markennamen – die Website legt eigene Texte darüber |
| **Menschen** | erlaubt, aber nicht porträtartig: von hinten, angeschnitten, Hände, Unschärfe. Keine erkennbaren Gesichter (wirkt sonst wie ein echtes Foto *dieses* Events) |
| **Stil** | dokumentarische Fotografie, natürliches Licht, warm, leicht entsättigt; nicht „Stockfoto-glatt“, keine Illustration |
| **Ablage** | `web/public/fallback/<motiv>-<nr>.webp`, z.B. `laufen-1.webp`, `laufen-2.webp` |

**Stil-Prompt** – jedem Motiv-Prompt voranstellen, damit die Serie einheitlich wirkt:

> Documentary-style photograph, natural light, warm and slightly desaturated colors, shallow depth of field,
> 3:2 landscape, main subject centered. No text, no signs, no logos, no brand names. People only from behind,
> cropped or out of focus, no recognizable faces. Urban German city atmosphere (Düsseldorf).

---

## Prio A – deckt rund drei Viertel der Lücken ab

| Motiv (`slug`) | Wofür, Beispiele aus den Daten | Events | Varianten |
|---|---|---|---|
| `theater` | Schauspielhaus: „Die Möwe“, „Tyll“, „1984“, Theaterbar, Improv | 39 | 6 |
| `sprachcafe` | English Meeting, German Practice, Sprachcafé, Stammtische (NL, JP, FR, IT) | 36 | 6 |
| `spieleabend` | Board Game Night, Pen & Paper, Werwölfe, Escape Room, Quiz, Billard | 25 | 6 |
| `fuehrung-ausstellung` | Öffentliche Führung, Taschenlampenführung, Vernissage, Atelier, Kunsthalle | 24 | 6 |
| `lesung-vortrag` | Lesungen, Vorträge der Büchereien, Book Club, Creative Writing, Dante-Lesung | 22 | 6 |
| `film` | Filmmuseum (Black Box), Stummfilm mit Orgel, Trickfilm, Film Screening | 18 | 5 |
| `kinder-geschichten` | Geschichtenzeit, Kamishibai, Vorlesen, Kuscheltierübernachtung, LEGO, Familienführung | 18 | 5 |
| `maker-workshop` | 3D-Druck, Basteln, FabLab, Repair Café, Handarbeit, Musikstudio | 15 | 5 |
| `tech-meetup` | Azure, C++, Power BI, KI/ML, Data, UX, WordPress | 15 | 5 |
| `halloween` | Halloween-Partys, Grusel-Basteln, Samhain *(saisonal, Oktober)* | 15 | 5 |
| `candlelight-klassik` | Candlelight-Konzerte, Trio, Big Band, Einaudi-Hommage, Rezitation | 11 | 5 |
| `bibliothek-beratung` | Onleihe & Co., Digitalsprechstunde, Bücherflohmarkt, Verbraucherzentrale | 11 | 5 |

## Prio B

| Motiv (`slug`) | Wofür, Beispiele aus den Daten | Events | Varianten |
|---|---|---|---|
| `business-networking` | Gründerstammtisch, Founders Meetup, Business-Frühstück, Toastmasters, Konferenzen | 10 | 5 |
| `ballsport` | 5vs5 Football, Cageball, Badminton, Padel, Cricket | 8 | 4 |
| `tanz-performance` | Tanzhaus NRW: zeitgenössischer Tanz, Performance | 7 | 4 |
| `fitness-yoga` | Yoga, Pilates, Barre, HIIT, Workout, Meditation | 7 | 4 |
| `clubnacht` | Party, Rave, Clubabend, Single-Party | 6 | 4 |
| `wandern` | Moonlight Hike, Wanderung Dickelsbach, Tagesausflüge | 6 | 4 |
| `oper-musiktheater` | Zauberflöte, My Fair Lady, Comedian Harmonists, Musical | 6 | 4 |
| `laufen` | Lauftreff, 5 km Run, Running Club, Parkrun | 2 (wöchentlich) | 4 |
| `live-konzert` | Rock/Pop/Indie-Konzerte, Bands, Singer-Songwriter | 4 | 4 |
| `karneval` | Sessionseröffnung 11.11., Sitzungen *(saisonal, ab November stark)* | 2 | 4 |
| `weihnachtsmarkt` | Advent, Weihnachtsmärkte, Weihnachtskonzerte *(saisonal, ab Mitte November)* | – | 4 |

## Prio C – selten, aber eindeutig

| Motiv (`slug`) | Wofür | Events | Varianten |
|---|---|---|---|
| `gaming` | Switch-Nachmittag, Gaming Time | 4 | 3 |
| `comedy` | Stand-up, Kabarett, Joke Jam | 3 | 3 |
| `speed-dating` | Speed Dating, Singles-Events | 3 | 3 |
| `jazz` | Jam Sessions, Jazzclub | 2 | 3 |
| `food-wein` | Weintasting, Dinner, Street Food, Brunch | 2 | 3 |
| `tanzkurs` | Tango, Salsa-Abend, Bachata | 1 | 3 |
| `laterne-martin` | Laterne basteln, Martinszug *(saisonal, November)* | 1 | 3 |

## Kategorie-Fallbacks – wenn kein Motiv passt (ca. 7 % der Fälle)

Je Kategorie **3 Varianten**: `kat-kultur`, `kat-musik`, `kat-food`, `kat-sport`, `kat-outdoor`, `kat-community`,
`kat-nightlife`, `kat-familie`, `kat-dating`, `kat-sonstiges`.
Diese Bilder dürfen allgemeiner sein (Stimmungsbild Düsseldorf + Thema), z.B. `kat-sonstiges` = Rheinufer am Abend.

**Gesamt: 161 Bilder** (Prio A 64 · Prio B 45 · Prio C 22 · Kategorie 30).
Prio A allein reicht für den Start; der Rest kann nach und nach dazukommen.

---

## Szenen je Variante (für Gemini)

Je Zeile ein Bild. Immer mit dem Stil-Prompt oben kombinieren. Bewusst verschiedene Perspektiven,
damit zwei Events mit demselben Motiv nebeneinander nicht gleich aussehen.

### Prio A

**theater**
1. Empty theater auditorium with red velvet seats, warm stage light on a bare stage
2. Actors on stage seen from the back row, silhouettes against colored stage lights
3. Backstage view: costumes on a rack, mirror with light bulbs, no faces
4. Small black-box stage with a single chair under a spotlight
5. Audience from behind, heads in silhouette, stage glowing in the distance
6. Theater bar in the foyer before the show, glasses and soft lighting, blurred people

**sprachcafe**
1. Café table with coffee cups and an open notebook, several people talking, only hands and arms visible
2. Small group around a wooden table in a cozy café, shot from behind/over the shoulder
3. Close-up of hands gesturing during a conversation, coffee and pastries on the table
4. Stammtisch atmosphere in a German pub, beer and water glasses, out-of-focus people
5. Evening café window from outside, warm light, group inside blurred
6. Name tags without text, cups and a small flag-free table setup for a language exchange

**spieleabend**
1. Top-down view of a board game in progress, cards, dice and wooden pieces
2. Hands holding playing cards around a table, warm lamp light
3. Pen-and-paper role-play table: dice, character sheets without readable text, snacks
4. Shelf full of board game boxes (no readable titles), cozy game café
5. Billiard table with balls mid-game, low warm light
6. Group laughing around a table, only hands and silhouettes, game pieces in focus

**fuehrung-ausstellung**
1. Bright white gallery space with large abstract paintings, a few visitors from behind
2. Museum guide gesturing at an artwork, small group from behind
3. Visitors with flashlights in a dark museum hall (flashlight tour)
4. Sculpture in a modern exhibition room, soft daylight
5. Vernissage: wine glasses, people mingling in front of artworks, blurred
6. Artist studio with canvases, paint and brushes

**lesung-vortrag**
1. Reading chair with a microphone and a stack of books on a small stage
2. Audience in rows in a library hall, speaker blurred in the distance
3. Open book on a lectern under a warm reading lamp
4. Book club: several books and tea cups on a table, hands turning pages
5. Lecture setting with a projector glow (no slide text) and audience from behind
6. Writing session: notebooks, pens, laptop, coffee on a wooden table

**film**
1. Dark cinema hall, light beam from the projector over empty seats
2. Vintage film projector with film reels
3. Audience from behind watching a bright screen (no visible image content)
4. Small art-house cinema with red seats and a curtain
5. Silent-film night: organ in front of a screen, warm dim light

**kinder-geschichten**
1. Children sitting on cushions in a library corner listening to a story (from behind)
2. Colorful picture books spread on a carpet
3. Paper theater (Kamishibai) wooden frame on a table, children's silhouettes
4. Plush toys sitting in a row on a library shelf
5. Kids building with LEGO bricks, only hands visible

**maker-workshop**
1. 3D printer printing a colorful object, close-up
2. Craft table with paper, scissors, glue and colorful materials
3. Repair café: hands repairing a small appliance with tools
4. Makerspace with workbenches, tools and laptops
5. Knitting and crochet: hands with yarn and needles

**tech-meetup**
1. Laptop screens with code (unreadable, blurred) in a modern meetup room
2. Speaker on a small stage seen from the back of the audience, projector glow
3. Developers at a long table with laptops and pizza, from behind
4. Close-up of hands typing on a laptop, colorful screen reflections
5. Whiteboard with abstract diagrams (no readable words), sticky notes

**halloween**
1. Carved pumpkins with candles on a dark wooden table
2. Halloween party with orange and purple lights, dancing silhouettes
3. Spooky decorations: cobwebs, candles, autumn leaves
4. Kids' Halloween crafts: paper bats, pumpkins, scissors
5. Costumed people from behind at a night party, blurred lights

**candlelight-klassik**
1. Hundreds of candles on a stage around a string quartet (from a distance, no faces)
2. Grand piano on a dark stage lit by candles
3. Close-up of a violin and bow in warm candle light
4. Concert hall from the balcony, orchestra small in the distance
5. Big band brass instruments on stands, warm stage light

**bibliothek-beratung**
1. Modern public library with shelves and reading spaces, daylight
2. Tablet showing an e-reader app (no readable text) on a library table
3. Book flea market: tables with stacked second-hand books
4. Helpful conversation at a library desk, hands and laptop, no faces
5. Cozy reading corner with armchair and lamp

### Prio B

**business-networking**
1. Networking event with standing tables, coffee and people from behind
2. Breakfast meeting: coffee, croissants, notebooks on a table
3. Speaker at a lectern from the audience perspective (no text on screen)
4. Startup office with laptops and a whiteboard
5. Handshake close-up in a modern office

**ballsport**
1. Indoor football cage with a ball, players' legs in motion
2. Badminton shuttlecock and racket on an indoor court
3. Padel court with glass walls, racket and ball
4. Amateur football on artificial turf under floodlights in the evening

**tanz-performance**
1. Contemporary dancer silhouette in motion, dramatic side light
2. Dance studio floor with motion blur of dancers
3. Performance on a black stage with haze and colored light
4. Group of dancers from behind in a rehearsal space

**fitness-yoga**
1. Yoga mats in a bright studio, people in a pose from behind
2. Outdoor yoga in a park in the morning light
3. Pilates/barre studio with equipment, soft light
4. Meditation: cushion, candle, calm dim room

**clubnacht**
1. Dance floor with colorful lights and haze, crowd silhouettes
2. DJ booth with turntables and hands on the mixer (no face)
3. Club ceiling with laser beams and smoke
4. Bar counter in a club, neon glow, blurred people

**wandern**
1. Forest trail in autumn near a small creek
2. Hikers from behind on a hilltop path
3. Evening walk with headlamps on a trail
4. Hiking boots on a path with fallen leaves

**oper-musiktheater**
1. Opera house auditorium with balconies and chandelier
2. Stage with elaborate set and dramatic lighting, performers small and distant
3. Orchestra pit seen from above
4. Musical scene with colorful costumes, motion blur, no faces

**laufen**
1. Group of runners from behind along the Rhine promenade, Düsseldorf skyline in the distance
2. Running shoes on wet asphalt, morning light
3. Running group in a park in autumn, motion blur
4. Runners with headlamps in the evening on a riverside path

**live-konzert**
1. Rock concert crowd with raised hands, stage lights in the background
2. Guitarist on stage seen from behind, crowd in front
3. Small club stage with drum kit and warm lights
4. Microphone on a stand, bokeh stage lights

**karneval**
1. Colorful confetti and streamers in the air, festive crowd blurred
2. Carnival costumes and hats from behind, red and white colors
3. Festive hall with decorations and people celebrating (no faces)
4. Street parade with colorful costumes, motion blur

**weihnachtsmarkt**
1. Christmas market stalls with warm lights at dusk
2. Mulled wine mugs and gingerbread close-up
3. Ice rink with fairy lights, skaters blurred
4. Christmas concert in a church with candles

### Prio C

**gaming** — 1. Game controller in hands, screen glow · 2. Kids playing a console in a library, from behind · 3. Cozy gaming corner with screens and colorful light

**comedy** — 1. Microphone on a stand in front of a brick wall, spotlight · 2. Audience laughing, from behind, dim club · 3. Small comedy stage with a stool and a glass of water

**speed-dating** — 1. Two glasses of wine on a small table, candle, blurred bar · 2. Rows of small tables with chairs in a stylish bar · 3. Hands toasting with glasses, evening light

**jazz** — 1. Saxophone on a stand in a dim jazz club · 2. Double bass and piano on a small stage · 3. Jam session from the audience, warm low light

**food-wein** — 1. Wine glasses and bottles (no labels) on a tasting table · 2. Shared dinner table with dishes, hands reaching · 3. Street food stalls at dusk with string lights

**tanzkurs** — 1. Couple's feet in dance shoes on a wooden floor · 2. Tango couple silhouette in a warm hall · 3. Salsa night, dancers in motion blur, colorful lights

**laterne-martin** — 1. Paper lanterns glowing in the dark · 2. Children's hands making lanterns · 3. Lantern procession in the evening, lights in a row

---

## Nächste Schritte (wenn die Bilder da sind)

1. Bilder als `.webp` nach `web/public/fallback/` legen (Benennung siehe oben).
2. Zuordnung im Frontend: Stichworte aus Titel/Beschreibung → Motiv, sonst Kategorie-Fallback
   (die Stichwortlisten aus dieser Analyse werden dafür übernommen).
3. Auswahl der Variante stabil per Event-ID; Bild-Alt-Text kennzeichnet es als Symbolbild.
4. Kennzeichnung „Symbolbild“ klein im Bild, damit niemand es für ein Foto des Events hält.
