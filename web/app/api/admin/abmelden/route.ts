// Admin-Bereich – Abmelden: Sitzung beim Auth-Server beenden und Cookie löschen. Geht auch ohne aal2.
import { ADMIN_COOKIE_ART } from "@/lib/admin/konfig";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { adminAbmelden } from "@/lib/admin/zwei-faktor";
import { sitzungsCookieLoeschen } from "@/lib/konto/cookies";

export async function POST(request: Request) {
  return adminRoute(request, { zweiFaktor: false }, async ({ admin, lokal }) => {
    try {
      await adminAbmelden(admin!.sitzung);
    } catch (e) {
      console.error("Admin-Abmelden beim Auth-Server fehlgeschlagen:", e);
    }
    return adminAntwort(200, { ok: true }, [sitzungsCookieLoeschen(lokal, ADMIN_COOKIE_ART)]);
  });
}
