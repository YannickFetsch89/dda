// Event-Tipps der Geburtstagsmail (Plan docs/plan-geburtstagsmail-2026-11-20.md, G2). Rein und getestet.
// Mit Einwilligung (a): persönliche Vorschläge für den Tag (lib/fuer-dich, Fenster „tag“, inklusive Ersatz „Beliebt“).
// Ohne (a) oder ohne Treffer: Tipp und Picks des Tages wie auf der Startseite. Nie sensible, abgesagte oder gemerkte.
import { filtern, startPlaetze, uhrzeitenVon, type StufenKontext } from "../ableitungen";
import { startVorschlaege, type Eingabe } from "../fuer-dich";
import { eventPfad } from "../pfade";
import { anzeigeTitel } from "../termine";
import type { DddEvent } from "../typen";

export const TIPPS_MAX = 3;

export interface Tipp {
  titel: string;
  ort: string;
  /** Erste Anfangszeit HH:MM oder null (ganztägig, ohne Zeit) */
  uhrzeit: string | null;
  /** Pfad auf diesdas.events, ohne Domain */
  pfad: string;
}

/** Tipp und Picks des Tages (wie die Startseite), ohne abgesagte und sensible Events. */
export function allgemeineTipps(events: DddEvent[], stufen: StufenKontext, heute: string, sensibel: ReadonlySet<string>): DddEvent[] {
  const { tipp, picks } = startPlaetze(filtern(events, { von: heute, bis: heute, mitLanglaeufern: true }), stufen, heute);
  return [tipp, ...picks].filter((e): e is DddEvent => !!e && !e.abgesagt && !sensibel.has(e.id));
}

/**
 * Bis zu drei Tipps für eine Person am Tag `e.heute`. `gemerkt`: IDs der eigenen Konto-Merkliste (fallen immer raus,
 * auch ohne Einwilligung (a) – die Merkliste ist Vertrag, nicht Personalisierung).
 */
export function tippsFuerNutzer(e: Eingabe, gemerkt: ReadonlySet<string>, allgemein: DddEvent[]): DddEvent[] {
  if (e.personalisierung) {
    const r = startVorschlaege(e, { von: e.heute, bis: e.heute, fokus: "tag" });
    if (r.art === "persoenlich") return r.liste.map((v) => v.event).slice(0, TIPPS_MAX);
    if (r.art === "ersatz") return r.liste.slice(0, TIPPS_MAX);
  }
  return allgemein.filter((ev) => !gemerkt.has(ev.id) && !e.sensibel.has(ev.id)).slice(0, TIPPS_MAX);
}

/** Nur die Felder, die die Mail braucht – keine Kategorie-Punkte, keine Begründung, keine IDs der Merkliste. */
export function tippAusgabe(ev: DddEvent): Tipp {
  return {
    titel: anzeigeTitel(ev.titel, ev.ort),
    ort: ev.ort,
    uhrzeit: uhrzeitenVon(ev)[0] ?? null,
    pfad: eventPfad(ev),
  };
}
