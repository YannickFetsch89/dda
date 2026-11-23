// Admin-Bereich – Vorschlag annehmen oder ablehnen (Plan Admin-Dashboard 3.5). Die Datenbank-Funktionen
// (database/admin_events_2026-11-23.sql) prüfen ist_admin() selbst und schreiben das Protokoll.
import { revalidateTag } from "next/cache";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { EVENTS_CACHE_TAG } from "@/lib/daten";
import { ORTE_CACHE_TAG } from "@/lib/orte";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function POST(request: Request, ctx: RouteContext<"/api/admin/vorschlaege/[id]">) {
  const { id } = await ctx.params;
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    if (!UUID.test(id)) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const aktion = body.aktion;
    if (aktion !== "annehmen" && aktion !== "ablehnen") return adminAntwort(400, { fehler: "Aktion annehmen oder ablehnen." }, setCookies);
    // Vorher lesen: Beim Zusammenlegen kann das behaltene Event ein Bild bekommen (Cursor-Prüfung Stufe 1d)
    const { data: v } = await admin!.db.from("admin_vorschlaege").select("art, vorschlag").eq("id", id).maybeSingle();
    const { data, error } = await admin!.db.rpc(aktion === "annehmen" ? "admin_vorschlag_annehmen" : "admin_vorschlag_ablehnen", { p_id: id });
    if (error) return adminAntwort(400, { fehler: error.message, code: "db" }, setCookies);
    if (aktion === "annehmen") {
      revalidateTag(EVENTS_CACHE_TAG, { expire: 0 });
      // Ortszuordnung und Ortsnamen ändern auch die Programme der Ortsseiten (Stufe 3c)
      if (v?.art === "ort_id" || v?.art === "ortsname") revalidateTag(ORTE_CACHE_TAG, { expire: 0 });
      const behalten = (v?.vorschlag as { behalten?: unknown } | null)?.behalten;
      if (v?.art === "dublette" && typeof behalten === "string" && UUID.test(behalten)) revalidateTag(`event-bild-${behalten.toLowerCase()}`, { expire: 0 });
    }
    return adminAntwort(200, { ok: true, ergebnis: data }, setCookies);
  });
}
