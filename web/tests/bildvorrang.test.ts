import { describe, expect, it } from "vitest";
import { beliebtheit, highlights, nachBeliebtheit, vielfaeltig } from "@/lib/ableitungen";
import type { EventPool } from "@/lib/typen";
import { ev } from "./hilfen";

// Auftraggeber 12.11.2026: Events ohne eigenes Bild (nur Symbolbild) nur, wenn es sonst nichts gibt
describe("Events ohne eigenes Bild sind nachrangig", () => {
  const mitBild = ev({ id: "a", titel: "Mit Bild", bild_url: "https://x/bild.jpg", datum: "2026-11-20" });
  const tippOhneBild = ev({ id: "b", titel: "Tipp ohne Bild", bild_url: null, tipp_des_tages: true, top_event_des_monats: true, datum: "2026-11-20" });
  const ohneBild = ev({ id: "c", titel: "Ohne Bild", bild_url: null, datum: "2026-11-20" });

  it("Beliebtheit: jedes Event mit Bild vor jedem ohne Bild – auch mit allen Redaktions-Markierungen", () => {
    const vollOhneBild = ev({
      id: "e",
      titel: "Alles gesetzt, kein Bild",
      bild_url: null,
      tipp_des_tages: true,
      top_event_des_monats: true,
      highlight_der_woche: true,
      beschreibung: "x".repeat(90),
      uhrzeit: "20:00",
      stadtteil: "Altstadt",
      datum: "2026-11-20",
    });
    expect(beliebtheit(mitBild)).toBeGreaterThan(beliebtheit(ohneBild));
    expect(beliebtheit(vollOhneBild)).toBeGreaterThan(beliebtheit(mitBild));
    expect([ohneBild, tippOhneBild, vollOhneBild, mitBild].sort(nachBeliebtheit)[0].id).toBe("a");
  });

  it("Auswahl greift auf Events ohne Bild nur zurück, wenn es sonst nichts gibt", () => {
    expect(vielfaeltig([ohneBild, mitBild], 1).map((e) => e.id)).toEqual(["a"]);
    expect(vielfaeltig([ohneBild], 1).map((e) => e.id)).toEqual(["c"]);
  });

  it("Top-Event des Monats ohne Bild verliert gegen ein Event mit Bild", () => {
    const vollOhneBild = ev({
      id: "e",
      bild_url: null,
      tipp_des_tages: true,
      top_event_des_monats: true,
      highlight_der_woche: true,
      beschreibung: "x".repeat(90),
      uhrzeit: "20:00",
      stadtteil: "Altstadt",
      datum: "2026-11-20",
    });
    const pool = {
      events: [vollOhneBild, mitBild, ev({ id: "d", titel: "Noch eins", bild_url: "https://x/2.jpg", datum: "2026-11-21" })],
      heute: "2026-11-19",
    } as unknown as EventPool;
    const { highlight, top } = highlights(pool);
    expect(highlight?.bild_url).toBeTruthy();
    expect(top?.bild_url).toBeTruthy();
    expect(top?.id).not.toBe(highlight?.id);
  });

  it("ohne jedes Bild bleibt die Redaktions-Markierung der Fallback und wirft nicht", () => {
    const pool = { events: [tippOhneBild], heute: "2026-11-19" } as unknown as EventPool;
    const { highlight, top } = highlights(pool);
    expect(highlight?.id).toBe("b");
    expect(top).toBeNull();
  });
});

describe("Vielfalt nur unter Events mit Bild", () => {
  it("eine zweite Kategorie ohne Bild verdrängt kein weiteres Event mit Bild", () => {
    const a = ev({ id: "a", kategorie: "musik", bild_url: "https://x/1.jpg" });
    const b = ev({ id: "b", kategorie: "musik", bild_url: "https://x/2.jpg" });
    const c = ev({ id: "c", kategorie: "kultur", bild_url: null });
    expect(vielfaeltig([a, b, c], 2).map((e) => e.id).sort()).toEqual(["a", "b"]);
    expect(vielfaeltig([a, c], 2).map((e) => e.id)).toEqual(["a", "c"]);
  });
});
