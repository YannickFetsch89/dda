// Anzahl je Guide für die Leiste unter dem Kopf (Auftraggeber 27.11.2026). Die Leiste steht im Layout, also auf jeder
// Seite: Gecacht wird nur das kleine Zahlen-Objekt, nicht die Ortslisten (Speicher, vgl. Ausfall 23.11.2026).
// Gezählt wird genau das, was der jeweilige Link zeigt.
import { cacheLife, cacheTag } from "next/cache";
import { ORTE_CACHE_TAG, orteLaden } from "./orte";
import { brauhaeuserFuerRestaurants, kneipenLaden } from "./kneipen-daten";
import { clubsLaden } from "./clubs-daten";
import { spielplaetzeLaden } from "./spielplaetze-daten";
import { weihnachtsmaerkteLaden } from "./weihnachtsmaerkte-daten";
import { heroZahlen } from "./weihnachtsmaerkte";
import type { GuideZahlSchluessel } from "./guide-hubs";

export type GuideZahlen = Partial<Record<GuideZahlSchluessel, number>>;

export async function guideZahlenLaden(): Promise<GuideZahlen> {
  "use cache";
  cacheTag(ORTE_CACHE_TAG); // Admin-Bereich leert ihn nach Änderungen an Orten
  const zahlen = await zaehlen();
  // Nach einem Fehler bald neu versuchen, sonst wie die Ortslisten
  cacheLife(zahlen ? { stale: 300, revalidate: 600, expire: 3600 } : { stale: 30, revalidate: 60, expire: 120 });
  return zahlen ?? {};
}

async function zaehlen(): Promise<GuideZahlen | null> {
  try {
    const [restaurants, brauhaeuser, cafes, kneipen, clubs, spielplaetze, maerkte] = await Promise.all([
      orteLaden(["restaurant"]), brauhaeuserFuerRestaurants(), orteLaden(["cafe"]), kneipenLaden(), clubsLaden(),
      spielplaetzeLaden(), weihnachtsmaerkteLaden(),
    ]);
    return {
      // ?typ=restaurant zeigt auch die Brauhäuser aus dem Kneipen-Hub (sie zählen dort als Restaurant)
      restaurants: restaurants.length + brauhaeuser.length,
      cafes: cafes.length,
      kneipen: kneipen.length,
      clubs: clubs.length,
      spielplaetze: spielplaetze.length,
      weihnachtsmaerkte: heroZahlen(maerkte).anzahl,
    };
  } catch (e) {
    // Ohne Zahlen bleibt die Leiste trotzdem nutzbar
    console.error("Guide-Zahlen für die Leiste konnten nicht geladen werden:", e);
    return null;
  }
}
