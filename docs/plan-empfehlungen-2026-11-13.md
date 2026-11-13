# Plan: Empfehlungen auf der Startseite

Stand: 13.11.2026, nach fünf Prüfungen und den Nachträgen. **Vom Auftraggeber freigegeben am 13.11.2026.** Umgesetzt am 13.11.2026 (lokal, noch nicht deployt; SQL `database/flaggen_zeitpunkt_2026-11-13.sql` steht aus).

Betrifft die Auswahl von Tipp, Picks, „Beliebt“, der Wochenend-Box, des Zeitraums Wochenende und des Highlights. Kalender, Suche, Kategoriezeilen und Stadtteilseiten bleiben, wie sie sind.

## 1. Ziel

Die Startseite empfiehlt, was jemand an diesem Tag in Düsseldorf unternehmen würde, und mischt ein Szene-Event und einen Fund darunter. Stammformate wie Sprachcafé, Kurs und Sprechstunde bleiben im Kalender und in den Kategoriezeilen, führen die Seite aber nicht an. Eine Ausstellung über Wochen ist nicht an jedem Tag der Tipp.

## 2. Befund

`beliebtheit()` in `web/lib/ableitungen.ts` (Zeilen 38–51) gibt einem Event mit Bild, Beschreibung über 80 Zeichen, Uhrzeit und Stadtteil 23 Punkte. Den Gleichstand entscheidet `hash(id) % 100 / 100`.

Das Bild ist zusätzlich ein hartes Sortierkriterium. `nachBeliebtheit` (Zeilen 97–104) stellt jedes Event mit Bild vor jedes ohne Bild, auch wenn Markierungen den Score darüber heben. Das gilt seit der Zusage vom 12.11.2026.

Tipp und Picks stehen in `web/app/page.tsx` (Zeilen 97–105). Der Tipp nimmt das erste Event im geladenen Zeitraum mit `tipp_des_tages` und Bild, sonst das erste nach `nachBeliebtheit`. Picks kommen aus `vielfaeltig()` (Zeilen 252–272): je eine Kategorie, dann der Rest. „Beliebt“ sind fünf Einträge derselben Sortierung, `auffuellen` (Seite, Zeilen 38–41) füllt aus der Woche auf.

Dieselbe Heuristik nutzen `wochenendProgramm()` und `highlights()` (`ableitungen.ts`, Zeilen 282–318). `highlights()` hängt auf `/entdecken`.

`filtern()` ruft `findetStatt()` ohne `mitLanglaeufern` auf (`ableitungen.ts` Zeile 164, `web/lib/datum.ts` Zeilen 161–165). Ein Langläufer steht damit nur an seinem Starttag in der Tagesliste. Eine Ausstellung, die schon läuft, fehlt an den Folgetagen ganz.

Die drei Flaggen sind Wahrheitswerte ohne Datum (`database/schema.sql`, Zeilen 55–57). Das Dashboard schaltet sie in `dashboard/app.py` (Zeilen 250–276) nur um. Der Link „Von der Redaktion“ steht in `page.tsx` (Zeile 169) auch dann, wenn die Heuristik gewählt hat.

Der Pool beginnt bei heute (`web/lib/daten.ts`, Zeilen 116–117: `datum >= heute` oder `datum_bis >= heute`). Vergangene Tage sind nicht geladen. Eine Erinnerung „was in den letzten sieben Tagen vorne stand“ lässt sich daraus nicht nachrechnen.

Abgesagte Events fehlen auf der Startseite (`page.tsx`, Zeile 65), der Tipp selbst prüft `abgesagt` aber nicht (Zeile 99). Ein abgesagtes, markiertes Event kann Tipp werden, sobald es im Zeitraum liegt.

## 3. Stufe

Jedes nicht abgesagte Event bekommt für die Empfehlungen eine Stufe. Abgesagte Events haben keine Stufe und besetzen keinen Platz.

So wird gerechnet. Die Schritte 4 und 5 sind Obergrenzen, keine eigenen Stufen.

1. **Stamm oder Sprachhinweis → 0, fertig.** Der Titel wird immer geprüft. In der Beschreibung zählt ein Treffer nur, wenn im selben Satz ein Wort für Regelmäßigkeit steht, ebenfalls ohne Rücksicht auf Großschreibung: `jeden (montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag|tag|abend|morgen|woche|monat)`, `wöchentlich`, `monatlich`, `regelmäßig`, `immer (montags|dienstags|mittwochs|donnerstags|freitags|samstags|sonntags)`. Ein Satz endet am nächsten `.`, `!` oder `?`, wie in Abschnitt 5. Das Stamm-Muster ist ausgeschrieben und gilt ohne Rücksicht auf Groß- und Kleinschreibung, Flag `i`: `yoga|pilates|meditation|lauftreff|parkrun|repair-?café|spieleabend|brettspiel|sprechstunde|\bmeetup\b|speed-?dating|sprachcaf[eé]|sprachtreff|sprachtandem|\btandem\b|language exchange|conversation club|stammtisch|(?<!dis)kurse?\b`. Vor „kurs“ steht keine Wortgrenze, damit Sprachkurs, Grundkurs und Einsteigerkurs treffen. Die Rückschau `(?<!dis)` lässt „Diskurs“ aus, die Wortgrenze nach „kurs“ lässt „Exkursion“ aus. `\bmeetup\b` trifft „Python Meetup Düsseldorf“. Oder der Sprachhinweis aus Abschnitt 5 greift. Beispiele: „Sprachcafé Englisch“ und „Move it!“ (Yoga und „jeden Mittwoch“ im selben Satz) → 0. „ENGLISH COMEDY NIGHT“ (YogArt nur als Veranstalter), „Wanderung im Grafenberger Wald“ („Tandem-Partner“ ohne Regelmäßigkeit) und „Speed tasting“ („Speed-Dating“ ohne Regelmäßigkeit) werden davon nicht 0. „AfterWorkOut“ ohne Treffer im Titel und ohne Regelmäßigkeit in der Beschreibung folgt den übrigen Regeln. „Exkursion …“ wird nicht 0. Ausnahme: eine geltende Tipp-Flagge (Abschnitt 8) macht das Event zum reinen Tipp-Kandidaten. Es bleibt Stufe 0, ist dann Tipp und besetzt keinen Pick.
2. **Grundstufe.** Zugpferd nach Abschnitt 4 → 3. Szene (Jam-Session, Open Stage, Open Mic, Karaoke) → 1. Sonst → 2. Kategorie `community`, oder „Workshop“, „Atelier“ oder „Foyer“ im Titel **oder im Ort**, bekommt an einem Zugpferd-Ort höchstens 2, nicht 3. „Opernhaus Düsseldorf Foyer“ und „Düsseldorfer Schauspielhaus Foyer“ bleiben damit höchstens 2.
3. **Serie** nach Abschnitt 6 → `min(Grundstufe, 1)`. Eine täglich laufende deutschsprachige Führung ist damit höchstens 1. Die Häufigkeit entscheidet vor der Kategorie.
4. **Langläufer** → `min(Grundstufe, 2)`, außer der Titel trifft `ZUGPFERD_TITEL`. `istLanglaeufer` (`web/lib/datum.ts`, Zeilen 84–85): `datum_bis` gesetzt, Laufzeit über 7 Tage, Kategorie nicht `nightlife` und nicht `food`. Diese Obergrenze gilt nicht für `nightlife` und `food`. Tipp und „Fund“ hängen für jedes mehrtägige Event am Fokustag (Abschnitt 7), nicht nur für Langläufer.
5. **Geltende Highlight- oder Top-Flagge** → Stufe +1, höchstens 3. Die Tipp-Flagge ändert die Stufe nicht.

Beispiele, die sich aus dieser Reihenfolge ergeben:

- Premiere im Kunstpalast: Grundstufe 3, keine Serie, kein Langläufer → 3.
- Ausstellung im Kunstpalast über 40 Tage: Grundstufe 3, ein Eintrag und damit keine Serie, Langläufer ohne Treffer in `ZUGPFERD_TITEL` → 2.
- Jam-Serie: Grundstufe 1, Serie → 1.
- Rheinkirmes über 10 Tage: Grundstufe 3 über `ZUGPFERD_TITEL`, Langläufer, die Obergrenze gilt für diesen Titel nicht → 3.

## 4. Zugpferd-Listen

Es gibt kein Feld „eigene Bühne“. `quelle_name` taugt nicht: nach der Dublettenprüfung steht dort oft der Aggregator, obwohl das Event in der Tonhalle stattfindet. `web/lib/symbolbild.ts` ab Zeile 121 ordnet Quellen Motive zu, nicht Orte.

Verglichen wird `norm(ort)` aus `web/lib/termine.ts` (Zeilen 63–69). Ein Listeneintrag trifft nur, wenn der normalisierte Ort **mit** dem Eintrag beginnt. „tonhalle“ trifft „Tonhalle“ und „Tonhalle Düsseldorf“. Er trifft nicht „Denkmal vor dem Restaurant Tonhalle in Düsseldorf Kaiserswerth“.

Das erste Wort nach dem Eintrag entscheidet, Bindestriche und Leerzeichen werden übersprungen. Ist dieses Wort eines von terrace, terrasse, café, cafe, club, bar, tiefgarage, ist es nicht das Haus. „Tonhalle Terrace“ und „Capitol Theater - Club Saal“ sind damit kein Treffer.

**`ZUGPFERD_ORTE`:**

- tonhalle
- deutsche oper am rhein
- opernhaus düsseldorf
- düsseldorfer schauspielhaus
- schauspielhaus
- fft
- tanzhaus nrw
- kunstpalast
- k20
- k21
- kunstsammlung nrw
- kunsthalle düsseldorf
- nrw-forum
- mitsubishi electric halle
- capitol theater
- kommödchen
- merkur spiel-arena
- psd bank dome

Je Eintrag zwei Tests. Der positive Fall ist der Eintrag selbst, auch mit nachgestelltem „Düsseldorf“. Der negative Fall ist ein Ort, der den Eintrag nur enthält oder mit einem der Ortswörter oben weitergeht. Belegte Fehltreffer:

- tonhalle → „Denkmal vor dem Restaurant Tonhalle in Düsseldorf Kaiserswerth“, „Tonhalle Terrace“
- deutsche oper am rhein → „Treffpunkt Social Night Out … Deutsche Oper am Rhein“
- opernhaus düsseldorf → „Opernhaus Dortmund“, „Opernhaus Wuppertal“
- kunsthalle düsseldorf → „G2 Kunsthalle“
- psd bank dome → „Tiefgarage PSD Bank Dome“
- capitol theater → „Capitol Club“, „Club im Capitol-Theater“, „Capitol Theater - Club Saal“

Für die übrigen Einträge genügt als Fehltreffer ein Ort, der den Eintrag in der Mitte trägt und nicht damit beginnt.

Kinos und das Filmmuseum stehen bewusst nicht auf der Liste. Ein einzelner Film bleibt Stufe 2, sonst füllt das Tagesprogramm jeden Tipp.

**`ZUGPFERD_TITEL`**, Muster auf dem Titel, je Eintrag ein Test:

- Rheinkirmes
- Japan-Tag
- Nacht der Museen
- CSD, mit derselben Ausnahme wie in `symbolbild.ts` Zeile 84, damit „Pride and Prejudice“ nicht trifft

Ein Treffer in `ZUGPFERD_TITEL` ist von der Langläufer-Obergrenze ausgenommen (Abschnitt 3, Schritt 4). Eine Ausstellung an einem Zugpferd-Ort bleibt höchstens 2. Die Rheinkirmes über etwa 10 Tage bleibt 3.

**Heimspiel.** Kategorie `sport`, und der Titel oder der Ort nennt Fortuna oder die DEG bzw. ihre Halle. „Auswärts“, „Public Viewing“ und „Fanshop“ bleiben außen vor. Je ein Test für ein Heimspiel und ein Auswärtsspiel.

## 5. Sprachhinweis

Das Muster `sprachcafe` in `symbolbild.ts` Zeile 101 wird nicht wiederverwendet. Es kennt „auf Französisch“ nicht und trifft dafür Bandnamen, „conversation“ und jeden Stammtisch. Dort ist ein Fehltreffer ein falsches Symbolbild, bei der Stufe wäre es ein verlorener Tipp.

Der Titel wird immer geprüft. Die Beschreibung nur, wenn das Event eine Führung, ein Kurs oder ein Treffen ist: Kategorie `stadtfuehrung` oder `community`, oder der Titel enthält Führung, Kurs, Treff oder Stammtisch. So stuft „Audioguide auf Englisch verfügbar“ in der Beschreibung einer Ausstellung nicht ab.

Vor dem Abstufen gilt die Ausnahme, wenn der geprüfte Text dieses Muster trifft:

`/deutsch und|und deutsch|zweisprachig|bilingual/i`

„Führung in Englisch und Deutsch“ bleibt damit auf der Stufe, die ohne den Sprachhinweis gilt.

Das Abstuf-Muster gilt ebenfalls ohne Rücksicht auf Groß- und Kleinschreibung:

`/\b(auf|in) (englisch|französisch|spanisch|italienisch|türkisch|niederländisch|polnisch)\b|\bin (englisch|französisch|spanisch|italienisch|türkisch|niederländisch|polnisch)(er|en)? sprache\b|\bin english\b|\b(english|french|spanish) (tour|guided tour)\b|visite guidée|visita guiada/i`

Kein Abstufen, wenn im selben Satz wie der Sprachtreffer „Audioguide“, „Untertitel“, „Übersetzung“ oder „übersetzt“ steht. Ein Satz endet am nächsten `.`, `!` oder `?`. Steht der Sprachhinweis in einem anderen Satz, gilt er.

Weitere Ausnahmen:

- Kategorie `musik`: keine Sprachabstufung. „French Jazz Night“ und „The English Beat“ bleiben unberührt.
- Unterkategorie `film` und Titel mit OmU oder OV: keine Sprachabstufung. Ein spanischer Filmtitel bleibt auf 2.

## 6. Serie

`ist_wiederkehrend` wird nicht verwendet. Die Spalte steht nicht im Select von `web/lib/daten.ts` (Zeilen 11–15), und der Kategorisierer setzt sie für jedes Event mit `datum_bis` (`pipeline/categorizer.py`, Zeilen 229–233). Damit wäre jede Ausstellung eine Serie.

Gezählt werden verschiedene Einträge nach der Bündelung (`web/lib/termine.ts`): Zeilen mit unterschiedlichem `datum`. Die Tage, über die sich ein einzelner Eintrag mit `datum_bis` erstreckt, zählen nicht. Ein Event mit `datum_bis` ist ein Eintrag. Eine Ausstellung über 20 Tage ist damit keine Serie.

Eine Serie ist, was zutrifft:

- das Feld `reihe` ist gesetzt, oder
- dieselbe Gruppe mit gleichem `norm(basisTitel(titel))` hat in irgendeinem Fenster von `datum` bis `datum + 14`, die Grenzen eingeschlossen, mindestens drei gebündelte Einträge mit unterschiedlichem `datum`, oder
- dieselbe Gruppe mit gleichem `norm(ort)` und gleicher Kategorie hat in einem solchen Fenster mindestens drei Einträge.

Der Status gilt für die ganze Gruppe, nicht für einen einzelnen Termin. Eine Führung an Montag, Dienstag und Mittwoch ist an allen drei Tagen Serie. Eine wöchentliche Reihe mit Terminen am Tag, an Tag +7 und an Tag +14 ist Serie, weil die Grenzen mitzählen. Zwei Termine im Abstand von 14 Tagen sind keine Serie.

Die dritte Regel gilt nicht für Orte aus `ZUGPFERD_ORTE` und nicht für `SAMMELORTE`. Fünf verschiedene Konzerte in der Tonhalle in 14 Tagen bleiben einzeln Stufe 3. Dieselbe betitelte Reihe, die dort an drei Tagen liegt, fällt über den Titel auf höchstens 1.

**`SAMMELORTE`**, `norm(ort)` ist genau dieser Wert, nicht ein Präfix. Beim Bau aus den Daten ergänzt:

- düsseldorf
- stadtbüchereien düsseldorf

„Stadtbüchereien Düsseldorf“ steht für alle Zweigstellen, „Düsseldorf“ für keinen Ort. Für beide gelten weder die dritte Serien-Regel noch die Ort-Eindeutigkeit in den fünf Plätzen. Zwei verschiedene Lesungen der Stadtbüchereien sind keine Serie. Zwei Events mit dem Ort „Düsseldorf“ dürfen beide in den Plätzen stehen. Eine Reihe mit gleichem Titel fällt weiter über die Titel-Regel.

Ort und Titel werden immer über `norm()` verglichen.

Grenze, die dieser Plan stehen lässt: tägliche Führungen mit wechselndem Titel und wechselndem Treffpunkt fallen durch alle drei Regeln. Sie bleiben Stufe 2, bis ein Beleg zeigt, dass das oft den Tipp belegt. Dann eigene Regel, nicht vorher.

Dieselbe Serie und derselbe `norm(ort)` kommen in den fünf Plätzen eines Tages nur einmal vor, Sammelorte ausgenommen. In einem Zeitraum (Abschnitt 7) nur einmal im ganzen Zeitraum, wieder mit Ausnahme der Sammelorte.

## 7. Fokustag und Zeiträume

Die Startseite kennt einzelne Tage und Zeiträume (`web/lib/datum.ts`, Zeilen 109–144): heute, morgen, ein gewähltes Datum, den Zeitraum Wochenende (`?datum=wochenende`), Woche, 30 Tage und 60 Tage. Die Wochenend-Box auf jeder Startseite ist etwas anderes: `wochenendProgramm()` in Abschnitt 9, drei Tageslisten für Freitag, Samstag und Sonntag.

Die Kandidaten für die fünf Plätze kommen aus `filtern(..., { mitLanglaeufern: true })`, in der Tagesansicht und in der Zeitraumansicht. Sonst fehlt eine schon laufende Ausstellung, und der Fokustag hätte keinen Tag, an dem er greift. Zahlen, Kategoriezeilen, die Abend-Box und die Menge für „Beliebt“ bleiben beim bisherigen `filtern` ohne `mitLanglaeufern`.

**Ein Tag** (`von === bis`, also heute, morgen und ein Datum aus der Leiste). Jedes Event mit `datum_bis` nach `datum` hat einen festen Fokustag, nicht nur ein Langläufer: `datum + hash(id) % Laufzeit`, Laufzeit in Tagen von `datum` bis `datum_bis` einschließlich. Das gilt für Tipp und „Fund“ gleich. `nightlife` und `food` sind nie Langläufer (`datum.ts`, Zeilen 80–85), auch über 30 Tage. Sie stehen jeden Tag in der Tagesliste, Tipp und „Fund“ aber nur am Fokustag. Eine Party-Reihe über 30 Tage in `nightlife` ist damit nicht an jedem Tag der Tipp. Liegt der Fokustag vor heute, ist er verstrichen. Dieselbe Rechnung heute und morgen ergibt denselben Tag, solange `datum`, `datum_bis` und `id` gleich bleiben. Ein Speicher für die letzten sieben Tage entfällt.

Ändert ein Scraper `datum_bis`, oder wechselt die Bündelung die ID, weil ein Termin abgesagt wird, verschiebt sich der Fokustag. Das wird hingenommen.

In der Tagesansicht verliert ein mehrtägiges Event an den anderen Tagen einen großen Pick gegen ein eintägiges Event derselben oder einer höheren Stufe mit Bild. So belegt weder eine Ausstellung über 20 Tage noch eine lange Party-Reihe an jedem Tag den ersten Pick. Eine Ausstellung, die vor heute begann, ist nur an ihrem Fokustag Tipp-Kandidat.

**Ein Zeitraum** (Zeitraum Wochenende auf der Startseite, Woche, 30 Tage, 60 Tage). Dieselbe Platzlogik über alle Events des Zeitraums, einschließlich mehrtägiger Events. Der Fokustag gilt hier nicht. Eine Ausstellung darf in der Woche Tipp sein, auch wenn ihr Fokustag nicht in diese Woche fällt. Dieselbe Serie und derselbe Ort kommen nur einmal im ganzen Zeitraum vor, Sammelorte ausgenommen. Die Wochenend-Box folgt dieser Regel nicht.

## 8. Flaggen

Die Wahrheitswerte bleiben. Die Website löscht sie nicht. `pipeline/publisher.py` (Zeilen 279–290) sortiert Instagram-Posts nach denselben Spalten; ein Löschlauf würde die Reihenfolge der noch nicht geposteten Events ändern.

- **Tipp.** Keine neue Spalte. Die Flagge ändert die Stufe nicht. Bei einem Event mit höchstens 7 Tagen Laufzeit gilt sie an jedem Tag der Laufzeit und schlägt den Fokustag. Liegt `datum_bis` mehr als 7 Tage nach `datum`, gilt sie nur am Fokustag. Das trifft Langläufer und ebenso `nightlife` und `food`. Eine markierte Ausstellung über 90 Tage ist damit nicht 90 Tage lang der Tipp. Gelten an einem Tag mehrere Tipp-Flaggen, entscheidet die höhere Stufe, dann `beliebtheit()` ohne Flaggen-Punkte, dann der Hash (Abschnitt 9).
- **Highlight.** Neue Spalte `highlight_gesetzt_am`. Gilt sieben Tage ab diesem Datum, gerechnet in `Europe/Berlin` wie `heuteBerlin()`. Danach ignoriert die Website die Flagge. Der Wahrheitswert in der Datenbank bleibt.
- **Top.** Neue Spalte `top_gesetzt_am`. Gilt bis zum Ende des Monats, in dem gesetzt wurde, ebenfalls in `Europe/Berlin`.

Das Dashboard schreibt den Zeitpunkt beim Einschalten und leert ihn beim Ausschalten. Die Migration liegt als SQL-Datei im Repo und setzt für schon gesetzte Highlight- und Top-Flaggen `highlight_gesetzt_am` bzw. `top_gesetzt_am` auf `now()`. Sonst verschwänden sie beim Deploy. Bis die Migration ausgeführt ist, lädt die Website über die vorhandene Spalten-Variante in `daten.ts` ohne die neuen Spalten, und eine Highlight- oder Top-Flagge ohne Zeitpunkt gilt nicht.

„Von der Redaktion“ erscheint nur, wenn der gezeigte Tipp die Tipp-Flagge trägt und sie an diesem Tag gilt.

## 9. Die fünf Plätze

Ein Sortierschlüssel für alle Plätze:

a) Stamm ist draußen, außer ein Stamm-Event mit geltender Tipp-Flagge für den Tipp selbst.
b) Mit Bild vor ohne Bild. „Beste Stufe 3, dann 2, dann 1“ gilt innerhalb der Events mit Bild. Events ohne Bild kommen nur zum Zug, wenn es für den Platz keinen Kandidaten mit Bild gibt.
c) Höhere Stufe.
d) Gleichstand nach dem bisherigen `beliebtheit()`, ohne die Punkte für die drei Flaggen, weil die Flaggen schon in die Stufe eingehen. Der Bild-Anteil ist innerhalb der Gruppe mit Bild und innerhalb der Gruppe ohne Bild konstant.
e) Zuletzt der Hash. Er bleibt der letzte Gleichstand, wie heute.

1. **Tipp.** Zuerst geltende Tipp-Flaggen mit Bild, darunter die höhere Stufe, dann `beliebtheit()` ohne Flaggen-Punkte, dann der Hash. Gibt es keine Flagge mit Bild, die beste Stufe 3 mit Bild, dann 2, dann 1. Gibt es überhaupt kein Event mit Bild, erst dann eine geltende Flagge ohne Bild, danach die Heuristik ohne Bild. Nie Stufe 0, außer mit geltender Tipp-Flagge. Ein wöchentliches Yoga mit geltender Flagge ist damit Tipp und nie ein Pick. Eine Flagge ohne Bild verliert gegen ein Stufe-3-Event mit Bild. In der Tagesansicht steht jedes Event mit `datum_bis` nach `datum` hier nur an seinem Fokustag, außer die Tipp-Flagge schlägt ihn bei höchstens 7 Tagen Laufzeit. Im Zeitraum gilt der Fokustag nicht (Abschnitt 7).
2. **Pick, groß.** Andere Kategorie als der Tipp, Stufe 3 oder 2. Gibt es keinen Tipp, entfällt die Kategorie-Regel. In der Tagesansicht verliert ein mehrtägiges Event, dessen Fokustag nicht dieser Tag ist, gegen ein eintägiges Event mit Bild derselben oder einer höheren Stufe.
3. **Pick, groß.** Anderer Stadtteil als die beiden ersten, Stufe 3 oder 2. Ein Event ohne Stadtteil ist für diesen Platz nicht wählbar. Bleibt der Platz dadurch leer, rückt die nächste Stufe ohne die Stadtteil-Regel nach. Dieselbe Fokustag-Regel wie bei Platz 2, nur in der Tagesansicht.
4. **Pick, Szene.** Genau eine Karte, deren Grundstufe Szene ist: Jam-Session, Open Stage, Open Mic oder Karaoke. Eine Serie mit dieser Grundstufe, etwa eine wöchentliche Jam-Session, darf hier stehen, höchstens einmal am Tag. Eine Serie mit anderer Grundstufe, deren Stufe nur über Abschnitt 3, Schritt 3 auf 1 gedeckelt ist, ist nicht wählbar. Eine täglich laufende Führung fällt damit nicht auf Platz 4. Ist kein Szene-Event da, rückt Stufe 2 oder 3 nach.
5. **Pick, Fund.** In der Tagesansicht ein eintägiges Event der Stufe 2 oder ein mehrtägiges Event an seinem Fokustag, das in den anderen Plätzen nicht vorkommt. Im Zeitraum entfällt der Fokustag.

Ist ein Platz leer, rückt die nächste Stufe nach, nie Stamm. Gibt es keinen Tipp, entfällt er. Das Raster `startraster` (`web/app/globals.css`, Zeilen 442–443) hat ab 1200 Pixel zwei Spalten. Ohne Tipp setzt die Seite die Klasse `startraster--ohne-tipp` mit einer Spalte. Sonst bliebe die erste Spalte leer, und die Picks lägen nur in der schmaleren zweiten.

**Beliebt.** Die Menge bleibt das bisherige `filtern` ohne Langläufer an Folgetagen. In der Tagesansicht steht ein mehrtägiges Event dort nur an seinem Fokustag, wie bei Tipp und „Fund“. Eine Party-Reihe über 30 Tage in `nightlife` steht damit nicht an jedem Tag unter „Beliebt“. Ein Langläufer, etwa eine Ausstellung, liegt in dieser Menge nur an seinem Starttag und bleibt nur, wenn dieser Tag auch der Fokustag ist. An den anderen Tagen kann dieselbe Ausstellung Tipp sein, weil die fünf Plätze Langläufer mitlesen. Die Reihenfolge ist der Sortierschlüssel a) bis e), Stamm bleibt draußen. Reichen Stufe 3, 2 und danach 1 nicht für fünf Einträge, wird die Liste kürzer. `auffuellen` aus der Woche hält die Fokustag-Regel für den gezeigten Tag ein. Im Zeitraum gilt der Fokustag nicht.

`highlights()` liest denselben Sortierschlüssel. Die Kandidaten nehmen mehrtägige Events mit. Highlight der Woche ist die geltende Highlight-Flagge, sonst das beste Zugpferd mit Bild der nächsten sieben Tage. Top des Monats ist die geltende Top-Flagge, sonst das beste Zugpferd mit Bild der nächsten 30 Tage. Gibt es darin kein Zugpferd mit Bild, die beste Stufe 2 mit Bild, wie die heutige Heuristik. Der jeweils andere Platz wird nicht doppelt belegt. Sieben Tage und Monatsende rechnen in `Europe/Berlin`, wie `heuteBerlin()`. Das ist ein Zeitraum: der Fokustag gilt dort nicht.

Die Wochenend-Box ist `wochenendProgramm()` (`web/lib/ableitungen.ts`, Zeilen 282–297), nicht der Zeitraum `?datum=wochenende`. Freitag, Samstag und Sonntag bleiben je ein Tag, mit den heutigen Anzahlen 3, 4 und 3. Die Kandidaten kommen aus `filtern(..., { mitLanglaeufern: true })`, danach gilt der Fokustag wie in der Tagesansicht. Heute lädt die Funktion ohne `mitLanglaeufern` (Zeile 292). Das reicht nicht, weil ein Langläufer mit Uhrzeit sonst nur an seinem Starttag in der Box stünde. Stamm bleibt draußen. Die Auswahl je Tag folgt dem Sortierschlüssel a) bis e) und der heutigen Kategorie-Mischung: je Kategorie einer, dann der Rest. Der Uhrzeit-Filter bleibt, Ausstellungen ohne Uhrzeit fallen damit heraus. `benutzt` gilt weiter über alle drei Tage, damit dasselbe Event nicht an zwei Tagen der Box steht. Eine Party über 30 Tage mit Uhrzeit steht in der Box nur an ihrem Fokustag, und nur wenn dieser Freitag, Samstag oder Sonntag ist. Eine Ausstellung mit Uhrzeit, deren Start vor dem Wochenende liegt und deren Fokustag ein Samstag ist, steht am Samstag in der Box.

## 10. Unverändert

Kategoriezeilen, Kalender, Stadtteilseiten und die Suche lesen diese Stufe nicht. Gebündelte Termine (`web/lib/termine.ts`, Zeilen 92–121) bleiben davor: eine Flagge gilt, wenn ein Termin der Gruppe sie hat, die Plätze sehen den gebündelten Eintrag. Abgesagte Events bleiben im Kalender markiert sichtbar und fehlen auf der Startseite.

Kein Modell, keine Klickdaten, keine tägliche Redaktionsrunde.

## 11. Umsetzung, erst nach Freigabe

1. `breite()` und die beiden Listen in `web/lib/ableitungen.ts`, Tests aus Abschnitt 12. Serien zählen gebündelte Einträge mit unterschiedlichem `datum`. Ein Event mit `datum_bis` zählt als ein Eintrag.
2. Tipp, Picks, die Wochenend-Box, `highlights()` und die Zeitraum-Ansicht auf die Plätze umstellen. Die Wochenend-Box behält Tageslisten, Uhrzeit-Filter und `benutzt`. Die Kandidaten dieser Flächen kommen aus `filtern(..., { mitLanglaeufern: true })`. „Beliebt“ bleibt beim bisherigen `filtern` und lässt in der Tagesansicht ein mehrtägiges Event nur am Fokustag zu. Zahlen, Kategoriezeilen und die Abend-Box bleiben beim bisherigen `filtern` ohne diese Einschränkung. Abgesagte vom Tipp ausschließen. Ohne Tipp erhält `startraster` die Klasse `startraster--ohne-tipp`.
3. SQL für `highlight_gesetzt_am` und `top_gesetzt_am`, inklusive Nachtrag `now()` für schon gesetzte Flaggen. Dashboard setzt und leert sie. Die Website ignoriert abgelaufene Flaggen und lädt die Spalten über die bestehende Variante.

## 12. Tests

- Führung „auf Französisch“ → Stufe 0. „Auf Deutsch und Englisch“ und „Führung in Englisch und Deutsch“ → nicht abgestuft.
- „In englischer Sprache“ bei einer Führung → 0. „Audioguide auf Englisch“ im selben Satz → nicht abgestuft. Steht „auf Englisch“ in einem anderen Satz als „Audioguide“, gilt die Abstufung.
- „Sprachcafé Englisch“ → 0. „Python Meetup Düsseldorf“ → 0.
- „Reisesprachkurs – Koreanisch“ im NRW-Forum → 0. „Einsteigerkurs Bouldern“ → 0. „Diskurs über …“ → nicht 0. „Exkursion …“ → nicht 0.
- „Move it!“ → 0. „ENGLISH COMEDY NIGHT“, „Wanderung im Grafenberger Wald“ und „Speed tasting“ → nicht 0. „AfterWorkOut“ ohne Treffer im Titel und ohne Regelmäßigkeit in der Beschreibung → Stufe nach den übrigen Regeln.
- „French Jazz Night“ in `musik` → nicht abgestuft. Spanischer Film mit OmU → 2. Bandname mit „Language“ → nicht abgestuft.
- Ort „Tonhalle“ und „Tonhalle Düsseldorf“ → 3. „Denkmal vor dem Restaurant Tonhalle …“, „Tonhalle Terrace“ und „Capitol Theater - Club Saal“ → nicht 3. Dieselbe Prüfung je Listeneintrag, Fehltreffer aus Abschnitt 4.
- Fünf verschiedene Tonhalle-Konzerte in 14 Tagen bleiben 3.
- Rheinkirmes über 10 Tage → 3. Fortuna-Heimspiel → 3. Fortuna auswärts → nicht 3.
- Premiere im Kunstpalast → 3. Workshop oder Foyer im Titel dort → höchstens 2. „Opernhaus Düsseldorf Foyer“ → höchstens 2.
- Wöchentliches Yoga → 0, auch bei „Yoga“ und „jeden Mittwoch“ mit großem Anfang. Jazz-Jam → 1. Wöchentliche Jam-Session → Platz 4, nur einmal am Tag. Tägliche Führung (Serie, Stufe 1) → nicht Platz 4, höchstens Stufe 1.
- Führung Montag, Dienstag, Mittwoch → alle drei Termine höchstens Stufe 1. Wöchentliche Reihe mit drei Terminen über 14 Tage, Grenzen eingeschlossen → Serie. Zwei Termine im Abstand von 14 Tagen → keine Serie.
- Ausstellung über 20 Tage → keine Serie, Stufe 2. Tipp und Fund nur am Fokustag. Dieselbe Funktion heute und morgen gerechnet liefert denselben Fokustag.
- Ausstellung, die vor heute begann → an ihrem Fokustag Tipp-Kandidat, an anderen Tagen nicht.
- Party-Reihe über 30 Tage in `nightlife` → nicht Langläufer, Tipp und Fund nur am Fokustag.
- Zwei verschiedene Lesungen mit Ort „Stadtbüchereien Düsseldorf“ → keine Serie. Zwei Events mit Ort „Düsseldorf“ dürfen beide in den Plätzen stehen.
- Event ohne Bild auf Stufe 2 gegen Event mit Bild auf Stufe 1: für Tipp und Picks gewinnt das mit Bild, solange eines existiert.
- Zwei Events derselben Stufe mit Bild: das mit höherem `beliebtheit()` ohne Flaggen-Punkte gewinnt, der Hash erst danach.
- Abgesagtes Event mit Tipp-Flagge → kein Platz.
- Wöchentliches Yoga mit geltender Tipp-Flagge → Tipp, nie Pick.
- Geltende Tipp-Flagge ohne Bild gegen Stufe 3 mit Bild → das mit Bild.
- Zwei geltende Tipp-Flaggen am selben Tag → die höhere Stufe, dann `beliebtheit()` ohne Flaggen-Punkte, dann der Hash.
- Tag, an dem nur Stamm-Events ein Bild haben → kein Tipp, Klasse `startraster--ohne-tipp` gesetzt.
- Platz 2 an einem Tag ohne Tipp → die Kategorie-Regel entfällt.
- Zeitraum Wochenende auf der Startseite: derselbe Ort und dieselbe Serie nur einmal, Fokustag gilt nicht.
- Zeitraum „Woche“: eine Ausstellung darf Tipp sein, auch wenn ihr Fokustag nicht in der Woche liegt.
- Wochenend-Box: eine Party über 30 Tage mit Uhrzeit steht nur an ihrem Fokustag in der Box, und nur wenn dieser Freitag, Samstag oder Sonntag ist. Ohne Uhrzeit fehlt sie. Eine Ausstellung mit Uhrzeit, Start vor dem Wochenende, Fokustag Samstag → steht am Samstag in der Box.
- „Beliebt“ in der Tagesansicht: eine Party-Reihe über 30 Tage in `nightlife` steht nur am Fokustag in der Liste.
- Highlight-Flagge älter als sieben Tage → auf der Website ignoriert, Wahrheitswert unverändert.

## 13. Eingearbeitet aus der Prüfung

Übernommen: Bild vor Stufe, Zugpferd über Orts- und Titellisten statt `quelle_name`, eigenes Sprachmuster, Fokustag statt Sieben-Tage-Speicher, Platzregeln für Zeiträume, Serie vor Kategorie, Flaggen beim Lesen ignorieren statt löschen, Abgesagte ohne Platz, leerer Tipp ohne Lücke, „Beliebt“ mit Stufe 1 aufgefüllt und sonst kürzer, Langläufer höchstens 2.

Bewusst anders als in der ersten Prüfung:

- Ort plus Kategorie zählt nicht als Serie, wenn der Ort auf `ZUGPFERD_ORTE` steht. Sonst würde jedes Tonhalle-Konzert Stufe 1. Die zweite Prüfung hat das bestätigt.
- `ist_wiederkehrend` bleibt außen vor, aus dem Grund in Abschnitt 6. Die zweite Prüfung hat das bestätigt.
- Die erste Fassung ohne `tipp_gesetzt_am` ließ eine Tipp-Flagge über die ganze Laufzeit gelten. Das ist mit Abschnitt 1 und 7 nicht vereinbar (M4). Variante (a), die Flagge nur am Setz-Tag und am Folgetag, ist es auch nicht: wer ein Konzert am Mittwoch für den Samstag markiert, verliert die Flagge vor dem Termin. Es gilt Variante (b). Keine Spalte `tipp_gesetzt_am`. Bis 7 Tage Laufzeit gilt die Flagge an jedem Tag und schlägt den Fokustag. Darüber hinaus nur am Fokustag. Die dritte Prüfung dehnt diesen Fokustag auf jedes Event mit `datum_bis` nach `datum` aus, nicht nur auf Langläufer.

Eingearbeitet aus der zweiten Prüfung:

- K1. Serien zählen gebündelte Einträge mit unterschiedlichem `datum`. Ein Event mit `datum_bis` ist ein Eintrag. Eine Ausstellung über 20 Tage ist keine Serie (Abschnitt 6, 3 und 12).
- K2. Die fünf Plätze, das Wochenende und `highlights()` lesen Langläufer über `mitLanglaeufern: true`. Zahlen, Kategoriezeilen, Abend-Box und die Menge für „Beliebt“ bleiben beim bisherigen `filtern` (Abschnitt 7, 9 und 11).
- M1. `ZUGPFERD_TITEL` ist von der Langläufer-Obergrenze ausgenommen. Die Rheinkirmes bleibt 3, eine Ausstellung am Zugpferd-Ort bleibt 2.
- M2. Abschnitt 3 ist eine Rechenregel. Serie und Langläufer sind Obergrenzen. Beispiele: Premiere im Kunstpalast 3, Ausstellung dort 2, Jam-Serie 1, Rheinkirmes 3.
- M3. Ortsliste ausgeschrieben, Treffer nur am Anfang von `norm(ort)`, Fehltreffer je Eintrag in Abschnitt 4 und 12.
- M4. Variante (b), wie oben. Mehrere Tipp-Flaggen: höhere Stufe, dann Hash.
- G1. Ausnahme `deutsch und|und deutsch|zweisprachig|bilingual`, Muster „in englischer Sprache“, Beschreibung nur bei Führung, Kurs und Treffen, ohne Audioguide, Untertitel und Übersetzung.
- G2. Nicht jedes Format am Zugpferd-Ort wird Stufe 3. Kategorie `community` sowie Workshop, Atelier und Foyer bleiben höchstens 2. Zusätzlich ist „Tonhalle Terrace“ kein Treffer, weil hinter dem Eintrag ein weiteres Ortswort steht. Die zweite Prüfung ließ diese Bar sonst auf 3, obwohl der Ort mit „tonhalle“ beginnt.
- G3. Verschobener Fokustag bei geändertem `datum_bis` oder gewechselter ID wird hingenommen. Die Migration trägt `now()` für schon gesetzte Highlight- und Top-Flaggen nach. Ohne Tipp setzt die Seite `startraster--ohne-tipp`.

Eingearbeitet aus der dritten Prüfung:

- M1. Ein Sortierschlüssel für alle Plätze: Stamm draußen, mit Bild vor ohne Bild, höhere Stufe, dann `beliebtheit()` ohne Flaggen-Punkte, zuletzt der Hash. „Stufe 3, dann 2, dann 1“ gilt nur unter den Events mit Bild. Ohne Bild nur, wenn der Platz sonst leer bliebe (Abschnitt 9 und 12).
- M2. Platz 1 sagt „Nie Stufe 0, außer mit geltender Tipp-Flagge“. Yoga mit Flagge ist Tipp und nie Pick.
- M3. Das Stamm-Muster nennt Sprachcafé, Sprachtreff, Tandem, Language Exchange, Conversation Club, Stammtisch und `\bkurse?\b`. „Sprachcafé Englisch“ wird 0, „Exkursion“ nicht.
- M4. Innerhalb einer Stufe entscheidet zuerst `beliebtheit()` ohne die Flaggen-Punkte. Der Hash bleibt nur der letzte Gleichstand, wie heute.
- M5. `SAMMELORTE` („düsseldorf“, „stadtbüchereien düsseldorf“) nehmen an Serien-Regel 3 und an der Ort-Eindeutigkeit nicht teil. Die Titel-Regel bleibt.
- G1. Der Fokustag gilt für jedes Event mit `datum_bis` nach `datum`, für Tipp und „Fund“ gleich, also auch für `nightlife` und `food`. Die Tipp-Flagge schlägt ihn nur bis 7 Tage Laufzeit. Eine Party-Reihe über 30 Tage ist nur am Fokustag Tipp.
- G2. Reihenfolge des heutigen Codes: Flagge mit Bild, dann Heuristik mit Bild, dann Flagge ohne Bild, dann Heuristik ohne Bild. Eine Flagge ohne Bild verliert gegen Stufe 3 mit Bild.
- G3. „Workshop“, „Atelier“ und „Foyer“ zählen im Titel und im Ort. „Opernhaus Düsseldorf Foyer“ bleibt höchstens 2.
- G4. Kein Abstufen, wenn Audioguide, Untertitel, Übersetzung oder „übersetzt“ im selben Satz steht, bis zum nächsten `.`, `!` oder `?`.
- G5. Ohne Tipp entfällt an Platz 2 die Kategorie-Regel. Ein Event ohne Stadtteil ist für Platz 3 nicht wählbar; bleibt der Platz leer, entfällt die Stadtteil-Regel. `highlights()` nimmt ohne Zugpferd mit Bild die beste Stufe 2 mit Bild. Sieben Tage und Monatsende rechnen in `Europe/Berlin`.

Eingearbeitet aus der vierten Prüfung:

- M1. Der Titel wird immer auf das Stamm-Muster geprüft. In der Beschreibung zählt ein Treffer nur im selben Satz wie ein Wort für Regelmäßigkeit. „Move it!“ wird 0. „ENGLISH COMEDY NIGHT“, „Wanderung im Grafenberger Wald“ und „Speed tasting“ nicht. „AfterWorkOut“ ohne Regelmäßigkeit folgt den übrigen Regeln.
- M2. „Zeitraum Wochenende“ auf der Startseite (`?datum=wochenende`) ist kein Fokustag. Die Wochenend-Box (`wochenendProgramm()`) bleibt drei Tageslisten mit Uhrzeit-Filter und `benutzt`. Dort gilt der Fokustag. Eine Party über 30 Tage mit Uhrzeit steht in der Box nur an ihrem Fokustag, wenn der in Fr–So liegt.
- G1. Nach einem Zugpferd-Eintrag zählt das erste Wort, Bindestriche und Leerzeichen übersprungen. „Capitol Theater - Club Saal“ ist kein Treffer.
- G2. Im Stamm-Muster steht `\bmeetup\b` statt `tech-meetup`. „Python Meetup Düsseldorf“ wird 0.
- G3. Der Sortierschlüssel in Abschnitt 9 ist a) bis e). Die Plätze bleiben 1 bis 5.
- G4. Fokustag bei Platz 1, 2, 3 und 5 nur in der Tagesansicht. Im Zeitraum „Woche“ darf eine Ausstellung Tipp sein, auch wenn ihr Fokustag nicht in der Woche liegt.

Eingearbeitet aus der fünften Prüfung:

- M1. Im Stamm-Muster steht `(?<!dis)kurse?\b` statt `\bkurse?\b`. Sprachkurs, Grundkurs und Einsteigerkurs werden 0, auch am NRW-Forum. „Diskurs“ und „Exkursion“ nicht.
- G1. Die Wochenend-Box lädt mit `mitLanglaeufern: true`, lässt Stamm draußen und sortiert je Tag nach a) bis e) mit der Kategorie-Mischung. Eine Ausstellung mit Uhrzeit steht an ihrem Fokustag in der Box, auch wenn der Start davor liegt.
- G2. „Beliebt“ ist nicht ausgenommen. In der Tagesansicht steht ein mehrtägiges Event dort nur am Fokustag. Die Menge bleibt das bisherige `filtern`, deshalb liegt eine Ausstellung darin nur am Starttag und nur, wenn der auch der Fokustag ist. Kategoriezeilen zeigen die Party-Reihe weiter an jedem Tag.

Eingearbeitet aus der eigenen Prüfung:

- Stamm-Muster und Sprachmuster gelten mit Flag `i`. Sonst treffen „Yoga“, „jeden Mittwoch“ und „Python Meetup Düsseldorf“ nicht, und die Tests in Abschnitt 12 fallen um.
- Das Serienfenster sollte nicht „ab heute“ gelten. Die erste Formulierung „ab dem Datum jedes einzelnen Events“ ist danach korrigiert, siehe unten.
- Platz 4 sollte eine Jam-Serie aufnehmen. Die erste Formulierung „jede Serie der Stufe 1“ ist danach korrigiert, siehe unten.

Korrigiert nach der Nachprüfung der eigenen Änderungen. Die Groß- und Kleinschreibung mit Flag `i` bleibt.

- Das Serienfenster hängt nicht am einzelnen Termin. Eine Gruppe ist Serie, wenn irgendein Fenster von `datum` bis `datum + 14`, Grenzen eingeschlossen, mindestens drei Einträge mit unterschiedlichem Datum hat. Dann gilt das für jeden Termin der Gruppe. Sonst wäre dieselbe Führung am Montag Stufe 1 und am Dienstag Stufe 2.
- Platz 4 nimmt nur Events, deren Grundstufe Szene ist, auch als Serie. Eine täglich laufende Führung, deren Stufe nur über Schritt 3 auf 1 gedeckelt ist, ist dort nicht wählbar.

## 14. Nachtrag nach der Cursor-Prüfung der Umsetzung (13.11.2026)

- Platz 3: Bleibt der Platz wegen des Stadtteils leer, rückt Stufe 1 ohne Stadtteil-Regel nach. Ein weiteres Event der Stufe 2 oder 3 aus einem schon belegten Stadtteil kommt nicht vorher.
- „Auswärts“, „Public Viewing“ und „Fanshop“ im Titel oder Ort heben weder über `ZUGPFERD_ORTE` noch über das Heimspiel auf 3. „Public Viewing“ in der Merkur Spiel-Arena bleibt 2.
- Stamm-Muster: `repair[-\s]?caf[eé]` und `speed[-\s]?dating` statt `repair-?café` und `speed-?dating`. „Repair Café“ und „Speed Dating“ mit Leerzeichen werden 0.
- Tipp-Flagge (Abschnitt 8): Die Laufzeit zählt einschließlich, wie beim Fokustag. Bis 7 Tage (z. B. 1.–7.) gilt die Flagge an jedem Tag, ab 8 Tagen (z. B. 1.–8.) nur am Fokustag. Entscheidung des Auftraggebers vom 13.11.2026; der Satz „mehr als 7 Tage nach `datum`“ ist damit überholt.
- Nach der zweiten Cursor-Prüfung: Stamm-Muster `repair[-\s]?caf[eé]s?(?![a-zäöüé])` und `\bspeed[-\s]?dating`, damit „Repair Cafeteria“ und „Highspeed Dating“ nicht 0 werden. Heimspiel-Ausschluss `auswärts|public[- ]viewing|fan[-\s]?shop`, damit auch „Public-Viewing“ und „Fan Shop“ greifen.
- Nach der dritten Cursor-Prüfung: Repair-Muster `repair[-\s]?caf[eé]s?(?!teria|téria)`, damit „Repair Caféabend“ wieder 0 ist und nur „Cafeteria“ draußen bleibt. Heimspiel-Ausschluss mit linker Grenze und beliebig vielen Trennern: `(?<![a-zäöüé])auswärts|(?<![a-zäöüé])public[-\s]*viewing|(?<![a-zäöüé])fan[-\s]*shop`. `\bspeed[-\s]?dating` bleibt rechts offen: „Speed-Datingabend“ ist Speed-Dating und soll 0 sein.
- Nach der vierten Cursor-Prüfung: Repair-Muster `repair[-\s]?caf[eé]s?(?![-\s]*t[eé]ria|taria)` (auch „Cafetaria“, „Cafe-teria“ draußen). Heimspiel-Ausschluss mit rechter Grenze bei `viewing` und `shop` („Fan Shopping“ trifft nicht, „Fortuna-Fanshop“ schon).
