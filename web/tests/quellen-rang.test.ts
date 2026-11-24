// Rangfolge der Quellen (Plan docs/plan-quellen-ausbau-2026-11-23.md, 4.1): dieselbe Tabelle wie pipeline/quellen_rang.py.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { istAggregator, uhrzeitUebernehmen } from "@/lib/admin/events";
import { RANG_GESPEICHERT, UNBEKANNT_GESPEICHERT, rangGespeichert } from "@/lib/quellen-rang";

const FIXTURE = JSON.parse(readFileSync(join(__dirname, "..", "..", "tests", "fixtures", "quellen_rang.json"), "utf-8")) as {
  unbekannt_gespeichert: number;
  gespeichert: Record<string, number>;
  faelle: { quelle_name: string | null; quelle_url: string | null; rang: number }[];
};

describe("Quellen-Rang", () => {
  it("hat dieselbe Tabelle wie die Pipeline", () => {
    expect(RANG_GESPEICHERT).toEqual(FIXTURE.gespeichert);
    expect(UNBEKANNT_GESPEICHERT).toBe(FIXTURE.unbekannt_gespeichert);
  });

  it("rechnet die gemeinsamen Fälle wie die Pipeline", () => {
    for (const fall of FIXTURE.faelle) {
      expect(rangGespeichert(fall), JSON.stringify(fall)).toBe(fall.rang);
    }
  });

  it("macht ein Haus mit Ticket-Link nicht zur Sammelquelle", () => {
    expect(istAggregator({ quelle_name: "d-live", quelle_url: "https://www.ticketmaster.de/event/x" })).toBe(false);
    expect(istAggregator({ quelle_name: "Ticketmaster", quelle_url: "https://www.ticketmaster.de/event/x" })).toBe(true);
    expect(istAggregator({ quelle_name: "Meetup.com" })).toBe(true);
  });

  it("übernimmt die Uhrzeit des Hauses in Dubletten-Vorschlägen", () => {
    const tm = { uhrzeit: "18:30:00", quelle_name: "Ticketmaster" };
    const haus = { uhrzeit: "19:30:00", quelle_name: "Mitsubishi Electric HALLE" };
    expect(uhrzeitUebernehmen(tm, haus)).toBe(true);
    expect(uhrzeitUebernehmen(haus, tm)).toBe(false);
  });
});
