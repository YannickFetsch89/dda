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
  BADGES, aktuelleSaison, badges, faqWerte, feiertag, heroZahlen, hubJahr, istIndexierbar, jetztText, listenReihenfolge, oeffnungAm, oeffnungText,
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
    // Sonderzeilen dürfen das Feld geschlossen:true tragen (Zeiten), aber nie einen gerechneten Zustand als Wert
    expect(text).not.toMatch(/"rating":\s*[0-9]|score|zustand|:"(offen|zu|geschlossen|unbekannt)"/i);
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

// ---------- Stufe 1b (Plan 7.2) ----------
import {
  EVENT_AUSSCHLUSS, badgeChips, eintragFuerEvent, gebietVon, kurzMaerkte, wmFilterHref, wmFilterLesen, wmFiltern, wmSortieren, WM_STANDARD,
} from "@/lib/weihnachtsmaerkte";
import { kanonischerStadtteil } from "@/lib/landing";

describe("Stufe 1b: Filter und Chips", () => {
  const gruppe = markt({ schluessel: "innenstadt", ist_gruppe: true });
  const teil = markt({ gruppe: "innenstadt", merkmale: { kunsthandwerk: { wert: "ja", quelle: "zitat", beleg: "x" } } }, { name: "Teil" });
  const eis = markt({ gruppe: "innenstadt", attraktion: true, art: ["eisbahn"], merkmale: { eisbahn: { wert: "ja", quelle: "zitat", beleg: "x" } },
    saisons: { "2026": FIXTURE.eintraege["koe-on-ice"]["2026"] } }, { name: "Eis" });
  const benrath = markt({ art: ["schloss", "kunsthandwerk"], merkmale: { kindereisenbahn: { wert: "ja", quelle: "zitat", beleg: "x" } },
    saisons: { "2026": FIXTURE.eintraege.benrath["2026"] } }, { name: "Benrath", stadtteil: "Benrath" });
  const neuss = markt({}, { name: "Neuss", stadtteil: "Neuss" });
  const alle = [gruppe, teil, eis, benrath, neuss];

  it("Parameter lesen: unbekannte Werte fallen weg, Href stabil sortiert", () => {
    const f = wmFilterLesen({ badge: "kunsthandwerk,quatsch,familien", gebiet: "mond", offen: "1", sort: "name" });
    expect(f).toEqual({ badges: ["kunsthandwerk", "familien"], gebiet: null, offen: true, sort: "name" });
    expect(wmFilterHref(f)).toBe("/guides/weihnachtsmaerkte?badge=familien%2Ckunsthandwerk&offen=1&sort=name");
    expect(wmFilterHref(WM_STANDARD)).toBe("/guides/weihnachtsmaerkte");
    expect(wmFilterHref(WM_STANDARD, { badges: ["familien"] })).toBe("/guides/weihnachtsmaerkte?badge=familien");
  });

  it("Gebiete: Gruppe und Teile = Innenstadt, Nachbarstädte eigen", () => {
    expect([gruppe, teil, eis, benrath, neuss].map(gebietVon)).toEqual(["innenstadt", "innenstadt", "innenstadt", "stadtteile", "neuss"]);
  });

  it("Filter UND, „heute geöffnet“ über den Bezugstag", () => {
    const f = { ...WM_STANDARD, badges: ["kunsthandwerk"] };
    expect(wmFiltern(alle, alle, f, "2026-11-25").map((o) => o.name).sort()).toEqual(["Benrath", "Teil"]);
    // Mi 25.11.: Benrath (nur Fr–So) zu, Teil offen
    expect(wmFiltern(alle, alle, { ...f, offen: true }, "2026-11-25").map((o) => o.name)).toEqual(["Teil"]);
    expect(wmFiltern(alle, alle, { ...WM_STANDARD, gebiet: "neuss" }, "2026-11-25").map((o) => o.name)).toEqual(["Neuss"]);
    expect(wmSortieren([benrath, teil], "name").map((o) => o.name)).toEqual(["Benrath", "Teil"]);
  });

  it("Chip-Schwellen: 2 allgemein, 1 für Eisbahn/Riesenrad/Kindereisenbahn, aktive bleiben", () => {
    const chips = badgeChips(alle.filter((o) => !wm(o).ist_gruppe), alle, []);
    const werte = chips.map((c) => c.wert);
    expect(werte).toContain("kunsthandwerk"); // 2 Treffer
    expect(werte).toContain("eisbahn"); // 1 Treffer reicht
    expect(werte).toContain("kindereisenbahn");
    expect(werte).not.toContain("riesenrad"); // 0 Treffer
    expect(badgeChips([], alle, ["familien"]).map((c) => c.wert)).toEqual(["familien"]);
  });
});

describe("Stufe 1b: Kurz-Markt-Liste und Event-Zuordnung", () => {
  const boehler = markt({ event_muster: ["weihnachtszauber.{0,30}b(ö|oe)hler"] }, { name: "Areal Böhler" });
  let k = 0;
  const ev = (titel: string, mehr: Record<string, unknown> = {}) => ({
    id: `e${++k}`, titel, datum: "2026-12-05", datum_bis: null, ort: "Ort", adresse: null, stadtteil: "Pempelfort", quelle_name: "Rausgegangen",
    quelle_url: `https://x.test/${k}`, abgesagt: false, slug: `e-${k}`, kategorie: "sonstiges", ...mehr,
  });

  it("Ausschlussliste ist ein Spiegel von data/weihnachtsmaerkte/event_ausschluss.csv", () => {
    const csv = readFileSync(join(__dirname, "..", "..", "data", "weihnachtsmaerkte", "event_ausschluss.csv"), "utf8").trim().split(/\r?\n/).slice(1);
    expect(new Set(csv.map((z) => z.split(",")[0]))).toEqual(EVENT_AUSSCHLUSS);
  });

  it("Treffer und bekannte Fehltreffer (Leipzig, Hürth, Meetup, Guide-Eintrag, Dublette)", () => {
    const events = [
      ev("Bücherweihnachtsmarkt 2026", { stadtteil: "Pempelfort" }),
      ev("Bücherweihnachtsmarkt 2026 in Düsseldorf", { stadtteil: "Pempelfort" }),
      ev("1. Alternativer Weihnachtsmarkt", { datum: "2026-12-06", stadtteil: "Flingern" }),
      ev("Veihnachtsmarkt Düsseldorf: der vegane Weihnachtsmarkt", { datum: "2026-11-28", stadtteil: null, adresse: "Fürstenwall 1, 40219 Düsseldorf" }),
      ev("Leipziger Weihnachtsmarkt 2026", { stadtteil: "Altstadt", quelle_url: "https://prinz.de/events/leipziger-weihnachtsmarkt/2026-12-12/" }),
      ev("Gertrudenhof Hundeweihnachtsmarkt", { stadtteil: null, adresse: null, ort: "Erlebnisbauernhof Gertrudenhof" }),
      ev("Adventsmarkt in Hürth", { stadtteil: null, adresse: "Hauptstraße 1, 50354 Hürth" }),
      ev("Oberbilker Lichterzauber", { datum: "2026-11-21", stadtteil: null, adresse: null, ort: "Josef-Saal" }),
      ev("Secret Hitl€r Friday + Weihnachtsmarkt", { quelle_name: "Meetup.com" }),
      ev("Weihnachtszauber auf dem Areal Böhler", { stadtteil: "Heerdt" }),
      ev("Weihnachtsmarkt von gestern", { datum: "2026-11-10" }),
      ev("Konzert im Advent"),
    ];
    const liste = kurzMaerkte(events, [boehler], "2026-11-17", kanonischerStadtteil);
    // Ohne Adresse und Stadtteil durchgelassen (18.11.2026), Gertrudenhof (Hürth) und PLZ außerhalb bleiben draußen
    expect(liste.map((e) => e.titel)).toEqual([
      "Oberbilker Lichterzauber",
      "Veihnachtsmarkt Düsseldorf: der vegane Weihnachtsmarkt",
      "Bücherweihnachtsmarkt 2026",
      "1. Alternativer Weihnachtsmarkt",
    ]);
  });

  it("Event ↔ Eintrag über event_muster (Titel und Ort, ohne Groß/Klein)", () => {
    expect(eintragFuerEvent({ titel: "WEIHNACHTSZAUBER auf dem Areal Böhler", ort: "" }, [boehler])?.name).toBe("Areal Böhler");
    expect(eintragFuerEvent({ titel: "Bücherweihnachtsmarkt", ort: "FFT" }, [boehler])).toBeNull();
    // ungültiges Muster wirft nie
    expect(eintragFuerEvent({ titel: "x", ort: "" }, [markt({ event_muster: ["(("] })])).toBeNull();
  });
});

// ---------- Cursor-Check Stufe 1b: fehlende Abdeckung ----------
import { gleicherOrt, pinZustand, topFuenfAm, wmKartenCache } from "@/lib/weihnachtsmaerkte";

describe("Cursor-Check Stufe 1b", () => {
  it("Top 5 nur vom 01.10. bis 30.12., ohne Tag nie", () => {
    const fuenf = [1, 2, 3, 4, 5].map((r) => markt({ top5_rang: r }));
    expect(topFuenfAm(fuenf, "2026-12-30")).toHaveLength(5);
    expect(topFuenfAm(fuenf, "2026-12-31")).toEqual([]);
    expect(topFuenfAm(fuenf, "2026-09-30")).toEqual([]);
    expect(topFuenfAm(fuenf, null)).toEqual([]);
  });

  it("Pin-Zustand: offen, zu, Saison, unbekannt", () => {
    expect(pinZustand(FIXTURE.eintraege.innenstadt, "2026-11-21")).toBe("offen");
    expect(pinZustand(FIXTURE.eintraege.innenstadt, "2026-11-22")).toBe("zu");
    expect(pinZustand(FIXTURE.eintraege.innenstadt, "2026-11-18")).toBe("saison");
    expect(pinZustand(FIXTURE.eintraege.innenstadt, "2026-12-31")).toBe("saison");
    expect(pinZustand(FIXTURE.eintraege.nordstrasse, "2026-11-22")).toBe("unbekannt");
  });

  it("Karten-Cache: „heute geöffnet“ ohne gültigen Tag nie aus geteilten Caches", () => {
    const pub = "public, max-age=300";
    expect(wmKartenCache({ offen: "1" }, pub)).toBe("private, no-store");
    expect(wmKartenCache({ offen: "1", tag: "2026-02-31" }, pub)).toBe("private, no-store");
    expect(wmKartenCache({ offen: "1", tag: "2026-12-24" }, pub)).toBe(pub);
    expect(wmKartenCache({}, pub)).toBe(pub);
    expect(wmKartenCache({ tag: "2026-12-24" }, pub)).toBe(pub);
  });

  it("FAQ 5 verlinkt in 1b den Familien-Filter", () => {
    const w = faqWerte([markt({ merkmale: { kinderprogramm: { wert: "ja", quelle: "zitat", beleg: "x" } } })], wmFilterHref(WM_STANDARD, { badges: ["familien"] }));
    expect(w.faq_familien).toContain("(/guides/weihnachtsmaerkte?badge=familien)");
  });

  it("Kurz-Markt-Liste: Bulle und gleichnamige Märkte an verschiedenen Orten bleiben getrennt", () => {
    let k = 0;
    const ev = (titel: string, mehr: Record<string, unknown> = {}) => ({
      id: `k${++k}`, titel, datum: "2026-12-04", datum_bis: null, ort: "Ort", adresse: null, stadtteil: "Flingern", quelle_name: "Rausgegangen",
      quelle_url: `https://y.test/${k}`, abgesagt: false, slug: `k-${k}`, kategorie: "sonstiges", ...mehr,
    });
    const liste = kurzMaerkte([
      ev("BULLE WINTERMARKT", { ort: "Bulle Bistro" }),
      ev("Adventsmarkt der Gemeinde", { ort: "St. Anna" }),
      ev("Adventsmarkt der Gemeinde", { ort: "St. Paulus", stadtteil: "Düsseltal" }),
    ], [], "2026-11-17", kanonischerStadtteil);
    expect(liste.map((e) => `${e.titel}@${e.ort}`).sort()).toEqual(["Adventsmarkt der Gemeinde@St. Anna", "Adventsmarkt der Gemeinde@St. Paulus", "BULLE WINTERMARKT@Bulle Bistro"]);
  });

  it("Einbaustellen und Foto-Cache stehen im Code (Textprüfung)", () => {
    const lies = (p: string) => readFileSync(join(__dirname, "..", p), "utf8");
    // Familie: Link steht im Familien-Eintrag hinter dem Schalter und zeigt auf den Filter des Hubs
    expect(lies("app/kategorie/[slug]/page.tsx")).toMatch(/familie: \[[\s\S]{0,300}WEIHNACHTSMAERKTE_VERLINKT[\s\S]{0,120}pfad: "\/guides\/weihnachtsmaerkte\?badge=familien"/);
    // Food/Märkte: Bedingung und Ziel gehören zusammen (Cursor-Recheck Stufe 1b)
    expect(lies("app/kategorie/[slug]/[unter]/page.tsx")).toMatch(/u\.slug === "maerkte"[\s\S]{0,240}pfad: "\/guides\/weihnachtsmaerkte"/);
    // Foto-Cache: Weihnachtsmärkte rufen bildQuelle mit dem 30-Tage-Schalter auf, und der Schalter begrenzt expire
    const foto = lies("app/ort-foto/[slug]/route.ts");
    expect(foto).toMatch(/bildQuelle\([\s\S]*?ort\?\.typ === "weihnachtsmarkt"/);
    expect(foto).toMatch(/hoechstens30Tage \? \{ stale: TAG, revalidate: 20 \* TAG, expire: 30 \* TAG \}/);
  });

  it("Dubletten: „FFT“ und „FFT Düsseldorf – Forum Freies Theater“ sind derselbe Ort (Cursor-Recheck)", () => {
    expect(gleicherOrt("fft", "fft düsseldorf forum freies theater")).toBe(true);
    expect(gleicherOrt("st anna", "st paulus")).toBe(false);
    expect(gleicherOrt("zk", "zk halle")).toBe(false); // zu kurz für einen sicheren Präfix
    const ev = (ort: string, titel: string) => ({
      id: `${ort}${titel}`, titel, datum: "2026-12-05", datum_bis: null, ort, adresse: null, stadtteil: "Pempelfort", quelle_name: "x",
      quelle_url: `https://z.test/${ort}/${titel}`, abgesagt: false, slug: "s", kategorie: "sonstiges",
    });
    const liste = kurzMaerkte([ev("FFT Düsseldorf – Forum Freies Theater", "Bücherweihnachtsmarkt 2026 in Düsseldorf"), ev("FFT", "Bücherweihnachtsmarkt 2026")],
      [], "2026-11-17", kanonischerStadtteil);
    expect(liste.map((e) => e.titel)).toEqual(["Bücherweihnachtsmarkt 2026"]);
  });
});

import { lokalesBild, ortBildAutorUrl, ortBildUrl } from "@/lib/orte";

describe("Eigene Bilder (Veranstalter) mit Bildnachweis", () => {
  const mitBild = (bild_url: string | null, extras: Record<string, unknown> = {}) => {
    const o = markt({});
    return { ...o, bild_url, bild_attribution: "IG Nordstraße", extras: { ...o.extras, ...extras } };
  };
  const google = { google_foto: { name: "places/abc/photos/def", autor_url: "https://maps.google.com/maps/contrib/1" } };

  it("Bild aus web/public wird direkt ausgeliefert, mit Version gegen alten Browser-Cache", () => {
    expect(ortBildUrl(mitBild("/ort-bilder/weihnachtsmaerkte/nordstrasse.webp", google))).toBe("/ort-bilder/weihnachtsmaerkte/nordstrasse.webp");
    expect(ortBildUrl(mitBild("/ort-bilder/weihnachtsmaerkte/nordstrasse.webp", { foto_version: 3 }))).toBe("/ort-bilder/weihnachtsmaerkte/nordstrasse.webp?v=3");
  });

  it("nur das enge Muster gilt als lokal – alles andere läuft weiter über den Proxy", () => {
    for (const falsch of ["/ort-bilder/../secret.webp", "//evil.example/x.webp", "/ort-bilder/weihnachtsmaerkte/x.svg", "/ort-bilder/x.webp", "/guides/weihnachtsmaerkte/x.webp", "https://x.de/a.webp", null]) {
      expect(lokalesBild(falsch)).toBeNull();
    }
    const fremd = mitBild("https://veranstalter.de/bild.jpg");
    expect(ortBildUrl(fremd)).toBe(`/ort-foto/${fremd.slug}`);
  });

  it("Link im Bildnachweis: beim eigenen Bild bild_link (nur https), beim Google-Foto der Urheber", () => {
    expect(ortBildAutorUrl(mitBild("/ort-bilder/weihnachtsmaerkte/nordstrasse.webp", { ...google, bild_link: "https://nordstrasse.de" }))).toBe("https://nordstrasse.de/");
    expect(ortBildAutorUrl(mitBild("/ort-bilder/weihnachtsmaerkte/nordstrasse.webp", { ...google, bild_link: "javascript:alert(1)" }))).toBeNull();
    expect(ortBildAutorUrl(mitBild("/ort-bilder/weihnachtsmaerkte/nordstrasse.webp", google))).toBeNull();
    expect(ortBildAutorUrl(mitBild(null, google))).toBe("https://maps.google.com/maps/contrib/1");
  });
});

describe("Zusammengelegte Märkte (Schadow-Markt = Märchen-Markt, 18.11.2026)", () => {
  it("gelöschter Schadow-Markt leitet dauerhaft auf den Märchen-Markt, andere unbekannte Slugs bleiben 404", () => {
    expect(ortEntscheidung("weihnachtsmaerkte", "schadow-markt-stadtmitte", null)).toEqual({ art: "umleiten", ziel: "/guides/weihnachtsmaerkte/maerchen-markt-stadtmitte" });
    expect(ortEntscheidung("weihnachtsmaerkte", "gibt-es-nicht", null)).toEqual({ art: "fehlt" });
  });
  it("Übersichtstext nennt den Schadow-Markt nicht mehr getrennt", () => {
    expect(JSON.stringify(GUIDE_TEXTE)).not.toContain("Schadow-Markt");
  });
});

describe("Eigene Bilder liegen außerhalb der Pfadprüfung", () => {
  it("proxy.ts prüft /ort-bilder/… nicht als Seite (unter /guides/<hub>/ wären die Bilder 404)", () => {
    expect(routeVon("/ort-bilder/weihnachtsmaerkte/nordstrasse.webp")).toBeNull();
    expect(routeVon("/guides/weihnachtsmaerkte/nordstrasse.webp")).not.toBeNull();
    const proxy = readFileSync(join(__dirname, "..", "proxy.ts"), "utf8");
    expect(proxy).not.toContain("/ort-bilder");
  });
});

describe("Karten-API packt nicht selbst (18.11.2026)", () => {
  it("kein eigenes gzip – Next.js 16.4.6 packt selbst, sonst doppelt gepackt und alle Guide-Karten leer", () => {
    const quelle = readFileSync(join(__dirname, "..", "app", "api", "guide-karte", "route.ts"), "utf8");
    expect(quelle).not.toContain("CompressionStream");
    expect(quelle).not.toMatch(/["']Content-Encoding["']\s*:/);
  });
});

import { fettTeile, kurzBeschreibung, ohneFett } from "@/lib/beschreibung";

describe("Fett in Beschreibungen (Weihnachtsmärkte, 18.11.2026)", () => {
  it("zerlegt **Wort** in fette Teile, einzelne Sternchen bleiben Text", () => {
    expect(fettTeile("Rund **15.000 LEDs** am **Kö-Bogen**.")).toEqual([
      { text: "Rund ", fett: false }, { text: "15.000 LEDs", fett: true }, { text: " am ", fett: false },
      { text: "Kö-Bogen", fett: true }, { text: ".", fett: false },
    ]);
    expect(fettTeile("Preis * ab 5 €")).toEqual([{ text: "Preis * ab 5 €", fett: false }]);
  });
  it("Meta-Description und JSON-LD ohne Sternchen", () => {
    expect(ohneFett("Die **Weihnachtspromenade** gibt es seit **2024**.")).toBe("Die Weihnachtspromenade gibt es seit 2024.");
    expect(kurzBeschreibung("Der **Altstadt-Markt** liegt\n\nmitten in der Altstadt.")).toBe("Der Altstadt-Markt liegt mitten in der Altstadt.");
    const j = JSON.stringify(weihnachtsmarktJsonLd(markt({}, { beschreibung: "Mit **Eisbahn**." }), "https://diesdas.events", "2026-11-20"));
    expect(j).toContain("Mit Eisbahn.");
    expect(j).not.toContain("**");
  });
});

describe("Kein „Unser Tipp“-Badge mehr (18.11.2026)", () => {
  it("auch Top-5-Märkte bekommen kein Tipp-Badge", () => {
    const o = markt({ top5_rang: 1 });
    expect(badges(o, [o]).map((b) => b.wert)).not.toContain("tipp");
    expect(BADGES.map((b) => b.wert)).not.toContain("tipp");
  });
});

import { EVENT_EINSCHLUSS } from "@/lib/weihnachtsmaerkte";

describe("Einschlussliste kleine Märkte (19.11.2026)", () => {
  it("ist ein Spiegel von data/weihnachtsmaerkte/event_einschluss.csv", () => {
    const csv = readFileSync(join(__dirname, "..", "..", "data", "weihnachtsmaerkte", "event_einschluss.csv"), "utf8").trim().split(/\r?\n/).slice(1);
    expect(new Set(csv.map((z) => z.split(",")[0]))).toEqual(EVENT_EINSCHLUSS);
  });
  it("nimmt eingeschlossene Events auch ohne passenden Titel auf", () => {
    const e = (titel: string, quelle_url: string) => ({
      id: titel, titel, datum: "2026-12-13", datum_bis: null, ort: "Franklinstraße 41", adresse: null, stadtteil: null, quelle_name: "Rausgegangen",
      quelle_url, abgesagt: false, slug: titel, kategorie: "sonstiges",
    });
    const liste = kurzMaerkte([
      e("HANDMADE MARKT Keramik & More Weihnachts Edition", "https://rausgegangen.de/events/handmade-markt-keramik-more-weihnachts-edition-0/"),
      e("Keramik-Workshop", "https://x.test/workshop"),
    ], [], "2026-11-19", kanonischerStadtteil);
    expect(liste.map((x) => x.titel)).toEqual(["HANDMADE MARKT Keramik & More Weihnachts Edition"]);
  });
});
