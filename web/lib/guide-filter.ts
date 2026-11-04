// Filter, Sortierung und Zählwerte für Guide-Übersichten (zuerst Restaurants & Cafés).
// Alle Filter stehen in Query-Parametern, damit Links teilbar sind und ohne JavaScript funktionieren:
//   ?typ=cafe&stadtteil=flingern&kueche=japanisch&preis=1,2&tags=terrasse,brunch&sort=bewertung&anzahl=36
import { kuecheVonTyp, slugify } from "./kueche";
import type { DddOrt, PreisNiveau } from "./typen";

export const SEITE = 9; // Karten pro "Seite" (Design: 9 pro Seite, dann "Weitere … laden")

export type SortWert = "empfohlen" | "bewertung" | "neu";
export const SORTIERUNGEN: { wert: SortWert; label: string }[] = [
  { wert: "empfohlen", label: "Empfohlen" },
  { wert: "bewertung", label: "Bewertung" },
  { wert: "neu", label: "Neu" },
];

const PREISE: PreisNiveau[] = ["€", "€€", "€€€"];

/** Tag-Filter in fester Reihenfolge (nur Tags, die die Daten tatsächlich liefern). */
export const FILTER_TAGS = [
  "Terrasse", "Brunch", "Frühstück", "Vegetarisch", "Hunde willkommen", "Kinderfreundlich", "Cocktails", "Reservierbar",
];

export interface GuideFilter {
  typ: "restaurant" | "cafe" | null;
  stadtteil: string | null; // Slug
  kueche: string | null; // Slug
  preise: number[]; // 1–3
  tags: string[]; // Slugs
  sort: SortWert;
  anzahl: number;
  ansicht: "grid" | "karte";
}

type SP = Record<string, string | string[] | undefined>;

function eins(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

function liste(v: string | string[] | undefined): string[] {
  return (eins(v) ?? "").split(",").map((s) => s.trim()).filter(Boolean);
}

export function filterLesen(sp: SP): GuideFilter {
  const typ = eins(sp.typ);
  const sort = eins(sp.sort);
  const anzahl = Number.parseInt(eins(sp.anzahl) ?? "", 10);
  return {
    typ: typ === "restaurant" || typ === "cafe" ? typ : null,
    stadtteil: eins(sp.stadtteil) || null,
    kueche: eins(sp.kueche) || null,
    preise: [...new Set(liste(sp.preis).map(Number).filter((n) => Number.isInteger(n) && n >= 1 && n <= 3))],
    tags: liste(sp.tags),
    sort: SORTIERUNGEN.some((s) => s.wert === sort) ? (sort as SortWert) : "empfohlen",
    anzahl: Number.isFinite(anzahl) && anzahl >= SEITE ? Math.min(anzahl, 2000) : SEITE,
    ansicht: eins(sp.ansicht) === "karte" ? "karte" : "grid",
  };
}

/** Link mit geändertem Filter (null/leer entfernt den Parameter). Seitenzahl wird zurückgesetzt. */
export function filterHref(basis: string, f: GuideFilter, aenderung: Partial<GuideFilter>): string {
  const n = { ...f, anzahl: SEITE, ...aenderung };
  const p = new URLSearchParams();
  if (n.typ) p.set("typ", n.typ);
  if (n.stadtteil) p.set("stadtteil", n.stadtteil);
  if (n.kueche) p.set("kueche", n.kueche);
  if (n.preise.length) p.set("preis", [...n.preise].sort().join(","));
  if (n.tags.length) p.set("tags", n.tags.join(","));
  if (n.sort !== "empfohlen") p.set("sort", n.sort);
  if (n.anzahl > SEITE) p.set("anzahl", String(n.anzahl));
  if (n.ansicht === "karte") p.set("ansicht", "karte");
  const qs = p.toString().replace(/%2C/g, ",");
  return qs ? `${basis}?${qs}` : basis;
}

export function umschalten<T>(liste: T[], wert: T): T[] {
  return liste.includes(wert) ? liste.filter((x) => x !== wert) : [...liste, wert];
}

export const preisStufe = (p: PreisNiveau | null) => (p ? PREISE.indexOf(p) + 1 : 0);
export const preisZeichen = (n: number) => PREISE[n - 1] ?? "";

export function kueche(o: DddOrt) {
  return kuecheVonTyp(o.extras?.google_primaertyp);
}

function vorabScore(o: DddOrt): number {
  const v = o.extras?.vorab_score;
  return typeof v === "number" ? v : 0;
}

/** Wendet die Filter an. `ohne` lässt einzelne Filter weg (für die Zählwerte an den Chips). */
export function filtern(orte: DddOrt[], f: GuideFilter, ohne: (keyof GuideFilter)[] = []): DddOrt[] {
  const tagNamen = new Map(FILTER_TAGS.map((t) => [slugify(t), t]));
  return orte.filter((o) => {
    if (!ohne.includes("typ") && f.typ && o.typ !== f.typ) return false;
    if (!ohne.includes("stadtteil") && f.stadtteil && slugify(o.stadtteil ?? "") !== f.stadtteil) return false;
    if (!ohne.includes("kueche") && f.kueche && kueche(o)?.slug !== f.kueche) return false;
    if (!ohne.includes("preise") && f.preise.length && !f.preise.includes(preisStufe(o.preis_niveau))) return false;
    if (!ohne.includes("tags") && f.tags.length) {
      for (const t of f.tags) if (!o.tags.includes(tagNamen.get(t) ?? "")) return false;
    }
    return true;
  });
}

export function sortieren(orte: DddOrt[], sort: SortWert): DddOrt[] {
  const kopie = [...orte];
  if (sort === "bewertung") {
    kopie.sort((a, b) => (b.google_rating ?? 0) - (a.google_rating ?? 0) || (b.google_bewertungen_anzahl ?? 0) - (a.google_bewertungen_anzahl ?? 0));
  } else if (sort === "neu") {
    kopie.sort((a, b) => (b.erstellt_am ?? "").localeCompare(a.erstellt_am ?? ""));
  } else {
    kopie.sort((a, b) => b.sortierung - a.sortierung || (b.qualitaets_score ?? 0) - (a.qualitaets_score ?? 0) || vorabScore(b) - vorabScore(a));
  }
  return kopie;
}

/** Zählt Werte (Stadtteile, Küchen) und sortiert absteigend. */
export function zaehlen(orte: DddOrt[], wert: (o: DddOrt) => string | null | undefined): { name: string; slug: string; anzahl: number }[] {
  const z = new Map<string, number>();
  for (const o of orte) {
    const w = wert(o);
    if (w) z.set(w, (z.get(w) ?? 0) + 1);
  }
  return [...z.entries()]
    .map(([name, anzahl]) => ({ name, slug: slugify(name), anzahl }))
    .sort((a, b) => b.anzahl - a.anzahl || a.name.localeCompare(b.name, "de"));
}

export const zahl = (n: number) => n.toLocaleString("de-DE");
export const sterne = (r: number) => r.toFixed(1).replace(".", ",");
