// Spielplatz-Guide (Plan docs/plan-spielplaetze-2026-11-12.md, Abschnitt 7 „Web“): reine Funktionen ohne Netz
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { GUIDE_TEXTE } from "@/lib/guide-texte";
import { hubPasstZuEvent } from "@/lib/landing";
import {
  CHIP_SCHWELLE, EXTRAS, GERAETE, STANDARD, chips, erfasst, extraBelegt, extraJa, filterHref, filterLesen, filtern, geraetBelegt, geraetJa, groesseText,
  hatParameter, istIndexierbar, namensStamm, nachbarn, ortStadtteilSlug, saisonHinweis, sortieren, spielplatzTitel,
  type SpielplatzDaten,
} from "@/lib/spielplaetze";
import { kostenlos, spielplatzJsonLd, spielplaetzeListeJsonLd } from "@/lib/spielplaetze-json-ld";
import { spielplatzKartenOrte } from "@/lib/spielplaetze-karte";
import type { DddOrt } from "@/lib/typen";

let n = 0;
function sp(daten: SpielplatzDaten, mehr: Partial<DddOrt> = {}): DddOrt {
  n += 1;
  return {
    id: `id-${n}`, name: `Spielplatz ${n}`, slug: `spielplatz-${n}`, typ: "spielplatz", untertitel: null, beschreibung: null,
    highlight: null, adresse: null, stadtteil: "Bilk", latitude: 51.2, longitude: 6.78, bild_url: null, bild_attribution: null,
    tags: [], preis_niveau: null, oeffnungszeiten: null, webseite: null, telefon: null, instagram: null, google_place_id: null,
    google_rating: null, google_bewertungen_anzahl: null, qualitaets_score: null, extras: { spielplatz: daten }, sortierung: 0,
    erstellt_am: null, aktualisiert_am: null, ...mehr,
  };
}
const ja = (quelle = "osm") => ({ wert: "ja" as const, quelle, beleg: "Beleg" });

describe("Indexierbarkeit (gemeinsame Fixture mit pytest)", () => {
  const faelle = JSON.parse(readFileSync(join(__dirname, "..", "..", "tests", "fixtures", "spielplatz_indexierbar.json"), "utf-8")) as
    { fall: string; erwartet: boolean; spielplatz: SpielplatzDaten }[];
  it.each(faelle.map((f) => [f.fall, f] as const))("%s", (_, f) => {
    expect(istIndexierbar(f.spielplatz)).toBe(f.erwartet);
  });
  it("Profil-Geräte mit Beleg zählen ohne OSM-Treffer; vermutetes Alter + 1 Gerät reicht nicht", () => {
    expect(istIndexierbar({ beschreibung: "x", ausstattung: { rutsche: ja("zitat"), schaukel: ja("zitat") } })).toBe(true);
    expect(istIndexierbar({ beschreibung: "x", alter: { wert: "3-6", art: "vermutlich" }, ausstattung: { rutsche: ja() } })).toBe(false);
    expect(istIndexierbar({ beschreibung: "x", alter: { wert: "3-6", art: "vermutlich" }, ausstattung: { rutsche: ja(), schaukel: ja() } })).toBe(true);
  });
});

describe("Filter", () => {
  const a = sp({ alter: { wert: "0-3", art: "belegt" }, ausstattung: { sandkasten: ja(), schaukel: ja() }, typ: "kinder" });
  const b = sp({ alter: { wert: "alle", art: "belegt" }, ausstattung: { sandkasten: ja() }, typ: "wasser" });
  const c = sp({ ausstattung: { schaukel: ja() }, typ: "abenteuer" }, { stadtteil: "Hafen" });
  const d = sp({ alter: { wert: "6-12", art: "vermutlich" }, typ: "wald", extras: { rollstuhl: { wert: "teilweise", quelle: "osm", beleg: "limited" } } });
  const alle = [a, b, c, d];
  const f = (x: Partial<typeof STANDARD>) => filtern(alle, { ...STANDARD, ...x }, ortStadtteilSlug).map((o) => o.id);

  it("Alter: „alle“ passt zu jedem Alter, unbekanntes nur ohne Altersfilter", () => {
    expect(f({ alter: "0-3" })).toEqual([a.id, b.id]);
    expect(f({ alter: "6-12" })).toEqual([b.id, d.id]);
    expect(f({ alter: null })).toEqual(alle.map((o) => o.id));
  });
  it("Geräte UND, nur „ja“", () => {
    expect(f({ geraete: ["sandkasten"] })).toEqual([a.id, b.id]);
    expect(f({ geraete: ["sandkasten", "schaukel"] })).toEqual([a.id]);
  });
  it("Typ ODER inklusive Abenteuer; Stadtteil über den Anzeige-Slug (Hafen → medienhafen)", () => {
    expect(f({ typen: ["wasser", "abenteuer"] })).toEqual([b.id, c.id]);
    expect(f({ stadtteile: ["medienhafen"] })).toEqual([c.id]);
  });
  it("Rollstuhl „teilweise“ (OSM limited) zählt nicht als Extra", () => {
    expect(extraJa(d, "rollstuhl")).toBe(false);
    expect(f({ extras: ["rollstuhl"] })).toEqual([]);
  });
  it("„X von Y erfasst“ und Sortierung zählen nur belegte Geräte (Quelle und Beleg)", () => {
    expect(erfasst(alle)).toBe(3);
    const ohneBeleg = sp({ ausstattung: { rutsche: { wert: "ja", quelle: "osm" }, schaukel: { wert: "ja", quelle: "profil", beleg: "x" } } });
    expect(geraetJa(ohneBeleg, "rutsche")).toBe(true); // Filter bleibt bei „ja“
    expect(geraetBelegt(ohneBeleg, "rutsche")).toBe(false);
    expect(erfasst([ohneBeleg])).toBe(0);
    expect(sortieren([ohneBeleg, c], "ausstattung")[0].id).toBe(c.id);
  });
  it("Chip-Schwelle 5: 4 Plätze → kein Chip, 5 → Chip, aktive Chips bleiben", () => {
    const vier = [1, 2, 3, 4].map(() => sp({ ausstattung: { rutsche: ja() } }));
    expect(CHIP_SCHWELLE).toBe(5);
    expect(chips(vier, GERAETE, geraetJa, []).map((c) => c.wert)).not.toContain("rutsche");
    expect(chips(vier, GERAETE, geraetJa, ["rutsche"]).map((c) => c.wert)).toContain("rutsche");
    expect(chips([...vier, sp({ ausstattung: { rutsche: ja() } })], GERAETE, geraetJa, []).map((c) => c.wert)).toContain("rutsche");
    expect(chips(vier, EXTRAS, extraJa, []).length).toBe(0);
    // Schwelle über Belege: fünf „ja“ ohne Beleg → kein Chip; die Zahl am Chip zählt wie der Filter
    const ohneBeleg = [1, 2, 3, 4, 5].map(() => sp({ ausstattung: { seilbahn: { wert: "ja", quelle: "osm" } } }));
    expect(chips(ohneBeleg, GERAETE, geraetJa, [], geraetBelegt).map((c) => c.wert)).not.toContain("seilbahn");
    const fuenfte = sp({ ausstattung: { rutsche: ja() } });
    const unbelegt = sp({ ausstattung: { rutsche: { wert: "ja" } } });
    const gemischt = chips([...vier, fuenfte, unbelegt], GERAETE, geraetJa, [], geraetBelegt).find((c) => c.wert === "rutsche");
    expect(gemischt?.anzahl).toBe(6);
    expect(gemischt?.belegt).toBe(5);
    const extras = [1, 2, 3, 4, 5].map(() => sp({ extras: { wc: { wert: "ja", quelle: "zitat", beleg: "Toilette" } } }));
    expect(chips(extras, EXTRAS, extraJa, [], extraBelegt).map((c) => c.wert)).toEqual(["wc"]);
  });
  it("URL-Parameter: lesen, schreiben, noindex-Erkennung; „In der Nähe“ ist kein Parameter", () => {
    const gelesen = filterLesen({ alter: "3-6", geraet: "rutsche,quatsch", typ: "wasser", stadtteil: "bilk", sort: "ausstattung", naehe: "1" });
    expect(gelesen).toEqual({ alter: "3-6", geraete: ["rutsche"], extras: [], typen: ["wasser"], stadtteile: ["bilk"], sort: "ausstattung" });
    expect(filterHref("/guides/spielplaetze", gelesen, { alter: null })).toBe("/guides/spielplaetze?geraet=rutsche&typ=wasser&stadtteil=bilk&sort=ausstattung");
    expect(hatParameter({ typ: "wald" })).toBe(true);
    expect(hatParameter({ naehe: "1" })).toBe(false);
  });
  it("Sortierung „Beste Ausstattung“ nach Anzahl der Geräte", () => {
    expect(sortieren(alle, "ausstattung")[0].id).toBe(a.id);
  });
});

describe("Titel, Nähe, Saison, Größe", () => {
  it("Titel „{Name} {inStadtteil}“ ohne Gedankenstrich", () => {
    expect(spielplatzTitel(sp({}, { name: "Wasserspielplatz Volksgarten", stadtteil: "Oberbilk" }))).toBe("Wasserspielplatz Volksgarten in Oberbilk");
    expect(spielplatzTitel(sp({}, { name: "Spielplatz X", stadtteil: "Altstadt" }))).toBe("Spielplatz X in der Altstadt");
  });
  it("Namensstamm ohne Typwort und Klammer; Gruppe bei gleichem Stamm, sonst die drei nächsten", () => {
    expect(namensStamm("Spielplatz Hanielpark (an der Rollerbahn)")).toBe("hanielpark");
    const w = sp({}, { name: "Wasserspielplatz Volksgarten" });
    const s = sp({}, { name: "Spielplatz Volksgarten (Mitte)" });
    const fern = [1, 2, 3, 4].map((i) => sp({}, { name: `Spielplatz Weg ${i}`, latitude: 51.2 + i / 100 }));
    const gruppe = nachbarn(w, [w, s, ...fern]);
    expect(gruppe.titel).toBe("Weitere Spielplätze: Volksgarten");
    expect(gruppe.orte.map((x) => x.o.id)).toEqual([s.id]);
    const ohne = nachbarn(fern[0], [w, s, ...fern]);
    expect(ohne.titel).toBe("Weitere Spielplätze in der Nähe");
    expect(ohne.orte).toHaveLength(3);
  });
  it("Saison: Wasserbereich, wenn eine Kinder-Teilfläche größer ist, sonst nur bei Typ Wasser; immer mit Text", () => {
    const saison = { text: "Mai bis September" };
    const teil = (objektart: string, groesse_m2: number) => ({ objektschluessel: objektart, stadt_name: "x", objektart, groesse_m2 });
    // Typ Wasser ohne größere Kinderfläche → ganzer Platz
    expect(saisonHinweis({ typ: "wasser", saison })).toEqual({ text: "Mai bis September", label: "Saison" });
    expect(saisonHinweis({ typ: "wasser", saison, teile: [teil("72 Wasserspielplatz", 900), teil("71 Kinderspielplatz", 300)] }))
      .toEqual({ text: "Mai bis September", label: "Saison" });
    // Größere Kinderfläche → nur der Wasserbereich, auch wenn der Platz als Wasserplatz geführt wird
    expect(saisonHinweis({ typ: "wasser", saison, teile: [teil("72 Wasserspielplatz", 300), teil("71 Kinderspielplatz", 900)] }))
      .toEqual({ text: "Mai bis September", label: "Saison des Wasserbereichs" });
    expect(saisonHinweis({ typ: "kinder", saison, teile: [teil("72 Wasserspielplatz", 300), teil("71 Kinderspielplatz", 900)] }))
      .toEqual({ text: "Mai bis September", label: "Saison des Wasserbereichs" });
    // Kinderplatz mit Wasserspiel, aber ohne Wasser-Teilfläche → kein Hinweis
    expect(saisonHinweis({ typ: "kinder", saison, ausstattung: { wasserspiel: ja() } })).toBeNull();
    expect(saisonHinweis({ typ: "wasser" })).toBeNull();
  });
  it("Größe gerundet „laut Stadt“", () => {
    expect(groesseText({ groesse_m2: 1234 })).toBe("ca. 1.200 m² laut Stadt");
    expect(groesseText({ groesse_m2: null })).toBeNull();
  });
});

describe("Karte und JSON-LD ohne Bewertung", () => {
  it("Kartenpunkte ohne Bewertung und ohne OSM-Tags", () => {
    const o = sp({ alter: { wert: "3-6", art: "vermutlich" }, osm: { id: "way/1" }, score: 8.4, ausstattung: { rutsche: ja() } }, { google_rating: 4.6 });
    const [p] = spielplatzKartenOrte([o]);
    expect(p.rating).toBeNull();
    expect(p.anzahl).toBeNull();
    expect(p.alter).toBe("3-6");
    expect(p.alterLabel).toBe("vermutlich 3–6 Jahre");
    expect(JSON.stringify(p)).not.toMatch(/way\/1|8\.4|4\.6|osm/);
  });
  it("Playground ohne aggregateRating; isAccessibleForFree nach Quelle", () => {
    const o = sp({ beschreibung: "x" }, { google_rating: 4.6, google_bewertungen_anzahl: 20, adresse: "Brehmstraße 30, 40239 Düsseldorf" });
    const ld = spielplatzJsonLd(o, "https://x.de");
    expect(ld["@type"]).toBe("Playground");
    expect(JSON.stringify(ld)).not.toContain("aggregateRating");
    expect(ld.isAccessibleForFree).toBe(true);
    expect(kostenlos({})).toBe(true);
    expect(kostenlos({ eintritt: "ja" })).toBe(false);
    expect(kostenlos({ quelle: "abenteuer", eintritt: "ja" })).toBe(false);
    expect(kostenlos({ quelle: "abenteuer", eintritt: "nein" })).toBe(true);
    expect(kostenlos({ quelle: "abenteuer", eintritt: null })).toBeUndefined();
  });
  it("ItemList nur mit indexierbaren Plätzen, höchstens 30", () => {
    const gut = Array.from({ length: 35 }, () => sp({ beschreibung: "x", ausstattung: { rutsche: ja(), schaukel: ja() } }));
    const duenn = sp({ beschreibung: "x" });
    const [, liste] = spielplaetzeListeJsonLd([duenn, ...gut], "https://x.de");
    expect(liste.numberOfItems).toBe(30);
    expect(JSON.stringify(liste)).not.toContain(duenn.slug + '"');
  });
});

describe("Einbaustellen und Texte", () => {
  it("Event-Link „Spielplätze …“ nur bei Kategorie Familie", () => {
    expect(hubPasstZuEvent("spielplaetze", "familie")).toBe(true);
    expect(hubPasstZuEvent("spielplaetze", "musik")).toBe(false);
    expect(hubPasstZuEvent("clubs", "musik")).toBe(true);
  });
  it("Fünf FAQs, keine Score-Zahl, Ansprache ihr/euch", () => {
    const t = GUIDE_TEXTE.spielplaetze;
    expect(t.faq).toHaveLength(5);
    // 6.2: jede Antwort mit mindestens einem internen Link
    for (const f of t.faq) expect(f.antwort, f.frage).toMatch(/\]\(\/[^)\s]+\)/);
    const alles = JSON.stringify(t);
    expect(alles).not.toMatch(/score|punkte|\/10\b/i);
    // „Sie“ kommt als 3. Person Plural vor („Sie sind oft aus Holz“) – geprüft werden Du- und Höflichkeitsformen
    expect(alles).not.toMatch(/\b(du|dich|dir|dein\w*|Ihnen|Ihre[mnrs]?)\b/);
    expect(alles).toMatch(/\bihr\b/);
    expect(t.einleitung).toContain("{anzahl}");
  });
});
