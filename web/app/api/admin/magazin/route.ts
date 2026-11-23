// Admin-Bereich – Magazin: Liste, Redaktionsplan, Kosten, Autoren; neuen Entwurf anlegen; Job starten; Autor speichern
// (Plan Admin-Dashboard 4.6, Stufe 2). Alles über die SECURITY-DEFINER-Funktionen aus database/admin_magazin_2026-11-23.sql.
import { revalidateTag } from "next/cache";
import { workflowStarten } from "@/lib/admin/github";
import { istRubrikWert, redaktionsplan, type ListenBeitrag } from "@/lib/admin/magazin";
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { heuteBerlin, plusTage } from "@/lib/datum";
import { MAGAZIN_CACHE_TAG } from "@/lib/magazin-daten";
import { zuVieleAnfragen } from "@/lib/formulare";

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const db = admin!.db;
    const heute = heuteBerlin(new Date());
    const [liste, kosten, autoren] = await Promise.all([
      db.rpc("admin_magazin_liste", { p_status: null }),
      db.rpc("admin_magazin_kosten", { p_von: `${plusTage(heute, -180).slice(0, 7)}-01` }),
      db.rpc("admin_magazin_autoren"),
    ]);
    const fehler = liste.error ?? kosten.error ?? autoren.error;
    if (fehler) return adminAntwort(500, { fehler: fehler.message, code: "db" }, setCookies);
    const beitraege = (liste.data ?? []) as ListenBeitrag[];
    return adminAntwort(200, { heute, beitraege, plan: redaktionsplan(beitraege, heute), kosten: kosten.data, autoren: autoren.data ?? [] }, setCookies);
  });
}

const AUFGABEN = new Set(["entwurf-wochenvorschau", "entwurf-monats-tipps"]);

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    const db = admin!.db;

    if (body.aktion === "anlegen") {
      if (!istRubrikWert(body.rubrik) || typeof body.autor !== "string" || typeof body.titel !== "string") {
        return adminAntwort(400, { fehler: "Rubrik, Autor und Titel nötig." }, setCookies);
      }
      const { data, error } = await db.rpc("admin_magazin_anlegen", { p_rubrik: body.rubrik, p_autor: body.autor, p_titel: body.titel });
      if (error) return adminAntwort(400, { fehler: error.message, code: "db" }, setCookies);
      return adminAntwort(200, { ok: true, id: data, weiter: `/admin/magazin/${data}` }, setCookies);
    }

    if (body.aktion === "job") {
      const aufgabe = String(body.aufgabe ?? "");
      if (!AUFGABEN.has(aufgabe)) return adminAntwort(400, { fehler: "Unbekannte Aufgabe." }, setCookies);
      const von = typeof body.von === "string" && /^\d{4}-\d{2}-\d{2}$/.test(body.von) ? body.von : "";
      if (zuVieleAnfragen("admin-magazin-job", "alle", 1, 10 * 60 * 1000)) {
        return adminAntwort(429, { fehler: "Es wurde gerade erst ein Magazin-Lauf gestartet. Bitte 10 Minuten warten." }, setCookies);
      }
      const inputs: Record<string, string> = { aufgabe, dry_run: body.dry_run === false ? "false" : "true" };
      if (von) inputs.von = von;
      const ergebnis = await workflowStarten("magazin", inputs);
      await protokollieren(db, { aktion: "magazin_job", nachher: { ...inputs, ergebnis } });
      return ergebnis.ok ? adminAntwort(200, { ok: true }, setCookies) : adminAntwort(502, { fehler: ergebnis.meldung }, setCookies);
    }

    if (body.aktion === "autor") {
      if (typeof body.slug !== "string" || !body.felder || typeof body.felder !== "object") return adminAntwort(400, { fehler: "Ungültig." }, setCookies);
      const { error } = await db.rpc("admin_magazin_autor_speichern", { p_slug: body.slug, p_felder: body.felder });
      if (error) return adminAntwort(400, { fehler: error.message, code: "db" }, setCookies);
      revalidateTag(MAGAZIN_CACHE_TAG, { expire: 0 });
      return adminAntwort(200, { ok: true }, setCookies);
    }

    return adminAntwort(400, { fehler: "Unbekannte Aktion." }, setCookies);
  });
}
