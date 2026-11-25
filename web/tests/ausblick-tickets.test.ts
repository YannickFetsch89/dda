// Ausblick, Ticket-Button und Ortswebsite (Plan docs/plan-quellen-ausbau-2026-11-23.md, 6.1, 5.5.3, 4.4, Schritt W2)
import { describe, expect, it } from "vitest";
import { type AusblickEintrag, ausblickAuswahl, ausblickBox, ausblickBuendeln, ausblickKategorien, termineHinweis } from "@/lib/ausblick";
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

  it("nur große Events: Grundstufe 3, keine Stammformate (Eingrenzung 25.11.2026)", () => {
    const liste = ausblickAuswahl([
      ev({ id: "tonhalle" }),
      ev({ id: "buecherei", ort: "Stadtbücherei Bilk", titel: "Onleihe, Pressreader & Co." }),
      ev({ id: "open-mic", ort: "Comedy Club Düsseldorf", titel: "Open Mic" }),
      ev({ id: "yoga", titel: "Yoga im Foyer" }),
      ev({ id: "heimspiel", kategorie: "sport", ort: "PSD Bank Dome", titel: "Düsseldorfer EG - Kölner Haie", ort_id: "ort-dome" }),
    ], orte);
    expect(liste.map((e) => e.id).sort()).toEqual(["heimspiel", "tonhalle"]);
  });

  it("Kategorien nach Häufigkeit", () => {
    const k = ausblickKategorien(ausblickBuendeln([
      ev({ id: "a", kategorie: "kultur", titel: "A" }), ev({ id: "b", kategorie: "musik", titel: "B" }), ev({ id: "c", kategorie: "musik", titel: "C" }),
    ]));
    expect(k).toEqual([{ slug: "musik", anzahl: 2 }, { slug: "kultur", anzahl: 1 }]);
  });
});

describe("Ausblick bündeln und Startseiten-Box", () => {
  it("gleicher Titel am gleichen Ort wird ein Eintrag mit erstem Termin und Zahl", () => {
    const b = ausblickBuendeln([
      ev({ id: "t3", titel: "La traviata", datum: "2027-03-14", ort_id: "ort-oper" }),
      ev({ id: "t1", titel: "La traviata", datum: "2027-01-29", ort_id: "ort-oper" }),
      ev({ id: "t2", titel: "LA TRAVIATA!", datum: "2027-02-05", ort_id: "ort-oper" }),
      ev({ id: "anders", titel: "La traviata", datum: "2027-02-01", ort_id: "ort-tonhalle" }),
    ]);
    expect(b.map((x) => [x.e.id, x.termine, x.bis])).toEqual([["t1", 3, "2027-03-14"], ["anders", 1, "2027-02-01"]]);
    expect(termineHinweis(b[0])).toBe("3 Termine bis 14.03.");
    expect(termineHinweis(b[1])).toBeNull();
    expect(termineHinweis({ e: ev({ datum: "2027-02-01" }), termine: 2, bis: "2027-02-01" })).toBe("2 Termine an diesem Tag");
  });

  it("Box: höchstens ein Eintrag je Haus, über die Monate verteilt, nach Datum", () => {
    const x = (id: string, datum: string, ort_id: string, bild = true): AusblickEintrag =>
      ({ e: ev({ id, datum, ort_id, titel: id, bild_url: bild ? "https://bild/x.jpg" : null }), termine: 1, bis: datum });
    const box = ausblickBox([
      x("jan-dome-1", "2027-01-26", "dome"), x("jan-dome-2", "2027-01-27", "dome"), x("jan-oper", "2027-01-28", "oper", false),
      x("feb-dome", "2027-02-02", "dome"), x("feb-capitol", "2027-02-03", "capitol"),
      x("mar-tonhalle", "2027-03-01", "tonhalle"), x("apr-tonhalle", "2027-04-01", "tonhalle"),
    ], 4);
    expect(box.map((y) => y.e.id)).toEqual(["jan-dome-1", "jan-oper", "feb-capitol", "mar-tonhalle"]);
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
