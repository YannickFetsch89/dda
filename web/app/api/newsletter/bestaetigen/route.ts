// Newsletter-Anmeldung bestätigen (Plan Admin-Dashboard 4.9, Stufe 4). POST { token } von der Seite
// /newsletter/bestaetigen – erst der Klick auf den Button bestätigt (Link-Scanner in Mailprogrammen lösen nichts aus).
import { absenderIp, antwort, zuGross, zuVieleAnfragen } from "@/lib/formulare";
import { bestaetigen } from "@/lib/newsletter-aktionen";

export async function POST(request: Request) {
  if (zuGross(request, 2 * 1024)) return antwort(413, { fehler: "Ungültige Anfrage." });
  if (zuVieleAnfragen("newsletter-bestaetigen", absenderIp(request.headers), 30, 60 * 60 * 1000)) {
    return antwort(429, { fehler: "Zu viele Anfragen in kurzer Zeit. Bitte versuch es später noch einmal." });
  }
  const daten = (await request.json().catch(() => ({}))) as { token?: unknown };
  const e = await bestaetigen(daten.token);
  return antwort(e.status, e.daten);
}
