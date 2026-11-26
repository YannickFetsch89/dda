# Cursor-Prüfung 3: Social-Plan, dritte Fassung — 26.11.2026

Geprüft: `docs/plan-social-2026-11-25.md` (dritte Fassung, Anhang H). Gegen den Code im Repo und die Meta-Doku vom 26.11.2026: [IG User Media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media) (Graph v27.0, Reel-Spezifikation im selben Dokument). Kein Code und kein Plan geändert. Anhänge E und G sind nicht erneut als offene Punkte gewertet.

**Freigabefähig: nein.** Drei Stellen würde ein Bau nach dem Text falsch oder leer lassen: die Reel-Datei, die Magazin-Slots, die Bild-Weiterleitung. Darunter die einzelnen Befunde.

---

## Mittel

### 1. Die Reel-Datei erfüllt die Meta-Vorgabe nicht

**Fundstelle:** Plan Abschnitt 6, Auftrag `reel` (`-c:v libx264 -pix_fmt` fehlt, `-movflags` fehlt). Meta, Reel Specifications: Container MP4, „no edit lists, moov atom at the front of the file“, Video „HEVC or H264, progressive scan, closed GOP, 4:2:0 chroma subsampling“, Audio AAC, höchstens 48 kHz, 1 oder 2 Kanäle, 3 Sekunden bis 15 Minuten, höchstens 300 MB.

**Befund:** Der Plan nennt H.264, stille AAC, 30 fps, etwa 25 Sekunden, 1080×1920. Das liegt in den Grenzen für Länge, Bildrate und Größe. Er legt das `moov`-Atom nicht an den Anfang und setzt kein 4:2:0. ffmpeg schreibt das Atom ohne `+faststart` ans Ende und kann aus den JPEG-Folien ein anderes Pixelformat nehmen. Meta holt die Datei per URL. Eine so erzeugte Datei kann der erste Reel-Lauf ablehnen. Schritt 0 prüft eine Story, nicht diese Datei.

**Vorschlag:** Im ffmpeg-Aufruf festschreiben: `-pix_fmt yuv420p`, `-movflags +faststart`, progressive, closed GOP, AAC mit höchstens 48 kHz und ein oder zwei Kanälen. Der Probe-Reel in Schritt 0 lädt diese Datei hoch, nicht nur ein Story-JPEG.

### 2. Wochenvorschau und Monats-Tipps entstehen zum beschriebenen Termin nicht

**Fundstelle:** Plan E2 und E7 (Sonntag 18:00, am 1. um 18:00, Vorschlag mindestens zwei Tage vorher, sonst entfällt der Slot). `.github/workflows/magazin.yml:11–13`: Entwurf Wochenvorschau Freitag 17:00 UTC, Entwurf Monats-Tipps am 28. um 17:00 UTC. `docs/plan-redaktion-2026-11-19.md` E6: Veröffentlichung der Wochenvorschau als Empfehlung Sonntag 8:00, Entwurf Freitag 18:00, Prüfung bis Samstagabend. Veröffentlichen kann nur der Auftraggeber (`pipeline/magazin.py:7`).

**Befund:** Der Social-Job läuft 04:00 UTC (Winter 05:00, Sommer 06:00 Berlin) und legt nur an, was noch mindestens 48 Stunden entfernt ist. Der letzte Lauf, der den Sonntag 18:00 noch anlegen darf, ist der Freitagmorgen. Der Magazin-Entwurf kommt erst Freitag 18:00 Berlin, die empfohlene Veröffentlichung Sonntag 8:00. Samstagmorgen liegt unter 48 Stunden, Sonntagmorgen auch, und der Artikel ist um 05:00 noch nicht da. Der Slot entfällt jede Woche, nicht nur beim belegten Ausreißer 23:58.

Monats-Tipps: Entwurf am 28. um 18:00 Berlin, Post am 1. um 18:00. Der letzte noch zulässige Social-Lauf ist der Morgen zwei Tage vor dem 1. (bei einem 31-Tage-Monat der 30. um 05:00). Im Februar liegt dieser Morgen vor dem Entwurf am 28. Der Februar-Post entsteht nie. In den anderen Monaten nur, wenn der Auftraggeber vor diesem Morgen veröffentlicht.

**Vorschlag:** Uhrzeit in den Plan schreiben. Für die Wochenvorschau entweder die Zwei-Tage-Regel für diesen einen Slot aussetzen und den Samstaglauf zulassen, oder den Social-Termin auf Montag legen, nachdem der Beitrag draußen ist. Für die Monats-Tipps den Entwurf so legen, dass nach dem 28. noch ein Job vor der 48-Stunden-Grenze läuft, und den Februar einzeln nennen. Solange der Beitrag nicht veröffentlicht ist, bleibt „Slot entfällt“ richtig.

### 3. Eine Weiterleitung umgeht die Positivliste

**Fundstelle:** Plan E6, `bildZulaessig`. `web/lib/bild-proxy.ts:172–184`: jede Weiterleitung wird nur mit `erlaubteAdresse` geprüft (öffentliche Adresse, http oder https), nicht gegen eine Host-Liste. Bis zu vier Sprünge (`MAX_WEITERLEITUNGEN`).

**Befund:** Die Positivliste gilt für den Host der gespeicherten Adresse. Der bestehende Bildabruf folgt danach auf jeden öffentlichen Host. Ein erlaubter Veranstalter kann auf einen anderen Host weiterleiten, auch auf einen, der in `_VERBOTEN` steht. Die Sperrliste sieht das Ziel nicht. Die Bytes landen im Schnappschuss.

**Vorschlag:** Nach jedem Sprung den Ziel-Host erneut gegen `bild_erlaubnisse` und gegen `_VERBOTEN` prüfen. Ein fremder Ziel-Host wird verworfen, die Folie bekommt das Symbolbild. Die Erlaubnis nennt den Host exakt, ohne automatische Subdomain (`cdn.` zählt nicht als `tonhalle.de`).

### 4. Der Schnappschuss hat keinen Abschluss, und die Erlaubnis wird beim Posten nicht erneut gelesen

**Fundstelle:** Plan E5 (nach dem Schnappschuss wird `bereit`) und E10, Vorab-Prüfung (Datum, Ort, abgelehnt, abgesagt, vorbei). Abschnitt 13, Widerruf einer Erlaubnis.

**Befund:** Der Plan sagt nicht, was gilt, wenn drei von neun JPEG hochgeladen sind und das vierte scheitert. Werden die drei öffentlichen Dateien verworfen und der Post bleibt `freigegeben`, oder wird `bereit` mit einer kurzen Folienliste gesetzt? Ein Karussell mit fehlenden Folien ginge so online. Die Vorab-Prüfung vergleicht Datum und Ort, nicht Titel, Bild und nicht die Zeile in `bild_erlaubnisse`. Ein Widerruf zwischen Freigabe und Takt ändert den schon gebauten Schnappschuss nicht. Der Post geht mit dem Foto raus. Titel und Bild im Schnappschuss sind das, was freigegeben wurde. Das ist richtig, solange der Admin die Abweichung sieht.

**Vorschlag:** `bereit` erst, wenn jede Folie als JPEG im Bucket liegt. Bei Abbruch die angefangene Version löschen, Status bleibt `freigegeben`. Unmittelbar vor dem ersten Kanal die Erlaubnis der verwendeten Hosts erneut lesen. Widerruf setzt den Post auf `fehler` und postet nicht. Ein geänderter Event-Titel ist kein Abbruch. Der Admin sieht im Protokoll, dass der Schnappschuss vom Live-Titel abweicht.

### 5. „Jetzt posten“ hat keinen Übergang

**Fundstelle:** Plan Abschnitt 8, Button „Jetzt posten“. E10 nennt ihn nicht. E9: veröffentlichen tut nur der Takt, und nur aus `bereit`.

**Befund:** Zwei Lesarten. Die sichere: der Button setzt an einem Post in `bereit` nur `geplant_fuer = now()`, der nächste Takt beansprucht. Die unsichere: die Admin-Route postet selbst oder setzt `bereit` aus `vorschlag` oder `freigegeben`, bevor der Schnappschuss da ist. Ein zweiter Weg neben dem Takt kann doppelt posten, weil der Anspruch dann nicht der einzige Einstieg ist. Zwei offene Admin-Tabs und ein zweiter Job sind durch `social_status_setzen` und `social_vorschlag_setzen` abgedeckt, dieser Button nicht.

**Vorschlag:** Eine Zeile in E10. „Jetzt posten“ ist ein bedingtes Update nur aus `bereit`: `geplant_fuer = now()`. Die Route ruft Meta nicht auf. Aus jedem anderen Status tut der Button nichts.

### 6. Das Admin-Protokoll bekommt unter `service_role` keine Admin-ID

**Fundstelle:** Plan Abschnitt 7: die vier Funktionen nur für `service_role`, „Admin-Protokoll wie die anderen Funktionen“. `database/admin_grundlagen_2026-11-23.sql:19`: `admin_id UUID NOT NULL DEFAULT auth.uid()`. `database/admin_magazin_2026-11-23.sql:18–29`: die bestehenden Admin-Funktionen rufen `admin_pflicht()` auf und sind für `authenticated` gedacht, nicht für `service_role`.

**Befund:** `search_path`, `SECURITY DEFINER`, wiederholbares SQL und eine Kontrollabfrage passen zu den vorhandenen Dateien. Der Unterschied ist der Aufrufer. Die Magazin-Funktionen laufen als eingeloggter Admin, `auth.uid()` füllt `admin_id`. Die Social-Funktionen laufen als `service_role`. Dann ist `auth.uid()` leer, und ein Protokolleintrag ohne eigene Admin-ID verletzt `NOT NULL`. `social_bearbeiten` hat einen Nutzer. `social_status_setzen` und `social_beanspruchen` haben keinen. Der Job hat auch keinen Admin. Das ist in Ordnung, wenn der Protokolleintrag die ID nur bei einer Admin-Aktion setzt und der Job eine Zeile ohne Admin schreibt oder gar nicht protokolliert. Der Default allein trägt das nicht.

**Vorschlag:** In den Funktionen `admin_id` ausdrücklich setzen: der übergebene Nutzer bei Freigabe, Ablehnung und Bearbeitung, `NULL` ist dort nicht erlaubt. Dafür die Spalte nicht über den Default füllen. Job-Läufe protokollieren ohne Admin-ID nur, wenn die Spalte das hergibt, sonst eine eigene Notiz in `social_posts`. `admin_pflicht()` in diesen Funktionen nicht aufrufen. Sie würde den Service-Aufruf ablehnen. `EXECUTE` bleibt bei `service_role`.

---

## Gering

### 7. Ein Slot ohne Events hat keine Regel

**Fundstelle:** Plan E2, E4, E7. `wochenendProgramm` verlangt Uhrzeit und Stufe mindestens 1 (`web/lib/ableitungen.ts`, wie im Plan beschrieben).

**Befund:** Ein stiller Montag, ein Feiertag oder ein dünner Januar kann null, ein oder zwei Events liefern. Der Plan sagt nicht, ob der Slot entfällt. Ein Karussell nur aus Titel und Schluss hat zwei Folien. Ein Feed-Einzeltipp ohne Highlight hat keine Folie. Die Obergrenze „zwei je Kategorie, mindestens ein Freier“ kann das Wochenende unter acht Events drücken. Das ist kein Fehler, nur ungesagt. Die Story würde mit `story_auto` Titel und Schluss trotzdem posten.

**Vorschlag:** Unter zwei Events entfällt Karussell, Reel und Einzeltipp. Die Story entfällt unter einem Event, auch bei `story_auto`. Die Kategorie-Obergrenze bleibt.

### 8. Die Caption-Prüfung deckt nicht, was der Prompt fragt

**Fundstelle:** Plan 5.1 (die Route gibt `beschreibung_kurz` mit) und 5.2 („keine fremden Texte im Wortlaut“). 5.3 prüft Datum, Preis-Wörter, „ausverkauft“, Handles, Hashtags, Länge.

**Befund:** `beschreibung_kurz` ist nirgends hergeleitet. Der einzige Event-Text in der Datenbank ist `beschreibung`. Schickt die Route den Quellentext, bekommt das Modell den Wortlaut, den 5.2 ausschließt. 5.3 erkennt eine übernommene Formulierung nicht. Uhrzeiten, erfundene Namen und umschriebene Preise („keine Karten mehr“) erkennt die Prüfung auch nicht. Die Freigabe sieht die Caption. Stories haben keinen Modelltext. Tote Handles, die dem Muster entsprechen und in `ort_instagram` stehen, fallen nicht auf. Ein totes `@` bricht den Post in der aktuellen Doku nicht. Hashtags: drei feste plus höchstens fünf aus der Liste, zusammen acht, unter der Grenze von 30.

**Vorschlag:** `beschreibung_kurz` aus den eigenen Feldern bauen (Titel, Ort, Datum, Uhrzeit, Preis), nicht aus `beschreibung`. Die Prüfung bleibt der Auffang. Die Freigabe bleibt die Sperre.

### 9. Schritt 1 lässt die Agenten-Anleitungen stehen

**Fundstelle:** Plan Schritt 1 nennt `CLAUDE.md` und `HANDOVER.md`. `agents/developer/CLAUDE.md`, `agents/qa/CLAUDE.md` und `agents/orchestrator/CLAUDE.md` beschreiben weiter `publisher.py`, `caption_generator.py` und `openai`.

**Befund:** Im lauffähigen Code hängen an den beiden Dateien nur `main.py`, `test_pipeline.py`, `tests/test_vorschau.py`, `test_instagram.py`, `config.py` und `.env.example`. Die nennt Schritt 1. Die drei Agenten-Dateien nicht. Sie posten nichts, sie schicken den nächsten Bau in die gelöschten Dateien.

**Vorschlag:** Dieselben drei Dateien in Schritt 1 auf den neuen Social-Weg umschreiben oder die alten Absätze streichen.

### 10. Eine Zeilenangabe ist verrutscht

**Fundstelle:** Plan E4, „`ableitungen.ts:738–744`“. Die Funktion `startPlaetze` beginnt in `web/lib/ableitungen.ts:756` und gibt in Zeile 804 den Tipp und bis zu vier Picks zurück.

**Befund:** Die Aussage stimmt, die Zeile nicht. Die übrigen nachgesehenen Stellen stimmen: `categorizer.py:182–189`, `caption_generator.py:218` und `:254`, `magazin.yml:11–13`. Der Kopf des Plans sagt weiter „Bestand am 25.11.2026“.

**Vorschlag:** Die Zeile auf 756–804 setzen und das Bestandsdatum auf den Tag der dritten Fassung.

### 11. Der Plan nennt keine Kosten

**Fundstelle:** Plan Abschnitt 11 und 13. Kein Betrag.

**Befund:** Stories rufen kein Modell. In einer normalen Woche sind es ein Einzeltipp, ein Wochenend-Karussell, ein Reel und eine Wochenvorschau, plus einmal im Monat die Monats-Tipps. Je Aufruf ein zweiter Versuch, wenn die Prüfung anschlägt. Das sind etwa vier bis acht Sonnet-Aufrufe in der Woche, kurze Prompts. ffmpeg läuft einmal je Woche für ein Video von etwa 25 Sekunden. Die JPEG und das eine MP4 löscht der Plan 30 Tage nach `gepostet` oder `verfallen`. Die Menge ist klein. Ein Euro-Betrag wäre eine Schätzung ohne die aktuellen Preise und steht deshalb hier nicht als Zahl.

**Vorschlag:** Im Plan die Mengen nennen (Modellaufrufe je Woche, ein Video, Löschfrist), keinen erfundenen Preis.

### 12. Livegang kann vor den Anwaltsantworten liegen

**Fundstelle:** Plan Schritt 7, 8 und 9. Anhang B ersetzt den Datenschutztext.

**Befund:** Schritt 7 läuft ab Schritt 2 parallel. Schritt 8 setzt `modus = vorschau` und liefert den neuen Datenschutztext mit aus. Schritt 9 setzt `modus = an`. Nichts im Plan hält Schritt 8 oder 9 an, bis A1 bis A6 beantwortet sind. Impressum (`web/app/impressum/page.tsx`) nennt Instagram und Facebook nicht. Partnerlinks (Quellen-Ausbau P2) stehen nicht in der Caption. Facebook verlinkt nur `/event/...`. Ein neuer Rechtswiderspruch über A1 bis A6 hinaus ist das nicht. A1 bis A6 sperren die technische Freigabe laut Prüfauftrag nicht.

**Vorschlag:** Den Datenschutzabsatz erst in den Deploy nehmen, wenn A1 beantwortet ist. `modus = an` erst danach.

### 13. `aus` und `vorschau` überspringen das Aufräumen

**Fundstelle:** Plan E9, Schritt 1 des Takts, und E10 zu Fehler 190.

**Befund:** Bei `aus` oder `vorschau` kehrt der Takt sofort zurück. `container_wartet` und `wird_gepostet` bleiben liegen. Es wird nichts veröffentlicht. Ein Reel-Container kann bei Meta verfallen, während die Zeile wartet. Kommt `an` zurück und `container_seit` ist älter als 60 Minuten, setzt der nächste Takt `fehler`. Fehler 190 schaltet auf `vorschau` und lässt den laufenden Post in `wird_gepostet`. Der nächste Takt räumt nicht auf. Erst nach der Rückkehr auf `an` wird daraus `unklar`, wenn die 15 Minuten um sind. Ein halbfertiger Post (`teilweise`) wird in der Zwischenzeit nicht erneut versucht. Ein Doppelpost entsteht so nicht.

**Vorschlag:** 190 setzt den Post, der gerade `wird_gepostet` ist und keine Media-ID für den offenen Kanal hat, auf `teilweise` oder `unklar`, bevor der Modus auf `vorschau` geht. `aus` lässt die Zeilen stehen. Das ist gewollt und sollte in E9 stehen.

---

## Was die Fragen sonst ergeben haben

**Doppelpost.** Der bekannte Rest bleibt: „erneut posten“ nach `unklar`, wenn die Media-ID nach einem Absturz fehlt. Ein zweiter Weg ist im Text offen. Eine klare Fehlerantwort setzt den Post zurück und der nächste Takt versucht es erneut. Antwortet Meta mit einem Fehler, obwohl der Post schon online ist, entsteht ein zweiter Post ohne Menschenentscheid. „Ohne Antwort“ ist dagegen richtig auf `unklar` gelegt. Zwei Tabs, zwei Jobs und Freigabe eine Minute vor der Uhrzeit ergeben keinen zweiten Post: der Schnappschuss setzt `bereit` erst danach, und der Anspruch ist ein bedingtes Update. Der Reel-Job setzt nur `freigegeben` auf `bereit`. Zeitumstellung: kein Slot liegt in der fehlenden Stunde (02:00 bis 03:00). `tag` setzt der Einrichter als Berliner Datum. Ein späteres Verschieben von `geplant_fuer` über die Umstellung hinweg kann `tag` und Berliner Kalendertag auseinanderlaufen lassen. Die festen Uhrzeiten tun das nicht.

**Auswahl und Caption.** Die Startseiten-Regeln sind im Plan richtig an `pool.heute` und an `magazinPoolLaden` gebunden. Leere Slots: Befund 7. Caption: Befund 8.

**Bilder.** Symbolbilder sind eigene KI-Bilder, keine abgeleiteten Veranstalterfotos (`docs/fallback-bilder.md`). Magazin-Hero und Google-Fotos in `orte.extras` nimmt die Positivliste nicht auf. CC-BY-Ortsbilder scheitern an der Liste, solange die Erlaubnis an der CSV-Lizenz hängt. Die Weiterleitung ist Befund 3. Ob eine öffentliche Supabase-URL von Meta abgerufen wird (Content-Type, Umleitung auf eine Signatur-URL), ist ohne einen echten Bucket nicht prüfbar. Der Plan verlangt JPEG, `Content-Type: image/jpeg`, keine Umleitung. Das ist die richtige Vorgabe.

**Satori.** `ImageResponse` zeichnet PNG, sharp macht daraus JPEG. Schriften müssen Dateien sein. Das steht im Plan und in der Next-Doku. `node_modules` ist in diesem Stand nicht installiert. Ob Satori die WebP-Dateien unter `web/public/ort-bilder/` und `web/public/fallback/` einbetten kann, ist hier nicht prüfbar. Die Next-Doku nennt die Bildformate nicht. Vor dem Einbetten mit sharp nach PNG zu wandeln schließt die Lücke, ohne die Bibliothek raten zu müssen. Der Server vom 23.11. ist durch die Bremse nur für `/guides` geschützt. Die Folien laufen nur in der Admin-Vorschau und im Takt, nicht als öffentliche Route. Ein Karussell mit zehn großen PNG auf demselben Prozess kann den Speicher trotzdem heben. Die vorhandene Grenze von zwei gleichzeitigen sharp-Verkleinerungen (`bild-proxy`) auf diesen Pfad zu legen ist der naheliegende Schutz. Gemessen ist das hier nicht.

**Schlüssel und Notaus.** `META_TOKEN`, `META_IG_ID`, `META_PAGE_ID` und beide Social-Schlüssel nach `web/.env.local`, nach dem Muster in `deploy.yml` (Länge loggen, Wert nicht). `SOCIAL_JOB_SCHLUESSEL` zusätzlich als GitHub-Secret für `social.yml`. `META_TOKEN` nicht in `social.yml`. `SOCIAL_TAKT_SCHLUESSEL` im Vault und als GitHub-Secret für den Deploy. Der Seiten-Token bleibt im Speicher. Ob `pg_net` die Anfrage-Header in `net._http_response` ablegt und der Takt-Schlüssel damit in der Datenbank steht, ist ohne das Projekt nicht prüfbar. Die Anleitung sollte den Aufruf so bauen, dass der Schlüssel nicht in einer gespeicherten URL steht. `pg_cron`, `pg_net` und `vault` sind im Repo nicht angelegt. Ob das Supabase-Projekt sie hat, ist nicht prüfbar. `modus = aus` stoppt den nächsten Takt innerhalb von fünf Minuten und löscht keine schon veröffentlichten Stories. Die bleiben bis zu 24 Stunden, das Löschen in der App klärt Schritt 0. Das ist im Plan gesagt.

**Schritte und Tests.** Schritt 1 kann vor dem SQL live gehen. Schritt 8 vor `pg_cron` postet nichts, solange niemand den Takt von Hand aufruft. Die Tests aus Abschnitt 12 treffen die Zustände aus E10 und die Positivliste. Sie treffen nicht: eine halbe Folienliste, „Jetzt posten“ gegen den Takt, Widerruf zwischen Freigabe und Post, Weiterleitung auf einen fremden Host, ffmpeg ohne `faststart`, den Freitagmorgen gegen den Magazin-Cron, den Februar, WebP in Satori, den Vault-Header. Beispieldaten: `magazinPoolLaden` wirft, die Route antwortet 503. Der Testpunkt „503 bei Beispieldaten“ ist damit richtig, auch wenn der Pool kein `quelle: beispiel` zurückgibt.

**Was später gehen kann, ohne S1 bis S4 zu verletzen.** Reels, das Wochenend-Karussell, die tägliche Story und der Einzeltipp bleiben. Facebook ist schon ein Schalter und kann aus bleiben. Wochenvorschau und Monats-Tipps können in eine zweite Stufe, bis die Uhrzeiten aus Befund 2 stehen. `@`-Handles und die Erinnerungsmail auch. Commons, Insights und Collaborators sind im Plan schon später.

**Nicht prüfbar:** ob Meta eine Supabase-URL abruft, ob Satori WebP lädt, ob `pg_cron`, `pg_net` und `vault` im Projekt an sind, ob `net._http_response` den Takt-Schlüssel speichert, der echte App-Review, der Speicher des Servers am 23.11.

---

## Gesamturteil

**Freigabefähig: nein.**

Der Automat aus E10 ist in sich geschlossen, und der bekannte Doppelpost bleibt der eine Fall „erneut posten“ ohne gespeicherte Media-ID, plus die offene Einordnung einer Fehlerantwort nach gelungenem Post. Die Bild-Positivliste ist die richtige Regel. Drei Angaben stimmen mit dem, was gebaut werden müsste, nicht überein: die Reel-Datei gegen die Meta-Spezifikation, die Magazin-Slots gegen den Freitags- und den 28.-Cron, die Weiterleitung gegen die Positivliste. Dazu der Schnappschuss ohne Abschluss und „Jetzt posten“ ohne Übergang. Das sind Textkorrekturen, kein neuer Entwurf. Nach diesen fünf mittleren Punkten ist die Fassung bau- und erneut prüfbar. Die Anwaltsfragen A1 bis A6 und die offenen Punkte O2 bis O8 sperren dieses Urteil nicht. O1 (`@dies.das.duesseldorf`) ist beantwortet und im Datenschutztext verwendet.
