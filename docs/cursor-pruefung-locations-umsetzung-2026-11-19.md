# Cursor-Prompt: Prüfung der Umsetzung „Ortsseiten“, Schritte 1 und 2 (19.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD, Branch `claude/setup-project-structure-5QNOf`).

---

Du prüfst die **Umsetzung** der Schritte 1 und 2 des freigegebenen Plans `docs/plan-locations-2026-11-18.md` (elfte Fassung) für die Website dies.das.düsseldorf (diesdas.events). Schritt 3, die Seiten unter `/orte`, ist noch nicht gebaut.

**Ändere keine Dateien und keine Datenbank. Schreib nur einen Befundbericht.**

## Stand
- **Commits:** `b1570ff` (Schritt 1), `f33890f` (Schritt 2), `eb00a70` und `cc95cf2` (Geo-Skript), `0e07f17` (Geo-SQL, Tiefgarage), `0d58755` (weitere 73 Orte, Kamp-Lintfort). Alles ist gepusht, der Pipeline-Code ist live.
- **Vom Auftraggeber im Supabase-SQL-Editor ausgeführt:**
  - `database/orte_spielstaetten_2026-11-19.sql`, dazu der Probelauf `…_trigger_probe_…` mit Ergebnis „alle 14 ok“
  - `orte_daten_central_…`, `ortsnamen_2026-11-19.sql` (Stone → Ratinger Hof)
  - `gebiet_bereinigung_2026-11-19.sql` und `…_2.sql`
  - `orte_koe_loesen_…`
  - `orte_spielstaetten_import_2026-11-19.sql` und `…_2.sql` (jetzt 229 Spielstätten, 26 mit Haus)
  - `ort_id_nachtrag_2026-11-19.sql` (2.861 Events)
  - `orte_spielstaetten_geo_2026-11-19.sql` (131 Adressen, 130 Koordinaten)
  - `orte_tiefgarage_weglassen_…`
- **Noch nicht ausgeführt:** `ort_id_nachtrag_2026-11-19_2.sql` (370 Events der 73 neuen Orte) und die Geo-Prüfung der 73 neuen Orte.
- **Entscheidungen des Auftraggebers vom 19.11. außerhalb des Plantexts:**
  - Sammelfreigabe aller Vorschläge der Kandidatenliste
  - Arten für 73 weitere Orte bestätigt, 12 ohne Seite
  - Stone im Ratinger Hof ist geschlossen → Ratinger Hof
  - Bilker Bunker und Schleuse Zwei sind getrennte Orte
  - Dachseite Kunstsammlung NRW: ja
  - D’haus Central (Worringer Straße 140) wird eigenes Haus mit den Sälen Central 1, Central 2 und Central Brücke
  - Tiefgarage PSD BANK DOME weglassen
  - Theater an der Kö: noch offen
  - neue Arten: Laden, Freizeit/Erlebnis, Ausflugsziel/Sehenswürdigkeit

## Was du lesen sollst
1. **Den Plan:** `docs/plan-locations-2026-11-18.md`, Abschnitt 3 und 4 (maßgeblich), dazu Abschnitt 7.2 (Punkte 1–21) und 9.
2. **Schritt 1:** `scraper/orte/spielstaetten_kandidaten.py`, `tests/test_spielstaetten_kandidaten.py`, `data/spielstaetten/kandidaten.csv`
3. **Schritt 2:**
   - **SQL:** `database/orte_spielstaetten_2026-11-19.sql`, `database/orte_spielstaetten_trigger_probe_2026-11-19.sql`, `database/orte_koe_loesen_2026-11-19.sql`, `database/orte_tiefgarage_weglassen_2026-11-19.sql`, `database/orte_daten_central_2026-11-19.sql`, die beiden Import-Dateien, die beiden Nachtrag-Dateien, `database/orte_spielstaetten_geo_2026-11-19.sql`
   - **Zuordnung:** `pipeline/ort_zuordnung.py`, `main.py` (Schritte 1d bis 1f, Kennzahlen nach dem Speichern)
   - **Dubletten:** `pipeline/deduplication.py` (`_ort_haus_regel`, `_ort_passt`, `_events_mergen`), `database/client.py` (`_ABGLEICH_SPALTEN`, `_anreicherungs_update_bauen`, `_tagesbestand`), `pipeline/dubletten_sql.py`
   - **Clubs:** `scraper/orte/clubs_profil.py` (`event_orte`, `event_orte_vereinigen`, `_events_fuer`, `freischalten`, `nicht_im_pruefen`, `club_orte`)
   - **Gebiet und Namen:** `pipeline/gebiet.py`, `pipeline/ortsnamen.py`, `scraper/tier2/schauspielhaus.py` (`adresse_fuer`)
   - **Import und Geo:** `scraper/orte/spielstaetten_import.py`, `scraper/orte/spielstaetten_geo.py`
   - **Tests:** `tests/test_ort_zuordnung.py`, `tests/test_spielstaetten_import.py`, `tests/test_spielstaetten_geo.py`, `tests/test_gebiet.py`, `tests/test_ortsnamen.py`
4. **Zusammenhang:** `database/schema_orte.sql`, `web/lib/pfad-pruefung.ts`, `web/lib/clubs-daten.ts`, `pipeline/rausgegangen_nachziehen.py`, `scraper/orte/google_places.py`

## Regeln des Projekts (Verstöße sind Befunde)
- **Eine URL je Ort.** Echte 404 und 308 nur im Proxy, nie `NextResponse.rewrite`.
- **Der Proxy liest mit dem anonymen Schlüssel** und sieht nur `aktiv = true`.
- **Automatische Läufe schreiben nie `NULL` über eine vorhandene `ort_id`.** Eine Zuordnung lösen geht nur ausdrücklich (Ausschlussliste plus SQL in derselben Datei).
- **`event_orte` der Clubs wächst nur.** Entfernt wird nur über `EVENT_ORTE_AUSSCHLUSS`.
- **Keine Google-Koordinaten speichern**, nur die `place_id`. Keine Google-Fotos.
- **Scraping:** mindestens 2 Sekunden Pause, Backoff bei 429.
- **SQL** nur als Datei in `database/`. Abfragen auf `orte` und `events` seitenweise.
- Keine neue Bibliothek ohne Rückfrage. Texte, Kommentare und Logs auf Deutsch.

## Worauf du besonders achten sollst
1. **Plan gegen Code:** Setzt der Code Abschnitt 3.3 bis 3.6, 3.12, 3.15 und 3.16 und die Deploy-Reihenfolge aus Abschnitt 4 wörtlich um? Nenn jede Abweichung, auch begründete.
2. **Schutz-Trigger (`orte_schutz`):**
   - Deckt er Löschen, Abschalten, Slug-Wechsel und Typwechsel ab, dazu Kinder bei jedem Elterntyp und Weiterleitungsziele?
   - Kann er einen heutigen Lauf blockieren, etwa `google_places.py`, `bars_einordnen`, `clubs_profil.freischalten`, das Weihnachtsmarkt-Import-Skript oder ein Spielplatz-Skript?
   - Ist der Probelauf aussagekräftig?
3. **Ortszuordnung (`pipeline/ort_zuordnung.py`):**
   - `schluessel()`: Führt die Normalisierung (Akzente, „Düsseldorf“ entfernt) zu falschen Gleichsetzungen? Bekannt sind „Holocafe Düsseldorf“ und „Holocafé Düsseldorf“ als mehrdeutig.
   - Regel „Saal vor Haus“.
   - `nicht_im_ort` gegen die frühere Regel in `event_orte()`
   - Ketten-Adressregel `adresse_passt`
   - Inaktive Zeilen
   - `bestand_pruefen`: Laufzeit über alle Events mit `ort_id`, und wird ihre Kennzahl richtig berichtet?
4. **Pipeline (`main.py`):**
   - Was passiert, wenn `index_laden` scheitert?
   - Landen die internen Felder `_haus_id` und `_kette` nie in der Datenbank?
   - Kommt `ort_id` beim Insert und beim Anreichern richtig an?
5. **Dubletten:**
   - Greift die Haus-Regel an allen Stellen (in einem Lauf, Tagesbestand, `dubletten_sql`)?
   - Bleibt `rausgegangen_nachziehen.py` beim Namensvergleich?
   - Gibt es heute erkannte Dubletten, die die neue Regel nicht mehr erkennt?
6. **`clubs_profil.py`:**
   - Wächst `event_orte` an allen drei Schreibstellen nur?
   - Wirkt die Ausschlussliste in `event_orte()` und in der Vereinigung?
   - Kann `club_orte` mit der neuen Spalte `slug` etwas anderes brechen?
7. **Import (`spielstaetten_import.py`):**
   - Ablehnungsregeln, Säle mit `parent_id`, Guide-Häuser als Eltern
   - Wiederholbarkeit des zweiten Laufs
   - `event_orte` je Zeile, besonders bei Häusern mit Sälen und bei zusammengeführten Dubletten
   - Escaping im SQL (Apostrophe, Anführungszeichen in JSON)
8. **Geo (`spielstaetten_geo.py`):**
   - Nominatim-Regeln
   - Stadtteil nur aus der PLZ
   - Koordinaten nur bei PLZ im Gebiet
   - Säle nicht geokodiert
   - Dachseite Kunstsammlung NRW ohne Adresse
   - Prüfdatei nur lokal (`.gitignore`)
9. **Kandidatenliste (`kandidaten.csv`):**
   - Nenn auffällige Zeilen konkret: falsche Art, falscher Saal, Ortsnamen wie Adressen. Bekannt sind „Flow, Mertensgasse 2, 40213 Düsseldorf“ als Name und Slug und „Franklinstraße Turnhalle“.
   - Fehlen Orte, die eine Seite haben sollten?
10. **Daten in der Datenbank** (nur lesen, falls du Zugriff hast; sonst aus den SQL-Dateien schließen):
    - Säle ohne `parent_id`
    - Spielstätten ohne `event_orte`
    - Slug-Kollisionen
    - Weiterleitungen, die auf inaktive Zeilen zeigen
11. **Tests:**
    - Fehlen Pflicht-Tests aus Abschnitt 4 für die Schritte 1 und 2?
    - Gibt es Tests, die etwas anderes prüfen, als ihr Name sagt?
12. **Risiken für Schritt 3:** Was muss Schritt 3 beachten, weil Schritt 1 oder 2 es anders gebaut hat als im Plan beschrieben? Zum Beispiel die neuen Arten, D’haus Central als eigenes Haus, Säle von Guide-Häusern.

## Bericht
Eine Liste, sortiert nach Schwere (**kritisch / hoch / mittel / gering / Hinweis**). Je Befund:
- Ort (Datei:Zeile)
- was falsch ist, mit einem konkreten Beispiel (Eingabe → falsches Ergebnis)
- warum es ein Problem ist
- Vorschlag

Am Ende:
- eine Gesamteinschätzung, ob Schritt 1 und 2 so stehen bleiben können
- welche Befunde vor Schritt 3 behoben sein müssen
