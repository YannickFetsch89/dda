// One-Click-Abmeldung nach RFC 8058 (Plan Admin-Dashboard 4.9, Stufe 4): Ziel der Kopfzeile List-Unsubscribe.
// Mailprogramme schicken POST mit dem Body „List-Unsubscribe=One-Click“ (application/x-www-form-urlencoded) von ihren
// eigenen Servern – daher keine Origin-Prüfung. Nur genau dieser Body meldet ab (Cursor-Prüfung 4, Befund 1); GET
// ändert nichts (405), damit Link-Scanner nichts auslösen. Das Token steht im Pfad und damit im Access-Log von nginx –
// wie bei der Geburtstagsmail hingenommen: Es kann nur abmelden.
// Bremslimit nur für ungültige Tokens (Cursor-Prüfung 4, Befund 4): One-Click kommt oft über wenige Server der
// Mailanbieter; gültige Abmeldungen dürfen daran nie scheitern. Raten hilft nicht (HMAC).
import { absenderIp, antwort, zuGross, zuVieleAnfragen } from "@/lib/formulare";
import { istOneClick, newsletterTokenPruefen } from "@/lib/newsletter";
import { abmelden } from "@/lib/newsletter-aktionen";

export async function POST(request: Request, ctx: RouteContext<"/api/newsletter/abmelden/[token]">) {
  if (zuGross(request, 1024)) return antwort(413, { fehler: "Ungültige Anfrage." });
  const { token } = await ctx.params;
  let roh = "";
  try {
    roh = decodeURIComponent(token ?? "");
  } catch {
    // kaputte Kodierung → ungültig
  }
  if (!newsletterTokenPruefen(roh, "abmelden")) {
    if (zuVieleAnfragen("newsletter-one-click", absenderIp(request.headers), 30, 60 * 60 * 1000)) {
      return antwort(429, { fehler: "Zu viele Anfragen in kurzer Zeit." });
    }
    return antwort(400, { fehler: "Dieser Link ist ungültig oder abgelaufen." });
  }
  const body = await request.text().catch(() => "");
  if (!istOneClick(request.headers.get("content-type"), body)) {
    return antwort(400, { fehler: "Bitte über den Link in der Mail abmelden." });
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
