// Admin-Bereich – Zwei-Faktor starten: Code abfragen oder TOTP einrichten (QR-Code). Braucht eine Admin-Sitzung (aal1).
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { zweiFaktorStarten } from "@/lib/admin/zwei-faktor";

export async function POST(request: Request) {
  return adminRoute(request, { zweiFaktor: false }, async ({ admin, setCookies }) => {
    const start = await zweiFaktorStarten(admin!.sitzung);
    if (start.art === "fehler") return adminAntwort(503, { fehler: "Zwei-Faktor nicht verfügbar.", code: "dienst" }, setCookies);
    return adminAntwort(200, start, setCookies);
  });
}
