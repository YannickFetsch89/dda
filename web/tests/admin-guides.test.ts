// Tests zu Stufe 3b (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.7): Bilder, Spielplätze, Weihnachtsmärkte, Clubs
import { describe, expect, it } from "vitest";
import {
  clubStand,
  codeBestaetigbar,
  eigenesBildErlaubt,
  fokusAusKlick,
  googleKandidaten,
  spielplatzFreischaltbar,
  spielplatzSperren,
  wmFreischaltbar,
} from "@/lib/admin/guides";
import { stammdatenPruefen } from "@/lib/admin/orte";

const NAME = "places/ChIJp5utnSG2uEcRiEASre9sJes/photos/AV-0GLces6_xqch0t";

describe("Bilder", () => {
  it("Google-Kandidaten: nur gültige Namen, Urheber nur mit https, höchstens 10", () => {
    const fotos = [
      { name: NAME, widthPx: 1440, heightPx: 961, authorAttributions: [{ displayName: "Nataliia Vitiuk", uri: "https://maps.google.com/x" }] },
      { name: "places/x/photos/../böse" },
      { name: `${NAME}b`, authorAttributions: [{ displayName: "X", uri: "javascript:alert(1)" }] },
      ...Array.from({ length: 12 }, (_, i) => ({ name: `${NAME}${i}` })),
    ];
    const k = googleKandidaten({ photos: fotos });
    expect(k).toHaveLength(10);
    expect(k[0]).toEqual({ name: NAME, breite: 1440, hoehe: 961, autor: "Nataliia Vitiuk", autor_url: "https://maps.google.com/x" });
    expect(k[1].autor_url).toBeNull();
    expect(googleKandidaten({})).toEqual([]);
  });

  it("eigene Bilder nur unter /ort-bilder", () => {
    expect(eigenesBildErlaubt("/ort-bilder/weihnachtsmaerkte/neusser-weihnachtsmarkt.webp")).toBe(true);
    expect(eigenesBildErlaubt("/ort-bilder/../geheim.webp")).toBe(false);
    expect(eigenesBildErlaubt("/fallback/theater-3.webp")).toBe(false);
    expect(eigenesBildErlaubt("/ort-bilder/orte/x.svg")).toBe(false);
  });

  it("Klick ins Bild → Prozent in 5er-Schritten", () => {
    expect(fokusAusKlick(0, 200)).toBe("0%");
    expect(fokusAusKlick(71, 200)).toBe("35%");
    expect(fokusAusKlick(250, 200)).toBe("100%");
    expect(fokusAusKlick(10, 0)).toBe("50%");
  });
});

describe("Spielplätze (wie score.py freischaltbar)", () => {
  it("sperrende Codes und Bestätigungen", () => {
    expect(spielplatzSperren({ pruefung: ["name_unklar", "access_private", "bezirk_abweichend"], bestaetigt: [] })).toEqual(["name_unklar", "access_private"]);
    expect(spielplatzSperren({ pruefung: ["access_private"], bestaetigt: ["access_private"] })).toEqual([]);
    expect(spielplatzFreischaltbar(false, { pruefung: ["gruppe_gemischt"], bestaetigt: ["gruppe_gemischt"] })).toBe(true);
    expect(spielplatzFreischaltbar(false, { ausgeschlossen: "Schulhof" })).toBe(false);
    expect(spielplatzFreischaltbar(true, {})).toBe(false);
    expect(codeBestaetigbar("kein_stadtteil")).toBe(false);
    expect(codeBestaetigbar("bezirk_abweichend")).toBe(true);
  });
});

describe("Weihnachtsmärkte (wie weihnachtsmaerkte_freischalten.sql)", () => {
  it("Freischalten nur mit Saison (von, bis, Zeiten) und ohne Ausschluss", () => {
    const saisons = { "2026": { von: "2026-11-19", bis: "2026-12-30", zeiten: [{ tage: "mo-so" }] } };
    expect(wmFreischaltbar(false, { saisons })).toBe(true);
    expect(wmFreischaltbar(false, { saisons: { "2026": { von: "2026-11-19", bis: "2026-12-30", zeiten: [] } } })).toBe(false);
    expect(wmFreischaltbar(false, { saisons, ausgeschlossen: "fällt aus" })).toBe(false);
    expect(wmFreischaltbar(true, { saisons })).toBe(false);
  });
});

describe("Clubs", () => {
  it("Stand: im Hub, Profil, Score, Freigabe", () => {
    expect(clubStand({ typ: "club", club: { passt: true }, club_score: { gesamt: 8 }, club_freigegeben: "2026-11-12", auch_club: null, kein_club: null })).toEqual({
      imHub: true,
      profil: true,
      score: 8,
      freigegeben: true,
    });
    expect(clubStand({ typ: "kneipe", club: null, club_score: null, club_freigegeben: null, auch_club: true, kein_club: "Bar" }).imHub).toBe(false);
  });
});

describe("Stammdaten aus CSV-Importen gesperrt (Q6)", () => {
  it("Weihnachtsmarkt und Spielplatz: Name, Adresse, Geo kommen aus der CSV", () => {
    expect(stammdatenPruefen({ name: "Neu" }, "weihnachtsmarkt").ok).toBe(false);
    expect(stammdatenPruefen({ latitude: "51.2", longitude: "6.7" }, "spielplatz").ok).toBe(false);
    expect(stammdatenPruefen({ name: "Neu" }, "kneipe").ok).toBe(true);
  });
});
