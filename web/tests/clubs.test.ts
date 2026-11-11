import { describe, expect, it } from "vitest";
import {
  CLUB_STANDARD, clubArt, clubBeschreibung, clubFilterHref, clubFilterLesen, clubHatParameter, clubProfil, clubsFiltern,
  clubsSortieren, eintrittKurz, eintrittStufe, hauptGenres, istSichtbarerClub,
} from "@/lib/clubs";
import type { DddOrt } from "@/lib/typen";

function ort(name: string, extras: Record<string, unknown>, mehr: Partial<DddOrt> = {}): DddOrt {
  return {
    id: name, name, slug: name.toLowerCase().replace(/\s+/g, "-"), typ: "club", untertitel: null, beschreibung: "Club-Text",
    highlight: null, adresse: null, stadtteil: "Altstadt", latitude: null, longitude: null, bild_url: null, bild_attribution: null,
    tags: [], preis_niveau: null, oeffnungszeiten: null, webseite: null, telefon: null, instagram: null, google_place_id: null,
    google_rating: 4.2, google_bewertungen_anzahl: 300, qualitaets_score: 8, extras, sortierung: 0, erstellt_am: null,
    aktualisiert_am: null, ...mehr,
  };
}

const profil = (p: Record<string, unknown> = {}) => ({
  passt: true, unterart: "club", genres: [{ wert: "Techno", anteil: "haupt", zitat: "x" }, { wert: "House", anteil: "neben" }],
  formate: [{ name: "Resident Night", rhythmus: "jeden Freitag", musik: "Techno" }], zusatz_events: [],
  fakten: { oeffnung: { text: "Fr und Sa ab 23 Uhr" }, unbekannt: { text: "weg" } }, eintritt: { min: 10, max: 15 },
  dresscode: "egal", publikum: ["Underground"], ausstattung: [], instagram: "javascript:alert(1)",
  resident_advisor: "https://ra.co/clubs/123", event_orte: ["Salon"], ...p,
});

const SALON = ort("Salon", { club: profil(), club_score: { gesamt: 9, programm: 9 } });
const SCHLAGER = ort("Schlager Cafe", {
  auch_club: true, club_unterart: "partylocation", club_beschreibung: "Party-Text",
  club: profil({ unterart: "partylocation", genres: [{ wert: "Schlager", anteil: "haupt" }], eintritt: { min: 0, max: null } }),
  club_score: { gesamt: 7, programm: 6 },
}, { typ: "restaurant", beschreibung: "Restaurant-Text", qualitaets_score: 5 });
const SCHWACH = ort("Schwach", { club: profil(), club_score: { gesamt: 6 } });
const PASST_NICHT = ort("Sauna", { club: profil({ passt: false }), club_score: { gesamt: 9 } });

describe("clubProfil", () => {
  it("normalisiert und verwirft Unbekanntes", () => {
    const p = clubProfil(SALON)!;
    expect(p.genres.map((g) => g.wert)).toEqual(["Techno", "House"]);
    expect(p.fakten).toEqual({ oeffnung: "Fr und Sa ab 23 Uhr" });
    expect(p.dresscode).toBe("Egal");
    expect(p.instagram).toBeNull(); // kein https-Instagram-Link
    expect(p.residentAdvisor).toBe("https://ra.co/clubs/123");
  });
});

describe("Sichtbarkeit und Texte", () => {
  it("Club-Score ≥ 7 und passt – unabhängig vom qualitaets_score des Haupt-Hubs", () => {
    expect(istSichtbarerClub(SALON)).toBe(true);
    expect(istSichtbarerClub(SCHLAGER)).toBe(true);
    expect(istSichtbarerClub(SCHWACH)).toBe(false);
    expect(istSichtbarerClub(PASST_NICHT)).toBe(false);
  });

  it("auch_club nutzt eigene Club-Texte und Unterart", () => {
    expect(clubBeschreibung(SCHLAGER)).toBe("Party-Text");
    expect(clubBeschreibung(SALON)).toBe("Club-Text");
    expect(clubArt(SCHLAGER)).toBe("partylocation");
    expect(hauptGenres(SALON)).toEqual(["Techno"]);
  });

  it("Eintritt nur mit Beleg von Website/Presse", () => {
    const ausBewertung = ort("Bewertet", { club: profil({ eintritt: { max: 35 }, fakten: { eintritt: { text: "teils 35 €", quelle: "Google (Kurzbeschreibung und Bewertungen)" } } }), club_score: { gesamt: 8 } });
    expect(eintrittKurz(ausBewertung)).toBeNull();
    const nurMax = ort("Bis", { club: profil({ eintritt: { max: 20 }, fakten: { eintritt: { text: "unter 20 €", quelle: "https://presse.example/" } } }), club_score: { gesamt: 8 } });
    expect(eintrittKurz(nurMax)).toBe("bis 20 €");
  });

  it("Eintritt", () => {
    expect(eintrittKurz(SALON)).toBe("10 €–15 €");
    expect(eintrittStufe(SALON)).toBe("bis10");
    expect(eintrittKurz(SCHLAGER)).toBe("Eintritt frei");
    expect(eintrittStufe(SCHLAGER)).toBe("frei");
  });
});

describe("Filter", () => {
  const alle = [SALON, SCHLAGER];

  it("liest und schreibt URL-Parameter", () => {
    const f = clubFilterLesen({ genre: "techno,unsinn", art: "club", eintritt: "bis10", sort: "neu" });
    expect(f).toEqual({ arten: ["club"], genres: ["techno"], stadtteile: [], eintritt: "bis10", sort: "neu" });
    expect(clubFilterHref("/guides/clubs", f, { sort: "empfohlen" })).toBe("/guides/clubs?art=club&genre=techno&eintritt=bis10");
    expect(clubHatParameter({})).toBe(false);
    expect(clubHatParameter({ genre: "techno" })).toBe(true);
  });

  it("Genres ODER-verknüpft, Eintritt „bis 10 €“ schließt Freies ein", () => {
    expect(clubsFiltern(alle, { ...CLUB_STANDARD, genres: ["techno", "schlager"] }).length).toBe(2);
    expect(clubsFiltern(alle, { ...CLUB_STANDARD, genres: ["house"] }).map((o) => o.name)).toEqual(["Salon"]);
    expect(clubsFiltern(alle, { ...CLUB_STANDARD, eintritt: "bis10" }).length).toBe(2);
    expect(clubsFiltern(alle, { ...CLUB_STANDARD, eintritt: "frei" }).map((o) => o.name)).toEqual(["Schlager Cafe"]);
    expect(clubsFiltern(alle, { ...CLUB_STANDARD, arten: ["partylocation"] }).map((o) => o.name)).toEqual(["Schlager Cafe"]);
  });

  it("Empfohlen sortiert nach Club-Score", () => {
    expect(clubsSortieren([SCHLAGER, SALON], "empfohlen").map((o) => o.name)).toEqual(["Salon", "Schlager Cafe"]);
  });
});
