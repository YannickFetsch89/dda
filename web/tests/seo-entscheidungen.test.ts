import { describe, expect, it } from "vitest";
import { eventSlugAusPfad, seoAktionFuer, tabelleAus, zielErlaubt } from "@/lib/seo-entscheidungen";

describe("SEO-Entscheidungen (301/410 für lange abgelaufene Events)", () => {
  const tabelle = tabelleAus([
    { slug: "jazz-2025-01-10", aktion: "weiterleiten", ziel: "/reihe/jazz-am-abend" },
    { slug: "alt-2025-02-01", aktion: "gone", ziel: null },
    { slug: "bleibt-2025-03-01", aktion: "behalten", ziel: null },
    { slug: "start-2025-04-01", aktion: "weiterleiten", ziel: "/" },
    { slug: "fremd-2025-05-01", aktion: "weiterleiten", ziel: "//evil.example" },
  ]);

  it("liest den Slug aus dem Eventpfad", () => {
    expect(eventSlugAusPfad("/event/musik/jazz-2025-01-10")).toBe("jazz-2025-01-10");
    expect(eventSlugAusPfad("/event/musik/k%C3%B6ln-2025")).toBe("köln-2025");
    expect(eventSlugAusPfad("/entdecken")).toBeNull();
    expect(eventSlugAusPfad("/event/musik/%E0%A4%A")).toBeNull();
  });

  it("301 und 410 nur für ausdrücklich entschiedene Events", () => {
    expect(seoAktionFuer("/event/musik/jazz-2025-01-10", tabelle)).toEqual({ aktion: "weiterleiten", ziel: "/reihe/jazz-am-abend" });
    expect(seoAktionFuer("/event/kultur/alt-2025-02-01", tabelle)).toEqual({ aktion: "gone" });
    expect(seoAktionFuer("/event/kultur/bleibt-2025-03-01", tabelle)).toBeNull();
    expect(seoAktionFuer("/event/kultur/unbekannt-2025-03-01", tabelle)).toBeNull();
  });

  it("nie auf die Startseite oder fremde Domains weiterleiten", () => {
    expect(zielErlaubt("/")).toBe(false);
    expect(zielErlaubt("//evil.example")).toBe(false);
    expect(zielErlaubt("/\\evil.example")).toBe(false);
    expect(zielErlaubt("/entdecken?kategorie=musik")).toBe(true);
    expect(seoAktionFuer("/event/x/start-2025-04-01", tabelle)).toBeNull();
    expect(seoAktionFuer("/event/x/fremd-2025-05-01", tabelle)).toBeNull();
  });
});
