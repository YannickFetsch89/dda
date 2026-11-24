// Tests zu Stufe 5b (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.10): SEO-Aufräumen wie dashboard/seo_aufraeumen.py
import { describe, expect, it } from "vitest";
import { abgelaufenFilter, csvFeld, entscheidungenBauen, webKategorie, zielFuer, type SeoEvent } from "@/lib/admin/seo";

const e = (x: Partial<SeoEvent>): SeoEvent => ({ id: "e1", slug: "s", titel: "T", datum: "2024-01-01", datum_bis: null, ort: "zakk", kategorie: "family", reihe: null, ...x });

describe("SEO-Aufräumen", () => {
  it("Ziele wie im Dashboard, nie die Startseite", () => {
    expect(zielFuer(e({ reihe: [{ slug: "jazz-montag" }] }), "reihe")).toBe("/reihe/jazz-montag");
    expect(zielFuer(e({}), "reihe")).toBeNull();
    expect(zielFuer(e({ ort: "Café Ölmühle" }), "ort")).toBe("/entdecken?q=Caf%C3%A9%20%C3%96lm%C3%BChle&datum=alle");
    expect(zielFuer(e({}), "kategorie")).toBe("/entdecken?kategorie=familie&datum=alle");
    expect(webKategorie(null)).toBe("sonstiges");
  });
  it("Entscheidungen bauen, Events ohne Ziel übersprungen", () => {
    const r = entscheidungenBauen([e({ id: "a" }), e({ id: "b", reihe: { slug: "r" } })], "reihe", "admin", "2026-11-24T00:00:00Z");
    expect(r.zeilen).toEqual([{ event_id: "b", slug: "s", aktion: "weiterleiten", ziel: "/reihe/r", entschieden_am: "2026-11-24T00:00:00Z", entschieden_von: "admin" }]);
    expect(r.uebersprungen.map((x) => x.id)).toEqual(["a"]);
    expect(entscheidungenBauen([e({})], "gone", null, "t").zeilen[0]).toMatchObject({ aktion: "gone", ziel: null });
  });
  it("Filter und CSV", () => {
    expect(abgelaufenFilter("2026-11-24")).toBe("datum_bis.lt.2025-11-24,and(datum_bis.is.null,datum.lt.2025-11-24)");
    expect(csvFeld("=HYPERLINK()")).toBe("'=HYPERLINK()");
    expect(csvFeld('a;b"c')).toBe('"a;b""c"');
  });
});
