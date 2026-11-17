// Einwilligungstexte: Die Prüfsummen im SQL müssen zum Code passen (Plan 4.4, 16.1). Weicht ein Wortlaut im Code ab,
// ohne dass eine neue Version und ein neues SQL entstanden sind, schlägt dieser Test fehl.
import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { TEXTVERSIONEN } from "@/lib/konto/konfig";
import { GESTUFT, NACHWEIS_TEXT, TEXT } from "@/lib/konto/texte";

const DB = join(__dirname, "..", "..", "database");
const sha = (t: string) => createHash("sha256").update(t, "utf8").digest("hex");

/** Alle Prüfsummen aus allen einwilligungstexte_*.sql (jede Version darf nur einmal vorkommen). */
function pruefsummenAusSql(): Map<string, string> {
  const summen = new Map<string, string>();
  for (const datei of readdirSync(DB).filter((d) => /^einwilligungstexte_.*\.sql$/.test(d))) {
    for (const m of readFileSync(join(DB, datei), "utf8").matchAll(/^-- sha256 (\S+) ([0-9a-f]{64})$/gm)) {
      expect(summen.has(m[1]), `Version ${m[1]} doppelt in den SQL-Dateien`).toBe(false);
      summen.set(m[1], m[2]);
    }
  }
  return summen;
}

describe("Einwilligungstexte", () => {
  const summen = pruefsummenAusSql();

  it.each(Object.keys(NACHWEIS_TEXT) as (keyof typeof NACHWEIS_TEXT)[])("%s: Wortlaut im Code = Fassung im SQL", (art) => {
    const version = TEXTVERSIONEN[art];
    expect(summen.get(version), `keine Prüfsumme für ${version} – SQL neu erzeugen und neue Version vergeben`).toBe(
      sha(NACHWEIS_TEXT[art].text),
    );
  });

  it("gestufte Anzeige: kurz + mehr ergibt genau den Wortlaut, sichtbar höchstens zwei Sätze", () => {
    const quelle = {
      personalisierung: TEXT.personalisierung,
      sensibelErklaerung: TEXT.sensibelErklaerung,
      sensibel: TEXT.sensibel,
      widerspruchErklaerung: TEXT.widerspruchErklaerung,
      geburtstag: TEXT.geburtstag,
    } as const;
    for (const [art, text] of Object.entries(quelle)) {
      const g = GESTUFT[art as keyof typeof GESTUFT];
      expect(g.mehr, art).not.toBe("");
      expect(`${g.kurz} ${g.mehr}`, art).toBe(text);
      expect(g.kurz.split(/(?<=[.!?:])\s+(?=[A-ZÄÖÜ])/).length, art).toBeLessThanOrEqual(2);
    }
    // „Abs. 1 lit. f“ bleibt im ersten Satz
    expect(GESTUFT.widerspruchErklaerung.kurz).toContain("Art. 6 Abs. 1 lit. f DSGVO).");
  });

  it("jede Art hat einen Nachweis-Text", () => {
    expect(Object.keys(NACHWEIS_TEXT).sort()).toEqual(Object.keys(TEXTVERSIONEN).sort());
  });
});
