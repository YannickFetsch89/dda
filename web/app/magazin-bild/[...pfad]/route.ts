// Zuschnitte der Magazin-Aufmacherbilder (Plan 5.11): 16:9, 4:3, 1:1 für JSON-LD, og:image und Feed.
// Nur Dateien aus public/fallback, public/magazin-bilder und public/ort-bilder/weihnachtsmaerkte; jede andere Anfrage → 404.
// Liegt außerhalb des Proxy-matchers; der Route-Handler setzt den Status selbst (kein Soft-404).
import { readFile } from "node:fs/promises";
import { cacheLife } from "next/cache";
import type { NextRequest } from "next/server";
import sharp from "sharp";
import { imErlaubtenOrdner } from "@/lib/magazin-bild-pfad";
import { ZUSCHNITT_MASSE, zuschnittPruefen, type Zuschnitt } from "@/lib/magazin-bilder";

/** Zuschnitt rechnen (gecacht: Pfad und Format sind der Schlüssel; neue Bilder bekommen neue Pfade). */
async function zuschnittRechnen(voll: string, z: Zuschnitt): Promise<string | null> {
  "use cache";
  cacheLife({ stale: 86_400, revalidate: 7 * 86_400, expire: 30 * 86_400 });
  try {
    const { breite, hoehe } = ZUSCHNITT_MASSE[z];
    const daten = await sharp(await readFile(voll)).resize(breite, hoehe, { fit: "cover", position: "centre" }).webp({ quality: 82 }).toBuffer();
    return daten.toString("base64");
  } catch {
    return null;
  }
}

const nichtDa = () =>
  new Response("Nicht gefunden", { status: 404, headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" } });

export async function GET(_req: NextRequest, ctx: { params: Promise<{ pfad: string[] }> }) {
  const { pfad } = await ctx.params;
  const geprueft = zuschnittPruefen(pfad);
  if (!geprueft) return nichtDa();
  const voll = imErlaubtenOrdner(geprueft.relativ);
  if (!voll) return nichtDa();
  const bild = await zuschnittRechnen(voll, geprueft.zuschnitt);
  if (!bild) return nichtDa();
  return new Response(Buffer.from(bild, "base64"), {
    headers: { "Content-Type": "image/webp", "Cache-Control": "public, max-age=31536000, immutable" },
  });
}
