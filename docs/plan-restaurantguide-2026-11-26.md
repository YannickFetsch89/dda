# Restaurant-Guide: Bilder, eigene Bewertung, Texte (Vorschläge 26.11.2026)

Stand der Daten: 684 sichtbare Orte (aktiv, Score ≥ 7): 472 Restaurants, 136 Cafés, 76 Imbisse.
Bug „Weitere laden“ und das Ausblenden der Google-Sterne sind gebaut (lokal, `e3246c3`, Branch `claude/restaurantguide`).

---

## A. Eigenes dies.das-Bewertungssystem (Vorschlag)

### Ausgangslage
- Der interne `qualitaets_score` (1–10) ist **vollständig aus Google gerechnet**: Bayes-Mittel aus Sternen und
  Anzahl der Bewertungen (`scraper/orte/flaechensuche.py`, `vorab_score`). Ihn als „dies.das-Bewertung“ zu zeigen,
  wäre eine umetikettierte Google-Bewertung:
  - **UWG § 5:** Eine eigene Note erweckt den Eindruck, wir hätten selbst geprüft. Das wäre irreführend.
  - **Google-EWR-Bedingungen 3.3.2(c):** Es dürfen keine Inhalte „auf Grundlage von Google-Maps-Inhalten“
    entstehen. Siehe die Notiz `google-eea-bedingungen.md`.
- Die Texte stützen sich vielfach auf Gästestimmen („Die Portionen fallen großzügig aus …“). Eine Note
  „Service 4/5“ wäre damit genauso wenig eigene Prüfung.

**Folge:** Eine glaubwürdige eigene Bewertung braucht eine **eigene Grundlage**. Ich schlage deshalb keine Sterne
oder Punkte vor, sondern **redaktionelle Auszeichnungen**, die ehrlich beschreiben, was wir tun.

### Vorschlag (Empfehlung: Variante 1, später 3 dazu)

**Variante 1: Auszeichnungen in drei Stufen, ohne Zahlen**

| Stufe | Bedeutung | Wer entscheidet | Anzeige |
|---|---|---|---|
| *(keine)* | Steht im Guide = von uns ausgewählt | Auswahl wie heute | nichts |
| **dies.das-Tipp** | Hebt sich klar ab (Küche, Konzept, Ort), Begründung in einem Satz | du im Admin (Häkchen + Satz) | goldenes Badge auf der Karte, Kasten „Warum wir es mögen“ auf der Detailseite |
| **Lieblingsort** | Selbst besucht und für richtig gut befunden | nur nach eigenem Besuch | Badge + Hinweis „von uns besucht“ |

- Startvorschläge für den Tipp erzeugt ein Skript. Grundlage: eigene, belegbare Merkmale wie eine Besonderheit
  laut Website, eine eigene Küche oder ein besonderer Ort, dazu der interne Score als Vorfilter. **Entschieden
  wird von Hand.** Ziel: rund 10 % der Orte.
- Filter „Nur dies.das-Tipps“ und Sortierung „Tipps zuerst“.
- **Transparenzseite** `/so-waehlen-wir-aus`, verlinkt bei jedem Badge und am Guide:
  - wie die Auswahl entsteht
  - dass niemand für einen Platz zahlt
  - was die Stufen bedeuten
  - was „Empfohlen“ bei der Sortierung heißt
  
  Das deckt auch die Pflicht ab, die wichtigsten Kriterien einer Rangfolge zu nennen (UWG § 5b Abs. 2), denn
  „Empfohlen“ ist eine Rangfolge.

**Variante 2: Eigene Noten je Kriterium (Küche, Atmosphäre, Service, Preis-Leistung)**
- Ehrlich nur mit eigenem Besuch. Für 684 Orte nicht leistbar, daher nicht empfohlen. Höchstens für die
  „Lieblingsorte“ als Zusatz.

**Variante 3 (später, mit Konten): Stimmen der dies.das-Community**
- Angemeldete Nutzer markieren „War ich, kann ich empfehlen“ (Daumen, keine Sterne). Gezeigt wird ab einer
  Mindestzahl von z. B. 5 Stimmen: „12 aus der Community empfehlen das“.
- **UWG § 5b Abs. 3:** Werden Verbraucherbewertungen gezeigt, muss dabei stehen, ob und wie wir sicherstellen,
  dass sie von echten Besuchern stammen. Ehrlich wäre: „nur angemeldete Konten, eine Stimme je Konto, keine
  Prüfung des Besuchs“.
- Für die Missbrauchs-Sperren bieten sich die vorhandene Bremse und die Admin-Meldungen an.
- Datenschutz: Die Stimme wird im Konto gespeichert, also braucht es eine Ergänzung der Datenschutzerklärung
  (**Anwalt**).

### Was bis zur Entscheidung gilt
- Die Sortierung **„Bewertung“** sortiert weiter nach Google-Sternen, zeigt sie aber nicht mehr an. Vorschlag:
  die Option streichen oder in „Tipps zuerst“ umbauen. Alte Links mit `sort=bewertung` fallen ohne Fehler auf
  „Empfohlen“ zurück.
- Meta-Text der Übersicht: aus „kuratiert nach Bewertung“ wird „von der Redaktion ausgewählt“.
- „Empfohlen“ nutzt intern weiter den Score. Das ist zulässig, gehört aber auf die Transparenzseite.

### SEO
- Das Entfernen der Sterne kostet nichts. Wir hatten bewusst nie `aggregateRating` im JSON-LD, Rich Snippets mit
  Sternen gab es also nicht.
- Variante 1: Badge-Text und „Warum wir es mögen“ sind eigener, einmaliger Inhalt, gut für Suchmaschinen und
  KI-Antworten. Ein `Review`-Markup mit Autor dies.das ginge nur, wenn wir wirklich besucht haben (Lieblingsort),
  sonst nicht.
- Variante 3: Ein `aggregateRating` aus eigenen Community-Stimmen wäre technisch möglich. Google zeigt bei
  LocalBusiness-Seiten Dritter aber nur selten Sterne an, also bitte nicht damit planen.

### Zu entscheiden
- **B1:** Variante 1 (Tipp + Lieblingsort) so umsetzen? Gibt es Namenswünsche für die Stufen?
- **B2:** Sortierung „Bewertung“ streichen oder durch „Tipps zuerst“ ersetzen?
- **B3:** Sollen Kneipen & Bars mitziehen? Dort sind die Sterne mit dieser Änderung ebenfalls weg, weil beide
  Guides dieselben Karten nutzen. Bei Clubs und Spielplätzen stehen sie noch: auch entfernen?

---

## B. Bessere Bilder (Plan, Freigabe nötig vor jedem Lauf)

### Ausgangslage
- **Alle 684** Orte zeigen das **erste Google-Foto**, ausgeliefert über unseren Server (`/ort-foto/<slug>`).
  Format: 442 quer, 206 hoch, 36 quadratisch.
- Bei rund 390 Fotos steht als Urheber vermutlich der Betrieb selbst (grober Namensvergleich), bei rund 294 eine
  Privatperson.
- Rechtlich wackelt die Google-Nutzung ohnehin (Notiz `google-eea-bedingungen.md`): Im EWR darf
  Places-Inhalt nur für eine abschließende Liste von Zwecken genutzt werden, ein Stadtführer steht nicht darauf.
  Fotonamen dürfen nicht gespeichert werden, und bei jedem Foto muss der Urheber genannt sein. **Eigene Bilder
  sind also auch rechtlich der bessere Weg**, wie schon bei den Ortsseiten (/orte).

### Rangfolge der Quellen
1. **Website des Betriebs** (592 von 684 haben eine): Bilder aus Startseite, „Über uns“ und Galerie sowie das
   `og:image`. Geladen, verkleinert, EXIF entfernt, gespeichert als
   `web/public/ort-bilder/restaurants/<slug>.webp`, mit Nachweis und Link (wie `scraper/orte/ortsbilder.py`).
2. **Google, vom Inhaber hochgeladen:** Die Places API liefert bis zu 10 Fotos mit `authorAttributions`.
   Inhaberfotos tragen dort den Namen des Betriebs. Erkannt wird das über den Abgleich des Autorennamens mit
   `displayName` (normalisiert und unscharf). Beim Probelauf prüfe ich von Hand, wie verlässlich das ist.
   Weiter nur über unseren Server, nie gespeichert, Urheber sichtbar.
3. **Google-Nutzerfoto** nur als Rückfall, wie heute.

### Auswahl je Ort
1. **Harte Filter:** mindestens 1.200 px breit, Seitenverhältnis 1,3 bis 2,2 (quer). Hochformat nur, wenn
   sonst nichts da ist. Keine Logos, Speisekarten, Texttafeln oder Stockfotos.
2. **KI-Bildbewertung** (Claude mit Bildeingabe, kleine Vorschau). Note 1–10 für:
   - Bildqualität: Schärfe, Licht, Aufbau
   - Aussagekraft: Gericht, Innenraum oder Außenansicht des Lokals
   - Abzug für Text oder Logo im Bild, Personen im Fokus, Collagen
   
   Dazu kommt ein Vorschlag für den Ausschnitt (`fokus`: oben, unten oder %).
3. **Ergebnis:** das beste Bild aus Quelle 1. Ist dort keins mit Note ≥ 7, kommt Quelle 2 zum Zug, sonst
   Quelle 3. Die Kandidatenliste mit Noten wird gespeichert.

### Kosten (Schätzung, Listenpreise vor dem Lauf in der Cloud-Konsole prüfen)
- **Website-Bilder:** keine API-Kosten. Etwa 2–4 Seitenabrufe je Ort, 2 s Pause, robots.txt beachtet. Für alle
  Orte rund 1–2 Stunden Laufzeit.
- **Google:**
  - Fotoliste je Ort (Place Details nur mit Feld `photos`): 684 Abrufe, das liegt etwa im monatlichen
    Freikontingent.
  - Vorschaubilder nur für quer-formatige Inhaberfotos (aus den Maßen vorab bekannt): grob 1.500–2.500
    Place-Photo-Abrufe, also etwa 5–15 $.
  - Vorschlag: den Google-Teil erst im **Dezember** laufen lassen, weil das Novemberkontingent schon genutzt ist.
- **KI-Bewertung:** rund 3–5 Kandidaten je Ort, kleine Vorschau. Für alle Orte eher im einstelligen
  Dollarbereich.

### Rechte und Nachweis
- **Website-Fotos** sind urheberrechtlich geschützt. Wie bei /orte (E4) gilt „Freigabe holt der Auftraggeber
  nachträglich“, mit sichtbarem Nachweis und Link.
  - **Anwaltsfrage:** Reicht das für einen redaktionellen Guide? Oder braucht es vorab eine Erlaubnis
    (z. B. Mail an die Betriebe mit Widerspruchsmöglichkeit)?
  - Das betrifft potenziell rund 600 Betriebe. Ich bereite gern eine Vorlage für die Mail vor.
- **Google-Fotos:** Urheber mit Link bleibt Pflicht (ist heute schon so). Die grundsätzliche EWR-Frage sollte der
  Anwalt mitbeantworten.

### Admin-Dashboard
- Der Lauf schreibt Kandidaten mit Note nach `extras.bild_kandidaten` (Quelle, Note, Format, Nachweis).
- Die Bilder-Pflege aus Stufe 3b zeigt sie sortiert an. Ein Klick übernimmt ein Bild (setzt `foto_version`).
- Von Hand gewählte Bilder (`foto_manuell`) überschreibt kein Lauf.
- Der Lauf selbst bleibt ein Skript (wie Geo und Kandidaten-Import), kein Button.

### Ablauf
1. Freigabe dieses Plans.
2. **Probelauf mit 15 Orten** (5 Restaurants, 5 Cafés, 5 Imbisse, gemischt mit und ohne Website). Ergebnis ist
   eine lokale Vorher/Nachher-Seite mit Quelle, Note und Ausschnitt. Google-Kosten dafür: unter 1 $.
3. Danach entscheidest du über den Volllauf. Bilddateien gehen per Deploy raus, die SQL führst du aus.

### Zu entscheiden
- **B4:** Plan so freigeben? Darf ich den Probelauf mit Website-Bildern sofort machen und den Google-Teil mit
  rund 15 Orten auch?
- **B5:** Anwaltsfrage Website-Fotos stellen? Mail-Vorlage an die Betriebe gewünscht?

---

## C. Texte (Beispiele, Ausführung erst nach OK)

### Befund
- Mindestens 5 Sätze: **673** Texte. 6–8 Sätze sind typisch, im Mittel rund 775 Zeichen.
- Weniger als 5 Sätze: **11**. Davon haben 7 gar keinen Text. Bei 4 steht ein einziger Satz, und der ist
  **wörtlich Googles Kurzbeschreibung** (`editorialSummary`). Diesen Satz sollten wir ohnehin in eigenen Worten
  schreiben.
- Technik: Fett (`**Wort**`) und Absätze (Leerzeile) kann die Website schon (`BeschreibungText` wie bei /orte).
  Die Restaurant-Detailseite nutzt das jetzt auch (lokal). **Reihenfolge:** erst deployen, dann die SQL
  ausführen, sonst stünden live Sternchen im Text.
- Sicherung: Die SQL legt vorher eine Kopietabelle `orte_texte_sicherung_2026_11_26` (id, beschreibung) an.
- Bei den 673 langen Texten prüft das Skript automatisch, dass **kein Wort geändert** wurde: Text ohne `**` und
  Umbrüche muss gleich dem alten sein. Sonst fällt der Text raus.

### Fall 1: mindestens 5 Sätze, nur Umbrüche und Fett

**Dubai Restaurant Neuss** (Restaurant)

> Wer im Neusser Raum **arabische Küche** sucht, die sich nach echtem Dubai anfühlt, sollte im Dubai Restaurant vorbeischauen. Das Essen wird **frisch zubereitet** und mit viel Liebe gemacht, man schmeckt die hausgemachten Zutaten sofort heraus.
>
> Besonders das **Schawarma mit Knoblauchsoße** ist ein Erlebnis: perfekt knusprig, unglaublich lecker und geschmacklich ganz nah an dem, was man aus Dubai kennt. Die Portionen fallen **großzügig** aus, sodass man satt und zufrieden wieder geht.
>
> Der Service ist aufmerksam und herzlich, das Team begrüßt die Gäste freundlich und lässt sie spüren, dass sie willkommen sind. Die Räume sind sauber und gepflegt, man fühlt sich schnell wohl. Eher ein **unkomplizierter Ort** für ein leckeres Essen als für einen langen Abend, dafür mit viel Herz am Teller.

**Rotkäppchen Café** (Café, Pempelfort)

> Wer in Pempelfort einen entspannten **Brunch** sucht, ist im Rotkäppchen Café richtig. Die **Bagels** sind großzügig mit frischem Gemüse belegt, die **Crêpes** schön knusprig und dabei angenehm leicht. Besonders beliebt sind die **Fisch-Pancakes** und der fischförmige Kuchen, der auch die Kleinen begeistert.
>
> Dazu gibt es Choco Latte, Cappuccino und Matcha, die mit viel Liebe angerichtet werden. Die Atmosphäre ist gemütlich und ruhig, die Einrichtung zuckersüß und liebevoll gestaltet, mit einer kleinen Rotkäppchen-Puppe an der Theke. Das Team begegnet Gästen herzlich und freundlich, man fühlt sich schnell willkommen.
>
> **Für Familien** passt es besonders gut, denn Stifte, Papier und Brettspiele stehen bereit. Ein schöner Ort zum Verweilen.

**The Döner Brothers Neuss** (Imbiss)

> Wer in Neuss richtig Lust auf **Döner** hat, sollte bei The Döner Brothers vorbeischauen. Das Fleisch wird hier **frisch zubereitet** und ist gut gewürzt, ob Hähnchen, Kalb oder Rind. Dazu kommen frische Salate, frittiertes Gemüse und die hausgemachte **Brudi Sauce**, die vielen besonders gut schmeckt. Ein kalter Ayran passt perfekt dazu.
>
> Die Portionen fallen großzügig aus, und die **Dönertasche** ist ordentlich gefüllt. Das Ambiente ist hip und angenehm, und das Team arbeitet freundlich und aufmerksam. Besonders schön: Wer dem Personal sagt, dass er richtig großen Hunger hat, bekommt Rücksicht.
>
> Der Laden passt für eine **schnelle Mahlzeit** zwischendurch, etwa bei einer Zugverspätung, und ebenso für alle, die einfach gern gut essen.

### Fall 2: weniger als 5 Sätze, ausführlicher, wo belegbar (Quelle: Website des Betriebs)

**Phox – Feine Phở Küche** (Stadtmitte). Bisher steht dort nur Googles Satz. Quelle: pho-x.de (Start, Speisekarte, Über uns).

> Im Phox in der Stadtmitte dreht sich alles um **Pho**: Die Brühen werden täglich frisch angesetzt und bis zu acht Stunden gekocht, dazu gibt es hausgemachte Rinder- und Hühnerbällchen, handgerollte Eiernudeln und eigenes Chili-Öl. Neben **Pho Bo** und **Pho Ga** stehen Klassiker wie Sommerrollen, Frühlingsrollen und Bún Bò Xào auf der Karte.
>
> Wer kein Fleisch isst, bekommt eine eigene **vegane Pho** mit Tofu und veganem Hack, auch viele andere Gerichte gibt es in einer veganen Variante. Unter der Woche gilt mittags eine eigene **Mittagskarte**.
>
> Eingerichtet ist das Phox mit **Vintage-Designermöbeln**, serviert wird auf Geschirr, das die Düsseldorfer Keramikerin Michiko Shida eigens dafür gefertigt hat. Das Restaurant versteht sich als Zuhause fernab von Zuhause und gibt lokalen Künstlerinnen und Künstlern Ausstellungsfläche. Der Feinschmecker zählte es zu den **zehn besten vietnamesischen Restaurants** Deutschlands.

*Frage: Die Feinschmecker-Auszeichnung steht nur auf der Website des Phox. Drinlassen oder streichen?*

**Küppers Bierstuben** (Heerdt). Bisher ohne Text. Quelle: kueppers-bierstuben.de (Start, Chronik, Speisen, Gaststube, Terrasse).

> Die Küppers Bierstuben sitzen im **Wetzelhof** an der Heerdter Hauptstraße, gleich vor der St.-Benediktus-Kirche. Der Westgiebel trägt die Jahreszahl **1578**, das Haus ist das letzte erhaltene Gebäude des alten Hofs, und seit 1878 werden hier Gäste bewirtet.
>
> Auf den Tisch kommt **gutbürgerliche, rheinische Küche**: Sauerbraten nach Omas Rezept mit hausgemachten Spätzle, Tafelspitz, Kalbsleber, Brauhaussülze und Schnitzel in vielen Varianten. Dazu läuft frisch gezapftes **Schlüssel Alt** vom Fass, und alle Gerichte gibt es auch zum Mitnehmen.
>
> Drinnen warten zwei Stuben mit Eichenbalken-Tresen und bunten Butzenscheiben, für **Feiern** gibt es einen Saal für bis zu 65 Personen. Im Sommer lockt die große **Terrasse** mit Markise und Heizstrahlern. Schützen und Tambourcorps haben hier ihr Vereinslokal.

**Rosie's** (Friedrichstadt). Die Website (rosies-düsseldorf.de) ist nicht erreichbar, dort ist also **nichts belegbar**.
Bisher steht dort Googles Satz. Vorschlag: denselben Inhalt in eigenen Worten, nicht länger, mit Fett.

> Stylishe **Bar mit Restaurant** in der Friedrichstadt: Von früh bis spät gibt es hier **internationale Küche**, bei gutem Wetter auch draußen auf der **Terrasse**.

### Ablauf nach OK
1. Code deployen (Detailseite mit Fett und Absätzen, Meta-Text ohne Sternchen).
2. Skript:
   - formatiert die 673 langen Texte per KI, mit Wortgleichheits-Prüfung
   - schreibt die 11 kurzen Texte nach Website-Recherche (Subagenten wie bei /orte)
   - legt eine Vorschau-Datei zur Durchsicht an
3. Danach `database/orte_texte_restaurants_2026-11-26.sql` mit Sicherung. Die SQL führst du aus.

### Zu entscheiden
- **B6:** Passt die Dosierung beim Fett (3–5 Schlagwörter je Text, 2–3 Absätze)?
- **B7:** Die Feinschmecker-Frage bei Phox. Allgemein gefragt: Auszeichnungen, die nur auf der eigenen Website stehen, übernehmen?
