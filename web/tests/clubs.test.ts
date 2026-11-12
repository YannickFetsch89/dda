import { describe, expect, it } from "vitest";
import {
  CLUB_STANDARD, clubArt, clubBeschreibung, clubFilterHref, clubFilterLesen, clubHatParameter, clubProfil, clubsFiltern,
  clubIndexierbar, clubStufe, clubsSortieren, eigeneClubSeite, eintrittKurz, eintrittStufe, hauptGenres, istSichtbarerClub,
  nachStufen,
} from "@/lib/clubs";
import { naechsteEvents } from "@/lib/clubs-daten";
import { clubsListeJsonLd } from "@/lib/clubs-json-ld";
import type { DddEvent, DddOrt, EventPool } from "@/lib/typen";

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

const SALON = ort("Salon", { club: profil(), club_score: { gesamt: 9, programm: 9 }, club_freigegeben: "2026-11-11" });
const SCHLAGER = ort("Schlager Cafe", {
  auch_club: true, club_unterart: "partylocation", club_beschreibung: "Party-Text",
  club: profil({ unterart: "partylocation", genres: [{ wert: "Schlager", anteil: "haupt" }], eintritt: { min: 0, max: null } }),
  club_score: { gesamt: 7, programm: 6 }, club_freigegeben: "2026-11-11",
}, { typ: "restaurant", beschreibung: "Restaurant-Text", qualitaets_score: 5 });
const SCHWACH = ort("Schwach", { club: profil(), club_score: { gesamt: 6 }, club_freigegeben: "2026-11-11" });
const OHNE_FREIGABE = ort("Vorschlag", { club: profil(), club_score: { gesamt: 9 } });
const PASST_NICHT = ort("Sauna", { club: profil({ passt: false }), club_score: { gesamt: 9 }, club_freigegeben: "2026-11-11" });

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
  it("alle passenden Clubs sichtbar (seit 12.11.2026), gestuft nach A/B/C", () => {
    expect(istSichtbarerClub(SALON)).toBe(true);
    expect(istSichtbarerClub(SCHLAGER)).toBe(true);
    expect(istSichtbarerClub(SCHWACH)).toBe(true);
    expect(istSichtbarerClub(OHNE_FREIGABE)).toBe(true);
    expect(istSichtbarerClub(PASST_NICHT)).toBe(false);
    // Vom Auftraggeber herausgenommen (Konvex → Bars)
    expect(istSichtbarerClub(ort("Bar", { ...SALON.extras, kein_club: "Bar" }))).toBe(false);
    // ohne Club-Score keine Einordnung
    expect(istSichtbarerClub(ort("Neu", { club: profil() }))).toBe(false);
  });

  it("Stufen: A = Freigabe + Score ≥ 7, B = Score ≥ 5, C = übrige", () => {
    expect(clubStufe(SALON)).toBe("a");
    expect(clubStufe(SCHLAGER)).toBe("a");
    // „passt“ der KI und hoher Score reichen nicht für die Top-Empfehlung – erst die Freigabe nach Sichtprüfung
    expect(clubStufe(OHNE_FREIGABE)).toBe("b");
    expect(clubStufe(SCHWACH)).toBe("b");
    const klein = ort("Klein", { club: profil(), club_score: { gesamt: 4 }, club_freigegeben: "2026-11-11" });
    expect(clubStufe(klein)).toBe("c");
    expect(clubIndexierbar(SCHWACH)).toBe(true);
    expect(clubIndexierbar(klein)).toBe(false);
    expect(nachStufen([klein, SCHWACH, SALON]).map((g) => [g.stufe.wert, g.orte.map((o) => o.name)])).toEqual([
      ["a", ["Salon"]], ["b", ["Schwach"]], ["c", ["Klein"]],
    ]);
  });

  it("Club-Seite ist kanonisch, wenn die Haupt-Seite im anderen Hub nicht sichtbar ist", () => {
    expect(eigeneClubSeite(SALON)).toBe(true);
    expect(eigeneClubSeite(SCHLAGER)).toBe(true); // Restaurant-Score 5 → keine Restaurant-Seite
    expect(eigeneClubSeite({ ...SCHLAGER, qualitaets_score: 8 })).toBe(false);
  });

  it("Profil-Links nur exakt, ohne Query", () => {
    const mit = (instagram: string) => clubProfil(ort("X", { club: profil({ instagram }) }))!.instagram;
    expect(mit("https://instagram.com/echterclub")).toBe("https://instagram.com/echterclub");
    expect(mit("https://instagram.com/echterclub?next=https://example.org/")).toBeNull();
    expect(mit("https://instagram.com/echterclub/p/abc")).toBeNull();
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
    expect(f).toEqual({ stufen: [], arten: ["club"], genres: ["techno"], stadtteile: [], eintritt: "bis10", sort: "neu", ansicht: "grid" });
    expect(clubFilterHref("/guides/clubs", f, { sort: "empfohlen" })).toBe("/guides/clubs?art=club&genre=techno&eintritt=bis10");
    expect(clubHatParameter({})).toBe(false);
    expect(clubHatParameter({ genre: "techno" })).toBe(true);
    // Stufen (Reihenfolge fest) und Kartenansicht
    const g = clubFilterLesen({ stufe: "c,a,x", ansicht: "karte" });
    expect(g.stufen).toEqual(["a", "c"]);
    expect(g.ansicht).toBe("karte");
    expect(clubFilterHref("/guides/clubs", g, {})).toBe("/guides/clubs?stufe=a,c&ansicht=karte");
    expect(clubFilterHref("/guides/clubs", g, { ansicht: "grid", stufen: [] })).toBe("/guides/clubs");
    expect(clubHatParameter({ stufe: "a" })).toBe(true);
    expect(clubHatParameter({ ansicht: "karte" })).toBe(true);
    expect(clubsFiltern(alle, { ...CLUB_STANDARD, stufen: ["a"] }).map((o) => o.name).sort()).toEqual(["Salon", "Schlager Cafe"]);
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

describe("Daten und JSON-LD", () => {
  const event = { id: "e1", titel: "Resident Night", datum: "2026-11-20", datum_bis: null, uhrzeit: "23:00", ort: "Salon",
    abgesagt: false } as DddEvent;
  const pool = (quelle: "supabase" | "beispiel") =>
    ({ heute: "2026-11-11", jetzt: "", events: [event], alle: [event], quelle, fehler: null }) as EventPool;

  it("keine Beispiel-Events als „Nächstes Event“", () => {
    expect(naechsteEvents(SALON, pool("supabase")).map((e) => e.id)).toEqual(["e1"]);
    expect(naechsteEvents(SALON, pool("beispiel"))).toEqual([]);
  });

  it("ItemList nutzt die kanonische URL (auch_club → Haupt-URL, wenn die sichtbar ist)", () => {
    const sichtbaresRestaurant = { ...SCHLAGER, qualitaets_score: 8 };
    const [, liste] = clubsListeJsonLd([SALON, sichtbaresRestaurant, SCHLAGER], "https://diesdas.events", "/guides/clubs");
    const urls = (liste.itemListElement as { url: string }[]).map((x) => x.url);
    expect(urls[0]).toBe("https://diesdas.events/guides/clubs/salon");
    expect(urls[1]).toBe("https://diesdas.events/guides/restaurants-cafes/schlager-cafe");
    expect(urls[2]).toBe("https://diesdas.events/guides/clubs/schlager-cafe"); // Restaurant-Seite nicht sichtbar
  });
});
