// Tests zu Stufe 5a (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.10): „Rückgängig“ im Protokoll
import { describe, expect, it } from "vitest";
import { rueckgaengigPlan, type ProtokollEintrag } from "@/lib/admin/rueckgaengig";

const ID = "11111111-1111-4111-8111-111111111111";
const eintrag = (x: Partial<ProtokollEintrag>): ProtokollEintrag => ({
  id: "p1",
  aktion: "event_bearbeiten",
  tabelle: "events",
  ziel_id: ID,
  vorher: { titel: "Alt", kategorie: "family", uhrzeit: "19:00:00", adresse: null },
  nachher: { titel: "Neu", kategorie: "musik", uhrzeit: "20:00", adresse: "Hauptstraße 1", redaktion_felder: ["titel"] },
  ...x,
});

describe("Rückgängig", () => {
  it("alte Werte als Formular-Eingabe, wenn seitdem nichts geändert wurde", () => {
    const p = rueckgaengigPlan(eintrag({}), { titel: "Neu", kategorie: "musik", uhrzeit: "20:00:00", adresse: "Hauptstraße 1" });
    expect(p).toEqual({
      ok: true,
      tabelle: "events",
      id: ID,
      felder: { titel: "Alt", kategorie: "familie", uhrzeit: "19:00", adresse: "" },
      // Cursor-Prüfung 5a, Befund 4: dieselbe Bedingung im UPDATE
      erwartet: [["titel", "Neu"], ["kategorie", "musik"], ["uhrzeit", "20:00"], ["adresse", "Hauptstraße 1"]],
    });
  });
  it("inzwischen wieder geändert → nein", () => {
    const p = rueckgaengigPlan(eintrag({}), { titel: "Noch neuer", kategorie: "musik", uhrzeit: "20:00:00", adresse: "Hauptstraße 1" });
    expect(p).toEqual({ ok: false, fehler: expect.stringContaining("titel") });
  });
  it("nur einfache Feldänderungen, nur mit Datensatz", () => {
    expect(rueckgaengigPlan(eintrag({ aktion: "ort_zusammenlegen" }), {}).ok).toBe(false);
    expect(rueckgaengigPlan(eintrag({}), null).ok).toBe(false);
    expect(rueckgaengigPlan(eintrag({ vorher: null }), {}).ok).toBe(false);
  });
  it("Orte: Stammdaten zurück", () => {
    const p = rueckgaengigPlan(eintrag({ aktion: "ort_bearbeiten", tabelle: "orte", vorher: { adresse: "A 1" }, nachher: { adresse: "B 2" } }), { adresse: "B 2" });
    expect(p).toEqual({ ok: true, tabelle: "orte", id: ID, felder: { adresse: "A 1" }, erwartet: [["adresse", "B 2"]] });
  });
});
