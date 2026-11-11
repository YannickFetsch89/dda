// SEO-/GEO-Plan Nov. 2026, Phase C: Anzeige-Titel (Maßnahme 9)
import { describe, expect, it } from "vitest";
import { anzeigeTitel, basisTitel } from "@/lib/termine";

describe("Anzeige-Titel", () => {
  it("„Düsseldorf“ am Ende fällt weg, am Anfang bleibt es", () => {
    expect(anzeigeTitel("The Pogues in Düsseldorf")).toBe("The Pogues");
    expect(anzeigeTitel("Blueprint - Comedy & Cocktails (Open Mic) | Düsseldorf")).toBe("Blueprint - Comedy & Cocktails (Open Mic)");
    expect(anzeigeTitel("SELIG /// The EPIC Years - Tour 2026 /// Düsseldorf")).toBe("SELIG /// The EPIC Years - Tour 2026");
    expect(anzeigeTitel("Düsseldorf – Christmas Market Single Walk ❄️❤️")).toBe("Düsseldorf – Christmas Market Single Walk");
  });

  it("einzelnes Datum am Ende fällt weg, Zeiträume bleiben", () => {
    expect(anzeigeTitel("Morgenandacht 15.11.2026")).toBe("Morgenandacht");
    expect(anzeigeTitel("Öffentliche Führung (Religion) Di 01.12.2026")).toBe("Öffentliche Führung (Religion)");
    expect(anzeigeTitel("Max Mutzke • Live Tour 2026 • 14.11.26 Düsseldorf")).toBe("Max Mutzke • Live Tour 2026");
    expect(anzeigeTitel("Zazen-Wochenende (Rinzai-Zen-Schule) 13.11.-15.11.2026")).toBe("Zazen-Wochenende (Rinzai-Zen-Schule) 13.11.-15.11.2026");
  });

  it("Ortsanhang fällt weg, wenn er zum Ort passt", () => {
    expect(anzeigeTitel("DISCOTECA - The Paradise Now", "The Paradise Now")).toBe("DISCOTECA");
    expect(
      anzeigeTitel("SOTTO LE NUVOLE · POMPEJI: UNTER DEN WOLKEN | Italienischer Filmclub - Black Box im Filmmuseum Düsseldorf", "Black Box im Filmmuseum"),
    ).toBe("SOTTO LE NUVOLE · POMPEJI: UNTER DEN WOLKEN | Italienischer Filmclub");
    // Anhang nur ein Teil des Ortsnamens: bleibt („Halle“ steckt in „Tonhalle“, ist aber nicht der Ort)
    expect(anzeigeTitel("Konzert - Halle", "Tonhalle")).toBe("Konzert - Halle");
    // Anderer Anhang bleibt
    expect(anzeigeTitel("Romeo und Julia - Schauspiel nach Shakespeare", "Schauspielhaus")).toBe("Romeo und Julia - Schauspiel nach Shakespeare");
  });

  it("Emojis am Rand, doppelte Trenner und Leerzeichen", () => {
    expect(anzeigeTitel("☕ Casual Conversation - All Welcome")).toBe("Casual Conversation - All Welcome");
    expect(anzeigeTitel("🎄The Coterie goes to the Christmas market 🎄")).toBe("The Coterie goes to the Christmas market");
    expect(anzeigeTitel("MTV´s UNPLUGGED NIRVANA by SMELLS LIKE NIRVANA - - SUNDAY MATINEE -")).toBe("MTV´s UNPLUGGED NIRVANA by SMELLS LIKE NIRVANA - SUNDAY MATINEE");
    expect(anzeigeTitel("UNIKATE. Kunst  Handwerk  Design 2026")).toBe("UNIKATE. Kunst Handwerk Design 2026");
  });

  it("Uhrzeit wie bisher, nie leer", () => {
    expect(anzeigeTitel("Führung (14:00 Uhr)")).toBe(basisTitel("Führung (14:00 Uhr)"));
    expect(anzeigeTitel("Düsseldorf")).toBe("Düsseldorf");
    expect(anzeigeTitel("🎉")).toBe("🎉");
  });
});

describe("Guide-Stadtteile kanonisch", () => {
  it("Rohwerte werden wie im Proxy aufgelöst, unbekannte fallen weg", async () => {
    const { kanonischerStadtteil } = await import("@/lib/landing");
    const { orteImStadtteil, stadtteileMitOrten } = await import("@/lib/guide-stadtteile");
    expect(kanonischerStadtteil("Medienhafen")).toBe("Hafen");
    expect(kanonischerStadtteil("Hafen")).toBe("Hafen");
    expect(kanonischerStadtteil("Neuss")).toBe("Neuss");
    expect(kanonischerStadtteil("Oberkassel-Süd")).toBeNull();
    const ort = (i: number, stadtteil: string) => ({ id: `o${i}`, stadtteil }) as never;
    const orte = [ort(1, "Hafen"), ort(2, "Medienhafen"), ort(3, "Hafen"), ort(4, "Medienhafen"), ort(5, "Hafen"), ...[6, 7, 8, 9, 10].map((i) => ort(i, "Oberkassel-Süd"))];
    expect(stadtteileMitOrten(orte)).toEqual([{ stadtteil: "Hafen", anzahl: 5 }]); // kein Eintrag für Oberkassel-Süd
    expect(orteImStadtteil(orte, "Hafen")).toHaveLength(5);
  });
});
