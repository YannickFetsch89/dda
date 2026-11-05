// Bild-Proxy: Fremde Bilder (Event-Bilder der Veranstalter, Google-Fotos der Orte) holt unser Server
// und reicht sie durch. Der Browser spricht so nur mit diesdas.events – keine Besucher-IP geht an
// Drittanbieter (gleiche Rechtslage wie bei Google Fonts).
//
// Event-Bilder werden zusätzlich auf der Platte des Servers zwischengespeichert (30 Tage, max. 2 GB),
// damit die Quellseiten nicht bei jedem Aufruf belastet werden. Google-Fotos werden NICHT dauerhaft
// gespeichert (Google-Nutzungsbedingungen), nur durchgereicht; nur der Browser cached sie einen Tag.
//
// Schutz vor Missbrauch (SSRF): Bildadressen stammen aus fremden Quellen. Deshalb wird jede
// Verbindung – auch nach Weiterleitungen – erst aufgebaut, nachdem der Hostname aufgelöst und
// JEDE Ziel-IP als öffentlich geprüft wurde (Prüfung direkt beim Verbindungsaufbau, damit ein
// zweiter DNS-Abruf nicht auf eine interne Adresse umgelenkt werden kann).
import "server-only";
import { createHash } from "node:crypto";
import dns from "node:dns";
import { mkdir, readFile, rename, stat, unlink, writeFile, readdir } from "node:fs/promises";
import http from "node:http";
import https from "node:https";
import net from "node:net";
import path from "node:path";

const MAX_BYTES = 8 * 1024 * 1024; // größere Bilder werden nicht ausgeliefert
const TIMEOUT_MS = 10_000;
const MAX_WEITERLEITUNGEN = 4;
const CACHE_TAGE = 30;
const CACHE_MAX_BYTES = 2 * 1024 * 1024 * 1024;
// Geschätzte Cache-Größe: beim ersten Schreiben nach dem Start und bei jedem Aufräumen genau gezählt,
// dazwischen je geschriebenem Bild erhöht – überschreitet sie die Grenze, wird sofort aufgeräumt
let cacheGroesse: number | null = null;
// Laufzeit-Verzeichnis, nicht Teil des Bundles (turbopackIgnore verhindert das Verfolgen des ganzen Projekts)
const CACHE_DIR = process.env.BILD_CACHE_DIR || path.join(/* turbopackIgnore: true */ process.cwd(), ".cache", "bilder");
const USER_AGENT = "diesdas.events Bildvorschau (+https://diesdas.events/impressum)";

export interface Bild {
  bytes: Uint8Array;
  typ: string;
}

/** Ergebnis eines Abrufs; status = letzter HTTP-Status der Quelle (fehlt bei Netzfehlern/Cache). */
export interface HolErgebnis {
  bild: Bild | null;
  status?: number;
}

// --- Erlaubte Ziele ---------------------------------------------------------------------------

/** Nicht-öffentliche Adressbereiche (privat, Loopback, Link-Local, CGNAT, Doku, Multicast, reserviert). */
// Getrennte Listen: eine BlockList prüft IPv4 sonst auch gegen IPv6-Regeln (::ffff:0:0/96 sperrte alles).
const GESPERRT_V4 = new net.BlockList();
for (const [netz, praefix] of [
  ["0.0.0.0", 8], ["10.0.0.0", 8], ["100.64.0.0", 10], ["127.0.0.0", 8], ["169.254.0.0", 16],
  ["172.16.0.0", 12], ["192.0.0.0", 24], ["192.0.2.0", 24], ["192.168.0.0", 16], ["198.18.0.0", 15],
  ["198.51.100.0", 24], ["203.0.113.0", 24], ["224.0.0.0", 4], ["240.0.0.0", 4],
] as const) GESPERRT_V4.addSubnet(netz, praefix, "ipv4");
const GESPERRT_V6 = new net.BlockList();
for (const [netz, praefix] of [
  ["::", 96] /* ::, ::1 und altes IPv4-kompatibles ::a.b.c.d */, ["64:ff9b::", 96], ["64:ff9b:1::", 48], ["100::", 64], ["2001::", 23], ["2001:db8::", 32],
  ["2002::", 16], ["fc00::", 7], ["fe80::", 10], ["fec0::", 10], ["ff00::", 8],
] as const) GESPERRT_V6.addSubnet(netz, praefix, "ipv6");

/** IPv4-in-IPv6 (::ffff:1.2.3.4 oder ::ffff:102:304) als IPv4 zurückgeben, sonst null. */
function eingebettetesIpv4(adresse: string): string | null {
  const gepunktet = /^::ffff:(\d{1,3}(?:\.\d{1,3}){3})$/i.exec(adresse);
  if (gepunktet) return gepunktet[1];
  const hex = /^::ffff:([0-9a-f]{1,4}):([0-9a-f]{1,4})$/i.exec(adresse);
  if (!hex) return null;
  const [hoch, tief] = [parseInt(hex[1], 16), parseInt(hex[2], 16)];
  return `${hoch >> 8}.${hoch & 255}.${tief >> 8}.${tief & 255}`;
}

/** true, wenn die IP-Adresse öffentlich erreichbar ist (IPv4-in-IPv6 wird als IPv4 geprüft). */
export function oeffentlicheIp(adresse: string): boolean {
  const ip = eingebettetesIpv4(adresse) ?? adresse;
  const familie = net.isIP(ip);
  if (familie === 4) return !GESPERRT_V4.check(ip, "ipv4");
  if (familie === 6) return !/^::ffff:/i.test(ip) && !GESPERRT_V6.check(ip, "ipv6");
  return false;
}

/** DNS-Auflösung, die nur öffentliche Ziele zulässt (wird von http/https beim Verbinden genutzt). */
const sichererLookup = ((
  hostname: string,
  optionen: dns.LookupOptions,
  rueckruf: (err: NodeJS.ErrnoException | null, adresse?: string | dns.LookupAddress[], familie?: number) => void,
) => {
  dns.lookup(hostname, { ...optionen, all: true }, (err, adressen) => {
    if (err) return rueckruf(err);
    if (!adressen.length || adressen.some((a) => !oeffentlicheIp(a.address))) {
      const fehler: NodeJS.ErrnoException = new Error(`${hostname} zeigt nicht auf eine öffentliche Adresse`);
      fehler.code = "EZIELGESPERRT";
      return rueckruf(fehler);
    }
    if (optionen.all) rueckruf(null, adressen);
    else rueckruf(null, adressen[0].address, adressen[0].family);
  });
}) as unknown as net.LookupFunction;

/** Nur http(s) ohne Zugangsdaten; IP-Literale müssen öffentlich sein (Hostnamen prüft sichererLookup). */
function erlaubteAdresse(roh: string | URL): URL | null {
  try {
    const url = new URL(roh);
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    if (url.username || url.password) return null;
    const h = url.hostname.toLowerCase().replace(/^\[|\]$/g, "");
    if (h === "localhost" || h.endsWith(".localhost") || h.endsWith(".local") || h.endsWith(".internal")) return null;
    if (net.isIP(h) && !oeffentlicheIp(h)) return null;
    return url;
  } catch {
    return null;
  }
}

// --- Abruf ------------------------------------------------------------------------------------

interface RohAntwort {
  status: number;
  weiter?: string | null;
  bild?: Bild;
}

/** Ein einzelner HTTP-Abruf ohne automatische Weiterleitung; bricht ab, sobald MAX_BYTES überschritten sind. */
function einmalHolen(url: URL, signal: AbortSignal): Promise<RohAntwort> {
  return new Promise((resolve, reject) => {
    const modul = url.protocol === "https:" ? https : http;
    const anfrage = modul.get(
      url,
      { lookup: sichererLookup, signal, headers: { "User-Agent": USER_AGENT, Accept: "image/*" } },
      (antwort) => {
        const status = antwort.statusCode ?? 0;
        if (status >= 300 && status < 400) {
          antwort.resume();
          resolve({ status, weiter: antwort.headers.location ?? null });
          return;
        }
        const typ = String(antwort.headers["content-type"] ?? "").split(";")[0].trim().toLowerCase();
        const kodierung = String(antwort.headers["content-encoding"] ?? "identity").toLowerCase();
        if (
          status !== 200 || !typ.startsWith("image/") || typ.includes("svg") || // SVG nicht durchreichen (Skripte möglich)
          kodierung !== "identity" || Number(antwort.headers["content-length"] ?? 0) > MAX_BYTES
        ) {
          antwort.resume();
          resolve({ status });
          return;
        }
        const teile: Buffer[] = [];
        let groesse = 0;
        antwort.on("data", (teil: Buffer) => {
          if (groesse > MAX_BYTES) return;
          groesse += teil.length;
          if (groesse <= MAX_BYTES) return void teile.push(teil);
          // Zu groß: Verbindung ohne Fehlerobjekt schließen; späte Socket-Fehler abfangen, damit
          // kein unbehandeltes "error"-Event den Prozess beenden kann
          teile.length = 0;
          antwort.socket?.on("error", () => {});
          antwort.destroy();
          resolve({ status: 413 });
        });
        antwort.on("end", () => resolve({ status, bild: { bytes: new Uint8Array(Buffer.concat(teile)), typ } }));
        antwort.on("error", reject);
        antwort.on("close", () => reject(new Error("Verbindung vorzeitig geschlossen")));
      },
    );
    anfrage.on("error", reject);
  });
}

/** Folgt Weiterleitungen selbst und prüft dabei jedes Ziel erneut. */
async function vonQuelleHolen(start: URL): Promise<HolErgebnis> {
  const signal = AbortSignal.timeout(TIMEOUT_MS);
  let url: URL | null = start;
  for (let schritt = 0; url && schritt <= MAX_WEITERLEITUNGEN; schritt++) {
    const antwort = await einmalHolen(url, signal);
    if (antwort.weiter === undefined) {
      const bild = antwort.bild && antwort.bild.bytes.byteLength > 0 ? antwort.bild : null;
      return { bild, status: antwort.status };
    }
    url = antwort.weiter ? erlaubteAdresse(new URL(antwort.weiter, url)) : null;
  }
  return { bild: null, status: 310 }; // zu viele oder unzulässige Weiterleitungen
}

// --- Platten-Cache (nur Event-/eigene Bilder) -------------------------------------------------
// Eine Datei je Bild: "<content-type>\n<bytes>" – so sind Typ und Inhalt immer gemeinsam atomar ersetzt.

async function ausCacheLesen(schluessel: string): Promise<Bild | null> {
  try {
    const datei = path.join(CACHE_DIR, `${schluessel}.bild`);
    if (Date.now() - (await stat(datei)).mtimeMs > CACHE_TAGE * 86_400_000) return null;
    const inhalt = await readFile(datei);
    const trenner = inhalt.indexOf(10);
    const typ = trenner > 0 ? inhalt.subarray(0, trenner).toString("utf8") : "";
    if (!typ.startsWith("image/")) return null;
    return { bytes: new Uint8Array(inhalt.subarray(trenner + 1)), typ };
  } catch {
    return null;
  }
}

async function inCacheSchreiben(schluessel: string, bild: Bild): Promise<void> {
  try {
    await mkdir(CACHE_DIR, { recursive: true });
    const tmp = path.join(CACHE_DIR, `${schluessel}.${process.pid}.${Date.now()}.tmp`);
    await writeFile(tmp, Buffer.concat([Buffer.from(`${bild.typ}\n`, "utf8"), bild.bytes]));
    await rename(tmp, path.join(CACHE_DIR, `${schluessel}.bild`));
    if (cacheGroesse !== null) cacheGroesse += bild.bytes.byteLength;
  } catch (err) {
    console.warn(`Bild-Cache nicht beschreibbar: ${err instanceof Error ? err.message : err}`);
  }
}

let raeumtAuf = false;

/**
 * Abgelaufenes löschen und den Cache unter 2 GB halten. Läuft beim ersten Schreiben nach dem Start,
 * sobald die geschätzte Größe die Grenze überschreitet, und sonst ca. bei jedem 200. Schreibvorgang.
 */
async function aufraeumen(): Promise<void> {
  const noetig = cacheGroesse === null || cacheGroesse > CACHE_MAX_BYTES || Math.random() < 0.005;
  if (!noetig || raeumtAuf) return;
  raeumtAuf = true;
  try {
    const grenze = Date.now() - CACHE_TAGE * 86_400_000;
    const dateien: { datei: string; zeit: number; groesse: number }[] = [];
    for (const name of await readdir(CACHE_DIR)) {
      const datei = path.join(CACHE_DIR, name);
      const info = await stat(datei).catch(() => null);
      if (!info) continue;
      if (info.mtimeMs < grenze) await unlink(datei).catch(() => {});
      else dateien.push({ datei, zeit: info.mtimeMs, groesse: info.size });
    }
    let summe = dateien.reduce((s, d) => s + d.groesse, 0);
    if (summe > CACHE_MAX_BYTES) {
      for (const d of dateien.sort((a, b) => a.zeit - b.zeit)) {
        if (summe <= CACHE_MAX_BYTES * 0.8) break;
        await unlink(d.datei).catch(() => {});
        summe -= d.groesse;
      }
    }
    cacheGroesse = summe;
  } catch {
    // Aufräumen ist optional (z.B. Ordner existiert noch nicht)
    cacheGroesse = 0;
  } finally {
    raeumtAuf = false;
  }
}

// --- Öffentliche Schnittstelle ----------------------------------------------------------------

/** Laufende Abrufe je Bild – gleichzeitige Anfragen teilen sich einen Abruf (kein Mehrfach-Download). */
const laufend = new Map<string, Promise<HolErgebnis>>();

/**
 * Holt ein Bild von einer fremden Adresse.
 * @param zwischenspeichern true = auf der Platte cachen (Event-/eigene Bilder), false = nur durchreichen (Google-Fotos)
 */
export async function bildHolen(adresse: string, zwischenspeichern: boolean): Promise<HolErgebnis> {
  const url = erlaubteAdresse(adresse);
  if (!url) return { bild: null };

  const schluessel = createHash("sha256").update(url.toString()).digest("hex");
  if (zwischenspeichern) {
    const treffer = await ausCacheLesen(schluessel);
    if (treffer) return { bild: treffer };
  }

  const kennung = `${schluessel}:${zwischenspeichern}`;
  const bestehend = laufend.get(kennung);
  if (bestehend) return bestehend;

  const abruf = (async (): Promise<HolErgebnis> => {
    try {
      const ergebnis = await vonQuelleHolen(url);
      if (ergebnis.bild && zwischenspeichern) {
        await inCacheSchreiben(schluessel, ergebnis.bild);
        void aufraeumen();
      }
      return ergebnis;
    } catch (err) {
      console.warn(`Bild ${url.hostname} nicht geladen: ${err instanceof Error ? err.message : err}`);
      return { bild: null };
    } finally {
      laufend.delete(kennung);
    }
  })();
  laufend.set(kennung, abruf);
  return abruf;
}

/**
 * HTTP-Antwort für ein Bild (oder 404, wenn keins da ist).
 * @param privat true = nur der Browser darf cachen, keine geteilten Caches/CDNs (für Google-Fotos, auch deren 404)
 */
export function bildAntwort(bild: Bild | null, browserCacheSekunden: number, privat = false): Response {
  if (!bild) {
    return new Response("Bild nicht verfügbar", {
      status: 404,
      headers: { "Cache-Control": `${privat ? "private" : "public"}, max-age=300` },
    });
  }
  return new Response(bild.bytes as BodyInit, {
    headers: {
      "Content-Type": bild.typ,
      "Content-Length": String(bild.bytes.byteLength),
      "Cache-Control": `${privat ? "private" : "public"}, max-age=${browserCacheSekunden}`,
      "X-Content-Type-Options": "nosniff",
    },
  });
}
