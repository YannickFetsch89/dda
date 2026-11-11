// Guide-Stadtteilseiten (/guides/{hub}/stadtteil/{slug}): welche Orte gehören zu welchem Hub und Stadtteil.
// Dieselben Ladefunktionen wie die Hubs – nur freigegebene Orte, jeder mit seiner einen kanonischen URL (ortPfad).
import { clubsLaden } from "./clubs-daten";
import { brauhaeuserFuerRestaurants, kneipenLaden } from "./kneipen-daten";
import { MIN_EINTRAEGE, type GuideHub } from "./landing";
import { orteLaden } from "./orte";
import type { DddOrt } from "./typen";

/** Alle Orte eines Hubs, wie der Hub sie zeigt. */
export async function hubOrte(hub: GuideHub): Promise<DddOrt[]> {
  if (hub === "restaurants-cafes") {
    const [eigene, brauhaeuser] = await Promise.all([orteLaden(["restaurant", "imbiss", "cafe"]), brauhaeuserFuerRestaurants()]);
    return [...eigene, ...brauhaeuser];
  }
  if (hub === "kneipen-bars") return kneipenLaden();
  return clubsLaden();
}

/** Stadtteile eines Hubs mit Anzahl, absteigend; nur ab mindestens `ab` Orten. */
export function stadtteileMitOrten(orte: DddOrt[], ab = MIN_EINTRAEGE): { stadtteil: string; anzahl: number }[] {
  const z = new Map<string, number>();
  for (const o of orte) if (o.stadtteil) z.set(o.stadtteil, (z.get(o.stadtteil) ?? 0) + 1);
  return [...z.entries()]
    .filter(([, n]) => n >= ab)
    .map(([stadtteil, anzahl]) => ({ stadtteil, anzahl }))
    .sort((a, b) => b.anzahl - a.anzahl || a.stadtteil.localeCompare(b.stadtteil, "de"));
}
