// Die Guide-Hubs an einer Stelle: Übersicht /guides und Guide-Reihe auf der Startseite (Auftraggeber 27.11.2026).
// Reihenfolge und Texte laut data/guides.json im Design-Handoff; der Saison-Guide steht während der Saison vorne
// (Plan Weihnachtsmärkte 5.6, Schalter in lib/schalter.ts). Kachelbilder: public/guides/<slug>.webp
import { SPIELPLAETZE_VERLINKT, WEIHNACHTSMAERKTE_VERLINKT } from "@/lib/schalter";

export interface Hub {
  slug: string;
  label: string;
  icon: string;
  teaser: string;
  einheit: string;
  fertig: boolean;
}

export const HUBS: Hub[] = [
  ...(WEIHNACHTSMAERKTE_VERLINKT
    ? [{ slug: "weihnachtsmaerkte", label: "Weihnachtsmärkte", icon: "wm:markt", teaser: "Wer heute geöffnet hat – mit Sonderzeiten an den Feiertagen", einheit: "Märkte", fertig: true }]
    : []),
  { slug: "restaurants-cafes", label: "Restaurants & Cafés", icon: "restaurant", teaser: "Die besten Adressen zum Essen und Kaffeetrinken", einheit: "Tipps", fertig: true },
  { slug: "kneipen-bars", label: "Kneipen & Bars", icon: "sports_bar", teaser: "Altbier, Cocktails und gemütliche Ecken", einheit: "Tipps", fertig: true },
  { slug: "clubs", label: "Clubs", icon: "nightlife", teaser: "Düsseldorfs Nachtleben von Techno bis Hip-Hop", einheit: "Tipps", fertig: true },
  { slug: "spielplaetze", label: "Spielplätze", icon: "sp:spielplatz", teaser: "Der perfekte Spielplatz für jedes Alter", einheit: "Plätze", fertig: SPIELPLAETZE_VERLINKT },
  { slug: "ausfluege", label: "Ausflüge", icon: "hiking", teaser: "Raus aus der Stadt – unter einer Stunde erreichbar", einheit: "Ziele", fertig: false },
  { slug: "wochenend-trips", label: "Wochenend-Trips", icon: "local_activity", teaser: "Ein Wochenende weg – unter 4 Stunden Anfahrt", einheit: "Trips", fertig: false },
];

/** Guide-Einträge der Leiste unter dem Kopf (mobil, Auftraggeber 27.11.2026): Restaurants und Cafés getrennt,
 * beide führen in den Restaurant-Guide mit vorgewähltem Filter. `zahl` ist der Schlüssel in guideZahlenLaden. */
export interface LeistenGuide {
  zahl: GuideZahlSchluessel;
  name: string;
  icon: string;
  href: string;
}
export type GuideZahlSchluessel = "weihnachtsmaerkte" | "restaurants" | "cafes" | "kneipen" | "clubs" | "spielplaetze";

export const LEISTEN_GUIDES: LeistenGuide[] = [
  ...(WEIHNACHTSMAERKTE_VERLINKT ? [{ zahl: "weihnachtsmaerkte" as const, name: "Weihnachts­märkte", icon: "wm:markt", href: "/guides/weihnachtsmaerkte" }] : []),
  { zahl: "restaurants", name: "Restaurants", icon: "restaurant", href: "/guides/restaurants-cafes?typ=restaurant" },
  { zahl: "cafes", name: "Cafés", icon: "local_cafe", href: "/guides/restaurants-cafes?typ=cafe" },
  { zahl: "kneipen", name: "Kneipen & Bars", icon: "sports_bar", href: "/guides/kneipen-bars" },
  { zahl: "clubs", name: "Clubs", icon: "nightlife", href: "/guides/clubs" },
  ...(SPIELPLAETZE_VERLINKT ? [{ zahl: "spielplaetze" as const, name: "Spielplätze", icon: "sp:spielplatz", href: "/guides/spielplaetze" }] : []),
];
