// Admin-Bereich – mehrere Vorschläge auf einmal annehmen oder ablehnen (Plan Admin-Dashboard 3.5 „einzeln oder
// gesammelt“, Stufe 3c). Nur für die Orte-Arten ortsname, ort_id und adresse: Sie ändern nur leere bzw. ungeschützte
// Felder. Dubletten und Gebiet (Zusammenlegen, Löschen) bleiben Einzelentscheidungen.
// POST { ids: [uuid…] (höchstens 200), aktion: "annehmen" | "ablehnen" } → je Vorschlag die DB-Funktion.
import { revalidateTag } from "next/cache";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { EVENTS_CACHE_TAG } from "@/lib/daten";
import { ORTE_CACHE_TAG } from "@/lib/orte";
import { SAMMEL_ARTEN } from "@/lib/admin/vorschlaege";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    const aktion = body.aktion;
    if (aktion !== "annehmen" && aktion !== "ablehnen") return adminAntwort(400, { fehler: "Aktion annehmen oder ablehnen." }, setCookies);
    const ids = Array.isArray(body.ids) ? [...new Set(body.ids.filter((x): x is string => typeof x === "string" && UUID.test(x)))] : [];
    if (!ids.length || ids.length > 200) return adminAntwort(400, { fehler: "1 bis 200 Vorschläge." }, setCookies);
    const db = admin!.db;
    const { data: zeilen, error } = await db.from("admin_vorschlaege").select("id, art, status").in("id", ids);
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    const fremd = (zeilen ?? []).filter((z) => !SAMMEL_ARTEN.includes(String(z.art)));
    if (fremd.length) return adminAntwort(400, { fehler: "Dubletten und Gebiet bitte einzeln entscheiden." }, setCookies);

    let erledigt = 0;
    const fehler: { id: string; fehler: string }[] = [];
    for (const z of (zeilen ?? []).filter((x) => x.status === "offen")) {
      const { error: e } = await db.rpc(aktion === "annehmen" ? "admin_vorschlag_annehmen" : "admin_vorschlag_ablehnen", { p_id: z.id });
      if (e) fehler.push({ id: String(z.id), fehler: e.message });
      else erledigt += 1;
    }
    if (aktion === "annehmen" && erledigt) {
      revalidateTag(EVENTS_CACHE_TAG, { expire: 0 });
      revalidateTag(ORTE_CACHE_TAG, { expire: 0 });
    }
    return adminAntwort(200, { ok: true, erledigt, fehler }, setCookies);
  });
}
