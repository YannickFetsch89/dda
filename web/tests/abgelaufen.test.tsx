import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { gleicherOrt, istAbgelaufen, kommendeEmpfehlungen, MAX_EMPFEHLUNGEN, ortSchluessel } from "@/lib/abgelaufen";
import { AbgelaufenHinweis } from "@/components/abgelaufen-hinweis";
import { ev } from "./hilfen";

const HEUTE = "2026-11-05";

describe("istAbgelaufen", () => {
  it("eintägiges Event von gestern ist abgelaufen", () => {
    expect(istAbgelaufen({ datum: "2026-11-04", datum_bis: null }, HEUTE)).toBe(true);
  });
  it("Event von heute gilt bis Tagesende als laufend (auch wenn die Uhrzeit vorbei ist)", () => {
    expect(istAbgelaufen({ datum: HEUTE, datum_bis: null }, HEUTE)).toBe(false);
  });
  it("zukünftiges Event ist nicht abgelaufen", () => {
    expect(istAbgelaufen({ datum: "2026-12-01", datum_bis: null }, HEUTE)).toBe(false);
  });
  it("mehrtägiges Event zählt ab dem Enddatum", () => {
    expect(istAbgelaufen({ datum: "2026-10-01", datum_bis: HEUTE }, HEUTE)).toBe(false);
    expect(istAbgelaufen({ datum: "2026-10-01", datum_bis: "2026-12-31" }, HEUTE)).toBe(false);
    expect(istAbgelaufen({ datum: "2026-10-01", datum_bis: "2026-11-04" }, HEUTE)).toBe(true);
  });
  it("Jahreswechsel und Monatsgrenzen", () => {
    expect(istAbgelaufen({ datum: "2026-12-31", datum_bis: null }, "2027-01-01")).toBe(true);
    expect(istAbgelaufen({ datum: "2026-10-31", datum_bis: null }, "2026-11-01")).toBe(true);
  });
});

describe("Hinweis auf der Eventseite", () => {
  it("erscheint bei abgelaufenen Events mit Text und Link", () => {
    const html = renderToStaticMarkup(<AbgelaufenHinweis abgelaufen />);
    expect(html).toContain("Dieses Event hat bereits stattgefunden.");
    expect(html).toContain('href="/entdecken"');
    expect(html).toContain("Aktuelle Events in Düsseldorf entdecken");
  });
  it("erscheint nicht bei kommenden Events", () => {
    expect(renderToStaticMarkup(<AbgelaufenHinweis abgelaufen={false} />)).toBe("");
  });
});

describe("ortSchluessel", () => {
  it("vereinheitlicht Schreibweisen", () => {
    expect(ortSchluessel("ZAKK")).toBe(ortSchluessel("zakk"));
    expect(ortSchluessel("Tonhalle  Düsseldorf!")).toBe("tonhalle düsseldorf");
  });
  it("ignoriert zu allgemeine Orte", () => {
    expect(ortSchluessel("Düsseldorf")).toBeNull();
    expect(ortSchluessel("Online")).toBeNull();
  });
});

describe("gleicherOrt", () => {
  it("erkennt Schreibvarianten desselben Orts", () => {
    expect(gleicherOrt("Zentrum für Aktion, Kultur und Kommunikation", "zakk - Zentrum für Aktion, Kultur und Kommunikation")).toBe(true);
    expect(gleicherOrt("zakk – Halle", "zakk – Club")).toBe(true);
    expect(gleicherOrt("Tonhalle (Mendelssohn-Saal)", "Tonhalle")).toBe(true);
  });
  it("verknüpft nicht über allgemeine Teile oder Bindestriche im Namen", () => {
    expect(gleicherOrt("Düsseldorf – Altstadt", "Düsseldorf – Flingern")).toBe(false);
    expect(gleicherOrt("Mendelssohn-Saal", "Robert-Schumann-Saal")).toBe(false);
  });
});

describe("kommendeEmpfehlungen", () => {
  const alt = ev({ id: "alt", titel: "Comedy Night", ort: "zakk", kategorie: "kultur", datum: "2026-11-01" });

  it("priorisiert Reihe > Ort > Kategorie und nimmt nur kommende Events", () => {
    const kandidaten = [
      ev({ id: "kat", titel: "Lesung", ort: "Stadtbücherei", kategorie: "kultur", datum: "2026-11-06" }),
      ev({ id: "ort", titel: "Konzert", ort: "ZAKK", kategorie: "musik", datum: "2026-11-20" }),
      ev({ id: "reihe", titel: "Comedy Night", ort: "zakk", kategorie: "kultur", datum: "2026-12-01" }),
      ev({ id: "vergangen", titel: "Comedy Night", ort: "zakk", kategorie: "kultur", datum: "2026-11-02" }),
    ];
    const ids = kommendeEmpfehlungen(alt, kandidaten, HEUTE).map((e) => e.id);
    expect(ids.slice(0, 3)).toEqual(["reihe", "ort", "kat"]);
    expect(ids).not.toContain("vergangen");
  });

  it("lässt abgesagte Events und das Event selbst weg", () => {
    const kandidaten = [
      ev({ id: "abgesagt", titel: "Comedy Night", ort: "zakk", datum: "2026-12-01", abgesagt: true }),
      { ...alt, datum: "2026-12-05" }, // gleiche ID
    ];
    expect(kommendeEmpfehlungen(alt, kandidaten, HEUTE)).toEqual([]);
  });

  it(`liefert höchstens ${MAX_EMPFEHLUNGEN} Events`, () => {
    const viele = Array.from({ length: 12 }, (_, i) => ev({ id: `k${i}`, kategorie: "kultur", ort: `Ort ${i}`, datum: "2026-11-10" }));
    expect(kommendeEmpfehlungen(alt, viele, HEUTE)).toHaveLength(MAX_EMPFEHLUNGEN);
  });

  it("füllt mit anderen kommenden Events auf, wenn nichts Verwandtes da ist", () => {
    const fremd = [ev({ id: "x", titel: "Yoga", ort: "Rheinpark", kategorie: "sport", datum: "2026-11-08" })];
    expect(kommendeEmpfehlungen(alt, fremd, HEUTE).map((e) => e.id)).toEqual(["x"]);
  });

  it("laufende mehrtägige Events zählen als kommend", () => {
    const laufend = [ev({ id: "ausstellung", kategorie: "kultur", ort: "K20", datum: "2026-10-01", datum_bis: "2027-01-10" })];
    expect(kommendeEmpfehlungen(alt, laufend, HEUTE).map((e) => e.id)).toEqual(["ausstellung"]);
  });
});
