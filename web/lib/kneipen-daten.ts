// Daten für den Kneipen-Hub: Kneipen & Bars plus Restaurants, die zusätzlich hier erscheinen
// (Brauhäuser, Gastropubs – Entscheidung E1). Jeder Ort behält seine EINE URL (ortPfad nach typ).
import { orteLaden } from "./orte";
import type { DddOrt } from "./typen";

export async function kneipenLaden(): Promise<DddOrt[]> {
  const [kneipen, restaurants] = await Promise.all([orteLaden(["kneipe"]), orteLaden(["restaurant"])]);
  return [...kneipen, ...restaurants.filter((o) => o.extras.auch_kneipe === true)];
}

/** Kneipen, die zusätzlich im Restaurant-Hub erscheinen (Brauhäuser und Gastropubs – beide mit Küche). */
export async function brauhaeuserFuerRestaurants(): Promise<DddOrt[]> {
  return (await orteLaden(["kneipe"])).filter((o) => o.extras.auch_restaurant === true);
}
