import { describe, expect, it } from "vitest";
import { orteSuchen, suchform } from "@/lib/orte-suche";
import type { DddOrt } from "@/lib/typen";

const ort = (id: string, name: string, typ = "restaurant", extras: Record<string, unknown> = {}, score = 8) =>
  ({ id, name, typ, slug: id, untertitel: null, stadtteil: "Altstadt", extras, qualitaets_score: score, tags: [] }) as unknown as DddOrt;

describe("Ortssuche", () => {
  const orte = [
    ort("1", "squarebar", "kneipe", { unterart: "bar" }),
    ort("2", "Café Schöne Aussicht", "cafe"),
    ort("3", "Brauerei im Füchschen", "kneipe", { unterart: "brauhaus" }),
    ort("4", "Trattoria La Castagnas", "restaurant", { google_primaertyp: "italian_restaurant" }),
    ort("5", "Bar Square One", "kneipe", { unterart: "bar" }),
  ];
  it("findet nach Name, unabhängig von Schreibweise und Umlauten", () => {
    expect(orteSuchen(orte, "squarebar").map((o) => o.id)).toEqual(["1"]);
    expect(orteSuchen(orte, "Square").map((o) => o.id)).toEqual(["1", "5"]); // Name beginnt mit … vor enthält …
    expect(orteSuchen(orte, "schoene aussicht").map((o) => o.id)).toEqual(["2"]);
    expect(orteSuchen(orte, "füchschen").map((o) => o.id)).toEqual(["3"]);
  });
  it("findet über Küche und Art", () => {
    expect(orteSuchen(orte, "italienisch").map((o) => o.id)).toEqual(["4"]);
    expect(orteSuchen(orte, "Brauhaus").map((o) => o.id)).toEqual(["3"]);
  });
  it("zu kurze Suche liefert nichts", () => {
    expect(orteSuchen(orte, "s")).toEqual([]);
    expect(orteSuchen(orte, undefined)).toEqual([]);
    expect(suchform("Café Ö-Bar")).toBe("cafeoebar");
  });
});
