// One-Click-Abmeldung der Geburtstagsmail nach RFC 8058 (Plan Geburtstagsmail G4, Kontenplan 13a).
// Ziel der Kopfzeile List-Unsubscribe; Mailprogramme schicken POST mit „List-Unsubscribe=One-Click“ von ihren eigenen
// Servern, daher hier KEINE Origin-Prüfung und kein JSON. GET ändert nichts (405), damit Link-Scanner nichts auslösen.
// Das Token steht im Pfad und damit im Access-Log von nginx – bewusst hingenommen (13a): Es kann nur abbestellen.
import { kontoDienstClient } from "@/lib/konto/clients";
import { geburtstagAbmelden, geburtstagTokenPruefen } from "@/lib/konto/geburtstag";
import { MELDUNG, kontenAktiv } from "@/lib/konto/konfig";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

export const POST = kontoRoute(
  { anmeldung: false, limit: { name: "geburtstag-abmelden", max: 30, fensterMs: ZEIT.STUNDE } },
  async (_ctx, { params }) => {
    const { token } = await params;
    let roh = "";
    try {
      roh = decodeURIComponent(token ?? "");
    } catch {
      // kaputte Kodierung → ungültig
    }
    const nutzerId = geburtstagTokenPruefen(roh);
    if (!nutzerId) return kontoAntwort(400, { fehler: "Ungültiger Link.", code: "token" });
    const dienst = kontoDienstClient();
    if (!dienst) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    const r = await geburtstagAbmelden(dienst, nutzerId);
    if (r !== "ok") return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    return kontoAntwort(200, { ok: true });
  },
);

/** GET ändert nichts (RFC 8058): 405 mit Allow-Kopf; ohne Schalter wie alle Konto-Routen 404. */
export async function GET(request: Request) {
  // Header lesen: Damit ist die Route nie vorgerendert (Cache Components)
  void request.headers.get("host");
  if (!kontenAktiv()) return kontoAntwort(404, { fehler: "Nicht gefunden." });
  return new Response(JSON.stringify({ fehler: "Bitte über den Link in der Mail abmelden." }), {
    status: 405,
    headers: { Allow: "POST", "Content-Type": "application/json; charset=utf-8", "Cache-Control": "private, no-store" },
  });
}
