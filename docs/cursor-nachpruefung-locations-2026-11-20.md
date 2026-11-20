# Cursor-Prompt: Nachprüfung der Befunde „Ortsseiten“ (20.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD, Branch `claude/setup-project-structure-5QNOf`).

---

Du hast heute die Ortsseiten komplett geprüft: Schritte 1, 2, 2a und 3 des Plans `docs/plan-locations-2026-11-18.md`. Den Prompt findest du in `docs/cursor-pruefung-locations-komplett-2026-11-20.md`. Deine Befunde 1 bis 7 sind im Commit **`60d9903`** behoben. Prüf jetzt, ob die Behebung stimmt und nichts Neues kaputtgegangen ist.

**Ändere keine Dateien und keine Datenbank. Schreib nur einen Befundbericht.**

## Stand
- **Nicht gepusht:** `60d9903` liegt lokal über `2d22e6c` (Schritt 2a), `42a8cd3` und `b602a1a` (Schritt 3).
- **Ebenfalls lokal:** `4f3b396` aus einer anderen Sitzung (Mein dies.das: Ziel nach der Anmeldung `/konto`). Er geht mit demselben Deploy live. Prüf ihn nur darauf, ob er mit den Ortsseiten kollidiert.
- **Ausgeführt hat der Auftraggeber:**
  - `database/orte_spielstaetten_geo_2026-11-20_2.sql`: 202 bestätigte Adressen, alle mit Koordinaten
  - `database/stadtbuechereien_filialen_2026-11-20.sql`: 175 Events in Filialen, 8 bleiben „Stadtbüchereien Düsseldorf“

## Was zu prüfen ist (`git show 60d9903`)

**Befund 1, Säle von Guide-Häusern in der Übersicht**
- **Dateien:**
  - `web/lib/spielstaetten-daten.ts`: `guideHaeuserLaden`, `uebersichtEintraege`, `fremdeHausIds`, `guideArt`
  - `web/app/orte/page.tsx`
- **Fragen:**
  - Stehen die zakk-Säle unter „zakk“ mit Link auf `/guides/clubs/zakk-flingern`?
  - Steht ein Saal mit unsichtbarem oder nicht ladbarem Haus selbst in der Liste?
  - Wie wirken die Filter (Art, Stadt, Stadtteil, Suche) auf die Guide-Häuser?
  - Zählt „N Orte“ jetzt richtig?
  - Fehlen die Guide-Häuser bewusst auf der Karte (`/api/guide-karte?hub=orte`)?
  - Kann ein Guide-Haus doppelt erscheinen, als Eintrag und als eigene Spielstätte?
  - Ist die Sortierung (jetzt `localeCompare` statt Datenbank-Reihenfolge) dieselbe wie die A–Z-Gruppen?

**Befund 2, Fehler der Saalliste**
- **Datei:** `web/app/orte/[slug]/page.tsx`, `Stand.listeFehler`
- **Fragen:**
  - Zeigt die Seite bei einem Fehler von `spielstaettenLaden` „Programm gerade nicht verfügbar“?
  - Setzt `generateMetadata` dann `noindex`?
  - Bleibt der Fehler nur kurz im Cache?
  - Was passiert, wenn `ortZeileLaden` für das Haus eines Saals scheitert?

**Befund 3, Saal-Filter auf Guide-Seiten**
- **Dateien:** `web/components/ort-programm.tsx`, `web/components/saal-filter.tsx` (neu, Client Component)
- **Fragen:**
  - Stimmen die Gruppen: „Alle“, je Saal mit Link auf die Saalseite, „Haus allgemein“ nur mit Haus-Events?
  - Die Listen rendert der Server vorab, der Client schaltet nur um. Ist das bei vielen Sälen zu viel HTML (zakk: 6 Säle × 10 Karten)?
  - Bedienbarkeit: `aria-pressed`, Tastatur, Rolle der Gruppe
  - Was sieht man ohne JavaScript?
  - Ein Saal ohne kommende Events: Erscheint sein Button trotzdem? Ist das gewollt?
  - Weicht das vom Saal-Filter der Ortsseite ab, die mit `?saal=` arbeitet? Ist die Abweichung vertretbar? Die Guide-Seiten sollen statisch bleiben.

**Befund 4, Cache des Ortslinks**
- **Datei:** `web/lib/spielstaetten-daten.ts`, `ortZeileAbfragen`, `ortZeileLaden`, `eventOrtLink`
- **Fragen:**
  - Ein Fehler wird nur `KURZ` gecacht, ein erfolgreiches „nicht da“ `NORMAL`. Stimmt das an allen Aufrufstellen von `ortZeileLaden`, auch in der Sitemap und auf der Ortsseite?
  - Übernimmt bei verschachteltem `"use cache"` der äußere Eintrag das kürzere Leben des inneren?

**Befund 5:** „Filiale von“ in `web/app/orte/[slug]/page.tsx`.

**Befund 6, HTTP 429**
- **Datei:** `scraper/utils/http_client.py`, `_backoff`, `seite_abrufen`
- **Fragen:**
  - Die Datei gilt für **alle** Scraper. Kann die Wartezeit (bis zu 120 s je Versuch, höchstens 3 Versuche) einen täglichen Lauf über das CI-Timeout von 75 Minuten treiben?
  - Wird `Retry-After` als Datum richtig behandelt?
  - Test: `tests/test_http_client_429.py`

**Befund 7, Tests**
- **Datei:** `web/tests/ortsseiten.test.ts`, Block „Cursor-Komplettprüfung 20.11.“
- **Fragen:**
  - Prüft der Timeout-Test wirklich den Pfad über `spielstaettePruefen` (gemockter `fetch`, Umgebungsvariablen)?
  - Stellt er den Zustand danach sauber wieder her (`speicherLeeren`, Umgebungsvariablen, `unstubAllGlobals`)?
  - Prüfen die neuen Tests, was ihr Name sagt?
- **Absichtlich nicht nachgezogen, bitte bestätigen oder widerlegen:**
  - „K20 und K21 sind zwei Seiten“ nur über die Daten
  - Hamm und Heerdt fehlen in `FILIAL_ADRESSEN`, weil die Adressen nicht sicher bekannt sind. Bis dahin gilt die Adresse von der Detailseite.

**Außerdem:**
- `/orte/zakk-flingern-tanzraum` liefert 200: Der Tanzraum hat beim Import eine eigene Zeile bekommen. Der Plan (Abschnitt 4, Pflicht-Tests) erwartet für einen Saal ohne Zeile 404. Ist das ein Widerspruch oder nur ein veraltetes Beispiel im Plan?
- Neue Fehler durch `60d9903` an anderen Stellen: Sitemap, Stadtteilseiten, Kneipen- und Restaurantseiten mit `OrtProgramm`.

## Bericht
Je Befund 1 bis 7: **behoben / teilweise / nicht behoben**, mit Begründung (Datei:Zeile). Danach neue Befunde, sortiert nach Schwere (**kritisch / hoch / mittel / gering / Hinweis**), je mit Beispiel und Vorschlag.

Am Ende: Kann der Stand mit `4f3b396` deployt werden? Was muss vorher noch geändert werden?
