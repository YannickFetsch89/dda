// SEO-/GEO-Plan Nov. 2026, Phase B: Landingpages (Kategorie, Stadtteil, Guide-Stadtteil), 301 für Einzelfilter,
// Organization/WebSite
import { describe, expect, it } from "vitest";
import { KATEGORIE_TEXTE, STADTTEIL_TEXTE } from "@/lib/landing-texte";
import {
  bezirkSatz, guideStadtteilPfad, kategoriePfad, nachbarStadtteile, stadtteilAusSlug, stadtteilPfad, stadtteilSlug,
} from "@/lib/landing";
import { KATEGORIEN } from "@/lib/kategorien";
import { entdeckenZiel, pfadPruefen, routeVon } from "@/lib/pfad-pruefung";
import { MARKE_SATZ, markeJsonLd } from "@/lib/seo";
import { BEZIRKE } from "@/lib/stadtteile";

describe("Slugs und Pfade", () => {
  it("Stadtteile: Anzeigename im Slug, Rückweg eindeutig", () => {
    expect(stadtteilSlug("Hafen")).toBe("medienhafen");
    expect(stadtteilSlug("Mörsenbroich")).toBe("moersenbroich");
    expect(stadtteilSlug("Flingern-Nord")).toBe("flingern-nord");
    expect(stadtteilAusSlug("medienhafen")).toBe("Hafen");
    expect(stadtteilAusSlug("FLINGERN")).toBe("Flingern");
    expect(stadtteilAusSlug("neuss")).toBeNull(); // Events: nur der Düsseldorfer Katalog
    expect(stadtteilAusSlug("neuss", true)).toBe("Neuss"); // Guides: auch die Nachbarstädte
    const alle = BEZIRKE.flatMap((b) => b.stadtteile);
    expect(new Set(alle.map(stadtteilSlug)).size).toBe(alle.length);
    for (const s of alle) expect(stadtteilAusSlug(stadtteilSlug(s))).toBe(s);
  });

  it("Links nur auf Seiten, die es gibt", () => {
    expect(stadtteilPfad("Unterbilk")).toBe("/stadtteil/unterbilk");
    expect(stadtteilPfad("Neuss")).toBeNull();
    expect(stadtteilPfad(null)).toBeNull();
    expect(kategoriePfad("musik")).toBe("/kategorie/musik");
    expect(kategoriePfad("sonstiges")).toBeNull();
    expect(kategoriePfad("family")).toBeNull();
    expect(guideStadtteilPfad("restaurants-cafes", "Hafen")).toBe("/guides/restaurants-cafes/stadtteil/medienhafen");
  });

  it("Bezirks-Satz und Nachbarn", () => {
    expect(bezirkSatz("Flingern")).toBe("Flingern gehört zum Düsseldorfer Stadtbezirk 2 (Flingern & Düsseltal).");
    expect(bezirkSatz("Neuss")).toContain("Nachbarschaft");
    expect(nachbarStadtteile("Bilk")).toContain("Unterbilk");
    expect(nachbarStadtteile("Bilk")).not.toContain("Bilk");
  });

  it("Texte: jede Kategorie hat einen eigenen Text, Stadtteiltexte nur für bekannte Stadtteile", () => {
    for (const k of KATEGORIEN) expect(KATEGORIE_TEXTE[k.slug]?.length, k.slug).toBeGreaterThan(0);
    for (const st of Object.keys(STADTTEIL_TEXTE)) expect(stadtteilAusSlug(stadtteilSlug(st), true), st).toBe(st);
    // Keine Schablone: kein Text beginnt wie ein anderer
    const anfaenge = Object.values(STADTTEIL_TEXTE).map((t) => t.split(" ").slice(0, 3).join(" "));
    expect(new Set(anfaenge).size).toBe(anfaenge.length);
  });
});

describe("Proxy: Landingpages", () => {
  it("erkennt die neuen Routen", () => {
    expect(routeVon("/kategorie/musik")).toEqual({ typ: "kategorie", slug: "musik" });
    expect(routeVon("/stadtteil/flingern")).toEqual({ typ: "stadtteil", slug: "flingern" });
    expect(routeVon("/guides/restaurants-cafes/stadtteil/unterbilk")).toEqual({ typ: "guide-stadtteil", hub: "restaurants-cafes", slug: "unterbilk" });
    expect(routeVon("/guides/spielplaetze/stadtteil/unterbilk")).toEqual({ typ: "guide-stadtteil", hub: "spielplaetze", slug: "unterbilk" });
  });

  it("echte 404 für Unbekanntes, ohne Netz", async () => {
    expect(await pfadPruefen("/kategorie/musik")).toEqual({ art: "weiter" });
    expect(await pfadPruefen("/kategorie/gibtsnicht")).toEqual({ art: "fehlt" });
    expect(await pfadPruefen("/kategorie/sonstiges")).toEqual({ art: "fehlt" });
    expect(await pfadPruefen("/stadtteil/medienhafen")).toEqual({ art: "weiter" });
    expect(await pfadPruefen("/stadtteil/neuss")).toEqual({ art: "fehlt" });
    expect(await pfadPruefen("/guides/clubs/stadtteil/neuss")).toEqual({ art: "weiter" });
    expect(await pfadPruefen("/guides/clubs/stadtteil/atlantis")).toEqual({ art: "fehlt" });
  });

  it("301 nur für genau einen Filter, der eine Landingpage trifft", () => {
    const z = (q: string) => entdeckenZiel(new URLSearchParams(q));
    expect(z("kategorie=musik")).toBe("/kategorie/musik");
    expect(z("stadtteil=Flingern")).toBe("/stadtteil/flingern");
    expect(z("stadtteil=Hafen")).toBe("/stadtteil/medienhafen");
    expect(z("kategorie=musik&datum=woche")).toBeNull(); // interne Filter-Links
    expect(z("kategorie=sonstiges")).toBeNull();
    expect(z("stadtteil=Neuss")).toBeNull();
    expect(z("q=jazz")).toBeNull();
    expect(z("")).toBeNull();
    expect(z("kategorie=musik&q=")).toBe("/kategorie/musik"); // leere Parameter zählen nicht
  });
});

describe("Organization und WebSite", () => {
  it("eine Entität für Domain und Schreibweise, Suche mit dem echten Parameter", () => {
    const d = markeJsonLd("https://diesdas.events") as { "@graph": Record<string, unknown>[] };
    const [org, site] = d["@graph"];
    expect(org).toMatchObject({ "@type": "Organization", name: "dies.das.düsseldorf", description: MARKE_SATZ });
    expect(site).toMatchObject({ "@type": "WebSite", alternateName: "diesdas.events", publisher: { "@id": "https://diesdas.events/#organisation" } });
    expect(JSON.stringify(site)).toContain("/entdecken?q={search_term_string}");
  });
});
