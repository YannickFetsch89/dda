import { describe, expect, it } from "vitest";
import { filterHref, filterLesen, filtern, typUmschalten } from "@/lib/guide-filter";
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
