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
    ];
    return { heute: HEUTE, jetzt: `${HEUTE}T10:00:00Z`, events: alle, alle, quelle: "supabase", fehler: null };
  },
}));
vi.mock("@/lib/orte", () => ({ orteLaden: async () => [] }));
vi.mock("@/components/ort-karten", () => ({ ortPfad: () => "/guides/x" }));

describe("Sitemap", () => {
  it("enthält kommende und laufende Events, aber keine abgelaufenen", async () => {
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls.some((u) => u.endsWith("/heute-2026-11-05"))).toBe(true);
    expect(urls.some((u) => u.endsWith("/ausstellung-2026-10-01"))).toBe(true);
    expect(urls.some((u) => u.endsWith("/gestern-2026-11-04"))).toBe(false);
    expect(urls.some((u) => u.endsWith("/vorbei-2026-10-01"))).toBe(false);
  });
});
