// Admin-Bereich – Scraper-Seite: Läufe, Quellen, Warnungen (Plan Admin-Dashboard 4.3). Nur lesend.
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { scraperDatenLaden } from "@/lib/admin/scraper";

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => adminAntwort(200, await scraperDatenLaden(admin!.db), setCookies));
}
