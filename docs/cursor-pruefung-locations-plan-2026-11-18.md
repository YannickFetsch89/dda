# Cursor-Prompt: Prüfung des Plans „Ortsseiten“, zehnte Fassung (19.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD, Branch `claude/setup-project-structure-5QNOf`).

---

Du prüfst die **zehnte Fassung eines Plans** für die Website dies.das.düsseldorf (diesdas.events). Umgesetzt ist davon noch nichts.

**Ändere keine Dateien und keine Datenbank. Schreib nur einen Befundbericht.**

Die neunte Fassung hat Claude selbst geprüft, am Code und mit einer Lese-Abfrage in der Datenbank. Daraus kamen vier Änderungen. Sie stehen ganz oben im Änderungsprotokoll der zehnten Fassung:

1. **`event_orte` der Clubs wächst nur.** Grund: `scores_neu` schreibt die Liste bei jedem Pipeline-Lauf aus den Events der letzten 180 Tage neu. `clubs_profil` leert nie eine `ort_id`.
2. **Ausschlussliste `EVENT_ORTE_AUSSCHLUSS` im Code.** Sonst würde `scores_neu` eine per SQL gelöste Schreibweise („Theater an der Kö“) noch am selben Tag wieder eintragen. Das Aufräum-SQL läuft erst nach dem Code-Deploy (Deploy-Punkt 2b).
3. **„zakk – nicht im zakk“ steht laut Datenbank nicht in `event_orte`.** `event_orte()` schließt es schon aus. Die Regel wandert in eine gemeinsame Funktion `nicht_im_ort` für `clubs_profil` und `ort_zuordnen`, ohne pauschales „enthält ‚nicht im‘“.
4. **Zwei Kennzahlen:** `ort_id_ohne_treffer` und `ort_id_mehrdeutig`.

Prüfe vor allem diese vier Punkte: Sind sie vollständig, widerspruchsfrei und mit dem Code vereinbar? Haben sie neue Fehler eingeführt?

## Was du lesen sollst
1. **Den Plan:** `docs/plan-locations-2026-11-18.md`
   - Änderungsprotokoll der zehnten Fassung
   - Abschnitt 3.2 (Club-Verknüpfungen), 3.4, 3.9 (Club-Karten)
   - Abschnitt 4 (Deploy-Reihenfolge mit Punkt 2b, Schritt 2, Pflicht-Tests)
   - Ältere Protokolle beschreiben nur den Stand ihrer Fassung.
2. **Code:**
   - `scraper/orte/clubs_profil.py`: `event_orte`, `kalender_laden`, `_events_fuer`, `scores_neu`, `neu_pruefen`, `profile_erstellen`, `manuell_korrigieren`, `NICHT_IM_HUB`, `speichern`/`extras_mergen`
   - `main.py`: Aufruf von `scores_neu`, Reihenfolge zum Speichern
   - `web/lib/clubs-daten.ts`: `naechsteEvents`
   - `web/lib/clubs.ts`: `clubProfil`, `eventOrte`

## Regeln des Projekts (Verstöße sind Befunde)
- **Eine URL je Ort.** Echte 404 und 308 nur im Proxy, **nie `NextResponse.rewrite`**.
- **Der Proxy liest mit dem anonymen Schlüssel** und sieht nur `aktiv = true`.
- SQL nur als Datei in `database/`. Abfragen seitenweise.
- Keine neue Bibliothek ohne Rückfrage. Deutsch.

## Worauf du besonders achten sollst
1. **Nur wachsendes `event_orte`:**
   - Gibt es heute einen Fall, in dem eine Schreibweise gewollt aus der Liste fallen muss und künftig nicht mehr fällt, etwa eine Fehlzuordnung durch einen Teiltreffer?
   - Ist die Ausschlussliste dafür der richtige und einzige Weg?
   - Wächst die Liste unbegrenzt? Ist das ein Problem für den Club-Score, der `_events_fuer` nutzt?
2. **Ausschlussliste und Deploy-Punkt 2/2b:**
   - Ist die Reihenfolge lückenlos: alter Code läuft bis Punkt 2, ab dann ordnet `ort_zuordnen` keine ausgeschlossene Schreibweise mehr zu, und 2b räumt die gespeicherte Liste auf?
   - Kann zwischen 2 und 2b eine falsche `ort_id` entstehen?
3. **`nicht_im_ort`:**
   - Lässt sich die Prüfung aus `event_orte()` so herauslösen, dass `ort_zuordnen` sie mit den Hausnamen der Kandidatenzeile nutzen kann?
   - Stimmen die drei Testfälle (zakk, Pitcher im Freien, „sondern im Pitcher Club“)?
4. **Club-Karten ohne eigene Filterlogik in TypeScript:** Ist es vertretbar, dass sie sich nur auf die gespeicherte, bereinigte Liste verlassen?
5. **Kennzahlen:** Steigen sie jetzt wirklich nicht mehr von selbst?
6. **Widersprüche** zwischen dem Änderungsprotokoll, Abschnitt 3 und Abschnitt 4.

## Bericht
Zuerst eine Tabelle mit den 4 Punkten: Bezeichnung, Urteil (**behoben** / **teilweise** / **nicht behoben**), Fundstelle.

Danach neue Befunde, sortiert nach Schwere (**kritisch / hoch / mittel / gering / Hinweis**). Je Befund:
- Ort
- was falsch ist, mit einem konkreten Beispiel
- warum es ein Problem ist
- Vorschlag

Am Ende: eine Gesamteinschätzung, ob der Plan freigabereif ist.
