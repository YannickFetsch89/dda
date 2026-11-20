# Cursor-Prompt: Gesamtprüfung „Mein dies.das – Stufe 1“ auf live (19.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD geöffnet, Branch `claude/setup-project-structure-5QNOf`).

**Vorbereitung durch den Auftraggeber (vor dem Einfügen):**
- Ein **eigenes Testkonto** auf https://diesdas.events anlegen (nicht das Hauptkonto). Onboarding abschließen, Interessen angeben (z. B. Musik und ein Stadtteil), alle Einwilligungen außer „sensible Events“ setzen, zwei kommende Events merken. „Erlebt“ füllt sich erst, wenn ein gemerktes Event vorbei ist; ist die Liste leer, prüft Cursor nur den Leer-Zustand.
- In Cursors Browser selbst anmelden, wenn Cursor danach fragt. Cursor gibt kein Passwort ein.

---

Du prüfst die **komplette Umsetzung** von „Mein dies.das – Stufe 1“ auf dies.das.düsseldorf. Sie ist auf https://diesdas.events live:
- Commit `1d541ec`: Schritte 1–4 (Rechnung, Routen, Seiten, Navigation, TabBar, Startseite).
- Commit `c15887f`: Schritt 5 (Anrede mit Vornamen, Widerrufssätze per du als neue Textversionen).

Der Schalter `KONTEN_AKTIV=1` ist an. Eine Prüfung des gebauten Stands vor dem Deploy hat es schon gegeben (Befunde behoben). Jetzt geht es um den **Live-Stand im echten Betrieb**, mit einem echten Konto.

**Regeln:**
- **Ändere keinen Code, keine Datenbank und keine Datei außer deinem Bericht.**
- Live schonend: höchstens rund 60 Anfragen an `/api/konto/*` insgesamt, keine Last- oder Brute-Force-Tests, keine fremden Konten.
- **Kein neues Konto anlegen.** Nutze nur das Testkonto, mit dem der Auftraggeber dich im Browser anmeldet. Gib selbst kein Passwort ein.
- Am Testkonto darfst du Einstellungen umschalten und Events merken oder entfernen. Stelle am Ende den Ausgangszustand wieder her (Interessen, Einwilligungen, Merkliste). **Das Konto nicht löschen, Mailadresse und Passwort nicht ändern.**
- Erfinde keine Befunde. Jeder Befund braucht einen Ort (Datei:Zeile oder URL) und ein Szenario zum Nachstellen.

## Grundlagen (zuerst lesen)
- **Plan:** `docs/plan-mein-bereich-stufe1-2026-11-18.md`, fünfte Fassung. Verbindlich sind die Abschnitte 2 (S1–S7), 3 (3.0 Zustände, 3.1–3.9 Seiten und Navigation), 4 (Startseite, B18), 5 (Rechnung), 6 (API), 8 (Datenschutz, E13) und 10 (Tests). Abschnitt 13 ist die Prüfhistorie mit allen Abweichungen und Nachträgen.
- **Vorige Prüfung:** `docs/cursor-pruefung-mein-bereich-umsetzung-2026-11-19.md`. Die dort gefundenen Befunde 1–3 sind laut Historie behoben; bitte gegenprüfen.
- **Diff:** `git show 1d541ec` und `git show c15887f`.
- **Wichtigste Dateien:**
  - `web/lib/fuer-dich.ts`, `web/lib/konto/mein-bereich.ts`
  - `web/app/api/konto/{start,fuer-dich,uebersicht}/route.ts`, `web/lib/konto/route.ts`
  - `web/lib/konto/merk-store.ts`, `web/lib/konto/kopf-skript.ts`, `web/app/layout.tsx`
  - `web/components/{mein-bereich,konto-bereich,konto-nav,start-persoenlich,client,konto,merkliste,karten}.tsx`
  - `web/app/page.tsx`, `web/app/konto/**`, `web/app/merkliste/page.tsx`, `web/app/globals.css` (Abschnitte „Mein dies.das“ und „Startseite angemeldet“)
- **Texte:** `web/lib/konto/texte.ts`, `web/lib/konto/konfig.ts` (`TEXTVERSIONEN`, `NAMEN_ANREDE = true`), `docs/einwilligungstexte-2026-11-17.md` (Nachtrag 19.11.), `database/einwilligungstexte_2026-11-19.sql` (ausgeführt, Kontrolle 3× „ok“), `web/app/datenschutz/konto-abschnitt.tsx`.
- **Betrieb:** nginx leitet an Next auf `localhost:3847` weiter. Die Startseite `/` ist dynamisch (searchParams) und hat `Cache-Control: private, no-cache, no-store, max-age=0, must-revalidate`; das war vor Stufe 1 schon so.

## Teil A: Live ohne Anmeldung (curl oder privates Browserfenster)
1. **Startseite `/` und `/?datum=morgen`:**
   - Kein `Set-Cookie`. Cache-Köpfe wie oben.
   - Im HTML: kein `data-konto`, keine Personendaten. Das Head-Skript (`ddd_konto=([01])`) ist da.
   - Vorschau „Für dich empfohlen“ mit Schloss-Kasten, „Kostenlos registrieren“ und „Schon ein Konto? Anmelden“. `weiter` zeigt auf die aktuelle Start-URL.
   - Die verschwommenen Karten sind nicht fokussierbar (Tab-Taste) und nicht anklickbar.
   - Netzwerk: kein Abruf von `/api/konto/start`.
2. **Neue Seiten:** `/konto`, `/konto/fuer-dich`, `/konto/erlebt`, `/konto/interessen`, `/konto/einstellungen`, `/konto/datenschutz` → 200, `X-Robots-Tag: noindex`, abgemeldet der Hinweis „Du bist nicht angemeldet“.
3. **APIs abgemeldet:** `GET /api/konto/start`, `/fuer-dich`, `/uebersicht` → 401, `Cache-Control: private, no-store`.
4. **Cookie `ddd_konto=0` gesetzt, ohne Sitzung:** keine Vorschau, kein Platzhalter, kein Abruf von `/api/konto/start`, heutige TabBar.
5. **Veraltetes Cookie `ddd_konto=1` ohne Sitzung:** Nach dem Laden wird abgeräumt (Cookie und `html[data-konto]` weg), dann erscheint die Vorschau. Kein Abruf in Schleife.
6. **`robots.txt` und `sitemap.xml`:** keine neuen `/konto`-Pfade.
7. **`/datenschutz`:** beim Namen „… und für die persönliche Anrede auf der Website und in der App“.

## Teil B: Live mit dem Testkonto (Browser, Desktop und Handybreite 375 px)
1. **Erster Paint:** Neu laden mit Cookie `1`. Keine Vorschau sichtbar, auch nicht kurz. Der Platzhalter hält Platz frei, dann kommen die Module. Unten mobil genau eine Leiste (Start · Entdecken · Für dich · Merkliste · Profil).
2. **Startseite:**
   - „Für dich empfohlen“ mit Begründungszeile je Karte, Link „Alle Vorschläge“, Unterzeile „Hallo <Vorname>“.
   - „Deine nächsten Events“ mit den gemerkten kommenden Events.
   - Keine Karte doppelt mit „Tipp und Picks“. Kein gemerktes Event unter den Vorschlägen.
   - Datum wechseln (Chips „Morgen“, „Dieses Wochenende“, Datumsleiste): neuer Abruf je Datum, kein doppelter.
   - `/?datum=` mit einem **vergangenen** Tag: „Für dich empfohlen“ fehlt, kein „Beliebt“; „Deine nächsten Events“ bleibt.
3. **Übersicht `/konto`:** „Mein dies.das“, Mailadresse klein, Kacheln Für dich / Merkliste / Erlebt / Interessen mit plausiblen Zahlen, Links „Konto und Sicherheit“ und „Datenschutz“. Kein Zurück-Pfeil.
4. **`/konto/fuer-dich`:** Abschnitte nur mit Treffern, jedes Event nur einmal, Begründung je Karte. Kein „Beliebt“-Ersatz auf dieser Seite.
5. **`/konto/erlebt`:** Gibt es vergangene Merkungen: nach Monat gruppiert, neueste zuerst; das Herz entfernt sofort (danach wieder merken, Ausgangszustand). Gibt es keine: Leer-Zustand „Noch nichts erlebt.“ mit Link zur Merkliste.
6. **`/merkliste`:** Bei vergangenen Merkungen „Erlebt (n) →“ statt „Vorbei“. Am Desktop Seitenleiste mit „Merkliste“ aktiv.
7. **`/konto/interessen`:** Chips mit Namen statt Slugs. „Interessen ändern“ führt in den Fragebogen und danach zurück auf `/konto/interessen`. Schalter (a): Beim Abschalten erscheint die Rückfrage; **„Interessen behalten“ wählen**, nicht löschen.
8. **`/konto/datenschutz`:** (b), (c), (d) mit gestuften Texten. Unter „Mehr dazu“: „Du kannst das jederzeit im Konto widerrufen. Dann werden sie aus deinem Konto entfernt.“ und „Du kannst das jederzeit im Konto oder über den Abmeldelink in jeder Mail widerrufen.“ Bei (a) auf `/konto/interessen`: „Du kannst das jederzeit im Konto widerrufen. Dann werden deine Antworten sofort gelöscht.“
   - Eine Einwilligung kurz umschalten und zurück (z. B. die Geburtstagsmail). Beides muss klappen (neue Textversionen in der Datenbank). Die Netzwerk-Antwort darf keine Fehlermeldung enthalten.
   - Export „Deine Daten herunterladen“: In der Datei steht beim Zweck der Pflichtangaben „persönliche Anrede“. Die Einwilligungen nennen die neuen Versionen nur dort, wo du gerade umgeschaltet hast.
9. **`/konto/einstellungen`:** die bisherigen Abschnitte (Mailadresse, Über dich, Passwort, Abmelden, Löschen) vollständig. **Nichts davon ausführen.** Der Hinweis unter „Über dich“ enthält „und um dich persönlich anzusprechen“.
10. **TabBar und Seitenleiste:**
    - „Für dich“ aktiv nur auf `/konto/fuer-dich`.
    - „Profil“ aktiv auf `/konto`, `/konto/einstellungen`, `/konto/datenschutz`, `/konto/interessen`, `/konto/erlebt`, `/konto/willkommen`.
    - Auf `/konto/anmelden` usw. kein Tab aktiv.
    - Nur eine Leiste per Tab-Taste erreichbar.
    - Mobil der Zurück-Pfeil (≥ 44 px) auf allen Unterseiten außer `/konto`.
11. **Ohne Neuladen:**
    - In einem zweiten Tab abmelden („Auf diesem Gerät abmelden“), zurück in den ersten Tab (Fokus): Module weg, Vorschau da, heutige TabBar.
    - Wieder anmelden (der Auftraggeber tippt), zurück auf `/`: Module ohne Neuladen.
12. **Netzwerk:** Konto-Anfragen nur an `/api/konto/*`, keine an `supabase.co` oder andere Dritte. Antworten von `start`, `fuer-dich`, `uebersicht` ohne Feld `sensibel`, ohne Punkte, ohne Nutzer-ID.

## Teil C: Code (Gesamtstand, nicht nur der letzte Diff)
- **Rechnung (`fuer-dich.ts`):** gegen Abschnitt 5, inklusive der Korrektur „vergangener Tag hat keine Kandidaten“.
- **E13:** sensible Events nie als Vorschlag, nie als Begründung oder Bezugs-Event. Die leere Seite und der Ersatz verraten nichts. Die Sensibel-Menge nur über `kontoDienstClient()`, Fehler nicht gecacht.
- **Zustände (3.0):** jeder Weg, der `ddd_konto` ändert, zieht `html[data-konto]` nach. Server-Momentaufnahmen lesen nie `document` oder Cookies. `hidden` an TabBar und Seitenleiste erst nach der Hydration.
- **Wrapper:** Hinweis-Cookie nur bei Cookie-Sitzung. Reset-Sitzung → 403 `passwort_setzen_noetig` an allen neuen Routen.
- **Texte:**
  - Konto-Oberfläche per du und „Button“; Datenschutzerklärung in Sie-Form.
  - Die drei neuen Textversionen sind konsistent in `texte.ts`, `TEXTVERSIONEN`, im SQL (Prüfsummen) und in `docs/einwilligungstexte-2026-11-17.md`.
  - Der Satz „Ich willige … Du kannst …“ wechselt bewusst die Person (Wunsch des Auftraggebers). Kein Befund, nur ein Hinweis, falls rechtlich etwas dagegen spricht.
- **Tests:** im Ordner `web` `npx vitest run` und `npx tsc --noEmit -p .` ausführen (Stand: grün). Fehlende Tests zu Fällen aus Abschnitt 10 auflisten.

## Bericht (in der Antwort)
1. **Befunde nach Schwere** (kritisch / hoch / mittel / gering / Hinweis). Je Befund: Ort, was passiert (mit Schritten oder Anfrage zum Nachstellen), warum es ein Problem ist (Planabschnitt), Vorschlag.
2. **Teil A und B als Prüfliste:** je Punkt „ok“, „Befund n“ oder „nicht geprüft“ (mit Grund).
3. **Gegenprüfung der Befunde 1–3 der vorigen Prüfung:** behoben ja/nein.
4. **Ausgangszustand des Testkontos wiederhergestellt:** ja/nein, was abweicht.
5. **Gesamteinschätzung:** „kann so live bleiben“, „kann live bleiben, Befunde zeitnah beheben“ oder „zurücknehmen“ (mit Grund). Wenn du nichts findest, sag das ausdrücklich.
