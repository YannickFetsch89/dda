import { describe, expect, it } from "vitest";
import { filterHref, filterLesen, filtern, preisDetail, preisKurz, preisStufeOrt, stadtteileText, typUmschalten } from "@/lib/guide-filter";
import { filterHref as kneipenHref, filterLesen as kneipenLesen, hatParameter } from "@/lib/kneipen";
import type { DddOrt } from "@/lib/typen";

const B = "/guides/restaurants-cafes";

function ort(id: string, typ: string, extras: Record<string, unknown> = {}): DddOrt {
  return {
    id, name: id, slug: id, typ, untertitel: null, beschreibung: null, highlight: null, adresse: null, stadtteil: "Altstadt",
    latitude: 51.2, longitude: 6.7, bild_url: null, bild_attribution: null, tags: [], preis_niveau: null, oeffnungszeiten: null,
    webseite: null, telefon: null, instagram: null, google_place_id: null, google_rating: null, google_bewertungen_anzahl: null,
    qualitaets_score: 8, extras, sortierung: 0, erstellt_am: null, aktualisiert_am: null,
  } as DddOrt;
}

describe("Restaurant-Hub: Standard und Mehrfachauswahl", () => {
  it("ohne Parameter: Restaurants + Cafés in der Kartenansicht", () => {
    const f = filterLesen({});
    expect(f.typen.sort()).toEqual(["cafe", "restaurant"]);
    expect(f.ansicht).toBe("karte");
    expect(filterHref(B, f, {})).toBe(B);
  });
  it("alte Links bleiben gültig", () => {
    expect(filterLesen({ typ: "cafe" }).typen).toEqual(["cafe"]);
    expect(filterLesen({ ansicht: "karte" }).ansicht).toBe("karte");
    expect(filterLesen({ kueche: "italienisch" }).kuechen).toEqual(["italienisch"]);
  });
  it("„alle“, Grid und mehrere Küchen in der URL", () => {
    const f = filterLesen({ typ: "alle", ansicht: "grid", kueche: "italienisch,japanisch" });
    expect(f.typen).toHaveLength(3);
    expect(filterHref(B, f, {})).toBe(`${B}?typ=alle&kueche=italienisch,japanisch&ansicht=grid`);
  });
  it("Art umschalten lässt nie eine leere Auswahl", () => {
    expect(typUmschalten(["cafe"], "cafe")).toEqual(["cafe"]);
    expect(typUmschalten(["restaurant", "cafe"], "cafe")).toEqual(["restaurant"]);
  });
  it("Standard blendet Schnellimbisse aus, Brauhäuser zählen als Restaurant", () => {
    const orte = [ort("r", "restaurant"), ort("c", "cafe"), ort("i", "imbiss"), ort("b", "kneipe", { auch_restaurant: true })];
    expect(filtern(orte, filterLesen({})).map((o) => o.id)).toEqual(["r", "c", "b"]);
    expect(filtern(orte, filterLesen({ typ: "imbiss" })).map((o) => o.id)).toEqual(["i"]);
  });
});

describe("Kneipen-Hub: Kartenansicht", () => {
  it("Karte ist Standard, Grid steht in der URL und ist noindex", () => {
    const f = kneipenLesen({});
    expect(f.ansicht).toBe("karte");
    expect(kneipenHref("/guides/kneipen-bars", f, {})).toBe("/guides/kneipen-bars");
    expect(kneipenHref("/guides/kneipen-bars", f, { ansicht: "grid" })).toBe("/guides/kneipen-bars?ansicht=grid");
    expect(hatParameter({ ansicht: "grid" })).toBe(true);
  });
});

describe("Mehrfachauswahl Stadtteile und Art", () => {
  const orte = [ort("a", "restaurant"), { ...ort("b", "restaurant"), stadtteil: "Bilk" }, { ...ort("c", "restaurant"), stadtteil: "Flingern" }];
  it("Restaurants: mehrere Stadtteile (ODER), alter Einzel-Link gültig", () => {
    const f = filterLesen({ stadtteil: "bilk,flingern" });
    expect(f.stadtteile).toEqual(["bilk", "flingern"]);
    expect(filtern(orte, f).map((o) => o.id)).toEqual(["b", "c"]);
    expect(filterHref(B, f, {})).toBe(`${B}?stadtteil=bilk,flingern`);
    expect(filterLesen({ stadtteil: "altstadt" }).stadtteile).toEqual(["altstadt"]);
  });
  it("Kneipen: mehrere Arten und Stadtteile, ungültige Werte fallen weg", () => {
    const f = kneipenLesen({ art: "brauhaus,bar,quatsch", stadtteil: "altstadt,bilk" });
    expect(f.arten).toEqual(["bar", "brauhaus"]);
    expect(f.stadtteile).toEqual(["altstadt", "bilk"]);
    expect(kneipenHref("/guides/kneipen-bars", f, {})).toBe("/guides/kneipen-bars?art=bar,brauhaus&stadtteil=altstadt,bilk");
  });
  it("Statuszeile für Stadtteile", () => {
    const name = (s: string) => s[0].toUpperCase() + s.slice(1);
    expect(stadtteileText([], name)).toBe("");
    expect(stadtteileText(["bilk", "flingern"], name)).toBe(" in Bilk & Flingern");
    expect(stadtteileText(["a", "b", "c"], name)).toBe(" in 3 Stadtteilen");
  });
});

describe("Preis pro Person", () => {
  const mitPreis = (id: string, preis_pp: unknown, google?: unknown, niveau: string | null = "€€") =>
    ({ ...ort(id, "restaurant", { preis_pp, ...(google ? { google_preisspanne: google } : {}) }), preis_niveau: niveau }) as DddOrt;
  it("Stufen aus der Spanne", () => {
    expect(preisStufeOrt(mitPreis("a", { von: 10, bis: 20, quelle: "google" }))).toBe(1);
    expect(preisStufeOrt(mitPreis("b", { von: 20, bis: 30, quelle: "google" }))).toBe(2);
    expect(preisStufeOrt(mitPreis("c", { von: 30, bis: 60, quelle: "google" }))).toBe(3);
    expect(preisStufeOrt(mitPreis("d", { von: 100, bis: null, quelle: "google" }))).toBe(4);
    // Fine Dining laut Google, auch wenn das günstigste Menü auf der Website darunter liegt
    expect(preisStufeOrt(mitPreis("e", { von: 89, bis: 89, quelle: "website" }, { von: 100, bis: null }))).toBe(4);
    // ohne Spanne: alte €-Stufe
    expect(preisStufeOrt(mitPreis("f", null, undefined, "€€€"))).toBe(3);
  });
  it("Anzeige kurz und auf der Detailseite", () => {
    expect(preisKurz(mitPreis("a", { von: 10, bis: 20, quelle: "google" }))).toBe("10–20 €");
    expect(preisKurz(mitPreis("d", { von: 100, bis: null, quelle: "google" }))).toBe("ab 100 €");
    expect(preisKurz(mitPreis("g", { von: 169, bis: 199, quelle: "website" }))).toBe("Menü 169–199 €");
    expect(preisDetail(mitPreis("a", { von: 10, bis: 20, quelle: "google+bewertungen" }))).toEqual({ zeile: "ca. 10–20 € pro Person", herkunft: "laut Google und Gästebewertungen" });
    expect(preisDetail(mitPreis("g", { von: 189, bis: 189, quelle: "website" }))?.zeile).toBe("Menü 189 € pro Person");
  });
  it("Filter mit Stufe 4", () => {
    const orte = [mitPreis("a", { von: 10, bis: 20 }), mitPreis("d", { von: 100, bis: null })];
    expect(filtern(orte, filterLesen({ preis: "4" })).map((o) => o.id)).toEqual(["d"]);
    expect(filterLesen({ preis: "1,4,5" }).preise).toEqual([1, 4]);
  });
});
