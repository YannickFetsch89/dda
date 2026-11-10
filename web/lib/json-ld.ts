// Strukturierte Daten (schema.org/Event) für Eventseiten. Gibt immer die echten Daten aus –
// auch bei abgelaufenen Events wird kein Datum angepasst.
import { istKostenlos, istOnline } from "./ableitungen";
import { eventBildUrl } from "./bilder";
import { symbolbild } from "./symbolbild";
import { basisTitel } from "./termine";
import type { DddEvent } from "./typen";
import { kurzBeschreibung } from "./beschreibung";

/** Versatz von Europe/Berlin zu einem UTC-Zeitpunkt in Minuten (60 = Winter, 120 = Sommer). */
function versatzMinuten(zeitpunkt: Date): number {
  const teil = new Intl.DateTimeFormat("en-US", { timeZone: "Europe/Berlin", timeZoneName: "longOffset" })
    .formatToParts(zeitpunkt)
    .find((t) => t.type === "timeZoneName")?.value;
  const m = teil?.match(/GMT([+-])(\d{2}):?(\d{2})?/);
  return m ? (m[1] === "-" ? -1 : 1) * (Number(m[2]) * 60 + Number(m[3] ?? 0)) : 60;
}

/**
 * UTC-Versatz der Berliner ORTSZEIT datum+uhrzeit, z.B. "+01:00" (Winter) oder "+02:00" (Sommer).
 * Zweistufig, damit auch die Umstellungssonntage stimmen: erst die Ortszeit grob als UTC deuten,
 * den dort gültigen Versatz abziehen und am so ermittelten echten Zeitpunkt erneut nachsehen.
 * Doppelte Stunde im Herbst (02:00–02:59) → Winterzeit.
 */
export function berlinVersatz(datum: string, uhrzeit = "12:00"): string {
  const alsUtc = new Date(`${datum}T${uhrzeit}:00Z`).getTime();
  const erster = versatzMinuten(new Date(alsUtc));
  const minuten = versatzMinuten(new Date(alsUtc - erster * 60_000));
  const v = Math.abs(minuten);
  return `${minuten < 0 ? "-" : "+"}${String(Math.floor(v / 60)).padStart(2, "0")}:${String(v % 60).padStart(2, "0")}`;
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
  if (e.reihe) {
    daten.superEvent = { "@type": "EventSeries", name: e.reihe.titel, url: `${siteUrl}/reihe/${encodeURIComponent(e.reihe.slug)}` };
  }
  if (e.beschreibung) daten.description = kurzBeschreibung(e.beschreibung, 500) ?? e.beschreibung;
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
export function jsonLdText(daten: unknown): string {
  return JSON.stringify(daten).replace(/</g, "\\u003c");
}
