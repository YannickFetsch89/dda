// Guide-Hub „Kneipen & Bars“: Merkmale aus extras (nur feste Werte, Happy Hour/Raucher nur mit Beleg)
// sowie Filter und URL-Parameter. Bewusst eigene Datei statt einer Verallgemeinerung von guide-filter.ts,
// damit der Restaurant-Hub unverändert bleibt; für den Club-Hub wiederverwendbar.
import { SEITE, type SortWert, SORTIERUNGEN } from "./guide-filter";
import { slugify } from "./kueche";
import type { DddOrt } from "./typen";

export const SPEZIALITAETEN = ["Craft Beer", "Cocktails", "Altbier", "Wein", "Whisky"] as const;
export const VIBES = ["Gemütlich", "Gesellig", "Draußen sitzen", "Sportsbar"] as const;
/** Filter-Chips Happy Hour / Raucherbereich erst ab so vielen Orten mit belegter Angabe (Entscheidung E6). */
export const MIN_FUER_SCHALTER = 8;

type Spez = (typeof SPEZIALITAETEN)[number];
type Vibe = (typeof VIBES)[number];

function liste<T extends string>(wert: unknown, erlaubt: readonly T[]): T[] {
  return Array.isArray(wert) ? erlaubt.filter((e) => wert.includes(e)) : [];
}

export type Unterart = "kneipe" | "bar" | "brauhaus";
/** Arten für Label und Filter „Art“ (Brauhaus ist eine eigene Unterkategorie). */
export const ARTEN: { wert: Unterart; label: string; mehrzahl: string; icon: string }[] = [
  { wert: "kneipe", label: "Kneipe", mehrzahl: "Kneipen", icon: "sports_bar" },
  { wert: "bar", label: "Bar", mehrzahl: "Bars", icon: "local_bar" },
  { wert: "brauhaus", label: "Brauhaus", mehrzahl: "Brauhäuser", icon: "liquor" },
];

/** Unterart des Ortes (Typ-Label der Card, Filter „Art“). */
export function unterart(o: DddOrt): Unterart {
  const u = o.extras.unterart;
  return u === "bar" || u === "brauhaus" ? u : "kneipe";
}

export const artInfo = (o: DddOrt) => ARTEN.find((a) => a.wert === unterart(o))!;

export const spezialitaeten = (o: DddOrt): Spez[] => liste(o.extras.spezialitaeten, SPEZIALITAETEN);
export const vibes = (o: DddOrt): Vibe[] => liste(o.extras.vibes, VIBES);

/** Happy-Hour-Text – nur mit Textbeleg (von der Einordnung im Code geprüft). */
export function happyHour(o: DddOrt): string | null {
  const hh = o.extras.happy_hour as { text?: unknown; beleg?: unknown } | undefined;
  return hh && typeof hh.text === "string" && hh.text.trim() && typeof hh.beleg === "string" && hh.beleg.trim()
    ? hh.text.trim()
    : null;
}

/** Raucherbereich („innen“ = Raucherkneipe, „aussen“ = ausgewiesener Raucherbereich draußen) – nur mit Beleg. */
export function raucher(o: DddOrt): "innen" | "aussen" | null {
  const r = o.extras.raucher as { wert?: unknown; beleg?: unknown } | undefined;
  if (!r || typeof r.beleg !== "string" || !r.beleg.trim()) return null;
  return r.wert === "innen" || r.wert === "aussen" ? r.wert : null;
}

export const RAUCHER_TEXT = { innen: "Ja – Raucherkneipe", aussen: "Ja – Außenbereich" } as const;

// ── Filter ──────────────────────────────────────────────────────────────────

export interface KneipenFilter {
  arten: Unterart[]; // leer = alle
  stadtteile: string[]; // Slugs (ODER)
  spez: string[]; // Slugs
  vibe: string[]; // Slugs
  hh: boolean;
  raucher: boolean;
  sort: SortWert;
  anzahl: number;
  ansicht: "karte" | "grid"; // Standard: Karte
}

type SP = Record<string, string | string[] | undefined>;
const eins = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) || undefined;
const mehrere = (v: string | string[] | undefined) => (eins(v) ?? "").split(",").map((s) => s.trim()).filter(Boolean);
const SPEZ_SLUGS = new Map(SPEZIALITAETEN.map((s) => [slugify(s), s]));
const VIBE_SLUGS = new Map(VIBES.map((v) => [slugify(v), v]));

export function filterLesen(sp: SP): KneipenFilter {
  const sort = eins(sp.sort);
  const anzahl = Number(eins(sp.anzahl));
  return {
    arten: ARTEN.map((a) => a.wert).filter((w) => mehrere(sp.art).includes(w)),
    stadtteile: [...new Set(mehrere(sp.stadtteil))],
    spez: mehrere(sp.spez).filter((s) => SPEZ_SLUGS.has(s)),
    vibe: mehrere(sp.vibe).filter((s) => VIBE_SLUGS.has(s)),
    hh: eins(sp.hh) === "1",
    raucher: eins(sp.raucher) === "1",
    sort: SORTIERUNGEN.some((s) => s.wert === sort) ? (sort as SortWert) : "empfohlen",
    anzahl: Number.isFinite(anzahl) && anzahl >= SEITE ? Math.min(Math.floor(anzahl), 500) : SEITE,
    ansicht: eins(sp.ansicht) === "grid" ? "grid" : "karte",
  };
}

/** Hat die URL irgendeinen Filter-, Sortier- oder Seiten-Parameter? (→ noindex) */
export function hatParameter(sp: SP): boolean {
  return ["art", "stadtteil", "spez", "vibe", "hh", "raucher", "sort", "anzahl", "ansicht"].some((k) => eins(sp[k]) !== undefined);
}

export function filterHref(basis: string, f: KneipenFilter, aenderung: Partial<KneipenFilter>): string {
  const n = { ...f, anzahl: SEITE, ...aenderung };
  const p = new URLSearchParams();
  if (n.arten.length) p.set("art", ARTEN.map((a) => a.wert).filter((w) => n.arten.includes(w)).join(","));
  if (n.stadtteile.length) p.set("stadtteil", n.stadtteile.join(","));
  if (n.spez.length) p.set("spez", n.spez.join(","));
  if (n.vibe.length) p.set("vibe", n.vibe.join(","));
  if (n.hh) p.set("hh", "1");
  if (n.raucher) p.set("raucher", "1");
  if (n.sort !== "empfohlen") p.set("sort", n.sort);
  if (n.anzahl > SEITE) p.set("anzahl", String(n.anzahl));
  if (n.ansicht === "grid") p.set("ansicht", "grid");
  const qs = p.toString().replace(/%2C/g, ",");
  return qs ? `${basis}?${qs}` : basis;
}

/** Filtern; `ohne` lässt einzelne Filter weg (für die Zählwerte an den Chips). */
export function filtern(orte: DddOrt[], f: KneipenFilter, ohne: (keyof KneipenFilter)[] = []): DddOrt[] {
  const mit = (k: keyof KneipenFilter) => !ohne.includes(k);
  return orte.filter((o) => {
    if (mit("arten") && f.arten.length && !f.arten.includes(unterart(o))) return false;
    if (mit("stadtteile") && f.stadtteile.length && !f.stadtteile.includes(slugify(o.stadtteil ?? ""))) return false;
    if (mit("spez") && f.spez.length) {
      const eigene = spezialitaeten(o).map(slugify);
      if (!f.spez.every((s) => eigene.includes(s))) return false;
    }
    if (mit("vibe") && f.vibe.length) {
      const eigene = vibes(o).map(slugify);
      if (!f.vibe.every((v) => eigene.includes(v))) return false;
    }
    if (mit("hh") && f.hh && !happyHour(o)) return false;
    if (mit("raucher") && f.raucher && !raucher(o)) return false;
    return true;
  });
}

/** Anzahl je Wert einer Merkmalsliste (für Chips mit Zahl). */
export function merkmalZaehlen(orte: DddOrt[], werte: readonly string[], von: (o: DddOrt) => string[]) {
  return werte.map((w) => ({ name: w, slug: slugify(w), anzahl: orte.filter((o) => von(o).includes(w)).length }));
}
