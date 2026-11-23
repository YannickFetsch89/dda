// Admin-Bereich – Daten fürs Cockpit (Plan Admin-Dashboard 4.2). Nur lesend, braucht Sitzung mit Zwei-Faktor.
import { cockpitLaden } from "@/lib/admin/cockpit";
import { adminAntwort, adminRoute } from "@/lib/admin/route";

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => adminAntwort(200, await cockpitLaden(admin!.db), setCookies));
}
