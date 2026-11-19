// „Gerade neu“ auf der Startseite: jedes Event nur einmal (Auftraggeber 19.11.2026)
import { describe, expect, it } from "vitest";
import { jeEventEinmal } from "@/lib/ableitungen";
import { ev } from "./hilfen";

describe("jeEventEinmal", () => {
  it("mehrere Termine desselben Titels am selben Ort zählen einmal, der erste bleibt", () => {
    const a = ev({ id: "a", titel: "Rennbahn-Weihnacht", ort: "Wetthalle Neuss", datum: "2026-12-05" });
    const b = ev({ id: "b", titel: "Rennbahn-Weihnacht", ort: "Wetthalle Neuss", datum: "2026-12-12" });
    const c = ev({ id: "c", titel: "rennbahn weihnacht!", ort: "Wetthalle  Neuss", datum: "2026-12-19" });
    const d = ev({ id: "d", titel: "Further Nikolausmarkt", ort: "St. Josef", datum: "2026-12-03" });
    expect(jeEventEinmal([a, b, d, c]).map((e) => e.id)).toEqual(["a", "d"]);
  });
  it("gleicher Titel an anderem Ort bleibt; gleiche Reihe zählt einmal, auch mit anderem Titel", () => {
    const x = ev({ id: "x", titel: "Weihnachtsmarkt", ort: "Altstadt" });
    const y = ev({ id: "y", titel: "Weihnachtsmarkt", ort: "Kaiserswerth" });
    const r1 = ev({ id: "r1", titel: "Comedy Mix #1", ort: "zakk", reihe: { slug: "comedy-mix", titel: "Comedy Mix" } });
    const r2 = ev({ id: "r2", titel: "Comedy Mix #2", ort: "zakk", reihe: { slug: "comedy-mix", titel: "Comedy Mix" } });
    expect(jeEventEinmal([x, y, r1, r2]).map((e) => e.id)).toEqual(["x", "y", "r1"]);
  });
});
