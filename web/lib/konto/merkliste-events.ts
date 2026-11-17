// Events zu den IDs einer Konto-Merkliste laden (Plan 5.5): zuerst aus dem gecachten Pool, den Rest mit EINEM
// id-IN-Abruf (keine Einzelabfragen, keine 100er-Grenze). Abgelehnte Events fehlen wie auf der Website
// („nicht mehr verfügbar“). Keine Kennzeichnung sensibler Events.
import "server-only";
import { eventPoolLaden, mitSpalten, normalisieren, supabaseClient, type Zeile } from "../daten";
import { basisTitel, termineAmTag } from "../termine";
import type { DddEvent } from "../typen";

export async function eventsFuerIds(ids: string[]): Promise<{ heute: string; events: DddEvent[] }> {
  const pool = await eventPoolLaden();
  const ausPool = new Map(pool.alle.map((e) => [e.id, e]));
  const fehlend = ids.filter((id) => !ausPool.has(id));
  const nachgeladen = new Map<string, DddEvent>();

  const client = supabaseClient();
  if (fehlend.length && client && pool.quelle !== "beispiel") {
    for (let i = 0; i < fehlend.length; i += 200) {
      const teil = fehlend.slice(i, i + 200);
      const { data, error } = await mitSpalten((spalten) =>
        client.from("events").select(spalten).eq("abgelehnt", false).in("id", teil),
      );
      if (error) throw new Error(`Merkliste-Events: ${error.message}`);
      for (const z of (data ?? []) as unknown as Zeile[]) {
        const e = normalisieren(z);
        nachgeladen.set(e.id, e);
      }
    }
  }

  const events = ids
    .map((id) => ausPool.get(id) ?? nachgeladen.get(id) ?? null)
    .filter((e): e is DddEvent => e !== null)
    .map((e) => {
      // Wie /api/events: weitere Uhrzeiten am selben Tag als „Diverse Uhrzeiten“
      const zeiten = termineAmTag(pool.alle, e).map((t) => t.uhrzeit).filter((z): z is string => !!z);
      return zeiten.length > 1 ? { ...e, titel: basisTitel(e.titel), uhrzeiten: zeiten } : e;
    });
  return { heute: pool.heute, events };
}
