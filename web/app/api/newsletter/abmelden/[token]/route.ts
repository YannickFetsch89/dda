// One-Click-Abmeldung nach RFC 8058 (Plan Admin-Dashboard 4.9, Stufe 4): Ziel der Kopfzeile List-Unsubscribe.
// Mailprogramme schicken POST mit „List-Unsubscribe=One-Click“ von ihren eigenen Servern – daher keine Origin-Prüfung
// und kein JSON. GET ändert nichts (405), damit Link-Scanner nichts auslösen. Das Token steht im Pfad und damit im
// Access-Log von nginx – wie bei der Geburtstagsmail hingenommen: Es kann nur abmelden.
import { absenderIp, antwort, zuVieleAnfragen } from "@/lib/formulare";
import { abmelden } from "@/lib/newsletter-aktionen";

export async function POST(request: Request, ctx: RouteContext<"/api/newsletter/abmelden/[token]">) {
  if (zuVieleAnfragen("newsletter-abmelden", absenderIp(request.headers), 30, 60 * 60 * 1000)) {
    return antwort(429, { fehler: "Zu viele Anfragen in kurzer Zeit." });
  }
  const { token } = await ctx.params;
  let roh = "";
  try {
    roh = decodeURIComponent(token ?? "");
  } catch {
    // kaputte Kodierung → ungültig
  }
  const e = await abmelden(roh);
  return antwort(e.status, e.daten);
}

export async function GET(request: Request) {
  // Header lesen: Damit ist die Route nie vorgerendert (Cache Components)
  void request.headers.get("host");
  return new Response(JSON.stringify({ fehler: "Bitte über den Link in der Mail abmelden." }), {
    status: 405,
    headers: { Allow: "POST", "Content-Type": "application/json; charset=utf-8", "Cache-Control": "private, no-store" },
  });
}
