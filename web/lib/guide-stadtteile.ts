// Guide-Stadtteilseiten (/guides/{hub}/stadtteil/{slug}): welche Orte gehören zu welchem Hub und Stadtteil.
// Dieselben Ladefunktionen wie die Hubs – nur freigegebene Orte, jeder mit seiner einen kanonischen URL (ortPfad).
import { clubIndexierbar } from "./clubs";
import { clubsLaden } from "./clubs-daten";
import { clubKanonischerPfad } from "./clubs-json-ld";
import { ortPfad } from "@/components/ort-karten";
import { brauhaeuserFuerRestaurants, kneipenLaden } from "./kneipen-daten";
import { MIN_EINTRAEGE, kanonischerStadtteil, type GuideHub } from "./landing";
import { orteLaden } from "./orte";
import { spielplaetzeLaden } from "./spielplaetze-daten";
import type { DddOrt } from "./typen";

/** Alle Orte eines Hubs, wie der Hub sie zeigt. */
export async function hubOrte(hub: GuideHub): Promise<DddOrt[]> {
  if (hub === "restaurants-cafes") {
    const [eigene, brauhaeuser] = await Promise.all([orteLaden(["restaurant", "imbiss", "cafe"]), brauhaeuserFuerRestaurants()]);
    return [...eigene, ...brauhaeuser];
  }
  if (hub === "kneipen-bars") return kneipenLaden();
  if (hub === "spielplaetze") return spielplaetzeLaden(); // ausdrücklicher Zweig, kein Rückfall auf Clubs (Plan 5.1)
  return clubsLaden();
}

/**
 * Zählt der Ort für die Index-Schwelle der Guide-Stadtteilseiten? Im Club-Hub nur Stufe A/B – Stufe C steht auf der
 * Seite, ist aber noindex und darf allein keine Stadtteilseite in den Index bringen (Cursor-Review 12.11.2026).
 */
export const zaehltFuerIndex = (hub: GuideHub) => (hub === "clubs" ? clubIndexierbar : () => true);

/** Indexierbare Guide-Stadtteile eines Hubs (ab MIN_EINTRAEGE zählenden Orten). */
export const stadtteileImHub = (hub: GuideHub, orte: DddOrt[]) => stadtteileMitOrten(orte, MIN_EINTRAEGE, zaehltFuerIndex(hub));

/** Kanonische URL eines Orts im Hub (Club-Hub: Club-Seite bzw. Haupt-URL bei auch_club, siehe clubKanonischerPfad). */
export const hubOrtPfad = (hub: GuideHub, o: DddOrt) => (hub === "clubs" ? clubKanonischerPfad(o) : ortPfad(o));

/** Orte eines Hubs in einem (kanonischen) Stadtteil – Rohwerte wie „Medienhafen“ zählen zu „Hafen“. */
export function orteImStadtteil(orte: DddOrt[], stadtteil: string): DddOrt[] {
  return orte.filter((o) => kanonischerStadtteil(o.stadtteil) === stadtteil);
}

/**
 * Stadtteile eines Hubs mit Anzahl, absteigend; nur ab mindestens `ab` Orten. Gruppiert nach dem kanonischen
 * Stadtteil, Rohwerte ohne eigene Seite fallen weg – dieselbe Regel wie Proxy und Seite.
 * `zaehlt`: welche Orte die Schwelle füllen (Club-Hub: nur indexierbare, Stufe A/B); `anzahl` zählt alle.
 */
export function stadtteileMitOrten(
  orte: DddOrt[], ab = MIN_EINTRAEGE, zaehlt: (o: DddOrt) => boolean = () => true,
): { stadtteil: string; anzahl: number }[] {
  const z = new Map<string, { alle: number; schwelle: number }>();
  for (const o of orte) {
    const st = kanonischerStadtteil(o.stadtteil);
    if (!st) continue;
    const w = z.get(st) ?? { alle: 0, schwelle: 0 };
    w.alle += 1;
    if (zaehlt(o)) w.schwelle += 1;
    z.set(st, w);
  }
  return [...z.entries()]
    .filter(([, w]) => w.schwelle >= ab)
    .map(([stadtteil, w]) => ({ stadtteil, anzahl: w.alle }))
    .sort((a, b) => b.anzahl - a.anzahl || a.stadtteil.localeCompare(b.stadtteil, "de"));
}
