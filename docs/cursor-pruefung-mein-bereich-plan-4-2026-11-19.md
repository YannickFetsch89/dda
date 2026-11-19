# Cursor-Prompt: Prüfung der vierten Fassung „Mein dies.das – Stufe 1“ (19.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD geöffnet, Branch `claude/setup-project-structure-5QNOf`).

---

Du prüfst die **vierte Fassung** des Plans `docs/plan-mein-bereich-stufe1-2026-11-18.md`. Du baust nichts.

**Vorgeschichte:**
- Zwei Cursor-Prüfungen (18.11. und 19.11.) haben die zweite und dritte Fassung ergeben.
- Danach hat Claude Code den Plan gegen den Live-Code geprüft und die vierte Fassung geschrieben.
- Die Entscheidungen S1–S7 hat der Auftraggeber bestätigt. Stell sie nicht grundsätzlich in Frage, außer etwas ist rechtlich oder technisch unhaltbar.

**Verwandt:**
- `docs/konzept-personalisierung-2026-11-18.md` (P1–P7)
- `docs/plan-nutzerkonten-2026-11-16.md` (E13, 3.5, 4.2, 4.4, Abschnitt 13)
- `docs/plan-empfehlungen-2026-11-13.md` (Abschnitt 9)

## Teil 1: Was Claude Code in der vierten Fassung geändert hat und warum

Bitte jeden Punkt **gegen den Code** gegenlesen. Ist eine Änderung falsch oder unnötig, korrigiere sie. Ist sie richtig, lass sie stehen.

1. **Abgleich von `html[data-konto]` ohne Neuladen (Abschnitt 3.0, hoch).**
   - **Warum:** Das Head-Skript setzt das Attribut nur beim ersten Paint. Anmelden, Bestätigen, Alters-Häkchen und Abmelden laufen ohne Neuladen (`router.push`), das Cookie ändert sich per `Set-Cookie` auf Abrufen oder in `hinweisSetzen` (`web/lib/konto/merk-store.ts`). Das Attribut stünde bis zum Neuladen falsch: Nach dem Anmelden wäre noch die Vorschau zu sehen, nach dem Abmelden die eingeloggte TabBar.
   - **Neu:**
     - `kontoAttributAbgleichen()` in `merk-store.ts`, aufgerufen in `hinweisSetzen`, im Fetch-Helfer `konto()` (`web/components/konto.tsx`) nach jeder Antwort und in `KontoSync` (Start, Pfadwechsel, `focus`/`visibilitychange`).
     - Ereignis `ddd-konto-geaendert`, abhängige Bausteine über `useSyncExternalStore`.
   - **Prüfen:** Gibt es Wege, die `ddd_konto` ändern, ohne über `konto()` oder `hinweisSetzen` zu laufen? Zum Beispiel `fetch` direkt in `merk-store.ts` (`abruf`), `merkliste.tsx`, `konto-zugang.tsx`. Reicht der Abgleich dort?
2. **Hinweis-Cookie nicht bei Bearer (Abschnitte 1 und 6, hoch).**
   - **Warum:** `web/lib/konto/route.ts` hängt nach dem Handler `hinweisCookie(hinweisFuer(profil))` an und bei 403 `mindestalter_fehlt` `hinweisCookie("0")`, ohne `sitzung.quelle` zu prüfen. Der Test der dritten Fassung „Bearer ohne `Set-Cookie`“ wäre gescheitert. In einer Capacitor-WebView würde das Cookie den Web-Zustand umschalten.
   - **Neu:** Hinweis-Cookie nur bei `ctx.sitzung.quelle === "cookie"`, für alle Konto-Routen.
   - **Prüfen:** Bricht das eine bestehende Route oder einen Test in `web/tests/konto.test.ts`, der mit Bearer arbeitet?
3. **401 ohne Sitzungs-Cookie (Abschnitte 1 und 3.0, mittel).**
   - **Warum:** In `web/lib/konto/sitzung.ts` gibt `!roh` die Rückgabe `{ ok: false, setCookies: [] }`. Die 401 löscht dann nichts. Ein fehlendes Profil ergibt ebenfalls eine 401 ohne Löschen. Die dritte Fassung behauptete, die 401 lösche immer beide Cookies.
   - **Neu:** Der Client räumt über `lokalAbmelden()` auf.
4. **TabBar `hidden`/`inert` (Abschnitt 3.9, mittel).**
   - **Warum:** Das Head-Skript läuft, bevor die `nav` im DOM steht, und kann dort keine Attribute setzen.
   - **Neu:** `display: none` über `html[data-konto]` (nimmt die Leiste aus Tab-Reihenfolge und Screenreader), dazu `hidden` nach der Hydration als zweite Sicherung.
5. **429, 503, 500 und Netzfehler auf der Insel (Abschnitt 3.0, mittel).**
   - **Warum:** Dafür war kein Zustand beschrieben.
   - **Neu:** Das Modul klappt still zu. Keine Vorschau, kein `lokalAbmelden`, keine Schleife.
6. **Langläufer (Abschnitt 5, mittel).**
   - **Warum:** `filtern()` lässt sie ohne `mitLanglaeufern` weg. Der Plan sagte nichts dazu.
   - **Neu:** `mitLanglaeufern: true` wie bei `startPlaetze`, begrenzt durch die Fokustag-Regel je `fokus`-Modus.
7. **Abgleich der Interessen mit Event-Feldern (Abschnitt 5, mittel).**
   - **Neu:**
     - Unterkategorie als `` `${e.kategorie}/${e.unterkategorie}` `` (der Fragebogen speichert `kategorie/unter`), `"keine"` trifft nie.
     - Stadtteil über `stadtteilSlug(e.stadtteil)`.
     - `praeferenzen.orte` gibt in Stufe 1 keine Punkte.
     - `abends`/`tagsueber` über `uhrzeitenVon(e)`, ohne Uhrzeit kein Treffer.
8. **Datenquelle von „Deine nächsten Events“ (Abschnitte 4.2 und 6, mittel).**
   - **Warum:** 4.2 nannte `/api/konto/merkliste`, 6 dagegen `naechste` in `GET start`.
   - **Neu:** nur `GET start`. Serverseitig `ctx.db` + `eventsFuerIds` + `merklisteAufteilen`. Bei Fehler `naechste` leer, `fuer_dich` trotzdem da.
9. **`/konto/fuer-dich` ohne Doppelte (Abschnitt 3.3, mittel).**
   - **Neu:** Jedes Event nur im ersten passenden Abschnitt (1 → 4), Fenster je Abschnitt ausdrücklich (`im-fenster`).
   - „Weil du … gemerkt hast“ bekommt 14 Tage und als Gleichstand das zuletzt gemerkte Event.
10. **Kleinere Änderungen (gering):**
    - Sortierung `nachEmpfehlung(stufen)` ohne `tag`. Bei `fokus: "tag"` erzwingt der Filter den Fokustag schon, wie in `beliebtAuswahl`.
    - `uebersicht` ohne 503, wenn nur die Sensibel-Menge fehlt (`vorschlaege: null`, `vorschlaege_unbekannt: true`).
    - Vergangener Tag über `/?datum=` (`istGueltigerTag` nimmt ihn an): Modul klappt zu, kein Ersatz.
    - Insel und Vorschau auch beim Leer-Hinweis an derselben Stelle.
    - `data-event-id` an den Tipp-und-Picks-Karten für `ohne`.
    - „läuft bis …“ für laufende Mehrtägige.
    - Merkungen nur auf dem Gerät fehlen in Modul und Zählung.
    - TabBar folgt auf öffentlichen Konto-Seiten allein dem Zustand, dort ist kein Tab aktiv.
    - `GET start` zählt als Aktivität (24-Monats-Frist).

## Teil 2: Den ganzen Plan noch einmal kritisch prüfen und anpassen

Danach prüfst du den **kompletten Plan**, nicht nur die Stellen aus Teil 1. Gegenlesen am Live-Code, erfinde keine Befunde.

**Code, mindestens:**
- `web/app/page.tsx`, `web/app/layout.tsx`
- `web/lib/ableitungen.ts` (`filtern`, `beliebtAuswahl`, `nachEmpfehlung`, `amFokustag`, `fokustag`, `startPlaetze`)
- `web/lib/datum.ts` (`zeitraumAuflösen`, `istGueltigerTag`)
- `web/lib/konto/route.ts`, `sitzung.ts`, `cookies.ts`, `merk-store.ts`, `merk-logik.ts`, `merkliste-events.ts`, `vorlieben.ts`
- `web/components/client.tsx` (TabBar), `web/components/konto.tsx` (`konto()`, `KontoSync`), `web/components/konto-bereich.tsx`, `web/components/merkliste.tsx`, `web/components/interessen-fragebogen.tsx`
- `web/app/api/konto/merkliste/route.ts`, `ich/route.ts`
- `database/konten_stammdaten_2026-11-17.sql`

**Besonders:**
- **Widersprüche zwischen den Abschnitten** 3, 4, 5, 6, 8 und 10. Fenster, Fokustag, Einwilligung, Ersatz „Beliebt“, Datenquellen, Fehlerzustände.
- **Ist alles eindeutig genug zum Bauen?** Wo müsste ein Entwickler raten?
- **Caching:**
  - Kein `cookies()`/`headers()`/`connection()` auf `/`.
  - Kein Personeninhalt im HTML von `/` oder `/?datum=`.
  - `data-konto` nie vom Server.
  - Kein `Set-Cookie` auf `/`.
- **E13:** Sensible Events nie als Eingabe der Punkte, nie als Vorschlag, nie als Begründung, nie in Statistik. Eigene Listen ohne Kennzeichnung. Keine Rückschlüsse über `ohne`, Zählungen oder den Ersatz.
- **Zustände:** abgemeldet, Cookie `0`/`1`, veraltet, Reset-Sitzung, unter 16, Schalter aus, unfertiges Profil, Einwilligung fehlt, 401/403/429/503, Wechsel ohne Neuladen, anderer Tab.
- **Barrierefreiheit:** TabBar, Vorschau B18 (`inert` nur auf den Karten), Zurück-Link, Rückfragen.
- **App-Tauglichkeit:** alle neuen Routen mit Bearer, ohne Cookie-Annahmen.
- **Tests (Abschnitt 10):** Fehlt ein Fall? Verlangt ein Test etwas, das der Code oder der Plan an anderer Stelle ausschließt?

**Wenn du Fehler, Widersprüche, Lücken oder unhaltbare Tests findest:**
- Korrigiere den Plan selbst (**fünfte Fassung**, Kopfzeile und Prüfhistorie ergänzen).
- Das Konzept fasst du nur an, wenn es dem Plan widerspricht.
- Kein Feature-Code, kein Deploy, keine neuen Bibliotheken.

## Bericht (in der Antwort, nicht nur in der Datei)
1. Teil 1: je Punkt „bestätigt“, „angepasst“ (mit Grund) oder „zurückgenommen“ (mit Grund).
2. Teil 2: Befunde nach Schwere (**kritisch / hoch / mittel / gering / Hinweis**), je Befund Planabschnitt, Problem mit Beleg aus Code oder Plan, was du geändert hast.
3. Gesamteinschätzung: „freigabereif“, „freigabereif nach Behebung“ oder „überarbeiten“. Wenn du nichts ändern musstest, sag das ausdrücklich.
