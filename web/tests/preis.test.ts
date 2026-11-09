import { describe, expect, it } from "vitest";
import { preisText } from "@/lib/daten";

describe("Preis-Schreibweise", () => {
  it("freier Eintritt heißt immer „kostenlos“", () => {
    for (const wert of ["Eintritt frei", "Kostenlos", "kostenfrei", "gratis", "0,00 €", "freier Eintritt"]) {
      expect(preisText(wert)).toBe("kostenlos");
    }
  });
  it("andere Angaben bleiben unverändert", () => {
    expect(preisText("kostenlos oder auf Anfrage")).toBe("kostenlos oder auf Anfrage");
    expect(preisText("10,00 €")).toBe("10,00 €");
    expect(preisText("  ")).toBeNull();
    expect(preisText(null)).toBeNull();
  });
});
