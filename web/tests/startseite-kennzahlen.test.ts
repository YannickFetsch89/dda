import { describe, expect, it } from "vitest";
import { kostenlosKennzahl, tagesleistenLaenge, zeitraumAuflösen, findetStatt } from "@/lib/datum";
import { ev } from "./hilfen";

const HEUTE = "2026-11-12"; // Donnerstag

describe("Kostenlos-Kennzahl", () => {
  it("heute, ein Tag und Zeiträume", () => {
    expect(kostenlosKennzahl(zeitraumAuflösen(undefined, HEUTE), HEUTE)).toBe("kostenlos heute");
    expect(kostenlosKennzahl(zeitraumAuflösen("morgen", HEUTE), HEUTE)).toBe("kostenlos am Fr 13.11.");
    expect(kostenlosKennzahl(zeitraumAuflösen("2026-12-03", HEUTE), HEUTE)).toBe("kostenlos am Do 03.12.");
    expect(kostenlosKennzahl(zeitraumAuflösen("wochenende", HEUTE), HEUTE)).toBe("kostenlos dieses Wochenende");
    expect(kostenlosKennzahl(zeitraumAuflösen("woche", HEUTE), HEUTE)).toBe("kostenlos diese Woche");
    expect(kostenlosKennzahl(zeitraumAuflösen("monat", HEUTE), HEUTE)).toBe("kostenlos in den nächsten 30 Tagen");
    expect(kostenlosKennzahl(zeitraumAuflösen("alle", HEUTE), HEUTE)).toBe("kostenlos in 60 Tagen");
    expect(kostenlosKennzahl(zeitraumAuflösen("unbekannt", HEUTE), HEUTE)).toBe("kostenlos heute");
  });
});

describe("Tagesleiste", () => {
  it("60 Tage, bei einem ferneren Tag 14 Tage danach, höchstens 366", () => {
    expect(tagesleistenLaenge(HEUTE, HEUTE)).toBe(60);
    expect(tagesleistenLaenge(HEUTE, "2026-12-03")).toBe(60);
    const fern = "2027-02-01";
    const tage = tagesleistenLaenge(HEUTE, fern);
    expect(tage).toBeGreaterThan(60);
    expect(tage).toBeLessThanOrEqual(366);
    expect(tagesleistenLaenge(HEUTE, "2030-01-01")).toBe(366);
  });

  it("ein Zeitraum hat keinen einzelnen aktiven Tag, ein Datum schon", () => {
    for (const key of ["wochenende", "woche", "monat", "alle"]) {
      const z = zeitraumAuflösen(key, HEUTE);
      expect(z.von === z.bis).toBe(false);
    }
    const tag = zeitraumAuflösen("2026-12-03", HEUTE);
    expect(tag.von).toBe(tag.bis);
    const sonntag = zeitraumAuflösen("wochenende", "2026-11-15");
    expect(sonntag.von).toBe(sonntag.bis);
  });
});

describe("Mehrtägige Events in der Tagesliste", () => {
  const party = ev({ id: "p", kategorie: "nightlife", datum: "2026-09-19", datum_bis: "2026-10-18" });
  const ausstellung = ev({ id: "a", kategorie: "kultur", datum: "2026-09-19", datum_bis: "2026-10-18" });

  it("Party und Food laufen an jedem Tag, eine Ausstellung nur am Starttag", () => {
    expect(findetStatt(party, "2026-10-01", "2026-10-01")).toBe(true);
    expect(findetStatt(ausstellung, "2026-10-01", "2026-10-01")).toBe(false);
    expect(findetStatt(ausstellung, "2026-09-19", "2026-09-19")).toBe(true);
    const food = ev({ id: "f", kategorie: "food", datum: "2026-09-19", datum_bis: "2026-10-18" });
    expect(findetStatt(food, "2026-10-01", "2026-10-01")).toBe(true);
  });
});
