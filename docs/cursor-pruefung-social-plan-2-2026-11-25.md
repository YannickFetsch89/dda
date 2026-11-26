# Cursor-Prüfung 2: Plan Social, zweite Fassung (25.11.2026)

Geprüft: `docs/plan-social-2026-11-25.md` (zweite Fassung) gegen den Code. Kein Code und kein Plan geändert.

Die 12 Befunde der Prüfung 1 sind eingearbeitet. Ein automatischer Weg, einen Post ohne Freigabe online zu stellen oder einen Kanal zweimal zu veröffentlichen, ist in E10 nicht mehr offen. Drei mittlere Punkte bleiben.

## 1. Die 12 Befunde

| Befund | Urteil |
|---|---|
| 1 Eindeutigkeits-Index | gelöst: Spalte `tag date`, `UNIQUE (slot, tag)`. Die bedingte Überschreib-Regel braucht eine SQL-Funktion (neuer Befund 1). |
| 2 Zustandsautomat | gelöst für die sieben Durchläufe unten. Zwei Ränder in den neuen Befunden 2 und 3. |
| 3 Auswahl und Cache | gelöst: `magazinPoolLaden(stichtag, bis)` setzt `heute = von` und hat kein `"use cache"` (`web/lib/daten.ts:263–265`). |
| 4 Bildherkunft | gelöst für https-URLs und für `orte/` über `bilder.csv` (89 Zeilen, 18 erlaubt, jede Datei hat eine Zeile). Neuer Befund 4 für Pfade ohne Host und für `koe-on-ice`. |
| 5 Meta | gelöst: Seiten-Token für beide Kanäle, `ads_read`, Reel über `rupload`, Codes 613, 80001, 9004/2207052, 36001/2207005. |
| 6 Reel-Zeitplan | gelöst: Karussell und Reel im selben Lauf, Freigabe des Reels erst nach dem Karussell. |
| 7 Schritt 1 und Tests | gelöst: `test_vorschau.py`, `test_pipeline.py`, `config.py`, `.env.example` stehen im Aufräumen. |
| 8 Kategorisierer NULL / `fehler` | gelöst, Abschnitt 1. |
| 9 `sameAs` ist ein Kommentar | gelöst, Abschnitt 1, `web/lib/seo.ts:44`. |
| 10 Schlüssel und `META_TOKEN` | gelöst: zweites Argument an `schluesselOk`, Token nur über `deploy.yml`. |
| 11 Story: Tipp + 3 Picks, ein `media_publish` je Folie | gelöst, Abschnitt 4. |
| 12 `INSTAGRAM_TAGE` / Admin-Plan 4.8 | gelöst, kein Widerspruch in der Wirkung. |

### Durchlauf Zustandsautomat

- **Zwei gleichzeitige Takte.** `social_beanspruchen` mit `WHERE status IN ('bereit','teilweise','container_wartet')` ist ein atomares Update. Der zweite Aufruf bekommt keine Zeile. Die Auswahl benutzt dieselbe Bedingung. `wird_gepostet` wird nicht ausgewählt.
- **Absturz zwischen `media_publish` und dem Speichern.** Der Post bleibt `wird_gepostet`, nach 15 Minuten `unklar`. Kein automatischer zweiter Versuch. „Erneut posten“ veröffentlicht nur Folien ohne Media-ID. Liegt die ID nur im abgestürzten Prozess, entscheidet der Blick in die App. Das ist der bewusste Rest, kein automatischer Zweipost.
- **Reel, `IN_PROGRESS` über 4 Takte.** Der Aufruf setzt `container_wartet`, der nächste Takt fragt neu. Die 15-Minuten-Regel gilt für hängendes `wird_gepostet`, nicht für `container_wartet`. Vier Takte bleiben unter der 60-Minuten-Grenze, wenn `container_seit` beim ersten `IN_PROGRESS` gesetzt und danach nicht erneuert wird (Befund 5).
- **`teilweise` und „erneut posten“.** Beansprucht wird `teilweise`. Bearbeitet werden nur Kanäle und Folien ohne Media-ID. Der gelungene Kanal bleibt stehen.
- **Bearbeitung, während der Job das Reel baut.** Der Job setzt `bereit` nur `WHERE status = 'freigegeben'` und verwirft das Video sonst. Eine Bearbeitung auf `vorschlag` lässt das Update ins Leere laufen. Offen ist eine Bearbeitung, während der Post schon `wird_gepostet` oder `container_wartet` ist (Befund 2), und eine spätere Änderung nur am Karussell (Befund 3).
- **Story-Abbruch nach Folie 3.** `ig_media_ids[0..2]` sind gespeichert, Status `teilweise`. Der nächste Takt veröffentlicht die Folien 4–6.
- **6-Stunden-Frist bei `container_wartet`.** Der Post ist auf keinem Kanal online, die Frist setzt ihn auf `verfallen`. Veröffentlicht wird er damit nicht. Die 60-Minuten-Regel muss davor greifen (Befund 5).

## 2. Neue Befunde

### Mittel

**1. `ON CONFLICT` mit Bedingung kann supabase-py nicht**
Abschnitt 7 · `pipeline/vorschlaege.py:295`, `pipeline/reihen_zuordnen.py:148`
Die Regel „nur überschreiben, wenn `vorschlag` und `bearbeitet_am IS NULL`“ ist ein `INSERT … ON CONFLICT (slot, tag) DO UPDATE … WHERE`. `supabase.table().upsert()` kann diese `WHERE`-Klausel nicht. Im Repo macht `upsert` entweder ein bedingungsloses Update oder `ignore_duplicates` (`ON CONFLICT DO NOTHING`). Ein täglicher Lauf mit `upsert` würde einen freigegebenen oder bearbeiteten Post mit einem neuen `vorschlag` überschreiben. `ignore_duplicates` würde umgekehrt einen unangetasteten `vorschlag` nicht auffrischen.
Vorschlag: SQL-Funktion `social_vorschlag_setzen(...)`, nur `service_role`, mit genau dieser `ON CONFLICT … WHERE`. Rückgabe: geschrieben oder unverändert gelassen. `social.py` ruft die Funktion auf, kein `upsert`.

**2. Rücksetzen nach der Bearbeitung nennt kein `alt[]`**
E7, E10, Abschnitt 7
`social_status_setzen(id, alt[], neu, …)` prüft den alten Status. Die Bearbeitung nach der Freigabe setzt auf `vorschlag`, ohne die erlaubten Alt-Status zu nennen. Ein Update aus `wird_gepostet` oder `container_wartet` würde den Status umlegen, während der Aufruf noch veröffentlicht, und der Abschluss des Takts könnte `vorschlag` danach auf `gepostet` setzen oder den Abbruch auf `unklar` verlieren.
Vorschlag: Rücksetzen nur aus `freigegeben` und `bereit`. Aus `wird_gepostet`, `container_wartet`, `teilweise`, `unklar` und `gepostet` lehnt die Funktion ab.

**3. Änderung am Karussell lässt das Reel stehen**
E7, E11, Abschnitt 5.1
Bei der Reel-Freigabe werden `event_ids` und Folien vom freigegebenen Karussell kopiert. Eine spätere Bearbeitung setzt nur das Karussell auf `vorschlag`. Das Reel bleibt `freigegeben` oder `bereit`, mit den alten Events und dem alten Video, und geht so online. Die Vorab-Prüfung sieht Datum und Ort der einzelnen Events, nicht „dieses Event ist aus dem Karussell genommen“.
Vorschlag: Solange das Reel derselben Woche noch nicht `gepostet` ist, setzt dieselbe Bearbeitung es mit auf `vorschlag` und verwirft `video_url`. Die nächste Freigabe kopiert neu und stößt den Video-Bau wieder an.

**4. Pfade ohne Host und ein bekanntes Fremdfoto**
E6, Abschnitt 6 · `web/lib/bilder.ts:8–12`, `web/lib/magazin-bilder.ts:38–40`, `web/lib/admin/events.ts:93–96`, `scraper/tier3/kleine_weihnachtsmaerkte.py:7`
Die Host-Prüfung trifft https-Adressen. Drei Wege haben keinen Host:

- `events.bild_url` darf ein eigener Pfad sein (`/ort-bilder/…`). `lokalesBild()` akzeptiert jeden Ordner unter `ort-bilder`, also auch `orte/` (CC-BY-Dateien) und `events/`.
- Die Website zeigt Fremdbilder als `/bild/event/<id>`. Liegt dieser Pfad als `folien.bild.pfad` in der Folie, sieht der Schnappschuss den Host der gespeicherten `bild_url` nicht mehr. Das Datenmodell der Folie hat `pfad`, `quelle` und `nennung`, keinen Host.
- `web/public/ort-bilder/events/` enthält `rennbahn-weihnacht.webp` und `further-nikolausmarkt.webp`. Die kleinen Märkte speichern genau diese Pfade als `bild_url`. Der Ordner `weihnachtsmaerkte/` ist pauschal erlaubt, das Magazin sperrt darin aber `/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp` als Fremdfoto (`magazin-bilder.ts:40`).

Vorschlag: Relative Pfade nur aus einer Positivliste: CSV-Lizenz wie bei `orte/`, Ordner `weihnachtsmaerkte/` ohne `koe-on-ice.webp`, Ordner `events/` als eigene Fotos. `/bild/event/` nie als Bildquelle. Die Folie speichert `host` (oder die ursprüngliche `bild_url`). Dieselbe Prüfung beim Schnappschuss und beim Umstellen im Admin. Ein Test mit `koe-on-ice.webp`, einem CC-BY-Ortsbild als `bild_url` und einem `/bild/event/<id>`.

### Gering

**5. `container_seit` und die Reihenfolge der Fristen**
E10, Abschnitt 8 (Ablauf der Takt-Route, Punkt 2)
`container_seit` steht im Datenmodell. Der Plan sagt nicht, dass es beim ersten `IN_PROGRESS` gesetzt und bei späteren Abfragen stehengelassen wird. Ein erneuertes `container_seit` lässt die 60 Minuten nie ablaufen. In Punkt 2 laufen „15 Minuten `wird_gepostet`“ und „Fristen nach E10“ in einem Satz. `container_wartet` ist nach 6 Stunden „nicht online“ und würde `verfallen`, obwohl der Container bei Meta noch existiert.
Vorschlag: `container_seit` einmal setzen. In Punkt 2 zuerst die 60 Minuten (`container_wartet` → `fehler`), danach die 6-Stunden-Frist. `container_wartet` unter 60 Minuten nicht anfassen.

**6. `upload_url` aus der Antwort von `start`**
Abschnitt 8, `lib/social/meta.ts`
Der Drei-Schritt-Upload stimmt mit der Reel-Doku überein (`upload_phase=start`, dann `rupload`, Kopf `file_url`, dann `finish` mit `video_state=PUBLISHED`). `start` liefert `upload_url`. Der Plan baut die Adresse selbst (`video-upload/<version>/<video_id>`). Die Doku zeigt die Adresse mal mit und mal ohne Versionssegment.
Vorschlag: Die `upload_url` aus der Antwort verwenden.

**7. Eine Zeile in Abschnitt 8 ohne die Statusbedingung**
Abschnitt 8, Pipeline, `reel --post`
Dort steht „Status `bereit`“. E10 und die Tests sagen `WHERE status = 'freigegeben'`, sonst wird das Video verworfen. Wer nur die Aufzählung liest, setzt `bereit` auch aus `vorschlag`.
Vorschlag: In der Aufzählung denselben `WHERE`-Satz wie in E10.

## 3. Auswahl, kurz gegen den Code

`startseitenAuswahl(pool, [], undefined)` mit `pool.heute` = morgigem Stichtag löst den Zeitraum als „heute“ auf diesen Stichtag auf (`web/lib/datum.ts:141–142`, der Schlüssel `heute` fällt in den Default). Stufen, Highlight- und Top-Flaggen und der Fokustag rechnen mit `pool.heute` bzw. `k.heute` (`startseite.ts:42`, `ableitungen.ts:580–603`, `tippGilt` ab Zeile 695). `neuSeit` und `pool.jetzt` benutzt dieser Weg nicht. `magazinPoolLaden` setzt `jetzt` auf die echte Uhr (`daten.ts:265`); die genannten Funktionen lesen es nicht.

`wochenendProgramm` mit `heute` = Donnerstag nimmt den Freitag dieser Woche (`datum.ts:119–123`, Donnerstag liegt vor Samstag/Sonntag). Der Pool ab diesem Donnerstag enthält Fr–So. Das ist dasselbe Wochenende, das die Startseite an diesem Donnerstag zeigt. Die Zusatzfilter (Uhrzeit, Stufe ≥ 1) bleiben die der Website.

## Gesamturteil

Freigabefähig: **ja.**

Die zwei kritischen Befunde der Prüfung 1 sind zu. Vor dem Bau die Befunde 1 bis 4 in den Plan schreiben. Sie ändern den Automaten nicht, ohne sie überschreibt der Job freigegebene Posts, ein Reel überlebt die Korrektur seines Karussells, und `koe-on-ice.webp` gilt als eigenes Bild. O1–O8 und A1–A6 blockieren die technische Freigabe nicht.
