// Datenzugriff für den Weihnachtsmarkt-Guide (Plan 5.1): eigener Lader OHNE Score-Schwelle (orteLaden verlangt
// qualitaets_score ≥ 7 und fiele aus). Sichtbar ist jede aktive Zeile mit typ weihnachtsmarkt (Freischaltung per SQL).
import { cacheLife } from "next/cache";
import { heuteBerlin } from "./datum";
import { SPALTEN_MIT_EXTRAS, normalisieren, type Zeile } from "./orte";
import { leseClient } from "./supabase-server";
import type { DddOrt } from "./typen";

const KURZ = { stale: 30, revalidate: 60, expire: 120 };
const NORMAL = { stale: 300, revalidate: 600, expire: 3600 };

/** Alle aktiven Weihnachtsmärkte (gecacht, 10 Minuten). */
export async function weihnachtsmaerkteLaden(): Promise<DddOrt[]> {
  "use cache";
  const client = leseClient();
  if (!client) {
    cacheLife(KURZ);
    return [];
  }
  try {
    const { data, error } = await client
      .from("orte")
      .select(SPALTEN_MIT_EXTRAS)
      .eq("aktiv", true)
      .eq("typ", "weihnachtsmarkt")
      .order("name", { ascending: true })
      .order("id", { ascending: true })
      .range(0, 999);
    if (error) {
      console.error(`Weihnachtsmärkte konnten nicht geladen werden: ${error.message}`);
      cacheLife(KURZ);
      return [];
    }
    cacheLife(NORMAL);
    return ((data ?? []) as unknown as Zeile[]).map(normalisieren);
  } catch (err) {
    console.error(`Fehler beim Laden der Weihnachtsmärkte: ${err instanceof Error ? err.message : err}`);
    cacheLife(KURZ);
    return [];
  }
}

/** Ein aktiver Weihnachtsmarkt per Slug (aus der gecachten Liste). */
export async function weihnachtsmarktLaden(slug: string): Promise<DddOrt | null> {
  return (await weihnachtsmaerkteLaden()).find((o) => o.slug === slug) ?? null;
}

/**
 * Heutiger Tag zur Anfragezeit für Startseiten-Box, Tagesleiste (Morgen/Samstag) und Top-5-Fenster: höchstens 5 Minuten
 * alt. Kurzlebiger Cache statt new Date() im Render – Cache Components bricht sonst den dynamischen Teil ab.
 */
export async function heuteKurz(): Promise<string> {
  "use cache";
  cacheLife({ stale: 60, revalidate: 60, expire: 300 });
  return heuteBerlin();
}

/**
 * Kalendertag für Dinge mit Tagesgenauigkeit, die nicht von der Uhrzeit abhängen (Event-JSON-LD nur in der Saison,
 * Jahr im Titel). Höchstens eine Stunde alt. NICHT für „heute geöffnet“ – das rechnet nur der Browser (Plan E5).
 */
export async function saisonTag(): Promise<string> {
  "use cache";
  cacheLife({ stale: 600, revalidate: 3600, expire: 7200 });
  return heuteBerlin();
}
