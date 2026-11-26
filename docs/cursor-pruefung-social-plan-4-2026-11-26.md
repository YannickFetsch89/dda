# Cursor-Prüfung 4: Social-Plan, vierte Fassung — 26.11.2026

Geprüft: `docs/plan-social-2026-11-25.md` (vierte Fassung) gegen den Code und die Meta-Doku. Auftrag war Anhang J: die 13 Befunde und zwei Zusatzpunkte aus Prüfung 3 nachsehen, die neuen Teile prüfen, Widersprüche nennen. Kein Code und kein Plan geändert.

**Freigabefähig: nein.** Zehn der dreizehn Befunde sind gelöst. Offen bleiben die Begründung zu Befund 8, der Abgleich eines Facebook-Reels und der Bild-Cache vor der neuen Host-Prüfung.

---

## Mittel

### 1. Die Begründung zu Befund 8 stimmt nicht

**Fundstelle:** Plan 5.1 (erste 400 Zeichen von `events.beschreibung`) und 5.2 („keine fremden Texte im Wortlaut“). Anhang I, Befund 8.

**Befund:** `pipeline/beschreibung_quellen.py:1–12` schreibt einen Text nur dann neu, wenn Haiku eine Quelle gefunden hat und die Prüfungen bestehen. Längere wörtliche Stücke werden dort verworfen (`MAX_UEBERNAHME`, Zeile 308). Das gilt nicht für die Spalte insgesamt.

- Der Kategorisierer erfindet keinen Text. Er setzt `beschreibung` auf `""` (`pipeline/categorizer.py:78–80` und `:114`) und lädt nur Zeilen mit `beschreibung IS NULL` (`:186`).
- Scraper schreiben den Quellentext direkt in die Spalte, zum Beispiel `scraper/utils/jsonld_events.py:143` (`description`) und `scraper/utils/ical.py:141` (`DESCRIPTION`). Dieselbe Übernahme gibt es in `wp_tribe.py`, `toubiz_lesen.py` und mehreren Tier-3-Scrapern.
- Für Rausgegangen bleibt der bisherige Text, wenn keine Quelle gefunden wird (`beschreibung_quellen.py:489–491`).
- `ersetzen_erlaubt` (`:607–610`) tauscht nur, wenn der alte Text kürzer als 200 Zeichen oder kürzer als der neue ist. Ein langer Quellentext bleibt stehen.

5.1 schickt also bei vielen Events den Quellentext an das Caption-Modell. 5.2 sagt das Gegenteil. Die Freigabe sieht die Caption. Stories nutzen den Text nicht. Die Aussage „die Spalte ist schon in eigenen Worten“ ist trotzdem falsch, und die Abweichung von Befund 8 trägt nicht.

**Vorschlag:** `beschreibung_kurz` nur füllen, wenn `beschreibung_quelle` gesetzt ist (dann hat Haiku geschrieben) oder die Redaktion das Feld selbst gesetzt hat (`redaktion_felder`). Sonst bleibt es leer, und das Modell bekommt nur die strukturierten Felder. 5.2 dann an 5.1 anpassen.

### 2. Der Abgleich sieht ein Facebook-Reel nicht

**Fundstelle:** Plan E10, Abgleich nach einer Fehlerantwort auf einen Veröffentlichen-Aufruf: `GET /{page-id}/posts?fields=id,created_time,message`. [Page Post](https://developers.facebook.com/docs/graph-api/reference/page-post/): „This endpoint does not return Reels.“ Dieselbe Grenze steht beim [Page Feed](https://developers.facebook.com/docs/graph-api/reference/page/feed/). Die Liste liegt auf `GET /{page-id}/video_reels` ([Reels Publishing](https://developers.facebook.com/docs/video-api/guides/reels-publishing/), Felder `id`, `description`, `updated_time`). Der Seiten-Token ist dort der richtige Token.

**Befund:** Für einen Feed-Post und ein Karussell passt `message`. Für ein Instagram-Reel passt `GET /{ig-id}/media?fields=id,timestamp,caption`: Reels stehen dort, Stories ausdrücklich nicht ([IG User Media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media), Hinweis zu `GET /{ig-id}/stories`). Für ein Facebook-Reel ist `/posts` leer, auch wenn `finish` den Film schon veröffentlicht hat. Der Plan wertet „nicht gefunden“ als erneuten Versuch. Das ist der Doppelpost, den der Abgleich schließen sollte, auf dem Facebook-Kanal des Reels.

Stories: `GET /{ig-id}/stories` hat keine Caption, und die Story selbst hat keine (Abschnitt 4). „Passende Anzahl Story-Folien“ zählt alle Stories der letzten 24 Stunden, nicht die Folien dieses einen Posts. Eine zweite Story am selben Morgen verschiebt die Zahl. Zu wenig Treffer führen zum zweiten Versuch, zu viele dazu, eine Folie als online zu verbuchen, die es nicht ist.

Container ohne `media_publish` verfällt nach 24 Stunden (dieselbe IG-Doku: „Containers expire after 24 hours“). `--test-reel` veröffentlicht damit nichts. Das stimmt.

**Vorschlag:** Facebook-Reel über `GET /{page-id}/video_reels` abgleichen, Beschreibung gegen `caption_fb`. Stories nicht über die Anzahl: ohne eindeutige ID wird der Abgleich `unklar`, und es gibt keinen zweiten Versuch. Feed, Karussell und Instagram-Reel bleiben beim Caption-Abgleich.

### 3. `hostErlaubt` sieht einen Cache-Treffer nicht

**Fundstelle:** Plan Abschnitt 6. `web/lib/bild-proxy.ts:300–316`: `bildHolen` liest den Platten-Cache und die laufende Anfrage, bevor `vonQuelleHolen` (`:173`) eine Weiterleitung prüft. Der Schlüssel der laufenden Anfrage ist nur Hash und `zwischenspeichern` (`:310`), ohne eine Host-Prüfung.

**Befund:** Ein optionaler Parameter am Ende ändert die heutigen Aufrufe nicht. Wirkt er nur in `vonQuelleHolen`, gilt er nur, wenn wirklich neu geladen wird. Liegt das Bild schon im Cache, kommt es von einem früheren Abruf der Website, inklusive einer Weiterleitung auf einen anderen Host. Dieselbe laufende Anfrage kann ein Social-Abruf und ein Website-Abruf teilen. Die Positivliste aus Prüfung 3 greift dann nicht. Die Website ohne Parameter bleibt, wie sie ist. Das ist richtig so.

**Vorschlag:** Social ruft mit `zwischenspeichern: false` auf und hängt sich nicht an `laufend`. `hostErlaubt` prüft die Startadresse und jeden Sprung. Ein Treffer der Website wird nicht wiederverwendet.

---

## Gering

### 4. Der Magazin-Anstoß kann nicht in der SQL-Funktion liegen

**Fundstelle:** Plan E7 (`admin_magazin_veroeffentlichen` stößt `social.yml` an). `web/app/api/admin/magazin/[id]/route.ts:83–87` ruft die Funktion auf und gibt danach zurück. Es gibt dort keinen Anstoß. `web/lib/job-anstoss.ts:8` und `:34` nimmt einen Workflow-Namen und Eingaben, keine Kommandozeile. `web/lib/admin/github.ts:6–14` hat noch kein `social`. `social.yml` nennt die Eingaben `aktion`, `post`, `dry_run` (Plan Abschnitt 8), kein `slot`.

**Befund:** Die SQL-Funktion kann `jobAnstossen` nicht aufrufen. Der Anstoß gehört in die Route, nach erfolgreichem `veroeffentlichen`, nicht nach `zurueckziehen`, und nur bei den Rubriken `wochenvorschau` und `monats-tipps`. `WORKFLOWS` braucht den Schlüssel `social`, sonst lässt sich der Name nicht übergeben. Eine Eingabe `slot`, die der Workflow nicht erklärt, lehnt GitHub ab. `anstossPlanen` startet je Workflow höchstens einmal in fünf Minuten. Ein dritter Aufruf in der Sperrzeit wird verworfen (`job-anstoss.ts:13–16`), nicht nachgeholt. Der tägliche Lauf ist die Absicherung, aber nur, solange er vor Mo 06:00 bzw. dem 3. um 06:00 noch kommt.

Die Uhrzeiten selbst passen. Mo 06:00 und der 3. um 06:00 liegen nicht in der fehlenden oder doppelten Stunde. Zwölf Stunden auf `timestamptz` sind an diesen Tagen auch zwölf Stunden Berliner Zeit, weil die Umstellung in der Nacht zum Sonntag liegt und der Post am Montag bzw. am 1. bis 3. steht. Der Test „28.02. 20:00 → 01.03. 18:00“ hat 22 Stunden Abstand und erfüllt die 12 Stunden. „03. um 10:00 → entfällt“ liegt nach der Frist.

E2 sagt für die Monats-Tipps zusätzlich „um 18:00 am Tag nach der Veröffentlichung, spätestens am 3.“ Eine Veröffentlichung am 3. um 05:00 hätte bis 18:00 noch mehr als 12 Stunden, fällt aber in „Tag danach“ und damit auf den 4. Der Slot entfällt, obwohl die Frist aus E7 ihn noch hergäbe.

**Vorschlag:** Den Anstoß in `route.ts` nach Zeile 86 setzen, `social` in `WORKFLOWS`, und `slot` als Workflow-Eingabe, wenn der Lauf nicht ohnehin die nächsten vier Tage anlegt. Die Postzeit ist 18:00 am ersten Tag, der mindestens 12 Stunden nach der Veröffentlichung liegt und nicht nach dem 3. um 18:00. Der tägliche Lauf bleibt der Auffang für einen verworfenen Anstoß.

### 5. `erwartet_bearbeitet_am` steht nur in der Signatur

**Fundstelle:** Plan Abschnitt 7, `admin_social_freigeben(id, version, bilder[], erwartet_bearbeitet_am)`, daneben weiter `social_bearbeiten` für `service_role` und `admin_social_bearbeiten` für `authenticated`.

**Befund:** Der Vergleich fehlt. Sicher ist die Freigabe nur mit `UPDATE … WHERE status = 'vorschlag' AND bearbeitet_am IS NOT DISTINCT FROM erwartet_bearbeitet_am`. Sonst gewinnt eine Freigabe aus dem zweiten Tab gegen eine eben gespeicherte Bearbeitung, und der Schnappschuss zeigt den alten Stand. Zwei Funktionen mit derselben Bearbeitungslogik können auseinanderlaufen. Der Admin-Client ist der Nutzer-Client (`web/lib/admin/sitzung.ts:74`, `nutzerClient`). `admin_pflicht()` und `auth.uid()` passen dazu. Der Job bleibt bei `service_role` und `verlauf`. Das löst Befund 6. Der Bucket lässt Schreiben nur für `service_role` (Abschnitt 7). Der Schnappschuss aus der Admin-Route braucht dafür den Dienst-Client. Der Nutzer-Client darf nur die `admin_social_*`-Funktion aufrufen.

**Vorschlag:** Die `WHERE`-Bedingung in Abschnitt 7 schreiben. Bearbeitung nur in einer Funktion. Hochladen mit dem Dienst-Client, Status nur über `admin_social_freigeben`.

### 6. „Keine Edit-Lists“ steht im Satz, nicht im ffmpeg-Aufruf

**Fundstelle:** Plan E11. [Reel Specifications](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media#reels-specs): „no edit lists, moov atom at the front“, H.264, progressive, closed GOP, 4:2:0, 23–60 fps, AAC höchstens 48 kHz, 1 oder 2 Kanäle, mindestens 3 Sekunden, höchstens 15 Minuten und 300 MB.

**Befund:** `-pix_fmt yuv420p`, `-profile:v high`, `-r 30`, `-g 60 -keyint_min 60 -sc_threshold 0 -flags +cgop`, `-movflags +faststart`, `-c:a aac -ar 48000 -ac 2` treffen Pixelformat, GOP, moov vorn, Ton und Länge (3–90 s liegt in den 15 Minuten). `+faststart` entfernt keine Edit-List. ffmpeg schreibt für AAC oft ein `elst`-Atom. Der `ffprobe`-Test prüft moov vor mdat, nicht das Fehlen von `elst`. Meta nennt Edit-Lists als Ablehnungsgrund.

**Vorschlag:** Den Aufruf so fassen, dass kein `elst` entsteht, und den Test darauf prüfen.

---

## Gelöst aus Prüfung 3

| Befund | Beleg |
|---|---|
| 1 Reel-Datei | E11 und der `ffprobe`-Test. Offen nur das `elst`, Befund 6 oben. |
| 2 Magazin-Termine | E2 Montag 18:00, E7 zwölf Stunden, letzter Termin Mo 06:00 und der 3. um 06:00. Der Februar-Test geht auf. Offen die „Tag danach“-Kante und der Ort des Anstoßes, Befund 4. |
| 3 Weiterleitung | Abschnitt 6, Parameter und exakte Hosts. Offen der Cache, Befund 3 oben. |
| 4 Schnappschuss und Erlaubnis | E10: alles oder nichts, Version löschen, Erlaubnis vor dem ersten Kanal neu, Titel nur als Hinweis. Tests in Abschnitt 12. |
| 5 „Jetzt posten“ | `admin_social_jetzt`, nur `bereit`, nur `geplant_fuer = now()`, kein Meta-Aufruf. |
| 6 Admin-Protokoll | `admin_social_*` für `authenticated` mit `admin_pflicht()`, Job und Takt in `verlauf`. Die Signatur-Lücke ist Befund 5 oben. |
| 7 Leere Slots | E7: unter zwei Events kein Karussell, ohne Highlight kein Einzeltipp, ohne Event keine Story. |
| 9 Agenten-Anleitungen | Abschnitt 8, Aufräumen, mit den Zeilen. |
| 10 Zeile `startPlaetze` | Abschnitt 4, `ableitungen.ts:756–804`. |
| 11 Kosten | Abschnitt 12, Mengen statt Euro. |
| 12 Anwalt vor dem Livegang | Schritte 8 und 9: Datenschutztext erst nach A1, `modus = an` erst nach A1–A4. |
| 13 Aufräumen bei `aus`/`vorschau`, Fehler 190 | E9 Punkt 1–2 und E10: der Post wird zurückgesetzt, bevor der Modus auf `vorschau` geht. |
| Satori/WebP, Warteschlange | Abschnitt 6: PNG vor dem Einbetten, höchstens zwei gleichzeitig. |
| Takt-Schlüssel | E9 und Abschnitt 9 Punkt 6: nur im Kopf, Schritt 0 prüft, ob `pg_net` Köpfe speichert. |

---

## Gesamturteil

**Freigabefähig: nein.**

Der Zustandsautomat, die Reel-Parameter bis auf die Edit-List, die neuen Fristen und die Trennung von Admin-Protokoll und Job sind nachvollziehbar und am Code geprüft. Drei Stellen sind noch falsch: die Caption bekommt Quellentext, obwohl der Plan das verneint; ein Facebook-Reel, das trotz Fehlerantwort online ist, wird ein zweites Mal gepostet, weil `/posts` keine Reels liefert; der Bild-Cache umgeht die Host-Prüfung. Das sind Nachträge an 5.1, E10 und Abschnitt 6, kein neuer Entwurf. O2–O8 und A1–A6 sperren dieses Urteil nicht.
