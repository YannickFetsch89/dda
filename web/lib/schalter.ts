// Kleine Schalter ohne Abhängigkeiten – auch in Client-Komponenten nutzbar (kein großer Import ins Browser-Bundle).

/**
 * Spielplatz-Guide verlinkt? Seit 14.11.2026 vorübergehend aus: Die Seiten bleiben live (Sitemap, direkte URLs),
 * aber nichts verlinkt sie, bis die Typ-Illustrationen fertig sind. Der Schalter steuert alle Stellen im Code:
 * Menü und Mobilmenü (components/client.tsx, components/rahmen.tsx), Footer samt Markenabsatz, /guides-Kachel,
 * Übersichtstext und FAQ (lib/guide-texte.ts), Familien-Kategorie, Event- und Stadtteilseiten (lib/landing.ts).
 * Von Hand bleibt nur public/llms.txt (statische Datei): die Spielplatz-Zeile unter „## Guides“ wieder einfügen.
 */
export const SPIELPLAETZE_VERLINKT = false;
