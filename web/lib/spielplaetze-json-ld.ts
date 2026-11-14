// Strukturierte Daten für den Spielplatz-Guide (Plan 5.2/5.3): Playground ohne Bewertung, ItemList nur indexierbarer Plätze.
import { brotkrumenJsonLd } from "./kneipen-json-ld";
import { ortIndexierbar, spielplatz, type SpielplatzDaten } from "./spielplaetze";
import type { DddOrt } from "./typen";

export const SPIELPLATZ_BASIS = "/guides/spielplaetze";

export const spielplatzPfad = (o: DddOrt) => `${SPIELPLATZ_BASIS}/${encodeURIComponent(o.slug)}`;

/**
 * isAccessibleForFree (5.3): städtisch nur bei eintritt=ja falsch, sonst wahr (fehlendes OSM-fee lässt den Platz frei).
 * Abenteuer aus dem Pflichtfeld: ja → falsch, nein → wahr, ohne gültigen Wert keine Angabe.
 */
export function kostenlos(sp: SpielplatzDaten): boolean | undefined {
  if (sp.quelle === "abenteuer") return sp.eintritt === "ja" ? false : sp.eintritt === "nein" ? true : undefined;
  return sp.eintritt !== "ja";
}

export function spielplatzJsonLd(o: DddOrt, siteUrl: string): Record<string, unknown> {
  const sp = spielplatz(o);
  const frei = kostenlos(sp);
  const [strasse, ...rest] = (o.adresse ?? "").split(", ");
  const plz = rest.join(" ").match(/\b(\d{5})\b/)?.[1];
  return {
    "@context": "https://schema.org",
    "@type": "Playground",
    name: o.name,
    url: `${siteUrl}${spielplatzPfad(o)}`,
    ...(sp.beschreibung ? { description: sp.beschreibung } : {}),
    ...(o.latitude != null && o.longitude != null ? { geo: { "@type": "GeoCoordinates", latitude: o.latitude, longitude: o.longitude } } : {}),
    ...(o.adresse
      ? {
          address: {
            "@type": "PostalAddress",
            streetAddress: strasse,
            ...(plz ? { postalCode: plz } : {}),
            addressLocality: "Düsseldorf",
            addressCountry: "DE",
          },
        }
      : {}),
    ...(o.stadtteil ? { containedInPlace: { "@type": "Place", name: `Düsseldorf-${o.stadtteil}` } } : {}),
    ...(frei !== undefined ? { isAccessibleForFree: frei } : {}),
  };
}

/** Hub: Brotkrumen + ItemList der indexierbaren Plätze (max. 30) in der übergebenen Reihenfolge. */
export function spielplaetzeListeJsonLd(orte: DddOrt[], siteUrl: string): Record<string, unknown>[] {
  const liste = orte.filter(ortIndexierbar).slice(0, 30);
  return [
    brotkrumenJsonLd(siteUrl, [
      { name: "Start", pfad: "/" },
      { name: "Düsseldorf entdecken", pfad: "/guides" },
      { name: "Spielplätze", pfad: SPIELPLATZ_BASIS },
    ]),
    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      name: "Spielplätze in Düsseldorf",
      numberOfItems: liste.length,
      itemListElement: liste.map((o, i) => ({ "@type": "ListItem", position: i + 1, url: `${siteUrl}${spielplatzPfad(o)}`, name: o.name })),
    },
  ];
}
