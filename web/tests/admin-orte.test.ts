// Tests zu Stufe 3a (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.7): Stammdaten, Texte, öffentlicher Pfad
import { describe, expect, it, vi } from "vitest";
import { aenderungen, oeffentlicherPfad, ortKopf, stammdatenPruefen, STADTTEILE, textPruefen } from "@/lib/admin/orte";

const QUELLE = "https://de.wikipedia.org/wiki/Capitol_Theater_(Düsseldorf)";
const TEXT = "Das **Capitol Theater** ist eine Bühne für Musicals und Shows. ".repeat(5);

describe("Stammdaten", () => {
  it("Whitelist, leere Texte werden NULL, Namen nie leer", () => {
    expect(stammdatenPruefen({ adresse: "  ", name: " Zakk " }, "club")).toEqual({ ok: true, felder: { adresse: null, name: "Zakk" } });
    expect(stammdatenPruefen({ name: "" }, "club").ok).toBe(false);
    expect(stammdatenPruefen({ slug: "neu" }, "club").ok).toBe(false);
    expect(stammdatenPruefen({ typ: "kneipe" }, "club").ok).toBe(false);
    expect(stammdatenPruefen({ qualitaets_score: 9 }, "club").ok).toBe(false);
  });

  it("aktiv nur einschalten, Abschalten läuft über Schließen", () => {
    expect(stammdatenPruefen({ aktiv: true }, "club")).toEqual({ ok: true, felder: { aktiv: true } });
    expect(stammdatenPruefen({ aktiv: false }, "club").ok).toBe(false);
  });

  it("Geo im Rahmen, mit Komma, nur zusammen", () => {
    expect(stammdatenPruefen({ latitude: "51,2277", longitude: "6.7735" }, "club")).toEqual({ ok: true, felder: { latitude: 51.2277, longitude: 6.7735 } });
    expect(stammdatenPruefen({ latitude: "6.77", longitude: "51.22" }, "club").ok).toBe(false); // vertauscht
    expect(stammdatenPruefen({ latitude: "51.2" }, "club").ok).toBe(false);
    expect(stammdatenPruefen({ latitude: "", longitude: "6.77" }, "club").ok).toBe(false);
    expect(stammdatenPruefen({ latitude: "", longitude: "" }, "club")).toEqual({ ok: true, felder: { latitude: null, longitude: null } });
  });

  it("Beschreibung einer Spielstätte nur über die Text-Freigabe", () => {
    expect(stammdatenPruefen({ beschreibung: "neu" }, "spielstaette").ok).toBe(false);
    expect(stammdatenPruefen({ beschreibung: "neu" }, "restaurant").ok).toBe(true);
  });

  it("Website, Preisniveau, Sortierung", () => {
    expect(stammdatenPruefen({ webseite: "zakk.de" }, "club").ok).toBe(false);
    expect(stammdatenPruefen({ preis_niveau: "€€€€" }, "restaurant").ok).toBe(false);
    expect(stammdatenPruefen({ preis_niveau: "" }, "restaurant")).toEqual({ ok: true, felder: { preis_niveau: null } });
    expect(stammdatenPruefen({ sortierung: "2.5" }, "club").ok).toBe(false);
  });

  it("nur echte Änderungen", () => {
    expect(aenderungen({ name: "A", adresse: null, latitude: 51.2 }, { name: "A", adresse: null, latitude: 51.3 })).toEqual({ latitude: 51.3 });
  });

  it("Stadtteil-Vorschläge enthalten die Bezirke", () => {
    expect(STADTTEILE).toContain("Flingern-Nord");
    expect(STADTTEILE).toContain("Hafen");
  });
});

describe("Text der Ortsseite", () => {
  it("Länge und Quellen wie admin_ort_text_speichern", () => {
    expect(textPruefen("kurz", [], false).ok).toBe(false);
    expect(textPruefen(TEXT, "", false)).toEqual({ ok: true, text: TEXT.trim(), quellen: [] });
    expect(textPruefen(TEXT, "", true).ok).toBe(false); // Freigabe braucht eine Quelle
    expect(textPruefen(TEXT, `${QUELLE}\n\n  http://unsicher.de `, true)).toEqual({ ok: false, fehler: "Quelle muss mit https:// beginnen: http://unsicher.de" });
    expect(textPruefen(TEXT, `${QUELLE}\r\n`, true)).toEqual({ ok: true, text: TEXT.trim(), quellen: [QUELLE] });
  });
});

describe("Öffentlicher Pfad (wie der Proxy)", () => {
  const kopf = (typ: string, aktiv: boolean, score: number | null, extras: Record<string, unknown> = {}) =>
    ortKopf({ typ, aktiv, qualitaets_score: score, extras_kopf: extras });

  it("Spielstätte unter /orte, nur aktiv", () => {
    expect(oeffentlicherPfad("capitol-theater", kopf("spielstaette", true, null))).toBe("/orte/capitol-theater");
    expect(oeffentlicherPfad("capitol-theater", kopf("spielstaette", false, null))).toBeNull();
  });

  it("Guides: Score-Schwelle, Spielplatz und Weihnachtsmarkt", () => {
    expect(oeffentlicherPfad("x", kopf("restaurant", true, 8))).toBe("/guides/restaurants-cafes/x");
    expect(oeffentlicherPfad("x", kopf("restaurant", true, 5))).toBeNull();
    expect(oeffentlicherPfad("x", kopf("spielplatz", true, null))).toBe("/guides/spielplaetze/x");
    expect(oeffentlicherPfad("x", kopf("weihnachtsmarkt", false, null))).toBeNull();
    expect(oeffentlicherPfad("x", kopf("ausflug", true, 9))).toBeNull();
  });
});

describe("Nachträge Cursor-Prüfung Stufe 3a", () => {
  it("Spielplatz und Weihnachtsmarkt nicht über das Aktiv-Häkchen freischalten (Befund 2)", () => {
    expect(stammdatenPruefen({ aktiv: true }, "spielplatz").ok).toBe(false);
    expect(stammdatenPruefen({ aktiv: true }, "weihnachtsmarkt").ok).toBe(false);
    expect(stammdatenPruefen({ telefon: "0211 1234" }, "weihnachtsmarkt").ok).toBe(true);
  });

  it("Proxy vergisst gemerkte Orte nach einer Änderung im Admin-Bereich (Befund 1)", async () => {
    const { pfadPruefen, speicherLeeren, orteZwischenspeicherVerwerfen } = await import("@/lib/pfad-pruefung");
    speicherLeeren();
    const alt = { url: process.env.SUPABASE_URL, key: process.env.SUPABASE_KEY };
    process.env.SUPABASE_URL = "https://test.supabase.co";
    process.env.SUPABASE_KEY = "test";
    let aktiv = true;
    vi.stubGlobal("fetch", async (url: string) => {
      if (url.includes("/orte?") && url.includes("slug=eq.capitol-theater")) {
        // anon sieht nur aktive Zeilen
        return new Response(aktiv ? '[{"typ":"spielstaette","aktiv":true,"qualitaets_score":null}]' : "[]", { status: 200 });
      }
      if (url.includes("/ort_weiterleitungen?")) return new Response('[{"ziel_ort_id":null}]', { status: 200 });
      return new Response("[]", { status: 200 });
    });
    try {
      expect(await pfadPruefen("/orte/capitol-theater")).toEqual({ art: "weiter" });
      aktiv = false; // im Admin geschlossen
      expect(await pfadPruefen("/orte/capitol-theater")).toEqual({ art: "weiter" }); // noch gemerkt
      await new Promise((r) => setTimeout(r, 2));
      orteZwischenspeicherVerwerfen();
      await new Promise((r) => setTimeout(r, 2));
      expect(await pfadPruefen("/orte/capitol-theater")).toEqual({ art: "umleiten", ziel: "/orte" });
    } finally {
      vi.unstubAllGlobals();
      for (const [k, v] of [["SUPABASE_URL", alt.url], ["SUPABASE_KEY", alt.key]] as const) {
        if (v === undefined) delete process.env[k];
        else process.env[k] = v;
      }
      speicherLeeren();
    }
  });
});
