// Datenzugriff für den Guide „Spielplätze“ (Plan 5.1): eigene Abfrage OHNE Score-Schwelle – sichtbar ist jeder aktive
// Spielplatz (freigeschaltet per SQL, Schritt 6). Mit extras.spielplatz (Profil), Google-Foto und Fotoversion.
import { cacheLife } from "next/cache";
import { SPALTEN_MIT_EXTRAS, normalisieren, type Zeile } from "./orte";
import { leseClient } from "./supabase-server";
import type { DddOrt } from "./typen";

const KURZ = { stale: 30, revalidate: 60, expire: 120 };
const NORMAL = { stale: 300, revalidate: 600, expire: 3600 };
const SEITENGROESSE = 1000;

/** Alle aktiven Spielplätze (seitenweise, gecacht). */
export async function spielplaetzeLaden(): Promise<DddOrt[]> {
  "use cache";
  const client = leseClient();
  if (!client) {
    cacheLife(KURZ);
    return [];
  }
  const orte: DddOrt[] = [];
  try {
    for (let seite = 0; seite < 10; seite++) {
      const { data, error } = await client
        .from("orte")
        .select(SPALTEN_MIT_EXTRAS)
        .eq("aktiv", true)
        .eq("typ", "spielplatz")
        .order("name", { ascending: true })
        .order("id", { ascending: true })
        .range(seite * SEITENGROESSE, (seite + 1) * SEITENGROESSE - 1);
      if (error) {
        console.error(`Spielplätze konnten nicht geladen werden (Seite ${seite + 1}): ${error.message}`);
        cacheLife(KURZ);
        return orte;
      }
      orte.push(...((data ?? []) as unknown as Zeile[]).map(normalisieren));
      if (!data || data.length < SEITENGROESSE) break;
    }
  } catch (err) {
    console.error(`Fehler beim Laden der Spielplätze: ${err instanceof Error ? err.message : err}`);
    cacheLife(KURZ);
    return orte;
  }
  cacheLife(NORMAL);
  return orte;
}

/** Ein aktiver Spielplatz per Slug (aus der gecachten Liste). */
export async function spielplatzLaden(slug: string): Promise<DddOrt | null> {
  return (await spielplaetzeLaden()).find((o) => o.slug === slug) ?? null;
}
