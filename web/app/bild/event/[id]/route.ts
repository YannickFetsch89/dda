// Event-Bild über den eigenen Server ausliefern (Bild-Proxy, siehe lib/bild-proxy.ts).
// Nur Bilder, die zu einem Event in unserer Datenbank gehören – kein offener Proxy für beliebige Adressen.
import { cacheLife } from "next/cache";
import type { NextRequest } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { bildAntwort, bildHolen } from "@/lib/bild-proxy";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Original-Bildadresse eines Events (1 Tag gecached; nach Fehlern nur kurz). */
async function bildQuelle(id: string): Promise<string | null> {
  "use cache";
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!url || !key) {
    cacheLife({ stale: 30, revalidate: 60, expire: 120 });
    return null;
  }
  const { data, error } = await createClient(url, key, { auth: { persistSession: false } })
    .from("events")
    .select("bild_url")
    .eq("id", id)
    .eq("abgelehnt", false)
    .maybeSingle();
  if (error) {
    console.warn(`Event-Bild ${id}: ${error.message}`);
    cacheLife({ stale: 30, revalidate: 60, expire: 120 });
    return null;
  }
  cacheLife({ stale: 3600, revalidate: 86_400, expire: 7 * 86_400 });
  return typeof data?.bild_url === "string" ? data.bild_url : null;
}

export async function GET(_req: NextRequest, ctx: RouteContext<"/bild/event/[id]">) {
  const { id } = await ctx.params;
  if (!UUID.test(id)) return bildAntwort(null, 0);
  const quelle = await bildQuelle(id.toLowerCase());
  const bild = quelle ? await bildHolen(quelle, true) : null;
  return bildAntwort(bild, 86_400);
}
