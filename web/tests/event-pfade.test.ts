// Event-URLs der Bestätigungsmail an Melder (pipeline/meldung_mail.py) müssen die der Website sein.
// Gemeinsame Prüfliste mit tests/test_meldung_mail.py.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { eventPfadSeo } from "@/lib/admin/seo";
import { eventPfad } from "@/lib/pfade";

const FIXTURE = JSON.parse(readFileSync(join(__dirname, "..", "..", "tests", "fixtures", "event_pfade.json"), "utf-8")) as {
  faelle: { kategorie: string; slug: string | null; id: string; pfad: string }[];
};

describe("Event-Pfade wie in der Melder-Mail", () => {
  for (const f of FIXTURE.faelle) {
    it(`${f.kategorie} / ${f.slug ?? "ohne Slug"} → ${f.pfad}`, () => {
      const pfad = f.slug
        ? eventPfadSeo({ id: f.id, titel: "", datum: "2026-12-05", datum_bis: null, ort: "", kategorie: f.kategorie, slug: f.slug, reihe: null })
        : eventPfad({ id: f.id, kategorie: f.kategorie as never, slug: null });
      expect(pfad).toBe(f.pfad);
    });
  }
});
