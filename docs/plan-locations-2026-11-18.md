# Plan: Eigene Seiten für Veranstaltungsorte („Locations“)

Stand: 18.11.2026 · **erster Entwurf, nicht freigegeben, nichts umgesetzt.** Erstellt von Claude auf Wunsch des Auftraggebers. Vorbild: rausgegangen.de/locations/… (z. B. Roncalli's Apollo Varieté). Ergebnis von Schritt 1 (Bestandsaufnahme, nur lesend) und ein Vorschlag mit offenen Entscheidungen.

Es gelten die üblichen Regeln: Deploy nur nach OK. SQL liegt als Datei in `database/`, der Auftraggeber führt sie aus. Keine neue Bibliothek ohne Rückfrage. Texte auf Deutsch. Der Browser kontaktiert keine Dritten (Bilder und Karten über den eigenen Server).

---

## 1. Bestandsaufnahme (18.11.2026)

**Datengrundlage:**
- Alle Events seit 18.11.2025 einschließlich der kommenden: 5.315, ohne abgelehnte 5.027.
- Die Ortsnamen sind über `pipeline/ortsnamen.py` vereinheitlicht.
- Abgeglichen wurde gegen `orte` (2.310 Zeilen): sichtbar ist ein Ort, wenn er aktiv ist und Score ≥ 7 hat (Spielplätze, Weihnachtsmärkte und Clubs nach ihren eigenen Regeln). Dazu kommen die Club-Verknüpfungen (`extras.club.event_orte`).
- Rohliste: Notizordner der Sitzung, Datei `orte-bestand-2026-11-18.txt`.

### 1.1 Zahlen

| Events je Ortsname (12 Monate + kommend) | Ortsnamen | davon ohne Seite | mit Guide-Seite | Club-Seite | in `orte`, aber unsichtbar |
|---|---|---|---|---|---|
| ≥ 1 | 919 | 831 | 39 | 24 | 25 |
| ≥ 2 | 469 | 414 | 23 | 18 | 14 |
| ≥ 5 | 225 | 182 | 21 | 15 | 7 |
| ≥ 10 | 112 | 92 | 9 | 10 | 1 |
| ≥ 20 | 50 | 42 | 2 | 6 | 0 |
| ≥ 50 | 13 | 11 | 0 | 2 | 0 |

- **78 % aller Events** finden an Orten mit mindestens 5 Events statt.
- Mit mindestens einem **kommenden** Event: 303 Ortsnamen, davon 252 ohne Seite.
- Ohne Stadtteil: 686 von 919 Namen, meist aus dem langen Ende der Liste. Mit Adresse: 424.
- **Bereinigt** um Treffpunkte, Online-Termine und Orte außerhalb und mit Sälen zu Häusern zusammengefasst, bleiben grob:
  - ≥ 3 Events: **≈ 230 echte Orte**
  - ≥ 5 Events: **≈ 140**
  - ≥ 20 Events: **≈ 27**

  Die Zählung ist eine Faustregel per Stichwort und kein fertiger Abgleich.

### 1.2 Was in der Liste steckt (wichtig für den Zuschnitt)

| Art | Beispiele | Folgerung |
|---|---|---|
| **Echte Spielstätten** | Kunstpalast (157), Kom(m)ödchen (79), Tanzhaus NRW (68), Mitsubishi Electric Halle (56), Kunsthalle (54), Capitol Theater (49), Jazz-Schmiede (37), PSD Bank Dome (38) | Kern der neuen Seiten |
| **Säle eines Hauses** | Schauspielhaus: Großes Haus 85, Kleines Haus 62, D'haus 34, Foyer 23, Central 1/2/Brücke 46/42/31, Bühne I/II; zakk: Halle, Club, Tanzraum, Studio, Raum 4, Kneipe; Tonhalle: Mendelssohn-Saal, Rotunde; Kunstsammlung K20/K21; Filmmuseum + Black Box | **Eine Seite je Haus**, Säle als Angabe am Event und als Filter auf der Seite |
| **Treffpunkte, Straßen, Plätze** | „U-Bahnhof Heinrich-Heine-Allee (Ausgang …)“ (70), „S- und U-Bahnhof Flingern, Ausgang …“ (70), „Eingang Kunstakademie“, „Auf ins Viertel – Treffpunkt …“, „Düsseldorf, Bolkerstraße“, Hofgarten, Volksgarten | **Keine Ortsseite** (Stadtführungen). Plätze und Parks höchstens später als eigene Art |
| **Allgemeine Angaben** | „Düsseldorf“ (199), „Altstadt Düsseldorf“ (50), TBA | keine Seite |
| **Online** | Meetup-Online-Gruppen, „Online (IHK)“ | keine Seite |
| **Außerhalb** | Theater Duisburg, Planetarium Erkrath, Neanderthal Museum, Theater Krefeld, FZW Dortmund, Kulturraffinerie Monheim | Entscheidung E3 (nur Düsseldorf, Neuss, Ratingen wie die Guides?) |
| **Netz mit vielen Filialen** | „Stadtbüchereien Düsseldorf“ (331, alle mit der Adresse der Zentralbibliothek) | eine Seite oder Filialen? Die Quelle liefert die Filiale nicht sauber (Folgepunkt) |

### 1.3 Nebenbei gefundene Datenfehler (Folgepunkte, nicht Teil dieses Plans)
- „Theater Duisburg“ (37 Events) und „UFO am Rather Carré“ stehen mit der Adresse der Oper Düsseldorf und Stadtteil Pempelfort bzw. Altstadt in der Datenbank.
- Meetup-Adressen enthalten das Wort „meetup9“, z. B. „Emmastrasse 25 meetup9 Düsseldorf“.
- „Galerie für Zeitgenössische Kunst“ liegt in Leipzig, kommt aber im Düsseldorfer Bestand vor.
- Varianten, die `ortsnamen.py` noch nicht kennt: „Roncalli's Apollo Varieté“ und „… Variete“, „Rudas Studios“ und „Rudas Studios Club“, „Rundum Yoga“ und „… Studio“, „R25 Kulturschlachthof“ und „Kulturschlachthof R25“ (verschiedene Adressen!).

## 2. Vorbild Rausgegangen (angesehen am 18.11.2026)

Am Beispiel `rausgegangen.de/locations/roncallis-apollo-variete/`:
- **Kopf:** Titelbild mit Nachweis „FOTO: © Roncalli's Apollo Varieté“, Name, Adresse, „Gefolgt von 276 Personen“, Buttons **Folgen** und **Teilen**.
- **Reiter:** Übersicht · Events (134) · Infos · Barrierefreiheit.
- **Inhalt:**
  - Nächste Events (4 sichtbar, „Mehr laden“, „Alle Events 22“)
  - „Über die Location“: Der Text ist erkennbar vom Haus selbst geschrieben („wir … bieten Euch“).
  - Öffnungszeiten, Links, Barrierefreiheit (oft „keine Infos“)
  - „Vielleicht gefällt dir auch das?“, „Ähnliche Seiten“ mit vielen internen Links
- **SEO:**
  - Titel „<Ort> in Düsseldorf | Alle Events, Termine & Tickets“, eigene Canonical-URL
  - JSON-LD `LocalBusiness` mit Adresse und Geo, `ItemList` der Events, `BreadcrumbList` Düsseldorf → Locations

Rausgegangen arbeitet mit Partnern. Die Häuser liefern Texte und Bilder offenbar selbst.

## 3. Vorschlag

### 3.1 Grundsatz: eine URL je Ort (E1 aus dem Orte-Guide)
- Ein Ort, der schon eine Guide-Seite hat (Bar, Club, Restaurant, Weihnachtsmarkt), bekommt **keine zweite Seite**.
  - Seine Guide-Seite erhält die Event-Liste.
  - `/orte/<slug>` leitet dorthin weiter (308).
- Alle anderen Spielstätten bekommen eine neue Seite **`/orte/<slug>`** und eine Übersicht **`/orte`**.
- Alternative für E1: `/locations/<slug>` wie Rausgegangen. Ich empfehle das deutsche `/orte`, passend zu `/stadtteile` und `/reihe`.

### 3.2 Datenmodell (Vorschlag, Entscheidung E5)
- **In der Tabelle `orte`** mit neuem Typ **`spielstaette`**: neue Zeile im CHECK, wie bei `weihnachtsmarkt`.
  - Adresse, Geo, Bild, `extras` und Seitenlogik gibt es dort schon.
  - Profil in `extras.spielstaette`:
    - Art: Theater, Museum, Konzert/Halle, Kino, Kunstraum, Kleinkunst, Bibliothek/Kultur, Sport, Kirche …
    - Säle
    - `event_orte`: alle Schreibweisen aus den Events, wie bei den Clubs
    - Webseite, Bildnachweis, kurzer eigener Text
- **Zuordnung Event → Ort:**
  - **Stufe A (schnell):** wie bei den Clubs über die Namensliste `event_orte` beim Rendern. Keine Änderung an `events`.
  - **Stufe B (für „Folgen“ nötig):** neue Spalte `events.ort_id`, gesetzt von der Pipeline beim Speichern, dazu ein Nachtrag per SQL. Damit gehen Abfragen wie „neue Events an Orten, denen ich folge“ (Konzept B4/B8) schnell und sicher.
  - Empfehlung: gleich Stufe B einplanen, weil die Personalisierung darauf baut.
- **Pflege:** `pipeline/ortsnamen.py` bleibt die Liste der Schreibweisen. Neu ist die Liste der Spielstätten mit ihren Sälen, als CSV wie `data/weihnachtsmaerkte/*.csv` und per Skript importiert.
- **Erstbefüllung:**
  - halbautomatisch aus der Bestandsliste (Gruppen bilden, Adresse aus den Events)
  - Geo und `place_id` per Google Places Text Search. Bei ≈ 230 Orten bleibt das voraussichtlich im Freikontingent, sonst wenige Dollar. Kosten werden vor dem Lauf genannt.
  - Der Auftraggeber sichtet die Liste vor dem Import.

### 3.3 Welche Orte bekommen eine Seite (Entscheidung E2)
- **Vorschlag:** ein echter Ort mit **≥ 3 Events in 12 Monaten** oder **≥ 1 kommendem Event und Adresse**. Das sind anfangs grob 230–260 Seiten.
- Indexiert wird eine Seite nur, wenn sie kommende Events oder einen eigenen Text hat. Sonst ist sie `noindex`, um dünne Seiten zu vermeiden.
- Keine Seiten für Treffpunkte, Straßen, Online-Termine und allgemeine Angaben.

### 3.4 Aufbau der Seite `/orte/<slug>`

| Block | Inhalt |
|---|---|
| Kopf | Bild mit Nachweis (oder Ersatz, 3.6), Name, Art („Theater“, „Museum“ …), Adresse, Stadtteil; Buttons Teilen, Route; **Folgen** kommt mit Konzept B4 |
| Nächste Events | alle kommenden, nach Datum, Filter nach Saal, wenn es mehrere gibt; Langläufer (Ausstellungen) oben gesondert |
| Über den Ort | 2–4 eigene Sätze (KI-Entwurf aus öffentlich belegbaren Angaben, vom Auftraggeber freigegeben). Später optional der Text, den das Haus selbst liefert |
| Infos | Webseite, Säle, ÖPNV-Haltestelle (optional), Barrierefreiheit nur mit Quelle |
| Karte | eigene MapLibre-Karte (vorhanden), kein Google auf der Seite |
| Reihen | Reihen an diesem Ort (Links auf `/reihe/<slug>`) |
| In der Nähe / ähnlich | andere Orte im Stadtteil und gleiche Art, Guide-Orte in der Nähe (Bars vor dem Konzert) |
| SEO | Titel „<Name> Düsseldorf: Programm, Termine & Infos“, Canonical, Brotkrumen Startseite → Orte → Name. JSON-LD je nach Art: `PerformingArtsTheater`, `Museum`, `MusicVenue`, `MovieTheater` oder sonst `Place`, dazu `ItemList` der Events |

**Übersicht `/orte`:** A–Z, Filter nach Art und Stadtteil, Karte, Suche. Verlinkt aus „Entdecken“, aus dem Fuß und von den Stadtteilseiten.

**Eventseiten:** Der Ortsname wird zum Link auf die Ortsseite. Das ersetzt den bisherigen Link „Weitere Events an diesem Ort“, der nur auf die Suche führt. Der Club-Link bleibt.

### 3.5 Technik
- **Proxy** (`web/proxy.ts`, `lib/pfad-pruefung.ts`): `/orte/:slug` kommt in den Matcher.
  - unbekannter Slug → echte 404 direkt aus dem Proxy, kein Rewrite (Memory „Proxy-Rewrite hinter nginx“)
  - Guide-Ort → 308 auf die Guide-URL
  - umbenannter oder zusammengelegter Ort → 308 (wie beim Märchen-Markt)
- **Caching** wie bei den Guides (`use cache`). Die Event-Liste kommt aus `eventPoolLaden()`.
- **Sitemap:** nur indexierbare Ortsseiten. Danach IndexNow wie bei den Weihnachtsmärkten.
- **Bilder** unter `/ort-bilder/orte/<slug>.webp`, nicht unter `/orte/…`, weil der Proxy diese Pfade als Seiten prüft. Das ist dieselbe Lehre wie bei `/guides/` und `/ort-bilder/`.

### 3.6 Bilder und Rechte (Entscheidung E4)
Der Auftraggeber möchte Bilder der Veranstalter bzw. Häuser. Das geht nur mit **Erlaubnis** und **Bildnachweis**.

| Weg | Rechte | Aufwand | Bewertung |
|---|---|---|---|
| **Haus fragen** (Mail: „Dürfen wir dieses Foto auf unserer Ortsseite mit Nachweis zeigen?“) | sauber, schriftliche Erlaubnis aufbewahren | mittel (Mail je Haus, Rücklauf) | **empfohlen** für die Top 30–50 |
| **Pressebereich des Hauses** (viele Theater, Museen, Hallen haben Pressefotos) | nur wenn die Bedingungen die Nutzung erlauben (oft „redaktionelle Berichterstattung mit Nachweis“). Je Haus prüfen und Wortlaut notieren | klein bis mittel | gut, mit Prüfung |
| **Wikimedia Commons** (CC BY / CC BY-SA, viele Düsseldorfer Häuser vorhanden) | erlaubt mit Urheber, Lizenz und Link. Bei BY-SA steht ein zugeschnittenes Bild wieder unter BY-SA | klein | gute Ergänzung, Nachweis-Zeile nötig |
| **Eigene Fotos** | eigene Rechte. Personen nur fern oder unscharf (wie bei den Weihnachtsmärkten) | Zeit vor Ort | sehr gut, langsam |
| **Google-Fotos** (wie in den Guides) | EWR-Bedingungen von Google, Anwaltsfrage offen | klein | nicht empfohlen für neue Seiten |
| **Bilder von Rausgegangen oder anderen Portalen übernehmen** | **nicht erlaubt**: fremdes Urheberrecht bzw. Nutzungsrecht, nur dem Portal eingeräumt | — | **ausgeschlossen** |
| **Event-Bilder der Quellen** als Ortsbild | zeigen das Event, nicht den Ort. Die Rechte gelten nur für die Bewerbung des Events | — | nicht als Ortsbild |
| **Ersatz ohne Foto** | eigene Kachel mit Art-Piktogramm, Farbe, Name; dazu die Karte | klein | Standard für alle ohne Freigabe |

**Ablauf** wie beim Weihnachtsmarkt-Guide (`scraper/weihnachtsmaerkte/bilder.py`, `data/weihnachtsmaerkte/bilder.csv`):
- CSV mit Ort, Datei, Nachweis, Link, Erlaubnis (Datum, Art: Mail/Presse/Lizenz)
- Das Skript bricht ohne Erlaubnis ab, verkleinert das Bild und legt es unter `/ort-bilder/orte/` ab.
- `extras.bild_link` zeigt auf den Nachweis.
- Die Erlaubnis-Mails liegen nicht im Repo (Firmenordner), im CSV steht nur ein Vermerk.
- **Vorlage für die Anfrage-Mail** liefert Claude nach der Entscheidung. Sie wird nur nach Freigabe verschickt, und zwar vom Auftraggeber.

### 3.7 Bezug zur Personalisierung (`docs/konzept-personalisierung-2026-11-18.md`)
- **B4 „Folgen“ von Orten** braucht genau diese Seiten und eine feste Orts-ID (`events.ort_id`, 3.2 Stufe B). Der Button „Folgen“ kommt dann auf die Ortsseite. Gefolgte Orte speisen „Neu bei deinen Orten“ in „Für dich“.
- **B1 „Für dich“:** „gleicher Ort wie ein gemerktes Event“ (Kontenplan 13) wird mit `ort_id` genauer als über den Namen.
- Reihenfolge: Ortsseiten zuerst. Folgen ist ein eigener Schritt im Personalisierungsplan.

## 4. Schritte (Vorschlag)

| Schritt | Inhalt | Wer |
|---|---|---|
| 0 | Dieser Plan, Entscheidungen E1–E7, Cursor-Prüfung | Auftraggeber |
| 1 | Liste der Spielstätten: Gruppen bilden (Häuser, Säle, Varianten), Klassen (Treffpunkt, online, außerhalb), Adresse, Art. CSV zur Sichtung | Claude, Sichtung Auftraggeber |
| 2 | SQL: Typ `spielstaette`, ggf. `events.ort_id` + Index. Import-Skript, Google-Abgleich für Geo (Kosten vorher), Nachtrag `ort_id`; `ortsnamen.py` um die neuen Varianten ergänzen | Claude schreibt, Auftraggeber führt aus |
| 3 | Seiten `/orte` und `/orte/<slug>`, Proxy-Regeln, Sitemap, Links von Eventseiten, Tests | Claude |
| 4 | Texte „Über den Ort“ (KI-Entwurf, Freigabe), Bilder nach 3.6 (Anfragen, Commons, eigene) | Claude + Auftraggeber |
| 5 | Cursor-Prüfung, Deploy nach OK, Live-Prüfung (`curl -I` auf 200/308/404), IndexNow | Claude, Auftraggeber |

## 5. Entscheidungen des Auftraggebers (18.11.2026)
- **E1 URL: `/orte/<slug>`.** Für SEO ist es praktisch egal: Google wertet das Wort im Pfad kaum, entscheidend sind Titel, Inhalt und interne Links. `/orte` passt zur deutschen Seite (`/stadtteile`, `/reihe`).
- **E2 Schwelle: ab 2 Events** (12 Monate + kommend), echte Orte. Indexiert nur mit kommenden Events oder eigenem Text (3.3).
- **E3 Gebiet: nur Düsseldorf, Neuss, Ratingen.** Events aus anderen Städten werden in der Pipeline **konsequent herausgefiltert**. Anlass: Ein Leipziger Event war auf der Seite. Umsetzung: neuer Filter `pipeline/gebiet.py` (18.11.2026, siehe Abschnitt 6).
- **E4 Bilder: direkt vom Veranstalter/Venue.** Die Freigaben holt der Auftraggeber später ein, das rechtliche Risiko trägt er. Der Bildnachweis wird trotzdem immer angezeigt, die Herkunft je Bild in der CSV festgehalten (Seite, Datum).
- **E5 Datenmodell: Typ `spielstaette` in `orte` und `events.ort_id`.** Dazu eine gute Dubletten-Erkennung für Orte: Varianten, Säle, gleiche Adresse/Geo, Abgleich mit bestehenden Guide-Orten (eine URL je Ort).
- **E6 Säle: beides.** Eine Seite je Haus mit Saal-Filter. Große Säle oder Bereiche mit vielen Events bekommen zusätzlich eine eigene Seite (z. B. Central, Großes Haus). Diese verweist auf das Haus und umgekehrt.
- **E7 Stadtbüchereien: je Filiale.** Voraussetzung: Der Scraper liefert die Filiale. Heute stehen alle 331 Events mit der Adresse der Zentralbibliothek in der Datenbank. Das wird als Teil von Schritt 1 geklärt.

## 6. Korrekturen der Datenfehler (18.11.2026, vor dem eigentlichen Plan)
1. **Gebietsfilter** `pipeline/gebiet.py`: Postleitzahl außerhalb von Düsseldorf (40210–40629), Neuss (41460–41472) und Ratingen (40878–40885), andere Städte im Ort oder in der Adresse und bekannte auswärtige Orte werden vor dem Speichern verworfen. Der Bestand wird per SQL bereinigt (`database/gebiet_bereinigung_<datum>.sql`).
2. **Oper am Rhein:** Die Standard-Adresse gilt nur noch für das Opernhaus Düsseldorf. Spielorte in Duisburg fallen durch den Gebietsfilter heraus. „UFO am Rather Carré“ bekommt keine falsche Opern-Adresse mehr.
3. **Meetup:** Platzhalter-Postleitzahlen („meetup9“) kommen nicht mehr in die Adresse, der Bestand wird bereinigt.
**SQL zum Bestand** (Reihenfolge):
1. `database/gebiet_bereinigung_2026-11-18.sql`: 348 Events außerhalb löschen, vor allem PRINZ.de (Region) und Oper/Duisburg.
2. `database/datenfehler_2026-11-18.sql`: Meetup-Platzhalter, R25-Adresse, Opern-Adressen.
3. `database/ortsnamen_2026-11-18.sql`: Namensvarianten.

Code: `pipeline/gebiet.py` (neu, in `main.py` als Schritt 1c), `scraper/tier2/oper_am_rhein.py`, `scraper/tier1/meetup.py`, `scraper/tier2/kulturschlachthof_r25.py`, `pipeline/stadtteil_mapper.py`, `pipeline/ortsnamen.py`, Tests `tests/test_gebiet.py`.

4. **Namensvarianten** in `pipeline/ortsnamen.py` ergänzt. Der Kulturschlachthof R25 hat die richtige Adresse Rather Straße 25, 40476 Düsseldorf (Derendorf), bisher stand dort die Adresse des Stahlwerks.

## 7. Ursprünglich offene Fragen (beantwortet in Abschnitt 5)
- **E1 URL:** `/orte/<slug>` (Vorschlag) oder `/locations/<slug>`?
- **E2 Schwelle:** Seite ab ≥ 3 Events in 12 Monaten oder ≥ 1 kommendem Event mit Adresse (≈ 230–260 Seiten)? Oder enger, ab ≥ 5 (≈ 140)?
- **E3 Gebiet:** nur Düsseldorf + Neuss + Ratingen (wie die Guides) oder auch Duisburg, Krefeld, Erkrath …, wenn dort regelmäßig Events stattfinden?
- **E4 Bilder:** Häuser anschreiben (Top 30–50) + Wikimedia Commons + Ersatzkachel als Standard? Google-Fotos für Ortsseiten ausschließen?
- **E5 Datenmodell:** neuer Typ in `orte` und gleich `events.ort_id` (Vorschlag), oder erst nur Namensliste?
- **E6 Säle:** eine Seite je Haus mit Saal-Filter (Vorschlag), oder eigene Seiten für große Säle (z. B. „Central“)?
- **E7 Stadtbüchereien:** eine Seite für das ganze Netz oder Filialen (dafür muss erst die Quelle die Filiale liefern)?
