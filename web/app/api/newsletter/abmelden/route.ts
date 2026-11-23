// Newsletter abmelden (Plan Admin-Dashboard 4.9, Stufe 4). POST { token } von der Seite /newsletter/abmelden.
// Löscht die Adresse sofort.
import { absenderIp, antwort, zuGross, zuVieleAnfragen } from "@/lib/formulare";
import { abmelden } from "@/lib/newsletter-aktionen";

export async function POST(request: Request) {
  if (zuGross(request, 2 * 1024)) return antwort(413, { fehler: "Ungültige Anfrage." });
  if (zuVieleAnfragen("newsletter-abmelden", absenderIp(request.headers), 30, 60 * 60 * 1000)) {
    return antwort(429, { fehler: "Zu viele Anfragen in kurzer Zeit. Bitte versuch es später noch einmal." });
  }
  const daten = (await request.json().catch(() => ({}))) as { token?: unknown };
  const e = await abmelden(daten.token);
  return antwort(e.status, e.daten);
}
