// Strukturierte Daten (schema.org/Event) für Eventseiten. Gibt immer die echten Daten aus –
// auch bei abgelaufenen Events wird kein Datum angepasst.
import { istKostenlos, istOnline } from "./ableitungen";
import { eventBildUrl } from "./bilder";
import { symbolbild } from "./symbolbild";
import { anzeigeTitel } from "./termine";
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

const ZAHL = String.raw`\d{1,4}(?:[.,]\d{1,2})?`;
const WAEHRUNG = String.raw`(?:€|eur\b|euro\b)`;
/** Spanne „4,00 bis 7,00 €“, „12–18 €“: beide Grenzen, auch wenn nur die obere ein €-Zeichen hat */
const SPANNE = new RegExp(String.raw`(${ZAHL})\s*${WAEHRUNG}?\s*(?:bis|–|—|-)\s*(${ZAHL})\s*${WAEHRUNG}`, "gi");
const EINZELN = new RegExp(String.raw`(${ZAHL})\s*${WAEHRUNG}|${WAEHRUNG}\s*(${ZAHL})`, "gi");
/** Beträge, die nur für bestimmte Gruppen gelten – zählen nur, wenn es keinen regulären Betrag gibt */
const ERMAESSIGT = /erm(?:ä|ae|a)(?:ß|ss)igt|erm\.|kinder|schüler|student|rentner|senior|mitglied|schwerbehindert/i;

/**
 * Niedrigster Betrag aus dem Preistext für schema.org/Offer.price (Google: „the lowest available price“), z. B.
 * „ab 12 €“ → 12, „4,00 bis 7,00 €“ → 4, „VVK 12,50 € / AK 13,00 €“ → 12,5. Ermäßigte Beträge zählen nur, wenn es
 * keinen anderen gibt („12 € / ermäßigt 8 €“ → 12). Ohne Betrag null. (Search Console 19.11.2026: price fehlte bei 26
 * Events mit mehreren Beträgen; Spannen lieferten bisher die obere Grenze.)
 */
export function preisBetrag(preis: string | null): number | null {
  if (!preis) return null;
  const funde: { wert: number; stelle: number }[] = [];
  const zahl = (t: string) => Number(t.replace(",", "."));
  for (const m of preis.matchAll(SPANNE)) funde.push({ wert: zahl(m[1]), stelle: m.index ?? 0 }, { wert: zahl(m[2]), stelle: m.index ?? 0 });
  for (const m of preis.matchAll(EINZELN)) funde.push({ wert: zahl(m[1] ?? m[2]), stelle: m.index ?? 0 });
  const gueltig = funde.filter((f) => Number.isFinite(f.wert));
  if (!gueltig.length) return null;
  // Gruppenpreis: Hinweis steht im Text vor dem Betrag, seit dem letzten Trenner („/“, „;“, „|“, Zeilenumbruch)
  const istErmaessigt = (f: { stelle: number }) => ERMAESSIGT.test(preis.slice(0, f.stelle).split(/[/;|\n]/).pop() ?? "");
  const regulaer = gueltig.filter((f) => !istErmaessigt(f));
  const werte = (regulaer.length ? regulaer : gueltig).map((f) => f.wert);
  // 0 € neben echten Preisen („0,00 bis 13,32 €“) ist meist eine Freikarten-Stufe (Kinder, Begleitung) – nicht als Preis
  // ausgeben, sonst zeigt Google das Event als kostenlos. Kostenlose Events erkennt istKostenlos.
  const positiv = werte.filter((w) => w > 0);
  return Math.min(...(positiv.length ? positiv : werte));
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
    // @id = URL der Eventseite: Reihen (EventSeries.subEvent) verweisen darauf
    "@id": seitenUrl,
    name: anzeigeTitel(e.titel, e.ort),
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
  // Ende: letzter Tag; bei eintägigen Events der Starttag (Uhrzeit des Endes kennen wir nicht; Search Console 19.11.2026)
  daten.endDate = e.datum_bis && e.datum_bis > e.datum ? e.datum_bis : e.datum;
  if (e.reihe) {
    daten.superEvent = { "@type": "EventSeries", name: e.reihe.titel, url: `${siteUrl}/reihe/${encodeURIComponent(e.reihe.slug)}` };
  }
  if (e.beschreibung) daten.description = kurzBeschreibung(e.beschreibung, 500) ?? e.beschreibung;
  if (bild) daten.image = [absolut(bild, siteUrl)];
  // Angebot: Ticket-Link des Hauses, sonst die Hauptquelle – immer die echte URL, nie ein Partner-Link (Plan 5.5.5)
  const angebotUrl = e.ticket_url || e.quelle_url;
  if (angebotUrl) {
    const betrag = istKostenlos(e) ? 0 : preisBetrag(e.preis);
    daten.offers = {
      "@type": "Offer",
      url: angebotUrl,
      ...(betrag !== null ? { price: betrag, priceCurrency: "EUR" } : {}),
      // Nur, wenn die Quelle es ausdrücklich sagt; sonst keine Angabe (Verfügbarkeit kennen wir nicht)
      ...(/ausverkauft/i.test(e.preis ?? "") ? { availability: "https://schema.org/SoldOut" } : {}),
    };
  }
  return daten;
}

/** JSON für ein <script type="application/ld+json"> – „<“ maskiert, damit kein </script> ausbricht. */
export function jsonLdText(daten: unknown): string {
  return JSON.stringify(daten).replace(/</g, "\\u003c");
}
