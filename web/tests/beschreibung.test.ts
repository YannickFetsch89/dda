import { describe, expect, it } from "vitest";
import { beschreibungsBloecke, kurzBeschreibung } from "@/lib/beschreibung";

const TEXT = `Du willst die zweite Altstadt erkunden? Bei dieser Tour bestimmst du das Tempo.

• Geschichten rund um die Kaiserpfalz
• Rätsel und Details

👉 Ohne Anmeldung nutzbar.
Auch offline.`;

describe("beschreibungsBloecke", () => {
  it("zerlegt in Absätze und Listen", () => {
    expect(beschreibungsBloecke(TEXT)).toEqual([
      { art: "absatz", zeilen: ["Du willst die zweite Altstadt erkunden? Bei dieser Tour bestimmst du das Tempo."] },
      { art: "liste", punkte: ["Geschichten rund um die Kaiserpfalz", "Rätsel und Details"] },
      { art: "absatz", zeilen: ["👉 Ohne Anmeldung nutzbar.", "Auch offline."] },
    ]);
  });

  it("kurzer Text ohne Umbruch bleibt ein Absatz", () => {
    expect(beschreibungsBloecke("Ein Abend mit Jazz.")).toEqual([{ art: "absatz", zeilen: ["Ein Abend mit Jazz."] }]);
    expect(beschreibungsBloecke(null)).toEqual([]);
  });
});

describe("kurzBeschreibung", () => {
  it("macht Fließtext ohne Listenzeichen", () => {
    expect(kurzBeschreibung(TEXT, 500)).toBe(
      "Du willst die zweite Altstadt erkunden? Bei dieser Tour bestimmst du das Tempo. Geschichten rund um die Kaiserpfalz Rätsel und Details 👉 Ohne Anmeldung nutzbar. Auch offline.",
    );
  });

  it("kürzt an einer Wortgrenze", () => {
    const kurz = kurzBeschreibung(TEXT, 60)!;
    expect(kurz.length).toBeLessThanOrEqual(60);
    expect(kurz.endsWith("…")).toBe(true);
    expect(kurz).toBe("Du willst die zweite Altstadt erkunden? Bei dieser Tour…");
  });

  it("leer bleibt leer", () => {
    expect(kurzBeschreibung("  ")).toBeNull();
  });
});
