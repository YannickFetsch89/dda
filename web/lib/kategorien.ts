// Kategorien laut Brand Identity (data/categories.json) plus "Sonstiges" aus dem DB-Schema
import type { CSSProperties } from "react";
import type { KategorieSlug } from "./typen";

export interface Kategorie {
  slug: KategorieSlug;
  name: string;
  icon: string;
  farbe: string;
  aufFarbe: string;
  tint: string;
  deep: string;
  beschreibung: string;
  unterkategorien: string[];
}

export const KATEGORIEN: Kategorie[] = [
  { slug: "kultur", name: "Kultur", icon: "theater_comedy", farbe: "#6B4A8E", aufFarbe: "#FFFFFF", tint: "#EFE9F5", deep: "#4E3369", beschreibung: "Ausstellungen, Theater, Oper, Film", unterkategorien: ["Ausstellungen", "Theater", "Film"] },
  { slug: "musik", name: "Musik", icon: "music_note", farbe: "#E63946", aufFarbe: "#FFFFFF", tint: "#FDE6E8", deep: "#A3202B", beschreibung: "Konzerte, DJ-Sets, Live-Musik", unterkategorien: ["Konzerte", "DJ-Sets", "Live-Musik"] },
  { slug: "food", name: "Food", icon: "ramen_dining", farbe: "#F4A261", aufFarbe: "#1B2540", tint: "#FDEEE2", deep: "#8A4A17", beschreibung: "Food Events, Märkte, Tastings", unterkategorien: ["Food Events", "Märkte", "Tastings"] },
  { slug: "sport", name: "Sport", icon: "sports_soccer", farbe: "#2A9D8F", aufFarbe: "#1B2540", tint: "#DFF2EF", deep: "#17655C", beschreibung: "Sportevents, Outdoor-Fitness", unterkategorien: ["Spiele", "Laufen", "Fitness"] },
  { slug: "outdoor", name: "Outdoor", icon: "park", farbe: "#4CAF50", aufFarbe: "#1B2540", tint: "#E4F4E5", deep: "#2A6B2D", beschreibung: "Natur, Parks, saisonale Aktivitäten", unterkategorien: ["Natur", "Parks", "Touren"] },
  { slug: "community", name: "Community", icon: "groups", farbe: "#457B9D", aufFarbe: "#FFFFFF", tint: "#E3EDF3", deep: "#2D5670", beschreibung: "Meetups, Networking, Workshops", unterkategorien: ["Meetups", "Networking", "Workshops"] },
  { slug: "nightlife", name: "Nightlife", icon: "nightlife", farbe: "#1B2540", aufFarbe: "#FFFFFF", tint: "#E4E7EF", deep: "#1B2540", beschreibung: "Partys, Clubs, Late-Night", unterkategorien: ["Partys", "Clubs", "Late-Night"] },
  { slug: "familie", name: "Familie", icon: "family_restroom", farbe: "#FFB347", aufFarbe: "#1B2540", tint: "#FFF1DC", deep: "#8A5A00", beschreibung: "Kinder- & Familienevents", unterkategorien: ["Kinder", "Familie", "Basteln"] },
  { slug: "dating", name: "Dating", icon: "favorite", farbe: "#E91E8C", aufFarbe: "#FFFFFF", tint: "#FCE3F1", deep: "#A3125F", beschreibung: "Speed Dating, Singles Events", unterkategorien: ["Speed Dating", "Singles", "Flirt"] },
];

// Nicht Teil des Designs, kommt aber aus der Pipeline. Neutral gestaltet.
const SONSTIGES: Kategorie = { slug: "sonstiges", name: "Sonstiges", icon: "interests", farbe: "#718096", aufFarbe: "#FFFFFF", tint: "#EDF0F4", deep: "#2D3748", beschreibung: "Alles andere", unterkategorien: [] };

const NACH_SLUG = new Map<string, Kategorie>([...KATEGORIEN, SONSTIGES].map((k) => [k.slug, k]));

export function kategorie(slug: string): Kategorie {
  return NACH_SLUG.get(slug) ?? SONSTIGES;
}

/** DB-Wert (z.B. "family") auf Website-Slug abbilden. */
export function kategorieAusDb(wert: string | null | undefined): KategorieSlug {
  const w = (wert ?? "").toLowerCase().trim();
  if (w === "family") return "familie";
  return NACH_SLUG.has(w) ? (w as KategorieSlug) : "sonstiges";
}

/** CSS-Variablen für alle kategoriefarbigen Elemente. */
export function katStil(slug: string): CSSProperties {
  const k = kategorie(slug);
  return { "--k": k.farbe, "--k-on": k.aufFarbe, "--k-tint": k.tint, "--k-deep": k.deep } as CSSProperties;
}
