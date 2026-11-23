// Admin-Bereich – Sitzung, Rolle und Zwei-Faktor-Stufe (Plan Admin-Dashboard 3.3).
// Token prüfen und erneuern übernimmt sitzungAusAnfrage aus web/lib/konto/ mit dem eigenen Cookie ddd_admin.
// Rolle kommt aus profiles (RLS: eigene Zeile), die Zwei-Faktor-Stufe (aal) aus dem geprüften Access-Token.
import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { nutzerClient } from "../konto/clients";
import { sitzungAusAnfrage, type Sitzung } from "../konto/sitzung";
import { ADMIN_COOKIE_ART } from "./konfig";

export type Aal = "aal1" | "aal2";

export interface AdminSitzung {
  sitzung: Sitzung;
  aal: Aal;
  /** Client mit dem Token des Admins – alle Zugriffe laufen unter RLS (ist_admin()) */
  db: SupabaseClient;
  setCookies: string[];
}

export type AdminSitzungsErgebnis =
  | { ok: true; admin: AdminSitzung }
  | { ok: false; status: 401 | 403 | 503; code: "abgemeldet" | "kein_admin" | "zwei_faktor" | "dienst"; setCookies: string[] };

/**
 * aal aus der Nutzlast eines Tokens. Nur für ein Token aufrufen, das tokenPruefen (Signatur, Ablauf) schon
 * bestanden hat – das passiert in sitzungAusAnfrage.
 */
export function aalAusToken(access: string): Aal {
  try {
    const teil = access.split(".")[1] ?? "";
    const nutzlast = JSON.parse(Buffer.from(teil, "base64url").toString("utf8")) as { aal?: unknown };
    return nutzlast.aal === "aal2" ? "aal2" : "aal1";
  } catch {
    return "aal1";
  }
}

/** Ist das Konto ein Admin? Liest die eigene Profilzeile mit dem Token des Nutzers. */
export async function istAdminKonto(db: SupabaseClient, nutzerId: string): Promise<boolean> {
  try {
    const { data, error } = await db.from("profiles").select("rolle").eq("id", nutzerId).maybeSingle();
    return !error && data?.rolle === "admin";
  } catch {
    return false;
  }
}

/**
 * Sitzung des Admin-Bereichs. `zweiFaktor`: verlangt aal2 (Standard für alle Daten-Routen). Ohne aal2 kommen nur
 * die Routen der Anmeldung und Einrichtung durch.
 */
export async function adminSitzung(request: Request, zweiFaktor = true): Promise<AdminSitzungsErgebnis> {
  const s = await sitzungAusAnfrage(request, Date.now(), ADMIN_COOKIE_ART);
  if (!s.ok) return { ok: false, status: 401, code: "abgemeldet", setCookies: s.setCookies };
  const db = nutzerClient(s.sitzung.access);
  if (!db) return { ok: false, status: 503, code: "dienst", setCookies: s.setCookies };
  if (!(await istAdminKonto(db, s.sitzung.nutzerId))) return { ok: false, status: 403, code: "kein_admin", setCookies: s.setCookies };
  const aal = aalAusToken(s.sitzung.access);
  if (zweiFaktor && aal !== "aal2") return { ok: false, status: 403, code: "zwei_faktor", setCookies: s.setCookies };
  return { ok: true, admin: { sitzung: s.sitzung, aal, db, setCookies: s.setCookies } };
}
