// Liefert das Google-Foto eines Ortes aus, ohne den API-Key öffentlich zu machen.
//
// Gespeichert ist nur der Foto-Ressourcenname (orte.extras.google_foto.name). Diese Route fragt
// serverseitig bei der Places API die eigentliche Bild-Adresse ab (skipHttpRedirect → photoUri
// auf googleusercontent.com, ohne Key) und leitet den Browser per 302 dorthin weiter.
// Die Adresse wird einige Stunden gecached, damit nicht jeder Seitenaufruf einen API-Abruf kostet.
import { cacheLife } from "next/cache";
import type { NextRequest } from "next/server";
import { ortLaden } from "@/lib/orte";

const FOTO_BREITE = 1200;
// Nur echte Ressourcennamen zulassen ("places/<id>/photos/<id>"), nichts anderes an Google weiterreichen
const FOTO_NAME = /^places\/[A-Za-z0-9_-]+\/photos\/[A-Za-z0-9_-]+$/;
const BROWSER_CACHE_SEKUNDEN = 6 * 3600;

async function fotoAdresseLaden(slug: string): Promise<string | null> {
  "use cache";
  cacheLife({ stale: 3600, revalidate: 6 * 3600, expire: 24 * 3600 });

  const key = process.env.GOOGLE_PLACES_API_KEY;
  if (!key) {
    console.warn("GOOGLE_PLACES_API_KEY fehlt in .env.local – Ort-Fotos können nicht geladen werden");
    return null;
  }

  const ort = await ortLaden(slug);
  const foto = ort?.extras?.google_foto as { name?: unknown } | undefined;
  const name = typeof foto?.name === "string" ? foto.name : null;
  if (!name || !FOTO_NAME.test(name)) return null;

  try {
    const antwort = await fetch(
      `https://places.googleapis.com/v1/${name}/media?maxWidthPx=${FOTO_BREITE}&skipHttpRedirect=true`,
      { headers: { "X-Goog-Api-Key": key } },
    );
    if (!antwort.ok) {
      // Foto-Namen laufen bei Google irgendwann ab → mit "google_places --aktualisieren" erneuern
      console.warn(`Ort-Foto für '${slug}' nicht geladen: HTTP ${antwort.status}`);
      return null;
    }
    const daten = (await antwort.json()) as { photoUri?: unknown };
    return typeof daten.photoUri === "string" && daten.photoUri.startsWith("https://") ? daten.photoUri : null;
  } catch (err) {
    console.warn(`Ort-Foto für '${slug}' nicht geladen: ${err instanceof Error ? err.message : err}`);
    return null;
  }
}

export async function GET(_req: NextRequest, ctx: RouteContext<"/ort-foto/[slug]">) {
  const { slug } = await ctx.params;
  const adresse = await fotoAdresseLaden(decodeURIComponent(slug));
  if (!adresse) {
    return new Response("Foto nicht verfügbar", { status: 404, headers: { "Cache-Control": "public, max-age=600" } });
  }
  return new Response(null, {
    status: 302,
    headers: { Location: adresse, "Cache-Control": `public, max-age=${BROWSER_CACHE_SEKUNDEN}` },
  });
}
