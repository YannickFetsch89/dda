import { describe, expect, it, vi } from "vitest";
import { ev } from "./hilfen";

const HEUTE = "2026-11-05";

vi.mock("@/lib/daten", () => ({
  eventPoolLaden: async () => {
    const alle = [
      ev({ id: "gestern", datum: "2026-11-04", slug: "gestern-2026-11-04" }),
      ev({ id: "heute", datum: HEUTE, slug: "heute-2026-11-05" }),
      ev({ id: "laufend", datum: "2026-10-01", datum_bis: "2026-12-01", slug: "ausstellung-2026-10-01" }),
      ev({ id: "vorbei", datum: "2026-10-01", datum_bis: "2026-11-01", slug: "vorbei-2026-10-01" }),
      ev({ id: "reihe-kommend", datum: "2026-11-20", slug: "comedy-2026-11-20", reihe: { slug: "comedy-zakk", titel: "Comedy" } }),
      ev({ id: "reihe-vorbei", datum: "2026-11-01", slug: "lesung-2026-11-01", reihe: { slug: "lesung-alt", titel: "Lesung" } }),
    ];
    return { heute: HEUTE, jetzt: `${HEUTE}T10:00:00Z`, events: alle, alle, quelle: "supabase", fehler: null };
  },
  // Fernpool (Plan Quellen-Ausbau 6.1): ein Event hinter Tag 60 und eines, das auch im Nah-Pool steht (keine Doppelung)
  fernPoolLaden: async () => {
    const alle = [
      ev({ id: "fern", datum: "2027-03-14", slug: "konzert-2027-03-14" }),
      ev({ id: "heute", datum: HEUTE, slug: "heute-2026-11-05" }),
    ];
    return { heute: HEUTE, jetzt: `${HEUTE}T10:00:00Z`, events: alle, alle, quelle: "supabase", fehler: null };
  },
}));
vi.mock("@/lib/orte", () => ({
  orteLaden: async () => [{ id: "r", slug: "r", typ: "restaurant", aktualisiert_am: null, extras: {} }],
  clubOrteLaden: async () => [],
  ortBildUrl: () => null,
}));
// Spielplätze: ein indexierbarer und ein dünner Platz (abgeschaltete lädt spielplaetzeLaden gar nicht)
const geraet = { wert: "ja", quelle: "osm", beleg: "x" };
vi.mock("@/lib/spielplaetze-daten", () => ({
  spielplaetzeLaden: async () => [
    { id: "s1", slug: "gut-bilk", typ: "spielplatz", aktualisiert_am: null, extras: { spielplatz: { beschreibung: "x", ausstattung: { rutsche: geraet, schaukel: geraet } } } },
    { id: "s2", slug: "duenn-bilk", typ: "spielplatz", aktualisiert_am: null, extras: { spielplatz: { beschreibung: null } } },
  ],
}));
vi.mock("@/components/ort-karten", () => ({ ortPfad: () => "/guides/x" }));
// Magazin (Schalter an seit Schritt 7): eigene Einträge prüft tests/magazin.test.ts (magazinEintraege); hier leer
vi.mock("@/lib/magazin-daten", () => ({ beitraegeLaden: async () => [], autorenLaden: async () => [], magazinHeute: async () => "2026-11-05" }));
// Ortsseiten (Plan Locations 3.11): ein indexierbares Haus mit Event, eines ohne
// (Die Regel selbst prüft tests/ortsseiten.test.ts; hier nur die Einbindung in die Sitemap.)
vi.mock("@/lib/spielstaetten-daten", () => {
  const haus = (id: string) => ({ id, slug: id, typ: "spielstaette", parentId: null, aktualisiert_am: null, extras: {} });
  return {
    indexierbareOrte: (alle: { id: string }[], anzahl: Map<string, number>) => alle.filter((o) => (anzahl.get(o.id) ?? 0) > 0),
    spielstaettenLaden: async () => ({ orte: [haus("tonhalle"), haus("leer")], fehler: false }),
    kommendeJeOrt: async () => ({ anzahl: new Map([["tonhalle", 3]]), fehler: false }),
    ortZeileLaden: async () => null,
  };
});
// Weihnachtsmärkte: ein indexierbarer (Zeitraum + Wochenzeiten + Beschreibung) und einer ohne Zeiten
const wmSaison = { "2026": { von: "2026-11-19", bis: "2026-12-30", zeiten: [{ tage: ["mo"], von: "11:00", bis: "20:00" }] } };
vi.mock("@/lib/weihnachtsmaerkte-daten", () => ({
  weihnachtsmaerkteLaden: async () => [
    { id: "w1", slug: "altstadt-markt", typ: "weihnachtsmarkt", beschreibung: "x", aktualisiert_am: null, extras: { weihnachtsmarkt: { saisons: wmSaison } } },
    { id: "w2", slug: "ohne-zeiten", typ: "weihnachtsmarkt", beschreibung: "x", aktualisiert_am: null, extras: { weihnachtsmarkt: { saisons: {} } } },
  ],
}));

describe("Sitemap", () => {
  it("Spielplätze: Hub und nur indexierbare Detailseiten", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls).toContain("https://diesdas.events/guides/spielplaetze");
    expect(urls).toContain("https://diesdas.events/guides/spielplaetze/gut-bilk");
    expect(urls.some((u) => u.includes("duenn-bilk"))).toBe(false);
  });

  it("Weihnachtsmärkte: Hub und nur indexierbare Detailseiten", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls).toContain("https://diesdas.events/guides/weihnachtsmaerkte");
    expect(urls).toContain("https://diesdas.events/guides/weihnachtsmaerkte/altstadt-markt");
    expect(urls.some((u) => u.includes("ohne-zeiten"))).toBe(false);
  });

  it("enthält kommende und laufende Events, aber keine abgelaufenen", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls.some((u) => u.endsWith("/heute-2026-11-05"))).toBe(true);
    expect(urls.some((u) => u.endsWith("/ausstellung-2026-10-01"))).toBe(true);
    expect(urls.some((u) => u.endsWith("/gestern-2026-11-04"))).toBe(false);
    expect(urls.some((u) => u.endsWith("/vorbei-2026-10-01"))).toBe(false);
  });

  it("enthält ferne Eventseiten aus dem Fernpool, jede nur einmal (Plan Quellen-Ausbau 6.1)", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls.some((u) => u.endsWith("/konzert-2027-03-14"))).toBe(true);
    expect(urls.filter((u) => u.endsWith("/heute-2026-11-05"))).toHaveLength(1);
  });

  it("enthält Reihenseiten mit kommenden Terminen, aber keine ohne", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls).toContain("https://diesdas.events/reihe/comedy-zakk");
    expect(urls).not.toContain("https://diesdas.events/reihe/lesung-alt");
    expect(urls.filter((u) => u.endsWith("/reihe/comedy-zakk"))).toHaveLength(1);
  });
});

describe("Sitemap: Ortsseiten (Plan Locations 3.11)", () => {
  it("/orte und nur indexierbare Ortsseiten", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls).toContain("https://diesdas.events/orte");
    expect(urls).toContain("https://diesdas.events/orte/tonhalle");
    expect(urls).not.toContain("https://diesdas.events/orte/leer");
  });
});
