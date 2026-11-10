// Suche über die Orte der Guides (Restaurants, Cafés, Imbisse, Kneipen & Bars) – für /entdecken?q=…
// Treffer im Namen zuerst, danach Küche und Art („italienisch“, „Brauhaus“, „Cocktailbar“).
import { kueche } from "./guide-filter";
import { artInfo } from "./kneipen";
import type { DddOrt } from "./typen";

/** Vergleichsform: klein, Umlaute ausgeschrieben, nur Buchstaben/Ziffern („Café Ö-Bar“ → „cafeoebar“). */
export function suchform(text: string): string {
  return text
    .toLowerCase()
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .normalize("NFKD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]/g, "");
}

function zusatz(o: DddOrt): string {
  return [kueche(o)?.name, o.typ === "kneipe" ? artInfo(o).label : null, o.untertitel].filter(Boolean).join(" ");
}

/** Orte zum Suchbegriff, nach Güte sortiert (Name beginnt mit > Name enthält > Küche/Art). */
export function orteSuchen(orte: DddOrt[], q: string | undefined): DddOrt[] {
  const s = suchform(q ?? "");
  if (s.length < 2) return [];
  const bewertet: { o: DddOrt; guete: number }[] = [];
  for (const o of orte) {
    const name = suchform(o.name);
    const guete = name.startsWith(s) ? 3 : name.includes(s) ? 2 : suchform(zusatz(o)).includes(s) ? 1 : 0;
    if (guete) bewertet.push({ o, guete });
  }
  return bewertet
    .sort((a, b) => b.guete - a.guete || (b.o.qualitaets_score ?? 0) - (a.o.qualitaets_score ?? 0))
    .map((x) => x.o);
}
