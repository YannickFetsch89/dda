# Plan: Nutzerkonten (Konto, Merkliste im Konto, Interessen)

Stand: 16.11.2026 · **elfte Fassung, vom Auftraggeber freigegeben am 16.11.2026**: acht Cursor-Prüfungen (Abschnitt 20, die sechste bis achte ohne kritischen Befund, die achte mit Empfehlung „freigabereif nach Behebung der geringen Punkte“), die Entscheidungen des Auftraggebers zu E2, E3 und E12, die rechtliche Einschätzung mit E4, E12a, E13 und E14, die Freigabe der Altersbestätigung durch den Anwalt und das Geburtsdatum (E15) sind eingearbeitet. Umsetzung nach Abschnitt 15. **Schritt 1 abgeschlossen** (16.11.2026, 4.0, 4.6). **Schritt 2 vorbereitet**, Ausführung beim Auftraggeber (Checkliste `docs/schritt2-checkliste-nutzerkonten-2026-11-16.md`).
Alle Produktentscheidungen sind getroffen. Die rechtliche Einschätzung liegt nur als Zusammenfassung vor, die sich selbst „keine verbindliche anwaltliche Beratung“ nennt (Abschnitt 19). Die damaligen Fragen stehen als Archivstand in `docs/anwalt-fragen-nutzerkonten-2026-11-16.md`, die Antworten sind hier eingearbeitet.

**Ziel:** Wer möchte, legt ein kostenloses Konto mit verifizierter Mailadresse an. Die Merkliste liegt dann im Konto und ist auf jedem Gerät da, später auch in der App. Bei der Anmeldung fragen wir Interessen ab, damit wir Events, Ausflüge und Orte besser empfehlen können. Gemerkte Events werten wir zusätzlich zusammengefasst aus, um zu sehen, was beliebt ist.

Es gelten dieselben Regeln wie bei den anderen Plänen: Deploy nur nach OK. SQL liegt als Datei in `database/`, der Auftraggeber führt sie aus. Keine neue Bibliothek ohne Rückfrage, Texte auf Deutsch. Leser-Ansprache ihr/euch, Datenschutz in Sie-Form. Der Browser spricht nur mit unserem eigenen Server.

---

## 1. Geprüfte Fakten (Code, Stand 16.11.2026)

### 1.1 Merkliste heute
- Die Merkliste besteht nur aus Event-IDs in `localStorage` unter dem Schlüssel `ddd-merkliste` (`web/components/client.tsx`, Zeilen 7–59). Die Tabs bleiben über das `storage`-Ereignis und ein eigenes Ereignis `ddd-merkliste-geaendert` im Gleichstand.
- `useMerkliste()` nutzt `useSyncExternalStore` mit dem Server-Snapshot `LEER` (Zeile 47). Der Server rendert jedes Herz deshalb als „nicht gemerkt“. **Gecachte Seiten enthalten keinen Merkzustand.** Diese Eigenschaft muss bleiben.
- `HerzButton` (Zeilen 61–78) steckt in `web/components/karten.tsx:97` (alle Karten) und `web/app/event/[kategorie]/[slug]/page.tsx:121` (Eventseite). Gemerkt wird die ID des gebündelten Eintrags, also des frühesten nicht abgesagten Termins (`web/lib/termine.ts`, `buendeln`).
- Die Seite `web/app/merkliste/page.tsx` ist schon `noindex` (Zeile 6). Zeile 14 zeigt fest „Nur auf diesem Gerät gespeichert“ (Screenshot des Auftraggebers vom 16.11.2026).
- `web/components/merkliste.tsx` holt die Events über `GET /api/events?ids=…` (`web/app/api/events/route.ts`). Die Route **kürzt auf 100 IDs** (Zeile 10). Nicht gefundene IDs zählen als „nicht mehr verfügbar“ (Zeilen 72–76). Die Texte stehen in du-Form („Tipp aufs Herz“, „Deine gemerkten Events sind vorbei“).
- Event-IDs sind UUIDs. Die Pipeline löscht keine Events: Dubletten bekommen `abgelehnt = true` und eine 301 über `event_seo_entscheidungen` (`pipeline/dubletten_sql.py`, Zeilen 13 und 168). Der Lesepfad `eventLaden` lässt abgelehnte Events weg (`web/lib/daten.ts`, Zeile 248). Eine gemerkte Dublette erscheint heute als „nicht mehr verfügbar“.

### 1.2 Fragebogen `web/components/fragebogen.tsx`
- Er gehört fest zum Restaurant-Hub. Er nutzt `FragebogenDaten` mit Orte-Tupeln (Zeilen 14–20), feste `ARTEN` für Restaurant, Café und Imbiss (Zeilen 34–39), `PREIS_STUFEN` und `filterHref` aus `lib/guide-filter.ts`. Er öffnet sich als `<dialog>` und springt am Ende auf eine Hub-URL (Zeilen 89–102).
- **Wiederverwendbar** sind das Bedienmuster und die CSS-Klassen: `fb__kopf`, `fb__fortschritt`, `fb__inhalt`, `fb__karten`/`fb__karte`, `fb__chips`, `gd-chip gd-chip--gross` mit `aria-pressed`, `fb__fuss`/`fb__weiter`, „Zurück“, Fortschrittsbalken und „Überall/alle“ als Chip, der die Auswahl leert.
- **Nicht wiederverwendbar** sind Datenform, Schritte, Zähllogik und das Ziel (URL statt Speichern).

### 1.3 Supabase Auth und Rechte heute
- `database/auth_rollen.sql` legt `public.profiles` an (1:1 zu `auth.users`, `ON DELETE CASCADE`) mit `rolle` (`admin` | `user`, Standard `user`), `anzeigename` und `praeferenzen JSONB DEFAULT '{}'`, das ausdrücklich für Website- und App-Nutzer gedacht ist. Ein Trigger legt das Profil bei der Registrierung an (`profil_anlegen`). `profil_vor_update` verhindert, dass jemand sich selbst zum Admin macht. Laut RLS liest und ändert jede Person ihre eigene Zeile, Admins alle Zeilen (`id = auth.uid() OR ist_admin()`, Zeilen 119–127). Das Dashboard liest aus `profiles` nur `rolle` (`dashboard/auth.py`, Zeile 34) und schreibt die Tabelle im Repo nicht.
- Das Dashboard meldet Admins per **Passwort** über Supabase Auth an (`dashboard/auth.py`, Zeile 59), im **selben Projekt**. Auth-Einstellungen wie Mailvorlagen, Signup und Rate Limits gelten also auch für die Admin-Konten.
- Viele Admin-Regeln hängen an `TO authenticated` plus `public.ist_admin()`, etwa für Newsletter, Meldungen, SEO-Entscheidungen, Scraper-Berichte und Storage. `meldungen_haertung_2026-11-05.sql` gibt `authenticated` SELECT, UPDATE und DELETE auf `newsletter_anmeldungen` und `event_meldungen`, abgesichert über Admin-Policies. **Mit öffentlichen Konten ist jeder angemeldete Nutzer `authenticated`.** Jede Tabelle ohne RLS oder mit einer zu weiten Policy wäre dann offen. Nicht alle Tabellen der Live-Datenbank sind im Repo belegt (z. B. Spielplatz-Daten). Deshalb gibt es vor allem anderen eine Prüfung (Schritt 1).
- Gewollt öffentlich lesbar und heute schon für alle Besucher offen sind `event_seo_entscheidungen` (`USING (true)` für `anon, authenticated`, `database/event_seo_2026-11-05.sql`, Zeilen 24–25; `web/proxy.ts` liest sie mit dem anon-Key), `reihen` (`USING (true)`, `database/reihen_2026-11-05.sql`, Zeile 27), `orte` (`USING (aktiv = true)`, `database/schema_orte.sql`, Zeilen 65–67) und `events` (`abgelehnt = FALSE`, `auth_rollen.sql`).
- `orte` erlaubt Schreiben nur über `auth.role() = 'service_role'` (`database/schema_orte.sql`, Zeilen 69–71). Für `authenticated` ist das unkritisch.
- Ob „Allow new users to sign up“ heute an ist, steht nicht im Repo. Der Auftraggeber prüft das in Schritt 2.

### 1.4 Rendering und Cache
- `next.config.ts` setzt `cacheComponents: true` und `partialPrefetching: true`. `eventPoolLaden()` ist mit `"use cache"` 10 Minuten gecacht (`web/lib/daten.ts`, Zeilen 217–232).
- Kein Server Component liest heute `cookies()` oder `headers()`. `layout.tsx` rendert `Kopf`, `KategorieLeiste`, `Fuss` und `TabBar` für jede Seite (Zeilen 49–56). Nach der Next-Doku (`node_modules/next/dist/docs/01-app/02-guides/authentication-with-cache-components.md`) gilt: Ein Sitzungs-Lesen im Layout hält jede Seite hinter der Anfrage auf, `cookies()` außerhalb einer Suspense-Grenze ist ein Build-Fehler, und Cache-Schlüssel liegen im Klartext vor.
- `web/proxy.ts` läuft nur für Event-, Tag-, Reihen-, Guide-, Landing- und `/entdecken`-Pfade (Zeile 63). Rewrites sind hinter nginx verboten (Memory „Proxy-Rewrite hinter nginx“).
- `lib/supabase-server.ts` hält je einen Client pro Prozess **ohne** Sitzung und ohne `autoRefreshToken`. Am 06.11.2026 ist der Server abgestürzt, weil pro Anfrage neue Clients mit Auffrisch-Timer entstanden (Zeilen 3–7).

### 1.5 Formulare, Bremslimit, Umgebung
- `lib/formulare.ts` bietet `absenderIp` (X-Real-IP von nginx, live geprüft), `zuGross`, `zuVieleAnfragen` (im Speicher, je Prozess, Zeilen 64–95) und `antwort` mit `Cache-Control: no-store` (Zeile 97). **Lücke in `zuVieleAnfragen`:** Die Bereinigung (Zeilen 73–75) löscht alle Schlüssel, deren Treffer älter sind als das Fenster des **gerade laufenden** Aufrufs. Heute nutzen alle Aufrufe eine Stunde (Newsletter, Event melden), also schadet das nicht. Mit einem 15-Minuten-Limit daneben würde es die Stundenzähler anderer Routen löschen. Für den Newsletter gibt es einen Honeypot und eine Antwort, die nicht verrät, ob eine Adresse schon bekannt ist (`app/api/newsletter/route.ts`, Zeilen 20 und 32).
- Der Deploy-Workflow schreibt nur `SUPABASE_SERVICE_KEY` (und `GOOGLE_PLACES_API_KEY`) nach `web/.env.local` (`.github/workflows/deploy.yml`, Zeilen 58–78). `SUPABASE_URL` und `SUPABASE_KEY` (anon), die `lib/supabase-server.ts` liest, müssen dort schon liegen. Öffentliche `NEXT_PUBLIC_SUPABASE_*`-Variablen gibt es nicht. Der neue Schalter `KONTEN_AKTIV` kommt auf dieselbe Weise in `web/.env.local` (Abschnitt 15).
- `next.config.ts` hat schon eine `headers()`-Funktion mit HSTS für `/:pfad*` (Zeilen 9–17). Neue Header kommen als weiterer Eintrag in dasselbe Array, sonst geht die HSTS-Regel verloren.
- In `package.json` ist `@supabase/supabase-js ^2.118.0` vorhanden, `@supabase/ssr` nicht.

### 1.6 Datenschutz und UI
- `web/app/datenschutz/page.tsx`, Stand Oktober 2026. Abschnitt 5 (Cookies) nennt die Merkliste als technisch notwendig. Abschnitt 7 sagt über `localStorage`: „ausschließlich lokal … nicht an uns übermittelt“. Abschnitt 9 sagt, der Browser verbinde sich „nicht direkt mit Supabase“. Abschnitt 14 nennt die Betroffenenrechte. Abschnitt 15 (Zeilen 289–295) sagt, eine Weitergabe an Dritte finde nicht statt, und nennt die Auftragsverarbeiter dabei nicht.
- Kopf: Herz-Icon nur auf dem Desktop (`web/components/rahmen.tsx`, Zeile 45). Im Mobilmenü stehen unter „Service“ Merkliste und Event melden (Zeilen 67–69), im Fuß steht „Merkliste“ (Zeile 169). Die TabBar hat fünf Tabs, einer davon ist Merkliste (`client.tsx`, Zeilen 295–301).
- `robots.ts` sperrt nur `/api/` (Zeile 9).

---

## 2. Entscheidungen

| Nr. | Frage | Stand |
|---|---|---|
| E1 | Merken ohne Konto? | **Entschieden (16.11.2026):** Das Konto ist freiwillig, das Herz geht weiter ohne Anmeldung. Auf der Merkliste und an passenden Stellen steht ein Hinweis auf die Anmeldung (Abschnitt 7). |
| E2 | Anmeldeverfahren | **Entschieden (16.11.2026):** Mailadresse und Passwort. Die Adresse wird mit einer Bestätigungsmail verifiziert. Dazu kommt „Passwort vergessen“ zum Zurücksetzen per Mail, außerdem „Passwort ändern“ im Konto (Abschnitt 5.1). |
| E3 | Mail-Dienst | **Entschieden (16.11.2026):** Versand über unseren eigenen Server, also das SMTP-Postfach beim Hoster, auf dem auch die Website läuft. Kein zusätzlicher Dienst (Abschnitt 10). |
| E4 | Grundlage der Beliebtheits-Zählung | **Entschieden (16.11.2026), nach der rechtlichen Einschätzung:** berechtigtes Interesse (Art. 6 Abs. 1 lit. f) mit dokumentierter Interessenabwägung (`docs/interessenabwaegung-statistik-<datum>.md`, vor dem Einschalten) und Widerspruch im Konto. `analyse_erlaubt` ist `false`, bis die Person den gesonderten Hinweis nach Art. 21 Abs. 4 gesehen hat (Abschlussseite, 5.3 (c)). Ohne Widerspruch setzt „Fertig“ es dort auf `true`. Konten, die die Abschlussseite nie erreichen, zählen nicht mit. **Sensible Events (E13) zählen nie mit.** Ein gesonderter Hinweis auf das Widerspruchsrecht (Art. 21 Abs. 4) steht auf der Abschlussseite (5.3) und im Konto. |
| E12 | Interessen und persönliche Empfehlungen | **Entschieden (16.11.2026), mit Änderung nach der rechtlichen Einschätzung (E12a):** Die Interessen werden **immer** gleich beim Anlegen eines neuen Kontos abgefragt, als fester Teil der Registrierung, mit „Ohne Interessen weiter“ auf jeder Seite. **Am Ende der Fragen** folgt eine Abschlussseite mit nicht vorangekreuzten Einwilligungen: (a) Interessen speichern und für Empfehlungen nutzen, (b) sensible Events im Konto speichern (E13). Erst dieses Häkchen ist die Einwilligung. Das bloße Ausfüllen gilt nicht mehr als Einwilligung, weil die Einschätzung das als „zu unsicher“ bewertet. Die Antworten bleiben bis dahin nur im Browser. Ohne Häkchen (a) wird nichts gespeichert (5.3). Abgefragt wird nach der Mail-Bestätigung. Nur die Anmeldung führt auf den Fragebogen, die übrige Website bleibt erreichbar, und der Fragebogen kommt bei der nächsten Anmeldung wieder, solange er nicht abgeschlossen ist. |
| E13 | Sensible Events | **Entschieden (16.11.2026):** Es gibt einen Sensibel-Filter. Events, aus deren Merkung sich besondere Kategorien nach Art. 9 DSGVO ableiten lassen (Gesundheit, Religion oder Weltanschauung, sexuelle Orientierung oder Identität, politische Meinung, Gewerkschaft, ethnische Herkunft), werden **nur im Backend** gekennzeichnet (Abschnitt 5.8). **Für Nutzer ist nirgendwo ersichtlich, welche Events als sensibel gelten:** keine Markierung, kein Hinweis am Event, keine eigene Liste. Ohne ausdrückliche Einwilligung (b) bleiben solche Merkungen nur auf dem Gerät. Mit Einwilligung kommen sie ins Konto. In Empfehlungen und Statistik fließen sie nie ein. Die Einwilligung erklärt allgemein, was wir als sensibel betrachten, ohne Events zu nennen. |
| E15 | Geburtsdatum | **Entschieden (16.11.2026):** Wir fragen nach dem Geburtsdatum, um z. B. Glückwunsch-Mails (später auch Push in der App) zu verschicken. Umsetzung: **freiwillig** auf der Abschlussseite (5.3 (d)), gespeichert nur zusammen mit der Einwilligung in Geburtstagsmails. Geburtstagsgrüße eines Unternehmens gelten als Werbung und brauchen nach § 7 Abs. 2 UWG eine ausdrückliche Einwilligung, und ohne diesen Zweck gäbe es keinen Grund, das Datum zu speichern (Datenminimierung, Art. 5 Abs. 1 lit. c). Ein Pflichtfeld wäre damit nicht haltbar. Das Alters-Häkchen bleibt die Altersbestätigung. Ein angegebenes Datum unter 16 Jahren wird abgelehnt und sperrt das Konto (4.5). Der Versand ist ein eigener Schritt nach dem Start (Abschnitt 13a). Web-Push im Browser gibt es nicht: Er liefe über Push-Dienste von Google, Mozilla oder Apple, und das verbietet die Regel „Browser kontaktiert keine Drittanbieter“. Push kommt mit der App. |
| E14 | Nutzungsbedingungen | **Entschieden (16.11.2026):** Es gibt Nutzungsbedingungen für Konten, Entwurf in `docs/nutzungsbedingungen-entwurf-2026-11-16.md`, vor dem Einschalten anwaltlich zu prüfen. Sie stehen auf der Seite `/nutzungsbedingungen`, sind im Registrierungsformular und im Fuß verlinkt und werden mit „Konto anlegen“ akzeptiert (5.1). |

Festlegungen von Claude, im Review änderbar:

- **E5:** Kein Login über Google, Apple oder Facebook. Das hält den Browser frei von Dritten und vermeidet die Apple-Pflicht im App Store, die mit fremden Logins einhergeht.
- **E6:** Mindestalter 16 (Art. 8 DSGVO). Es gibt Dating- und Nightlife-Inhalte, und eine Einwilligung unter 16 bräuchte die Eltern. Bestätigt wird es nach der rechtlichen Einschätzung **vor der Kontoanlage**, mit einem Pflicht-Häkchen im Registrierungsformular (5.1). Ein Alters-Häkchen ist kein sicherer Altersnachweis, für dieses risikoarme Angebot aber angemessen. **Vom Anwalt am 16.11.2026 so freigegeben** (Häkchen, Grenze 16, Ablauf wie in 5.1).
- **E7:** Keine neue Bibliothek. `@supabase/supabase-js` reicht: Registrierung, Anmeldung und Passwortwechsel laufen serverseitig (`signUp`, `signInWithPassword`, `updateUser`), Bestätigungs- und Reset-Links über `verifyOtp` mit Token-Hash. Dafür braucht es weder PKCE noch Browser-Client. `@supabase/ssr` wäre die Alternative, nur nach Rückfrage.
- **E8:** Merken im Konto gilt in dieser Runde nur für Events. Orte aus den Guides kommen später in eine eigene Tabelle.
- **E9:** Vergangene gemerkte Events bleiben im Konto. Die Merkliste zeigt sie eingeklappt unter „Vorbei“, und sie dienen den Empfehlungen, sensible ausgenommen (E13).
- **E10:** Der Schalter `KONTEN_AKTIV` steuert alle sichtbaren Teile **und die Konto-Routen**. Ist er aus, antwortet jede Route unter `/api/konto/*` mit 404, und es gibt keine Links und keine Hinweise. Der Code kann damit ausgeschaltet live gehen, bevor Postfach und Datenschutztext fertig sind. Jeder Push ist ein Live-Deploy, und ohne die 404 wären die Routen aus Schritt 4 sonst schon erreichbar.
- **E11:** Ein Konto wird gelöscht nach 24 Monaten ohne Nutzung, mit Warnmail 30 Tage vorher (Abschnitt 9.3). Unbestätigte Konten werden nach 48 Stunden gelöscht, bestätigte Konten ohne Alters-Bestätigung nach 7 Tagen (nach der rechtlichen Einschätzung, vorher 30).

---

## 3. Architektur

### 3.1 Überblick

```
Browser ──► unser Next-Server (Route-Handler /api/konto/*) ──► Supabase Auth (Passwort, Bestätigung, Reset, Sitzung)
   │                    │                                      └► Postgres mit RLS (profiles, merkliste, einwilligungen)
   │                    └► Mail: Supabase Auth verschickt über SMTP unseres eigenen Servers (E3)
   └ öffentliche Seiten: unverändert gecacht, kein Cookie, kein Sitzungs-Lesen
```

- Der Browser spricht **nie direkt** mit Supabase. Abschnitt 9 der Datenschutzerklärung bleibt damit wahr.
- Alle persönlichen Daten laufen über `/api/konto/*`. Die Seiten unter `/konto/*` sind statische Hüllen (noindex) mit Client-Komponenten, die diese Routen abfragen. **Kein Server Component liest `cookies()`.** Damit gibt es auch kein `use cache: private`, keine Suspense-Löcher im Layout und keine persönlichen Daten in einem Server-Cache.
- Dieselben Routen bedienen später die App, mit `Authorization: Bearer` statt Cookie (3.3).

### 3.2 Sitzung und Cookies
- Nach erfolgreicher Anmeldung mit Passwort, nach dem Klick auf den Bestätigungslink und nach dem Klick auf den Reset-Link liefert Supabase eine Sitzung aus Access-Token (JWT, Standard 1 Stunde) und Refresh-Token.
- **`ddd_sitzung`**: Access- und Refresh-Token als base64url-JSON. `HttpOnly`, `Secure` (außer auf localhost), `SameSite=Lax`, **`Path=/api/konto`**, `Max-Age` 30 Tage, verlängert bei jeder Erneuerung. Wegen des Pfads schickt der Browser das Cookie bei keinem Seitenaufruf mit, nur an die Konto-Routen. Die Größe von etwa 1,5 KB liegt unter 4 KB. Beim Bau wird gemessen; bei mehr als 3,5 KB werden Access und Refresh auf zwei Cookies verteilt.
- **`ddd_konto`**: ein reiner Anzeige-Hinweis. Nicht `HttpOnly`, `Path=/`, gleiche Laufzeit, Inhalt nur `1` (angemeldet, Mindestalter bestätigt) oder `0` (angemeldet, Alters-Häkchen fehlt, nur bei Konten am Registrierungsformular vorbei, 5.3). Der Server setzt ihn bei jeder Konto-Antwort passend zu `mindestalter_bestaetigt_am`. Die Oberfläche weiß damit ohne Netzwerkabfrage, ob sie die Konto-Ansicht zeigt. Bei `0` bleibt die Merkliste im Gerätemodus (5.4 Schritt 0a). Ein falscher Hinweis schadet nicht: Antwortet die API mit 401, löscht der Client ihn.
- **Erneuern:** `lib/konto/sitzung.ts` liest das Cookie. Ist das `exp` im Access-Token weniger als 60 Sekunden entfernt, erneuert ein **anfragebezogener** Auth-Client (`persistSession: false`, `autoRefreshToken: false`, kein Timer, siehe 1.4) mit `refreshSession` und setzt das Cookie neu. Zwei Anfragen, die gleichzeitig erneuern, nutzen zwei Clients, und die Bibliothek fasst nur innerhalb eines Clients zusammen. Das Reuse-Fenster von Supabase (Standard 10 Sekunden ab der ersten Einlösung) deckt also nur Anfragen ab, die **innerhalb von 10 Sekunden** kommen. Kommt die zweite später mit dem alten Refresh-Token, widerruft Supabase die ganze Token-Familie. Dann löscht die Route beide Cookies und antwortet mit 401, und der Client meldet lokal ab (5.5). Eine erneute Anmeldung ist nötig, verloren geht nichts. Der Client verringert das Risiko: Alle schreibenden Merklisten-Anfragen laufen über die eine Warteschlange und Sperre aus 5.5, also nie zwei gleichzeitig aus einem Browser.
- **Abmelden:** `signOut` mit Geltung „dieses Gerät“ oder „alle Geräte“ (`scope: 'global'`). Beide Cookies werden gelöscht und der lokale Merklisten-Spiegel geleert (5.6).
- **Nach einem Passwortwechsel** (im Konto oder über „Passwort vergessen“) meldet der Server alle **anderen** Sitzungen ab (`signOut({ scope: 'others' })`). Wer ein fremdes Gerät mit offener Sitzung vergessen hat, ist damit dort sofort draußen.
- Die Cookies sind technisch notwendig (§ 25 Abs. 2 Nr. 2 TDDDG). Das Cookie-Banner bleibt unverändert.

### 3.3 Token für die spätere App
- Konten liegen in Supabase Auth. Die App meldet sich mit derselben Mailadresse und demselben Passwort an. Registrierung, Bestätigung und „Passwort vergessen“ kann die App für den Start im Browser öffnen (unsere Seiten), Deep Links sind dafür nicht nötig.
- `sitzungAusAnfrage()` liest das Cookie **oder** `Authorization: Bearer <access>`. Mit Bearer entfällt die Origin-Prüfung (11.2). Eine Route, die Token für die App als JSON ausgibt, und das Erneuern für die App kommen mit dem App-Plan. Dieser Plan sorgt nur dafür, dass nichts fest am Cookie hängt.
- RLS schützt die Tabellen auch dann, wenn die App später direkt mit Supabase spricht.

### 3.4 Welcher Client wofür
- **Nutzer-Client** (pro Anfrage): anon-Key plus Header `Authorization: Bearer <access>`, ohne Sitzung und ohne Timer. Alle Lese- und Schreibzugriffe auf Konto-Daten laufen darüber. RLS ist damit die zweite Mauer hinter der API-Prüfung, und PostgREST prüft das JWT.
- **Dienst-Client** (`dienstClient()`, vorhanden): für `auth.admin.deleteUser` und `konto_protokoll_loeschen` (Kontolöschung), den Aufräumjob, spätere Summen-Statistiken und **alle Einwilligungen**. `mindestalter_bestaetigt_am`, `personalisierung`, `sensible_events_erlaubt` und `analyse_erlaubt` sowie die Zeilen in `einwilligungen` schreiben nur die Routen `abschluss`, `einstellungen` und `vorlieben` (5.3, 5.7) mit dem Dienst-Client, für die Nutzer-ID aus der geprüften Sitzung, je Angabe in **einem** Aufruf (RPC `einwilligung_setzen`, siehe 4.5). Bei der Registrierung setzt die Route `registrieren` Alter und Nutzungsbedingungen über denselben Weg (5.1 Schritt 2). Die Routen rufen zuerst `einwilligung_setzen('personalisierung', true)` auf, falls (a) noch nicht gilt, und speichern danach `praeferenzen`. In dieser Reihenfolge ist die CHECK-Bedingung aus 4.1 immer erfüllt. Der Body enthält nur die Angaben und neuen Werte. `textversion` setzt die Route aus Konstanten im Code (je Einwilligung eine, z. B. `interessen-2026-11`, `sensible-events-2026-11`, `analyse-hinweis-2026-11`). Sie gehören zum angezeigten Text, werden bei jeder Textänderung hochgezählt und stehen gleichlautend in `einwilligungstexte` (4.4). Ein Client kann also keinen Nachweis für einen Text erzeugen, den das Formular nie gezeigt hat. So gibt es keine Einwilligung ohne Nachweiszeile, auch nicht, wenn später eine App mit dem JWT direkt bei Supabase schreibt.
- Speicher-Test beim Bau: 1.000 Anfragen gegen `/api/konto/ich`. Der Heap muss stabil bleiben (Lehre aus dem 06.11.2026).

### 3.5 Caching-Regeln (verbindlich)
1. Kein **neues** `cookies()`, `headers()` oder `connection()` in Layout, Kopf, Fuß, Kategorieleiste und öffentlichen Seiten. Das bestehende `connection()` für die Öffnungszeiten (`web/components/ort-detail.tsx`, Zeile 51, hinter einer Suspense-Grenze) bleibt, wie es ist.
2. Persönliche Daten nur aus `/api/konto/*`, Antwort immer `Cache-Control: private, no-store`, wie `antwort()` in `lib/formulare.ts`.
3. Kein `use cache` mit Nutzer-ID oder Mailadresse als Argument oder Tag.
4. Der Merkzustand bleibt rein clientseitig. Der Server-Snapshot `LEER` bleibt.
5. Prüfung: Die Routen-Tabelle von `next build` vorher und nachher ist für alle öffentlichen Routen gleich. `curl -I` auf `/`, `/heute`, eine Eventseite und einen Guide liefert kein `Set-Cookie` und unveränderte Cache-Header.

---

## 4. Datenmodell

### 4.0 Vorab-Prüfung der Rechte (Schritt 1, nur SELECT)
Datei `database/konten_rechte_pruefung_<datum>.sql`. Sie listet auf:
- alle Tabellen in `public` und `storage` mit `relrowsecurity = false`;
- alle Policies, deren Rollen `public` oder `authenticated` enthalten, mit Ausdruck (`qual`, `with_check`), markiert, wenn kein `ist_admin()` und kein `auth.uid()` darin steht;
- alle Tabellenrechte (`information_schema.role_table_grants`) für `anon` und `authenticated` mit INSERT, UPDATE oder DELETE;
- Funktionen mit `SECURITY DEFINER`, die `anon` oder `authenticated` ausführen dürfen.

**Whitelist der gewollten öffentlichen Lesewege** (stehen in der Ausgabe, gelten aber nicht als Lücke): `events` (`abgelehnt = FALSE OR ist_admin()`), `event_seo_entscheidungen` (`USING (true)`, gelesen von `web/proxy.ts` mit dem anon-Key), `reihen` (`USING (true)`), `orte` (`USING (aktiv = true)`). Die Whitelist gilt nur für SELECT. Jede Schreib-Policy und jedes Schreibrecht ohne `ist_admin()` bzw. `service_role` ist ein Treffer.

Jeder Treffer, der nicht ausdrücklich gewollt ist, wird **vor** dem Einschalten öffentlicher Registrierungen per Härtungs-SQL geschlossen.

**Ergebnis vom 16.11.2026** (`database/konten_rechte_pruefung_2026-11-16.sql`, vom Auftraggeber ausgeführt):
- Keine Tabelle in `public` oder `storage` ohne RLS.
- Alle Policies für `public`, `anon` oder `authenticated` sind an `ist_admin()`, `auth.uid()` oder `service_role` gebunden oder stehen als SELECT auf der Whitelist. Das hat Claude an den vollständigen Ausdrücken im Ergebnis nachgesehen, nicht nur an der Bewertungsspalte: Keine Policy enthält `IS NOT NULL`, `true` neben einer Bindung oder einen Bucket-Filter mit `OR`.
- **Keine öffentlichen Schreibwege mehr.** Die drei INSERT-Policies aus `meldungen_newsletter_2026-11-05.sql` („Newsletter anmelden“, „Event melden“, „Meldungsbild hochladen“) hat `meldungen_haertung_2026-11-05.sql` entfernt, samt INSERT-Recht für `anon` und `authenticated`. Seitdem schreiben `web/app/api/newsletter/route.ts` und `web/app/api/event-melden/route.ts` serverseitig mit dem Service-Key. Der Live-Lauf bestätigt das: Keine der drei Policies ist vorhanden, und `anon` hat auf beiden Tabellen kein Recht. **Taucht eine davon bei einer Wiederholung auf, ist das eine LÜCKE** (Rückfall auf den alten Stand), keine gewollte Ausnahme.
- **Bewertungsformel verschärft** (zweite Fassung der Prüfdatei, nach Cursor-Prüfung): Die erste Fassung wertete jede Policy als „ok“, deren Text `ist_admin`, `auth.uid` oder `service_role` enthielt. Damit wären auch `auth.uid() IS NOT NULL` oder `ist_admin() OR true` durchgerutscht. Jetzt geht ein Ausdruck nur noch als gebunden durch, wenn er nach dem Ersetzen der bekannten Bindungen vollständig aufgeht. Erlaubt sind dann nur `ist_admin()`, `auth.role() = 'service_role'`, `<spalte> = auth.uid()`, deren `OR`-Verknüpfung und ein Bucket-Filter mit `AND`. Geprüft werden je Befehl genau die Ausdrücke, die Postgres anwendet. Ein INSERT ohne `WITH CHECK` gilt als offen. Alles andere erscheint als „LÜCKE prüfen“, mit dem nicht aufgegangenen Rest in der Spalte `detail`. Die Wiederholungen vor Schritt 8 laufen mit dieser Fassung. **Kontrolllauf am 16.11.2026: keine LÜCKE.**
  - Alle Admin-, Profil-, Storage- und `orte_admin_alles`-Policies gehen vollständig auf.
  - Nur die vier Whitelist-Lesewege bleiben übrig: `events`, `event_seo_entscheidungen`, `reihen` und `orte`. Bei ihnen geht `true`, `aktiv = true` bzw. `abgelehnt = false or #b` nicht auf, und sie stehen deshalb ausdrücklich als „gewollter öffentlicher Leseweg“.
- `authenticated` hat UPDATE und DELETE auf `event_meldungen` und `newsletter_anmeldungen`. Das ist gewollt (Admin-Oberfläche), die Policies lassen nur Admins durch. Gleiches gilt für Schreibrechte in `storage`.
- Bucket `event-bilder` öffentlich (gewollt, Event-Bilder), `event-meldungen` privat.
- `ist_admin()` und `profil_anlegen()` sind die einzigen SECURITY-DEFINER-Funktionen mit Aufrufrecht, beide gewollt.
- **Einziger Treffer:** `anon` und `authenticated` haben die Supabase-Standardrechte TRUNCATE, REFERENCES und TRIGGER auf `events`, `event_seo_entscheidungen`, `orte`, `profiles`, `reihen`, `scraper_ergebnisse` und `scraper_laeufe`. TRUNCATE umgeht RLS, ist aber über die Supabase-API nicht erreichbar, und beide Rollen können sich nicht direkt an der Datenbank anmelden. Heute also nur theoretisch. Kein Code im Repo nutzt diese Rechte. Geschlossen mit `database/konten_haertung_2026-11-16.sql` (entzieht die drei Rechte auf allen Tabellen in `public` und als Standardrecht für künftige Tabellen von `postgres`). Danach läuft die Rechte-Prüfung noch einmal und darf keine „LÜCKE“ mehr zeigen.

**Härtung ausgeführt und zweite Prüfung, 16.11.2026: keine LÜCKE mehr.** Schritt 1 ist abgeschlossen.
- Auf allen bestehenden Tabellen in `public` haben `anon` und `authenticated` kein TRUNCATE, REFERENCES und TRIGGER mehr.
- **Rest, bewusst so gelassen:** Die Standardrechte für Tabellen, die `supabase_admin` künftig in `public` anlegt, enthalten diese drei Rechte weiter. `postgres` darf sie nicht ändern. `supabase_admin` legt in `public` nur bei internen Supabase-Vorgängen Tabellen an; unsere Tabellen legt `postgres` im SQL-Editor an. Gegenmaßnahme: Die Migration aus Schritt 3 setzt für jede neue Tabelle die Rechte ausdrücklich (`REVOKE ALL … FROM anon, authenticated`, danach nur das Nötige, 4.5). **Die Rechte-Prüfung läuft nach Schritt 3 und vor dem Einschalten des Schalters (Schritt 8) noch einmal**, damit auch eine fremd angelegte Tabelle auffällt.
- Die verbleibenden Schreibrechte (INSERT, UPDATE, DELETE) von `anon` und `authenticated` auf Tabellen in `public` und `storage` sind Supabase-Standard. RLS ist überall an, und keine Schreib-Policy lässt jemand anderen als Admins, die eigene Person oder `service_role` durch. Ohne passende Policy, etwa bei `storage.buckets` oder INSERT/DELETE auf `profiles`, ist Schreiben gesperrt.
- **`profiles` heute:** Angemeldete dürfen ihr eigenes Profil ändern. Die Rolle schützt der Trigger `profil_vor_update` (nur Admins ändern Rollen), Selbstbeförderung ist also nicht möglich. `praeferenzen`, `anzeigename` und `erstellt_am` sind auf der eigenen Zeile heute frei änderbar (`aktualisiert_am` setzt der Trigger immer neu). Solange die Registrierung aus ist, betrifft das nur die Admin-Konten und ändert keine Rechte. Die Spaltenrechte aus 4.1 kommen mit Schritt 3, vor dem Einschalten der Registrierung.

### 4.1 `profiles` erweitern
```sql
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS onboarding_fertig_am       TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS mindestalter_bestaetigt_am TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS personalisierung           BOOLEAN NOT NULL DEFAULT FALSE, -- E12a: nur mit Einwilligung (a)
  ADD COLUMN IF NOT EXISTS sensible_events_erlaubt    BOOLEAN NOT NULL DEFAULT FALSE, -- E13: nur mit ausdrücklicher Einwilligung (b)
  ADD COLUMN IF NOT EXISTS analyse_erlaubt            BOOLEAN NOT NULL DEFAULT FALSE, -- E4: true erst nach dem Hinweis (Abschlussseite) ohne Widerspruch
  ADD COLUMN IF NOT EXISTS nutzungsbedingungen_version TEXT,                          -- E14: akzeptierte Fassung
  ADD COLUMN IF NOT EXISTS geburtstagsmail            BOOLEAN NOT NULL DEFAULT FALSE, -- E15: Einwilligung (d)
  ADD COLUMN IF NOT EXISTS geburtsdatum               DATE,                           -- E15: nur mit (d)
  ADD COLUMN IF NOT EXISTS geburtstagsmail_zuletzt    DATE,                           -- Jahr des letzten Versands, gegen Doppelversand
  ADD COLUMN IF NOT EXISTS unter16_gesperrt_am        TIMESTAMPTZ,                    -- E15: Geburtsdatum unter 16 angegeben, Löschung beim nächsten Lauf
  ADD COLUMN IF NOT EXISTS letzte_aktivitaet_am       TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS merkliste_begonnen_am      TIMESTAMPTZ; -- erster Eintrag je, setzt ein Trigger (4.3)
ALTER TABLE public.profiles ADD CONSTRAINT praeferenzen_form
  CHECK (jsonb_typeof(praeferenzen) = 'object' AND pg_column_size(praeferenzen) <= 8192);
-- Interessen gibt es nur mit Einwilligung (E12); auch ein direkter Schreibversuch ohne sie scheitert
ALTER TABLE public.profiles ADD CONSTRAINT praeferenzen_nur_mit_einwilligung
  CHECK (personalisierung OR praeferenzen = '{}'::jsonb);
-- Geburtsdatum nur mit Einwilligung (d), plausibel ab 1900
ALTER TABLE public.profiles ADD CONSTRAINT geburtsdatum_nur_mit_einwilligung
  CHECK ((geburtstagsmail AND geburtsdatum IS NOT NULL) OR (NOT geburtstagsmail AND geburtsdatum IS NULL));
ALTER TABLE public.profiles ADD CONSTRAINT geburtsdatum_plausibel
  CHECK (geburtsdatum IS NULL OR geburtsdatum >= DATE '1900-01-01');
```
- Die Altersgrenze (mindestens 16 Jahre) prüft `geburtstag_setzen` (4.5) mit dem aktuellen Datum in `Europe/Berlin`. Eine CHECK-Bedingung darf `current_date` nicht verwenden.
- Bestehende Profile (Admins) haben `praeferenzen = '{}'`, die Bedingung gilt also sofort. Die Migration prüft das vorher mit einer Abfrage und bricht sonst mit Meldung ab.
- `letzte_aktivitaet_am` setzt **jede** angemeldete Konto-Route (Merken, Merkliste, Vorlieben, Export, `ich` …), höchstens einmal am Tag je Konto. Der Merker dafür liegt im Speicher, der Schreibbefehl lautet `UPDATE … WHERE letzte_aktivitaet_am IS NULL OR letzte_aktivitaet_am < current_date`. `auth.users.last_sign_in_at` reicht nicht, weil es beim bloßen Erneuern des Tokens nicht wächst. Wer zwei Jahre lang nur Herzen setzt, gälte sonst als inaktiv. Für `NULL` (Konto nie benutzt) rechnet der Inaktivitäts-Job mit `erstellt_am`. So steht es auch in der Erklärung.
- Rechte: `REVOKE UPDATE ON public.profiles FROM authenticated`, dann nur `GRANT UPDATE (anzeigename, praeferenzen, onboarding_fertig_am, letzte_aktivitaet_am)`. `rolle`, `id`, `erstellt_am`, `merkliste_begonnen_am`, `nutzungsbedingungen_version` und die Einwilligungs-Spalten (`mindestalter_bestaetigt_am`, `personalisierung`, `sensible_events_erlaubt`, `analyse_erlaubt`, `geburtstagsmail`, `geburtsdatum`, `geburtstagsmail_zuletzt`, `unter16_gesperrt_am`) sind mit dem Nutzer-JWT nicht änderbar, nur über den Dienst-Client (3.4) (auch bei der Registrierung, 5.1 Schritt 2). Der bestehende Trigger bleibt als zweite Sperre. Laut 1.3 ändert das Dashboard `profiles` nicht, Rollen setzt der SQL-Editor. Das ist vor dem Ausführen noch einmal zu prüfen.

### 4.2 Format von `praeferenzen` (Version 1)
```json
{ "version": 1,
  "kategorien": ["musik", "kultur"],
  "unterkategorien": ["musik/jazz", "kultur/comedy"],
  "stadtteile": ["bilk", "flingern-nord"],
  "merkmale": ["kostenlos", "mit-kindern", "abends", "tagsueber", "wochenende"],
  "orte": ["restaurants-cafes", "kneipen-bars", "clubs", "spielplaetze"] }
```
- Alles ist optional, eine leere Liste heißt „keine Vorliebe“. Der Server prüft gegen Whitelists und lässt Unbekanntes still weg: `KATEGORIEN` ohne `sonstiges`, `unterkategorien.json` (Slugs werden laut Datei nie umbenannt), `stadtteilSlug()` der bekannten Stadtteile inklusive Neuss und Ratingen, `GuideHub`. Jede Liste hat höchstens 60 Einträge.
- Ändert sich die Taxonomie, übersetzt `version` auf dem Lesepfad.

### 4.3 `merkliste`
```sql
CREATE TABLE public.merkliste (
  nutzer_id  UUID NOT NULL REFERENCES public.profiles (id) ON DELETE CASCADE,
  event_id   UUID NOT NULL REFERENCES public.events (id)   ON DELETE CASCADE,
  gemerkt_am TIMESTAMPTZ NOT NULL DEFAULT now(),
  quelle     TEXT NOT NULL DEFAULT 'konto' CHECK (quelle IN ('konto', 'geraet', 'app')),
  PRIMARY KEY (nutzer_id, event_id)
);
CREATE INDEX merkliste_event_idx ON public.merkliste (event_id);  -- für Statistik und Löschen von Events
```
- Ein BEFORE-INSERT-Trigger `merkliste_vor_insert()` begrenzt auf **500 Einträge** je Konto und meldet sonst `merkliste_voll`. Derselbe Trigger setzt `profiles.merkliste_begonnen_am = now()` für `NEW.nutzer_id`, wenn es noch leer ist. Die Funktion ist `SECURITY DEFINER` mit `SET search_path = ''`. Der Nutzer hat kein Spaltenrecht auf `merkliste_begonnen_am` (4.1), als Aufrufer liefe das `UPDATE` sonst ins Leere oder bräche das Merken ab. Sie schreibt nur diese eine Spalte und nur für `NEW.nutzer_id`. Wird der INSERT danach abgewiesen (Grenze, Policy, `ON CONFLICT DO NOTHING` bei schon gemerktem Event), rollt die Transaktion bzw. die Anweisung das `UPDATE` mit zurück. Ein `INSERT … ON CONFLICT DO NOTHING` feuert den BEFORE-Trigger auch für ein schon gemerktes Event. Deshalb prüft der Trigger zuerst, ob `(nutzer_id, event_id)` schon existiert, und tut dann nichts: keine Grenzprüfung (sonst meldete ein volles Konto beim erneuten Merken fälschlich `merkliste_voll`), kein `UPDATE`. Der Wert bleibt auch dann, wenn die Merkliste später wieder leer wird. Daran erkennt 5.4, ob ein leeres Konto „noch nie“ oder „wieder“ leer ist. Alle Schreibwege (Herz, Übernahme, später die App) gehen über diesen INSERT und setzen den Wert damit gleich.
- Merken (`INSERT`) verlangt zusätzlich `mindestalter_bestaetigt_am IS NOT NULL` im eigenen Profil. Ein Konto, das nur über den anon-Key bei Supabase angelegt wurde und das Alters-Häkchen nie gesetzt hat, kann also nichts speichern (11.1). **Umsetzung (Schritt 3, Abweichung zur Freigabe, vom Auftraggeber bestätigt am 16.11.2026):** Die Prüfung steht im Trigger `merkliste_vor_insert` (Fehler `mindestalter_fehlt`), nicht als `EXISTS` in der Policy `WITH CHECK`.
  - Für Nutzer wirkt das gleich: Ein gesperrtes Konto oder eines ohne Häkchen kann nichts speichern.
  - Die Prüfung gilt so für jeden Schreibweg, auch `service_role` und die spätere App.
  - Die INSERT-Policy bleibt eine reine Bindung `nutzer_id = auth.uid()`, die die verschärfte Rechte-Prüfung (4.0) eindeutig als gebunden erkennt. Mit einem `EXISTS` hätte sie dauerhaft „prüfen“ gezeigt.
  - Die Route übersetzt `mindestalter_fehlt` in 403 `mindestalter_fehlt` (5.4 Schritt 10).
- **Sensible Events (E13):** Derselbe Trigger prüft, ob `NEW.event_id` in `event_sensibel` (4.8) steht. Ist das so und hat das Profil `sensible_events_erlaubt = false`, bricht er mit dem Fehlercode `nur_geraet` ab. Diese Sperre gilt für jeden Schreibweg, auch für eine spätere App, die direkt mit Supabase spricht. Die Route übersetzt den Code in die neutrale Antwort aus 5.8.
- `quelle = 'geraet'` markiert Einträge aus der Übernahme (5.4). Die Auswertung kann sie trennen.
- Für ein späteres „gemerkt / wieder entfernt“-Protokoll gibt es in dieser Runde keine Tabelle. Die Analyse kennt den Bestand und `gemerkt_am`.

### 4.4 `einwilligungen` (Nachweis, Art. 7 Abs. 1 DSGVO)
```sql
CREATE TABLE public.einwilligungen (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nutzer_id   UUID NOT NULL REFERENCES public.profiles (id) ON DELETE CASCADE,
  art         TEXT NOT NULL CHECK (art IN ('mindestalter', 'nutzungsbedingungen', 'personalisierung', 'sensible_events', 'analyse', 'geburtstagsmail')),
  erteilt     BOOLEAN NOT NULL,          -- bei 'analyse': false = Widerspruch
  textversion TEXT NOT NULL REFERENCES public.einwilligungstexte (version),
  handlung    TEXT NOT NULL CHECK (handlung IN ('registrierung', 'abschlussseite', 'konto_schalter', 'interessen_aendern', 'abmeldelink', 'altersgrenze')),
  zeitpunkt   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Archiv der gezeigten Texte (Nachweis nach der rechtlichen Einschätzung, Frage 8)
CREATE TABLE public.einwilligungstexte (
  version    TEXT PRIMARY KEY CHECK (length(version) <= 40),   -- z. B. 'sensible-events-2026-11'
  art        TEXT NOT NULL,
  zweck      TEXT NOT NULL,
  sprache    TEXT NOT NULL DEFAULT 'de',
  text       TEXT NOT NULL,                                    -- vollständiger angezeigter Wortlaut
  gueltig_ab TIMESTAMPTZ NOT NULL DEFAULT now()
);
```
(In der SQL-Datei wird `einwilligungstexte` vor `einwilligungen` angelegt.)
- Jedes Umschalten im Konto ergibt eine neue Zeile. Geschrieben wird nur über `einwilligung_setzen` (4.5) (auch bei der Registrierung, 5.1 Schritt 2), nie mit dem Nutzer-JWT. Es gibt kein UPDATE und kein DELETE. Die Zeilen verschwinden mit dem Konto. Eine IP-Adresse wird nicht gespeichert, die Einschätzung hält sie nicht für nötig.
- **`einwilligungstexte` ist unveränderbar:** Ein Trigger verbietet UPDATE und DELETE (auch für `service_role`, nur `postgres` im SQL-Editor kann sie bewusst abschalten). Neue Fassungen kommen als neue Zeile per SQL-Datei, die der Auftraggeber ausführt. Der Code hat dieselben Texte als Konstanten. Ein Test in 16.1 vergleicht beide über eine Prüfsumme, die in der SQL-Datei als Kommentar steht. RLS ist an, Lesen dürfen `anon` und `authenticated` (die Texte sind öffentlich). Schreiben darf niemand über die API.
- `handlung` hält fest, wo die Einwilligung gegeben wurde (Nachweis der tatsächlichen Handlung).

### 4.5 RLS und Rechte
- `merkliste`: RLS an. `REVOKE ALL FROM anon, authenticated`, danach `GRANT SELECT, INSERT, DELETE TO authenticated`. Die Policies prüfen `nutzer_id = (SELECT auth.uid())` (`USING` bzw. `WITH CHECK`). UPDATE gibt es nicht.
- `einwilligungen`: RLS an, nur `GRANT SELECT TO authenticated` mit Policy auf das eigene Konto. Kein INSERT für `authenticated`.
- **`public.einwilligung_setzen(nutzer UUID, art TEXT, erteilt BOOLEAN, textversion TEXT)`**: `SECURITY DEFINER`, `SET search_path = ''`, `REVOKE ALL … FROM PUBLIC, anon, authenticated`, `GRANT EXECUTE … TO service_role`. Sie bekommt zusätzlich `handlung` und setzt in einer Transaktion die passende Spalte in `profiles` (`mindestalter` → `mindestalter_bestaetigt_am = now()` bzw. `NULL`, `nutzungsbedingungen` → `nutzungsbedingungen_version = textversion`, `personalisierung` → `personalisierung`, `sensible_events` → `sensible_events_erlaubt`, `analyse` → `analyse_erlaubt`, `geburtstagsmail` **nur mit `erteilt = false`** → `geburtstagsmail = false, geburtsdatum = NULL` in einer Anweisung; `erteilt = true` lehnt die Funktion ab, das setzt allein `geburtstag_setzen`) und schreibt die Zeile in `einwilligungen`. `mindestalter` mit `erteilt = true` lehnt sie ab, wenn `unter16_gesperrt_am` gesetzt ist (siehe `geburtstag_setzen`). **Widerruf der Einwilligung für sensible Events:** In derselben Transaktion löscht sie alle Zeilen in `merkliste` dieses Kontos, deren Event in `event_sensibel` steht, und gibt deren IDs zurück. Die Route reicht sie an das Gerät weiter, auf dem widerrufen wurde. Dort bleiben sie lokal (5.8). Beim Widerruf der Personalisierung steht beides in **einer einzigen UPDATE-Anweisung**: `SET personalisierung = false, praeferenzen = '{}'`. Die CHECK-Bedingung aus 4.1 wird sofort geprüft und schlüge bei zwei getrennten Anweisungen fehl.
- **`public.geburtstag_setzen(nutzer UUID, datum DATE, textversion TEXT, handlung TEXT)`** (E15): `SECURITY DEFINER`, `SET search_path = ''`, nur `service_role`.
  - **Altersprüfung, festgelegt:** `datum > (timezone('Europe/Berlin', now()))::date - interval '16 years'` heißt „unter 16“. Der 16. Geburtstag selbst zählt als 16. Ein Datum in der Zukunft ist ebenfalls „unter 16“.
  - Bei „unter 16“ speichert sie das Datum **nicht** und setzt in einer Transaktion: `mindestalter_bestaetigt_am = NULL`, `unter16_gesperrt_am = now()` (neue Spalte, 4.1) und eine Nachweiszeile `mindestalter`, `erteilt = false`, `handlung = 'altersgrenze'`. Danach antwortet sie mit `unter_16`.
  - **Sperre statt neuem Häkchen:** Ist `unter16_gesperrt_am` gesetzt, lehnt `einwilligung_setzen` ein erneutes `mindestalter = true` ab, und `/konto/willkommen` bietet das Häkchen nicht mehr an. Das Konto kann nichts speichern (Policy 4.3, Routen 403). Die Meldung lautet: „dies.das-Konten gibt es ab 16 Jahren. Ihr Konto wird daher gelöscht.“ Gelöscht wird **beim nächsten Lauf des Aufräumjobs** ab dem Zeitpunkt der Sperre, nicht nach `created_at` (9.3). Aufheben kann die Sperre nur ein Admin per SQL, etwa nach einem Tippfehler, den die Person per Mail meldet.
  - Sonst setzt sie in **einer** Anweisung `geburtsdatum = datum, geburtstagsmail = true` und schreibt die Nachweiszeile `geburtstagsmail`, `erteilt = true`.
  - Ändern des Datums im Konto ruft dieselbe Funktion auf.
- `anon` bekommt auf keine der beiden Tabellen Rechte.
- **Summen für die Analyse:** `public.merk_statistik(von DATE, bis DATE)`, `SECURITY DEFINER`, `SET search_path = ''`. Sie läuft nur, wenn `ist_admin()` stimmt, sonst gibt es eine Exception. Sie liefert `event_id`, Anzahl und erstes/letztes `gemerkt_am`, **nur aus Konten mit `analyse_erlaubt = true`** (kein Widerspruch) und **nie für Events in `event_sensibel`** (E4, E13), nie eine Nutzer-ID. Neue Funktionen darf in Postgres standardmäßig `PUBLIC` ausführen, deshalb zuerst `REVOKE ALL ON FUNCTION public.merk_statistik(DATE, DATE) FROM PUBLIC, anon`, dann `GRANT EXECUTE … TO authenticated`, wie bei `ist_admin()` in `auth_rollen.sql`. Die Admin-Prüfung steht als erste Anweisung der Funktion vor jedem Lesen. Genutzt wird sie in Phase 3 (Dashboard).
- Jede neue Funktion dieser Migration hat dieselbe Form: `SECURITY DEFINER` nur, wo nötig, immer `SET search_path = ''` und voll qualifizierte Namen (`public.…`, `auth.…`), zuerst `REVOKE ALL ON FUNCTION … FROM PUBLIC, anon, authenticated`, dann nur das nötige `GRANT`. Im Einzelnen:
  - `merk_statistik` → `authenticated` (Admin-Prüfung innen).
  - `merkliste_vor_insert()` (Trigger, `SECURITY DEFINER`) → `GRANT EXECUTE` an `authenticated`. Das ist unschädlich, denn eine Funktion mit Rückgabetyp `trigger` lässt sich nicht direkt aufrufen. Es stellt sicher, dass ein INSERT als Nutzer nicht an `permission denied for function` scheitert, falls Postgres das Recht beim Auslösen prüft. Der Test in 16.2 läuft deshalb als Nutzer A, nicht als `postgres`.
  - `einwilligung_setzen`, `geburtstag_setzen` und `konto_protokoll_loeschen` → nur `service_role`. (Die Funktion `konto_status` der vierten Fassung entfällt mit E2. Beim Passwort-Weg ist der Typ jedes Links bekannt, 5.1.)
  - Die Trigger-Funktionen auf `events` und `event_sensibel` (4.8) → kein `GRANT`. `profil_anlegen()` aus `auth_rollen.sql` bleibt unverändert (5.1).

### 4.6 Löschen
- Wird ein Konto gelöscht (`auth.admin.deleteUser`), räumen die Fremdschlüssel nacheinander `profiles`, `merkliste` und `einwilligungen` ab. Summen werden nicht gespeichert, sondern bei Bedarf gezählt. Ein gelöschtes Konto zählt danach also nicht mehr mit. Das ist gewollt.
- `auth.audit_log_entries` enthält je nach Ereignis Nutzer-ID und Mailadresse im Payload, und `deleteUser` räumt diese Zeilen nicht ab. **Beim Löschen eines Kontos** ruft die Route vor `deleteUser` die Funktion `public.konto_protokoll_loeschen(nutzer UUID)` auf (`SECURITY DEFINER`, `SET search_path = ''`, nur `service_role`, siehe 4.5). Der Aufrufer übergibt nur die ID. Die Mailadresse bestimmt die Funktion selbst: aus `auth.users` zur ID, und wenn es dort keine Zeile mehr gibt (laufender Job, siehe unten), aus den Audit-Zeilen derselben ID (`traits.user_email` bzw. `actor_username`). Der Aufrufer kann keine fremde Adresse einschleusen. Der Abgleich über die **Mailadresse** läuft nur, wenn kein **anderes** lebendes Konto in `auth.users` dieselbe Adresse trägt. Hat sich jemand später mit derselben Adresse neu registriert, löscht die Funktion nur Zeilen per ID und Zeilen mit dieser Adresse, die älter sind als `created_at` des neuen Kontos. Sie löscht alle Zeilen, deren `payload->>'actor_id'` oder `payload->'traits'->>'user_id'` die Nutzer-ID ist oder deren `payload->>'actor_username'` bzw. `payload->'traits'->>'user_email'` die Mailadresse ist. Die genauen Payload-Felder werden in Schritt 1 mit einer SELECT-Abfrage auf echte Zeilen festgestellt, bevor die Funktion geschrieben wird.
- **Laufend:** Der Aufräumjob ruft dieselbe Funktion für jede Nutzer-ID, die in Audit-Zeilen vorkommt, aber nicht mehr in `auth.users` steht, z. B. gelöschte unbestätigte Konten. Ohne Zeile in `auth.users` löscht die Funktion trotzdem per ID und holt die Mail aus den Audit-Zeilen (siehe oben). Sie bricht dort nicht ab. Zeilen bestehender Konten löscht er **nicht**, auch nicht von Admins.
- **Ob in `auth.audit_log_entries` gelöscht werden darf, klärt Schritt 1.** Abfrage `has_table_privilege(<Eigentümer der späteren Funktion>, 'auth.audit_log_entries', 'DELETE')` und ob RLS auf der Tabelle Zeilen versteckt. Danach ein Probelauf **als derselbe Eigentümer** (im SQL-Editor `postgres`, Eigentümer bei Supabase-Funktionen ist in der Regel `postgres`; das wird mit `SELECT proowner::regrole` geprüft) in einer Transaktion: `BEGIN;` eine gekennzeichnete Testzeile einfügen (`payload = '{"ddd_test": true}'`), genau diese löschen, Zahl der gelöschten Zeilen prüfen, `ROLLBACK;`. Eine echte Zeile wird dabei nie berührt. Darf er es nicht, gibt es keinen eigenen Löschweg. (Die erste Fassung sah dafür einen Job mit 30-Tage-Frist vor, der aber dasselbe Recht gebraucht hätte.) Dann gilt: Der Auftraggeber fragt beim Supabase-Support die Aufbewahrungsdauer der Auth-Protokolle ab, und die Erklärung nennt sie als Protokoll zur Sicherheit des Dienstes (Art. 6 Abs. 1 lit. f). Laut rechtlicher Einschätzung (Frage 5) ist das zulässig, wenn Zweck, Verantwortlichkeit und eine **tatsächlich begrenzte** Frist feststehen. Ein bloßer Hinweis in der Erklärung reicht nicht. Ist die Frist bei Supabase nicht begrenzt oder nicht in Erfahrung zu bringen, wird nicht eingeschaltet, sondern neu entschieden. Welcher Weg gilt, steht nach Schritt 1 fest. Vorher wird der Schalter nicht eingeschaltet.
- **Ergebnis von Schritt 1 (16.11.2026):**
  - `postgres` darf in `auth.audit_log_entries` lesen, einfügen und löschen. RLS ist an, Eigentümer der Tabelle ist `supabase_auth_admin`, Eigentümer von `ist_admin()` ist `postgres`. Der Probelauf als `postgres` hat die Testzeile gefunden und gelöscht („gelöscht: 1“), alles wurde zurückgerollt. **Der eigene Löschweg funktioniert.** `konto_protokoll_loeschen` wird wie oben geschrieben, Eigentümer `postgres`.
  - Die Tabelle hat **0 Zeilen**, obwohl es Admin-Anmeldungen gibt. Belegt ist damit nur: Supabase schreibt die Auth-Protokolle in diesem Projekt heute nicht in diese Tabelle. Vermutlich liegen sie nur in den Plattform-Protokollen (Logs im Dashboard). Was dort steht (IP, Mail, Nutzer-ID) und wie lange, ist nicht belegt und wird in Schritt 2 im Dashboard nachgesehen (Checkliste Teil H). Plattform-Protokolle sind nicht per SQL löschbar; ihre Aufbewahrung ist laut Supabase tarifabhängig.
  - Die Payload-Felder ließen sich ohne Zeilen nicht prüfen. Die Funktion nutzt die Felder aus dem Aufbau von Supabase Auth (`actor_id`, `actor_username`, `traits.user_id`, `traits.user_email`). Sie läuft heute ins Leere und schadet nicht. Sie greift, falls Supabase künftig doch Zeilen schreibt. Kommen in Schritt 4 (Vortest) Zeilen dazu, läuft `konten_audit_pruefung_2026-11-16.sql` noch einmal und bestätigt die Felder.
  - **Folge für Schritt 2:** Der Auftraggeber prüft im Supabase-Dashboard, ob das Schreiben der Auth-Protokolle in die Datenbank aus ist (es bleibt aus: weniger Daten bei uns), und notiert die Aufbewahrungsdauer der Plattform-Protokolle laut Tarif. Dazu sieht er nach, welche Angaben die Auth-Logs im Dashboard enthalten. Die Dauer steht in der Datenschutzerklärung (9.1, 9.4). Ist sie begrenzt, ist die Bedingung aus Frage 5 der rechtlichen Einschätzung erfüllt. Ist sie wider Erwarten nicht zu ermitteln, wird nicht eingeschaltet (siehe oben).
- Admin-Konten (`rolle = 'admin'`) lassen sich über die Website nicht löschen (Meldung „Bitte im Supabase-Dashboard löschen“).

### 4.7 Migration
- Eine Datei `database/konten_<datum>.sql`, wiederholbar (`IF NOT EXISTS`, `DROP POLICY IF EXISTS`), mit Kontrollabfrage am Ende wie in `meldungen_haertung_2026-11-05.sql`.
- Reihenfolge: Erst die Rechte-Prüfung (4.0) und ihre Härtung, dann diese Datei, dann der Deploy mit dem Schalter aus.
- Der Code läuft auch vor der Migration: Ist der Schalter aus, antworten die Konto-Routen mit 404 (E10) und fassen die Tabellen nicht an. Bei angeschaltetem Schalter ohne Tabellen antworten sie mit 503 und „Konten sind gerade nicht verfügbar“. Die anonyme Merkliste läuft weiter.

### 4.8 `event_sensibel` (E13, nur Backend)
```sql
CREATE TABLE public.event_sensibel (
  event_id   UUID PRIMARY KEY REFERENCES public.events (id) ON DELETE CASCADE,
  grund      TEXT NOT NULL CHECK (grund IN ('gesundheit', 'religion', 'sexualitaet', 'politik', 'gewerkschaft', 'herkunft')),
  quelle     TEXT NOT NULL CHECK (quelle IN ('regel', 'ki', 'hand')),
  gesetzt_am TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE public.event_sensibel ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.event_sensibel FROM PUBLIC, anon, authenticated;  -- keine Policy: nur service_role und SECURITY-DEFINER-Funktionen
```
- **Bewusst eine eigene Tabelle, keine Spalte in `events`.** `events` ist für `anon` lesbar (`auth_rollen.sql`). Eine Spalte `sensibel` dort könnte jeder mit dem anon-Key über die Data-API abfragen. Die eigene Tabelle hat keine Rechte für `anon` und `authenticated` und kommt in keiner Antwort der Website vor.
- **Kennzeichnung per Datenbank-Trigger, in derselben Transaktion wie das Event.** Die Pipeline speichert jedes Event in einem eigenen Insert (`database/client.py`, Zeile 331), die Anreicherung überschreibt Titel und Beschreibung später, und `dashboard/meldungen.py` (Zeile 154) legt Events ohne die Pipeline an. Damit kein Weg ein Event ungekennzeichnet sichtbar macht, läuft die Prüfung **in der Datenbank**:
  - `public.sensibel_regeln` (Tabelle: `id` (Identity), `prioritaet INT NOT NULL`, `grund`, `muster`, `kontext_muster` (NULL oder Muster, das zusätzlich treffen muss), `ausnahme_muster` (NULL oder Muster, das den Treffer aufhebt), `aktiv`). RLS an, `REVOKE ALL … FROM PUBLIC, anon, authenticated`, keine Policy. Die Startregeln stehen in 5.8. Die SQL-Datei ist in UTF-8 gespeichert, damit Umlaute in den Mustern stimmen.
  - `public.sensibel_grund(titel TEXT, beschreibung TEXT, ort TEXT) RETURNS TEXT`: `STABLE`, `SET search_path = ''`, prüft die aktiven Regeln mit `~*` **in der Reihenfolge `ORDER BY prioritaet, id`** und gibt den Grund der ersten treffenden Regel zurück oder NULL. `REVOKE ALL ON FUNCTION … FROM PUBLIC, anon, authenticated`, kein `GRANT`. Supabase legt Funktionen in `public` sonst in die Data-API. Sie läuft nur im Trigger und für den Nachtrag als `postgres`.
  - Trigger `events_sensibel_pruefen` `AFTER INSERT OR UPDATE OF titel, beschreibung, ort ON public.events FOR EACH ROW` (`SECURITY DEFINER`, `SET search_path = ''`): Trifft eine Regel und steht die Event-ID nicht in `event_sensibel_ausnahmen`, legt er die Zeile in `event_sensibel` an (`quelle = 'regel'`, `ON CONFLICT DO NOTHING`). Er nimmt nie eine Kennzeichnung zurück. Schlägt der Trigger fehl, schlägt der Insert des Events mit fehl. Es gibt also kein sichtbares, ungekennzeichnetes Event.
  - `public.event_sensibel_ausnahmen (event_id UUID PRIMARY KEY REFERENCES events ON DELETE CASCADE, notiz TEXT, gesetzt_am TIMESTAMPTZ)`: von Hand bestätigte Fehltreffer. Rechte wie `event_sensibel`.
  - Der Trigger wirft bei einem Treffer keine Meldung mit dem Grund. Ein Fehler (z. B. ein kaputtes Muster) landet nur im Pipeline-Log bzw. im Dashboard, nie in einer öffentlichen Antwort. Eine öffentliche Einfüge-Route für Events gibt es nicht.
  - Die Reihe (`reihe:reihen`) fließt nicht ein, weil sie per Fremdschlüssel hängt und der Trigger auf `events` sie nicht ohne Weiteres sieht. Reihentitel stehen in aller Regel auch im Event-Titel.
- **Gebündelte Termine:** Eine Gruppe gibt es in der Datenbank nicht. Gebündelt wird nur auf der Website (`terminSchluessel` in `web/lib/termine.ts`: Titel, Tag, Ort). **Jeder Termin wird nach seinem eigenen Text gekennzeichnet.** Gemerkt wird die ID des gebündelten Eintrags, also des frühesten nicht abgesagten Termins (1.1). Sie gilt nur dann als sensibel, wenn genau diese Zeile trifft. Weichen die Beschreibungen der Termine voneinander ab, kann ein späterer Termin gekennzeichnet sein und der gemerkte nicht. Das wird hingenommen: Titel und Ort sind bei gebündelten Terminen gleich, und die meisten Regeln greifen schon auf den Titel.
- **Folge einer späteren Kennzeichnung** (Text geändert, Regel nachgetragen, von Hand): Ein AFTER-INSERT-Trigger auf `event_sensibel` (`SECURITY DEFINER`, `SET search_path = ''`) löscht die Zeilen dieses Events aus `merkliste` bei allen Konten mit `sensible_events_erlaubt = false`. **Bewusst ohne Rückgabe an die Geräte:** Eine Rückgabe bräuchte eine gespeicherte Zuordnung „Person X hatte sensibles Event Y gemerkt“, also genau die Art-9-Information ohne Einwilligung, die E13 vermeiden soll. Folge: Die Merkung verschwindet beim nächsten Abgleich auf **allen** Geräten dieser Person, nicht nur im Konto (Abschnitt 17). Damit das selten vorkommt: Neue Events werden beim Insert geprüft, der Nachtrag läuft vor dem Einschalten (5.8), und vor jeder Hand-Kennzeichnung oder neuen Regel zeigt eine SQL-Abfrage, wie viele Konten betroffen wären.
- Eine aufgehobene Kennzeichnung (Zeile gelöscht und Event in `event_sensibel_ausnahmen`) hat keine Rückwirkung. Was nur auf Geräten lag, bleibt dort, bis die Person das Herz neu setzt.
- Admins sehen und ändern die Kennzeichnung im Dashboard (Phase 3) oder per SQL. Eine Liste sensibler Events erscheint nie auf der Website.

---

## 5. Abläufe

### 5.1 Registrieren, Anmelden, Passwort (E2)
Seiten: `/konto/anmelden` (oben ein Umschalter „Anmelden“ / „Konto anlegen“), `/konto/bestaetigen` (Landeseite für Bestätigungs- und Reset-Links, 5.2), `/konto/passwort-vergessen`, `/konto/passwort-neu`. Auf jedem Formular mit Mailadresse steht der Hinweis nach Art. 13: „Wir nutzen eure Adresse für die Anmeldung und euer Konto. Mehr dazu in der [Datenschutzerklärung](/datenschutz#konto).“ Jedes Formular hat einen Honeypot wie der Newsletter.

**Passwortregeln** (im Supabase-Dashboard und in unserer Route gleich):
- mindestens 10 Zeichen, höchstens 72 (Grenze von bcrypt). Keine Pflicht zu Sonderzeichen oder Ziffern: Länge schützt besser, und Zwangsregeln führen zu „Passwort1!“.
- Das Formular zeigt die Regel vorher an und hat einen „Anzeigen“-Knopf. `autocomplete="new-password"` bei Registrierung und neuem Passwort, `current-password` beim Anmelden, damit Passwort-Manager mitspielen.
- **Prüfung gegen geleakte Passwörter:** Supabase bietet sie („Leaked password protection“, HaveIBeenPwned) nur im Pro-Tarif. Ist der Tarif da, wird sie eingeschaltet. Sonst bleibt es in dieser Runde bei der Mindestlänge (Abschnitt 19). Eine eigene Abfrage bei HaveIBeenPwned vom Server aus wäre möglich, ohne den Browser zu beteiligen, ist aber ein zusätzlicher Dienst und braucht eine eigene Entscheidung.

**Registrieren**
1. „Konto anlegen“: Mailadresse, Passwort, **Pflicht-Häkchen „Ich bin mindestens 16 Jahre alt.“** (E6, nicht vorangekreuzt) und über dem Knopf der Satz: „Mit ‚Konto anlegen‘ akzeptiert ihr unsere [Nutzungsbedingungen](/nutzungsbedingungen). Wie wir eure Daten verarbeiten, steht in der [Datenschutzerklärung](/datenschutz#konto).“ Dazu ein Link auf die Widerrufsbelehrung in den Nutzungsbedingungen (E14). Ohne Häkchen ist der Knopf gesperrt, und die Route lehnt mit 400 ab.
2. `POST /api/konto/registrieren` → `signUp({ email, password })` serverseitig, **ohne** Alter oder Nutzungsbedingungen in den Metadaten. `raw_user_meta_data` kann jeder mit dem anon-Key frei setzen, daraus wird nie ein Nachweis. Der Trigger `profil_anlegen()` aus `auth_rollen.sql` **bleibt unverändert**: Er legt wie heute nur `id` und `anzeigename` an, ein Fehler in neuem Trigger-Code kann also keine Kontoanlage abbrechen, auch nicht die von Admins.
   **Nachweis von Alter und Nutzungsbedingungen, nur serverseitig:** Die Route setzt den Nachweis **nur für ein Konto, das durch genau diese Anfrage entstanden ist**. Bedingungen:
   - `signUp` liefert ein Nutzerobjekt mit nicht leerer `identities`-Liste;
   - dessen `created_at` liegt, beide als UTC-Zeitpunkt verglichen, im Fenster `Eingang − 60 s ≤ created_at ≤ Eingang + 5 s`. „Eingang“ ist der Zeitpunkt, zu dem die Antwort von `signUp` bei unserem Server ankommt. Die 5 Sekunden fangen eine vorgehende Uhr bei Supabase ab. Liegt `created_at` außerhalb des Fensters, wird kein Nachweis gesetzt, und es greift der Rückfall aus Schritt 7 (Häkchen auf `/konto/willkommen`);
   - `mindestalter_bestaetigt_am` und `nutzungsbedingungen_version` sind im Profil noch leer.

   Dann ruft sie mit dem Dienst-Client zweimal `einwilligung_setzen` auf (`mindestalter` und `nutzungsbedingungen`, `handlung = 'registrierung'`, Versionen aus Konstanten, 3.4). Ein älteres, unbestätigtes Konto, etwa eines, das jemand vorher über den anon-Key angelegt hat, bekommt so keinen Nachweis von einer fremden Person, die nur die Adresse kennt. Es fragt das Häkchen nach der Bestätigung auf `/konto/willkommen` ab und fällt sonst unter die Löschung „bestätigt ohne Alter“ (9.3). Der Vorversuch (Schritt 13) hält für alle drei Fälle fest (neu, unbestätigt wiederholt, bestätigt), ob `identities` leer ist und welches `created_at` zurückkommt. Bei verschleiertem Objekt oder Fehler passiert nichts. Der Nachweis entsteht damit nur auf dem Weg über unser Formular mit gesetztem Häkchen. Wer direkt über den anon-Key registriert, hat kein Alters-Häkchen (11.1). Scheitert der Aufruf, fehlt das Alter, und `/konto/willkommen` fragt es nach der Bestätigung ab (Schritt 7). Verloren geht nichts. Den zusätzlichen Aufruf deckt die Mindestdauer aus Schritt 13 gegen Zeitunterschiede ab.
   Die Antwort der Route: Die Route antwortet in **allen** Fällen gleich: neue Adresse, schon registriert und unbestätigt, schon bestätigt, Fehler von Supabase. Immer Status 200, nie ein Nutzerobjekt und kein Fehlerfeld, immer derselbe Text: „Fast geschafft! Wir haben euch eine Mail geschickt. Bitte bestätigt eure Adresse über den Link darin. Habt ihr euch schon einmal registriert und noch nicht bestätigt, gilt das Passwort von damals.“ Hintergrund: Die Bibliothek gibt die Serverantwort durch (`GoTrueClient.js`, Zeilen 570–572 und 729–784). Für eine bestätigte Adresse kommt je nach Einstellung ein verschleiertes Nutzerobjekt (leere `identities`) oder der Fehler „User already registered“. Für eine unbestätigte Adresse lässt der Auth-Server den Nutzer unverändert, schickt die Bestätigung erneut, und das **zuerst** gesetzte Passwort bleibt gültig. Darum steht der letzte Satz in der Meldung. Ein echter Ausfall (z. B. Supabase nicht erreichbar) wird nur geloggt. Der Nutzer sieht dieselbe Meldung und kann „Mail erneut senden“ nutzen.
3. Die Mail „Confirm signup“ enthält einen Link und als Ersatz einen 6-stelligen Code (5.2). Nach dem Klick auf „Adresse bestätigen“ auf `/konto/bestaetigen` (Knopf, kein automatisches Prüfen) folgt `POST /api/konto/link-pruefen` mit `art=neu` → `verifyOtp({ token_hash, type })`. Danach werden die Cookies gesetzt (3.2), und es geht weiter auf `/konto/willkommen` (5.3).
4. „Keine Mail bekommen?“ → `POST /api/konto/bestaetigung-erneut` → `resend({ type: 'signup', email })`, mit derselben neutralen Antwort und frühestens nach 60 Sekunden erneut.

**Anmelden**
5. „Anmelden“: Mailadresse, Passwort, Knopf „Anmelden“, darunter „Passwort vergessen?“ und „Noch kein Konto? Konto anlegen“.
6. `POST /api/konto/anmelden` → `signInWithPassword` serverseitig. Jeder Fehler ergibt dieselbe Meldung: „Mailadresse oder Passwort stimmen nicht.“ Einzige Ausnahme ist die noch nicht bestätigte Adresse (`email_not_confirmed`): „Bitte bestätigt zuerst eure Mailadresse“ mit Knopf „Mail erneut senden“. Der Vorversuch prüft, dass Supabase diesen Fehler **nur bei richtigem Passwort** liefert. Sonst bekommt auch er die einheitliche Meldung, damit niemand ohne Passwort erfährt, dass eine Adresse registriert ist.
   **Bremse gegen Erraten, ohne Fremde auszusperren:** Fehlversuche zählen je **Paar aus IP und Adresse**. Nach 5 Fehlversuchen in 15 Minuten ist dieses Paar 15 Minuten gesperrt: Der 6. Versuch ist der erste in der Pause. Er wird ohne Aufruf von Supabase mit derselben Meldung abgewiesen, auch mit richtigem Passwort. Von einer anderen IP aus, also für die echte Person, gilt die Pause nicht. Wer nur eine Adresse kennt, kann damit niemanden aussperren. Dazu kommen das Limit je IP (30 Versuche je Stunde über alle Adressen) und das eigene Limit von Supabase. Verteiltes Raten über viele IPs bremsen Mindestlänge und das Supabase-Limit.
7. Bei Erfolg werden die Cookies gesetzt, und die Übernahme der lokalen Merkliste (5.4) startet sofort. **Fehlt `onboarding_fertig_am`**, geht es auf `/konto/willkommen` (5.3), sonst auf `weiter`. **Fehlt `mindestalter_bestaetigt_am`**, gibt es zwei Fälle:
   - **Ohne Sperre** (Konto am Registrierungsformular vorbei angelegt, oder Nachweis bei der Registrierung nicht gesetzt, etwa wegen der Zeitprüfung in Schritt 2): `/konto/willkommen` zeigt zuerst das Alters-Häkchen allein. Bis es gesetzt ist, gilt der Gerätemodus aus 5.4 Schritt 0a.
   - **Mit Sperre** (`unter16_gesperrt_am` gesetzt, 4.5): `/konto/willkommen` zeigt **kein** Häkchen, sondern nur die Meldung aus 4.5. Das Konto bleibt im Gerätemodus, bis es gelöscht ist.

   **Vorrang der Sperre:** Ist `unter16_gesperrt_am` gesetzt, gilt das **unabhängig von `onboarding_fertig_am`**. Auch bei einem Konto, das sein Profil schon abgeschlossen hatte und erst danach ein Datum unter 16 angegeben hat, führt die Anmeldung nicht auf `weiter`, sondern auf `/konto`. Dort steht nur die Meldung aus 4.5: kein Häkchen, kein Fragebogen, keine Schalter, keine Merkliste-Ansicht im Kontomodus (`ddd_konto=0`, Gerätemodus). Erlaubt bleiben nur „Abmelden“ und „Konto löschen“.

**Passwort vergessen**
8. `/konto/passwort-vergessen`: Mailadresse, Knopf „Link schicken“ → `POST /api/konto/passwort-vergessen` → `resetPasswordForEmail(email)`. Die Antwort ist immer gleich: „Wenn es ein Konto mit dieser Adresse gibt, ist eine Mail unterwegs.“
9. Die Mail „Reset Password“ enthält **nur den Link, keinen Ersatz-Code**. Ein 6-stelliger Code ließe sich mit dem anon-Key direkt bei Supabase raten, an unserem Bremslimit vorbei. Beim Reset hieße das Übernahme des Kontos (5.2). Auf `/konto/bestaetigen` folgt nach dem Klick auf „Neues Passwort festlegen“ `POST /api/konto/link-pruefen` mit `art=reset` → `verifyOtp({ token_hash, type: 'recovery' })`. Die Route setzt eine **eingeschränkte Reset-Sitzung** und leitet auf `/konto/passwort-neu`:
   - Das Cookie `ddd_sitzung` trägt zusätzlich `nur_passwort: true` und hat `Max-Age` 1 Stunde statt 30 Tage. `ddd_konto` wird nicht gesetzt, die Website bleibt im abgemeldeten Zustand.
   - Mit einer solchen Sitzung beantworten alle Konto-Routen außer `passwort-setzen` und `abmelden` die Anfrage mit 403 `passwort_setzen_noetig`.
   - Wer den Link öffnet und kein neues Passwort setzt, ist nach spätestens einer Stunde wieder draußen. Andere Sitzungen und das alte Passwort bleiben bis dahin unberührt.
   - Den Merker im Cookie könnte die Person selbst entfernen. Das brächte ihr aber nichts, was sie nicht ohnehin durch Setzen eines neuen Passworts bekäme. Er ist ein Schutz vor vergessenen Reset-Sitzungen, keine Sicherheitsgrenze gegen Dritte.
10. `/konto/passwort-neu`: ein Feld für das neue Passwort mit „Anzeigen“-Knopf statt doppelter Eingabe → `POST /api/konto/passwort-setzen` → `updateUser({ password })` mit dem Nutzer-Client. Danach `signOut({ scope: 'others' })` (3.2). Die Route ersetzt das Cookie durch eine normale Sitzung (30 Tage, ohne `nur_passwort`, `ddd_konto` passend zu 3.2) und meldet: „Euer Passwort ist geändert. Andere Geräte sind abgemeldet.“ Danach geht es wie nach einer Anmeldung weiter (Schritt 7).
11. Die Reset-Vorlage gilt auch für die Admin-Konten des Dashboards. Deren Ablauf ändert sich damit: Der Link führt auf die Website, das neue Passwort gilt danach auch im Dashboard. Getestet in 16.3, Punkt 8.

**Passwort ändern im Konto**
12. `/konto` → „Passwort ändern“: aktuelles und neues Passwort → `POST /api/konto/passwort-aendern`. Die Route prüft das aktuelle Passwort mit `signInWithPassword` in einem eigenen, anfragebezogenen Client mit **denselben Optionen wie in 3.2: `persistSession: false`, `autoRefreshToken: false`, `detectSessionInUrl: false`**. Ohne `autoRefreshToken: false` startet supabase-js in Node einen `setInterval`, der den Client im Speicher hält (`GoTrueClient.js`, Zeilen 4463–4466 und 4722–4724). Das war das Leck vom 06.11.2026. Die Anmeldung ergibt eine frische Sitzung im Speicher dieses Clients. Mit demselben Client ruft die Route `updateUser({ password })` auf. „Secure password change“ verlangt eine Sitzung aus den letzten 24 Stunden oder ein Nonce (`GoTrueClient.js`, Zeilen 2169–2173 und 2836–2844), und die frische Anmeldung erfüllt das. Danach `signOut({ scope: 'others' })` (`GoTrueClient.js`, Zeilen 3409–3436), das die aktuelle Sitzung stehen lässt. In das Cookie kommt die Sitzung **nach** `updateUser` (`getSession()` desselben Clients), nicht die von `signInWithPassword` davor. Dieselben Client-Optionen gelten für jeden weiteren anfragebezogenen Auth-Client in diesem Plan (Löschen mit Passwort, 5.7).

**Gemeinsam**
13. Der **Vorversuch** (Schritt 4 in Abschnitt 15, gegen das echte Projekt mit Testadressen) legt fest, was die Bibliothek nicht eindeutig sagt:
    - welcher `type` den Bestätigungslink annimmt (`email` oder `signup`); für Reset gilt `recovery`, für den Ersatz-Code der Bestätigung derselbe Typ mit `email`;
    - was `signUp` in den drei Fällen tut (neu, unbestätigt mit anderem Passwort, bestätigt): Status, Antwortform, ob eine Mail verschickt wird und welches Passwort danach gilt;
    - ob `email_not_confirmed` nur bei richtigem Passwort kommt, und ob „Confirm phone“ im Projekt an ist;
    - welches Verify-Limit im Projekt gilt (Zahl, und ob es je IP oder je Adresse zählt). Gilt es nur je IP, bekommt auch die Bestätigungsmail keinen Ersatz-Code, und der Link bleibt der einzige Weg (5.2);
    - welche Antwortzeiten die Fälle haben.

    Unterscheiden sich die Zeiten von `registrieren`, `anmelden` und `passwort-vergessen` messbar je nachdem, ob es die Adresse gibt, antworten diese Routen frühestens nach einer festen Mindestdauer über dem langsamsten Fall. Die erlaubten Typen stehen in `EmailOtpType` (`@supabase/auth-js`, `lib/types.d.ts`, Zeile 746).
14. `weiter` wird so geprüft (`weiterPruefen`):
   - Mit `decodeURIComponent` dekodieren, bis sich der Text nicht mehr ändert, höchstens zweimal. Ein Dekodierfehler führt zum Standard.
   - Danach muss der **ganze** Wert mit genau einem `/` beginnen und darf an keiner Stelle `//`, `\`, `%2F`/`%2f`, `%5C`/`%5c`, `%25`, Steuerzeichen (`\u0000–\u001F`, `\u007F`) oder Leerraum enthalten.
   - Höchstens 200 Zeichen. Zurückgegeben wird der dekodierte, geprüfte Pfad, sonst `/merkliste`.

   Das verhindert einen offenen Redirect, auch über `%2F%2F`, `%252F%252F`, `%255C` und `/\`. Die Weiterleitung macht der Client mit `router.push`. Der Pfad wird danach nicht noch einmal dekodiert.

### 5.2 Links aus der Mail (Bestätigung und Reset), sicher gegen Link-Scanner
- Der Link führt auf **unsere** Domain, das Token steht im **Fragment**: `https://diesdas.events/konto/bestaetigen#token_hash={{ .TokenHash }}&art=neu` (Vorlage „Confirm signup“) bzw. `&art=reset` (Vorlage „Reset Password“). Ein Fragment schickt der Browser nicht an den Server, also steht es weder im nginx- noch im Next-Log. Nur das Skript der Seite liest es.
- In den Vorlagen steht **nie** `{{ .ConfirmationURL }}`. Der zeigt auf Supabase und verbraucht das Token schon beim GET.
- **Ersatz-Code (nur in der Bestätigungsmail):** Die Mail „Confirm signup“ enthält zusätzlich `{{ .Token }}` als 6-stelligen Code, sofern der Vorversuch ein Verify-Limit je Adresse zeigt (5.1 Schritt 13). Die Reset-Mail enthält **keinen** Code (5.1 Schritt 9). Wer einen beschädigten Reset-Link bekommt, fordert einen neuen an oder öffnet die Mail in einem anderen Programm. Manche Gateways (z. B. Outlook Safe Links) rufen die URL ohne Fragment ab und leiten danach ohne `#…` weiter. Dann kommt `/konto/bestaetigen` leer an. Die Seite sagt in diesem Fall: „Der Link ist unvollständig angekommen. Gebt einfach eure Mailadresse und den 6-stelligen Code aus der Mail ein“, mit beiden Feldern auf derselben Seite. Bei einem Reset-Link heißt es stattdessen: „Der Link ist unvollständig angekommen. Fordert bitte einen neuen an“, mit Knopf. Ob Supabase `{{ .TokenHash }}` hinter `#` ersetzt und welche Mailprogramme das Fragment behalten, prüft 16.3 (Gmail, GMX/Web.de, Outlook.com).
- Die Seite prüft beim Laden **nicht**. Sie zeigt einen Knopf („Adresse bestätigen“ bzw. „Neues Passwort festlegen“), erst der Klick schickt `POST /api/konto/link-pruefen` mit `{ token_hash, art }` (oder `{ email, code, art }`) → `verifyOtp(…)` mit dem Typ aus 5.1 Schritt 13. Mail-Scanner (Outlook Safe Links, Firmen-Gateways) rufen Links per GET ab und würden das Einmal-Token sonst verbrauchen. Ein Scanner, der Skripte ausführt, klickt den Knopf nicht.
- Die Seite entfernt das Fragment sofort mit `history.replaceState` aus der Adresszeile und setzt `referrer: no-referrer`.
- Ist der Link abgelaufen oder verbraucht, kommt die Meldung „Der Link ist abgelaufen“ mit dem passenden Knopf: „Bestätigungsmail erneut senden“ bzw. „Neuen Link anfordern“.
- Ein Link, der auf einem anderen Gerät geöffnet wird, meldet **dieses** Gerät an. Das ist erwartetes Verhalten und steht so im Mailtext.
- Die installierte Bibliothek kennt `verifyOtp({ email, token, type })` und `verifyOtp({ token_hash, type })` ohne PKCE und ohne `@supabase/ssr` (geprüft von Cursor, `@supabase/auth-js`, `lib/types.d.ts`, Zeilen 739–746).

### 5.3 Anlegen des Profils: Alter und Interessen (`/konto/willkommen`, E12)
- `/konto/willkommen` ist **fester Teil der Registrierung**. Er kommt direkt nach der Bestätigung der Mailadresse, und bei jeder Anmeldung erneut, solange `onboarding_fertig_am` leer ist. Erst danach führt die Anmeldung auf `weiter` bzw. `/merkliste`. Später lassen sich die Interessen im Konto unter „Interessen ändern“ jederzeit bearbeiten.
- **Nur die Anmeldung führt auf `/konto/willkommen`, die übrige Website bleibt erreichbar.** Öffentliche Seiten lesen keine Cookies und leiten nicht um (3.5). Wer nach dem Alters-Häkchen den Fragebogen verlässt und z. B. auf `/heute` geht, kann merken: Mit `ddd_konto=1` läuft die Merkliste im Kontomodus. Der Fragebogen kommt bei der nächsten Anmeldung wieder. Zusätzlich zeigt `/konto` und die Merkliste-Seite, solange `onboarding_fertig_am` leer ist, einen Hinweis „Euer Profil ist noch nicht fertig“ mit Link. Ohne Alters-Häkchen gilt der Gerätemodus aus 5.4 Schritt 0a.
- **Alters-Häkchen:** Es steht im Registrierungsformular (5.1) und ist bei der Kontoanlage schon gespeichert. Ein **gesperrtes** Konto (`unter16_gesperrt_am`, 4.5) sieht auf `/konto/willkommen` nur die Meldung aus 4.5, kein Häkchen, keinen Fragebogen. Nur ein Konto **ohne Sperre**, dessen Alter fehlt (am Formular vorbei angelegt oder Nachweis bei der Registrierung nicht gesetzt, 5.1 Schritte 2 und 7), sieht auf `/konto/willkommen` zuerst ein einzelnes Pflicht-Häkchen „Ich bin mindestens 16 Jahre alt.“ (`einwilligung_setzen('mindestalter', true)`, `handlung = 'abschlussseite'`). Bis dahin antworten alle angemeldeten Routen außer `ich`, `einstellungen`, `abmelden`, `export`, `loeschen`, `passwort-setzen` und `passwort-aendern` mit 403 `mindestalter_fehlt`, und die Policy in 4.3 sperrt das Merken auch in der Datenbank. Mit gesetztem Häkchen setzt der Server `ddd_konto=1`, und die Übernahme (5.4) startet parallel zum Fragebogen.
- **Schritte 1–4: Interessen** (Fragen und Optionen in Abschnitt 8) folgen direkt. Über Schritt 1 steht nur eine Einleitung, keine Einwilligung:
  > **Was interessiert euch?**
  > Ein paar kurze Fragen, damit wir euch passende Events vorschlagen können. Am Ende entscheidet ihr, ob wir eure Antworten speichern.
- In jedem Schritt gibt es „Weiter“ (auch ohne Auswahl, das heißt dann „keine Vorliebe“ in diesem Punkt) und, gut sichtbar, aber nachrangig gestaltet, den Link **„Ohne Interessen weiter“**. Er springt direkt zur Abschlussseite und verwirft alle Antworten.
- **Die Antworten bleiben bis zur Abschlussseite nur im Browser** (Zustand der Komponente, kein `localStorage`). Gesendet wird nichts, bevor eingewilligt ist. So entsteht vor der Einwilligung kein Profil, wie es die rechtliche Einschätzung verlangt.
- **Abschlussseite „Fast fertig“** (immer, auch nach „Ohne Interessen weiter“). Jede Einwilligung hat ein eigenes, nicht vorangekreuztes Häkchen mit eigenem Text. Jeder Text steht wörtlich in `einwilligungstexte` (4.4). Erklärtexte stehen wie die übrigen Datenschutztexte in Sie-Form, die Häkchen-Sätze in der Ich-Form der erklärenden Person:
  - **(a) Interessen und Empfehlungen** (nur sichtbar, wenn Antworten vorliegen):
    > ☐ Ich willige ein, dass dies.das meine Antworten in meinem Konto speichert und zusammen mit meiner Merkliste nutzt, um mir passende Events vorzuschlagen. Sensible Events (siehe unten) fließen nie in Empfehlungen ein. Ich kann das jederzeit im Konto widerrufen. Dann werden meine Antworten sofort gelöscht.
  - **(b) Sensible Events** (immer sichtbar, ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a):
    > **Datenschutz ist uns hier besonders wichtig.** Manche Events lassen Rückschlüsse auf sehr persönliche Dinge zu: Gesundheit, Religion oder Weltanschauung, sexuelle Orientierung oder geschlechtliche Identität, politische Meinung, Gewerkschaftszugehörigkeit oder ethnische Herkunft. Merken Sie sich solche Events, speichern wir sie ohne Ihre ausdrückliche Einwilligung **nur auf dem Gerät**, auf dem Sie sie gemerkt haben, und nicht in Ihrem Konto. Auf anderen Geräten sehen Sie sie dann nicht. Für Empfehlungen und Statistiken nutzen wir sie nie, auch nicht mit Einwilligung.
    > ☐ Ich willige ausdrücklich ein, dass dies.das auch solche Events, die ich mir merke, in meinem Konto speichert, damit sie auf allen meinen Geräten verfügbar sind. Ich kann das jederzeit im Konto widerrufen. Dann werden sie aus meinem Konto entfernt.
  - **(c) Hinweis auf das Widerspruchsrecht** (E4, Art. 21 Abs. 4, keine Einwilligung, als eigener, abgesetzter Kasten):
    > **Ihr Widerspruchsrecht:** Wir zählen anonym, wie oft Events gemerkt werden, um zu sehen, was in Düsseldorf beliebt ist (berechtigtes Interesse, Art. 6 Abs. 1 lit. f DSGVO). Wer was gemerkt hat, sieht dabei niemand, und sensible Events zählen nie mit. Sie können dem jederzeit widersprechen: ☐ Meine Merkliste nicht mitzählen. (Auch später im Konto.)
  - **(d) Geburtstag** (freiwillig, E15, Einwilligung nach Art. 6 Abs. 1 lit. a DSGVO und § 7 Abs. 2 UWG, weil Geburtstagsgrüße eines Unternehmens als Werbung gelten):
    > Feld „Geburtsdatum“ (Tag, Monat, Jahr, optional)
    > ☐ Ich möchte an meinem Geburtstag eine Mail von dies.das bekommen, mit Glückwünschen und Event-Tipps für den Tag. Dafür speichert dies.das mein Geburtsdatum. Ich kann das jederzeit im Konto oder über den Abmeldelink in jeder Mail widerrufen. Dann wird mein Geburtsdatum gelöscht.
    Das Datum wird nur mit Häkchen gesendet und gespeichert. Ohne Häkchen bleibt das Feld ungenutzt.
  - Knopf **„Fertig“**. Er ist immer aktiv, kein Häkchen ist Pflicht.
- **Speichern** über `POST /api/konto/abschluss` mit `{ praeferenzen?, interessen_ok, sensibel_ok, widerspruch, geburtsdatum?, geburtstagsmail_ok }`. Die Route:
  1. setzt jede der Angaben (a), (b), (c), (d) mit Nachweiszeile (`handlung = 'abschlussseite'`), auch die verneinten (`erteilt = false`):
     - (a), (b), (c) über `einwilligung_setzen`. Für (c) heißt das: ohne Widerspruch `analyse_erlaubt = true`, mit Widerspruch `false`. Erst ab hier wird ein Konto mitgezählt, weil erst jetzt der gesonderte Hinweis gezeigt wurde (E4);
     - (d) **bejaht** mit Datum nur über `geburtstag_setzen` (4.5): Datum, `geburtstagsmail = true` und Nachweis in einer Anweisung, mit Altersprüfung. Bei `unter_16` bricht die Route hier ab, speichert keine weiteren Angaben und zeigt die Meldung aus 4.5;
     - (d) **verneint** (Häkchen fehlt oder kein Datum) über `einwilligung_setzen('geburtstagsmail', false)`;
  2. speichert `praeferenzen` nur, wenn (a) angehakt ist. Ohne Häkchen bleibt `praeferenzen = '{}'`, und gesendete Antworten werden verworfen. Ohne Häkchen (a) schickt der Client sie gar nicht erst mit;
  3. setzt `onboarding_fertig_am`;
  4. bei (b) = ja: Danach schickt der Client die lokal gehaltenen Events aus `ddd-merkliste-geraet` (5.8) einmal an `merkliste/uebernehmen`.
- **Fehler mittendrin und Wiederholung:** Die Route arbeitet die Punkte der Reihe nach ab und meldet, welche gespeichert sind. Das Formular bleibt mit allen Angaben stehen („Konnte nicht vollständig gespeichert werden. Bitte nochmal versuchen.“). Beim zweiten Versuch gilt:
  - `einwilligung_setzen` wird nur für Angaben aufgerufen, die sich vom gespeicherten Stand unterscheiden;
  - `praeferenzen` werden **immer** erneut geschrieben, wenn (a) gilt und der Body Antworten enthält. Das ist auch dann so, wenn (a) schon beim ersten Versuch gespeichert wurde und nur das Speichern der Antworten scheiterte;
  - `onboarding_fertig_am` wird gesetzt, wenn es noch leer ist.

  Die CHECK-Bedingung aus 4.1 ist in jedem Zwischenzustand erfüllt, weil (a) vor `praeferenzen` gesetzt wird.
- Schließt jemand die Seite vor „Fertig“, ist nichts außer dem Alters-Häkchen gespeichert. `onboarding_fertig_am` bleibt leer, und Fragebogen und Abschlussseite kommen bei der nächsten Anmeldung wieder.
- **Im Konto (5.7)** lassen sich (a), (b), der Widerspruch (c) und (d) mit dem Geburtsdatum jederzeit einzeln umschalten bzw. ändern. „Interessen ändern“ öffnet den Fragebogen mit den gespeicherten Werten. Ist (a) aus, endet er mit derselben Einwilligung (a). Widerruf (a) leert `praeferenzen` sofort. Widerruf (b) entfernt sensible Events aus dem Konto, auf dem Gerät des Widerrufs bleiben sie lokal (4.5, 5.8).
- Die Interessen werden erst **nach** der Mail-Bestätigung abgefragt, nicht im Registrierungsformular. So speichern wir von unbestätigten Adressen nichts außer Adresse, Passwort-Hash und den Angaben aus dem Formular (Alter, Nutzungsbedingungen), und die werden nach 48 Stunden gelöscht (9.3).

### 5.4 Übernahme der lokalen Merkliste ins Konto (ohne Datenverlust)
Grundsätze:
- **Auf dem Gerät wird nur gelöscht, was nachweislich im Konto liegt oder nie gültig sein kann.**
- **Automatisch übernommen wird nur in ein Konto, das noch nie eine Merkliste hatte.** Sonst wird gefragt.
- **Aus dem Konto gelöscht wird nur, was ein Mensch per Herz oder „Verwerfen“ entfernt hat**, nie aus einem Unterschied zwischen zwei Listen geschlossen.

0. **Eine Sperre für alle Schreibzugriffe auf die Konto-Merkliste.** Übernahme (Schritte 1–9) und das Abarbeiten der Herz-Warteschlange (5.5) laufen unter derselben Web-Locks-Sperre `ddd-merkliste`. Das ist eine Browser-Schnittstelle ohne Bibliothek. Die Regeln:
   - Aufruf `navigator.locks.request('ddd-merkliste', { signal: AbortSignal.timeout(30_000) }, async () => { … })`. Der Callback gibt das Promise des **ganzen** Ablaufs zurück, einschließlich Abarbeiten der Warteschlange. Sonst wäre die Sperre sofort wieder frei.
   - Jeder Abruf darin hat eine eigene Zeitgrenze (`AbortSignal.timeout(15_000)`). Ein hängender Abruf hält die Sperre also nicht länger als etwa 15 Sekunden je Schritt fest.
   - Bricht das Warten nach 30 Sekunden ab, tut dieser Tab nichts. Die Geräteliste und die Warteschlange bleiben liegen und werden beim nächsten Auslöser (Seitenaufruf, Fokus, Herz-Klick) erneut versucht.
   - Ein zweiter Tab, der die Sperre nach einer Übernahme bekommt, liest Konto und Geräteliste neu und beginnt bei Schritt 1. Er übernimmt nichts doppelt und löscht nichts.
   - **Ersatz ohne Web Locks** (alte Browser): Der Tab schreibt einen Merker `ddd-merkliste-sperre = { token, bis }` mit Zufalls-Token und Ablauf in 30 Sekunden, liest ihn sofort zurück und arbeitet nur weiter, wenn dort das **eigene** Token steht. Sonst wartet er, bis `bis` verstrichen ist, und beginnt bei Schritt 1. Der Merker wird am Ende immer gelöscht (`finally`). Laufen trotzdem zwei Übernahmen gleichzeitig, schadet das nicht: Beide fügen nur ein (`ON CONFLICT DO NOTHING`), und niemand löscht aus einem Listenunterschied.
0a. **Erst mit bestätigtem Alter.** Normalerweise ist das Alter mit der Registrierung bestätigt (5.1). Nur bei Konten ohne Alters-Häkchen gilt: Solange `ddd_konto=0` ist (3.2), bleibt die Merkliste im Gerätemodus. Das Herz schreibt in `ddd-merkliste`, und die Merkliste-Seite zeigt die Geräteliste mit dem Hinweis „Bestätigt kurz euer Alter, dann landet eure Merkliste im Konto“ samt Link auf `/konto/willkommen`. Die Übernahme beginnt erst, wenn das Häkchen gespeichert ist (5.3).
0b. **Sensible Events (E13, 5.8):** Die Übernahme kann einzelne IDs nicht ins Konto schreiben, wenn sie sensibel sind und keine Einwilligung (b) vorliegt. Der Server meldet sie in `bleiben_auf_geraet`. Der Client verschiebt sie aus `ddd-merkliste` nach `ddd-merkliste-geraet`. Sie erscheinen **nicht** im Block „Nur auf diesem Gerät“ (Schritt 3), sondern ohne jede Kennzeichnung gemischt in der normalen Merkliste dieses Geräts.
1. Nach erfolgreicher Anmeldung holt der Client `GET /api/konto/ich` (enthält `merkliste_begonnen_am`) und `GET /api/konto/merkliste` (IDs) und vergleicht mit `ddd-merkliste`. „Nur auf dem Gerät“ sind die IDs, die das Konto nicht hat.
2. **`merkliste_begonnen_am` ist leer** (das Konto hatte nie einen Eintrag) → automatische Übernahme (Schritt 4). Das ist der Normalfall bei der ersten Anmeldung. Ein Konto, das einmal Einträge hatte und jetzt leer ist, fällt **nicht** hierunter, sondern unter Schritt 3. So kommen alte Geräte-IDs nach einem bewussten Leeren nicht ungefragt zurück.
3. **Sonst, wenn das Gerät IDs hat, die das Konto nicht hat** → keine automatische Übernahme. Die Merkliste-Seite (und einmal nach der Anmeldung ein Hinweis mit Link dorthin) zeigt: „Auf diesem Gerät sind noch 4 Events gemerkt, die nicht in eurem Konto sind.“ mit den Knöpfen [Ins Konto übernehmen] und [Auf diesem Gerät verwerfen]. Bis zur Entscheidung bleibt `ddd-merkliste` unverändert. Angezeigt wird die Konto-Liste, die vier Events stehen darunter in einem eigenen Block „Nur auf diesem Gerät“. Ein auf einem anderen Gerät entferntes Event kommt damit nie ungefragt zurück.
4. Übernehmen: Der Client schickt **alle** Geräte-IDs an `POST /api/konto/merkliste/uebernehmen`. Mehr als 1.000 IDs oder mehr als 48 KB lehnt der Server mit 413 ab, ohne etwas zu schreiben. Die Geräteliste bleibt dann unverändert, und die Seite meldet „Zu viele Einträge auf diesem Gerät“. Bei bis zu 500 möglichen Konto-Einträgen tritt das praktisch nicht auf.
5. Der Server prüft das UUID-Format, entfernt Doppelte und sortiert `beispiel-*` und IDs ohne Zeile in `events` als **ungültig** aus. Eine **abgelehnte Dublette mit Weiterleitung** in `event_seo_entscheidungen` wird auf das behaltene Event umgeschrieben, wenn sich `ziel` (Pfad `/event/<kategorie>/<slug>`) zu einer bestehenden Event-ID auflösen lässt. Lässt es sich nicht auflösen, wird die Ursprungs-ID unverändert übernommen und erscheint wie jede abgelehnte Dublette als „nicht mehr verfügbar“. Andere abgelehnte Events werden ebenso übernommen.
6. `INSERT … ON CONFLICT DO NOTHING` mit `quelle = 'geraet'`, bis die 500er-Grenze erreicht ist, in der Reihenfolge der Geräteliste. Kein Eintrag im Konto wird durch die Übernahme gelöscht.
7. Antwort (Status 200):
   - `konto`: vollständige Konto-Liste nach dem Einfügen;
   - `umgeschrieben`: `[{ von, nach }]` für jede aufgelöste Dublette;
   - `ungueltig`: IDs aus Schritt 5;
   - `nicht_uebernommen`: IDs, die wegen der Grenze draußen blieben;
   - `bleiben_auf_geraet`: IDs, die wegen E13 nicht ins Konto dürfen (Schritt 0b, 5.8). Der Name ist bewusst neutral und nennt keinen Grund;
   - `uebernommen` (Anzahl) und `vollstaendig` (`true`, wenn `nicht_uebernommen` leer ist; `bleiben_auf_geraet` zählt nicht als unvollständig).
8. Der Client entfernt aus `ddd-merkliste` **nur**:
   - IDs, die in `konto` stehen;
   - ein `von` aus `umgeschrieben`, aber nur, wenn das zugehörige `nach` in `konto` steht;
   - IDs aus `ungueltig` (sie zeigen auf kein Event und können nie übernommen werden);
   - IDs aus `bleiben_auf_geraet`. Sie wandern **nach `ddd-merkliste-geraet`** und werden nicht gelöscht (5.8).

   Alles andere bleibt auf dem Gerät, vor allem `nicht_uebernommen`. Das gilt bei `vollstaendig: true` genauso wie bei `false`. Die Seite meldet z. B.: „3 Events übernommen. 2 passen nicht mehr ins Konto (höchstens 500) und bleiben auf diesem Gerät.“
9. **Herz-Klicks während der Übernahme:** Jeder Herz-Klick im Kontomodus landet ohnehin in der Warteschlange `ddd-merkliste-warteschlange` (5.5), in jedem Tab. Abgearbeitet wird sie nur unter der Sperre aus Schritt 0, also erst **nach** der Übernahme und in Klick-Reihenfolge. Ein Entfernen während der Übernahme landet damit sicher im Konto, auch wenn die Übernahme dieselbe ID gerade eingefügt hat. Ein `DELETE` kann nicht vor dem `INSERT` der Übernahme ankommen.
10. Schlägt der Abruf fehl (Netz, 5xx, 401, 403, 413), bleibt `ddd-merkliste` unverändert. Die Warteschlange bleibt in `ddd-merkliste-warteschlange` erhalten, bei 401 gilt 5.5. Bei 403 `mindestalter_fehlt` (Alters-Häkchen fehlt) geht es zurück zu Schritt 0a. Beim nächsten Versuch beginnt es wieder bei Schritt 1. Ist `merkliste_begonnen_am` danach gesetzt (die Übernahme hat schon etwas geschrieben), gilt Schritt 3, die Nachfrage. Sonst gilt wieder Schritt 2. Das ist gewollt: Nichts geht verloren, und nichts kommt still dazu.

### 5.5 Merken mit Konto
- Der Store `useMerkliste()` bekommt diese Quellen:
  - im Gerätemodus (abgemeldet oder `ddd_konto=0`): `ddd-merkliste` wie heute, vereint mit `ddd-merkliste-geraet` (5.8);
  - im Kontomodus (`ddd_konto=1`): der Spiegel `ddd-merkliste-konto`, angewendet auf die noch offene Warteschlange, vereint mit `ddd-merkliste-geraet`.

  Server-Snapshot bleibt `LEER`. Die Vereinigung ist für die Oberfläche **eine** Liste ohne Unterscheidung (E13).
- **Warteschlange `ddd-merkliste-warteschlange`** in `localStorage`, unabhängig vom Spiegel: eine Liste `[{ op: 'merken' | 'entfernen', id, zeit }]`. Jeder Herz-Klick im Kontomodus ändert sofort den Spiegel (das Herz schaltet sofort um) und hängt einen Eintrag an. Ein Arbeiter arbeitet die Liste unter der Sperre `ddd-merkliste` (5.4 Schritt 0) ab: ein Aufruf nach dem anderen, in Reihenfolge, `PUT` bzw. `DELETE /api/konto/merkliste/<event_id>`. Ein Eintrag wird erst nach erfolgreicher Antwort entfernt. Beide Aufrufe sind idempotent, ein erneutes Senden nach einem Abbruch schadet also nicht. Der Arbeiter startet nach jedem Klick, beim Seitenaufruf und beim Fokus. Ein geschlossener Tab verliert damit nichts, der nächste Seitenaufruf arbeitet den Rest ab.
- **Fehler:**
  - Netz oder 5xx: Der Eintrag bleibt, ein neuer Versuch folgt beim nächsten Auslöser, höchstens alle 10 Sekunden. Nach drei Fehlschlägen hintereinander erscheint `role="status"`: „Noch nicht gespeichert, wir versuchen es weiter.“
  - 401 (abgemeldet, z. B. Token-Familie widerrufen) und ebenso **beim Abmelden**: Jeder noch nicht gesendete Eintrag wird auf die Geräteliste `ddd-merkliste` angewendet (`merken` → hinzufügen, `entfernen` → dort löschen). Danach werden Warteschlange und Spiegel geleert. Beim nächsten Anmelden fallen diese Einträge unter die Schritte 2 bzw. 3 in 5.4: automatisch, wenn das Konto nie eine Merkliste hatte, sonst „nur auf diesem Gerät“ mit Nachfrage. So geht nichts verloren.
  - 403 `mindestalter_fehlt` (11.1): wie 401 auf die Geräteliste anwenden, `ddd_konto=0` setzen und auf `/konto/willkommen` führen.
  - 400/404 für eine einzelne ID (Event existiert nicht): Eintrag verwerfen, Herz zurück.
  - Antwort `{ gespeichert: 'geraet' }` auf `PUT` (sensibles Event ohne Einwilligung, 5.8): Kein Fehler. Der Client nimmt die ID aus dem Spiegel und legt sie in `ddd-merkliste-geraet`. Das Herz bleibt gefüllt, es gibt keinen Hinweis.
- Abgleich zwischen Geräten: `GET /api/konto/merkliste` beim Öffnen der Merkliste und beim Fokus des Tabs, höchstens alle 60 Sekunden. Andere Tabs desselben Browsers bleiben über das `storage`-Ereignis gleich.
- `/merkliste` lädt angemeldet die Events über `GET /api/konto/merkliste?mit=events`. Das ist ein einziger `id IN (…)`-Abruf für die IDs außerhalb des Pools, keine 500 Einzelabfragen und keine 100er-Grenze. Darstellung: kommende nach Datum, darunter eingeklappt „Vorbei (n)“ (E9).
- Die bekannte Grenze bleibt: Gemerkt wird die ID des gebündelten Eintrags (1.1). Wird der früheste Termin später abgesagt, zeigt die Gruppe ein leeres Herz. Gelöst wird das nicht in dieser Runde (Abschnitt 19).

### 5.6 Mehrere Geräte und Abmelden
- Jedes Gerät hat eine eigene Sitzung. Im Konto stehen „Auf diesem Gerät abmelden“ und „Überall abmelden“.
- Beim Abmelden wendet der Client zuerst die noch offene Warteschlange auf die Geräteliste an (5.5). Danach leert er Warteschlange und Spiegel `ddd-merkliste-konto`, damit auf geteilten Geräten keine fremde Liste stehen bleibt. Die Liste liegt ja im Konto. `ddd-merkliste-geraet` bleibt stehen: Diese Merkungen gibt es nur auf diesem Gerät, wie die Merkliste ohne Konto heute auch.

### 5.7 Konto-Übersicht `/konto`
- **Gesperrtes Konto (`unter16_gesperrt_am` gesetzt, 4.5):** `/konto` zeigt nur die Meldung aus 4.5 sowie „Abmelden“ und „Konto löschen“. Alle folgenden Bereiche (Interessen, Einwilligungen, Passwort, Export) entfallen, auch wenn `onboarding_fertig_am` gesetzt ist (Vorrang der Sperre, 5.1 Schritt 7).
- „Eure Mailadresse: …“, ohne Ändern in dieser Runde (Abschnitt 19). Hinweis: „Adresse ändern? Schreibt uns an moin@rocktician.com.“
- Interessen: Kurzfassung plus „Interessen ändern“, das den Fragebogen mit den gespeicherten Werten öffnet.
- Bereich **„Eure Einwilligungen“** mit vier Schaltern und je dem Wortlaut aus `einwilligungstexte`. Er erscheint erst, wenn `onboarding_fertig_am` gesetzt ist. Vorher zeigt `/konto` nur den Hinweis „Euer Profil ist noch nicht fertig“ mit Link auf `/konto/willkommen` (E4: der Hinweis nach Art. 21 Abs. 4 kommt zuerst):
  - „Interessen speichern und Empfehlungen“ (`personalisierung`, Einwilligung (a)). Beim Einschalten ohne gespeicherte Interessen wird der Fragebogen angeboten.
  - „Sensible Events im Konto speichern“ (`sensible_events_erlaubt`, ausdrückliche Einwilligung (b), mit dem Erklärtext aus 5.3). Ausschalten entfernt sie aus dem Konto, auf diesem Gerät bleiben sie lokal (5.8). Einschalten lädt die lokal gehaltenen Events dieses Geräts hoch.
  - „Meine Merkliste nicht anonym mitzählen“ (Widerspruch, `analyse_erlaubt = false`, E4).
  - „Geburtstagsmail“ mit dem Geburtsdatum (`geburtstagsmail`, Einwilligung (d), E15): Einschalten fragt das Datum ab (`geburtstag_setzen`), Ausschalten löscht das Datum. Das Datum lässt sich ändern, ebenfalls über `geburtstag_setzen`. Liegt ein **neues** Datum unter 16, wird es nicht gespeichert. Das bisherige Datum bleibt technisch in der Spalte, das Konto wird aber gesperrt (4.5). Die Oberfläche zeigt dann nur noch die Meldung aus 4.5 und behandelt das alte Datum nicht als weiter gültig. Bis zur Löschung beim nächsten Job-Lauf geht keine Geburtstagsmail mehr an das Konto (13a schließt gesperrte Konten aus).

  Jedes Umschalten schreibt eine Zeile in `einwilligungen` (`handlung = 'konto_schalter'`).
- „Passwort ändern“ (5.1 Schritt 12).
- „Eure Daten herunterladen“ (`GET /api/konto/export`): eine JSON-Datei mit Konto (Mail, angelegt, letzte Anmeldung), Interessen, Geburtsdatum (falls angegeben) und Datum der letzten Geburtstagsmail, Schaltern, Einwilligungs-Verlauf mit Wortlaut und Merkliste mit Titel und Datum. Kein Passwort-Hash, keine Kennzeichnung sensibler Events. Darunter der Hinweis: „Eine vollständige Auskunft nach Art. 15 DSGVO bekommt ihr auch per Mail an moin@rocktician.com.“ Der Export ersetzt das Auskunftsrecht nicht (rechtliche Einschätzung).
- „Konto löschen“: ein Dialog, in dem man das **aktuelle Passwort** eingibt und „LÖSCHEN“ eintippt, dann `POST /api/konto/loeschen`. Die Route prüft das Passwort wie in 5.1 Schritt 12, bevor sie löscht. Ein offen gelassenes Gerät reicht damit nicht zum Löschen. Danach sind die Cookies und der Spiegel weg, und die Bestätigung auf der Seite lautet: „Euer Konto und eure Merkliste sind gelöscht.“ Eine Mail dazu gibt es nicht, Supabase hat dafür keine Vorlage, und eigener Versand bräuchte eine Bibliothek.
- Abmelden (5.6).

### 5.8 Sensible Events (E13)
**Kennzeichnung (Datenbank-Trigger, nur Backend, 4.8)**
- Die Regeln liegen als Zeilen in `sensibel_regeln` und werden vom Trigger auf `events` bei jedem Insert und bei Änderungen an Titel, Beschreibung oder Ort angewendet, egal ob Pipeline, Anreicherung oder Dashboard schreibt. Python braucht keine eigene Kopie der Regeln.
- **Startregeln (verbindlich, PostgreSQL-Regex mit `~*`, `\y` = Wortgrenze).** Geprüft wird `titel || ' ' || coalesce(ort,'') || ' ' || coalesce(beschreibung,'')`:

| Grund | `muster` | `kontext_muster` (muss zusätzlich treffen) | `ausnahme_muster` (hebt auf) |
|---|---|---|---|
| sexualitaet | `\y(csd|christopher street day|queer\w*|lgbt\w*|lsbt\w*|schwul\w*|lesbisch\w*|bisexuell\w*|transgender|transident\w*|nonbinär\w*|non-binary|drag ?(queen|king|show)s?)\y` | – | – |
| sexualitaet | `\ypride\y` | – | `pride and prejudice|stolz und vorurteil` |
| religion | `\y(gottesdienst\w*|andacht\w*|freitagsgebet|gebetsabend|moschee\w*|synagoge\w*|kirchengemeinde\w*|pfarrgemeinde\w*|taufe|firmung|konfirmation|kommunion|ramadan|iftar|chanukka|bibelkreis|bibelabend|koranlesung)\y` | – | – |
| religion | `\ymesse\y` | `\y(kirche\w*|gemeinde\w*|pfarr\w*|gottes\w*|heilige?n?|dom|kapelle)\y` | – |
| gesundheit | `\y(selbsthilfe\w*|suchtberatung|suchthilfe|suchtkrank\w*|anonyme alkoholiker|hiv|aids-hilfe|aidshilfe|krebsberatung|krebshilfe|krebserkrank\w*|depression\w*|demenz\w*|trauergruppe\w*|trauercaf[eé]|psychotherap\w*|blutspende\w*)\y` | – | – |
| politik | `\y(cdu|csu|spd|fdp|afd|bsw|linkspartei|bündnis 90|die grünen|freie wähler|piratenpartei|ödp|tierschutzpartei)\y` | – | – |
| politik | `\y(die linke|die partei)\y` | `\y(partei\w*|wahl\w*|kandidat\w*|ortsverband|kreisverband|fraktion|bundestag|landtag|stadtrat)\y` | – |
| politik | `\yvolt\y` | `\y(partei|europa|wahl\w*|kandidat\w*)\y` | – |
| politik | `\y(parteitag|ortsverband|kreisverband|wahlkampf\w*|kundgebung)\y` | – | – |
| politik | `\ydemonstration\y` | `\y(gegen|für|protest\w*|kundgebung|bündnis|aufruf|solidarität\w*|rathaus|landtag)\y` | `\y(live|koch|produkt|tanz)[- ]?demonstration\y` |
| gewerkschaft | `\y(gewerkschaft\w*|ver\.di|ig metall|ig bce|dgb|betriebsrat|betriebsräte\w*)\y` | – | – |

- `herkunft` hat **keine automatische Regel**. Muster wie Länderküche oder Kulturfeste (Japan-Tag) träfen fast nur Fehltreffer. Gekennzeichnet wird hier nur von Hand (`quelle = 'hand'`). Der Grund bleibt im CHECK der Tabelle.
- Bewusst **nicht** in der Liste: „Verdi“ ohne Punkt (Giuseppe Verdi, Oper), „Grüne“ allein („Grüne Woche“, „ins Grüne“), „Demo“ allein (Kochdemo, Demotape), „Sucht“ allein (das Verb „sucht“), „Krebs“ allein, „Gebet“ allein.
- **Bekannte Fehltreffer, die bewusst hingenommen und bei der Sichtprüfung per Ausnahme aufgehoben werden:** ein Theaterstück oder Film mit „Demenz“ im Titel (gesundheit), „Pride“ in Titeln außer dem ausgenommenen Buchtitel (z. B. Bandnamen), „SPD“ in einem Bandnamen. Die Regeln bleiben dafür bewusst weit („im Zweifel sensibel“ bei der Sichtprüfung). Ein Fehltreffer kostet nur Komfort.
- **Reihenfolge der Regeln:** `prioritaet` in der Reihenfolge der Tabelle oben (sexualitaet 10, 11; religion 20, 21; gesundheit 30; politik 40, 41, 42, 43, 44 in Tabellenreihenfolge, also Parteiliste, „Die Linke/Die Partei“, „Volt“, Parteitag usw., „Demonstration“; gewerkschaft 50). Bei mehreren Treffern zählt der Grund der Regel mit der kleinsten Priorität. Der Grund ist nur intern und ändert am Verhalten nichts.
- **Umlaute:** `\y` und `\w` zählen Umlaute nur dann als Buchstaben, wenn die Datenbank mit einem passenden Locale läuft. 16.2 prüft deshalb ausdrücklich „ÖDP“, „nonbinär“, „Bündnis 90“ und „Trauercafé“. Greift einer davon nicht, werden die betroffenen Muster in Schritt 3 ohne `\y` an der Umlautstelle bzw. mit `[[:alpha:]]` geschrieben.
- **Erweitern nur nach Sichtprüfung:** Neue Regeln kommen erst nach einer Sichtprüfung der Treffer der letzten 60 Tage dazu (SQL-Datei mit SELECT-Vorschau, dann INSERT in `sensibel_regeln`, ausgeführt vom Auftraggeber). „Im Zweifel sensibel“ gilt **nur für diese Sichtprüfung**: Ist bei einem Treffer unklar, ob er sensibel ist, bleibt er gekennzeichnet. Zur Laufzeit gilt allein die Regeltabelle.
- **Fehltreffer:** Der Auftraggeber bestätigt sie von Hand. Die Zeile in `event_sensibel` wird gelöscht und die ID in `event_sensibel_ausnahmen` eingetragen, damit der Trigger sie bei einer Textänderung nicht wieder kennzeichnet. Bis Phase 3 per SQL, danach im Dashboard.
- **Nachtrag für vorhandene Events** (Schritt 7 in Abschnitt 15): `database/sensibel_nachtrag_<datum>.sql` in zwei Teilen. Teil 1 ist eine SELECT-Vorschau aller Treffer ab heute minus 400 Tage mit Titel, Ort und Grund für die Sichtprüfung durch den Auftraggeber. Teil 2 ist das INSERT. Läuft **vor** dem ersten Einschalten der Konten, damit noch keine Merkliste betroffen ist.
- Tests: SQL-Tests in 16.2 (je Regel ein Treffer und ein Fehltreffer aus der Liste oben). Die KI-Kategorisierung bleibt unverändert. Eine KI-Einschätzung (`quelle = 'ki'`) ist vorbereitet, aber nicht Teil dieser Runde.

**Unsichtbar für Nutzer**
- Keine Markierung am Event, auf Karten, in Listen, in der Merkliste oder im Export. Kein Hinweis beim Merken. `event_sensibel` ist für `anon` und `authenticated` nicht lesbar (4.8) und wird nie an den Browser ausgeliefert.
- Die Merkliste zeigt Konto- und Geräte-Merkungen als **eine** Liste (5.5). Lokal gehaltene sensible Events stehen nicht im Block „Nur auf diesem Gerät“ (5.4 Schritt 0b).
- Der Einwilligungstext (b) erklärt nur allgemein, welche Arten von Events wir als sensibel betrachten, und nennt keine Events (5.3).
- **Technische Grenze, offen benannt:** Wer mit Entwicklerwerkzeugen den Datenverkehr mitliest, sieht an drei Antworten, dass einzelne Events nicht ins Konto gingen bzw. es verlassen: `{ gespeichert: 'geraet' }` (Herz), `bleiben_auf_geraet` (Übernahme) und die Liste `zurueck_aufs_geraet` beim Widerruf von (b) (`einstellungen`, 4.5). Kleiner wird die Grenze nicht, ohne dass Merkungen verloren gehen. Ohne diese Information könnte der Browser die Merkung nicht sicher auf dem Gerät halten. Für die Oberfläche bleibt es unsichtbar. Die Antworten sind neutral benannt und nennen keinen Grund. Auch der lokale Schlüssel heißt neutral `ddd-merkliste-geraet`.

**Verhalten**
- **Ohne Einwilligung (b):** `PUT /api/konto/merkliste/<id>` für ein sensibles Event schreibt nichts. Der Trigger in 4.3 bricht mit `nur_geraet` ab, und die Route antwortet 200 `{ gespeichert: 'geraet' }`. Der Client hält die ID in `ddd-merkliste-geraet` (5.5). `DELETE` einer solchen ID entfernt sie lokal, der Server-Aufruf schadet nicht.
- **Mit Einwilligung (b):** Sensible Events gehen normal ins Konto und sind auf allen Geräten da. Für Empfehlungen (Abschnitt 13) und Statistik (4.5) werden sie trotzdem nie verwendet.
- **Einwilligung (b) erteilt** (Abschlussseite oder Konto): Der Client schickt `ddd-merkliste-geraet` einmal an `merkliste/uebernehmen` und leert die übernommenen IDs nach den Regeln aus 5.4 Schritt 8.
- **Einwilligung (b) widerrufen:** `einwilligung_setzen` löscht die sensiblen Zeilen aus dem Konto und gibt ihre IDs zurück (4.5), die Route liefert sie als `zurueck_aufs_geraet`. Der Client des widerrufenden Geräts legt sie in `ddd-merkliste-geraet`. Auf anderen Geräten verschwinden sie beim nächsten Abgleich. Das sagt der Widerrufsdialog allgemein: „Sensible Events entfernen wir aus Ihrem Konto. Auf diesem Gerät bleiben sie gemerkt, auf Ihren anderen Geräten verschwinden sie.“
- **Spätere Kennzeichnung** eines schon gemerkten Events: siehe 4.8. Das betrifft nur Konten ohne Einwilligung (b). Die Merkung verschwindet dann auf allen Geräten, eine Rückgabe gibt es bewusst nicht. Durch die Prüfung beim Insert ist das selten.

---

## 6. API-Routen (alle unter `web/app/api/konto/`, `Cache-Control: private, no-store`)

| Route | Methode | Zweck | Anmeldung | Bremslimit |
|---|---|---|---|---|
| `registrieren` | POST | Konto anlegen, Bestätigungsmail (5.1) | nein | je IP 10/Std, je Adresse 3/Std |
| `bestaetigung-erneut` | POST | Bestätigungsmail erneut senden | nein | je IP 10/Std, je Adresse 3/Std, mindestens 60 s Abstand |
| `anmelden` | POST | Anmelden mit Passwort, Sitzung setzen | nein | je IP 30/Std; je Paar aus IP und Adresse 5 Fehlversuche/15 Min, der 6. Versuch ist der erste in 15 Min Pause (gleiche Meldung, ohne Aufruf von Supabase). Andere IPs sind nicht betroffen (5.1 Schritt 6) |
| `passwort-vergessen` | POST | Reset-Mail | nein | je IP 10/Std, je Adresse 3/Std |
| `link-pruefen` | POST | Bestätigungs- oder Reset-Link bzw. Ersatz-Code der Bestätigung prüfen, Sitzung setzen (Reset: eingeschränkt, 5.1 Schritt 9) | nein | je IP 30/Std, je Adresse 5 Fehlversuche/15 Min (beim Code) |
| `passwort-setzen` | POST | neues Passwort nach Reset (5.1 Schritt 10) | ja | je Nutzer 10/Std |
| `passwort-aendern` | POST | Passwort im Konto ändern (5.1 Schritt 12) | ja | je Nutzer 5 Fehlversuche/15 Min |
| `ich` | GET | Status, Profil, Schalter, `onboarding_fertig_am`; setzt `letzte_aktivitaet_am` | ja | je Nutzer 120/Std |
| `abmelden` | POST | `{ ueberall: boolean }` | ja | – |
| `abschluss` | POST | Abschlussseite: `{ praeferenzen?, interessen_ok, sensibel_ok, widerspruch, geburtsdatum?, geburtstagsmail_ok }`, Einwilligungen über `einwilligung_setzen` bzw. für (d) bejaht über `geburtstag_setzen`, dann `praeferenzen` (nur mit (a)) und `onboarding_fertig_am` (5.3) | ja | je Nutzer 30/Std |
| `vorlieben` | PUT | Interessen ändern im Konto: `{ praeferenzen }`, nur wenn (a) gilt bzw. mit `interessen_ok: true` in derselben Anfrage (5.3, 5.7) | ja | je Nutzer 60/Std |
| `einstellungen` | PUT | Einzelner Schalter: Mindestalter, Personalisierung, sensible Events, Widerspruch, über `einwilligung_setzen` (Dienst-Client, 4.5). Geburtstagsmail: `{ art: 'geburtstagsmail', erteilt: true, geburtsdatum }` über `geburtstag_setzen`, `erteilt: false` über `einwilligung_setzen`. **Die Art `analyse` lehnt die Route mit 409 ab, solange `onboarding_fertig_am` leer ist**, weil der Hinweis nach Art. 21 Abs. 4 erst auf der Abschlussseite kommt (E4). Beim Widerruf (b) Antwort mit `zurueck_aufs_geraet` (5.8) | ja | je Nutzer 60/Std |
| `merkliste` | GET | IDs, optional mit Events | ja | je Nutzer 120/Std |
| `merkliste/[id]` | PUT/DELETE | merken / entfernen. `PUT` antwortet `{ gespeichert: 'konto' }` oder `{ gespeichert: 'geraet' }` (5.8), beides 200 | ja | je Nutzer 300/Std |
| `merkliste/uebernehmen` | POST | Übernahme (5.4), höchstens 1.000 IDs, sonst 413 ohne Schreiben. Antwort mit `bleiben_auf_geraet` (5.8) | ja | je Nutzer 10/Std |
| `export` | GET | JSON-Download | ja | je Nutzer 5/Std |
| `loeschen` | POST | Konto löschen, nur mit aktuellem Passwort | ja | je Nutzer 3/Std |
| `geburtstag-abmelden` | POST | Abmeldung von Geburtstagsmails über die Seite, Token im Body (13a, gebaut in Schritt 9a) | nein, Token | je IP 30/Std |
| `geburtstag-abmelden/[token]` | POST (GET → 405) | One-Click-Abmeldung nach RFC 8058 aus dem Mailprogramm (13a, Schritt 9a) | nein, Token | je IP 30/Std |

- Passwörter erscheinen nie in Logs, Fehlermeldungen oder Bremslimit-Schlüsseln. Die Routen lesen sie aus dem Body und reichen sie nur an Supabase weiter. Der Fehlertext von Supabase wird nicht durchgereicht, sondern auf unsere festen Meldungen abgebildet.

- Die Schlüssel fürs Bremslimit sind die IP (wie heute) oder der SHA-256 der kleingeschriebenen Adresse bzw. die Nutzer-ID. Sie liegen nur im Speicher (`zuVieleAnfragen`).
- **`zuVieleAnfragen` wird vorher repariert** (1.5): Jeder Schlüssel speichert sein eigenes Fenster (`{ fensterMs, zeiten }`). Die Bereinigung entfernt einen Schlüssel nur, wenn alle seine Treffer älter als **sein** Fenster sind. Die Notbereinigung über `MAX_SCHLUESSEL` (heute Zeilen 86–92) entfernt zuerst die nach ihrem eigenen Fenster abgelaufenen Schlüssel und danach, wie heute, die am längsten nicht genutzten, bis die Map unter 80 Prozent liegt. Die Zahl der Schlüssel bleibt also auch bei vielen lebenden Fenstern begrenzt. Die Signatur bleibt gleich, Newsletter und Event melden laufen unverändert. Test in 16.1.
- Jede angemeldete Route setzt `letzte_aktivitaet_am` (4.1). Ist `KONTEN_AKTIV` aus, antworten alle Routen dieser Tabelle mit 404 (E10). Ohne `mindestalter_bestaetigt_am` antworten die angemeldeten Routen außer `ich`, `einstellungen`, `abmelden`, `export`, `loeschen`, `passwort-setzen` und `passwort-aendern` mit 403 `mindestalter_fehlt` (5.3).
- `zuGross` gilt überall: 4 KB, für `uebernehmen` 48 KB. Alle Routen akzeptieren nur JSON.
- Einheitliche Fehltexte: Anmelden „Mailadresse oder Passwort stimmen nicht.“, Link/Code „Der Link oder Code stimmt nicht oder ist abgelaufen.“, Registrieren und Passwort vergessen immer die neutrale Erfolgsmeldung aus 5.1.

---

## 7. Oberfläche und Einbaustellen

### 7.1 Merkliste-Seite (`web/app/merkliste/page.tsx`, `components/merkliste.tsx`)
Die Seite bleibt eine statische Hülle. Der Untertitel und der Hinweis werden zu einer kleinen Client-Komponente, damit der Server weiter nichts über die Sitzung weiß.

**Abgemeldet, mit Einträgen (Fall aus dem Screenshot):**
- Untertitel bleibt „Nur auf diesem Gerät gespeichert“.
- Direkt darunter, über dem Raster, ein Hinweiskasten:
  > **Eure Merkliste auf allen Geräten**
  > Mit einem kostenlosen Konto liegt sie sicher bei uns – auf dem Handy, am Laptop und bald in unserer App. Beim ersten Konto nehmen wir sie mit. Habt ihr schon eine Merkliste im Konto, fragt die Seite nach, was dazukommen soll.
  > [Anmelden oder Konto anlegen] · Kostenlos, mit Mailadresse und Passwort.
- Der Knopf führt auf `/konto/anmelden?weiter=/merkliste`.
- Der Kasten ist dezent in der Navy- oder Gold-Tönung des Designs, mit Icon `cloud_sync`. Er ist nicht wegklickbar, weil er auf dieser Seite der Ort für den Hinweis ist.

**Abgemeldet, leer:** der bestehende Leerzustand, dazu der Satz „Schon ein Konto? [Anmelden], dann seht ihr eure Merkliste von anderen Geräten.“

**Angemeldet:** Untertitel „In eurem Konto gespeichert“, kein Kasten. Nach einer Übernahme einmal der Status „n Events von diesem Gerät übernommen“. Liegen auf dem Gerät noch Events, die nicht im Konto sind (5.4, Schritte 3 und 8), steht unter der Konto-Liste ein eigener Block „Nur auf diesem Gerät“ mit den Knöpfen [Ins Konto übernehmen] und [Auf diesem Gerät verwerfen]. „Verwerfen“ fragt einmal nach („4 Events von diesem Gerät entfernen?“) und leert dann nur diese IDs.

**Bestehende du-Texte** auf der Seite werden im selben Zug auf ihr/euch umgestellt: „Tippt aufs Herz, dann landet ein Event hier.“ und „Eure gemerkten Events sind vorbei.“

### 7.2 Hinweis nach dem ersten Merken (Vorschlag, abgemeldet)
- Nach dem **ersten** Herz-Klick auf einem Gerät erscheint einmalig ein kleiner Hinweis über der TabBar: „Gemerkt! Eure Merkliste liegt nur auf diesem Gerät. [Mit Konto überall dabei] ✕“
- Er erscheint nie beim Seitenaufruf, nur nach dem Klick, ist also SEO-neutral. Er verschwindet nach 8 Sekunden oder per ✕. Danach ist ein Merker in `localStorage` gesetzt (`ddd-konto-hinweis`), und der Hinweis kommt nie wieder.
- `role="status"`, per Tastatur erreichbar, bei `prefers-reduced-motion` ohne Animation.

### 7.3 Kopf, Mobilmenü, Fuß, TabBar
- **Kopf, Desktop** (`rahmen.tsx`, Zeile 45): Rechts neben dem Herz kommt ein Icon-Knopf `person` mit `aria-label="Konto"` und Ziel `/konto`. Das Label ist immer „Konto“: Der Kopf ist statisch, und ein wechselnder Text würde nach dem Laden flackern. `/konto` zeigt abgemeldet die Anmeldung.
- **Mobilmenü** (Zeilen 67–69): Unter „Service“ steht „Konto“ vor „Merkliste“.
- **Fuß** (Zeile 169): „Konto“ neben „Merkliste“. Bei den Rechtstexten (Zeilen 175–176) kommt „Nutzungsbedingungen“ neben Impressum und Datenschutz dazu (E14). Dieser Link erscheint erst mit dem Schalter.
- **TabBar:** keine Änderung. Fünf Tabs reichen, und die Merkliste-Seite führt zum Konto.
- Alles hängt am Schalter `KONTEN_AKTIV`. Ist er aus, gibt es keinen Konto-Link, keinen Hinweis, und `/konto/*` zeigt „Noch nicht verfügbar“ (noindex).

### 7.4 Neue Seiten
`/konto` (Übersicht), `/konto/anmelden` (Anmelden / Konto anlegen), `/konto/bestaetigen`, `/konto/passwort-vergessen`, `/konto/passwort-neu`, `/konto/willkommen` (Fragebogen und Abschlussseite). Jede bekommt `metadata.robots = { index: false, follow: false }`, steht nicht in der Sitemap und nicht in `llms.txt`. Alle sind mobil zuerst gebaut, im hellen und dunklen Modus geprüft, ohne Querscrollen.

Dazu kommt **`/nutzungsbedingungen`** (E14) als normale, indexierbare Rechtsseite wie `/datenschutz` und `/impressum`. Text aus `docs/nutzungsbedingungen-entwurf-2026-11-16.md` nach anwaltlicher Prüfung, Sie-Form wie die übrigen Rechtstexte, mit „Stand“ und Versionskennung (z. B. `nutzungsbedingungen-2026-12`). Dieselbe Kennung steht in `einwilligungstexte` und im Code (4.4). Die Seite ist statisch und gecacht und wird erst mit dem Schalter verlinkt. Erreichbar ist sie schon vorher, damit der Anwalt sie live prüfen kann (noindex, bis der Schalter an ist).

---

## 8. Interessen-Fragebogen (`components/interessen-fragebogen.tsx`, neu)

- Er ist eine eigene Komponente als **Seiteninhalt**, kein Dialog. So funktioniert er auch auf kleinen Geräten und später gleich in der App. Er nutzt die Klassen und das Bedienmuster aus `fragebogen.tsx` (1.2).
- `fragebogen.tsx` selbst **bleibt unverändert**. Das Auslagern eines gemeinsamen Rahmens ist ein späterer, getrennter Schritt, damit der Restaurant-Hub kein Risiko trägt.
- Zahlen wie „124 Events in den nächsten 30 Tagen“ je Kategorie kommen aus dem gecachten Pool, als Prop der statischen Seite. Sie sind nicht persönlich.

| Schritt | Frage | Auswahl | Speichern |
|---|---|---|---|
| – | (Alters-Häkchen steht im Registrierungsformular, 5.1. Nur Konten ohne Häkchen **und ohne Sperre** sehen es hier vorab. Gesperrte Konten sehen nur die Meldung aus 4.5 und keinen Fragebogen.) | – | – |
| 1 | „Worauf habt ihr Lust?“ | 10 Kategorien als Karten mit Icon und Farbe, Mehrfachauswahl, Chip „Von allem etwas“ | `kategorien` |
| 2 | „Was genau?“ | Unterkategorien der gewählten Kategorien, gruppiert. Entfällt ohne Wahl in Schritt 1 | `unterkategorien` (`kategorie/slug`) |
| 3 | „Wo seid ihr unterwegs?“ | „Überall in Düsseldorf“ (Standard) oder Stadtteile nach Bezirken (`BEZIRKE`), dazu Neuss und Ratingen | `stadtteile` |
| 4 | „Was passt zu euch?“ | Merkmale: „Gern kostenlos“, „Mit Kindern unterwegs“, „Eher abends“, „Eher tagsüber“, „Am liebsten am Wochenende“. Orte: Restaurants & Cafés, Kneipen & Bars, Clubs, Spielplätze | `merkmale`, `orte` |
| Ende | „Fast fertig“ | Einwilligungen (a) Interessen und Empfehlungen, (b) sensible Events, Hinweis (c) Widerspruch Zählung, (d) Geburtsdatum mit Geburtstagsmail (freiwillig), Wortlaut in 5.3 | `personalisierung`, `sensible_events_erlaubt`, `analyse_erlaubt`, `geburtstagsmail` und `geburtsdatum` nur mit (d), `einwilligungen`, `praeferenzen` nur mit (a), `onboarding_fertig_am` |

Die Schritte 1–4 kommen beim Anlegen immer (E12, 5.3), außer bei einem gesperrten Konto (`unter16_gesperrt_am`). Dort gilt der Vorrang der Sperre aus 5.1 Schritt 7: nur die Meldung aus 4.5, kein Fragebogen, auch nicht über „Interessen ändern“. Über Schritt 1 steht die neutrale Einleitung aus 5.3, jeder Schritt hat „Weiter“ und „Ohne Interessen weiter“. Die Antworten bleiben bis zur Abschlussseite im Browser. Erst „Fertig“ dort speichert, und nur mit Häkchen (a). Danach geht es auf `weiter` bzw. `/merkliste`. Im Konto unter „Interessen ändern“ öffnet sich derselbe Fragebogen mit den gespeicherten Werten. Ist (a) noch nicht erteilt, endet er mit derselben Einwilligung (a).
- Die Kategorie-Auswahl enthält keine sensiblen Kategorien. Die zehn Kategorien (Kultur, Musik, Food, Sport, Outdoor, Stadtführung, Community, Nightlife, Familie, Dating) und ihre Unterkategorien lassen keine Art.-9-Rückschlüsse zu. Kommt später eine Unterkategorie dazu, die das täte (z. B. „Religion“), erscheint sie im Fragebogen nicht. Die Spielplätze stehen in der Auswahl, auch solange der Guide nicht verlinkt ist (`SPIELPLAETZE_VERLINKT`), weil es nur um ein Interesse geht.

---

## 9. Datenschutz (DSGVO, TDDDG)

### 9.1 Zwecke und Rechtsgrundlagen

| Verarbeitung | Daten | Rechtsgrundlage | Speicherdauer |
|---|---|---|---|
| Konto führen, Anmeldung | Mail, Passwort-Hash (bei Supabase, nie bei uns im Klartext), Anmeldezeitpunkte, Sitzungen | Art. 6 Abs. 1 lit. b (Nutzungsvertrag) | bis zur Löschung, spätestens 24 Monate nach der letzten Nutzung (`letzte_aktivitaet_am`, ohne Nutzung ab Anlage, E11) |
| Merkliste im Konto (ohne sensible Events) | Event-IDs, `gemerkt_am` | lit. b (Kernfunktion des Kontos) | wie Konto |
| Sensible Events im Konto (E13) | Event-IDs gekennzeichneter Events, `gemerkt_am` | **Art. 9 Abs. 2 lit. a i. V. m. Art. 6 Abs. 1 lit. a**, ausdrückliche Einwilligung (b), Widerruf im Konto. Ohne Einwilligung keine Speicherung bei uns, nur lokal auf dem Gerät | wie Konto bzw. bis zum Widerruf |
| Interessen und persönliche Empfehlungen | `praeferenzen` und die **Auswertung der Merkliste für Empfehlungen** (ohne sensible Events; die Speicherung der Merkliste selbst bleibt lit. b) | **lit. a**, Einwilligung (a) mit eigenem, nicht vorangekreuztem Häkchen auf der Abschlussseite (E12a, 5.3). Vor der Einwilligung wird nichts gespeichert. Widerruf im Konto leert `praeferenzen` sofort, die Merkliste bleibt | wie Konto bzw. bis zum Widerruf |
| Summen „was ist beliebt“ (E4) | Anzahl je Event, ohne Personenbezug im Ergebnis, **ohne sensible Events** | **lit. f** nach dokumentierter Interessenabwägung, Widerspruch im Konto und auf der Abschlussseite (Art. 21, gesonderter Hinweis) | wie Konto. Summen werden nicht gespeichert |
| Kennzeichnung sensibler Events | Merkmal am **Event**, nicht an Personen | kein Personenbezug | solange das Event gespeichert ist |
| Geburtsdatum und Geburtstagsmails (E15) | Geburtsdatum, Einwilligung, Datum des letzten Versands | **lit. a** und § 7 Abs. 2 UWG (Werbung per Mail nur mit ausdrücklicher Einwilligung), Widerruf im Konto oder per Abmeldelink in jeder Mail | bis zum Widerruf, dann Datum sofort gelöscht; spätestens mit dem Konto |
| Nutzungsbedingungen (E14) | akzeptierte Fassung, Zeitpunkt | lit. b | wie Konto |
| Protokoll der Anmeldungen (Supabase) | Nutzer-ID, Mail, IP, Zeitpunkt, **soweit die Plattform-Protokolle von Supabase sie führen** (belegt ist nur: heute nicht in `auth.audit_log_entries`, Schritt 1; Inhalt der Plattform-Protokolle prüft der Auftraggeber in Schritt 2) | lit. f (Sicherheit des Dienstes) | Plattform-Protokolle: die Aufbewahrungsdauer laut Supabase-Tarif (Frist aus Schritt 2; ohne ermittelte Frist wird nicht eingeschaltet, 4.6). Zeilen in `auth.audit_log_entries`, falls Supabase sie künftig schreibt: beim Löschen des Kontos sofort mit gelöscht (4.6) |
| Missbrauchsschutz | IP, gehashte Adresse im Speicher | lit. f | rund 1 Stunde, nur im Arbeitsspeicher |
| Mindestalter, Einwilligungsnachweis | `einwilligungen` mit Handlung, Zeitpunkt und Verweis auf den archivierten Wortlaut (`einwilligungstexte`) | Art. 7 Abs. 1, Art. 8 | wie Konto. Ob Nachweise nach der Kontolöschung länger aufbewahrt werden müssen (Verjährung möglicher Ansprüche), klärt die anwaltliche Durchsicht der Erklärung (Abschnitt 19) |
| Sitzungs-Cookie `ddd_sitzung` | Token | § 25 Abs. 2 Nr. 2 TDDDG: unbedingt erforderlich, damit eine ausdrücklich gewünschte Anmeldung über Seitenwechsel hinweg besteht | 30 Tage rollierend, Reset-Sitzung 1 Stunde |
| Anzeige-Cookie `ddd_konto` | „0“ oder „1“ | § 25 Abs. 2 Nr. 2 TDDDG: unbedingt erforderlich, damit die angemeldete Person auf öffentlichen (gecachten) Seiten den richtigen Merkzustand sieht, ohne dass bei jedem Seitenaufruf das Sitzungs-Cookie mitgeschickt wird (3.2, 3.5). Laufzeit gleich der Sitzung, gelöscht beim Abmelden. Begründung so in der Erklärung (rechtliche Einschätzung: der Inhalt allein macht es nicht einwilligungsfrei) | wie `ddd_sitzung` |
| Lokale Merkliste und Hilfsdaten (`localStorage`) | `ddd-merkliste`, `ddd-merkliste-geraet`, Spiegel, Warteschlange, Hinweis-Merker | § 25 Abs. 2 Nr. 2 TDDDG: vom Nutzer gewünschte Merkfunktion | bis zum Löschen durch den Nutzer bzw. Abmelden (Spiegel, Warteschlange) |

- **Zweckbindung:** Merkliste und Interessen dienen nur dem Konto, den eigenen Empfehlungen und den Summen. Für sie gilt: keine Werbung, keine Weitergabe an Veranstalter, keine Verknüpfung mit Google Analytics, kein Newsletter ohne eigene Anmeldung. Davon getrennt ist die Geburtstagsmail (E15): Sie ist Werbung und läuft nur mit der eigenen Einwilligung (d). Ihre Event-Tipps nutzen die Interessen nur, wenn auch (a) erteilt ist (13a).
- **Art. 9 DSGVO (rechtliche Einschätzung, Frage 1):** Aus Merkungen bestimmter Events lassen sich besondere Kategorien ableiten, auch ohne dass wir das tun. Umsetzung: Diese Events werden im Backend gekennzeichnet (E13, 4.8, 5.8). Ohne ausdrückliche Einwilligung bleiben ihre Merkungen nur auf dem Gerät. Sie fließen nie in Empfehlungen oder Statistik ein. Ein verpasster Treffer der Kennzeichnung ist das Restrisiko (Abschnitt 17). Dagegen helfen weit gefasste Regeln und die Sichtprüfung, für die „im Zweifel sensibel“ gilt (5.8). Zur Laufzeit gilt allein die Regeltabelle.
- **Interessenabwägung für die Zählung (E4):** Dokument `docs/interessenabwaegung-statistik-<datum>.md`, vor dem Einschalten geschrieben (Claude) und vom Auftraggeber freigegeben. Inhalt: Zweck (Programmplanung, Hervorheben beliebter Events), Erforderlichkeit, Datenminimierung (nur Summen, keine Nutzer-ID im Ergebnis, nur Admins, keine sensiblen Events), erwartbare Nutzung, Widerspruch per Schalter, Ergebnis der Abwägung.
- **DSFA-Schwellenwertprüfung (rechtliche Einschätzung, Frage 10):** Dokument `docs/dsfa-schwellenwert-nutzerkonten-<datum>.md` vor dem Einschalten. Es geht die Kriterien der DSFA-Liste der Aufsichtsbehörden und der EDSA-Leitlinien durch (sensible Daten, Profilbildung, Minderjährige ab 16, Umfang) und hält das Ergebnis fest. Ergibt es eine Pflicht zur vollständigen DSFA, wird nicht eingeschaltet, bevor sie vorliegt.

### 9.2 Auftragsverarbeiter und Pflichten des Auftraggebers
- **Supabase (rechtliche Einschätzung, Frage 7):** Frankfurt als Speicherort schließt Zugriffe aus Drittländern nicht aus. Vor dem Einschalten prüft und dokumentiert der Auftraggeber:
  - das aktuelle Data Processing Addendum (DPA) von Supabase ist abgeschlossen;
  - die passenden Standardvertragsklauseln (Modul 2, Verantwortlicher an Auftragsverarbeiter) sind enthalten;
  - eine kurze Transfer-Folgenabschätzung (TIA) für Supabase Inc. (Singapur/USA);
  - die Liste der Unterauftragsverarbeiter von Supabase;
  - die Aufbewahrungsfristen der Supabase-Logs und -Backups (auch Auth-Protokolle, 4.6).

  Auf das EU-US Data Privacy Framework verweist die Erklärung nur, wenn ein konkreter Empfänger zertifiziert ist und es tatsächlich als Grundlage dient. Vorlagen und Checkliste dafür liefert Claude in Schritt 2.
- **Mailversand über den eigenen Server (E3):** Der Hoster ist schon Auftragsverarbeiter für die Website. Der Auftraggeber prüft, ob der bestehende AV-Vertrag mit dem Hoster den Mailversand mit abdeckt, und ergänzt ihn sonst. Ein zusätzlicher Dienst entsteht nicht. Tracking gibt es beim eigenen Postfach nicht.
- Das **Verzeichnis der Verarbeitungstätigkeiten** (Art. 30) um „Nutzerkonten“ ergänzen.
- Datenschutz-Folgenabschätzung: Statt einer bloßen Einschätzung gibt es die dokumentierte Schwellenwertprüfung aus 9.1.

### 9.3 Löschung, Export, Inaktivität
- Jeder kann das Konto jederzeit selbst löschen (5.7), der Export ist eine JSON-Datei (Art. 15 und 20).
- **Unbestätigte Konten:** `signUp` legt schon vor der Bestätigung einen Eintrag in `auth.users` an, mit Adresse und Passwort-Hash. Der Aufräumjob löscht Einträge mit `email_confirmed_at IS NULL` und `created_at` älter als 48 Stunden. Er ist ein Python-Skript nach dem Muster von `pipeline/meldungen_aufraeumen.py`, mit demselben Aufrufort und dem Dienst-Client (`auth.admin`). **Einheitliche Formulierung überall** (Plan, Erklärung, Anwaltsdatei): „unbestätigt nach 48 Stunden, durch den Drei-Tage-Lauf der Pipeline spätestens nach fünf Tagen“. **Der Job ist live, bevor die Registrierung öffentlich wird** (gebaut in Schritt 7, live in Schritt 8 von Abschnitt 15). Admin-Konten (`rolle = 'admin'`) lässt er immer aus.
- **Bestätigt, aber ohne Alters-Bestätigung:** Konten mit bestätigter Adresse, ohne `mindestalter_bestaetigt_am` und mit `created_at` älter als **7 Tage** löscht derselbe Job, Admins ausgenommen. Die rechtliche Einschätzung hielt 30 Tage für begründungsbedürftig. Da das Alter jetzt im Registrierungsformular bestätigt wird (5.1), betrifft das vor allem Konten, die jemand am Formular vorbei angelegt hat (11.1), und Konten, deren Nachweis bei der Registrierung nicht gesetzt wurde (5.1 Schritt 2). Auch hier gilt der Drei-Tage-Lauf: „nach 7 Tagen, spätestens nach 10 Tagen“. Die Erklärung nennt diese Frist.
- **Gesperrt wegen Alter unter 16 (E15):** Konten mit gesetztem `unter16_gesperrt_am` löscht derselbe Job **beim nächsten Lauf**, unabhängig von `created_at`. Admins sind ausgenommen. Einheitliche Formulierung in Plan, Erklärung und Nutzungsbedingungen (§ 3 Abs. 2): „Ergibt ein angegebenes Geburtsdatum ein Alter unter 16 Jahren, sperren wir das Konto sofort und löschen es innerhalb von drei Tagen.“
- **Backups:** Gelöschte Daten bleiben bis zum Ablauf der Backup-Aufbewahrung von Supabase in deren Sicherungen (Frist aus 9.2). Die Erklärung nennt das. Eine Wiederherstellung aus einer Sicherung würde gelöschte Konten nicht reaktivieren, ohne dass der Löschlauf sie erneut entfernt.
- **Inaktivität:** `letzte_aktivitaet_am` älter als 23 Monate → Warnmail. Ist `letzte_aktivitaet_am` leer, zählt `profiles.erstellt_am`. Admin-Konten sind ausgenommen. Nach 24 Monaten wird gelöscht. Die Warnmail verschickt das Skript über das SMTP-Postfach unseres Servers (E3) mit `smtplib` aus der Standardbibliothek, ohne neue Bibliothek. Fällig wird das erstmals im Oktober 2028. Der Job muss bis dahin gebaut sein, gehört aber nicht zur ersten Runde (Abschnitt 19).

### 9.4 Datenschutzerklärung (Entwurf, Sie-Form, zur Freigabe vor dem Einschalten)
- **Neuer Abschnitt „Nutzerkonto“** (Anker `#konto`, verlinkt vom Anmeldeformular, 5.1) nach Abschnitt 12, mit dem Inhalt von 9.1: welche Daten, wozu, Rechtsgrundlagen, Speicherdauer, Supabase und Hoster (auch Mailversand) als Empfänger, Passwort nur als Hash bei Supabase, persönliche Empfehlungen als Einwilligung (a) auf der Abschlussseite und wie man sie widerruft, sensible Events: allgemeine Beschreibung der Arten, ausdrückliche Einwilligung (b), ohne sie nur lokale Speicherung, nie Empfehlungen oder Statistik, Summen-Auswertung mit Interessenabwägung und **gesondertem Hinweis auf das Widerspruchsrecht** (Art. 21 Abs. 4), Mindestalter 16, Nutzungsbedingungen, Geburtsdatum und Geburtstagsmails (freiwillig, Einwilligung, Abmeldung in jeder Mail, Löschen des Datums beim Widerruf, E15), Löschen und Export im Konto, Hinweis, dass der Export die Auskunft nach Art. 15 nicht ersetzt, Inaktivitätslöschung (auch für nie benutzte Konten ab Anlage), Löschung unbestätigter Konten (nach 48 Stunden, spätestens nach fünf Tagen) und bestätigter Konten ohne Alters-Bestätigung (nach 7, spätestens nach 10 Tagen), Sperre und Löschung bei einem Geburtsdatum unter 16 (innerhalb von drei Tagen), Backups (9.3), das Anmeldeprotokoll bei Supabase und seine Löschung bzw. Frist (4.6), Drittlandbezug von Supabase mit Grundlage (9.2).
- **Abschnitt 5 (Cookies):** Anmelde-Cookies `ddd_sitzung` und `ddd_konto` mit Zweck, Begründung der Erforderlichkeit und Laufzeit aus 9.1.
- **Abschnitt 7 (localStorage):** Der Satz „nicht an uns übermittelt“ gilt nur noch ohne Konto. Neu: „Wenn Sie angemeldet sind, wird Ihre Merkliste in Ihrem Konto gespeichert (Abschnitt Nutzerkonto); auf dem Gerät liegt dann nur eine Kopie, die beim Abmelden gelöscht wird.“ Außerdem neu: der Merker für den einmaligen Hinweis (7.2) und dass manche Merkungen ohne Einwilligung (b) nur auf dem Gerät bleiben (allgemein, ohne Events zu nennen).
- **Abschnitt 9 (Supabase):** Ergänzung „sowie Nutzerkonten und Merklisten“. Der Satz „Ihr Browser verbindet sich nicht direkt mit Supabase“ bleibt richtig.
- **Abschnitt 3 (Hosting):** ergänzen, dass der Hoster auch die Kontomails (Bestätigung, Passwort zurücksetzen, Hinweis vor der Inaktivitäts-Löschung) über seinen Mailserver versendet.
- **Abschnitt 14:** Hinweis auf Selbstbedienung im Konto.
- **Abschnitt 15 (Keine Weitergabe an Dritte):** ergänzen, dass Auftragsverarbeiter (Hosting einschließlich Mailversand, Supabase) Daten in unserem Auftrag nach Art. 28 DSGVO verarbeiten und das keine Weitergabe im Sinne dieses Abschnitts ist. Heute nennt der Abschnitt sie nicht, obwohl Supabase schon in Abschnitt 9 steht.
- **Stand** auf den Monat des Einschaltens setzen.

Der Wortlaut wird vor Schritt 6 als eigener Textblock zur Freigabe vorgelegt. Eine anwaltliche Durchsicht wird empfohlen.

---

## 10. E-Mail

### 10.1 Versand über den eigenen Server (E3)
- Supabase Auth verschickt die Mails nicht selbst, sondern über **SMTP unseres Servers** beim Hoster (Server `k49q02.meinserver.io`, Verwaltung über ISPConfig). Der Auftraggeber legt dort das Postfach `konto@diesdas.events` an, mit eigenem Passwort nur für den Versand.
- **Erreichbarkeit:** Supabase (AWS Frankfurt) muss den Mailserver von außen auf Port 587 (STARTTLS) oder 465 (TLS) erreichen und sich dort anmelden dürfen. Das prüft die erste Testmail in Schritt 2. Blockt der Hoster fremde Absender-IPs oder begrenzt er Mails pro Stunde, steht das in seinen Bedingungen. Der Auftraggeber fragt das beim Hoster ab (Abschnitt 19).
- **Zustellbarkeit hängt am Ruf unseres Servers.** Das ist der Preis für „kein zusätzlicher Dienst“. Pflicht dafür:
  - **SPF:** Der DNS-Eintrag von `diesdas.events` erlaubt den Mailserver des Hosters.
  - **DKIM:** In ISPConfig für `diesdas.events` einschalten und den öffentlichen Schlüssel als DNS-Eintrag setzen.
  - **DMARC:** zunächst `p=none; rua=mailto:…`, nach zwei Wochen sauberer Berichte `p=quarantine`.
  - **Reverse-DNS (PTR)** der Server-IP passt zum Hostnamen des Mailservers. Das stellt der Hoster.
  - Prüfen, ob die Server-IP auf einer Sperrliste steht (z. B. Spamhaus), vor dem Start und bei Zustellproblemen.
  - **TLS-Zertifikat:** Das Zertifikat des Mailservers passt zu genau dem Hostnamen, den der Auftraggeber in Supabase als SMTP-Host einträgt. Sonst bricht Supabase die Verbindung ab.
  - **Envelope-Absender (Return-Path):** Viele Hoster schreiben ihn auf den Servernamen um (z. B. `…@k49q02.meinserver.io`). Dann passt SPF nicht zur Absender-Domain, und DMARC scheitert, obwohl SPF für `diesdas.events` gesetzt ist. Der Return-Path muss `@diesdas.events` lauten, oder DKIM muss mit `d=diesdas.events` signieren, damit DMARC über DKIM besteht. In der Testmail die Kopfzeilen `Return-Path` und `DKIM-Signature: d=` prüfen.
  - **IPv6:** Versendet der Server über IPv6, braucht auch die IPv6-Adresse einen PTR-Eintrag und muss im SPF-Eintrag stehen (`ip6:`). Sonst lehnt Gmail ab. Alternativ versendet der Server nur über IPv4. Das klärt der Auftraggeber mit dem Hoster.
  - Kontrolle: Eine Testmail an Gmail, GMX/Web.de und Outlook.com zeigt `spf=pass`, `dkim=pass`, `dmarc=pass` und landet nicht im Spam (16.4).
- **Rückfall:** Kommen Mails trotz dieser Einträge dauerhaft im Spam an oder blockt der Hoster, wird ein EU-Versanddienst nachgerüstet. Für die Auth-Mails ist das nur eine andere SMTP-Zeile in Supabase, der Website-Code bleibt gleich. Zusätzlich nötig: den Dienst in den **SPF-Eintrag** aufnehmen, seinen DKIM-Schlüssel setzen und die **Zugangsdaten des Inaktivitäts-Jobs** umstellen, der per `smtplib` direkt sendet und der Supabase-Einstellung nicht folgt. Der Wechsel bräuchte eine neue Entscheidung (E3).
- Absender ist `dies.das.düsseldorf <konto@diesdas.events>`, Antwort-An `moin@rocktician.com`. Den Namen bestätigt der Auftraggeber. `hallo@diesdas.events` ist laut `rahmen.tsx` noch ungeprüft.
- Kein Tracking: Das eigene Postfach schreibt keine Links um und baut keine Zählpixel ein.
- Eine reine Textfassung braucht es nicht: Supabase verschickt HTML. Die Vorlagen sind deshalb schlicht, ohne Bilder von fremden Servern und mit lesbarem Text ohne CSS.
- Der spätere Inaktivitäts-Job (9.3) nutzt dasselbe Postfach. Die Zugangsdaten liegen dann auch in der `.env` des Jobs, nie im Code.

### 10.2 Supabase-Einstellungen (Auftraggeber, Werte aus diesem Plan)
- Authentication → **SMTP**: Host, Port, Benutzer `konto@diesdas.events` und Passwort des Postfachs auf unserem Server, Absendername „dies.das.düsseldorf“.
- **Site URL** `https://diesdas.events`. **Redirect URLs**: `https://diesdas.events/konto/bestaetigen`, `http://localhost:3100/konto/bestaetigen`, `http://localhost:3200/konto/bestaetigen`. Die Links in den Vorlagen bauen wir selbst aus `{{ .SiteURL }}` (10.3). Die Redirect-Liste ist nur eine Absicherung, falls Supabase doch selbst weiterleitet.
- **Email-Provider:** an. „Confirm email“ an. „Secure email change“ an. „Secure password change“ an (5.1 Schritt 12 ist darauf ausgelegt). „Allow new users to sign up“ an, **erst in Schritt 8** mit dem Schalter, nachdem der Aufräumjob einmal gelaufen ist.
- **Passwort:** Mindestlänge 10. Keine Pflicht zu Zeichenklassen. „Leaked password protection“ an, falls der Tarif sie hat (5.1, Abschnitt 19).
- **Mail-Token (Bestätigung, Reset, Ersatz-Code der Bestätigung):** 6 Stellen. Gültigkeit für die Bestätigung 24 Stunden, für Reset 1 Stunde, falls Supabase das getrennt erlaubt. Sonst einheitlich 1 Stunde, dann geht die Bestätigung über „Bestätigungsmail erneut senden“.
- **Rate Limits:** Mails pro Stunde **zum Start 20** (mit eigenem SMTP einstellbar). Hochgesetzt wird erst, wenn das Mail-Log eine Woche lang unauffällig war und echte Registrierungen an die Grenze stoßen. Verify-Limit: Zahl und Zählweise im Vorversuch festhalten (5.1 Schritt 13), nicht lockern.
- **Mail-Log in den ersten Tagen:** In den ersten sieben Tagen nach dem Einschalten schaut der Auftraggeber täglich, noch am selben Tag, ins Mail-Log des Servers bzw. in die Auth-Logs von Supabase: Zahl der Mails, Häufung an fremde Adressen, Bounces. Bei Auffälligkeiten wird der Schalter `KONTEN_AKTIV` ausgeschaltet und „Allow new users to sign up“ abgeschaltet.
- **Sitzungen:** JWT-Laufzeit 3.600 Sekunden, Rotation der Refresh-Token an, Reuse-Intervall 10 Sekunden.

### 10.3 Vorlagen (Entwurf, ihr-Form; Endfassung als `docs/konto-mails-<datum>.md` zur Freigabe)
Angepasst werden **Confirm signup** und **Reset Password** (beide in Gebrauch), dazu **Change Email Address** (für später) und **Reauthentication** (für „Secure password change“). **Magic Link** wird nicht genutzt, bekommt aber einen neutralen deutschen Text. Reset Password gilt auch für die Admin-Konten des Dashboards (5.1 Schritt 11).

**Confirm signup**
> **Betreff:** Bitte bestätigt eure Mailadresse für dies.das
>
> Hallo!
> Schön, dass ihr ein Konto bei dies.das.düsseldorf anlegt. Bitte bestätigt eure Mailadresse:
> [Adresse bestätigen] → `{{ .SiteURL }}/konto/bestaetigen#token_hash={{ .TokenHash }}&art=neu`
> Klappt der Knopf nicht? Dann gebt auf der Seite eure Mailadresse und diesen Code ein: **{{ .Token }}** *(Zeile nur, wenn der Vorversuch ein Verify-Limit je Adresse zeigt, 5.2)*
> Der Link gilt einmal. Ihr habt kein Konto angelegt? Dann ignoriert diese Mail einfach, es passiert nichts.
> dies.das.düsseldorf · Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf

**Reset Password**
> **Betreff:** Neues Passwort für dies.das
>
> Hallo!
> Jemand möchte das Passwort für euer Konto bei dies.das.düsseldorf zurücksetzen. Wart ihr das? Dann legt hier ein neues fest:
> [Neues Passwort festlegen] → `{{ .SiteURL }}/konto/bestaetigen#token_hash={{ .TokenHash }}&art=reset`
> Klappt der Knopf nicht? Dann fordert auf der Website einfach einen neuen Link an.
> Der Link gilt eine Stunde und einmal. Wart ihr das nicht? Dann ignoriert diese Mail. Euer Passwort bleibt, wie es ist.
> dies.das.düsseldorf · Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf

Nie `{{ .ConfirmationURL }}` (5.2). Die Endfassung kommt zusammen mit den übrigen Vorlagen als Datei zur Freigabe.

**Endfassung zur Freigabe: `docs/konto-mails-2026-11-16.md`** (16.11.2026, Schritt 2). Sie enthält alle sechs Supabase-Vorlagen: Confirm signup, Reset Password, Reauthentication, Change Email Address, Magic Link und Invite user.
- Abweichung zur Freigabe: **Change Email Address, Magic Link und Invite user enthalten keinen Link.** Mailänderung gibt es in dieser Runde nur per Mail an uns (19, Punkt 4). Magic Link und Einladung nutzen wir nicht. Ohne Link lässt sich nichts bestätigen, auch wenn jemand diese Mails mit seinem eigenen Token direkt bei Supabase auslöst.
- Die Zeile mit dem Ersatz-Code steht als eigener Block daneben und wird erst nach dem Vorversuch eingetragen, nicht als HTML-Kommentar: Supabase würde den Code sonst in den Quelltext schreiben.

---

## 11. Sicherheit

### 11.1 Missbrauch
- Bremslimits wie in Abschnitt 6, Honeypot im Adressformular, eine Antwort, die nichts über bestehende Konten verrät.
- **Passwörter erraten (Brute Force, Credential Stuffing):**
  - unser Bremslimit je Adresse (5 Fehlversuche in 15 Minuten, danach Pause mit derselben Meldung) und je IP (Abschnitt 6);
  - dazu das eigene Limit von Supabase für Anmeldeversuche;
  - Mindestlänge 10 und, wenn der Tarif es erlaubt, die Prüfung gegen geleakte Passwörter (5.1);
  - nach jedem Passwortwechsel werden andere Sitzungen beendet (3.2).

  Eine Zwei-Faktor-Anmeldung gibt es in dieser Runde nicht (Abschnitt 19).
- **Konto-Ausspähen (Enumeration):** Registrieren, „Passwort vergessen“ und „Bestätigungsmail erneut senden“ antworten immer gleich. Anmelden meldet immer „Mailadresse oder Passwort stimmen nicht“ (Ausnahme nur bei richtigem Passwort, 5.1 Schritt 6). Bei messbaren Zeitunterschieden gibt es eine Mindestdauer (5.1 Schritt 13).
- **Signup direkt bei Supabase:** Der anon-Key steht nicht im Browser-Bundle, gilt aber als öffentlich (er ist für Clients gedacht und liegt auch beim Dashboard). Sobald „Allow new users to sign up“ an ist, nimmt Supabase `signUp` damit an, **auch wenn `/api/konto/*` noch 404 liefert**. Die Dashboard-Einstellung ersetzt also nicht den Schalter, und umgekehrt. Folgen und Absicherung: Unbestätigte Konten räumt der Job ab (9.3). Ein so bestätigtes Konto hat das Registrierungsformular nie gesehen, also auch kein Alters-Häkchen und keine akzeptierten Nutzungsbedingungen. Es bekommt von unseren Routen 403 `mindestalter_fehlt` (6), die Policy auf `merkliste` verlangt das Mindestalter (4.3), Einwilligungen kann es mit dem JWT nicht setzen (4.1, 4.5). Es kann also nichts speichern außer `anzeigename`, `onboarding_fertig_am` und `letzte_aktivitaet_am`, und der Job löscht es nach 7 Tagen (9.3). Sensible Events kann es ohnehin nicht speichern (4.3).
- **Mail-Bombing über den öffentlichen anon-Key:** Wer Supabase direkt anspricht (`signUp`, `resend`, `resetPasswordForEmail`), umgeht unser Bremslimit und den Honeypot. Dagegen helfen das 60-Sekunden-Limit je Adresse von Supabase und das projektweite Stundenlimit (10.2). Beim Versand über den eigenen Server kommt ein Risiko dazu: Massenhaft Mails an fremde Adressen können den **Ruf unseres Mailservers** beschädigen, und davon wären auch andere Mails der Domain betroffen. Deshalb startet das Stundenlimit in Supabase bei 20, und das Mail-Log wird in den ersten sieben Tagen täglich noch am selben Tag geprüft (10.2). Bei Auffälligkeiten werden Schalter und Signup abgeschaltet. Ein CAPTCHA (Turnstile, hCaptcha) würde den Browser an Dritte binden und ist deshalb nicht vorgesehen. Das Restrisiko wird hingenommen und beobachtet (Abschnitt 17).
- Spam-Konten: Unbestätigte Konten werden gelöscht (9.3). Bestätigte Konten können nichts Öffentliches schreiben.

### 11.2 Angriffe auf die Sitzung
- **CSRF:** Ändernde Routen mit Cookie verlangen, dass `Origin` gleich `SITE_URL` ist (lokal `http://localhost:3100` bzw. 3200), sowie `Content-Type: application/json`. Zusammen mit `SameSite=Lax` reicht das.
- **XSS:** Die Tokens sind `HttpOnly`. Die Website rendert keinen fremden HTML-Code neu, die bestehenden Regeln gelten.
- **Offener Redirect:** `weiter` wird geprüft (5.1).
- **Rechte:** Spaltenrechte auf `profiles` (4.1) und RLS auf den neuen Tabellen. Die Prüfung in Schritt 1 schließt alte Lücken, bevor die Registrierung öffentlich wird.

### 11.3 Admin-Konten
- Sie liegen im selben Auth-Projekt. Die Website-Routen fassen nur Konto-Tabellen an. Ein Admin, der sich auf der Website anmeldet, bekommt dort keine Admin-Funktion.
- Die Mindestlänge 10 prüft Supabase nur beim Setzen eines Passworts (`signUp`, `updateUser`), nicht bei `signInWithPassword`. Bestehende kürzere Admin-Passwörter bleiben gültig, bis sie geändert werden. Das Dashboard (`dashboard/auth.py`, Zeile 59) ruft kein `updateUser` auf, „Secure password change“ betrifft es also nicht. Empfehlung an die Admins: beim nächsten Wechsel mindestens 10 Zeichen.
- Admin-Konten lassen sich nicht über die Website löschen (4.6). Die Passwort-Anmeldung des Dashboards bleibt unberührt. Test 16.3, Punkt 8.

---

## 12. SEO
- `/konto/*`: `noindex, nofollow` per Metadata **und** `X-Robots-Tag: noindex` über `headers()` in `next.config.ts`, als **zweiter Eintrag im bestehenden Array** (`source: "/konto/:pfad*"`) neben der HSTS-Regel. Eine zweite `headers()`-Funktion würde HSTS ersetzen (1.5). Test: `curl -I /` zeigt weiter `Strict-Transport-Security`, `curl -I /konto` zusätzlich `X-Robots-Tag`. Nicht in Sitemap und `llms.txt`.
- **Kein** `Disallow` in `robots.ts`, sonst sieht Google das `noindex` nicht. `/api/` bleibt gesperrt.
- Öffentliche Seiten bleiben gleich (3.5). Kein Anmelde-Popup beim Seitenaufruf, der Hinweis in 7.2 kommt nur nach einem Klick.
- `/merkliste` bleibt `noindex`.

---

## 13. Persönliche Empfehlungen (Phase 2, eigene Freigabe)
In dieser Runde werden nur die Daten gesammelt. Die Anzeige folgt nach eigener Freigabe. Grundregeln, damit Datenmodell und Fragebogen jetzt schon passen:
- „Für euch“ steht als Zeile auf `/konto` und auf `/merkliste` und wird clientseitig über `GET /api/konto/fuer-euch` geladen. Die Startseite bleibt gecacht. Eine Zeile dort käme nur als nachgeladene Client-Insel und nach eigener Prüfung.
- Kandidaten sind Events der nächsten 14 Tage aus `eventPoolLaden()`, nicht abgesagt, mit `breite()` von mindestens 1, ohne Stamm, ohne schon Gemerktes.
- **Eingaben nur mit Einwilligung (a) und nie aus sensiblen Events (E13):** Gemerkte Events, die in `event_sensibel` stehen, gehen nicht in die Punkte ein (gleiche Reihe, gleicher Ort). Die Berechnung läuft serverseitig mit dem Dienst-Client, der `event_sensibel` lesen darf. Das Ergebnis enthält keinen Hinweis darauf.
- Punkte: Unterkategorie trifft +3, Kategorie trifft +2, Stadtteil +1, Merkmal +1 (z. B. kostenlos, Familie bei „mit Kindern“), gleiche Reihe oder gleicher Ort wie ein gemerktes Event +1. Bei Gleichstand gilt der Sortierschlüssel a) bis e) aus dem Empfehlungs-Plan.
- Mit `personalisierung = false` gibt es die Zeile nicht.
- Die Funktion ist rein und getestet (`lib/fuer-euch.ts`).

### 13a. Geburtstagsmails (E15, eigener Schritt nach dem Start)
In dieser Runde werden Geburtsdatum und Einwilligung erhoben und gespeichert (5.3 (d)). Der Versand folgt als eigener Schritt mit eigener Freigabe. Grundregeln:
- **Versandjob:** Python-Skript `pipeline/geburtstag_mails.py` mit `smtplib` aus der Standardbibliothek über das Postfach unseres Servers (E3, 10.1). Es läuft täglich um 9:00 Uhr `Europe/Berlin` über einen eigenen GitHub-Actions-Workflow `geburtstag.yml`. Der bestehende Scrape-Lauf kommt nur jeden dritten Tag durch, deshalb ein eigener Workflow. Die SMTP-Zugangsdaten liegen als Secrets.
- **Empfänger:** Konten mit `geburtstagsmail = true`, `unter16_gesperrt_am IS NULL`, `mindestalter_bestaetigt_am IS NOT NULL`, Tag und Monat von `geburtsdatum` gleich heute, `geburtstagsmail_zuletzt` nicht in diesem Jahr. Wer am 29. Februar Geburtstag hat, bekommt die Mail in Nicht-Schaltjahren am 28. Februar. Gegen Doppelversand siehe unten.
- **Inhalt:** Glückwunsch, bei Einwilligung (a) bis zu drei Event-Tipps für den Tag nach Abschnitt 13, sonst drei Tipps nach den allgemeinen Empfehlungen der Startseite (`web/lib/ableitungen.ts`). Keine sensiblen Events (E13). Absender wie 10.1, ihr-Form, schlicht, ohne Bilder von fremden Servern, ohne Zählpixel.
- **Abmelden** (Pflicht bei Werbung, § 7 Abs. 3 Nr. 4 UWG sinngemäß, Art. 7 Abs. 3 DSGVO): Jede Mail hat einen Link auf `/konto/geburtstag-abmelden#t=<Token>`. Das Token ist ein HMAC über Nutzer-ID und Zweck mit einem Server-Geheimnis, ohne Ablauf und nur für diesen Zweck. Die Seite ist eine statische Hülle wie in 7.4 (noindex, kein `cookies()`, `headers()` oder `connection()`), liest das Token per Skript aus dem Fragment und zeigt einen Knopf „Keine Geburtstagsmails mehr“. Erst der Klick schickt `POST /api/konto/geburtstag-abmelden` mit dem Token im Body (nicht schon beim Aufruf, wegen der Link-Scanner, 5.2).
  - **One-Click für Mailprogramme:** Die Kopfzeilen `List-Unsubscribe: <https://diesdas.events/api/konto/geburtstag-abmelden/<Token>>` und `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (RFC 8058) zeigen auf eine **eigene POST-Adresse mit dem Token im Pfad**, weil Mailprogramme kein Fragment senden und kein Skript ausführen. `GET` auf diese Adresse ändert nichts und antwortet 405. **Das Token steht damit im Access-Log von nginx. Das ist bewusst hingenommen:** Es eröffnet keine Sitzung und kann nur die Geburtstagsmail abbestellen. Es gehört deshalb **nicht** ins Fragment zurück, sonst funktioniert One-Click nicht. Beide Wege rufen `einwilligung_setzen('geburtstagsmail', false, handlung = 'abmeldelink')` auf und löschen damit das Geburtsdatum.
  - Beide Routen stehen in der Routentabelle (Abschnitt 6), werden aber erst in Schritt 9a gebaut. Sie brauchen keine Anmeldung, haben ein Bremslimit von 30 je IP und Stunde und antworten bei ausgeschaltetem `KONTEN_AKTIV` wie alle Konto-Routen mit 404.
- **Doppelversand ausschließen:** Der Job beansprucht jede Mail vor dem Versand mit `UPDATE public.profiles SET geburtstagsmail_zuletzt = <heute> WHERE id = … AND geburtstagsmail AND (geburtstagsmail_zuletzt IS NULL OR geburtstagsmail_zuletzt < date_trunc('year', <heute>)) RETURNING id`. Nur bei einer zurückgegebenen Zeile geht die Mail raus. So schickt auch ein zweiter, gleichzeitiger Lauf nichts doppelt. Schlägt der Versand danach fehl, wird `geburtstagsmail_zuletzt` auf den alten Wert zurückgesetzt und die Mail beim nächsten Lauf am selben Tag erneut versucht.
- **Push** kommt erst mit der App (E15). Dort mit eigener Einwilligung über die Push-Freigabe des Betriebssystems.
- Tests (im Versand-Schritt): Auswahl der Empfänger, 29. Februar, kein Doppelversand, Abmeldetoken fälschungssicher, Abmeldung löscht das Datum, keine sensiblen Events in den Tipps.

**Phase 3:** Statistik im Dashboard, Reiter „Meistgemerkt“, über `merk_statistik()`. Eine öffentliche Anzeige wie „42 haben das gemerkt“ kommt nur nach eigener Entscheidung und frühestens ab 5 Personen.

---

## 14. Kosten
- **Supabase Auth:** Konten sind im Tarif enthalten. Free: 50.000 aktive Nutzer im Monat, Pro: 100.000 (Stand des Wissens, im Dashboard prüfen, welcher Tarif läuft). Keine Zusatzkosten zu erwarten.
- **Mailversand (E3):** über das Postfach auf unserem eigenen Server, im Hosting enthalten, 0 € zusätzlich. Falls der Hoster ein Stundenlimit für Mails hat, steht es in seinen Bedingungen (Abschnitt 19).
- **Speicher:** Eine Merkliste-Zeile hat rund 100 Byte. Selbst 10.000 Konten mit je 50 Einträgen sind etwa 50 MB inklusive Index, gut im Tarif.
- **Bibliotheken:** keine neuen, 0 €.
- **Rechtsberatung** (empfohlen): extern, nicht geschätzt.

---

## 15. Ablauf und Freigaben

| Schritt | Inhalt | Wer | Freigabe/Ergebnis |
|---|---|---|---|
| 0 | Dieser Plan, Cursor-Prüfung, alle Entscheidungen (E1–E4, E12–E14, getroffen 16.11.2026) | Auftraggeber | **Plan freigegeben** |
| 1 | Rechte-Prüfung `database/konten_rechte_pruefung_<datum>.sql` (nur SELECT, mit Whitelist aus 4.0), dazu eine SELECT-Abfrage auf `auth.audit_log_entries` für die Payload-Felder (4.6). Ergebnis zurück, gegebenenfalls Härtungs-SQL | Claude schreibt, Auftraggeber führt aus | Keine offene Lücke für `authenticated`. Weg für das Audit-Log festgelegt. **Erledigt 16.11.2026:** einziger Treffer TRUNCATE/REFERENCES/TRIGGER, Härtung `konten_haertung_2026-11-16.sql` ausgeführt, zweite Prüfung ohne LÜCKE (4.0). Audit-Log: eigener Löschweg geht, Tabelle leer, Plattform-Protokolle (4.6) |
| 2 | Postfach `konto@diesdas.events` auf unserem Server, Fragen an den Hoster (Erreichbarkeit von außen, Mail-Limit, PTR), DNS (SPF, DKIM, DMARC), SMTP in Supabase, Auth-Einstellungen 10.2 (Signup **noch aus**), Vorlagen 10.3, AV-Verträge, **Supabase-Unterlagen aus 9.2** (DPA, Standardvertragsklauseln, TIA, Unterauftragsverarbeiter, Log- und Backup-Fristen) | Auftraggeber (Claude liefert Texte und Checkliste) | Testmail kommt an, DKIM/SPF/DMARC „pass“, Supabase-Unterlagen abgelegt. **Unterlagen geliefert 16.11.2026:** `docs/schritt2-checkliste-nutzerkonten-2026-11-16.md` (Ablauf A–J samt Hoster-Anfrage und Rückmeldebogen), `docs/konto-mails-2026-11-16.md`, `docs/supabase-unterlagen-vorlagen-2026-11-16.md` (TIA, Verzeichnis-Eintrag) |
| 3 | `database/konten_<datum>.sql` (4.1–4.5, 4.8 mit `sensibel_regeln` samt Startregeln und Trigger auf `events`, **noch ohne Zeilen** in `einwilligungstexte`; die kommen erst in Schritt 6 nach der Freigabe der Wortlaute). Dazu liegt eine **Rückbau-Datei** `database/konten_rueckbau_<datum>.sql` bei: Teil 1 entfernt nur den Sensibel-Trigger auf `events` (`DROP TRIGGER IF EXISTS events_sensibel_pruefen ON public.events`), für den Fall, dass er die Pipeline stört (Abschnitt 17). Teil 2 entfernt alle neuen Objekte dieser Migration, nur nach ausdrücklicher Entscheidung. Den Sensibel-Trigger führt der Auftraggeber außerhalb eines Pipeline-Laufs aus | Claude schreibt, Auftraggeber führt aus | Kontrollabfrage grün, SQL-Tests 16.2 grün, ein Testlauf der Pipeline (`--dry-run` bzw. ein einzelnes Test-Event) speichert normal. **Geschrieben 16.11.2026:**<br>• `database/konten_2026-11-16.sql` (mit Kontrollabfrage samt 28 Muster-Tests einschließlich der Umlaute)<br>• `database/konten_tests_2026-11-16.sql` (16.2 als Testlauf mit erzwungenem Rückrollen; nicht abgedeckt sind die Fälle, die eine Route brauchen)<br>• `database/konten_rueckbau_2026-11-16.sql`<br>Ausführung durch den Auftraggeber steht aus |
| 4 | Zuerst der **Vorversuch** (5.1 Schritt 13) mit Testadressen: Typ des Bestätigungslinks, Mail bei schon registrierter Adresse, `email_not_confirmed` nur bei richtigem Passwort, Antwortzeiten. Ergebnis in den Plan. Dann Server: Reparatur von `zuVieleAnfragen` (6), `lib/konto/*` (Sitzung, Nutzer-Client, Prüfungen), API-Routen mit 404 bei Schalter aus und 403 ohne Mindestalter, Tests 16.1 | Claude (Vorversuch braucht Schritt 2) | Typ-Regel eingetragen, `npm test` und Build grün, Speicher-Test. **Reihenfolge geändert auf Wunsch des Auftraggebers (16.11.2026):** Schritt 2 setzt er später um. Bis dahin baut Claude weiter: Schritt 3, dann der Server-Teil von Schritt 4, dann Schritt 5, jeweils lokal und ohne Deploy. Der Vorversuch und die Typ-Regel (5.1 Schritt 13) folgen, sobald Schritt 2 erledigt ist und 19.14 entschieden ist. Bis dahin bleibt die Typ-Regel in den Routen als Annahme markiert. Schritt 8 setzt alles voraus.<br>**Server-Teil gebaut am 16.11.2026** (lokal, nichts deployt):<br>• `zuVieleAnfragen` repariert (`lib/formulare.ts`)<br>• `lib/konto/*` und alle 17 Routen unter `app/api/konto/` aus Abschnitt 6, ohne `geburtstag-abmelden` (Schritt 9a)<br>• `tests/konto.test.ts` mit 84 Tests<br>• `npm test` grün (347 Tests)<br>Offen: Vorversuch, Speicher-Test (braucht die Migration und einen laufenden Server), Umsetzungsdetails siehe 20 |
| 5 | Oberfläche: Seiten, Fragebogen, Herz-Store, Übernahme, Hinweise, Kopf, Menü, Fuß, Schalter | Claude | Browser-Prüfung 16.3 lokal. **Gebaut am 16.11.2026** (lokal, nichts deployt):<br>• Store `lib/konto/merk-logik.ts` und `merk-store.ts`<br>• Seiten unter `app/konto/`<br>• `components/konto*.tsx` und `interessen-fragebogen.tsx`<br>• Merkliste, Kopf, Menü, Fuß, Layout, `X-Robots-Tag`<br>• 16 weitere Tests, `npm test` grün (363)<br>Browser-Prüfung nur abgemeldet (ohne ausgeführte Migration und ohne Schritt 2 nicht weiter möglich). Offen: Abläufe angemeldet (16.3), `/nutzungsbedingungen` (Schritt 6) |
| 6 | Rechtstexte: Datenschutzerklärung (9.4), Nutzungsbedingungen (E14, Entwurf liegt vor), Einwilligungstexte (5.3), Interessenabwägung (E4) und DSFA-Schwellenwertprüfung (9.1). Danach **anwaltliche Durchsicht** von Erklärung, Nutzungsbedingungen und Einwilligungstexten | Claude schreibt, Anwalt prüft, Auftraggeber gibt frei | Wortlaute freigegeben, Versionen in `einwilligungstexte` eingetragen |
| 7 | **Sensibel-Nachtrag:** `database/sensibel_nachtrag_<datum>.sql` (Teil 1 Vorschau zur Sichtprüfung durch den Auftraggeber, Teil 2 INSERT, 5.8). Regeln und Trigger kommen schon mit Schritt 3. Dazu der Aufräumjob für drei Klassen (9.3): unbestätigte Konten (48 Stunden), bestätigte Konten ohne Alters-Häkchen (7 Tage) und **wegen Alter unter 16 gesperrte Konten (beim nächsten Lauf ab `unter16_gesperrt_am`)**, außerdem, wenn Schritt 1 das Löschrecht bestätigt hat, für Audit-Zeilen nicht mehr existierender Nutzer (4.6). Lokal mit `--dry-run` gegen die echte Datenbank | Claude | Probelauf zeigt die richtigen Kandidaten, keine Admin-Konten, keine Zeilen lebender Konten |
| 8 | Cursor-Prüfung der Umsetzung → Deploy **mit Schalter aus** (Code, Job) → live prüfen: `/api/konto/ich` gibt 404, öffentliche Seiten wie in 3.5, erster Job-Lauf im Log → Rechte-Prüfung `konten_rechte_pruefung_2026-11-16.sql` noch einmal, ohne LÜCKE (4.0) → Signup an + Schalter an + Datenschutz und Nutzungsbedingungen live → Abnahme 18 | Claude, Auftraggeber | **zwei getrennte Deploy-OKs** (aus, dann an). Signup erst, wenn der Job einmal gelaufen ist und der Sensibel-Nachtrag (Schritt 7) durch ist. Signup im Supabase-Dashboard und Schalter `KONTEN_AKTIV` werden **im selben Zug** eingeschaltet. Das eine ersetzt das andere nicht (11.1). |
| 9 | Phase 2 „Für euch“ (Abschnitt 13) | eigener Mini-Plan | eigene Freigabe |
| 9a | Geburtstagsmails (Abschnitt 13a): Versandjob, Workflow, Abmeldeseite, Mailvorlage | Claude, eigener Mini-Plan | eigene Freigabe, Vorlage zur Freigabe |
| 10 | Phase 3 Dashboard-Statistik | eigener Mini-Plan | eigene Freigabe |

Jeder Push ist ein Live-Deploy. Gepusht wird nur nach ausdrücklichem OK.

---

## 16. Tests

### 16.1 Unit-Tests (`web/tests/konto.test.ts`, vitest)
- `vorliebenPruefen`: unbekannte Kategorie, Unterkategorie und Stadtteil fallen raus. `sonstiges` fällt raus. `musik/jazz` bleibt. Mehr als 60 Einträge werden gekappt. Ohne `version` wird 1 gesetzt. Kein Objekt → Fehler.
- `uebernahmeVorbereiten` (Server): UUID-Filter, `beispiel-e1` und unbekannte UUIDs → `ungueltig`, Doppelte raus. 1.001 IDs → 413, nichts geschrieben. Dublette mit auflösbarem `ziel` → `umgeschrieben: { von, nach }`. Dublette mit nicht auflösbarem `ziel` → Ursprungs-ID übernommen, kein Eintrag in `umgeschrieben`.
- **Merkliste-Darstellung (E9):** Kommende Events nach Datum sortiert, vergangene eingeklappt unter „Vorbei (n)“ mit richtiger Anzahl. Ein mehrtägiges Event mit `datum_bis` ab heute gilt als kommend.
- **Zeitfenster bei der Registrierung:** `created_at` = Eingang − 61 s → kein Nachweis. Eingang − 30 s → Nachweis. Eingang + 4 s (vorgehende Uhr) → Nachweis. Eingang + 6 s → kein Nachweis.
- Store-Logik (reine Funktion): abgemeldet → `ddd-merkliste`. Angemeldet → Spiegel. Abmelden → Spiegel leer.
- `weiterPruefen`: `/merkliste` ja. `//evil.example`, `https://evil.example`, `/\evil`, `javascript:` und Pfade mit Steuerzeichen werden zu `/merkliste`.
- `sitzungsCookie`: `HttpOnly`, `SameSite=Lax`, `Path=/api/konto`, `Secure` außer auf localhost, `Max-Age` 30 Tage. Das Hinweis-Cookie ist nicht `HttpOnly`, hat `Path=/` und den Inhalt „0“ (angemeldet, Alters-Häkchen fehlt) bzw. „1“ (Häkchen gesetzt). Der Wechsel von „0“ auf „1“ folgt nach dem Speichern des Alters-Häkchens. Die Reset-Sitzung setzt kein `ddd_konto`, trägt `nur_passwort: true` und hat `Max-Age` 1 Stunde (5.1 Schritt 9).
- `tokenLaeuftAb`: `exp` minus 60 Sekunden, abgelaufenes und kaputtes JWT → erneuern bzw. abmelden.
- `originErlaubt`: gleicher Ursprung ja, fremder nein, Bearer ohne Origin ja.
- Schlüssel fürs Bremslimit: Adressen nur als Hash, Groß- und Kleinschreibung gleich.
- Texte: Hinweiskasten nur abgemeldet und mit Schalter an. Untertitel „In eurem Konto gespeichert“ nur angemeldet.
- **Übernahme (5.4), reine Funktion `geraetelisteNachUebernahme`:**
  - `merkliste_begonnen_am` leer, Konto leer, Gerät 3 → automatisch, alle 3 übernommen (`vollstaendig: true`), Geräteliste leer.
  - Konto hat 400, Gerät 600 (davon 50 schon im Konto), Übernahme per Knopf → 100 übernommen, die übrigen 450 bleiben auf dem Gerät, `vollstaendig: false`. Bei `vollstaendig: true` gilt dieselbe Regel: entfernt wird nur, was in `konto` oder `ungueltig` steht.
  - `ungueltig` (z. B. `beispiel-e1`, unbekannte UUID) → vom Gerät entfernt, nie ins Konto.
  - `umgeschrieben { von: X, nach: Y }` und Y in `konto` → X verschwindet vom Gerät. Y fehlt in `konto` (Grenze erreicht) → X bleibt.
  - Antwort 500, 413, Netzfehler oder 401 → Geräteliste unverändert.
  - Konto hat Einträge, Gerät hat 4 andere → **keine** automatische Übernahme, Zustand „Nachfrage“ mit 4 IDs.
  - Konto ist leer, aber `merkliste_begonnen_am` gesetzt (früher geleert), Gerät hat 3 → **keine** automatische Übernahme, Nachfrage.
  - **Zwei Tabs übernehmen gleichzeitig:** Tab 1 hält die Sperre und übernimmt {A, B, C}, Tab 2 wartet und liest danach neu. Ergebnis: Konto hat A, B, C, Gerät leer, **kein** `DELETE`.
  - Herz-Klick „entfernen B“ in diesem Tab während der laufenden Übernahme von {A, B, C} → nach der Antwort `DELETE B`. Konto hat A und C.
  - Herz-Klick „merken D“ während der Übernahme → landet in der Warteschlange, nach der Übernahme `PUT D`.
  - Warteschlange [entfernen B, merken D] offen, dann 401 → Geräteliste ohne B, mit D. Warteschlange und Spiegel leer. Dasselbe beim Abmelden.
  - Warteschlange offen, Tab geschlossen, neuer Seitenaufruf → Arbeiter sendet die Einträge in Reihenfolge, jeder genau bis zum Erfolg.
  - Sperre: Warten länger als 30 Sekunden → dieser Tab tut nichts, Geräteliste und Warteschlange unverändert. Ersatz ohne Web Locks: fremdes Token im Merker → kein Schreiben bis zum Ablauf, eigenes Token → Arbeit, Merker danach gelöscht.
  - `ddd_konto=0` (Alters-Häkchen fehlt) → Gerätemodus, keine Übernahme. Nach gespeichertem Häkchen → Übernahme startet.
  - Antwort mit `bleiben_auf_geraet: [S]` → S wandert aus `ddd-merkliste` nach `ddd-merkliste-geraet`, erscheint **nicht** im Block „Nur auf diesem Gerät“, steht aber in der angezeigten Merkliste.
  - `PUT S` mit Antwort `{ gespeichert: 'geraet' }` → S aus dem Spiegel nach `ddd-merkliste-geraet`, Herz bleibt gefüllt, kein Hinweis.
  - Einwilligung (b) erteilt → einmaliger Upload von `ddd-merkliste-geraet`, übernommene IDs dort entfernt. Widerruf (b) → zurückgegebene IDs landen in `ddd-merkliste-geraet`.
  - Abmelden → `ddd-merkliste-geraet` bleibt, abgemeldete Ansicht zeigt `ddd-merkliste` ∪ `ddd-merkliste-geraet`.
  - Teilübernahme mit Abbruch vor dem ersten INSERT (413) → `merkliste_begonnen_am` leer, nächster Lauf Schritt 2. Nach mindestens einem INSERT → Schritt 3.
  - Herz-Fehler → Rücksprung. Bei 401 → Eintrag in die Geräteliste, Status abgemeldet. Bei 403 `mindestalter_fehlt` → Rücksprung, Ziel `/konto/willkommen`.
- **`weiterPruefen`** zusätzlich: `%2F%2Fevil.example`, `%252F%252Fevil.example`, `/%5Cevil`, `/%255Cevil`, `/a//b`, `/a%2Fb`, `%0d%0a`, kaputte Kodierung (`%E0%A4%A`) → `/merkliste`. `/event/kultur/abc?x=1` → bleibt.
- **`zuVieleAnfragen`**: Schlüssel X mit 1-Stunden-Fenster und Treffern vor 30 Minuten, danach ein Aufruf mit 15-Minuten-Fenster für Schlüssel Y nach mehr als 1 Minute → X zählt weiter (vorher gelöscht). Mehr als 10.000 lebende Schlüssel → die Map schrumpft auf unter 80 Prozent, die zuletzt genutzten bleiben. Bestehende Aufrufe für Newsletter und Event melden verhalten sich gleich.
- **`letzte_aktivitaet_am`**: zweiter Aufruf am selben Tag schreibt nicht. Jede angemeldete Route stößt den Merker an.
- **Erneuern**: Supabase meldet ein widerrufenes Refresh-Token → beide Cookies gelöscht, Antwort 401.
- **Schalter aus** → jede Route unter `/api/konto/*` gibt 404.
- **`registrieren`** (mit Supabase-Attrappe): neu, unbestätigt mit anderem Passwort, bestätigt (verschleiertes Objekt), bestätigt (Fehler „User already registered“), Supabase nicht erreichbar → in allen fünf Fällen Status 200, identischer Body ohne `user` und `error`.
- **Bremse beim Anmelden**: 5 Fehlversuche für (IP A, Adresse X) → 6. Versuch von A abgewiesen ohne Supabase-Aufruf, auch mit richtigem Passwort. Gleichzeitig (IP B, Adresse X) mit richtigem Passwort → Aufruf an Supabase, angemeldet.
- **Reset-Sitzung**: Cookie mit `nur_passwort: true` → jede Konto-Route außer `passwort-setzen` und `abmelden` antwortet 403 `passwort_setzen_noetig`. `Max-Age` 3600. Nach `passwort-setzen` normales Cookie ohne den Merker.
- **Client-Optionen**: Jeder anfragebezogene Auth-Client (Erneuern, Passwort ändern, Löschen) wird mit `persistSession: false`, `autoRefreshToken: false`, `detectSessionInUrl: false` erzeugt (Test über eine Fabrikfunktion `authClientAnfrage()`).
- **`abschluss`**: (a) nein, Antworten im Body → `praeferenzen` bleibt `{}`, Nachweis `personalisierung = false`. (a) ja → Reihenfolge `einwilligung_setzen('personalisierung', true)` vor `praeferenzen`. (b) ja/nein und Widerspruch ja/nein → je eine Nachweiszeile mit `handlung = 'abschlussseite'`, auch für „nein“. Fehler nach (a) beim Speichern von `praeferenzen` → Antwort nennt den gespeicherten Stand. Der zweite Aufruf ruft `einwilligung_setzen` nicht erneut für (a) auf, **schreibt `praeferenzen` aber erneut** und setzt `onboarding_fertig_am`. `textversion` aus Konstanten, ein `textversion` im Body wird ignoriert. Ohne Widerspruch → `analyse_erlaubt` wechselt von `false` auf `true`. Mit Widerspruch → bleibt `false`. (d) mit Datum vor 20 Jahren → gespeichert. (d) mit Datum vor 15 Jahren → `unter_16`, Datum nicht gespeichert, Alters-Häkchen entzogen und gesperrt, Meldung, keine weiteren Angaben gespeichert. `einstellungen` mit Art `analyse` vor `onboarding_fertig_am` → 409. `einstellungen` mit `{ art: 'geburtstagsmail', erteilt: true }` ohne Datum → 400. (d) ohne Häkchen, aber mit Datum im Body → Datum verworfen.
- **Fragebogen-Komponente**: Bis „Fertig“ auf der Abschlussseite geht keine Anfrage mit Antworten raus (Netzwerk-Attrappe zählt null Aufrufe). „Ohne Interessen weiter“ verwirft den Zustand. Keine der Antworten landet in `localStorage`.
- **Einwilligungstexte**: Die Prüfsumme jeder Text-Konstante im Code stimmt mit der Prüfsumme im Kommentar der SQL-Datei überein (4.4).
- **Keine Kennzeichnung im Browser**: Kein Route-Body und kein Server-Component-Prop enthält `sensibel`, `grund` oder den Inhalt von `event_sensibel` (Test über alle Konto-Routen mit Attrappe, Suche nach den Schlüsselwörtern im JSON).
- **`passwortPruefen`**: 9 Zeichen → abgewiesen, 10 → ok, 73 → abgewiesen, nur Leerzeichen → abgewiesen. Keine Zeichenklassen-Pflicht.
- **Fehlerabbildung**: jeder Supabase-Fehler bei `anmelden` außer `email_not_confirmed` → „Mailadresse oder Passwort stimmen nicht.“ `registrieren` und `passwort-vergessen` → immer die neutrale Meldung, auch bei Supabase-Fehler „schon registriert“.
- **Keine Passwörter in Logs**: Eine Route mit absichtlichem Fehler schreibt in die Konsole weder das Passwort noch den Body.
- **`passwort-aendern`** (mit Supabase-Attrappe): falsches aktuelles Passwort → 403 ohne `updateUser`. Richtiges → `updateUser` mit der frischen Sitzung, danach `signOut({ scope: 'others' })`, Cookie mit der frischen Sitzung.
- **`vorlieben`**: Reihenfolge `einwilligung_setzen('personalisierung', true)` vor dem Speichern von `praeferenzen`. `{ praeferenzen, interessen_ok: false }` → kein `praeferenzen`-Schreiben, Nachweis `false` (gleiche Schlüssel wie in der Routentabelle, Abschnitt 6).

### 16.2 SQL-Tests (Skript im SQL-Editor, zwei Testkonten A und B)
- A liest, schreibt und löscht nur eigene `merkliste`-Zeilen. Der Einfüge-Versuch mit `nutzer_id = B` scheitert.
- `anon` liest nichts aus `merkliste`, `einwilligungen` und fremden `profiles`.
- A kann `rolle` nicht ändern, weder per Spaltenrecht noch per Trigger. A kann `praeferenzen` mit 9 KB nicht speichern.
- Der 501. Eintrag scheitert mit `merkliste_voll`.
- `merk_statistik()` als A → Exception. Als `anon` → `permission denied` (kein EXECUTE). Als Admin → nur Summen, A mit `analyse_erlaubt = false` zählt nicht. Kontrollabfrage: `has_function_privilege('anon', 'public.merk_statistik(date,date)', 'EXECUTE')` und dasselbe für `public` ergeben `false`. Für `konto_protokoll_loeschen` gilt das auch für `authenticated`.
- Erster Eintrag von A **als Nutzer A** (im SQL-Editor mit `SET LOCAL ROLE authenticated` und `SET LOCAL request.jwt.claims = '{"sub":"<A>","role":"authenticated"}'`) setzt `merkliste_begonnen_am`. Nach dem Löschen aller Einträge bleibt der Wert. Ein abgewiesener INSERT (501. Eintrag, fehlendes Mindestalter) lässt die Spalte leer. Erneutes Merken eines schon gemerkten Events bei vollem Konto (`ON CONFLICT DO NOTHING`) → kein Fehler.
- Neues Konto über die Route `registrieren` → `mindestalter_bestaetigt_am` und `nutzungsbedingungen_version` gesetzt, zwei Nachweiszeilen `handlung = 'registrierung'`. `signUp` direkt mit dem anon-Key und erfundener Version in den Metadaten → nichts gesetzt, keine Nachweiszeile.
- Neues Konto direkt nach der Registrierung (vor der Abschlussseite) → `analyse_erlaubt = false`, `merk_statistik` zählt es nicht. Nach „Ohne Interessen weiter“, ohne (a), ohne (b), ohne Widerspruch, ohne (d) → `personalisierung = false`, `sensible_events_erlaubt = false`, `analyse_erlaubt = true`, `geburtstagsmail = false`, `geburtsdatum IS NULL`, `praeferenzen = {}`, je eine Nachweiszeile mit `erteilt = false` bzw. `true` für `analyse`.
- **Geburtsdatum:** Update mit `geburtsdatum` gesetzt, aber `geburtstagsmail = false` → CHECK-Verstoß. `geburtstag_setzen(A, <heute minus 15 Jahre>)` → `unter_16`, Datum nicht gespeichert, `mindestalter_bestaetigt_am IS NULL`, `unter16_gesperrt_am` gesetzt, Nachweiszeile mit `handlung = 'altersgrenze'`. Danach `einwilligung_setzen(A, 'mindestalter', true)` → abgelehnt. Der Aufräumjob nennt A im nächsten Probelauf, unabhängig von `created_at`. Grenzfall: Datum genau heute vor 16 Jahren → gilt als 16, wird gespeichert. Datum morgen vor 16 Jahren → `unter_16`. `einwilligung_setzen(A, 'geburtstagsmail', true)` → abgelehnt (nur `geburtstag_setzen` darf `true`). Widerruf (d) → `geburtsdatum IS NULL` in derselben Anweisung. A setzt `geburtsdatum` mit dem eigenen JWT → `permission denied`.
- **Registrierung ohne Metadaten-Vertrauen:** `signUp` direkt mit dem anon-Key, mit beliebigen `raw_user_meta_data` (auch einer echten Versionskennung) → Profil wie heute, `mindestalter_bestaetigt_am IS NULL`, keine Nachweiszeile. `profil_anlegen` ist unverändert, die Anlage eines Admin-Kontos im Supabase-Dashboard gelingt. Ein über den anon-Key angelegtes, unbestätigtes Konto X, danach Registrierung über unser Formular mit derselben Adresse (mehr als 60 Sekunden später) → kein Nachweis bei X (Prüfung auf `created_at`, 5.1 Schritt 2).
- **Sensibel-Trigger:** Je Regel aus 5.8 ein Treffer- und ein Fehltreffer-Event (z. B. „Messe Düsseldorf“ → nicht, „Heilige Messe St. Lambertus“ → religion; „La Traviata (Verdi)“ → nicht, „ver.di-Versammlung“ → gewerkschaft; „Pride and Prejudice“ → nicht, „CSD Düsseldorf“ → sexualitaet). Insert über die Pipeline-Funktion (`database/client.py`) und über `dashboard/meldungen.py` → beide gekennzeichnet. Update der Beschreibung mit Treffer → Kennzeichnung nachgetragen. Event in `event_sensibel_ausnahmen` → nach Textänderung nicht wieder gekennzeichnet. Ein absichtlicher Fehler im Trigger (Testdatenbank) → Insert des Events schlägt fehl, kein ungekennzeichnetes Event.
- **Erster INSERT sensibel:** A ohne (b), erster INSERT ist ein sensibles Event → `nur_geraet`, `merkliste_begonnen_am` bleibt leer. Der nächste gültige INSERT setzt es. Mit (a) → `personalisierung = true` mit Nachweiszeile **vor** dem Speichern von `praeferenzen`.
- **Sensible Events:** Event S in `event_sensibel`. A ohne (b) fügt S in `merkliste` ein → Trigger bricht mit `nur_geraet` ab. A mit (b) → eingefügt. `einwilligung_setzen(A, 'sensible_events', false)` → S aus A's Merkliste gelöscht, S als Rückgabe. Später gekennzeichnetes Event T, das B ohne (b) gemerkt hat → Zeile bei B gelöscht, bei C mit (b) nicht. `merk_statistik()` als Admin enthält S und T nie, auch nicht mit Konten mit (b).
- `anon` und `authenticated` lesen nichts aus `event_sensibel`, `sensibel_regeln` und `event_sensibel_ausnahmen` (`permission denied`), auch nicht über eine Join-Abfrage auf `events`. `has_function_privilege` für `sensibel_grund` bei `public`, `anon` und `authenticated` → `false`. Ein Aufruf über die Data-API (`/rest/v1/rpc/sensibel_grund`) mit dem anon-Key scheitert.
- **Umlaute in den Mustern:** Events mit „ÖDP-Infostand“, „Treffen für nonbinäre Menschen“, „Bündnis 90 lädt ein“ und „Trauercafé im Stadtteil“ werden gekennzeichnet. Ein Titel „Kochdemonstration“ und ein Text mit „Live-Demonstration der neuen Technik“ nicht. „Demonstration vor dem Rathaus“ und „Demonstration gegen Rechts“ → politik. „Kurz davor Demonstration für Klimaschutz“ → politik (die Ausnahme greift nicht, weil sie eine Wortgrenze verlangt). „Die Linke“ nur mit Kontext. Ein Event, auf das zwei Regeln passen, bekommt den Grund der Regel mit der kleineren Priorität.
- `einwilligungstexte`: UPDATE und DELETE als `service_role` → vom Trigger abgelehnt. `einwilligungen` mit unbekannter `textversion` → Fremdschlüssel-Fehler.
- A setzt mit dem eigenen JWT `personalisierung`, `sensible_events_erlaubt`, `analyse_erlaubt`, `mindestalter_bestaetigt_am`, `nutzungsbedingungen_version`, `merkliste_begonnen_am`, `geburtsdatum`, `geburtstagsmail`, `geburtstagsmail_zuletzt` oder `unter16_gesperrt_am` → `permission denied`. A setzt `praeferenzen` ohne Personalisierung → Verstoß gegen `praeferenzen_nur_mit_einwilligung`. A fügt in `einwilligungen` ein → `permission denied`.
- `einwilligung_setzen(A, 'personalisierung', false, …)` als `service_role` → `praeferenzen = {}` und eine neue Zeile in `einwilligungen`, beides in einer Transaktion. Als `authenticated` → `permission denied`.
- A ohne `mindestalter_bestaetigt_am` fügt in `merkliste` ein → von der Policy abgelehnt.
- Konto A löschen (über die Route, also mit `konto_protokoll_loeschen`) → keine Zeilen von A in `profiles`, `merkliste`, `einwilligungen` und `auth.audit_log_entries`.
- `has_function_privilege` für alle neuen Funktionen: `public` und `anon` immer `false`. `authenticated` nur bei `merk_statistik` und `merkliste_vor_insert` `true`. `einwilligung_setzen`, `geburtstag_setzen` und `konto_protokoll_loeschen` nur für `service_role` (`has_function_privilege` für `authenticated` → `false`).
- Aufräumjob im Probelauf: Er nennt nur Audit-Zeilen von Nutzer-IDs, die es in `auth.users` nicht gibt, keine eines Admins. `konto_protokoll_loeschen` für eine gelöschte ID ohne Zeile in `auth.users` löscht deren Zeilen per ID und per Mail aus den Audit-Zeilen. Hat sich dieselbe Adresse neu registriert, bleiben die Zeilen des neuen Kontos stehen.
- Bestätigtes Testkonto ohne Mindestalter, `created_at` älter als 7 Tage (im Test zurückdatiert) → der Job nennt es zum Löschen. Ein Admin ohne Mindestalter → nicht.
- `textversion` in `einwilligungen` entspricht nach einem Aufruf der Route immer der Konstante, auch wenn der Body ein eigenes `textversion` mitschickt (Route-Test, 16.1).

### 16.3 Ablauf im Browser (lokal, dev Port 3100 und `next start` Port 3200)
1. Abgemeldet drei Events merken → Hinweis 7.2 einmal, Kasten 7.1 sichtbar.
2. Konto anlegen mit **neuer** Testadresse, Passwort und Alters-Häkchen (ohne Häkchen ist der Knopf gesperrt) → neutrale Meldung → Mail „Confirm signup“ → Link → Knopf „Adresse bestätigen“ → Fragebogen → Auswahl → Abschlussseite: (a) angehakt, (b) nicht → „Fertig“ → Merkliste zeigt die drei Events „aus diesem Gerät übernommen“. Netzwerk-Mitschnitt: Vor „Fertig“ ging keine Antwort des Fragebogens raus. Eine zweite neue Adresse über den **Ersatz-Code** bestätigen, „Ohne Interessen weiter“ wählen, auf der Abschlussseite nichts anhaken → keine Interessen gespeichert, Zählung an (kein Widerspruch).
2a. **Sensible Events:** Mit Konto ohne (b) ein Test-Event aus `event_sensibel` merken. Das Herz bleibt gefüllt, kein Hinweis, die Merkliste zeigt es ohne Unterschied. Auf dem zweiten Gerät fehlt es. In (b) im Konto einwilligen → nach dem Abgleich auf beiden Geräten da. Widerrufen → auf dem widerrufenden Gerät weiter da, auf dem anderen weg. Nirgends in Oberfläche, Export oder Seitenquelltext steht „sensibel“ oder ein Grund. Konto anlegen mit einer schon registrierten Adresse → dieselbe neutrale Meldung.
3. Zweiter Browser (anderes Profil), mit zwei anderen lokal gemerkten Events: Anmelden mit Mailadresse und Passwort → die drei Konto-Events, darunter der Block „Nur auf diesem Gerät“ mit 2 Events. [Ins Konto übernehmen] → 5 Events. Dort eins entfernen → im ersten Browser nach Fokus weg.
3a. Im ersten Browser abmelden, ein zuvor auf Gerät 2 entferntes Event lokal neu merken, wieder anmelden → es kommt **nicht** still ins Konto, sondern erscheint unter „Nur auf diesem Gerät“.
4. Abmelden im ersten Browser → Merkliste leer mit Anmeldehinweis, `localStorage` ohne Spiegel.
5. Export herunterladen und Inhalt prüfen. Konto löschen mit Passwort → Anmelden mit derselben Adresse scheitert, eine neue Registrierung legt ein neues, leeres Konto an.
6. Link mit `curl` (GET) aufrufen, danach im Browser klicken → funktioniert noch (Scanner-Schutz). Im Log des Next-Servers steht kein `token_hash`.
6a. Anmeldeformular: Links zur Datenschutzerklärung (`/datenschutz#konto`) und zu den Nutzungsbedingungen (`/nutzungsbedingungen`, Widerrufsbelehrung) funktionieren.
6c. Mail-Link in Gmail, GMX/Web.de und Outlook.com öffnen. Notieren, wo das Fragment ankommt. Kommt es leer an, zeigt die Seite das Code-Feld, und die Anmeldung per Code klappt.
6d. Zwei Tabs offen, in einem anmelden (lokal 3 Events) → beide Tabs zeigen danach dieselben 3 Konto-Events, keines fehlt.
6b. Einwilligung (a) im Konto widerrufen → `praeferenzen` leer. „Interessen ändern“ bietet den Fragebogen wieder an und endet mit Einwilligung (a). Widerspruch gegen die Zählung im Konto umschalten → Nachweiszeile, `merk_statistik` zählt das Konto nicht mehr.
7. Mobil (375 px) hell und dunkel, ohne Querscrollen, Tastatur-Bedienung, Screenreader-Labels.
8. Admin-Anmeldung im Dashboard per Passwort funktioniert unverändert. „Passwort vergessen“ mit einer Admin-Adresse führt über die Website-Seite zu einem neuen Passwort, das danach im Dashboard gilt.
9. **Passwort-Abläufe:** falsches Passwort → einheitliche Meldung. Fünf Fehlversuche von einer IP in 15 Minuten, dann der sechste Versuch von dort (auch mit richtigem Passwort) → Pause mit derselben Meldung. Dasselbe Konto von einer **anderen** IP mit richtigem Passwort → angemeldet. Fremde können also niemanden aussperren. Unbestätigte Adresse mit richtigem Passwort → „Bitte bestätigt zuerst …“ mit „Mail erneut senden“, mit falschem Passwort → einheitliche Meldung. „Passwort vergessen“ → Mail ohne Code → Link → Knopf → `/konto/passwort-neu`. Vor dem Setzen: `/api/konto/merkliste` → 403 `passwort_setzen_noetig`, das Cookie läuft nach 1 Stunde ab. Neues Passwort → zweites Gerät ist abgemeldet, dieses Gerät hat eine normale Sitzung. Konto anlegen mit einer unbestätigten Adresse und anderem Passwort → gleiche Meldung, nach der Bestätigung gilt das erste Passwort. Konto anlegen mit bestätigter Adresse → gleiche Meldung, Status 200, kein Nutzerobjekt in der Antwort. „Passwort ändern“ im Konto mit falschem aktuellem Passwort → abgewiesen. Mit richtigem → geändert, andere Geräte abgemeldet, dieses Gerät bleibt angemeldet. Passwort mit 9 Zeichen → abgewiesen, mit 10 → angenommen.
10. Konto löschen ohne oder mit falschem Passwort → abgewiesen.

### 16.4 Cache, Zustellung, Last
- Die Routen-Tabelle von `next build` vorher und nachher ist für öffentliche Routen gleich. `curl -I` auf die öffentlichen Seiten zeigt kein `Set-Cookie`. Die Konto-Routen antworten mit `private, no-store`.
- Live nach dem Deploy mit Schalter aus: `curl -I -H "Cookie: ddd_konto=1"` auf `/`, `/heute` und eine Eventseite liefert dieselben Status- und Cache-Header wie ohne Cookie. So ist geprüft, dass nginx das Anzeige-Cookie nicht anders behandelt.
- Testmails an Gmail, GMX/Web.de und Outlook.com, Zustellzeit unter einer Minute, nicht im Spam, Header mit „pass“.
- 1.000 Anfragen gegen `/api/konto/ich` lokal, Heap stabil.

---

## 17. Risiken

| Risiko | Folge | Gegenmaßnahme |
|---|---|---|
| Alte Tabelle ohne RLS oder mit zu weiter Policy | Jeder angemeldete Nutzer liest oder schreibt sie | Schritt 1 vor jeder öffentlichen Registrierung |
| Mail-Scanner verbrauchen den Link | „Link abgelaufen“ | Bestätigung per POST (5.2), Code als zweiter Weg |
| Mails landen im Spam | Keine Anmeldung möglich | eigener Server: SPF, DKIM, DMARC, PTR, Sperrlisten-Prüfung, schlichte Vorlage, Tests 16.4; Rückfall auf einen EU-Versanddienst ist nur eine SMTP-Zeile (10.1) |
| Cookie oder Sitzung zieht auf öffentliche Seiten durch | Cache-Verlust, langsamere Seiten | Regeln 3.5, `Path=/api/konto`, Build-Vergleich |
| Speicherleck durch Clients pro Anfrage | Absturz wie am 06.11.2026 | `autoRefreshToken: false`, Speicher-Test |
| Datenverlust bei der Übernahme | Gemerktes fehlt | Lokal nur löschen, was im Konto steht oder ungültig ist, Teilübernahme bleibt auf dem Gerät, Tests 16.1 |
| Entferntes Event kommt über ein anderes Gerät zurück | Merkliste „füllt sich wieder“ | Automatische Übernahme nur, wenn `merkliste_begonnen_am` leer ist (das Konto hatte nie eine Merkliste), sonst Nachfrage (5.4) |
| Zwei verspätete Erneuerungen widerrufen die Token-Familie | Gerät wird abgemeldet | Warteschlange je Tab, 401 mit sauberem Abmelden, nichts geht verloren (3.2) |
| Anmelde-Token in Server-Logs | Fremde Anmeldung bei Log-Zugriff | Token im Fragment, nicht in der Query (5.2) |
| Missbrauch über den öffentlichen anon-Key (Mail-Bombing) | Fremde bekommen Mails, Kontingent erschöpft | Projektlimit Supabase, Beobachten der Mailzahlen in der ersten Woche |
| Sensible Rückschlüsse (Art. 9) | Rechtliches Risiko | Sensibel-Filter (E13): ohne ausdrückliche Einwilligung nur lokal, nie Empfehlungen oder Statistik |
| Sensibel-Filter verpasst ein Event | Merkung landet ohne Art.-9-Einwilligung im Konto und in der Statistik | Weit gefasste Regeln, Sichtprüfung der Treffer beim Nachtrag (dort gilt „im Zweifel sensibel“, zur Laufzeit allein die Regeltabelle, 5.8), Korrektur von Hand, nachträgliche Kennzeichnung entfernt die Zeilen (4.8) |
| Sensibel-Filter trifft zu viel (z. B. „Messe Düsseldorf“) | Event bleibt ohne Einwilligung nur auf dem Gerät, fehlt in der Statistik | Enge Muster mit Kontextbedingung (5.8), Fehltreffer per Hand aufheben |
| Spätere Kennzeichnung eines schon gemerkten Events | Merkung verschwindet bei Personen ohne Einwilligung (b) aus dem Konto **und beim nächsten Abgleich auf allen ihren Geräten**. Eine Rückgabe gibt es bewusst nicht, weil sie die Art.-9-Zuordnung ohne Einwilligung speichern müsste | Kennzeichnung per Trigger schon beim Insert, Nachtrag vor dem Einschalten, Zählung der betroffenen Konten vor jeder Hand-Kennzeichnung oder neuen Regel (4.8) |
| Fehler im Sensibel-Trigger auf `events` | Pipeline, Anreicherung und Dashboard können keine Events mehr speichern | Einfacher Trigger ohne externe Aufrufe, SQL-Tests vor dem Ausführen (16.2), Ausführen der SQL außerhalb des Pipeline-Laufs, Rückbau-SQL (`DROP TRIGGER`) liegt bei |
| Geburtsdatum widerspricht dem Alters-Häkchen | Konto einer Person unter 16 | `geburtstag_setzen` prüft, entzieht das Häkchen und sperrt das Konto. Gelöscht wird beim nächsten Lauf des Aufräumjobs, innerhalb von drei Tagen (4.5, 9.3) |
| Kennzeichnung über Datenverkehr erkennbar | Technisch Versierte sehen, dass ein Event nur lokal gespeichert wurde | Neutrale Antworten ohne Grund, keine Liste, nichts in der Oberfläche (5.8). Bewusst hingenommen |
| Einwilligungstexte im Code und in der Datenbank weichen ab | Nachweis passt nicht zum gezeigten Text | Prüfsummen-Test (16.1), Texte unveränderbar (4.4) |
| Bündel-ID wechselt bei Absage | Herz wirkt „vergessen“ | Bekannte Grenze, Abschnitt 19 |
| Supabase-Einstellung betrifft das Admin-Dashboard | Admin-Login gestört | Reset-Vorlage bleibt, Test 16.3/8 |
| Bremslimit nur im Speicher | Ein Neustart setzt zurück | Wie bei den Formularen hingenommen. Supabase hat eigene Limits |
| Erratene oder wiederverwendete Passwörter | fremder Zugriff auf Merkliste und Interessen | Bremslimit je Paar aus IP und Adresse und je IP, Mindestlänge 10, Prüfung gegen geleakte Passwörter je nach Tarif, Abmelden anderer Geräte nach Passwortwechsel (11.1) |
| Eigener Mailserver landet auf einer Sperrliste | Bestätigungs- und Reset-Mails kommen nicht an | niedriges Stundenlimit, Beobachtung, Rückfall EU-Versanddienst (10.1) |
| Reset-Vorlage ändert den Ablauf für Admins | Admin findet den Reset-Link auf der Website statt bei Supabase | Test 16.3 Punkt 8, Hinweis an die Admins |

---

## 18. Abnahmekriterien
1. Ein neues Konto ist erst nach Bestätigung der Mailadresse (Link oder Ersatz-Code) nutzbar. Anmelden geht mit Mailadresse und Passwort, „Passwort vergessen“ setzt per Mail ein neues Passwort, und danach sind andere Geräte abgemeldet. Unbestätigte Konten verschwinden nach 48 Stunden, durch den Drei-Tage-Lauf spätestens nach fünf Tagen. Bestätigte Konten ohne Alters-Häkchen verschwinden nach 7, spätestens nach 10 Tagen. Das Alters-Häkchen und die Nutzungsbedingungen stehen im Registrierungsformular. Der Job läuft schon, bevor die Registrierung öffentlich ist. Eine geöffnete, aber nicht abgeschlossene Reset-Sitzung endet nach spätestens einer Stunde.
2. Gemerkte Events erscheinen nach der Anmeldung auf einem zweiten Gerät. Entfernen wirkt auf beiden, und ein entferntes Event kommt nicht ungefragt zurück.
3. Lokal gemerkte Events landen beim ersten Anmelden vollständig im Konto, auch mit mehr als 100 Einträgen. Was nicht ins Konto passt, bleibt auf dem Gerät.
4. Abgemeldet zeigt die Merkliste den Anmeldehinweis aus 7.1. Angemeldet steht dort „In eurem Konto gespeichert“.
5. Der Interessen-Fragebogen speichert gültige Werte, lässt sich überspringen und ist im Konto änderbar.
6. Export und Löschen funktionieren ohne Mail an uns. Nach dem Löschen gibt es keine Zeile mehr zur Person, auch nicht im Anmeldeprotokoll. Ist das Löschen dort nicht möglich (4.6), nennt die Erklärung die Aufbewahrungsdauer von Supabase.
6a. Interessen werden nur mit Einwilligung (a) auf der Abschlussseite gespeichert, vorher verlässt keine Antwort den Browser. Beim Widerruf sind sie sofort leer.
6b. Sensible Events liegen ohne Einwilligung (b) nie im Konto, fließen nie in Statistik oder Empfehlungen ein, und nirgends in Oberfläche oder Export ist erkennbar, welche Events sensibel sind. Der Nachtrag für vorhandene Events ist vor dem Einschalten gelaufen.
6c. Jede Einwilligung und jeder Widerspruch hat eine Nachweiszeile mit Handlung, Zeitpunkt und archiviertem Wortlaut.
7. Öffentliche Seiten haben unveränderte Cache-Header, kein `Set-Cookie` und dieselbe Routen-Tabelle wie vorher.
7a. Vergangene gemerkte Events stehen auf der Merkliste eingeklappt unter „Vorbei (n)“, kommende nach Datum darüber (E9, 5.5).
7b. Ein Konto mit Geburtsdatum unter 16 ist sofort gesperrt, sieht kein Alters-Häkchen mehr, bekommt keine Geburtstagsmail und ist nach dem nächsten Job-Lauf gelöscht.
8. `/konto/*` ist `noindex` und steht weder in der Sitemap noch in `llms.txt`.
9. Datenschutzerklärung, Nutzungsbedingungen und Einwilligungstexte sind angepasst, anwaltlich durchgesehen und vom Auftraggeber freigegeben, bevor der Schalter an geht. Interessenabwägung (E4) und DSFA-Schwellenwertprüfung liegen vor. Die Supabase-Unterlagen aus 9.2 sind abgelegt.
10. Der Admin-Login im Dashboard funktioniert unverändert.
11. Unit-Tests, SQL-Tests und Build sind grün. Die Cursor-Prüfung ist ohne offenen kritischen Punkt.

---

## 19. Offene Punkte
1. Alle Produktentscheidungen sind getroffen (E1–E4, E12–E15 am 16.11.2026). **Die rechtliche Einschätzung** vom 16.11.2026 liegt nur als Zusammenfassung vor, die sich selbst „keine verbindliche anwaltliche Beratung“ nennt. Vor dem Einschalten bestätigt ein Anwalt die Kernpunkte verbindlich: E13-Umsetzung, Einwilligungstexte (a) und (b), Interessenabwägung (E4), Nutzungsbedingungen mit Widerrufsbelehrung, Datenschutzerklärung (Schritt 6 in Abschnitt 15).
2. E5–E11 bestätigen oder ändern, besonders den Hinweis nach dem ersten Merken (7.2). **Altersbestätigung per Häkchen ab 16 ist vom Anwalt am 16.11.2026 freigegeben** (E6).
2a. **Stichwortliste des Sensibel-Filters** (5.8): Der Auftraggeber sieht die Trefferliste des Nachtrags durch, bevor er echt läuft.
2c. **Geburtstagsmails** (E15): Mailvorlage und Versandjob in Schritt 9a. Der Einwilligungstext (d) ist neu und gehört in die anwaltliche Durchsicht der Einwilligungstexte (Schritt 6).
2b. **Aufbewahrung der Einwilligungsnachweise nach Kontolöschung:** heute gelöscht mit dem Konto. Ob sie für die Verjährungsfrist möglicher Ansprüche bleiben sollen, klärt die anwaltliche Durchsicht.
3. Bestehende du-Texte auf der Merkliste auf ihr/euch umstellen (7.1)? Der Plan sagt ja. Die übrige Website (Fragebogen „Wo dürfen wir für dich suchen?“, Newsletter) bleibt in dieser Runde bei du.
4. Mailadresse im Konto ändern: in dieser Runde per Mail an uns, später im Konto über „Secure email change“?
5. Die rechtliche Einschätzung hat die Fragen 1–10 beantwortet (Antworten eingearbeitet in E4, E6, E12a, E13, E14, 4.4, 9.1–9.4). Frage 11 (Datenschutzerklärung) kann erst mit dem Entwurf aus Schritt 6 geprüft werden.
5a. E12 umgesetzt: Interessen immer beim Anlegen, „Ohne Interessen weiter“ auf jeder Seite, Einwilligungen (a) und (b) am Ende. Dass Interessen erst nach der Mail-Bestätigung abgefragt werden und nicht im Registrierungsformular, ist eine Auslegung von Claude (5.3). Bitte bestätigen.
6. Welcher Supabase-Tarif (davon hängt die Prüfung gegen geleakte Passwörter ab)? Wer hat Zugang zum DNS von `diesdas.events`? Fragen an den Hoster: Darf Supabase von außen über unser Postfach senden (Port 587/465)? Gibt es ein Mail-Limit pro Stunde? Stimmt der PTR-Eintrag (auch für IPv6, oder Versand nur über IPv4)? Passt das TLS-Zertifikat zum SMTP-Hostnamen? Bleibt der Envelope-Absender `@diesdas.events`, oder schreibt der Server ihn um? Deckt der AV-Vertrag den Mailversand ab?
7. Inaktivitäts-Job mit Warnmail bis spätestens Oktober 2028.
7a. Schritt 1 hat gezeigt: `auth.audit_log_entries` ist löschbar, aber leer. Die Anmeldeprotokolle liegen in den Plattform-Protokollen von Supabase. Der Auftraggeber ermittelt in Schritt 2 deren Aufbewahrungsdauer laut Tarif und prüft, dass das Schreiben in die Datenbank aus bleibt (4.6).
8. Gruppen-ID beim Merken stabilisieren (z. B. Schlüssel aus Titel, Datum und Ort statt Termin-ID), eigener kleiner Plan.
9. Orte aus den Guides merken (E8), eigener Plan.
10. App: Routen für Token als JSON, Deep Links, Push. Kommt mit dem App-Plan.
11. Newsletter bleibt getrennt. Später ein freiwilliges Häkchen im Konto mit eigenem Double-Opt-in?
12. Zwei-Faktor-Anmeldung (z. B. App-Code) ist nicht Teil dieser Runde. Für ein Konto ohne Zahlungs- oder Gesundheitsdaten reicht nach Einschätzung ein Passwort mit Bremslimit. Später möglich, Supabase unterstützt TOTP.
13. Eigene Prüfung gegen geleakte Passwörter vom Server aus (HaveIBeenPwned, k-Anonymität), falls der Supabase-Tarif sie nicht enthält: eigene Entscheidung, weil es ein zusätzlicher Dienst wäre.
14. **Vorversuch (Schritt 4) bei ausgeschaltetem Signup:** `signUp` gegen das echte Projekt scheitert, solange „Allow new users to sign up“ aus ist. Vor Schritt 4 zu entscheiden: Signup für die Dauer des Vorversuchs kurz einschalten (wenige Minuten, unter Aufsicht; Testkonten und fremde Konten danach löschen) oder ein zweites, leeres Supabase-Projekt nur für den Vorversuch. Gefunden beim Vorbereiten von Schritt 2, 16.11.2026. **Empfehlung (Cursor und Claude): kurz einschalten**, weil nur das echte Projekt `identities`, `email_not_confirmed`, Token-Typen und Verify-Limit mit seinen tatsächlichen Auth-Einstellungen zeigt. Ablauf dann: Signup an, Vorversuch, Signup aus. Danach unter Authentication → Users alle Konten außer Admins löschen, Testkonten und etwaige fremde gleichermaßen. Entscheidung durch den Auftraggeber vor Schritt 4.

---

## 20. Prüfhistorie
- 16.11.2026: erste Fassung. E1 vom Auftraggeber entschieden (Konto freiwillig, Hinweis auf der Merkliste laut Screenshot).
- 16.11.2026: **erste Cursor-Prüfung** eingearbeitet. Alle Befunde wurden am Code nachgeprüft und sind übernommen:
  - **K (Datenverlust):** Lokal wird nur gelöscht, was im Konto steht oder ungültig ist. Eine Teilübernahme bleibt auf dem Gerät. Tests mit 600/400 (5.4, 16.1).
  - **M (Rückkehr gelöschter Events):** Automatische Übernahme nur in ein leeres Konto, sonst Nachfrage. Tab-Änderungen während der Übernahme werden nachgezogen (5.4, 7.1). *(In Runde 2 ersetzt durch Sperre, Warteschlange und `merkliste_begonnen_am`.)*
  - **M (Inaktivität):** Jede angemeldete Route setzt `letzte_aktivitaet_am`, `NULL` zählt ab `erstellt_am` (4.1, 9.3).
  - **M (Rechtsgrundlage):** Interessen und Empfehlungen per Einwilligung (E12). Summen bis zur Rechtsprüfung nur mit Einwilligung, Standard `false` (E4, 4.1, 5.3, 9.1).
  - **M (Art. 13 und 17):** Datenschutz-Link am Anmeldeformular. Audit-Zeilen werden beim Löschen entfernt, Rückfall mit 30-Tage-Frist in der Erklärung (4.6, 5.1, 9.4).
  - **M (Reihenfolge):** Aufräumjob vor dem öffentlichen Signup. Konto-Routen geben bei Schalter aus 404 (E10, 15).
  - **M (Rechte-Prüfung):** Whitelist der gewollten öffentlichen Lesewege. Falsche Aussage zu `event_seo_entscheidungen` in 1.3 korrigiert (1.3, 4.0).
  - **M (`merk_statistik`):** `REVOKE … FROM PUBLIC, anon` für alle neuen Funktionen, Test über `has_function_privilege` (4.5, 16.2).
  - **M (`weiter`):** dekodieren, dann den ganzen Pfad prüfen. Weitere Tests (5.1, 16.1).
  - **M (Bremslimit):** `zuVieleAnfragen` bekommt ein Fenster je Schlüssel. Heute ohne Folgen, weil alle Aufrufe eine Stunde nutzen (1.5, 6, 16.1).
  - **M (OTP-Typ):** `signup` und `email` je nach Mailart, beide Mailarten mit Code und Link getestet, nie `{{ .ConfirmationURL }}` (5.1, 5.2, 16.3).
  - **M (Token in Logs):** `token_hash` im Fragment statt in der Query (5.2, 10.3).
  - **G:** Umgebungsvariablen genauer beschrieben (1.5), Admin-Lesezugriff auf `profiles` (1.3), HSTS-Regel in `headers()` erhalten (1.5, 12), Abschnitt 15 der Erklärung ergänzt (9.4), Grenze des Reuse-Fensters beim Erneuern (3.2).
  - **Nicht prüfbar** laut Cursor und weiter offen: Live-Einstellungen in Supabase, DNS, Tabellen nur in der Live-Datenbank (Schritt 1 deckt sie ab) und das Verhalten von nginx beim Cookie `ddd_konto`. Dafür neuer Test in 16.4.
- 16.11.2026: **zweite Cursor-Prüfung** eingearbeitet. Alle Befunde wurden geprüft und übernommen. Dazu kommt ein eigener Fund.
  - **K (zwei Tabs):** Kein Schluss mehr aus dem Unterschied zweier Listen. Nur ein Tab übernimmt (Web-Locks-Sperre), Herz-Klicks während der Übernahme laufen über eine Warteschlange, Test „zwei Übernahmen parallel“ (5.4 Schritte 0 und 9, 16.1, 16.3/6d).
  - **M (geleertes Konto):** Automatisch nur, wenn `merkliste_begonnen_am` leer ist. Ein Trigger setzt den Wert beim ersten Eintrag (4.1, 4.3, 5.4 Schritt 2).
  - **M (Herz während der Übernahme):** Warteschlange gegen das Konto statt Beobachtung der Geräteliste (5.4 Schritt 9).
  - **M (Dubletten):** Antwortfeld `umgeschrieben: [{ von, nach }]`. `von` wird nur gelöscht, wenn `nach` im Konto steht. Ein nicht auflösbares Ziel bleibt als Ursprungs-ID (5.4 Schritte 5, 7 und 8).
  - **M (alte Tests):** Die alten Sätze in 16.1 sind ersetzt. Mehr als 1.000 IDs ergeben 413 ohne Schreiben.
  - **M (Signup am anon-Key):** In 11.1 und Schritt 8 beschrieben. 403 `mindestalter_fehlt` in den Routen, und die `merkliste`-Policy verlangt das Mindestalter.
  - **M (Löschfunktion, Rückfall):** `search_path`, `REVOKE` und `GRANT` nur an `service_role` für alle neuen Funktionen. Der Job löscht nur Zeilen nicht mehr existierender Nutzer. **Eigener Fund:** Der 30-Tage-Rückfall der zweiten Fassung hätte dasselbe Löschrecht gebraucht, dessen Fehlen er abfangen sollte. Er entfällt. Ohne Löschrecht nennt die Erklärung die Aufbewahrungsdauer von Supabase (4.6, 9.1, 18, 19).
  - **M (`weiter`):** dekodieren, bis sich nichts mehr ändert (höchstens zweimal), danach `%2F`, `%5C` und `%25` ablehnen (5.1, 16.1).
  - **M (Fragment-Link):** Der Code ist der verlässliche Weg, eine leere Ankunft zeigt das Code-Feld. Die Typ-Regel einschließlich `magiclink` legt erst ein Vorversuch in Schritt 4 fest, abhängig davon, ob ein falscher Typ das Token verbraucht (5.1, 5.2, 15, 16.3/6c).
  - **M (Einwilligungs-Spalten):** Nur noch über `einwilligung_setzen` mit dem Dienst-Client. Dazu die CHECK-Bedingung `personalisierung OR praeferenzen = '{}'`, `einwilligungen` ohne INSERT für `authenticated` (3.4, 4.1, 4.4, 4.5, 16.2).
  - **G:** Verweis bei 401 auf die Schritte 2 und 3 (5.5). Die Zeile in 9.1 spricht von „Auswertung der Merkliste für Empfehlungen“. Regel 3.5 heißt „nicht neu hinzufügen“. Die Notbereinigung von `zuVieleAnfragen` entfernt zuerst die abgelaufenen, dann die ältesten Schlüssel (6).
  - Die Angabe „Rückfall mit 30-Tage-Frist“ aus der ersten Runde oben ist damit überholt.
- 16.11.2026: **dritte Cursor-Prüfung** ohne kritischen Befund. Alle mittleren und geringen Befunde sind übernommen:
  - **Trigger:** `merkliste_vor_insert()` ist `SECURITY DEFINER` mit leerem `search_path` und schreibt nur `merkliste_begonnen_am`. `GRANT EXECUTE` an `authenticated`, das ist unschädlich, weil sich Trigger-Funktionen nicht direkt aufrufen lassen. Ob Postgres das Recht beim Auslösen überhaupt prüft, ist offen, der Grant macht es unerheblich. Ein schon gemerktes Event (`ON CONFLICT`) überspringt die Grenzprüfung. Der Test läuft als Nutzer A (4.3, 4.5, 16.2).
  - **Reihenfolge Übernahme und Häkchen:** Die Übernahme startet erst nach Häkchen 1. Bis dahin gilt der Gerätemodus über `ddd_konto=0`, und 403 steht in Schritt 10 (3.2, 5.1, 5.3, 5.4 Schritte 0a und 10).
  - **Warteschlange:** eigener Schlüssel `ddd-merkliste-warteschlange` mit `[{ op, id, zeit }]` für **alle** Herz-Klicks im Kontomodus, abgearbeitet unter derselben Sperre. Bei 401, 403 und beim Abmelden wird sie auf die Geräteliste angewendet. Ein geschlossener Tab verliert nichts (5.5, 5.6, 16.1).
  - **Sperre:** ein Name `ddd-merkliste` für Übernahme und Warteschlange, Wartegrenze 30 Sekunden, je Abruf 15 Sekunden, der Callback gibt das ganze Promise zurück. Der Ersatz arbeitet mit Token, Rücklesen und `finally` (5.4 Schritt 0).
  - **Audit-Job:** Die Funktion löscht auch ohne Zeile in `auth.users` per ID und holt die Mail aus den Audit-Zeilen. Bei neu registrierter gleicher Adresse bleiben deren Zeilen stehen. Der Probelauf läuft als Funktions-Eigentümer mit Testzeile und `ROLLBACK` (4.6).
  - **Kontostand:** `konto_status(mail)` nur für `service_role`, bei jedem Code aufgerufen, gleiche Fehlerantwort, feste Mindestdauer. Der Vorversuch hält Fehlercode und zweiten Versuch fest (5.1).
  - **Passwort-Registrierung:** Prüfauftrag in 10.2, Restrisiko in 11.1. **Abweichung vom Vorschlag:** Statt „im Dashboard aus“ als Tatsache gibt es neu eine 30-Tage-Löschung für bestätigte Konten ohne Schritt 0 (9.3, 9.4, 16.2). Ob Supabase Passwort und OTP getrennt schalten kann, ist nicht belegt.
  - **`textversion`:** Sie kommt aus einer Konstante der Route, nie aus dem Body (3.4, 5.3, 16.2).
  - **G:** Schritt 10 unterscheidet jetzt nach `merkliste_begonnen_am` (5.4). Der Widerruf steht in einer einzigen UPDATE-Anweisung (4.5). Der Kastentext in 7.1 ist angepasst, ebenso Zeile 4 zu E4, der Probelauf mit `ROLLBACK` (4.6), die Risikotabelle in 17 und die Fußnote zur Runde 1 in dieser Historie.
- 16.11.2026: **Entscheidungen des Auftraggebers** eingearbeitet (fünfte Fassung):
  - **E2:** Mailadresse und Passwort, Bestätigungsmail, „Passwort vergessen“. Neu sind die Routen `registrieren`, `bestaetigung-erneut`, `anmelden`, `passwort-vergessen`, `passwort-setzen` und `passwort-aendern`, Passwortregeln (mindestens 10 Zeichen), Abmelden anderer Geräte nach einem Passwortwechsel, Löschen nur mit Passwort, Schutz gegen Erraten und Ausspähen. Der Code-Weg der vierten Fassung samt `konto_status` entfällt. Der Ersatz-Code in den Mails bleibt als Rückfall für abgeschnittene Links (5.1, 5.2, 6, 11.1, 16).
  - **E3:** Mailversand über das SMTP-Postfach unseres eigenen Servers. Dazu Pflichten zu SPF, DKIM, DMARC und PTR, Fragen an den Hoster, ein EU-Versanddienst als Rückfall und das Risiko für den Ruf des Mailservers (9.2, 10.1, 11.1, 14, 17).
  - **E12:** Interessen immer beim Anlegen, Opt-out „Ohne Interessen fortfahren“. Das Häkchen „persönliche Empfehlungen“ entfällt. Als Einwilligung gilt „Fertig“ nach dem Hinweistext. Abgefragt wird nach der Mail-Bestätigung, nicht im Registrierungsformular (Auslegung von Claude, 5.3, 8, 9.1, 19 Punkt 5a).
  - **E4:** Fragen an den Anwalt in `docs/anwalt-fragen-nutzerkonten-2026-11-16.md`. Bis zur Antwort bleibt es beim Start mit Einwilligung.
- 16.11.2026: **vierte Cursor-Prüfung** (der fünften Fassung) ohne kritischen Befund. Alle Befunde sind übernommen (sechste Fassung):
  - **Registrieren:** In allen Fällen Status 200, gleicher Text, kein Nutzerobjekt. Hinweis, dass bei offener Registrierung das erste Passwort gilt. Der Vorversuch prüft die unbestätigte Wiederholung (5.1 Schritte 2 und 13, 16.1, 16.3).
  - **Pause beim Anmelden:** gezählt je Paar aus IP und Adresse, der 6. Versuch ist der erste in der Pause. Andere IPs sind nicht betroffen, also kein Aussperren durch Fremde (5.1 Schritt 6, 6, 16).
  - **Reset-Sitzung:** eingeschränkt (`nur_passwort`, 1 Stunde, nur `passwort-setzen` und `abmelden`). Die Reset-Mail hat **keinen** Ersatz-Code. Die Bestätigungsmail bekommt ihn nur bei einem Verify-Limit je Adresse (5.1 Schritt 9, 5.2, 10.3).
  - **Client für den Passwortwechsel:** dieselben Optionen wie in 3.2 (`autoRefreshToken: false` gegen das Leck), Cookie aus der Sitzung nach `updateUser`, Bibliotheksstellen belegt (5.1 Schritt 12).
  - **Mailserver:** TLS-Zertifikat, Envelope-Absender und IPv6 als Prüfpunkte. Der Rückfall nennt SPF und die Zugangsdaten des Jobs. Stundenlimit zum Start 20, Mail-Log in den ersten sieben Tagen täglich (10.1, 10.2, 11.1, 19).
  - **Opt-out:** läuft über `einwilligung_setzen(false)`, Fehler zwischen Einwilligung und Speichern geregelt, auch „Fertig“ ohne Auswahl ist Einwilligung, gleich in Plan und Anwaltsdatei (5.3, 16.1).
  - **Tor:** Nur die Anmeldung führt auf `/konto/willkommen`, die Website bleibt erreichbar, Hinweis „Profil noch nicht fertig“ (E12, 5.3).
  - **Fristen:** „48 Stunden, spätestens fünf Tage“ und „30, spätestens 33 Tage“ einheitlich in 9.3, 9.4, 15, 18 und in der Anwaltsdatei.
  - **G:** `konto_status` aus 16.2 gestrichen, Abschnitt 19 Punkte 1 und 5 nachgezogen, Cookie-Test mit `0` und `1`, E10 sagt „Postfach“, Admin-Passwörter unter 10 Zeichen bleiben gültig (11.3).
- 16.11.2026: **Rechtliche Einschätzung** (Zusammenfassung, nicht verbindlich) und **Entscheidungen des Auftraggebers** eingearbeitet (siebte Fassung):
  - **E13 Sensible Events (neu):** Kennzeichnung nur im Backend in eigener Tabelle `event_sensibel` ohne API-Rechte, gesetzt von `pipeline/sensibel.py` vor dem Speichern, mit Nachtrag. Ohne ausdrückliche Einwilligung (b) bleiben Merkungen nur auf dem Gerät (`ddd-merkliste-geraet`), mit Einwilligung im Konto. Nie in Empfehlungen oder Statistik. Für Nutzer nirgends erkennbar. Die Grenze beim Mitlesen des Datenverkehrs ist offen benannt (4.3, 4.8, 5.4, 5.5, 5.8).
  - **E12a:** Fragebogen weiter immer beim Anlegen mit „Ohne Interessen weiter“. Die Einwilligungen kommen am Ende auf einer Abschlussseite mit nicht vorangekreuzten Häkchen: (a) Interessen und Empfehlungen, (b) sensible Events mit Erklärtext, (c) Hinweis und Schalter zum Widerspruch gegen die Zählung. Antworten bleiben bis dahin im Browser (5.3, 8).
  - **E4:** berechtigtes Interesse mit Widerspruch, `analyse_erlaubt` standardmäßig `true`, sensible Events ausgeschlossen, Interessenabwägung als Dokument (2, 4.1, 4.5, 9.1).
  - **E14 Nutzungsbedingungen:** Entwurf `docs/nutzungsbedingungen-entwurf-2026-11-16.md` mit Widerrufsbelehrung und Prüfpunkten für den Anwalt. Seite `/nutzungsbedingungen`, Annahme im Registrierungsformular (5.1, 7.3, 7.4).
  - **Ohne Rückfrage umgesetzt:** Alters-Häkchen ins Registrierungsformular (E6, 5.1), Frist für Konten ohne Alter 7 statt 30 Tage (9.3), unveränderbares Archiv der Einwilligungstexte mit Handlung (4.4), Begründung der Cookies (9.1), DSFA-Schwellenwertprüfung (9.1), Supabase-Unterlagen (DPA, Standardvertragsklauseln, TIA, Unterauftragsverarbeiter, Fristen) und Data Privacy Framework nur bei tatsächlicher Nutzung (9.2), Backups (9.3), Export ersetzt keine Auskunft (5.7), Auth-Protokolle nur mit tatsächlich begrenzter Frist (4.6).
- 16.11.2026: **fünfte Cursor-Prüfung** (der siebten Fassung), dazu die **Freigabe der Altersbestätigung** durch den Anwalt und die neue Entscheidung **E15 Geburtsdatum** (achte Fassung):
  - **K (Nachweis über den anon-Key):** `profil_anlegen` bleibt unverändert. Kein Nachweis mehr aus `raw_user_meta_data`. Alter und Nutzungsbedingungen setzt die Route `registrieren` serverseitig über `einwilligung_setzen`, nur bei echter Neuanlage (nicht leere `identities`) (5.1 Schritt 2, 16.2).
  - **M (Kennzeichnung nicht in einer Transaktion):** Die Kennzeichnung läuft jetzt als Datenbank-Trigger auf `events` (Insert und Text-Update) mit Regeln in `sensibel_regeln`. Das gilt für Pipeline, Anreicherung und Dashboard gleich. „Gruppe“ = `terminSchluessel`, das Python-Modul entfällt (4.8, 5.8, 15 Schritt 7).
  - **M (Regeln mehrdeutig):** Startregeln als konkrete Regex mit Wortgrenzen, Kontext- und Ausnahmemustern, feste Parteiliste, keine automatische Regel für `herkunft`. „Im Zweifel“ gilt nur für die Sichtprüfung (5.8).
  - **M (spätere Kennzeichnung):** **Bewusst anders als vorgeschlagen:** keine Rückgabe der IDs an die Geräte, weil das die Art.-9-Zuordnung ohne Einwilligung speichern müsste. Dafür ehrlich in 4.8 und 17: Die Merkung verschwindet auf allen Geräten. Vor jeder Hand-Kennzeichnung wird gezählt, wie viele Konten betroffen sind.
  - **M (Art. 21 Abs. 4):** `analyse_erlaubt` startet mit `false` und wird erst auf der Abschlussseite nach dem Hinweis ohne Widerspruch `true` (E4, 4.1, 5.3).
  - **M (Wiederholung Abschluss, Testschlüssel):** `praeferenzen` werden bei gültigem (a) immer erneut geschrieben. Der Test nutzt `interessen_ok` (5.3, 16.1).
  - **M (Texte vor Freigabe):** `einwilligungstexte` bekommt Zeilen erst in Schritt 6 (15).
  - **M (Nutzungsbedingungen):** Fristen samt Laufzeit des Jobs in § 7, Vorbehalt für sensible Events in § 2, Geburtstag ergänzt, Prüfpunkt Alter erledigt.
  - **M (Anwaltsdatei):** als Archivstand gekennzeichnet.
  - **G:** dritte Antwort `zurueck_aufs_geraet` in 5.8 benannt, Erklärtexte (b), (c) und Widerrufsdialog in Sie-Form, SQL-Test „erster INSERT sensibel“.
  - **Hinweis zu Cursors Einleitung:** Der dort genannte „kritische Befund“ zum Zeitstempel beschreibt gewolltes Verhalten (ein abgewiesener INSERT setzt `merkliste_begonnen_am` nicht). Er ist im Text als geringer Befund behandelt und als Test ergänzt.
  - **E15 Geburtsdatum (neu):** freiwillig auf der Abschlussseite, nur mit Einwilligung (d) in Geburtstagsmails gespeichert (§ 7 Abs. 2 UWG), Prüfung unter 16 mit Entzug der Altersbestätigung, Versand als eigener Schritt 9a (Abschnitt 13a), Web-Push ausgeschlossen, Push erst mit der App (2, 4.1, 4.4, 4.5, 5.3, 5.7, 6, 9.1, 9.4, 13a, 16, 17).
- 16.11.2026: **sechste Cursor-Prüfung** (der achten Fassung) ohne kritischen Befund. Die Begründung zur späteren Kennzeichnung (4.8) hat Cursor bestätigt. Alle Befunde sind übernommen (neunte Fassung):
  - **Registrierung:** Der Nachweis wird nur für ein Konto geschrieben, das durch genau diese Anfrage entstanden ist (`created_at` höchstens 60 Sekunden alt). Ein älteres, unbestätigtes Konto bekommt keinen Nachweis von Fremden. Der Vorversuch prüft `identities` und `created_at` (5.1 Schritt 2, 16.2).
  - **Unter 16:** Sperre über `unter16_gesperrt_am`, kein erneutes Alters-Häkchen, Löschung beim nächsten Job-Lauf ab der Sperre, Prüfformel festgeschrieben (der 16. Geburtstag zählt als 16), gleicher Satz in 9.3, 9.4 und Nutzungsbedingungen § 3 und § 7 (4.1, 4.5, 9.3, 16.2).
  - **Zählung vor dem Hinweis:** `einstellungen` lehnt `analyse` vor `onboarding_fertig_am` ab, die Schalter im Konto erscheinen erst danach (6, 5.7).
  - **Geburtstag über die richtige Funktion:** „ja“ nur über `geburtstag_setzen`, „nein“ über `einwilligung_setzen(false)`. `einwilligung_setzen` lehnt `geburtstagsmail = true` ab (4.5, 5.3).
  - **Routen und Abschnitt 8:** `abschluss`, `einstellungen` und die Zeile „Ende“ mit (d). Neue Routen `geburtstag-abmelden` und `geburtstag-abmelden/[token]` (6, 8).
  - **Abmeldelink:** Seite mit Fragment und Knopf für Menschen, eigene POST-Adresse mit Token im Pfad für One-Click (RFC 8058), GET ändert nichts. Versand wird per `UPDATE … RETURNING` vorab beansprucht (13a).
  - **Gruppierung:** Satz zur Gruppe gestrichen. Jeder Termin wird nach eigenem Text gekennzeichnet (4.8).
  - **Regeln:** Kontextbedingung für „Demonstration“, „Die Linke“ und „Die Partei“, bekannte Fehltreffer benannt, Priorität und `ORDER BY` für den ersten Grund, UTF-8, Umlaut-Tests (4.8, 5.8, 16.2).
  - **9.1:** „im Zweifel sensibel“ nur für die Sichtprüfung.
  - **G:** `sensibel_grund` ohne Rechte für `PUBLIC`, `anon` und `authenticated`, Tests für alle drei Sensibel-Tabellen. „Vier Schalter“, Geburtsdatum im Export, Zweckbindung neben Geburtstagsmail, E15 in Abschnitt 19 Punkt 1.
- 16.11.2026: **siebte Cursor-Prüfung** (der neunten Fassung) ohne kritischen Befund. Prüfformel, Sperre, Zählung, Geburtstagswege, Abmeldung und Doppelversand bestätigt. Alle neun Befunde sind übernommen (zehnte Fassung):
  - **Regeln:** Ausnahme `\y(live|koch|produkt|tanz)[- ]?demonstration\y` mit Wortgrenzen und ohne „vor“, „Rathaus“ und „Landtag“ im Kontext, Prioritäten 40–44 in Tabellenreihenfolge, Tests „Demonstration vor dem Rathaus“ und „davor Demonstration“ (5.8, 16.2).
  - **Sperre in der Oberfläche:** Gesperrte Konten sehen auf `/konto/willkommen` kein Häkchen und keinen Fragebogen, nur die Meldung aus 4.5. Gleichlautend in 5.1 Schritt 7, 5.3 und Abschnitt 8.
  - **Schritt 7:** dritte Löschklasse (gesperrt unter 16). **Schritt 3:** Rückbau-Datei mit `DROP TRIGGER`, Ausführen außerhalb eines Pipeline-Laufs, Testlauf der Pipeline als Ergebnis.
  - **Risiken:** Löschung bei unter 16 „beim nächsten Lauf, innerhalb von drei Tagen“. „Im Zweifel sensibel“ nur für die Sichtprüfung.
  - **G:** Zeitfenster `Eingang − 60 s ≤ created_at ≤ Eingang + 5 s` in UTC mit Rückfall in Schritt 7 und Test. 5.7 beschreibt die Datumsänderung unter 16. 13a hält fest, dass das One-Click-Token bewusst im Log steht. Geburtstagsmails gehen nicht an gesperrte Konten. JWT-Test und Rechte-Test um die Geburtstagsspalten, `unter16_gesperrt_am` und `geburtstag_setzen` ergänzt. Abnahme 7a für „Vorbei“ (E9) und 7b für die Sperre.
- 16.11.2026: **achte Cursor-Prüfung** (der zehnten Fassung): kein kritischer und kein mittlerer Befund. Alle neun Punkte aus Runde 7 sind bestätigt geschlossen. Empfehlung: „freigabereif nach Behebung der geringen Punkte“. Der einzige geringe Befund ist behoben (elfte Fassung): **Vorrang der Sperre** unter 16 auch nach abgeschlossenem Profil. Die Anmeldung führt dann auf `/konto` mit nur der Meldung aus 4.5, „Abmelden“ und „Konto löschen“, ohne Häkchen, Fragebogen und Schalter (5.1 Schritt 7, 5.7, 8).
- **16.11.2026: vom Auftraggeber freigegeben.** Umsetzung strikt nach diesem Plan und den Freigaben in Abschnitt 15. Weicht der Code vom Plan ab, wird gefragt und der Plan nachgezogen.
- 16.11.2026: **Schritt 1 ausgeführt** (Rechte-Prüfung, Audit-Prüfung, Audit-Probelauf). Keine echte Lücke. Einziger Treffer: Supabase-Standardrechte TRUNCATE, REFERENCES und TRIGGER für `anon` und `authenticated`, Härtung in `database/konten_haertung_2026-11-16.sql` (4.0). Audit-Log: Löschen als `postgres` geht, die Tabelle ist aber leer. Die Protokolle liegen in den Plattform-Protokollen von Supabase, deren Frist in Schritt 2 ermittelt wird (4.6, 9.1, 19 Punkt 7a).
- 16.11.2026: **Schritt 1 abgeschlossen.** Härtung ausgeführt, zweite Rechte-Prüfung ohne LÜCKE. Rest: Standardrechte für künftige Tabellen von `supabase_admin` (von `postgres` nicht änderbar). Dagegen setzt Schritt 3 die Rechte jeder neuen Tabelle ausdrücklich, und die Rechte-Prüfung läuft vor dem Einschalten in Schritt 8 noch einmal (4.0, 15).
- 16.11.2026: **Schritt 2 vorbereitet.** Checkliste, Mailvorlagen (ohne Link bei Mailänderung, Magic Link und Einladung, 10.3) und Vorlagen für TIA und Verarbeitungsverzeichnis geliefert. Neuer offener Punkt 19.14: Vorversuch braucht einen Weg trotz ausgeschaltetem Signup.
- 16.11.2026: **neunte Cursor-Prüfung** (Schritt 1 und Unterlagen zu Schritt 2): kein kritischer Befund. Urteil: Schritt 1 abgeschlossen, Unterlagen können an den Auftraggeber. Alle Befunde behoben:
  - **M (Bewertungsformel der Rechte-Prüfung):** „ok“ nur noch, wenn der Ausdruck nach Ersetzen der bekannten Bindungen vollständig aufgeht. `OR true`, `IS NOT NULL`, Bucket-Filter mit `OR` und INSERT ohne `WITH CHECK` ergeben „prüfen“. Nachgeprüft mit Testausdrücken (4.0). Der zweite Teil des Befunds traf nicht zu: Die drei öffentlichen INSERT-Policies hat `meldungen_haertung_2026-11-05.sql` schon entfernt, der Live-Lauf bestätigt das. 4.0 nennt sie jetzt ausdrücklich als „darf nicht wieder auftauchen“.
  - **M (TIA):** Die FISA-702-Einordnung und die Verschlüsselung im Ruhezustand sind jetzt Fragen an den Anwalt. Als ergänzende Maßnahmen stehen nur noch solche ohne Schlüsselhoheit. Der Ergebnis-Mustersatz behauptet keinen Drittland-Hinweis in der Einwilligung mehr.
  - **G:** `erstellt_am` in 4.0 genannt. SPF-Vorlage getrennt nach „nur IPv4“ und „mit IPv6“, ohne `a:` und `mx`. Teil F prüft nur SMTP, der Linktest steht allein in G und läuft nur über „Send password recovery“. Hinweis, Einladen und Magic Link nicht zu nutzen und Admins nur per „Add user“ anzulegen. 9.1 und 4.6 sagen jetzt „soweit die Plattform-Protokolle sie führen“. Der Inhalt der Auth-Logs wird in Schritt 2 nachgesehen (Checkliste H, J).
  - **19.14:** Empfehlung „Signup kurz einschalten“ eingetragen. Die Entscheidung trifft der Auftraggeber vor Schritt 4.
- 16.11.2026: **Kontrolllauf der verschärften Rechte-Prüfung** (zweite Fassung): fehlerfrei durchgelaufen, keine LÜCKE. Nur die vier Whitelist-Lesewege gehen nicht auf und werden als gewollt erkannt (4.0). Schritt 1 bleibt abgeschlossen.
- 16.11.2026: **Schritt 3 geschrieben** (Migration, SQL-Tests, Rückbau). Auf Wunsch des Auftraggebers geht der Bau vor Schritt 2 weiter. Nur der Vorversuch in Schritt 4 wartet auf Schritt 2 (15).
  - Abweichung zur Freigabe: Die Mindestalter-Prüfung beim Merken steht im Trigger statt in der Policy (4.3). Vom Auftraggeber bestätigt am 16.11.2026.
  - Ergänzungen ohne Änderung des Verhaltens:
    - Die CHECK-Bedingungen in `sensibel_regeln` kompilieren jedes Muster beim Eintragen, damit ein kaputtes Muster nie einen Event-Insert scheitern lässt.
    - `einwilligungstexte` ist auch gegen TRUNCATE geschützt.
    - `konto_protokoll_loeschen` lehnt Admin-Konten ab (`admin_konto`).
    - `merk_statistik` rechnet `von`/`bis` in deutscher Zeit, beide Grenzen einschließlich.
    - `anon` verliert alle Rechte auf `profiles` (ohne Policy waren sie wirkungslos).
  - Rechte-Prüfung: `einwilligungstexte` steht auf der Whitelist. `merk_statistik` wird als gewollt erkannt (4.0).
- 16.11.2026: **Schritt 4, Server-Teil gebaut** (ohne Vorversuch). Umsetzungsdetails, die der Plan offen ließ oder die beim Bau dazukamen:
  - **Identität prüfen:** Die Nutzer-ID kommt nie ungeprüft aus dem Cookie. `tokenPruefen` (`lib/konto/clients.ts`) prüft jedes Access-Token mit `auth.getClaims` auf dem einen Lese-Client pro Prozess: lokal über die JWKS, bei symmetrischen Schlüsseln per `getUser`. Grund: Die Routen schreiben mit dem Dienst-Client für genau diese ID.
  - **Annahmen bis zum Vorversuch:**
    - Bestätigungslink mit `type: 'email'` (`BESTAETIGUNG_TYP` in `link-pruefen`).
    - `email_not_confirmed` gilt als Fehler, der nur bei richtigem Passwort kommt.
    - Noch keine Mindestdauer gegen Zeitunterschiede.
    - Alle drei Punkte werden nach dem Vorversuch geprüft und gegebenenfalls geändert.
  - **`abschluss`:** (d) Geburtstag wird **zuerst** verarbeitet. So ist bei „unter 16“ nachweislich nichts anderes gespeichert, wie es 16.1 verlangt. Danach folgen (a), (b), (c), `praeferenzen` und `onboarding_fertig_am`. Bei der Wiederholung erkennt die Route an den eigenen Zeilen in `einwilligungen` (`handlung = 'abschlussseite'`), ob eine verneinte Angabe schon einen Nachweis hat.
  - **`einstellungen`:** Ohne Alters-Häkchen ist dort nur die Art `mindestalter` erlaubt, alle anderen antworten 403 `mindestalter_fehlt`. `mindestalter` nimmt nur `erteilt: true` an.
  - **Übernahme:** Existenz, Ablehnung und Weiterleitung prüft der Dienst-Client, weil abgelehnte Events für `authenticated` per RLS unsichtbar sind und sonst fälschlich als „ungültig“ vom Gerät gelöscht würden. Eingefügt wird in einer Anweisung (`upsert`, `ignoreDuplicates`). Scheitert sie, ist nichts geschrieben, und die Geräteliste bleibt unverändert (5.4 Schritt 10).
  - **Origin:** `localhost:3100/3200` gelten nur, wenn die Anfrage selbst an localhost geht. Live gilt allein `SITE_URL`.
  - **Bremse:** Fehlversuche beim Anmelden, beim Ersatz-Code und bei `passwort-aendern` zählen über eigene Schlüssel (`anfragenImFenster`).
  - **Noch nicht gebaut:** Das Aufteilen des Sitzungs-Cookies über 3,5 KB (bisher nur eine Fehlermeldung im Log; gemessen wird im Vorversuch). Tests für `passwort-aendern`, `vorlieben` und `link-pruefen` mit Attrappe. Die Prüfsummen der Einwilligungstexte folgen mit Schritt 6.
- 16.11.2026: **Schritt 5 gebaut** (Oberfläche, lokal). Umsetzungsdetails:
  - **Schalter in der Oberfläche:** Server-Komponenten lesen `KONTEN_AKTIV` beim Build (`kontenAktiv()`) für Kopf, Menü, Fuß, die Konto-Seiten und die Merkliste. Client-Bausteine lesen ihn aus `<body data-konten="1">`. Ein Umschalten braucht also einen neuen Build, wie bei jedem Deploy.
  - **Merklisten-Store:** Die reine Logik liegt in `lib/konto/merk-logik.ts` (getestet), der Browser-Teil in `merk-store.ts`, mit Web-Locks-Sperre und Ersatz-Merker. `KontoSync` im Layout startet die Übernahme beim Seitenaufruf sowie Warteschlange und Abgleich beim Fokus.
  - **„Interessen ändern“** öffnet `/konto/willkommen?modus=interessen` mit den gespeicherten Werten.
  - **„Vorbei (n)“ (E9)** gilt auch abgemeldet, nicht nur im Konto. Abgemeldet bleibt es bei `/api/events` mit höchstens 100 IDs wie bisher.
  - **Einwilligungstexte** stehen als Entwurf in `lib/konto/texte.ts` (Wortlaut aus 5.3), endgültig mit Schritt 6.
  - **`/nutzungsbedingungen`** gibt es noch nicht (Schritt 6). Der Link im Registrierungsformular führt bis dahin auf 404, der Fuß-Link ist noch nicht eingebaut.
  - **Nicht abgedeckt:** Der Komponenten-Test „Fragebogen sendet nichts vor Fertig“ ist offen, weil die Tests ohne Browser-Umgebung laufen. Das Verhalten folgt aus dem Aufbau: Die Antworten liegen nur im Zustand der Komponente, und die einzige Anfrage steht in `speichern`.
  - **Browser-Prüfung abgemeldet**, Dev-Server mit `KONTEN_AKTIV=1`, Konfiguration `ddd-web-konten` in `C:\Claude_DDD\.claude\launch.json`. Geprüft und in Ordnung:
    - Leerzustand mit Anmeldehinweis
    - Hinweis nach dem ersten Merken
    - Kasten „Eure Merkliste auf allen Geräten“
    - Anmelden und Konto anlegen, mit gesperrtem Knopf ohne Alters-Häkchen
    - `/konto` abgemeldet
    - `/konto/bestaetigen` ohne Fragment (Code-Feld) und mit Reset-Fragment: Das Fragment wird entfernt, `no-referrer` ist gesetzt.
    - `X-Robots-Tag` nur auf `/konto`, kein `Set-Cookie` auf `/`, `Cache-Control: private, no-store` auf `/api/konto/ich`
    - mobil 375 px ohne Querscrollen, dunkler Modus
    - Konto-Links in Kopf, Mobilmenü und Fuß

    Keine Formulare abgeschickt (sie sprächen das echte Supabase-Projekt an).
- 16.11.2026: **zehnte Cursor-Prüfung** (Umsetzung der Schritte 3–5). Kein kritischer Befund. Urteil: Die Migration kann ausgeführt werden. Server und Oberfläche sind für die angemeldeten Tests nach Schritt 2 bereit. Alle Befunde behoben:
  - **M (Abmelden):** `abmelden()` (`merk-store.ts`) sendet zuerst die Warteschlange, solange die Sitzung gilt, und wartet dann auf `POST /api/konto/abmelden`. Lokal abgemeldet wird nur bei 200, 401 oder 404. Sonst bleibt alles, wie es ist, und die Seite meldet den Fehler (5.6).
  - **G (offene Löschung):** Ein beim lokalen Abmelden noch nicht gesendetes „entfernen“ landet in `ddd-merkliste-entfernen-offen`. Die Konto-Ansicht blendet es aus, und beim nächsten Anmelden auf diesem Gerät geht es als Löschauftrag in die Warteschlange. Wird das Event abgemeldet neu gemerkt, entfällt die offene Löschung.
    - Restrisiko, hingenommen: Meldet sich auf demselben Gerät danach ein **anderes** Konto an, das dasselbe Event gemerkt hat, wird es dort entfernt. Das setzt voraus, dass beide Konten dasselbe Gerät nutzen und die Sitzung widerrufen wurde, während eine Löschung offen war.
  - **G (Ersatz-Sperre):** Ohne Web Locks wartet der Tab bis zum Ablauf eines fremden Merkers und versucht es genau einmal erneut (5.4 Schritt 0).
  - Hinweis aus dem Urteil: Abschluss, Schalter und Nachweise schreiben erst, wenn die Versionen aus `TEXTVERSIONEN` als Zeilen in `einwilligungstexte` stehen (Schritt 6). Für angemeldete Tests vorher braucht es Testzeilen, die nach dem Test wieder entfernt werden. Das klärt der Auftraggeber vor den Tests.
- 17.11.2026: **Mailversand über den eigenen Server erprobt** (E3 bleibt).
  - Von außen geprüft: Ports 587 und 465 sind offen, Zertifikat gültig nur für `k49q02.meinserver.io`, Reverse-DNS passt, SPF `a mx` deckt den Server ab, keine IPv6-Adresse.
  - Der Auftraggeber hat Mail-Domain und Postfach `konto@diesdas.events` in ISPConfig angelegt und SMTP in Supabase eingetragen (Host `k49q02.meinserver.io`, Port 587). Die Recovery-Mail kommt an.
  - **Offen: DKIM- und DMARC-Eintrag im DNS bei Timme** (Stand 17.11.: fehlen noch). Die Fragen an den Hoster aus der Checkliste Teil B sind damit größtenteils durch den Test beantwortet; offen bleiben nur Mail-Limit und AV-Vertrag.
  - **Mailvorlagen im dies.das-Design:** erzeugt aus `web/scripts/konto-mails.mjs` nach `docs/konto-mails/` (sechs Vorlagen, Vorschau, Ersatz-Code-Block). `docs/konto-mails-2026-11-16.md` ist die zweite Fassung zur Freigabe.
- 17.11.2026: **Mailvorlagen auf du umgestellt** (Wunsch des Auftraggebers). Bedienelemente heißen in den Mails „Button“ statt „Knopf“. Dritte Fassung von `docs/konto-mails-2026-11-16.md`, neu erzeugt aus `web/scripts/konto-mails.mjs`. Offen ist die Frage, ob die Konto-Seiten der Website (ihr-Form laut Plan, 7.1 und Abschnitt 19 Punkt 3) ebenfalls auf du umgestellt werden.
- 17.11.2026: **Ansprache auf du umgestellt, auch auf der Website** (Entscheidung des Auftraggebers). Damit ist Abschnitt 19 Punkt 3 entschieden.
  - Betroffen: Konto-Seiten, Merkliste-Seite, Hinweis nach dem ersten Merken, Fragebogen und alle Fehler- und Erfolgsmeldungen der Konto-Routen. Bedienelemente heißen „Button“.
  - Die Plan-Wortlaute in 5.1, 5.3, 7.1 und 7.2 gelten sinngemäß in du-Form.
  - **Bewusst noch in Sie-Form:** die Datenschutz-Erklärtexte in den Einwilligungen („Ihr Widerspruchsrecht“, Erklärtext zu sensiblen Events, Widerrufsdialog), weil Datenschutztexte nach Projektregel gesiezt werden. Ob sie für die Seite ebenfalls ins du wechseln, klärt die anwaltliche Durchsicht in Schritt 6.
  - Die Häkchen-Sätze bleiben in der Ich-Form.
- 17.11.2026: **Auch die Datenschutz-Erklärtexte in den Einwilligungen per du** (Entscheidung des Auftraggebers): „Dein Widerspruchsrecht“, Erklärtext zu sensiblen Events, Widerrufsdialog (`lib/konto/texte.ts`). Die Datenschutzerklärung (`/datenschutz`) bleibt unverändert in Sie-Form. Die Vorschau `docs/konto-mails/vorschau.html` hat jetzt je Vorlage „Betreff kopieren“ und „HTML kopieren“.
- 17.11.2026: **Mailversand vollständig eingerichtet:** Vorlagen in Supabase eingetragen, DKIM (`default._domainkey`, 2048 Bit) und DMARC (`p=none`) im DNS bei Timme. Testmail mit SPF, DKIM und DMARC „PASS“ (Auftraggeber). Die Hoster-Anfrage aus Schritt 2 entfällt bis auf den AV-Vertrag.
- 17.11.2026: **Schritt 6 vorbereitet (Rechtstexte als Entwürfe für den Anwalt).** Die Datenschutzerklärung auf der Website bleibt unverändert, bis die Texte freigegeben sind.
  - `docs/datenschutz-konto-entwurf-2026-11-17.md`: neuer Abschnitt 13 „Nutzerkonto“ und Änderungen an 3, 5, 7, 9, 14–17, Sie-Form
  - `docs/nutzungsbedingungen-entwurf-2026-11-16.md`: durchgesehen, neue Prüfpunkte 6–8
  - `docs/einwilligungstexte-2026-11-17.md`: alle Wortlaute mit Versionen, du-Form
  - `docs/interessenabwaegung-statistik-2026-11-17.md`
  - `docs/dsfa-schwellenwert-nutzerkonten-2026-11-17.md`: Vorschlag „keine vollständige DSFA“
  - `docs/anwalt-schritt6-nutzerkonten-2026-11-17.md`: Begleitschreiben mit 13 Fragen
  - Offen vor der Veröffentlichung: Supabase-Log- und Backup-Fristen, DPF-Status, Aufbewahrung der Nachweise nach Löschung, Monat für „Stand“. Nach der Freigabe folgen: SQL für `einwilligungstexte`, die Ergänzung von `/datenschutz` und die Seite `/nutzungsbedingungen`.
- 17.11.2026: **Schritt 6 freigegeben (Anwalt, Mitteilung des Auftraggebers).** Kein Befund. Duzen ist akzeptabel, der Versand über den eigenen Server ist optimal.
  - Datenschutz-Ergänzung, Nutzungsbedingungen, Einwilligungstexte und Interessenabwägung: so umsetzbar.
  - DSFA: Der Anwalt sieht keine zwingende Notwendigkeit. Der Auftraggeber entscheidet, ohne DSFA umzusetzen (dokumentiert in `docs/dsfa-schwellenwert-nutzerkonten-2026-11-17.md`).
  - Angaben: Supabase-Logs 7 Tage, Backups 7 Tage, nicht unter dem EU-US Data Privacy Framework (Grundlage bleiben die Standardvertragsklauseln), erwartet 500–1.000 Konten im ersten Jahr.
  - **SQL `database/einwilligungstexte_2026-11-17.sql`**: erzeugt aus `web/lib/konto/texte.ts` (`NACHWEIS_TEXT`) durch `web/scripts/einwilligungstexte-sql.mjs`, mit SHA-256-Prüfsummen. `tests/konto-texte.test.ts` prüft Code gegen SQL (Plan 4.4, 16.1).
  - Noch offen in Schritt 6: Übernahme in `/datenschutz` und Seite `/nutzungsbedingungen`. Beides geht erst mit dem Einschalten live (Schritt 8). Der „Stand“ wird der Monat des Einschaltens.
- 17.11.2026: **Schritt 7 gebaut.**
  - **Sensibel-Nachtrag** in zwei Dateien statt einer (sicherer, weil der SQL-Editor immer alles ausführt): `database/sensibel_nachtrag_vorschau_2026-11-17.sql` (nur lesend, Treffer ab heute minus 400 Tage) und `database/sensibel_nachtrag_2026-11-17.sql` (Ausnahmen-Block für bestätigte Fehltreffer plus INSERT in einer Transaktion).
  - **Aufräumjob** `pipeline/konten_aufraeumen.py`: unbestätigt nach 48 h, ohne Alter nach 7 Tagen, gesperrt unter 16 beim nächsten Lauf, Anmeldeprotokoll-Waisen.
    - Admins nie. Bestätigte Konten ohne Profil bleiben stehen. Mehr als 200 Löschungen je Lauf nur mit `--erzwingen`.
    - `--dry-run` für den Probelauf. Ins Log kommen nur Anzahlen und gekürzte IDs.
    - Eingehängt in `main.py` als Schritt 2c.
    - Hilfsfunktion `konto_protokoll_waisen()` in `database/konten_aufraeumen_2026-11-17.sql`.
    - Tests: `tests/test_konten_aufraeumen.py` (unittest, 8 Tests grün).
  - Hinweis: Der Job läuft erst nach einem Deploy in der Pipeline. Ohne ausgeführte Migration bricht er mit einer Meldung ab und löscht nichts.
- 17.11.2026: **Migration Schritt 3 ausgeführt** (Auftraggeber). Die Kontrollabfrage von `konten_2026-11-16.sql` zeigt alle Zeilen „ok“, auch alle 28 Muster-Tests einschließlich der Umlaute. Die SQL-Tests `konten_tests_2026-11-16.sql` zeigen „65 ok, 0 FEHLER“ (zurückgerollt). Nächste Dateien: `einwilligungstexte_2026-11-17.sql`, `konten_aufraeumen_2026-11-17.sql`, `sensibel_nachtrag_vorschau_2026-11-17.sql`.
- 17.11.2026: Einwilligungstexte eingetragen. Vier Fassungen sind „ok“. Zwei Fassungen mit Absatz (sensible-events, analyse-hinweis) wichen ab, vermutlich weil die Zeilenumbrüche beim Kopieren unter Windows zu `\r\n` wurden. Der Generator schreibt Umbrüche jetzt als `\n`-Escape. `database/einwilligungstexte_reparatur_2026-11-17.sql` ersetzt nur abweichende Fassungen ohne Nachweise und schaltet den Schutz-Trigger dafür kurz ab. `konten_aufraeumen_2026-11-17.sql` ist ausgeführt (Rechte korrekt, 0 Waisen).
- 17.11.2026: **Sichtprüfung Sensibel-Nachtrag.** 46 Treffer (gesundheit 5, gewerkschaft 1, politik 1, religion 7, sexualitaet 32). Vorschlag: 13 Fehltreffer als Ausnahmen. Grundsatz: Steht das Stichwort nur in der Inhaltsbeschreibung eines Stücks, Films, Konzerts oder einer Ausstellung, ist das ein Fehltreffer; im Zweifel bleibt der Treffer sensibel. Die Ausnahmen stehen in `database/sensibel_nachtrag_2026-11-17.sql`. **Vom Auftraggeber übernommen und ausgeführt:** 13 Ausnahmen, 33 Events gekennzeichnet (gesundheit 3, gewerkschaft 1, politik 1, religion 5, sexualitaet 23). Beobachtung für später: Die Regeln zu sexualitaet treffen oft auf Inhaltsbeschreibungen. Eine Verfeinerung (z. B. nur Titel und Ort oder Kontextwörter) wäre ein eigener kleiner Plan.
- 17.11.2026: Reparatur der Einwilligungstexte ausgeführt. Alle sechs Fassungen sind „ok“, keine Windows-Zeilenumbrüche mehr, Schutz-Trigger wieder an.
- 17.11.2026: **Probelauf des Aufräumjobs** (Auftraggeber): ein Konto (Admin), keine Kandidaten, 0 Waisen, 0 Fehler. **Schritt 7 damit abgeschlossen.** Nachbesserung aus dem Probelauf: httpx loggte die Anfrage-URLs mit vollständigen Nutzer-IDs auf INFO. Der Job dämpft diese Bibliotheken jetzt während des Laufs auf WARNING, weil das Pipeline-Log als Artefakt in GitHub Actions liegt.
- 17.11.2026: **E16 – Name und Geburtsdatum als Pflichtangaben** (Entscheidung des Auftraggebers, ersetzt E15 „Geburtsdatum freiwillig“). Vorname, Nachname und Geburtsdatum werden nach den Interessen im neuen Schritt „Noch kurz zu dir“ abgefragt, alle Pflicht, im Konto änderbar (`PUT /api/konto/stammdaten`). Rechtsgrundlage lit. b: Geburtsdatum zur Altersprüfung, Name laut Auftraggeber für den geplanten Ticketverkauf. Claude hat auf Zweckbindung und Datenminimierung hingewiesen (Abfrage beim ersten Ticketkauf wäre vorsichtiger); die schriftliche Freigabe holt der Auftraggeber beim Anwalt ein (`docs/anwalt-nachtrag-stammdaten-2026-11-17.md`). Die Geburtstagsmail bleibt Einwilligung (d) nach § 7 Abs. 2 UWG, auch eine reine Glückwunschmail gilt als Werbung. Neue Fassung `geburtstagsmail-2026-11-2`, Widerruf löscht das Datum nicht mehr. Datenbank: `database/konten_stammdaten_2026-11-17.sql` (Spalten vorname/nachname, Prüfbedingungen name_plausibel, geburtstagsmail_nur_mit_datum, onboarding_nur_mit_stammdaten, Funktion stammdaten_setzen ersetzt geburtstag_setzen). SQL-Tests in `konten_tests_2026-11-16.sql` angepasst. Datenschutz-Entwurf, Nutzungsbedingungen und Textkatalog angepasst. Nebenbei: Registrierung bricht ohne Service-Key jetzt mit 503 ab, statt ein Konto ohne Altersnachweis anzulegen; Datenschutz-Hinweis im Registrierungsformular zusammengezogen.
- 17.11.2026: Folgeplan **Freunde und Sichtbarkeit der Merkliste** als Entwurf angelegt: `docs/plan-sichtbarkeit-freunde-2026-11-17.md` (Entscheidungen F1–F9 und Anwaltsfragen A1–A6 offen, beginnt erst nach Schritt 8 dieses Plans).
- 17.11.2026: **Rechtstexte eingebaut (Rest von Schritt 6), Schalter im Deploy (Vorbereitung Schritt 8).** Abschnitt 13 „Nutzerkonto“ samt Ergänzungen in den Abschnitten 3, 5, 7, 9, 15, 16 steht in `web/app/datenschutz/page.tsx` (+ `konto-abschnitt.tsx`) und erscheint nur mit `KONTEN_AKTIV`; die Abschnitte danach werden dann zu 14–18. Neue Seite `web/app/nutzungsbedingungen/page.tsx` (ohne Schalter 404), Link im Fuß. Offene Klammern aus den Entwürfen mit den freigegebenen Werten gefüllt (Kündigungsfrist zwei Wochen, Änderungsmitteilung sechs Wochen, Nachweise „wie das Konto“), Prüfhinweise entfernt. „Stand“ steht auf November 2026 (`STAND_MIT_KONTEN` bzw. `STAND`) und ist beim Einschalten auf den Monat anzupassen. `deploy.yml` schreibt `KONTEN_AKTIV` aus der GitHub-Variable `vars.KONTEN_AKTIV` (nur „1“ schaltet ein, sonst immer ausdrücklich 0) vor dem Build nach `web/.env.local`. Geprüft: Build mit Schalter aus (Erklärung unverändert, Nutzungsbedingungen 404) und an (Abschnitte 1–18, Tabelle seitlich scrollbar), 408 Tests grün.
