// SEO-/GEO-Plan Nov. 2026, Phase A1: Pfadprüfung (echte Statuscodes), Seiten-Metadaten, Tagesprüfung, Sitemap-Daten
import { describe, expect, it } from "vitest";
import { juengstes } from "@/app/sitemap";
import { istGueltigerTag } from "@/lib/datum";
import { eventPfad } from "@/lib/pfade";
import { ortEntscheidung, routeVon, tagGueltig } from "@/lib/pfad-pruefung";
import { hatParameter, seitenMetadaten } from "@/lib/seo";

describe("routeVon", () => {
  it("erkennt die geprüften Routen", () => {
    expect(routeVon("/event/c9f25a3d-1506-4c59-80ae-5c536fde5ad3")).toEqual({ typ: "event-uuid", id: "c9f25a3d-1506-4c59-80ae-5c536fde5ad3" });
    expect(routeVon("/event/musik/konzert-2026-11-20")).toEqual({ typ: "event", kategorie: "musik", slug: "konzert-2026-11-20" });
    expect(routeVon("/tag/2026-11-12")).toEqual({ typ: "tag", datum: "2026-11-12" });
    expect(routeVon("/reihe/comedy-zakk")).toEqual({ typ: "reihe", slug: "comedy-zakk" });
    expect(routeVon("/guides/clubs/salon-des-amateurs-altstadt")).toEqual({ typ: "ort", hub: "clubs", slug: "salon-des-amateurs-altstadt" });
    expect(routeVon("/guides/spielplaetze/x")).toEqual({ typ: "ort", hub: "spielplaetze", slug: "x" });
  });

  it("Einzelsegment unter /event/ ohne UUID ist ungültig (echte 404 statt Soft-404 der alten Seite)", () => {
    expect(routeVon("/event/kein-uuid")).toEqual({ typ: "ungueltig" });
  });

  it("lässt alles andere durch", () => {
    expect(routeVon("/guides/clubs")).toBeNull();
    expect(routeVon("/guides/spielplaetze")).toBeNull();
    expect(routeVon("/heute")).toBeNull();
    expect(routeVon("/event/musik/%E0%A4%A")).toBeNull(); // kaputtes Prozentzeichen
  });
});

describe("Tage", () => {
  it("nur echte Kalendertage", () => {
    for (const ok of ["2026-11-12", "2028-02-29"]) {
      expect(tagGueltig(ok)).toBe(true);
      expect(istGueltigerTag(ok)).toBe(true);
    }
    for (const falsch of ["2099-99-99", "2026-02-30", "2027-02-29", "2026-13-01", "20261112", "x"]) {
      expect(tagGueltig(falsch)).toBe(false);
      expect(istGueltigerTag(falsch)).toBe(false);
    }
    // Seite und Proxy mit derselben Grenze (2020–2100) – sonst rendert die Seite, der Proxy sagt 404
    expect(tagGueltig("2019-06-01")).toBe(false);
    expect(istGueltigerTag("2019-06-01")).toBe(false);
  });
});

describe("ortEntscheidung", () => {
  const ort = (mehr: Record<string, unknown>) => ({
    typ: "restaurant", aktiv: true, qualitaets_score: 8, club: null, club_score: null, club_freigegeben: null, auch_club: null, ...mehr,
  });
  const club = { passt: true, genres: [] };

  it("Restaurant/Kneipe: aktiv, passender Typ, Score ≥ 7", () => {
    expect(ortEntscheidung("restaurants-cafes", "x", ort({}))).toEqual({ art: "weiter" });
    expect(ortEntscheidung("restaurants-cafes", "x", ort({ qualitaets_score: 6 }))).toEqual({ art: "fehlt" });
    expect(ortEntscheidung("kneipen-bars", "x", ort({}))).toEqual({ art: "fehlt" }); // falscher Hub
    expect(ortEntscheidung("restaurants-cafes", "x", null)).toEqual({ art: "fehlt" });
  });

  it("Clubs: alle mit passendem Profil sichtbar; umgetypte Orte → 308 auf die Club-Seite", () => {
    const sichtbar = ort({ typ: "club", club, club_score: { gesamt: 8 }, club_freigegeben: "2026-11-11" });
    expect(ortEntscheidung("clubs", "zakk-flingern", sichtbar)).toEqual({ art: "weiter" });
    // Ohne Freigabe: Stufe B/C, aber sichtbar
    expect(ortEntscheidung("clubs", "x", { ...sichtbar, club_freigegeben: null, club_score: { gesamt: 3 } })).toEqual({ art: "weiter" });
    expect(ortEntscheidung("clubs", "x", { ...sichtbar, club: { passt: false } })).toEqual({ art: "fehlt" });
    expect(ortEntscheidung("clubs", "x", { ...sichtbar, aktiv: false })).toEqual({ art: "fehlt" });
    expect(ortEntscheidung("restaurants-cafes", "zakk-flingern", sichtbar)).toEqual({ art: "umleiten", ziel: "/guides/clubs/zakk-flingern" });
  });

  it("Spielplätze (Plan 5.5): sichtbar ohne Score; nie freigeschaltet → 404; abgeschaltet → 308 auf die Stadtteilseite", () => {
    const sp = (mehr: Record<string, unknown>) =>
      ort({ typ: "spielplatz", qualitaets_score: null, aktiv: true, stadtteil: "Bilk", freigeschaltet_am: "2026-11-13", ...mehr });
    expect(ortEntscheidung("spielplaetze", "x", sp({}))).toEqual({ art: "weiter" });
    // Wieder freigeschaltet: aktiv, gleicher Slug → 200
    expect(ortEntscheidung("spielplaetze", "x", sp({ freigeschaltet_am: "2026-11-01" }))).toEqual({ art: "weiter" });
    expect(ortEntscheidung("spielplaetze", "x", sp({ aktiv: false, freigeschaltet_am: null }))).toEqual({ art: "fehlt" });
    expect(ortEntscheidung("spielplaetze", "x", null)).toEqual({ art: "fehlt" });
    expect(ortEntscheidung("spielplaetze", "x", sp({ typ: "restaurant", qualitaets_score: 9 }))).toEqual({ art: "fehlt" });
    expect(ortEntscheidung("spielplaetze", "x", sp({ aktiv: false }))).toEqual({ art: "umleiten", ziel: "/guides/spielplaetze/stadtteil/bilk" });
    // Gespeichertes „Hafen“ → Anzeige-Slug „medienhafen“
    expect(ortEntscheidung("spielplaetze", "x", sp({ aktiv: false, stadtteil: "Hafen" }))).toEqual({ art: "umleiten", ziel: "/guides/spielplaetze/stadtteil/medienhafen" });
    // Ohne gültigen Stadtteil → Hub
    expect(ortEntscheidung("spielplaetze", "x", sp({ aktiv: false, stadtteil: null }))).toEqual({ art: "umleiten", ziel: "/guides/spielplaetze" });
    expect(ortEntscheidung("spielplaetze", "x", sp({ aktiv: false, stadtteil: "Atlantis" }))).toEqual({ art: "umleiten", ziel: "/guides/spielplaetze" });
    // Spielplatz-URL unter einem anderen Hub bleibt 404
    expect(ortEntscheidung("restaurants-cafes", "x", sp({}))).toEqual({ art: "fehlt" });
  });

  it("Aus dem Club-Hub genommen (Konvex) → Bar-Seite; nur als Club sichtbare Bar → Club-Seite", () => {
    const konvex = ort({ typ: "kneipe", qualitaets_score: 7, club, club_score: { gesamt: 7 }, auch_club: null, kein_club: "Bar" });
    expect(ortEntscheidung("clubs", "konvex-flingern", konvex)).toEqual({ art: "umleiten", ziel: "/guides/kneipen-bars/konvex-flingern" });
    expect(ortEntscheidung("kneipen-bars", "konvex-flingern", konvex)).toEqual({ art: "weiter" });
    // Giselle Bar: Bar-Score 4, aber Club (auch_club) → Bar-URL leitet auf die Club-Seite
    const giselle = ort({ typ: "kneipe", qualitaets_score: 4, club, club_score: { gesamt: 7 }, auch_club: true });
    expect(ortEntscheidung("kneipen-bars", "giselle", giselle)).toEqual({ art: "umleiten", ziel: "/guides/clubs/giselle" });
    expect(ortEntscheidung("clubs", "giselle", giselle)).toEqual({ art: "weiter" });
    // Sichtbares Restaurant mit Club-Ansicht: falscher Hub bleibt 404 (eine URL je Ort)
    const schlager = ort({ typ: "restaurant", qualitaets_score: 7, club, club_score: { gesamt: 6 }, auch_club: true });
    expect(ortEntscheidung("kneipen-bars", "schlager", schlager)).toEqual({ art: "fehlt" });
    // Club-URL eines normalen Restaurants → auf seine Seite
    expect(ortEntscheidung("clubs", "pizza", ort({}))).toEqual({ art: "umleiten", ziel: "/guides/restaurants-cafes/pizza" });
  });
});

describe("Seiten-Metadaten", () => {
  it("indexierbar: Canonical auf sich selbst, Open Graph mit Layout-Feldern", () => {
    const m = seitenMetadaten({ pfad: "/heute", titel: "Heute in Düsseldorf", beschreibung: "B" });
    expect(m.alternates?.canonical).toBe("/heute");
    expect(m.robots).toBeUndefined();
    expect(m.openGraph).toMatchObject({ url: "/heute", siteName: "dies.das.düsseldorf", locale: "de_DE", type: "website" });
  });

  it("Varianten mit Parametern: noindex, follow und kein fremdes Canonical", () => {
    const m = seitenMetadaten({ pfad: "/entdecken", noindex: true });
    expect(m.robots).toEqual({ index: false, follow: true });
    expect(m.alternates).toBeUndefined();
    expect(hatParameter({ kategorie: "musik" })).toBe(true);
    expect(hatParameter({ kategorie: undefined, q: "" })).toBe(false);
  });

  it("Bild → große Twitter-Karte; ohne eigenes Bild das Standardbild", () => {
    expect(seitenMetadaten({ pfad: "/x", bild: "/bild.jpg" }).twitter).toMatchObject({ card: "summary_large_image", images: ["/bild.jpg"] });
    const ohne = seitenMetadaten({ pfad: "/x" });
    expect((ohne.openGraph as { images: { url: string }[] }).images[0].url).toBe("/og-standard.png");
    expect(ohne.twitter).toMatchObject({ card: "summary_large_image", images: ["/og-standard.png"] });
  });
});

describe("Pfade und Sitemap-Daten", () => {
  it("eventPfad kanonisch", () => {
    expect(eventPfad({ id: "u", kategorie: "musik", slug: "a b" })).toBe("/event/musik/a%20b");
    expect(eventPfad({ id: "u", kategorie: "musik", slug: null })).toBe("/event/u");
  });

  it("lastModified = jüngstes Inhaltsdatum, sonst keins", () => {
    expect(juengstes([{ erstellt_am: "2026-11-01T10:00:00Z" }, { erstellt_am: "2026-11-09T13:55:40Z" }, { erstellt_am: null }])?.toISOString())
      .toBe("2026-11-09T13:55:40.000Z");
    expect(juengstes([{ erstellt_am: null }])).toBeUndefined();
  });
});

describe("Kategorie wie auf der Seite", () => {
  it("DB „family“ → Pfad „familie“ (sonst zwei URLs je Familien-Event)", async () => {
    const { kategorieAusDb } = await import("@/lib/kategorien");
    expect(eventPfad({ id: "u", kategorie: kategorieAusDb("family"), slug: "kinderfest" })).toBe("/event/familie/kinderfest");
  });
});
