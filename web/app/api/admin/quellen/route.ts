// Admin-Bereich – Quellen an/aus (Plan Admin-Dashboard 4.10, Stufe 5b). Tabelle quellen_einstellungen
// (database/admin_quellen_2026-11-24.sql); main.py überspringt abgeschaltete Quellen beim nächsten Lauf.
// GET                                   → alle Quellen des letzten Laufs (Namen wie QUELLEN in main.py) mit Status und Schalter
// POST { quelle, aktiv, grund? }        → schalten (Abschalten braucht einen Grund)
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const db = admin!.db;
    const [lauf, einstellungen] = await Promise.all([
      db.from("scraper_laeufe").select("id, gestartet_am").neq("status", "laeuft").order("gestartet_am", { ascending: false }).limit(1).maybeSingle(),
      db.from("quellen_einstellungen").select("quelle, aktiv, grund, geaendert_am"),
    ]);
    if (einstellungen.error) return adminAntwort(500, { fehler: `${einstellungen.error.message} – SQL admin_quellen_2026-11-24.sql ausgeführt?`, code: "db" }, setCookies);
    const ergebnisse = lauf.data
      ? ((await db.from("scraper_ergebnisse").select("quelle, tier, status, anzahl, meldung").eq("lauf_id", lauf.data.id)).data ?? [])
      : [];
    const schalter = new Map((einstellungen.data ?? []).map((z) => [String(z.quelle), z]));
    const namen = [...new Set([...ergebnisse.map((e) => String(e.quelle)), ...schalter.keys()])];
    const quellen = namen
      .map((n) => {
        const e = ergebnisse.find((x) => x.quelle === n);
        const s = schalter.get(n);
        return { quelle: n, tier: e?.tier ?? null, status: e?.status ?? null, anzahl: e?.anzahl ?? null, meldung: e?.meldung ?? null, aktiv: s ? s.aktiv !== false : true, grund: s?.grund ?? null, geaendert_am: s?.geaendert_am ?? null };
      })
      .sort((a, b) => (a.tier ?? 9) - (b.tier ?? 9) || a.quelle.localeCompare(b.quelle, "de"));
    return adminAntwort(200, { lauf: lauf.data ?? null, quellen }, setCookies);
  });
}

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    const quelle = typeof body.quelle === "string" ? body.quelle.trim() : "";
    if (!quelle || quelle.length > 120) return adminAntwort(400, { fehler: "Ungültige Quelle." }, setCookies);
    if (typeof body.aktiv !== "boolean") return adminAntwort(400, { fehler: "aktiv: ja oder nein." }, setCookies);
    const grund = typeof body.grund === "string" ? body.grund.trim().slice(0, 300) : "";
    if (!body.aktiv && grund.length < 3) return adminAntwort(400, { fehler: "Bitte einen Grund angeben." }, setCookies);
    const db = admin!.db;
    const { error } = await db
      .from("quellen_einstellungen")
      .upsert({ quelle, aktiv: body.aktiv, grund: grund || null, geaendert_am: new Date().toISOString(), geaendert_von: admin!.sitzung.nutzerId }, { onConflict: "quelle" });
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    await protokollieren(db, { aktion: body.aktiv ? "quelle_an" : "quelle_aus", tabelle: "quellen_einstellungen", ziel_id: quelle.slice(0, 200), nachher: { grund: grund || null } });
    return adminAntwort(200, { ok: true }, setCookies);
  });
}
