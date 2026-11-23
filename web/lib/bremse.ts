// Bremse gegen Massenabrufe (Ausfall 23.11.2026 ab 22:41: ein einzelner Client rief /guides/restaurants-cafes rund
// 3.000-mal in kurzer Zeit ab, jede Antwort wurde neu gerechnet, der Node-Prozess lief alle ~40 s voll).
// Im Proxy, also bevor eine Seite gerechnet wird: mehr als MAX Aufrufe je Fenster von derselben Adresse → 429.
// Zähler im Speicher je Prozess (wie lib/formulare.ts zuVieleAnfragen). Die Adresse kommt aus X-Real-IP, das unser
// nginx selbst setzt (live geprüft, siehe absenderIp in lib/formulare.ts). Rein, getestet in web/tests/bremse.test.ts.

export const BREMSE_FENSTER_MS = 60_000;
export const BREMSE_MAX = 40;
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

/** Nur für Tests */
export function bremseZuruecksetzen(): void {
  zaehler.clear();
}
