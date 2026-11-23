// Admin-Bereich – Empfehlungen (Plan Admin-Dashboard 4.5, Stufe 1e).
// GET  ?tag=YYYY-MM-DD           → Tagesvorschau wie die Startseite, Kandidaten mit „Warum“, Kalender 30 Tage
// POST { event, flagge, wert }   → Tipp / Highlight / Top / nicht empfehlen setzen (Zeitpunkte wie im alten Dashboard)
import { revalidateTag } from "next/cache";
import { empfehlungenLaden, FLAGGEN, flaggenUpdate, type Flagge } from "@/lib/admin/empfehlungen";
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { EVENTS_CACHE_TAG } from "@/lib/daten";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ setCookies }) => {
    const tag = new URL(request.url).searchParams.get("tag");
    return adminAntwort(200, await empfehlungenLaden(tag), setCookies);
  });
}

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    const event = typeof body.event === "string" ? body.event : "";
    const flagge = body.flagge as Flagge;
    if (!UUID.test(event) || !(FLAGGEN as readonly string[]).includes(flagge) || typeof body.wert !== "boolean") {
      return adminAntwort(400, { fehler: "Ungültige Anfrage.", code: "eingabe" }, setCookies);
    }
    const update = flaggenUpdate(flagge, body.wert);
    const db = admin!.db;
    const { data: vorher } = await db
      .from("events")
      .select("tipp_des_tages, highlight_der_woche, highlight_gesetzt_am, top_event_des_monats, top_gesetzt_am, nicht_empfehlen")
      .eq("id", event)
      .maybeSingle();
    if (!vorher) return adminAntwort(404, { fehler: "Event nicht gefunden." }, setCookies);
    const { error } = await db.from("events").update(update).eq("id", event);
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    await protokollieren(db, { aktion: `flagge_${flagge}`, tabelle: "events", ziel_id: event, vorher, nachher: update });
    revalidateTag(EVENTS_CACHE_TAG, { expire: 0 });
    return adminAntwort(200, { ok: true }, setCookies);
  });
}
