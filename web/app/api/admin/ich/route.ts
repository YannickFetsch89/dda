// Admin-Bereich – Wer ist angemeldet? Für den Rahmen der Admin-Seiten (Mailadresse, Abmelden).
// Antwortet 401 (abgemeldet) bzw. 403 mit code „zwei_faktor“, damit die Seite zur Anmeldung bzw. zum Code weiterleitet.
import { adminAntwort, adminRoute } from "@/lib/admin/route";

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) =>
    adminAntwort(200, { email: admin!.sitzung.email, aal: admin!.aal }, setCookies),
  );
}
