// robots.txt: Filter-Adressen gesperrt, Inhaltsseiten und Bilder frei (Search Console 19.11.2026)
import { describe, expect, it } from "vitest";
import { ROBOTS_GESPERRT as GESPERRT } from "@/lib/seo";

/** Vereinfachte Google-Regel: Präfix-Vergleich, „*“ steht für beliebige Zeichen */
function gesperrt(pfad: string): boolean {
  const maskiert = (t: string) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return GESPERRT.some((r) => new RegExp("^" + r.split("*").map(maskiert).join(".*")).test(pfad));
}

describe("robots.txt", () => {
  it("sperrt Filter-Adressen", () => {
    for (const p of [
      "/?datum=2026-11-20",
      "/entdecken?thema=Halloween&datum=wochenende&preis=kostenlos",
      "/entdecken?kategorie=musik",
      "/wochenende?tag=sa",
      "/stadtteile?datum=heute",
      "/guides/clubs?genre=techno",
      "/guides/weihnachtsmaerkte?tag=2026-12-24",
      "/guides/restaurants-cafes?typ=alle",
      "/api/konto",
    ]) expect(gesperrt(p), p).toBe(true);
  });
  it("lässt Inhaltsseiten und Bilder frei", () => {
    for (const p of [
      "/",
      "/entdecken",
      "/wochenende",
      "/stadtteile",
      "/guides",
      "/guides/clubs",
      "/guides/clubs/ampere-flingern",
      "/guides/weihnachtsmaerkte/advent-am-konvent-neuss",
      "/guides/weihnachtsmaerkte.webp",
      "/event/musik/jazz-am-abend-2026-11-20",
      "/reihe/comedy-mix",
      "/kategorie/musik",
      "/stadtteil/altstadt",
      "/ort-foto/ampere-flingern?v=3",
      "/icon.svg?icon.2l_5iupkzl7eo.svg",
      "/bild/event/11111111-1111-1111-1111-111111111111",
    ]) expect(gesperrt(p), p).toBe(false);
  });
});
