// Admin-Bereich – Vorschau eines Google-Fotos per Ressourcenname (Plan Admin-Dashboard 4.7, Stufe 3b).
// GET ?name=places/<id>/photos/<id>  → Bild (verkleinert), nur mit Admin-Sitzung.
// Wie /ort-foto/[slug]: Der Key bleibt auf dem Server, das Bild wird nur durchgereicht (nicht gespeichert, Google-
// Nutzungsbedingungen); der Browser darf es einen Tag privat behalten. Jeder Abruf kostet (Place Photo).
import { FOTO_NAME } from "@/lib/admin/guides";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { bildAntwort, bildHolen } from "@/lib/bild-proxy";

const BREITE = 640;

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ setCookies }) => {
    const name = new URL(request.url).searchParams.get("name") ?? "";
    if (!FOTO_NAME.test(name)) return adminAntwort(400, { fehler: "Ungültiger Foto-Name." }, setCookies);
    const key = process.env.GOOGLE_PLACES_API_KEY;
    if (!key) return adminAntwort(503, { fehler: "GOOGLE_PLACES_API_KEY fehlt." }, setCookies);
    try {
      const r = await fetch(`https://places.googleapis.com/v1/${name}/media?maxWidthPx=${BREITE}&skipHttpRedirect=true`, {
        headers: { "X-Goog-Api-Key": key },
        signal: AbortSignal.timeout(10_000),
      });
      if (!r.ok) return adminAntwort(502, { fehler: `Google: HTTP ${r.status}` }, setCookies);
      const adresse = ((await r.json()) as { photoUri?: unknown }).photoUri;
      if (typeof adresse !== "string") return adminAntwort(502, { fehler: "Google lieferte keine Bildadresse." }, setCookies);
      const { bild } = await bildHolen(adresse, false);
      const antwort = bildAntwort(bild, 86400, true);
      for (const c of setCookies) antwort.headers.append("Set-Cookie", c);
      return antwort;
    } catch (e) {
      return adminAntwort(502, { fehler: e instanceof Error ? e.message : "Foto nicht ladbar." }, setCookies);
    }
  });
}
