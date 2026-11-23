// Admin-Bereich – Vorschläge der Pipeline lesen (Plan Admin-Dashboard 3.5). Standard: offene, neueste zuerst.
import { adminAntwort, adminRoute } from "@/lib/admin/route";

const ARTEN = new Set(["dublette", "gebiet"]);
const STATUS = new Set(["offen", "angenommen", "abgelehnt"]);

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const p = new URL(request.url).searchParams;
    const status = STATUS.has(p.get("status") ?? "") ? p.get("status")! : "offen";
    let q = admin!.db
      .from("admin_vorschlaege")
      .select("id, art, ziel_id, schluessel, vorschlag, begruendung, status, erstellt_am, entschieden_am", { count: "exact" })
      .eq("status", status);
    if (ARTEN.has(p.get("art") ?? "")) q = q.eq("art", p.get("art")!);
    const { data, count, error } = await q.order("erstellt_am", { ascending: false }).limit(200);
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    return adminAntwort(200, { status, gesamt: count ?? 0, vorschlaege: data ?? [] }, setCookies);
  });
}
