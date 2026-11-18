// Fehlertolerante Event-Suche (lib/suche.ts, Auftraggeber 18.11.2026)
import { describe, expect, it } from "vitest";
import { sucheTrifft, suchText, tippAbstand, wortstamm } from "@/lib/suche";

const VEGAN = "Veihnachtsmarkt Düsseldorf: der vegane Weihnachtsmarkt in der Jugendkirche Jugendkirche Düsseldorf";

describe("Event-Suche", () => {
  it("findet die Fälle des Auftraggebers", () => {
    expect(sucheTrifft(VEGAN, "jugendkriche")).toBe(true); // vertauschte Buchstaben
    expect(sucheTrifft(VEGAN, "veihnachten")).toBe(true); // Wortstamm
    expect(sucheTrifft(VEGAN, "Jugendkirche")).toBe(true);
    expect(sucheTrifft(VEGAN, "vegan")).toBe(true);
  });

  it("wortweise: alle Wörter müssen passen, Reihenfolge egal", () => {
    expect(sucheTrifft(VEGAN, "jugendkirche weihnachtsmarkt")).toBe(true);
    expect(sucheTrifft(VEGAN, "weihnachtsmarkt jugendkirche")).toBe(true);
    expect(sucheTrifft(VEGAN, "jugendkirche konzert")).toBe(false);
  });

  it("Umlaute und Schreibweisen", () => {
    expect(sucheTrifft("Brauerei Füchschen", "fuechschen")).toBe(true);
    expect(sucheTrifft("Brauerei Fuechschen", "füchschen")).toBe(true);
    expect(sucheTrifft("Café del Sol", "cafe")).toBe(true);
    expect(suchText("Kö-Bogen")).toBe("koe bogen");
  });

  it("kurze Wörter nur exakt, sonst zu viele Zufallstreffer", () => {
    expect(sucheTrifft("Jazz im Park", "jaz")).toBe(true); // Teilwort
    expect(sucheTrifft("Jazz im Park", "jazs")).toBe(false); // unter 5 Buchstaben kein Tippfehler
    expect(sucheTrifft("Lesung mit Autorin", "konzert")).toBe(false);
  });

  it("Wortanfang mit Tippfehler trifft zusammengesetzte Wörter", () => {
    expect(sucheTrifft("Weihnachtsmarkt am Rathaus", "wihnachts")).toBe(true);
  });

  it("leere Suche passt immer", () => {
    expect(sucheTrifft("irgendwas", "")).toBe(true);
    expect(sucheTrifft("irgendwas", undefined)).toBe(true);
  });

  it("Hilfsfunktionen", () => {
    expect(wortstamm("weihnachten")).toBe("weihnacht");
    expect(wortstamm("kino")).toBe("kino");
    expect(tippAbstand("jugendkriche", "jugendkirche", 2)).toBe(1);
    expect(tippAbstand("konzert", "lesung", 1)).toBe(2);
  });
});
