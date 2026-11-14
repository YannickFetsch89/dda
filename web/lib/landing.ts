// Landingpages für Kategorie, Stadtteil und Guide-Stadtteil (SEO-/GEO-Plan Nov. 2026, Phase B, Maßnahme 5).
// Reine Hilfen ohne Netz: Pfade, Slugs, die Mindestinhalt-Regel und die Zuordnung Slug → Stadtteil.
import { KATEGORIEN } from "./kategorien";
import { slugify } from "./kueche";
import { BEZIRKE, bezirkVon, stadtteilName } from "./stadtteile";
import type { KategorieSlug } from "./typen";

/** Ab so vielen kommenden Einträgen ist eine Landingpage indexierbar (Arbeitsgrenze, mit der Search Console nachschärfen). */
export const MIN_EINTRAEGE = 5;
/** Zeitraum der Event-Liste auf Kategorie- und Stadtteilseiten */
export const LANDING_TAGE = 30;

/** Guide-Stadtteile dürfen auch die Nachbarstädte der Guides sein (die Orte tragen sie als Stadtteil). */
export const GUIDE_NACHBARSTAEDTE = ["Neuss", "Ratingen"];

const KATALOG = BEZIRKE.flatMap((b) => b.stadtteile);

/** URL-Slug eines Stadtteils (Anzeigename: „Hafen“ → „medienhafen“). */
export function stadtteilSlug(stadtteil: string): string {
  return slugify(stadtteilName(stadtteil));
}

/** Stadtteil (DB-Schreibweise) zu einem Slug; mitNachbarn: auch Neuss und Ratingen (nur Guides). */
export function stadtteilAusSlug(slug: string, mitNachbarn = false): string | null {
  const liste = mitNachbarn ? [...KATALOG, ...GUIDE_NACHBARSTAEDTE] : KATALOG;
  return liste.find((s) => stadtteilSlug(s) === slug.toLowerCase()) ?? null;
}

/**
 * Kanonischer Stadtteil zu einem Rohwert aus der Datenbank („Medienhafen“ → „Hafen“), so wie der Proxy und die
 * Seite ihn auflösen. null = keine Guide-Stadtteilseite (z. B. „Oberkassel-Süd“) – dann auch kein Link, kein Sitemap-Eintrag.
 */
export function kanonischerStadtteil(roh: string | null | undefined): string | null {
  return roh ? stadtteilAusSlug(stadtteilSlug(roh), true) : null;
}

/** Event-Stadtteilseite, nur für Stadtteile im Katalog (sonst kein Link). */
export function stadtteilPfad(stadtteil: string | null | undefined): string | null {
  if (!stadtteil || !bezirkVon(stadtteil)) return null;
  return `/stadtteil/${stadtteilSlug(stadtteil)}`;
}

export function kategorieGueltig(slug: string): slug is KategorieSlug {
  return KATEGORIEN.some((k) => k.slug === slug);
}

/** Kategorieseite (nicht für „sonstiges“ – das ist keine Intention). */
export function kategoriePfad(slug: string): string | null {
  return kategorieGueltig(slug) ? `/kategorie/${slug}` : null;
}

/** Unterkategorie gehört zur Kategorie? „keine“ (geprüft, nichts passt) ist nie eine Unterkategorie. */
export function unterkategorieGueltig(kategorie: string, unter: string): boolean {
  if (!kategorieGueltig(kategorie) || unter === "keine") return false;
  return KATEGORIEN.find((k) => k.slug === kategorie)!.unterkategorien.some((u) => u.slug === unter);
}

export function unterkategoriePfad(kategorie: string, unter: string): string {
  return `/kategorie/${kategorie}/${unter}`;
}

export type GuideHub = "restaurants-cafes" | "kneipen-bars" | "clubs" | "spielplaetze";
export const GUIDE_HUBS: Record<GuideHub, { name: string; mehrzahl: string; icon: string }> = {
  "restaurants-cafes": { name: "Restaurants & Cafés", mehrzahl: "Restaurants und Cafés", icon: "restaurant" },
  "kneipen-bars": { name: "Kneipen & Bars", mehrzahl: "Kneipen und Bars", icon: "sports_bar" },
  clubs: { name: "Clubs", mehrzahl: "Clubs", icon: "nightlife" },
  spielplaetze: { name: "Spielplätze", mehrzahl: "Spielplätze", icon: "sp:spielplatz" },
};

/**
 * Spielplatz-Guide verlinkt? Seit 14.11.2026 vorübergehend aus: Die Seiten bleiben live (Sitemap, direkte URLs),
 * aber Menü, Footer, /guides-Kachel, Übersichtstext, Familien-Kategorie, Event- und Stadtteilseiten verlinken sie
 * nicht, bis Bilder und Vorschaubilder fertig sind. Wieder einschalten: true setzen (+ client.tsx, rahmen.tsx, llms.txt).
 */
export const SPIELPLAETZE_VERLINKT = false;

/** Darf ein Hub von außen (Event-, Stadtteilseiten) verlinkt werden? */
export const hubVerlinkt = (hub: GuideHub) => hub !== "spielplaetze" || SPIELPLAETZE_VERLINKT;

/** Guide-Stadtteil-Links auf Event-Seiten: Spielplätze nur bei Kategorie Familie (E16 im Spielplatz-Plan). */
export function hubPasstZuEvent(hub: GuideHub, kategorie: string): boolean {
  if (!hubVerlinkt(hub)) return false;
  return hub !== "spielplaetze" || kategorie === "familie";
}

export function istGuideHub(hub: string): hub is GuideHub {
  return hub in GUIDE_HUBS;
}

export function guideStadtteilPfad(hub: GuideHub, stadtteil: string): string {
  return `/guides/${hub}/stadtteil/${stadtteilSlug(stadtteil)}`;
}

// Stadtteile mit Artikel („in der Altstadt“, „im Medienhafen“) – sonst „in Flingern“
const MIT_ARTIKEL: Record<string, string> = {
  Altstadt: "in der Altstadt",
  Carlstadt: "in der Carlstadt",
  Friedrichstadt: "in der Friedrichstadt",
  Stadtmitte: "in der Stadtmitte",
  Hafen: "im Medienhafen",
};

/** „in der Altstadt“, „im Medienhafen“, „in Flingern“ */
export function inStadtteil(stadtteil: string): string {
  return MIT_ARTIKEL[stadtteil] ?? `in ${stadtteilName(stadtteil)}`;
}

/** Erster Satz einer Stadtteilseite, falls kein eigener Text gepflegt ist: Bezirk bzw. Nachbarstadt. */
export function bezirkSatz(stadtteil: string): string {
  const b = bezirkVon(stadtteil);
  // „in der Altstadt“ → „Die Altstadt“, „im Medienhafen“ → „Der Medienhafen“
  const art = MIT_ARTIKEL[stadtteil];
  const subjekt = art ? art.replace(/^in der /, "Die ").replace(/^im /, "Der ") : stadtteilName(stadtteil);
  if (b) return `${subjekt} gehört zum Düsseldorfer Stadtbezirk ${b.nr} (${b.name}).`;
  return `${stadtteilName(stadtteil)} liegt in der Nachbarschaft von Düsseldorf.`;
}

/** Die übrigen Stadtteile desselben Bezirks (für Querverweise). */
export function nachbarStadtteile(stadtteil: string): string[] {
  const b = bezirkVon(stadtteil);
  return b ? b.stadtteile.filter((s) => s !== stadtteil) : [];
}
