// Tests zu Stufe 5b (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.10): Meldungen freigeben
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { BESCHREIBUNG_MAX, freigabePruefen, kuerzen, slugErzeugen, slugMitSuffix, stadtteilAusAdresse } from "@/lib/admin/meldungen";

// Gemeinsame Prüfliste mit tests/test_admin_5b.py (pipeline/slug_generator.py)
const FIXTURE = JSON.parse(readFileSync(join(__dirname, "..", "..", "tests", "fixtures", "slugs.json"), "utf-8")) as {
  slugs: { titel: string; ort: string; datum: string; slug: string }[];
  suffix: { basis: string; vergeben: string[]; slug: string }[];
};

describe("Slug wie in Python", () => {
  it.each(FIXTURE.slugs)("$titel", (f) => {
    expect(slugErzeugen(f.titel, f.ort, f.datum)).toBe(f.slug);
  });
  it("Suffixe", () => {
    for (const f of FIXTURE.suffix) expect(slugMitSuffix(f.basis, new Set(f.vergeben))).toBe(f.slug);
  });
});

describe("Freigabe", () => {
  const gut = { titel: "Konzert im Park", kategorie: "musik", datum: "2026-12-01", ort: "Volksgarten", beschreibung: "Ein schönes Konzert unter freiem Himmel." };
  it("Pflichtfelder und Formate", () => {
    expect(freigabePruefen(gut).ok).toBe(true);
    expect(freigabePruefen({ ...gut, beschreibung: "kurz" }).ok).toBe(false);
    expect(freigabePruefen({ ...gut, kategorie: "quatsch" }).ok).toBe(false);
    expect(freigabePruefen({ ...gut, datum_bis: "2026-11-01" }).ok).toBe(false);
    expect(freigabePruefen({ ...gut, uhrzeit: "25:00" }).ok).toBe(false);
    expect(freigabePruefen({ ...gut, link: "javascript:alert(1)" }).ok).toBe(false);
  });
  it("Stadtteil aus der PLZ, Beschreibung gekürzt", () => {
    expect(stadtteilAusAdresse("Fichtenstraße 40, 40233 Düsseldorf")).toBeTruthy();
    expect(stadtteilAusAdresse("Hauptstraße 1, 41460 Neuss")).toBeNull();
    const lang = "Satz eins ist hier. ".repeat(30);
    expect(kuerzen(lang, 300).length).toBeLessThanOrEqual(300);
    expect(kuerzen(lang, 300).endsWith(".")).toBe(true);
  });
  it("Beschreibung: keine 300-Zeichen-Grenze mehr, Absätze bleiben (26.11.2026)", () => {
    const text = "Erster Absatz mit   doppelten Leerzeichen.\r\n\r\n\r\nZweiter Absatz.\n- Punkt eins\n- Punkt zwei";
    expect(kuerzen(text)).toBe("Erster Absatz mit doppelten Leerzeichen.\n\nZweiter Absatz.\n- Punkt eins\n- Punkt zwei");
    const mittel = "Ein ganz normaler Satz über das Event. ".repeat(30); // gut 1.100 Zeichen
    expect(kuerzen(mittel)).toBe(mittel.trim());
    expect(BESCHREIBUNG_MAX).toBe(2000);
    const zuLang = "Satz eins ist hier.\n".repeat(150); // 3.000 Zeichen
    const gekuerzt = kuerzen(zuLang);
    expect(gekuerzt.length).toBeLessThanOrEqual(BESCHREIBUNG_MAX);
    expect(gekuerzt.endsWith(".")).toBe(true);
    expect(gekuerzt).toContain("\n");
  });
});
