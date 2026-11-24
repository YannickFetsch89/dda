// Ausblick, Ticket-Button und Ortswebsite (Plan docs/plan-quellen-ausbau-2026-11-23.md, 6.1, 5.5.3, 4.4, Schritt W2)
import { describe, expect, it } from "vitest";
import { ausblickAuswahl, ausblickKategorien } from "@/lib/ausblick";
import { eventJsonLd } from "@/lib/json-ld";
import { ortWebsite, quellenLesen, ticketZiel } from "@/lib/ticket-button";
import type { DddEvent } from "@/lib/typen";

function ev(teil: Partial<DddEvent>): DddEvent {
  return {
    id: teil.id ?? "x", titel: "Konzert", datum: "2027-03-01", datum_bis: null, uhrzeit: "20:00", ort: "Tonhalle",
    adresse: null, kategorie: "musik", beschreibung: null, preis: null, quelle_name: "Tonhalle Düsseldorf",
    quelle_url: "https://www.tonhalle.de/e/1", bild_url: null, stadtteil: null, erstellt_am: null, tipp_des_tages: false,
    highlight_der_woche: false, top_event_des_monats: false, slug: "konzert", abgesagt: false, reihe: null,
    uhrzeiten: null, ort_id: "ort-tonhalle", ...teil,
  } as DddEvent;
}

describe("Ausblick-Auswahl", () => {
  const orte = new Set(["ort-tonhalle", "ort-dome"]);

  it("nur Rang 1–2, nur Orte mit Ortsseite, keine Absagen, nach Datum", () => {
    const liste = ausblickAuswahl([
      ev({ id: "spaet", datum: "2027-05-01" }),
      ev({ id: "tm", datum: "2027-04-01", quelle_name: "Ticketmaster", ort_id: "ort-dome" }),
      ev({ id: "rg", quelle_name: "Rausgegangen", quelle_url: "https://rausgegangen.de/e" }),
      ev({ id: "portal", quelle_name: "Kulturportal Düsseldorf" }),
      ev({ id: "ohne-ort", ort_id: null }),
      ev({ id: "fremder-ort", ort_id: "ort-kneipe" }),
      ev({ id: "abgesagt", abgesagt: true }),
      ev({ id: "frueh", datum: "2027-02-01" }),
    ], orte);
    expect(liste.map((e) => e.id)).toEqual(["frueh", "tm", "spaet"]);
  });

  it("Kategorien nach Häufigkeit", () => {
    const k = ausblickKategorien([ev({ kategorie: "kultur" }), ev({ kategorie: "musik" }), ev({ kategorie: "musik" })]);
    expect(k).toEqual([{ slug: "musik", anzahl: 2 }, { slug: "kultur", anzahl: 1 }]);
  });
});

describe("Ticket-Button (5.5.3)", () => {
  it("Ticket-Link des Hauses zuerst", () => {
    expect(ticketZiel(ev({ ticket_url: "https://www.eventim.de/e/1" }), [{ name: "Ticketmaster", url: "https://www.ticketmaster.de/e/9", rang: 2 }]))
      .toBe("https://www.eventim.de/e/1");
  });

  it("sonst eine Ticketverkaufs-Quelle aus der Liste", () => {
    const quellen = [
      { name: "Tonhalle Düsseldorf", url: "https://www.tonhalle.de/e/1", rang: 1 },
      { name: "Rausgegangen", url: "https://rausgegangen.de/e", rang: 5 },
      { name: "Ticketmaster", url: "https://www.ticketmaster.de/e/9", rang: 2 },
    ];
    expect(ticketZiel(ev({}), quellen)).toBe("https://www.ticketmaster.de/e/9");
  });

  it("kein zweiter Button, wenn der Haupt-Button schon Tickets verkauft oder nichts da ist", () => {
    expect(ticketZiel(ev({ quelle_name: "Ticketmaster", quelle_url: "https://www.ticketmaster.de/e/9", ticket_url: "https://www.eventim.de/e/1" }))).toBeNull();
    expect(ticketZiel(ev({ ticket_url: "https://www.tonhalle.de/e/1" }), [{ name: "Ticketmaster", url: "https://www.ticketmaster.de/e/9", rang: 2 }])).toBeNull();
    expect(ticketZiel(ev({}), [])).toBeNull();
    expect(ticketZiel(ev({ ticket_url: "javascript:alert(1)" }))).toBeNull();
  });

  it("Quellenliste robust lesen", () => {
    expect(quellenLesen([{ name: "A", url: "https://a", rang: 1 }, null, { url: "x" }, "kaputt"])).toEqual([{ name: "A", url: "https://a", rang: 1 }]);
    expect(quellenLesen(null)).toEqual([]);
  });
});

describe("Website von <Ort> (4.4)", () => {
  const rg = ev({ quelle_name: "Rausgegangen", quelle_url: "https://rausgegangen.de/e" });

  it("nur bei Rausgegangen-Events mit Ortswebsite", () => {
    expect(ortWebsite(rg, { name: "Pretty Vacant", webseite: "https://prettyvacant.de" })).toEqual({ name: "Pretty Vacant", url: "https://prettyvacant.de/" });
    expect(ortWebsite(ev({}), { name: "Tonhalle", webseite: "https://www.tonhalle.de" })).toBeNull();
    expect(ortWebsite(rg, { name: "X", webseite: null })).toBeNull();
    expect(ortWebsite(rg, null)).toBeNull();
  });
});

describe("JSON-LD-Angebot (5.5.5)", () => {
  it("nimmt den Ticket-Link des Hauses als echte URL, sonst die Hauptquelle", () => {
    const mit = eventJsonLd(ev({ ticket_url: "https://www.eventim.de/e/1" }), "https://diesdas.events/e", "https://diesdas.events");
    expect((mit.offers as { url: string }).url).toBe("https://www.eventim.de/e/1");
    const ohne = eventJsonLd(ev({}), "https://diesdas.events/e", "https://diesdas.events");
    expect((ohne.offers as { url: string }).url).toBe("https://www.tonhalle.de/e/1");
  });
});
