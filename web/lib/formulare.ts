// Gemeinsame Server-Helfer für die Website-Formulare (Newsletter, Event melden).
// Der Browser schickt nur an unseren eigenen Server (Route-Handler) – Supabase wird ausschließlich
// serverseitig mit dem anon-Key angesprochen. Per RLS darf dieser nur NEUE Einträge anlegen
// (database/meldungen_newsletter_2026-11-05.sql), nichts lesen.
import "server-only";
import { createClient } from "@supabase/supabase-js";

export function schreibClient() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!url || !key) return null;
  return createClient(url, key, { auth: { persistSession: false } });
}

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
export function emailGueltig(wert: string): boolean {
  return wert.length <= 254 && EMAIL.test(wert);
}

/** Text säubern: trimmen, Steuerzeichen raus, auf Höchstlänge kürzen; leer → null. */
export function text(wert: FormDataEntryValue | unknown, max: number): string | null {
  if (typeof wert !== "string") return null;
  const t = wert.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "").trim();
  return t ? t.slice(0, max) : null;
}

/** IP des Absenders (hinter dem Reverse-Proxy des Servers aus X-Forwarded-For). */
export function absenderIp(headers: Headers): string {
  return headers.get("x-forwarded-for")?.split(",")[0].trim() || headers.get("x-real-ip") || "unbekannt";
}

// Einfaches Bremslimit im Speicher des Server-Prozesses (pro Formular und IP). Reicht für einen
// einzelnen Next-Prozess; bei Neustart beginnt es von vorn.
const zugriffe = new Map<string, number[]>();

export function zuVieleAnfragen(formular: string, ip: string, max: number, fensterMs: number): boolean {
  const jetzt = Date.now();
  const schluessel = `${formular}|${ip}`;
  const liste = (zugriffe.get(schluessel) ?? []).filter((t) => jetzt - t < fensterMs);
  if (liste.length >= max) {
    zugriffe.set(schluessel, liste);
    return true;
  }
  liste.push(jetzt);
  zugriffe.set(schluessel, liste);
  // Speicher klein halten
  if (zugriffe.size > 5000) {
    for (const [k, v] of zugriffe) if (!v.some((t) => jetzt - t < fensterMs)) zugriffe.delete(k);
  }
  return false;
}

export const antwort = (status: number, daten: Record<string, unknown>) =>
  Response.json(daten, { status, headers: { "Cache-Control": "no-store" } });
