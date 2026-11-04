// Bild-Proxy: Fremde Bilder (Event-Bilder der Veranstalter, Google-Fotos der Orte) holt unser Server
// und reicht sie durch. Der Browser spricht so nur mit diesdas.events – keine Besucher-IP geht an
// Drittanbieter (gleiche Rechtslage wie bei Google Fonts).
//
// Event-Bilder werden zusätzlich auf der Platte des Servers zwischengespeichert (30 Tage), damit
// die Quellseiten nicht bei jedem Aufruf belastet werden. Google-Fotos werden NICHT dauerhaft
// gespeichert (Google-Nutzungsbedingungen), nur durchgereicht; der Browser cached sie einen Tag.
import "server-only";
import { createHash } from "node:crypto";
import { mkdir, readFile, rename, stat, unlink, writeFile, readdir } from "node:fs/promises";
import path from "node:path";

const MAX_BYTES = 8 * 1024 * 1024; // größere Bilder werden nicht ausgeliefert
const TIMEOUT_MS = 10_000;
const CACHE_TAGE = 30;
// Laufzeit-Verzeichnis, nicht Teil des Bundles (turbopackIgnore verhindert das Verfolgen des ganzen Projekts)
const CACHE_DIR = process.env.BILD_CACHE_DIR || path.join(/* turbopackIgnore: true */ process.cwd(), ".cache", "bilder");

export interface Bild {
  bytes: Uint8Array;
  typ: string;
}

/** Nur öffentliche http(s)-Adressen – keine lokalen/privaten Ziele (Schutz vor Missbrauch als Proxy ins Netz). */
function erlaubteAdresse(roh: string): URL | null {
  try {
    const url = new URL(roh);
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    const h = url.hostname.toLowerCase();
    if (
      h === "localhost" || h.endsWith(".localhost") || h.endsWith(".local") || h === "[::1]" ||
      /^(127\.|10\.|0\.|169\.254\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(h)
    ) return null;
    return url;
  } catch {
    return null;
  }
}

async function ausCacheLesen(schluessel: string): Promise<Bild | null> {
  try {
    const datei = path.join(CACHE_DIR, `${schluessel}.bin`);
    const info = await stat(datei);
    if (Date.now() - info.mtimeMs > CACHE_TAGE * 86_400_000) return null;
    const [bytes, typ] = await Promise.all([readFile(datei), readFile(path.join(CACHE_DIR, `${schluessel}.typ`), "utf8")]);
    return { bytes: new Uint8Array(bytes), typ };
  } catch {
    return null;
  }
}

async function inCacheSchreiben(schluessel: string, bild: Bild): Promise<void> {
  try {
    await mkdir(CACHE_DIR, { recursive: true });
    const tmp = path.join(CACHE_DIR, `${schluessel}.${process.pid}.tmp`);
    await writeFile(path.join(CACHE_DIR, `${schluessel}.typ`), bild.typ);
    await writeFile(tmp, bild.bytes);
    await rename(tmp, path.join(CACHE_DIR, `${schluessel}.bin`));
  } catch (err) {
    console.warn(`Bild-Cache nicht beschreibbar: ${err instanceof Error ? err.message : err}`);
  }
}

/** Gelegentlich abgelaufene Cache-Dateien löschen (ca. jeder 200. Aufruf). */
async function aufraeumen(): Promise<void> {
  if (Math.random() > 0.005) return;
  try {
    const grenze = Date.now() - CACHE_TAGE * 86_400_000;
    for (const name of await readdir(CACHE_DIR)) {
      const datei = path.join(CACHE_DIR, name);
      if ((await stat(datei)).mtimeMs < grenze) await unlink(datei).catch(() => {});
    }
  } catch {
    // Aufräumen ist optional
  }
}

/**
 * Holt ein Bild von einer fremden Adresse.
 * @param zwischenspeichern true = auf der Platte cachen (Event-Bilder), false = nur durchreichen (Google-Fotos)
 */
export async function bildHolen(adresse: string, zwischenspeichern: boolean): Promise<Bild | null> {
  const url = erlaubteAdresse(adresse);
  if (!url) return null;

  const schluessel = createHash("sha256").update(url.toString()).digest("hex");
  if (zwischenspeichern) {
    const treffer = await ausCacheLesen(schluessel);
    if (treffer) return treffer;
  }

  try {
    const antwort = await fetch(url, {
      signal: AbortSignal.timeout(TIMEOUT_MS),
      headers: { "User-Agent": "diesdas.events Bildvorschau (+https://diesdas.events/impressum)", Accept: "image/*" },
      cache: "no-store",
    });
    const typ = antwort.headers.get("content-type")?.split(";")[0].trim() ?? "";
    if (!antwort.ok || !typ.startsWith("image/") || typ.includes("svg")) return null; // SVG nicht durchreichen (Skripte möglich)
    if (Number(antwort.headers.get("content-length") ?? 0) > MAX_BYTES) return null;
    const bytes = new Uint8Array(await antwort.arrayBuffer());
    if (bytes.byteLength > MAX_BYTES || bytes.byteLength === 0) return null;
    const bild = { bytes, typ };
    if (zwischenspeichern) {
      await inCacheSchreiben(schluessel, bild);
      void aufraeumen();
    }
    return bild;
  } catch (err) {
    console.warn(`Bild ${url.hostname} nicht geladen: ${err instanceof Error ? err.message : err}`);
    return null;
  }
}

/** HTTP-Antwort für ein Bild (oder 404, wenn keins da ist). */
export function bildAntwort(bild: Bild | null, browserCacheSekunden: number): Response {
  if (!bild) {
    return new Response("Bild nicht verfügbar", { status: 404, headers: { "Cache-Control": "public, max-age=600" } });
  }
  return new Response(bild.bytes as BodyInit, {
    headers: {
      "Content-Type": bild.typ,
      "Content-Length": String(bild.bytes.byteLength),
      "Cache-Control": `public, max-age=${browserCacheSekunden}`,
      "X-Content-Type-Options": "nosniff",
    },
  });
}
