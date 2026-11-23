// Admin-Bereich – Google-Fotos eines Ortes als Kandidaten (Plan Admin-Dashboard 4.7, Stufe 3b; Q6: auf Knopfdruck).
// GET → bis zu 10 Fotos {name, breite, hoehe, autor, autor_url} aus der Places API (nur Feld „photos“).
// Die Vorschaubilder lädt die Seite einzeln über /api/admin/orte/foto?name=… (jedes kostet einen Place-Photo-Abruf).
// Spielstätten bekommen keine Google-Fotos (scraper/orte/ortsbilder.py).
import { googleKandidaten, PLACE_ID } from "@/lib/admin/guides";
import { adminAntwort, adminRoute } from "@/lib/admin/route";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function GET(request: Request, ctx: RouteContext<"/api/admin/orte/[id]/google-fotos">) {
  const { id } = await ctx.params;
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    if (!UUID.test(id)) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const { data, error } = await admin!.db.from("orte").select("typ, google_place_id").eq("id", id).maybeSingle();
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    if (!data) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    if (data.typ === "spielstaette") return adminAntwort(400, { fehler: "Spielstätten bekommen keine Google-Fotos." }, setCookies);
    const placeId = typeof data.google_place_id === "string" ? data.google_place_id : "";
    if (!PLACE_ID.test(placeId)) return adminAntwort(400, { fehler: "Für diesen Ort ist kein Google-Eintrag hinterlegt." }, setCookies);
    const key = process.env.GOOGLE_PLACES_API_KEY;
    if (!key) return adminAntwort(503, { fehler: "GOOGLE_PLACES_API_KEY fehlt." }, setCookies);
    try {
      const r = await fetch(`https://places.googleapis.com/v1/places/${encodeURIComponent(placeId)}`, {
        headers: { "X-Goog-Api-Key": key, "X-Goog-FieldMask": "photos" },
        signal: AbortSignal.timeout(10_000),
      });
      if (!r.ok) return adminAntwort(502, { fehler: `Google: HTTP ${r.status}` }, setCookies);
      return adminAntwort(200, { fotos: googleKandidaten(await r.json()) }, setCookies);
    } catch (e) {
      return adminAntwort(502, { fehler: e instanceof Error ? e.message : "Google nicht erreichbar." }, setCookies);
    }
  });
}
