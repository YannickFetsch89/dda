// Fernpool und Monats-Label (Plan docs/plan-quellen-ausbau-2026-11-23.md, 6.1/6.2, Schritt W1)
import { describe, expect, it } from "vitest";
import { MAX_ZEITRAUM_TAGE, monatName, monatsLabel, nachMonat } from "@/lib/datum";
import { FERN_AB_TAG, FERN_BIS_TAG, istFern } from "@/lib/daten";

const HEUTE = "2026-11-24";

describe("Fernpool-Grenzen", () => {
  it("beginnt an Tag 61 und reicht bis Tag 365", () => {
    expect(FERN_AB_TAG).toBe(61);
    expect(FERN_BIS_TAG).toBe(365);
    expect(istFern("2027-01-23", HEUTE)).toBe(false); // Tag 60
    expect(istFern("2027-01-24", HEUTE)).toBe(true); // Tag 61
    expect(MAX_ZEITRAUM_TAGE).toBe(366);
  });
});

describe("Monats-Label", () => {
  it("erst hinter Tag 60, Monat groß mit Jahr", () => {
    expect(monatsLabel("2027-01-23", HEUTE)).toBeNull();
    expect(monatsLabel("2027-03-14", HEUTE)).toBe("MÄRZ 2027");
    expect(monatsLabel("kaputt", HEUTE)).toBeNull();
  });

  it("gruppiert Termine nach Monat in Reihenfolge", () => {
    const gruppen = nachMonat([{ datum: "2027-03-01" }, { datum: "2027-03-20" }, { datum: "2027-04-02" }]);
    expect(gruppen.map((g) => [g.monat, g.termine.length])).toEqual([["März 2027", 2], ["April 2027", 1]]);
    expect(monatName("2027-12-31")).toBe("Dezember 2027");
  });
});
