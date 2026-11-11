// Feinfilter je Kategorie (Unterkategorien aus der KI-Zuordnung, pipeline/unterkategorien.py)
import { describe, expect, it } from "vitest";
import { filtern, unterkategorienZaehlen } from "@/lib/ableitungen";
import { KATEGORIEN, kategorie } from "@/lib/kategorien";
import type { DddEvent, KategorieSlug } from "@/lib/typen";

const ev = (i: number, kat: KategorieSlug, unterkategorie: string | null) =>
  ({ id: `e${i}`, titel: `Event ${i}`, kategorie: kat, unterkategorie, datum: "2026-11-12", datum_bis: null, uhrzeit: "20:00" }) as DddEvent;

describe("Unterkategorien", () => {
  it("jede Kategorie hat eine Liste mit eindeutigen, URL-tauglichen Slugs", () => {
    for (const k of KATEGORIEN) {
      expect(k.unterkategorien.length, k.slug).toBeGreaterThan(0);
      const slugs = k.unterkategorien.map((u) => u.slug);
      expect(new Set(slugs).size).toBe(slugs.length);
      for (const s of slugs) expect(s).toMatch(/^[a-z0-9-]+$/);
      expect(slugs).not.toContain("keine"); // reserviert: „geprüft, nichts passt“
    }
    expect(kategorie("sonstiges").unterkategorien).toEqual([]);
  });

  it("Zähler nur mit Treffern, in fester Reihenfolge", () => {
    const events = [ev(1, "musik", "jazz"), ev(2, "musik", "jazz"), ev(3, "musik", "klassik"), ev(4, "musik", "keine"), ev(5, "kultur", "film")];
    expect(unterkategorienZaehlen(events, "musik")).toEqual([
      { slug: "klassik", name: "Klassik", anzahl: 1 },
      { slug: "jazz", name: "Jazz & Soul", anzahl: 2 },
    ]);
    expect(unterkategorienZaehlen([], "musik")).toEqual([]);
  });

  it("Filter „unter“", () => {
    const events = [ev(1, "musik", "jazz"), ev(2, "musik", "klassik"), ev(3, "musik", null)];
    expect(filtern(events, { kategorie: "musik", unter: "jazz", von: "2026-11-12", bis: "2026-11-12" }).map((e) => e.id)).toEqual(["e1"]);
  });
});
