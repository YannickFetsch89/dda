// Tests zu Stufe 3c (Plan docs/plan-admin-dashboard-2026-11-23.md, 3.5): Vorschlagsarten und Sammel-Entscheidung
import { describe, expect, it } from "vitest";
import { SAMMEL_ARTEN, VORSCHLAG_ARTEN } from "@/lib/admin/vorschlaege";

describe("Vorschlagsarten", () => {
  it("alle fünf Arten, Werte wie in pipeline/vorschlaege.py", () => {
    expect(VORSCHLAG_ARTEN.map((a) => a.wert)).toEqual(["dublette", "gebiet", "ortsname", "ort_id", "adresse"]);
  });
  it("gesammelt nur die Orte-Arten – Zusammenlegen und Löschen bleiben Einzelentscheidungen", () => {
    expect(SAMMEL_ARTEN).toEqual(["ortsname", "ort_id", "adresse"]);
    expect(SAMMEL_ARTEN).not.toContain("dublette");
    expect(SAMMEL_ARTEN).not.toContain("gebiet");
  });
});
