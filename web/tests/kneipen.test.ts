import { describe, expect, it } from "vitest";
import { filterHref, filterLesen, filtern, happyHour, hatParameter, raucher, spezialitaeten, unterart, vibes } from "@/lib/kneipen";
import { barOrPubJsonLd, oeffnungszeitenSpec } from "@/lib/kneipen-json-ld";
import type { DddOrt } from "@/lib/typen";

function ort(teil: Partial<DddOrt> & { id: string }): DddOrt {
  return {
    name: "Testkneipe", slug: `test-${teil.id}`, typ: "kneipe", untertitel: null, beschreibung: null, highlight: null,
    adresse: "Bolkerstraße 1, 40213 Düsseldorf", stadtteil: "Altstadt", latitude: 51.22, longitude: 6.77,
    bild_url: null, bild_attribution: null, tags: [], preis_niveau: "€€", oeffnungszeiten: null, webseite: null,
    telefon: null, instagram: null, google_place_id: null, google_rating: 4.5, google_bewertungen_anzahl: 300,
    qualitaets_score: 8, extras: {}, sortierung: 0, erstellt_am: null, aktualisiert_am: null,
    ...teil,
  };
}

const UERIGE = ort({ id: "1", name: "Uerige", extras: { unterart: "kneipe", spezialitaeten: ["Altbier", "Unsinn"], vibes: ["Gemütlich", "Draußen sitzen"] } });
const BAR = ort({
  id: "2", name: "Cocktailbar", stadtteil: "Flingern",
  extras: { unterart: "bar", spezialitaeten: ["Cocktails"], vibes: ["Gesellig"],
    happy_hour: { text: "17–19 Uhr", beleg: "Happy Hour von 17 bis 19 Uhr", quelle: "ki" },
    raucher: { wert: "innen", beleg: "Raucherkneipe, hier wird noch gequalmt", quelle: "ki" } },
});
const OHNE_BELEG = ort({ id: "3", extras: { happy_hour: { text: "18–20 Uhr", quelle: "ki" }, raucher: { wert: "aussen" } } });

describe("Merkmale aus extras", () => {
  it("nur feste Werte, Unbekanntes fällt weg", () => {
    expect(spezialitaeten(UERIGE)).toEqual(["Altbier"]);
    expect(vibes(UERIGE)).toEqual(["Gemütlich", "Draußen sitzen"]);
    expect(unterart(BAR)).toBe("bar");
    expect(unterart(ort({ id: "x" }))).toBe("kneipe");
  });
  it("Happy Hour und Raucher nur mit Textbeleg", () => {
    expect(happyHour(BAR)).toBe("17–19 Uhr");
    expect(raucher(BAR)).toBe("innen");
    expect(happyHour(OHNE_BELEG)).toBeNull();
    expect(raucher(OHNE_BELEG)).toBeNull();
  });
});

describe("Filter", () => {
  const alle = [UERIGE, BAR, OHNE_BELEG];
  it("liest nur gültige Werte aus der URL", () => {
    const f = filterLesen({ spez: "altbier,quatsch", vibe: "gemuetlich", hh: "1", sort: "bewertung", anzahl: "18" });
    expect(f.spez).toEqual(["altbier"]);
    expect(f.vibe).toEqual(["gemuetlich"]);
    expect(f.hh).toBe(true);
    expect(f.sort).toBe("bewertung");
    expect(f.anzahl).toBe(18);
  });
  it("filtert nach Spezialität, Vibe, Stadtteil, Happy Hour, Raucher", () => {
    const leer = filterLesen({});
    expect(filtern(alle, { ...leer, spez: ["altbier"] }).map((o) => o.id)).toEqual(["1"]);
    expect(filtern(alle, { ...leer, stadtteil: "flingern" }).map((o) => o.id)).toEqual(["2"]);
    expect(filtern(alle, { ...leer, hh: true }).map((o) => o.id)).toEqual(["2"]);
    expect(filtern(alle, { ...leer, raucher: true }).map((o) => o.id)).toEqual(["2"]);
    expect(filtern(alle, { ...leer, vibe: ["gemuetlich", "draussen-sitzen"] }).map((o) => o.id)).toEqual(["1"]);
  });
  it("baut saubere URLs und erkennt Parameter für noindex", () => {
    const f = filterLesen({});
    expect(filterHref("/guides/kneipen-bars", f, {})).toBe("/guides/kneipen-bars");
    expect(filterHref("/guides/kneipen-bars", f, { spez: ["altbier", "cocktails"], hh: true })).toBe("/guides/kneipen-bars?spez=altbier%2Ccocktails&hh=1");
    expect(hatParameter({})).toBe(false);
    expect(hatParameter({ anzahl: "18" })).toBe(true);
    expect(hatParameter({ stadtteil: "altstadt" })).toBe(true);
  });
});

describe("JSON-LD BarOrPub", () => {
  it("Pflichtfelder, Öffnungszeiten strukturiert, keine Bewertung", () => {
    const o = { ...BAR, extras: { ...BAR.extras, oeffnungszeiten_perioden: [{ open: { day: 5, hour: 18, minute: 0 }, close: { day: 6, hour: 2, minute: 0 } }] } };
    const d = barOrPubJsonLd(o, "https://diesdas.events");
    expect(d["@type"]).toBe("BarOrPub");
    expect(d.name).toBe("Cocktailbar");
    expect(d.url).toBe("https://diesdas.events/guides/kneipen-bars/test-2");
    expect(d.address).toMatchObject({ streetAddress: "Bolkerstraße 1", postalCode: "40213", addressLocality: "Düsseldorf" });
    expect(d.openingHoursSpecification).toEqual([
      { "@type": "OpeningHoursSpecification", dayOfWeek: "https://schema.org/Friday", opens: "18:00", closes: "02:00" },
    ]);
    expect(d.aggregateRating).toBeUndefined();
  });
  it("ungültige Perioden ergeben nichts", () => {
    expect(oeffnungszeitenSpec("Mo 18–2")).toEqual([]);
    expect(oeffnungszeitenSpec([{ close: { day: 1, hour: 2 } }])).toEqual([]);
  });
  it("Restaurant mit auch_kneipe behält seine Restaurant-URL", () => {
    const d = barOrPubJsonLd(ort({ id: "9", typ: "restaurant", extras: { auch_kneipe: true } }), "https://diesdas.events");
    expect(d.url).toBe("https://diesdas.events/guides/restaurants-cafes/test-9");
  });
});
