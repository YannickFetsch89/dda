// Nutzerkonten – reine Prüffunktionen ohne Netz (Plan 5.1, 6, 11, Tests 16.1).
import { createHash } from "node:crypto";
import { ERNEUERN_VOR_SEKUNDEN } from "./konfig";
import { weiterPruefen } from "./weiter";

export { weiterPruefen };


/** Passwortregel (Plan 5.1): mindestens 10 Zeichen, höchstens 72 Byte (bcrypt), nicht nur Leerraum. */
export function passwortPruefen(wert: unknown): wert is string {
  if (typeof wert !== "string") return false;
  if (!wert.trim()) return false;
  if ([...wert].length < 10) return false;
  return new TextEncoder().encode(wert).length <= 72;
}

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/** Mailadresse normalisieren: getrimmt, kleingeschrieben; ungültig → null. */
export function adresseNormal(wert: unknown): string | null {
  if (typeof wert !== "string") return null;
  const a = wert.trim().toLowerCase();
  return a.length <= 254 && EMAIL.test(a) ? a : null;
}

/** Schlüssel fürs Bremslimit: nur der SHA-256 der kleingeschriebenen Adresse, nie die Adresse selbst. */
export function adressSchluessel(adresse: string): string {
  return createHash("sha256").update(adresse.trim().toLowerCase()).digest("hex");
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export const uuidGueltig = (wert: unknown): wert is string => typeof wert === "string" && UUID.test(wert);

/**
 * Darf die Route bei der Registrierung den Nachweis von Alter und Nutzungsbedingungen setzen? (Plan 5.1 Schritt 2)
 * Nur für ein Konto, das durch genau diese Anfrage entstanden ist: Eingang − 60 s ≤ created_at ≤ Eingang + 5 s.
 */
export function nachweisImZeitfenster(createdAt: unknown, eingangMs: number): boolean {
  if (typeof createdAt !== "string") return false;
  const t = Date.parse(createdAt);
  if (Number.isNaN(t)) return false;
  return t >= eingangMs - 60_000 && t <= eingangMs + 5_000;
}

/** Nutzlast eines JWT lesen (OHNE Prüfung der Signatur – nur für exp; die Identität prüft sitzung.ts). */
export function jwtNutzlast(jwt: string): Record<string, unknown> | null {
  const teile = jwt.split(".");
  if (teile.length !== 3) return null;
  try {
    const json = Buffer.from(teile[1], "base64url").toString("utf8");
    const daten = JSON.parse(json);
    return daten && typeof daten === "object" ? (daten as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/**
 * Muss das Access-Token erneuert werden? (Plan 3.2)
 * „gueltig“ = noch mehr als 60 s; „erneuern“ = läuft bald ab oder ist abgelaufen; „kaputt“ = kein lesbares JWT → abmelden.
 */
export function tokenLaeuftAb(jwt: string, jetztMs: number): "gueltig" | "erneuern" | "kaputt" {
  const nutzlast = jwtNutzlast(jwt);
  const exp = nutzlast?.exp;
  if (typeof exp !== "number") return "kaputt";
  return exp * 1000 - jetztMs < ERNEUERN_VOR_SEKUNDEN * 1000 ? "erneuern" : "gueltig";
}

/**
 * Erlaubte Ursprünge für ändernde Anfragen mit Cookie (Plan 11.2). Die localhost-Ursprünge (dev 3100,
 * `next start` 3200) gelten nur, wenn die Anfrage selbst an localhost geht – live (Host diesdas.events) nie.
 * Ein Angreifer kann den Host-Kopf im Browser seines Opfers nicht setzen.
 */
export function erlaubteUrspruenge(headers?: Headers): string[] {
  const site = (process.env.SITE_URL ?? "https://diesdas.events").replace(/\/+$/, "");
  const host = (headers?.get("host") ?? "").toLowerCase();
  // Live leitet nginx mit Host localhost:3847 weiter – dann nie die localhost-Ursprünge (siehe istLokal in cookies.ts)
  const hinterProxy = !!headers && (headers.has("x-forwarded-proto") || headers.has("x-forwarded-for") || headers.has("x-real-ip"));
  const lokal = /^(localhost|127\.0\.0\.1)(:\d+)?$/.test(host) && !hinterProxy;
  // Lokal zusätzlich der eigene Ursprung (auch wenn der Dev-Server auf einen freien Port ausweicht, z. B. 3101)
  return lokal ? [site, "http://localhost:3100", "http://localhost:3200", `http://${host}`] : [site];
}

/**
 * CSRF-Schutz (Plan 11.2): Mit Cookie muss Origin einer unserer Ursprünge sein. Mit Bearer-Token (spätere App)
 * und ohne Cookie entfällt die Prüfung.
 */
export function originErlaubt(headers: Headers, erlaubt: string[] = erlaubteUrspruenge(headers)): boolean {
  const bearer = /^Bearer\s+\S+/i.test(headers.get("authorization") ?? "");
  const mitCookie = (headers.get("cookie") ?? "").includes("ddd_sitzung=");
  if (bearer && !mitCookie) return true;
  const origin = headers.get("origin");
  return !!origin && erlaubt.includes(origin.replace(/\/+$/, ""));
}

/** Nur JSON wird angenommen (Plan 6, 11.2). */
export function istJson(headers: Headers): boolean {
  return (headers.get("content-type") ?? "").toLowerCase().split(";")[0].trim() === "application/json";
}

/**
 * Wohin nach Anmeldung bzw. Bestätigung? (Plan 5.1 Schritt 7) Die Sperre unter 16 hat Vorrang vor allem,
 * dann fehlendes Alters-Häkchen und unfertiges Profil (beide /konto/willkommen), sonst das geprüfte `weiter`.
 */
export function zielNachAnmeldung(
  profil: { unter16_gesperrt_am: string | null; mindestalter_bestaetigt_am: string | null; onboarding_fertig_am: string | null } | null,
  weiter: unknown,
): string {
  if (!profil) return "/konto/willkommen";
  if (profil.unter16_gesperrt_am) return "/konto";
  if (!profil.mindestalter_bestaetigt_am || !profil.onboarding_fertig_am) return "/konto/willkommen";
  return weiterPruefen(weiter);
}

// Buchstaben (auch mit Akzent), dazwischen Leerzeichen, Bindestrich, Apostroph, Punkt
const NAME = /^\p{L}[\p{L}\p{M}' ’.\-]*$/u;

/**
 * Vor- oder Nachname (E16): getrimmt, Leerraum innen zu einem Leerzeichen, NFC, 1–60 Zeichen, beginnt mit einem
 * Buchstaben. Ungültig → null. Die Datenbank prüft zusätzlich (Prüfbedingung name_plausibel).
 */
export function nameNormal(wert: unknown): string | null {
  if (typeof wert !== "string") return null;
  const n = wert.normalize("NFC").replace(/\s+/g, " ").trim();
  const laenge = [...n].length;
  return laenge >= 1 && laenge <= 60 && NAME.test(n) ? n : null;
}

/** Geburtsdatum aus dem Formular: echtes Kalenderdatum YYYY-MM-DD ab 1900 (die Altersgrenze prüft die Datenbank). */
export function geburtsdatumGueltig(wert: unknown): wert is string {
  if (typeof wert !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(wert)) return false;
  const d = new Date(`${wert}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === wert && wert >= "1900-01-01";
}
