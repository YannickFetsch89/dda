# Plan: Admin-Dashboard neu (admin.diesdas.events) – erste Fassung, 23.11.2026

**Status:** ENTWURF. Nicht freigegeben, nichts gebaut.
**Grundlage:** Entscheidungen des Auftraggebers vom 23.11.2026 (Abschnitt 2) und Bestand am Stand `79c7459` (Abschnitt 1).
**Gebaut wird erst nach Freigabe**, und zwar stufenweise. Jede Stufe hat eigene SQL, einen eigenen Deploy und eine eigene Abnahme.

---

## 1. Ausgangslage (geprüft am 23.11.2026)

### 1.1 Was unter admin.diesdas.events läuft

- **Streamlit-App** aus `dashboard/` (`app.py` 763 Zeilen, `meldungen.py`, `seo_aufraeumen.py`, `auth.py`).
  - Läuft auf `127.0.0.1:8502`, gestartet von `dashboard/dashboard.sh` (Watchdog per PID-Datei, Jail ohne `ps`).
  - Davor steht nginx als eigene Website in ISPConfig (`HANDOVER.md:96–104`). `curl https://admin.diesdas.events` liefert `<title>Streamlit`.
  - `deploy.yml` startet sie bei jedem Push neu und prüft `/_stcore/health`.
- **Anmeldung** (`dashboard/auth.py`): Supabase-Passwort-Login. Zugang nur mit `profiles.rolle = 'admin'`. Jede Sitzung hat einen eigenen Client mit anon-Key und dem Token des Admins, alles läuft unter RLS (`ist_admin()`). Der Service-Key wird bewusst nicht benutzt.
- **Tabs heute:** Tagesplaner, Event-Liste, Featured (Tipp/Highlight/Top/„nicht empfehlen“), Scraper-Report (nur lesen, „Jetzt neu scrapen“ startet `main.py` lokal per subprocess), Meldungen (prüfen, bearbeiten, freigeben), Newsletter (Liste, CSV), SEO-Aufräumen (`event_seo_entscheidungen`).

### 1.2 Was heute nur per SQL-Datei oder von Hand geht

Hauptbefund: Ein großer Teil der täglichen Redaktionsarbeit läuft über SQL-Dateien. Python-Skripte erzeugen sie (`--sql`), Claude schreibt sie, der Auftraggeber führt sie im SQL-Editor aus.

| Bereich | Aufgabe | Beispiele (`database/`) | Häufigkeit |
|---|---|---|---|
| Events | Dubletten zusammenlegen (behaltenes Event ergänzen, Dublette `abgelehnt`, 301 in `event_seo_entscheidungen`) | `dubletten_2026-11-11*.sql` aus `pipeline/dubletten_sql.py` | wiederkehrend |
| Events | `abgesagt` setzen | `korrekturen_2026-11-04.sql` | gelegentlich |
| Events | Adresse, Stadtteil, Ort korrigieren | `adressen_*`, `stadtteile_*`, `fft_kap1_*`, `datenfehler_*` | mehrmals pro Woche |
| Events | Ortsnamen vereinheitlichen | `ortsnamen_*` aus `pipeline/ortsnamen.py` | alle 1–3 Tage |
| Events | Gebiet bereinigen (Events außerhalb D/Neuss/Ratingen löschen) | `gebiet_bereinigung_*` (8 Dateien) aus `pipeline/gebiet.py --sql` | fast täglich |
| Events | `ort_id` nachtragen | `ort_id_nachtrag_*` aus `pipeline.ort_zuordnung --sql` | wiederkehrend |
| Events | Bild von Hand setzen | `weihnachtsmarkt_event_bild_further_*` | gelegentlich |
| Orte | Import, Texte freigeben, Bilder, Geo, Art, Zusammenlegen, Schließen, Zuordnung lösen | `orte_spielstaetten_*`, `orte_texte_*`, `orte_bilder_*`, `orte_korrekturen_*`, `orte_*_zusammen`, `orte_*_weglassen`, `orte_koe_loesen_*` | in Ausbauphasen täglich |
| Guides | Clubs/Kneipen (Club ↔ Bar, Score, Fotos), Spielplätze (freischalten, Fotos, Bildausschnitt), Weihnachtsmärkte (freischalten, Top-5, Score, Texte, Bilder, Zusammenlegung) | `clubs_abc_*`, `club_fotos_*`, `spielplaetze_freischalten.sql`, `weihnachtsmarkt_*` | saisonal fast täglich |
| Magazin | Entwurf korrigieren, veröffentlichen, Autoren | `magazin_wochenvorschau_*_korrektur.sql`, `magazin_startbeitraege_freigabe_*` | wöchentlich |
| Konten | neue Fassung der Einwilligungstexte | `einwilligungstexte_*` | selten |
| Sensibel | Fehltreffer bestätigen, Ausnahmen | `sensibel_nachtrag_*` | gelegentlich |
| Schalter | `KONTEN_AKTIV`, `MAGAZIN_AKTIV`, `GEBURTSTAG_AKTIV`, `ORTSSEITEN_MELDEN` | GitHub-Variablen | selten |

**Wichtig für die Umsetzung:**
- **Magazin veröffentlichen:** Der Trigger `magazin_status_pruefen` (`database/magazin_2026-11-19.sql:162–195`) lässt den Wechsel auf `veroeffentlicht` nur zu, wenn `current_user` nicht `service_role`, `anon` oder `authenticated` ist, also praktisch nur `postgres` im SQL-Editor. Ein Admin-Bereich braucht dafür eine `SECURITY DEFINER`-Funktion (Abschnitt 5, S2).
- **Pipeline überschreibt Felder:** `_anreicherungs_update_bauen` (`database/client.py:75–120`) ersetzt bei einem Duplikat `bild_url` (Rausgegangen → andere Quelle), `kategorie` (`kategorie_ersetzen`), die `uhrzeit` und beim Quellenwechsel auch Beschreibung, Preis und Adresse. **Eine Korrektur im Dashboard kann also beim nächsten Lauf verschwinden.**
- **Abgleich über Titel, Datum, Ort:** Die Pipeline findet bestehende Events über `titel + datum + ort` (`client.py:300`), danach über den Slug und über Ähnlichkeit. Ändert man im Dashboard Titel oder Ort, kann der nächste Lauf ein **neues Duplikat** anlegen. Beides löst E7 (Abschnitt 4.4).

### 1.3 Jobs (GitHub Actions)

| Workflow | Was | Zeitplan | Schalter | Schreibt |
|---|---|---|---|---|
| `scrape.yml` | `main.py --jetzt` (Scraper, KI, Captions, Posten) | täglich 05:00 UTC, läuft nur jeden 3. Tag; manuell immer | `ORTSSEITEN_MELDEN` | `scraper_laeufe`, `scraper_ergebnisse`, Log als Artefakt |
| `magazin.yml` | Wochenvorschau, Monats-Tipps, IndexNow, Prüfen | Fr 17:00, am 28. 17:00, stündlich, täglich 04:40 UTC | `MAGAZIN_AKTIV` | `magazin_beitraege`, `magazin_ki_kosten` |
| `geburtstag.yml` | Geburtstagsmails | täglich 08:00 UTC | `GEBURTSTAG_AKTIV` | `profiles.geburtstagsmail_zuletzt` |
| `deploy.yml` | Deploy per SSH | bei Push | `KONTEN_AKTIV` | – |
| `waechter.yml` | Website-Wächter | alle 15 min | – | Server-Datei `logs/waechter.txt` |
| `diagnose.yml` | Server-Diagnose | manuell | – | – |

### 1.4 Instagram

`pipeline/publisher.py` (Graph API v21.0) ist fertig und wird in `main.py:326–330` aufgerufen. **Er postet aber nichts**, weil `INSTAGRAM_ACCESS_TOKEN` und `INSTAGRAM_ACCOUNT_ID` in `scrape.yml` fehlen. Captions werden trotzdem bei jedem Lauf erzeugt (Limit 50). Benutzte Spalten: `events.status` (`neu | aufbereitet | gepostet | fehler`), `instagram_caption`, `gepostet_am`. `post_typ` steht nur in `CLAUDE.md`, nicht im Schema.

---

## 2. Entscheidungen des Auftraggebers (23.11.2026)

| Nr. | Entscheidung |
|---|---|
| D1 | Das Dashboard bleibt unter **admin.diesdas.events**. |
| D2 | **Automatisches Instagram-Posten** ist eines der nächsten Projekte. Der Admin-Bereich bekommt dafür einen festen Platz. |
| D3 | **Keine getrennten Rollen.** Es gibt nur Admin (`profiles.rolle = 'admin'`, `ist_admin()`). |
| D4 | **Reihenfolge:** (1) Cockpit, Scraper-Warnungen, Events, Empfehlungen → (2) Magazin → (3) Orte und Guides → (4) Newsletter mit Double-Opt-in → (5) Rest: Konten in Zahlen, Technik und Kosten, Schalter und Protokoll. |

---

## 3. Technik: Streamlit oder neuer Admin-Bereich?

### 3.1 Empfehlung (E1): neuer Admin-Bereich in der bestehenden Next.js-App

Der Admin-Bereich wird Teil von `web/` (Routen unter `/admin/**` und `/api/admin/**`) und wird über admin.diesdas.events ausgeliefert. Streamlit läuft während der Umstellung weiter und wird am Ende abgeschaltet (Stufe 6).

**Begründung:**
1. **Dieselbe Logik wie die Website.** Die Startseiten-Vorschau („Was wäre am 28.11. Tipp und Picks, und warum?“) rechnet mit `startPlaetze`, `breite`, `tippGilt` aus `web/lib/ableitungen.ts`. Die Magazin-Vorschau rendert mit `web/lib/magazin-markdown.ts`. In Streamlit müsste man das in Python nachbauen oder die Website im iframe zeigen, und es würde auseinanderlaufen.
2. **Sofort sichtbar.** Die Website hält den Event-Pool bis zu 10 Minuten im Cache (`cacheLife` in `web/lib/daten.ts`). Aus Next heraus kann eine Admin-Aktion den Cache gezielt leeren (`cacheTag`/`revalidateTag`, wie schon in `web/app/ort-foto/[slug]/route.ts`). Ein Tipp ist dann sofort live.
3. **Handy.** Streamlit ist auf dem Handy kaum bedienbar. Ein eigener Bereich mit dem Design-System der Website schon.
4. **Ein Stack, ein Prozess.** Kein zweiter Python-Webserver im Jail, kein eigener Watchdog, keine zweite Abhängigkeitsliste (`dashboard/requirements.txt`). Tests laufen mit Vitest wie der Rest.
5. **Login gibt es schon** in `web/lib/konto/` (Supabase-Sitzung, Cookies, `profiles.rolle`).

**Nachteile, offen benannt:**
- Mehr Aufwand am Anfang als ein Ausbau von Streamlit.
- Ein Fehler im Admin-Code kann den gemeinsamen Build brechen und damit die Website. Gegenmittel: Tests, Typprüfung und Build vor jedem Push, wie heute.
- Aufgaben, die Python-Code brauchen (Slug und Stadtteil bei Meldungen, Gebiet, Ortsnamen, Ortszuordnung, Scraper starten), laufen nicht im Admin-Prozess. Sie laufen als Job (Abschnitt 3.4) oder werden nach TypeScript übertragen.

**Alternativen (nicht empfohlen):**
- **Streamlit ausbauen:** schneller für Tabellen, aber die Punkte 1–3 fehlen. Je mehr Bereiche, desto größer der Nachbau.
- **Eigene zweite Next-App** (`admin/`, eigener Port): sauber getrennt, aber zwei Builds im Jail (Arbeitsspeicher, Dauer), zwei Abhängigkeitslisten, doppelte Bausteine.

### 3.2 Ausliefern unter admin.diesdas.events (ohne Rewrite)

Regel aus dem Betrieb: **Kein `NextResponse.rewrite` in `proxy.ts`**, hinter nginx gibt es live 500 (Memory „Proxy-Rewrite hinter nginx“, Commit faa29e8). Deshalb:
- **nginx (ISPConfig, macht der Auftraggeber):** Die Website admin.diesdas.events leitet ab dem Wechsel alles unverändert an `127.0.0.1:3847` (die Next-App) statt an 8502. WebSocket-Weiterleitung braucht Next nicht.
- **`proxy.ts`, Host `admin.diesdas.events`:**
  - `/` → **308** auf `/admin`.
  - Erlaubt: `/admin/**`, `/api/admin/**`, `/_next/**`, Schriften, Icons. Alles andere → echte **404** aus dem Proxy.
  - Jede Antwort: `X-Robots-Tag: noindex, nofollow`, `Cache-Control: private, no-store`, `Referrer-Policy: no-referrer`.
- **`proxy.ts`, Host `diesdas.events`:** `/admin/**` und `/api/admin/**` → **404**. So ist der Admin-Bereich nur über die Subdomain erreichbar.
- Lokal (`localhost:3100`) gilt der Admin-Host über einen Schalter in `.env.local`, damit man ihn entwickeln kann.

### 3.3 Anmeldung und Sicherheit

- **Login-Seite** `/admin/anmelden`: E-Mail und Passwort über Supabase (dieselben Konten wie auf der Website), danach Prüfung `profiles.rolle = 'admin'`. Ohne Admin-Rolle: Abmelden und neutrale Meldung.
- **Eigenes Cookie** `ddd_admin` (HttpOnly, Secure, `SameSite=Strict`, `Path=/`, ohne `Domain`, gilt also nur für admin.diesdas.events). Es ist getrennt vom Konto-Cookie der Website (`Path=/api/konto`). Laufzeit 12 Stunden, Token-Erneuerung wie in `web/lib/konto/sitzung.ts`.
- **Jede Seite und jede Route** prüft serverseitig Sitzung und Rolle, nicht nur das Layout.
- **Datenbank mit dem Token des Admins** (RLS über `ist_admin()`), wie heute in Streamlit. Den Service-Key nur, wo RLS nicht reicht (Zahlen aus `auth.users`, Storage-Kopie bei Meldungen). Jede solche Stelle ist im Code markiert.
- **Schreibende Routen:** nur `POST`, Origin-Prüfung (gibt es schon: `web/lib/konto/pruefungen.ts`), JSON, Größenlimit.
- **Zwei-Faktor (E2):** Supabase bietet TOTP. Vorschlag: **in Stufe 1 einbauen**, weil der Bereich viel ändern darf (Events löschen, Beiträge veröffentlichen). Alternative: später.
- **Protokoll:** Jede schreibende Admin-Aktion landet in `admin_protokoll` (Abschnitt 5, S1), mit Vorher/Nachher. Einfache Feldänderungen lassen sich daraus zurücknehmen.

### 3.4 Jobs aus dem Admin-Bereich starten (E3)

Für Python-Aufgaben (Scraper-Lauf, Magazin-Entwurf, Gebiet, Ortsnamen, Ortszuordnung) startet der Admin-Bereich den passenden **GitHub-Workflow** per `workflow_dispatch` und zeigt dessen Status an.
- Dazu braucht es einen **Fine-grained Token** nur für dieses Repo mit `Actions: read and write` und `Variables: read` als Secret `ADMIN_GITHUB_TOKEN`. `deploy.yml` schreibt ihn in `web/.env.local`, wie die anderen Schlüssel.
- Der Admin-Bereich liest damit auch den Stand der letzten Läufe (Deploy, Wächter, Geburtstag, Magazin) fürs Cockpit.
- **Schalter-Variablen werden nur angezeigt, nicht geändert** (E4). Ändern bleibt in GitHub, weil `KONTEN_AKTIV` erst mit einem Deploy wirkt.
- Der heutige Knopf „Jetzt neu scrapen“ (startet `main.py` auf dem Server) entfällt. Gescrapt wird nur noch in GitHub Actions.

### 3.5 Vorschläge statt SQL-Dateien (E5)

Statt dass Python-Skripte SQL-Dateien erzeugen, schreiben sie **Vorschläge** in eine Tabelle `admin_vorschlaege` (Abschnitt 5, S1). Im Admin-Bereich sieht man sie als Liste mit Begründung und nimmt sie einzeln oder gesammelt an oder lehnt sie ab. Erst die Annahme ändert die Daten, über eine Datenbank-Funktion mit `ist_admin()`-Prüfung.
- **Stufe 1:** Dubletten, Gebiet (außerhalb D/Neuss/Ratingen).
- **Stufe 3:** Ortsnamen, `ort_id`-Nachtrag, Adressen/Geo, Orte-Import.
- Abgelehnte Vorschläge merkt sich die Tabelle, damit der nächste Lauf sie nicht wieder vorschlägt.
- **Offene Frage (E6):** Sollen sehr sichere Vorschläge automatisch angewendet werden? Zum Beispiel ein Gebiet-Treffer mit eindeutiger Stadt außerhalb, etwa Köln. Vorschlag: **zuerst alles von Hand**. Nach zwei Wochen entscheiden wir je Art, was automatisch laufen darf.

---

## 4. Funktionsumfang je Stufe

### 4.1 Stufe 1a: Grundgerüst

- Routing, Login, Zwei-Faktor (falls E2 ja), Layout mit Navigation, `admin_protokoll`, gemeinsame Bausteine (Tabelle, Filterleiste, Bestätigungsdialog, Toast).
- **Navigation (fest, auch für spätere Stufen):** Cockpit · Events · Empfehlungen · Scraper · Magazin · Orte & Guides · Instagram · Newsletter · Meldungen · Konten · Technik · Protokoll. Was noch nicht gebaut ist, erscheint als „kommt in Stufe n“ mit Link auf den Streamlit-Tab, solange es ihn gibt.
- **Übergang Streamlit (E7a):** Streamlit zieht auf `admin.diesdas.events/alt/` um (`--server.baseUrlPath alt`, nginx-Location `/alt` → 8502 mit WebSocket). Die Next-Proxy-Regel lässt `/alt/**` dann nicht erreichen. Darum braucht nginx die `/alt`-Location **vor** der allgemeinen. **Alternative:** Streamlit bleibt bis zum Ende von Stufe 1 auf admin.diesdas.events, und der neue Bereich wird so lange nur lokal getestet.

### 4.2 Stufe 1b: Cockpit (Startseite `/admin`)

- **Ampeln** (grün/gelb/rot mit Zeitpunkt und Link):
  - Letzter Scraper-Lauf: Status, Alter (gelb > 4 Tage, rot > 7 Tage, Rhythmus 3 Tage), Zahl der Quellen mit Warnung.
  - Deploy, Wächter, Geburtstagsmails, Magazin-Job: letzter Lauf laut GitHub (E3).
  - Website: Antwort von `diesdas.events/robots.txt` (Server-Abruf beim Laden der Seite).
- **Zu erledigen** (je Zeile Anzahl + Link):
  - offene Meldungen (`event_meldungen.status = 'neu'`);
  - Magazin-Entwürfe `in_pruefung` (rot, wenn `gueltig_von` in ≤ 2 Tagen);
  - offene Vorschläge (`admin_vorschlaege`, je Art);
  - kommende 14 Tage: Tage **ohne** Redaktions-Tipp;
  - kommende 7 Tage: Events ohne Bild, ohne Stadtteil, ohne Adresse.
- **Kennzahlen:** Events heute / nächste 7 Tage, neu seit dem letzten Lauf, Konten gesamt (Zahl, Stufe 5 ausführlicher).

### 4.3 Stufe 1c: Scraper

- **Läufe:** Liste aus `scraper_laeufe` mit Kennzahlen und Link zum GitHub-Log.
- **Quellen:** Je Quelle die letzten 10 Läufe als kleine Zeile (Anzahl, Status), letzter erfolgreicher Lauf, letzte Meldung.
- **Warnregeln** (gerechnet beim Anzeigen, keine neue Tabelle):

| Nr. | Regel | Stufe |
|---|---|---|
| W1 | Status `fehler` im letzten Lauf | rot |
| W2 | 0 Events (`leer`), obwohl die Quelle in 2 der letzten 3 Läufe > 0 hatte. `saisonal` und `uebersprungen` zählen nicht | rot |
| W3 | Anzahl < 40 % des Medians der letzten 5 Läufe (Median ≥ 10) | gelb |
| W4 | Seit 3 Läufen kein `ok` | rot |
| W5 | Lauf älter als 4 Tage oder noch `laeuft` nach 90 min | rot |
| W6 | `speicher_fehler > 0` im Lauf | gelb |

- **Benachrichtigung (E8):** Vorschlag: Am Ende jedes Laufs schickt `main.py` bei W1/W2/W4/W6 **eine Mail** an hallo@diesdas.events über denselben SMTP-Weg wie die Geburtstagsmails (`smtplib`, keine neue Bibliothek). Dieselben Regeln stehen dann in Python **und** TypeScript. Ein gemeinsamer Testfall sichert, dass beide gleich rechnen. **Alternative:** nur im Cockpit anzeigen, keine Mail.
- **Lauf starten** (E3): Button „Scraper-Lauf starten“ → `scrape.yml` per `workflow_dispatch`, danach Status-Anzeige.
- **Quellen an/aus:** **nicht in Stufe 1** (braucht Änderungen in `main.py`). Vorgemerkt für Stufe 5.

### 4.4 Stufe 1d: Events

- **Liste und Suche:** Zeitraum, Kategorie, Stadtteil, Quelle, Ort, Text. Filter-Chips: abgelehnt, abgesagt, nicht empfehlen, ohne Bild, ohne Stadtteil, ohne Adresse, ohne `ort_id`, sensibel. Seitenweise, 50 je Seite.
- **Detailseite** mit Vorschau der Eventkarte wie auf der Website und Link zur Live-Seite.
- **Bearbeiten** (Whitelist): `titel`, `datum`, `datum_bis`, `uhrzeit`, `ort`, `adresse`, `stadtteil`, `kategorie`, `unterkategorie`, `preis`, `beschreibung`, `bild_url`, `ort_id`, dazu die Schalter `abgesagt`, `abgelehnt`, `nicht_empfehlen`. Der Slug bleibt immer gleich, damit Links und Merklisten halten.
- **Schutz vor Überschreiben (E7):**
  - Neue Spalte `events.redaktion_felder text[]`: Jedes im Dashboard geänderte Feld kommt hinein. `_anreicherungs_update_bauen` lässt diese Felder in Ruhe, auch bei Bild, Kategorie, Uhrzeit und Quellenwechsel.
  - Neue Spalten `events.abgleich_titel` und `events.abgleich_ort`: Ändert die Redaktion Titel oder Ort, bleiben hier die Werte der Quelle stehen. Der Abgleich in `client.py` (Schritt 1) sucht zusätzlich über diese Spalten. So entsteht kein neues Duplikat.
  - Ein Button „Redaktionsänderungen zurücksetzen“ leert `redaktion_felder` für ein Event.
- **Dubletten:** Die Pipeline (`pipeline/dubletten_sql.py`, umgebaut) schreibt Vorschläge (E5). Die Annahme macht in einer Funktion dasselbe wie heute die SQL: behaltenes Event ergänzen, Dublette `abgelehnt = true`, 301 in `event_seo_entscheidungen`, Merklisten-Einträge auf das behaltene Event umziehen. Dazu in der Event-Detailseite **„Als Dublette von … markieren“** von Hand, mit Suche nach dem Ziel-Event.
- **Gebiet:** `pipeline/gebiet.py` schreibt Vorschläge statt SQL. Annahme = Event löschen wie heute (`DELETE`). Ist es schon in einer Merkliste, wird es stattdessen `abgelehnt` (Prüfung in der Funktion).
- **Cache:** Nach jeder Änderung wird der Event-Pool-Cache der Website geleert (`cacheTag('events')` in `eventPoolLaden`, `revalidateTag` in der Admin-Route).

### 4.5 Stufe 1e: Empfehlungen

- **Tagesvorschau** `/admin/empfehlungen?tag=2026-11-28`: zeigt genau, was die Startseite an dem Tag zeigt (Tipp, Picks, „Diese Woche beliebt“, Wochenend-Tipps), gerechnet mit denselben Funktionen aus `web/lib/ableitungen.ts`. Je Event **warum**: Stufe 0–3 mit Grund (Stamm, Serie, Langläufer, Zugpferd-Ort), Flaggen, Fokustag.
- Darunter alle weiteren Kandidaten des Tages, sortiert nach `nachEmpfehlung`, je mit den Buttons **Tipp des Tages**, **Highlight der Woche**, **Top-Event des Monats**, **nicht empfehlen**. Nach dem Klick rechnet die Vorschau neu.
- **Kalender** der nächsten 30 Tage: je Tag der Tipp (Redaktion oder automatisch), geltende Highlight- und Top-Flagge, Hinweis „kein Bild“.
- Die Flaggen-Zeitpunkte setzt die Route wie heute `flagge_setzen` im Dashboard (`highlight_gesetzt_am`, `top_gesetzt_am`).

### 4.6 Stufe 2: Magazin

- **Redaktionsplan:** Kalender mit festen Terminen (Wochenvorschau Fr → Ausgabe Mo–So, Monats-Tipps am 28.) und allen Beiträgen nach `gueltig_von`/`veroeffentlicht_am` mit Status. Fehlender Entwurf für einen festen Termin = rot.
- **Entwürfe:**
  - Liste nach Status.
  - Vorschau im Admin-Bereich mit demselben Renderer wie `/magazin/vorschau/[id]`. Der Vorschau-Schlüssel ist im Admin-Bereich nicht nötig, weil die Admin-Sitzung reicht.
  - Ergebnis der automatischen Prüfung (`pruefung` jsonb) als Liste (a)–(i) mit grün/rot.
  - KI-Angaben aus `ki_entwurf` (Modell, Kosten).
- **Bearbeiten:** `titel`, `seo_titel`, `teaser`, `inhalt_md` (Editor mit Live-Vorschau), `kurzfassung`, `faq`, `hero_*`, `gueltig_*`, `korrektur_hinweis`. Nach dem Speichern läuft die Prüfung erneut, über einen Job (`magazin.yml`, Schritt `pruefen`) oder über eine Route, falls die Prüfung in TypeScript vorliegt (bei der Umsetzung klären).
- **Events tauschen** (Wochenvorschau, Monats-Tipps): Ein Event aus der Auswahl entfernen oder durch einen Kandidaten ersetzen. Das ändert `event_ids` und den betreffenden Block in `inhalt_md`.
- **Veröffentlichen:** Button → RPC `admin_magazin_veroeffentlichen(id)` (`SECURITY DEFINER`, Eigentümer `postgres`, prüft `ist_admin()`). Dadurch gilt der bestehende Trigger mit allen Pflichtprüfungen weiter. Setzt `freigegeben_von`, `freigegeben_am`, `veroeffentlicht_am` und leert `vorschau_hash`. Danach Cache leeren, IndexNow über den bestehenden Job.
- **Zurückziehen, Korrekturhinweis, neuer Beitrag** (Rubriken `saison`, `stadtleben`, `nachtleben`, `genuss`, `familie` ohne Job) als leerer Entwurf.
- **Job starten:** Wochenvorschau oder Monats-Tipps neu erzeugen (`magazin.yml`, `dry_run` wählbar).
- **Autoren:** Liste, bearbeiten. Profilbilder bleiben Dateien im Repo, wie heute.
- **KI-Kosten:** Summe je Monat aus `magazin_ki_kosten`.

### 4.7 Stufe 3: Orte und Guides

- **Orte-Liste** (`orte`): Filter nach Typ (Spielstätte, Club, Bar, Restaurant, Spielplatz, Weihnachtsmarkt …), aktiv/freigeschaltet, ohne Text, ohne Bild, ohne Geo.
- **Ort bearbeiten:** Stammdaten (Name, Typ, Adresse, Stadtteil, Geo, Website), `aktiv`/`freigeschaltet_am`, Score und `score_manuell`, typabhängige `extras` (Formular je Typ, kein freies JSON).
- **Texte:** Entwurf neben der Live-Fassung, Quellen, Button „Text freigeben“ (ersetzt `orte_texte_*.sql`).
- **Bilder:** Kandidaten (Google-Foto, eigenes WebP), Auswahl, Bildausschnitt (`bild_fokus`) per Klick ins Bild. Eigene Bilder bleiben Dateien im Repo, weil das Upload-Thema offen ist (Q5).
- **Zusammenlegen** (Ort A in Ort B): Weiterleitung in `ort_weiterleitungen`, Events umhängen, Zeile löschen, als Funktion. **Schließen/Weglassen** mit Pflicht-Weiterleitung, wegen Trigger `orte_schutz`.
- **Zuordnung:** Events eines Ortes sehen, einzelne lösen (ersetzt `orte_koe_loesen_*`).
- **Vorschläge** (E5): Ortsnamen, `ort_id`-Nachtrag, Adressen/Geo, Import aus Kandidaten.
- **Guide-spezifisch:** Clubs ↔ Bar verschieben, Weihnachtsmärkte Top-5-Rang und Ruhetage, Spielplätze freischalten mit Prüf-Codes. Die CSV-Dateien unter `data/` bleiben Quelle für Importe. Was im Dashboard gepflegt wird, gilt danach als führend. Bei der Umsetzung je Guide festlegen, welche CSV-Spalten wegfallen (Q6).

### 4.8 Platz für Instagram (D2, eigener Plan)

Nur der Platz, gebaut wird es im eigenen Plan „Instagram-Posting“:
- Navigation „Instagram“ mit Hinweis „kommt“.
- **Vorgemerktes Datenmodell** `instagram_posts` (Entwurf, nicht in Stufe 1 anlegen): `id`, `event_id` oder `beitrag_id`, `typ` (`feed | reel | story | karussell`), `geplant_fuer`, `caption`, `bilder text[]`, `status` (`vorschlag | freigegeben | geplant | gepostet | fehler | verworfen`), `ig_media_id`, `fehler`, `freigegeben_von/_am`, `erstellt_am`.
- Aus Stufe 1e kommt der Button „für Instagram vormerken“ (deaktiviert, bis der Plan steht).
- **Hinweis:** Heute erzeugt jeder Scraper-Lauf bis zu 50 Captions, die niemand nutzt (Kosten). Vorschlag: im Instagram-Plan entscheiden, ob `captions_generieren` bis dahin pausiert (Q7).

### 4.9 Stufe 4: Newsletter mit Double-Opt-in

- Tabelle `newsletter_anmeldungen` hat schon `bestaetigt_am` und `abgemeldet_am`. Es fehlen ein Token für Bestätigung und Abmeldung, die Bestätigungsmail und die Seiten.
- **Ablauf:** Anmeldung → Mail mit Bestätigungslink (Token wie bei der Geburtstagsmail: HMAC, eigener Schlüssel) → `bestaetigt_am`. Abmeldelink in jeder Mail, One-Click (RFC 8058). Unbestätigte Anmeldungen nach 30 Tagen löschen.
- **Wer schickt die Mail? (E9):** Next hat kein SMTP ohne neue Bibliothek. Vorschlag: Die Website legt die Anmeldung an, und ein **Python-Job alle 15 Minuten** (GitHub Actions) schickt die Bestätigungsmails über `smtplib`. Nachteil: bis zu 15 Minuten Wartezeit. **Alternative:** `nodemailer` in `web/` (neue Bibliothek, Rückfrage nötig), dann sofort.
- **Im Admin-Bereich:** Liste (bestätigt / unbestätigt / abgemeldet), Export nur der Bestätigten, Löschen auf Anfrage.
- **Versand der „Zehn Tipps“** ist **nicht** Teil dieses Plans (eigener Plan, mit Vorschau aus `wochenendProgramm`).
- **Rechtliches:** Datenschutzerklärung (Abschnitt Newsletter) anpassen. Vorlage für den Anwalt, wie bei den Konten.

### 4.10 Stufe 5: Rest

- **Meldungen:** Umzug aus Streamlit. Slug und Stadtteil heute aus Python (`pipeline/stadtteil_mapper.py`, Slug der Pipeline). Vorschlag: Freigabe legt das Event mit `status = 'neu'` ohne Slug an, und der nächste Lauf ergänzt ihn. **Alternative:** Slug-Regel nach TypeScript übertragen. Entscheidung bei der Umsetzung.
- **SEO-Aufräumen:** Umzug aus Streamlit, unverändert.
- **Konten in Zahlen:** Funktion `admin_konten_kennzahlen()` (`SECURITY DEFINER`, nur Zahlen, nie Personen): Konten gesamt, neu je Woche, aktiv in 30 Tagen, Einwilligungen je Zweck, Interessen-Verteilung, Geburtstagsmails dieses Jahr. **Bewusst keine Suche nach Personen** (Datenschutz). Löschung und Auskunft bleiben im Supabase-Dashboard.
- **Sensibel-Regeln:** Treffer der letzten 30 Tage, Fehltreffer per Klick als Ausnahme (`event_sensibel_ausnahmen`).
- **Technik und Kosten:**
  - Speicherplatz auf dem Server (`fs.statfs` in einer Route).
  - Größe von `logs/` und `.next`.
  - KI-Kosten Magazin.
  - Anthropic- und Google-Kosten gesamt nur, wenn es dafür eine Quelle gibt (Q8).
- **Schalter:** `KONTEN_AKTIV`, `MAGAZIN_AKTIV`, `GEBURTSTAG_AKTIV`, `ORTSSEITEN_MELDEN` anzeigen (E4), mit Link zur GitHub-Seite.
- **Quellen an/aus:** Tabelle `quellen_einstellungen` (`quelle`, `aktiv`, `grund`), von `main.py` gelesen.
- **Protokoll:** Liste aus `admin_protokoll` mit Filter und „Rückgängig“ für einfache Feldänderungen.

### 4.11 Stufe 6: Streamlit abschalten

`dashboard/` und die Streamlit-Schritte in `deploy.yml` entfernen, nginx-Location `/alt` löschen, `dashboard/requirements.txt` streichen. Erst, wenn jeder Tab ersetzt ist.

---

## 5. Datenmodell und SQL-Bedarf (führt der Auftraggeber aus, jeweils vor dem Deploy der Stufe)

| Nr. | Stufe | Datei (Vorschlag) | Inhalt |
|---|---|---|---|
| S1 | 1a/1d | `database/admin_grundlagen_<datum>.sql` | `admin_protokoll` (id, zeitpunkt, admin_id, aktion, tabelle, ziel_id, vorher jsonb, nachher jsonb). RLS: lesen/schreiben nur `ist_admin()`, kein Update/Delete. `admin_vorschlaege` (id, art, ziel_tabelle, ziel_id, vorschlag jsonb, begruendung, status `offen/angenommen/abgelehnt`, quelle_lauf, erstellt_am, entschieden_von/_am, eindeutiger Schlüssel gegen Doppelvorschläge). Pipeline schreibt als `service_role`, Admin liest und entscheidet. Funktionen `admin_vorschlag_annehmen(id)`/`ablehnen(id)` je Art. |
| S2 | 1d | dieselbe Datei | `events.redaktion_felder text[] NOT NULL DEFAULT '{}'`, `events.abgleich_titel text`, `events.abgleich_ort text`. Prüfen, ob die RLS-Policy für Admin-Updates auf `events` alle neuen Felder erlaubt. Funktion `admin_dublette_zusammenlegen(behalten, dublette)`. |
| S3 | 2 | `database/admin_magazin_<datum>.sql` | `admin_magazin_veroeffentlichen(id)` und `admin_magazin_zurueckziehen(id)` (`SECURITY DEFINER`, Eigentümer `postgres`, `ist_admin()`-Prüfung, `search_path` fest). Admin-Policies für Lesen/Ändern von Entwürfen (bisher nur `service_role` und SQL-Editor). |
| S4 | 3 | `database/admin_orte_<datum>.sql` | Funktionen `admin_ort_zusammenlegen(von, nach)`, `admin_ort_schliessen(id, weiterleitung)`, `admin_ort_text_freigeben(id)`. Admin-Policies auf `orte`, `ort_weiterleitungen` prüfen. |
| S5 | 4 | `database/newsletter_doi_<datum>.sql` | Spalten für Token-Zeitpunkt, Versandstatus der Bestätigung. Aufräumregel. |
| S6 | 5 | `database/admin_rest_<datum>.sql` | `admin_konten_kennzahlen()`, `quellen_einstellungen`. |
| S7 | später | eigener Instagram-Plan | `instagram_posts`. |

Python-Änderungen: `database/client.py` (E7), `pipeline/dubletten_sql.py` und `pipeline/gebiet.py` (Vorschläge statt SQL), `main.py` (Warn-Mail E8, später Quellen an/aus), in Stufe 3 `pipeline/ortsnamen.py`, `pipeline/ort_zuordnung.py`, `pipeline/adressen_ergaenzen.py`.

---

## 6. Tests

- **Vitest** (`web/tests/admin-*.test.ts`):
  - Proxy: Host-Regeln (Admin-Host `/` → 308, fremde Pfade 404, Haupthost `/admin` 404).
  - Rollenprüfung: Route ohne Sitzung 401, ohne Admin-Rolle 403.
  - Warnregeln W1–W6 mit Beispielläufen.
  - Tagesvorschau gleich Startseite: für einen Beispieltag dieselbe Auswahl wie `startPlaetze`.
  - Whitelist beim Bearbeiten: unbekannte Felder abgewiesen; `redaktion_felder` wird gepflegt.
- **Python** (`tests/`):
  - `_anreicherungs_update_bauen` lässt `redaktion_felder` in Ruhe.
  - Abgleich über `abgleich_titel`/`abgleich_ort` findet das umbenannte Event.
  - Warnregeln gleich wie in TypeScript (gemeinsame Fixture).
  - Vorschläge statt SQL in Dubletten und Gebiet.
- **SQL:** Kontrollabfragen am Ende jeder Datei (wie bisher). Ein Test, dass ein Nicht-Admin die Funktionen nicht aufrufen kann.
- **Von Hand je Stufe:** Login mit Admin- und Nicht-Admin-Konto, eine Änderung je Bereich, sichtbare Wirkung auf der Website, Protokolleintrag, Rückgängig.

---

## 7. Umsetzungsschritte und Freigaben

| Schritt | Inhalt | SQL vorher | Freigabe |
|---|---|---|---|
| 0 | Dieser Plan, Cursor-Prüfung, Freigabe | – | Plan |
| 1a | Grundgerüst, Login, Protokoll, Proxy-Regeln, nginx-Umstellung (E7a) | S1 (Protokoll) | Deploy + nginx durch Auftraggeber |
| 1b | Cockpit | – | Deploy |
| 1c | Scraper + Warnregeln (+ Mail, E8) | – | Deploy |
| 1d | Events, Schutz vor Überschreiben, Dubletten/Gebiet als Vorschläge | S1 (Vorschläge), S2 | Deploy, erster Scraper-Lauf danach prüfen |
| 1e | Empfehlungen | – | Deploy |
| 2 | Magazin | S3 | Deploy, ein echter Beitrag über den neuen Weg |
| 3 | Orte und Guides | S4 | Deploy je Teilbereich |
| 4 | Newsletter DOI | S5 | Anwalt, Deploy |
| 5 | Meldungen, SEO, Konten, Technik, Schalter, Quellen | S6 | Deploy |
| 6 | Streamlit abschalten | – | Deploy + nginx |

Jeder Schritt: lokal bauen und testen, Cursor-Prüfung der Umsetzung, Push nur mit OK, Push aus einem temporären Worktree.

---

## 8. Risiken

- **Gemeinsamer Build:** Ein Fehler im Admin-Code legt auch die Website lahm. Gegenmittel: Tests, `tsc`, Build vor jedem Push. Admin-Code nur unter `web/app/admin`, `web/app/api/admin`, `web/lib/admin`.
- **Rechte:** Ein Fehler in der Rollenprüfung würde die Datenbank öffnen. Gegenmittel: RLS bleibt die zweite Sicherung, weil mit dem Admin-Token geschrieben wird und nicht mit dem Service-Key. Tests für 401/403.
- **Pipeline-Änderung (E7):** Der Abgleich ist heikel (Duplikate, Quellenwechsel). Gegenmittel: Python-Tests mit echten Fällen, erster Lauf nach dem Deploy wird im Scraper-Report geprüft.
- **Zwei Dashboards gleichzeitig:** Während des Übergangs können beide dasselbe Event ändern. Hingenommen, weil es nur einen Admin gibt.
- **GitHub-Token** auf dem Server: Fine-grained, nur dieses Repo, nur Actions und Variablen lesen. Ablauf nach 1 Jahr: im Cockpit anzeigen.

---

## 9. Offene Fragen an den Auftraggeber

| Nr. | Frage | Vorschlag |
|---|---|---|
| E1 | Neuer Admin-Bereich in Next.js statt Streamlit? | ja (3.1) |
| E2 | Zwei-Faktor (TOTP) für den Admin-Login schon in Stufe 1? | ja |
| E3 | GitHub-Token für Jobs und Laufstatus? | ja, Fine-grained, nur Actions und Variablen lesen |
| E4 | Schalter nur anzeigen, nicht ändern? | ja |
| E5 | Vorschläge statt SQL-Dateien (Dubletten, Gebiet, später Orte)? | ja |
| E6 | Sichere Vorschläge automatisch anwenden? | zuerst nein, nach zwei Wochen je Art entscheiden |
| E7 | Redaktionsänderungen vor der Pipeline schützen (`redaktion_felder`, `abgleich_*`)? | ja |
| E7a | Streamlit während des Übergangs unter `/alt`? | ja (nginx-Location durch den Auftraggeber) |
| E8 | Warn-Mail nach dem Scraper-Lauf an hallo@? | ja |
| E9 | DOI-Mail per Python-Job (bis 15 min Verzug) oder `nodemailer` (neue Bibliothek)? | Python-Job |
| Q5 | Bilder-Upload im Admin-Bereich (Storage) oder weiter Dateien im Repo? | vorerst Repo, Upload in eigenem Schritt |
| Q6 | CSV-Dateien der Guides: Was bleibt führend? | bei Stufe 3 je Guide |
| Q7 | Captions bis zum Instagram-Plan pausieren? | im Instagram-Plan entscheiden |
| Q8 | Gibt es Zugänge für Kostenzahlen (Anthropic Admin-API, Google Cloud Billing)? | sonst nur Magazin-Kosten |

---

## Anhang A: Cursor-Prüf-Prompt (erste Fassung)

```
Prüfe den Plan `docs/plan-admin-dashboard-2026-11-23.md` (Admin-Bereich neu unter admin.diesdas.events) gegen den
tatsächlichen Code im Repo. Ändere keinen Code und keinen Plan – nur Befunde.

Schwerpunkte:
1. Abschnitt 1: Stimmen die Fakten zum Bestand (dashboard/auth.py, dashboard/app.py, deploy.yml, Workflows,
   Trigger magazin_status_pruefen in database/magazin_2026-11-19.sql, publisher.py/main.py:326–330)?
2. Abschnitt 3.2: Lassen sich die Host-Regeln in web/proxy.ts ohne NextResponse.rewrite umsetzen (nur Redirect und
   direkte Response, siehe Kommentar in proxy.ts)? Bricht etwas an der bestehenden Pfad-Prüfung (web/lib/pfad-pruefung.ts)?
   Erreichen /_next-Dateien und Schriften den Admin-Host?
3. Abschnitt 3.3: Kann das Admin-Login die Sitzungslogik aus web/lib/konto/ (sitzung.ts, cookies.ts, clients.ts)
   wiederverwenden, mit eigenem Cookie (Path=/, SameSite=Strict, host-only)? Wo hängt sie an KONTEN_AKTIV oder am
   Cookie-Pfad /api/konto?
4. Abschnitt 4.4 / E7: Reicht `redaktion_felder` in `_anreicherungs_update_bauen` (database/client.py:75–120), um
   Redaktionsänderungen zu schützen (bild_url, kategorie, uhrzeit, Quellenwechsel)? Findet der Abgleich in
   client.py (Schritt 1 titel+datum+ort, Schritt 2 Slug, Schritt 3 Ähnlichkeit) ein Event wieder, dessen Titel oder
   Ort die Redaktion geändert hat, wenn zusätzlich über `abgleich_titel`/`abgleich_ort` gesucht wird? Was ist mit
   geänderter Uhrzeit oder geändertem Datum?
5. Abschnitt 4.4: Entspricht `admin_dublette_zusammenlegen` dem, was pipeline/dubletten_sql.py heute erzeugt
   (inkl. event_seo_entscheidungen)? Was passiert mit Merklisten-Einträgen der Dublette?
6. Abschnitt 4.5: Kann die Tagesvorschau dieselbe Auswahl liefern wie die Startseite (page.tsx: eventPoolLaden,
   filtern mit mitLanglaeufern, stufenKontext, startPlaetze, beliebtAuswahl, wochenendProgramm mit vergangenen
   Wochenendtagen)? Welche Eingaben fehlen?
7. Abschnitt 4.4/4.5: Ist `cacheTag('events')` + `revalidateTag` mit cacheComponents und dem bestehenden
   cacheLife in web/lib/daten.ts möglich, ohne die Startseite zu verlangsamen?
8. Abschnitt 4.6 / S3: Umgeht `admin_magazin_veroeffentlichen` als SECURITY DEFINER (Eigentümer postgres) den
   Trigger korrekt (current_user = postgres), ohne seine Pflichtprüfungen auszuhebeln? Welche RLS-Policies auf
   magazin_beitraege fehlen für Admin-Lesen/-Ändern?
9. Abschnitt 4.3: Sind die Warnregeln W1–W6 mit den Spalten von scraper_laeufe/scraper_ergebnisse
   (database/scraper_report.sql, scraper_laeufe_ort_kennzahlen_2026-11-20.sql) rechenbar? Status-Werte richtig?
10. Abschnitt 5: Fehlen Tabellen, Policies oder Funktionen? Widersprüche zwischen Abschnitt 4, 5 und 7?

Ausgabe je Befund: Schweregrad (kritisch / mittel / gering) · Fundstelle (Plan-Abschnitt + Datei:Zeile) · Befund ·
Vorschlag. Nach Schweregrad sortiert. Am Ende: Gesamturteil (freigabefähig ja/nein). Die offenen Fragen E1–E9 und
Q5–Q8 entscheidet der Auftraggeber; sie blockieren die technische Prüfung nicht.
```

## Prüfhistorie

- 23.11.2026: erste Fassung (Claude), Bestand per Code und SQL-Dateien geprüft.
