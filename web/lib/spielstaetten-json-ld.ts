// JSON-LD der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.11): nur mit bestätigter Adresse; Typ je Art,
// kein LocalBusiness; ItemList nur mit echten kommenden Events; Säle mit containedInPlace (kanonische Haus-URL);
// addressLocality ist die Stadt aus der PLZ, nie der Stadtteil.
import { eventPfad } from "./pfade";
import { artInfo, stadtVon } from "./spielstaetten";
import type { DddEvent, DddOrt } from "./typen";

export function spielstaetteJsonLd(
  o: DddOrt, art: string | null, siteUrl: string, pfad: string, haus: { name: string; pfad: string } | null,
  events: DddEvent[], adresseBestaetigt: boolean,
): Record<string, unknown> | null {
  if (!adresseBestaetigt || !o.adresse) return null;
  const [strasse] = o.adresse.split(", ");
  const plz = /\b(4\d{4})\b/.exec(o.adresse)?.[1];
  const daten: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": artInfo(art).schemaTyp,
    name: o.name,
    url: `${siteUrl}${pfad}`,
    address: {
      "@type": "PostalAddress",
      streetAddress: strasse,
      ...(plz ? { postalCode: plz } : {}),
      addressLocality: stadtVon(o) ?? "Düsseldorf",
      addressCountry: "DE",
    },
  };
  if (o.latitude != null && o.longitude != null) {
    daten.geo = { "@type": "GeoCoordinates", latitude: o.latitude, longitude: o.longitude };
  }
  if (haus) daten.containedInPlace = { "@type": "Place", name: haus.name, url: `${siteUrl}${haus.pfad}` };
  const kommend = events.filter((e) => !e.abgesagt).slice(0, 20);
  if (kommend.length) {
    daten.event = kommend.map((e) => ({
      "@type": "Event",
      name: e.titel,
      startDate: e.datum,
      ...(e.datum_bis ? { endDate: e.datum_bis } : {}),
      url: `${siteUrl}${eventPfad(e)}`,
      location: { "@type": "Place", name: o.name },
    }));
  }
  return daten;
}
