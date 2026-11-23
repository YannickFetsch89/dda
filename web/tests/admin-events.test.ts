// Tests zu Events bearbeiten, Stufe 1d (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.4)
import { describe, expect, it } from "vitest";
import { eingabenPruefen, kategorieInDb, updateBauen, type EventZeile } from "@/lib/admin/events";

const bisher: EventZeile = {
  id: "e1",
  titel: "Konzert",
  datum: "2026-11-28",
  uhrzeit: "20:00:00",
  ort: "zakk",
  beschreibung: "Text mit Leerzeichen am Ende  ",
  kategorie: "musik",
  redaktion_felder: [],
  abgleich_datum: null,
};

describe("Eingaben prüfen (Whitelist)", () => {
  it("unbekannte Felder werden abgewiesen", () => {
    expect(eingabenPruefen({ slug: "x" }).ok).toBe(false);
    expect(eingabenPruefen({ status: "gepostet" }).ok).toBe(false);
  });

  it("Formate: Datum, Uhrzeit, Kategorie, Bild, Pflichtfelder", () => {
    expect(eingabenPruefen({ datum: "28.11.2026" }).ok).toBe(false);
    expect(eingabenPruefen({ uhrzeit: "25:00" }).ok).toBe(false);
    expect(eingabenPruefen({ kategorie: "quatsch" }).ok).toBe(false);
    expect(eingabenPruefen({ bild_url: "http://unsicher.de/x.jpg" }).ok).toBe(false);
    expect(eingabenPruefen({ titel: "  " }).ok).toBe(false);
    expect(eingabenPruefen({ abgesagt: "ja" }).ok).toBe(false);
    const ok = eingabenPruefen({ uhrzeit: "19:30", kategorie: "familie", adresse: "", bild_url: "/ort-bilder/x.webp", abgesagt: true });
    expect(ok).toEqual({ ok: true, felder: { uhrzeit: "19:30", kategorie: "family", adresse: null, bild_url: "/ort-bilder/x.webp", abgesagt: true } });
  });

  it("Kategorie Website → DB", () => {
    expect(kategorieInDb("familie")).toBe("family");
    expect(kategorieInDb("musik")).toBe("musik");
    expect(kategorieInDb("family")).toBeNull();
  });
});

describe("Update mit Feldschutz und abgleich_* (4.4 Teil A und B)", () => {
  it("nur geänderte Felder; unberührte Felder (Leerzeichen, HH:MM:SS) gelten nicht als geändert", () => {
    const { update, geaendert } = updateBauen(bisher, { titel: "Konzert", uhrzeit: "20:00", beschreibung: "Text mit Leerzeichen am Ende" });
    expect(geaendert).toEqual([]);
    expect(update).toEqual({});
  });

  it("geändertes Feld kommt in redaktion_felder; Kategorie allein setzt keine abgleich_*", () => {
    const { update, geaendert } = updateBauen({ ...bisher, redaktion_felder: ["preis"] }, { kategorie: "kultur" });
    expect(geaendert).toEqual(["kategorie"]);
    expect(update).toEqual({ kategorie: "kultur", redaktion_felder: ["kategorie", "preis"] });
  });

  it("erste Änderung von Uhrzeit speichert die Werte der Quelle als abgleich_*", () => {
    const { update } = updateBauen(bisher, { uhrzeit: "19:30" });
    expect(update).toMatchObject({
      uhrzeit: "19:30",
      redaktion_felder: ["uhrzeit"],
      abgleich_titel: "Konzert",
      abgleich_datum: "2026-11-28",
      abgleich_uhrzeit: "20:00:00",
      abgleich_ort: "zakk",
    });
  });

  it("spätere Änderungen lassen abgleich_* stehen (das sind die Werte der Quelle)", () => {
    const { update } = updateBauen({ ...bisher, titel: "Konzert (neu)", abgleich_datum: "2026-11-28" }, { titel: "Konzert (ganz neu)" });
    expect(update).not.toHaveProperty("abgleich_titel");
    expect(update).not.toHaveProperty("abgleich_datum");
  });
});
