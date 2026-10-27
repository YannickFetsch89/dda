// Stadtteil-Clustering: Die Pipeline (pipeline/stadtteil_mapper.py) liefert Stadtteile,
// hier werden sie den 10 Düsseldorfer Stadtbezirken zugeordnet.
// x/y sind grobe Positionen (0–100) für die schematische Karte, Norden oben, Rhein links.

export interface Bezirk {
  nr: number;
  name: string;
  stadtteile: string[];
  x: number;
  y: number;
}

export const BEZIRKE: Bezirk[] = [
  { nr: 1, name: "Innenstadt", stadtteile: ["Altstadt", "Carlstadt", "Stadtmitte", "Pempelfort", "Derendorf", "Golzheim"], x: 43, y: 42 },
  { nr: 2, name: "Flingern & Düsseltal", stadtteile: ["Flingern", "Flingern-Nord", "Flingern-Süd", "Düsseltal"], x: 63, y: 40 },
  { nr: 3, name: "Bilk & Hafen", stadtteile: ["Bilk", "Unterbilk", "Hafen", "Friedrichstadt", "Oberbilk", "Hamm", "Flehe", "Volmerswerth"], x: 45, y: 63 },
  { nr: 4, name: "Linksrheinisch", stadtteile: ["Oberkassel", "Niederkassel", "Heerdt", "Lörick"], x: 18, y: 44 },
  { nr: 5, name: "Norden", stadtteile: ["Stockum", "Lohausen", "Kaiserswerth", "Kalkum", "Angermund", "Wittlaer"], x: 42, y: 13 },
  { nr: 6, name: "Rath & Mörsenbroich", stadtteile: ["Rath", "Unterrath", "Mörsenbroich", "Lichtenbroich"], x: 64, y: 21 },
  { nr: 7, name: "Gerresheim & Grafenberg", stadtteile: ["Gerresheim", "Grafenberg", "Ludenberg", "Hubbelrath", "Knittkuhl"], x: 84, y: 33 },
  { nr: 8, name: "Eller & Lierenfeld", stadtteile: ["Eller", "Lierenfeld", "Vennhausen", "Unterbach"], x: 74, y: 60 },
  { nr: 9, name: "Benrath & Wersten", stadtteile: ["Benrath", "Wersten", "Holthausen", "Hassels", "Reisholz", "Himmelgeist", "Itter", "Urdenbach"], x: 60, y: 79 },
  { nr: 10, name: "Garath & Hellerhof", stadtteile: ["Garath", "Hellerhof"], x: 68, y: 93 },
];

const BEZIRK_VON = new Map<string, Bezirk>();
BEZIRKE.forEach((b) => b.stadtteile.forEach((s) => BEZIRK_VON.set(s.toLowerCase(), b)));

export function bezirkVon(stadtteil: string | null | undefined): Bezirk | null {
  if (!stadtteil) return null;
  return BEZIRK_VON.get(stadtteil.toLowerCase()) ?? null;
}

// Anzeigenamen, wo der DB-Wert nicht der gebräuchliche Name ist
const ANZEIGE: Record<string, string> = { Hafen: "Medienhafen" };

export function stadtteilName(stadtteil: string): string {
  return ANZEIGE[stadtteil] ?? stadtteil;
}

export const OHNE_ZUORDNUNG = "Ohne Zuordnung";
