// Filter, Sortierung und Zählwerte für Guide-Übersichten (zuerst Restaurants & Cafés).
// Alle Filter stehen in Query-Parametern, damit Links teilbar sind und ohne JavaScript funktionieren:
//   ?typ=cafe&stadtteil=flingern,bilk&kueche=japanisch&preis=1,2&tags=terrasse,brunch&sort=bewertung&anzahl=36
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

export type OrtTyp = "restaurant" | "imbiss" | "cafe";
export const ALLE_TYPEN: OrtTyp[] = ["restaurant", "cafe", "imbiss"];
/** Standard ohne Parameter: Restaurants und Cafés, Schnellimbisse nur auf Wunsch. */
export const STANDARD_TYPEN: OrtTyp[] = ["restaurant", "cafe"];

export interface GuideFilter {
  typen: OrtTyp[]; // nie leer
  stadtteile: string[]; // Slugs (ODER)
  kuechen: string[]; // Slugs (ODER)
  preise: number[]; // 1–4 (PREIS_STUFEN)
  tags: string[]; // Slugs
  sort: SortWert;
  anzahl: number;
  ansicht: "grid" | "karte"; // Standard: Karte
}

const gleicheMenge = <T,>(a: T[], b: T[]) => a.length === b.length && a.every((x) => b.includes(x));

type SP = Record<string, string | string[] | undefined>;

function eins(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

function liste(v: string | string[] | undefined): string[] {
  return (eins(v) ?? "").split(",").map((s) => s.trim()).filter(Boolean);
}

/** typ-Parameter: fehlt → Standard (Restaurants + Cafés), „alle“ → alle drei, sonst Kommaliste. */
function typenLesen(v: string | string[] | undefined): OrtTyp[] {
  const roh = liste(v);
  if (!roh.length) return [...STANDARD_TYPEN];
  if (roh.includes("alle")) return [...ALLE_TYPEN];
  const typen = ALLE_TYPEN.filter((t) => roh.includes(t));
  return typen.length ? typen : [...STANDARD_TYPEN];
}

export function filterLesen(sp: SP): GuideFilter {
  const sort = eins(sp.sort);
  const anzahl = Number.parseInt(eins(sp.anzahl) ?? "", 10);
  return {
    typen: typenLesen(sp.typ),
    stadtteile: [...new Set(liste(sp.stadtteil))],
    kuechen: [...new Set(liste(sp.kueche))],
    preise: [...new Set(liste(sp.preis).map(Number).filter((n) => Number.isInteger(n) && n >= 1 && n <= 4))],
    tags: liste(sp.tags),
    sort: SORTIERUNGEN.some((s) => s.wert === sort) ? (sort as SortWert) : "empfohlen",
    anzahl: Number.isFinite(anzahl) && anzahl >= SEITE ? Math.min(anzahl, 2000) : SEITE,
    ansicht: eins(sp.ansicht) === "grid" ? "grid" : "karte",
  };
}

/** Steht die Filter-Art auf dem Standard (Restaurants + Cafés)? */
export const typenStandard = (typen: OrtTyp[]) => gleicheMenge(typen, STANDARD_TYPEN);

/** Link mit geändertem Filter (null/leer entfernt den Parameter). Seitenzahl wird zurückgesetzt. */
export function filterHref(basis: string, f: GuideFilter, aenderung: Partial<GuideFilter>): string {
  const n = { ...f, anzahl: SEITE, ...aenderung };
  const p = new URLSearchParams();
  if (!n.typen.length || typenStandard(n.typen)) {
    // Standard: kein Parameter
  } else if (gleicheMenge(n.typen, ALLE_TYPEN)) {
    p.set("typ", "alle");
  } else {
    p.set("typ", ALLE_TYPEN.filter((t) => n.typen.includes(t)).join(","));
  }
  if (n.stadtteile.length) p.set("stadtteil", n.stadtteile.join(","));
  if (n.kuechen.length) p.set("kueche", n.kuechen.join(","));
  if (n.preise.length) p.set("preis", [...n.preise].sort().join(","));
  if (n.tags.length) p.set("tags", n.tags.join(","));
  if (n.sort !== "empfohlen") p.set("sort", n.sort);
  if (n.anzahl > SEITE) p.set("anzahl", String(n.anzahl));
  if (n.ansicht === "grid") p.set("ansicht", "grid");
  const qs = p.toString().replace(/%2C/g, ",");
  return qs ? `${basis}?${qs}` : basis;
}

/** Art umschalten: mindestens eine bleibt gewählt; „Alle“ ist die Auswahl aller drei. */
export function typUmschalten(typen: OrtTyp[], typ: OrtTyp): OrtTyp[] {
  const neu = umschalten(typen, typ);
  return neu.length ? neu : typen;
}

export function umschalten<T>(liste: T[], wert: T): T[] {
  return liste.includes(wert) ? liste.filter((x) => x !== wert) : [...liste, wert];
}

export const preisStufe = (p: PreisNiveau | null) => (p ? PREISE.indexOf(p) + 1 : 0);
export const preisZeichen = (n: number) => PREISE[n - 1] ?? "";

// ── Preis pro Person (extras.preis_pp aus scraper/orte/preisspanne.py) ─────────────────────────
// Stufen für Filter und Fragebogen. Fine Dining = Google „ab 100 € p. P.“ oder Spanne im Schnitt ab 100 €.
export const PREIS_STUFEN = [
  { wert: 1, label: "bis 20 €", name: "Günstig", text: "bis 20 € p. P." },
  { wert: 2, label: "20–40 €", name: "Mittel", text: "20–40 € p. P." },
  { wert: 3, label: "40–100 €", name: "Gehoben", text: "40–100 € p. P." },
  { wert: 4, label: "Fine Dining", name: "Fine Dining", text: "ab 100 € p. P." },
] as const;

interface Spanne { von: number; bis: number | null; quelle?: string }

function spanne(wert: unknown): Spanne | null {
  if (!wert || typeof wert !== "object") return null;
  const s = wert as Record<string, unknown>;
  if (typeof s.von !== "number") return null;
  return { von: s.von, bis: typeof s.bis === "number" ? s.bis : null, quelle: typeof s.quelle === "string" ? s.quelle : undefined };
}

export function preisSpanne(o: DddOrt): Spanne | null {
  return spanne(o.extras?.preis_pp);
}

/** Preisstufe 1–4 eines Ortes (0 = unbekannt). Ohne Spanne zählt die alte €-Stufe (€ → 1, €€ → 2, €€€ → 3). */
export function preisStufeOrt(o: DddOrt): number {
  const pp = preisSpanne(o);
  if (!pp) return preisStufe(o.preis_niveau);
  const google = spanne(o.extras?.google_preisspanne);
  if ((google && google.von >= 100) || pp.von >= 100) return 4;
  const mitte = (pp.von + (pp.bis ?? pp.von * 1.5)) / 2;
  if (mitte >= 100) return 4;
  return mitte < 20 ? 1 : mitte < 40 ? 2 : 3;
}

/** Kurzform für Karten und Popups: „10–20 €“, „ab 100 €“, „Menü 169–199 €“; ohne Spanne die €-Stufe. */
export function preisKurz(o: DddOrt): string | null {
  const pp = preisSpanne(o);
  if (!pp) return o.preis_niveau ?? null;
  const betrag = pp.bis == null ? `ab ${pp.von} €` : pp.von === pp.bis ? `${pp.von} €` : `${pp.von}–${pp.bis} €`;
  return pp.quelle === "website" ? `Menü ${betrag}` : betrag;
}

/** Für die Detailseite: Zeile und Herkunft („ca. 10–20 € pro Person“ · „laut Google und Gästebewertungen“). */
export function preisDetail(o: DddOrt): { zeile: string; herkunft: string } | null {
  const pp = preisSpanne(o);
  if (!pp) {
    const alt: Record<string, string> = { "€": "günstig", "€€": "mittleres Preisniveau", "€€€": "gehoben" };
    return o.preis_niveau ? { zeile: o.preis_niveau, herkunft: alt[o.preis_niveau] ?? "" } : null;
  }
  const betrag = pp.bis == null ? `ab ${pp.von} €` : pp.von === pp.bis ? `${pp.von} €` : `${pp.von}–${pp.bis} €`;
  if (pp.quelle === "website") return { zeile: `Menü ${betrag} pro Person`, herkunft: "laut Website des Restaurants" };
  if (pp.quelle === "manuell") return { zeile: `ca. ${betrag} pro Person`, herkunft: "Einschätzung der Redaktion" };
  const herkunft = pp.quelle === "bewertungen" ? "geschätzt aus Gästebewertungen"
    : pp.quelle === "google+bewertungen" ? "laut Google und Gästebewertungen" : "laut Google";
  return { zeile: `ca. ${betrag} pro Person`, herkunft };
}

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
    // Brauhäuser aus dem Kneipen-Hub (typ „kneipe“) zählen als Restaurant
    if (!ohne.includes("typen") && !f.typen.includes(o.typ === "kneipe" ? "restaurant" : (o.typ as OrtTyp))) return false;
    if (!ohne.includes("stadtteile") && f.stadtteile.length && !f.stadtteile.includes(slugify(o.stadtteil ?? ""))) return false;
    if (!ohne.includes("kuechen") && f.kuechen.length && !f.kuechen.includes(kueche(o)?.slug ?? "")) return false;
    if (!ohne.includes("preise") && f.preise.length && !f.preise.includes(preisStufeOrt(o))) return false;
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
    // Schnellimbisse (viele Bewertungen, z.B. Dönerläden) stehen bei „Empfohlen“ hinter Restaurants und Cafés;
    // im Tab „Schnellimbiss“ wirkt das nicht, dort haben alle denselben Typ
    const imbiss = (o: DddOrt) => (o.typ === "imbiss" ? 1 : 0);
    kopie.sort((a, b) => b.sortierung - a.sortierung || imbiss(a) - imbiss(b) || (b.qualitaets_score ?? 0) - (a.qualitaets_score ?? 0) || vorabScore(b) - vorabScore(a));
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

/** Statuszeile für gewählte Stadtteile: „in Flingern“, „in Flingern & Bilk“, „in 3 Stadtteilen“. */
export function stadtteileText(slugs: string[], name: (slug: string) => string): string {
  if (!slugs.length) return "";
  if (slugs.length <= 2) return ` in ${slugs.map(name).join(" & ")}`;
  return ` in ${slugs.length} Stadtteilen`;
}
