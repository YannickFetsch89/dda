// Geburtstagsmail (Plan docs/plan-geburtstagsmail-2026-11-20.md, G4): Abmelde-Token und Abmeldung.
// Token: "<nutzer-id>.<HMAC-SHA256(GEBURTSTAG_TOKEN_SCHLUESSEL, "geburtstag:" + nutzer-id), base64url>".
// Erzeugt im Versandjob (pipeline/geburtstag_mails.py), geprüft hier. Ohne Ablauf, nur für diesen Zweck.
import "server-only";
import { schluesselBereinigen } from "@/lib/schluessel";
import { createHmac, timingSafeEqual } from "node:crypto";
import type { SupabaseClient } from "@supabase/supabase-js";
import { einwilligungSetzen } from "./einwilligungen";

const ZWECK = "geburtstag:";
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

function mac(nutzerId: string, schluessel: string): string {
  return createHmac("sha256", schluessel).update(ZWECK + nutzerId, "utf8").digest("base64url");
}

/** Token für eine Nutzer-ID (Tests; der Job erzeugt es in Python mit derselben Rechnung). */
export function geburtstagToken(nutzerId: string, roh: string | undefined = process.env.GEBURTSTAG_TOKEN_SCHLUESSEL): string | null {
  const schluessel = schluesselBereinigen(roh);
  if (!schluessel || !UUID.test(nutzerId)) return null;
  return `${nutzerId}.${mac(nutzerId, schluessel)}`;
}

/** Prüft ein Token; gibt die Nutzer-ID zurück oder null. Vergleich in konstanter Zeit, nie ein Fehler. */
export function geburtstagTokenPruefen(token: unknown, roh: string | undefined = process.env.GEBURTSTAG_TOKEN_SCHLUESSEL): string | null {
  const schluessel = schluesselBereinigen(roh);
  if (!schluessel || typeof token !== "string" || token.length > 200) return null;
  const punkt = token.indexOf(".");
  if (punkt < 0) return null;
  const id = token.slice(0, punkt);
  const gesendet = token.slice(punkt + 1);
  if (!UUID.test(id) || !/^[A-Za-z0-9_-]{43}$/.test(gesendet)) return null;
  const a = Buffer.from(gesendet, "utf8");
  const b = Buffer.from(mac(id, schluessel), "utf8");
  return a.length === b.length && timingSafeEqual(a, b) ? id : null;
}

export type AbmeldeErgebnis = "ok" | "fehler";

/**
 * Geburtstagsmail abbestellen (G4): einwilligung_setzen(geburtstagsmail, false, abmeldelink). Das Geburtsdatum bleibt
 * (E16). Schon abgemeldet oder Konto gelöscht → „ok“ ohne neue Nachweiszeile (die Antwort verrät nichts über das Konto).
 */
export async function geburtstagAbmelden(dienst: SupabaseClient, nutzerId: string): Promise<AbmeldeErgebnis> {
  const { data, error } = await dienst.from("profiles").select("geburtstagsmail").eq("id", nutzerId).maybeSingle();
  if (error) {
    console.error(`Geburtstagsmail abmelden: Profil nicht lesbar (${error.code ?? "fehler"})`);
    return "fehler";
  }
  if (!data || !data.geburtstagsmail) return "ok";
  const r = await einwilligungSetzen(dienst, nutzerId, "geburtstagsmail", false, "abmeldelink");
  return r.ok ? "ok" : "fehler";
}
