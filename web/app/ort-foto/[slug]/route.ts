// Liefert das Google-Foto eines Ortes aus, ohne den API-Key öffentlich zu machen.
//
// Gespeichert ist nur der Foto-Ressourcenname (orte.extras.google_foto.name). Diese Route fragt
// serverseitig bei der Places API die eigentliche Bild-Adresse ab (skipHttpRedirect → photoUri
// auf googleusercontent.com, ohne Key) und leitet den Browser per 302 dorthin weiter.
//
// Cache-Dauer je nach Ergebnis (jeder Abruf bei Google kostet, bei über 600 Orten wichtig):
//   - Treffer: 30 Tage (die Adresse enthält keinen Ablaufparameter)
//   - dauerhaft kein Foto (Ort/Foto unbekannt, Google 400/403/404): 1 Tag
//   - vorübergehender Fehler (429, 5xx, Netzwerk, fehlender Key): 5 Minuten – sonst bliebe
//     ein Ausfall für Tage im Cache hängen
import { cacheLife } from "next/cache";
import type { NextRequest } from "next/server";
import { ortLaden, slugDekodieren } from "@/lib/orte";

const FOTO_BREITE = 1200;
// Nur echte Ressourcennamen zulassen ("places/<id>/photos/<id>"), nichts anderes an Google weiterreichen
const FOTO_NAME = /^places\/[A-Za-z0-9_-]+\/photos\/[A-Za-z0-9_-]+$/;
const BROWSER_CACHE_SEKUNDEN = 24 * 3600;
const TAG = 24 * 3600;

type Ergebnis = { adresse: string | null; voruebergehend?: boolean };

/** Nur Bildadressen von Google ohne Key weiterreichen. */
function gueltigeBildadresse(wert: unknown): string | null {
  if (typeof wert !== "string") return null;
  try {
    const url = new URL(wert);
    const googleHost = url.hostname === "googleusercontent.com" || url.hostname.endsWith(".googleusercontent.com");
    return url.protocol === "https:" && googleHost && !/[?&]key=/i.test(url.search) ? wert : null;
  } catch {
    return null;
  }
}

async function fotoLaden(slug: string): Promise<Ergebnis> {
  const key = process.env.GOOGLE_PLACES_API_KEY;
  if (!key) {
    console.warn("GOOGLE_PLACES_API_KEY fehlt in .env.local – Ort-Fotos können nicht geladen werden");
    return { adresse: null, voruebergehend: true };
  }

  const ort = await ortLaden(slug);
  const foto = ort?.extras?.google_foto as { name?: unknown } | undefined;
  const name = typeof foto?.name === "string" ? foto.name : null;
  if (!name || !FOTO_NAME.test(name)) return { adresse: null, voruebergehend: false };

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
    const adresse = gueltigeBildadresse(((await antwort.json()) as { photoUri?: unknown }).photoUri);
    return adresse ? { adresse } : { adresse: null, voruebergehend: false };
  } catch (err) {
    console.warn(`Ort-Foto für '${slug}' nicht geladen: ${err instanceof Error ? err.message : err}`);
    return { adresse: null, voruebergehend: true };
  }
}

async function fotoAdresseLaden(slug: string): Promise<string | null> {
  "use cache";
  const ergebnis = await fotoLaden(slug);
  // Genau ein cacheLife-Aufruf je Durchlauf, abhängig vom Ergebnis
  if (ergebnis.adresse) {
    cacheLife({ stale: TAG, revalidate: 30 * TAG, expire: 45 * TAG });
  } else if (ergebnis.voruebergehend) {
    cacheLife({ stale: 60, revalidate: 300, expire: 600 });
  } else {
    cacheLife({ stale: 3600, revalidate: TAG, expire: 2 * TAG });
  }
  return ergebnis.adresse;
}

export async function GET(_req: NextRequest, ctx: RouteContext<"/ort-foto/[slug]">) {
  const slug = slugDekodieren((await ctx.params).slug);
  const adresse = slug ? await fotoAdresseLaden(slug) : null;
  if (!adresse) {
    return new Response("Foto nicht verfügbar", { status: 404, headers: { "Cache-Control": "public, max-age=600" } });
  }
  return new Response(null, {
    status: 302,
    headers: { Location: adresse, "Cache-Control": `public, max-age=${BROWSER_CACHE_SEKUNDEN}` },
  });
}
