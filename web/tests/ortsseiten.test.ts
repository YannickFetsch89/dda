// Ortsseiten /orte (Plan docs/plan-locations-2026-11-18.md, Pflicht-Tests Abschnitt 4: Proxy, Verknüpfungen, Seiten)
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { config as proxyConfig } from "@/proxy";
import { guideZiel, routeVon, spielstaetteEntscheidung, type OrtKopf } from "@/lib/pfad-pruefung";
import { artInfo, filterLesen, indexierbar, orteFiltern, stadtAusPlz } from "@/lib/spielstaetten";
import { indexierbareOrte, sichtbarerPfad, type Spielstaette } from "@/lib/spielstaetten-daten";
import { spielstaetteJsonLd } from "@/lib/spielstaetten-json-ld";
import type { DddOrt } from "@/lib/typen";

const kopf = (x: Partial<OrtKopf>): OrtKopf => ({
  typ: "spielstaette", aktiv: true, qualitaets_score: null, club: null, club_score: null, club_freigegeben: null, auch_club: null, ...x,
});
const ort = (x: Partial<Spielstaette> & { id: string }): Spielstaette => ({
  name: x.id, slug: x.id, typ: "spielstaette", untertitel: null, beschreibung: null, highlight: null, adresse: null, stadtteil: null,
  latitude: null, longitude: null, bild_url: null, bild_attribution: null, tags: [], preis_niveau: null, oeffnungszeiten: null,
  webseite: null, telefon: null, instagram: null, google_place_id: null, google_rating: null, google_bewertungen_anzahl: null,
  qualitaets_score: null, extras: {}, sortierung: 0, erstellt_am: null, aktualisiert_am: null, parentId: null, ...x,
});

describe("Proxy /orte", () => {
  it("Matcher und Routen", () => {
    expect(proxyConfig.matcher).toContain("/orte/:path+");
    expect(routeVon("/orte/tonhalle")).toEqual({ typ: "spielstaette", slug: "tonhalle" });
    expect(routeVon("/orte")).toBeNull(); // Übersicht: immer 200
    expect(routeVon("/orte/a/b")).toEqual({ typ: "ungueltig" });
  });

  it("aktive Spielstätte 200, unbekannt 404", () => {
    expect(spielstaetteEntscheidung("tonhalle", kopf({}), undefined, null)).toEqual({ art: "weiter" });
    expect(spielstaetteEntscheidung("gibts-nicht", null, undefined, null)).toEqual({ art: "fehlt" });
  });

  it("Guide-Slug: 308 auf die kanonische Guide-URL, unsichtbar 404", () => {
    expect(spielstaetteEntscheidung("zakk-flingern", kopf({ typ: "club", club: { passt: true } }), undefined, null).art).not.toBe("weiter");
    // Kneipe mit Score ≥ 7 → Kneipen-Hub
    expect(spielstaetteEntscheidung("pitcher", kopf({ typ: "kneipe", qualitaets_score: 8 }), undefined, null))
      .toEqual({ art: "umleiten", ziel: "/guides/kneipen-bars/pitcher" });
    // Unsichtbare Guide-Zeile (Score < 7, kein Club) → 404
    expect(spielstaetteEntscheidung("starbucks", kopf({ typ: "cafe", qualitaets_score: 4 }), undefined, null)).toEqual({ art: "fehlt" });
    // Spielplatz und Weihnachtsmarkt über den eigenen Pfad
    expect(guideZiel(kopf({ typ: "spielplatz" }), "x")).toBe("/guides/spielplaetze/x");
    expect(guideZiel(kopf({ typ: "weihnachtsmarkt" }), "m")).toBe("/guides/weihnachtsmaerkte/m");
    // Ausflug/Wochenend-Trip: kein Ziel (kein 308 auf /guides/restaurants-cafes)
    expect(spielstaetteEntscheidung("a", kopf({ typ: "ausflug" }), undefined, null)).toEqual({ art: "fehlt" });
    expect(spielstaetteEntscheidung("w", kopf({ typ: "wochenendtipp" }), undefined, null)).toEqual({ art: "fehlt" });
  });

  it("Ort mit Bar- und Club-Seite: Hauptseite, wenn sichtbar, sonst Club-Seite (Plan 4, Pflicht-Tests)", () => {
    const club = { passt: true, unterart: "club", genres: [{ wert: "Techno", anteil: "haupt" }] };
    const bar = (score: number) => kopf({ typ: "kneipe", qualitaets_score: score, auch_club: true, club, club_score: { gesamt: 7 }, club_freigegeben: "2026-11-11" });
    expect(spielstaetteEntscheidung("giselle", bar(8), undefined, null)).toEqual({ art: "umleiten", ziel: "/guides/kneipen-bars/giselle" });
    expect(spielstaetteEntscheidung("giselle", bar(4), undefined, null)).toEqual({ art: "umleiten", ziel: "/guides/clubs/giselle" });
    // Weiterleitung auf einen auch_club: vor dem Score-Wechsel Club-Seite, danach Hauptseite
    expect(spielstaetteEntscheidung("alt", null, { ziel_ort_id: "id" }, { ...bar(4), slug: "giselle" })).toEqual({ art: "umleiten", ziel: "/guides/clubs/giselle" });
    expect(spielstaetteEntscheidung("alt", null, { ziel_ort_id: "id" }, { ...bar(8), slug: "giselle" })).toEqual({ art: "umleiten", ziel: "/guides/kneipen-bars/giselle" });
  });

  it("zakk: Guide-Haus 308, Kurzname und Saal ohne Zeile 404", () => {
    // Die Zeile „zakk-flingern-tanzraum“ gibt es nicht → der Proxy findet weder Zeile noch Weiterleitung
    expect(spielstaetteEntscheidung("zakk", null, undefined, null)).toEqual({ art: "fehlt" });
    expect(spielstaetteEntscheidung("zakk-flingern-tanzraum", null, undefined, null)).toEqual({ art: "fehlt" });
    // Weiterleitung auf eine umbenannte Spielstätte: eine Stufe, neuer Slug
    expect(spielstaetteEntscheidung("alt", null, { ziel_ort_id: "id" }, { ...kopf({}), slug: "neu" })).toEqual({ art: "umleiten", ziel: "/orte/neu" });
    // Inaktives Ziel (anon sieht es nicht) → /orte
    expect(spielstaetteEntscheidung("alt", null, { ziel_ort_id: "id" }, { ...kopf({ aktiv: false, typ: "kneipe", qualitaets_score: 9 }), slug: "x" }))
      .toEqual({ art: "umleiten", ziel: "/orte" });
  });

  it("zusammengelegter Markt: ein einziger 308 auf den verbliebenen", () => {
    expect(spielstaetteEntscheidung("schadow-markt-stadtmitte", null, undefined, null))
      .toEqual({ art: "umleiten", ziel: "/guides/weihnachtsmaerkte/maerchen-markt-stadtmitte" });
  });

  it("Weiterleitung über ziel_ort_id: Ziel zur Laufzeit, unsichtbar → /orte, nie 404", () => {
    const ziel = { ...kopf({}), slug: "bambi" };
    expect(spielstaetteEntscheidung("bambi-filmstudio", null, { ziel_ort_id: "id" }, ziel)).toEqual({ art: "umleiten", ziel: "/orte/bambi" });
    expect(spielstaetteEntscheidung("tiefgarage-psd-bank-dome", null, { ziel_ort_id: "id" }, null)).toEqual({ art: "umleiten", ziel: "/orte" });
    expect(spielstaetteEntscheidung("gertrudenhof", null, { ziel_ort_id: null }, null)).toEqual({ art: "umleiten", ziel: "/orte" });
    // Guide-Ziel unsichtbar geworden → /orte statt 308 auf eine 404
    const weg = { ...kopf({ typ: "cafe", qualitaets_score: 3 }), slug: "altes-cafe" };
    expect(spielstaetteEntscheidung("x", null, { ziel_ort_id: "id" }, weg)).toEqual({ art: "umleiten", ziel: "/orte" });
  });

  it("kein rewrite im Proxy", () => {
    expect(readFileSync(join(__dirname, "..", "proxy.ts"), "utf8")).not.toMatch(/NextResponse\.rewrite/);
  });
});

describe("Indexierungsregel (gemeinsam mit pipeline/indexnow.py)", () => {
  it("dieselben Fälle wie tests/fixtures/ort_indexierbar.json", () => {
    const faelle = JSON.parse(readFileSync(join(__dirname, "..", "..", "tests", "fixtures", "ort_indexierbar.json"), "utf8")) as
      { adresseBestaetigt: boolean; textFreigegeben: boolean; kommende: number; erwartet: boolean }[];
    for (const f of faelle) expect(indexierbar(f)).toBe(f.erwartet);
  });

  it("Säle erben die bestätigte Adresse, Haus zählt die Events der Kinder", () => {
    const haus = ort({ id: "haus", extras: { spielstaette: { adresse_bestaetigt: { datum: "x" } } } });
    const saal = ort({ id: "saal", parentId: "haus" });
    const zakkSaal = ort({ id: "zakk-halle", parentId: "zakk" });
    const leer = ort({ id: "leer", extras: { spielstaette: { adresse_bestaetigt: { datum: "x" } } } });
    const anzahl = new Map([["saal", 2], ["zakk-halle", 1]]);
    const ok = indexierbareOrte([haus, saal, zakkSaal, leer], anzahl, new Map([["haus", true], ["zakk", true]])).map((o) => o.id);
    expect(ok).toEqual(["haus", "saal", "zakk-halle"]); // „leer“ ohne kommende Events: noindex
  });
});

describe("Seiten", () => {
  it("Stadt nur aus der PLZ", () => {
    expect(stadtAusPlz("Markt 1, 41460 Neuss")).toBe("Neuss");
    expect(stadtAusPlz("Steinstr. 1, Düsseldorf")).toBeNull();
  });

  it("Filter /orte: Stadt Neuss ohne Stadtteil, Art über den Slug", () => {
    const neuss = ort({ id: "n", adresse: "Markt 1, 41460 Neuss", extras: { spielstaette: { art: "Kino" } } });
    const dus = ort({ id: "d", adresse: "Bilker Allee 1, 40217 Düsseldorf", stadtteil: "Unterbilk", extras: { spielstaette: { art: "Museum/Ausstellung" } } });
    expect(orteFiltern([neuss, dus], filterLesen({ stadt: "Neuss" })).map((o) => o.id)).toEqual(["n"]);
    expect(orteFiltern([neuss, dus], filterLesen({ art: "museum" })).map((o) => o.id)).toEqual(["d"]);
    expect(orteFiltern([neuss, dus], filterLesen({ stadtteil: "Unterbilk" })).map((o) => o.id)).toEqual(["d"]);
  });

  it("neue Arten haben ein Symbol", () => {
    for (const a of ["Laden", "Freizeit/Erlebnis", "Ausflugsziel/Sehenswürdigkeit", "Öffentliches Gebäude", "Gastronomie/Eventlocation"]) {
      expect(artInfo(a).wert).toBe(a);
    }
  });

  it("Ortsseite nutzt weder eventPoolLaden noch ortBildUrl (keine Beispieldaten, keine Google-Fotos)", () => {
    for (const datei of [join("app", "orte", "[slug]", "page.tsx"), join("app", "orte", "page.tsx"), join("lib", "spielstaetten-daten.ts")]) {
      // Nur Code prüfen, nicht die Kommentare („NICHT eventPoolLaden()“)
      const text = readFileSync(join(__dirname, "..", datei), "utf8").replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
      expect(text).not.toMatch(/eventPoolLaden\(/);
      expect(text).not.toMatch(/ortBildUrl\(/);
    }
  });

  it("JSON-LD: Saal eines Guide-Hauses verweist auf die kanonische Guide-URL, Stadt aus der PLZ, ohne Adresse keins", () => {
    const saal = ort({ id: "zakk-flingern-halle", name: "zakk – Halle", adresse: "Fichtenstraße 40, 40233 Düsseldorf", stadtteil: "Flingern" });
    const ld = spielstaetteJsonLd(saal, null, "https://diesdas.events", "/orte/zakk-flingern-halle",
      { name: "zakk", pfad: "/guides/clubs/zakk-flingern" }, [], true)!;
    expect(ld.containedInPlace).toEqual({ "@type": "Place", name: "zakk", url: "https://diesdas.events/guides/clubs/zakk-flingern" });
    expect((ld.address as { addressLocality: string }).addressLocality).toBe("Düsseldorf"); // nie der Stadtteil
    expect(spielstaetteJsonLd(saal, null, "https://diesdas.events", "/orte/x", null, [], false)).toBeNull();
  });

  it("Eventseite: kanonischer Ortslink nach den Hub-Regeln", () => {
    const basis = ort({ id: "x", slug: "x" }) as DddOrt;
    expect(sichtbarerPfad({ ...basis, typ: "spielstaette", slug: "tonhalle" })).toBe("/orte/tonhalle");
    expect(sichtbarerPfad({ ...basis, typ: "kneipe", qualitaets_score: 8, slug: "bar" })).toBe("/guides/kneipen-bars/bar");
    expect(sichtbarerPfad({ ...basis, typ: "cafe", qualitaets_score: 3, slug: "c" })).toBeNull();
    expect(sichtbarerPfad({ ...basis, typ: "ausflug", slug: "a" })).toBeNull();
  });
});

describe("Cursor-Komplettprüfung 20.11.", () => {
  it("Übersicht: Säle eines Guide-Hauses stehen unter dem Haus (Link auf die Guide-Seite), unsichtbares Haus → Saal selbst", async () => {
    const { uebersichtEintraege } = await import("@/lib/spielstaetten-daten");
    const halle = ort({ id: "halle", name: "zakk – Halle", parentId: "zakk" });
    const club = ort({ id: "zakk", name: "zakk", slug: "zakk-flingern", typ: "club" }) as DddOrt;
    const tonhalle = ort({ id: "tonhalle", name: "Tonhalle" });
    const rotunde = ort({ id: "rotunde", name: "Tonhalle – Rotunde", parentId: "tonhalle" });
    const verwaist = ort({ id: "saal-x", name: "Saal X", parentId: "unsichtbar" });
    // Club sichtbar → Eintrag „zakk“ mit Guide-Link, Halle darunter
    const sichtbar = { ...club, extras: { club: { passt: true }, club_score: { gesamt: 8 }, club_freigegeben: "2026-11-11" } };
    const e = uebersichtEintraege([halle, tonhalle, rotunde, verwaist], [sichtbar]);
    expect(e.haeuser.map((o) => o.id)).toEqual(["saal-x", "tonhalle", "zakk"]);
    expect(e.pfad.get("zakk")).toBe("/guides/clubs/zakk-flingern");
    expect(e.kinder.get("zakk")?.map((o) => o.id)).toEqual(["halle"]);
    expect(e.kinder.get("tonhalle")?.map((o) => o.id)).toEqual(["rotunde"]);
    // Guide-Haus nicht sichtbar oder nicht ladbar → die Halle steht selbst in der Liste
    expect(uebersichtEintraege([halle], []).haeuser.map((o) => o.id)).toEqual(["halle"]);
  });

  it("Saal-Filter: Saalseite nur eigene Events, „Haus allgemein“ nur Haus-ID", async () => {
    const { saalEvents } = await import("@/lib/spielstaetten");
    const ev = (id: string, ortId: string) => ({ id, ort_id: ortId }) as unknown as import("@/lib/typen").DddEvent;
    const programm = [ev("1", "haus"), ev("2", "saal-a"), ev("3", "saal-b")];
    expect(saalEvents({ id: "saal-a", parentId: "haus" }, programm, null).map((e) => e.id)).toEqual(["2"]);
    expect(saalEvents({ id: "haus", parentId: null }, programm, "haus").map((e) => e.id)).toEqual(["1"]);
    expect(saalEvents({ id: "haus", parentId: null }, programm, "saal-b").map((e) => e.id)).toEqual(["3"]);
    expect(saalEvents({ id: "haus", parentId: null }, programm, null)).toHaveLength(3);
  });

  it("Proxy: scheitert die Zielabfrage einer Weiterleitung (Timeout), gilt „weiter“ – kein 308 auf /orte", async () => {
    const { pfadPruefen, speicherLeeren } = await import("@/lib/pfad-pruefung");
    speicherLeeren();
    const alt = { url: process.env.SUPABASE_URL, key: process.env.SUPABASE_KEY };
    process.env.SUPABASE_URL = "https://test.supabase.co";
    process.env.SUPABASE_KEY = "test";
    vi.stubGlobal("fetch", async (url: string) => {
      if (url.includes("/orte?") && url.includes("slug=eq.")) return new Response("[]", { status: 200 }); // keine eigene Zeile
      if (url.includes("/ort_weiterleitungen?")) return new Response('[{"ziel_ort_id":"z1"}]', { status: 200 });
      throw new DOMException("Zeitüberschreitung", "TimeoutError"); // Zielabfrage
    });
    try {
      expect(await pfadPruefen("/orte/alter-name")).toEqual({ art: "weiter" });
    } finally {
      vi.unstubAllGlobals();
      for (const [k, v] of [["SUPABASE_URL", alt.url], ["SUPABASE_KEY", alt.key]] as const) {
        if (v === undefined) delete process.env[k]; else process.env[k] = v;
      }
      speicherLeeren();
    }
  });
});

describe("Texte der Ortsseiten (Plan 3.14, Schritt 4)", () => {
  it("JSON-LD: description nur mit freigegebenem Text und ohne „**“", async () => {
    const { spielstaetteJsonLd: ld } = await import("@/lib/spielstaetten-json-ld");
    const o = ort({ id: "tonhalle", adresse: "Ehrenhof 1, 40479 Düsseldorf" });
    const mit = ld(o, null, "https://diesdas.events", "/orte/tonhalle", null, [], true, "Die **Tonhalle** am **Ehrenhof**.\n\nZweiter Absatz.")!;
    expect(mit.description).toBe("Die Tonhalle am Ehrenhof.\n\nZweiter Absatz.");
    expect(ld(o, null, "https://diesdas.events", "/orte/tonhalle", null, [], true)!.description).toBeUndefined();
  });

  it("Ortsseite zeigt den Text mit Fettschrift", () => {
    const seite = readFileSync(join(__dirname, "..", "app", "orte", "[slug]", "page.tsx"), "utf8");
    expect(seite).toMatch(/<BeschreibungText text=\{ort\.beschreibung\} fett \/>/);
  });
});
