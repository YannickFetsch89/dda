import { describe, expect, it } from "vitest";
import { berlinVersatz, eventJsonLd, jsonLdText, preisBetrag, startDatum } from "@/lib/json-ld";
import { ev } from "./hilfen";

const SITE = "https://diesdas.events";

describe("Zeitzone und Startdatum", () => {
  it("Winter- und Sommerzeit in Berlin", () => {
    expect(berlinVersatz("2026-01-15")).toBe("+01:00");
    expect(berlinVersatz("2026-07-15")).toBe("+02:00");
  });
  it("Startdatum mit Uhrzeit trägt den Versatz, ohne Uhrzeit nur das Datum", () => {
    expect(startDatum({ datum: "2026-11-10", uhrzeit: "20:00" })).toBe("2026-11-10T20:00:00+01:00");
    expect(startDatum({ datum: "2026-06-10", uhrzeit: "19:30" })).toBe("2026-06-10T19:30:00+02:00");
    expect(startDatum({ datum: "2026-11-10", uhrzeit: null })).toBe("2026-11-10");
  });
});

describe("preisBetrag", () => {
  it("liest eindeutige Beträge", () => {
    expect(preisBetrag("ab 12 €")).toBe(12);
    expect(preisBetrag("15,50 EUR")).toBe(15.5);
    expect(preisBetrag("€ 8")).toBe(8);
  });
  it("gibt bei mehreren oder keinen Beträgen null zurück", () => {
    expect(preisBetrag("12 € / ermäßigt 8 €")).toBeNull();
    expect(preisBetrag("siehe Veranstalter")).toBeNull();
    expect(preisBetrag(null)).toBeNull();
  });
});

describe("eventJsonLd", () => {
  const basis = ev({
    id: "11111111-1111-1111-1111-111111111111",
    titel: "Jazz am Abend",
    datum: "2026-11-01",
    uhrzeit: "20:00",
    ort: "Jazz-Schmiede",
    adresse: "Himmelgeister Str. 107g",
    preis: "ab 12 €",
    quelle_url: "https://example.org/tickets",
    beschreibung: "Ein Abend mit Jazz.",
  });

  it("gibt die echten Daten aus – auch für ein abgelaufenes Event", () => {
    const d = eventJsonLd(basis, `${SITE}/event/musik/jazz`, SITE);
    expect(d["@type"]).toBe("Event");
    expect(d.startDate).toBe("2026-11-01T20:00:00+01:00");
    expect(d.eventStatus).toBe("https://schema.org/EventScheduled");
    expect(d.location).toMatchObject({ "@type": "Place", name: "Jazz-Schmiede", address: { streetAddress: "Himmelgeister Str. 107g", addressLocality: "Düsseldorf" } });
    expect(d.offers).toEqual({ "@type": "Offer", url: "https://example.org/tickets", price: 12, priceCurrency: "EUR" });
    expect(d.endDate).toBeUndefined();
  });

  it("abgesagt → EventCancelled", () => {
    expect(eventJsonLd({ ...basis, abgesagt: true }, SITE, SITE).eventStatus).toBe("https://schema.org/EventCancelled");
  });

  it("mehrtägig → endDate, kostenlos → Preis 0", () => {
    const d = eventJsonLd({ ...basis, datum_bis: "2026-11-30", preis: "kostenlos" }, SITE, SITE);
    expect(d.endDate).toBe("2026-11-30");
    expect(d.offers).toMatchObject({ price: 0, priceCurrency: "EUR" });
  });

  it("online → VirtualLocation", () => {
    const d = eventJsonLd({ ...basis, ort: "Online", titel: "Webinar" }, SITE, SITE);
    expect(d.eventAttendanceMode).toBe("https://schema.org/OnlineEventAttendanceMode");
    expect(d.location).toMatchObject({ "@type": "VirtualLocation" });
  });

  it("Bild als absolute URL", () => {
    const d = eventJsonLd({ ...basis, bild_url: "https://example.org/b.jpg" }, SITE, SITE);
    expect(d.image).toEqual([`${SITE}/bild/event/${basis.id}`]);
  });

  it("Einzeltermin einer Reihe verweist per superEvent auf die Reihenseite", () => {
    const d = eventJsonLd({ ...basis, reihe: { slug: "jazz-am-abend-jazz-schmiede", titel: "Jazz am Abend" } }, SITE, SITE);
    expect(d.superEvent).toEqual({ "@type": "EventSeries", name: "Jazz am Abend", url: `${SITE}/reihe/jazz-am-abend-jazz-schmiede` });
    expect(eventJsonLd(basis, SITE, SITE).superEvent).toBeUndefined();
  });

  it("jsonLdText maskiert </script>", () => {
    const text = jsonLdText({ name: "</script><script>alert(1)</script>" });
    expect(text).not.toContain("</script>");
    expect(JSON.parse(text).name).toBe("</script><script>alert(1)</script>");
  });
});
