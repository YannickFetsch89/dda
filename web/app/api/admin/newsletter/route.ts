// Admin-Bereich – Newsletter (Plan Admin-Dashboard 4.9, Stufe 4). Liest mit dem Admin-Token (Policies „Admins lesen/
// löschen Newsletter“ aus meldungen_newsletter_2026-11-05.sql).
// GET ?export=1                                    → CSV nur der bestätigten Adressen (Protokoll mit Anzahl, ohne Adressen)
// POST { aktion: "liste", status?, q?, seite? }     → Zahlen (admin_newsletter_zahlen) und Liste, 100 je Seite.
//      Als POST, damit eine gesuchte Adresse nicht in der Adresse und im Access-Log steht (Cursor-Prüfung 4, Befund 2).
// POST { aktion: "loeschen", id }                  → Adresse löschen (auf Anfrage); das Protokoll enthält keine Adresse
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";

const SEITE = 100;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** CSV-Feld: Anführungszeichen verdoppeln; führende =, +, -, @ entschärfen (Formel-Einschleusung in Tabellen) */
function feld(w: string): string {
  const s = /^[=+\-@]/.test(w) ? `'${w}` : w;
  return `"${s.replace(/"/g, '""')}"`;
}

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const db = admin!.db;
    const p = new URL(request.url).searchParams;

    if (p.get("export") === "1") {
      const zeilen: { email: string; bestaetigt_am: string }[] = [];
      for (let start = 0; ; start += 1000) {
        const { data, error } = await db
          .from("newsletter_anmeldungen")
          .select("email, bestaetigt_am")
          .not("bestaetigt_am", "is", null)
          .order("bestaetigt_am")
          .range(start, start + 999);
        if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
        zeilen.push(...((data ?? []) as typeof zeilen));
        if ((data ?? []).length < 1000) break;
      }
      await protokollieren(db, { aktion: "newsletter_export", tabelle: "newsletter_anmeldungen", nachher: { anzahl: zeilen.length } });
      // Mit BOM (\uFEFF), damit Excel die Datei als UTF-8 erkennt
      const csv = ["email;bestaetigt_am", ...zeilen.map((z) => `${feld(z.email)};${feld(z.bestaetigt_am)}`)].join("\r\n") + "\r\n";
      const antwort = new Response("\uFEFF" + csv, {
        status: 200,
        headers: {
          "Content-Type": "text/csv; charset=utf-8",
          "Content-Disposition": `attachment; filename="newsletter-bestaetigt-${new Date().toISOString().slice(0, 10)}.csv"`,
          "Cache-Control": "private, no-store",
        },
      });
      for (const c of setCookies) antwort.headers.append("Set-Cookie", c);
      return antwort;
    }

    return adminAntwort(400, { fehler: "Liste bitte per POST laden." }, setCookies);
  });
}

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    if (body.aktion === "liste") {
      const db = admin!.db;
      const seite = Math.max(0, Math.min(500, Number(body.seite) || 0));
      let q = db
        .from("newsletter_anmeldungen")
        .select("id, email, quelle, erstellt_am, bestaetigt_am, bestaetigung_gesendet_am, bestaetigung_zugestellt_am, mails_gesendet", { count: "exact" });
      if (body.status === "bestaetigt") q = q.not("bestaetigt_am", "is", null);
      if (body.status === "offen") q = q.is("bestaetigt_am", null);
      const suche = typeof body.q === "string" ? body.q.trim().replace(/[%_,()*\\]/g, " ").slice(0, 80) : "";
      if (suche) q = q.ilike("email", `%${suche}%`);
      const [liste, zahlen] = await Promise.all([
        q.order("erstellt_am", { ascending: false }).range(seite * SEITE, seite * SEITE + SEITE - 1),
        db.rpc("admin_newsletter_zahlen"),
      ]);
      if (liste.error) return adminAntwort(500, { fehler: liste.error.message, code: "db" }, setCookies);
      return adminAntwort(200, { seite, proSeite: SEITE, gesamt: liste.count ?? 0, anmeldungen: liste.data ?? [], zahlen: zahlen.data ?? null }, setCookies);
    }
    if (body.aktion !== "loeschen") return adminAntwort(400, { fehler: "Unbekannte Aktion." }, setCookies);
    const id = typeof body.id === "string" ? body.id : "";
    if (!UUID.test(id)) return adminAntwort(400, { fehler: "Ungültige ID." }, setCookies);
    const db = admin!.db;
    const { data, error } = await db.from("newsletter_anmeldungen").delete().eq("id", id).select("id, bestaetigt_am");
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    if (!data?.length) return adminAntwort(404, { fehler: "Nicht gefunden oder keine Rechte." }, setCookies);
    await protokollieren(db, {
      aktion: "newsletter_loeschen",
      tabelle: "newsletter_anmeldungen",
      ziel_id: id,
      vorher: { bestaetigt: !!data[0].bestaetigt_am },
    });
    return adminAntwort(200, { ok: true }, setCookies);
  });
}
