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
    const erlaubt = /^\/(guides(\/(restaurants-cafes|kneipen-bars|clubs)(\/stadtteil)?(\/[a-z0-9-]+)?)?|heute|wochenende|entdecken|stadtteile|kategorie\/[a-z-]+)$/;
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

  it("Platzhalter und FAQ-JSON-LD", () => {
    expect(textFuellen("{anzahl} Clubs", { anzahl: "35" })).toBe("35 Clubs");
    const ld = faqJsonLd([{ frage: "F?", antwort: "Siehe [Clubs](/guides/clubs)." }]);
    expect(ld["@type"]).toBe("FAQPage");
    expect(JSON.stringify(ld)).toContain('"text":"Siehe Clubs."');
    // In den Antworten bleiben keine Platzhalter übrig (Zahlen nur in Einleitungen)
    for (const s of SEITEN) for (const f of GUIDE_TEXTE[s].faq) expect(f.antwort + f.frage).not.toMatch(/\{\w+\}/);
  });
});
