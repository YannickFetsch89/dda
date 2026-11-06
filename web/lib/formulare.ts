// Gemeinsame Server-Helfer für die Website-Formulare (Newsletter, Event melden).
// Der Browser schickt nur an unseren eigenen Server (Route-Handler). Geschrieben wird serverseitig mit
// dem Service-Key – der anon-Key (gilt als öffentlich) hat auf diese Tabellen und den Upload-Bucket
// KEINE Rechte (database/meldungen_haertung_2026-11-05.sql). So führt der einzige Weg in die Tabellen
// über diese Routen mit Prüfung, Honeypot und Bremslimit. Der Service-Key bleibt auf dem Server
// ("server-only"), er steht in web/.env.local (vom Deploy aus dem GitHub-Secret geschrieben).
import "server-only";
import { dienstClient } from "./supabase-server";

/** Gemeinsamer Schreib-Client mit Service-Key (einer pro Prozess, siehe lib/supabase-server.ts). */
export function schreibClient() {
  const client = dienstClient();
  if (!client) console.error("SUPABASE_URL / SUPABASE_SERVICE_KEY fehlen – Formulare können nicht speichern");
  return client;
}

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
export function emailGueltig(wert: string): boolean {
  return wert.length <= 254 && EMAIL.test(wert);
}

const STEUERZEICHEN = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g;

/** Mehrzeiliger Text: trimmen, Steuerzeichen raus (Zeilenumbrüche bleiben), kürzen; leer → null. */
export function text(wert: FormDataEntryValue | unknown, max: number): string | null {
  if (typeof wert !== "string") return null;
  const t = wert.replace(STEUERZEICHEN, "").trim();
  return t ? t.slice(0, max) : null;
}

/** Einzeiliger Text: wie text(), aber jeder Leerraum (auch Tab/Zeilenumbruch) wird zu einem Leerzeichen. */
export function zeile(wert: FormDataEntryValue | unknown, max: number): string | null {
  if (typeof wert !== "string") return null;
  const t = wert.replace(STEUERZEICHEN, " ").replace(/\s+/g, " ").trim();
  return t ? t.slice(0, max) : null;
}

/** Echtes Kalenderdatum im Format YYYY-MM-DD (lehnt z.B. 2026-02-31 ab). */
export function kalenderdatum(wert: string | null): boolean {
  if (!wert || !/^\d{4}-\d{2}-\d{2}$/.test(wert)) return false;
  const d = new Date(`${wert}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === wert;
}

/**
 * IP des Absenders. X-Real-IP setzt unser nginx (ISPConfig) selbst und überschreibt dabei einen vom
 * Client mitgeschickten Wert – live geprüft am 05.11.2026: 7 Anfragen mit 7 verschiedenen gefälschten
 * X-Real-IP/X-Forwarded-For-Werten → ab der 6. kam 429. Ändert sich der Proxy, das hier neu prüfen.
 * Fallback: letzter X-Forwarded-For-Eintrag (den hängt der Proxy an, alle davor setzt der Client).
 */
export function absenderIp(headers: Headers): string {
  const real = headers.get("x-real-ip")?.trim();
  if (real) return real;
  const kette = headers.get("x-forwarded-for")?.split(",").map((s) => s.trim()).filter(Boolean) ?? [];
  return kette.at(-1) || "unbekannt";
}

/** Anfrage größer als erlaubt (laut Content-Length)? Ohne Angabe gilt sie als zu groß. */
export function zuGross(request: Request, maxBytes: number): boolean {
  const laenge = Number(request.headers.get("content-length"));
  return !Number.isFinite(laenge) || laenge <= 0 || laenge > maxBytes;
}

// Einfaches Bremslimit im Speicher des Server-Prozesses (pro Formular und IP). Reicht für einen
// einzelnen Next-Prozess; bei Neustart beginnt es von vorn. Die Zahl der Schlüssel ist hart begrenzt.
const zugriffe = new Map<string, number[]>();
const MAX_SCHLUESSEL = 10_000;
let letzteBereinigung = 0;

export function zuVieleAnfragen(formular: string, ip: string, max: number, fensterMs: number): boolean {
  const jetzt = Date.now();
  // Höchstens einmal pro Minute: abgelaufene Einträge (IP-Adressen) aus dem Speicher werfen
  if (jetzt - letzteBereinigung > 60_000) {
    letzteBereinigung = jetzt;
    for (const [k, v] of zugriffe) if (!v.some((t) => jetzt - t < fensterMs)) zugriffe.delete(k);
  }
  const schluessel = `${formular}|${ip}`;
  const liste = (zugriffe.get(schluessel) ?? []).filter((t) => jetzt - t < fensterMs);
  if (liste.length >= max) {
    zugriffe.set(schluessel, liste);
    return true;
  }
  liste.push(jetzt);
  zugriffe.delete(schluessel); // neu einfügen → steht in der Map-Reihenfolge hinten (zuletzt genutzt)
  zugriffe.set(schluessel, liste);
  if (zugriffe.size > MAX_SCHLUESSEL) {
    // Erst Abgelaufene entfernen, dann notfalls die am längsten nicht genutzten
    for (const [k, v] of zugriffe) if (!v.some((t) => jetzt - t < fensterMs)) zugriffe.delete(k);
    for (const k of zugriffe.keys()) {
      if (zugriffe.size <= MAX_SCHLUESSEL * 0.8) break;
      zugriffe.delete(k);
    }
  }
  return false;
}

export const antwort = (status: number, daten: Record<string, unknown>) =>
  Response.json(daten, { status, headers: { "Cache-Control": "no-store" } });
