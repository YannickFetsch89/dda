# Cursor-Prompt: zweite Prüfung des Plans „Mein dies.das – Stufe 1“ (18.11.2026)

**Erledigt 19.11.2026.** Ergebnis steht in der **dritten Fassung** von `docs/plan-mein-bereich-stufe1-2026-11-18.md`. Diesen Prompt nicht erneut ausführen.

Alles unterhalb der Linie war der ursprüngliche Cursor-Auftrag (Agent-Modus, Repo DD geöffnet).

---

Du prüfst die **zweite Fassung** eines Plans, keinen Code zum Bauen: `docs/plan-mein-bereich-stufe1-2026-11-18.md`. **Ändere keine Dateien. Schreib nur einen Befundbericht.**

Die erste Prüfung hat den Plan gegen den Live-Code gelesen und die zweite Fassung daraus gemacht. Deine Aufgabe ist, diese Fassung erneut kritisch zu prüfen: Was ist noch falsch, widersprüchlich oder zu dünn zum Bauen? Bestätige einen Punkt nur, wenn er zum Code passt. Erfinde keine Befunde.

## Was die erste Prüfung geändert hat (bitte gegen den Code gegenlesen)

1. **Startseite ist nicht „statisch ohne searchParams“.** `web/app/page.tsx` hat `instant = false` und liest `searchParams`. `fokusTag` ist nur gesetzt, wenn `von === bis` (Zeile 97). `beliebtAuswahl` filtert `amFokustag` nur bei `tag !== null`. Der Plan darf kein `cookies()` auf `/` verlangen und kein `s-maxage`, das der Code nicht setzt.
2. **`ddd_konto` hat drei Zustände**, nicht zwei (`web/lib/konto/route.ts`, `hinweisFuer`; `merk-store.ts` `kontomodus` / `hinweisGesetzt`). Fehlt = abgemeldet. `1` = Alter bestätigt. `0` = Alter fehlt oder unter 16 gesperrt. Eine Reset-Sitzung setzt das Cookie nicht (`anmeldung.ts`).
3. **Das Skript muss im Head stehen**, neben `THEME_SCRIPT` (`web/app/layout.tsx`). `body[data-konten]` ist beim Head-Skript noch nicht da. `<html>` hat `suppressHydrationWarning`. `data-konto` darf nicht vom Server ins HTML.
4. **Unter 16:** `konten_stammdaten_2026-11-17.sql` leert `mindestalter_bestaetigt_am` und setzt `unter16_gesperrt_am`. Der Wrapper antwortet dann 403 `mindestalter_fehlt` und setzt `ddd_konto=0`, bevor die Route läuft (`route.ts` um Zeile 179). Eine eigene 403 `unter16_gesperrt` muss `ctx.ohneHinweis` setzen, sonst hängt der Wrapper danach `hinweisFuer` an und würde bei noch gesetztem Mindestalter wieder `ddd_konto=1` schreiben (Zeile 191).
5. **401** löscht beide Cookies über `cookiesLoeschen`. Der Client muss das Attribut selbst wegnehmen. Die Merkliste ruft dafür `lokalAbmelden()` (`merk-store.ts`, `spiegelLaden`). 403 `mindestalter_fehlt` ruft `lokalAbmelden(true)` auf.
6. **`GET /api/konto/merkliste?mit=events` liefert Vergangenheit schon.** `merklisteAufteilen` in `web/lib/konto/merk-logik.ts`. Ein `?vorbei=1` wäre doppelt.
7. **Kontenplan Abschnitt 13** heißt `fuer-euch` / `lib/fuer-euch.ts`. Der Plan ersetzt das durch `fuer-dich` und darf nicht beide bauen.
8. **„Von allem etwas“** speichert alle Kategorie-Slugs außer `sonstiges` (`interessen-fragebogen.tsx`), kein Flag. `KATEGORIEN` in `web/lib/kategorien.ts` hat keinen Slug „Kinder“. `mit-kindern` trifft den Slug `familie`.
9. **Gleichstand** ist `nachEmpfehlung()` in `ableitungen.ts` (Bild, Stufe, am einzelnen Tag der Fokustag, Beliebtheit ohne Flaggen, Hash, Zeit, ID). Nicht ein zweites a)–e) daneben.
10. **Einwilligung (a)** sperrt die Punkte, nicht die eigene Merkliste. „Deine nächsten Events“ und die Zählung kommende/erlebt dürfen eigene sensible Merkungen zeigen, ohne Kennzeichnung und ohne sie als Begründung zu benutzen. `event_sensibel` liest nur `kontoDienstClient()` (`uebernehmen/route.ts`). `ctx.db` darf das nicht.
11. **TabBar** `istAktiv` nutzt `startsWith` (`client.tsx`). Ein Profil-Tab auf `/konto` wäre sonst auch auf `/konto/fuer-dich` aktiv. Hash-Ziele `/konto#…` gibt es im Code nicht. Es gibt `/konto/willkommen?modus=interessen` und `/datenschutz#konto`.
12. **S3:** `TEXT.stammdaten.text` (`texte.ts`) und die Zeile „Name und Geburtsdatum (Pflichtangaben)“ in `datenschutz/konto-abschnitt.tsx` nennen den Namen nur für Ticketkäufe. `profiles.vorname` existiert. `GET /api/konto/ich` liefert den Vornamen schon. Die Oberfläche zeigt ihn erst mit `NAMEN_ANREDE`.
13. **Bearer** liest `sitzungAusAnfrage` schon. GET prüft den Origin nicht.

S1–S7 bleiben bestätigt. Stell sie nicht grundsätzlich in Frage, außer ein Punkt ist rechtlich oder technisch nicht haltbar.

## Bitte lesen
- Plan, zweite Fassung, ganz.
- `docs/konzept-personalisierung-2026-11-18.md` (P1–P7), soweit der Plan davon abweicht.
- Kontenplan: 3.5 Caching, 4.2 `praeferenzen`, 4.4 Einwilligungen, 5.8 und E13, Abschnitt 13, Abschnitt 20.
- Empfehlungs-Plan, Abschnitt 9 (Fokustag, Sortierschlüssel a–e).
- Code nur zur Gegenprobe: `web/app/page.tsx`, `web/app/layout.tsx`, `web/lib/ableitungen.ts` (`beliebtAuswahl`, `nachEmpfehlung`, `amFokustag`), `web/lib/konto/route.ts`, `web/lib/konto/sitzung.ts`, `web/lib/konto/merk-store.ts`, `web/lib/konto/merk-logik.ts`, `web/components/client.tsx` (TabBar), `web/components/merkliste.tsx`, `web/app/api/konto/merkliste/route.ts`, `web/app/api/konto/ich/route.ts`, `web/app/datenschutz/konto-abschnitt.tsx`, `web/lib/konto/texte.ts`.

## Worauf du besonders achten sollst
1. **Widersprüche in der zweiten Fassung selbst.** Abschnitt 4, 5 und 6 müssen dieselbe Fenster-, Fokustag- und Einwilligungsregel sagen. Der Ersatz „Beliebt“ darf nicht einmal persönlich und einmal öffentlich heißen.
2. **Zustände, die immer noch fehlen:** Cookie `0` auf `/merkliste` und in der TabBar, 401, 403 `passwort_setzen_noetig`, 403 `mindestalter_fehlt`, 403 `unter16_gesperrt`, Schalter aus, unfertiges Profil, Einwilligung fehlt, veraltetes Cookie.
3. **Caching:** Kann das Head-Skript vor dem ersten Paint laufen? Schreibt irgendein Schritt Personeninhalt in das HTML von `/` oder `/?datum=`? Ruft die Insel `cookies()` auf der Startseite auf?
4. **E13:** Kann eine Zählung, eine Begründung, `ohne` oder der Ersatz „Beliebt“ verraten, dass ein Event sensibel ist oder dass die Merkliste nur aus sensiblen Events besteht?
5. **API:** Passt `ohne` (Deckel 24, stilles Verwerfen), `datum` über `zeitraumAuflösen`, 503 wenn der Dienst-Client scheitert, Bremslimit je Nutzer, kein `resetErlaubt`? Ist `vorname` wirklich nur bei `NAMEN_ANREDE` in der neuen Antwort, ohne `ich` zu verändern?
6. **Navigation:** Bleiben `/konto`, `/konto/willkommen?modus=interessen`, Mails und `/datenschutz#konto`? Ist der Aktiv-Zustand der TabBar eindeutig, auch für `/konto/willkommen`?
7. **Barrierefreiheit:** `inert` und `aria-hidden` nur auf den Karten, Button erreichbar. Zurück-Link 44 px.
8. **Leistung:** Rechnet die Startseite die Punkte mit, oder nur die API? Ruft ein anonymer Besuch `/api/konto/start` auf?
9. **Tests:** Welcher beschriebene Fall hat keinen Test? Welcher Test prüft etwas, das der Plan an anderer Stelle verbietet?
10. **App später:** Kommt eine Route mit einer Annahme aus, die nur das Cookie kennt und Bearer bricht?

## Bericht
Eine Liste, sortiert nach Schwere (**kritisch / hoch / mittel / gering / Hinweis**). Je Befund: Planabschnitt, Problem mit konkretem Beispiel aus dem Code oder aus einem Widerspruch im Plan, Vorschlag. Was stimmt, steht in einem Satz am Ende, nicht als eigener Befund.

Am Ende eine Gesamteinschätzung: „freigabereif“, „freigabereif nach Behebung“ oder „überarbeiten“.
