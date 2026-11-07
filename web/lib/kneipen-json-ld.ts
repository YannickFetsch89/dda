// Strukturierte Daten (schema.org) für den Kneipen-Hub: BarOrPub, BreadcrumbList, ItemList.
// Keine aggregateRating aus Google-Daten (Fremdbewertungen dürfen nicht als eigene ausgezeichnet werden).
import { ortPfad } from "@/components/ort-karten";
import { unterart } from "./kneipen";
import { ortBildUrl, sichereUrl } from "./orte";
import type { DddOrt } from "./typen";

const TAGE = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

interface Punkt { day?: number; hour?: number; minute?: number }
interface Periode { open?: Punkt; close?: Punkt }

const zeit = (p?: Punkt) =>
  p && typeof p.hour === "number" ? `${String(p.hour).padStart(2, "0")}:${String(p.minute ?? 0).padStart(2, "0")}` : null;

/** Google-Öffnungsperioden (regularOpeningHours.periods) → schema.org OpeningHoursSpecification. */
export function oeffnungszeitenSpec(perioden: unknown): Record<string, unknown>[] {
  if (!Array.isArray(perioden)) return [];
  return (perioden as Periode[]).flatMap((p) => {
    const von = zeit(p.open);
    if (typeof p.open?.day !== "number" || !von) return [];
    // Ohne Schließzeit: rund um die Uhr geöffnet (Google liefert dann nur open 00:00)
    const bis = zeit(p.close) ?? "23:59";
    return [{ "@type": "OpeningHoursSpecification", dayOfWeek: `https://schema.org/${TAGE[p.open.day]}`, opens: von, closes: bis }];
  });
}

function absolut(pfad: string, siteUrl: string): string {
  return /^https?:\/\//.test(pfad) ? pfad : `${siteUrl}${pfad}`;
}

export function barOrPubJsonLd(o: DddOrt, siteUrl: string): Record<string, unknown> {
  const url = `${siteUrl}${ortPfad(o)}`;
  const bild = ortBildUrl(o);
  const [strasse, ...rest] = (o.adresse ?? "").split(", ");
  const plzOrt = rest.join(", ").match(/(\d{5})\s+(.+)/);
  const daten: Record<string, unknown> = {
    "@context": "https://schema.org",
    // Brauhäuser als schema.org/Brewery, sonst BarOrPub
    "@type": unterart(o) === "brauhaus" ? "Brewery" : "BarOrPub",
    name: o.name,
    url,
    address: {
      "@type": "PostalAddress",
      ...(strasse ? { streetAddress: strasse } : {}),
      ...(plzOrt ? { postalCode: plzOrt[1], addressLocality: plzOrt[2] } : { addressLocality: o.stadtteil === "Neuss" || o.stadtteil === "Ratingen" ? o.stadtteil : "Düsseldorf" }),
      addressCountry: "DE",
    },
  };
  if (o.beschreibung) daten.description = o.beschreibung;
  if (bild) daten.image = [absolut(bild, siteUrl)];
  if (o.latitude != null && o.longitude != null) daten.geo = { "@type": "GeoCoordinates", latitude: o.latitude, longitude: o.longitude };
  if (o.telefon) daten.telephone = o.telefon;
  const web = sichereUrl(o.webseite);
  if (web) daten.sameAs = [web];
  if (o.preis_niveau) daten.priceRange = o.preis_niveau;
  const oz = oeffnungszeitenSpec(o.extras.oeffnungszeiten_perioden);
  if (oz.length) daten.openingHoursSpecification = oz;
  return daten;
}

export function brotkrumenJsonLd(siteUrl: string, teile: { name: string; pfad: string }[]): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: teile.map((t, i) => ({ "@type": "ListItem", position: i + 1, name: t.name, item: `${siteUrl}${t.pfad}` })),
  };
}

export function kneipenListeJsonLd(orte: DddOrt[], siteUrl: string, basis: string): Record<string, unknown>[] {
  return [
    brotkrumenJsonLd(siteUrl, [
      { name: "Start", pfad: "/" },
      { name: "Düsseldorf entdecken", pfad: "/guides" },
      { name: "Kneipen & Bars", pfad: basis },
    ]),
    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      name: "Kneipen & Bars in Düsseldorf",
      itemListElement: orte.map((o, i) => ({ "@type": "ListItem", position: i + 1, url: `${siteUrl}${ortPfad(o)}`, name: o.name })),
    },
  ];
}
