# Cursor-Prompt: Prüfung des Plans „Ortsseiten“ (18.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD, Branch `claude/setup-project-structure-5QNOf`).

---

Du prüfst einen **Plan** für die Website dies.das.düsseldorf (diesdas.events), noch keine Umsetzung. **Ändere keine Dateien und keine Datenbank. Schreib nur einen Befundbericht.**

## Was du lesen sollst
1. **Den Plan:** `docs/plan-locations-2026-11-18.md`. Abschnitt 5 enthält die Entscheidungen des Auftraggebers E1–E7, Abschnitt 7 das Ergebnis von Schritt 1. Diese Entscheidungen sind gesetzt, prüfe nur, ob der Plan sie richtig und vollständig umsetzt.
2. **Die Kandidatenliste:** `data/spielstaetten/kandidaten.csv` (Semikolon) und das Skript, das sie erzeugt: `scraper/orte/spielstaetten_kandidaten.py`.
3. **Den schon umgesetzten Teil** (seit Commit `884d3fc` live, Nachträge in diesem Arbeitsstand):
   - `pipeline/gebiet.py` (Gebietsfilter, in `main.py` Schritt 1c), `tests/test_gebiet.py`
   - `pipeline/ortsnamen.py`, `tests/test_ortsnamen.py`, `pipeline/stadtteil_mapper.py`
   - Scraper: `scraper/tier2/oper_am_rhein.py`, `scraper/tier1/meetup.py`, `scraper/tier2/kulturschlachthof_r25.py`, `scraper/tier2/fft_duesseldorf.py`
   - SQL: `database/gebiet_bereinigung_2026-11-18*.sql`, `database/datenfehler_2026-11-18.sql`, `database/ortsnamen_2026-11-18*.sql`
4. **Den Zusammenhang:**
   - bestehende Orte und Guides: `web/lib/orte.ts`, `web/components/ort-karten.tsx` (`ortPfad`, `ortRoute`), `web/lib/clubs.ts`
   - Proxy: `web/proxy.ts`, `web/lib/pfad-pruefung.ts`
   - Eventseite: `web/app/event/[kategorie]/[slug]/page.tsx`
   - Datenbank: `database/schema_orte.sql`, `database/orte_typ_weihnachtsmarkt_2026-11-17.sql` (CHECK auf `orte.typ`)
   - Bilder: Weihnachtsmarkt-Guide `scraper/weihnachtsmaerkte/bilder.py`, `data/weihnachtsmaerkte/bilder.csv`
   - Personalisierung: `docs/konzept-personalisierung-2026-11-18.md` (Baustein B4 „Folgen“)

## Bekannte Regeln des Projekts (Verstöße sind Befunde)
- **Eine URL je Ort (E1 aus dem Orte-Guide):** Ein Ort mit Guide-Seite bekommt keine zweite Seite.
- **Echte Statuscodes nur im Proxy:**
  - 404 und 308 entstehen in `web/proxy.ts` mit direkter Antwort bzw. Redirect.
  - **Nie `NextResponse.rewrite`.** Hinter nginx führt ein Rewrite zu HTTP 500.
  - Mit cacheComponents streamt das Layout vor `notFound()`, die Seite selbst kann also keine echte 404 liefern.
- **Bildpfade unter `/ort-bilder/<hub>/…`,** nie unter einem Seitenpfad, den der Proxy prüft. `/orte/…` wäre so ein Pfad.
- **Der Browser kontaktiert keine Dritten:** Bilder über den eigenen Server, Karte selbst gehostet (MapLibre + PMTiles).
- **Datenbank:**
  - SQL nur als Datei in `database/`, der Auftraggeber führt sie aus.
  - Supabase-Abfragen auf `orte`/`events` seitenweise (mehr als 1.000 Zeilen).
- **Pipeline-Ortsnamen:** gepflegte Liste ohne unscharfes Zusammenführen. Säle bleiben getrennt. Namen ohne Trenner, Ausnahmen „zakk – Halle“ und die FFT-Säle, weil `reihen_zuordnen.ort_basis` am Trenner schneidet.
- Keine neue Bibliothek ohne Rückfrage. Texte und Kommentare auf Deutsch.

## Worauf du besonders achten sollst
1. **Gebietsfilter:**
   - Gibt es Fehltreffer in Düsseldorf, Neuss oder Ratingen? Denk an Straßen nach Städten (Kölner, Duisburger, Krefelder Straße), Namen mit „Essen“ und „Halle“, die Köln-Düsseldorfer, Stadtteile wie Hamm.
   - Gibt es Lücken? Orte außerhalb ohne Stadtnamen und ohne Postleitzahl.
   - Stimmen die PLZ-Bereiche (Düsseldorf 40210–40629, Neuss 41460–41472, Ratingen 40878–40885)?
   - Läuft der Filter an der richtigen Stelle der Pipeline, auch für alle Quellen?
2. **SQL-Dateien:** Sicherheit der DELETEs (nur Treffer-IDs, Kaskaden auf `merkliste`, `event_sensibel`, `event_seo_entscheidungen`), Wiederholbarkeit, Reihenfolge.
3. **Kandidatenliste:**
   - Stimmen Haus und Saal? Fehlen Zusammenfassungen, oder gibt es falsche?
   - Stimmen die Klassen (Treffpunkt, online, allgemein, Gruppe)?
   - Stimmt der Guide-Abgleich?
   - Nenn Zeilen mit falschem Vorschlag konkret.
4. **Datenmodell (E5):**
   - Typ `spielstaette` in `orte` mit Profil in `extras` plus `events.ort_id`: Passt das?
   - Wie wird `ort_id` gesetzt (Pipeline, Nachtrag), was passiert bei Umbenennung, Zusammenlegung und Löschung eines Orts?
   - Wie verhält sich `ort_id` zu bestehenden Guide-Orten (Clubs mit `event_orte`) und zu Sälen (E6)?
   - Ist die Dubletten-Erkennung ausreichend beschrieben?
5. **Seiten und URLs:**
   - `/orte/<slug>`, `/orte`, 308 auf Guide-Seiten, 404 für Unbekanntes, Saal-Seiten nach E6 ohne doppelten Inhalt (Canonical?)
   - indexiert nur mit kommenden Events oder eigenem Text, Sitemap, JSON-LD
6. **Bilder (E4):** Ist die Umsetzung (Nachweis, Herkunft je Bild, schnelles Entfernen) vollständig, und widerspricht sie dem Projektgrundsatz „keine Dritten im Browser“?
7. **Lücken im Plan:**
   - Was fehlt für Schritt 2 (Import, Geo, Stadtbüchereien-Filialen)?
   - Was fehlt für Schritt 3 (Caching, Performance bei 236+ Seiten, Tests)?
   - Wie ist der Bezug zu „Folgen“ (B4)?

## Bericht
Eine Liste, sortiert nach Schwere (**kritisch / hoch / mittel / gering / Hinweis**). Je Befund:
- Ort (Datei:Zeile oder Planabschnitt)
- was falsch ist, mit einem konkreten Beispiel (z. B. Zeile der CSV oder Ortsname, der falsch gefiltert würde)
- warum es ein Problem ist
- Vorschlag

Am Ende: eine Gesamteinschätzung, ob der Plan nach Behebung der Befunde freigabereif ist.
