// Tests zu lib/fuer-dich.ts (Plan docs/plan-mein-bereich-stufe1-2026-11-18.md, Abschnitte 3.3, 4.2, 5 und 10)
import { describe, expect, it } from "vitest";
import { beliebtAuswahl, filtern, fokustag, stufenKontext } from "@/lib/ableitungen";
import {
  ABSCHNITT_MAX, START_MAX, anzahlVorschlaege, bewerten, fuerDichSeite, kandidaten, mitDeckeln, startFenster,
  startVorschlaege, type Eingabe, type Gemerkt, type Interessen,
} from "@/lib/fuer-dich";
import { KATEGORIEN } from "@/lib/kategorien";
import { stadtteilSlug } from "@/lib/landing";
import type { DddEvent } from "@/lib/typen";
import { ev } from "./hilfen";

// Donnerstag; Wochenende Fr 20. – So 22.11.
const HEUTE = "2026-11-19";
const MORGEN = "2026-11-20";

function eingabe(events: DddEvent[], teil: Partial<Eingabe> = {}, heute = HEUTE): Eingabe {
  return {
    events, heute, stufen: stufenKontext(events, heute), personalisierung: true, interessen: {}, merkliste: [],
    sensibel: new Set(), ...teil,
  };
}
const heuteFenster = startFenster(HEUTE, HEUTE, HEUTE);
const gemerkt = (event: DddEvent, gemerktAm = "2026-11-01T10:00:00Z"): Gemerkt => ({ event, gemerktAm });
const ids = (liste: { event: DddEvent }[]) => liste.map((v) => v.event.id);

describe("Fenster der Startseite (4.2)", () => {
  it("Heute → sieben Tage im-fenster, anderer Tag → tag, Zeitraum → kein", () => {
    expect(startFenster(HEUTE, HEUTE, HEUTE)).toEqual({ von: HEUTE, bis: "2026-11-25", fokus: "im-fenster" });
    expect(startFenster(MORGEN, MORGEN, HEUTE)).toEqual({ von: MORGEN, bis: MORGEN, fokus: "tag" });
    expect(startFenster(HEUTE, "2026-11-25", HEUTE)).toEqual({ von: HEUTE, bis: "2026-11-25", fokus: "kein" });
  });
});

describe("Punkte (5)", () => {
  const flingern = "Flingern-Nord";
  const interessen: Interessen = {
    kategorien: ["musik"], unterkategorien: ["musik/jazz"], stadtteile: [stadtteilSlug(flingern)],
    merkmale: ["kostenlos", "abends"],
  };
  it("Unterkategorie +3, Kategorie +2, Stadtteil +1, je Merkmal +1", () => {
    const e = ev({ id: "a", datum: HEUTE, kategorie: "musik", unterkategorie: "jazz", stadtteil: flingern, preis: "kostenlos", uhrzeit: "20:00" });
    const v = bewerten(eingabe([e], { interessen }), e, heuteFenster);
    expect(v.punkte).toBe(3 + 2 + 1 + 1 + 1);
    expect(v.begruendung).toBe("Jazz & Soul · Musik");
  });
  it("unterkategorie „keine“ trifft nie, ohne Stadtteil kein Treffer, orte geben keine Punkte", () => {
    const e = ev({ id: "a", datum: HEUTE, kategorie: "kultur", unterkategorie: "keine", stadtteil: null });
    const v = bewerten(
      eingabe([e], { interessen: { unterkategorien: ["kultur/keine"], stadtteile: ["flingern-nord"], orte: ["clubs", "kneipen-bars"] } }),
      e, heuteFenster,
    );
    expect(v.punkte).toBe(0);
  });
  it("mit-kindern trifft nur die Kategorie familie", () => {
    const fam = ev({ id: "f", datum: HEUTE, kategorie: "familie" });
    const kul = ev({ id: "k", datum: HEUTE, kategorie: "kultur", titel: "Kindertheater" });
    const e = eingabe([fam, kul], { interessen: { merkmale: ["mit-kindern"] } });
    expect(bewerten(e, fam, heuteFenster).punkte).toBe(1);
    expect(bewerten(e, kul, heuteFenster).punkte).toBe(0);
  });
  it("„Von allem etwas“ (alle KATEGORIEN) gibt kein +2", () => {
    const e = ev({ id: "a", datum: HEUTE, kategorie: "musik", unterkategorie: "jazz" });
    const alle = KATEGORIEN.map((k) => k.slug);
    expect(alle).not.toContain("sonstiges");
    const v = bewerten(eingabe([e], { interessen: { kategorien: alle, unterkategorien: ["musik/jazz"] } }), e, heuteFenster);
    expect(v.punkte).toBe(3);
  });
  it("Bündel mit 11:00 und 19:00 trifft abends und tagsüber, ohne Uhrzeit keines", () => {
    const b = ev({ id: "b", datum: HEUTE, uhrzeiten: ["11:00", "19:00"] });
    const o = ev({ id: "o", datum: HEUTE });
    const e = eingabe([b, o], { interessen: { merkmale: ["abends", "tagsueber"] } });
    expect(bewerten(e, b, heuteFenster).punkte).toBe(2);
    expect(bewerten(e, o, heuteFenster).punkte).toBe(0);
  });
  it("Wochenende: bei fokus tag der Tag selbst, sonst ein Tag der Laufzeit im Fenster", () => {
    const sa = ev({ id: "s", datum: "2026-11-21" });
    const e = eingabe([sa], { interessen: { merkmale: ["wochenende"] } });
    expect(bewerten(e, sa, { von: "2026-11-21", bis: "2026-11-21", fokus: "tag" }).punkte).toBe(1);
    expect(bewerten(e, sa, heuteFenster).punkte).toBe(1);
    const di = ev({ id: "d", datum: "2026-11-24" });
    expect(bewerten(eingabe([di], { interessen: { merkmale: ["wochenende"] } }), di, heuteFenster).punkte).toBe(0);
  });
  it("Reihe und Ort eines gemerkten Events zusammen nur einmal +1; Sammelort und sensibles Bezugs-Event nie", () => {
    const g = ev({ id: "g", datum: "2026-11-10", ort: "zakk", reihe: { slug: "jazzabend", titel: "Jazzabend" }, titel: "Jazzabend" });
    const beides = ev({ id: "x", datum: HEUTE, ort: "zakk", reihe: { slug: "jazzabend", titel: "Jazzabend" } });
    const e = eingabe([beides], { merkliste: [gemerkt(g)] });
    const v = bewerten(e, beides, heuteFenster);
    expect(v.punkte).toBe(1);
    expect(v.bezuege).toEqual(["g"]);
    expect(v.begruendung).toBe("wie ‚Jazzabend‘");

    const sammel = ev({ id: "s", datum: HEUTE, ort: "Düsseldorf" });
    const gs = ev({ id: "gs", datum: "2026-11-10", ort: "Düsseldorf" });
    expect(bewerten(eingabe([sammel], { merkliste: [gemerkt(gs)] }), sammel, heuteFenster).punkte).toBe(0);

    const sensibelGemerkt = eingabe([beides], { merkliste: [gemerkt(g)], sensibel: new Set(["g"]) });
    const vs = bewerten(sensibelGemerkt, beides, heuteFenster);
    expect(vs.punkte).toBe(0);
    expect(vs.begruendung).not.toContain("Jazzabend");
  });
});

describe("Kandidaten (5)", () => {
  it("Gemerkte, sensible, abgesagte, Stamm-, vorbei- und `ohne`-Events fallen raus", () => {
    const events = [
      ev({ id: "ok", datum: HEUTE, ort: "A" }),
      ev({ id: "gemerkt", datum: HEUTE, ort: "B" }),
      ev({ id: "sensibel", datum: HEUTE, ort: "C" }),
      ev({ id: "abgesagt", datum: HEUTE, ort: "D", abgesagt: true }),
      ev({ id: "stamm", datum: HEUTE, ort: "E", titel: "Sprachcafé" }),
      ev({ id: "ohne", datum: HEUTE, ort: "F" }),
    ];
    const e = eingabe(events, { merkliste: [gemerkt(events[1])], sensibel: new Set(["sensibel"]) });
    expect(kandidaten(e, heuteFenster, new Set(["ohne"])).map((x) => x.id)).toEqual(["ok"]);
  });
  it("Fokustag: tag → nur am Fokustag, im-fenster → Fokustag im Fenster, kein → immer", () => {
    const m = ev({ id: "mehr", datum: HEUTE, datum_bis: "2026-11-23", ort: "Kunsthalle" });
    const f = fokustag(m);
    const e = eingabe([m]);
    const anderer = f === HEUTE ? "2026-11-23" : HEUTE;
    expect(kandidaten(e, { von: f, bis: f, fokus: "tag" }).length).toBe(1);
    expect(kandidaten(e, { von: anderer, bis: anderer, fokus: "tag" }).length).toBe(0);
    expect(kandidaten(e, { von: f, bis: f, fokus: "im-fenster" }).length).toBe(1);
    expect(kandidaten(e, { von: anderer, bis: anderer, fokus: "im-fenster" }).length).toBe(0);
    expect(kandidaten(e, { von: anderer, bis: anderer, fokus: "kein" }).length).toBe(1);
  });
  it("Langläufer sind dabei (mitLanglaeufern), begrenzt durch die Fokustag-Regel; Gegenprobe ohne Schalter", () => {
    const l = ev({ id: "lang", datum: "2026-11-01", datum_bis: "2026-12-31", ort: "Museum", kategorie: "kultur" });
    const e = eingabe([l]);
    const zeitraum = { von: "2026-11-20", bis: "2026-11-22", fokus: "kein" as const };
    expect(kandidaten(e, zeitraum).map((x) => x.id)).toEqual(["lang"]);
    expect(filtern([l], { von: zeitraum.von, bis: zeitraum.bis }).length).toBe(0);
    const f = fokustag(l);
    const nichtFokus = f === "2026-11-20" ? "2026-11-21" : "2026-11-20";
    expect(kandidaten(e, { von: nichtFokus, bis: nichtFokus, fokus: "tag" }).length).toBe(0);
  });
  it("Vergangener einzelner Tag: keine Kandidaten, kein Ersatz", () => {
    const alt = ev({ id: "alt", datum: "2026-11-10" });
    const e = eingabe([alt]);
    expect(startVorschlaege(e, startFenster("2026-11-10", "2026-11-10", HEUTE))).toEqual({ art: "leer" });
  });
  it("Vergangener Tag = Fokustag eines noch laufenden Mehrtägigen: trotzdem keine Kandidaten (Cursor-Befund 1)", () => {
    // Laufzeit 16.–22.11., heute 19.11.; eine ID suchen, deren Fokustag vor heute liegt
    const lauf = Array.from({ length: 40 }, (_, i) =>
      ev({ id: `lauf${i}`, datum: "2026-11-16", datum_bis: "2026-11-22", kategorie: "kultur" }),
    ).find((x) => fokustag(x) < HEUTE)!;
    const tag = fokustag(lauf);
    const e = eingabe([lauf], { interessen: { kategorien: ["kultur"] } });
    expect(kandidaten(e, startFenster(tag, tag, HEUTE))).toEqual([]);
    expect(startVorschlaege(e, startFenster(tag, tag, HEUTE))).toEqual({ art: "leer" });
    // Gegenprobe: wäre dieser Tag heute, wäre das Event Kandidat
    expect(kandidaten(eingabe([lauf], {}, tag), startFenster(tag, tag, tag)).map((x) => x.id)).toEqual([lauf.id]);
  });
});

describe("Liste und Deckel (5)", () => {
  const interessen: Interessen = { kategorien: ["musik", "kultur"], merkmale: ["kostenlos"] };
  it("höchstens 2 je Kategorie, 1 je Reihe, 2 je Ort, ohne Nachschub; Sammelort ohne Ort-Deckel", () => {
    const musik = [1, 2, 3].map((n) => ev({ id: `m${n}`, datum: HEUTE, ort: `Ort ${n}`, kategorie: "musik", preis: "kostenlos" }));
    const reihe = [1, 2].map((n) => ev({ id: `r${n}`, datum: HEUTE, ort: `R ${n}`, kategorie: "kultur", reihe: { slug: "lesung", titel: "Lesung" } }));
    const e = eingabe([...musik, ...reihe], { interessen });
    const r = startVorschlaege(e, heuteFenster);
    expect(r.art).toBe("persoenlich");
    if (r.art !== "persoenlich") return;
    expect(ids(r.liste).filter((i) => i.startsWith("m")).length).toBe(2);
    expect(ids(r.liste).filter((i) => i.startsWith("r")).length).toBe(1);

    const gleicherOrt = [1, 2, 3].map((n) => ev({ id: `o${n}`, datum: HEUTE, ort: "zakk", kategorie: n === 1 ? "musik" : "kultur", preis: "kostenlos" }));
    const sammel = [1, 2, 3].map((n) => ev({ id: `s${n}`, datum: HEUTE, ort: "Düsseldorf", kategorie: n === 1 ? "musik" : "kultur", preis: "kostenlos" }));
    const e2 = eingabe([...gleicherOrt], { interessen });
    const vs = gleicherOrt.map((x) => bewerten(e2, x, heuteFenster));
    expect(mitDeckeln(vs, 8).length).toBe(2);
    const e3 = eingabe([...sammel], { interessen });
    const vs3 = sammel.map((x) => bewerten(e3, x, heuteFenster));
    // Kategorie-Deckel greift (2× kultur), der Ort-Deckel nicht
    expect(mitDeckeln(vs3, 8).length).toBe(3);
  });
  it("Mindestens 2 Punkte; sonst Ersatz „Beliebt“ (bis 8, ohne Deckel, ohne sensible)", () => {
    const viele = Array.from({ length: 12 }, (_, n) => ev({ id: `e${n}`, datum: HEUTE, ort: "zakk", kategorie: "sport" }));
    const e = eingabe(viele, { interessen: { merkmale: ["kostenlos"] }, sensibel: new Set(["e0"]) });
    const r = startVorschlaege(e, heuteFenster);
    expect(r.art).toBe("ersatz");
    if (r.art !== "ersatz") return;
    expect(r.liste.length).toBe(START_MAX);
    expect(r.liste.map((x) => x.id)).not.toContain("e0");
  });
  it("Ohne Einwilligung: keine Punkte, kein Ersatz, Merkliste wird nicht angesehen", () => {
    const e = eingabe([ev({ id: "a", datum: HEUTE })], { personalisierung: false });
    Object.defineProperty(e, "merkliste", { get: () => { throw new Error("Merkliste gelesen"); } });
    expect(startVorschlaege(e, heuteFenster)).toEqual({ art: "ohne-einwilligung" });
    expect(fuerDichSeite(e)).toEqual({ art: "ohne-einwilligung" });
    expect(anzahlVorschlaege(e)).toBeNull();
  });
  it("Leere Kandidatenmenge → leer, kein Ersatz", () => {
    expect(startVorschlaege(eingabe([], { interessen: { kategorien: ["musik"] } }), heuteFenster)).toEqual({ art: "leer" });
  });
  it("Öffentliches „Heute“ (7 Tage) ist nicht beliebtAuswahl der Startseite (ein Tag + Reserve)", () => {
    const heute = ev({ id: "h", datum: HEUTE, ort: "A", kategorie: "musik" });
    const spaeter = ev({ id: "s", datum: "2026-11-23", ort: "B", kategorie: "musik" });
    const e = eingabe([heute, spaeter], { interessen: { kategorien: ["musik"] } });
    const r = startVorschlaege(e, heuteFenster);
    const oeffentlich = beliebtAuswahl(filtern([heute, spaeter], { von: HEUTE, bis: HEUTE }), [], e.stufen, HEUTE, 5);
    expect(r.art === "persoenlich" && ids(r.liste)).toContain("s");
    expect(oeffentlich.map((x) => x.id)).not.toContain("s");
  });
  it("anzahlVorschlaege = Länge der persönlichen Liste im 7-Tage-Fenster, 0 bei Ersatz", () => {
    const a = ev({ id: "a", datum: HEUTE, ort: "A", kategorie: "musik" });
    expect(anzahlVorschlaege(eingabe([a], { interessen: { kategorien: ["musik"] } }))).toBe(1);
    expect(anzahlVorschlaege(eingabe([a], { interessen: { kategorien: ["kultur"] } }))).toBe(0);
  });
});

describe("Seite /konto/fuer-dich (3.3)", () => {
  const SAMSTAG = "2026-11-21";
  it("jedes Event nur einmal; Wochenende Fr–So aus wochenende(), an Sa auch mit laufendem Freitag-Event", () => {
    const events = [
      ev({ id: "sa", datum: SAMSTAG, ort: "A", kategorie: "musik" }),
      ev({ id: "so", datum: "2026-11-22", ort: "B", kategorie: "musik" }),
      ev({ id: "di", datum: "2026-11-24", ort: "C", kategorie: "kultur" }),
    ];
    const e = eingabe(events, { interessen: { kategorien: ["musik", "kultur"] } }, SAMSTAG);
    const r = fuerDichSeite(e);
    expect(r.art).toBe("abschnitte");
    if (r.art !== "abschnitte") return;
    const alle = r.abschnitte.flatMap((a) => ids(a.liste));
    expect(new Set(alle).size).toBe(alle.length);
    expect(r.abschnitte[0].schluessel).toBe("heute");
    expect(ids(r.abschnitte[0].liste).sort()).toEqual(["sa", "so"]);
    expect(r.abschnitte.find((a) => a.schluessel === "wochenende")).toBeUndefined();
    expect(r.abschnitte.find((a) => a.schluessel === "interessen")?.liste.map((v) => v.event.id)).toEqual(["di"]);
  });
  it("Abschnitt 3: nur mit mindestens 2 Punkten, genau ein Bezugs-Event (meiste Treffer, dann zuletzt gemerkt, dann event_id)", () => {
    const g1 = ev({ id: "g1", datum: "2026-11-01", ort: "zakk", titel: "Konzert im zakk" });
    const g2 = ev({ id: "g2", datum: "2026-11-02", ort: "Tonhalle", titel: "Abend in der Tonhalle" });
    const events = [
      ev({ id: "z1", datum: "2026-11-25", ort: "zakk", kategorie: "musik" }),
      ev({ id: "t1", datum: "2026-11-26", ort: "Tonhalle", kategorie: "musik" }),
      ev({ id: "z2", datum: "2026-11-27", ort: "zakk", kategorie: "kultur" }),
      ev({ id: "nurbezug", datum: "2026-11-28", ort: "zakk", kategorie: "sport" }),
    ];
    const e = eingabe(events, {
      interessen: { kategorien: ["musik", "kultur"] },
      merkliste: [gemerkt(g1, "2026-11-01T10:00:00Z"), gemerkt(g2, "2026-11-05T10:00:00Z")],
    });
    const r = fuerDichSeite(e);
    if (r.art !== "abschnitte") throw new Error("erwartet Abschnitte");
    const a3 = r.abschnitte.find((a) => a.schluessel === "gemerkt")!;
    expect(a3.titel).toBe("Weil du ‚Konzert im zakk‘ gemerkt hast");
    expect(ids(a3.liste).sort()).toEqual(["z1", "z2"]);
    // nurbezug hat nur +1 aus dem Bezug: kein Vorschlag
    expect(r.abschnitte.flatMap((a) => ids(a.liste))).not.toContain("nurbezug");
    expect(ids(r.abschnitte.find((a) => a.schluessel === "interessen")!.liste)).toEqual(["t1"]);
  });
  it("Gleichstand der Bezüge: zuletzt gemerkt gewinnt", () => {
    const g1 = ev({ id: "g1", datum: "2026-11-01", ort: "zakk", titel: "Früher gemerkt" });
    const g2 = ev({ id: "g2", datum: "2026-11-02", ort: "Tonhalle", titel: "Später gemerkt" });
    const events = [
      ev({ id: "z", datum: "2026-11-25", ort: "zakk", kategorie: "musik" }),
      ev({ id: "t", datum: "2026-11-26", ort: "Tonhalle", kategorie: "musik" }),
    ];
    const e = eingabe(events, {
      interessen: { kategorien: ["musik"] },
      merkliste: [gemerkt(g1, "2026-11-01T10:00:00Z"), gemerkt(g2, "2026-11-05T10:00:00Z")],
    });
    const r = fuerDichSeite(e);
    if (r.art !== "abschnitte") throw new Error("erwartet Abschnitte");
    expect(r.abschnitte.find((a) => a.schluessel === "gemerkt")!.titel).toBe("Weil du ‚Später gemerkt‘ gemerkt hast");
  });
  it("sensibles gemerktes Event erzeugt keinen Abschnitt „Weil du … gemerkt hast“", () => {
    const g = ev({ id: "g", datum: "2026-11-01", ort: "zakk", titel: "Heikles Event" });
    const events = [ev({ id: "z", datum: "2026-11-25", ort: "zakk", kategorie: "musik" })];
    const r = fuerDichSeite(eingabe(events, { interessen: { kategorien: ["musik"] }, merkliste: [gemerkt(g)], sensibel: new Set(["g"]) }));
    if (r.art !== "abschnitte") throw new Error("erwartet Abschnitte");
    expect(r.abschnitte.map((a) => a.schluessel)).not.toContain("gemerkt");
    expect(JSON.stringify(r)).not.toContain("Heikles");
  });
  it("Deckel je Abschnitt bis zur Obergrenze, leere Seite ohne Ersatz", () => {
    const viele = Array.from({ length: 10 }, (_, n) => ev({ id: `h${n}`, datum: HEUTE, ort: `Ort ${n}`, kategorie: n % 2 ? "musik" : "kultur", unterkategorie: null }));
    const e = eingabe(viele, { interessen: { kategorien: ["musik", "kultur"] } });
    const r = fuerDichSeite(e);
    if (r.art !== "abschnitte") throw new Error("erwartet Abschnitte");
    expect(r.abschnitte[0].liste.length).toBeLessThanOrEqual(ABSCHNITT_MAX);
    expect(r.abschnitte[0].liste.length).toBe(4); // je Kategorie 2
    const leer = fuerDichSeite(eingabe(viele, { interessen: { kategorien: ["sport"] } }));
    expect(leer).toEqual({ art: "abschnitte", abschnitte: [] });
  });
});
