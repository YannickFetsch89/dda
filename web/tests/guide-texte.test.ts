import { describe, expect, it } from "vitest";
import { GUIDE_TEXTE, faqJsonLd, linkZiele, ohneLinks, textFuellen, type GuideSeite } from "@/lib/guide-texte";

const SEITEN = Object.keys(GUIDE_TEXTE) as GuideSeite[];

describe("Guide-Texte", () => {
  it("jede Seite: Einleitung (2–3 Sätze), längerer Text und genau fünf Fragen", () => {
    for (const s of SEITEN) {
      const t = GUIDE_TEXTE[s];
      const saetze = ohneLinks(t.einleitung).split(/[.!?](?:\s|$)/).filter((x) => x.trim()).length;
      expect(saetze, s).toBeGreaterThanOrEqual(2);
      expect(saetze, s).toBeLessThanOrEqual(3);
      const woerter = t.abschnitte.flatMap((a) => a.absaetze).join(" ").split(/\s+/).length;
      expect(woerter, s).toBeGreaterThan(200);
      expect(t.faq).toHaveLength(5);
    }
  });

  it("Links nur intern und auf bekannte Seitentypen", () => {
    const erlaubt = /^\/(guides(\/(restaurants-cafes|kneipen-bars|clubs|spielplaetze|weihnachtsmaerkte)(\/stadtteil)?(\/[a-z0-9-]+)?)?|guides\/spielplaetze\?(typ=(wasser|wald|abenteuer)|alter=(0-3|3-6|6-12)|extra=[a-z]+)|heute|wochenende|entdecken|stadtteile|kategorie\/[a-z-]+)$/;
    for (const s of SEITEN) for (const z of linkZiele(GUIDE_TEXTE[s])) expect(z, `${s}: ${z}`).toMatch(erlaubt);
  });

  it("jede Seite hat einen eigenen Text (keine gleichen Sätze, keine gleichen Fragen)", () => {
    const gesehen = new Map<string, string>();
    for (const s of SEITEN) {
      const t = GUIDE_TEXTE[s];
      const saetze = [t.einleitung, ...t.abschnitte.flatMap((a) => a.absaetze), ...t.faq.map((f) => f.frage)]
        .flatMap((x) => ohneLinks(x).split(/(?<=[.!?])\s+/)).map((x) => x.trim()).filter((x) => x.length > 30);
      for (const satz of saetze) {
        expect(gesehen.get(satz), `doppelt: ${satz}`).toBeUndefined();
        gesehen.set(satz, s);
      }
    }
  });

  it("erklärt die Club-Einteilung nicht und verlinkt keine Club-Ansicht von Orten mit Haupt-Seite", () => {
    for (const s of SEITEN) {
      const t = GUIDE_TEXTE[s];
      const alles = [t.einleitung, ...t.abschnitte.flatMap((a) => a.absaetze), ...t.faq.flatMap((f) => [f.frage, f.antwort])].join(" ");
      expect(alles, s).not.toMatch(/Stufe|Score|A\/B\/C|Top-Empfehlung/);
    }
    // auch_club-Orte mit sichtbarer Kneipen-/Restaurant-Seite: Club-Ansicht ist noindex → Haupt-URL verlinken
    const MIT_HAUPTSEITE = ["pitcher-flingern", "schlager-cafe-duesseldorf-altstadt"];
    for (const s of SEITEN) for (const z of linkZiele(GUIDE_TEXTE[s])) {
      for (const slug of MIT_HAUPTSEITE) expect(z, `${s}: ${z}`).not.toBe(`/guides/clubs/${slug}`);
    }
  });

  it("Platzhalter und FAQ-JSON-LD", () => {
    expect(textFuellen("{anzahl} Clubs", { anzahl: "35" })).toBe("35 Clubs");
    const ld = faqJsonLd([{ frage: "F?", antwort: "Siehe [Clubs](/guides/clubs)." }]);
    expect(ld["@type"]).toBe("FAQPage");
    expect(JSON.stringify(ld)).toContain('"text":"Siehe Clubs."');
    // In den Antworten bleiben keine Platzhalter übrig (Zahlen nur in Einleitungen). Ausnahme Weihnachtsmärkte
    // (Plan Weihnachtsmärkte 6.2): feste Satzmuster, die Seite füllt sie mit faqWerte() – nur diese Platzhalter erlaubt
    const WM_PLATZHALTER = new Set(["{saison}", "{faq_start}", "{faq_totensonntag}", "{faq_feiertage}", "{faq_eisbahn}", "{faq_familien}"]);
    for (const s of SEITEN) for (const f of GUIDE_TEXTE[s].faq) {
      const rest = s === "weihnachtsmaerkte" ? (f.antwort + f.frage).replace(/\{\w+\}/g, (p) => (WM_PLATZHALTER.has(p) ? "" : p)) : f.antwort + f.frage;
      expect(rest, s).not.toMatch(/\{\w+\}/);
    }
  });
});
