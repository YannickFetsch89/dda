// SEO-/GEO-Plan Nov. 2026, Phase A2: Sätze aus echten Daten, Stand-Zeile, ItemList/BreadcrumbList, EventSeries
import { describe, expect, it } from "vitest";
import { eventListeJsonLd, MAX_LISTE, reiheJsonLd } from "@/lib/listen-json-ld";
import { aufzaehlung, datumText, standText, tagesSatz, topKategorien, wochenendSatz } from "@/lib/tagestext";
import type { DddEvent, KategorieSlug } from "@/lib/typen";

const ev = (i: number, kategorie: KategorieSlug = "musik") =>
  ({ id: `e${i}`, titel: `Event ${i}`, kategorie, slug: `event-${i}`, datum: "2026-11-12" }) as DddEvent;

describe("Tages-Satz", () => {
  it("nennt die Zahl der Zeilen und die häufigsten Kategorien", () => {
    const events = [ev(1, "musik"), ev(2, "musik"), ev(3, "kultur"), ev(4, "nightlife"), ev(5, "kultur"), ev(6, "musik")];
    expect(tagesSatz("2026-11-11", events)).toBe("Am 11. November 2026 stehen in Düsseldorf 6 Events an, die meisten aus Musik, Kultur und Nightlife.");
  });

  it("Grenzfälle ohne holprige Sätze", () => {
    expect(tagesSatz("2026-11-11", [])).toBe("Für den 11. November 2026 sind in Düsseldorf noch keine Events eingetragen.");
    expect(tagesSatz("2026-11-11", [ev(1)])).toBe("Am 11. November 2026 steht in Düsseldorf ein Event an.");
    expect(tagesSatz("2026-11-11", [ev(1), ev(2)])).toBe("Am 11. November 2026 stehen in Düsseldorf 2 Events an.");
  });

  it("Hilfen", () => {
    expect(datumText("2027-01-05")).toBe("5. Januar 2027");
    expect(aufzaehlung(["Musik"])).toBe("Musik");
    expect(aufzaehlung(["Musik", "Kultur"])).toBe("Musik und Kultur");
    expect(topKategorien([ev(1, "kultur"), ev(2, "musik")])).toEqual(["Kultur", "Musik"]); // Gleichstand: alphabetisch
    expect(topKategorien([ev(1, "family" as KategorieSlug)])).toEqual(["Sonstiges"]); // unbekannt → Sonstiges
  });
});

describe("Wochenend-Satz", () => {
  it("Zeitraum, Zahl, Kategorien und Tipps", () => {
    const events = [ev(1, "musik"), ev(2, "musik"), ev(3, "kultur")];
    expect(wochenendSatz("2026-11-13", "2026-11-15", events, 9)).toBe(
      "Vom 13. bis 15. November 2026 stehen in Düsseldorf 3 Events an, die meisten aus Musik und Kultur; neun davon empfehlen wir.",
    );
    // Monatswechsel
    expect(wochenendSatz("2026-11-27", "2026-11-29", [], 0)).toBe("Vom 27. bis 29. November 2026 sind in Düsseldorf noch keine Events eingetragen.");
    expect(wochenendSatz("2027-01-29", "2027-01-31", events, 3)).toContain("drei davon empfehlen wir");
    expect(wochenendSatz("2026-12-31", "2027-01-02", events, 0)).toMatch(/^Vom 31\. Dezember bis 2\. Januar 2027/);
    // Sonntag: nur noch ein Tag
    expect(wochenendSatz("2026-11-15", "2026-11-15", events, 3)).toBe(
      "Am 15. November 2026 stehen in Düsseldorf 3 Events an, die meisten aus Musik und Kultur; drei davon empfehlen wir.",
    );
  });
});

describe("Stand-Zeile", () => {
  it("Berliner Zeit, auch über die Zeitumstellung", () => {
    expect(standText("2026-11-11T13:05:00Z")).toBe("Stand: 11.11.2026, 14:05 Uhr");
    expect(standText("2026-07-01T04:30:00Z")).toBe("Stand: 01.07.2026, 06:30 Uhr");
    expect(standText(null)).toBeNull();
    expect(standText("kaputt")).toBeNull();
  });
});

describe("Listen-JSON-LD", () => {
  it("ItemList verweist auf die kanonischen Event-URLs, gedeckelt", () => {
    const events = Array.from({ length: 40 }, (_, i) => ev(i));
    const [krumen, liste] = eventListeJsonLd("https://diesdas.events", "Heute", [{ name: "Start", pfad: "/" }, { name: "Heute", pfad: "/heute" }], events);
    expect(krumen["@type"]).toBe("BreadcrumbList");
    expect(liste["@type"]).toBe("ItemList");
    const eintraege = liste.itemListElement as { url: string; name: string }[];
    expect(eintraege).toHaveLength(MAX_LISTE);
    expect(eintraege[0]).toMatchObject({ url: "https://diesdas.events/event/musik/event-0", name: "Event 0" });
  });

  it("ohne Einträge keine leere ItemList", () => {
    expect(eventListeJsonLd("https://x", "Heute", [{ name: "Start", pfad: "/" }], [])).toHaveLength(1);
  });

  it("EventSeries mit Verweisen per @id", () => {
    const d = reiheJsonLd("https://diesdas.events", { slug: "comedy-zakk", titel: "Comedy im zakk", ort: "zakk" }, [ev(1)]);
    expect(d).toMatchObject({ "@type": "EventSeries", url: "https://diesdas.events/reihe/comedy-zakk" });
    expect(d.subEvent).toEqual([{ "@id": "https://diesdas.events/event/musik/event-1", url: "https://diesdas.events/event/musik/event-1", name: "Event 1" }]);
    expect(reiheJsonLd("https://x", { slug: "a", titel: "A", ort: "o" }, []).subEvent).toBeUndefined();
  });
});
