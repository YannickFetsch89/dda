// Strukturierte Daten (schema.org) für den Club-Hub: NightClub bzw. MusicVenue, BreadcrumbList, ItemList.
// Keine aggregateRating aus Google-Daten (Fremdbewertungen dürfen nicht als eigene ausgezeichnet werden).
import { ortPfad } from "@/components/ort-karten";
import { clubArt, clubBeschreibung, clubProfil } from "./clubs";
import { kurzBeschreibung } from "./beschreibung";
import { brotkrumenJsonLd, oeffnungszeitenSpec } from "./kneipen-json-ld";
import { ortBildUrl, sichereUrl } from "./orte";
import type { DddOrt } from "./typen";

const clubUrl = (o: DddOrt, siteUrl: string) => `${siteUrl}/guides/clubs/${encodeURIComponent(o.slug)}`;

export function clubJsonLd(o: DddOrt, siteUrl: string): Record<string, unknown> {
  const bild = ortBildUrl(o);
  const [strasse, ...rest] = (o.adresse ?? "").split(", ");
  const plzOrt = rest.join(", ").match(/(\d{5})\s+(.+)/);
  const profil = clubProfil(o);
  const daten: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": clubArt(o) === "kulturhaus" ? "MusicVenue" : "NightClub",
    name: o.name,
    // Haupt-URL des Ortes (bei auch_club die Seite im anderen Hub)
    url: o.typ === "club" ? clubUrl(o, siteUrl) : `${siteUrl}${ortPfad(o)}`,
    address: {
      "@type": "PostalAddress",
      ...(strasse ? { streetAddress: strasse } : {}),
      ...(plzOrt ? { postalCode: plzOrt[1], addressLocality: plzOrt[2] } : { addressLocality: o.stadtteil === "Neuss" || o.stadtteil === "Ratingen" ? o.stadtteil : "Düsseldorf" }),
      addressCountry: "DE",
    },
  };
  const beschreibung = kurzBeschreibung(clubBeschreibung(o), 500);
  if (beschreibung) daten.description = beschreibung;
  if (bild) daten.image = [/^https?:\/\//.test(bild) ? bild : `${siteUrl}${bild}`];
  if (o.latitude != null && o.longitude != null) daten.geo = { "@type": "GeoCoordinates", latitude: o.latitude, longitude: o.longitude };
  if (o.telefon) daten.telephone = o.telefon;
  const sameAs = [sichereUrl(o.webseite), profil?.instagram, profil?.residentAdvisor].filter(Boolean);
  if (sameAs.length) daten.sameAs = sameAs;
  const oz = oeffnungszeitenSpec(o.extras.oeffnungszeiten_perioden);
  if (oz.length) daten.openingHoursSpecification = oz;
  return daten;
}

export function clubsListeJsonLd(orte: DddOrt[], siteUrl: string, basis: string): Record<string, unknown>[] {
  return [
    brotkrumenJsonLd(siteUrl, [
      { name: "Start", pfad: "/" },
      { name: "Düsseldorf entdecken", pfad: "/guides" },
      { name: "Clubs", pfad: basis },
    ]),
    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      name: "Clubs in Düsseldorf",
      itemListElement: orte.slice(0, 30).map((o, i) => ({ "@type": "ListItem", position: i + 1, url: clubUrl(o, siteUrl), name: o.name })),
    },
  ];
}
