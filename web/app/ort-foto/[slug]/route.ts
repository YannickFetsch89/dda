// Liefert das Foto eines Ortes über den eigenen Server aus (Bild-Proxy, siehe lib/bild-proxy.ts).
//
// - Eigenes Bild (orte.bild_url): wird geholt, auf der Platte gecached und durchgereicht.
// - Google-Foto (orte.extras.google_foto.name): Die Bildadresse wird serverseitig bei der Places API
//   abgefragt (skipHttpRedirect → photoUri, ohne Key) und das Bild durchgereicht. Der Browser spricht
//   dabei nie mit Google, der API-Key verlässt nie den Server. Google-Bilder werden nicht dauerhaft
//   gespeichert (Nutzungsbedingungen); nur die Bildadresse wird gecached, weil jeder Abruf kostet:
//     Treffer 30 Tage · dauerhaft kein Foto 1 Tag · vorübergehender Fehler 5 Minuten
import { cacheLife } from "next/cache";
import type { NextRequest } from "next/server";
import { bildAntwort, bildHolen } from "@/lib/bild-proxy";
import { ortLaden, slugDekodieren } from "@/lib/orte";

const FOTO_BREITE = 1200;
// Nur echte Ressourcennamen zulassen ("places/<id>/photos/<id>"), nichts anderes an Google weiterreichen
const FOTO_NAME = /^places\/[A-Za-z0-9_-]+\/photos\/[A-Za-z0-9_-]+$/;
const TAG = 24 * 3600;

type Ergebnis = { adresse: string | null; voruebergehend?: boolean };

/** Nur Bildadressen von Google ohne Key verwenden. */
function gueltigeGoogleAdresse(wert: unknown): string | null {
  if (typeof wert !== "string") return null;
  try {
    const url = new URL(wert);
    const googleHost = url.hostname === "googleusercontent.com" || url.hostname.endsWith(".googleusercontent.com");
    return url.protocol === "https:" && googleHost && !/[?&]key=/i.test(url.search) ? wert : null;
  } catch {
    return null;
  }
}

async function googleFotoAdresse(name: string, slug: string): Promise<Ergebnis> {
  const key = process.env.GOOGLE_PLACES_API_KEY;
  if (!key) {
    console.warn("GOOGLE_PLACES_API_KEY fehlt in .env.local – Ort-Fotos können nicht geladen werden");
    return { adresse: null, voruebergehend: true };
  }
  try {
    const antwort = await fetch(
      `https://places.googleapis.com/v1/${name}/media?maxWidthPx=${FOTO_BREITE}&skipHttpRedirect=true`,
      { headers: { "X-Goog-Api-Key": key } },
    );
    if (!antwort.ok) {
      // 400/403/404: Foto-Name abgelaufen o.ä. → mit "google_places --aktualisieren" erneuern
      console.warn(`Ort-Foto für '${slug}' nicht geladen: HTTP ${antwort.status}`);
      return { adresse: null, voruebergehend: antwort.status === 429 || antwort.status >= 500 };
    }
    const adresse = gueltigeGoogleAdresse(((await antwort.json()) as { photoUri?: unknown }).photoUri);
    return { adresse, voruebergehend: false };
  } catch (err) {
    console.warn(`Ort-Foto für '${slug}' nicht geladen: ${err instanceof Error ? err.message : err}`);
    return { adresse: null, voruebergehend: true };
  }
}

/** Bildquelle eines Ortes: { adresse, google } – gecached nach Ergebnis (siehe Kopfkommentar). */
async function bildQuelle(slug: string): Promise<{ adresse: string | null; google: boolean }> {
  "use cache";
  const ort = await ortLaden(slug);
  if (ort?.bild_url && !ort.bild_url.includes("key=")) {
    cacheLife({ stale: 3600, revalidate: TAG, expire: 7 * TAG });
    return { adresse: ort.bild_url, google: false };
  }
  const foto = ort?.extras?.google_foto as { name?: unknown } | undefined;
  const name = typeof foto?.name === "string" && FOTO_NAME.test(foto.name) ? foto.name : null;
  const ergebnis: Ergebnis = name ? await googleFotoAdresse(name, slug) : { adresse: null };
  // Genau ein cacheLife-Aufruf je Durchlauf, abhängig vom Ergebnis
  if (ergebnis.adresse) cacheLife({ stale: TAG, revalidate: 30 * TAG, expire: 45 * TAG });
  else if (ergebnis.voruebergehend) cacheLife({ stale: 60, revalidate: 300, expire: 600 });
  else cacheLife({ stale: 3600, revalidate: TAG, expire: 2 * TAG });
  return { adresse: ergebnis.adresse, google: true };
}

export async function GET(_req: NextRequest, ctx: RouteContext<"/ort-foto/[slug]">) {
  const slug = slugDekodieren((await ctx.params).slug);
  const quelle = slug ? await bildQuelle(slug) : null;
  // Google-Fotos nur durchreichen (nicht auf der Platte speichern), eigene Bilder cachen
  const bild = quelle?.adresse ? await bildHolen(quelle.adresse, !quelle.google) : null;
  return bildAntwort(bild, TAG);
}
