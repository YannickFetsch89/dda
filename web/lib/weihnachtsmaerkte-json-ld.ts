// Strukturierte Daten des Weihnachtsmarkt-Guides (Plan 5.2/5.3): Event nur während der Saison, sonst Place.
// Kein aggregateRating, keine Google-Werte.
import { brotkrumenJsonLd } from "./kneipen-json-ld";
import { ortBildUrl } from "./orte";
import { ohneFett } from "./beschreibung";
import type { DddOrt } from "./typen";
import { WM_BASIS, aktuelleSaison, istIndexierbar, wm, wmPfad } from "./weihnachtsmaerkte";

function ort(o: DddOrt): Record<string, unknown> {
  const plz = (o.adresse ?? "").match(/\b(\d{5})\b/)?.[1];
  const stadt = o.stadtteil === "Neuss" || o.stadtteil === "Ratingen" ? o.stadtteil : "Düsseldorf";
  return {
    "@type": "Place",
    name: o.name,
    ...(o.latitude != null && o.longitude != null ? { geo: { "@type": "GeoCoordinates", latitude: o.latitude, longitude: o.longitude } } : {}),
    address: {
      "@type": "PostalAddress",
      ...(o.adresse ? { streetAddress: o.adresse.split(", ")[0] } : {}),
      ...(plz ? { postalCode: plz } : {}),
      addressLocality: stadt,
      addressCountry: "DE",
    },
  };
}

/** Absolute Bildadresse: eigenes Foto bzw. Google-Foto über /ort-foto, sonst das Guide-Bild (SEO-Prüfung 19.11.2026). */
function bild(o: DddOrt, siteUrl: string): string {
  return `${siteUrl}${ortBildUrl(o) ?? "/guides/weihnachtsmaerkte.webp"}`;
}

/** Detail: Event, solange heute ≤ bis der aktuellen Saison; danach nur Place. */
export function weihnachtsmarktJsonLd(o: DddOrt, siteUrl: string, heute: string): Record<string, unknown> {
  const d = wm(o);
  const s = aktuelleSaison(d.saisons);
  const url = `${siteUrl}${wmPfad(o)}`;
  if (!s || heute > s.bis) {
    return { "@context": "https://schema.org", ...ort(o), url, image: bild(o, siteUrl), ...(o.beschreibung ? { description: ohneFett(o.beschreibung) } : {}) };
  }
  return {
    "@context": "https://schema.org",
    "@type": "Event",
    name: `${o.name} ${s.jahr}`,
    url,
    ...(o.beschreibung ? { description: ohneFett(o.beschreibung) } : {}),
    startDate: s.von,
    endDate: s.bis,
    eventStatus: "https://schema.org/EventScheduled",
    eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
    location: ort(o),
    image: [bild(o, siteUrl)],
    ...(d.eintritt ? { isAccessibleForFree: d.eintritt.wert === "frei" } : {}),
    // Freier Eintritt als Angebot zu 0 € (von Google für Event-Snippets empfohlen); sonst keine erfundenen Preise
    ...(d.eintritt?.wert === "frei"
      ? { offers: { "@type": "Offer", price: 0, priceCurrency: "EUR", availability: "https://schema.org/InStock", url, validFrom: s.von } }
      : {}),
    ...(d.veranstalter ? { organizer: { "@type": "Organization", name: d.veranstalter } } : {}),
  };
}

export function weihnachtsmaerkteListeJsonLd(orte: DddOrt[], siteUrl: string): Record<string, unknown>[] {
  const liste = orte.filter(istIndexierbar).slice(0, 30);
  return [
    brotkrumenJsonLd(siteUrl, [
      { name: "Start", pfad: "/" },
      { name: "Düsseldorf entdecken", pfad: "/guides" },
      { name: "Weihnachtsmärkte", pfad: WM_BASIS },
    ]),
    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      name: "Weihnachtsmärkte in Düsseldorf",
      numberOfItems: liste.length,
      itemListElement: liste.map((o, i) => ({ "@type": "ListItem", position: i + 1, url: `${siteUrl}${wmPfad(o)}`, name: o.name })),
    },
  ];
}
