// Ausblick (Plan docs/plan-quellen-ausbau-2026-11-23.md, 6.1/6.4, Schritt W2): große Events von Tag 61 bis 365.
// Seite /ausblick und Startseiten-Box. Aus dem Fernpool nur Quellen mit Rang 1–2 (Haus, Ticketverkauf) und nur
// Orte mit eigener Ortsseite – keine Kleinst-Events. Die Suche auf /entdecken nutzt den Fernpool ohne diesen Filter.
import { fernPoolLaden } from "./daten";
import { rangGespeichert, TICKETVERKAUF } from "./quellen-rang";
import { spielstaettenLaden } from "./spielstaetten-daten";
import type { DddEvent } from "./typen";

/** Einträge der Startseiten-Box (Q10) */
export const AUSBLICK_BOX = 6;

/** Auswahl für den Ausblick: nicht abgesagt, Rang ≤ 2, Ort mit Ortsseite; nach Datum und Uhrzeit. */
export function ausblickAuswahl(events: DddEvent[], ortIds: ReadonlySet<string>): DddEvent[] {
  return events
    .filter((e) => !e.abgesagt && rangGespeichert(e) <= TICKETVERKAUF && !!e.ort_id && ortIds.has(e.ort_id))
    .sort((a, b) => a.datum.localeCompare(b.datum) || (a.uhrzeit ?? "").localeCompare(b.uhrzeit ?? "") || a.titel.localeCompare(b.titel));
}

/** Kategorien, die im Ausblick vorkommen (für die Filter-Chips), in der Reihenfolge der Häufigkeit. */
export function ausblickKategorien(events: DddEvent[]): { slug: string; anzahl: number }[] {
  const zaehler = new Map<string, number>();
  for (const e of events) zaehler.set(e.kategorie, (zaehler.get(e.kategorie) ?? 0) + 1);
  return [...zaehler].map(([slug, anzahl]) => ({ slug, anzahl })).sort((a, b) => b.anzahl - a.anzahl || a.slug.localeCompare(b.slug));
}

/**
 * Lädt den Ausblick: Fernpool (eigener Cache, bei Fehler leer – nie Beispieldaten) und die aktiven Spielstätten
 * (Orte mit Seite unter /orte). `heute` für Monats-Labels, `letzter` für den Seitentitel („bis <Monat Jahr>“).
 */
export async function ausblickLaden(): Promise<{ heute: string; events: DddEvent[]; letzter: string | null }> {
  const [fern, { orte }] = await Promise.all([fernPoolLaden(), spielstaettenLaden()]);
  const events = ausblickAuswahl(fern.events, new Set(orte.map((o) => o.id)));
  return { heute: fern.heute, events, letzter: events.length ? events[events.length - 1].datum : null };
}
