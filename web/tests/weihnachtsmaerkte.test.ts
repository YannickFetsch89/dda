// Weihnachtsmarkt-Guide (Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, Abschnitt 7.1): reine Funktionen ohne Netz.
// Öffnungslogik gegen dieselbe Fixture wie scraper/weihnachtsmaerkte/zeiten.py (tests/fixtures/weihnachtsmaerkte_oeffnung.json).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { startboxAktiv } from "@/components/wm-startbox";
import { GUIDE_TEXTE } from "@/lib/guide-texte";
import { ortEntscheidung, pfadPruefen, routeVon, weihnachtsmarktEntscheidung } from "@/lib/pfad-pruefung";
import type { DddOrt } from "@/lib/typen";
import {
  aktuelleSaison, badges, faqWerte, feiertag, heroZahlen, hubJahr, istIndexierbar, jetztText, listenReihenfolge, oeffnungAm, oeffnungText,
  saisonFuer, sonderTage, sonderZelle, sortieren, topFuenf, totensonntag, wm, type Saisons,
} from "@/lib/weihnachtsmaerkte";
import { weihnachtsmarktJsonLd } from "@/lib/weihnachtsmaerkte-json-ld";
import { weihnachtsmarktKartenOrte } from "@/lib/weihnachtsmaerkte-karte";

const FIXTURE = JSON.parse(readFileSync(join(__dirname, "..", "..", "tests", "fixtures", "weihnachtsmaerkte_oeffnung.json"), "utf8")) as {
  eintraege: Record<string, Saisons>;
  faelle: { eintrag: string; datum: string; zustand: string; von?: string; bis?: string; grund?: string }[];
  totensonntag: Record<string, string>;
};

let n = 0;
function markt(extra: Record<string, unknown>, mehr: Partial<DddOrt> = {}): DddOrt {
  n += 1;
  return {
    id: `id-${n}`, name: `Markt ${n}`, slug: `markt-${n}`, typ: "weihnachtsmarkt", untertitel: null, beschreibung: "Beschreibung.",
    highlight: null, adresse: null, stadtteil: "Altstadt", latitude: 51.226, longitude: 6.772, bild_url: null, bild_attribution: null,
    tags: [], preis_niveau: null, oeffnungszeiten: null, webseite: null, telefon: null, instagram: null, google_place_id: null,
    google_rating: null, google_bewertungen_anzahl: null, qualitaets_score: null,
    extras: { weihnachtsmarkt: { schluessel: `m${n}`, merkmale: {}, saisons: { "2026": FIXTURE.eintraege.innenstadt["2026"] }, ...extra } },
    sortierung: 0, erstellt_am: null, aktualisiert_am: null, ...mehr,
  };
}

describe("Öffnungslogik (gemeinsame Fixture mit Python)", () => {
  it("alle Fixture-Fälle", () => {
    for (const f of FIXTURE.faelle) {
      const o = oeffnungAm(FIXTURE.eintraege[f.eintrag], f.datum);
      expect(o.zustand, `${f.eintrag} ${f.datum}`).toBe(f.zustand);
      if (f.von) expect(o.von, `${f.eintrag} ${f.datum}`).toBe(f.von);
      if (f.bis) expect(o.bis, `${f.eintrag} ${f.datum}`).toBe(f.bis);
      if (f.grund) expect(o.grund, `${f.eintrag} ${f.datum}`).toBe(f.grund);
    }
  });

  it("Totensonntag berechnet (2026: 22.11., 2027: 21.11.)", () => {
    for (const [jahr, datum] of Object.entries(FIXTURE.totensonntag)) expect(totensonntag(Number(jahr))).toBe(datum);
    expect(feiertag("2027-11-21")).toBe("Totensonntag");
    expect(feiertag("2027-11-22")).toBeNull();
  });

  it("Saison über von/bis, nicht über das Kalenderjahr; leerer Schlüssel 2027 ändert nichts", () => {
    expect(saisonFuer(FIXTURE.eintraege["koe-on-ice"], "2027-01-05")).toEqual({ schluessel: "2026", lage: "in" });
    const s = aktuelleSaison(FIXTURE.eintraege["leer-2027"]);
    expect(s?.jahr).toBe("2026");
  });

  it("Texte: vor/nach Saison, unbekannt am Feiertag, Uhrzeit", () => {
    expect(oeffnungText(oeffnungAm(FIXTURE.eintraege["winter-village"], "2026-11-19"))).toBe("Öffnet am Fr, 20.11.");
    expect(oeffnungText(oeffnungAm(FIXTURE.eintraege.nordstrasse, "2026-11-22"))).toBe("Totensonntag: nicht veröffentlicht");
    expect(oeffnungText(oeffnungAm(FIXTURE.eintraege.innenstadt, "2026-12-31"))).toBe("Saison 2026 beendet");
    // Jahr aus dem Saisonschlüssel, nicht aus dem Enddatum (Kö on Ice endet am 10.01.2027, Cursor-Check Stufe 1a)
    expect(oeffnungText(oeffnungAm(FIXTURE.eintraege["koe-on-ice"], "2027-01-11"))).toBe("Saison 2026 beendet");
    const offen = oeffnungAm(FIXTURE.eintraege.innenstadt, "2026-11-21"); // Sa 11–21
    expect(jetztText(offen, 10 * 60 + 59)).toBe("Öffnet heute um 11 Uhr");
    expect(jetztText(offen, 11 * 60)).toBe("Jetzt geöffnet bis 21 Uhr");
    expect(jetztText(offen, 21 * 60 + 1)).toBe("Heute schon geschlossen");
  });

  it("Sonderzeiten-Tabelle: sechs Tage inkl. Silvester/Neujahr, „–“ außerhalb, „nicht veröffentlicht“ ohne Beleg", () => {
    expect(sonderTage(2026).map((t) => t.name)).toEqual(["Totensonntag", "Heiligabend", "1. Weihnachtstag", "2. Weihnachtstag", "Silvester", "Neujahr"]);
    expect(sonderZelle(FIXTURE.eintraege.innenstadt, "2026-12-31")).toBe("–");
    expect(sonderZelle(FIXTURE.eintraege.innenstadt, "2026-11-22")).toBe("geschlossen");
    expect(sonderZelle(FIXTURE.eintraege.nordstrasse, "2026-11-22")).toBe("nicht veröffentlicht");
    expect(sonderZelle(FIXTURE.eintraege["koe-on-ice"], "2026-12-31")).toBe("11–18 Uhr");
  });
});

describe("Rollen, Zahlen, Badges, Sortierung", () => {
  const gruppe = markt({ schluessel: "innenstadt", ist_gruppe: true });
  const teil = markt({ gruppe: "innenstadt" });
  const eis = markt({ gruppe: "innenstadt", attraktion: true, art: ["eisbahn"], merkmale: { eisbahn: { wert: "ja", quelle: "zitat", beleg: "Eisbahn" } },
    saisons: { "2026": FIXTURE.eintraege["koe-on-ice"]["2026"] } });
  const benrath = markt({ art: ["schloss", "kunsthandwerk"], merkmale: { kindereisenbahn: { wert: "ja", quelle: "zitat", beleg: "Eisenbahn" } },
    saisons: { "2026": FIXTURE.eintraege.benrath["2026"] } }, { name: "Benrath" });
  const alle = [gruppe, teil, eis, benrath];

  it("Hero zählt keine Gruppenzeile und keine Attraktion; Zeitraum nur aus Märkten", () => {
    expect(heroZahlen(alle)).toEqual({ anzahl: 2, von: "2026-11-19", bis: "2026-12-30", jahr: "2026" });
  });

  it("Jahr im Hub nur bis zum spätesten bis aller Einträge (Eisbahn bis 10.01.)", () => {
    expect(hubJahr(alle, "2026-11-17")).toBe("2026");
    expect(hubJahr(alle, "2027-01-10")).toBe("2026");
    expect(hubJahr(alle, "2027-01-11")).toBeNull();
    expect(hubJahr([], "2026-11-17")).toBeNull();
  });

  it("Badges aus Daten; Gruppe erbt Eisbahn über die Attraktion", () => {
    expect(badges(gruppe, alle).map((b) => b.wert)).toContain("eisbahn");
    expect(badges(teil, alle).map((b) => b.wert)).not.toContain("eisbahn");
    expect(badges(benrath, alle).map((b) => b.wert)).toEqual(["familien", "kindereisenbahn", "kunsthandwerk", "schloss", "wochenende"]);
  });

  it("Sortierung: Top-5-Rang, dann manueller vor gerechnetem Score (auch 0), dann Name", () => {
    const a = markt({ score: { wert: 9 } }, { name: "A" });
    const b = markt({ score: { wert: 9, manuell: 0 } }, { name: "B" });
    const c = markt({ top5_rang: 1 }, { name: "C" });
    expect(sortieren([a, b, c]).map((o) => o.name)).toEqual(["C", "A", "B"]);
  });

  it("Top 5 nur mit genau fünf Rängen", () => {
    const vier = [1, 2, 3, 4].map((r) => markt({ top5_rang: r }));
    expect(topFuenf(vier)).toEqual([]);
    expect(topFuenf([...vier, markt({ top5_rang: 5 })])).toHaveLength(5);
  });

  it("Liste: Gruppe mit Teilen (Märkte vor Attraktionen), danach die übrigen", () => {
    const l = listenReihenfolge(alle);
    expect(l[0].gruppe.id).toBe(gruppe.id);
    expect(l[0].teile.map((t) => t.id)).toEqual([teil.id, eis.id]);
    expect(l[1].gruppe.id).toBe(benrath.id);
  });

  it("Indexierbar mit Zeitraum, Wochenzeiten und Beschreibung", () => {
    expect(istIndexierbar(teil)).toBe(true);
    expect(istIndexierbar(markt({}, { beschreibung: null }))).toBe(false);
    expect(istIndexierbar(markt({ saisons: { "2026": FIXTURE.eintraege["ohne-zeiten"]["2026"] } }))).toBe(false);
    expect(istIndexierbar(markt({ saisons: FIXTURE.eintraege["leer-2027"] }))).toBe(true); // leerer neuer Schlüssel
  });

  it("Kartenpunkte: kein Pin für die Gruppe, keine Bewertung, kein Score, kein Zustand", () => {
    const punkte = weihnachtsmarktKartenOrte(alle);
    expect(punkte.map((p) => p.id)).not.toContain(gruppe.id);
    const text = JSON.stringify(punkte);
    // „Lange offen“ ist ein Badge, kein Zustand – geprüft werden Werte, keine Wortteile
    expect(text).not.toMatch(/"rating":\s*[0-9]|score|zustand|"(offen|zu|geschlossen|unbekannt)"/i);
  });

  it("JSON-LD: Event nur in der Saison, ohne aggregateRating", () => {
    const inSaison = weihnachtsmarktJsonLd(teil, "https://x.test", "2026-11-25");
    expect(inSaison["@type"]).toBe("Event");
    expect(inSaison.startDate).toBe("2026-11-19");
    expect(JSON.stringify(inSaison)).not.toContain("aggregateRating");
    expect(weihnachtsmarktJsonLd(teil, "https://x.test", "2027-01-05")["@type"]).toBe("Place");
  });

  it("FAQ-Werte: Totensonntag nennt geschlossene und unbelegte Einträge, Familien-Link in 1a ohne Parameter", () => {
    const w = faqWerte(alle);
    expect(w.saison).toBe("2026");
    expect(w.faq_totensonntag).toContain("22.11.2026");
    expect(w.faq_totensonntag).toContain("Geschlossen sind");
    expect(w.faq_familien).toContain("(/guides/weihnachtsmaerkte)");
    expect(w.faq_feiertage).toContain("Silvester");
  });
});

describe("Pfade und Einbau", () => {
  it("Stadtteil-Unterpfad ist immer 404, auch bei gültigem Stadtteil", async () => {
    expect(routeVon("/guides/weihnachtsmaerkte/stadtteil/altstadt")).toEqual({ typ: "guide-stadtteil", hub: "weihnachtsmaerkte", slug: "altstadt" });
    expect(await pfadPruefen("/guides/weihnachtsmaerkte/stadtteil/altstadt")).toEqual({ art: "fehlt" });
  });

  it("Detail: aktiv weiter, nie freigeschaltet 404, abgeschaltet 308 auf den Hub; wirft nicht", () => {
    const kopf = { typ: "weihnachtsmarkt", aktiv: true, qualitaets_score: null, club: null, club_score: null, club_freigegeben: null, auch_club: null };
    expect(weihnachtsmarktEntscheidung(kopf)).toEqual({ art: "weiter" });
    expect(weihnachtsmarktEntscheidung({ ...kopf, aktiv: false })).toEqual({ art: "fehlt" });
    expect(weihnachtsmarktEntscheidung({ ...kopf, aktiv: false, wm_freigeschaltet_am: "2026-11-18" })).toEqual({ art: "umleiten", ziel: "/guides/weihnachtsmaerkte" });
    expect(weihnachtsmarktEntscheidung({ ...kopf, typ: "spielplatz" })).toEqual({ art: "fehlt" });
    expect(() => ortEntscheidung("weihnachtsmaerkte", "x", kopf)).not.toThrow();
    expect(ortEntscheidung("weihnachtsmaerkte", "x", null)).toEqual({ art: "fehlt" });
  });

  it("Startseiten-Box nur vom 15.11. bis 30.12. und nur mit Schalter", () => {
    expect(startboxAktiv("2026-11-14", true)).toBe(false);
    expect(startboxAktiv("2026-11-15", true)).toBe(true);
    expect(startboxAktiv("2026-12-30", true)).toBe(true);
    expect(startboxAktiv("2026-12-31", true)).toBe(false);
    expect(startboxAktiv("2026-11-20", false)).toBe(false);
  });

  it("Texte: fünf FAQs, keine Score-Zahl, keine Google-Sterne", () => {
    const t = GUIDE_TEXTE.weihnachtsmaerkte;
    expect(t.faq).toHaveLength(5);
    const alles = JSON.stringify(t);
    expect(alles).not.toMatch(/Score|Sterne|Google-Bewertung/);
  });

  it("extras.weihnachtsmarkt wird nur aus bekannten Feldern gelesen", () => {
    const o = markt({ top5_rang: 7, merkmale: { eisbahn: { wert: "vielleicht" } } });
    expect(wm(o).top5_rang).toBeNull();
    expect(wm(o).merkmale).toEqual({});
  });
});
