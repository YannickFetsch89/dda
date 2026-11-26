# Cursor-Prüfung 5: Social-Plan, fünfte Fassung — 26.11.2026

Geprüft: `docs/plan-social-2026-11-25.md` (fünfte Fassung) gegen den Code und die Meta-Doku. Auftrag war Anhang L: die 6 Befunde aus Prüfung 4, neue Widersprüche, und was einen Bau falsch machen würde. Kein Code und kein Plan geändert.

**Freigabefähig: ja.** Alle sechs Befunde sind im Text gelöst. Ein geringer Rest bleibt beim Facebook-Reel, wenn die Liste den Film noch nicht zeigt.

---

## Gering

### 1. `video_reels` muss den Film nicht im selben Moment enthalten

**Fundstelle:** Plan E10, Abgleich Facebook-Reel: `GET /{page-id}/video_reels?fields=id,description,updated_time`, zuerst die gespeicherte `fb_video_id`. [Reels Publishing](https://developers.facebook.com/docs/video-api/guides/reels-publishing/): die Liste kommt mit Seiten-Token und enthält `id`, `description`, `updated_time`. [Page Post](https://developers.facebook.com/docs/graph-api/reference/page-post/) bleibt richtig: Reels stehen dort nicht. Die Doku sagt nicht, dass ein gerade per `finish` veröffentlichter Film sofort in der Liste liegt.

**Befund:** Endpunkt, Felder und Token stimmen. Der Abgleich sucht die ID aus `start`. Fehlt sie, weil die Liste hinterherhinkt, wertet der Plan das als „nicht gefunden“ und versucht `finish` erneut. Das kann ein zweites Reel werden. Stories sind davon getrennt und gehen bei einer Fehlerantwort auf `unklar`. Das ist gelöst.

**Vorschlag:** War der Veröffentlichen-Aufruf eine Fehlerantwort und die gespeicherte `fb_video_id` steht nicht in der Liste, wird der Post `unklar`, ohne zweiten `finish`. „Nicht gefunden“ bleibt nur dann ein erneuter Versuch, wenn noch gar keine `fb_video_id` aus `start` gespeichert ist.

---

## Gelöst aus Prüfung 4

**Befund 1, `beschreibung_kurz`.** 5.1 füllt das Feld nur, wenn `beschreibung_quelle` gesetzt ist oder `beschreibung` in `redaktion_felder` steht. Sonst leer. 5.2 sagt dasselbe. Geschrieben wird `beschreibung_quelle` nur an zwei Stellen, und nur zusammen mit dem neuen Text, wenn `freigegeben` wahr ist (`pipeline/beschreibung_quellen.py:525–527` und `:774–776`). `freigegeben` verlangt einen nicht leeren Text, mindestens zwei belegte Zitate und höchstens sieben Wörter am Stück aus der Quelle (`:375–377`). Ein Scraper setzt die Spalte nicht. Beim Quellenwechsel lässt `database/client.py:195–196` eine gesetzte `beschreibung_quelle` stehen und überschreibt den Text nicht. Leert die Redaktion die Beschreibung, landet `beschreibung` in `redaktion_felder` (`web/lib/admin/events.ts:159`), und die Pipeline schreibt geschützte Felder nicht (`database/client.py:225–227`). Ein Weg, auf dem die Spalte gesetzt ist und der Text doch vom Scraper stammt, ist im Code nicht da. Die Redaktion darf den Text danach selbst ändern. Das ist der zweite erlaubte Fall.

**Befund 2, Facebook-Reel und Stories.** Der Abgleich ist je Format getrennt. Instagram-Feed, Karussell und Reel über `GET /{ig-id}/media` mit Caption. Facebook-Foto und Karussell über `/{page-id}/posts` mit `message`. Facebook-Reel über `video_reels`. Story ohne Abgleich, Fehlerantwort auf das Veröffentlichen einer Folie setzt `unklar`. Der Rest in Befund 1 oben ist die Zeit bis zum Erscheinen in der Liste, nicht der falsche Endpunkt.

**Befund 3, `bildHolenGeprueft`.** `vonQuelleHolen` (`web/lib/bild-proxy.ts:173`) prüft heute nur die öffentliche Adresse und nimmt keinen Host-Rückruf. `bildHolen` (`:300–316`) liest Cache und `laufend` davor. `bildVerkleinern` (`:206`) ist exportiert und benutzt die Warteschlange von höchstens zwei. Die neue Funktion kann in derselben Datei stehen: `vonQuelleHolen` bekommt einen optionalen Prüfparameter, Standard ohne Prüfung, damit `bildHolen` und die Website gleich bleiben. Die neue Funktion übergibt `hostErlaubt` für die Startadresse und jeden Sprung, liest keinen Cache, hängt sich nicht an `laufend` und schreibt keinen. Danach `bildVerkleinern`. So ist sie baubar, ohne das Verhalten der Website zu ändern.

**Befund 4, Anstoß und Postzeit.** Der Anstoß steht in E7 in `web/app/api/admin/magazin/[id]/route.ts` nach dem erfolgreichen `veroeffentlichen` (heute `:83–87`), nur für `wochenvorschau` und `monats-tipps`, nicht bei `zurueckziehen`. Aufruf `jobAnstossen("social", { aktion: "vorschlaege", slot })`. `social` kommt in `WORKFLOWS`, `slot` in die Eingaben von `social.yml`. Der tägliche Lauf fängt verworfene Anstöße auf und baut fehlende Reel-Videos. Die Beispiele in E2 stimmen: 28. → 1. um 18:00. 2. um 10:00 → nicht am 2. (8 Stunden), sondern am 3. um 18:00. 3. um 05:00 → 3. um 18:00 (13 Stunden). 3. um 10:00 entfällt, weil der nächste 18-Uhr-Termin der 4. wäre. Mo 06:00 und der 3. um 06:00 liegen nicht in der umgestellten Stunde.

**Befund 5, zwei Tabs und `NULL`.** `bearbeitet_am IS NOT DISTINCT FROM p_erwartet_bearbeitet_am` ist in Freigabe und Bearbeitung geschrieben. In PostgreSQL gilt `NULL` als gleich `NULL`. Die erste Freigabe, solange noch niemand bearbeitet hat, trifft die Zeile. Bearbeitet der zweite Tab, wird `bearbeitet_am` gesetzt, und die Freigabe mit dem alten `NULL` trifft keine Zeile. Zwei Freigaben ohne Bearbeitung: die erste setzt den Status, die zweite scheitert an `status = 'vorschlag'`. `social_bearbeiten` für `service_role` ist gestrichen. Der Upload läuft mit dem Dienst-Client, der Status nur über `admin_social_freigeben` mit `nutzerClient` (`web/lib/admin/sitzung.ts:74`).

**Befund 6, Edit-List.** `-use_editlist 0` ist der Schalter des MP4-Muxers gegen das `elst`-Atom, neben `-movflags +faststart`. ffmpeg ist auf diesem Rechner nicht installiert, eine Datei wurde hier nicht erzeugt. Ohne Edit-List bleibt die AAC-Vorlaufzeit im stillen Ton (etwa 21 ms bei 48 kHz). Die Bilder verschieben sich dadurch nicht. Der Test liest die Atome und verlangt kein `elst` und `moov` vor `mdat`. Schreibt eine ffmpeg-Fassung das Atom trotzdem, fällt der Test auf, bevor ein Reel rausgeht.

---

## Gesamturteil

**Freigabefähig: ja.**

Die sechs offenen Punkte aus Prüfung 4 sind so gefasst, dass ein Bau sie nicht wieder falsch macht. `beschreibung_quelle` hängt nur am geprüften Haiku-Text, der Reel-Abgleich nutzt die Kante, die Reels auch liefert, der Bildabruf für Social geht am Cache vorbei, die erste Freigabe mit `bearbeitet_am = NULL` trifft, und die Postzeiten der Monats-Tipps passen zu den Beispielen. Der eine geringe Punkt ist die mögliche Verzögerung der Reel-Liste. Er ändert den Endpunkt nicht. O2–O8 und A1–A6 sperren dieses Urteil nicht. Anhang I enthält noch den alten Satz zu Befund 8. Maßgeblich ist 5.1 und Anhang K, der die Abweichung zurücknimmt.
