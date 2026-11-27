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

/** Kurznamen für die Kreisleiste unter dem Kopf (mobil): passen in einen 66 px breiten Kreis-Eintrag */
export const HUB_KURZ: Record<string, string> = {
  weihnachtsmaerkte: "Weihnachts­märkte",
  "restaurants-cafes": "Essen gehen",
  "kneipen-bars": "Kneipen & Bars",
  clubs: "Clubs",
  spielplaetze: "Spielplätze",
};
