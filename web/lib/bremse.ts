// Bremse gegen Massenabrufe (Ausfall 23.11.2026 ab 22:41: ein einzelner Client rief /guides/restaurants-cafes rund
// 3.000-mal in kurzer Zeit ab, jede Antwort wurde neu gerechnet, der Node-Prozess lief alle ~40 s voll).
// Im Proxy, also bevor eine Seite gerechnet wird: mehr als MAX Aufrufe je Fenster von derselben Adresse → 429.
// Zähler im Speicher je Prozess (wie lib/formulare.ts zuVieleAnfragen). Die Adresse kommt aus X-Real-IP, das unser
// nginx selbst setzt (live geprüft, siehe absenderIp in lib/formulare.ts). Rein, getestet in web/tests/bremse.test.ts.

export const BREMSE_FENSTER_MS = 60_000;
// 120 statt 40 (27.11.2026): Ein Seitenbesuch löst durch die Vorab-Abrufe von Next.js (Links im Sichtbereich, Kopf- und
// Leistenmenüs) rund ein Dutzend Abrufe unter /guides aus; beim Durchklicken von Restaurants war 40 nach 2–3 Seiten
// erreicht (weiße Seite „Zu viele Anfragen“). Vorab-Abrufe lassen sich im Proxy nicht erkennen: Next entfernt die
// Köpfe rsc/next-router-prefetch und den Parameter _rsc vorher (lokal gemessen). Ein Massenabruf wie am 23.11.
// (rund 3.000 in kurzer Zeit von einer Adresse) wird weiter gestoppt; teure Übersichten haben zusätzlich SAMMEL_MAX.
export const BREMSE_MAX = 120;
const MAX_SCHLUESSEL = 20_000;

const zaehler = new Map<string, { start: number; anzahl: number }>();

/** Adresse des Absenders: X-Real-IP (nginx), sonst letzter X-Forwarded-For-Eintrag. */
export function bremsAdresse(headers: Headers): string {
  const real = headers.get("x-real-ip")?.trim();
  if (real) return real;
  const kette = headers.get("x-forwarded-for")?.split(",").map((s) => s.trim()).filter(Boolean) ?? [];
  return kette.at(-1) || "unbekannt";
}

/** true = zu viele Aufrufe von dieser Adresse im laufenden Fenster (dieser Aufruf zählt mit). */
export function gebremst(adresse: string, jetzt: number = Date.now(), max: number = BREMSE_MAX, fensterMs: number = BREMSE_FENSTER_MS): boolean {
  if (zaehler.size > MAX_SCHLUESSEL) {
    for (const [k, v] of zaehler) if (jetzt - v.start > fensterMs) zaehler.delete(k);
    if (zaehler.size > MAX_SCHLUESSEL) zaehler.clear();
  }
  const z = zaehler.get(adresse);
  if (!z || jetzt - z.start > fensterMs) {
    zaehler.set(adresse, { start: jetzt, anzahl: 1 });
    return false;
  }
  z.anzahl += 1;
  return z.anzahl > max;
}

/**
 * Statische Dateien unter /guides (Icons wie /guides/icons/sp-spielplatz.svg, Guide-Bilder wie /guides/clubs.webp):
 * kosten keine Rechnung und zählen nicht. Vorher zählten sie mit (27.11.2026). Die Guide-
 * Bilder (/guides/<hub>.webp) fielen außerdem unter die gemeinsame Grenze aller Besucher (istGuideUebersicht).
 */
export const istDateiPfad = (pfad: string) => /\.(svg|webp|png|jpe?g|gif|avif|ico|txt|xml|json|woff2?)$/i.test(pfad);

/** Nur für Tests */
export function bremseZuruecksetzen(): void {
  zaehler.clear();
  sammel.clear();
}

// Gemeinsame Grenze je Pfad über alle Adressen (Ausfall 23.11.2026: Die Abrufe kamen von über 1.300 Adressen mit
// demselben User-Agent – die Grenze je Adresse greift dort kaum). Gilt nur für die teuren Guide-Übersichten, die
// bei jedem Aufruf alle Orte mit den Filtern aus der Adresse neu rechnen.
export const SAMMEL_MAX = 60;
const sammel = new Map<string, { start: number; anzahl: number }>();

/** true = für diesen Pfad sind im laufenden Fenster schon zu viele Aufrufe gekommen (von allen Adressen zusammen). */
export function sammelGebremst(schluessel: string, jetzt: number = Date.now(), max: number = SAMMEL_MAX, fensterMs: number = BREMSE_FENSTER_MS): boolean {
  const z = sammel.get(schluessel);
  if (!z || jetzt - z.start > fensterMs) {
    if (sammel.size > 1000) sammel.clear();
    sammel.set(schluessel, { start: jetzt, anzahl: 1 });
    return false;
  }
  z.anzahl += 1;
  return z.anzahl > max;
}

/** Guide-Übersicht (/guides/<hub>, ohne Unterseite) – dort rechnet jede Anfrage alle Orte neu */
export const istGuideUebersicht = (pfad: string) => /^\/guides\/[^/]+$/.test(pfad);

// ---------- Saubere Adressen der Guide-Übersichten (Absicherung nach dem Ausfall 23.11.2026) ----------
// Unbekannte Parameter (Cache-Brecher, Tracking) leitet der Proxy per 308 auf die Adresse ohne sie um, bevor gerechnet
// wird. Nur für Übersichten, deren Filter feststehen (lib/guide-filter.ts, lib/kneipen.ts, lib/clubs.ts). „_rsc“ nutzt
// Next für Seitenwechsel im Browser und bleibt immer.
export const GUIDE_PARAMETER: Readonly<Record<string, readonly string[]>> = {
  "restaurants-cafes": ["typ", "stadtteil", "kueche", "preis", "tags", "sort", "anzahl", "ansicht"],
  "kneipen-bars": ["art", "stadtteil", "spez", "vibe", "hh", "raucher", "sort", "anzahl", "ansicht"],
  clubs: ["art", "stadtteil", "genre", "eintritt", "stufe", "sort", "ansicht"],
};
const INTERN = ["_rsc"];

/**
 * Bereinigte Abfrage für eine Guide-Übersicht oder null, wenn nichts zu ändern ist (auch: Übersicht ohne feste Liste).
 * Entfernt unbekannte Parameter und doppelte Werte desselben Parameters (der erste gilt).
 */
export function parameterBereinigen(pfad: string, suche: URLSearchParams): string | null {
  const hub = pfad.split("/")[2] ?? "";
  const erlaubt = GUIDE_PARAMETER[hub];
  if (!erlaubt) return null;
  const neu = new URLSearchParams();
  let geaendert = false;
  for (const [k, w] of suche) {
    if ((!erlaubt.includes(k) && !INTERN.includes(k)) || neu.has(k)) {
      geaendert = true;
      continue;
    }
    neu.append(k, w);
  }
  return geaendert ? neu.toString().replace(/%2C/g, ",") : null;
}

/** Übersichten, deren Inhalt je Filterkombination gecacht ist (ohne Filter: kaum Kosten, keine gemeinsame Grenze) */
export const GECACHTE_UEBERSICHTEN: readonly string[] = ["restaurants-cafes"];

/** Gemeinsame Grenze nötig? Immer bei Filtern; ohne Filter nur bei Übersichten, die nicht gecacht sind. */
export function sammelGrenzePruefen(pfad: string, suche: URLSearchParams): boolean {
  return hatGuideFilter(suche) || !GECACHTE_UEBERSICHTEN.includes(pfad.split("/")[2] ?? "");
}

/** Hat die Abfrage Filter (also etwas, das die Übersicht neu rechnen lässt)? „_rsc“ zählt nicht. */
export function hatGuideFilter(suche: URLSearchParams): boolean {
  for (const k of suche.keys()) if (!INTERN.includes(k)) return true;
  return false;
}
