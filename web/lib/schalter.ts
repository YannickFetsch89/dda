// Kleine Schalter ohne Abhängigkeiten – auch in Client-Komponenten nutzbar (kein großer Import ins Browser-Bundle).

/**
 * Spielplatz-Guide verlinkt? Seit 14.11.2026 vorübergehend aus: Die Seiten bleiben live (Sitemap, direkte URLs),
 * aber nichts verlinkt sie, bis die Typ-Illustrationen fertig sind. Der Schalter steuert alle Stellen im Code:
 * Menü und Mobilmenü (components/client.tsx, components/rahmen.tsx), Footer samt Markenabsatz, /guides-Kachel,
 * Übersichtstext und FAQ (lib/guide-texte.ts), Familien-Kategorie, Event- und Stadtteilseiten (lib/landing.ts).
 * Von Hand bleibt nur public/llms.txt (statische Datei): die Spielplatz-Zeile unter „## Guides“ wieder einfügen.
 */
export const SPIELPLAETZE_VERLINKT = false;

/**
 * Weihnachtsmarkt-Guide verlinkt (Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, 5.6)? Während der Saison an, am
 * 02.01.2027 per Commit aus – die Seiten bleiben danach erreichbar und in der Sitemap (E10). Der Schalter steuert:
 * Menü und Mobilmenü (components/client.tsx GUIDE_LINKS, components/rahmen.tsx), Footer-Spalte und Markenabsatz,
 * /guides-Kachel an erster Stelle (app/guides/page.tsx), Kategorie food (app/kategorie/[slug]/page.tsx), Startseiten-Box
 * (app/page.tsx, zusätzlich Datumsfenster 15.11.–30.12.) und die FAQ „Welche Guides kommen noch dazu?“ (lib/guide-texte.ts).
 * Von Hand: public/llms.txt (Zeile „Weihnachtsmärkte“ unter „## Guides“).
 */
export const WEIHNACHTSMAERKTE_VERLINKT = true;

/**
 * Magazin (Plan docs/plan-redaktion-2026-11-19.md, T9) verlinkt UND indexiert? Aus: Die Seiten unter /magazin sind
 * erreichbar, aber noindex,follow, stehen nicht in der Sitemap, der Feed antwortet 404 und kein <head> verlinkt ihn.
 * An (Livegang, Schritt 7): Menü, Footer, Startseite, Sitemap, Feed, Feed-Link im <head>, publishingPrinciples.
 * Von Hand dann: public/llms.txt (Abschnitt „## Magazin“). Die IndexNow-Meldung der Pipeline folgt dem Feed (T6).
 */
// An seit dem Livegang (Schritt 7, 20.11.2026, Auftraggeber: „Yes, build it like this“).
export const MAGAZIN_VERLINKT = true;
