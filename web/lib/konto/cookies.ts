// Nutzerkonten – Cookies (Plan 3.2). Reine Funktionen: Wert kodieren/lesen und Set-Cookie-Zeilen bauen.
// ddd_sitzung: Tokens, HttpOnly, nur an /api/konto. ddd_konto: reiner Anzeige-Hinweis „0“/„1“ für die Oberfläche.
import { HINWEIS_COOKIE, RESET_SITZUNG_SEKUNDEN, SITZUNG_COOKIE, SITZUNG_SEKUNDEN } from "./konfig";

export interface SitzungsWert {
  access: string;
  refresh: string;
  /** Eingeschränkte Reset-Sitzung: nur passwort-setzen und abmelden (Plan 5.1 Schritt 9) */
  nur_passwort?: true;
}

export function sitzungKodieren(wert: SitzungsWert): string {
  return Buffer.from(JSON.stringify(wert), "utf8").toString("base64url");
}

export function sitzungDekodieren(roh: string | null | undefined): SitzungsWert | null {
  if (!roh) return null;
  try {
    const w = JSON.parse(Buffer.from(roh, "base64url").toString("utf8"));
    if (!w || typeof w.access !== "string" || typeof w.refresh !== "string" || !w.access || !w.refresh) return null;
    return { access: w.access, refresh: w.refresh, ...(w.nur_passwort === true ? { nur_passwort: true as const } : {}) };
  } catch {
    return null;
  }
}

/** Einen Cookie-Wert aus dem Cookie-Header lesen. */
export function cookieLesen(headers: Headers, name: string): string | null {
  const kopf = headers.get("cookie");
  if (!kopf) return null;
  for (const teil of kopf.split(";")) {
    const i = teil.indexOf("=");
    if (i > 0 && teil.slice(0, i).trim() === name) return teil.slice(i + 1).trim();
  }
  return null;
}

/** Läuft die Anfrage lokal (dann ohne Secure, sonst kämen die Cookies über http://localhost nicht an)? */
/**
 * Läuft die Anfrage direkt an einen lokalen Next-Server (dev 3100, `next start` 3200)? Nur dann fehlt „Secure“ an den
 * Cookies und gelten die localhost-Ursprünge. Live kommt die Anfrage über nginx mit Host `localhost:3847` – der Host
 * allein reicht also nicht. nginx setzt X-Forwarded-Proto/-For bzw. X-Real-IP; sobald einer davon da ist, ist es keine
 * lokale Anfrage (Vorabprüfung vor dem ersten Deploy, 17.11.2026). Ein Angreifer kann diese Köpfe im Browser seines
 * Opfers nicht setzen, und weglassen kann er sie hinter nginx nicht.
 */
export function istLokal(headers: Headers): boolean {
  const host = (headers.get("host") ?? "").toLowerCase();
  if (!/^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$/.test(host)) return false;
  return !headers.has("x-forwarded-proto") && !headers.has("x-forwarded-for") && !headers.has("x-real-ip");
}

/** Set-Cookie für die Sitzung. Reset-Sitzung: 1 Stunde und Merker nur_passwort. */
export function sitzungsCookie(wert: SitzungsWert, lokal: boolean): string {
  const maxAge = wert.nur_passwort ? RESET_SITZUNG_SEKUNDEN : SITZUNG_SEKUNDEN;
  const kodiert = sitzungKodieren(wert);
  if (kodiert.length > 3500) {
    // Plan 3.2: bei mehr als 3,5 KB auf zwei Cookies verteilen. Bisher nicht nötig (etwa 1,5 KB), daher nur melden.
    console.error(`Sitzungs-Cookie ist ${kodiert.length} Zeichen lang – Aufteilen nötig (Plan 3.2)`);
  }
  return [
    `${SITZUNG_COOKIE}=${kodiert}`,
    "Path=/api/konto",
    `Max-Age=${maxAge}`,
    "HttpOnly",
    "SameSite=Lax",
    ...(lokal ? [] : ["Secure"]),
  ].join("; ");
}

/** Set-Cookie für den Anzeige-Hinweis: „1“ = angemeldet mit Alters-Häkchen, „0“ = angemeldet ohne. */
export function hinweisCookie(wert: "0" | "1", lokal: boolean): string {
  return [`${HINWEIS_COOKIE}=${wert}`, "Path=/", `Max-Age=${SITZUNG_SEKUNDEN}`, "SameSite=Lax", ...(lokal ? [] : ["Secure"])].join("; ");
}

/** Beide Cookies löschen (Abmelden, widerrufene Sitzung, Konto gelöscht). */
export function cookiesLoeschen(lokal: boolean): string[] {
  const secure = lokal ? [] : ["Secure"];
  return [
    [`${SITZUNG_COOKIE}=`, "Path=/api/konto", "Max-Age=0", "HttpOnly", "SameSite=Lax", ...secure].join("; "),
    [`${HINWEIS_COOKIE}=`, "Path=/", "Max-Age=0", "SameSite=Lax", ...secure].join("; "),
  ];
}
