import { describe, expect, it } from "vitest";
import { symbolMotiv } from "@/lib/symbolbild";

const ev = (titel: string, datum: string, beschreibung: string | null = null, kategorie = "sonstiges") =>
  ({ titel, datum, beschreibung, quelle_name: null, kategorie }) as Parameters<typeof symbolMotiv>[0];

describe("Saisonale Symbolbilder", () => {
  it("Karneval am 11.11. und in der Session bis Aschermittwoch", () => {
    expect(symbolMotiv(ev("Hoppeditz-Erwachen", "2026-11-11"))).toBe("karneval");
    expect(symbolMotiv(ev("Sessionseröffnung im Brauhaus", "2026-11-11"))).toBe("karneval");
    expect(symbolMotiv(ev("Altweiber-Party", "2027-02-04"))).toBe("karneval");
    expect(symbolMotiv(ev("Kostümparty im Club", "2027-02-06"))).toBe("karneval");
  });

  it("kein Karneval für Datumsangaben „11.11.“ oder außerhalb der Zeitfenster", () => {
    expect(symbolMotiv(ev("VERLEGT AUF 11.11.2026 Musikstudio - Erste Schritte mit Logic Pro", "2026-11-10"))).not.toBe("karneval");
    expect(symbolMotiv(ev("ENTFÄLLT! 11.11.2026 | \"Kinder sicher im Internet\" in Bilk", "2026-11-11"))).not.toBe("karneval");
    expect(symbolMotiv(ev("Karnevalsparty", "2026-11-20"))).not.toBe("karneval");
    // Zeitfenster laut docs/fallback-bilder.md: bis einschließlich Aschermittwoch (2027: 10.02.)
    expect(symbolMotiv(ev("Karnevalsparty", "2027-02-10"))).toBe("karneval");
    expect(symbolMotiv(ev("Karnevalsparty", "2027-02-11"))).not.toBe("karneval");
  });

  it("Sankt Martin nur mit Martins-Wörtern, nicht bei jeder Laterne", () => {
    expect(symbolMotiv(ev("Martinszug durch Bilk", "2026-11-11"))).toBe("sankt-martin");
    expect(symbolMotiv(ev("Laternen basteln für Kinder", "2026-11-08"))).toBe("sankt-martin");
    expect(symbolMotiv(ev("Nachtwächter-Führung", "2026-11-12", "Mit Laterne und Hellebarde durch die Altstadt"))).not.toBe("sankt-martin");
    expect(symbolMotiv(ev("Martinszug", "2026-11-20"))).not.toBe("sankt-martin");
  });

  it("Halloween nur im Oktober", () => {
    expect(symbolMotiv(ev("Halloween Party", "2026-10-31"))).toBe("halloween");
    expect(symbolMotiv(ev("Halloween Party", "2026-11-01"))).not.toBe("halloween");
  });
});
