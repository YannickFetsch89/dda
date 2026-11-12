// Feinschliff-Roadmap Nov. 2026: Unterkategorie-Seiten, /kostenlos, Sätze auf /entdecken und /stadtteile
import { describe, expect, it } from "vitest";
import { unterkategorieGueltig, unterkategoriePfad } from "@/lib/landing";
import { kostenlosIndexierbar, unterkategorieIndexierbar, unterkategorieText } from "@/lib/landing-listen";
import { UNTERKATEGORIE_TEXTE } from "@/lib/landing-texte";
import { KATEGORIEN } from "@/lib/kategorien";
import { entdeckenZiel, pfadPruefen, routeVon } from "@/lib/pfad-pruefung";
import { entdeckenSatz, stadtteileSatz } from "@/lib/tagestext";
import type { DddEvent, EventPool, KategorieSlug } from "@/lib/typen";

const ev = (i: number, kategorie: KategorieSlug, mehr: Partial<DddEvent> = {}) =>
  ({ id: `e${i}`, titel: `Event ${i}`, kategorie, datum: "2026-11-13", datum_bis: null, uhrzeit: "20:00", ...mehr }) as DddEvent;
const pool = (events: DddEvent[], quelle: EventPool["quelle"] = "supabase") => ({ events, alle: events, heute: "2026-11-12", quelle }) as unknown as EventPool;

describe("Unterkategorie-Seiten", () => {
  it("Route und echte 404 vor dem Rendern", async () => {
    expect(routeVon("/kategorie/kultur/theater")).toEqual({ typ: "unterkategorie", kategorie: "kultur", unter: "theater" });
    expect(await pfadPruefen("/kategorie/kultur/theater")).toEqual({ art: "weiter" });
    expect(await pfadPruefen("/kategorie/kultur/gibt-es-nicht")).toEqual({ art: "fehlt" });
    expect(await pfadPruefen("/kategorie/musik/theater")).toEqual({ art: "fehlt" }); // gehört nicht zu Musik
    expect(await pfadPruefen("/kategorie/kultur/keine")).toEqual({ art: "fehlt" }); // reservierter Wert
    expect(await pfadPruefen("/kategorie/sonstiges/theater")).toEqual({ art: "fehlt" });
    expect(unterkategorieGueltig("food", "maerkte")).toBe(true);
    expect(unterkategoriePfad("kultur", "theater")).toBe("/kategorie/kultur/theater");
  });

  it("Texte nur für gültige Unterkategorien", () => {
    for (const schluessel of Object.keys(UNTERKATEGORIE_TEXTE)) {
      const [k, u] = schluessel.split("/");
      expect(unterkategorieGueltig(k, u), schluessel).toBe(true);
    }
  });

  it("indexierbar nur mit Text UND mindestens fünf Events", () => {
    const theater = Array.from({ length: 5 }, (_, i) => ev(i, "kultur", { unterkategorie: "theater" }));
    expect(unterkategorieIndexierbar(pool(theater), "kultur", "theater")).toBe(true);
    expect(unterkategorieIndexierbar(pool(theater.slice(0, 4)), "kultur", "theater")).toBe(false); // zu wenig
    expect(unterkategorieIndexierbar(pool(theater, "beispiel"), "kultur", "theater")).toBe(false); // Beispieldaten
    // Viele Events, aber kein freigegebener Text → nicht indexierbar
    const film = Array.from({ length: 9 }, (_, i) => ev(i, "kultur", { unterkategorie: "film" }));
    expect(unterkategorieText("kultur", "film")).toBeNull();
    expect(unterkategorieIndexierbar(pool(film), "kultur", "film")).toBe(false);
  });
});

describe("/kostenlos", () => {
  it("301 nur für genau preis=kostenlos", () => {
    const z = (q: string) => entdeckenZiel(new URLSearchParams(q));
    expect(z("preis=kostenlos")).toBe("/kostenlos");
    expect(z("preis=kostenlos&datum=woche")).toBeNull();
    expect(z("preis=sonstwas")).toBeNull();
    expect(z("preis=bezahlt")).toBeNull();
  });

  it("indexierbar ab fünf kostenlosen Events", () => {
    const gratis = Array.from({ length: 5 }, (_, i) => ev(i, "community", { preis: "kostenlos" }));
    expect(kostenlosIndexierbar(pool(gratis))).toBe(true);
    expect(kostenlosIndexierbar(pool(gratis.slice(0, 4)))).toBe(false);
  });
});

describe("Sätze auf /entdecken und /stadtteile", () => {
  it("Entdecken: Zahl und Kategorien, keine Ortsnamen, Sonstiges zählt nicht", () => {
    const events = [ev(1, "musik"), ev(2, "musik"), ev(3, "kultur"), ev(4, "sonstiges"), ev(5, "nightlife")];
    expect(entdeckenSatz(events)).toBe("In den nächsten sieben Tagen stehen in Düsseldorf 5 Events an, die meisten aus Musik, Kultur und Nightlife.");
    expect(entdeckenSatz([])).toBe("In den nächsten sieben Tagen sind in Düsseldorf noch keine Events eingetragen.");
  });

  it("Stadtteile: Zahl und drei Stadtteile mit Artikel, ohne Quote", () => {
    expect(stadtteileSatz(462, ["in Pempelfort", "in Flingern", "in der Friedrichstadt"])).toBe(
      "In den nächsten sieben Tagen stehen in Düsseldorf 462 Events an, die meisten in Pempelfort, in Flingern und in der Friedrichstadt.",
    );
    expect(stadtteileSatz(3, ["in Bilk"])).toBe("In den nächsten sieben Tagen stehen in Düsseldorf 3 Events an.");
    expect(stadtteileSatz(0, [])).toContain("noch keine Events");
  });
});

describe("Kategorien", () => {
  it("jede Kategorie hat Unterkategorien, „keine“ ist nie eine davon", () => {
    for (const k of KATEGORIEN) expect(k.unterkategorien.some((u) => u.slug === "keine")).toBe(false);
  });
});
