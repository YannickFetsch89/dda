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
}));
vi.mock("@/lib/orte", () => ({
  orteLaden: async () => [{ id: "r", slug: "r", typ: "restaurant", aktualisiert_am: null, extras: {} }],
  clubOrteLaden: async () => [],
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

describe("Sitemap", () => {
  it("Spielplätze: Hub und nur indexierbare Detailseiten", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls).toContain("https://diesdas.events/guides/spielplaetze");
    expect(urls).toContain("https://diesdas.events/guides/spielplaetze/gut-bilk");
    expect(urls.some((u) => u.includes("duenn-bilk"))).toBe(false);
  });

  it("enthält kommende und laufende Events, aber keine abgelaufenen", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls.some((u) => u.endsWith("/heute-2026-11-05"))).toBe(true);
    expect(urls.some((u) => u.endsWith("/ausstellung-2026-10-01"))).toBe(true);
    expect(urls.some((u) => u.endsWith("/gestern-2026-11-04"))).toBe(false);
    expect(urls.some((u) => u.endsWith("/vorbei-2026-10-01"))).toBe(false);
  });

  it("enthält Reihenseiten mit kommenden Terminen, aber keine ohne", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls).toContain("https://diesdas.events/reihe/comedy-zakk");
    expect(urls).not.toContain("https://diesdas.events/reihe/lesung-alt");
    expect(urls.filter((u) => u.endsWith("/reihe/comedy-zakk"))).toHaveLength(1);
  });
});
