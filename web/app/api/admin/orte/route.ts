// Admin-Bereich – Orte-Liste mit Suche und Filtern (Plan Admin-Dashboard 4.7, Stufe 3a). Liest mit dem Admin-Token;
// die Policy orte_admin_lesen zeigt Admins auch inaktive Orte. extras nur in Teilen (dort liegen auch große
// Google-Rohdaten, siehe lib/orte.ts).
import { ORT_FILTER, istOrtTyp, type OrtFilter } from "@/lib/admin/orte";
import { adminAntwort, adminRoute } from "@/lib/admin/route";

const SEITE = 50;
const LISTEN_SPALTEN =
  "id, name, slug, typ, stadtteil, adresse, aktiv, qualitaets_score, bild_url, latitude, parent_id, " +
  "hat_text:beschreibung, google_foto:extras->google_foto, text_freigegeben:extras->spielstaette->text_freigegeben, " +
  "text_entwurf:extras->spielstaette->text_entwurf->datum, score_manuell:extras->score_manuell";

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const p = new URL(request.url).searchParams;
    const seite = Math.max(0, Math.min(200, Number(p.get("seite")) || 0));
    const filter = (p.get("filter") ?? "").split(",").filter((f): f is OrtFilter => (ORT_FILTER as readonly string[]).includes(f));

    let q = admin!.db.from("orte").select(LISTEN_SPALTEN, { count: "exact" });
    const typ = p.get("typ");
    if (istOrtTyp(typ)) q = q.eq("typ", typ);
    // Standard: nur aktive; „inaktiv“ zeigt nur abgeschaltete/noch nicht freigeschaltete; „alle“ beides
    const status = p.get("status");
    if (status !== "alle") q = q.eq("aktiv", filter.includes("inaktiv") ? false : true);
    const suche = p.get("q")?.trim().replace(/[%_,()*]/g, " ").slice(0, 80);
    if (suche) q = q.or(`name.ilike.*${suche}*,slug.ilike.*${suche}*,adresse.ilike.*${suche}*`);
    if (filter.includes("ohne_text")) q = q.is("beschreibung", null);
    if (filter.includes("text_entwurf")) q = q.not("extras->spielstaette->text_entwurf", "is", null);
    if (filter.includes("ohne_bild")) q = q.is("bild_url", null).is("extras->google_foto", null);
    if (filter.includes("ohne_geo")) q = q.is("latitude", null);
    if (filter.includes("ohne_adresse")) q = q.is("adresse", null);

    const { data, count, error } = await q.order("name").range(seite * SEITE, seite * SEITE + SEITE - 1);
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    // Den Text selbst braucht die Liste nicht, nur ob es ihn gibt
    const orte = (data ?? []).map((z) => {
      const { hat_text, ...rest } = z as unknown as Record<string, unknown>;
      return { ...rest, hat_text: typeof hat_text === "string" && hat_text.trim().length > 0 };
    });
    return adminAntwort(200, { seite, proSeite: SEITE, gesamt: count ?? 0, orte }, setCookies);
  });
}
