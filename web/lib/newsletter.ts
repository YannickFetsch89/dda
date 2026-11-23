// Newsletter mit Double-Opt-in (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.9, Stufe 4).
// Tokens wie bei der Geburtstagsmail: "<id>.<HMAC-SHA256(NEWSLETTER_TOKEN_SCHLUESSEL, zweck + id), base64url>" mit den
// Zwecken „newsletter-bestaetigen:“ und „newsletter-abmelden:“ – gleich wie pipeline/newsletter_bestaetigung.py.
// Getestet in web/tests/newsletter.test.ts.
import { createHmac, timingSafeEqual } from "node:crypto";

export type TokenZweck = "bestaetigen" | "abmelden";
const ZWECK: Record<TokenZweck, string> = { bestaetigen: "newsletter-bestaetigen:", abmelden: "newsletter-abmelden:" };
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function mac(id: string, zweck: TokenZweck, schluessel: string): string {
  return createHmac("sha256", schluessel).update(ZWECK[zweck] + id, "utf8").digest("base64url");
}

/** Token für eine Anmeldung (Tests; der Job erzeugt es in Python mit derselben Rechnung). */
export function newsletterToken(id: string, zweck: TokenZweck, schluessel: string | undefined = process.env.NEWSLETTER_TOKEN_SCHLUESSEL): string | null {
  if (!schluessel || !UUID.test(id)) return null;
  return `${id}.${mac(id, zweck, schluessel)}`;
}

/** Anmelde-ID aus einem gültigen Token, sonst null (zeitkonstanter Vergleich; ein Token gilt nur für seinen Zweck). */
export function newsletterTokenPruefen(token: unknown, zweck: TokenZweck, schluessel: string | undefined = process.env.NEWSLETTER_TOKEN_SCHLUESSEL): string | null {
  if (!schluessel || typeof token !== "string" || token.length > 200) return null;
  const punkt = token.indexOf(".");
  if (punkt < 0) return null;
  const id = token.slice(0, punkt);
  if (!UUID.test(id)) return null;
  const a = Buffer.from(token.slice(punkt + 1));
  const b = Buffer.from(mac(id, zweck, schluessel));
  return a.length === b.length && timingSafeEqual(a, b) ? id.toLowerCase() : null;
}

/**
 * RFC 8058: Eine One-Click-Abmeldung ist ein POST mit Content-Type application/x-www-form-urlencoded und genau dem
 * Body „List-Unsubscribe=One-Click“ (Cursor-Prüfung 4, Befund 1). Alles andere meldet nicht ab.
 */
export function istOneClick(contentType: string | null, body: string): boolean {
  const art = (contentType ?? "").split(";")[0].trim().toLowerCase();
  if (art !== "application/x-www-form-urlencoded") return false;
  const felder = new URLSearchParams(body.trim());
  return [...felder.keys()].length === 1 && felder.get("List-Unsubscribe") === "One-Click";
}

export interface Bestand {
  id: string;
  bestaetigt_am: string | null;
  bestaetigung_gesendet_am: string | null;
  bestaetigung_zugestellt_am?: string | null;
  mails_gesendet: number | null;
}

/** Höchstens so viele Bestätigungsmails je Adresse (Schutz gegen Missbrauch des Formulars mit fremden Adressen) */
export const MAX_MAILS = 3;
const ERNEUT_NACH_MS = 24 * 3600 * 1000;

/**
 * Was eine (erneute) Anmeldung bewirkt – nach außen immer dieselbe Antwort, damit niemand erfährt, ob eine Adresse
 * angemeldet ist: neue Adresse → anlegen (der Job schickt die Mail); schon bestätigt → nichts; unbestätigt und die
 * letzte Mail älter als 24 Stunden → noch einmal schicken (höchstens MAX_MAILS); sonst nichts.
 */
export function anmeldungPlanen(bestand: Bestand | null, jetzt: number = Date.now()): "anlegen" | "erneut_senden" | "nichts" {
  if (!bestand) return "anlegen";
  if (bestand.bestaetigt_am) return "nichts";
  // Noch nicht zugestellt: Der Job schickt sie ohnehin (auch einen hängengebliebenen Anspruch nach 30 Minuten)
  if (!bestand.bestaetigung_zugestellt_am) return "nichts";
  if ((bestand.mails_gesendet ?? 0) >= MAX_MAILS) return "nichts";
  return jetzt - Date.parse(bestand.bestaetigung_zugestellt_am) > ERNEUT_NACH_MS ? "erneut_senden" : "nichts";
}
