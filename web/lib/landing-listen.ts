// Event-Listen und Indexierungsregeln der Landingpages – eine Quelle für Seiten, Sitemap und Eventseite
// (Feinschliff-Roadmap Nov. 2026). Gleiches Fenster überall: die nächsten LANDING_TAGE Tage, gebündelt, ohne Langläufer.
import { filtern, nachZeit } from "./ableitungen";
import { plusTage } from "./datum";
import { KOSTENLOS_TEXTE, UNTERKATEGORIE_TEXTE } from "./landing-texte";
import { LANDING_TAGE, MIN_EINTRAEGE, unterkategorieGueltig } from "./landing";
import type { DddEvent, EventPool, KategorieSlug } from "./typen";

function fenster(pool: EventPool) {
  return { von: pool.heute, bis: plusTage(pool.heute, LANDING_TAGE - 1) };
}

export function kategorieEvents(pool: EventPool, kategorie: KategorieSlug): DddEvent[] {
  return filtern(pool.events, { ...fenster(pool), kategorie }).sort(nachZeit);
}

export function unterkategorieEvents(pool: EventPool, kategorie: KategorieSlug, unter: string): DddEvent[] {
  return kategorieEvents(pool, kategorie).filter((e) => e.unterkategorie === unter);
}

export function kostenlosEvents(pool: EventPool): DddEvent[] {
  return filtern(pool.events, { ...fenster(pool), preis: "kostenlos" }).sort(nachZeit);
}

/** Text für eine Unterkategorie-Seite, nur wenn freigegeben. */
export function unterkategorieText(kategorie: string, unter: string): string[] | null {
  return UNTERKATEGORIE_TEXTE[`${kategorie}/${unter}`] ?? null;
}

/** Indexierbar nur mit freigegebenem Text UND mindestens MIN_EINTRAEGE Events (Feinschliff-Roadmap, Paket 4). */
export function unterkategorieIndexierbar(pool: EventPool, kategorie: KategorieSlug, unter: string): boolean {
  if (!unterkategorieGueltig(kategorie, unter) || !unterkategorieText(kategorie, unter)) return false;
  return pool.quelle === "supabase" && unterkategorieEvents(pool, kategorie, unter).length >= MIN_EINTRAEGE;
}

export function kostenlosIndexierbar(pool: EventPool): boolean {
  return KOSTENLOS_TEXTE.length > 0 && pool.quelle === "supabase" && kostenlosEvents(pool).length >= MIN_EINTRAEGE;
}
