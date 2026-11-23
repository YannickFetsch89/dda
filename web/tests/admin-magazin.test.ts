// Tests zu Stufe 2 (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.6): Redaktionsplan, Eingaben, Prüfung nach Bearbeitung
import { describe, expect, it } from "vitest";
import { magazinEingabe, redaktionsplan, type ListenBeitrag } from "@/lib/admin/magazin";
import { eingebetteteEvents, linkErlaubt, magazinPruefen, teilen, type PruefEingabe } from "@/lib/admin/magazin-pruefung";

const E1 = "11111111-1111-4111-8111-111111111111";
const E2 = "22222222-2222-4222-8222-222222222222";

function beitrag(teil: Partial<ListenBeitrag>): ListenBeitrag {
  return {
    id: "b",
    slug: "s",
    rubrik: "wochenvorschau",
    autor_slug: "a",
    titel: "T",
    status: "entwurf",
    gueltig_von: null,
    gueltig_bis: null,
    veroeffentlicht_am: null,
    erstellt_am: "2026-11-20T10:00:00Z",
    pruefung_ergebnis: null,
    ...teil,
  };
}

describe("Redaktionsplan", () => {
  it("Montag dieser Woche ist die erste Wochenvorschau; Ampel nach Status und Entwurfstag", () => {
    const plan = redaktionsplan(
      [
        beitrag({ id: "v", rubrik: "wochenvorschau", gueltig_von: "2026-11-23", status: "veroeffentlicht" }),
        beitrag({ id: "p", rubrik: "wochenvorschau", gueltig_von: "2026-11-30", status: "in_pruefung" }),
      ],
      "2026-11-25", // Mittwoch
    );
    const wochen = plan.filter((t) => t.rubrik === "wochenvorschau");
    expect(wochen.map((t) => t.von)).toEqual(["2026-11-23", "2026-11-30", "2026-12-07", "2026-12-14", "2026-12-21", "2026-12-28"]);
    expect(wochen[0].farbe).toBe("gruen");
    expect(wochen[1].farbe).toBe("gelb");
    expect(wochen[2]).toMatchObject({ entwurfAm: "2026-12-04", farbe: "grau" });
    const monate = plan.filter((t) => t.rubrik === "monats-tipps");
    expect(monate.map((t) => [t.von, t.entwurfAm])).toEqual([["2026-11-01", "2026-10-28"], ["2026-12-01", "2026-11-28"]]);
    expect(monate[0].farbe).toBe("rot"); // laufender Monat ohne Entwurf
  });

  it("verpasster Entwurfstag ohne Beitrag ist rot", () => {
    const plan = redaktionsplan([], "2026-11-29"); // Sonntag: Entwurf für 30.11. war am 27.11.
    expect(plan.find((t) => t.von === "2026-11-30")?.farbe).toBe("rot");
  });
});

describe("Eingaben", () => {
  it("event_ids folgen den Einbettungen im Text; Whitelist; Längen wie die CHECKs", () => {
    const r = magazinEingabe({ inhalt_md: `Text\n\n{{event:${E2}}}\n\n{{event:${E1}}}\n{{event:${E2}}}` });
    expect(r).toEqual({ ok: true, felder: { inhalt_md: expect.any(String), event_ids: [E2, E1] } });
    expect(magazinEingabe({ status: "veroeffentlicht" }).ok).toBe(false);
    expect(magazinEingabe({ teaser: "zu kurz" }).ok).toBe(false);
    expect(magazinEingabe({ kurzfassung: ["a", "b"] }).ok).toBe(false);
    expect(magazinEingabe({ gueltig_von: "2026-12-07", gueltig_bis: "2026-12-01" }).ok).toBe(false);
  });
});

// 630 Wörter Fließtext, damit die Wortgrenze (600–1800) erfüllt ist
const FUELLTEXT = "In Flingern trifft man sich gern an der Ecke. ".repeat(70);

const GUT: PruefEingabe = {
  rubrik: "stadtleben",
  titel: "Ein Abend in Flingern",
  teaser: "Wo es in Flingern abends gemütlich wird: drei Orte, an denen man gut sitzen kann und die Nachbarschaft trifft.",
  kurzfassung: ["Erster Punkt", "Zweiter Punkt", "Dritter Punkt"],
  faq: null,
  inhalt_md: `## Unterwegs\n\nFlingern ist abends lebendig. Mehr im [Guide](/guides/kneipen-bars).\n\n${FUELLTEXT}\n\n{{event:${E1}}}\n`,
  hero_bild: "/fallback/theater-3.webp",
  hero_alt: "Bühne",
  gueltig_von: null,
  gueltig_bis: null,
};
const STATUS = new Map([[E1, { abgelehnt: false, abgesagt: false }]]);

describe("Prüfung nach Bearbeitung (wie pipeline/magazin.py)", () => {
  it("sauberer Beitrag ist grün", () => {
    expect(magazinPruefen(GUT, STATUS)).toEqual({ ergebnis: "gruen", punkte: [] });
  });

  it("Uhrzeit, Preis, Datum im Fließtext, fremder Link, Ich-Form, Clickbait → rot", () => {
    const r = magazinPruefen({ ...GUT, inhalt_md: "Ab 20:00 Uhr für 12 € – ich finde das unglaublich, am 3. Dezember. [x](http://foo.de)" }, STATUS);
    expect(r.ergebnis).toBe("rot");
    const text = r.punkte.join("\n");
    for (const teil of ["(b) Uhrzeit", "(b) Preis", "(b) Datumsangabe", "(c) Link", "(e) Clickbait", "(e) Ich-Form"]) expect(text).toContain(teil);
  });

  it("abgesagtes oder fehlendes Event, fehlendes Bild, Teaserlänge, Hub-Titel → rot", () => {
    const r = magazinPruefen(
      { ...GUT, titel: "Clubs in Düsseldorf: neu", teaser: "kurz", hero_bild: null, inhalt_md: `{{event:${E1}}}\n{{event:${E2}}}` },
      new Map([[E1, { abgelehnt: false, abgesagt: true }]]),
    );
    const text = r.punkte.join("\n");
    expect(text).toContain(`(a) Event ${E1} ist abgesagt`);
    expect(text).toContain(`(a) Event ${E2} existiert nicht`);
    expect(text).toContain("(i) Aufmacherbild fehlt");
    expect(text).toContain("(d) Teaser");
    expect(text).toContain("(h)");
  });

  it("Daten in Überschriften nur im Zeitraum", () => {
    const im = { ...GUT, gueltig_von: "2026-11-23", gueltig_bis: "2026-11-29", inhalt_md: `## Montag, 23. November\n\n${FUELLTEXT}` };
    expect(magazinPruefen(im, STATUS).ergebnis).toBe("gruen");
    const aus = { ...im, inhalt_md: `## Montag, 7. Dezember\n\n${FUELLTEXT}` };
    expect(magazinPruefen(aus, STATUS).punkte.join()).toContain("außerhalb des Zeitraums");
  });

  it("Links und Teilen", () => {
    expect(linkErlaubt("https://x.de")).toBe(true);
    expect(linkErlaubt("mailto:hallo@diesdas.events")).toBe(true);
    expect(linkErlaubt("mailto:jemand@gmail.com")).toBe(false);
    expect(linkErlaubt("/tag/2026-11-28")).toBe(true);
    expect(linkErlaubt("//boese.de")).toBe(false);
    expect(teilen(`## Kopf\n\nText\n{{event:${E1}}}`)).toEqual({ ueberschriften: ["Kopf"], text: "Text" });
    expect(eingebetteteEvents(`{{event:${E1.toUpperCase()}}}`)).toEqual([E1]);
  });
});

describe("Nachträge Cursor-Prüfung Stufe 2", () => {
  it("Wortgrenze gilt für jede Rubrik", () => {
    expect(magazinPruefen({ ...GUT, inhalt_md: "Kurz." }, STATUS).punkte.join()).toContain("(d) Text hat 1 Wörter");
  });
  it("Datum im Titel ohne Zeitraum ist rot", () => {
    expect(magazinPruefen({ ...GUT, titel: "Tipps zum 3. Dezember" }, STATUS).punkte.join()).toContain("kein Zeitraum");
  });
});
