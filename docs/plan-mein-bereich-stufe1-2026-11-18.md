# Plan: „Mein dies.das“ – Stufe 1 (eingeloggter Bereich, „Für dich“, Startseiten-Module, Vorschau für Abgemeldete)

Stand: 19.11.2026 · **fünfte Fassung, vom Auftraggeber FREIGEGEBEN am 19.11.2026. Umsetzung erst auf ausdrückliche Anweisung.** S1–S7 bleiben bestätigt. Eingearbeitet: erste Cursor-Prüfung (18.11.), zweite Cursor-Prüfung (19.11.), dritte Prüfung durch Claude Code gegen den Live-Code (19.11.) und vierte Prüfung durch Cursor (19.11., Abschnitt 13): Abgleich von `html[data-konto]` auch über `abruf` und die Merkliste, Hinweis-Cookie bei Bearer nur an den zwei Wrapper-Stellen, Fenster und Deckel je Abschnitt, `metaZeile` statt „in 3 Tagen“, keine Geräte-IDs als `ohne`. Nichts umgesetzt. Nächster Schritt: Freigabe durch den Auftraggeber.

**Grundlagen:**
- `docs/konzept-personalisierung-2026-11-18.md` (P1–P7; S1–S7 bestätigt). Leitidee 4 im Konzept ist für **Vorschläge und Statistik** gemeint. Eigene Merkliste, „Deine nächsten Events“, Erlebt und die Zählungen dürfen eigene sensible Merkungen zeigen, ohne Kennzeichnung (Kontenplan E13 + S4, siehe 8).
- `docs/plan-nutzerkonten-2026-11-16.md`: Abschnitt 13 „Für euch“ (wird ersetzt), E13, 3.5 Caching, 4.4 Einwilligungen

Regeln wie bei den anderen Plänen: Deploy nur nach OK, SQL nur als Datei in `database/` (führt der Auftraggeber aus), keine neue Bibliothek ohne Rückfrage, Texte auf Deutsch. Konto-Seiten per du, „Button“ statt „Knopf“.

**Umfang Stufe 1:**
1. Der eingeloggte Bereich wird in Unterseiten geteilt: Inhalte getrennt vom Organisatorischen (P2).
2. **B1** „Für dich“: persönliche Vorschläge aus Interessen und Merkliste.
3. **B2** Startseite bekommt zwei persönliche Module, „Für dich empfohlen“ und „Deine nächsten Events“ (P3).
4. **B18** Vorschau „Für dich empfohlen“ für Abgemeldete, verschwommen, mit Hinweis zur Registrierung (P1).

**Nicht in Stufe 1:** Folgen (B4, nach den Location-Seiten), Feedback (B3), Kalender und ICS (B5), Benachrichtigungen (B6–B9, B14), App.

---

## 1. Geprüfte Fakten (Code, Stand 19.11.2026)
- **Startseite `web/app/page.tsx`:**
  - `instant = false`. Sie liest `searchParams` oben (`/?datum=`). Das ist kein `cookies()`, kein `headers()` und kein `connection()`. Persönliche Daten stehen nicht im HTML.
  - `/` bleibt die gecachte Startseite. `/?datum=…` ist eine Variante derselben Seite und bei Parametern `noindex` (`hatParameter`). Beide Varianten bleiben ohne `Set-Cookie`. Es gibt im Code kein `s-maxage` auf `/`; keines verlangen.
  - Reihenfolge: Hero mit Kennzahlen und Datumsleiste → „Tipp und Picks“ (`startPlaetze`) → `WmStartBox` (Weihnachtsmärkte, in Suspense) → „Diese Woche beliebt“ (`beliebtAuswahl`) → Infoboxen (Abend, Neu, Stadtteile) → Kategoriezeilen → Kostenlos/Themen → Wochenend-Programm.
  - Der Zeitraum kommt aus `zeitraumAuflösen` (`web/lib/datum.ts`). Ungültiger Key fällt auf „heute“ (`von` = `bis` = `heute`), kein 400.
  - **Öffentliches „Heute“** ist ein einzelner Tag (`von === bis`). `fokusTag` in `page.tsx` Zeile 97 ist nur dann gesetzt. `beliebtAuswahl(imZeitraum, woche, stufen, fokusTag, 5, schonGezeigt)` filtert `amFokustag` nur bei `tag !== null`. Die Woche ist nur **Reserve** zum Auffüllen, und auch die Reserve muss am Fokustag von *heute* liegen. Das persönliche Modul auf „Heute“ (4.2: sieben Tage) ist **nicht** derselbe Aufruf.
- **Empfehlungslogik `web/lib/ableitungen.ts`:**
  - Stufen und Sortierschlüssel: `stufenKontext`, `breite` (Stufe 0–3, abgesagt → null), `startPlaetze`, `beliebtAuswahl`.
  - `nachEmpfehlung(k, tag)`: Bild, Stufe, nur wenn `tag` gesetzt *und* beide ein Bild haben zusätzlich Fokustag, dann Beliebtheit ohne Flaggen, Hash, Zeit, ID.
  - `beliebtAuswahl` filtert `amFokustag(e, tag)` hart und sortiert dann mit `nachEmpfehlung(k)` **ohne** `tag`. Wo der Fokustag schon Filter ist, ändert ein `tag` in der Sortierung nichts.
  - `filtern()` lässt Langläufer standardmäßig weg (`findetStatt(…, mitLanglaeufern)`). `startPlaetze` bekommt sie (`mitLanglaeufern: true`), `beliebtAuswahl` auf der Startseite nicht (`imZeitraum`, `woche` ohne Langläufer).
  - `beliebtAuswahl` kann **nicht** „Fokustag liegt irgendwo in sieben Tagen“ ausdrücken. Entweder ein Tag (`tag` gesetzt) oder kein Fokustag (`tag === null`). Persönliche Fenster mit `fokus: im-fenster` brauchen eine eigene Kandidatenliste, danach Sortierung (5).
  - Serien und Stamm werden erkannt.
- **Event-Daten:**
  - `eventPoolLaden()` in `web/lib/daten.ts`, gecacht. `heute` kommt aus `heuteBerlin` (`Europe/Berlin`).
  - Karten aus `web/components/karten.tsx` (`EventKarte`, `KompaktKarte`) sind auch in Client-Komponenten nutzbar, so macht es heute schon die Merkliste.
- **Merkliste `web/components/merkliste.tsx`:**
  - Angemeldet über `GET /api/konto/merkliste?mit=events`, abgemeldet über `/api/events?ids=…`.
  - Kommende Events sortiert, darunter „Vorbei (n)“ eingeklappt (E9).
  - `GET /api/konto/merkliste` läuft **ohne** `ohneMindestalter`. Cookie `0` (Alter fehlt / unter 16) bekommt 403 `mindestalter_fehlt`; der Client ruft `lokalAbmelden(true)` auf und zeigt die Geräteliste. Deshalb bleibt auf `/merkliste` bei Cookie `0` „Vorbei“, nicht „Erlebt“.
- **Konto heute:**
  - Eine Seite `/konto` (`components/konto-bereich.tsx`, `KontoSeite`) mit den Abschnitten Konto, Interessen, Über dich, Einwilligungen, Passwort, Daten, Abmelden, Löschen.
  - Interessen ändern läuft über `/konto/willkommen?modus=interessen`.
  - Alle Konto-Seiten sind statische Hüllen, die Daten kommen per Client-Abruf (`private, no-store`).
  - 403 `passwort_setzen_noetig` auf der Konto-Hülle: Redirect nach `/konto/passwort-neu` (`konto-bereich.tsx`). Die Startseiten-Insel hat diese Hülle nicht (3.0, 4.1).
- **Kontomodus im Browser:**
  - Hinweis-Cookie `ddd_konto` (`web/lib/konto/cookies.ts`, `hinweisFuer` in `web/lib/konto/route.ts`):
    - fehlt = abgemeldet
    - `1` = angemeldet und `mindestalter_bestaetigt_am` gesetzt
    - `0` = angemeldet, aber Alters-Häkchen fehlt **oder** Konto unter 16 gesperrt (`stammdaten_setzen` bei unter 16: `mindestalter_bestaetigt_am = NULL`, `unter16_gesperrt_am = now()`, Client setzt Cookie `0`)
  - Eine Reset-Sitzung (`nur_passwort`) setzt `ddd_konto` nicht (`anmeldung.ts`). Die Website bleibt im abgemeldeten Aussehen (Kontenplan 5.1), **einschließlich B18**.
  - `body[data-konten="1"]` ist nur der Schalter `KONTEN_AKTIV` beim Rendern des Layouts (`web/app/layout.tsx`). Das ist kein Personenstatus.
  - `useKontomodus()` / `kontomodus()` liest nur `ddd_konto=1`. `angemeldetOhneAlter()` liest `=0`. Es gibt noch kein `html[data-konto]`.
  - Der Client ändert `ddd_konto` selbst nur in `hinweisSetzen` (`merk-store.ts`, über `lokalAbmelden`). Sonst setzt der Server es per `Set-Cookie` auf Konto-Abrufen (Anmelden, Bestätigen, Alters-Häkchen, jede erfolgreiche Konto-Route). Danach navigiert der Client meist ohne Neuladen (`router.push`). **Ein Skript im Head allein würde `data-konto` also nach Anmelden, Abmelden oder 403 bis zum nächsten Neuladen falsch stehen lassen.** `KontoSync` (`components/konto.tsx`) gleicht heute nur die Merkliste ab, nicht das Attribut (3.0, „Abgleich im Client“).
- **Frühes Skript:** `THEME_SCRIPT` in `web/app/layout.tsx` setzt `data-theme` am `html`, bevor React malt. `<html>` hat `suppressHydrationWarning`. Das Konto-Attribut folgt diesem Muster und wird **nicht** vom Server ins HTML geschrieben.
- **TabBar (mobil)** `components/client.tsx`, `TABS`: Start, Entdecken, Heute, Wochenende, Merkliste. `istAktiv` nutzt `startsWith` (Ausnahme `/` exakt, `/heute` inkl. `/tag/`). Ein Tab auf `/konto` wäre damit auch auf `/konto/fuer-dich` aktiv. Die neue Leiste braucht eigene Regeln (3.9). Beide Leisten stehen im gecachten HTML.
- **Kopf:** Konto-Icon „Mein Konto“ führt auf `/konto`, mobil und am Desktop.
- **Konto-Daten für Vorschläge:**
  - Interessen in `profiles.praeferenzen` (Format Kontenplan 4.2), nur mit `personalisierung = true` (CHECK in der Datenbank). „Von allem etwas“ ist kein eigenes Feld: der Fragebogen speichert alle Slugs aus `KATEGORIEN` (`willkommen/page.tsx` mappt `KATEGORIEN`; `sonstiges` liegt nicht in diesem Array, `vorlieben.ts` filtert es zusätzlich).
  - Vorname und Nachname liegen in `profiles.vorname` und `profiles.nachname`, nicht in `anzeigename`.
  - Merkliste in `public.merkliste`. `GET /api/konto/merkliste?mit=events` liefert die IDs und die Events, kommende und vergangene. Die Seite teilt sie lokal (`merklisteAufteilen` in `merk-logik.ts`). Ein Parameter `vorbei` existiert nicht.
  - Kennzeichnung sensibler Events in `public.event_sensibel`. Lesen darf das nur der Dienst-Client (`kontoDienstClient()`), so wie `uebernehmen/route.ts`. Der Nutzer-Client aus `kontoRoute` (`ctx.db`) darf die Tabelle nicht lesen.
- **`kontoRoute` (`web/lib/konto/route.ts`):**
  - Schalter aus → 404. Keine gültige Sitzung → 401 `abgemeldet`. `cookiesLoeschen` (Sitzung **und** `ddd_konto`) hängt nur dran, wenn ein Sitzungs-Cookie da war, aber unleserlich, kaputt, mit fehlgeschlagenem Refresh oder mit ungültiger Signatur ist. **Fehlt das Sitzungs-Cookie ganz** (`sitzungAusAnfrage`: `!roh`), fehlt das Profil, oder scheitert das Erneuern schon daran, dass kein Auth-Client da ist (`!client`, `setCookies: []`), kommt die 401 **ohne** Lösch-Cookies. Ein liegengebliebenes `ddd_konto=1` räumt dann nur der Client (`lokalAbmelden()`).
  - `nur_passwort` ohne `resetErlaubt` → 403 `passwort_setzen_noetig`. Profil wird in diesem Zweig **nicht** geladen, `ddd_konto` wird nicht gesetzt.
  - Ohne `mindestalter_bestaetigt_am` → 403 `mindestalter_fehlt` und `ddd_konto=0`, außer `ohneMindestalter` (u. a. `GET /api/konto/ich`). Heute auch bei Bearer; dieser Plan hängt das Cookie nur noch bei `quelle === "cookie"` an (6).
  - **`unter16_gesperrt_am` prüft der Wrapper nicht.** Nach einer Sperre ist `mindestalter_bestaetigt_am` leer (`konten_stammdaten_2026-11-17.sql` Zeile 210–214). Der Normalfall der neuen GET-Routen ist deshalb 403 `mindestalter_fehlt`, **bevor** der Handler läuft. Eine eigene 403 `unter16_gesperrt` ist nur erreichbar, wenn die Route `ohneMindestalter` nutzt oder eine inkonsistente Zeile (Sperre *und* gesetztes Mindestalter) vorliegt. Neue Routen nutzen **kein** `ohneMindestalter`; die Extra-Prüfung im Handler ist Verteidigung, nicht der Hauptpfad (6).
  - Jede Antwort `Cache-Control: private, no-store`. Bremslimit über `opt.limit`, Schlüssel ist die Nutzer-ID, sobald eine Sitzung da ist.
  - Bearer-Token liest `sitzungAusAnfrage` schon (`quelle: "bearer"`, `setCookies: []`). GET-Routen prüfen den Origin nicht (`originErlaubt` nur bei `aendernd` oder `json`).
  - **Aber:** Der Wrapper selbst hängt nach jedem erfolgreichen Handler `hinweisCookie(hinweisFuer(profil))` an (Zeile 191) und bei 403 `mindestalter_fehlt` `hinweisCookie("0")` (Zeile 183), **auch bei Bearer**. Eine Bearer-Antwort enthält heute also `Set-Cookie: ddd_konto=…`. Für die App ist das unnötig und in einer WebView-Hülle (Capacitor) sogar störend, weil es den Web-Zustand umschaltet. Dieser Plan ändert **genau diese zwei Stellen** (6). Andere `Set-Cookie` bleiben: `sitzungStarten` (Anmelden, Link, Passwort), `cookiesLoeschen` (Abmelden, Löschen, kaputtes Sitzungs-Cookie) und das ausdrückliche `hinweisCookie("0")` in `stammdaten` und `abschluss` bei unter 16. Die legt der Handler selbst auf `ctx.setCookies`, der Wrapper kopiert sie unabhängig von `quelle`.
- **Links, die es wirklich gibt:** `/konto`, `/konto/willkommen`, `/konto/willkommen?modus=interessen`, `/konto/anmelden?weiter=…`, `/konto/anmelden?neu=1`, `/datenschutz#konto`. Hash-Anker auf `/konto` gibt es im Code nicht.
- **Kontenplan Abschnitt 13** nennt `GET /api/konto/fuer-euch` und `lib/fuer-euch.ts`. Dieser Plan ersetzt beides durch `fuer-dich` (S7). Es wird nur der neue Name gebaut.

## 2. Entscheidungen

**Aus dem Konzept (Auftraggeber, 18.11.2026):** P1 (B1, B2, B4, B7 wichtig; B18 neu), P2 (Unterseiten, Inhalte getrennt vom Organisatorischen), P3 (Startseite wie gehabt plus 2–3 Module).

**Für diese Stufe, vorgeschlagen von Claude, vom Auftraggeber am 18.11.2026 bestätigt (alle wie vorgeschlagen):**

| Nr. | Frage | Vorschlag |
|---|---|---|
| S1 | Wo sitzen die Module auf der Startseite? | Direkt **nach „Tipp und Picks“**, vor der Weihnachtsmarkt-Box und „Diese Woche beliebt“. Sichtbar, ohne den Kopf der Seite zu verändern |
| S2 | Bilder der Vorschau für Abgemeldete | **Echte Events** aus „Diese Woche beliebt“ (öffentlich, für alle gleich), verschwommen und nicht anklickbar |
| S3 | Begrüßung mit Vornamen („Hallo Yannick“) | Der Vorname ist laut Datenschutzerklärung nur „für Ticketkäufe“ erhoben. Für die Anrede braucht es den Zusatz „und für die persönliche Anrede auf der Website und in der App“ in Erklärung und Hinweis (Abschnitt 8). **Vorschlag:** Zusatz aufnehmen, kurz vom Anwalt bestätigen lassen; bis dahin ohne Namen („Für dich empfohlen“) |
| S4 | Sensible Events in den **Vorschlägen** | **Nie vorschlagen** (nicht nur nie als Eingabe). Sonst entstünde aus Interessen eine Empfehlung zu Religion, Gesundheit oder Sexualität, die wie eine Einordnung der Person wirkt. Öffentlich bleiben sie überall sichtbar |
| S5 | Mobile Leiste unten (TabBar) eingeloggt | **Start · Entdecken · Für dich · Merkliste · Profil.** „Heute“ und „Wochenende“ bleiben über die Chips auf der Startseite und im Menü erreichbar. Abgemeldet bleibt die Leiste wie heute |
| S6 | Vergangene gemerkte Events | Angemeldet eigene Seite **„Erlebt“**, auf der Merkliste ein Link „Erlebt (n)“ statt des eingeklappten Blocks. Abgemeldet bleibt „Vorbei“ wie heute |
| S7 | URL-Schema | `/konto` (Übersicht), `/konto/fuer-dich`, `/merkliste` (bleibt, ist öffentlich bekannt), `/konto/erlebt`, `/konto/interessen`, `/konto/einstellungen` (Konto und Sicherheit), `/konto/datenschutz` |

## 3. Seiten und Navigation

### 3.0 Zustände (für jede neue Fläche)
Das frühe Skript steht im `<head>`, direkt beim `THEME_SCRIPT`, und nur wenn `kontenAktiv()` beim Rendern wahr ist. Es liest das Cookie und setzt `document.documentElement.dataset.konto` auf `0` oder `1`. Fehlt das Cookie, setzt es nichts. Es liest nicht `body`, denn der ist im Head noch nicht da. Bei ausgeschaltetem Schalter fehlt das Skript, auch wenn ein Cookie liegenbleibt. `<html>` hat schon `suppressHydrationWarning`. Der Server schreibt `data-konto` nicht ins HTML.

| Cookie | Attribut | Oberfläche |
|---|---|---|
| fehlt | keines | Abgemeldet: Vorschau B18, heutige TabBar, Merkliste auf dem Gerät |
| `0` | `data-konto="0"` | Angemeldet, aber blockiert (Alter fehlt oder unter 16). Keine Vorschau mit „Registrieren“, keine Insel, heutige TabBar. Der bestehende Hinweis führt auf `/konto` |
| `1` | `data-konto="1"` | Persönliche Module, neue TabBar, Seitenleiste |

**Abgleich im Client (Pflicht).** Das Head-Skript gilt nur für den ersten Paint. Danach hält genau eine Funktion `kontoAttributAbgleichen()` (in `merk-store.ts`, neben `kontomodus()`) Attribut und Cookie gleich. Sie liest `document.cookie`, setzt oder entfernt `document.documentElement.dataset.konto` und löst das Ereignis `ddd-konto-geaendert` aus, **nur wenn sich der Wert ändert**. `hinweisSetzen` schreibt selbst nie `1`, nur `0` oder Löschen. Der Wechsel auf `1` kommt immer von einem `Set-Cookie` der Antwort.

Aufgerufen wird sie:
1. in `hinweisSetzen` (also bei jedem `lokalAbmelden`, auch `lokalAbmelden(true)`),
2. im Fetch-Helfer `konto()` (`components/konto.tsx`) nach **jeder** Antwort, denn dann hat der Browser ein `Set-Cookie` schon angewandt. Darüber laufen Anmelden, Bestätigen, Alters-Häkchen, Abschluss und die Seiten in `konto-zugang.tsx` und `konto-bereich.tsx`,
3. am Ende von `abruf()` in `merk-store.ts`. Dieser Fetch geht **nicht** durch `konto()`. 401 und 403 `mindestalter_fehlt` rufen oft danach `lokalAbmelden` auf, aber nicht jeder Aufrufer: `nurGeraetHochladen` und der `ich`-Abruf in `uebernahmePruefen` kehren bei einem Fehler einfach zurück. Eine 401 mit `cookiesLoeschen` hätte `ddd_konto` dann gelöscht, das Attribut bliebe bis zum nächsten Fokus,
4. nach dem eigenen `fetch` in `eventsLaden` (`components/merkliste.tsx`, `GET /api/konto/merkliste?mit=events`). Der geht weder durch `konto()` noch durch `abruf()`. Bei 403 setzt der Server `ddd_konto=0`, die Funktion wirft nur,
5. in `KontoSync` beim Start, bei `focus` und bei `visibilitychange`. **Auch wenn `kontomodus()` falsch ist.** Der bisherige Listener bricht mit `if (!kontomodus()) return` ab, bevor er etwas liest. Der Abgleich steht **vor** dieser Zeile, sonst sieht ein Tab das Anmelden im anderen Tab nie.

Die Pfadänderung hängt nicht direkt in `KontoSync`. `usePathname` ohne Suspense blockiert das Vorrendern, deshalb liegt die Leiste schon in einer Grenze (`client.tsx`, Kommentar an `TabBar`). Ein Kind von `KontoSync`, das nur `null` rendert, steht in `<Suspense>` und ruft dort `kontoAttributAbgleichen()` bei Pfadwechsel auf. `konto-zugang.tsx` braucht keinen eigenen Aufruf.

Alle Bausteine, die vom Zustand abhängen (Insel, `hidden` an der TabBar, „Erlebt“-Link, Seitenleiste, das heutige `useKontomodus`), lesen ihn über `useSyncExternalStore` mit `ddd-konto-geaendert`. `useKontomodus` hört heute nur `ddd-merkliste-geaendert` und `focus`. Die Server-Momentaufnahme ist immer abgemeldet (kein Attribut, `false`). Sie liest kein Cookie und kein `document`. Sonst käme der Kontostand ins HTML oder die Hydration liefe auseinander. Ergebnis: Nach dem Anmelden erscheinen die Module ohne Neuladen, nach dem Abmelden die Vorschau. Die Weiterleitung auf `/konto/abgemeldet` zeigt die abgemeldete TabBar.

Weitere Fälle, alle ohne Personeninhalt im gecachten HTML:

- **`KONTEN_AKTIV` aus:** keine Vorschau, keine Insel, keine neuen Links, keine neuen Routen (404). Das Skript läuft nicht.
- **Reset-Sitzung (`nur_passwort`), Cookie fehlt (Normalfall):** sieht aus wie abgemeldet, **B18 inklusive**. Das ist derselbe Kompromiss wie die Merkliste während des Reset. Die Insel ruft die neuen Routen **nicht** auf (kein `data-konto="1"`). Ein versehentlicher Abruf antwortet 403 `passwort_setzen_noetig`.
- **Reset-Sitzung, Cookie `1` noch da** (altes Cookie, neue Reset-Sitzung): die Insel ruft `GET start` auf und bekommt 403 `passwort_setzen_noetig`. Cookie und Sitzung bleiben. Die Insel zeigt denselben Satz wie die Konto-Hülle plus Link `/konto/passwort-neu`. Kein `lokalAbmelden()`, keine B18, kein erneuter Abruf in einer Schleife. `data-konto` bleibt `1`.
- **Abgelaufene oder fehlende Sitzung bei Cookie `1`:** 401 `abgemeldet`. Bei unleserlichem, kaputtem, abgelehntem Refresh oder ungültigem Sitzungs-Cookie löscht die Antwort beide Cookies. **Fehlt das Sitzungs-Cookie ganz, fehlt das Profil, oder gibt es beim Erneuern keinen Auth-Client, kommt kein Lösch-Cookie** (1). In allen diesen Fällen ruft der Client `lokalAbmelden()` auf (wie `spiegelLaden` heute). Das löscht `ddd_konto` und nimmt über `kontoAttributAbgleichen()` das Attribut weg. Dann erscheint die Vorschau, nicht ein leerer Platzhalter.
- **429 (Bremslimit), 503, 500 oder keine Verbindung** auf `GET start`: kein `lokalAbmelden()`, keine Vorschau B18, kein erneuter Abruf **desselben** Fehlschlags in einer Schleife. Der Platzhalter klappt still zu (Modul fehlt). Ein Wechsel des Datums (`useSearchParams`, 4.1) lädt neu. Auf `/konto/fuer-dich` und `/konto` die übliche Fehlermeldung (`Meldung art="fehler"`).
- **403 `mindestalter_fehlt`:** bei einer Cookie-Sitzung setzt der Wrapper `ddd_konto=0`. Der Client ruft `lokalAbmelden(true)` auf und setzt `data-konto="0"`. Keine Module, keine Vorschau mit „Registrieren“. Bei Bearer setzt der Wrapper das Cookie nicht; die App wertet den Code aus.
- **Unfertiges Profil** (`onboarding_fertig_am` leer, Alter bestätigt, Cookie `1`): der heutige Hinweis „Dein Profil ist noch nicht fertig“ bleibt auf der Übersicht. Vorschläge laufen, sobald `personalisierung = true` ist. Ein leeres Onboarding sperrt „Für dich“ nicht. Die neue TabBar gilt (Cookie `1`), inkl. `/konto/willkommen` als Profil-Tab (3.9).
- **Gesperrt unter 16:** Die Sperre leert `mindestalter_bestaetigt_am`. Der Wrapper antwortet auf `start` / `fuer-dich` / `uebersicht` mit 403 `mindestalter_fehlt` und, nur bei Cookie-Sitzung, `ddd_konto=0`. `/konto` lädt `GET /api/konto/ich` (`ohneMindestalter`) und zeigt `Gesperrt` (Abmelden, Löschen). Jede neue Unterseite tut dasselbe, sobald `ich.gesperrt` ist. Zusätzlich prüfen die drei neuen Handler `unter16_gesperrt_am` (Verteidigung, falls Mindestalter noch stünde): 403 `unter16_gesperrt`, `ctx.ohneHinweis = true`, und nur bei `quelle === "cookie"` zusätzlich `ddd_konto=0`. Ohne `ohneHinweis` würde Zeile 191 in `route.ts` das Cookie sonst wieder auf `1` setzen.
- **Einwilligung (a) fehlt:** Cookie kann `1` sein. „Deine nächsten Events“ bleibt (Vertrag, Merkliste). „Für dich“ rechnet nicht und zeigt den Hinweis auf `/konto/interessen`.
- **Veraltetes Cookie `0` ohne Sitzung:** die Insel ruft `GET start` nicht auf. B18 bleibt aus. Räumen tun andere Konto-Abrufe (401 → `lokalAbmelden()`). Kein Extra-Abruf nur dafür.

### 3.1 Übersicht `/konto`
- **Kopf:** „Mein dies.das“, darunter die Mailadresse klein.
- **Hinweis bei unfertigem Profil**, wie heute: „Dein Profil ist noch nicht fertig. Jetzt abschließen“.
- **Gruppe „Für mich“**, Kacheln mit Zahl:
  - **Für dich**: Anzahl der persönlichen Vorschläge für das Fenster „heute und die nächsten 6 Tage“ (dieselbe Liste wie das Startmodul auf öffentlichem „Heute“, nach Deckeln und Kappung auf 8, ohne `ohne`, 4.2 und 6). Der Ersatz „Beliebt“ zählt nicht mit, 0 bleibt 0. Das ist **nicht** die Summe der Abschnitte auf `/konto/fuer-dich` (die nutzen andere Fenster: heute/morgen, Wochenende, 14 Tage). Fehlt die Einwilligung (a), steht auf der Kachel „Interessen angeben“, nicht „0“. Ist die Zahl gerade nicht berechenbar (`vorschlaege_unbekannt`), steht nur „Ansehen“.
  - **Merkliste** (kommende)
  - **Erlebt** (vergangene)
  - **Interessen** (Summe der Einträge in `kategorien`, `unterkategorien`, `stadtteile`, `merkmale`, `orte`; „Noch keine“ bei 0)
- **Gruppe „Konto“**, Liste mit Pfeil:
  - **Konto und Sicherheit** (Name und Geburtsdatum, Mailadresse, Passwort, Abmelden, Löschen)
  - **Datenschutz** (Einwilligungen, Auskunft)
- Mobil wirkt das wie die Einstellungen einer App. Am Desktop ist die Übersicht zugleich der Einstieg in die Seitenleiste.
- **Hülle:** `KontoRahmen` und `KONTO_ROBOTS` wie `web/app/konto/page.tsx`. `X-Robots-Tag` gilt für neue Pfade schon über `source: "/konto/:pfad*"` in `web/next.config.ts`. Schalter aus: der Rahmen zeigt „Noch nicht verfügbar“, die API 404.
- **Reset-Sitzung auf jeder neuen Unterseite:** `GET /api/konto/ich` antwortet 403 `passwort_setzen_noetig`, dann `router.push("/konto/passwort-neu")`, wie `useIch` in `konto-bereich.tsx` heute. Dieselbe Hülle zeigt bei `ich.gesperrt` nur `Gesperrt` (3.0).

### 3.2 Gemeinsame Navigation (`components/konto-nav.tsx`, neu)
- **Desktop:** Seitenleiste links auf allen `/konto/*`-Seiten und auf `/merkliste`, nur bei `data-konto="1"`. Cookie `0` und Abgemeldete sehen die Merkliste wie heute, ohne Seitenleiste.
- **Mobil:** oben ein Zurück-Pfeil zu `/konto` mit dem Seitentitel, keine Seitenleiste. Der Pfeil ist ein Link, mindestens 44 px, mit `aria-label` „Zurück zur Übersicht“. Auf der Übersicht `/konto` selbst kein Zurück-Pfeil.
- Die Hülle ist statisch und hängt nur an `kontenAktiv()`. Welche Gruppe offen ist, entscheidet das Attribut im Browser. Der Server schreibt keinen Kontostand ins HTML.

### 3.3 `/konto/fuer-dich` (B1)
- **Abschnitte**, jeweils nur, wenn es Treffer gibt. Die Rechnung ist die aus Abschnitt 5 (Mindestens 2 Punkte, Sensibel-Menge, nicht gemerkt). Der Ersatz „Beliebt in Düsseldorf“ gibt es **nur** im Startmodul (4.2), nicht auf dieser Seite.
  1. **„Heute und morgen für dich“**: bis zu 6. Fenster unten.
  2. **„Dein Wochenende“**: bis zu 6. Liegt heute auf Fr, Sa oder So, ist es dieses Wochenende, sonst das nächste Fr–So. Die drei Tage kommen aus `wochenende()` in `datum.ts` (`fr`, `sa`, `so`), **nicht** aus `zeitraumAuflösen("wochenende")`: der schneidet an Sa/So den Freitag ab (`von = heute`). Ein Freitag, der schon vorbei ist, fällt über `istVorbei` heraus. Ein noch laufendes Mehrtägiges mit Fokustag am Freitag bleibt drin.
  3. **„Weil du ‚…‘ gemerkt hast“**: bis zu 6. Nur Kandidaten, die mindestens 2 Punkte haben **und** Reihe oder Ort eines gemerkten, nicht sensiblen Events treffen. Der +1 dafür zählt mit, allein reicht er nicht. Der Titel nennt genau ein Bezugs-Event: das mit den meisten solchen Treffern, die nicht schon in Abschnitt 1 oder 2 stehen. Bei Gleichstand das zuletzt gemerkte (`gemerkt_am` aus der Merkliste-Zeile, nicht vom Event; `eventsFuerIds` liefert das Feld nicht). Bei gleichem `gemerkt_am` die größere `event_id`. In den Abschnitt kommen nur die Treffer **dieses** Bezugs. Treffer anderer gemerkter Events rutschen in Abschnitt 4, wenn sie dort ins Fenster fallen.
  4. **„Mehr aus deinen Interessen“**: die nächsten 14 Tage, bis zu 12.
- **Fenster je Abschnitt** (`im-fenster`, Abschnitt 5):
  - Abschnitt 1: `[heute, morgen]`
  - Abschnitt 2: `[Fr, So]` wie oben
  - Abschnitte 3 und 4: `[heute, heute+13]`
- **Jedes Event steht auf der Seite nur einmal**, im ersten passenden Abschnitt in der Reihenfolge 1 → 4. Beispiel: Ist heute Samstag, stehen Treffer von heute nur unter „Heute und morgen“, nicht noch einmal unter „Dein Wochenende“. Die Deckel aus Abschnitt 5 gelten **beim Füllen jedes Abschnitts bis zu dessen Obergrenze** (6 bzw. 12), nicht nur unter den ersten 8. Was der Deckel auslässt, wird nicht nachgeschoben.
- **Leere Seite bei Einwilligung:** kein Abschnitt hat Treffer. Kein Ersatz „Beliebt“. Ein Satz „Im Moment haben wir keine Vorschläge für dich.“ und der Button „Interessen ansehen“ → `/konto/interessen`. Kein Grund, keine Zahl, kein Hinweis auf die Merkliste. So verrät die leere Seite nicht, dass nur sensible Merkungen da waren (8).
- **Ohne Einwilligung (a)** (`personalisierung = false`): keine Punkte, kein Ersatz „Beliebt“. Nur der Hinweis „Für Vorschläge brauchen wir deine Interessen“ mit Button „Interessen angeben“ → `/konto/interessen`. Die Merkliste wird dafür nicht gelesen.
- **Begründung je Karte** (klein, eine Zeile), z. B. „Musik · Flingern“ oder „wie ‚Jazz im Hofgarten‘“. Der zitierte Titel stammt nur von einem gemerkten Event, das nicht in `event_sensibel` steht. Fehlt so ein Bezugs-Event, entfällt der Abschnitt „Weil du … gemerkt hast“ ohne Ersatzsatz. Ein leerer Abschnitt würde verraten, dass die gemerkten Events ausgenommen wurden.

### 3.4 Merkliste `/merkliste`, angemeldet
- Kommende Events wie heute.
- Nur bei `data-konto="1"`: statt „Vorbei (n)“ ein Link **„Erlebt (n) →“** auf `/konto/erlebt` (S6). Abgemeldet **und bei Cookie `0`** bleibt „Vorbei (n)“ wie heute (Geräteliste nach 403, siehe 1).
- Seitenleiste nur bei `data-konto="1"` (3.2).

### 3.5 `/konto/erlebt`
- Vergangene gemerkte Events aus `GET /api/konto/merkliste?mit=events`, geteilt mit `merklisteAufteilen`, nach Monat gruppiert, neueste zuerst. Es gibt keinen neuen Query-Parameter.
- Herz zum Entfernen bleibt (`DELETE` wie heute). Eigene sensible Merkungen stehen in der Liste, ohne Kennzeichnung.
- Kein Feedback in Stufe 1 (B3 kommt später).

### 3.6 `/konto/interessen`
- **Lesbare Übersicht** statt „9 Angaben gespeichert“: Kategorien, Unterkategorien, Stadtteile, Merkmale und Orte als Chips.
- **Button „Interessen ändern“** → bestehender Fragebogen `/konto/willkommen?modus=interessen`.
- Der Schalter (a) liegt auch hier, mit gestuftem Text und Rückfrage beim Abschalten (wie heute im Konto).

### 3.7 `/konto/einstellungen` („Konto und Sicherheit“)
- Die heutigen Abschnitte ziehen hierher um, unverändert: Dein Konto mit Mailadresse und „Mailadresse ändern“, Über dich, Passwort, Abmelden, Konto löschen.

### 3.8 `/konto/datenschutz`
- Einwilligungen (b), (c) und (d) mit gestuften Texten, so wie heute. Die Interessen (a) liegen zusätzlich unter `/konto/interessen` (derselbe Schalter, dieselben Routen; Umschalten auf einer Seite gilt sofort auf der anderen).
- Download „Eine vollständige Auskunft nach Art. 15 DSGVO herunterladen.“
- Links zur Datenschutzerklärung (`#konto`) und zu den Nutzungsbedingungen.

### 3.9 TabBar und Kopf (S5)
- **TabBar:** Beide Fassungen stehen im HTML. CSS schaltet über `html[data-konto]`, gesetzt vom frühen Skript (3.0), nach dem Muster von `THEME_SCRIPT`. So flackert nichts und das gecachte HTML bleibt für alle gleich.
  - `html[data-konto="1"]`: Start · Entdecken · Für dich (`/konto/fuer-dich`) · Merkliste · Profil (`/konto`).
  - Ohne Attribut und bei `data-konto="0"`: die heutige Leiste.
  - Die **inaktive** Leiste blendet CSS über `html[data-konto]` mit `display: none` aus (nicht Opacity, nicht `visibility`). Ein Element mit `display: none` ist weder fokussierbar noch für Screenreader vorhanden. Das reicht schon vor der Hydration für „nur eine Leiste bedienbar“.
  - Zusätzlich setzt die TabBar-Komponente nach der Hydration `hidden` an der inaktiven `nav` (über den Zustand aus 3.0), als zweite Sicherung, falls CSS fehlt.
  - Das Head-Skript fasst die `nav` **nicht** an: Sie steht beim Ausführen im `<head>` noch nicht im DOM. Korrektur der dritten Fassung, die das dem Skript zugetraut hatte.
- **Aktiv-Zustand**, nicht `startsWith("/konto")`:
  - „Für dich“ nur bei Pfad **exakt** `/konto/fuer-dich`.
  - „Profil“ bei `/konto`, `/konto/einstellungen`, `/konto/datenschutz`, `/konto/interessen`, `/konto/erlebt` und `/konto/willkommen` (inkl. `?modus=interessen`). Nicht bei `/konto/fuer-dich`.
  - Welche Leiste sichtbar ist, folgt überall allein dem Zustand (3.0), auch auf `/konto/anmelden`, `/konto/passwort-neu`, `/konto/passwort-vergessen`, `/konto/bestaetigen` und `/konto/abgemeldet`. Auf diesen Seiten ist in der neuen Leiste **kein** Tab aktiv. Sie sind kein Profil-Tab. Nach dem Abmelden ist das Attribut schon weg (3.0), `/konto/abgemeldet` zeigt also die heutige Leiste.
  - „Merkliste“ nur bei `/merkliste` (nicht `/merkliste/…`, gibt es nicht).
  - „Start“ nur bei `/` (wie heute, nicht `startsWith`).
- **Kopf:** unverändert („Mein Konto“-Icon → `/konto`).
- **Bestehende Ziele bleiben:** `/konto/willkommen` und `/konto/willkommen?modus=interessen` ziehen nicht um. Mails und der Hinweis „Profil ist noch nicht fertig“ zeigen weiter auf `/konto`. `/datenschutz#konto` bleibt. Es gibt keine Hash-Ziele auf `/konto` umzubiegen.

## 4. Startseite (B2, B18)

### 4.1 Einbau
- **Eine Client-Insel `StartPersoenlich`** an der Stelle aus S1. Die Startseite ruft kein `cookies()`, kein `headers()` und kein `connection()` auf. Die Insel importiert sie ebenfalls nicht (auch nicht in einer Server-Hülle um die Insel). `/` bleibt die heutige `searchParams`-Seite (`instant = false`).
- **Flackerfrei über `html[data-konto]`** (Skript aus 3.0, im Head, vor dem ersten Paint):
  - **Kein Attribut:** Die Vorschau B18 steht im HTML und ist sofort sichtbar. Sie wird nur gerendert, wenn `kontenAktiv()` wahr ist.
  - **`data-konto="1"`:** CSS blendet die Vorschau mit **`display: none`** aus (nicht Opacity – sonst bleibt sie fokussierbar) und hält einen Platzhalter in der Höhe des ersten Moduls frei. Die Insel lädt die Daten **nur in diesem Zustand**. Das zweite Modul darf die Seite danach länger machen. Beide Höhen zu reservieren ließe bei leerer Merkliste eine große Lücke.
  - **`data-konto="0"`:** CSS blendet Vorschau und Platzhalter mit `display: none` aus. **Kein Abruf** von `/api/konto/start`.
- Ist der Schalter aus, gibt es weder Vorschau noch Insel noch Skript.
- Die Insel liest `datum` aus der öffentlichen URL, nicht als serverseitiges Prop. Sie steht in einer **eigenen** `<Suspense>`-Grenze (die der `WmStartBox` bleibt ihre). Den Query liest sie mit `useSearchParams()` und lädt neu, wenn er sich ändert (Datumsleiste, Chips, `scroll={false}`). Ein einmaliges Lesen von `window.location` beim Mount verpasst diesen Wechsel. Ohne die Suspense-Grenze blockiert `useSearchParams` das Vorrendern der Startseite, so wie `usePathname` an der TabBar.
- `ohne` sind die IDs der **sichtbaren** Tipp-und-Picks-Karten, eindeutig. `TippDesTages` ist keine `KompaktKarte`; das Attribut `data-event-id` liegt auf dem `<article>` des Tipps und auf beiden Pick-Listen. Mobil und Desktop stehen beide im HTML (`nur-mobil` / `nur-desktop`), dieselben IDs also doppelt. Die Insel sammelt eine Menge, höchstens 5 verschiedene. Der Deckel 24 der Route greift trotzdem. Zeigt die Seite den Leer-Hinweis, gibt es keine Karten und `ohne` bleibt leer. **Nicht** mitgeschickt werden IDs aus der Geräteliste oder aus `ddd-merkliste-geraet`. Das wären Merkungen, die der Server wegen fehlender Einwilligung (b) nicht kennen darf (8).
- **Ort im Seitenaufbau:** direkt nach dem Block „Tipp und Picks“. Zeigt die Startseite statt dieses Blocks den Leer-Hinweis („Heute ist es ruhig.“), sitzen Vorschau und Insel direkt danach. In beiden Fällen dieselbe Stelle vor `WmStartBox`.
- Die Insel hängt am Zustand aus 3.0 (`useSyncExternalStore`, Server-Momentaufnahme immer abgemeldet), nicht nur am ersten Mount. Wechselt er ohne Neuladen von `1` auf „fehlt“ (Abmelden in einem anderen Tab), verschwindet das Modul und die Vorschau erscheint. Wechselt er auf `1` (Anmelden), lädt die Insel.
- `WmStartBox` ruft `connection()` in ihrer eigenen Suspense-Grenze auf. Die Insel importiert `connection`, `cookies` und `headers` nicht.
- Anonyme Besucher und Cookie `0` rufen `/api/konto/start` nicht auf. Die Punktrechnung läuft nur in der API.

### 4.2 Module angemeldet
1. **„Für dich empfohlen“:** bis zu 8 Karten (`EventKarte`, Reihe wie „Beliebt“), weniger sind erlaubt und werden nicht aufgefüllt. Link „Alle Vorschläge“ → `/konto/fuer-dich`.
   - **Zeitraum**, aus der öffentlichen URL. Öffentliches `fokusTag` in `page.tsx` bleibt `von === bis`. Das persönliche Fenster weicht nur bei „Heute“ ab:
     | Öffentliche Ansicht | Persönliches Fenster | Fokustag-Filter |
     |---|---|---|
     | „Heute“ (`von === bis === heute`) | heute bis heute+6 | `im-fenster`: mehrtägig nur, wenn `amFokustag` auf einen der sieben Tage fällt |
     | anderer einzelner Tag (`von === bis !== heute`) | nur dieser Tag | `tag`: nur `amFokustag` dieses Tages |
     | Zeitraum (`woche`, `wochenende`, eigener Bereich, `von !== bis`) | Von–Bis | `kein`: Fokustag filtert nicht |
   - **Vergangener Tag** (`/?datum=` mit einem einzelnen Tag vor heute; `istGueltigerTag` nimmt ihn an, der Pool beginnt trotzdem bei heute) oder **Fenster ohne Kandidaten:** keine Vorschläge und kein Ersatz. Das Modul „Für dich empfohlen“ klappt still zu. „Deine nächsten Events“ bleibt, wenn es Kommendes gibt. „Ohne Kandidaten“ heißt: nach Fenster, Fokustag, Absage, Stamm, Sensibel-Menge, Merkliste und `ohne` ist die Menge leer. Ein Bereich `von_bis`, dessen Ende vor heute liegt, ist für `zeitraumAuflösen` ungültig und wird zu „heute“, nicht zu diesem Sonderfall.
   - **Ohne Einwilligung (a):** die schmale Zeile „Gib deine Interessen an und bekomme hier passende Vorschläge“ mit Button → `/konto/interessen`. Keine Punkte, kein Ersatz „Beliebt“, die Merkliste wird dafür nicht gelesen.
   - **Mit Einwilligung, aber ohne Treffer** (Kandidaten da, keiner mit mindestens 2 Punkten; das ist nicht „ohne Kandidaten“): Überschrift wird „Beliebt in Düsseldorf“. Der Link „Alle Vorschläge“ entfällt. Quelle ist **nicht** die öffentliche Box und **nicht** der Live-Aufruf `beliebtAuswahl(imZeitraum, woche, …, fokusTag, 5, …)` auf „Heute“. Quelle ist dieselbe Kandidatenmenge wie die persönlichen Vorschläge (Tabelle oben), ohne `event_sensibel`, ohne eigene Konto-Merkliste, ohne `ohne` (Tipp/Picks), sortiert mit `nachEmpfehlung(stufen)` (Abschnitt 5), die ersten bis zu 8. Die öffentliche Box „Diese Woche beliebt“ bleibt unverändert (S2 gilt nur für B18). Auf `/konto/fuer-dich` gibt es diesen Ersatz nicht (3.3).
2. **„Deine nächsten Events“:** die nächsten bis zu 4 gemerkten Events (`KompaktKarte`), weniger wenn weniger da sind. Link „Zur Merkliste“.
   - **Datenquelle:** das Feld `naechste` aus `GET start` (ein Abruf für die Insel, kein zweiter auf `/api/konto/merkliste`). Serverseitig nutzt die Route dieselben Bausteine wie die Merkliste-Route: `ctx.db.from("merkliste")` für die IDs, `eventsFuerIds` für die Events, `merklisteAufteilen` für „kommend“.
   - **Beschriftung:** die der Karte, `metaZeile` in `datum.ts` (so macht es `KompaktKarte` schon): „Heute“, „Morgen“, sonst `tagKurz` („Fr 30.10.“). Ein mehrtägiges Event, das schon läuft (`datum` < heute und `datum_bis` ≥ heute), heißt „läuft bis TT.MM.“. Es gibt keine eigene Formel „in 3 Tagen“. Abgesagte gemerkte Events tragen das Schild „Abgesagt“ über `Bild` (`karten.tsx`), nicht über einen neuen Text.
   - Ohne kommende Merkungen entfällt das Modul. Es bleibt auch ohne Einwilligung (a).
   - Eigene sensible Merkungen **im Konto** stehen darin, ohne Kennzeichnung und ohne als Begründung für „Für dich“ zu dienen. Merkungen, die nur auf dem Gerät liegen („Nur auf diesem Gerät“, sensibel ohne Einwilligung (b)), kennt der Server nicht. Sie fehlen im Modul und in den Zählungen der Übersicht. Die Merkliste-Seite zeigt sie weiter. Sie können in „Für dich“ noch einmal auftauchen, weil der Client ihre IDs nicht als `ohne` schickt (4.1, 8). Das ist hingenommen.
3. **Begrüßung:** Nur wenn die Konstante `NAMEN_ANREDE` an ist (erst nach der Anwaltsbestätigung, Abschnitt 8): „Hallo“ plus `profiles.vorname` als Unterzeile im Kopf des ersten Moduls, ohne zusätzlichen Platz. `GET /api/konto/ich` liefert den Vornamen schon heute und **bleibt unverändert**. Die neue Route `GET start` sendet `vorname` nur, wenn `NAMEN_ANREDE` an ist; sonst fehlt das Feld. `anzeigename` wird nicht benutzt.
- Doppelte vermeiden: die Insel schickt die IDs der sichtbaren Tipp-und-Picks-Karten als `ohne` (Abschnitt 6). Die Route schließt die **Konto-**Merkliste zusätzlich aus. Geräte-IDs schickt die Insel nicht mit (4.1).

### 4.3 Vorschau für Abgemeldete (B18)
- **Gerendert in der statischen Seite**, nur bei `kontenAktiv()`:
  - Überschrift „Für dich empfohlen“, darunter bis zu 4 verschwommene Karten. Es sind die **ersten Karten der schon gerenderten Box „Diese Woche beliebt“** (S2), nicht eine zweite Auswahl und nicht das 7-Tage-Fenster aus 4.2. Sind es weniger als 4, bleiben es weniger.
  - `aria-hidden` und `inert` liegen nur auf den Karten, nie auf einem Elter, der den Button enthält. Die Karten sind nicht anklickbar und nicht fokussierbar. `data-nosnippet` auf den Karten. Kein Dialog, nicht wegklickbar.
- **Darüber ein Kasten:**
  - Schloss-Symbol
  - **Titel:** „Events, die zu dir passen“
  - **Text:** „Mit einem kostenlosen Konto zeigen wir dir hier Vorschläge nach deinen Interessen und deiner Merkliste.“
  - **Button:** „Kostenlos registrieren“ → `/konto/anmelden?neu=1&weiter=` plus die aktuelle Start-URL (`/` oder `/?datum=…`, von `window.location.pathname` + `search`; serverseitig im ersten HTML reicht `weiter=/`, die Insel oder ein kleines Skript darf `weiter` auf die aktuelle URL setzen, ohne Personenbezug).
  - **Link:** „Schon ein Konto? Anmelden“ → `/konto/anmelden?weiter=` plus dieselbe aktuelle Start-URL (**ohne** `neu=1`).
- Nicht wegklickbar, verdeckt nur dieses Modul. Auf dem Handy als Kasten unter der Überschrift, die Karten verschwommen dahinter.
- Bei `data-konto="1"` oder `"0"`: ganzer Vorschau-Block `display: none` (4.1), damit Button und Link nicht in der Tab-Reihenfolge bleiben.

## 5. Berechnung der Vorschläge (`web/lib/fuer-dich.ts`, rein und getestet)

**Eingaben:**
- Pool: `eventPoolLaden().events`, das gebündelte Feld (ein Terminbündel, eine Karte, `uhrzeiten` gefüllt). Nicht `pool.alle`, sonst zerfallen Bündel in mehrere Karten und `uhrzeitenVon` sieht nur eine Zeit.
- Profil (`praeferenzen`, `personalisierung`).
- Merkliste des Kontos (IDs und `gemerkt_am`) – nur wenn (a) gilt. `gemerkt_am` kommt aus der Zeile `merkliste`, nicht aus `eventsFuerIds`.
- Menge der sensiblen Event-IDs, von der Route übergeben. Die Route liest und cacht sie (unten). Die reine Funktion tut das nicht.
- Fenster: `{ von, bis, fokus: "kein" | "tag" | "im-fenster" }`, Ausschlussliste `ohne`.

Die Funktion rechnet nicht selbst in der Datenbank. Die Route übergibt Pool, Profil, Merkliste und die Sensibel-Menge. Fehlt die Einwilligung (a), gibt die Funktion keine Vorschläge zurück und liest die Merkliste nicht für Punkte. „Deine nächsten Events“ ist eine eigene, separate Auswahl ohne Punkte (`merklisteAufteilen`).

**Kandidaten** (gemeinsam für Punkte **und** den Ersatz „Beliebt in Düsseldorf“):
- Im Fenster (`von`–`bis`): `filtern(pool.events, { von, bis, mitLanglaeufern: true })`, also **mit** Langläufern wie bei `startPlaetze`. Die Fokustag-Regel (unten) begrenzt sie. `breite` deckelt Langläufer ohnehin auf Stufe 2.
- Nicht abgesagt, `breite ≥ 1` (kein Stamm), nicht vorbei (`istVorbei` / Ende vor `heute` aus dem Pool).
- Nicht gemerkt, nicht in der Sensibel-Menge (S4), nicht in `ohne`.
- Fokustag nach `fokus`, nicht nach einer globalen Regel:
  - `tag`: `amFokustag(e, von)` (`von === bis`).
  - `im-fenster`: mehrtägig nur, wenn `amFokustag` auf einen Kalendertag im geschlossenen Intervall `[von, bis]` fällt; eintägige Events wie bisher über die Laufzeit im Fenster.
  - `kein`: kein `amFokustag`-Filter.
- Ein Event, eine Karte.
- Der Tag „heute“ kommt aus `eventPoolLaden` (`Europe/Berlin`), nicht aus der Uhr des Browsers.

**Punkte** (Kontenplan 13, hier ersetzt):
- Unterkategorie trifft: +3. Gespeichert ist `"<kategorie>/<unter>"` (Fragebogen), verglichen wird mit `` `${e.kategorie}/${e.unterkategorie}` ``. `unterkategorie` leer oder `"keine"` trifft nie.
- Kategorie trifft: +2 (`e.kategorie` gegen `praeferenzen.kategorien`)
- Stadtteil trifft: +1. Gespeichert sind Slugs (`stadtteilSlug`), verglichen wird mit `stadtteilSlug(e.stadtteil)`. Ohne `stadtteil` kein Treffer und kein Aufruf von `stadtteilSlug` mit `null`. Nachbarstädte stehen in derselben Liste, es gibt keine zusätzliche Umkreis-Logik. „Hafen“ und „Medienhafen“ fallen über `stadtteilName` auf denselben Slug.
- Merkmal trifft: +1 je Merkmal
  - `kostenlos` → `istKostenlos`
  - `mit-kindern` → Kategorie-Slug `familie`; eine Unterkategorie „Kinder“ gibt es nicht
  - `abends` → eine der Anfangszeiten (`uhrzeitenVon(e)`, Vergleich `>= "17:00"` wie die Abend-Box der Startseite; Zeiten sind `HH:MM`) 
  - `tagsueber` → eine Anfangszeit vor 17 Uhr; ohne Uhrzeit keiner der beiden Treffer. Ein Bündel mit 11:00 und 19:00 trifft beide Merkmale, je +1
  - `wochenende` → bei `fokus === "tag"` der Fokustag, sonst ein Tag der Laufzeit im Fenster, auf Fr–So
- `praeferenzen.orte` (Restaurants & Cafés, Kneipen & Bars, Clubs, Spielplätze) zählt in Stufe 1 **nicht**. Das sind Guide-Arten für Orte, keine Event-Merkmale (später mit B12).
- Gleiche `reihe.slug` oder gleicher Ort wie ein gemerktes Event, das nicht in der Sensibel-Menge steht: **einmal** +1, nicht einmal für die Reihe und noch einmal für den Ort. Ort über `norm()` aus `termine.ts`. `istSammelort` („düsseldorf“, „stadtbüchereien düsseldorf“) zählt nicht als gleicher Ort, sonst hinge an einem gemerkten Event mit Ort „Düsseldorf“ fast die ganze Stadt. Die Serien-Erkennung in `stufenKontext` (gleicher Titel, gleicher Ort) fließt nur in `breite` ein, nicht in diesen Punkt und nicht in den Reihen-Deckel.
- „Von allem etwas“: `praeferenzen.kategorien` enthält jeden Slug aus dem exportierten Array `KATEGORIEN` (`sonstiges` liegt dort nicht). Dann entfällt +2 für die Kategorie. Unterkategorien, Stadtteile, Merkmale und die Merkliste zählen weiter.
- Mindestens 2 Punkte, sonst kein Vorschlag.

**Reihenfolge und Vielfalt:**
- Punkte absteigend. Bei Gleichstand `nachEmpfehlung(stufen)` aus `ableitungen.ts`, **ohne** `tag`, wie `beliebtAuswahl`. Bei `fokus === "tag"` hat der Kandidatenfilter jeden Mehrtägigen schon auf den Fokustag dieses Tages beschränkt, ein `tag` in der Sortierung würde nichts mehr ändern. Beim 7-Tage-Fenster wäre ein einzelner `tag` falsch. Kein zweiter, nachgebauter Sortierschlüssel.
- Deckel beim Füllen, nicht danach: höchstens 2 je Kategorie, höchstens 1 je `reihe.slug`, höchstens 2 je `norm(ort)`. Auf der Startseite bis zur Kappung 8, auf `/konto/fuer-dich` bis zur Obergrenze des Abschnitts (3.3: 6 bzw. 12). Ein Event ohne Reihe, ohne Ortsname oder mit `istSammelort` fällt unter keinen Ort- bzw. Reihen-Deckel. Was der Deckel auslässt, wird **nicht** nachgeschoben. (Das gilt für die **persönliche** Liste. Der Ersatz „Beliebt“ hat keine Kategorie-/Ort-Deckel, nur die Sortierung und die Kappung auf 8.)

**Wenig Daten:**
- Nur mit Einwilligung, **nicht leerer** Kandidatenmenge und leerer persönlicher Liste nach Mindestpunkten: Ersatz aus denselben Kandidaten (oben), Sortierung `nachEmpfehlung`, bis zu 8, Überschrift „Beliebt in Düsseldorf“. Das ist kein persönlicher Vorschlag und **nicht** die öffentliche Box. `beliebtAuswahl` mit den Argumenten der Startseite wird dafür nicht aufgerufen. Nur das Startmodul (4.2). `/konto/fuer-dich` zeigt stattdessen den leeren Satz aus 3.3.
- Ohne Einwilligung gibt es diesen Ersatz nicht. Eine leere Kandidatenmenge auch nicht (4.2, „ohne Kandidaten“).

**Begründung:**
- Die höchste Trefferart als kurzer Text, z. B. „Jazz“, „Flingern · kostenlos“, „wie ‚…‘“.
- Der Titel in „wie …“ stammt nur von einem gemerkten Event außerhalb der Sensibel-Menge. Gibt es keinen solchen Bezug, entfällt der Abschnitt ohne Ersatzsatz.

**Sensibel-Menge:**
- Die Route liest `event_sensibel` nur mit `kontoDienstClient()`, nie mit `ctx.db`.
- Cache im Prozess, etwa 10 Minuten, Schlüssel ist eine Konstante, nie eine Nutzer-ID. Ein Fehler wird **nicht** gecacht, der nächste Aufruf versucht es neu. Die Menge steht nie in der Antwort und nie im HTML.
- Schlägt das Lesen fehl, antworten `start` und `fuer-dich` mit 503 und rechnen nicht. Sie empfehlen nicht „auf gut Glück“ ohne die Ausschlussmenge. `uebersicht` antwortet in diesem Fall 200 mit `vorschlaege: null` (6), sonst fehlte auch die Merkliste-Zahl.
- Anonyme Besucher rufen die Route nicht auf. Die Rechnung läuft nur in der API, nicht beim Rendern von `/`.

## 6. API (unter `web/app/api/konto/`, `private, no-store`, Wrapper `kontoRoute`)

| Route | Antwort | Bremslimit |
|---|---|---|
| `GET start?datum=…&ohne=id,id` | `{ fuer_dich, naechste, personalisierung, ersatz }` für die Startseiten-Insel. Feld `vorname` nur bei `NAMEN_ANREDE` | 120/Std, Name `start` |
| `GET fuer-dich` | `{ abschnitte, personalisierung }` für `/konto/fuer-dich` | 60/Std, Name `fuer-dich` |
| `GET uebersicht` | Zahlen für `/konto` | 120/Std, Name `uebersicht` |

Alle drei: `kontoRoute({ anmeldung: true })`, ohne `resetErlaubt`, ohne `ohneMindestalter`. Bearer funktioniert damit schon (`sitzungAusAnfrage`). GET prüft den Origin nicht. Der Bremslimit-Schlüssel ist `nutzer:<id>`, sobald eine Sitzung da ist. Bearer ohne Cookie: 401 löscht keine Cookies (`sitzungAusAnfrage` gibt `setCookies: []`).

- **Änderung am Wrapper (`web/lib/konto/route.ts`):** Das automatische Hinweis-Cookie (`hinweisFuer` nach dem Handler, Zeile 191, und `hinweisCookie("0")` bei 403 `mindestalter_fehlt`, Zeile 183) wird nur noch angehängt, wenn `ctx.sitzung.quelle === "cookie"` ist. Das gilt für alle Konto-Routen, nicht nur die neuen. Im Web ändert sich nichts, weil der Browser immer mit Cookie kommt. `web/tests/konto.test.ts` schickt Bearer nur im Unit-Test von `originErlaubt`, in keiner Route. Die Tests, die `ddd_konto=0` oder `=1` erwarten, laufen mit Sitzungs-Cookie (`sitzung()`) und bleiben grün.
  - **Nicht** anfassen: `sitzungStarten` (Anmelden setzt Sitzung und Hinweis, sonst käme niemand ins Konto), `cookiesLoeschen` (Abmelden, Löschen, kaputtes Cookie) und das `hinweisCookie("0")`, das `stammdaten` und `abschluss` selbst auf `ctx.setCookies` legen. Die Zeile 190 kopiert `ctx.setCookies` für jede Quelle.
  - Die neue Verteidigung `unter16_gesperrt` legt `hinweisCookie("0")` ebenfalls nur bei `quelle === "cookie"` auf `ctx.setCookies` und setzt immer `ohneHinweis`. Sonst schriebe sie bei Bearer das Cookie, das Zeile 191 gerade weglässt, und bei Cookie würde Zeile 191 es wieder auf `1` setzen (`mindestalter_bestaetigt_am` steht in dieser inkonsistenten Zeile noch).
- **Aktivität:** `aktivitaetMerken` läuft im Wrapper **vor** dem Handler, für jede angemeldete Route mit Alters-Häkchen, höchstens einmal am Tag je Nutzer und Prozess. `GET start` braucht keinen zweiten Aufruf. Ein angemeldeter Besuch der Startseite zählt damit als Nutzung für die 24-Monats-Frist. Das passt zu `konto-abschnitt.tsx` („jede Anmeldung und jede Aktion im Konto“), weil die Insel ein Konto-Abruf ist. 403 `mindestalter_fehlt` kommt davor und zählt nicht.

- **Kein neuer Merkliste-Parameter.** `GET /api/konto/merkliste?mit=events` liefert kommende und vergangene Events schon. Erlebt und die Zählung teilen mit `merklisteAufteilen`.
- **`datum`:** dieselbe `zeitraumAuflösen`-Eingabe wie die Startseite. Ungültig heißt „heute“, kein 400. Daraus folgt das persönliche Fenster nach der Tabelle in 4.2 (öffentliches „Heute“ → sieben Tage `im-fenster`; anderes Einzeltag → `tag`; Zeitraum → `kein`).
- **`ohne`:** kommagetrennte IDs, höchstens 24, der Rest fällt weg. Ungültige IDs fallen weg. Kein 400. Die Antwort sagt nicht, welche IDs fehlten oder sensibel waren, und sie wiederholt die Liste nicht. Die Route schließt die eigene Konto-Merkliste zusätzlich aus, auch ohne `ohne`. IDs, die nur auf dem Gerät liegen, kommen nicht an (4.1).
- **`fuer_dich`:** Event-Objekte wie die Merkliste sie schon ausliefert, plus `begruendung` (string). Keine Punkte, kein Feld `sensibel`, keine Nutzer-ID. `ersatz: true`, wenn die Liste der Ersatz „Beliebt in Düsseldorf“ ist.
- **`naechste`:** die ersten bis zu 4 kommenden Merkungen (`merklisteAufteilen`, nach `datum`), auch ohne Einwilligung (a), inklusive eigener sensibler Merkungen im Konto, ohne Kennzeichnung. Gelesen über `ctx.db` (eigene Zeilen, RLS, `limit` 1000, `gemerkt_am` mitnehmen für Abschnitt 3) und `eventsFuerIds`, wie in der Merkliste-Route. Schlägt das Laden der Events fehl, ist `naechste` leer und `fuer_dich` wird trotzdem geliefert (wie die Merkliste-Route, die bei Fehlern `events: []` sendet).
- **`uebersicht`:** `vorschlaege` ist eine Zahl oder `null`, wenn (a) fehlt (`null` zeigt die Kachel „Interessen angeben“). Die Zahl ist die Länge der persönlichen Liste für „heute und die nächsten 6 Tage“ (`im-fenster`), nach Mindestpunkten, Deckeln und Kappung auf 8, **ohne** den Parameter `ohne` (den hat die Übersicht nicht) und **ohne** den Ersatz. 0 bleibt 0, auch wenn das Startmodul dann „Beliebt in Düsseldorf“ zeigt. Sie ist nicht die Summe der Abschnitte von `GET fuer-dich`. `kommende` und `erlebt` zählen die eigene Merkliste, inklusive sensibler Merkungen, ohne deren IDs. `interessen` ist die Summe der Chip-Listen (3.1).
  - **Kein 503 für die ganze Übersicht**, wenn nur die Sensibel-Menge fehlt: dann `vorschlaege: null` und `vorschlaege_unbekannt: true`. Die Kachel zeigt keine Zahl, nur „Ansehen“. Die anderen Zahlen kommen trotzdem. Nur `start` und `fuer-dich` antworten in diesem Fall 503 (Abschnitt 5).
- **403 und 401** wie in 3.0. Hauptpfad unter 16: 403 `mindestalter_fehlt`. Extra-Prüfung `unter16_gesperrt_am` im Handler nur als Verteidigung (dann `ohneHinweis` und, nur bei Cookie, `ddd_konto=0`). Tests müssen den **erreichbaren** Pfad (leeres Mindestalter) als 403 `mindestalter_fehlt` erwarten, nicht als `unter16_gesperrt`.
- **Schalter aus** → 404.
- Kontenplan Abschnitt 13 (`fuer-euch`, `lib/fuer-euch.ts`) wird durch diese Namen ersetzt. Beide Paare werden nicht gebaut.

## 7. Daten und Datenbank
- **Keine Migration nötig.** Alles nutzt vorhandene Spalten und Tabellen.
- Der Dienst-Client liest `event_sensibel` für die Ausschlussmenge, wie bei der Übernahme der Merkliste.
- **Rechte-Prüfung:** unverändert. Es gibt keine neue Funktion und keine neue Policy.

## 8. Datenschutz und Texte
- **B1/B2:** abgedeckt durch die Einwilligung (a). Ihr Wortlaut lautet: „… zusammen mit meiner Merkliste nutzt, um mir passende Events vorzuschlagen …“.
- **„Deine nächsten Events“, Erlebt, Zählung kommende/erlebt:** Vertrag (Merkliste), keine neue Verarbeitung. Eigene sensible Merkungen dürfen dort stehen, ohne Kennzeichnung (E13: für die Person nicht erkennbar, welche Events als sensibel gelten; nicht: aus der eigenen Liste streichen).
- **B18:** keine Personendaten.
- **S3 Anrede mit Vornamen:** neue Zweckangabe für eine Pflichtangabe. Heute steht an beiden Stellen nur der Ticketkauf. Nötige Änderungen, erst nach schriftlicher Bestätigung:
  - `web/app/datenschutz/konto-abschnitt.tsx`, Zeile „Name und Geburtsdatum (Pflichtangaben)“: der Zweck endet heute mit „Name für Ticketkäufe über das Konto“. Ergänzen: „und für die persönliche Anrede auf der Website und in der App“.
  - `TEXT.stammdaten.text` in `web/lib/konto/texte.ts`: der Satz lautet heute „Deinen Namen brauchen wir für Ticketkäufe über dein Konto.“ Ergänzen: „und um dich persönlich anzusprechen“.
  - Die Änderung ist Information nach Art. 13, keine Einwilligung, also keine neue Zeile in `einwilligungstexte`. Bis zur Bestätigung bleibt `NAMEN_ANREDE` aus und die Oberfläche ohne Namen.
- **Datenschutzerklärung zu B1:** Die Zeile „Interessen und persönliche Vorschläge“ deckt Startseite und „Für dich“ schon ab. Optional ergänzen: „Die Vorschläge siehst nur du, nach der Anmeldung.“
- **E13 / S4:** Sensible Events sind weder **Eingabe der Punktrechnung** noch **Vorschlag**. Statistik (`merk_statistik`) bleibt ausgeschlossen. Eigene Listen und Zählungen bleiben. Antworten enthalten keine Kennzeichnung (Test). Der Ersatz „Beliebt“ und eine leere persönliche Liste verraten nicht, dass die Merkliste nur aus sensiblen Events besteht. IDs, die nur auf dem Gerät liegen, gehen nicht als `ohne` an den Server: Das wäre die Art.-9-Information ohne Einwilligung (b). Dass ein solches Event in „Für dich“ noch einmal erscheinen kann, ist der Preis dafür.

## 9. Ablauf und Freigaben

| Schritt | Inhalt | Wer | Freigabe |
|---|---|---|---|
| 0 | Dieser Plan, fünfte Fassung (nach der vierten Prüfung durch Cursor) | Auftraggeber | Plan freigegeben |
| 1 | `lib/fuer-dich.ts` mit Tests (Punkte, Vielfalt, Ausschluss sensibel, Wenig-Daten-Ersatz, Fokustag je `fokus`-Modus, 7-Tage-Heute ≠ öffentliche Box) | Claude | Tests grün |
| 2 | API-Routen `start`, `fuer-dich`, `uebersicht`. Keine Änderung an `merkliste`. `ich` unverändert. Wrapper: automatisches Hinweis-Cookie nur bei `quelle === "cookie"` (6), dasselbe für das Verteidigungs-Cookie der neuen Handler. `kontoAttributAbgleichen()` in `hinweisSetzen`, `konto()`, `abruf()`, `eventsLaden` und `KontoSync` (3.0); Pfadwechsel in Suspense | Claude | Tests grün |
| 3 | Seiten und Navigation (3.1–3.9), Umzug der Konto-Abschnitte | Claude | Browser-Prüfung lokal, mobil und Desktop |
| 4 | Startseiten-Insel und Vorschau (4.1–4.3), Skript im Head | Claude | Browser-Prüfung: kein Flackern. Der erste Block verschiebt sich nicht. Der zweite darf wachsen. Cache-Köpfe von `/` und `/?datum=` bleiben wie heute, kein `Set-Cookie` |
| 5 | Texte S3 (falls bestätigt), Anwalt | Claude, Anwalt | schriftliche Bestätigung |
| 6 | Cursor-Prüfung der Umsetzung, dann Deploy | Auftraggeber | Deploy-OK |

## 10. Tests (Auszug)
- **Unit `fuer-dich`:**
  - Punkte je Trefferart, `mit-kindern` nur über den Slug `familie`.
  - „Von allem etwas“: alle Slugs aus `KATEGORIEN` (ohne `sonstiges`), dann kein +2.
  - Mindestpunkte 2.
  - Vielfalt beim Füllen der persönlichen Liste, keine Nachschubliste. Event ohne Reihe bleibt erlaubt. Sammelort fällt unter keinen Ort-Deckel. Ersatz „Beliebt“ ohne diese Deckel, höchstens 8.
  - Gemerkte, sensible, abgesagte und Stamm-Events nie vorgeschlagen.
  - Ein gemerktes sensibles Event erzeugt keine „wie …“-Treffer und keinen Abschnitt „Weil du … gemerkt hast“, wenn es der einzige Bezug wäre. Reihe und Ort zusammen geben nur einmal +1.
  - Ersatz „Beliebt“ nur mit Einwilligung, nicht leerer Kandidatenmenge und ohne persönliche Treffer, ohne sensible IDs, höchstens 8. Leere Kandidatenmenge: kein Ersatz.
  - `fokus: "tag"` nutzt `amFokustag` dieses Tages. `fokus: "kein"` nicht. `fokus: "im-fenster"`: Event mit Fokustag außerhalb von `[von, bis]` raus, innerhalb drin.
  - Öffentliches „Heute“ (7 Tage, `im-fenster`) ≠ `beliebtAuswahl` der Startseite (ein Tag + Reserve). Ein Test, der beide Listen vergleicht, darf sie nicht als gleich verlangen.
  - Ein Event im Fenster nur eine Karte. Eingabe ist `pool.events` (gebündelt), nicht `pool.alle`.
  - Langläufer: bei `fokus: "tag"` nur am eigenen Fokustag, bei `im-fenster` nur mit Fokustag im Fenster, bei `kein` dabei. Ein Event, das nur über `mitLanglaeufern` ins Fenster kommt, fehlt ohne diesen Schalter (Gegenprobe).
  - Abgleich: Unterkategorie über `kategorie/unter`, Stadtteil über `stadtteilSlug(e.stadtteil)` (ohne Stadtteil kein Aufruf), `unterkategorie: "keine"` trifft nie, `praeferenzen.orte` gibt keine Punkte, `abends`/`tagsueber` über `uhrzeitenVon` (11:00 und 19:00 treffen beide), ohne Uhrzeit kein Treffer. `istSammelort` gibt keinen Reihen-oder-Ort-Punkt.
  - `/konto/fuer-dich`: dasselbe Event nicht in zwei Abschnitten. Wochenende über `wochenende()`, nicht über `zeitraumAuflösen("wochenende")`. Abschnitt 3 nur mit mindestens 2 Punkten und nur zum einen Bezugs-Event. Gleichstand über `gemerkt_am`, dann `event_id`.
  - Vergangener einzelner Tag: keine Vorschläge, kein Ersatz. Ein ungültiger Bereich wird zu „heute“.
- **Routen:**
  - Ohne Einwilligung: `fuer_dich` leer, `ersatz` falsch, keine Punkte. `naechste` trotzdem gefüllt, wenn die Merkliste Kommendes hat.
  - Antworten ohne `sensibel`, ohne Nutzer-ID, ohne Punkte, ohne die ausgeschlossenen IDs. `vorname` fehlt, solange `NAMEN_ANREDE` aus ist; `GET /api/konto/ich` enthält `vorname` weiter.
  - 404 ohne Schalter. 401 mit unleserlichem, kaputtem, abgelehntem Refresh oder ungültigem Sitzungs-Cookie: `Set-Cookie` löscht `ddd_sitzung` und `ddd_konto`. 401 ganz ohne Sitzungs-Cookie, 401 ohne Profil und 401 weil beim Erneuern kein Auth-Client da ist: kein Lösch-Cookie. 403 `mindestalter_fehlt` setzt `ddd_konto=0`, wenn die Sitzung aus dem Cookie kommt (auch wenn `unter16_gesperrt_am` gesetzt ist – das ist der Live-Pfad). 403 `passwort_setzen_noetig` ohne `resetErlaubt`. 403 `unter16_gesperrt` nur in einem Test mit inkonsistenter Zeile oder gemocktem Profil, das Mindestalter *und* Sperre gesetzt hat; dann `ohneHinweis` und bei Cookie `ddd_konto=0`.
  - `ohne` mit 25 IDs und mit einer ungültigen ID: 200, die überzähligen und ungültigen fehlen still. Die Antwort enthält die Liste nicht.
  - Dienst-Client für `event_sensibel` fehlgeschlagen: `start` und `fuer-dich` 503, keine Vorschläge. Der Fehler steht nicht 10 Minuten im Cache.
  - Bearer ohne Cookie: 200 mit gültigem Token, **ohne** das automatische `Set-Cookie` für `ddd_konto` (Zeile 191; heute würde der Test scheitern). Bearer bei leerem Mindestalter: 403 `mindestalter_fehlt` ebenfalls ohne `Set-Cookie` (Zeile 183). Mit Cookie bleibt alles wie heute (Hinweis-Cookie gesetzt). Anmelden, Abmelden und Löschen setzen ihre Cookies weiter, auch der Test darauf.
  - 401 ohne Sitzungs-Cookie (nur `ddd_konto=1` geschickt): Antwort ohne `Set-Cookie`; der Client-Test erwartet danach trotzdem kein `ddd_konto` und kein `data-konto` (über `lokalAbmelden()`). Das widerspricht dem Fall „kaputtes Cookie löscht per Set-Cookie“ nicht: dort liegt ein Sitzungs-Cookie bei.
  - `uebersicht` bei fehlender Sensibel-Menge: 200, `vorschlaege: null`, `vorschlaege_unbekannt: true`, die übrigen Zahlen gesetzt. `start` und `fuer-dich`: 503.
  - `naechste`: höchstens 4, laufendes mehrtägiges Event mit `metaZeile` „läuft bis …“, abgesagtes gemerktes Event enthalten, Fehler beim Event-Laden → `naechste` leer, `fuer_dich` trotzdem da. `vorschlaege` zählt den Ersatz nicht mit.
- **Browser:**
  - Abgemeldet: Vorschau sofort, Button und Anmelden-Link erreichbar, Karten nicht fokussierbar.
  - Cookie `1`: keine Vorschau (nicht in der Tab-Reihenfolge), Platzhalter des ersten Moduls, dann Inhalt. Der zweite Block darf die Seite länger machen. Kein Abruf bei Cookie `0`.
  - Cookie `0` auf `/merkliste`: „Vorbei“, nicht „Erlebt“.
  - 401 räumt das Attribut ab und zeigt die Vorschau.
  - 403 `passwort_setzen_noetig` bei Cookie `1`: Satz plus Link `/konto/passwort-neu`, keine B18, kein Fetch-Loop.
  - TabBar: „Für dich“ nur auf `/konto/fuer-dich`. „Profil“ nicht gleichzeitig auf dieser Seite. Auf `/konto/willkommen` ist „Profil“ aktiv. Nur eine Leiste fokussierbar.
  - Alle Konto-Unterseiten mobil und am Desktop. `/konto` als Übersicht, dort kein Zurück-Pfeil.
  - `curl` von `/` und `/?datum=` ohne `Set-Cookie`. Die Cache-Köpfe bleiben die heutigen. Ein `s-maxage` steht im Code nicht und wird nicht verlangt.
  - Anonymer Besuch: Network ohne `/api/konto/start`.
  - **Ohne Neuladen:** abgemeldet auf der Startseite anmelden (fertiges Profil, Formular, `router.push`) → zurück auf `/`: Module statt Vorschau, neue TabBar. „Überall abmelden“ → `/konto/abgemeldet`: heutige TabBar, kein `data-konto`. In einem zweiten Tab abmelden → im ersten Tab nach `focus` Vorschau statt Modulen. In einem zweiten Tab anmelden, während der erste abgemeldet ist: nach `focus` die Module, auch obwohl `kontomodus()` beim Registrieren des Listeners falsch war.
  - 429 auf `GET start` (Bremslimit im Test herabgesetzt): Modul klappt zu, keine Vorschau, kein weiterer Abruf desselben Fehlers. Ein anderes `?datum=` lädt neu.
  - Leer-Hinweis statt Tipp und Picks (Tag ohne Events): Vorschau bzw. Insel an derselben Stelle vor der Weihnachtsmarkt-Box. `ohne` ist dann leer.
  - Vergangener Tag `/?datum=` vor heute: Modul „Für dich empfohlen“ fehlt, „Deine nächsten Events“ bleibt, wenn es Kommendes gibt. Kein Ersatz „Beliebt“.

## 11. Risiken
- **Leere Vorschläge** bei wenigen Interessen → Ersatz „Beliebt“ (Abschnitt 5), Hinweis auf Interessen. Auf „Heute“ kann dieser Ersatz andere Events zeigen als die öffentliche Box darunter; das ist Absicht (anderes Fenster).
- **Rechenzeit:** Der Pool hat einige tausend Events, die Punktrechnung ist linear. Sie läuft je Anfrage im Speicher, ohne Datenbank außer Profil, Merkliste und gecachter Sensibel-Menge.
- **Verschiebung beim Laden:** Das Skript im Head setzt das Attribut vor dem ersten Paint. Der Platzhalter gilt für das erste Modul. Das zweite Modul darf die Seite danach länger machen.
- **Gewohnheit:** Wer `/konto` als eine Seite kennt, findet die Abschnitte jetzt auf Unterseiten. Die Übersicht verlinkt alles.
- **Zwei TabBars im HTML:** Die inaktive ist über `display: none` aus Tastatur und Screenreader raus, schon vor der Hydration; `hidden` nach der Hydration ist zweite Sicherung (3.9).
- **Veraltetes Attribut:** Ohne den Abgleich aus 3.0 stünde `data-konto` nach Anmelden oder Abmelden bis zum Neuladen falsch. Der Abgleich ist deshalb Pflichtteil von Schritt 2, mit eigenen Browser-Tests (10).

## 12. Offene Punkte
- S1–S7 bestätigt am 18.11.2026. Zu S3: Die Module werden zunächst ohne Namen gebaut; der Text-Zusatz (Abschnitt 8) geht an den Anwalt, erst danach kommt „Hallo Vorname“.
- Ob „Für dich“ in Stufe 2 Orte (B4) mit einbezieht, entscheidet der Location-Plan (`docs/plan-locations-2026-11-18.md`).

## 13. Prüfhistorie
- 18.11.2026: erste Fassung (Claude). S1–S7 vom Auftraggeber bestätigt.
- 18.11.2026: zweite Fassung nach der ersten Cursor-Prüfung. Eingearbeitet: drei Zustände von `ddd_konto`, Skript im Head statt über `body`, Startseite liest `searchParams`, kein `?vorbei=1`, `fuer-euch` wird ersetzt und nicht daneben gebaut, Fokustag je Fläche, Gleichstand über `nachEmpfehlung`, Deckel ohne Nachschub, Einwilligung (a) sperrt nur die Punkte und nicht „Deine nächsten Events“, Sensibel-Lesen nur mit Dienst-Client und 503 bei Ausfall, `ohne` gekappt, TabBar ohne `startsWith("/konto")`, S3 an den zwei heutigen Textstellen, `NAMEN_ANREDE` bis zur Anwaltsbestätigung aus.
- 19.11.2026: dritte Fassung nach der zweiten Cursor-Prüfung. Eingearbeitet: persönliches 7-Tage-Fenster auf „Heute“ ist nicht der Live-Aufruf von `beliebtAuswahl`; `fokus` dreistufig (`kein` / `tag` / `im-fenster`); Ersatz 6–8 aus derselben Kandidatenmenge; 403 unter 16 vs. Wrapper (`mindestalter_fehlt` ist der Live-Pfad); Reset-Sitzung vs. B18; TabBar/B18 `display: none` plus `hidden`/`inert`; Anmelden-Link und `weiter` auf die aktuelle Start-URL; `ich` unverändert, `vorname` nur in `GET start` bei Flag; Übersicht-Zahl ≠ Summe der Für-dich-Abschnitte; E13-Wortlaut für eigene Listen; Tests für die erreichbaren 403-Pfade und gegen Gleichsetzen mit der öffentlichen Box.
- 19.11.2026: **vierte Fassung nach der dritten Prüfung durch Claude Code** (gegen den Live-Code: `page.tsx`, `layout.tsx`, `ableitungen.ts`, `datum.ts`, `konto/route.ts`, `sitzung.ts`, `merk-store.ts`, `merk-logik.ts`, `merkliste-events.ts`, `client.tsx`, `merkliste/route.ts`, `konten_stammdaten_2026-11-17.sql`). Eingearbeitet:
  - **hoch:** `data-konto` muss ohne Neuladen nachgeführt werden (Anmelden und Abmelden laufen per `router.push`). Neu `kontoAttributAbgleichen()` mit Aufrufen in `hinweisSetzen`, `konto()` und `KontoSync`; abhängige Bausteine über `useSyncExternalStore` (3.0).
  - **hoch:** Der Wrapper hängt das Hinweis-Cookie auch an Bearer-Antworten. Der Test der dritten Fassung („Bearer ohne `Set-Cookie`“) wäre gegen den Code gescheitert. Wrapper-Änderung `quelle === "cookie"` aufgenommen (1, 6, 9, 10).
  - **mittel:** Die 401 ohne Sitzungs-Cookie kommt ohne `Set-Cookie`. Fakten und 3.0 korrigiert, der Client räumt.
  - **mittel:** Das Head-Skript kann `hidden`/`inert` nicht an der TabBar setzen, weil die `nav` dann noch nicht im DOM steht. `display: none` reicht für Tastatur und Screenreader. `hidden` kommt nach der Hydration (3.9).
  - **mittel:** Kein Zustand für 429, 503 und Netzfehler auf der Insel. Ergänzt: still zuklappen, keine Vorschau, keine Schleife (3.0).
  - **mittel:** Langläufer nicht geregelt. Jetzt `mitLanglaeufern: true` wie `startPlaetze`, begrenzt durch die Fokustag-Regel (5).
  - **mittel:** Abgleich der Interessen mit Event-Feldern ungenau. Unterkategorie als `kategorie/unter`, Stadtteil über `stadtteilSlug`, `orte` ohne Punkte, Uhrzeiten über `uhrzeitenVon` (5).
  - **mittel:** Widerspruch 4.2/6: `naechste` kam einmal aus der Merkliste-Route, einmal aus `GET start`. Jetzt nur `GET start`, serverseitig mit denselben Bausteinen (4.2, 6).
  - **gering:**
    - Sortierung vereinfacht auf `nachEmpfehlung(stufen)` ohne `tag`, weil der Filter den Fokustag schon erzwingt (wie `beliebtAuswahl`).
    - `uebersicht` ohne 503 bei fehlender Sensibel-Menge.
    - Platz der Insel auch beim Leer-Hinweis.
    - `data-event-id` an Tipp und Picks für `ohne`.
    - „läuft bis …“ für laufende Mehrtägige.
    - Merkungen nur auf dem Gerät fehlen in Modul und Zählung (Hinweis).
    - TabBar-Regel für öffentliche Konto-Seiten eindeutig.
    - Startseiten-Insel zählt als Aktivität.
  - **Aus der zweiten Durchsicht des ganzen Plans:**
    - **mittel:** Auf `/konto/fuer-dich` konnte dasselbe Event in mehreren Abschnitten stehen (z. B. samstags „Heute und morgen“ und „Dein Wochenende“). Jetzt jedes Event nur einmal, Fenster je Abschnitt ausdrücklich.
    - **gering:** Fenster und Gleichstand für „Weil du … gemerkt hast“ festgelegt.
    - **gering:** Vergangener Tag über `/?datum=` (wird angenommen) bzw. leeres Fenster: Modul klappt zu, kein Ersatz.
  - **Unverändert bestätigt gegen den Code:**
    - `fokusTag` nur bei `von === bis`.
    - Ungültiges `datum` wird zu „heute“.
    - Unter 16 führt über `mindestalter_fehlt`.
    - `ohneHinweis` greift nach dem Handler.
    - `merklisteAufteilen` gibt es schon, kein `?vorbei`.
    - `istAktiv` arbeitet mit `startsWith`.
    - `THEME_SCRIPT` steht im `<head>`, `<html>` hat `suppressHydrationWarning`.
- 19.11.2026: **fünfte Fassung nach der vierten Prüfung durch Cursor** (gegen denselben Live-Code, zusätzlich `konto.tsx`, `konto-zugang.tsx`, `merkliste.tsx`, `karten.tsx`, `termine.ts`, `vorlieben.ts`, `kategorien.ts`, `landing.ts`, `next.config.ts`, `konto.test.ts`). Die Änderungen der vierten Fassung bleiben, soweit unten nicht anders gesagt.
  - **hoch:** `kontoAttributAbgleichen()` auch in `abruf()` und nach dem Fetch in `merkliste.tsx`. `KontoSync` darf den Abgleich nicht hinter `if (!kontomodus())` verstecken. Pfadwechsel nur in `<Suspense>`, sonst blockiert `usePathname` das Vorrendern. Server-Momentaufnahme von `useSyncExternalStore` bleibt abgemeldet. `useKontomodus` hört `ddd-konto-geaendert`.
  - **hoch:** „Bearer-Antworten tragen kein Set-Cookie“ war zu weit. Nur Zeile 183 und 191 im Wrapper, plus das Verteidigungs-Cookie der neuen Handler. Anmelden, Abmelden, Löschen und die unter-16-Cookies in `stammdaten`/`abschluss` bleiben. Kein bestehender Route-Test nutzt Bearer.
  - **hoch:** Geräte-IDs dürfen nicht als `ohne` mitgehen (E13). Sie können in „Für dich“ doppelt erscheinen.
  - **hoch:** Die Insel liest `datum` über `useSearchParams()` in eigener Suspense-Grenze. `data-event-id` auch am Tipp, IDs eindeutig (mobil und Desktop stehen beide im DOM).
  - **mittel:** „6–8“ und „3–4“ sind jetzt „bis zu 8“ und „bis zu 4“. Deckel gelten bis zur Obergrenze des Abschnitts, nicht nur unter den ersten 8. Abschnitt 3 verlangt mindestens 2 Punkte und genau ein Bezugs-Event. Wochenende über `wochenende()`, nicht über den beschnittenen öffentlichen Key. Ersatz „Beliebt“ nur auf der Startseite und nur bei nicht leerer Kandidatenmenge. Leere Für-dich-Seite hat einen Satz ohne Grund.
  - **mittel:** Beschriftung ist `metaZeile`, nicht „in 3 Tagen“. Pool ist `events`, nicht `alle`. Ort über `norm()` und ohne `istSammelort`. `gemerkt_am` aus der Merkliste-Zeile. Fehler der Sensibel-Menge werden nicht gecacht. `vorschlaege` zählt den Ersatz nicht.
  - **mittel:** Der Test „401 ohne Sitzung löscht das Cookie“ widersprach dem Test „401 ohne Sitzungs-Cookie löscht nichts“. Jetzt nach dem Code in `sitzung.ts` getrennt.
  - **gering:** Neue Seiten nutzen `KontoRahmen`, `KONTO_ROBOTS` und die Weiterleitung bei `passwort_setzen_noetig`. Ein Datumswechsel nach 429 lädt neu. Ein vergangener Bereich `von_bis` wird zu „heute“.
- 19.11.2026: **Vom Auftraggeber freigegeben** (fünfte Fassung). Umsetzung erst auf ausdrückliche Anweisung.
- 19.11.2026: **Schritt 1 gebaut** (lokal, nicht committet): `web/lib/fuer-dich.ts` (Fenster `startFenster`, `kandidaten`, `bewerten`, `mitDeckeln`, `startVorschlaege`, `anzahlVorschlaege`, `fuerDichSeite`) und `web/tests/fuer-dich.test.ts` (23 Tests). Gesamte Suite 476/476 grün, TypeScript und ESLint ohne Befund. Begründung: die zwei höchsten Treffer, z. B. „Jazz & Soul · Musik“ bzw. „wie ‚…‘“ beim Bezug.
- 19.11.2026: **Schritt 2 gebaut** (lokal, nicht committet): Routen `GET /api/konto/start`, `/fuer-dich`, `/uebersicht` mit gemeinsamem Baustein `web/lib/konto/mein-bereich.ts` (Sensibel-Menge mit 10-Minuten-Cache ohne Fehler-Cache, Stufen je Pool, Merkliste mit `gemerkt_am`, `ohne` gekappt auf 24, Verteidigung `unter16_gesperrt`). Wrapper: Hinweis-Cookie nur bei `quelle === "cookie"` (Zeile 183 und 191). `NAMEN_ANREDE = false` in `konfig.ts`. Abgleich `kontoAttributAbgleichen()` in `merk-store.ts` (in `hinweisSetzen`, `abruf`, `konto()`, `eventsLaden`, `KontoSync` inkl. Fokus vor der Sperre und Pfadwechsel in eigener Suspense-Grenze), `useKontoZustand()` und `useKontomodus` hören `ddd-konto-geaendert`. Zusätzlich gegenüber dem Plan: `start` antwortet 503, wenn schon die Merkliste nicht lesbar ist (sonst ließen sich gemerkte Events nicht ausschließen); gemerkte Events ohne geladene Daten werden trotzdem ausgeschlossen. Tests: `tests/mein-bereich.test.ts` (14), `tests/konto-attribut.test.ts` (2); Suite 492/492, TypeScript und ESLint ohne Befund, Build mit Schalter an ok, Browser: Attribut folgt Cookie 0/fehlt, veraltetes 1 wird über 401 geräumt.
- 19.11.2026: **Schritt 3 gebaut** (lokal, nicht committet): Übersicht `/konto` („Mein dies.das“, Kacheln Für dich / Merkliste / Erlebt / Interessen aus `GET uebersicht`, Liste Konto und Sicherheit / Datenschutz) und neue Seiten `/konto/fuer-dich`, `/konto/erlebt` (`components/mein-bereich.tsx`), `/konto/interessen` (Chips, Schalter a mit Rückfrage), `/konto/einstellungen` (bisherige Abschnitte unverändert), `/konto/datenschutz` (b–d, Auskunft, Links) in `components/konto-bereich.tsx` mit gemeinsamer Hülle `KontoHuelle` (401, Reset-Sitzung, gesperrt). Navigation `components/konto-nav.tsx` (Seitenleiste ab 1024 px auf `/konto/*` und `/merkliste`) und mobiler Zurück-Pfeil im `KontoRahmen`, beide nur bei `data-konto="1"` (CSS, danach zusätzlich `hidden`). TabBar mit zwei Leisten, Umschaltung per CSS über `html[data-konto]`, Aktiv-Regeln `istAktivKonto` (Profil-Pfade als feste Liste). Merkliste: „Erlebt (n) →“ statt „Vorbei“ nur bei `data-konto="1"`. Zusätzlich gegenüber dem Plan: `GET fuer-dich` liefert `heute` (für die Datumszeile der Karten); nach „Interessen ändern“ geht es zurück auf `/konto/interessen` statt `/konto`; `useKontoZustand` liegt jetzt in `client.tsx` (Ring-Import vermieden), `konto.tsx` reicht ihn weiter; Fragebogen-Daten in `app/konto/fragebogen-daten.ts` für Willkommen und Interessen. Tests: `tests/tabbar-aktiv.test.ts` (4), `heute` in `mein-bereich.test.ts`; Suite 496/496, TypeScript ohne Befund, Build mit Schalter an ok. Browser (ohne echtes Konto, API-Antworten im Browser simuliert): Leisten-Umschaltung in beide Richtungen, nur eine Leiste bedienbar, Profil aktiv auf Unterseiten, „Für dich“ nur auf seiner Seite, Seitenleiste nur bei 1, Cookie 0 zeigt „Vorbei“, Erlebt nach Monat, Herz entfernt sofort, veraltetes Cookie 1 wird über 401 geräumt.
- 19.11.2026: **Schritt 4 gebaut** (lokal, nicht committet): Head-Skript `web/lib/konto/kopf-skript.ts` (nur bei `kontenAktiv()` in `layout.tsx`, setzt `html[data-konto]` aus `ddd_konto`, liest `body` nicht). Startseite `web/app/page.tsx`: Vorschau B18 (`StartVorschau`, erste bis zu 4 Karten aus „Diese Woche beliebt“, `aria-hidden` + `inert` + `data-nosnippet` nur am Karten-Container, Kasten mit Schloss, „Kostenlos registrieren“ / „Schon ein Konto? Anmelden“ mit `weiter` = aktuelle Start-URL) und Insel `web/components/start-persoenlich.tsx` in eigener Suspense-Grenze, beide nach „Tipp und Picks“ bzw. dem Leer-Hinweis, vor `WmStartBox`. `data-start-gezeigt` an „Tipp und Picks“, `data-event-id` am Tipp und an den Picks (`KompaktKarte mitId`); die Insel schickt höchstens 5 eindeutige IDs als `ohne`. Insel lädt nur bei `data-konto="1"`, je Datum einmal (`key`), 401 → `lokalAbmelden()`, 403 `mindestalter_fehlt` → `lokalAbmelden(true)`, 403 `passwort_setzen_noetig` → Satz + Link, sonst still zu. Zusätzlich gegenüber dem Plan: `GET start` liefert `heute`; die Insel rendert abgemeldet einen leeren Platzhalter, den CSS nur bei `1` zeigt (`/` ist dynamisch, der Server löst die Suspense-Grenze selbst auf; sonst fehlte die reservierte Höhe vor der Hydration). Tests: Head-Skript in `konto-attribut.test.ts`, `heute` in `mein-bereich.test.ts`; Suite 531/531 (inkl. Tests anderer Sitzungen), TypeScript ohne Befund, Build ok (`/` weiter dynamisch). Browser: abgemeldet Vorschau ohne Abruf und Karten nicht fokussierbar; Cookie 0 ohne Vorschau, Platzhalter und Abruf; veraltetes Cookie 1 → Vorschau; mit simulierten Antworten beide Module, ohne Einwilligung, Ersatz ohne Link, 429 still zu ohne Wiederholung, 401 → Vorschau, Reset-Sitzung mit Link, neuer Abruf je Datum. `curl` von `/` und `/?datum=morgen`: kein `Set-Cookie`, kein `data-konto`, Cache-Köpfe wie live. Offen: Schritt 5 (S3 nach Anwalt), Schritt 6 (Cursor-Prüfung der Umsetzung: `docs/cursor-pruefung-mein-bereich-umsetzung-2026-11-19.md`, dann Deploy nach OK).
- 19.11.2026: **Cursor-Prüfung der Umsetzung (Schritte 1–4)**, Prompt `docs/cursor-pruefung-mein-bereich-umsetzung-2026-11-19.md`. Ergebnis „bereit für Schritt 6 nach Behebung“, Abweichungen 1–7 alle in Ordnung. Befunde behoben (lokal, nicht committet):
  - **mittel, Befund 1:** Vergangener einzelner Tag mit noch laufendem Mehrtägigen, dessen Fokustag genau dieser Tag ist, lieferte Vorschläge bzw. „Beliebt“. Jetzt `kandidaten()` leer, wenn `fokus === "tag"` und der Tag vor `heute` liegt (`web/lib/fuer-dich.ts`). Test mit Gegenprobe.
  - **mittel, Befund 2:** `hidden` an Konto-Leiste und Seitenleiste stand schon im Server-HTML (Server-Momentaufnahme „abgemeldet“). In Chromium gewinnt das Autoren-CSS (gemessen: `display: grid` trotz `hidden`), in anderen Engines nicht sicher. Jetzt setzen TabBar und Seitenleiste `hidden` erst nach der Hydration (`useHydriert()` in `web/components/client.tsx`).
  - **gering, Befund 3:** Übersicht zeigte bei nicht geladenen Merkliste-Events 0 in „Merkliste“ und „Erlebt“. Jetzt „Ansehen“ ohne Zahl bei `merkliste_unvollstaendig` (`web/components/mein-bereich.tsx`).
  - **Tests ergänzt:** vergangener Tag als Fokustag eines Mehrtägigen, `uebersicht` mit Ladefehler, Reset-Sitzung (403 `passwort_setzen_noetig`) an `start`, `fuer-dich`, `uebersicht`. Suite 536/536, TypeScript und ESLint ohne Befund. Die Browserfälle aus Abschnitt 10 bleiben manuell (Claude Code hat sie mit simulierten Antworten geprüft).
- 19.11.2026: **Schritte 1–4 LIVE** (Commit 1d541ec, Deploy ok). Live geprüft: alle neuen Seiten 200, neue APIs ohne Anmeldung 401, `/` ohne `Set-Cookie` und ohne `data-konto` im HTML, Cache-Köpfe unverändert, Vorschau B18 abgemeldet sichtbar ohne Abruf von `/api/konto/start`. Offen: Abnahme durch den Auftraggeber mit echtem Konto, Schritt 5 (S3 nach Anwalt).
- 19.11.2026: **Schritt 5 gebaut** (lokal, nicht committet): Anrede mit Vornamen vom Auftraggeber freigegeben. `NAMEN_ANREDE = true`; Zweck „persönliche Anrede“ ergänzt in `web/app/datenschutz/konto-abschnitt.tsx`, `TEXT.stammdaten.text` und in der Art.-15-Auskunft (`web/app/api/konto/export/route.ts`). Startmodul zeigt „Hallo <Vorname>“ unter „Für dich empfohlen“. Dazu auf Wunsch des Auftraggebers die Widerrufssätze von (b) und (d) per du: neue Textversionen `sensible-events-2026-11-2` und `geburtstagsmail-2026-11-3`, SQL `database/einwilligungstexte_2026-11-19.sql` (muss **vor** dem Deploy laufen, Fremdschlüssel `einwilligungen.textversion`). Suite 536/536, Build ok, im Browser geprüft (Gruß, beide Sätze auf `/konto/datenschutz`, Zeile in `/datenschutz`).
- 19.11.2026: Auf Wunsch des Auftraggebers auch der Widerrufssatz von (a) per du: `interessen-2026-11-2` („Du kannst das jederzeit im Konto widerrufen. Dann werden deine Antworten sofort gelöscht.“). `database/einwilligungstexte_2026-11-19.sql` enthält jetzt drei Fassungen (a, b, d) und muss vor dem Deploy laufen. Suite 536/536.
- 19.11.2026: **Schritt 5 LIVE** (Commit c15887f, Deploy ok), SQL einwilligungstexte_2026-11-19.sql vorher vom Auftraggeber ausgeführt (3× ok). Live geprüft: Zeile in /datenschutz, neue du-Sätze in den ausgelieferten Skripten von /konto/datenschutz und /konto/interessen, keine alten „Ich kann“-Sätze. Stufe 1 damit vollständig.
- 20.11.2026: **Cursor-Gesamtprüfung live** (`docs/cursor-pruefung-mein-bereich-live-2026-11-19.md`): „kann live bleiben“, Teil A vollständig ok, Teil B ok bis auf zwei nicht prüfbare Fälle (Fokuswechsel ohne Neuladen im Hintergrund-Tab, „Erlebt (n)“ ohne vergangene Merkung); Befunde 1–3 der vorigen Prüfung live bestätigt behoben. Einziger Befund (gering): Ziel nach der Anmeldung ohne `weiter` war `/merkliste`. Behoben (lokal, nicht committet): `STANDARD_ZIEL = "/konto"` in `web/lib/konto/weiter.ts` (gilt auch nach dem Onboarding und bei ungültigem `weiter`), Ersatzziel im Client (`konto-bereich.tsx`) angeglichen, Tests angepasst. Suite 553/553.
