# Plan: Automatische Posts auf Instagram und Facebook – dritte Fassung, 26.11.2026

**Status:** ENTWURF zur Freigabe. Gebaut wird erst nach der Freigabe. Cursor-Prüfung 1 (12 Befunde, 2 kritisch) ist eingearbeitet (Anhang E). Cursor-Prüfung 2 urteilt „freigabefähig: ja“; ihre 7 Befunde (4 mittel, 3 gering) sind ebenfalls eingearbeitet (Anhang G).
**Kanäle:** Instagram (Business-Konto, mit der Facebook-Seite verknüpft) und Facebook-Seite [facebook.com/dies.das.duesseldorf](https://www.facebook.com/dies.das.duesseldorf).
**Grundlage:** `CLAUDE.md` (Phase 1: Instagram-Pipeline), Platzhalter im Admin-Plan (`docs/plan-admin-dashboard-2026-11-23.md`, Abschnitte 1.4 und 4.8, Frage Q7). Diesen Plan hat der Admin-Plan als „eigener Plan Instagram-Posting“ vorgemerkt.

---

## 1. Ausgangslage (Bestand am 25.11.2026, Stand origin dd63059)

| Baustein | Zustand | Was damit passiert |
|---|---|---|
| `pipeline/publisher.py` | Graph API v21.0. Kann nur Einzelbild-Feed-Posts (`image_url` + Caption). **Hat nie gepostet:** `INSTAGRAM_ACCESS_TOKEN`/`INSTAGRAM_ACCOUNT_ID` fehlen in `scrape.yml`. Setzt `events.status` auf `gepostet`/`fehler` und mischt damit Posten in den Event-Status. Wird in `main.py` als Schritt 5 aufgerufen. | **entfernen** (Schritt 1). Der Zwei-Schritt-Ablauf (Container anlegen → veröffentlichen) wird im neuen Code in TypeScript nachgebaut. |
| `pipeline/caption_generator.py` | Schreibt in jedem Scraper-Lauf bis zu 50 Captions mit `claude-sonnet-4-6` in `events.instagram_caption` und setzt `status` von `neu` auf `aufbereitet`. **Niemand nutzt sie**, sie kosten nur Geld (Q7 im Admin-Plan). | **entfernen** (Schritt 1). Der Prompt dient als Vorlage. Der Kategorisierer lädt nur `status = neu` mit `beschreibung IS NULL` (`categorizer.py:182–189`). Events mit leerem Text `""` bleiben dort wie bisher `neu`, der Caption-Generator lässt sie ohnehin aus (`caption_generator.py:218`). Der Wegfall ändert die Kategorisierung also nicht. Bei einem API-Fehler setzt der Caption-Generator heute `status = 'fehler'` (`:254`); das fällt mit ihm weg, und vorhandene Werte `aufbereitet`/`fehler` sind unschädlich. Website und Admin filtern nicht auf `status`, `aufbereitet`, `gepostet` oder `instagram_caption`. `dashboard/` gibt es nicht mehr. **Tests und Konfiguration** hängen an beiden Dateien: `tests/test_vorschau.py:94–99`, `test_pipeline.py:26` und `:83`, `config.py:19–20`, `.env.example` (Schritt 1). |
| `test_instagram.py` | Hilfsskript: Account-ID über `/me/accounts` ermitteln. | wird durch `tools/meta_pruefen.py` ersetzt (Schritt 0). |
| `visual/` (brand.py, image_renderer.py, image_generator.py, reel_renderer.py), `assets/templates/`, DALL-E 3, Canva-Vorlagen, ffmpeg-Reels | **Gibt es nicht.** Steht nur in `CLAUDE.md`. `openai` steht in `requirements.txt`, wird aber nirgends importiert. | `CLAUDE.md` und `requirements.txt` aufräumen (Schritt 1). |
| Spalten `events.instagram_caption`, `events.instagram_location_id`, `events.gepostet_am`, Status `aufbereitet/gepostet` | `post_typ` steht nur in `CLAUDE.md`, nicht im Schema. | bleiben vorerst stehen (unschädlich). Löschen in einem späteren Aufräum-SQL. |
| Admin | Menüpunkt „Instagram“ mit Hinweis „eigener Plan“ (`web/app/admin/rahmen.tsx:17`). Tabelle `instagram_posts` im Admin-Plan 4.8 nur vorgemerkt, nicht angelegt. | wird „Social“ (Abschnitt 8). |
| Datenschutzerklärung | Die Abschnitte „Instagram und Facebook (Meta)“ und „Instagram Graph API (automatisches Posting)“ gibt es schon (`web/app/datenschutz/page.tsx:192–224`), inklusive Art. 26 (Seiten-Insights). | kleine Anpassung (Abschnitt 10). |
| `web/lib/seo.ts:44` | Ein Kommentar sagt, dass `sameAs` (Social-Media-Profile) wiederkommt, „wenn Instagram aktiv bespielt wird“. Ein auskommentierter Block ist es nicht. | `sameAs` nach dem Livegang neu eintragen. |
| Marke | Logos `web/public/logo/*.svg`, Farben Navy `#1b2540` und Gold `#c9a84c`, Schriften DM Serif Display und Inter, eigene KI-Symbolbilder `web/public/fallback/` (`docs/fallback-bilder.md`). | Grundlage der Folien. |
| Muster im Projekt | Auswahl über eine Website-Route mit Job-Schlüssel (Magazin `api/magazin/auswahl`, Geburtstag `api/intern/geburtstag-tipps`); Job-Anstoß aus der Website (`web/lib/job-anstoss.ts`); Supabase Storage (`event-bilder`); `sharp` im Web-Paket. | wiederverwenden. |

**Wichtig für den Takt:** Zeitpläne in GitHub Actions sind unzuverlässig. Die Magazin-Wochenvorschau kam am Freitag um 23:58 statt um 18 Uhr, und der 15-Minuten-Zeitplan der Newsletter-Bestätigung lief am 24.11. gar nicht (`web/lib/job-anstoss.ts:1–3`). Feste Postzeiten können deshalb nicht an einem GitHub-Zeitplan hängen (E9).

---

## 2. Entscheidungen des Auftraggebers (25.11.2026)

| Nr. | Entscheidung |
|---|---|
| S1 | **Formate:** Karussell, tägliche Story, Feed-Einzeltipp **und Reels gleich zum Start**. |
| S2 | **Freigabe:** Feed-Posts, Karussells und Reels brauchen eine Freigabe im Admin. **Stories laufen automatisch** (mit Notaus). |
| S3 | **Bilder:** eigene Grafiken im Markenstil und eigene KI-Symbolbilder (gekennzeichnet), **dazu Veranstalterfotos, wenn das Haus schriftlich zugestimmt hat** (Liste im Admin). |
| S4 | **Meta:** Das Instagram-Business-Konto existiert und ist mit der Facebook-Seite verknüpft. |

---

## 3. Vorschläge zur Bestätigung

| Nr. | Frage | Vorschlag |
|---|---|---|
| E1 | Datenmodell | **Eigene Tabellen** `social_posts`, `social_einstellungen` und `bild_erlaubnisse` (Abschnitt 7). `events.status` wird für Social nicht mehr benutzt. Ein Post kennt seine Events über `event_ids uuid[]`. |
| E2 | Wochenplan und Zeiten (Europe/Berlin) | **Story täglich 08:30** „Heute in Düsseldorf“. **Di 18:00** Feed-Einzeltipp „Tipp der Woche“. **Do 17:00** Karussell „Wochenende in Düsseldorf“. **Fr 12:00** Reel zum Wochenende. **So 18:00** Karussell „Deine Woche“ aus der Magazin-Wochenvorschau. **Am 1. jedes Monats um 18:00** Karussell „Top-Events im <Monat>“ aus den Monats-Tipps. Das sind 4 Feed-Posts in der Woche plus 7 Stories. Der Plan steht als JSON in `social_einstellungen.wochenplan` und lässt sich ohne Deploy ändern. Der Job legt Vorschläge für die **nächsten 4 Tage** an. Das Wochenend-Karussell (Do) und das Reel (Fr) entstehen deshalb **im selben Lauf am Montag oder Dienstag**, beide als `vorschlag` (Befund 6). |
| E3 | Auswahl der Events | Rechnet die Website. Eine interne Route `POST /api/intern/social-auswahl` nutzt dieselbe Logik wie Startseite und Magazin, damit Social nie etwas anderes empfiehlt als die Website (Abschnitt 5). |
| E4 | Texte | **Claude Sonnet 5.5** (`claude-sonnet-5-5`) schreibt die Captions für Instagram und Facebook sowie je Folie eine kurze Zeile „Warum hin?“ (höchstens 80 Zeichen). Anrede **du**, Marke „dies.das.düsseldorf“. Danach laufen Prüfungen wie beim Magazin (Abschnitt 5.3). **Stories bekommen keinen KI-Text**, nur Daten aus der Datenbank (Titel, Zeit, Ort, Kategorie). So bleibt der automatische Teil frei von KI-Fehlern. |
| E5 | Wie entstehen die Bilder? | Die Folien rendert **die Website selbst** mit `next/og` (Satori), `sharp` macht daraus JPEG. Formate: Feed **1080×1350** (4:5), Story und Reel **1080×1920** (9:16). Alle Folien eines Karussells sind dasselbe 4:5-JPEG, weil Meta jedes Karussell auf das Format der ersten Folie zuschneidet (Standard 1:1). Die Vorschau im Admin zeigt genau dieses Bild. **Bei der Freigabe** (bei Stories: beim Posten) wird ein **Schnappschuss** als JPEG in den öffentlichen Storage-Bucket `social` gelegt. Meta holt die Bilder von dort und nicht von unserem Server (keine Last, keine Bremse aus `lib/bremse.ts`). Gepostet wird, was freigegeben wurde. **Alternative:** Rendern mit Playwright im GitHub-Job. Das ist langsamer, und die Vorschau im Admin wäre nicht sofort da. |
| E6 | Bildquelle je Folie (Rangfolge) | Die Herkunft eines Bildes erkennt der Code **am Host der gespeicherten `bild_url`**, nicht an `quelle_name`. Nach dem Zusammenführen von Dubletten kann das Bild von einer anderen Quelle stammen (`pipeline/deduplication.py`), eine Herkunftsspalte gibt es nicht (Befund 4). Rangfolge: (1) **Veranstalterfoto**: nur wenn der Host von `bild_url` in den `hosts` einer gültigen Erlaubnis in `bild_erlaubnisse` steht (z. B. `tonhalle.de`, `www.tonhalle.de`) und nicht auf der Sperrliste. Die Folie zeigt dann „Foto: <Nennung laut Erlaubnis>“. (2) **Ortsbild** aus `web/public/ort-bilder/`, nur wenn `data/spielstaetten/bilder.csv` für den Slug als `lizenz` `CC0`, `Public Domain`/`Public domain` oder `Gemeinfrei (Public Domain)` nennt, oder wenn es ein eigenes Bild des Auftraggebers ist (Ordner `web/public/ort-bilder/weihnachtsmaerkte/` ohne `koe-on-ice.webp`, Ordner `web/public/ort-bilder/events/`). Die Zuordnung Slug → Lizenz erzeugt ein Skript beim Bau als `web/lib/social/ortsbild-lizenzen.json`; ein Test prüft, dass sie zu `bilder.csv` passt. **Google-Fotos** (`orte.extras.google_foto`, Route `/ort-foto/…`) sind **nie** zulässig. (3) **KI-Symbolbild** aus `web/public/fallback/`, mit dem Hinweis „Symbolbild · KI-generiert“ auf der Folie. (4) **Reine Grafik** ohne Foto. **Sperrliste, auch mit Erlaubnis nie:** dieselbe Hostliste wie `_VERBOTEN` in `scraper/orte/ortsbilder.py:52` (Google, Eventim, Ticketmaster, Reservix, Rausgegangen, Prinz, AllEvents, Eventbrite, Meetup, Facebook/Instagram-CDN), dazu Eventfinder und meinestadt. Sie steht als gemeinsame Liste in `web/lib/social/bildquellen.ts`, ein Testvektor hält sie gleich mit der Python-Liste. **Pfade ohne Host** (Cursor-Prüfung 2, Befund 4): `events.bild_url` kann ein eigener Pfad sein (`/ort-bilder/…`), und `lokalesBild()` akzeptiert jeden Ordner darunter. Relative Pfade gelten deshalb nur aus einer **Positivliste**:
- `/ort-bilder/orte/<slug>…` nur mit erlaubter Lizenz laut `bilder.csv`
- `/ort-bilder/weihnachtsmaerkte/…` **außer `koe-on-ice.webp`** (Fremdfoto, wie `FREMDFOTO` in `web/lib/magazin-bilder.ts:40`)
- `/ort-bilder/events/…` (eigene Fotos der kleinen Märkte, `scraper/tier3/kleine_weihnachtsmaerkte.py:7`)
- `/fallback/…` als Symbolbild

Alles andere fällt durch. **`/bild/event/<id>` ist nie eine Bildquelle**, denn dieser Proxy-Pfad verdeckt den Host. Die Folie speichert in `bild` zusätzlich `original` (die gespeicherte `bild_url` bzw. den Pfad) und `host`, sodass Schnappschuss und Admin dieselbe Prüfung auf der ursprünglichen Adresse wiederholen können.

**Dieselbe Prüfung** (`bildZulaessig(original)` in `web/lib/social/bildquellen.ts`) gilt beim Vorschlag in der Auswahl-Route, beim Umstellen der Bildquelle und beim Tauschen von Events im Admin sowie beim Schnappschuss. |
| E7 | Freigabe-Ablauf | Vorschläge für Feed, Karussell und Reel entstehen **mindestens 2 Tage vorher** als `vorschlag`. Ohne Freigabe bis zur Postzeit wird ein Post zu `verfallen`: Es wird nichts gepostet, es gibt keinen Ersatz. Stories legt der Job mit `status = 'freigegeben'` und `freigegeben_von = 'auto'` an, solange `story_auto` an ist. Bis zur Postzeit lassen sie sich im Admin verwerfen. **Das Reel** lässt sich erst freigeben, wenn das Wochenend-Karussell derselben Woche freigegeben ist. Bei seiner Freigabe übernimmt es dessen `event_ids` und Folien. Die Zwei-Tage-Regel gilt für das Reel dann nicht mehr; der Admin zeigt „wartet auf Karussell“ bzw. „Video wird gebaut“. **Jede Bearbeitung** nach der Freigabe (Caption, Events, Bild, Zeit) setzt den Post zurück auf `vorschlag`, weil der Schnappschuss nicht mehr stimmt. Das geht **nur aus `freigegeben` und `bereit`**. In `wird_gepostet`, `container_wartet`, `teilweise`, `unklar` und `gepostet` ist der Post gesperrt: Die Funktion lehnt ab, und der Admin zeigt „wird gerade gepostet“ bzw. „schon online“ (Cursor-Prüfung 2, Befund 2). **Karussell und Reel hängen zusammen** (Befund 3): Wird das Wochenend-Karussell bearbeitet oder verworfen, setzt dieselbe Aktion das Reel derselben Woche mit auf `vorschlag`, sofern es noch `freigegeben` oder `bereit` ist. Dabei wird `video_url` geleert und das alte Video gelöscht. Die nächste Reel-Freigabe kopiert Events und Folien neu und stößt den Video-Bau wieder an. Ist das Reel schon in einem gesperrten Status, wird das Karussell nicht zurückgesetzt, und der Admin sagt warum. **Kurz vor jedem Post** prüft der Takt erneut: Ist ein Event inzwischen abgelehnt, abgesagt, vorbei oder geändert (Datum oder Ort anders als beim Schnappschuss)? Bei Stories fällt dann nur diese Folie weg. Bei Feed, Karussell und Reel wird nicht gepostet, der Post wird `fehler` mit Grund und erscheint im Cockpit. |
| E8 | Was geht auf Facebook? | Feed-Einzeltipp, Karussell (als Beitrag mit mehreren Fotos) und Reel, **mit klickbaren Links** auf die Event-Seiten (`/event/<kategorie>/<slug>`) bzw. den Magazin-Beitrag. **Facebook-Stories nicht** (geringe Reichweite, eigener API-Weg). Instagram-Captions enthalten keine Links, sondern „Link in Bio“ (E14). Facebook lässt sich in `social_einstellungen.facebook` getrennt abschalten. |
| E9 | Wo läuft was? | **Vorbereiten** (Auswahl abrufen, Texte mit Claude, Prüfungen, Reel-Video mit ffmpeg) läuft im **GitHub-Job** `social.yml`: täglich gegen 04:00 UTC, manuell und per Anstoß aus dem Admin. Die Vorschläge liegen Tage im Voraus, deshalb schadet ein verspäteter Lauf nicht. **Veröffentlichen** übernimmt die **Website** (Next.js auf unserem Server) in `POST /api/intern/social-takt`. Diese Route ruft **Supabase `pg_cron` + `pg_net` alle 5 Minuten** auf, mit einem Schlüssel aus dem Supabase-Vault. Der Meta-Token liegt nur auf dem Server. **Alternative zum Auslöser:** ein `crontab`-Eintrag auf dem Server (`curl` alle 5 Minuten), den der Auftraggeber anlegt wie den nginx-Block. |
| E10 | Zustandsautomat und Schutz vor doppelten Posts | **Nur `bereit` ist postbar, und `bereit` entsteht nur aus `freigegeben`** (Befund 2). Übergänge, jeweils als bedingtes `UPDATE … WHERE id = … AND status = <alt> RETURNING`: <br>• `vorschlag → freigegeben` (Admin) bzw. Anlage als `freigegeben` (Story auto). <br>• `freigegeben → bereit`: Feed und Karussell sofort bei der Freigabe nach dem Schnappschuss; Story im Takt nach dem Schnappschuss; Reel erst, wenn der Job das Video hochgeladen hat (`WHERE status = 'freigegeben'`, sonst verwirft der Job sein Video). <br>• **Beanspruchen** im Takt: `UPDATE … SET status = 'wird_gepostet', takt_am = now() WHERE id = … AND status IN ('bereit','teilweise','container_wartet') AND geplant_fuer <= now() RETURNING`. Die **Auswahl** der fälligen Posts benutzt **genau diese Bedingung**; ein Post in `wird_gepostet` wird nie ausgewählt. <br>• Ein Aufruf arbeitet einen beanspruchten Post vollständig ab (höchstens 45 s) und setzt am Ende `gepostet`, `teilweise`, `container_wartet` oder `fehler`. `wird_gepostet` gibt es also nur während eines laufenden Aufrufs. **Fortschritt je Kanal und Folie** wird nach jedem Meta-Aufruf sofort gespeichert (`ig_container_ids[n]`, `ig_media_ids[n]`, `fb_post_id`, `fb_video_id`). Ein erneut beanspruchter Post bearbeitet **nur Kanäle und Folien ohne gespeicherte Media-ID** (gilt für `teilweise`, Story-Folien nach Abbruch und „erneut posten“). <br>• **Reel-Container in Arbeit:** Ist `status_code = IN_PROGRESS`, setzt der Aufruf `container_wartet` (nicht `wird_gepostet`), und der nächste Takt fragt erneut. `FINISHED` → veröffentlichen. `ERROR`/`EXPIRED` oder länger als 60 Minuten → `fehler` (nichts wurde veröffentlicht). <br>• **Unklar:** Steht ein Post länger als 15 Minuten auf `wird_gepostet`, ist der Aufruf abgebrochen → `unklar`. Ebenso sofort `unklar`, wenn ein `media_publish`- oder Facebook-Veröffentlichen-Aufruf **ohne Antwort** endet (Zeitüberschreitung, Netzfehler). **Nie ein automatischer zweiter Versuch** nach einem Veröffentlichen-Aufruf ohne Antwort. Bei `unklar` schaut der Auftraggeber in der App nach und markiert im Admin „ist online“ (→ `gepostet`) oder „erneut posten“ (→ `teilweise`, nur fehlende Kanäle/Folien). <br>• **Wiederholbar** sind nur Fehler mit klarer Fehlerantwort von Meta (Container ließ sich nicht anlegen, Limit, Bild nicht abrufbar): `teilweise` bzw. `bereit` bleibt, `versuche + 1`, höchstens 3, dann `fehler`. <br>• **Frist:** Ist ein Post 6 Stunden nach `geplant_fuer` noch nicht auf einem Kanal online, wird er `verfallen`; ist er `teilweise`, wird er `fehler` mit „Facebook/Instagram nicht nachgeholt“. Freigegebene, aber nie `bereit` gewordene Posts (Reel-Video nicht fertig) verfallen ebenso. Ausnahme: `container_wartet` unter 60 Minuten bleibt stehen; die 60-Minuten-Regel greift vor der Frist (Abschnitt 8, Takt-Route Punkt 2). |
| E11 | Reels | Eine **Diashow in 9:16** aus den Wochenend-Events: Titelfolie, bis zu 8 Event-Folien (je etwa 2,5 s, leichter Zoom, weiche Überblendung) und eine Schlussfolie, zusammen etwa 25 s. ffmpeg im GitHub-Job baut sie aus den Schnappschuss-JPEGs (H.264, AAC-Stille, 30 fps). **Ohne Musik**, weil die Musikbibliothek von Instagram über die API nicht nutzbar ist (O6). Das Titelbild ist die erste Folie (`cover_url`), `share_to_feed = true`. Weil Instagram das Reel-Cover im Raster auf das mittlere Quadrat schneidet, steht alles Wichtige der Titelfolie im mittleren Quadrat (Befund 5). Vorschlag zusammen mit dem Karussell, Freigabe und Video wie in E7/E10: Die Freigabe stößt `social.yml reel --post <id>` über `lib/job-anstoss.ts` an. |
| E12 | Schalter | In der Datenbank, damit sie sofort wirken (der Takt liest sie bei jedem Aufruf): `social_einstellungen.modus` (`aus` = nichts / `vorschau` = Vorschläge ja, Posten nein / `an`), `story_auto`, `facebook`. Im Admin unter Social. Die GitHub-Variable `SOCIAL_AKTIV` schaltet nur den Job (`1` = Vorschläge erzeugen). |
| E13 | Token | Ein **Token für einen Systembenutzer** im Business-Portfolio, **ohne Ablauf**, nur mit den nötigen Rechten (Abschnitt 9). Er liegt als Secret `META_TOKEN` nur in `web/.env.local` auf dem Server. Nur `deploy.yml` schreibt ihn dorthin, wie die Job-Schlüssel. `social.yml` übernimmt ihn **nicht** in `env:`. **Instagram und Facebook rufen wir beide mit dem Seiten-Token auf**, den der Server aus `GET /{page-id}?fields=access_token` mit dem Systembenutzer-Token holt (im Speicher, höchstens 1 Stunde). Bei Instagram mit Facebook-Login verlangt Meta den Seiten-Token (Befund 5). Lässt Meta den Systembenutzer ohne Freischaltung nicht zu, gibt es als **Ersatzweg** ein Seiten-Token ohne Ablauf, abgeleitet aus einem langlebigen Nutzer-Token des Auftraggebers. Ein Token-Fehler (Code 190) schaltet `modus` auf `vorschau` und meldet das im Cockpit. |
| E14 | „Link in Bio“ | Eine neue Seite **`diesdas.events/links`**. Sie zeigt die Events der Posts der letzten 7 Tage mit Links zu den Event-Seiten, den neuesten Magazin-Beitrag sowie Impressum und Datenschutz. Ohne Cookies und ohne Tracking, `noindex`. Diese Adresse steht in der Instagram-Bio. So ist das Impressum mit 2 Klicks erreichbar (Abschnitt 10). |
| E15 | Häuser erwähnen | Hat der Ort eines Events in `orte.instagram` ein Profil, nennt die Caption es als `@handle`, höchstens 3 je Post und nur, wenn das Muster passt (`^[A-Za-z0-9._]{1,30}$`). Das bringt Reichweite, und Häuser teilen solche Posts oft. Markierungen im Bild (`user_tags`) und Einladungen als Mitwirkende (`collaborators`) kommen erst später. |
| E16 | Erinnerung an Freigaben | Im **Cockpit**: „x Social-Posts warten auf Freigabe, der nächste in y Stunden“. Dazu eine **Sammelmail** an `hallo@diesdas.events`, wenn ein Post der nächsten 36 Stunden noch nicht freigegeben ist. Höchstens eine Mail am Tag, verschickt aus dem täglichen Job über das vorhandene SMTP-Postfach (wie `geburtstag_mails.py`). |
| E17 | Altbestand | **Captions und Publisher jetzt entfernen** (Q7 = ja, Schritt 1), unabhängig vom Rest dieses Plans. Das spart sofort die Kosten für bis zu 50 Captions je Lauf. |

---

## 4. Formate im Einzelnen

Alle Folien folgen einem gemeinsamen Raster: Navy-Fläche oder Foto mit Abdunklung, Wortmarke „dies.das.düsseldorf“ klein oben, Gold als Akzentfarbe für Datum und Kategorie, Titel in DM Serif Display, Angaben in Inter. Die Entwürfe gibt der Auftraggeber vor dem Bau frei (Schritt 2).

| Format | Slot (`slot`) | Inhalt | Folien | Caption |
|---|---|---|---|---|
| **Story** „Heute in Düsseldorf“ | `story-heute` | Tipp des Tages und die ersten 3 Picks des Tages (die Startseite liefert Tipp + bis zu 4 Picks, `web/lib/ableitungen.ts:738–744`) | 1 Titelfolie („Heute · Mi 26.11.“), bis zu 4 Event-Folien (Foto/Symbolbild, Kategorie, Titel, Uhrzeit, Ort, „gratis“ falls zutreffend), 1 Schlussfolie („Alle Tipps auf diesdas.events“). **Jede Folie ist eine eigene Veröffentlichung** (`media_publish` je Folie, also bis zu 6). Nach einem Abbruch gilt E10: gespeicherte Folien werden nicht erneut veröffentlicht. | keine (Stories haben keine Caption, Link-Sticker gibt es über die API nicht) |
| **Feed-Einzeltipp** „Tipp der Woche“ | `tipp-woche` | Highlight der kommenden 7 Tage | 1 Folie, 4:5 | IG: 2–4 Sätze, Datum/Zeit/Ort, „Mehr: Link in Bio“, bis zu 8 Hashtags. FB: dasselbe ohne Hashtag-Block, mit Link zur Event-Seite |
| **Karussell** „Wochenende in Düsseldorf“ | `wochenende` | Fr–So, bis zu 8 Events | Titelfolie, bis zu 8 Event-Folien, Schlussfolie (höchstens 10) | IG: kurze Einleitung und je Event eine Zeile (Tag, Titel, Ort). FB: dasselbe mit einem Link je Event |
| **Reel** zum Wochenende | `reel-wochenende` | dieselben Events wie das freigegebene Karussell | 9:16-Fassungen der Karussell-Folien als Video (E11) | wie das Karussell, gekürzt |
| **Karussell** „Deine Woche“ | `wochenvorschau` | die Events aus dem **veröffentlichten** Magazin-Beitrag Wochenvorschau | wie oben | Verweis auf den Beitrag („ganzer Artikel: Link in Bio“, auf FB als Link) |
| **Karussell** „Top-Events im <Monat>“ | `monats-tipps` | die Events aus dem veröffentlichten Beitrag Monats-Tipps | wie oben | wie oben |

Ist der Magazin-Beitrag bis zum Vorschlagszeitpunkt nicht veröffentlicht, **entfällt** der Slot in dieser Woche (kein Ersatz aus der Startseiten-Logik, damit Social und Magazin nicht auseinanderlaufen).

---

## 5. Auswahl und Texte

### 5.1 Interne Auswahl-Route

`POST /api/intern/social-auswahl`, Kopf `x-social-schluessel` = `SOCIAL_JOB_SCHLUESSEL`. Ohne gültigen Schlüssel gibt es 404, bei einem Datenbankfehler 503, und die Antwort ist immer `no-store`, nach dem Muster von `api/magazin/auswahl`. Eingabe: `{ slot, datum }`. Ausgabe: `{ slot, datum, events: [...], ersatz: [...], beitrag? }`, je Event `id`, `titel`, `datum`, `uhrzeit`, `ort`, `ort_id`, `ort_instagram`, `kategorie`, `gratis`, `url`, `bild` (Vorschlag nach E6), `beschreibung_kurz`. Die Ersatzliste (bis zu 10 weitere Kandidaten) dient dem Tauschen im Admin.

**Pool (Befund 3):** Die Auswahlfunktionen rechnen mit `pool.heute`. `eventPoolLaden()` setzt `heute` immer auf den echten heutigen Tag und liegt im Cache der Startseite (`web/lib/daten.ts:238–254`). Die Route nutzt deshalb **`magazinPoolLaden(stichtag, bis)`** (`daten.ts:263`, ohne Cache, `heute = von`, wirft bei Fehlern statt Beispieldaten zu liefern). So sieht der Pool aus wie der Pool der Startseite am Stichtag. Der Cache der Startseite bleibt unberührt. Der Name bleibt (die Funktion wird nur mitbenutzt); ein Kommentar ergänzt „auch Social“.

| Slot | Stichtag (`pool.heute`) | Logik (vorhandene Funktionen) |
|---|---|---|
| `story-heute` | Tag der Story | `startseitenAuswahl(pool, [], undefined)` → `tipp` + die ersten 3 `picks` (Zeitraum „heute“ = Stichtag) |
| `tipp-woche` | Tag des Posts | `highlightsImZeitraum(pool, {von: stichtag, bis: stichtag + 6}, "highlight")` |
| `wochenende` | Donnerstag des Slots | `wochenendProgramm(pool)` (hat kein Datumsargument und hängt nur an `pool.heute`) |
| `wochenvorschau`, `monats-tipps` | – | `magazin_beitraege.event_ids` des veröffentlichten Beitrags für den Zeitraum. Die IDs stammen aus den Einbettungen `{{event:<uuid>}}` in der Reihenfolge des Beitrags (`web/lib/admin/magazin-pruefung.ts:44`). Die Event-Daten kommen aus einem Pool mit Stichtag = Posttag. |
| `reel-wochenende` | – | keine eigene Auswahl. Der Vorschlag zeigt die Events des Karussell-Vorschlags derselben Woche; bei der Reel-Freigabe übernimmt es `event_ids` und Folien des **freigegebenen** Karussells (E7) |

Die Sensibel-Menge ist `sensibelMenge()` aus `web/lib/konto/mein-bereich.ts:22`, dieselbe wie bei der Geburtstagsmail.

**Zusätzliche Regeln für Social** (in der Route, getestet): Nie abgelehnte, abgesagte oder als sensibel markierte Events (gleiche Menge wie bei der Geburtstagsmail). Nur Events mit Ort und Datum. Ein Event steht höchstens einmal in 14 Tagen in einem Feed-Post (Stories dürfen wiederholen). Im Karussell höchstens 2 Events derselben Kategorie und, wenn vorhanden, mindestens 1 kostenloses. Der Pool kommt nur aus Supabase: Wirft `magazinPoolLaden`, antwortet die Route mit 503, und der Job legt für diesen Slot nichts an (Lehre aus der Geburtstagsmail). Die Route prüft den Schlüssel mit `schluesselOk(kopf, process.env.SOCIAL_JOB_SCHLUESSEL)`. Das zweite Argument ist Pflicht, denn ohne prüft `schluesselOk` den Magazin-Schlüssel (`web/lib/magazin-auswahl.ts:142`, Befund 10).

### 5.2 Texte (Job)

`pipeline/social.py vorschlaege` ruft je Slot die Auswahl ab, dann Claude (`claude-sonnet-5-5`, ein Aufruf je Post, strukturierte Ausgabe). Ergebnis: `caption_ig`, `caption_fb`, je Event-Folie `warum` (höchstens 80 Zeichen). Eingabe sind nur die Felder aus der Route, keine fremden Texte im Wortlaut. Ton: locker, empfehlend, du, kein Clickbait, höchstens 2 Emojis. Hashtags: fest `#düsseldorf #duesseldorf #diesdasduesseldorf`, dazu bis zu 5 passende aus einer festen Liste je Kategorie (`pipeline/social_hashtags.py`). Die KI erfindet keine Hashtags.

### 5.3 Prüfungen vor dem Speichern

Wie beim Magazin (`pipeline/magazin.py` `daten_im_text`, `CLICKBAIT`), dazu:
- Jedes Datum im Text gehört zu einem Event des Posts.
- Keine URL in `caption_ig`. In `caption_fb` nur URLs auf `diesdas.events`.
- `@handles` nur aus `ort_instagram`.
- Länge: IG höchstens 2200 Zeichen und 30 Hashtags (Instagram-Grenzen), unser Ziel sind 600 Zeichen und 8 Hashtags.
- Kein Hinweis „ausverkauft“, „letzte Tickets“ oder Preise, die nicht in den Daten stehen.

Fällt eine Prüfung durch, versucht der Job es einmal neu. Fällt sie wieder durch, wird der Post trotzdem als `vorschlag` gespeichert, mit Prüfvermerk in `pruefung` (rot im Admin). Freigeben geht erst nach einer Bearbeitung.

Die Kosten je Aufruf schreibt der Job in `social_posts.ki_kosten_usd`. Das Cockpit summiert sie wie beim Magazin.

---

## 6. Bilder und Rechte

- **Rendern** (E5): `web/lib/social/folien.tsx` (Satori-JSX) und die Route `GET /api/admin/social/[id]/folie/[n]` (nur Admin) für die Vorschau. Für den Schnappschuss schreibt `lib/social/schnappschuss.ts` nach `social/<post-id>/<version>/<n>.jpg` (JPEG, Qualität 88, sRGB, unter 8 MB). Die Schriften liegen als Dateien im Repo (`web/lib/social/schriften/`, OFL-Lizenzen beigelegt), weil `next/font/google` für Satori keine Dateien liefert.
- **Veranstalterfotos** (S3): Sie werden über den vorhandenen Bild-Proxy (`lib/bild-proxy.ts`, verkleinert große Bilder) geholt, nur bei gültiger Erlaubnis für den Host von `bild_url` und nicht auf der Sperrliste (E6). Die Folie nennt „Foto: <Name>“.
- **Erlaubnisse** (`bild_erlaubnisse`, Abschnitt 7) pflegt der Auftraggeber im Admin: Haus oder Quelle, **erlaubte Bild-Hosts**, Name für die Nennung, erteilt am, Nachweis (z. B. „Mail vom 02.12.2026 an hallo@“), Umfang (`social`), widerrufen am. Ein Host auf der Sperrliste lässt sich nicht eintragen. Eine Vorlage für die Anfrage an die Häuser steht in Anhang C (prüft der Anwalt).
- **KI-Symbolbilder:** Hinweis auf der Folie „Symbolbild · KI-generiert“. Besteht ein Post nur aus Symbolbildern, steht in der Caption „Symbolbilder KI-generiert“. Ob sich das Meta-Label „KI-Info“ über die API setzen lässt, klärt Schritt 0. Geht das nicht, genügt nach unserem Verständnis der sichtbare Hinweis (A4).
- **Ortsbilder von Wikimedia Commons** mit CC BY, CC BY-SA, FAL oder ohne Lizenzangabe kommen vorerst **nicht** in Posts (O7). Laut `bilder.csv` betrifft das 71 von 89 Zeilen. Erlaubt sind nur CC0 und gemeinfreie Bilder (18 Zeilen) sowie die eigenen Bilder der Weihnachtsmärkte (ohne `koe-on-ice.webp`) und der kleinen Märkte (E6). **Google-Fotos nie.**

---

## 7. Datenmodell (SQL, führt der Auftraggeber aus)

`database/social_2026-11-xx.sql`:

**`social_posts`**
`id uuid pk`, `slot text` (CHECK: Liste aus Abschnitt 4), `typ text` (`feed | karussell | story | reel`), `kanaele text[]` (`instagram`, `facebook`), `geplant_fuer timestamptz`, `tag date` (Berliner Kalendertag von `geplant_fuer`, vom Anleger gesetzt), `event_ids uuid[]`, `beitrag_id uuid null` (→ `magazin_beitraege`), `folien jsonb` (je Folie: `art` = titel/event/schluss, `event_id`, `bild` = {`quelle`: veranstalter/ort/symbol/keins, `pfad`, `original` (ursprüngliche `bild_url` bzw. Pfad), `host` (leer bei Pfaden), `nennung`}, `warum`, Stand von Datum und Ort für die Vorab-Prüfung), `caption_ig text`, `caption_fb text`, `pruefung jsonb`, `status text` (`vorschlag | freigegeben | bereit | wird_gepostet | container_wartet | gepostet | teilweise | fehler | unklar | verworfen | verfallen`), `bilder text[]` (Schnappschuss-URLs), `video_url text`, `ig_container_ids text[]` (je Folie bzw. ein Eintrag), `ig_media_ids text[]` (je veröffentlichter Story-Folie bzw. ein Eintrag), `ig_permalink text`, `fb_post_id text`, `fb_video_id text`, `fehler text`, `versuche int default 0`, `takt_am timestamptz`, `container_seit timestamptz`, `freigegeben_von text` (Nutzer-ID oder `auto`), `freigegeben_am`, `bearbeitet_am` (letzte Bearbeitung im Admin), `gepostet_am`, `ki_kosten_usd numeric`, `erstellt_am`, `geaendert_am`.
**Eindeutig: `UNIQUE (slot, tag)`** (Befund 1). Ein Ausdrucksindex mit `AT TIME ZONE` ginge nicht, weil der Ausdruck nicht `IMMUTABLE` ist. Der Job legt Vorschläge **nur über die SQL-Funktion `social_vorschlag_setzen(daten jsonb)`** an (nur `service_role`, Cursor-Prüfung 2, Befund 1). Sie enthält `INSERT … ON CONFLICT (slot, tag) DO UPDATE … WHERE social_posts.status = 'vorschlag' AND social_posts.bearbeitet_am IS NULL` und gibt `angelegt`, `aufgefrischt` oder `unveraendert` zurück. **Kein `upsert` aus supabase-py:** Das kann die `WHERE`-Bedingung nicht. Ein normales `upsert` würde freigegebene Posts überschreiben, und `ignore_duplicates` würde unbearbeitete Vorschläge nie auffrischen. „Neu erzeugen“ im Admin setzt vorher `bearbeitet_am = NULL` (nur bei `vorschlag`).
`teilweise` = ein Kanal oder ein Teil der Story-Folien ist online, der Rest fehlt. Was schon eine Media-ID hat, wird nie neu gepostet (E10).
Übergänge nur über die Funktionen `social_status_setzen(id, alt[], neu, felder jsonb)` (prüft den alten Status, schreibt `geaendert_am`), `social_beanspruchen(id)` (E10), `social_vorschlag_setzen(daten)` (Anlegen/Auffrischen, siehe oben) und `social_bearbeiten(id, aenderungen jsonb, nutzer)` (Bearbeitung im Admin: nur aus `vorschlag`, `freigegeben`, `bereit`; setzt `bearbeitet_am`; aus `freigegeben`/`bereit` zurück auf `vorschlag`; beim Wochenend-Karussell in derselben Transaktion das Reel der Woche zurücksetzen, E7). Alle nur für `service_role`.

**`social_einstellungen`** (genau eine Zeile): `modus text` (`aus | vorschau | an`, Start: `aus`), `story_auto bool` (Start: `false`), `facebook bool` (Start: `false`), `wochenplan jsonb` (E2), `geaendert_von`, `geaendert_am`.

**`bild_erlaubnisse`**: `id`, `ort_id uuid null`, `quelle text null` (Scraper-Name; genau eins von beiden), `hosts text[]` (erlaubte Bild-Hosts, klein geschrieben, mindestens einer), `nennung text`, `umfang text` (`social`), `erteilt_am date`, `nachweis text`, `widerrufen_am date null`, `notiz`, `erstellt_von`, `erstellt_am`.

**RLS:** Alle drei Tabellen nur über `ist_admin()` bzw. `service_role` lesbar und schreibbar. Die Linkseite `/links` liest über den Dienst-Client nur `event_ids` und `gepostet_am` gesendeter Posts.

**Storage:** Bucket `social`, öffentlich lesbar (Meta muss die Bilder holen), Schreiben nur `service_role`. Aufräumen: Schnappschüsse 30 Tage nach `gepostet_am` bzw. `verfallen` löschen (im täglichen Job).

**Takt-Auslöser** (eigenes SQL nach dem Deploy, E9): `pg_cron`-Job `social-takt` alle 5 Minuten, `net.http_post('https://diesdas.events/api/intern/social-takt', headers: x-social-schluessel aus vault.decrypted_secrets)`. Kontrollabfrage am Ende jedes SQL wie bisher.

Protokoll: Freigeben, Verwerfen, Jetzt posten, Schalter und Erlaubnisse schreiben ins vorhandene Admin-Protokoll.

---

## 8. Bauteile

**Website (`web/`)**
- `lib/social/meta.ts`: Graph-API-Client (Version als Konstante, beim Bau die aktuelle Version prüfen). Instagram: `POST /{ig-id}/media` (Bild, `is_carousel_item`, `CAROUSEL` mit `children`, `STORIES`, `REELS` mit `video_url`/`cover_url`/`share_to_feed`), Status des Containers über `GET /{container}?fields=status_code` (Reels: über mehrere Takte als `container_wartet`, bis `FINISHED`, E10), `POST /{ig-id}/media_publish`, Permalink über `GET /{media}?fields=permalink`. **Alle Aufrufe mit dem Seiten-Token** (E13). Facebook: Einzelbild über `POST /{page-id}/photos` (`url`, `message`). Mehrere Bilder: zuerst unveröffentlicht hochladen (`published=false`), dann `POST /{page-id}/feed` mit `attached_media`. **Reel in drei Schritten** (Befund 5): `POST /{page-id}/video_reels` mit `upload_phase=start` → `video_id` und `upload_url`; dann `POST <upload_url>` (die Adresse aus der Antwort, nicht selbst gebaut; Cursor-Prüfung 2, Befund 6) mit Kopf `file_url: <video_url>`; dann `POST /{page-id}/video_reels` mit `upload_phase=finish`, `video_id`, `video_state=PUBLISHED`, `description`. Fehler (Befund 5): 190 (Token) → `modus = vorschau` (E13). **4, 17, 32, 613 und 80001** (Limits) → bleibt postbar, im nächsten Takt erneut. 9004/2207052 (Bild nicht abrufbar) → erneut bis 3 Versuche. 36001/2207005 (kein JPEG) → `fehler`. Zeitüberschreitung bei einem Veröffentlichen-Aufruf → `unklar` (E10). Token und Schlüssel erscheinen nie im Log.
- `lib/social/folien.tsx`, `lib/social/schnappschuss.ts`, Schriften (Abschnitt 6).
- `lib/social/pruefen.ts`: Vorab-Prüfung vor dem Posten (E7), rein und getestet.
- `app/api/intern/social-auswahl/route.ts` (5.1) und `app/api/intern/social-takt/route.ts` (E9, E10). Die Takt-Route prüft `schluesselOk(kopf, process.env.SOCIAL_TAKT_SCHLUESSEL)` und arbeitet je Aufruf in dieser Reihenfolge:
  1. `modus` lesen; bei `aus` oder `vorschau` endet der Aufruf hier.
  2. Aufräumen in dieser Reihenfolge (Cursor-Prüfung 2, Befund 5):
     - (a) `wird_gepostet` älter als 15 Minuten → `unklar`.
     - (b) `container_wartet` mit `container_seit` älter als 60 Minuten → `fehler`. `container_seit` wird **einmal** beim ersten `IN_PROGRESS` gesetzt und bei späteren Abfragen nicht erneuert. `container_wartet` unter 60 Minuten bleibt unangetastet, auch jenseits der 6-Stunden-Frist.
     - (c) Erst danach die 6-Stunden-Frist nach E10 → `verfallen` bzw. `fehler`.
  3. Fällige Stories in `freigegeben`: Vorab-Prüfung, Schnappschuss → `bereit`.
  4. Höchstens 3 Posts mit `status IN ('bereit','teilweise','container_wartet') AND geplant_fuer <= now()` auswählen, einzeln beanspruchen, Vorab-Prüfung (nur vor dem ersten Kanal), dann abarbeiten. Zeitbudget 45 s.
  5. Jüngere `wird_gepostet` (laufender Aufruf) bleiben unangetastet.
- **Admin „Social“** (statt „Instagram“ in `rahmen.tsx`):
  - Wochenansicht mit den nächsten 14 Tagen, Slots mit Status-Farbe.
  - „Freigeben“ macht bei Feed und Karussell sofort den Schnappschuss (→ `bereit`). Beim Reel ist der Button gesperrt, bis das Karussell derselben Woche freigegeben ist; danach stößt er den Video-Bau an (E7, E10).
  - Post-Seite mit Folienvorschau, Captions für IG und FB zum Bearbeiten, Events tauschen und umsortieren (aus `ersatz`), Bildquelle je Folie, Postzeit ändern. Buttons: Freigeben, Verwerfen, Neu erzeugen (stößt `social.yml` für diesen Post an), Jetzt posten (mit Rückfrage), bei `unklar`: „ist online“ / „erneut posten“.
  - Verlauf mit Permalinks und Fehlern, Bild-Erlaubnisse, Schalter (E12) und eine Verbindungsprüfung (Token gültig, Rechte, `content_publishing_limit`).
- Cockpit: Kachel „Social“ (wartet auf Freigabe, Fehler/unklar, Token-Zustand).
- `app/links/page.tsx` (E14).
- `lib/admin/github.ts`: Workflow `social` in `WORKFLOWS`.
- `deploy.yml`: `META_TOKEN`, `META_IG_ID`, `META_PAGE_ID`, `SOCIAL_JOB_SCHLUESSEL` und `SOCIAL_TAKT_SCHLUESSEL` nach `web/.env.local` (mit `tr -d` wie die anderen Schlüssel, `lib/schluessel.ts`).
- Datenschutz-Text (Abschnitt 10), `seo.ts` `sameAs`, Footer mit Links zu Instagram und Facebook (nach dem Livegang).

**Pipeline**
- `pipeline/social.py`:
  - `vorschlaege [--tage 4] [--slot …] [--post <id>] [--dry-run]` (5.2, 5.3)
  - `reel --post <id>`: Schnappschüsse laden, ffmpeg, Upload nach `social/<id>/<version>/reel.mp4`, dann `social_status_setzen(id, ['freigegeben'], 'bereit', {video_url})`. Lehnt die Funktion ab (Post inzwischen bearbeitet oder verworfen), löscht der Job sein Video wieder (Cursor-Prüfung 2, Befund 7).
  - `aufraeumen` (Storage, Abschnitt 7)
  - `erinnern` (E16)
  - Log nur mit Zahlen und Slot-Namen.
- `pipeline/social_hashtags.py`.
- `.github/workflows/social.yml`:
  - täglich 04:00 UTC, manuell (Eingaben `aktion`, `post`, `dry_run`) und per Anstoß aus dem Admin.
  - `if: vars.SOCIAL_AKTIV == '1'` (manueller `--dry-run` auch ohne).
  - `apt-get install ffmpeg`.
  - Secrets `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ANTHROPIC_API_KEY`, `SOCIAL_JOB_SCHLUESSEL`, SMTP wie Geburtstag.
- Aus `main.py` die Schritte 4/5 entfernen (Schritt 1).

**Keine neue Bibliothek** (Regel aus `CLAUDE.md`): `next/og` gehört zu Next. `sharp`, `anthropic` und `httpx` sind schon da. ffmpeg kommt nur als Systempaket in den GitHub-Job (`apt-get`), so wie es `requirements.txt` schon vorsieht.

**Aufräumen (Schritt 1):** `pipeline/caption_generator.py`, `pipeline/publisher.py` und `test_instagram.py` löschen. Dazu gehören (Befund 7):
- In `tests/test_vorschau.py` den Test `test_captions_und_publisher_bleiben_nah` (`:94–99`) entfernen.
- In `test_pipeline.py` den Import (`:26`) und den Caption-Schritt (`:83`) entfernen.
- In `config.py:19–20` die Instagram-Variablen entfernen.
- In `.env.example` die Instagram-Variablen entfernen.
- `openai` aus `requirements.txt` entfernen (wird nirgends importiert, folgenlos).
- Danach die Python-Tests laufen lassen. `CLAUDE.md`: Phase-1-Beschreibung, Tech-Stack (DALL-E, Canva, Pillow-Overlay), Struktur (`visual/`, `assets/`) und Regeln (Reels via ffmpeg Phase 1) auf diesen Plan umschreiben. `HANDOVER.md`: Hinweise auf den Publisher.

---

## 9. Meta-Einrichtung (Schritt 0, Auftraggeber mit Anleitung)

Ausführliche Klickanleitung in Anhang D. Kurzfassung:

1. **Business-Portfolio** (business.facebook.com): Facebook-Seite und Instagram-Konto sind dort als Assets eingetragen, der Auftraggeber ist Admin, die Zwei-Faktor-Anmeldung ist an.
2. **Meta for Developers** (developers.facebook.com): Entwicklerkonto, neue App vom Typ **Business**, mit dem Business-Portfolio verbunden. Anwendungsfälle: „Instagram API mit Facebook-Login“ und „Alles auf deiner Seite verwalten“. App-Icon (`web/public/logo/app-icon.svg` als PNG). Datenschutz-URL `https://diesdas.events/datenschutz`. Die Kontaktadresse ist `hallo@diesdas.events`.
3. **Berechtigungen (Standardzugriff):** `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `business_management` und **`ads_read`**. Meta verlangt `ads_read` oder `ads_management` zusätzlich, wenn die Rolle für die Seite über den Business Manager vergeben wurde, wie bei Punkt 4 (Befund 5). `ads_read` genügt, Anzeigen schalten wir nicht. Laut Meta braucht eine App, die nur eigene Konten bespielt, **kein App-Review** (Standardzugriff genügt). Später optional `instagram_manage_insights` und `read_insights` für Zahlen.
4. **Systembenutzer** (Unternehmenseinstellungen → Nutzer → Systembenutzer):
   - Name `diesdas-social`, Rolle **Mitarbeiter** (nicht Admin; Meta rät davon ab, Assets über einen Admin-Systembenutzer zu verwalten).
   - Assets zuweisen: die App (verwalten), die Seite (Inhalte erstellen) und das Instagram-Konto (Inhalte).
   - **Token erzeugen** mit Ablauf „nie“ und den Rechten aus Punkt 3.
   - Verweigert Meta das (fehlender Marketing-API-Zugang), nehmen wir den Ersatzweg aus E13.
5. **App-Modus:** Ob Posts im Entwicklungsmodus öffentlich erscheinen oder die App „live“ sein muss, zeigt der Test in Punkt 6. Für „live“ braucht die App die Datenschutz-URL, eine URL für die Datenlöschung (`/datenschutz`) und vielleicht eine Unternehmensverifizierung.
6. **Prüfung:** `python tools/meta_pruefen.py` (liest `META_TOKEN` aus `secrets/.env`, gibt den Token nie aus):
   - Token gültig, alle Rechte aus Punkt 3 einschließlich `ads_read` (`debug_token`)
   - Seiten-ID und Instagram-ID, Seiten-Token abrufbar
   - `content_publishing_limit`
   - optional `--test-story`: eine Story mit der Testfolie, die nach 24 h verschwindet.
   - Es prüft auch, ob sich das Label „KI-Info“ setzen lässt und ob die API Posts löschen kann.
7. **Secrets** in GitHub: `META_TOKEN`, `SOCIAL_JOB_SCHLUESSEL`, `SOCIAL_TAKT_SCHLUESSEL` (zufällig, hex). Variablen: `META_IG_ID`, `META_PAGE_ID`, `SOCIAL_AKTIV` (zuerst leer).
8. **Profile:**
   - Instagram-Bio mit Link `diesdas.events/links`.
   - Facebook-Seite: Feld „Impressum“ mit `https://diesdas.events/impressum` und Website `https://diesdas.events`.

---

## 10. Datenschutz, Impressum, Anwalt

**Datenschutzerklärung** (Abschnitt „Soziale Netzwerke“, Sie-Form; Entwurf in Anhang B):
- Instagram-Profil mit Namen und Facebook-Seite mit Adresse nennen; das „ggf.“ fällt weg.
- Den Unterabschnitt „Instagram Graph API“ zu „Automatisches Veröffentlichen auf Instagram und Facebook“ erweitern: Über die Schnittstellen von Meta gehen nur von uns erstellte Inhalte raus (Texte, Grafiken, Fotos mit Erlaubnis der Rechteinhaber) sowie öffentliche Event-Angaben. Daten von Website-Nutzern werden nicht übermittelt.
- Die Seite `/links` setzt keine Cookies und nutzt kein Tracking.
- Die Hinweise zu Art. 26 (Seiten-Insights) bleiben.

**Impressum in den Profilen:** Nach § 5 DDG muss das Impressum auch von den Profilen aus leicht erreichbar sein. Lösung: die Instagram-Bio verlinkt `/links`, dort steht „Impressum“ ganz oben. Auf Facebook steht es im Feld „Impressum“ (A2).

**Fragen an den Anwalt** (eine Vorlage `docs/anwalt-social-2026-11-xx.md` entsteht in Schritt 7):
- A1: Neuer Text für die Datenschutzerklärung (Anhang B).
- A2: Reicht die Impressum-Lösung über `/links` für Instagram?
- A3: Vorlage für die Erlaubnis zu Veranstalterfotos (Anhang C): Nutzungsrecht für Website und Social Media, Nennung, Zusicherung der Rechte an abgebildeten Personen, Widerruf.
- A4: KI-Kennzeichnung. Genügt der sichtbare Hinweis „Symbolbild · KI-generiert“? Müssen KI-gestützte Captions gekennzeichnet werden? Unser Verständnis: Die Captions gibt der Auftraggeber frei und trägt dafür die redaktionelle Verantwortung (Art. 50 Abs. 4 KI-VO). Die automatischen Stories enthalten keinen KI-Text.
- A5: Können Künstler:innen und Häuser genannt und per `@handle` erwähnt werden, ohne vorher zu fragen?
- A6: Werbung. Posts über Events mit Partnerlinks (Awin und andere) verlinken auf Instagram gar nicht und auf Facebook nur auf unsere Event-Seite, wo der Partnerlink gekennzeichnet ist. Braucht der Post selbst eine Kennzeichnung? Unser Vorschlag: nein, solange kein Haus für einen Post bezahlt.

---

## 11. Schritte

| Schritt | Wer | Inhalt | Ergebnis |
|---|---|---|---|
| 0 | Auftraggeber (Anleitung von Claude) | Meta-Einrichtung (Abschnitt 9), `tools/meta_pruefen.py`, Test-Story | Token gilt, IDs bekannt, Test-Story sichtbar |
| 1 | Claude | Altbestand aufräumen (E17, Abschnitt 8). Kann **sofort** und unabhängig vom Rest live gehen (Deploy nur mit OK) | keine ungenutzten Captions mehr |
| 2 | Claude → Auftraggeber | Folien-Entwürfe: Titel, Event (mit Foto, Symbolbild, ohne Foto), Schluss, je 4:5 und 9:16, mit echten Events gerendert, als Bilder in `docs/social-vorlagen/` | **Freigabe der Gestaltung** |
| 3 | Claude, Auftraggeber führt aus | SQL (Abschnitt 7, ohne `pg_cron`) | Tabellen, Bucket, Kontrollabfrage ok |
| 4 | Claude | Website: Rendern, Auswahl-Route, Meta-Client, Takt-Route, Admin Social, Cockpit, `/links`, Tests | lokal grün |
| 5 | Claude | Pipeline: `social.py`, Hashtags, `social.yml`, Tests | lokal grün, `--dry-run` gegen die Live-Daten |
| 6 | Cursor, dann Claude | Prüfung der Umsetzung (Prompt wie Anhang A, Fassung „Umsetzung“), Befunde beheben | abnahmefähig |
| 7 | Anwalt (ab Schritt 2 parallel) | A1–A6 | Texte freigegeben |
| 8 | Auftraggeber + Claude | Deploy (nach OK), Secrets, `pg_cron`-SQL. `modus = vorschau`, `SOCIAL_AKTIV = 1`. **Eine Woche nur Vorschläge**, Abnahme im Admin | Vorschläge stimmen |
| 9 | Auftraggeber | `modus = an`: zuerst `story_auto` an (3 Tage beobachten), dann die ersten Feed-Freigaben, dann `facebook` an. Danach `sameAs` und Footer-Links (kleiner Deploy) | live |
| später | – | Zahlen (Insights) im Admin, `collaborators`/`user_tags` für Häuser, Musik in Reels (O6), Kommentare im Cockpit, Commons-Bilder (O7) | eigener Mini-Plan |

---

## 12. Tests

- **Website:**
  - Auswahl-Route: 404 ohne Schlüssel, 503 bei Beispieldaten; nie abgelehnte, abgesagte oder sensible Events; 14-Tage-Sperre; Kategorie-Mischung; die Magazin-Slots übernehmen die Reihenfolge des Beitrags.
  - Vorab-Prüfung: Datum oder Ort geändert → Feed `fehler`, bei der Story fällt die Folie weg.
  - Auswahl mit Stichtag: `story-heute` für morgen nutzt `pool.heute` = morgen; `wochenende` rechnet vom Donnerstag des Slots; der Cache der Startseite wird nicht berührt; `schluesselOk` mit Social-Schlüssel (der Magazin-Schlüssel öffnet die Route nicht).
  - Takt (Zustandsautomat E10):
    - Beanspruchen ist atomar: Zwei gleichzeitige Takte ergeben einen Post.
    - Ein `vorschlag` oder ein nur `freigegeben`er Post wird nie gepostet. Der Job setzt `bereit` für ein Reel nur aus `freigegeben`; ein verworfenes Reel bleibt verworfen.
    - `wird_gepostet` wird nie ausgewählt. Nach 15 Minuten → `unklar`, ohne neuen Versuch.
    - Zeitüberschreitung bei `media_publish` → `unklar` und kein zweiter Aufruf.
    - `teilweise`: Nur der fehlende Kanal wird nachgeholt. Story-Abbruch nach Folie 3: nur die Folien 4–6 werden veröffentlicht.
    - Reel: `IN_PROGRESS` → `container_wartet` über mehrere Takte, nicht `unklar`. `FINISHED` → veröffentlicht. Nach 60 Minuten → `fehler`.
    - Limit-Fehler (4, 17, 32, 613, 80001) → erneut im nächsten Takt, höchstens 3 Versuche.
    - Fehler 190 → `modus = vorschau`.
    - 6-Stunden-Frist → `verfallen` bzw. `fehler` bei `teilweise`.
    - Eine Bearbeitung nach der Freigabe setzt auf `vorschlag` zurück, aber nur aus `freigegeben` und `bereit`. Während `wird_gepostet`, `container_wartet`, `teilweise`, `unklar` und `gepostet` wird sie abgelehnt.
    - Eine Bearbeitung des Karussells setzt ein `freigegeben`es oder `bereit`es Reel der Woche mit zurück und leert `video_url`.
    - `container_seit` bleibt beim zweiten bis vierten `IN_PROGRESS` unverändert. Bei 61 Minuten → `fehler`, bei 59 Minuten und mehr als 6 Stunden nach `geplant_fuer` kein `verfallen`.
    - Facebook-Reel: Der Upload geht an die `upload_url` aus der Antwort von `start`.
  - Meta-Client gegen aufgezeichnete Antworten (kein echter Aufruf in Tests). Seiten-Token für Instagram und Facebook; drei Schritte beim Facebook-Reel.
  - Folien:
    - Die Sperrliste greift am Host von `bild_url`, auch mit Erlaubnis und auch, wenn `quelle_name` etwas anderes sagt.
    - Pfade ohne Host: `/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp` wird abgelehnt, ein CC-BY-Ortsbild als `bild_url` (`/ort-bilder/orte/…`) wird abgelehnt, `/bild/event/<id>` wird abgelehnt, `/ort-bilder/events/rennbahn-weihnacht.webp` ist erlaubt.
    - Ein Veranstalterfoto erscheint nur bei einer Erlaubnis für genau diesen Host. Eine widerrufene Erlaubnis greift nicht mehr.
    - Ortsbilder nur bei CC0, gemeinfrei oder eigenem Bild; Google-Fotos nie. Dieselbe Prüfung gilt beim Tauschen und Umstellen im Admin.
    - Die Hinweise „Symbolbild · KI-generiert“ und „Foto: …“ stehen auf der Folie.
    - Alle Karussell-Folien haben 1080×1350.
    - `ortsbild-lizenzen.json` passt zu `bilder.csv`, und die Sperrliste hat in TypeScript und Python denselben Testvektor.
  - Schnappschuss-JPEG mit der richtigen Größe.
  - `/links`: ohne Cookies, `noindex`.
  - Admin-Rechte: nur `ist_admin()`.
- **Pipeline:**
  - Prüfungen (Datum fremd, URL in IG, fremder `@handle`, Clickbait, Länge), zweiter Versuch.
  - Eindeutigkeit über `social_vorschlag_setzen` (kein `upsert`): Ein doppelter Lauf erzeugt keine zweiten Vorschläge und überschreibt keinen bearbeiteten oder freigegebenen Post.
  - Karussell und Reel entstehen im selben Lauf.
  - Story ohne KI-Aufruf.
  - Reel-Befehl für ffmpeg (Dauer, Format); `reel` setzt `bereit` nur aus `freigegeben`.
  - `META_TOKEN` steht nicht in `social.yml`, und das Log enthält keine Schlüssel.
  - Nach Schritt 1 laufen `test_vorschau.py` und `test_pipeline.py` ohne die gelöschten Module.
- **SQL:** RLS (anon und angemeldet sehen nichts), `UNIQUE (slot, tag)`, `social_vorschlag_setzen` (neu → `angelegt`; unbearbeiteter `vorschlag` → `aufgefrischt`; bearbeiteter `vorschlag` und `freigegeben` → `unveraendert`), `social_bearbeiten` (gesperrte Status, Reel-Kopplung), `social_status_setzen` lehnt einen falschen alten Status ab, `bild_erlaubnisse.hosts` nicht leer, Kontrollabfrage.

---

## 13. Risiken

- **Meta sperrt oder drosselt automatisierte Konten**, wenn sie wie Spam wirken. Gegenmittel: höchstens 4 Feed-Posts in der Woche, wenige feste Hashtags, keine Massen-Erwähnungen, alle Feed-Posts von Hand freigegeben.
- **Fehler in den Daten** (falsches Datum, abgesagtes Event) gehen öffentlich raus. Gegenmittel: Freigabe, Vorab-Prüfung kurz vor dem Post, Stories nur mit Datenbank-Daten. Bleibt ein Rest: Eine Story mit falscher Uhrzeit ist bis zu 24 h sichtbar. Wir löschen sie dann in der App.
- **Reels ohne Musik** erreichen weniger Leute. Das wird hingenommen, Musik ist O6.
- **Token und API-Änderungen:** Meta ändert die Graph-API-Versionen etwa zweimal im Jahr. Die Version steht in einer Konstante, und die Verbindungsprüfung im Admin zeigt Abkündigungen.
- **Supabase `pg_cron` fällt aus:** Dann wird nichts gepostet, und Posts werden `verfallen` (kein Doppelpost). Das Cockpit zeigt „letzter Takt vor x Minuten“. Ersatzweg ist der `crontab` auf dem Server.
- **Speicher auf dem Server:** Gerendert wird nur bei Vorschau und Schnappschuss, und nur für Admins. Keine öffentliche Render-Route, die Bots auslösen könnten.
- **Veranstalterfotos mit Personen:** Für die Rechte steht das Haus ein (Vorlage Anhang C). Bei einem Widerruf: Erlaubnis im Admin widerrufen und alte Posts in der App löschen. Ob die API Posts löschen kann, klärt Schritt 0.

---

## 14. Offene Fragen an den Auftraggeber

| Nr. | Frage | Vorschlag |
|---|---|---|
| O1 | Wie heißt das Instagram-Konto (`@…`)? | – (für Datenschutz, `sameAs`, Footer) |
| O2 | Passen Wochenplan und Uhrzeiten aus E2? | wie E2 |
| O3 | Takt-Auslöser: Supabase `pg_cron` oder `crontab` auf dem Server? | `pg_cron` (kein Eingriff am Server) |
| O4 | Adresse der Linkseite: `/links`? | `/links` |
| O5 | Erinnerungsmail bei offenen Freigaben (E16) gewünscht? | ja, höchstens 1 am Tag |
| O6 | Musik in Reels: lizenzfreie Musik (z. B. gekaufte Lizenz) in das Video einbauen? | zuerst ohne, später entscheiden |
| O7 | Commons-Bilder (CC BY/BY-SA) mit Nennung in Posts? | vorerst nein |
| O8 | Wer fragt die Häuser nach der Foto-Erlaubnis, und welche zuerst? | Claude stellt eine Liste der 20 häufigsten Häuser in Posts zusammen. Der Auftraggeber schreibt mit der Vorlage aus Anhang C |

---

## 15. Prüfhistorie

- 25.11.2026: Bestandsaufnahme und erste Fassung (Claude), nach den Entscheidungen S1–S4 des Auftraggebers.
- 25.11.2026: **Cursor-Prüfung 1** der ersten Fassung: „nicht freigabefähig“ (2 kritisch, 5 mittel, 5 gering). Alle 12 Befunde eingearbeitet → **zweite Fassung** (Anhang E).
- 25.11.2026: **Cursor-Prüfung 2** der zweiten Fassung (`docs/cursor-pruefung-social-plan-2-2026-11-25.md`): **„freigabefähig: ja“**. Alle 12 Befunde gelöst, sieben Durchläufe des Zustandsautomaten halten. 4 mittlere und 3 geringe neue Befunde.
- 26.11.2026: Befunde der Prüfung 2 eingearbeitet → **dritte Fassung** (Anhang G).

---

## Anhang A: Cursor-Prüf-Prompt (Prüfung 1, erste Fassung; für Prüfung 2 siehe Anhang F)

> Prüfe den Plan `docs/plan-social-2026-11-25.md` (automatische Posts auf Instagram und Facebook für diesdas.events) gegen den tatsächlichen Code im Repo. Ändere keinen Code und keinen Plan, liefere nur Befunde.
>
> Prüfe bitte besonders:
> 1. **Bestand (Abschnitt 1):** Stimmen die Aussagen zu `pipeline/publisher.py`, `pipeline/caption_generator.py`, `main.py` (Schritte 4/5) und `test_instagram.py`? Bricht etwas, wenn Captions und Publisher wegfallen? Prüfe vor allem `categorizer.py` (lädt `status = neu`), `web/` und `dashboard/` auf Abhängigkeiten von `status = aufbereitet/gepostet` oder `instagram_caption`.
> 2. **Auswahl (5.1):** Lassen sich `startseitenAuswahl`, `highlightsImZeitraum` und `wochenendProgramm` (`web/lib/startseite.ts`, `web/lib/ableitungen.ts`) für ein beliebiges `datum` aufrufen, ohne den Cache der Startseite zu teilen? Wo steht die Sensibel-Menge, die die Geburtstagsmail benutzt (`web/app/api/intern/geburtstag-tipps/route.ts`), und lässt sie sich hier gleich verwenden? Woher kommen die Event-IDs eines Magazin-Beitrags (`magazin_beitraege`)?
> 3. **Rendern (E5, Abschnitt 6):** Ist `next/og` (`ImageResponse`) in Next 16.4 mit unserem Setup (Cache Components, `"use cache"`, `proxy.ts`, nginx) auf dem Server lauffähig? Fehlen Schriften als Dateien? Kann `sharp` PNG → JPEG ohne neue Abhängigkeit?
> 4. **Takt (E9, E10):** Ist das Beanspruchen wirklich atomar? Lücken im Zustandsautomaten (`freigegeben → bereit → wird_gepostet → gepostet/teilweise/fehler/unklar/verfallen`)? Besonders: Reel-Container, der über mehrere Takte wartet; Absturz zwischen `media_publish` und dem Speichern; Facebook nach Instagram.
> 5. **Meta-API (Abschnitt 8, 9):** Stimmen Endpunkte, Parameter und Rechte für Instagram (Bild, Karussell bis 10, Story, Reel) und für die Facebook-Seite (Foto, mehrere Fotos über `attached_media`, `video_reels`) mit der aktuellen Meta-Dokumentation überein? Reichen die Rechte aus Abschnitt 9 Punkt 3?
> 6. **Sicherheit:** Token nur auf dem Server? Interne Routen 404 ohne Schlüssel, keine Schlüssel im Log? Admin-Routen nur mit `ist_admin()`? Ist der öffentliche Bucket `social` unbedenklich (nur freigegebene Inhalte, kein Auflisten)? Admin-Host-Trennung (`X-DDD-Bereich`, Admin-Plan 1a) für die neuen Admin-Routen?
> 7. **Bildrechte (E6):** Greift die Sperrliste für alle Wege, auf denen ein Bild in eine Folie kommt (auch beim Tauschen im Admin)? Woran erkennt der Code, aus welcher Quelle `bild_url` stammt?
> 8. **Widersprüche** zwischen den Abschnitten 3–12 und zu bestehenden Plänen (Admin-Plan 4.8, Magazin-Plan, Quellen-Ausbau-Plan 5.3 `INSTAGRAM_TAGE`).
>
> Ausgabe je Befund: Schweregrad (kritisch / mittel / gering) · Fundstelle (Plan-Abschnitt + Datei:Zeile) · Befund · Vorschlag. Nach Schweregrad sortiert. Am Ende: Gesamturteil (freigabefähig ja/nein). Die offenen Fragen O1–O8 und die Anwaltsfragen A1–A6 sind bekannt und blockieren die technische Freigabe nicht.

---

## Anhang B: Entwurf Datenschutzerklärung (ersetzt `web/app/datenschutz/page.tsx:192–224`)

> **Instagram und Facebook (Meta)**
> Wir betreiben das Instagram-Profil @<O1> und die Facebook-Seite facebook.com/dies.das.duesseldorf. Betreiber der Plattformen ist die Meta Platforms Ireland Limited, Merrion Road, Dublin 4, D04 X2K5, Irland. Wenn Sie unsere Profile besuchen, verarbeitet Meta Ihre Daten nach der Meta-Datenschutzrichtlinie, u. a. Ihre IP-Adresse, Browser-Informationen und Ihr Nutzungsverhalten.
> *(Absätze zu Seiten-Insights/Art. 26 und zur Rechtsgrundlage unverändert.)*
>
> **Automatisches Veröffentlichen auf Instagram und Facebook**
> Wir veröffentlichen Beiträge auf unseren Profilen teilweise automatisiert über die Schnittstellen von Meta (Instagram Graph API, Facebook Graph API). Dabei übermitteln wir ausschließlich von uns erstellte Inhalte (Texte, Grafiken, Symbolbilder) sowie Fotos, deren Rechteinhaber zugestimmt haben, und öffentliche Angaben zu Veranstaltungen (Titel, Datum, Ort). Personenbezogene Daten von Nutzerinnen und Nutzern unserer Website werden dabei nicht übermittelt.
>
> **Linkseite für Instagram**
> Die Seite diesdas.events/links, auf die unser Instagram-Profil verweist, setzt keine Cookies und verwendet kein Tracking. Es gelten die Angaben zum Server-Log in Abschnitt <n>.

---

## Anhang C: Vorlage Anfrage Foto-Erlaubnis (Entwurf, prüft der Anwalt)

> Betreff: Eure Fotos auf dies.das.düsseldorf
>
> Hallo <Name>,
>
> wir sind dies.das.düsseldorf (diesdas.events), ein unabhängiger Stadtguide für Düsseldorf. Wir stellen eure Veranstaltungen auf unserer Website und ab Dezember auch auf Instagram und Facebook vor.
>
> Dürfen wir dafür die Pressefotos nutzen, die ihr auf eurer Website zu euren Veranstaltungen zeigt? Konkret: auf diesdas.events und in unseren Posts auf Instagram und Facebook, jeweils mit dem Vermerk „Foto: <euer Name oder Fotograf:in>“. Die Fotos werden nur zugeschnitten und mit Titel, Datum und Ort versehen, sonst nicht verändert.
>
> Wenn ihr einverstanden seid, bestätigt das bitte kurz per Mail. Bitte schreibt dazu, ob ihr die Rechte an den Fotos habt und ob abgebildete Personen einverstanden sind, und wie der Fotovermerk lauten soll. Widerrufen könnt ihr jederzeit mit einer Mail an hallo@diesdas.events; neue Posts nutzen eure Fotos dann nicht mehr.
>
> Viele Grüße
> <Signatur>

---

## Anhang D: Klickanleitung Meta (für Schritt 0)

Die Anleitung entsteht als eigene Datei `docs/meta-einrichtung-anleitung.md` direkt nach der Freigabe, mit Screenshots der aktuellen Oberflächen (Meta ändert die Menüs häufig). Inhalt wie Abschnitt 9, Punkte 1–8, je Punkt: wo klicken, was eintragen, woran man erkennt, dass es geklappt hat.

---

## Anhang E: Einarbeitung Cursor-Prüfung 1 (25.11.2026)

| Befund | Schwere | Eingearbeitet in |
|---|---|---|
| 1 Eindeutigkeits-Index mit `AT TIME ZONE` nicht anlegbar | kritisch | Abschnitt 7: Spalte `tag date`, `UNIQUE (slot, tag)`, `ON CONFLICT` mit Schutz bearbeiteter Posts; Tests 12 |
| 2 Zustandsautomat: Reel ohne Freigabe, `teilweise`, 15-Minuten-Regel bei Reels, Auswahl nur nach Uhrzeit | kritisch | E10 neu (Übergänge, `container_wartet`, Fortschritt je Kanal/Folie, `unklar` nur bei abgebrochenem Aufruf oder Veröffentlichen ohne Antwort), E7 (Reel-Freigabe), Abschnitt 7 (Status, Funktionen), Abschnitt 8 (Ablauf der Takt-Route), Tests 12 |
| 3 Auswahlfunktionen ohne Stichtag, Cache der Startseite | mittel | 5.1: `magazinPoolLaden(stichtag, bis)` mit `heute` = Stichtag je Slot; Tabelle mit Stichtag; Tests 12 |
| 4 Bildherkunft nur über URL, Ortsbild-Lizenz in `bilder.csv`, Google-Fotos | mittel | E6 (Host der `bild_url`, Sperrliste wie `_VERBOTEN`, Erlaubnis je Host, Lizenzliste aus `bilder.csv`, Google nie, dieselbe Prüfung überall), Abschnitt 6, 7 (`hosts`), Tests 12 |
| 5 Seiten-Token für Instagram, `ads_read`, Facebook-Reel über `rupload`, Karussell-Format, Reel-Cover, Limits 613/80001 | mittel | E13, E5, E11, Abschnitt 8 (`meta.ts`), Abschnitt 9 Punkte 3 und 6 |
| 6 Reel und Karussell zeitlich | mittel | E2 (beide im selben Lauf, 4 Tage Vorlauf), E7 (Reel-Freigabe nach Karussell, ohne Zwei-Tage-Regel), Admin in Abschnitt 8 |
| 7 Schritt 1 bricht Tests | mittel | Abschnitt 1 (Tabelle), Abschnitt 8 (Aufräumen), Tests 12 |
| 8 Kategorisierer: NULL statt leerer Text, `fehler` vom Caption-Generator | gering | Abschnitt 1 (Tabelle) |
| 9 `sameAs` ist ein Kommentar | gering | Abschnitt 1 (Tabelle) |
| 10 `schluesselOk()` ohne Argument = Magazin-Schlüssel; `META_TOKEN` nur über `deploy.yml` | gering | 5.1, Abschnitt 8 (Takt-Route), E13, Tests 12 |
| 11 Story: Tipp + 4 Picks, eine Veröffentlichung je Folie | gering | Abschnitt 4 (Story: Tipp + 3 Picks, Abbruchregel), 5.1, Tests 12 |
| 12 `INSTAGRAM_TAGE` / Admin-Plan 4.8 | gering | kein Widerspruch; `INSTAGRAM_TAGE` fällt mit Schritt 1 weg, `social_posts` löst `instagram_posts` ab, den Button „für Instagram vormerken“ gibt es im Code nicht (entfällt) |

---

## Anhang F: Cursor-Prüf-Prompt (Prüfung 2, zweite Fassung)

> Prüfe die **zweite Fassung** des Plans `docs/plan-social-2026-11-25.md` (automatische Posts auf Instagram und Facebook für diesdas.events) erneut gegen den Code im Repo. Ändere keinen Code und keinen Plan, liefere nur Befunde.
>
> Deine Prüfung 1 hatte 12 Befunde (2 kritisch, 5 mittel, 5 gering). Anhang E nennt, wo jeder eingearbeitet ist.
>
> Prüfe bitte:
> 1. Sind alle 12 Befunde gelöst (Anhang E)? Besonders Befund 2.
> 2. **Zustandsautomat (E10, Abschnitt 7 und 8):** Gibt es noch einen Weg, auf dem ein Post ohne Freigabe online geht oder ein Kanal oder eine Story-Folie zweimal veröffentlicht wird? Spiele durch:
>    - zwei gleichzeitige Takte
>    - Absturz zwischen `media_publish` und dem Speichern
>    - Reel mit `IN_PROGRESS` über 4 Takte
>    - `teilweise` → „erneut posten“
>    - Bearbeitung nach der Freigabe, während der Job das Reel-Video baut
>    - Story-Abbruch nach Folie 3
>    - die 6-Stunden-Frist bei `container_wartet`
> 3. **`UNIQUE (slot, tag)` mit `ON CONFLICT`:** Lässt sich die Regel „nur überschreiben, wenn `vorschlag` und `bearbeitet_am IS NULL`“ mit supabase-py (`upsert`) umsetzen, oder braucht es eine SQL-Funktion?
> 4. **Auswahl (5.1):** Liefert `startseitenAuswahl(magazinPoolLaden(morgen, …), [], undefined)` den Tipp und die Picks, die die Startseite morgen zeigen würde? Gibt es Teile, die mit `jetzt` statt `pool.heute` rechnen (Stufen, „Neu“, Fokustag)? Passt `wochenendProgramm` mit `heute` = Donnerstag?
> 5. **Bildquellen (E6):** Erfasst die Host-Prüfung alle Wege, auf denen ein Bild in eine Folie kommt? Kann ein Bild-Proxy-Pfad (`/bild/event/<id>`) oder ein lokales Bild (`lokalesBild`) die Prüfung umgehen? Gibt es Ortsbilder ohne Zeile in `bilder.csv`?
> 6. **Meta (Abschnitt 8, 9):** Stimmen jetzt Seiten-Token für Instagram, `ads_read`, der Facebook-Reel in drei Schritten (`rupload`) und die Fehlercodes mit der aktuellen Doku?
> 7. **Widersprüche** zwischen E2/E7/E10/E11, Abschnitt 4, 7, 8, 12 und den Anhängen.
>
> Ausgabe je Befund: Schweregrad (kritisch / mittel / gering) · Fundstelle (Plan-Abschnitt + Datei:Zeile) · Befund · Vorschlag. Nach Schweregrad sortiert. Am Ende: Gesamturteil (freigabefähig ja/nein). O1–O8 und A1–A6 sind bekannt und blockieren die technische Freigabe nicht. Speichere das Ergebnis als `docs/cursor-pruefung-social-plan-2-2026-11-25.md`.

---

## Anhang G: Einarbeitung Cursor-Prüfung 2 (26.11.2026)

| Befund | Schwere | Eingearbeitet in |
|---|---|---|
| 1 `ON CONFLICT … WHERE` geht nicht mit supabase-py `upsert` | mittel | Abschnitt 7: SQL-Funktion `social_vorschlag_setzen`, Rückgabe `angelegt/aufgefrischt/unveraendert`, kein `upsert`; Tests 12 (Pipeline, SQL) |
| 2 Rücksetzen auf `vorschlag` ohne erlaubte Alt-Status | mittel | E7 (nur aus `freigegeben`/`bereit`, sonst gesperrt), Abschnitt 7 (`social_bearbeiten`), Tests 12 |
| 3 Änderung am Karussell lässt das Reel stehen | mittel | E7 (Kopplung Karussell → Reel, `video_url` leeren, Neu-Freigabe kopiert neu), Abschnitt 7 (`social_bearbeiten` in einer Transaktion), Tests 12 |
| 4 Pfade ohne Host, `/bild/event/`, `koe-on-ice.webp` | mittel | E6 (Positivliste für Pfade, `/bild/event/` nie, `original`/`host` in der Folie, `bildZulaessig`), Abschnitt 6, Abschnitt 7 (`folien.bild`), Tests 12 |
| 5 `container_seit` einmal setzen, Reihenfolge der Fristen | gering | E10 (Ausnahme bei der Frist), Abschnitt 8 (Takt-Route Punkt 2 a–c), Tests 12 |
| 6 `upload_url` aus der Antwort von `start` | gering | Abschnitt 8 (`meta.ts`), Tests 12 |
| 7 `reel --post` ohne Statusbedingung | gering | Abschnitt 8 (Pipeline: `social_status_setzen(id, ['freigegeben'], 'bereit', …)`, sonst Video löschen) |

Bewusst verbleibender Rest (laut Prüfung 2): Der Button „erneut posten“ nach `unklar` kann doppelt posten, wenn die Media-ID nach einem Absturz nicht gespeichert wurde. Deshalb steht vor dem Button der Blick in die App (E10).
