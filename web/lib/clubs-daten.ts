// Daten für den Club-Hub: Clubs (typ = club) plus Orte anderer Hubs mit extras.auch_club (Pitcher, Konvex,
// Schlager Cafe …). Sichtbar ist nur, was laut Profil passt und einen Club-Score ≥ 7 hat.
import { clubProfil, istSichtbarerClub } from "./clubs";
import { clubOrteLaden } from "./orte";
import type { DddEvent, DddOrt, EventPool } from "./typen";

export async function clubsLaden(): Promise<DddOrt[]> {
  return (await clubOrteLaden()).filter(istSichtbarerClub);
}

/** Club für die Detailseite /guides/clubs/[slug] (auch Orte mit auch_club, die eine eigene Haupt-URL haben). */
export async function clubLaden(slug: string): Promise<DddOrt | null> {
  return (await clubsLaden()).find((o) => o.slug === slug) ?? null;
}

/** Kommende Events an diesem Ort aus dem Kalender (Abgleich über die gespeicherten Schreibweisen des Orts). */
export function naechsteEvents(o: DddOrt, pool: EventPool, anzahl = 8): DddEvent[] {
  const namen = new Set(clubProfil(o)?.eventOrte ?? []);
  if (!namen.size) return [];
  return pool.events
    .filter((e) => namen.has(e.ort) && !e.abgesagt && (e.datum >= pool.heute || (e.datum_bis ?? "") >= pool.heute))
    .sort((a, b) => a.datum.localeCompare(b.datum) || (a.uhrzeit ?? "").localeCompare(b.uhrzeit ?? ""))
    .slice(0, anzahl);
}
