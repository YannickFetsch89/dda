# Plan: Eigene Seiten für Veranstaltungsorte („Locations“)

Stand: **19.11.2026 · elfte Fassung, FREIGEGEBEN vom Auftraggeber am 19.11.2026.** Nach 8 Cursor-Runden und 2 eigenen Prüfungen. Umgesetzt wird wörtlich nach Abschnitt 3 und 4, in der Reihenfolge der Schritte. Die Umsetzung startet erst auf ausdrückliche Anweisung des Auftraggebers. Erstellt von Claude auf Wunsch des Auftraggebers, Vorbild rausgegangen.de/locations/… Erste Fassung: 18.11.2026.

Es gelten die üblichen Regeln:
- Deploy nur nach OK.
- SQL liegt als Datei in `database/`, der Auftraggeber führt sie aus.
- Keine neue Bibliothek ohne Rückfrage. Texte auf Deutsch.
- Der Browser kontaktiert keine Dritten: Bilder über den eigenen Server, Karte selbst gehostet.

## Änderungsprotokoll 19.11.2026, elfte Fassung (Cursor-Prüfung der zehnten)

Cursor hat alle vier Änderungen der zehnten Fassung als behoben bestätigt und den Plan als freigabereif eingeschätzt. Ein geringer Befund ist eingearbeitet:

1. **Die Kontrolle auf „nicht im“-Schreibweisen** nutzt `nicht_im_ort` selbst, als lokale Lese-Prüfung vor Deploy-Punkt 2. Es ist keine SQL-Suche nach der Zeichenfolge „nicht im“, die fälschlich „Pitcher, nicht im Freien“ melden würde (3.4, Abschnitt 4).

## Änderungsprotokoll 19.11.2026, zehnte Fassung (Prüfung der neunten durch Claude)

Die neunte Fassung ist am Code und mit einer Lese-Abfrage in der Datenbank geprüft. Gefunden und eingearbeitet:

1. **Die Schreibweisen-Liste der Clubs ändert sich bei jedem Lauf** (hoch):
   - `scores_neu` läuft bei jedem Pipeline-Lauf (`main.py`, nach dem Speichern) und schreibt `extras.club.event_orte` neu, aus den Events der letzten 180 Tage (`kalender_laden` in `scraper/orte/clubs_profil.py`). `profile_erstellen` und `neu_pruefen` tun dasselbe.
   - Die Regel der neunten Fassung „verschwindet eine Schreibweise, wird die `ort_id` geleert“ hätte deshalb täglich die Zuordnung alter Events gelöscht, sobald eine Schreibweise aus dem 180-Tage-Fenster fällt. Die Kennzahl wäre dauernd gestiegen.
   - **Jetzt:**
     - `event_orte` wächst nur: Neue Schreibweisen kommen dazu, gespeicherte bleiben.
     - `clubs_profil` leert nie eine `ort_id`.
     - Entfernt wird nur ausdrücklich (3.4).
2. **Eine bewusste Lösung würde am selben Tag zurückgenommen** (hoch, neu gefunden):
   - Es gibt heute keine Ausschlussliste. Nimmt SQL „Theater an der Kö“ aus der Liste des Kö-Clubs, findet `event_orte()` es beim nächsten `scores_neu` im Kalender wieder und trägt es neu ein.
   - **Jetzt:** eine Ausschlussliste `EVENT_ORTE_AUSSCHLUSS` im Code (Club → Schreibweisen). `event_orte()` und `ort_zuordnen` beachten sie beide.
   - Sie kommt mit dem Pipeline-Code (Deploy-Punkt 2). Das Aufräum-SQL läuft danach (3.4, Abschnitt 4).
3. **„zakk – nicht im zakk“ steht nicht in `event_orte`** (mittel):
   - Die Lese-Abfrage zeigt beim zakk (`zakk-flingern`) 7 Schreibweisen ohne „nicht im zakk“. `event_orte()` schließt „nicht im …“ schon heute aus (`clubs_profil.py`, Regel mit den Ausnahmen „sondern“, „aber“, „dafür“).
   - Die Aussage früherer Fassungen beruhte auf einer Verwechslung der Kandidaten-CSV mit `event_orte`. Sie ist richtiggestellt.
   - Die Sicherung in `ort_zuordnen` nutzt **dieselbe Regel**, nicht „jeder Name mit ‚nicht im‘“. Sonst fiele „Pitcher, nicht im Freien“ weg, das zum Pitcher gehört.
   - Das SQL dazu ist nur noch eine Kontrollabfrage, die 0 erwartet (3.4).
4. **Zwei Kennzahlen statt einer:** `ort_id_ohne_treffer` und `ort_id_mehrdeutig` (3.4).

## Änderungsprotokoll 19.11.2026, neunte Fassung (Cursor-Prüfung der achten)

Cursor hat die achte Fassung als freigabereif eingeschätzt, mit zwei geringen Befunden. Beide sind eingearbeitet.

1. **Kennzahl über den ganzen Bestand:** `ort_id_ohne_treffer` liest einmal je Pipeline-Lauf alle Events mit gesetzter `ort_id`, seitenweise, nicht nur die Events dieses Scrapers. Mehrdeutig zählt mit. `clubs_profil` leert beim Entfernen einer Schreibweise die `ort_id` derselben Events, analog zur SQL-Regel (3.4). *In der zehnten Fassung ersetzt: `event_orte` wächst nur, `clubs_profil` leert nie eine `ort_id`.*
2. **Nachziehen nur bei der Umbenennung:** Der Satz gilt nur noch dort, weil die UUID bleibt. Beim Löschen und Abschalten bleibt das Umhängen Pflicht (3.3 Punkt 4).

Ältere Protokolle beschreiben den Stand ihrer Fassung. **Maßgeblich ist immer Abschnitt 3 und 4.**

## Änderungsprotokoll 19.11.2026, achte Fassung (Cursor-Prüfung der siebten)

Cursor hat die Weiterleitung über `ziel_ort_id` bestätigt, einschließlich des Rückfalls auf `/orte`. Von den 12 alten Punkten sind 10 behoben und 2 teilweise. Dazu kamen 5 neue Befunde. Alle sind am Code nachgeprüft und eingearbeitet.

1. **Ältere Weiterleitungen beim Zusammenlegen oder Abschalten:**
   - Bevor eine Zeile gelöscht oder abgeschaltet wird, werden alle Einträge mit `ziel_ort_id` = alte Zeile auf das neue Ziel umgehängt.
   - Der Trigger erzwingt das für jeden Typ, und es gibt einen Test (3.3 Punkt 8, 3.4).
2. **„nicht im zakk“ vor dem Pipeline-Deploy:**
   - Das SQL, das die Schreibweise aus `event_orte` nimmt, läuft schon in Deploy-Punkt 1, also bevor die Pipeline zuordnet.
   - Es leert in derselben Datei die `ort_id` dieser Events.
   - **Allgemeine Regel:** Wer eine Schreibweise aus `event_orte` nimmt, leert in derselben Datei die zugehörigen `ort_id`.
   - Ein Lauf, der eine gespeicherte `ort_id` ohne Treffer findet, meldet sie im Log und als Kennzahl, ändert aber nichts (3.4).
3. **`naechsteEvents` hat drei Aufrufe** (Club-Detailseite, Club-Übersicht, „Ähnliche Clubs“), nicht einen.
   - Die Detailseite nutzt nur noch die `ort_id`-Abfrage.
   - Die Karten behalten `naechsteEvents` und filtern Namen mit „nicht im“ aus (3.9). *In der zehnten Fassung ersetzt: keine eigene Filterlogik in TypeScript, die gespeicherte Liste ist bereinigt.*
4. **IndexNow bei einem Saal eines Guide-Hauses:** Gemeldet wird nur die Saalseite unter `/orte`. Die Guide-URL meldet IndexNow wie heute nicht, sie kommt über die Sitemap. Grund: Die Regeln für die kanonische Guide-URL gibt es nur in TypeScript, und eine zweite Fassung in Python wäre eine neue Fehlerquelle. Das weicht bewusst von Cursor ab. Ein Test hält zakk und Spielstätte auseinander (3.11).
5. **Proxy:**
   - Der Test nutzt den echten Slug `/orte/zakk-flingern`.
   - Schlägt die Abfrage der Zielzeile fehl, gilt „weiter“, nicht ein 308 auf `/orte`.
   - Die Zielabfrage liest den `slug` mit (3.10).

## Änderungsprotokoll 19.11.2026, siebte Fassung (Cursor-Prüfung der sechsten)

Cursor hat 4 der 11 neuen Regeln bestätigt und 7 „mit Änderung“ bewertet. Dazu kamen 8 Befunde und 4 Hinweise. Alle sind am Code nachgeprüft und stimmen.

1. **Eine Programmquelle für Guide-Seiten:**
   - **Heute:** Die Club-Seite zeigt „Nächste Events hier“ über `naechsteEvents` (`web/lib/clubs-daten.ts`): aus dem 60-Tage-Pool, Abgleich über `extras.club.event_orte`. Damit erschiene „zakk – nicht im zakk“ weiter im Programm.
   - **Jetzt:** Die Guide-Seiten von Clubs, Kneipen und Restaurants & Cafés lesen ihr Programm über dieselbe gecachte Abfrage wie die Ortsseite, also über `ort_id` des Hauses und der Kinder (3.2, 3.6, 3.9). `naechsteEvents` und der Pool entfallen dort.
   - Weihnachtsmärkte und Spielplätze behalten ihre eigene, geprüfte Logik (`web/lib/weihnachtsmaerkte.ts` mit `event_einschluss.csv`).
2. **`ort_id` beim Zusammenführen:**
   - Automatische Läufe (Pipeline, Nachtrag) schreiben **nie `NULL` über eine vorhandene `ort_id`**. Sie setzen oder ersetzen nur mit einem Treffer.
   - Beim Zusammenführen zählen die Ortsnamen aller beteiligten Events, zuerst der verbleibende.
   - Eine Zuordnung **lösen** geht nur über ausdrückliches SQL in derselben Datei, die `event_orte` ändert (3.4).
   - Die Bestandsabfragen laden `ort_id` (`_ABGLEICH_SPALTEN` in `database/client.py`, Spaltenliste in `pipeline/dubletten_sql.py`).
   - In `pipeline/rausgegangen_nachziehen.py` und überall ohne geladene Häuser bleibt der heutige Namensvergleich (3.4).
3. **Weiterleitungen zeigen auf eine ID, nicht auf einen Pfad:**
   - `ort_weiterleitungen.ziel_ort_id` statt eines festen Guide-Pfads. Der Proxy bildet die kanonische URL beim Aufruf mit denselben Regeln wie in 3.10.
   - Ist das Ziel nicht mehr sichtbar oder gelöscht, geht der 308 auf `/orte`.
   - Damit gibt es keinen 308 auf eine 404, keine veralteten Ziele nach einem Score-Wechsel und keine Ketten nach einer Umbenennung, denn die UUID bleibt.
   - Das ist robuster als die von Cursor vorgeschlagene tägliche Prüfung (3.3 Punkt 4).
4. **Slugs:**
   - Saal = **vorhandener** Haus-Slug + Saal, z. B. `zakk-flingern-halle`.
   - Neue Häuser bekommen die tatsächliche Ausgabe von `_slug_erzeugen`. Erfundene Beispiele sind entfernt (3.3 Punkt 7).
5. **Hinweis „Ort nicht gefunden“:** nur bei erfolgreich leerer Abfrage. Ein Fehler wird mit `cacheLife(KURZ)` gecacht und gilt nicht als „fehlt“ (3.10).
6. **IndexNow für Ortsseiten:**
   - Ein Schalter ist erst ab Deploy-Punkt 5 an.
   - Die Abfrage lädt `ort_id` und die Ortszeile. Bei einem Saal wird die Hausseite mitgemeldet.
   - Ein eigener Test prüft, welche URL aus einer `ort_id` entsteht (3.11, Abschnitt 4).
7. **`freischalten` in `scraper/orte/clubs_profil.py`** fängt einen Trigger-Fehler je Zeile ab, schreibt ihn ins Log und macht weiter. Im Probelauf wird der Saal mit `aktiv = true` angelegt (3.3 Punkt 8).
8. **Canonical und `noindex` auf `/orte?…`** werden von Hand gesetzt wie auf den Guide-Hubs, nicht über das `noindex`-Flag von `seitenMetadaten` (es streicht den Canonical). Es gibt keinen 301 auf eine Landingpage (3.8).
9. **Hinweise:**
   - Die Ortszuordnung wird in `main.py` der neue Schritt 1d, die Deduplizierung wird 1e.
   - Abschnitt 9 nennt jetzt die tatsächlichen Central-Säle.
   - „Tonhalle Terrace“ (2 Events) steht in der Saalliste.
   - Das Protokoll der sechsten Fassung, Punkt 6, ist durch 3.4 präzisiert: `ort_zuordnen` für Pipeline und Nachtrag, die Haus-Regel in `_ort_passt`.

## Änderungsprotokoll 19.11.2026, sechste Fassung (eigene Gesamtprüfung)

Der Auftraggeber hat eine weitere eigene Prüfung verlangt. Gefunden und eingearbeitet:

1. **Säle von Guide-Häusern:**
   - **Befund:** zakk ist eine Club-Guide-Seite, steht aber mit sechs Sälen in der Saalliste. Der Plan sagte bisher nur „Hausseite = `/orte/<slug>`“.
   - **Jetzt:** Bei einem Guide-Haus ist die Guide-Seite die Hausseite. Saalseiten unter `/orte/…` hängen per `parent_id` an der Guide-Zeile (3.6).
   - Der Trigger prüft Kinder deshalb bei jedem Elterntyp, nicht nur bei Spielstätten. Sonst würde das Löschen der zakk-Clubzeile die Säle verwaisen lassen (3.3 Punkt 8).
2. **Säle ohne eigene Seite haben keine `orte`-Zeile.** Eine aktive Zeile hieße sonst 200 im Proxy, also eine Seite ohne Freigabe. Der Saal-Filter der Hausseite arbeitet über die Saalliste und den Ortsnamen des Events (3.6).
3. **Säle erben** Adresse, Koordinaten, Stadtteil, Stadt und, wenn nicht gesetzt, die Art vom Haus. Sie werden nicht einzeln geokodiert (3.6, 3.12).
4. **Der „Übergang“ in 3.9 ist gestrichen.** Er widersprach der Reihenfolge: Der Nachtrag der `ort_id` läuft in Schritt 2, die Seiten kommen erst in Schritt 3. Neu steht eine feste **Deploy-Reihenfolge** in Abschnitt 4: Schema-SQL, Pipeline-Code, Nachtrag, Seiten.
5. **Slug-Kollision:** Die Annahme „gleicher Slug = gleicher Ort“ war falsch. Ein Beispiel ist „Central“ als Saal des Schauspielhauses und als möglicher anderer Ort.
   - Slugs entstehen jetzt nach dem vorhandenen Muster `_slug_erzeugen(name, stadtteil)`, Säle als `<haus-slug>-<saal>`.
   - Bei einer Kollision lehnt der Import die Zeile ab, mit Meldung.
   - Ein Slug, der in `ort_weiterleitungen` steht, wird nicht neu vergeben (3.3 Punkt 7).
6. **Eine gemeinsame Zuordnungsfunktion** für Pipeline, Nachtrag und alle drei Dubletten-Stellen:
   - `pipeline/deduplication.py`, der Abgleich mit dem Tagesbestand in `database/client.py` und `pipeline/dubletten_sql.py`
   - Der Pipeline-Schritt sitzt in `main.py` zwischen Gebietsfilter (1c) und Dubletten (3.4).
7. **Weiterleitungen ohne Ketten:**
   - Ziele sind nur `/orte/<slug>` einer aktiven Spielstätte, eine kanonische Guide-URL oder `/orte`.
   - Wird ein Ziel umbenannt oder zusammengelegt, zieht dieselbe SQL-Datei die alten Einträge nach (3.3 Punkt 4). *In der siebten Fassung ersetzt durch `ziel_ort_id` mit Ziel zur Laufzeit.*
8. **Fehler im Proxy:** Bei Netzwerkfehlern gilt wie heute „weiter“ (Grundsatz in `web/lib/pfad-pruefung.ts`). Die Seite zeigt dann für einen unbekannten Slug einen Hinweis mit `noindex`, keine Ersatzdaten (3.10).
9. **Filter auf `/orte`** laufen über Query-Parameter. Die Canonical-URL ist immer `/orte`, gefilterte Ansichten stehen nicht in der Sitemap. Stadtteilseiten verlinken mit Parameter (3.8, 3.11).
10. **IndexNow für Ortsseiten:**
    - Die Indexierungsregel gibt es in TypeScript (Seite, Sitemap) und in Python (IndexNow). Beide prüft ein gemeinsamer Satz Testfälle als JSON.
    - Gemeldet werden nach jedem Lauf die indexierbaren Ortsseiten, die neue Events bekommen haben, analog zu den Tagesseiten (3.11).
11. **Offene Club-Fälle bis zur Entscheidung:** Stone im Ratinger Hof bleibt so zugeordnet wie heute. Es gibt keine neue Seite und keinen neuen Link (3.2).

## Änderungsprotokoll 19.11.2026, fünfte Fassung (Cursor-Prüfung der vierten)

Cursor hat alle 9 Punkte der vierten Fassung als behoben bestätigt und den Plan als freigabereif eingeschätzt. Dazu kamen 4 geringe Hinweise. Sie sind am Code und an der CSV nachgeprüft und eingearbeitet:

1. **`ausflug` und `wochenendtipp`** sind kein Ziel für einen 308, denn ihre Hubs haben keine Detailseiten. `/orte/<slug>` bleibt für sie 404. `ortPfad()` wird nur für Spielplatz und Weihnachtsmarkt genutzt, weil es für andere Typen auf `/guides/restaurants-cafes` zurückfällt (3.10, Test).
2. **Sieben weitere Häuser ohne Art-Wort** stehen mit vorgeschlagener Art in der Namensliste (7.2 Punkt 18).
3. **Die Saalliste** ist vollständig ausgeschrieben, mit allen Sälen ab 2 Events aus der CSV (3.6).
   - **Abweichung:** „KIT – Kunst im Tunnel“ ist kein Saal, sondern der ausgeschriebene Name des KIT. Die Zeile bleibt eine Schreibweise des Hauses.
4. **Koordinaten nur mit Stadt:** Ohne PLZ in den drei Bereichen werden keine Koordinaten gespeichert. Karte, Stadt-Filter und JSON-LD hängen damit an derselben Bedingung (3.12).

## Änderungsprotokoll 19.11.2026, vierte Fassung (Cursor-Prüfung der dritten)

Cursor hat 11 der 13 alten Befunde als behoben bestätigt, 2 als teilweise behoben, und 7 neue gemeldet. Alle sind am Code und an der CSV nachgeprüft und stimmen.

- **Alt 5 und neu 1, Trigger:** Er feuert jetzt auch bei `UPDATE OF typ`. Wechselt eine Zeile weg von `spielstaette`, gilt dieselbe Pflicht zur Weiterleitung wie beim Abschalten (3.3 Punkt 8).
- **Alt 12, Bildversion:** `?v=` genau wie `ortBildUrl()`, also nur bei `foto_version > 1`. Der Test ist angepasst (3.13).
- **Neu 2, Proxy:** Spielplätze und Weihnachtsmärkte bekommen ihr Ziel über `ortPfad()`. Ein zusammengelegter Markt geht über `WM_ZUSAMMENGELEGT` auf den verbliebenen (3.10, zwei Tests).
- **Neu 3, Art-Muster:** `pfarr` kommt ins Kirchen-Muster. Kulturhaus und Klanghaus bleiben eigene Art-Wörter, Billardzentrum geht nach Sport. Das Gerhart-Hauptmann-Haus bekommt eine ausdrückliche Art (7.2 Punkt 18).
- **Neu 4, Dubletten:**
  - Bei Ketten reicht der Name nicht, es gilt die Adresse.
  - Ein Saal ohne `parent_id` wird nicht importiert.
  - Der zakk-Test bekommt eine Variante ohne Eltern (3.4).
- **Neu 5, Stadt bei Neuss und Ratingen:** Kopf, Karte und JSON-LD (`addressLocality`) nutzen die Stadt aus der PLZ. Der Stadtteil-Filter gilt nur für Düsseldorf, daneben gibt es einen Stadt-Filter (3.8, 3.11, 3.12).
- **Neu 6, Trigger-Probelauf:** eigene Datei mit `BEGIN` … `ROLLBACK`, nie in der Migrationsdatei (3.3 Punkt 8, Abschnitt 4).
- **Neu 7, Säle:** Eine Saalzeile entsteht nur für Säle aus einer gepflegten Saalliste je Haus, nicht bei jedem Trenner. PubCrawl, „Stadtfenster“ und Herzkammer bleiben Schreibweisen ihres Hauses (3.6, 7.2 Punkt 21).

## Änderungsprotokoll 19.11.2026, dritte Fassung (Cursor-Prüfung der zweiten)

Cursor hat 13 Befunde gemeldet. Alle sind am Code und an der CSV nachgeprüft und stimmen. Sie sind so eingearbeitet:

1. **Dubletten mit `ort_id`:**
   - Gleiche ID heißt gleicher Ort.
   - Verschiedene IDs heißen verschiedener Ort nur, wenn sie auf verschiedene Häuser zeigen.
   - Säle desselben Hauses bleiben über den Namen zusammenlegbar (3.4, Test mit dem zakk-Paar).
2. **Reihen-Schlüssel:** Keine Namensänderung, die einen Reihen-Schlüssel ändert. Eine solche Schreibweise kommt nur in `event_orte`, nicht in `SPIELSTAETTEN` (3.5, Test).
3. **„Xafe in KAP 1 Zentralbibliothek“** ist ein Café, keine Bibliothek (7.2 Punkt 12).
4. **Acht weitere CSV-Fehler** mit Zeile und gewünschtem Vorschlag (7.2 Punkte 13–20). Entscheidungszeilen gibt es für Säle auch unter der Hinweisgrenze (FFT Bühne I, KAP1).
   - **Eine Abweichung:** „Bahnhof“ kommt nicht pauschal ins Treffpunkt-Muster. „Alter Bahnhof Oberkassel“ ist ein Lokal und bekommt einen Prüfhinweis (7.2 Punkt 15).
5. **Lebenszyklus in der Datenbank erzwungen:**
   - Der Import setzt `aktiv = true`.
   - Ein Trigger bricht Löschen, Abschalten und Slug-Wechsel einer Spielstätte ohne Weiterleitung ab, ebenso das Löschen eines Hauses mit Sälen (3.3 Punkt 8, 3.4, Test).
6. **„Mülheim“** wird als ganzes Wort gefiltert. Der Vorschlag aus Cursor ist übernommen, die Abweichung der zweiten Fassung entfällt. Grund: „Stadthalle Mülheim“ ohne Komma rutscht heute durch. „Mülheimer Straße“ bleibt drin, weil nach dem „m“ kein Wortende liegt (3.16, Tests).
7. **Stadtteil** nur aus der PLZ der bestätigten Adresse (`PLZ_STADTTEIL`), nicht über den Ortsnamen. Neuss und Ratingen haben keinen Stadtteil-Filter, solange der Mapper ihre PLZ nicht kennt (3.12).
8. **Blocker vor 308** gilt nur für Slugs, deren Ziel die falsche Club-Seite wäre (3.2).
9. **308 auf die kanonische Guide-URL** nach `hauptSeiteSichtbar` und `eigeneClubSeite`, nicht auf irgendeine sichtbare (3.10, Test).
10. **Fünf weitere Pflicht-Tests** (Abschnitt 4).
11. **Einstiege** aus Entdecken, Fuß und Stadtteilseiten stehen in Schritt 3.
12. **Bildversion:** `?v=<foto_version>` auch am lokalen Pfad (3.13).
13. **Cache:**
    - kurz bei Fehler
    - eine gecachte Liste je Haus (mit Kindern)
    - Zielfeld des Bücherei-Scrapers genannt (3.9, 3.15)

## Änderungsprotokoll 19.11.2026, zweite Fassung

Grundlage war eine Prüfliste des Auftraggebers mit 19 Punkten. Jeder Punkt ist am Code und an `data/spielstaetten/kandidaten.csv` geprüft.

**Bestätigt** (Zahlen und Code stimmen, eingearbeitet):
- CSV-Zahlen: 236 „neue Ortsseite“, davon 144 ohne Adresse, 156 ohne Stadtteil, 114 ohne kommendes Event, 99 mit Art „Sonstiges“.
- 14 Kandidaten mit unsichtbarer `orte`-Zeile.
- Falsche oder offene Club-Verknüpfungen:
  - Theater an der Kö → Kö-Club
  - Stone im Ratinger Hof
  - Bilker Bunker und Schleuse Zwei, beide Aachener Str. 39
- `ort_basis` schneidet am Trenner (`pipeline/reihen_zuordnen.py`).
- Der Proxy liest mit dem anonymen Schlüssel, die Lese-Regel ist `aktiv = true` (`database/schema_orte.sql`, Policy `orte_lesen`). `WM_ZUSAMMENGELEGT` liegt in `web/lib/pfad-pruefung.ts`.
- `eventPoolLaden()` reicht 60 Tage (`TAGE_VORAUS`) und fällt bei Fehlern auf Beispieldaten zurück (`quelle: "beispiel"`).
- `orteLaden()` filtert auf Score ≥ 7. Spielplätze und Weihnachtsmärkte sind ohne Score sichtbar.
- `scraper/weihnachtsmaerkte/bilder.py` bricht ohne Erlaubnis ab. Die Guide-Karte ist MapLibre mit PMTiles. `GoogleKarte` steht in `web/components/client.tsx`.
- Fehler im Klassifikator: Hansaallee 190, Marktplatz, Tourist-Information, „flin“ in Flingern, Franklinstraße Turnhalle, zu weite Muster für „haus“ und „forum“.

**Abweichend von der Prüfliste:** Das Verhalten des Codes bleibt, die Begründung steht hier.
- **Unterbach** ist ein Düsseldorfer Stadtteil (Stadtbezirk 8, `web/lib/stadtteile.ts`). Er kommt nicht auf die Liste auswärtiger Orte, sonst fielen Düsseldorfer Events heraus. Hochdahl (Erkrath), Büderich und Osterath (Meerbusch) kommen dagegen auf die Liste. Sie stehen heute in keinem Event, das ist eine Vorsorge.
- ~~**Mülheim** bleibt nur als eigener Abschnitt.~~ In der dritten Fassung nach der Cursor-Prüfung geändert: Mülheim wird als ganzes Wort gefiltert (3.16).

**Zusätzlich gefunden und eingearbeitet:**
1. **Inaktive Orte sind für den Proxy unsichtbar** (RLS `aktiv = true`, anonymer Schlüssel). Die Zweige „abgeschaltet → 308“ in `spielplatzEntscheidung` und `weihnachtsmarktEntscheidung` werden deshalb nie erreicht. Ein abgeschalteter Spielplatz oder Markt endet heute als 404, nicht als 308.
   - Für die Ortsseiten gibt es deshalb eine eigene, öffentlich lesbare Weiterleitungstabelle (3.3 Punkt 4, 3.4).
   - Für Spielplätze und Weihnachtsmärkte ist das ein Folgepunkt außerhalb dieses Plans (Abschnitt 9).
2. **Google-Koordinaten dauerhaft speichern verstößt gegen die Bedingungen von Google.** Dauerhaft speichern darf man nur die `place_id`. Koordinaten kommen deshalb aus der bestätigten Adresse über OpenStreetMap Nominatim, mit Rate-Limit und ohne neue Bibliothek (3.12).
3. **Schon eingetragene Entscheidungen** in der CSV dürfen beim Neuerzeugen nicht verloren gehen. Das Skript führt sie über einen Schlüssel zusammen (Schritt 1).
4. **Ketten** mit vielen Filialen und einer `orte`-Zeile (Starbucks, Extrablatt, ALEX): Eine `ort_id` gibt es nur, wenn die Event-Adresse zur Adresse der Zeile passt (3.4).
5. **Importskripte der Guides** dürfen Zeilen vom Typ `spielstaette` nicht anfassen. Das ist im Test festgehalten.
6. **Dubletten bei Events:** `ort_id` wird ein Signal in `pipeline/deduplication.py`. Die genaue Regel nach Häusern steht in der dritten Fassung (3.4).
7. **Rausgegangen** sperrt Unterseiten in der robots.txt. Von dort wird nichts automatisch übernommen, weder Daten noch Bilder (Abschnitt 2).
8. **Stadtteil** einer Spielstätte: nur aus der PLZ der bestätigten Adresse (`PLZ_STADTTEIL` in `pipeline/stadtteil_mapper.py`), sonst leer. Leere Stadtteile fehlen in Filtern, Karte und Stadtteilseiten.

**Bei der Gesamtprüfung der neuen Fassung noch gefunden:**
9. **Google-Foto als Rückfall:** `ortBildUrl()` in `web/lib/orte.ts` zeigt ohne lokales Bild das Google-Foto über `/ort-foto/[slug]`, sobald `extras.google_foto` gesetzt ist. Außerdem schickt die Funktion jedes nicht lokale `bild_url` über diese Route. Ortsseiten nutzen deshalb nur `lokalesBild()`, sonst die Ersatzkachel. `extras.google_foto` wird für `spielstaette` nie gesetzt, und `bild_url` ist nur ein lokaler Pfad (3.13, Test).
10. **IndexNow** meldet heute nur Event-, Tages- und Startseiten (`urls_bauen` in `pipeline/indexnow.py`). Ortsseiten brauchen eine eigene Meldung (3.11).
11. **Sitemap:** `web/app/sitemap.ts` lädt Orte über `orteLaden()` mit Score-Filter. Ortsseiten brauchen dort die eigene Ladefunktion aus 3.3 (3.11).
12. **Nominatim und die Projektregeln:** In CLAUDE.md steht „mindestens 2 Sekunden zwischen Anfragen“. Das ist strenger als die Nominatim-Regel (1 pro Sekunde) und gilt deshalb (3.12).
13. **`.gitignore`:** Freigegeben ist bisher nur `data/spielstaetten/kandidaten.csv`.
    - `bilder.csv` und `texte.csv` bekommen eigene Ausnahmen.
    - Die Geo-Prüfdatei enthält Google-Inhalte und bleibt lokal, wie die Prüf-CSV der Weihnachtsmärkte (3.12).

**Umbau des Dokuments:**
- Abschnitt 1 ist als historischer Stand vor dem Gebietsfilter gekennzeichnet.
- Abschnitte 3 und 4 enthalten nur noch den beschlossenen Weg.
- Abschnitt 7 ist der aktuelle, noch nicht freigegebene Kandidatenstand.
- Abschnitt 8 (alte offene Fragen) ist erledigt.
- Neu ist Abschnitt 9 mit den offenen Einzelentscheidungen.

---

## 1. Bestandsaufnahme vom 18.11.2026 (HISTORISCH, Stand vor dem Gebietsfilter)

> Diese Zahlen stammen aus der ersten Fassung, **bevor** die Events außerhalb von Düsseldorf, Neuss und Ratingen gelöscht wurden (insgesamt 374 Events, Abschnitt 6). Sie bleiben nur zur Nachvollziehbarkeit stehen. Der aktuelle Stand ist Abschnitt 7.

**Grundlage:** 5.027 Events seit 18.11.2025 einschließlich der kommenden, ohne abgelehnte, gegen 2.310 Zeilen in `orte`.

| Events je Ortsname | Ortsnamen | ohne Seite | Guide-Seite | Club-Seite | in `orte`, unsichtbar |
|---|---|---|---|---|---|
| ≥ 1 | 919 | 831 | 39 | 24 | 25 |
| ≥ 2 | 469 | 414 | 23 | 18 | 14 |
| ≥ 5 | 225 | 182 | 21 | 15 | 7 |
| ≥ 20 | 50 | 42 | 2 | 6 | 0 |

Arten von Einträgen:
- echte Spielstätten
- Säle eines Hauses
- Treffpunkte, Straßen und Plätze
- allgemeine Angaben
- Online-Termine
- Orte außerhalb
- das Büchereinetz unter einer Adresse

## 2. Vorbild Rausgegangen (angesehen am 18.11.2026)

**Aufbau** am Beispiel `rausgegangen.de/locations/roncallis-apollo-variete/`:
- Kopf: Titelbild mit Nachweis, Name, Adresse, Folgen, Teilen
- Reiter: Übersicht, Events, Infos, Barrierefreiheit
- Inhalt: nächste Events, ein „Über die Location“-Text des Hauses (wir-Form), Öffnungszeiten, Links, ähnliche Seiten
- Für Suchmaschinen: JSON-LD `LocalBusiness`, `ItemList` und `BreadcrumbList`

Wir übernehmen den Aufbau, nicht die Inhalte. Die robots.txt von Rausgegangen sperrt Unterseiten. Von dort wird nichts automatisch gelesen oder übernommen, weder Texte noch Bilder noch Listen.

## 3. Beschlossener Weg

### 3.1 Veröffentlichungsgrenze (E2)
- **Kandidat:** echter Ort mit ≥ 2 Events in 12 Monaten plus kommend, im Gebiet nach E3 (Kandidatenliste, Abschnitt 7). Der Vorschlag des Skripts ist **keine Freigabe**.
- **Eine Seite entsteht nur, wenn**
  - in der CSV `entscheidung = ja` steht,
  - die Art vom Auftraggeber in `art_korrigiert` gesetzt ist („Sonstiges“ ist nicht zulässig),
  - und der Ort eine echte Spielstätte ist (kein Treffpunkt, keine Straße, keine Gruppe, keine Kette, kein Netz).

  Das Import-Skript lehnt jede andere Zeile ab.
- **Indexiert wird eine Seite nur, wenn beides gilt:**
  - Adresse bestätigt **oder** Text freigegeben,
  - **und** mindestens ein kommendes Event **oder** freigegebener Text.

  Ohne diese Voraussetzungen ist die Seite erreichbar, aber `noindex`, nicht in der Sitemap und nicht bei IndexNow.

### 3.2 Eine URL je Ort (E1)
- **Sichtbare Guide-Orte** (Kneipen & Bars, Restaurants & Cafés, Clubs, Spielplätze, Weihnachtsmärkte):
  - keine zweite Zeile, keine Ortsseite
  - `events.ort_id` zeigt auf die vorhandene Zeile
  - Ihre Guide-Seite bekommt den Block **„Nächste Events“** (Schritt 3), gespeist aus derselben Abfrage über `ort_id` wie die Ortsseite (3.9).
    - Die Club-Seite hat diesen Block heute schon, über `naechsteEvents` in `web/lib/clubs-daten.ts`: 60-Tage-Pool und Abgleich über `extras.club.event_orte`. Das wird ersetzt.
    - So fallen „nicht im …“-Events (ohne `ort_id`) weg, und Säle lassen sich filtern.
    - `extras.club.event_orte` bleibt die Grundlage der **Zuordnung** (3.4), nicht mehr der Anzeige.
- **Unsichtbare Guide-Zeilen** (Score < 7):
  - Heute 14 Kandidaten: hirschchen, Cosmo Sports, The Paradise Now, Kasematten, Cafe Extrablatt, das Alfreds, Kausal, Starbucks, Simple Miles, ALEX, Bier zu Liebe, CADO, Café Mélancholie, Zoopavillon.
  - keine zweite Zeile, kein Typ `spielstaette`
  - `ort_id` zeigt auf die vorhandene Zeile, bei Ketten nur mit passender Adresse (3.4)
  - Öffentlich gibt es keinen Link auf sie, die Eventseite behält den bisherigen Suchlink.
- **Ketten** (viele Filialen, eine `orte`-Zeile: Starbucks, Extrablatt, ALEX): keine stadtweite Spielstättenseite.
- **Links auf der Eventseite:** genau ein Ortslink.
  - Auf die kanonische URL, wenn der Ort eine sichtbare Seite hat (Guide-Seite nach den bestehenden Hub-Regeln oder `/orte/<slug>`).
  - Sonst bleibt der bisherige Link „Weitere Events an diesem Ort“ auf die Suche.
  - Der zusätzliche Club-Link entfällt, wenn er auf ein anderes Ziel zeigen würde.
  - Interne Links gehen nie über den Umweg `/orte/<guide-slug>`.
- **Falsche Club-Verknüpfungen blockieren nur die betroffenen Slugs** (Schritt 2):
  - Ein 308 ist verboten, solange sein Ziel noch die falsche Club-Seite wäre. Alle anderen Weiterleitungen warten nicht auf Abschnitt 9.
  - „Theater an der Kö“ kommt in Schritt 2 in die Ausschlussliste `EVENT_ORTE_AUSSCHLUSS` des Kö-Clubs (3.4) und wird damit dauerhaft aus seinem `event_orte` und seiner Zuordnung genommen. Ob es eine eigene Seite bekommt, entscheidet die Sichtung (Abschnitt 9).
  - „Stone im Ratinger Hof“ und das Paar Bilker Bunker / Schleuse Zwei entscheidet der Auftraggeber (Abschnitt 9).
    - Bis dahin gibt es für diese drei Namen weder eine Ortsseite noch einen 308.
    - Ihre heutige Zuordnung bleibt unverändert, auch für die `ort_id`. Stone zählt also weiter zum Club Ratinger Hof.

### 3.3 Datenmodell (E5, E6)
Eigene SQL-Datei nach dem Muster `database/orte_typ_weihnachtsmarkt_2026-11-17.sql`. `schema_orte.sql` bleibt unverändert.

1. **Typ `spielstaette`:**
   - Vorprüfung: Kein bestehender Wert verletzt die neue Regel.
   - Neue CHECK-Liste vollständig: `restaurant, imbiss, cafe, kneipe, club, spielplatz, ausflug, wochenendtipp, weihnachtsmarkt, spielstaette`.
   - Kontrollabfrage am Ende.
2. **`orte.parent_id`:** UUID, nullable, Fremdschlüssel auf `orte(id)` mit `ON DELETE SET NULL`, Index. Verbindet Saal und Haus (E6) bzw. Standort und Dach (K20/K21 → Kunstsammlung NRW, optional).
3. **`events.ort_id`:** UUID, nullable, Fremdschlüssel auf `orte(id)` mit `ON DELETE SET NULL`, Index. Gesetzt für **jeden** Treffer, auch Guides und Clubs, weil B4 („Folgen“) dieselbe ID nutzt.
4. **`ort_weiterleitungen`:**
   - **Spalten:**
     - `alter_slug` (Primärschlüssel)
     - `ziel_ort_id` (UUID, Fremdschlüssel auf `orte(id)` mit `ON DELETE SET NULL`, nullable)
     - `grund`, `erstellt_am`
   - Es gibt **keinen festen Zielpfad**.
   - RLS: Lesen für alle (auch der anonyme Schlüssel des Proxys), Schreiben nur mit dem Service-Schlüssel.
   - Nötig, weil inaktive `orte`-Zeilen für den Proxy unsichtbar sind.
   - **Ziel zur Laufzeit:** Der Proxy lädt die Zielzeile über `ziel_ort_id` (anonymer Schlüssel, also nur aktive Zeilen) und bildet die kanonische URL nach denselben Regeln wie in 3.10.
     - aktive Spielstätte → `/orte/<slug>`
     - sichtbare Guide-Zeile → ihre kanonische Guide-URL
     - nicht sichtbar, inaktiv, gelöscht oder `ziel_ort_id` leer → `/orte`
   - **Folge:**
     - kein 308 auf eine 404
     - kein veraltetes Ziel, wenn ein `auch_club` durch einen Score-Wechsel die kanonische Seite wechselt
     - keine Ketten nach einer Umbenennung des Ziels, weil die UUID bleibt. Beim Umbenennen ist ein Nachziehen alter Einträge nicht nötig.
   - **Ein Ziel ist nie selbst eine Weiterleitung.** Der Proxy folgt höchstens einer Stufe: `alter_slug` → Zielzeile → URL.
   - **Zielabfrage:** Sie liest `slug`, `typ`, `aktiv`, Score und Club-Felder, also dieselben Felder wie `ortLaden` in `web/lib/pfad-pruefung.ts`, dazu den Slug.
     - Schlägt sie fehl (Fehler, Timeout, `undefined`), ist die Entscheidung **„weiter“**, nicht ein 308 auf `/orte`.
     - Nur eine erfolgreich leere Antwort heißt „Ziel nicht sichtbar“ und führt auf `/orte`.
   - **Kein leeres Ziel durch Löschen:** Wird eine Zeile gelöscht oder abgeschaltet, auf die Einträge zeigen (`ziel_ort_id` = diese Zeile), hängt dieselbe SQL-Datei sie **vorher** um (`UPDATE ort_weiterleitungen SET ziel_ort_id = <neues Ziel> WHERE ziel_ort_id = <alte ID>`). Der Trigger erzwingt das (Punkt 8). `ON DELETE SET NULL` bleibt nur letzte Sicherung.
5. **Vorhandene Spalten von `orte` werden genutzt, nicht in `extras` gedoppelt:**
   - `adresse`, `stadtteil`, `latitude`/`longitude`, `webseite`, `google_place_id`
   - `beschreibung` (nur der freigegebene Text)
   - `bild_url` (lokaler Pfad `/ort-bilder/orte/<slug>.webp`, den `lokalesBild()` in `web/lib/orte.ts` schon akzeptiert), `bild_attribution` (Nachweis), `extras.bild_link` (Link zum Nachweis)

   **Nur das Zusätzliche in `extras.spielstaette`:**
   - `art`, `event_orte` (alle zugeordneten Schreibweisen, wie bei Clubs)
   - `adresse_bestaetigt` (Datum, Quelle), `text_quellen` (Quellen-URL je Satz), `text_freigegeben` (Datum)
   - `bild_herkunft` (Seiten-URL, Abrufdatum, `erlaubnis = nachtraeglich`), `geo_quelle`
6. **Sichtbarkeit:** `spielstaette` ist sichtbar, wenn `aktiv` gilt, ohne Qualitäts-Score, wie bei Spielplätzen und Weihnachtsmärkten.
   - Eigene Ladefunktion, nicht `orteLaden()` und nicht `MIN_QUALITAETS_SCORE`.
   - `google_place_id` liegt in der vorhandenen Spalte.
   - `aktiv` steht in `schema_orte.sql` standardmäßig auf `false`. **Der Import setzt `aktiv = true` ausdrücklich**, sonst wäre die neue Seite für den Proxy unsichtbar (404).
7. **Slugs** sind über alle Zeilen von `orte` eindeutig (UNIQUE gibt es schon).
   - **Bildung:**
     - **Neue Häuser** bekommen die tatsächliche Ausgabe von `_slug_erzeugen(name, stadtteil)` aus `scraper/orte/google_places.py`. Der Stadtteil wird angehängt, wenn er nicht schon im Namen steckt. Ohne bestätigten Stadtteil gibt es keinen Anhang.
     - **Säle** bekommen den **gespeicherten Slug der vorhandenen Hauszeile** plus Saal, z. B. `zakk-flingern-halle`, weil der Club zakk heute `zakk-flingern` heißt. Es wird nie ein neuer Haus-Slug erzeugt.
     - Der Slug steht vor dem Import in der CSV, damit der Auftraggeber ihn sieht. Er wird nach dem Import nicht mehr neu berechnet.
   - **Kollision:** Ein gleicher Slug heißt **nicht** gleicher Ort, z. B. „Central“. Der Import lehnt die Zeile mit Meldung ab. Ob es derselbe Ort ist (dann `ort_id` auf die vorhandene Zeile, keine zweite Zeile) oder ein anderer (dann ein anderer Slug), entscheidet der Auftraggeber.
   - **Kein Slug aus `ort_weiterleitungen.alter_slug`** wird neu vergeben. Der Import prüft das, weil die Weiterleitung sonst still unwirksam würde.
8. **Schutz-Trigger** auf `orte` als `BEFORE DELETE OR UPDATE OF aktiv, slug, typ`. Er gilt für Zeilen mit `OLD.typ = 'spielstaette'` und bricht mit Fehlermeldung ab,
   - wenn eine Zeile gelöscht, auf `aktiv = false` gesetzt, ihr Slug geändert oder ihr `typ` von `spielstaette` weg geändert wird und `ort_weiterleitungen` keine Zeile mit `alter_slug = OLD.slug` hat. Der Typwechsel zählt wie Abschalten, denn sonst endet `/orte/<slug>` als 404. Ein Umbau in zwei Schritten (erst `typ`, dann löschen) ist damit auch abgedeckt.
   - wenn ein Haus gelöscht oder abgeschaltet wird, das noch Kinder hat (`parent_id = OLD.id`, aktiv). Die Kinder bekommen vorher einen neuen `parent_id` oder werden selbst mit Weiterleitung abgeschaltet.
     - **Diese Kinder-Prüfung gilt für jeden Elterntyp**, nicht nur für Spielstätten. Ein Guide-Haus wie zakk (Typ `club`) kann Säle haben (3.6).
   - wenn eine Zeile **beliebigen Typs** gelöscht oder abgeschaltet wird, auf die noch ein Eintrag in `ort_weiterleitungen` zeigt (`ziel_ort_id = OLD.id`). Diese Einträge müssen vorher umgehängt werden (Punkt 4).
   - **Aufbau des Triggers:**
     - Die Weiterleitungspflicht für den eigenen Slug gilt nur bei `OLD.typ = 'spielstaette'`.
     - Die Kinder-Prüfung und die Prüfung „Ziel einer Weiterleitung“ gelten bei jeder Zeile.
     - Für Guide-Zeilen ohne Kinder ändert sich nichts, ihre Importskripte laufen weiter wie bisher.
     - **`freischalten` in `scraper/orte/clubs_profil.py`** setzt `aktiv` je Club und fängt Fehler heute nicht ab. Es fängt künftig einen Trigger-Fehler je Zeile, schreibt „Club hat aktive Säle, nicht abgeschaltet“ ins Log und macht mit dem nächsten Club weiter. Was mit den Sälen passiert, entscheidet der Auftraggeber.

   **Probelauf des Triggers** in einer eigenen Datei (`database/orte_spielstaette_trigger_probe_<datum>.sql`), nie in der Migrationsdatei, weil ein erwarteter Fehler dort die Migration abbrechen würde:
   - alles in einer Transaktion `BEGIN` … `ROLLBACK`
   - Die Datei legt ihre Test-Spielstätte (mit Saal) selbst an, dazu eine Test-Guide-Zeile mit Saal für die Kinder-Prüfung.
   - Jeder Test-Saal wird **ausdrücklich mit `aktiv = true`** angelegt. Der Standard ist `false`, und ein inaktiver Saal ließe den Löschtest aus dem falschen Grund durchgehen.
   - Jeder erwartete Fehler steckt in einem `DO`-Block mit `EXCEPTION`, der „ok“ oder „FEHLER“ ausgibt. So läuft die Datei bis zum `ROLLBACK` durch.

   Deshalb gilt in jeder SQL-Datei: zuerst die Weiterleitung einfügen, dann ändern. `ON DELETE SET NULL` an `parent_id`, `events.ort_id` und `ort_weiterleitungen.ziel_ort_id` bleibt als letzte Sicherung. Bei Spielstätten greift es wegen des Triggers nur nach einem bewussten Umhängen.

### 3.4 Zuordnung und Lebenszyklus von `ort_id`
- **Eine Funktion für alles:** `ort_zuordnen(event, orte_index)` in einem neuen Modul `pipeline/ort_zuordnung.py`. Pipeline und Nachtrag nutzen dieselbe Funktion, damit sie nie verschieden zuordnen.
  - Grundlage: einheitlicher Name (`einheitlicher_name`) gleich einem Eintrag in `event_orte` einer aktiven Zeile, bei Guides auch gleich `orte.name` (normalisiert). Für Clubs zählt `extras.club.event_orte`, für Spielstätten `extras.spielstaette.event_orte`.
  - Mehrdeutig (mehrere Zeilen) → keine neue `ort_id` und ein Eintrag im Log. Steht schon eine `ort_id`, bleibt sie und zählt als `ort_id_mehrdeutig` (unten).
  - Schreibweisen aus `EVENT_ORTE_AUSSCHLUSS` (unten) und „nicht im …“-Namen nach der Regel aus `event_orte()` ergeben nie einen Treffer, auch wenn sie noch in einem gespeicherten `event_orte` stehen.
  - Ketten nur, wenn die Event-Adresse zur Adresse der Zeile passt.
- **Pipeline:** neuer **Schritt 1d** „Ortszuordnung“ in `main.py`, zwischen `gebiet_filtern` (1c) und der Deduplizierung. Die Deduplizierung heißt heute „Schritt 1d“ und wird zu **1e** umbenannt, auch in den Log-Zeilen. Die Dubletten-Erkennung hat die `ort_id` damit schon.
  - Der `orte_index` wird einmal je Lauf geladen, seitenweise, mit dem Service-Schlüssel, damit auch inaktive Zeilen erkannt und nicht zugeordnet werden.
- **Wann eine `ort_id` geschrieben wird:**
  - **Automatische Läufe** (Pipeline und Nachtrag) setzen oder ersetzen eine `ort_id` nur mit einem **Treffer**. Sie schreiben **nie `NULL` über einen vorhandenen Wert**.
  - **Beim Zusammenführen zweier Events** (`_events_mergen`, Abgleich mit dem Tagesbestand) wird die `ort_id` aus den Ortsnamen **aller** beteiligten Events berechnet, zuerst aus dem verbleibenden Namen, dann aus den übrigen. Beispiel: „zakk – Halle“ von Rausgegangen hat eine Saal-ID, der Veranstalter liefert eine Schreibweise ohne Treffer. Dann bleibt die Saal-ID, auch wenn nach der Vorrang-Regel der Name des Veranstalters gewinnt.
  - Gibt es keinen Treffer, bleibt der vorhandene Wert stehen.
  - **Eine Zuordnung lösen** (z. B. „Theater an der Kö“ vom Kö-Club) geht nur ausdrücklich, in zwei Teilen:
    1. **Code:** Die Schreibweise kommt in die Ausschlussliste `EVENT_ORTE_AUSSCHLUSS` in `scraper/orte/clubs_profil.py` (Club-Name → Schreibweisen, mit Begründung, wie `NICHT_IM_HUB`). `event_orte()` nimmt sie nie wieder auf, und `ort_zuordnen` vergibt für sie nie die ID dieses Clubs.
    2. **SQL, nach dem Deploy dieses Codes:** Die Schreibweise wird aus dem gespeicherten `event_orte` genommen. In derselben Datei steht `UPDATE events SET ort_id = NULL WHERE ort = … AND ort_id = …`.

    Ohne Teil 1 würde `scores_neu` die Schreibweise beim nächsten Lauf aus dem Kalender wieder eintragen. So läuft kein automatischer Lauf gegen eine bewusste Lösung, und der Nachtrag bleibt wiederholbar.
  - Für **Spielstätten** pflegt der Import `extras.spielstaette.event_orte` aus der CSV. Kein automatischer Lauf schreibt diese Liste neu. Eine Lösung ist dort nur Teil 2.
  - Ändert sich eine Zuordnung, weil z. B. ein Saal eine eigene Seite bekommt, ersetzt der nächste Nachtrag die Haus-ID durch die Saal-ID. Das ist ein Treffer, also erlaubt.
- **Nachtrag** für den Bestand als eigene, wiederholbare SQL-Datei, erzeugt von einem Skript (nur lesend), wie `pipeline/gebiet.py --sql`. Nur Zeilen, deren berechneter Treffer vom gespeicherten Wert abweicht.
- **Säle:** `ort_id` zeigt auf die Saalzeile, wenn der Saal eine eigene freigegebene Seite hat, sonst auf das Haus. Ein Saal ohne Seite hat keine eigene Zeile (3.6).
- **„nicht im …“** (z. B. „zakk – nicht im zakk“, 43 Events) bekommt keine `ort_id` des Hauses. Diese Events zählen nicht zum Programm.
  - **Ist-Stand (Lese-Abfrage 19.11.):** Die Schreibweise steht **nicht** in `extras.club.event_orte` des zakk. Dort stehen zakk, Club, Halle, Kneipe, Raum 4, Studio, Tanzraum. `event_orte()` in `clubs_profil.py` schließt „nicht im …“ schon heute aus.
  - **Eine gemeinsame Regel:** Die Prüfung aus `event_orte()` wandert in eine kleine Funktion `nicht_im_ort(ort, hausnamen)`, die `clubs_profil.py` und `ort_zuordnen` beide nutzen.
    - „zakk – nicht im zakk“ zählt nicht zum zakk.
    - „Pitcher, nicht im Freien“ zählt zum Pitcher.
    - „nicht im Saal, sondern im Pitcher Club“ zählt zum Pitcher.
    - Kein pauschales „enthält ‚nicht im‘“.
  - **Kontrolle vor Deploy-Punkt 2:** Es ist kein SQL, sondern eine Lese-Prüfung mit `nicht_im_ort` selbst (`python -m scraper.orte.clubs_profil --nicht-im-pruefen`). Sie läuft lokal aus dem neuen Code, bevor er deployt wird.
    - Sie erwartet 0 Club-Schreibweisen, die nach `nicht_im_ort` nicht zum Club gehören. Sie ändert nichts.
    - Eine bloße Suche nach der Zeichenfolge „nicht im“ wäre zu grob: Sie meldete auch „Pitcher, nicht im Freien“, das zum Pitcher gehört.
    - Ist das Ergebnis nicht 0, wird vor Punkt 2 nachgesehen.
- **`event_orte` der Clubs wächst nur:**
  - `scores_neu` (bei jedem Pipeline-Lauf), `neu_pruefen` und `profile_erstellen` vereinigen künftig die neu gefundenen Schreibweisen mit den gespeicherten, statt die Liste zu ersetzen. Ausgenommen sind die Einträge aus `EVENT_ORTE_AUSSCHLUSS`.
  - **Grund:** Die neue Liste entsteht aus den Events der letzten 180 Tage (`kalender_laden`). Ohne Vereinigung fiele eine Schreibweise heraus, sobald 180 Tage kein Event mit ihr kam.
    - Ein Event mit dieser Schreibweise fände dann in Schritt 1d keinen Treffer. `scores_neu` läuft erst nach dem Speichern.
    - Die Kennzahl unten stiege laufend.
  - `clubs_profil` **leert nie eine `ort_id`**. Eine Zuordnung lösen geht nur über die beiden Teile oben.
- **Allgemeine Regel:** Wer eine Schreibweise ausdrücklich aus `event_orte` nimmt, setzt in derselben SQL-Datei die `ort_id` der Events mit dieser Schreibweise und dieser Zeile auf `NULL`. Bei Clubs steht sie vorher in `EVENT_ORTE_AUSSCHLUSS`.
- **Meldung statt stiller Fehler:**
  - Findet ein Lauf ein Event mit gespeicherter `ort_id`, aber ohne Treffer oder mit mehreren Treffern, ändert er nichts.
  - Die Pipeline prüft dafür **einmal je Lauf den ganzen Bestand**: alle Events mit `ort_id IS NOT NULL`, seitenweise, nicht nur die Events dieses Scrapers. Der Nachtrag prüft denselben Bestand.
  - Jeder Fall geht ins Log und zählt als Kennzahl im Lauf-Bericht, getrennt nach `ort_id_ohne_treffer` (keine passende Zeile mehr) und `ort_id_mehrdeutig` (mehrere Zeilen). Eine Zahl über 0 ist ein Hinweis auf eine vergessene Lösung bzw. eine doppelte Schreibweise.
  - Weil `event_orte` nur wächst, steigt keine der beiden Zahlen von selbst.
- **Umbenennen:** Die UUID bleibt. Bei einem neuen Slug kommt der alte zuerst in `ort_weiterleitungen` mit `ziel_ort_id` = dieselbe Zeile, dann wird der Slug geändert.
- **Zusammenlegen:** in dieser Reihenfolge
  1. Weiterleitung anlegen, `ziel_ort_id` = verbleibender Ort.
  2. **Ältere Weiterleitungen umhängen:** `UPDATE ort_weiterleitungen SET ziel_ort_id = <verbleibend> WHERE ziel_ort_id = <alt>`. Beispiel: `/orte/central` zeigte auf die alte Zeile und zeigt danach auf das Haus, nicht ins Leere.
  3. Events auf den verbleibenden Ort verschieben (`UPDATE events SET ort_id = …`).
  4. Kinder umhängen und `event_orte` zusammenführen.
  5. Die alte Zeile löschen.
- **Abschalten** (Haus geschlossen): nur zusammen mit einer Weiterleitung. `ziel_ort_id` ist das Haus (bei Sälen), ein verwandter Ort oder leer (dann `/orte`). Ältere Einträge, die auf die abgeschaltete Zeile zeigen, werden ebenso umgehängt.
- **Grundregel:** Eine URL, die einmal ausgeliefert wurde, endet nie als 404. Das ist dieselbe Regel wie bei den Spielplätzen. Für Spielstätten erzwingt sie der Trigger (3.3 Punkt 8), nicht die Disziplin beim Schreiben.
- **Dubletten bei Events** (`pipeline/deduplication.py`):
  - Das **Haus** eines Events ist `parent_id` der Zeile, sonst die Zeile selbst.
  - **Gleiche `ort_id`:** gleicher Ort.
  - **Beide haben eine `ort_id`, die Häuser sind verschieden:** verschiedener Ort. Diese Paare werden nicht zusammengelegt.
  - **Gleiches Haus, verschiedene Säle**, oder mindestens ein Event ohne `ort_id`: der heutige Namensvergleich (Kern ohne Raumwörter wie Halle, Saal, Studio). „zakk – Studio“ und „zakk - Zentrum für Aktion, Kultur und Kommunikation“ bleiben dadurch zusammenlegbar, wie im Kommentar in `deduplication.py` beschrieben.
  - **Ausnahme Ketten:** Hat ein Event die `ort_id` einer Kettenzeile und dem anderen fehlt sie, reicht der Name nicht. Zusammengelegt wird nur, wenn auch die Adressen passen, nach derselben Regel wie bei der Zuordnung.
    - Beispiel: Starbucks Steinstraße mit ID und Starbucks Schadowstraße ohne ID bleiben getrennt.
    - Ketten sind Guide-Zeilen, keine Spielstätten. Sie stehen in einer festen Liste im Pipeline-Schritt (heute Starbucks, Cafe Extrablatt, ALEX). Dieselbe Liste nutzen die Zuordnung (oben) und die Kandidatenliste (7.2 Punkt 14).
  - **Säle haben immer ein Haus:** Eine Saalzeile ohne `parent_id` wird nicht importiert, der Import lehnt sie ab. Ohne diese Regel gälte ein Saal als eigenes Haus, und das zakk-Paar würde getrennt.
  - Die Häuser kommen aus einer einmal je Lauf geladenen Zuordnung `ort_id → Haus`.
  - **Dieselbe Regel an allen Stellen, an denen heute Dubletten erkannt werden:**
    - `deduplizieren` in `pipeline/deduplication.py` (innerhalb eines Laufs)
    - der Abgleich mit dem Tagesbestand in `database/client.py` (`_tagesbestand` / `bester_treffer`). `ort_id` kommt dafür in `_ABGLEICH_SPALTEN`.
    - `pipeline/dubletten_sql.py` (Aufräum-SQL). `ort_id` kommt in dessen Spaltenliste.

    Der Ortsvergleich steckt heute in `_ort_passt`. Dort wird die neue Regel eingebaut, damit alle Stellen sie automatisch bekommen.
  - **Die Haus-Zuordnung** `ort_id → Haus` liegt auf `orte` (`parent_id`), nicht auf dem Event. `_ort_passt` bekommt sie als optionales Argument.
    - **Ohne geladene Häuser** gilt der heutige Namensvergleich. Es gibt dann nie den Schluss „verschiedene Orte“ allein aus verschiedenen IDs.
    - Das betrifft auch `pipeline/rausgegangen_nachziehen.py`, das `aehnliches_event` aufruft. Dort bleibt es beim Namensvergleich, bis die Häuser dort geladen werden.

### 3.5 Namen und Reihen
Es bleibt das **eine** Namensschema aus `pipeline/ortsnamen.py`, ohne zweites daneben.
- **Säle mit dem Haus vorne und „ – “:** Das ist die bestehende Ausnahme für zakk und FFT, der Test in `tests/test_ortsnamen.py` ist dafür erweitert.
  - `ort_basis` liefert dann das Haus, die Reihen zählen also Haus-weit.
  - Ein Stück auf zwei Bühnen bleibt eine Reihe. Das ist gewollt.
- **Säle mit anderem Anfang** (Central 1, „D'haus im Central“, „Black Box Kino im Filmmuseum“, „Tonhalle Mendelssohn-Saal“) bleiben ohne Trenner und unverändert, die Reihen also auch.
- **Zuordnung Saal → Haus:** über `orte.parent_id` und `event_orte`, **nicht über den Namen**.
- **Reihen bleiben in diesem Bau unverändert:** Slugs und interne Schlüssel (`titel|ort_basis`). Hintergrund: `python -m pipeline.ortsnamen --sql` behält zwar die Slugs, schreibt aber den Schlüssel um und bricht bei einer Kollision ab (`sql_erzeugen` in `pipeline/ortsnamen.py`).
- **Neue Schreibweisen:**
  - **Fall 1:** Die Schreibweise ändert keinen Reihen-Schlüssel, weil `ort_basis` gleich bleibt oder keine Reihe betroffen ist. Dann kommt sie wie bisher als Variante in `SPIELSTAETTEN`, und der Bestand wird per `--sql` nachgezogen.
  - **Fall 2:** Die Schreibweise würde einen Schlüssel ändern. Dann kommt sie **nicht** in `SPIELSTAETTEN`. Sie wird nur in `extras.spielstaette.event_orte` des Ortes eingetragen. Für `ort_id` genügt das, der gespeicherte Name bleibt.
  - **Prüfung:** Vor jedem Namens-SQL vergleicht ein Testlauf die Reihen-Schlüssel vorher und nachher. Erwartet wird keine Änderung. Gibt es eine, ist das Fall 2.
- Keine Umbenennung, die `ort_basis` ändert.

### 3.6 Säle (E6)
- **Hausseite:** Events des Hauses und aller Kinder (`parent_id`), mit Filter nach Saal.
  - Bei einer Spielstätte ist das `/orte/<slug>`.
  - Bei einem **Guide-Haus** (z. B. zakk, Typ `club`, Slug `zakk-flingern`) ist es die kanonische Guide-Seite.
    - Ihr Block „Nächste Events“ liest dieselbe Abfrage über `ort_id` des Hauses und der Kinder (3.9), nicht mehr `naechsteEvents` über `event_orte` und den Pool.
    - Dazu kommt derselbe Saal-Filter.
  - Eine zweite Hausseite unter `/orte` gibt es nicht. `/orte/zakk-flingern` (der gespeicherte Club-Slug) leitet nach 3.10 auf die Guide-Seite. `/orte/zakk` ist ohne eigene Weiterleitung ein unbekannter Slug, also 404.
- **Saal-Filter:**
  - Er gruppiert die Events des Hauses nach der Saalliste (unten), über den Ortsnamen des Events.
  - Säle mit eigener Seite stehen dort mit Link.
  - Events ohne erkennbaren Saal stehen unter „Haus allgemein“.
- **Säle ohne eigene Seite haben keine `orte`-Zeile.** Eine aktive Zeile bekäme im Proxy 200, wäre also eine Seite ohne Freigabe. Ihre Events tragen die `ort_id` des Hauses.
- **Saalseite** (nur nach Freigabe je Zeile): eigene Zeile vom Typ `spielstaette` mit `parent_id` auf das Haus. Das Haus kann eine Spielstätte oder eine Guide-Zeile sein.
  - nur die eigenen Events, ein Verweis aufs Haus, **kein wiederholter Haustext**
  - Die Canonical-URL ist die eigene.
  - Im JSON-LD steht das Haus als `containedInPlace`, mit der kanonischen URL des Hauses.
  - **Erbt vom Haus:** Adresse, Koordinaten, Stadtteil, Stadt und, wenn `art_korrigiert` leer ist, die Art. Ein Saal wird nicht einzeln geokodiert und hat keine eigene `google_place_id`.
- **Was ein Saal ist**, steht in einer gepflegten **Saalliste je Haus** im Kandidaten-Skript, als Erweiterung von `HAUS_REGELN`. Stand nach der CSV vom 18.11., Säle ab 2 Events:

  | Haus | Säle |
  |---|---|
  | zakk | Halle, Club, Studio, Tanzraum, Raum 4, Kneipe |
  | FFT Düsseldorf | Bühne I, Bühne II |
  | Düsseldorfer Schauspielhaus | Großes Haus, Kleines Haus, Foyer, Junges Schauspiel, Unterhaus, Central 1, Central 2, Central Brücke |
  | Tonhalle Düsseldorf | Mendelssohn-Saal, Rotunde, Trautvetter-Brückner-Saal, Terrace |
  | Opernhaus Düsseldorf | Foyer |
  | Capitol Theater | Club Saal |
  | Balletthaus | Studio 1, Studio 2 |
  | Filmmuseum | Black Box |

  - Eine Entscheidungszeile ist keine Seite. Ob ein Saal eine Seite bekommt, entscheidet der Auftraggeber je Zeile.
  - **Kein Saal:** „KIT – Kunst im Tunnel“. Das ist der ausgeschriebene Name des KIT, also eine Schreibweise des Hauses.
  - Schritt 1 gleicht die Liste mit der neu erzeugten CSV ab. Säle, die dabei neu auf 2 Events kommen, nennt das Skript als Hinweis „Saal? in Saalliste aufnehmen“. Automatisch aufgenommen werden sie nicht.
  - Ein Teil nach einem Trenner ist **kein** Saal, nur weil er hinter einem Bindestrich steht. Er bleibt eine Schreibweise des Hauses, z. B.:
    - „PubCrawl Düsseldorf - das Original! seit 2008!“
    - „Zentralbibliothek Düsseldorf / Stadtfenster“
    - Herzkammer
    - „NEU #GoFreizeitGO - Deine Freizeit- und Eventbörse“
    - die Bindestrich-Teile von „Treffpunkt Social Night Out Düsseldorf“
- **Jeder Saal aus der Saalliste** bekommt **eine eigene Entscheidungszeile** in der CSV, ab 2 Events wie jeder Kandidat.
  - Das gilt auch unter der Hinweisgrenze, z. B. FFT Bühne I mit 19 Events.
  - „Ab 20 Events“ setzt nur den Hinweis „eigene Seite empfohlen“, es filtert keine Zeile weg.
  - Ausgenommen sind die Fälle im nächsten Punkt.
- **Keine Saalseite** für „zakk – nicht im zakk“ und für „Auf ins Viertel“ (Treffpunkte, auch wenn einer 20 Events hat).
- **K20 (Grabbeplatz) und K21 (Ständehaus)** sind zwei Standorte, keine Säle. Sie bekommen zwei Seiten, optional mit Eltern-Eintrag „Kunstsammlung NRW“, falls der Auftraggeber eine Dachseite will (Abschnitt 9).

### 3.7 Dubletten (E5)
- **Gleiche Adresse führt nicht automatisch zusammen.**
  - Tanzhaus NRW und Capitol Theater bleiben zwei Häuser.
  - Kunsthalle und Salon des Amateurs bleiben zwei Orte.
  - Gustaf-Gründgens-Platz ist kein Haus.
- **Vor der nächsten Sichtung zusammengeführt** (Schritt 1):
  - Holo Cafe, Holocafe Düsseldorf und Holocafe Immermannstraße 7 werden eine Zeile.
  - La Paillette und La Pailette werden eine Zeile.
- **Getrennt bis zur Prüfung:**
  - Holocafé am Wehrhahn 41
  - Bambi: Es steht mit Ehrenhof 2 in der Liste, der Adresse des NRW-Forums. Das Bambi-Kino liegt an der Klosterstraße. Die Event-Adressen werden vor jedem Zusammenlegen geprüft.

### 3.8 Seiten
- **`/orte/<slug>`** (Haus oder Saal), Aufbau:
  - Kopf: Bild mit Nachweis oder Ersatzkachel, Name, Art, Adresse, Stadtteil, sonst die Stadt aus der PLZ (Neuss, Ratingen), Teilen, Route
  - Nächste Events
  - Langläufer in einem eigenen Block
  - Über den Ort (nur mit freigegebenem Text)
  - Infos: Webseite, Säle
  - Karte
  - Reihen an diesem Ort
  - Orte in der Nähe und gleicher Art
- **`/orte`** (Übersicht):
  - Zum Start A–Z und Suche.
  - **Filter:**
    - **Art:** nur Zeilen mit Art.
    - **Stadt:** Düsseldorf, Neuss, Ratingen, aus der PLZ der bestätigten Adresse.
    - **Stadtteil:** nur Düsseldorfer Zeilen mit Stadtteil. Für Neuss und Ratingen bleibt dieser Filter leer.
  - **Karte:** alle Zeilen mit Koordinaten, unabhängig vom Stadtteil. Neuss und Ratingen erscheinen also auf der Karte.
  - Zeilen ohne bestätigte Adresse haben keine Stadt und keine Koordinaten. Sie stehen nur in A–Z und in der Suche.
  - Säle stehen nicht einzeln in der Übersicht, sondern unter ihrem Haus.
  - **Filter über Query-Parameter** (`/orte?art=…&stadt=…&stadtteil=…`): Die Canonical-URL ist immer `/orte`. Gefilterte Ansichten stehen nicht in der Sitemap.
    - Gefilterte Ansichten bekommen `noindex, follow` **und** Canonical `/orte`, wie auf den Guide-Hubs (Kneipen, Clubs).
    - Beides wird **von Hand** gesetzt, nicht über das `noindex`-Flag von `seitenMetadaten` in `web/lib/seo.ts`. Dieses Flag streicht den Canonical.
    - Es gibt keinen 301 auf eigene Landingpages (anders als `/entdecken`).
  - Verlinkt aus Entdecken und dem Fuß. Stadtteilseiten verlinken auf `/orte?stadtteil=<stadtteil>`.
- **Karte:** das vorhandene MapLibre mit PMTiles (`web/components/guide-karte.tsx`), nicht `GoogleKarte`.
- **„Route“:** ein gewöhnlicher externer Link, kein eingebetteter Google-Rahmen. Der Browser lädt auf der Ortsseite keine Karte und kein Bild von Dritten.
- **Folgen:** Der Button kommt mit B4 im Personalisierungsplan, nicht in diesem Bau.

### 3.9 Eventliste der Ortsseite
- **Nicht `eventPoolLaden()`:** Der Pool reicht nur 60 Tage und zeigt bei Fehlern Beispieldaten.
- **Eigene Abfrage:**
  - über `ort_id` (Haus plus Kinder), alle kommenden Events, `datum_bis` eingeschlossen, `abgelehnt = false`
  - seitenweise (mehr als 1.000 Zeilen möglich)
- **Cache:**
  - **eine** gecachte Funktion je Haus: `use cache`, Schlüssel ist die `ort_id` des Hauses, Ergebnis sind die kommenden Events von Haus und Kindern
  - Saalseiten filtern daraus, statt selbst abzufragen. So fragt kein Seitenaufruf Supabase direkt ab.
  - **Guide-Seiten von Clubs, Kneipen und Restaurants & Cafés** nutzen für „Nächste Events“ dieselbe Funktion mit der `id` ihrer Zeile.
    - **Club-Detailseite:** Der Block „Nächste Events“ ersetzt den heutigen Aufruf `naechsteEvents(ort, pool, 10)` in `web/app/guides/clubs/[slug]/page.tsx`.
    - **Karten** (Club-Übersicht `web/app/guides/clubs/page.tsx` und „Ähnliche Clubs“ auf der Detailseite) zeigen weiter je ein nächstes Event über `naechsteEvents`.
      - Grund: Die Karten brauchen nur ein Event je Club und laden den Pool ohnehin. Eine Abfrage je Karte wäre teurer.
      - `naechsteEvents` (TypeScript) gleicht über das gespeicherte `event_orte` ab und bekommt **keine eigene Filterlogik**. Die Regeln (`nicht_im_ort`, `EVENT_ORTE_AUSSCHLUSS`) liegen nur in Python. Eine Kopie in TypeScript würde auseinanderlaufen.
      - Die gespeicherte Liste enthält „nicht im …“-Namen schon heute nicht. „Theater an der Kö“ verschwindet mit dem Aufräum-SQL in Deploy-Punkt 2b (3.4, Abschnitt 4). Danach zeigt keine Karte eines dieser Events.
    - Damit gibt es eine Programmquelle für alle Detailseiten von Orten, an denen Events stattfinden.
  - **Weihnachtsmärkte und Spielplätze bleiben unverändert.**
    - Die Termine der Märkte kommen aus einer eigenen Logik in `web/lib/weihnachtsmaerkte.ts`: Titel-Abgleich, `event_einschluss.csv`, `event_ausschluss.csv`. Diese ist geprüft und live und wird durch diesen Plan nicht ersetzt.
    - Ihre Zeilen bekommen trotzdem eine `ort_id`-Zuordnung, für B4.
  - `cacheLife` wie in `web/lib/orte.ts`: im Normalfall `NORMAL`, bei Fehler `KURZ`, nach dem Muster `cacheLife(fehler ? KURZ : NORMAL)`. Ein Fehler bleibt also nur kurz im Cache.
- **Bei Fehler:** Hinweis „Programm gerade nicht verfügbar“, **keine Ersatzdaten**. An der Indexierung ändert sich dadurch nichts.
- **Langläufer** (`datum_bis` nach `datum`) stehen in einem eigenen Block über der Liste.
- **Kein Übergang über den Pool.** Die Seiten gehen erst live, wenn der Nachtrag der `ort_id` ausgeführt ist (Deploy-Reihenfolge in Abschnitt 4). Ein Test stellt sicher, dass die Ortsseite `eventPoolLaden` nicht aufruft und Beispieldaten nie erscheinen.

### 3.10 Proxy und URLs (E1)
- **Matcher in `web/proxy.ts`:** `/orte` und `/orte/:slug`. Echte Statuscodes nur dort, **nie `NextResponse.rewrite`**.
- **`/orte`** ist die Übersicht und liefert 200.
- **`/orte/<slug>`:**
  - aktive Spielstätte → 200
  - Guide-Slug → 308 auf die **kanonische** Guide-URL. Ist die Guide-Seite nicht sichtbar, gibt es 404. Ziel je Typ:
    - **Restaurant, Café, Imbiss, Kneipe:** `sichtbarerHub` liefert den Hub. Ziel ist `/guides/<hub>/<slug>`.
    - **Club und Orte mit Bar- und Club-Seite (`auch_club`):** Gilt `hauptSeiteSichtbar`, geht es auf die Hauptseite, sonst auf die Club-Seite (`eigeneClubSeite`, `web/lib/clubs.ts`). Ein Club, der nicht `clubSichtbar` ist, ergibt 404.
    - **Spielplatz und Weihnachtsmarkt:** `sichtbarerHub` schließt beide aus, und `spielplatzEntscheidung` bzw. `weihnachtsmarktEntscheidung` liefern nur „weiter“, keinen Pfad. Das Ziel bildet deshalb `ortPfad()` aus `web/components/ort-karten.tsx` (`/guides/spielplaetze/<slug>`, `/guides/weihnachtsmaerkte/<slug>`), wenn die jeweilige Entscheidung „weiter“ ergibt.
      - `ortPfad()` wird **nur** für diese beiden Typen genutzt. Für alle anderen Typen fällt es auf `/guides/restaurants-cafes` zurück.
    - **`ausflug` und `wochenendtipp`:** kein Ziel. Ihre Hubs sind nicht fertig (`fertig: false` in `web/app/guides/page.tsx`) und haben keine Detailseite. `/orte/<slug>` ergibt 404.
    - **Zusammengelegter Weihnachtsmarkt:** Fehlt die Zeile und steht der Slug in `WM_ZUSAMMENGELEGT`, ist das Ziel `/guides/weihnachtsmaerkte/<verbliebener Slug>`. Es gibt einen einzigen 308, keine Kette über die alte Guide-URL.
    - nie auf eine zweite, nicht kanonische Ansicht
  - unbekannt → zuerst `ort_weiterleitungen`. Bei einem Treffer gibt es einen 308 auf das zur Laufzeit gebildete Ziel (3.3 Punkt 4), sonst eine echte 404 aus dem Proxy.
  - **Netzwerk- oder Datenbankfehler:** wie heute „weiter“. Das ist der Grundsatz in `web/lib/pfad-pruefung.ts`: Nur eine erfolgreiche Abfrage ohne Treffer gilt als „fehlt“.
    - Die Seite unterscheidet wie `orteLaden` in `web/lib/orte.ts` zwischen **Fehler** und **erfolgreich leer**.
    - **Erfolgreich leer:** Hinweis „Ort nicht gefunden“ mit `noindex` und Link auf `/orte`.
    - **Fehler:** Hinweis „Gerade nicht verfügbar“ mit `noindex`. Gecacht mit `cacheLife(KURZ)`, auch die Metadaten, damit ein kurzer Datenbankfehler nicht bis zu einer Stunde einen existierenden Ort verdeckt.
    - keine Ersatzdaten, kein Absturz
- **Bilder** liegen unter `/ort-bilder/orte/<slug>.webp`, nie unter `/orte/…`, weil der Proxy diese Pfade prüft.

### 3.11 SEO
- Eigener Titel je Haus und je Saal, z. B. „<Name> Düsseldorf: Programm & Infos“.
- **Sitemap** (`web/app/sitemap.ts`): Indexierbare Ortsseiten kommen über die eigene Ladefunktion (3.3 Punkt 6) hinein, nicht über `orteLaden()`. `noindex`-Seiten fehlen dort.
- **IndexNow** (`pipeline/indexnow.py` meldet heute nur Event-, Tages- und Startseiten):
  - einmalige Meldung aller indexierbaren Ortsseiten nach Deploy-Punkt 4, als eigener Aufruf (Deploy-Punkt 5)
  - **Danach im täglichen Lauf**, nur wenn `ORTSSEITEN_MELDEN = 1`: jede indexierbare Ortsseite, deren Haus oder Saal in diesem Lauf neue Events bekommen hat.
    - Das läuft analog zu den Tagesseiten in `urls_bauen`.
    - Die Abfrage in `nach_lauf_melden` lädt dafür zusätzlich `ort_id`. Die zugehörigen Ortszeilen (Slug, Typ, `parent_id`, `adresse_bestaetigt`, `text_freigegeben`) kommen einmal je Lauf dazu.
    - **Saal:** Trägt ein neues Event die `ort_id` eines Saals, wird die Saalseite gemeldet. Die Hausseite wird nur mitgemeldet, wenn das Haus eine Spielstätte ist (`/orte/<haus>`).
    - **Guide-Häuser** (z. B. zakk): Die Guide-URL wird **nicht** gemeldet, wie heute. Sie steht in der Sitemap. Die Regeln für die kanonische Guide-URL (`hauptSeiteSichtbar` u. a.) gibt es nur in TypeScript. Eine zweite Fassung in Python wäre eine neue Fehlerquelle.
  - nach einem Slug-Wechsel die neue URL
  - `noindex`-Seiten nie
- **Indexierungsregel an zwei Stellen** (TypeScript für Seite und Sitemap, Python für IndexNow, Regel aus 3.1): Beide Seiten prüfen dieselbe Datei mit Testfällen (`tests/fixtures/ort_indexierbar.json`) in vitest und unittest. So laufen die beiden Fassungen nicht auseinander.
- **JSON-LD nur mit bestätigter Adresse:**
  - Typ je nach Art: `PerformingArtsTheater`, `Museum`, `MusicVenue`, `MovieTheater`, sonst `Place`. Kein `LocalBusiness`.
  - `ItemList` nur mit echten kommenden Events.
  - Saalseiten mit `containedInPlace`.
  - `address` als `PostalAddress`: `streetAddress` und `postalCode` aus der bestätigten Adresse, `addressLocality` ist die **Stadt** aus der PLZ (Düsseldorf, Neuss, Ratingen), nie der Stadtteil.
- Brotkrumen: Startseite → Orte → Name.

### 3.12 Geo und Adresse
- **Kein automatisches Schreiben von Google-Treffern.** Zuerst eine Prüfdatei mit diesen Spalten:
  - Suchbegriff, zurückgegebener Name, Adresse, Koordinaten, `place_id`
  - Adresse laut Website des Hauses, Bestätigung (ja/nein)
- **Nur für Häuser mit `entscheidung = ja`.** Nicht geokodiert werden Säle (sie erben vom Haus, 3.6), Treffpunkte, „nicht im …“, das Büchereinetz und unsichtbare Guides.
- **Kosten:** Sie werden vor dem Lauf anhand der aktuellen Places-SKU genannt.
- **Was gespeichert wird:**
  - Nur die `place_id`, in die vorhandene Spalte `google_place_id`.
  - Google-Koordinaten **nicht** speichern (Google-Bedingungen).
  - Koordinaten kommen aus der bestätigten Adresse über OpenStreetMap Nominatim, mit `httpx`, also ohne neue Bibliothek. Das Ergebnis steht ebenfalls in der Prüfdatei und wird erst nach Bestätigung übernommen.
    - mindestens 2 Sekunden Pause (Projektregel, strenger als Nominatim) und Backoff bei 429
    - User-Agent, der das Projekt erkennbar nennt, wie es Nominatim verlangt (Ausnahme vom Browser-String)
    - `geo_quelle = osm`
    - Hinweis „© OpenStreetMap-Mitwirkende“, den die Karte schon zeigt
- **Koordinaten nur mit Stadt:** Koordinaten werden nur gespeichert, wenn die bestätigte Adresse eine PLZ in den drei Bereichen hat (Düsseldorf, Neuss, Ratingen, wie in `pipeline/gebiet.py`).
  - Fehlt die PLZ in der Event-Adresse (z. B. „Steinstr. 1, Düsseldorf“), trägt die Bestätigung sie von der Website des Hauses nach.
  - Ohne PLZ gibt es keine Koordinaten, also auch keinen Kartenpunkt.
  - So hängen Karte, Stadt-Filter und `addressLocality` an derselben Bedingung.
- **Die Prüfdatei bleibt lokal** (`data/spielstaetten/`, nicht in `.gitignore` freigegeben), weil sie Google-Inhalte enthält. Ins SQL gehen nur die bestätigte Adresse, die `place_id` und die OSM-Koordinaten.
- **Keine Google-Fotos.**
- **Stadtteil:**
  - nur aus der PLZ der bestätigten Adresse über die Tabelle `PLZ_STADTTEIL` in `pipeline/stadtteil_mapper.py`, sonst leer
  - **nicht** über `stadtteil_ermitteln()`, weil diese Funktion zuerst den Ortsnamen auswertet und ein Name den Stadtteil falsch setzen kann
  - Neuss (41460–41472) und Ratingen (40878–40885): kein Stadtteil, weil der Mapper nur `40xxx` aus Düsseldorf kennt. Diese Orte haben keinen Stadtteil-Filter und keine Stadtteilseite.
  - Kopf, Stadt-Filter, Karte und JSON-LD nutzen die Stadt aus der PLZ (3.8, 3.11). Die PLZ-Bereiche sind dieselben wie in `pipeline/gebiet.py`.

### 3.13 Bilder (E4)
- **Bilder der Häuser werden jetzt gespeichert.** Die Freigabe holt der Auftraggeber später, das Risiko trägt er.
- **Neues Skript** `scraper/orte/ortsbilder.py`. Das Weihnachtsmarkt-Skript wird nicht wiederverwendet, weil es ohne Erlaubnis abbricht. Das neue Skript
  - lädt nur die Bild-URL aus `data/spielstaetten/bilder.csv`: mindestens 2 Sekunden Pause, Backoff bei 429, User-Agent nach Projektregel, robots.txt beachtet,
  - entfernt EXIF einschließlich Standort, verkleinert und speichert als WebP unter `/ort-bilder/orte/<slug>.webp`,
  - setzt `erlaubnis = nachtraeglich`.
- **CSV je Bild:** Seiten-URL (Herkunft), Abrufdatum, Nachweis, Link.
- **Nachweis immer sichtbar,** mit Link.
- **Anzeige:**
  - nur über `lokalesBild()`, nie über `ortBildUrl()`, weil diese Funktion auf Google-Fotos zurückfällt
  - `extras.google_foto` wird für `spielstaette` nie gesetzt
  - An den lokalen Pfad kommt dieselbe Versionsangabe wie in `ortBildUrl()` (`web/lib/orte.ts`): `?v=<extras.foto_version>` **nur bei `foto_version > 1`**. Das erste Bild hat keine Angabe. Das Skript erhöht `foto_version` beim Ersetzen, damit ein ersetztes Bild nicht im Cache hängen bleibt.
- **Entfernen:** Zeile und Datei löschen, SQL für `bild_url`, `bild_attribution` und `extras` schreiben, neu bauen.
- **`.gitignore`:** Ausnahmen für `data/spielstaetten/bilder.csv` und `texte.csv`. Die Bilddateien liegen unter `web/public/ort-bilder/orte/`.
- **Ausgeschlossen:** Hotlinking, Bilder von Portalen, Eventbilder als Ortsbild, Google-Fotos.
- **Wikimedia** nur mit Urheber, Lizenz und Quelllink. Ein Zuschnitt eines BY-SA-Bildes steht wieder unter BY-SA.
- **Ohne Datei** zeigt die Seite die Ersatzkachel: Art-Piktogramm, Farbe, Name.

### 3.14 Texte
- **Auftraggeber 20.11.2026:** möglichst **5 bis 10 Sätze**, nur Belegbares, sonst kürzer (mindestens 2). Gegliedert wie die Weihnachtsmärkte: Absätze durch Leerzeile, Schlagwörter **fett** (die Ortsseite zeigt sie, Meta-Description und JSON-LD ohne Sternchen). Werkzeug: `scraper/orte/spielstaetten_texte.py` (Prüfung: eine Quelle je Satz, kein „wir“, Hinweis bei Uhrzeit/Preis/Spielzeit). Bilder: `scraper/orte/ortsbilder.py`.
- Ursprünglich: Zwei bis vier Sätze in `data/spielstaetten/texte.csv`, **jeder Satz mit einer öffentlichen Quellen-URL**.
- Der Auftraggeber gibt sie vor dem Indexieren frei.
- Keine vom Haus übernommenen „wir“-Texte, keine erfundenen Öffnungszeiten, keine erfundene Barrierefreiheit.

### 3.15 Stadtbüchereien (E7)
- **Keine Seite für das Netz** an der Adresse der Zentralbibliothek.
- **Keine Filialseite**, bis der Scraper die Filiale liefert.
- Die **29 Events**, die schon „Zentralbibliothek“ oder „KAP1“ im Namen tragen, können eine Filialseite werden, wenn die Adresse als diese Filiale bestätigt ist.
- **„Xafe in KAP 1 Zentralbibliothek“** ist ein Café im Haus, keine Bibliothek. Die gleiche Adresse ist kein Grund zum Zusammenlegen (7.2 Punkt 12).
- Der Bücherei-Scraper ist ein **eigener Teilschritt** und hält die übrigen Orte nicht auf.
- **Zielfeld des Scrapers:** `ort` bekommt den kanonischen Namen der Filiale, z. B. „Stadtbücherei Benrath“ oder „Zentralbibliothek KAP1“.
  - Die Namen stehen neu in `SPIELSTAETTEN`. Varianten bestehender Schreibweisen gehen nach den beiden Fällen aus 3.5.
  - Jeder Name kommt in `extras.spielstaette.event_orte` der Filialzeile. Darüber setzt die Pipeline die `ort_id`.
  - Die Adresse der Filiale steht in `adresse`.

### 3.16 Gebiet (E3)
- **Bleibt:** nur Düsseldorf, Neuss, Ratingen (`pipeline/gebiet.py`, live seit `884d3fc` und `3ee2de9`).
- **Neu auf der Liste auswärtiger Orte:** Hochdahl, Büderich, Osterath (Vorsorge).
- **Nicht auf die Liste:** Unterbach (Stadtbezirk 8) und Hamm (Stadtbezirk 3), beide Düsseldorfer Stadtteile (`web/lib/stadtteile.ts`).
- **„Mülheim“** wandert aus `STAEDTE_ABSCHNITT` in `STAEDTE_EINDEUTIG` und wird damit als ganzes Wort gefiltert.
  - Grund: „Stadthalle Mülheim“ und „Theater Mülheim“ ohne Komma rutschen heute durch.
  - „Mülheimer Straße“ bleibt drin, weil `\bMülheim\b` dort nicht greift.
  - Die Bestandsbereinigung läuft wie bisher als Datei über `python -m pipeline.gebiet --sql`. Der Auftraggeber führt sie aus.
- **Bleiben drin:** Straßen wie Berliner Allee, Erkrather Straße, Kölner Straße, Duisburger Straße, Neusser Straße, Mülheimer Straße.
- **Tests** in `tests/test_gebiet.py`:
  - draußen: „Stadthalle Mülheim“, Hochdahl, Büderich, Osterath
  - drin: „Mülheimer Straße, 40221 Düsseldorf“, Unterbach, Hamm und die Straßen oben

### 3.17 Bezug zur Personalisierung
B4 „Folgen“ (`docs/konzept-personalisierung-2026-11-18.md`) nutzt `events.ort_id` und die Seiten dieses Plans. Der Button kommt mit B4, nicht in diesem Bau.

## 4. Schritte

| Schritt | Inhalt | Wer |
|---|---|---|
| 0 | Diese Überarbeitung, erneutes Lesen, Cursor-Prüfung, Freigabe | Auftraggeber |
| 1 | **Korrigierte Kandidatenliste**, dann Sichtung durch den Auftraggeber. Inhalt: alle 21 Punkte aus 7.2, darunter eigene Zeilen für die Säle aus der Saalliste (3.6) und für Standorte, Dubletten nach 3.7, Ketten, unsichtbare Guides, das Büchereinetz als „keine Seite“ und die Filiale KAP1 als eigene Zeile. Schon eingetragene Entscheidungen bleiben beim Neuerzeugen erhalten | Claude, Sichtung Auftraggeber |
| 2 | **SQL und Daten** (siehe unten) | Claude schreibt, Auftraggeber führt aus |
| 2a | Bücherei-Scraper mit Filiale (E7), unabhängig, hält nichts auf | Claude |
| 3 | **Seiten und Technik** (siehe unten) | Claude |
| 4 | **Texte und Bilder:** `texte.csv` mit Quellen, Freigabe; `bilder.csv`, `ortsbilder.py` (3.13) | Claude + Auftraggeber |
| 5 | Cursor-Prüfung, Deploy nur nach OK, live `curl -I` auf 200, 308 und 404, IndexNow nur für indexierbare URLs | Claude, Auftraggeber |

**Deploy-Reihenfolge (verbindlich):** Jeder Punkt erst, wenn der vorige erledigt und geprüft ist.
1. **Schema-SQL** ausgeführt: Typ, `parent_id`, `ort_id`, `ort_weiterleitungen` mit RLS, Trigger. Danach der Trigger-Probelauf mit Ergebnis „ok“.
   - Nach Punkt 1 und vor Punkt 2 läuft die **Lese-Prüfung mit `nicht_im_ort`**, lokal aus dem neuen Code (3.4). Sie erwartet 0 Club-Schreibweisen, die nach dieser Regel nicht zum Club gehören. Ist das Ergebnis nicht 0, wird vor Punkt 2 nachgesehen.
   - Es gibt hier **kein Aufräum-SQL für „Theater an der Kö“**. Der noch laufende alte Code (`scores_neu`) würde es sonst noch am selben Tag wieder eintragen. Die Lösung kommt in Punkt 2 und 2b.
2. **Pipeline-Code** deployt: Schritt 1d (Ortszuordnung), 1e (Deduplizierung) mit der Haus-Regel, Gebietsfilter-Nachtrag, das abgesicherte `freischalten`.
   - Ohne die Spalte `ort_id` würde das Speichern scheitern, deshalb muss Punkt 1 vorher erledigt sein.
   - Die IndexNow-Meldung von Ortsseiten ist hier noch **aus**: Schalter `ORTSSEITEN_MELDEN = 0`, eine GitHub-Variable wie `KONTEN_AKTIV`.
   - Mit diesem Code kommen `EVENT_ORTE_AUSSCHLUSS` (mit „Theater an der Kö“ beim Kö-Club), `nicht_im_ort` und das „nur wachsende“ `event_orte` in `clubs_profil.py`. Ab hier vergibt `ort_zuordnen` keine ausgeschlossene Zuordnung mehr, auch wenn die gespeicherte Liste sie noch enthält.

   2b. **Aufräum-SQL** nach dem Deploy von Punkt 2: „Theater an der Kö“ aus dem gespeicherten `event_orte` des Kö-Clubs nehmen. In derselben Datei `ort_id = NULL` für diese Events, auch wenn noch keine gesetzt sein sollte. Danach findet `scores_neu` die Schreibweise nicht wieder, weil sie in der Ausschlussliste steht.
3. **Import** der freigegebenen Zeilen und **Nachtrag** der `ort_id` ausgeführt. Kontrollabfrage: Der zweite Lauf des Nachtrags erzeugt keine Änderung.
4. **Seiten und Proxy** deployt (Schritt 3). Erst ab hier ist `/orte` erreichbar.
5. **IndexNow-Erstmeldung** der indexierbaren Ortsseiten, danach `ORTSSEITEN_MELDEN = 1`. Erst ab hier meldet der tägliche Lauf `/orte/…`.

**Schritt 2 im Einzelnen:**
- SQL für den Typ `spielstaette`, `parent_id`, `ort_id`, `ort_weiterleitungen` und den Schutz-Trigger (3.3 Punkt 8)
- Import nur freigegebener Zeilen, mit `aktiv = true`
- Geo-Prüfdatei (3.12), Kosten vorher nennen
- Namensvarianten nach den beiden Fällen in 3.5, mit Schlüssel-Vergleich vor jedem SQL
- Lösen der falschen Club-Verknüpfungen: „Theater an der Kö“ über `EVENT_ORTE_AUSSCHLUSS` (Code, Deploy-Punkt 2) und Aufräum-SQL (Deploy-Punkt 2b), die übrigen nach Abschnitt 9 (3.2)
- Nachtrag `ort_id` als wiederholbare SQL
- `pipeline/ort_zuordnung.py`, Pipeline-Schritt 1d und Dubletten-Regel nach Häusern in `_ort_passt` (Schritt 1e). `ort_id` in `_ABGLEICH_SPALTEN` und in der Spaltenliste von `dubletten_sql.py` (3.4).
- Lese-Prüfung `--nicht-im-pruefen` mit `nicht_im_ort` (vor Deploy-Punkt 2). „Pitcher, nicht im Freien“ meldet sie nicht. Aufräum-SQL für „Theater an der Kö“ mit ausdrücklichem `UPDATE events SET ort_id = NULL …` (Deploy-Punkt 2b, 3.4)
- In `scraper/orte/clubs_profil.py`:
  - `EVENT_ORTE_AUSSCHLUSS`
  - `nicht_im_ort` als gemeinsame Funktion für `event_orte()` und `ort_zuordnen`
  - `event_orte` nur wachsend in `scores_neu`, `neu_pruefen` und `profile_erstellen`
  - Keine dieser Funktionen leert eine `ort_id` (3.4).
- Kennzahlen `ort_id_ohne_treffer` und `ort_id_mehrdeutig` im Lauf-Bericht, über alle Events mit gesetzter `ort_id`, nicht nur die dieses Scrapers (3.4)
- `freischalten` in `scraper/orte/clubs_profil.py` fängt Trigger-Fehler je Zeile ab (3.3 Punkt 8)
- Gebietsfilter-Nachtrag (3.16): Mülheim, Hochdahl, Büderich, Osterath, dazu die Bereinigungs-SQL

**Schritt 3 im Einzelnen:**
- `/orte`, `/orte/<slug>`, Proxy (Matcher erweitern), Sitemap mit eigener Ladefunktion
- IndexNow-Meldung der indexierbaren Ortsseiten (3.11)
- `.gitignore`-Ausnahmen für `bilder.csv` und `texte.csv`
- ein Ortslink auf der Eventseite
- Links auf `/orte` aus Entdecken, dem Fuß und den Stadtteilseiten (3.8)
- Block „Nächste Events“ auf Guide-Seiten, bei Guide-Häusern mit Sälen mit Saal-Filter (3.6)
- Eventliste über `ort_id` (3.9)
- Tests (unten)

**Pflicht-Tests** (vitest bzw. unittest):
- **Proxy:**
  - 200 für `/orte`
  - 200 für eine aktive Spielstätte
  - 404 für einen unbekannten Slug
  - 308 nur auf die kanonische Guide-URL, 404 bei unsichtbarer Guide-Zeile
  - Ort mit Bar- und Club-Seite: 308 auf die Hauptseite, wenn `hauptSeiteSichtbar` gilt, sonst auf die Club-Seite
  - aktiver Spielplatz: 308 auf `/guides/spielplaetze/<slug>`
  - aktiver Weihnachtsmarkt: 308 auf `/guides/weihnachtsmaerkte/<slug>`
  - zusammengelegter Markt aus `WM_ZUSAMMENGELEGT` (z. B. `schadow-markt-stadtmitte`): ein einziger 308 auf den verbliebenen Markt
  - Slug einer Zeile vom Typ `ausflug` oder `wochenendtipp`: 404, kein 308 auf `/guides/restaurants-cafes`
  - **308 aus `ort_weiterleitungen`**, Ziel zur Laufzeit über `ziel_ort_id`:
    - Ziel ist eine aktive Spielstätte → `/orte/<slug>`, auch nachdem diese umbenannt wurde (neuer Slug, eine Stufe, keine Kette).
    - Ziel ist ein `auch_club`: vor dem Score-Wechsel → Club-Seite, danach → Hauptseite.
    - Ziel unsichtbar, inaktiv, gelöscht oder leer → `/orte`. Nie ein 308 auf eine 404.
  - `/orte/zakk-flingern` (Guide-Haus): 308 auf die Club-Seite. `/orte/zakk` (kein Slug, keine Weiterleitung): 404. `/orte/zakk-flingern-tanzraum` (Saal ohne eigene Seite, keine Zeile): 404.
  - **Weiterleitung, deren Zielabfrage fehlschlägt** (Timeout): „weiter“, kein 308 auf `/orte`.
  - **Netzwerkfehler:** „weiter“.
    - Erfolgreich leer → „Ort nicht gefunden“ mit `noindex`.
    - Abfragefehler → „Gerade nicht verfügbar“ mit `noindex`, gecacht nur mit `KURZ`.
  - kein `rewrite`
- **Verknüpfungen und Säle:**
  - „Theater an der Kö“ leitet nicht auf den Kö-Club.
  - „nicht im zakk“ hat keine Seite und steht nicht auf der zakk-Seite.
  - K20 und K21 sind zwei Seiten.
  - Events eines Saals erscheinen nicht auf einem anderen Haus.
  - Die Hausseite zeigt die Kinder.
  - Der Saal-Filter gruppiert nach der Saalliste. Events ohne erkennbaren Saal stehen unter „Haus allgemein“.
  - Eine Saalseite eines Guide-Hauses verweist im JSON-LD (`containedInPlace`) auf die kanonische Guide-URL.
  - **Club-Seite des zakk:**
    - „Nächste Events“ kommt aus der `ort_id`-Abfrage, nicht aus `naechsteEvents` oder dem Pool.
    - „nicht im zakk“ erscheint nicht.
    - Der Saal-Filter zeigt die Säle aus der Saalliste.
  - **Saal-Slug:** Er entsteht aus dem gespeicherten Haus-Slug, z. B. `zakk-flingern-halle`.
- **Daten:**
  - Der Nachtrag von `ort_id` ist wiederholbar und erzeugt beim zweiten Lauf keine Änderung.
  - Der Import lehnt eine leere Entscheidung, „Sonstiges“ und eine fehlende korrigierte Art ab. Er setzt `aktiv = true`.
  - Der Import lehnt ab: einen schon vergebenen Slug, einen Slug aus `ort_weiterleitungen.alter_slug` und eine Saalzeile ohne `parent_id`.
  - **Pipeline und Nachtrag** ordnen für dieselben Events gleich zu (gemeinsame Funktion `ort_zuordnen`).
  - **`ort_id` beim Zusammenführen:**
    - Rausgegangen „zakk – Halle“ (Treffer) und Veranstalter-Schreibweise ohne Treffer → die Saal-ID bleibt, auch wenn der Veranstaltername gewinnt.
    - Ein automatischer Lauf schreibt nie `NULL` über eine vorhandene `ort_id`.
    - Das ausdrückliche Lösungs-SQL setzt sie auf `NULL`, und der nächste Nachtrag setzt sie nicht wieder.
  - **`nicht_im_ort`** (dieselben Fälle in `clubs_profil` und `ort_zuordnen`):
    - „zakk – nicht im zakk“ gehört nicht zum zakk und bekommt keine `ort_id`, auch wenn der Name in einem `event_orte` stünde.
    - „Pitcher, nicht im Freien“ gehört zum Pitcher.
    - „nicht im Saal, sondern im Pitcher Club“ gehört zum Pitcher.
  - **`EVENT_ORTE_AUSSCHLUSS`:**
    - „Theater an der Kö“ bekommt nie die ID des Kö-Clubs, auch solange es noch im gespeicherten `event_orte` steht.
    - `scores_neu` trägt es nicht wieder ein.
  - **`event_orte` wächst nur:**
    - Eine gespeicherte Schreibweise ohne Event in den letzten 180 Tagen bleibt nach `scores_neu` in der Liste.
    - Die `ort_id` ihrer Events bleibt unverändert.
    - Kein Lauf von `clubs_profil` schreibt `NULL` in `events.ort_id`.
  - **Kennzahlen:**
    - Gespeicherte `ort_id` ohne Treffer: unverändert, mit Log-Zeile, `ort_id_ohne_treffer` + 1.
    - Bei mehreren Treffern: unverändert, `ort_id_mehrdeutig` + 1.
    - Geprüft wird auch ein Event, das in diesem Scraper nicht vorkommt.
  - **Zusammenlegen** (Probe-SQL): `/orte/central` zeigte auf die alte Zeile. Nach dem Zusammenlegen zeigt der Eintrag auf das verbleibende Haus, und der Proxy leitet dorthin, nicht auf `/orte`.
  - **`_ort_passt` ohne Haus-Zuordnung** (z. B. aus `rausgegangen_nachziehen.py`) entscheidet wie heute über den Namen und schließt nie „verschiedene Orte“ aus verschiedenen IDs.
  - **`freischalten`:** Ein Club mit aktivem Saal, der abgeschaltet werden soll, landet im Log. Der Lauf macht mit dem nächsten Club weiter.
  - Importskripte der Guides lassen Zeilen vom Typ `spielstaette` unverändert.
  - **Kette:** Ein Event mit Starbucks-Namen und anderer Adresse als die `orte`-Zeile bekommt keine `ort_id`. Mit passender Adresse bekommt es sie.
  - **Entscheidungen beim Neuerzeugen:**
    - Eine Entscheidung auf `Holo Cafe` steht nach dem Zusammenführen an der einen verbleibenden Holo-Zeile.
    - Zwei widersprüchliche Entscheidungen ergeben „Entscheidung prüfen“.
  - **Reihen-Schlüssel:** Vor und nach dem Namens-SQL sind sie gleich (3.5). Eine Schreibweise, die einen Schlüssel ändern würde, landet in `event_orte`, nicht in `SPIELSTAETTEN`.
  - **Schutz-Trigger** (Probelauf-Datei mit `BEGIN` … `ROLLBACK`, legt die Test-Spielstätte selbst an, 3.3 Punkt 8):
    - Löschen, Abschalten, Slug-Wechsel und Typwechsel weg von `spielstaette` ohne Weiterleitung brechen ab.
    - Mit Weiterleitung klappt jeder der vier Fälle.
    - Löschen eines Hauses mit aktiven Kindern bricht ab. Das gilt für eine Spielstätte und für eine Guide-Zeile. Die Test-Säle sind ausdrücklich `aktiv = true`.
    - Eine Guide-Zeile ohne Kinder lässt sich wie bisher ändern und löschen.
    - Löschen oder Abschalten einer Zeile, auf die noch ein Eintrag in `ort_weiterleitungen` zeigt, bricht ab. Das gilt für Spielstätte und Guide-Zeile. Nach dem Umhängen der Einträge klappt es.
  - **Dubletten:**
    - Das zakk-Paar aus `deduplication.py` mit zwei Sälen desselben Hauses wird zusammengelegt.
    - Zwei Events mit `ort_id` verschiedener Häuser, gleichem Titel und gleicher Zeit werden nicht zusammengelegt.
    - Starbucks mit Ketten-ID und Starbucks Schadowstraße ohne ID, mit gleichem Titel und gleicher Zeit, aber anderer Adresse, werden nicht zusammengelegt.
    - Dieselben Fälle gelten im Abgleich mit dem Tagesbestand (`database/client.py`), nicht nur in `deduplizieren`.
  - **Säle:**
    - Der Import lehnt eine Saalzeile ohne `parent_id` ab.
    - Die Kandidatenliste erzeugt für „PubCrawl Düsseldorf - das Original! seit 2008!“ keine Saalzeile.
  - **Google-Fotos:** Kein Pipeline- oder Importpfad setzt `extras.google_foto` bei `typ = 'spielstaette'`. Geprüft wird das am Import- und am Bildskript.
  - **Kandidatenliste:** Für die Punkte 1, 4, 12, 16, 17, 18, 19 und 21 aus 7.2 stimmt der Vorschlag oder die Art. Dazu gehören Pfarrzentrum (Kirche), Billardzentrum (Sport), Kulturhaus Süd, Klanghaus und Gerhart Hauptmann Haus (Kultur-/Bürgerzentrum).
- **Seiten:**
  - Die Ortsseite ruft `eventPoolLaden` nicht auf. Beispieldaten erscheinen nie.
  - `noindex`-Seiten fehlen in der Sitemap und bei IndexNow. Indexierbare Ortsseiten sind in beiden enthalten.
  - Die Indexierungsregel in TypeScript und in Python liefert für alle Fälle aus `tests/fixtures/ort_indexierbar.json` dasselbe Ergebnis.
  - **IndexNow:**
    - Es meldet eine indexierbare Ortsseite, deren Haus neue Events bekommen hat. Eine `noindex`-Seite meldet es nicht.
    - Ein neues Saal-Event meldet Saal- und Hausseite, wenn das Haus eine Spielstätte ist.
    - Ein neues Event in einem Saal des zakk meldet nur die Saalseite, keine `/guides/…`-URL und nicht `/orte/zakk-flingern`.
    - Mit `ORTSSEITEN_MELDEN = 0` meldet es keine `/orte`-URL.
  - **`/orte?stadtteil=…`:** `noindex, follow` und Canonical `/orte`, beides zugleich in den Metadaten. Es gibt keinen 301.
  - Eine Spielstätte ohne lokales Bild zeigt die Ersatzkachel, nie `/ort-foto/…` und kein Google-Foto.
  - Mit lokalem Bild und `foto_version` 2 trägt der Pfad `?v=2`. Mit `foto_version` 1 oder ohne Angabe hat er keine Query, wie bei `ortBildUrl()`.
  - Eine Spielstätte in Neuss mit Koordinaten und ohne Stadtteil erscheint auf der Karte und im Stadt-Filter. Ihr JSON-LD hat `addressLocality` „Neuss“.
  - Eine bestätigte Adresse ohne PLZ in den drei Bereichen ergibt keine Koordinaten. Die Übernahme aus der Geo-Prüfdatei lehnt sie ab.
  - Bei Fehler der Eventabfrage erscheint der Hinweis „Programm gerade nicht verfügbar“, das Ergebnis wird mit `KURZ` gecacht.
- **Gebietsfilter:**
  - „Stadthalle Mülheim“, Hochdahl, Büderich und Osterath fliegen raus.
  - „Mülheimer Straße, 40221 Düsseldorf“, Unterbach, Hamm und die Straßenfälle aus 3.16 bleiben drin.

## 5. Entscheidungen des Auftraggebers (18.11.2026, verbindlich)
- **E1 URL:** `/orte/<slug>`, eine URL je Ort (3.2, 3.10). Für SEO ist das Wort im Pfad praktisch egal, `/orte` passt zur deutschen Seite.
- **E2 Schwelle:** Kandidaten ab 2 Events (12 Monate + kommend). Veröffentlichen und Indexieren nach 3.1.
- **E3 Gebiet:** nur Düsseldorf, Neuss, Ratingen, konsequent gefiltert (3.16, Abschnitt 6).
- **E4 Bilder:** direkt vom Haus bzw. Veranstalter, die Freigabe holt der Auftraggeber nachträglich, das Risiko trägt er (3.13).
- **E5 Datenmodell:** Typ `spielstaette` in `orte`, `events.ort_id`, gute Dubletten-Erkennung (3.3, 3.4, 3.7).
- **E6 Säle:** Seite je Haus mit Filter. Große oder viel bespielte Säle bekommen zusätzlich eine eigene Seite, je Zeile freigegeben (3.6).
- **E7 Stadtbüchereien:** je Filiale, sobald der Scraper sie liefert (3.15).

## 6. Korrekturen der Datenfehler (ERLEDIGT, live seit `884d3fc` und `3ee2de9`)
- **Gebietsfilter** `pipeline/gebiet.py` (Schritt 1c in `main.py`): PLZ, andere Städte, bekannte auswärtige Orte.
- **Bestand bereinigt:** 348 + 26 Events gelöscht (`database/gebiet_bereinigung_2026-11-18.sql`, `…_2.sql`, beide ausgeführt).
- **Oper am Rhein:** Die Opern-Adresse gilt nur noch für das Opernhaus. Meetup-Platzhalter („meetup9“) entfernt. Kulturschlachthof R25: Rather Straße 25, Derendorf. `database/datenfehler_2026-11-18.sql` ist ausgeführt.
- **Namensvarianten** (R25, Roncalli's, Rudas, Rundum Yoga, Metropol, Drachental, Salon des Amateurs). FFT-Säle als „FFT Düsseldorf – Bühne I/II“. `database/ortsnamen_2026-11-18.sql` und `…_2.sql` sind ausgeführt.

## 7. Kandidatenliste: aktueller Stand (19.11.2026, NICHT freigegeben)

### 7.1 Stand der Datei
**Datei:** `data/spielstaetten/kandidaten.csv`, erzeugt am 18.11.2026 von `python -m scraper.orte.spielstaetten_kandidaten`, nach dem Gebietsfilter. Sie enthält 354 Häuser mit ≥ 2 Events.

| Vorschlag | Anzahl |
|---|---|
| neue Ortsseite | 236 (144 ohne Adresse, 156 ohne Stadtteil, 114 ohne kommendes Event, 99 Art „Sonstiges“) |
| Guide- oder Club-Seite vorhanden | 33 |
| keine Seite: Treffpunkt / allgemein / online / Gruppe | 42 / 21 / 14 / 8 |

**Diese Fassung wird vor der Sichtung durch Schritt 1 ersetzt.** Die Spalte `vorschlag` ist keine Freigabe.

### 7.2 Bekannte Fehler, die Schritt 1 behebt
1. **„Hansaallee 190“ wird als Ort eingestuft.** Das Muster „saal“ steckt in „Hansaallee“, damit greift die Straßen-Ausnahme. Abhilfe: Ortswörter nur als ganzes Wort.
2. **„Marktplatz Düsseldorf“ wird als Ort eingestuft,** weil „platz“ nicht am Ende steht. Abhilfe: Straßen- und Platzwörter auch vor „Düsseldorf“ erkennen.
3. **„Tourist-Information - Visit Düsseldorf“** (30 Events) ist ein Treffpunkt von Führungen.
4. **„S- und U-Bahnhof Flingern“** bekommt die Art „Oper/Theater“, weil „flin“ in „Flingern“ steckt. Abhilfe: `\bflin\b`.
5. **„Franklinstraße Turnhalle“** braucht eine Art (Sport). Der Name allein ist kein Grund für „Sonstiges“.
6. **Die Art-Muster „haus“ und „forum“ sind zu weit.** Abhilfe: nur gezielte Wörter wie „Bürgerhaus“ oder „Gemeindehaus“.
7. **„Sonstiges“ darf nicht importiert werden** (3.1).
8. **Säle und Standorte:** Jeder Saal aus der Saalliste (3.6) bekommt eine eigene Entscheidungszeile in der CSV. Eine `orte`-Zeile entsteht erst nach Freigabe. K20 und K21 werden zwei Zeilen. Für „zakk – nicht im zakk“ und „Auf ins Viertel“ gibt es keinen Saalvorschlag.
9. **Dubletten nach 3.7** zusammenführen (Holo, La Paillette). Bambi und Holocafé Wehrhahn bekommen einen Prüfhinweis.
10. **Weitere Fälle mit „keine Seite“:**
    - Ketten, auch einzelne Filialzeilen wie `Starbucks Reserve` (Z. 108) und `Starbucks Schadowstr` (Z. 227) neben der unsichtbaren Zeile `Starbucks` (Z. 107)
    - die 14 unsichtbaren Guide-Zeilen (mit Hinweis „ort_id ja, keine Seite“). In der Datei heißt eine davon `CADO Kaffeebar` (Z. 186).
    - das Büchereinetz als Ganzes („Stadtbüchereien Düsseldorf“, Z. 3). Ausnahme: Punkt 20.
    - Gustaf-Gründgens-Platz
11. **Schon eingetragene Entscheidungen** bleiben beim Neuerzeugen erhalten.
    - Zusammenführung über den normalisierten Namen.
    - Werden nach 3.7 mehrere Zeilen zu einer, wandern ihre Entscheidungen auf die verbleibende Zeile. Widersprechen sie sich, wird die Zeile mit dem Hinweis „Entscheidung prüfen“ markiert und leer gelassen.

**Von Cursor am 19.11. zusätzlich gefunden** (Zeilennummern der heutigen Datei):

12. **`Xafe in KAP 1 Zentralbibliothek`** (Z. 171) steht als „Bibliothek/Bildung“, weil „Zentralbibliothek“ früher greift.
    - Soll: Art Café.
    - keine Bibliotheksseite
    - Hinweis „gleiche Adresse wie Zentralbibliothek, nicht zusammenlegen“
    - Abhilfe: Café-Wörter (Café, Cafe, Xafe, Kaffeebar) vor Bibliothek prüfen.
13. **`Bambi Filmstudio`** (Z. 179, ohne Adresse) ist die zweite Bambi-Zeile neben `Bambi` (Z. 178, Ehrenhof 2).
    - Soll: beide mit Prüfhinweis „Dublette? Adresse Klosterstraße prüfen“.
    - Kein Zusammenlegen vor der Adressprüfung (3.7).
14. **Starbucks-Filialen:** siehe Punkt 10. Soll: „keine Seite (Kette)“.
    - Abhilfe: Kettennamen als Wortanfang erkennen, nicht nur als ganzen Namen.
15. **`Alter Bahnhof Oberkassel`** (Z. 176) ist ein Lokal in einem alten Bahnhofsgebäude, kein Treffpunkt.
    - „Bahnhof“ kommt deshalb **nicht** pauschal ins Treffpunkt-Muster, das weicht von Cursor ab.
    - Soll: „neue Ortsseite“ mit Prüfhinweis „Art und Adresse prüfen“. Die Art setzt der Auftraggeber.
16. **`Kloster Flingern`** (Z. 131) hat die Art „Oper/Theater“, weil „flin“ in „Flingern“ steckt.
    - Soll: Art Kirche/Kloster.
    - Die Korrektur `\bflin\b` (Punkt 4) heilt die falsche Art. Das Kirchen-Muster muss „Kloster“ und „Kirche“ dann erkennen.
17. **`Interimmuseum Hansaallee 190`** (Z. 158) ist ein Museum und bleibt „neue Ortsseite“.
    - Die Straßen-Korrektur aus Punkt 1 gilt nur für den Namen `Hansaallee 190` (Z. 49), nicht für Namen, die die Straße enthalten.
    - Ein Test hält beide Zeilen fest.
18. **`Rathaus Düsseldorf`** (Z. 218) hat die Art „Kultur-/Bürgerzentrum“, weil „haus“ in „Rathaus“ steckt.
    - Soll: eigene Art „Öffentliches Gebäude“. Die Art setzt der Auftraggeber.
    - **`Pfarrzentrum Heerdt`** (Z. 217) hat aus demselben Grund die falsche Art, hier über „zentrum“. Soll: Kirche/Gemeinde.
    - **Abhilfe:**
      - „zentrum“ wird wie „haus“ und „forum“ nur in gezielten Wörtern erkannt. Für Kultur-/Bürgerzentrum sind das Kulturzentrum, Bürgerzentrum, Stadtteilzentrum, Bürgerhaus, Gemeindehaus, **Kulturhaus** und **Klanghaus**.
      - **`pfarr`** kommt ins Kirchen-Muster (heute: kirche, gemeinde, basilika, kloster, synagoge, moschee, maxhaus). Ohne das fiele das Pfarrzentrum nach der Engführung auf „Sonstiges“.
      - Ein **Sport**-Muster bekommt `billard`, `turnhalle`, `sporthalle`. Damit geht `Billardzentrum` (Z. 145) nach Sport, und Punkt 5 ist mit erledigt.
      - **Ausdrückliche Art** über eine kleine Namensliste im Skript, für Häuser, deren Name kein Art-Wort trägt. Die Art ist ein Vorschlag, der Auftraggeber bestätigt sie in der Sichtung über `art_korrigiert`.

        | Zeile | Name | vorgeschlagene Art |
        |---|---|---|
        | 21 | Gerhart Hauptmann Haus | Kultur-/Bürgerzentrum |
        | 23 | zentrum plus Holthausen | Kultur-/Bürgerzentrum |
        | 26 | EKŌ-Haus der Japanischen Kultur | Kultur-/Bürgerzentrum |
        | 65 | Haus Spilles | Kultur-/Bürgerzentrum, Prüfhinweis „Art prüfen“ |
        | 89 | Rigpa Zentrum Düsseldorf | Kirche/Gemeinde (buddhistisches Zentrum), Prüfhinweis „Art prüfen“ |
        | 155 | Heine Haus Literaturhaus Düsseldorf | Kultur-/Bürgerzentrum, zusätzlich `literaturhaus` als Art-Wort |
        | 177 | ASG-Bildungsforum Düsseldorf | Bibliothek/Bildung |
        | 216 | Nilsson, Initiativen Haus | Kultur-/Bürgerzentrum |
    - **Nach der Änderung zu prüfen:**
      - `Kulturhaus Süd / Freizeitstätte Garath` (Z. 161) und `Klanghaus` (Z. 130) bleiben Kultur-/Bürgerzentrum.
      - `Rathaus Düsseldorf` fällt nicht mehr darunter.
19. **`FFT Düsseldorf – Bühne I`** (19 Events, Z. 10) hat heute keine Entscheidungszeile, nur Bühne II mit 22.
    - Soll: beide Bühnen als eigene Zeilen nach 3.6.
    - Die Grenze 20 setzt nur den Hinweis.
20. **`Zentralbibliothek KAP1`** (29 Events, in Z. 3 unter dem Büchereinetz)
    - Soll: eigene Entscheidungszeile „Filiale Zentralbibliothek“ nach 3.15, mit Hinweis „Adresse bestätigen“.
    - Das Netz als Ganzes bleibt „keine Seite“.

**Von Cursor in der dritten Runde gefunden:**

21. **Schein-Säle durch den Trenner:** Säle kommen nur aus der Saalliste je Haus (3.6).
    - `PubCrawl Düsseldorf - das Original! seit 2008!` (Z. 140, 2 Events) ist eine Schreibweise von PubCrawl, kein Saal.
    - Bei der Bücherei bleiben „Zentralbibliothek Düsseldorf / Stadtfenster“ (3 Events) und ähnliche Teile Schreibweisen. Die einzige Bücherei-Zeile außer dem Netz ist KAP1 (Punkt 20), bis der Scraper Filialen liefert.
    - Herzkammer ist ebenfalls kein Saal.
    - Ein Test hält PubCrawl als Fall ohne Saalzeile fest.

## 8. Alte offene Fragen der ersten Fassung: ERLEDIGT
Die Fragen der ersten Fassung sind durch E1–E7 (Abschnitt 5) beantwortet.

## 9. Offene Einzelentscheidungen für den Auftraggeber
- **Stone im Ratinger Hof:** eigener Ort oder Saal des Ratinger Hofs? Heute ist er dem Club Ratinger Hof zugeordnet.
- **Bilker Bunker und Schleuse Zwei** (beide Aachener Str. 39): ein Haus mit Bereich, oder zwei Orte? Heute ist Schleuse Zwei ein Club, der Bunker ein Kandidat.
- **Theater an der Kö:** eigene Ortsseite? Die Verknüpfung mit dem Kö-Club wird in jedem Fall gelöst.
- **Kunstsammlung NRW:** Dachseite über K20 und K21 ja oder nein?
- **Saalseiten:** Entscheidung je Zeile in der CSV, für jeden Saal aus der Saalliste ab 2 Events (3.6). Die Saalliste selbst sieht der Auftraggeber in Schritt 1 mit durch. Kandidaten sind unter anderem Großes Haus, Kleines Haus, Central 1, Central 2, Central Brücke, Bühne I/II des FFT, Mendelssohn-Saal und Black Box.
- **Art für Rathaus und Alter Bahnhof Oberkassel** (7.2 Punkte 15 und 18): Bleibt es bei „Öffentliches Gebäude“ bzw. „Gastronomie/Eventlocation“, oder will der Auftraggeber andere Arten?
- **Folgepunkt außerhalb dieses Plans:** Abgeschaltete Spielplätze und Weihnachtsmärkte enden heute als 404, weil der Proxy inaktive Zeilen nicht lesen kann (Änderungsprotokoll, Punkt 1). Die Lösung wäre dieselbe Tabelle `ort_weiterleitungen`.
