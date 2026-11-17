// Interessen (praeferenzen, Plan 4.2): Server prüft gegen Whitelists und lässt Unbekanntes still weg.
import { KATEGORIEN } from "../kategorien";
import { BEZIRKE } from "../stadtteile";
import { GUIDE_NACHBARSTAEDTE, stadtteilSlug } from "../landing";
import { VORLIEBEN_MAX_JE_LISTE } from "./konfig";

export interface Vorlieben {
  version: 1;
  kategorien: string[];
  unterkategorien: string[];
  stadtteile: string[];
  merkmale: string[];
  orte: string[];
}

export const MERKMALE = ["kostenlos", "mit-kindern", "abends", "tagsueber", "wochenende"] as const;
export const ORTE = ["restaurants-cafes", "kneipen-bars", "clubs", "spielplaetze"] as const;

const KATEGORIE_SLUGS = new Set(KATEGORIEN.filter((k) => k.slug !== "sonstiges").map((k) => k.slug as string));
const UNTERKATEGORIEN = new Set(
  KATEGORIEN.filter((k) => k.slug !== "sonstiges").flatMap((k) => k.unterkategorien.map((u) => `${k.slug}/${u.slug}`)),
);
const STADTTEILE = new Set([...BEZIRKE.flatMap((b) => b.stadtteile), ...GUIDE_NACHBARSTAEDTE].map(stadtteilSlug));

function liste(wert: unknown, erlaubt: ReadonlySet<string>): string[] {
  if (!Array.isArray(wert)) return [];
  const raus: string[] = [];
  for (const w of wert) {
    if (typeof w !== "string" || !erlaubt.has(w) || raus.includes(w)) continue;
    raus.push(w);
    if (raus.length >= VORLIEBEN_MAX_JE_LISTE) break;
  }
  return raus;
}

/** Prüft praeferenzen aus dem Body. Kein Objekt → null (Route antwortet 400). */
export function vorliebenPruefen(roh: unknown): Vorlieben | null {
  if (!roh || typeof roh !== "object" || Array.isArray(roh)) return null;
  const r = roh as Record<string, unknown>;
  return {
    version: 1,
    kategorien: liste(r.kategorien, KATEGORIE_SLUGS),
    unterkategorien: liste(r.unterkategorien, UNTERKATEGORIEN),
    stadtteile: liste(r.stadtteile, STADTTEILE),
    merkmale: liste(r.merkmale, new Set(MERKMALE)),
    orte: liste(r.orte, new Set(ORTE)),
  };
}

/** Enthält mindestens eine Liste etwas? (Sonst gibt es nichts zu speichern.) */
export const vorliebenLeer = (v: Vorlieben) =>
  !v.kategorien.length && !v.unterkategorien.length && !v.stadtteile.length && !v.merkmale.length && !v.orte.length;
