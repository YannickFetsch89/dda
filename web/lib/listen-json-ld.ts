// Strukturierte Daten für Event-Listen (SEO-/GEO-Plan Nov. 2026, Maßnahme 7):
// ItemList der SICHTBAREN Einträge (nur Verweise – das Event-Rich-Result gehört auf die Eventseite) plus
// BreadcrumbList; EventSeries für Reihen mit subEvent als Verweis auf die kommenden Termine.
import { brotkrumenJsonLd } from "./kneipen-json-ld";
import { eventPfad } from "./pfade";
import { basisTitel } from "./termine";
import type { DddEvent } from "./typen";

/** Höchstzahl Einträge in einer ItemList (die Liste selbst kann länger sein). */
export const MAX_LISTE = 30;

export interface Krume { name: string; pfad: string }

/** ItemList + BreadcrumbList. Ohne Einträge keine ItemList (ein leeres ItemList wird nicht ausgezeichnet). */
export function eventListeJsonLd(siteUrl: string, name: string, krumen: Krume[], events: DddEvent[]): Record<string, unknown>[] {
  const daten: Record<string, unknown>[] = [brotkrumenJsonLd(siteUrl, krumen)];
  const liste = events.slice(0, MAX_LISTE);
  if (liste.length) {
    daten.push({
      "@context": "https://schema.org",
      "@type": "ItemList",
      name,
      numberOfItems: liste.length,
      itemListElement: liste.map((e, i) => ({
        "@type": "ListItem",
        position: i + 1,
        url: `${siteUrl}${eventPfad(e)}`,
        name: basisTitel(e.titel),
      })),
    });
  }
  return daten;
}

/** EventSeries einer Reihe: Name, URL und die kommenden Termine als Verweise (keine Kopie der Event-Daten). */
export function reiheJsonLd(siteUrl: string, reihe: { slug: string; titel: string; ort: string }, kommende: DddEvent[]): Record<string, unknown> {
  const daten: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "EventSeries",
    name: reihe.titel,
    url: `${siteUrl}/reihe/${encodeURIComponent(reihe.slug)}`,
  };
  const termine = kommende.slice(0, MAX_LISTE);
  if (termine.length) {
    // Nur Verweise per @id (= URL der Eventseite) – Teil-Objekte mit @type Event ohne Ort würde der
    // Rich-Results-Test als unvollständige Events melden
    daten.subEvent = termine.map((e) => ({ "@id": `${siteUrl}${eventPfad(e)}`, url: `${siteUrl}${eventPfad(e)}`, name: basisTitel(e.titel) }));
  }
  return daten;
}
