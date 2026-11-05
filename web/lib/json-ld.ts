// Strukturierte Daten (schema.org/Event) für Eventseiten. Gibt immer die echten Daten aus –
// auch bei abgelaufenen Events wird kein Datum angepasst.
import { istKostenlos, istOnline } from "./ableitungen";
import { eventBildUrl } from "./bilder";
import { symbolbild } from "./symbolbild";
import { basisTitel } from "./termine";
import type { DddEvent } from "./typen";

/** UTC-Versatz von Europe/Berlin an einem Tag/Uhrzeit, z.B. "+01:00" (Winter) oder "+02:00" (Sommer). */
export function berlinVersatz(datum: string, uhrzeit = "12:00"): string {
  // Erst grob als UTC annehmen, dann den in Berlin gültigen Versatz ablesen
  const probe = new Date(`${datum}T${uhrzeit}:00Z`);
  const teil = new Intl.DateTimeFormat("en-US", { timeZone: "Europe/Berlin", timeZoneName: "longOffset" })
    .formatToParts(probe)
    .find((t) => t.type === "timeZoneName")?.value;
  const m = teil?.match(/GMT([+-]\d{2}):?(\d{2})?/);
  return m ? `${m[1]}:${m[2] ?? "00"}` : "+01:00";
}

/** Startzeitpunkt im ISO-Format: mit Uhrzeit und Zeitzone, sonst nur das Datum. */
export function startDatum(e: Pick<DddEvent, "datum" | "uhrzeit">): string {
  return e.uhrzeit ? `${e.datum}T${e.uhrzeit}:00${berlinVersatz(e.datum, e.uhrzeit)}` : e.datum;
}

/** Eindeutiger Betrag aus dem Preistext ("ab 12 €", "15,50 EUR") – bei mehreren Beträgen null. */
export function preisBetrag(preis: string | null): number | null {
  if (!preis) return null;
  const betraege = [...preis.matchAll(/(\d{1,4}(?:[.,]\d{1,2})?)\s*(?:€|eur\b|euro\b)|(?:€|eur\b)\s*(\d{1,4}(?:[.,]\d{1,2})?)/gi)]
    .map((m) => Number((m[1] ?? m[2]).replace(",", ".")));
  return betraege.length === 1 && Number.isFinite(betraege[0]) ? betraege[0] : null;
}

function absolut(pfad: string, siteUrl: string): string {
  return /^https?:\/\//i.test(pfad) ? pfad : `${siteUrl}${pfad.startsWith("/") ? "" : "/"}${pfad}`;
}

export function eventJsonLd(e: DddEvent, seitenUrl: string, siteUrl: string): Record<string, unknown> {
  const online = istOnline(e);
  const bild = eventBildUrl(e) ?? symbolbild(e);
  const daten: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Event",
    name: basisTitel(e.titel),
    url: seitenUrl,
    startDate: startDatum(e),
    eventStatus: e.abgesagt ? "https://schema.org/EventCancelled" : "https://schema.org/EventScheduled",
    eventAttendanceMode: online
      ? "https://schema.org/OnlineEventAttendanceMode"
      : "https://schema.org/OfflineEventAttendanceMode",
    location: online
      ? { "@type": "VirtualLocation", ...(e.quelle_url ? { url: e.quelle_url } : {}) }
      : {
          "@type": "Place",
          name: e.ort,
          address: {
            "@type": "PostalAddress",
            ...(e.adresse ? { streetAddress: e.adresse } : {}),
            addressLocality: "Düsseldorf",
            addressCountry: "DE",
          },
        },
  };
  if (e.datum_bis && e.datum_bis !== e.datum) daten.endDate = e.datum_bis;
  if (e.beschreibung) daten.description = e.beschreibung;
  if (bild) daten.image = [absolut(bild, siteUrl)];
  if (e.quelle_url) {
    const betrag = istKostenlos(e) ? 0 : preisBetrag(e.preis);
    daten.offers = {
      "@type": "Offer",
      url: e.quelle_url,
      ...(betrag !== null ? { price: betrag, priceCurrency: "EUR" } : {}),
    };
  }
  return daten;
}

/** JSON für ein <script type="application/ld+json"> – „<“ maskiert, damit kein </script> ausbricht. */
export function jsonLdText(daten: Record<string, unknown>): string {
  return JSON.stringify(daten).replace(/</g, "\\u003c");
}
