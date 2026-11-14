// Guide „Spielplätze“ (Plan docs/plan-spielplaetze-2026-11-12.md, Abschnitt 5): reine Funktionen ohne Netz.
// Profil nur aus bekannten Werten lesen, Filter, Indexierbarkeit, Alter, Namensstamm, Entfernung.
// Die Regeln für Indexierbarkeit müssen zu scraper/spielplaetze/score.py passen (gemeinsame Fixture in tests/fixtures).
import { inStadtteil, stadtteilSlug } from "./landing";
import type { DddOrt } from "./typen";

export type SpielplatzTyp = "kinder" | "wald" | "wasser" | "abenteuer";
export type Alter = "0-3" | "3-6" | "6-12" | "alle";
export type Wert = "ja" | "nein" | "teilweise";

export interface Eintrag { wert: Wert; quelle?: string; beleg?: string; url?: string; notiz?: string | null; stand?: string }
export interface SpielplatzDaten {
  quelle?: string;
  typ?: SpielplatzTyp;
  teile?: { objektschluessel: string; stadt_name: string; objektart: string; groesse_m2: number | null }[];
  groesse_m2?: number | null;
  notfallnummer?: string | null;
  datenstand?: string;
  quelle_url?: string;
  traeger?: string | null;
  eintritt?: "ja" | "nein" | null;
  ausstattung?: Record<string, Eintrag>;
  extras?: Record<string, Eintrag>;
  alter?: { wert: Alter; art: "belegt" | "vermutlich"; beleg?: string; quelle?: string } | null;
  saison?: { text: string; beleg?: string; url?: string } | null;
  beschreibung?: string | null;
  highlight?: string | null;
  profil_stand?: string | null;
  profil?: { quellen?: string[]; datum?: string } | null;
  osm?: { id?: string | null } | null;
  score?: number;
  top?: boolean;
}

// ---------- Konstanten ----------

/** Filter-Geräte (Chip ab 5 sichtbaren Plätzen) – Schlüssel wie in extras.spielplatz.ausstattung */
export const GERAETE: { wert: string; label: string; icon: string }[] = [
  { wert: "sandkasten", label: "Sandkasten", icon: "sp:sandkasten" },
  { wert: "schaukel", label: "Schaukel", icon: "sp:schaukel" },
  { wert: "rutsche", label: "Rutsche", icon: "sp:rutsche" },
  { wert: "klettern", label: "Klettern", icon: "landscape" },
  { wert: "wasserspiel", label: "Wasserspiel", icon: "water_drop" },
  { wert: "seilbahn", label: "Seilbahn", icon: "cable" },
  { wert: "tischtennis", label: "Tischtennis", icon: "sports_tennis" },
  { wert: "fussball", label: "Fußball", icon: "sports_soccer" },
  { wert: "basketball", label: "Basketball", icon: "sports_basketball" },
];
export const NEBENGERAETE: { wert: string; label: string }[] = [
  { wert: "federwippe", label: "Federwippe" }, { wert: "wippe", label: "Wippe" }, { wert: "karussell", label: "Karussell" },
  { wert: "balancierbalken", label: "Balancierbalken" }, { wert: "volleyball", label: "Volleyball" }, { wert: "skaten", label: "Skaten" },
];
export const EXTRAS: { wert: string; label: string; icon: string }[] = [
  { wert: "schatten", label: "Schatten", icon: "beach_access" },
  { wert: "wc", label: "WC", icon: "wc" },
  { wert: "eingezaeunt", label: "Eingezäunt", icon: "fence" },
  { wert: "picknick", label: "Picknick", icon: "deck" },
  { wert: "rollstuhl", label: "Rollstuhlgerecht", icon: "accessible" },
];
export const ALTERSGRUPPEN: { wert: Alter; label: string; kurz: string }[] = [
  // Farben aus dem Design-Handoff (14_spielplaetze/data/spielplaetze.json), als CSS-Klassen sp-alter--<wert>
  { wert: "0-3", label: "0–3 Jahre", kurz: "0–3 Jahre" },
  { wert: "3-6", label: "3–6 Jahre", kurz: "3–6 Jahre" },
  { wert: "6-12", label: "6–12 Jahre", kurz: "6–12 Jahre" },
  { wert: "alle", label: "Für alle Altersgruppen", kurz: "alle Altersgruppen" },
];
export const TYPEN: { wert: SpielplatzTyp; label: string; mehrzahl: string; icon: string; bild: string }[] = [
  { wert: "kinder", label: "Spielplatz", mehrzahl: "Spielplätze", icon: "sp:spielplatz", bild: "/guides/spielplatz-typ-kinder.webp" },
  { wert: "wasser", label: "Wasserspielplatz", mehrzahl: "Wasserspielplätze", icon: "water_drop", bild: "/guides/spielplatz-typ-wasser.webp" },
  { wert: "wald", label: "Waldspielplatz", mehrzahl: "Waldspielplätze", icon: "forest", bild: "/guides/spielplatz-typ-wald.webp" },
  { wert: "abenteuer", label: "Abenteuerspielplatz", mehrzahl: "Abenteuerspielplätze", icon: "cottage", bild: "/guides/spielplatz-typ-kinder.webp" },
];
/** Chips für Geräte und Extras erst ab so vielen sichtbaren Plätzen mit Beleg (E11) */
export const CHIP_SCHWELLE = 5;
const BELEG_QUELLEN = ["osm", "zitat", "sichtung"];

// ---------- Profil lesen ----------

export function spielplatz(o: DddOrt): SpielplatzDaten {
  const sp = o.extras?.spielplatz;
  return sp && typeof sp === "object" ? (sp as SpielplatzDaten) : {};
}

export function typInfo(o: DddOrt) {
  const t = spielplatz(o).typ;
  return TYPEN.find((x) => x.wert === t) ?? TYPEN[0];
}

/** Belegte Filter-Geräte (wert ja, Quelle OSM/Zitat/Sichtung, mit Beleg). */
export function belegteGeraete(sp: SpielplatzDaten, auswahl = GERAETE.map((g) => g.wert)): string[] {
  return Object.entries(sp.ausstattung ?? {})
    .filter(([k, v]) => auswahl.includes(k) && v?.wert === "ja" && BELEG_QUELLEN.includes(v.quelle ?? "") && !!v.beleg)
    .map(([k]) => k);
}

/** Detail indexierbar: Profil-Beschreibung und ≥ 2 belegte Geräte (5.4). Vermutetes Alter ersetzt keins. */
export function istIndexierbar(sp: SpielplatzDaten): boolean {
  return !!sp.beschreibung?.trim() && belegteGeraete(sp).length >= 2;
}

export const ortIndexierbar = (o: DddOrt) => istIndexierbar(spielplatz(o));

export function extraWert(sp: SpielplatzDaten, merkmal: string): Eintrag | null {
  const e = sp.extras?.[merkmal];
  return e && (e.wert === "ja" || e.wert === "nein" || e.wert === "teilweise") ? e : null;
}

export function alterInfo(o: DddOrt) {
  const a = spielplatz(o).alter;
  const g = a ? ALTERSGRUPPEN.find((x) => x.wert === a.wert) : undefined;
  return g ? { ...g, vermutlich: a!.art === "vermutlich" } : null;
}

/** „3–6 Jahre“ bzw. „vermutlich 3–6 Jahre“ */
export function alterText(o: DddOrt): string | null {
  const a = alterInfo(o);
  return a ? `${a.vermutlich ? "vermutlich " : ""}${a.kurz}` : null;
}

/** Slug des Stadtteils für Filter (Anzeigename: „Hafen“ → „medienhafen“), leer ohne Stadtteil. */
export const ortStadtteilSlug = (o: DddOrt) => (o.stadtteil ? stadtteilSlug(o.stadtteil) : "");

/** Titel-Muster „{Name} {inStadtteil}“ ohne Gedankenstrich (5.3). */
export function spielplatzTitel(o: DddOrt): string {
  return o.stadtteil ? `${o.name} ${inStadtteil(o.stadtteil)}` : o.name;
}

// ---------- Filter ----------

export type SortWert = "empfohlen" | "ausstattung";
export const SORTIERUNGEN: { wert: SortWert; label: string }[] = [
  { wert: "empfohlen", label: "Empfohlen" },
  { wert: "ausstattung", label: "Beste Ausstattung" },
];

export interface SpielplatzFilter {
  alter: Alter | null;
  geraete: string[];
  extras: string[];
  typen: SpielplatzTyp[];
  stadtteile: string[]; // Slugs wie in guide-filter (zaehlen)
  sort: SortWert;
}
export const STANDARD: SpielplatzFilter = { alter: null, geraete: [], extras: [], typen: [], stadtteile: [], sort: "empfohlen" };

type SP = Record<string, string | string[] | undefined>;
const liste = (w: string | string[] | undefined) => (Array.isArray(w) ? w.join(",") : w ?? "").split(",").map((s) => s.trim()).filter(Boolean);

export function filterLesen(sp: SP): SpielplatzFilter {
  const alter = liste(sp.alter)[0];
  const sort = liste(sp.sort)[0];
  return {
    alter: ALTERSGRUPPEN.some((g) => g.wert === alter) ? (alter as Alter) : null,
    geraete: liste(sp.geraet).filter((g) => GERAETE.some((x) => x.wert === g)),
    extras: liste(sp.extra).filter((g) => EXTRAS.some((x) => x.wert === g)),
    typen: liste(sp.typ).filter((t): t is SpielplatzTyp => TYPEN.some((x) => x.wert === t)),
    stadtteile: liste(sp.stadtteil),
    sort: SORTIERUNGEN.some((s) => s.wert === sort) ? (sort as SortWert) : "empfohlen",
  };
}

/** Hat die URL Filter-Parameter? Dann noindex mit Canonical auf den Hub. */
export function hatParameter(sp: SP): boolean {
  return ["alter", "geraet", "extra", "typ", "stadtteil", "sort"].some((k) => liste(sp[k]).length > 0);
}

export function filterHref(basis: string, f: SpielplatzFilter, a: Partial<SpielplatzFilter>): string {
  const n = { ...f, ...a };
  const q = new URLSearchParams();
  if (n.alter) q.set("alter", n.alter);
  if (n.geraete.length) q.set("geraet", n.geraete.join(","));
  if (n.extras.length) q.set("extra", n.extras.join(","));
  if (n.typen.length) q.set("typ", n.typen.join(","));
  if (n.stadtteile.length) q.set("stadtteil", n.stadtteile.join(","));
  if (n.sort !== "empfohlen") q.set("sort", n.sort);
  const s = q.toString();
  return s ? `${basis}?${s}` : basis;
}

/** „alle“ passt zu jedem Altersfilter; ohne Alter nur unter „Alle Alter“ (kein Filter). */
export function alterPasst(o: DddOrt, alter: Alter | null): boolean {
  if (!alter) return true;
  const a = spielplatz(o).alter?.wert;
  return a === alter || a === "alle";
}

/** Filter (5.1): Gerät mit „ja“, unabhängig von der Quelle. */
export const geraetJa = (o: DddOrt, g: string) => spielplatz(o).ausstattung?.[g]?.wert === "ja";
/** Belegt (5.2/E11): „ja“ mit Quelle OSM/Zitat/Sichtung und Beleg – für „X von Y“, Sortierung und Chip-Schwelle. */
const belegt = (e: Eintrag | undefined) => e?.wert === "ja" && BELEG_QUELLEN.includes(e.quelle ?? "") && !!e.beleg;
export const geraetBelegt = (o: DddOrt, g: string) => belegt(spielplatz(o).ausstattung?.[g]);
export const extraBelegt = (o: DddOrt, e: string) => belegt(extraWert(spielplatz(o), e) ?? undefined);
/** Extra gilt nur mit „ja“ (Rollstuhl „teilweise“ zählt nicht, E11). */
export const extraJa = (o: DddOrt, e: string) => extraWert(spielplatz(o), e)?.wert === "ja";

export function filtern(orte: DddOrt[], f: SpielplatzFilter, stadtteilSlug: (o: DddOrt) => string, ohne: (keyof SpielplatzFilter)[] = []): DddOrt[] {
  return orte.filter((o) =>
    (ohne.includes("alter") || alterPasst(o, f.alter)) &&
    (ohne.includes("geraete") || f.geraete.every((g) => geraetJa(o, g))) &&
    (ohne.includes("extras") || f.extras.every((e) => extraJa(o, e))) &&
    (ohne.includes("typen") || !f.typen.length || f.typen.includes(typInfo(o).wert)) &&
    (ohne.includes("stadtteile") || !f.stadtteile.length || f.stadtteile.includes(stadtteilSlug(o))));
}

export function sortieren(orte: DddOrt[], sort: SortWert): DddOrt[] {
  const name = (a: DddOrt, b: DddOrt) => a.name.localeCompare(b.name, "de");
  if (sort === "ausstattung") {
    const n = (o: DddOrt) => belegteGeraete(spielplatz(o)).length;
    return [...orte].sort((a, b) => n(b) - n(a) || name(a, b));
  }
  const score = (o: DddOrt) => spielplatz(o).score ?? 0;
  return [...orte].sort((a, b) => score(b) - score(a) || name(a, b));
}

/** „Ausstattung für X von Y erfasst“: X = mindestens ein belegtes Filter-Gerät. */
export function erfasst(orte: DddOrt[]): number {
  return orte.filter((o) => belegteGeraete(spielplatz(o)).length > 0).length;
}

/**
 * Geräte-/Extra-Chips: erst ab CHIP_SCHWELLE sichtbaren Plätzen mit Beleg (belegtHat, E11); aktive Chips bleiben.
 * Die Zahl am Chip zählt wie der Filter (hat), damit sie zur Trefferzahl nach dem Klick passt.
 */
export function chips<T extends { wert: string }>(
  orte: DddOrt[], liste: T[], hat: (o: DddOrt, w: string) => boolean, aktiv: string[], belegtHat: (o: DddOrt, w: string) => boolean = hat,
) {
  return liste.map((x) => ({ ...x, anzahl: orte.filter((o) => hat(o, x.wert)).length, belegt: orte.filter((o) => belegtHat(o, x.wert)).length }))
    .filter((x) => x.belegt >= CHIP_SCHWELLE || aktiv.includes(x.wert));
}

// ---------- „In der Nähe“ ----------

const TYPWOERTER = /^(wasserspielplatz|waldspielplatz|abenteuerspielplatz|spielplatz)\s+/i;

/** Namensstamm: ohne führendes Typwort und ohne Klammerzusatz („Spielplatz Hanielpark (…)“ → „Hanielpark“). */
export function namensStamm(name: string): string {
  return name.replace(TYPWOERTER, "").replace(/\s*\(.*\)\s*$/, "").trim().toLowerCase();
}

/** Entfernung in Metern (Haversine). */
export function entfernungM(a: { lat: number; lng: number }, b: { lat: number; lng: number }): number {
  const r = (x: number) => (x * Math.PI) / 180;
  const h = Math.sin(r(b.lat - a.lat) / 2) ** 2 + Math.cos(r(a.lat)) * Math.cos(r(b.lat)) * Math.sin(r(b.lng - a.lng) / 2) ** 2;
  return 2 * 6371000 * Math.asin(Math.sqrt(h));
}

export function entfernungText(m: number): string {
  return m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1).replace(".", ",")} km`;
}

const punkt = (o: DddOrt) => (o.latitude != null && o.longitude != null ? { lat: o.latitude, lng: o.longitude } : null);

/** „Weitere Spielplätze in {Park}“ bei gleichem Stamm, sonst die 3 nächsten. */
export function nachbarn(o: DddOrt, alle: DddOrt[]): { titel: string; orte: { o: DddOrt; m: number | null }[] } {
  const stamm = namensStamm(o.name);
  const p = punkt(o);
  const mitAbstand = (x: DddOrt) => {
    const q = punkt(x);
    return { o: x, m: p && q ? entfernungM(p, q) : null };
  };
  const gleich = stamm ? alle.filter((x) => x.id !== o.id && namensStamm(x.name) === stamm) : [];
  if (gleich.length) {
    const park = o.name.replace(TYPWOERTER, "").replace(/\s*\(.*\)\s*$/, "").trim();
    return { titel: `Weitere Spielplätze: ${park}`, orte: gleich.slice(0, 3).map(mitAbstand) };
  }
  const naechste = alle.filter((x) => x.id !== o.id && punkt(x)).map(mitAbstand)
    .sort((a, b) => (a.m ?? Infinity) - (b.m ?? Infinity)).slice(0, 3);
  return { titel: "Weitere Spielplätze in der Nähe", orte: naechste };
}

const istWasserTeil = (t: { objektart: string }) => /wasserspielplatz/i.test(t.objektart);

/**
 * Saison-Hinweis (5.3), nur mit Text aus einer Quelle: Ist eine Kinder-Teilfläche größer als die Wasser-Teilfläche,
 * gilt die Saison nur für den Wasserbereich; sonst steht sie nur bei Typ Wasser, für den ganzen Platz.
 */
export function saisonHinweis(sp: SpielplatzDaten): { text: string; label: string } | null {
  if (!sp.saison?.text) return null;
  const teile = sp.teile ?? [];
  const wasser = Math.max(0, ...teile.filter(istWasserTeil).map((t) => t.groesse_m2 ?? 0));
  const kinder = Math.max(0, ...teile.filter((t) => !istWasserTeil(t)).map((t) => t.groesse_m2 ?? 0));
  if (teile.some(istWasserTeil) && kinder > wasser) return { text: sp.saison.text, label: "Saison des Wasserbereichs" };
  return sp.typ === "wasser" ? { text: sp.saison.text, label: "Saison" } : null;
}

/** „ca. 1.200 m² laut Stadt“ */
export function groesseText(sp: SpielplatzDaten): string | null {
  if (!sp.groesse_m2) return null;
  const gerundet = sp.groesse_m2 >= 1000 ? Math.round(sp.groesse_m2 / 100) * 100 : Math.round(sp.groesse_m2 / 10) * 10;
  return `ca. ${gerundet.toLocaleString("de-DE")} m² laut Stadt`;
}
