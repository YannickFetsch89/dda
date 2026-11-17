// Nutzerkonten – Supabase-Clients (Plan 3.4, 1.4).
// Lehre aus dem Absturz am 06.11.2026: Jeder Client, der pro Anfrage entsteht, läuft OHNE Sitzungsspeicher und
// OHNE Auffrisch-Timer (autoRefreshToken: false). Sonst hält ein setInterval den Client für immer im Speicher.
import "server-only";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { dienstClient, leseClient } from "../supabase-server";

/** Dienst-Client (Service-Key, einer pro Prozess): Einwilligungen, Löschen, Protokoll (Plan 3.4). */
export const kontoDienstClient = (): SupabaseClient | null => dienstClient();

/** Optionen für jeden anfragebezogenen Client (Test 16.1 „Client-Optionen“). */
export const ANFRAGE_OPTIONEN = {
  auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
} as const;

function zugang(): { url: string; anon: string } | null {
  const url = process.env.SUPABASE_URL;
  const anon = process.env.SUPABASE_KEY;
  return url && anon ? { url, anon } : null;
}

/**
 * Auth-Client für genau eine Anfrage (Erneuern, Anmelden, Passwort ändern, Löschen mit Passwort).
 * Hält eine Sitzung nur im eigenen Speicher und wird danach vom Garbage Collector entfernt.
 */
export function authClientAnfrage(): SupabaseClient | null {
  const z = zugang();
  return z ? createClient(z.url, z.anon, ANFRAGE_OPTIONEN) : null;
}

/**
 * Identität prüfen: Ist das Access-Token echt (Signatur, Ablauf) und von unserem Auth-Server? Liefert sub und
 * Mailadresse. Die Nutzlast eines Cookies darf nie ungeprüft gelten, denn die Routen schreiben mit dem
 * Dienst-Client für genau diese Nutzer-ID. getClaims prüft asymmetrische Tokens lokal über die JWKS (im
 * Prozess zwischengespeichert), bei symmetrischen fragt es den Auth-Server (getUser). Der Client ist der
 * eine Lese-Client pro Prozess: getClaims(jwt) speichert keine Sitzung.
 */
export async function tokenPruefen(access: string): Promise<{ sub: string; email: string | null } | null> {
  const client = leseClient();
  if (!client) return null;
  try {
    const { data, error } = await client.auth.getClaims(access);
    const sub = data?.claims?.sub;
    if (error || typeof sub !== "string" || !sub) return null;
    const email = typeof data.claims.email === "string" ? data.claims.email : null;
    return { sub, email };
  } catch {
    return null;
  }
}

/**
 * Nutzer-Client (Plan 3.4): anon-Key plus Access-Token der geprüften Sitzung. Alle Lese- und Schreibzugriffe auf
 * Konto-Daten laufen darüber, RLS ist damit die zweite Mauer hinter der API-Prüfung.
 */
export function nutzerClient(access: string): SupabaseClient | null {
  const z = zugang();
  if (!z) return null;
  return createClient(z.url, z.anon, {
    ...ANFRAGE_OPTIONEN,
    global: { headers: { Authorization: `Bearer ${access}` } },
  });
}
