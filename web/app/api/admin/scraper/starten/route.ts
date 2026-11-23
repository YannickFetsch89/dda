// Admin-Bereich – Scraper-Lauf starten (Plan Admin-Dashboard 4.3, E3): scrape.yml per workflow_dispatch.
// Ein manueller Start läuft immer, auch außerhalb des 3-Tage-Rhythmus. Läuft schon einer, reiht GitHub ihn ein
// (concurrency „scraper“). Höchstens ein Start je 10 Minuten.
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { workflowStarten } from "@/lib/admin/github";
import { zuVieleAnfragen } from "@/lib/formulare";

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    if (zuVieleAnfragen("admin-scraper-start", "alle", 1, 10 * 60 * 1000)) {
      return adminAntwort(429, { fehler: "Es wurde gerade erst ein Lauf gestartet. Bitte 10 Minuten warten.", code: "bremse" }, setCookies);
    }
    const ergebnis = await workflowStarten("scrape");
    await protokollieren(admin!.db, { aktion: "scraper_starten", nachher: ergebnis });
    if (!ergebnis.ok) return adminAntwort(502, { fehler: ergebnis.meldung, code: "github" }, setCookies);
    return adminAntwort(200, { ok: true }, setCookies);
  });
}
