# Cursor-Prompt: Prüfung der Umsetzung „Mein dies.das – Stufe 1“, Schritte 1–4 (19.11.2026)

Alles unterhalb der Linie in Cursor einfügen (Agent-Modus, Repo DD geöffnet, Branch `claude/setup-project-structure-5QNOf`).

---

Du prüfst die **Umsetzung** des freigegebenen Plans `docs/plan-mein-bereich-stufe1-2026-11-18.md` (fünfte Fassung, Commit d0e21d3). Claude Code hat die Schritte 1 bis 4 gebaut. Der Stand ist **lokal und nicht committet**. Du liest also den Arbeitsstand der Dateien, nicht einen Commit.

**Wichtig:**
- **Du änderst keinen Code** und keine Datei außer deinem Bericht. Im selben Ordner arbeiten andere Sitzungen. Claude Code behebt deine Befunde danach.
- Im Arbeitsstand liegen auch fremde, nicht committete Änderungen anderer Vorhaben. Die prüfst du **nicht**: `web/lib/seo.ts`, `web/proxy.ts`, `web/lib/pfad-pruefung.ts`, `web/lib/schalter.ts`, `web/app/guides/**`, `web/app/reihe/**`, `web/app/event-melden/**`, `scraper/**`, `data/**`, Weihnachtsmarkt- und Blog-Dateien.
- Erfinde keine Befunde. Jeder Befund braucht eine Stelle (Datei:Zeile) und ein konkretes Szenario: Eingabe oder Zustand → falsches Ergebnis.
- Die Entscheidungen S1–S7 und E13 stehen fest. Stell sie nur in Frage, wenn etwas rechtlich oder technisch unhaltbar ist.

**Die Prüfhistorie am Ende des Plans** (Abschnitt 13, Einträge „Schritt 1 gebaut“ bis „Schritt 4 gebaut“) beschreibt, was gebaut wurde und wo Claude Code vom Plan abweicht. Lies sie zuerst.

## Was gebaut wurde (Dateien)

**Schritt 1: Rechnung**
- `web/lib/fuer-dich.ts` (neu): Fenster, Kandidaten, Punkte, Deckel, Startliste, Ersatz „Beliebt“, Seite „Für dich“
- `web/tests/fuer-dich.test.ts` (neu)

**Schritt 2: API und Kontozustand**
- `web/lib/konto/mein-bereich.ts` (neu): Sensibel-Menge mit Cache, Merkliste mit `gemerkt_am`, Eingabe, `ohne`, Abwehr `unter16_gesperrt`
- `web/app/api/konto/start/route.ts`, `web/app/api/konto/fuer-dich/route.ts`, `web/app/api/konto/uebersicht/route.ts` (neu)
- `web/lib/konto/route.ts`: Hinweis-Cookie nur bei `quelle === "cookie"`
- `web/lib/konto/konfig.ts`: `NAMEN_ANREDE = false`
- `web/lib/konto/merk-store.ts`: `kontoAttributAbgleichen()`, `KONTO_EVENT`, `kontoZustand()`
- `web/components/konto.tsx`: Abgleich in `konto()` und `KontoSync` (Start, Fokus vor der `kontomodus()`-Sperre, Pfadwechsel in eigener Suspense-Grenze)
- `web/components/merkliste.tsx`: Abgleich nach dem eigenen Fetch
- `web/tests/mein-bereich.test.ts`, `web/tests/konto-attribut.test.ts` (neu)

**Schritt 3: Seiten und Navigation**
- `web/components/mein-bereich.tsx` (neu): Übersicht `/konto`, `/konto/fuer-dich`, `/konto/erlebt`
- `web/components/konto-bereich.tsx`: `KontoHuelle`, `/konto/einstellungen`, `/konto/datenschutz`, `/konto/interessen` (Chips), Einwilligungen aufgeteilt
- `web/components/konto-nav.tsx` (neu): Seitenleiste
- `web/app/konto/rahmen.tsx` (`KontoRaster`, Zurück-Pfeil, `breit`), `web/app/konto/page.tsx`, neue Seiten unter `web/app/konto/{fuer-dich,erlebt,interessen,einstellungen,datenschutz}/page.tsx`, `web/app/konto/fragebogen-daten.ts` (aus `willkommen/page.tsx` herausgezogen)
- `web/app/merkliste/page.tsx` (Seitenleiste), `web/components/merkliste.tsx` („Erlebt (n) →“ nur bei `data-konto="1"`)
- `web/components/client.tsx`: zwei TabBars, `istAktivKonto`, `useKontoZustand` (aus `konto.tsx` hierher verschoben, Ring-Import)
- `web/components/karten.tsx`: `EventKarte` mit `grund`, `KompaktKarte` mit `mitId`
- `web/components/interessen-fragebogen.tsx`: `MERKMALE`, `ORTE` exportiert
- `web/app/globals.css`: Abschnitte „Mein dies.das (Plan Mein Bereich 3)“ und „Startseite angemeldet und Vorschau B18“ am Ende
- `web/tests/tabbar-aktiv.test.ts` (neu)

**Schritt 4: Startseite**
- `web/lib/konto/kopf-skript.ts` (neu) und `web/app/layout.tsx`: Head-Skript für `html[data-konto]`, nur bei `kontenAktiv()`
- `web/app/page.tsx`: `StartVorschau` (B18), Insel in eigener Suspense-Grenze, `data-start-gezeigt` / `data-event-id` an Tipp und Picks
- `web/components/start-persoenlich.tsx` (neu): Insel `StartPersoenlich`, Links der Vorschau
- `web/app/api/konto/start/route.ts`: zusätzlich `heute`

## Abweichungen vom Plan, die Claude Code bewusst gemacht hat (bitte bewerten)
1. `GET start` und `GET fuer-dich` liefern zusätzlich `heute` (aus dem Pool), damit die Karten „Heute“/„Morgen“ schreiben können. Nicht persönlich.
2. `GET start` antwortet 503, wenn schon die **Merkliste** nicht lesbar ist (sonst ließen sich gemerkte Events nicht ausschließen). Der Plan nannte 503 nur für die Sensibel-Menge.
3. Nach „Interessen ändern“ (`/konto/willkommen?modus=interessen`) geht es zurück auf `/konto/interessen` statt `/konto`.
4. Die Insel rendert im abgemeldeten Zustand einen leeren Platzhalter (`start-platzhalter`). CSS zeigt ihn nur bei `html[data-konto="1"]`. Grund: `/` ist dynamisch, der Server löst die Suspense-Grenze der Insel selbst auf; ohne diesen Platzhalter fehlte die reservierte Höhe vor der Hydration.
5. Seitenleiste und Zurück-Pfeil erscheinen auch auf den öffentlichen Konto-Seiten (Anmelden usw.), wenn `data-konto="1"` gilt. Der Plan sagt „auf allen `/konto/*`-Seiten“.
6. Auf `/konto/datenschutz` stehen beide bisherigen Export-Links (Button „Deine Daten herunterladen“ und der Art.-15-Satz), gleiche Datei.
7. Die Interessen-Chips zeigen „Von allem etwas“ als einen Chip, wenn alle Kategorien gespeichert sind.

## Was du prüfst

**Gegen den Plan:**
- Abschnitt 3.0 (Zustände), 3.1–3.9, 4.1–4.3, 5, 6, 8, 10. Fehlt etwas, ist etwas anders gebaut als beschrieben, oder widerspricht der Code dem Plan?

**Korrektheit:**
- **Rechnung (`fuer-dich.ts`):** Punkte, Mindestpunkte, „Von allem etwas“, Fokustag je Modus, Langläufer, Deckel beim Füllen, kein Nachschub, Ersatz nur mit Einwilligung und nicht leerer Kandidatenmenge, Abschnitte ohne Doppelte, Bezugs-Event (Gleichstand `gemerkt_am`, dann `event_id`), Wochenende über `wochenende()`.
- **Routen:** 401/403/404/429/503 wie in 3.0 und 6. `ohne` gekappt und still gefiltert. Bearer ohne `Set-Cookie` des Hinweises. `vorname` nur bei `NAMEN_ANREDE`.
- **Kontozustand:** Gibt es einen Weg, auf dem `ddd_konto` sich ändert und `html[data-konto]` nicht nachzieht? Liest eine Server-Momentaufnahme irgendwo `document` oder das Cookie? Kann es eine Hydrationsabweichung geben?
- **Insel (`start-persoenlich.tsx`):** Lädt sie nur bei `1`? Kein Abruf bei `0` und abgemeldet. Kein Wiederholen desselben Fehlschlags. Neuer Abruf bei anderem `datum`. Reset-Sitzung ohne `lokalAbmelden`. `ohne` nur aus `[data-start-gezeigt] [data-event-id]`, höchstens 5, keine Geräte-IDs.
- **Seiten:** `KontoHuelle` (401, Reset → `/konto/passwort-neu`, gesperrt). Unfertiges Profil. Erlebt: Gruppierung nach Monat, Herz entfernt. Merkliste: „Erlebt“ nur bei `1`, „Vorbei“ bei `0` und abgemeldet.
- **TabBar:** genau eine Leiste sichtbar und fokussierbar, Aktiv-Regeln aus 3.9.

**Datenschutz und E13:**
- Kein Feld `sensibel`, keine Punkte, keine Nutzer-ID in Antworten. Sensible Events nie vorgeschlagen, nie als Begründung, nie als Bezugs-Event. Eine leere Seite oder der Ersatz verrät nichts über sensible Merkungen.
- Sensibel-Menge nur über `kontoDienstClient()`, Cache-Schlüssel ohne Nutzerbezug, Fehler nicht gecacht.

**Caching der Startseite:**
- Kein `cookies()`, `headers()` oder `connection()` auf `/` und in der Insel. Kein Personeninhalt und kein `data-konto` im Server-HTML. Kein `Set-Cookie` auf `/` und `/?datum=…`. Die Cache-Köpfe von `/` sollen gleich bleiben (lokal und live: `private, no-cache, no-store, max-age=0, must-revalidate`).

**Barrierefreiheit:**
- Vorschau B18: `aria-hidden` und `inert` nur auf dem Karten-Container, Button und Link bedienbar. Bei `0`/`1` ganz `display: none`.
- Zurück-Pfeil ≥ 44 px mit `aria-label`. Seitenleiste mit `aria-current`. Überschriften-Reihenfolge auf den neuen Seiten.

**Tests:**
- Decken die Tests die Fälle aus Plan Abschnitt 10 ab? Welche fehlen? Prüfen sie das Richtige, oder nur, dass etwas zurückkommt?
- Bitte selbst ausführen: im Ordner `web` `npx vitest run` und `npx tsc --noEmit -p .`. Stand bei Claude Code: alles grün (531 Tests).

**Vom Browser aus geprüft hat Claude Code** (ohne echtes Konto, API-Antworten im Browser simuliert):
- Umschalten der Leisten ohne Neuladen, Aktiv-Zustände, Seitenleiste, „Erlebt“/„Vorbei“
- Startseite abgemeldet (Vorschau, kein Abruf), angemeldet (beide Module, Begründung), ohne Einwilligung, Ersatz, 429, 401, Reset-Sitzung, Datumswechsel

**Mit einem echten Konto nicht geprüft.** Falls du das Ergebnis mit echten Daten nachvollziehen kannst, sag es, sonst nur Code-Lesen.

## Bericht (in der Antwort)
1. **Befunde nach Schwere** (kritisch / hoch / mittel / gering / Hinweis). Je Befund: Datei:Zeile, Problem, konkretes Szenario, Beleg (Plan-Abschnitt oder Code), Vorschlag zur Behebung.
2. **Abweichungen 1–7:** je Punkt „in Ordnung“ oder „ändern“ mit Grund.
3. **Fehlende Tests** als Liste.
4. **Gesamteinschätzung:** „bereit für Schritt 6 (Deploy) nach Behebung der Befunde“, „bereit“ oder „überarbeiten“. Wenn du nichts findest, sag das ausdrücklich.
