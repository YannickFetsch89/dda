// Admin-Bereich – Konten in Zahlen und Sensibel-Treffer (Plan Admin-Dashboard 4.10, Stufe 5a).
// GET ?tage=30                                   → admin_konten_kennzahlen (nur Zahlen, nie Personen) und
//                                                  admin_sensibel_liste (Kennzeichnungen und Ausnahmen der letzten Tage)
// POST { aktion: "ausnahme", event, notiz }      → admin_sensibel_ausnahme (Fehltreffer)
// POST { aktion: "aufheben", event }             → admin_sensibel_ausnahme_aufheben
// Bewusst keine Suche nach Personen; Löschung und Auskunft bleiben im Supabase-Dashboard.
import { adminAntwort, adminRoute } from "@/lib/admin/route";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const tage = Math.max(1, Math.min(400, Number(new URL(request.url).searchParams.get("tage")) || 30));
    const db = admin!.db;
    const [zahlen, sensibel] = await Promise.all([db.rpc("admin_konten_kennzahlen"), db.rpc("admin_sensibel_liste", { p_tage: tage })]);
    if (zahlen.error) return adminAntwort(500, { fehler: zahlen.error.message, code: "db" }, setCookies);
    if (sensibel.error) return adminAntwort(500, { fehler: sensibel.error.message, code: "db" }, setCookies);
    return adminAntwort(200, { tage, zahlen: zahlen.data, sensibel: sensibel.data }, setCookies);
  });
}

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    const event = typeof body.event === "string" ? body.event : "";
    if (!UUID.test(event)) return adminAntwort(400, { fehler: "Ungültiges Event." }, setCookies);
    const db = admin!.db;
    const { data, error } =
      body.aktion === "ausnahme"
        ? await db.rpc("admin_sensibel_ausnahme", { p_event: event, p_notiz: typeof body.notiz === "string" ? body.notiz : "" })
        : body.aktion === "aufheben"
          ? await db.rpc("admin_sensibel_ausnahme_aufheben", { p_event: event })
          : { data: null, error: { message: "Unbekannte Aktion." } };
    if (error) return adminAntwort(400, { fehler: error.message, code: "db" }, setCookies);
    return adminAntwort(200, { ok: true, ergebnis: data }, setCookies);
  });
}
