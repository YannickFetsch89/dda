# Plan: Admin-Dashboard neu (admin.diesdas.events) – vierte Fassung, freigegeben 23.11.2026

**Status:** **FREIGEGEBEN 23.11.2026** durch den Auftraggeber (vierte Fassung). Die Entscheidungen E1–E9 und Q5–Q8 sind wie vorgeschlagen bestätigt. Vier Cursor-Prüfungen sind eingearbeitet (Anhänge B–E); Prüfung 3 und 4 urteilen „freigabefähig“. Umsetzung ab Schritt 1a-0.
**Grundlage:** Entscheidungen des Auftraggebers vom 23.11.2026 (Abschnitt 2) und Bestand am Stand `79c7459` (Abschnitt 1).
**Gebaut wird erst nach Freigabe**, und zwar stufenweise. Jede Stufe hat eigene SQL, einen eigenen Deploy und eine eigene Abnahme.

---

## 1. Ausgangslage (geprüft am 23.11.2026)

### 1.1 Was unter admin.diesdas.events läuft

- **Streamlit-App** aus `dashboard/` (`app.py` 763 Zeilen, `meldungen.py`, `seo_aufraeumen.py`, `auth.py`).
  - Läuft auf `127.0.0.1:8502`, gestartet von `dashboard/dashboard.sh` (Watchdog per PID-Datei, Jail ohne `ps`).
  - Davor steht nginx als eigene Website in ISPConfig (`HANDOVER.md:96–104`). `curl https://admin.diesdas.events` liefert `<title>Streamlit`.
  - `deploy.yml` startet sie bei jedem Push auf `claude/setup-project-structure-5QNOf` neu und prüft `/_stcore/health`.
  - nginx gibt an die Apps den Host `localhost:<port>` und `X-Forwarded-Proto` weiter, nicht den öffentlichen Host (Kommentar in `web/proxy.ts:17–19`). Das ist wichtig für 3.2.
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
- **Magazin veröffentlichen:** Der Trigger `magazin_status_pruefen` (`database/magazin_2026-11-19.sql:162–195`) lässt den Wechsel auf `veroeffentlicht` nur zu, wenn `current_user` nicht `service_role`, `anon` oder `authenticated` ist, also praktisch nur `postgres` im SQL-Editor. Ein Admin-Bereich braucht dafür `SECURITY DEFINER`-Funktionen (Abschnitt 5, S3). `authenticated` hat auf `magazin_beitraege` heute nur `SELECT` auf die öffentlichen Spalten veröffentlichter Beiträge (`magazin_2026-11-19.sql:245–256`). Auf `magazin_ki_kosten` hat `authenticated` gar keinen Zugriff.
- **Pipeline überschreibt Felder:** `_anreicherungs_update_bauen` (`database/client.py:75–135`) ersetzt bei einem Duplikat an drei Stellen:
  1. in der Schleife `bild_url` (Rausgegangen → andere Quelle), `kategorie` (`kategorie_ersetzen`) und leere Felder, wobei `abgesagt = false` als leer gilt;
  2. im Uhrzeit-Block (`:120–124`) die Uhrzeit, wenn ein Veranstalter gegen einen Aggregator steht;
  3. beim Quellenwechsel (`:127–133`) Quelle, Bild, Beschreibung, Preis und Adresse.

  **Eine Korrektur im Dashboard kann also beim nächsten Lauf verschwinden.**
- **Abgleich:** Die Pipeline findet ein bestehendes Event so (`client.py:296–335`):
  - Schritt 1: `titel + datum + ort` mit passender Uhrzeit.
  - Schritt 2: Slug-Basis (aus den Quelldaten gerechnet) mit gleicher Uhrzeit. Eine andere Uhrzeit gilt als weitere Vorstellung und bekommt einen neuen Slug (`:186–198`).
  - Schritt 3: Ähnlichkeit am selben Datum.

  Ändert die Redaktion Uhrzeit oder Datum, legt der nächste Lauf eine **zweite Zeile** an. Der Unique-Schlüssel `(titel, datum, ort, uhrzeit)` lässt das zu. Titel oder Ort allein fängt meist Schritt 2 ab, weil der Slug bleibt. Beides löst E7 (Abschnitt 4.4).

### 1.3 Jobs (GitHub Actions)

| Workflow | Was | Zeitplan | Schalter | Schreibt |
|---|---|---|---|---|
| `scrape.yml` | `main.py --jetzt` (Scraper, KI, Captions, Posten) | täglich 05:00 UTC, läuft nur jeden 3. Tag; manuell immer | – (`ORTSSEITEN_MELDEN` schaltet nur die IndexNow-Meldung der Ortsseiten) | `scraper_laeufe`, `scraper_ergebnisse`, Log als Artefakt |
| `magazin.yml` | Wochenvorschau, Monats-Tipps, IndexNow, Prüfen | Fr 17:00, am 28. 17:00, stündlich, täglich 04:40 UTC | `MAGAZIN_AKTIV` | `magazin_beitraege`, `magazin_ki_kosten` |
| `geburtstag.yml` | Geburtstagsmails | täglich 08:00 UTC | `GEBURTSTAG_AKTIV` | `profiles.geburtstagsmail_zuletzt` |
| `deploy.yml` | Deploy per SSH | bei Push auf `claude/setup-project-structure-5QNOf` | `KONTEN_AKTIV` | – |
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

Regeln aus dem Betrieb:
- **Kein `NextResponse.rewrite` in `proxy.ts`.** Hinter nginx gibt es live 500 (Memory „Proxy-Rewrite hinter nginx“, Commit faa29e8). Erlaubt sind nur Redirect und direkte Response, wie heute schon in `proxy.ts`.
- **Next sieht den öffentlichen Host nicht.** nginx gibt `Host: localhost:3847` weiter. `request.nextUrl.hostname` ist für diesdas.events und admin.diesdas.events also gleich (Cursor-Befund 1). Eine Host-Regel braucht deshalb einen eigenen Kopf.

**Lösung: zwei Sicherungen, nginx und Proxy.**

1. **nginx (ISPConfig, macht der Auftraggeber, Anleitung kommt mit Schritt 1a):**
   - **Beide** Websites setzen einen festen Kopf, der einen vom Browser mitgeschickten Wert überschreibt:
     - diesdas.events: `proxy_set_header X-DDD-Bereich web;`
     - admin.diesdas.events: `proxy_set_header X-DDD-Bereich admin;`
   - **Reihenfolge (Cursor-Prüfung 2, Befund 1):** Der Eintrag auf **diesdas.events** kommt **vor** dem ersten Deploy mit Admin-Code (Schritt 1a-0 in Abschnitt 7). Er ändert für die Website nichts, solange der Code ihn nicht liest. Ohne ihn käme jeder, der `X-DDD-Bereich: admin` selbst mitschickt, auf der öffentlichen Website an die Admin-Routen. Dort fängt ihn zwar noch die Anmeldung ab, aber die Trennung wäre weg. Ob nginx den Kopf wirklich überschreibt, zeigt erst die Prüfung **nach dem Deploy von Schritt 1a**: `curl -H "X-DDD-Bereich: admin" https://diesdas.events/admin` muss 404 liefern (Abschnitt 7 und 8). Direkt nach 1a-0 sagt diese Prüfung nichts, weil `/admin` dann noch nicht existiert (Cursor-Prüfung 3, Befund 4).
   - admin.diesdas.events leitet an `127.0.0.1:3847` (Next) statt an 8502, **aber nur diese Pfade:** `/admin`, `/api/admin`, `/_next` (dort liegen auch die Schriften unter `/_next/static/media`), `/bild`, `/fallback`, `/magazin-bild`, `/magazin-autoren`, `/ort-foto`, `/ort-bilder`, `/icon.svg`.
   - `location = /` → `return 308 /admin;` (relative Adresse, kein localhost in `Location`).
   - Alle anderen Pfade → `return 404;`.
   - Für den Übergang zusätzlich `location /alt/` → 8502 mit WebSocket (4.1).
2. **`web/proxy.ts`** (zweite Sicherung, testbar):
   - Matcher um `"/"`, `"/admin/:path*"` und `"/api/admin/:path*"` ergänzen. `/_next` und die Bildpfade bleiben **außerhalb** des Matchers, damit die Website nicht langsamer wird. Die übrigen Matcher-Einträge und Zweige bleiben unverändert.
   - `/admin/**` oder `/api/admin/**` **ohne** `X-DDD-Bereich: admin` → echte 404 (`NICHT_GEFUNDEN_HTML`). Diese Prüfung steht **vor** allen bestehenden Zweigen. Fehlt der Kopf, gilt die Anfrage als Website, der Admin-Bereich ist also geschlossen.
   - `/` **mit** `X-DDD-Bereich: admin` → 308 mit `Location: /admin`, gebaut als `new NextResponse(null, { status: 308, headers: { Location: "/admin" } })`. Nie mit `request.url`, sonst zeigt `Location` auf localhost.
   - Admin-Antworten bekommen `X-Robots-Tag: noindex, nofollow`, `Cache-Control: private, no-store`, `Referrer-Policy: no-referrer`. Das passiert im Proxy für `/admin` und `/api/admin` und zusätzlich über `headers()` in `next.config.ts`.
3. **Lokal:** `ADMIN_LOKAL=1` in `web/.env.local` lässt `/admin` ohne Kopf zu, **nur** wenn die Anfrage nicht hinter einem Proxy kommt (gleiche Erkennung wie `erlaubteUrspruenge` in `web/lib/konto/pruefungen.ts:74–82`: kein `x-forwarded-*`). Ein Schalter, der nur am Host `localhost` hängt, träfe live ebenfalls zu, weil der Host dort `localhost:3847` ist.
4. **Bildpfade auf dem Admin-Host** (Cursor-Befund 9): Eventkarten laden `/bild/event/<id>` und `/fallback/…` (`web/lib/bilder.ts:20–25`, `web/lib/symbolbild.ts:168`), die Magazin-Vorschau `/magazin-bild/…` (`web/lib/magazin-bilder.ts:89`), Orte `/ort-foto/…` und `/ort-bilder/…`. Deshalb stehen sie in der nginx-Liste. Diese Antworten sind ohnehin öffentlich, eigene Köpfe brauchen sie nicht.

### 3.3 Anmeldung und Sicherheit

- **Login-Seite** `/admin/anmelden`: E-Mail und Passwort über Supabase (dieselben Konten wie auf der Website), danach Prüfung `profiles.rolle = 'admin'`. Ohne Admin-Rolle: Abmelden und neutrale Meldung.
- **Eigenes Cookie** `ddd_admin` (HttpOnly, Secure, `SameSite=Strict`, `Path=/`, ohne `Domain`, gilt also nur für admin.diesdas.events). Laufzeit 12 Stunden.
- **Was aus `web/lib/konto/` wiederverwendet wird** (Cursor-Befund 8):
  - **Unverändert:** `authClientAnfrage`, `tokenPruefen`, `nutzerClient`. Sie hängen nicht an `KONTEN_AKTIV`.
  - **Mit Parameter:** Heute setzt `sitzungsCookie` fest `ddd_sitzung`, `Path=/api/konto`, `SameSite=Lax`, 30 Tage (`cookies.ts:53–67`). `cookiesLoeschen` löscht nur die Konto-Cookies. Beide bekommen ein Optionsobjekt (Name, Pfad, SameSite, Max-Age), die Konto-Aufrufe bleiben bitgleich. `sitzungAusAnfrage` (`sitzung.ts:28–79`) bekommt den Cookie-Namen als Argument.
  - **Nicht wiederverwendet:** `kontoRoute` (`route.ts:132–137`). Sie antwortet bei `KONTEN_AKTIV ≠ 1` mit 404 und hängt am Konto-Ablauf. Die Admin-Routen bekommen einen eigenen Rahmen `adminRoute` in `web/lib/admin/route.ts`: Bereichs-Kopf, Origin, JSON, Größe, Sitzung, Rolle, Zwei-Faktor-Stufe (`aal2`), Protokoll.
  - **Origin-Prüfung:** `erlaubteUrspruenge` erlaubt live nur `SITE_URL`, und `originErlaubt` sucht nur `ddd_sitzung` (`pruefungen.ts:74–94`). Für den Admin-Bereich gibt es `ADMIN_URL` (`https://admin.diesdas.events`) und eine eigene Prüfung, die `ddd_admin` kennt und nur `ADMIN_URL` erlaubt. Die Konto-Prüfung bleibt unverändert.
- **Jede Seite und jede Route** prüft serverseitig Sitzung, Rolle und Zwei-Faktor-Stufe, nicht nur das Layout.
- **Datenbank mit dem Token des Admins** (RLS über `ist_admin()`), wie heute in Streamlit.
  - Wo RLS oder Trigger den Admin-Token nicht durchlassen, laufen **`SECURITY DEFINER`-Funktionen**: Eigentümer `postgres`, erste Zeile `IF NOT public.ist_admin() THEN RAISE …`, fester `search_path`, `EXECUTE` nur für `authenticated`. Betroffen sind Dubletten, Gebiet, Magazin und Orte, die Liste steht in Abschnitt 5. `ist_admin()` liest `auth.uid()`, nicht `current_user`, und funktioniert deshalb auch in diesen Funktionen.
  - Den Service-Key nur, wo es keine Funktion gibt (Zahlen aus `auth.users` in Stufe 5, Storage-Kopie bei Meldungen). Jede solche Stelle ist im Code markiert.
- **Schreibende Routen:** nur `POST`, Origin-Prüfung (s. o.), JSON, Größenlimit.
- **Zwei-Faktor (E2, entschieden: ja, Stufe 1a):** TOTP über Supabase Auth MFA. Beim ersten Login wird es eingerichtet. Ohne `aal2` gibt es nur die Einrichtungs- bzw. Code-Seite.
- **Protokoll:** Jede schreibende Admin-Aktion landet in `admin_protokoll` (Abschnitt 5, S1), mit Vorher/Nachher. Einfache Feldänderungen lassen sich daraus zurücknehmen.

### 3.4 Jobs aus dem Admin-Bereich starten (E3)

Für Python-Aufgaben (Scraper-Lauf, Magazin-Entwurf, Gebiet, Ortsnamen, Ortszuordnung) startet der Admin-Bereich den passenden **GitHub-Workflow** per `workflow_dispatch` und zeigt dessen Status an.
- Dazu braucht es einen **Fine-grained Token** nur für dieses Repo mit **`Actions: read and write`** (Starten per `workflow_dispatch` braucht Schreibrecht, Cursor-Befund 11) und **`Variables: read`** als Secret `ADMIN_GITHUB_TOKEN`. Weitere Rechte bekommt er nicht. `deploy.yml` schreibt ihn in `web/.env.local`, wie die anderen Schlüssel.
- Der Admin-Bereich liest damit auch den Stand der letzten Läufe (Deploy, Wächter, Geburtstag, Magazin) fürs Cockpit.
- **Schalter-Variablen werden nur angezeigt, nicht geändert** (E4). Ändern bleibt in GitHub, weil `KONTEN_AKTIV` erst mit einem Deploy wirkt.
- Der heutige Knopf „Jetzt neu scrapen“ (startet `main.py` auf dem Server) entfällt. Gescrapt wird nur noch in GitHub Actions.

### 3.5 Vorschläge statt SQL-Dateien (E5)

Statt dass Python-Skripte SQL-Dateien erzeugen, schreiben sie **Vorschläge** in eine Tabelle `admin_vorschlaege` (Abschnitt 5, S1). Im Admin-Bereich sieht man sie als Liste mit Begründung und nimmt sie einzeln oder gesammelt an oder lehnt sie ab. Erst die Annahme ändert die Daten, über eine `SECURITY DEFINER`-Funktion mit `ist_admin()`-Prüfung (3.3). Der Admin-Token allein darf weder Events löschen noch fremde Merklisten-Zeilen ändern.
- **Stufe 1:** Dubletten, Gebiet (außerhalb D/Neuss/Ratingen).
- **Stufe 3:** Ortsnamen, `ort_id`-Nachtrag, Adressen/Geo, Orte-Import.
- Abgelehnte Vorschläge merkt sich die Tabelle, damit der nächste Lauf sie nicht wieder vorschlägt.
- **E6 (entschieden):** zuerst alles von Hand. Nach zwei Wochen entscheiden wir je Art, was automatisch laufen darf.

---

## 4. Funktionsumfang je Stufe

### 4.1 Stufe 1a: Grundgerüst

- Routing (3.2), Login mit Zwei-Faktor, Layout mit Navigation, `admin_protokoll` **und** `admin_vorschlaege` (beide in S1, damit das Cockpit sie ab 1b zählen kann, Cursor-Befund 10), gemeinsame Bausteine (Tabelle, Filterleiste, Bestätigungsdialog, Toast).
- **Navigation (fest, auch für spätere Stufen):** Cockpit · Events · Empfehlungen · Scraper · Magazin · Orte & Guides · Instagram · Newsletter · Meldungen · Konten · Technik · Protokoll. Was noch nicht gebaut ist, erscheint als „kommt in Stufe n“ mit Link auf den Streamlit-Tab, solange es ihn gibt.
- **Übergang Streamlit (E7a, entschieden):** Streamlit zieht auf `admin.diesdas.events/alt/` um (`--server.baseUrlPath alt` in `dashboard/dashboard.sh`, Health-Check in `deploy.yml` dann `/alt/_stcore/health`). nginx leitet `location /alt/` an 8502 mit WebSocket (3.2). `/alt` erreicht Next nie.

### 4.2 Stufe 1b: Cockpit (Startseite `/admin`)

- **Ampeln** (grün/gelb/rot mit Zeitpunkt und Link):
  - Letzter Scraper-Lauf: Status, Alter (gelb > 4 Tage, rot > 7 Tage, Rhythmus 3 Tage), Zahl der Quellen mit Warnung.
  - Deploy, Wächter, Geburtstagsmails, Magazin-Job: letzter Lauf laut GitHub (E3).
  - Website: Antwort von `diesdas.events/robots.txt` (Server-Abruf beim Laden der Seite).
  - Host-Trennung: `https://diesdas.events/admin` mit selbst gesetztem `X-DDD-Bereich: admin` muss 404 liefern, sonst rot (8). Ob der Server im Jail seine eigene öffentliche Adresse erreicht, zeigt erst der Betrieb. Kann er es nicht, zeigt die Ampel grau „nicht prüfbar“; die `curl`-Prüfung nach jedem Deploy bleibt davon unabhängig.
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

Quellen-Status (`scraper_ergebnisse.status`): `ok | leer | saisonal | uebersprungen | fehler`. Lauf-Status (`scraper_laeufe.status`): `laeuft | erfolgreich | fehler` (`database/scraper_report.sql:18`, `:43`).

| Nr. | Ebene | Regel | Stufe |
|---|---|---|---|
| W1 | Quelle (`scraper_ergebnisse`) | Status `fehler` im letzten Lauf | rot |
| W2 | Quelle | Status `leer`, obwohl die Quelle in 2 der letzten 3 Läufe `ok` mit Anzahl > 0 hatte | rot |
| W3 | Quelle | Anzahl < 40 % des Medians. Der Median läuft über die letzten 5 Läufe der Quelle mit Status `ok` oder `leer`; `saisonal`, `uebersprungen` und `fehler` zählen nicht mit. Gilt nur bei Median ≥ 10 | gelb |
| W4 | Quelle | In den letzten 3 Läufen der Quelle kein Status `ok`; `saisonal` und `uebersprungen` zählen nicht | rot |
| W5 | Lauf (`scraper_laeufe`) | Letzter Lauf älter als 4 Tage, oder Status `laeuft` seit mehr als 90 min | rot |
| W6 | Lauf | `speicher_fehler > 0` | gelb |

- **Benachrichtigung (E8, entschieden):** Am Ende jedes Laufs schickt `main.py` bei W1, W2, W4 oder W6 **eine Mail** an hallo@diesdas.events. Der Weg ist derselbe SMTP-Weg wie bei den Geburtstagsmails (`smtplib`, keine neue Bibliothek). Die Regeln W1–W6 stehen in Python (`pipeline/lauf_warnungen.py`) **und** TypeScript (`web/lib/admin/warnregeln.ts`). Eine gemeinsame JSON-Fixture in `tests/fixtures/` prüft beide.
- **Lauf starten** (E3): Button „Scraper-Lauf starten“ → `scrape.yml` per `workflow_dispatch`, danach Status-Anzeige.
- **Quellen an/aus:** **nicht in Stufe 1** (braucht Änderungen in `main.py`). Vorgemerkt für Stufe 5.

### 4.4 Stufe 1d: Events

- **Liste und Suche:** Zeitraum, Kategorie, Stadtteil, Quelle, Ort, Text. Filter-Chips: abgelehnt, abgesagt, nicht empfehlen, ohne Bild, ohne Stadtteil, ohne Adresse, ohne `ort_id`, sensibel. Seitenweise, 50 je Seite.
- **Detailseite** mit Vorschau der Eventkarte wie auf der Website und Link zur Live-Seite.
- **Bearbeiten** (Whitelist): `titel`, `datum`, `datum_bis`, `uhrzeit`, `ort`, `adresse`, `stadtteil`, `kategorie`, `unterkategorie`, `preis`, `beschreibung`, `bild_url`, `ort_id`, dazu die Schalter `abgesagt`, `abgelehnt`, `nicht_empfehlen`. Der Slug bleibt immer gleich, damit Links und Merklisten halten.
- **Schutz vor Überschreiben (E7), Teil A: Felder** (Cursor-Befund 5):
  - Neue Spalte `events.redaktion_felder text[] NOT NULL DEFAULT '{}'`. Jedes im Dashboard geänderte Feld kommt hinein.
  - `_anreicherungs_update_bauen` (`database/client.py:75–135`) prüft sie an **allen vier Stellen**: beim `ort_id`-Nachtrag vor der Schleife (`:100–101`, Cursor-Prüfung 4), in der Schleife über `_ANREICHERBARE_FELDER` (inklusive `bild_url` und `kategorie`), im Uhrzeit-Block (`:120–124`) und beim Quellenwechsel (`:127–133`, Felder aus `_QUELL_FELDER + _VORRANG_FELDER`). Ein Feld in `redaktion_felder` wird nie ins `update` geschrieben. Das gilt auch für `quelle_name`/`quelle_url`, falls die Redaktion sie gesetzt hat, und für `ort_id`.
  - **`abgesagt`:** `false` gilt in der Schleife heute als leer und würde von der Quelle wieder auf `true` gesetzt. Steht `abgesagt` in `redaktion_felder`, bleibt es so, wie die Redaktion es gesetzt hat.
  - `titel`, `datum`, `ort`, `datum_bis`, `abgelehnt` und `nicht_empfehlen` schreibt weder der Builder noch ein anderer Schritt im Lauf. Für sie reicht Teil B.
  - **Weitere Schreiber im selben Lauf** (Cursor-Prüfung 2, Befund 2, plus eigener Fund; Cursor-Prüfungen 3 und 4): Sie lassen Felder aus `redaktion_felder` ebenfalls stehen. Je nach Schreiber gibt es zwei Arten (Cursor-Prüfung 4, Befund 1):
    - **Filter in der Abfrage** (`not.redaktion_felder.cs.{feld}`): dort, wo das geschützte Feld der einzige Schreibzweck ist. Bei den Beschreibungs-Skripten verhindert genau dieser Filter, dass die Events ohne `beschreibung_gesucht_am` in jedem Lauf neu gesucht werden.
      - `pipeline/unterkategorien.py` **`nachtragen()`** (`:115–166`): sucht `unterkategorie IS NULL` und würde eine von der Redaktion geleerte Unterkategorie wieder füllen → `unterkategorie`.
      - `pipeline/beschreibung_quellen.py` **`veranstalter_nachziehen()`** (`:669–741`): ersetzt `beschreibung`, wenn der alte Text kürzer als 200 Zeichen ist oder der neue länger (`ersetzen_erlaubt`, `:584–587`) → `beschreibung`.
      - `pipeline/beschreibung_quellen.py` **`beschreibungen_nachziehen()`** (`:471–511`): ersetzt bei Rausgegangen-Events ohne `beschreibung_gesucht_am` die Beschreibung ohne Längenprüfung → `beschreibung`. (Eigener Fund.)
    - **Zeile laden, nur das geschützte Feld aus dem `update` lassen:** dort, wo der Schreiber noch anderes tut oder die Zeile für eine Rechnung braucht. Hier würde ein Filter zu viel ausschließen.
      - `pipeline/categorizer.py` **`kategorisieren()`** (`:180–254`): schreibt `beschreibung` und `ist_wiederkehrend` und die `kategorie` nur, wenn die KI eine andere vorschlägt (`:241–248`). Mit einem Filter bekäme ein Event mit geschützter Kategorie nie eine Beschreibung und bliebe auf `neu`. Darum fällt nur `kategorie` aus `aktualisierung`, wenn sie in `redaktion_felder` steht.
      - `pipeline/unterkategorien.py` **`vereinheitlichen()`** (`:208–244`): bildet die Mehrheit aus allen Zeilen einer Gruppe (`:190–204`). Die geschützte Zeile zählt deshalb weiter mit. Nur ihre Änderung fällt aus `aenderungen` heraus.
    - Brauchen nichts (Cursor-Prüfungen 2 und 3):
      - `adressen_ergaenzen` und `stadtteil_mapper` füllen nur leere Felder im Speicher, danach schützt `client.py`;
      - `reihen_zuordnen` setzt nur ein leeres `reihe_id`;
      - `ort_zuordnung.zuordnen_alle` setzt `ort_id` nur an neuen Events im Speicher, und `bestand_pruefen` ändert nichts;
      - Captions und Publisher schreiben nur `instagram_caption` und `status`;
      - `konten_aufraeumen` schreibt keine Events;
      - der `ort_id`-Nachtrag läuft nicht in `main.py`.
    - **Stufe 3:** Die Annahme von Ortsnamen- und `ort_id`-Vorschlägen schreibt `ort` bzw. `ort_id` nur, wenn das Feld nicht in `redaktion_felder` steht. `abgleich_ort` bleibt dabei unverändert.
  - Button „Redaktionsänderungen zurücksetzen“: leert `redaktion_felder` und `abgleich_*` für ein Event.
- **Schutz vor Überschreiben (E7), Teil B: Wiederfinden** (Cursor-Befund 2):
  - Neue Spalten `abgleich_titel`, `abgleich_datum`, `abgleich_uhrzeit`, `abgleich_ort`. Ändert die Redaktion **zum ersten Mal** eines der vier Felder `titel`, `datum`, `uhrzeit` oder `ort`, schreibt die Route alle vier mit den **bisherigen** Werten. Spätere Änderungen lassen sie stehen; das sind die Werte der Quelle.
  - **Neuer Schritt 0** in `database/client.py` vor Schritt 1: Suche nach einer Zeile mit `abgleich_titel = titel`, `abgleich_datum = datum`, `abgleich_ort = ort` des eingehenden Events und passender Uhrzeit gegen `abgleich_uhrzeit` (dieselbe Regel wie Schritt 1, `:306–312`). Ein Treffer gilt als `bestehendes`, die Schritte 1–3 entfallen. Der Treffer geht danach durch die Anreicherung mit Feldschutz (Teil A).
    - **Ohne eingehende Uhrzeit** (Cursor-Prüfung 2, Befund 3) passt jede Uhrzeit. Schritt 0 trifft dann nur, wenn **genau eine** Zeile übrig bleibt. Bei mehreren bearbeiteten Vorstellungen desselben Titels am selben Tag laufen stattdessen die Schritte 1–3 wie bisher. Mit Uhrzeit ist der Treffer eindeutig, weil verschiedene Vorstellungen verschiedene `abgleich_uhrzeit` haben.
    - Ablauf im Lauf: Ein Treffer läuft in den bestehenden `else`-Zweig (Anreicherung, `duplikate += 1`). `neu_pro_quelle` zählt weiter nur Inserts. `tagesbestand` bleibt allein bei Schritt 3.
  - **Warum ein eigener Schritt statt Änderungen in Schritt 1–3:** Damit sind alle vier Fälle gedeckt: geänderter Titel, Ort, Uhrzeit, Datum, auch zusammen. Schritt 2 (Slug und Uhrzeit) und Schritt 3 (Ähnlichkeit am selben Datum, gleiche Quelle mit anderer Uhrzeit ist ein eigener Termin) bleiben unverändert und können eine umgestellte Uhrzeit oder ein umgestelltes Datum nicht wiederfinden.
  - Index auf `(abgleich_datum, abgleich_titel)` mit `WHERE abgleich_datum IS NOT NULL`.
  - **Eindeutigkeit:** Der Unique-Schlüssel `(titel, datum, ort, uhrzeit)` (`database/schema.sql:37–39`) kann beim Bearbeiten greifen, wenn es die Zielkombination schon gibt. Die Route meldet das als „Gibt es schon: <Link>, als Dublette zusammenlegen?“.
- **Dubletten** (Cursor-Befunde 4 und 15):
  - `pipeline/dubletten_sql.py` schreibt Vorschläge (Art `dublette`) statt SQL. Dazu kommt in der Event-Detailseite **„Als Dublette von … markieren“** von Hand, mit Suche nach dem Ziel-Event.
  - Die Annahme ruft `admin_dublette_zusammenlegen(behalten uuid, dublette uuid)` (`SECURITY DEFINER`, 3.3). Die Funktion macht für das Paar dasselbe wie `dubletten_sql.py:161–186` heute:
    - behaltene Zeile: `COALESCE` auf `bild_url`, `beschreibung`, `preis`, `adresse`; Uhrzeit nur, wenn die behaltene leer ist oder ein Aggregator gegen einen Veranstalter steht; `abgesagt = true`, wenn die Dublette abgesagt ist. Felder aus `redaktion_felder` der behaltenen Zeile bleiben unberührt;
    - Dublette: `abgelehnt = true`;
    - `event_seo_entscheidungen`: `INSERT … aktion = 'weiterleiten'`, Ziel `/event/<kategorie>/<slug>` der behaltenen Zeile, `ON CONFLICT (event_id) DO UPDATE`.
  - **Neu gegenüber heute, Merkliste:** Heute bleiben die Zeilen an der Dublette hängen und verschwinden auf der Website, weil `merkliste-events.ts` `abgelehnt = false` filtert. Die Funktion zieht sie per `UPDATE merkliste SET event_id = behalten WHERE event_id = dublette` um. Vorher löscht sie die Zeilen der Dublette bei Konten, die das behaltene Event schon gemerkt haben (Primärschlüssel `(nutzer_id, event_id)`). `UPDATE` läuft nicht durch `merkliste_vor_insert`, Mindestalter und Sensibel-Prüfung greifen also nicht neu. Das ist hingenommen, weil es dasselbe Event ist.
  - Nicht Teil der Funktion: Jazz-Schmiede-Uhrzeiten und die Titelbereinigung ohne Paar (Abschnitt 3 der heutigen SQL). Sie werden eigene Vorschlagsarten (`titel_bereinigen`).
- **Gebiet:** `pipeline/gebiet.py` schreibt Vorschläge (Art `gebiet`) statt SQL. Die Annahme ruft `admin_gebiet_entfernen(event uuid)` (`SECURITY DEFINER`). Ohne Merklisten-Zeile wird gelöscht wie heute (`DELETE`, `gebiet.py:194`). Mit Merklisten-Zeile wird stattdessen `abgelehnt = true` gesetzt, damit keine Merkliste still per `ON DELETE CASCADE` schrumpft.
- **Cache** (Cursor-Befund 7):
  - `cacheTag("events")` kommt in alle drei `"use cache"`-Funktionen, die Events halten: `eventPoolLaden`, `vergangeneWochenendEvents`, `eventLaden` (`web/lib/daten.ts`).
  - Die Admin-Route ruft nach jeder Änderung `revalidateTag("events", { expire: 0 })` auf, wie `web/app/ort-foto/[slug]/route.ts:35`. Ohne `expire: 0` bliebe `stale: 300`.
  - Ändert sich `bild_url`, wird zusätzlich der Bild-Cache dieses Events geleert (`/bild/event/<id>`, eigener Tag je Event).

### 4.5 Stufe 1e: Empfehlungen

- **Tagesvorschau** `/admin/empfehlungen?tag=2026-11-28`: zeigt genau, was die Startseite unter `/?datum=2026-11-28` zeigt (Tipp, Picks, „Diese Woche beliebt“, Wochenend-Tipps).
  - **Gleiche Rechnung, eine Funktion** (Cursor-Befund 6): Die Rechnung für Tipp, Picks, Beliebt und Wochenende aus `web/app/page.tsx:62–121` wandert in eine Funktion `startseitenAuswahl(pool, vergangene, datumParam)` in `web/lib/startseite.ts`. Startseite und Vorschau rufen für diese vier Blöcke **nur** diese Funktion.
    - **Sie rechnet nur, sie lädt nicht** (Cursor-Prüfung 2, Befund 5). Kein `"use cache"`. Das Laden (`eventPoolLaden`, `vergangeneWochenendEvents`) bleibt in der Seite bzw. in der Admin-Route, das Caching der Startseite ändert sich nicht.
    - Kennzahlen, Abend, Frisch, Stadtteile, Themen und Tagesleiste bleiben in `page.tsx`.
    - Sie bekommt bzw. rechnet:
    - den Pool aus `eventPoolLaden` (gebündelt, `abgelehnt` schon weg); `abgesagt` entfernt sie selbst;
    - `heute` und `jetzt` aus dem Pool für `stufenKontext`, `highlightGilt` und `topGilt`. Der gewählte Tag geht nur als `fokusTag` ein (`null`, sobald von ≠ bis);
    - `startPlaetze(filtern(…, { von, bis, mitLanglaeufern: true }), stufen, fokusTag)`;
    - `beliebtAuswahl` mit Tag und Woche ohne Langläufer und `schonGezeigt` aus Tipp und Picks;
    - `wochenendProgramm(pool, vergangene)`. `vergangene` lädt der Aufrufer vorher mit `vergangeneWochenendEvents(pool.heute)`. Die Box hängt an `pool.heute`, nicht am gewählten Tag. Das zeigt die Vorschau so an.
  - Ein Test sichert für denselben Pool, dass die vier Blöcke (Tipp, Picks, Beliebt, Wochenende) gleich der bisherigen Rechnung in `page.tsx` sind.
  - **„Warum“:** Einen fertigen Grund-Text gibt es nicht. Neu ist `stufeErklaeren(e, k)` in `ableitungen.ts`. Sie liefert dieselben Schritte wie `stufeRechnen` als Liste: Stamm oder Sprachhinweis (`istStamm`), Grundstufe (`grundstufe`, `ZUGPFERD_ORTE`), Serie (`serienErkennen`), Langläufer (`istLanglaeufer`), Flagge. Dazu kommen „nicht empfehlen“ und der Fokustag. Ein Test sichert, dass die erklärte Stufe gleich `breite()` ist.
- Darunter alle weiteren Kandidaten des Tages, sortiert nach `nachEmpfehlung`, je mit den Buttons **Tipp des Tages**, **Highlight der Woche**, **Top-Event des Monats**, **nicht empfehlen**. Nach dem Klick rechnet die Vorschau neu.
- **Kalender** der nächsten 30 Tage: je Tag der Tipp (Redaktion oder automatisch), geltende Highlight- und Top-Flagge, Hinweis „kein Bild“.
- Die Flaggen-Zeitpunkte setzt die Route wie heute `flagge_setzen` im Dashboard (`highlight_gesetzt_am`, `top_gesetzt_am`).

### 4.6 Stufe 2: Magazin

- **Redaktionsplan:** Kalender mit festen Terminen (Wochenvorschau Fr → Ausgabe Mo–So, Monats-Tipps am 28.) und allen Beiträgen nach `gueltig_von`/`veroeffentlicht_am` mit Status. Fehlender Entwurf für einen festen Termin = rot.
- **Entwürfe:**
  - Liste nach Status.
  - Vorschau im Admin-Bereich mit denselben Bausteinen wie `/magazin/vorschau/[id]`. Der Vorschau-Schlüssel ist dort nicht nötig, weil die Admin-Sitzung reicht.
    - Die öffentliche Vorschau-Seite lädt über `vorschauLaden` (Service-Schlüssel, `web/lib/magazin-daten.ts:204–221`) und prüft den Hash. Das bleibt unverändert (Cursor-Prüfung 2, Befund 4).
    - Die Admin-Vorschau holt den Beitrag über `admin_magazin_beitrag`. Daraus baut `beitragAus` (`magazin-daten.ts` ab `:25`; ohne Slug liefert es `null`, daher der Slug schon beim Anlegen) einen `MagazinBeitrag`. Das Artikel-Markup aus `web/app/magazin/vorschau/[id]/page.tsx` ab `:58` wandert dafür in eine gemeinsame Komponente `MagazinArtikel` (Kopf mit Autor, Hero über `heroFuer`, Kurzfassung, `parsen` + `MagazinText`, Entstehungshinweis). Vorschau, Admin-Vorschau und Beitragsseite nutzen sie. **Lesezeit, Inhaltsverzeichnis, FAQ, Quellen, Korrekturhinweis und „Weiterlesen“ bleiben außerhalb der Komponente** in der Beitragsseite (`web/app/magazin/[slug]/page.tsx:86–175`). Die Bildunterschrift bekommt einen Schalter für den Ersatzbild-Hinweis, den heute nur die Vorschau zeigt. So ändert sich die öffentliche Seite nicht (Cursor-Prüfung 3, Befund 3).
    - Daneben ruft die Admin-Vorschau `eventsFuerIds`, `orteFuerSlugs` und `autorenLaden` auf, wie die öffentliche Seite.
  - Ergebnis der automatischen Prüfung (`pruefung` jsonb) als Liste (a)–(i) mit grün/rot.
  - KI-Angaben aus `ki_entwurf` (Modell, Kosten).
- **Bearbeiten:** `titel`, `seo_titel`, `teaser`, `inhalt_md` (Editor mit Live-Vorschau), `kurzfassung`, `faq`, `hero_*`, `gueltig_*`, `korrektur_hinweis`. Nach dem Speichern läuft die Prüfung erneut, über einen Job (`magazin.yml`, Schritt `pruefen`) oder über eine Route, falls die Prüfung in TypeScript vorliegt (bei der Umsetzung klären).
- **Events tauschen** (Wochenvorschau, Monats-Tipps): Ein Event aus der Auswahl entfernen oder durch einen Kandidaten ersetzen. Das ändert `event_ids` und den betreffenden Block in `inhalt_md`.
- **Rechte (Cursor-Befund 3):** Der Admin-Token kann heute keine Entwürfe lesen. Es fehlen die Spalten-GRANTs und eine Policy. `UPDATE` ist nicht vergeben, und jedes Update einer veröffentlichten Zeile als `authenticated` wirft `magazin_veroeffentlicht_gesperrt`. Deshalb läuft **der ganze Magazin-Bereich über `SECURITY DEFINER`-Funktionen** (S3), nicht über Tabellenrechte:
  - lesen: `admin_magazin_liste(status)`, `admin_magazin_beitrag(id)` (alle Spalten), `admin_magazin_kosten(monat)`;
  - anlegen: `admin_magazin_anlegen(rubrik, autor_slug, titel)` legt einen leeren Entwurf mit `status = 'entwurf'` an und gibt die `id` zurück (Cursor-Prüfung 2, Befund 4: `authenticated` darf nicht einfügen). **`slug` ist `NOT NULL UNIQUE`** (`magazin_2026-11-19.sql:51`). Die Funktion erzeugt ihn deshalb aus dem Titel nach dem Muster `^[a-z0-9]+(-[a-z0-9]+)*$`, Umlaute umgeschrieben, ohne die reservierten Wörter. Bei Kollision hängt sie `-2`, `-3` … an (Cursor-Prüfung 4, Befund 3);
  - schreiben: `admin_magazin_speichern(id, felder jsonb)`.
    - Nur die Felder aus „Bearbeiten“ und **`event_ids`** (für „Events tauschen“) sind erlaubt.
    - Nie `status`, `freigegeben_*`, `vorschau_hash`, `pruefung` oder `ki_entwurf`.
    - **Nur für `entwurf` und `in_pruefung`.** Bei `veroeffentlicht` oder `zurueckgezogen` wirft die Funktion einen Fehler. Sonst würde sie als `postgres` am Korrekturhinweis vorbei schreiben.
    - Danach geht `pruefung` zurück auf „neu prüfen“;
  - `admin_magazin_veroeffentlichen(id)`, `admin_magazin_zurueckziehen(id)`, `admin_magazin_korrektur(id, hinweis, inhalt_md)`. Die letzte ist der einzige Weg, einen veröffentlichten Beitrag zu ändern: Sie setzt `korrektur_hinweis` und `aktualisiert_am` immer mit;
  - Autoren: `admin_magazin_autor_speichern(slug, felder jsonb)`.
  - **Wirkung auf den Trigger:** In einer `SECURITY DEFINER`-Funktion mit Eigentümer `postgres` ist `current_user = postgres`, auch im Trigger `magazin_status_pruefen` (`magazin_2026-11-19.sql:164–206`). `maschine` ist dann falsch, die Sperre „nur Redaktion“ öffnet sich. **Das ist gewollt:** Der Admin ist die Redaktion (D3). Die **Pflichtprüfungen des Triggers bleiben**: nur aus `in_pruefung`, Pflichtfelder, `pruefung->>'ergebnis' = 'gruen'`. Die Funktion `admin_magazin_speichern` kann den Status nicht ändern; nur `…_veroeffentlichen` und `…_zurueckziehen` tun das.
- **Veröffentlichen:** Button → `admin_magazin_veroeffentlichen(id)`. Setzt `status = 'veroeffentlicht'`, `freigegeben_von` (Mailadresse aus `auth.jwt()`), `freigegeben_am`, `veroeffentlicht_am` (falls leer: jetzt) und leert `vorschau_hash`. Danach IndexNow über den bestehenden Job (`melden`, stündlich).
- **Cache** (Cursor-Prüfung 2, Befund 4): Die Magazin-Loader haben heute nur `cacheLife(MAGAZIN_CACHE)` (`magazin-daten.ts:62–179`). `magazinHeute`, `beitraegeLaden`, `beitragLaden`, `autorenLaden`, `eventsFuerIds` und `orteFuerSlugs` bekommen `cacheTag("magazin")`. Nach Veröffentlichen, Zurückziehen, Korrektur und Autor-Speichern ruft die Route `revalidateTag("magazin", { expire: 0 })` auf. Bei Entwürfen ist das nicht nötig, sie sind öffentlich unsichtbar.
- **Zurückziehen, Korrektur, neuer Beitrag:** Ein neuer Beitrag (Rubriken `saison`, `stadtleben`, `nachtleben`, `genuss`, `familie`, ohne Job) entsteht über `admin_magazin_anlegen` als leerer Entwurf.
- **Job starten:** Wochenvorschau oder Monats-Tipps neu erzeugen (`magazin.yml`, `dry_run` wählbar).
- **Autoren:** Liste, bearbeiten. Profilbilder bleiben Dateien im Repo, wie heute.
- **KI-Kosten:** Summe je Monat aus `magazin_ki_kosten`.

### 4.7 Stufe 3: Orte und Guides

- **Rechte (Cursor-Befund 12):** `orte_lesen` zeigt nur `aktiv = true` (`database/schema_orte.sql:65–71`). `orte_admin_alles` und `ort_weiterleitungen_admin` prüfen `auth.role() = 'service_role'`, nicht `ist_admin()` (`orte_spielstaetten_2026-11-19.sql:85–87`). S4 ergänzt deshalb:
  - eine `SELECT`- und eine `UPDATE`-Policy mit `ist_admin()` auf `orte`, für die Liste und die Stammdaten;
  - Zusammenlegen, Schließen, Löschen und Text freigeben als `SECURITY DEFINER`-Funktionen. Dabei bleibt der Trigger `orte_schutz` wirksam, die Funktion legt die Weiterleitung zuerst an.
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
- **Wer schickt die Mail? (E9, entschieden):** Die Website legt die Anmeldung an, und ein **Python-Job alle 15 Minuten** (GitHub Actions) schickt die Bestätigungsmails über `smtplib`. Dabei sind bis zu 15 Minuten Wartezeit hingenommen. Keine neue Bibliothek in `web/`.
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

Alle `SECURITY DEFINER`-Funktionen folgen demselben Muster (3.3): Eigentümer `postgres`, erste Prüfung `ist_admin()`, `SET search_path = public, pg_temp`, `REVOKE EXECUTE … FROM PUBLIC, anon`, `GRANT EXECUTE … TO authenticated`, Protokolleintrag in `admin_protokoll` in derselben Transaktion.

| Nr. | Stufe | Datei (Vorschlag) | Inhalt |
|---|---|---|---|
| S1 | 1a | `database/admin_grundlagen_<datum>.sql` | **`admin_protokoll`** (id, zeitpunkt, admin_id, aktion, tabelle, ziel_id, vorher jsonb, nachher jsonb). RLS: lesen und einfügen nur `ist_admin()`, kein Update/Delete. **`admin_vorschlaege`** (id, art, ziel_tabelle, ziel_id, `schluessel text NOT NULL` (je Art festgelegt, z. B. bei `dublette` „behalten-id:dubletten-id“, bei `gebiet` die Event-ID), vorschlag jsonb, begruendung, status `offen/angenommen/abgelehnt`, quelle_lauf, erstellt_am, entschieden_von/_am; eindeutig `(art, schluessel)` gegen Doppelvorschläge, die Pipeline schreibt mit `ON CONFLICT DO NOTHING`, so bleiben abgelehnte liegen). Die Pipeline schreibt als `service_role`, der Admin liest per Policy `ist_admin()`. Entschieden wird nur über die Funktionen aus S2 (ab 1d). |
| S2 | 1d | `database/admin_events_<datum>.sql` | `events.redaktion_felder text[] NOT NULL DEFAULT '{}'`, `events.abgleich_titel text`, `abgleich_datum date`, `abgleich_uhrzeit time`, `abgleich_ort text` mit Teilindex. Die bestehende Policy „Admins ändern Events“ (`auth_rollen.sql:152–157`, UPDATE mit `ist_admin()`) deckt die neuen Spalten. DEFINER-Funktionen: `admin_dublette_zusammenlegen(behalten, dublette)` (mit Merkliste und `event_seo_entscheidungen`, 4.4), `admin_gebiet_entfernen(event)`, `admin_vorschlag_annehmen(id)` und `admin_vorschlag_ablehnen(id)`. Die beiden letzten verteilen je Art an die passende Funktion. |
| S3 | 2 | `database/admin_magazin_<datum>.sql` | Nur DEFINER-Funktionen, keine neuen Tabellenrechte für `authenticated`: `admin_magazin_liste`, `_beitrag`, `_kosten`, `_anlegen`, `_speichern` (Feld-Whitelist inkl. `event_ids`, kein Status, nur `entwurf`/`in_pruefung`), `_veroeffentlichen`, `_zurueckziehen`, `_korrektur`, `_autor_speichern` (4.6). Der Trigger `magazin_status_pruefen` bleibt unverändert. |
| S4 | 3 | `database/admin_orte_<datum>.sql` | Policies `orte_admin_lesen` (SELECT, `ist_admin()`) und `orte_admin_aendern` (UPDATE, `ist_admin()`) auf `orte`. DEFINER-Funktionen: `admin_ort_zusammenlegen(von, nach)`, `admin_ort_schliessen(id, weiterleitung)`, `admin_ort_text_freigeben(id)`, `admin_ort_zuordnung_loesen(event, ort)`. `ort_weiterleitungen` wird nur über diese Funktionen geschrieben. |
| S5 | 4 | `database/newsletter_doi_<datum>.sql` | Spalten für Token-Zeitpunkt, Versandstatus der Bestätigung. Aufräumregel. |
| S6 | 5 | `database/admin_rest_<datum>.sql` | `admin_konten_kennzahlen()`, `quellen_einstellungen`. |
| S7 | später | eigener Instagram-Plan | `instagram_posts`. |

Python-Änderungen:
- **Stufe 1d:**
  - `database/client.py` (E7: Feldschutz an drei Stellen, Schritt 0);
  - **`pipeline/unterkategorien.py`** (`nachtragen`: Filter in der Abfrage; `vereinheitlichen`: Zeile mitzählen, Änderung auslassen), **`pipeline/beschreibung_quellen.py`** (`veranstalter_nachziehen`, `beschreibungen_nachziehen`: Filter in der Abfrage) und **`pipeline/categorizer.py`** (`kategorisieren`: nur `kategorie` aus dem Update lassen), 4.4 Teil A, Cursor-Prüfungen 3 und 4;
  - `pipeline/dubletten_sql.py` und `pipeline/gebiet.py` (Vorschläge statt SQL).
- Weitere: `main.py` (Warn-Mail E8, später Quellen an/aus), in Stufe 3 `pipeline/ortsnamen.py`, `pipeline/ort_zuordnung.py`, `pipeline/adressen_ergaenzen.py`.

---

## 6. Tests

- **Vitest** (`web/tests/admin-*.test.ts`):
  - Proxy:
    - `/admin` ohne `X-DDD-Bereich: admin` gibt 404, auch mit Host `localhost:3847` und `x-forwarded-proto`.
    - `/` mit Kopf gibt 308 und `Location: /admin`, ohne localhost.
    - `ADMIN_LOKAL=1` wirkt nur ohne `x-forwarded-*`.
    - Die bestehenden Proxy-Tests bleiben grün.
  - Sitzung: Die Konto-Cookies sind nach dem Umbau auf Parameter bitgleich. `ddd_admin` hat `Path=/`, `SameSite=Strict` und 12 h.
  - Origin: Die Admin-Prüfung erlaubt nur `ADMIN_URL`, die Konto-Prüfung unverändert nur `SITE_URL`.
  - Rollenprüfung: Route ohne Sitzung 401, ohne Admin-Rolle 403, ohne `aal2` 403.
  - Warnregeln W1–W6 aus der gemeinsamen Fixture.
  - `startseitenAuswahl` liefert für denselben Pool dasselbe wie die bisherige Rechnung in `page.tsx`.
  - `stufeErklaeren` ergibt dieselbe Stufe wie `breite()`.
  - Whitelist beim Bearbeiten: Unbekannte Felder werden abgewiesen, `redaktion_felder` und `abgleich_*` werden richtig gepflegt (nur beim ersten Ändern).
- **Python** (`tests/`):
  - Feldschutz an allen drei Stellen: Schleife inklusive `bild_url`, `kategorie` und `abgesagt = false`; Uhrzeit-Block; Quellenwechsel.
  - Schritt 0 findet das Event wieder bei geändertem Titel, Ort, Uhrzeit, Datum und bei Datum plus Uhrzeit zusammen. Ohne `abgleich_*` laufen die Schritte 1–3 unverändert. Ohne eingehende Uhrzeit und mit zwei bearbeiteten Vorstellungen trifft Schritt 0 nicht, dann greifen die Schritte 1–3.
  - `nachtragen()`, `veranstalter_nachziehen()` und `beschreibungen_nachziehen()` wählen Events mit dem jeweiligen Feld in `redaktion_felder` gar nicht erst aus.
  - `kategorisieren()` schreibt bei geschützter Kategorie trotzdem `beschreibung` und `ist_wiederkehrend`, aber nicht `kategorie`.
  - `vereinheitlichen()` zählt die geschützte Zeile bei der Mehrheit mit, ändert sie aber nicht.
  - `ort_id`-Nachtrag in `_anreicherungs_update_bauen` (`:100–101`) beachtet `redaktion_felder`.
  - Warnregeln gleich wie in TypeScript (gemeinsame Fixture).
  - Vorschläge statt SQL in Dubletten und Gebiet; die Feldliste der Dubletten wie in `dubletten_sql.py`.
- **SQL:** Kontrollabfragen am Ende jeder Datei, wie bisher. Dazu je Funktion: Aufruf als Nicht-Admin wirft, Aufruf als `anon` ist nicht erlaubt.
  - Dublette: Merkliste wird umgezogen, und bei doppelt Gemerkten bleibt genau eine Zeile.
  - Gebiet: Mit Merkliste wird abgelehnt statt gelöscht.
  - Magazin:
    - `_speichern` kann den Status nicht ändern und wirft bei `veroeffentlicht`.
    - `_anlegen` legt einen Entwurf an.
    - `_veroeffentlichen` scheitert bei `pruefung` ≠ grün.
    - `_korrektur` setzt `korrektur_hinweis` und `aktualisiert_am`.
- **Von Hand je Stufe:** Login mit Admin- und Nicht-Admin-Konto, eine Änderung je Bereich, sichtbare Wirkung auf der Website, Protokolleintrag, Rückgängig.

---

## 7. Umsetzungsschritte und Freigaben

| Schritt | Inhalt | SQL vorher | Freigabe |
|---|---|---|---|
| 0 | Dieser Plan, Cursor-Prüfung, Freigabe | – | Plan |
| 1a-0 | **Vor jedem Admin-Code:** nginx diesdas.events bekommt `proxy_set_header X-DDD-Bereich web;` (Auftraggeber, Anleitung). Kein Deploy | – | Auftraggeber; danach prüft Claude mit `curl`, dass die Website unverändert läuft |
| 1a | Grundgerüst, Login mit Zwei-Faktor, Protokoll, Proxy-Regeln. Danach nginx admin.diesdas.events umstellen (Kopf `admin`, Pfadliste, `/` → 308, `/alt`) | S1 | Deploy, dann nginx admin durch Auftraggeber, dann Prüfung mit `curl` gegen beide Hosts, auch mit selbst gesetztem Kopf |
| 1b | Cockpit | – | Deploy |
| 1c | Scraper + Warnregeln + Warn-Mail (E8) | – | Deploy |
| 1d | Events, Schutz vor Überschreiben (Feldschutz, Schritt 0), Dubletten/Gebiet als Vorschläge, Cache-Tags | S2 | Deploy, erster Scraper-Lauf danach im Report prüfen |
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
- **Rechte:** Ein Fehler in der Rollenprüfung würde die Datenbank öffnen. Gegenmittel: RLS bleibt die zweite Sicherung, weil mit dem Admin-Token geschrieben wird und nicht mit dem Service-Key. Jede DEFINER-Funktion prüft `ist_admin()` selbst. Tests für 401/403 und SQL-Tests als Nicht-Admin.
- **DEFINER öffnet Trigger-Sperren:** In den Funktionen ist `current_user = postgres`. Sperren, die an `current_user` hängen, gelten dort nicht (Magazin). Gegenmittel: Feld-Whitelist in jeder Funktion, keine Funktion mit freiem SQL oder freien Spaltennamen.
- **Host-Trennung hängt an nginx** (Cursor-Prüfung 2, Befund 1):
  - Setzt admin.diesdas.events den Kopf nicht, ist der Admin-Bereich nicht erreichbar.
  - **Überschreibt diesdas.events den Kopf nicht**, kann jeder, der `X-DDD-Bereich: admin` selbst mitschickt, die Admin-Routen auf der öffentlichen Website aufrufen. Dort steht dann nur noch die Anmeldung mit Zwei-Faktor davor.
  - Gegenmittel: Schritt 1a-0 setzt den Kopf auf diesdas.events **vor** dem ersten Admin-Code. Nach jedem Deploy und jeder nginx-Änderung prüft Claude mit `curl -H "X-DDD-Bereich: admin" https://diesdas.events/admin`, dass 404 kommt. Das Cockpit macht diese Prüfung zusätzlich bei jedem Aufruf und zeigt rot, wenn sie fehlschlägt.
- **Pipeline-Änderung (E7):** Der Abgleich ist heikel (Duplikate, Quellenwechsel). Gegenmittel: Python-Tests mit echten Fällen, erster Lauf nach dem Deploy wird im Scraper-Report geprüft.
- **Zwei Dashboards gleichzeitig:** Während des Übergangs können beide dasselbe Event ändern. Hingenommen, weil es nur einen Admin gibt.
- **GitHub-Token** auf dem Server: Fine-grained, nur dieses Repo, `Actions: read and write`, `Variables: read`, sonst nichts. Wer ihn hat, kann Workflows starten, aber keinen Code ändern. Er läuft nach 1 Jahr ab; das Cockpit zeigt den Ablauf an.

---

## 9. Entscheidungen zu den offenen Fragen (alle wie vorgeschlagen bestätigt, 23.11.2026)

| Nr. | Frage | Entscheidung |
|---|---|---|
| E1 | Neuer Admin-Bereich in Next.js statt Streamlit? | ja (3.1) |
| E2 | Zwei-Faktor (TOTP) für den Admin-Login schon in Stufe 1? | ja |
| E3 | GitHub-Token für Jobs und Laufstatus? | ja, Fine-grained, nur dieses Repo: `Actions: read and write` (Starten braucht Schreibrecht), `Variables: read` |
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

## Anhang A: Cursor-Prüf-Prompt (dritte Fassung)

```
Prüfe die **dritte Fassung** des Plans `docs/plan-admin-dashboard-2026-11-23.md` (Admin-Bereich neu unter
admin.diesdas.events) erneut gegen den tatsächlichen Code im Repo. Ändere keinen Code und keinen Plan – nur Befunde.

Deine Prüfung 2 hatte 6 Befunde (1 kritisch, 3 mittel, 2 gering). Alle sind eingearbeitet; Anhang C nennt die
Stellen. Dazu ein eigener Fund: `beschreibungen_nachziehen()` (pipeline/beschreibung_quellen.py:471–511) ersetzt
bei Rausgegangen-Events die Beschreibung ebenfalls. Die wichtigsten Änderungen:
- 3.2 / 7 / 8: Neuer Schritt 1a-0 – nginx diesdas.events setzt `X-DDD-Bereich web` VOR dem ersten Admin-Code;
  Prüfung per curl mit selbst gesetztem Kopf, zusätzlich als Ampel im Cockpit. Risiko-Text präzisiert.
  Schriften: `/_next/static/media`, `/fonts` aus der nginx-Liste gestrichen.
- 4.4 Teil A: weitere Schreiber beachten `redaktion_felder`: `unterkategorien.vereinheitlichen()`,
  `beschreibung_quellen.veranstalter_nachziehen()` und `beschreibungen_nachziehen()`. Stufe-3-Vorschläge
  (Ortsnamen, ort_id) schreiben nur ohne Eintrag in `redaktion_felder` und lassen `abgleich_ort` stehen.
- 4.4 Teil B: Schritt 0 ohne eingehende Uhrzeit nur bei genau einer Zeile.
- 4.5: `startseitenAuswahl` rechnet nur (kein Laden, kein "use cache"); Test vergleicht die vier Blöcke.
- 4.6 / S3: `admin_magazin_anlegen`; `event_ids` in der Whitelist; `_speichern` nur für entwurf/in_pruefung;
  `_korrektur` als einziger Weg für Veröffentlichte; gemeinsame Komponente `MagazinArtikel`;
  `cacheTag("magazin")` an den Loadern, `revalidateTag("magazin", { expire: 0 })`.
- 5: Tabellenkopf repariert, `schluessel` in admin_vorschlaege, eindeutig `(art, schluessel)`.

Prüfe bitte:
1. Sind alle 6 Befunde aus Prüfung 2 gelöst (Anhang C)?
2. Gibt es außer den jetzt genannten noch Schreiber auf `events`, die Redaktionsänderungen überschreiben können
   (main.py-Ablauf vollständig, auch Aufräum- und Nachtragsschritte, pipeline/ort_zuordnung Nachtrag im Lauf)?
3. 4.6: Lässt sich das Artikel-Markup aus web/app/magazin/vorschau/[id]/page.tsx als gemeinsame Komponente
   herauslösen, ohne die öffentliche Magazin-Beitragsseite oder die Vorschau zu verändern? Wird
   `cacheTag("magazin")` an allen sechs Loadern die öffentliche Seite korrekt erneuern (Sitemap, Feed, Autorenseiten)?
4. Abschnitt 5 / S1: Reicht `(art, schluessel)` mit `ON CONFLICT DO NOTHING`, damit abgelehnte Vorschläge nicht
   wiederkommen, aber ein geänderter Sachverhalt (z. B. anderes Ziel-Event) neu vorgeschlagen wird?
5. Widersprüche zwischen den Abschnitten oder zu Anhang B/C nach dieser Fassung?

Ausgabe je Befund: Schweregrad (kritisch / mittel / gering) · Fundstelle (Plan-Abschnitt + Datei:Zeile) · Befund ·
Vorschlag. Nach Schweregrad sortiert. Am Ende: Gesamturteil (freigabefähig ja/nein). Die Entscheidungen E1–E9 und
Q5–Q8 hat der Auftraggeber getroffen; sie sind nicht Gegenstand der Prüfung.
```

## Anhang B: Cursor-Prüfung 1 vom 23.11.2026 – Einarbeitung

Alle 15 Befunde sind am Code nachgeprüft und stimmen (`web/proxy.ts`, `database/client.py`, `database/magazin_2026-11-19.sql`, `database/auth_rollen.sql`, `database/konten_2026-11-16.sql`, `database/schema_orte.sql`, `database/orte_spielstaetten_2026-11-19.sql`, `web/lib/konto/pruefungen.ts`).

| Nr. | Schwere | Befund (kurz) | Eingearbeitet in |
|---|---|---|---|
| 1 | kritisch | Next sieht den öffentlichen Host nicht (`localhost:3847`), Matcher deckt `/`, `/admin`, `/_next` nicht | 1.1, 3.2 (Kopf `X-DDD-Bereich`, nginx-Pfadliste, Matcher, relative 308, `ADMIN_LOKAL` nur ohne Proxy), 6, 7 (1a), 8 |
| 2 | kritisch | Geänderte Uhrzeit oder geändertes Datum erzeugt eine zweite Zeile, `abgleich_titel/_ort` reichen nicht | 1.2, 4.4 Teil B (vier `abgleich_*`-Spalten, Schritt 0), 5 (S2), 6 |
| 3 | kritisch | Magazin: DEFINER öffnet die Sperre „nur Redaktion“, Admin-Token fehlen GRANTs und UPDATE | 1.2, 4.6 „Rechte“ (alles über DEFINER-Funktionen, Whitelist), 5 (S3), 6, 8 |
| 4 | kritisch | Admin-Token darf kein DELETE und keine fremden Merklisten ändern, Funktionen nicht DEFINER | 3.3, 3.5, 4.4 (Dubletten, Gebiet), 5 (S2), 6 |
| 5 | mittel | Feldschutz an drei Stellen, `abgesagt = false` gilt als leer | 1.2, 4.4 Teil A, 6 |
| 6 | mittel | Tagesvorschau braucht dieselben Eingaben wie `page.tsx`, kein fertiger „Grund“ | 4.5 (`startseitenAuswahl`, `stufeErklaeren`), 6 |
| 7 | mittel | `revalidateTag` braucht `{ expire: 0 }`, weitere Caches | 4.4 „Cache“ |
| 8 | mittel | Cookie fest auf `ddd_sitzung`/`/api/konto`, `kontoRoute` hängt an `KONTEN_AKTIV`, Origin nur `SITE_URL` | 3.3 (Parameter, `adminRoute`, `ADMIN_URL`), 6 |
| 9 | mittel | Bildpfade auf dem Admin-Host fehlen | 3.2 Punkt 1 und 4 |
| 10 | mittel | Cockpit zählt Vorschläge vor deren SQL; Verweis S2 statt S3 | 1.2, 4.1, 5 (S1 in 1a), 7 |
| 11 | mittel | Starten braucht `Actions: write` | 3.4, 8, 9 (E3) |
| 12 | mittel | `orte`-Policies prüfen `service_role`, Admin sieht inaktive Orte nicht | 4.7 „Rechte“, 5 (S4) |
| 13 | gering | Drei Sätze im Bestand ungenau (Verweis, Zeilen `75–120`, Push-Zweig, `ORTSSEITEN_MELDEN`) | 1.1, 1.2, 1.3 |
| 14 | gering | Warnregeln: Ebene und Median-Grundlage unklar | 4.3 (Tabelle mit Ebene, Median nur `ok`/`leer`) |
| 15 | gering | Feldliste der Dubletten, Merkliste bleibt heute hängen, Titelbereinigung | 4.4 „Dubletten“ |

## Anhang C: Cursor-Prüfung 2 vom 23.11.2026 – Einarbeitung

Alle 6 Befunde sind am Code nachgeprüft und stimmen (`pipeline/unterkategorien.py:208–244`, `pipeline/beschreibung_quellen.py:584–587` und `:669–741`, `web/lib/magazin-daten.ts:62–221`, `database/client.py:296–335`). Cursor bestätigt außerdem: Die neue 404-Prüfung ändert die bestehenden Proxy-Zweige nicht, die relative `Location: /admin` ist hinter nginx richtig, Schritt 0 passt vor Schritt 1, und das Umziehen der Merkliste ist mit den Triggern vereinbar (nur `merkliste_vor_insert`, kein UPDATE-Trigger).

| Nr. | Schwere | Befund (kurz) | Eingearbeitet in |
|---|---|---|---|
| 1 | kritisch | Kopf nur sicher, wenn diesdas.events ihn überschreibt; Reihenfolge Deploy/nginx | 3.2 Punkt 1 (Reihenfolge, `curl`-Prüfung), 4.2 (Ampel), 7 (Schritt 1a-0), 8 (Risiko neu formuliert) |
| 2 | mittel | `vereinheitlichen()` und `veranstalter_nachziehen()` schreiben an `redaktion_felder` vorbei | 4.4 Teil A „Weitere Schreiber“, 6; eigener Fund `beschreibungen_nachziehen()` ebenda |
| 3 | mittel | Schritt 0 ohne Uhrzeit kann bei mehreren Vorstellungen die falsche treffen | 4.4 Teil B, 6 |
| 4 | mittel | Magazin: Anlegen fehlt, `event_ids` nicht in der Whitelist, `_speichern` schreibt Veröffentlichte, Admin-Vorschau, Cache-Tags | 4.6 (Rechte, Entwürfe, Cache, neuer Beitrag), 5 (S3), 6 |
| 5 | gering | `startseitenAuswahl` lädt oder rechnet? | 4.5 |
| 6 | gering | Tabellenköpfe in Abschnitt 5, `schluessel` fehlt | 5 |

## Anhang D: Cursor-Prüfung 3 vom 23.11.2026 – Einarbeitung

Gesamturteil Cursor: **freigabefähig**. Alle 4 Hinweise sind am Code nachgeprüft und stimmen (`pipeline/unterkategorien.py:115–166`, `pipeline/categorizer.py:180–254`). Cursor bestätigt außerdem: Im Lauf von `main.py` gibt es keine weiteren Schreiber. `(art, schluessel)` hält abgelehnte Vorschläge fest und schlägt ein anderes Ziel-Event neu vor. `cacheTag("magazin")` erneuert Beitragsseite, Rubrik, Autor, Magazin-Start, Startseiten-Verweise, Sitemap und Feed. Der Feed behält über `Cache-Control: public, max-age=300` bis zu 5 Minuten in Zwischenspeichern, das ist hingenommen.

| Nr. | Schwere | Befund (kurz) | Eingearbeitet in |
|---|---|---|---|
| 1 | mittel | Python-Liste in Abschnitt 5 ohne `unterkategorien.py` und `beschreibung_quellen.py` | 5 (Liste Stufe 1d) |
| 2 | gering | `nachtragen()` und `kategorisieren()` als Randfälle; Filter in der Abfrage statt vor dem Update | 4.4 Teil A, 5, 6 |
| 3 | gering | `MagazinArtikel`: was in der Beitragsseite bleibt | 4.6 „Entwürfe“ |
| 4 | gering | `curl`-Prüfung direkt nach 1a-0 sagt nichts | 3.2 Punkt 1 |

Außerdem: Satz in 4.5 zu `vergangeneWochenendEvents` an „rechnet nur“ angepasst.

## Anhang E: Cursor-Prüfung 4 vom 23.11.2026 – Einarbeitung

Gesamturteil Cursor: **freigabefähig**, sobald der Filter-Satz für `kategorisieren()` und `vereinheitlichen()` getrennt ist. Alle Hinweise sind am Code nachgeprüft und stimmen (`pipeline/categorizer.py:238–248`, `pipeline/unterkategorien.py:186–206`, `database/client.py:100–101`, `database/magazin_2026-11-19.sql:51`).

| Nr. | Schwere | Befund (kurz) | Eingearbeitet in |
|---|---|---|---|
| 1 | mittel | Abfrage-Filter schließt bei `kategorisieren()` und `vereinheitlichen()` zu viel aus | 4.4 Teil A (zwei Arten), 5, 6 |
| 2 | gering | `ort_id`-Nachtrag vor der Schleife ist eine vierte Stelle | 4.4 Teil A, 6 |
| 3 | gering | `admin_magazin_anlegen` braucht einen Slug; Zeilenangaben | 4.6 |
| 4 | gering | 4.9 nannte `nodemailer` noch als Alternative | 4.9 |

Bewusst offen (Cursor bestätigt, kein Befund): Magazin-Prüfung als Job oder Route (4.6), Slug bei Meldungen (4.10), führende CSV je Guide (Q6). Ob die Host-Ampel aus dem Jail prüfen kann, zeigt der Betrieb (4.2).

## Anhang F: Umsetzungsnotizen Stufe 1a (23.11.2026)

Abweichungen vom Wortlaut, beim Bau gemessen:
- **Weiterleitungen im Proxy (3.2):** Eine von Hand relative `Location: /admin` lehnt der Next-Proxy mit 500 ab (`TypeError: Invalid URL`, lokal gemessen). Umgesetzt wie die bestehenden Zweige mit `NextResponse.redirect(new URL("/admin", request.url), 308)`. Next macht eine Location mit eigenem Ursprung beim Ausliefern selbst relativ. Live gemessen an `/entdecken?kategorie=musik` → `location: /kategorie/musik`, lokal an `/` mit Admin-Kopf → `location: /admin`.
- **`ADMIN_LOKAL` (3.2 Punkt 3):** Next setzt im Proxy selbst `X-Forwarded-*`-Köpfe, `istLokal` ist dort also auch ohne nginx falsch. Der Schalter wirkt deshalb nur unter `next dev` (`NODE_ENV=development`). Live läuft immer `next start`, dort greift er nie.
- **Seiten-Schutz (3.3):** Die Admin-Seiten sind statische Hüllen. Ohne Cookie `ddd_admin` leitet der Proxy auf `/admin/anmelden`. Daten gibt es nur über `/api/admin/*`, das Sitzung, Rolle und `aal2` voll prüft. Die Hülle fragt `/api/admin/ich` und leitet je nach Antwort zur Anmeldung oder zum Code.
- **Website-Rahmen:** Der Wurzel-Layout rendert Kopf, Fuß und Tab-Leiste auch unter `/admin`. Statt alle Seiten in eine Routengruppe zu verschieben, blendet `app/admin/admin.css` sie per `body:has(.admin-rahmen)` aus.
- **Streamlit unter `/alt`:** Mit dem Deploy von 1a startet Streamlit mit `--server.baseUrlPath alt`. Bis nginx für admin.diesdas.events umgestellt ist (`docs/admin-nginx-anleitung.md`, Teil B), ist das alte Dashboard kurz nicht erreichbar.

Stufen 1b–1d (23.11.2026):
- **Cockpit (1b):** Die Ampel des GitHub-Wächters wird erst nach 12 Stunden ohne Lauf gelb. Grund: GitHub führt den 15-Minuten-Zeitplan nur alle 4–8 Stunden aus (Läufe 20.–23.11.). Die Zahlen, die der Admin-Token nicht sehen darf (Magazin-Entwürfe, Konten), liefert `admin_cockpit_zahlen()` (`database/admin_cockpit_2026-11-23.sql`).
- **Scraper (1c):** Python-Tests laufen mit `unittest`, pytest ist nicht installiert und kommt nicht dazu.
- **Vorschläge (1d):** `pipeline/dubletten_sql.py` und `pipeline/gebiet.py` bleiben als Werkzeuge für SQL von Hand. Die Vorschläge schreibt das neue Modul `pipeline/vorschlaege.py` mit deren Regeln (`paare_finden`, `grund_ausserhalb`), aufgerufen in `main.py` als Schritt 3e.
- **Feldschutz (1d):** In `_anreicherungs_update_bauen` filtert eine einzige Stelle am Ende alle Schlüssel aus `redaktion_felder` aus dem Update. Damit sind alle vier Schreibstellen abgedeckt.
- **Admin-Rahmen:** Er liegt in `Suspense`, weil `usePathname` bei `/admin/events/[id]` erst im Browser feststeht.
- **Offen:** Für den Feldschutz in `categorizer.kategorisieren()` gibt es keinen eigenen Test (der Schritt ruft die KI). Den Code hat Cursor bei der Umsetzungsprüfung gesehen.

Stufe 1e (23.11.2026):
- `web/lib/startseite.ts` (`startseitenAuswahl`) rechnet Tipp, Picks, „Beliebt“ und Wochenende. Startseite und Admin-Vorschau nutzen sie beide.
  - Ein Test vergleicht die vier Blöcke mit der bisherigen Rechnung.
  - Lokal gegen live verglichen: gleiche Tipps und Picks für den 28.11., für heute und für das Wochenende.
- `stufeErklaeren` in `ableitungen.ts`. Ein Test sichert, dass ihre Stufe gleich `breite()` ist.
- `/` → `/admin` greift nur mit dem echten Kopf `X-DDD-Bereich: admin` (`hatAdminKopf`), nicht mit `ADMIN_LOKAL`. So bleibt die Startseite beim Entwickeln erreichbar.

Stufe 2 (23.11.2026):
- **Prüfung nach Bearbeitung:** `web/lib/admin/magazin-pruefung.ts` überträgt die festen Regeln (a)–(i) aus `pipeline/magazin.py` auf das fertige Markdown. (g) entfällt, die gilt nur vor dem Modellaufruf.
  - Zusätzlich: Alt-Text Pflicht, `/event/`-Links erlaubt.
  - Gegen die drei veröffentlichten Beiträge geprüft: alle grün, wie in der Pipeline.
  - Das Ergebnis übergibt die Route an `admin_magazin_speichern`. Grün → `in_pruefung`, rot → `entwurf`.
- **Events tauschen:** `event_ids` folgt beim Speichern den Einbettungen `{{event:<id>}}` im Text. Getauscht wird also im Text, die Liste geht automatisch mit.
- **`MagazinArtikel`:** Die gemeinsame Komponente nutzen die öffentliche Entwurfs-Vorschau und die Admin-Vorschau. Die öffentliche Beitragsseite bleibt unverändert (geringeres Risiko). Das weicht vom Wortlaut in 4.6 ab.
- **Admin-Vorschau:** Sie ist eine Server-Komponente. Sie liest die Sitzung, erneuert sie aber nicht (`adminSitzungLesen`): Ein Erneuern würde den Refresh-Token verbrauchen, ohne das Cookie zu setzen.
- **SQL S3:** `database/admin_magazin_2026-11-23.sql`, 11 Funktionen inklusive `admin_pflicht()` und `admin_magazin_autoren()`.
- **Cursor-Prüfung Stufe 2 (deploybar):**
  - Behoben: Wortgrenze 600–1800 für jede Rubrik; Datum im Kopf ohne Zeitraum ist rot; Redaktionsplan mit laufendem Monat; leerer Korrekturtext wird abgewiesen.
  - Bewusst hingenommen: `admin_magazin_speichern` übernimmt das Prüfergebnis der Route. Ein direkter Aufruf mit Admin-Sitzung und Zwei-Faktor könnte grün melden – der Admin ist die Redaktion und darf ohnehin veröffentlichen.
  - Bewusst erweitert: Aufmacherbilder aus `/fallback/` gelten nach der Liste der Website (`ERLAUBTE_FALLBACK_HEROS`, alle ≥ 675 px), nicht nur die sieben Rubrik-Ersatzbilder der Pipeline.

Stufe 3a – Orte (23.11.2026):
- **Teilbereiche:** 3a = Orte-Liste, Stammdaten, Score, Texte der Spielstätten, Zuordnung lösen, Zusammenlegen, Schließen/Löschen. 3b = Bilder (Kandidaten, `bild_fokus`) und Guide-Pflege (Clubs ↔ Bar, Weihnachtsmärkte Top 5/Ruhetage, Spielplätze freischalten mit Prüf-Codes, typabhängige `extras`-Formulare, `freigeschaltet_am`). 3c = Vorschläge (Ortsnamen, `ort_id`-Nachtrag, Adressen/Geo, Import).
- **SQL S4:** `database/admin_orte_2026-11-23.sql`: Policies `orte_admin_lesen`/`orte_admin_aendern` (ist_admin()) und fünf DEFINER-Funktionen: `admin_ort_zusammenlegen`, `admin_ort_schliessen` (mit `p_loeschen`), `admin_ort_text_speichern` (Entwurf oder Freigabe), `admin_ort_zuordnung_loesen`, `admin_ort_score_setzen`.
- **Slug und Typ** sind in 3a nicht änderbar (URL-Wechsel; Typwechsel Clubs ↔ Bar kommt mit `vorher_typ` in 3b). Abschalten nur über „Schließen“ mit Weiterleitung, auch bei Nicht-Spielstätten (strenger als der Trigger, Plan 4.7).
- **Texte:** Entwurf in `extras.spielstaette.text_entwurf` {text, quellen, datum}; Freigabe setzt `beschreibung` und `text_freigegeben` und löscht den Entwurf. Nur Spielstätten (nur dort gibt es die Freigabe). Bei anderen Typen bleibt die Beschreibung ein Stammdatenfeld. Später kann `scraper/orte/spielstaetten_texte.py` Entwürfe direkt in `text_entwurf` schreiben statt SQL-Dateien.
- **Zuordnung lösen:** setzt `ort_id` NULL und `ort_id` in `redaktion_felder` (Feldschutz aus Stufe 1d). Eine ganze Schreibweise aus `event_orte` lösen gehört zur Guide-Pflege (3b), weil `clubs_profil.py` die Club-Liste neu berechnet.
- **Score:** `extras.score_manuell` = Begründung; `flaechensuche.py` lässt den Score dann stehen. Spielplätze und Weihnachtsmärkte haben eigene Scores (3b).
- **Zusammenlegen:** wie `orte_balletthaus_zusammen_2026-11-20.sql`, zusätzlich Säle umhängen und Schreibweisen beider Listen (club, spielstaette) plus Name übernehmen. Ziel muss aktiv sein.
- **Cache:** Alle Orte-Lader (`orte.ts`, `spielstaetten-daten.ts`, `spielplaetze-daten.ts`, `weihnachtsmaerkte-daten.ts`, `orteFuerSlugs`) bekommen `cacheTag("orte")`; die Routen leeren ihn nach jeder Änderung (bei Event-Umzug auch `events`).
- **Bekannt:** Für geschlossene Guide-Orte (Restaurant, Club …) bleibt `/guides/<hub>/<slug>` eine 404 – `ort_weiterleitungen` wirkt nur unter `/orte/<slug>` (wie bisher, z. B. Gertrudenhof).
- **Cursor-Prüfung Stufe 3a (deploybar, SQL S4 ausgeführt):**
  - Befund 1 (mittel) behoben: Der Proxy merkte sich eine aktive Spielstätte bis zu 10 Minuten. Jede Orte-Änderung im Admin setzt jetzt einen Stand in `globalThis` (`orteZwischenspeicherVerwerfen`), gemerkte `ort:`/`ort-weiter:`/`ort-id:`-Einträge davor gelten nicht mehr. Proxy läuft laut Build mit `runtime: nodejs` im selben Prozess.
  - Befund 2 (mittel) behoben: Spielplätze und Weihnachtsmärkte lassen sich in 3a weder über das Häkchen freischalten noch löschen (nur schließen; dann greift die Hub-Weiterleitung über `freigeschaltet_am`). Freischalten kommt mit der Guide-Pflege 3b.
  - Befund 3 (gering): Schreibweisen ordnet die Pipeline nur bei Clubs und Spielstätten zu; die Oberfläche sagt das jetzt so. Die Funktion bleibt unverändert.
  - Befund 4 (gering) behoben: „auch vergangene zeigen“ listet die letzten 100 zugeordneten Events, auch alte Zuordnungen lassen sich lösen.

Stufe 3b – Bilder und Guide-Pflege (23.11.2026):
- **Q6 entschieden (Auftraggeber 23.11.2026):** Weihnachtsmärkte – Top-5-Rang, Ausschließen und Freischalten im Dashboard; `import_maerkte.py` übernimmt `top5_rang`, `ausgeschlossen` und `freigeschaltet_am` bei vorhandenen Zeilen aus der Datenbank (`dashboard_felder_behalten`, Warnung im Log bei abweichender CSV); Saisonzeiten und Ruhetage bleiben CSV. Spielplätze – Prüf-Codes bestätigen, Ausschließen, Freischalten im Dashboard; jede Änderung trägt das Feld in `extras.spielplatz.redaktion` ein, `stadt_import.py` und `abenteuer_import.py` lassen es stehen (`scraper/spielplaetze/redaktion.py`). Bilder – Google-Fotos auf Knopfdruck.
- **Gesperrte Stammdaten:** Spalten, die ein Import bei jedem Lauf neu schreibt (Weihnachtsmarkt: Name, Stadtteil, Adresse, Geo, Website, Beschreibung; Spielplatz: Name, Stadtteil, Adresse, Geo, Öffnungszeiten), sind im Formular gesperrt (`CSV_FELDER`), sonst wären Änderungen beim nächsten Lauf weg.
- **SQL:** `database/admin_guides_2026-11-23.sql`, fünf DEFINER-Funktionen: `admin_ort_bild_setzen`, `admin_ort_bild_fokus`, `admin_club_setzen`, `admin_wm_setzen`, `admin_spielplatz_setzen`.
- **Bilder:** Kandidaten von Google über die Places API (`X-Goog-FieldMask: photos`), Vorschau über `/api/admin/orte/foto` (nur durchgereicht, nicht gespeichert). Spielstätten nie mit Google-Fotos. Eigene Dateien aus `web/public/ort-bilder` (Auswahl, kein Upload, Q5). Jede Auswahl setzt `foto_manuell` und erhöht `foto_version`; die Route leert zusätzlich `ort-foto:<slug>`. Bildausschnitt per Klick in 5-%-Schritten.
- **Clubs:** Top-Empfehlung (`club_freigegeben`) setzen/entziehen ersetzt `clubs_profil.py freigeben`. „Aus dem Club-Hub“: `kein_club` mit Grund; eine Zeile vom Typ `club` wird zur Bar (`typ kneipe`, `vorher_typ club`, `unterart bar`). „In den Club-Hub“: `auch_club`, sichtbar erst mit Profil und Score aus `clubs_profil.py`.
- **Weihnachtsmärkte:** Rang 1–5 ist eindeutig (ein anderer Markt mit dem Rang verliert ihn). Freischalten mit derselben Bedingung wie `weihnachtsmaerkte_freischalten.sql`.
- **Spielplätze:** `name_unklar` und `kein_stadtteil` lassen sich nicht bestätigen (sperren immer, Korrektur über `korrekturen.csv`). Freischalten mit derselben Bedingung wie `spielplaetze_freischalten.sql`.
- **Offen für 3c:** Vorschläge (Ortsnamen, `ort_id`-Nachtrag, Adressen/Geo, Import aus Kandidaten).
- **Cursor-Prüfung Stufe 3b (deploybar, SQL ausgeführt):**
  - Befund 1 (mittel) behoben: Ein aktiver Club wird nur zur Bar, wenn sein Score mindestens 7 ist (Route). Nur dann leitet die alte Club-URL auf die Bar-Seite; darunter wäre sie eine 404 geworden. Bar-Seiten unter 7 auszuliefern hätte die Score-Regel der Guides aufgeweicht.
  - Befund 2 (gering) behoben: `?v=` hängt ab `foto_version` 1 an der Bildadresse (`ortBildUrl`, Ortsseiten-Kopfbild), damit auch die erste Bildwahl im Admin eine neue Adresse ergibt.

Stufe 3c – Vorschläge zu Orten (23.11.2026):
- **Drei neue Arten** in `pipeline/vorschlaege.py`, erzeugt im Lauf (Schritt 3e) statt der SQL-Dateien:
  - `ortsname` (je alter → neuer Name, Regeln von `ortsnamen.py umbenennungen`, Reihen-Ort und -Schlüssel ziehen mit; ist ein neuer Reihen-Schlüssel schon vergeben, entfällt der Vorschlag mit Warnung im Log);
  - `ort_id` (je Event ab heute, Regeln von `ort_zuordnung.ort_zuordnen`, nie NULL);
  - `adresse` (je künftigem Rausgegangen-Event ohne Adresse, Regeln von `adressen_ergaenzen` ohne OpenStreetMap; Stadtteil nur, wenn leer).
  - Events mit dem Feld in `redaktion_felder` bekommen keinen Vorschlag; die Annahme prüft es noch einmal (Plan 4.4). `abgleich_ort` bleibt unverändert.
- **SQL:** `database/admin_vorschlaege_orte_2026-11-23.sql` legt `admin_vorschlag_annehmen` vollständig neu an (Dublette und Gebiet unverändert) und dazu `admin_ortsname_anwenden` (nur intern aufrufbar). Ein Event, das beim Umbenennen mit einem anderen Termin zusammenfiele, bleibt beim alten Namen (unique_violation je Event abgefangen). Ein `ort_id`-Vorschlag auf einen inzwischen inaktiven oder gelöschten Ort wird abgewiesen.
- **Gesammelt:** `/api/admin/vorschlaege/sammel` nimmt bis zu 200 angezeigte Vorschläge an oder lehnt sie ab – nur für die drei Orte-Arten (setzen nur leere bzw. ungeschützte Felder). Dubletten und Gebiet bleiben Einzelentscheidungen.
- **Bewusst nicht in 3c (bleiben Skripte):** Geo der Ortsseiten (`spielstaetten_geo.py`: Google-Suche, Bestätigung der Adresse von Hand, dann OpenStreetMap) und der Import neuer Ortsseiten aus `data/spielstaetten/kandidaten.csv` (Entscheidungen je Haus, Säle, Arten). Beides läuft selten und braucht die Sichtung in der CSV; bei Bedarf eigener Teilbereich.
- **Cursor-Prüfung Stufe 3c (deploybar, SQL ausgeführt):**
  - Befund 1 (mittel) behoben: Ortsnamen-Vorschläge wachsen mit (`ortsname_plan`): Ein offener Vorschlag für alt → neu bekommt bei jedem Lauf die aktuellen Events; nach einer Annahme entsteht ein neuer („alt→neu#2“ …), solange Events die alte Schreibweise tragen; eine Ablehnung gilt für die Schreibweise.
  - Befund 2 (gering) behoben: Reihen bekommen den neuen Ort nur zusammen mit dem passenden Schlüssel (`vorschlag.reihen: [{id, schluessel}]`); Reihen mit einem geschützten Event bleiben ganz beim alten Namen. SQL dafür geändert, erneut auszuführen.

Stufe 4 – Newsletter mit Double-Opt-in (23.11.2026):
- **SQL:** `database/newsletter_doi_2026-11-23.sql`: Spalten `bestaetigung_gesendet_am`, `mails_gesendet`; Job-Funktionen `newsletter_bestaetigung_beanspruchen` (SKIP LOCKED, höchstens 3 Mails je Adresse), `_freigeben`, `newsletter_aufraeumen` (nur `service_role`); `admin_newsletter_zahlen` für den Admin.
- **Job:** `pipeline/newsletter_bestaetigung.py`, Workflow `.github/workflows/newsletter.yml` alle 15 Minuten, nur mit Variable `NEWSLETTER_AKTIV=1` (E9). SMTP-Verbindung nur, wenn etwas zu senden ist; scheitert der Versand, wird die Anmeldung wieder frei. Neues Secret `NEWSLETTER_TOKEN_SCHLUESSEL` (hex, auch in `deploy.yml` → `web/.env.local`).
- **Website:** Anmeldung legt an oder merkt eine neue Mail vor (frühestens nach 24 Stunden, höchstens 3); Antwort immer gleich. Seiten `/newsletter/bestaetigen` und `/newsletter/abmelden` (Token im Fragment, erst der Button schickt es), One-Click `/api/newsletter/abmelden/<token>` (RFC 8058, GET 405).
- **Abweichung vom Plan:** Abmelden **löscht** die Adresse sofort, wie es die Datenschutzerklärung (Abschnitt 11) schon verspricht. Deshalb gibt es im Admin keine Liste „abgemeldet“, nur „bestätigt“ und „nicht bestätigt“. Unbestätigte werden 30 Tage nach der Bestätigungsmail gelöscht (nicht nach der Anmeldung), damit bestehende Anmeldungen ohne Double-Opt-in erst ihre Mail bekommen.
- **Bestehende Anmeldungen** bekommen nach dem Einschalten einmal die Bestätigungsmail – angekündigt in der heutigen Datenschutzerklärung.
- **Admin:** `/admin/newsletter` mit Zahlen, Liste, CSV-Export nur der Bestätigten (BOM, Formel-Schutz), Löschen auf Anfrage; Protokoll ohne Adressen.
- **Rechtliches:** `docs/anwalt-newsletter-doi-2026-11-23.md` (Ablauf, vier Fragen, Entwurf Abschnitt 11 und Hinweis unter dem Formular). Die Datenschutzerklärung bleibt bis zur Freigabe unverändert; ebenso bleibt `NEWSLETTER_AKTIV` aus.
- **Anwalt hat freigegeben (23.11.2026):** Abschnitt 11 der Datenschutzerklärung und der Hinweis unter dem Anmeldefeld wörtlich übernommen; der Satz zum Mailserver gilt jetzt immer (Konto-Mails nur mit Schalter). `NEWSLETTER_AKTIV` setzt der Auftraggeber nach dem Deploy.
- **Cursor-Prüfung Stufe 4 (deploybar, SQL ausgeführt, Secret gesetzt):**
  - Befund 1 (mittel) behoben: One-Click löscht nur bei `application/x-www-form-urlencoded` mit genau `List-Unsubscribe=One-Click` (RFC 8058, `istOneClick`), sonst 400.
  - Befund 2 (gering) behoben: Die Admin-Liste lädt per POST, eine gesuchte Adresse steht nicht mehr in URL und Access-Log.
  - Befund 3 (gering) behoben: Anspruch (`bestaetigung_gesendet_am`) und Zustellung (`bestaetigung_zugestellt_am`, `newsletter_bestaetigung_versandt`) getrennt; ein Anspruch ohne Zustellung wird nach 30 Minuten wieder aufgenommen; gezählt und gelöscht wird nach der Zustellung. SQL geändert, erneut auszuführen.
  - Befund 4 (gering) behoben: Bremslimit der One-Click-Route nur für ungültige Tokens.

## Prüfhistorie

- 23.11.2026: erste Fassung (Claude), Bestand per Code und SQL-Dateien geprüft.
- 23.11.2026: Auftraggeber bestätigt E1–E9 und Q5–Q8 wie vorgeschlagen.
- 23.11.2026: Cursor-Prüfung 1: nicht freigabefähig, 15 Befunde (4 kritisch). Alle nachgeprüft und eingearbeitet → zweite Fassung.
- 23.11.2026: Cursor-Prüfung 2: nicht freigabefähig, 6 Befunde (1 kritisch) plus ein eigener Fund. Alle nachgeprüft und eingearbeitet → dritte Fassung.
- 23.11.2026: Cursor-Prüfung 3: freigabefähig, 4 Hinweise (1 mittel, 3 gering), nachgeprüft und eingearbeitet.
- 23.11.2026: Cursor-Prüfung 4: freigabefähig nach Trennung des Filter-Satzes, 4 Hinweise eingearbeitet → vierte Fassung. **Vom Auftraggeber freigegeben.**
- 23.11.2026: Stufe 1a gebaut (09b56cb, lokal), Umsetzungsnotizen in Anhang F.
- 23.11.2026: Stufen 1b und 1c LIVE (5246581, 11d3945), Stufe 1d LIVE (c16f017, Cursor: deploybar, 5 Hinweise behoben), Stufe 1e gebaut (lokal); Notizen in Anhang F.
- 23.11.2026: Stufe 1 komplett LIVE (eeb93fd), Stufe 2 Magazin gebaut (lokal); Notizen in Anhang F.
- 23.11.2026: Stufe 2 LIVE (cf82caf). Stufe 3a Orte gebaut (lokal), SQL S4 `admin_orte_2026-11-23.sql`; Notizen in Anhang F.
- 23.11.2026: SQL S4 ausgeführt, Cursor-Prüfung 3a deploybar, 4 Befunde eingearbeitet (Anhang F).
- 23.11.2026: Stufe 3a LIVE (38899b9). Stufe 3b Bilder und Guide-Pflege gebaut (lokal), SQL `admin_guides_2026-11-23.sql`, Q6 entschieden; Notizen in Anhang F.
- 23.11.2026: SQL `admin_guides_2026-11-23.sql` ausgeführt, Cursor-Prüfung 3b deploybar, 2 Befunde eingearbeitet (Anhang F).
- 23.11.2026: Stufe 3b LIVE (81bb408). Stufe 3c Vorschläge zu Orten gebaut (lokal), SQL `admin_vorschlaege_orte_2026-11-23.sql`; Notizen in Anhang F.
- 23.11.2026: SQL Stufe 3c ausgeführt, Cursor-Prüfung 3c deploybar, 2 Befunde eingearbeitet (SQL geändert, erneut auszuführen).
- 23.11.2026: Stufe 3c LIVE (d3b0bf3). Stufe 4 Newsletter-Double-Opt-in gebaut (lokal), SQL `newsletter_doi_2026-11-23.sql`, Anwaltsvorlage; Notizen in Anhang F.
- 23.11.2026: Anwalt hat Stufe 4 freigegeben (Texte übernommen), Cursor-Prüfung 4 deploybar, 4 Befunde eingearbeitet (SQL geändert, erneut auszuführen).
