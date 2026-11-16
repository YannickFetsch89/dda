import { describe, expect, it } from "vitest";
import { istEigenerZeitraum, kostenlosKennzahl, tagesleistenLaenge, zeitraumAuflösen, zeitraumImSatz, zeitraumKey, findetStatt } from "@/lib/datum";
import { ev } from "./hilfen";

const HEUTE = "2026-11-12"; // Donnerstag

describe("Kostenlos-Kennzahl", () => {
  it("heute, ein Tag und Zeiträume", () => {
    expect(kostenlosKennzahl(zeitraumAuflösen(undefined, HEUTE), HEUTE)).toBe("kostenlos heute");
    expect(kostenlosKennzahl(zeitraumAuflösen("morgen", HEUTE), HEUTE)).toBe("kostenlos Fr 13.11.");
    expect(kostenlosKennzahl(zeitraumAuflösen("2026-12-03", HEUTE), HEUTE)).toBe("kostenlos Do 03.12.");
    expect(kostenlosKennzahl(zeitraumAuflösen("wochenende", HEUTE), HEUTE)).toBe("kostenlos dieses Wochenende");
    expect(kostenlosKennzahl(zeitraumAuflösen("woche", HEUTE), HEUTE)).toBe("kostenlos diese Woche");
    expect(kostenlosKennzahl(zeitraumAuflösen("monat", HEUTE), HEUTE)).toBe("kostenlos in den nächsten 30 Tagen");
    expect(kostenlosKennzahl(zeitraumAuflösen("alle", HEUTE), HEUTE)).toBe("kostenlos in 60 Tagen");
    expect(kostenlosKennzahl(zeitraumAuflösen("unbekannt", HEUTE), HEUTE)).toBe("kostenlos heute");
  });
});

describe("Eigener Zeitraum aus dem Kalender (datum=von_bis)", () => {
  it("Start und Ende einschließlich, Label groß, Kennzahl ohne Kleinschreibung", () => {
    const z = zeitraumAuflösen("2026-11-18_2026-11-22", HEUTE);
    expect(z).toEqual({ key: "2026-11-18_2026-11-22", label: "Mi 18.11. – So 22.11.", von: "2026-11-18", bis: "2026-11-22" });
    expect(kostenlosKennzahl(z, HEUTE)).toBe("kostenlos Mi 18.11. – So 22.11.");
    expect(istEigenerZeitraum(z.key)).toBe(true);
    expect(zeitraumImSatz(z)).toBe("Mi 18.11. – So 22.11.");
    expect(zeitraumImSatz(zeitraumAuflösen("woche", HEUTE))).toBe("diese Woche");
  });
  it("gleicher Start und Ende = einzelner Tag; zeitraumKey baut beides", () => {
    expect(zeitraumAuflösen("2026-11-20_2026-11-20", HEUTE)).toEqual({ key: "2026-11-20", label: "Fr 20.11.", von: "2026-11-20", bis: "2026-11-20" });
    expect(zeitraumKey("2026-11-20", "2026-11-20")).toBe("2026-11-20");
    expect(zeitraumKey("2026-11-20", "2026-11-22")).toBe("2026-11-20_2026-11-22");
  });
  it("Vergangenes beginnt heute, höchstens 60 Tage, ungültige Angaben → heute", () => {
    expect(zeitraumAuflösen("2026-11-01_2026-11-15", HEUTE)).toMatchObject({ von: HEUTE, bis: "2026-11-15", key: "2026-11-12_2026-11-15" });
    expect(zeitraumAuflösen("2026-11-12_2027-06-01", HEUTE)).toMatchObject({ von: HEUTE, bis: "2027-01-10" });
    expect(zeitraumAuflösen("2026-11-22_2026-11-18", HEUTE).key).toBe("heute"); // Ende vor Start
    expect(zeitraumAuflösen("2026-11-01_2026-11-05", HEUTE).key).toBe("heute"); // ganz vorbei
    expect(zeitraumAuflösen("2026-02-30_2026-03-02", HEUTE).key).toBe("heute"); // kein echter Tag
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
