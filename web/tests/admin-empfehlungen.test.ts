// Tests zu Stufe 1e (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.5): gemeinsame Rechnung mit der Startseite,
// „Warum“ gleich breite(), Flaggen-Update wie im alten Dashboard.
import { describe, expect, it } from "vitest";
import { beliebtAuswahl, breite, filtern, startPlaetze, stufeErklaeren, stufenKontext, tippGilt, wochenendProgramm } from "@/lib/ableitungen";
import { flaggenUpdate } from "@/lib/admin/empfehlungen";
import { plusTage } from "@/lib/datum";
import { startseitenAuswahl } from "@/lib/startseite";
import type { DddEvent, EventPool } from "@/lib/typen";
import { ev } from "./hilfen";

const HEUTE = "2026-11-23"; // Montag
const BILD = "https://x/b.jpg";

function pool(events: DddEvent[]): EventPool {
  return { heute: HEUTE, jetzt: `${HEUTE}T10:00:00Z`, events, alle: events, quelle: "supabase", fehler: null };
}

const EVENTS: DddEvent[] = [
  ev({ id: "a", titel: "Sinfoniekonzert", ort: "Tonhalle", kategorie: "musik", datum: "2026-11-28", uhrzeit: "20:00", bild_url: BILD }),
  ev({ id: "b", titel: "Weihnachtsmarkt vegan", ort: "Jugendkirche", kategorie: "food", datum: "2026-11-28", uhrzeit: "12:00", bild_url: BILD, tipp_des_tages: true }),
  ev({ id: "c", titel: "Jam Session", ort: "Bar X", kategorie: "musik", datum: "2026-11-28", uhrzeit: "21:00", bild_url: BILD }),
  ev({ id: "d", titel: "Lesung", ort: "Zentralbibliothek", kategorie: "kultur", datum: "2026-11-28", uhrzeit: "19:00" }),
  ev({ id: "e", titel: "Ausstellung Farbräume", ort: "Kunstpalast", kategorie: "kultur", datum: "2026-11-01", datum_bis: "2026-12-20", bild_url: BILD }),
  ev({ id: "f", titel: "Abgesagtes Konzert", ort: "zakk", kategorie: "musik", datum: "2026-11-28", abgesagt: true, bild_url: BILD }),
  ev({ id: "g", titel: "Party", ort: "Club Y", kategorie: "nightlife", datum: "2026-11-29", uhrzeit: "23:00", bild_url: BILD, nicht_empfehlen: true }),
  ev({ id: "h", titel: "Flohmarkt", ort: "Messe", kategorie: "food", datum: "2026-11-27", uhrzeit: "10:00", bild_url: BILD }),
];

describe("startseitenAuswahl = bisherige Rechnung der Startseite", () => {
  for (const datum of ["2026-11-28", undefined, "wochenende"]) {
    it(`gleiche vier Blöcke für ?datum=${datum ?? "(leer)"}`, () => {
      const vergangene: DddEvent[] = [];
      const a = startseitenAuswahl(pool(EVENTS), vergangene, datum);

      // Bisherige Rechnung aus web/app/page.tsx (vor Stufe 1e), Schritt für Schritt
      const p = { ...pool(EVENTS), events: EVENTS.filter((e) => !e.abgesagt) };
      const z = a.z;
      const imZeitraum = filtern(p.events, { von: z.von, bis: z.bis });
      const woche = filtern(p.events, { von: z.von, bis: plusTage(z.von, 6) });
      const fokusTag = z.von === z.bis ? z.von : null;
      const stufen = stufenKontext(p.events, HEUTE);
      const { tipp, picks } = startPlaetze(filtern(p.events, { von: z.von, bis: z.bis, mitLanglaeufern: true }), stufen, fokusTag);
      const schon = new Set([tipp, ...picks].filter((e): e is DddEvent => !!e).map((e) => e.id));

      expect(a.tipp?.id).toBe(tipp?.id);
      expect(a.picks.map((e) => e.id)).toEqual(picks.map((e) => e.id));
      expect(a.vonRedaktion).toBe(!!tipp && tippGilt(tipp, fokusTag));
      expect(a.beliebt.map((e) => e.id)).toEqual(beliebtAuswahl(imZeitraum, woche, stufen, fokusTag, 5, schon).map((e) => e.id));
      expect(a.wochenende.map((w) => w.events.map((e) => e.id))).toEqual(wochenendProgramm(p, vergangene).map((w) => w.events.map((e) => e.id)));
    });
  }

  it("Redaktions-Tipp am 28.11. steht auf Platz 1", () => {
    const a = startseitenAuswahl(pool(EVENTS), [], "2026-11-28");
    expect(a.tipp?.id).toBe("b");
    expect(a.vonRedaktion).toBe(true);
  });
});

describe("stufeErklaeren", () => {
  it("ergibt für jedes Event dieselbe Stufe wie breite()", () => {
    const k = stufenKontext(EVENTS, HEUTE);
    for (const e of EVENTS) expect(stufeErklaeren(e, k).stufe).toBe(breite(e, k));
  });

  it("nennt Gründe", () => {
    const k = stufenKontext(EVENTS, HEUTE);
    expect(stufeErklaeren(EVENTS[0], k).gruende[0]).toMatch(/Zugpferd-Ort/);
    expect(stufeErklaeren(EVENTS[2], k).gruende[0]).toMatch(/Szene/);
    expect(stufeErklaeren(EVENTS[6], k).gruende).toEqual(["Redaktion: nicht empfehlen"]);
  });
});

describe("Flaggen setzen", () => {
  const jetzt = new Date("2026-11-23T10:00:00Z");
  it("Highlight und Top mit Zeitpunkt, beim Ausschalten geleert", () => {
    expect(flaggenUpdate("highlight", true, jetzt)).toEqual({ highlight_der_woche: true, highlight_gesetzt_am: "2026-11-23T10:00:00.000Z" });
    expect(flaggenUpdate("top", false, jetzt)).toEqual({ top_event_des_monats: false, top_gesetzt_am: null });
    expect(flaggenUpdate("tipp", true, jetzt)).toEqual({ tipp_des_tages: true });
    expect(flaggenUpdate("nicht_empfehlen", true, jetzt)).toEqual({ nicht_empfehlen: true });
  });
});
