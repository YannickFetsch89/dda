// Datenauswahl für die laufenden Magazin-Rubriken (Plan docs/plan-redaktion-2026-11-19.md, 4.2 Punkt 1, T11).
// Deterministisch, ohne KI: dieselbe Stufen- und Highlight-Logik wie die Startseite (lib/ableitungen.ts). Die Pipeline
// (Python) ruft sie über die geschützte Route app/api/magazin/auswahl auf.
import "server-only";
import { createHash, timingSafeEqual } from "node:crypto";
import { breite, filtern, highlightsImZeitraum, nachEmpfehlung, stufenKontext } from "./ableitungen";
import { istGueltigerTag, plusTage, wochentag } from "./datum";
import { eventPfad } from "./pfade";
import { norm } from "./termine";
import type { DddEvent, EventPool } from "./typen";

export type AuswahlRubrik = "wochenvorschau" | "monats-tipps";

/** Zeitraum passt zur Rubrik: Wochenvorschau Montag bis Sonntag, Monats-Tipps 1. bis letzter Tag des Monats. */
export function zeitraumPassend(rubrik: string, von: string, bis: string): rubrik is AuswahlRubrik {
  if (!istGueltigerTag(von) || !istGueltigerTag(bis)) return false;
  if (rubrik === "wochenvorschau") return wochentag(von) === 1 && bis === plusTage(von, 6);
  if (rubrik === "monats-tipps") {
    if (!von.endsWith("-01")) return false;
    const [j, m] = von.split("-").map(Number);
    const naechster = m === 12 ? `${j + 1}-01-01` : `${j}-${String(m + 1).padStart(2, "0")}-01`;
    return bis === plusTage(naechster, -1);
  }
  return false;
}

export interface Kandidat {
  id: string;
  titel: string;
  datum: string;
  datum_bis: string | null;
  uhrzeit: string | null;
  ort: string;
  stadtteil: string | null;
  kategorie: string;
  preis: string | null;
  beschreibung: string | null;
  pfad: string;
  stufe: number;
}

export interface Auswahl {
  rubrik: AuswahlRubrik;
  von: string;
  bis: string;
  kandidaten: Kandidat[];
  /** Highlight der Woche (Wochenvorschau) */
  highlight: string | null;
  /** Top-Event des Monats (Monats-Tipps) */
  top: string | null;
}

const MAX_WOCHE = 20;
const MAX_JE_ORT = 3;
const MIN_KATEGORIEN = 4;
const JE_WOCHE_IM_MONAT = 3;
const MAX_MONAT = 15;

function kandidat(e: DddEvent, stufe: number): Kandidat {
  return {
    id: e.id, titel: e.titel, datum: e.datum, datum_bis: e.datum_bis, uhrzeit: e.uhrzeit, ort: e.ort, stadtteil: e.stadtteil,
    kategorie: e.kategorie, preis: e.preis, beschreibung: e.beschreibung, pfad: eventPfad(e), stufe,
  };
}

/** Auswahl nach Rangfolge mit höchstens 3 je Ort; danach mindestens 4 Kategorien durch Tausch (Plan 4.2 Punkt 1). */
function vielfalt(sortiert: DddEvent[], max: number): DddEvent[] {
  const je = new Map<string, number>();
  const gewaehlt: DddEvent[] = [];
  for (const e of sortiert) {
    if (gewaehlt.length >= max) break;
    const ort = norm(e.ort);
    if ((je.get(ort) ?? 0) >= MAX_JE_ORT) continue;
    je.set(ort, (je.get(ort) ?? 0) + 1);
    gewaehlt.push(e);
  }
  const kategorien = () => new Set(gewaehlt.map((e) => e.kategorie));
  for (const e of sortiert) {
    if (kategorien().size >= MIN_KATEGORIEN) break;
    if (gewaehlt.includes(e) || kategorien().has(e.kategorie)) continue;
    // Letztes Event einer mehrfach vertretenen Kategorie ersetzen
    for (let i = gewaehlt.length - 1; i >= 0; i--) {
      if (gewaehlt.filter((x) => x.kategorie === gewaehlt[i].kategorie).length > 1) {
        gewaehlt.splice(i, 1);
        gewaehlt.push(e);
        break;
      }
    }
  }
  return gewaehlt;
}

/** Montage der Kalenderwochen, die den Zeitraum berühren. */
function wochen(von: string, bis: string): { von: string; bis: string }[] {
  const ergebnis: { von: string; bis: string }[] = [];
  let start = plusTage(von, -((wochentag(von) + 6) % 7));
  while (start <= bis) {
    const ende = plusTage(start, 6);
    ergebnis.push({ von: start < von ? von : start, bis: ende > bis ? bis : ende });
    start = plusTage(start, 7);
  }
  return ergebnis;
}

/** Kandidaten einer Ausgabe aus einem Pool von magazinPoolLaden(von, bis). */
export function auswahlRechnen(pool: EventPool, rubrik: AuswahlRubrik, von: string, bis: string): Auswahl {
  const aktiv = pool.events.filter((e) => !e.abgesagt);
  const k = stufenKontext(aktiv, von);
  const vergleich = nachEmpfehlung(k);
  const stufe = (e: DddEvent) => breite(e, k) ?? 0;
  const imZeitraum = (z: { von: string; bis: string }) => filtern(aktiv, { ...z, mitLanglaeufern: true }).filter((e) => stufe(e) >= 1).sort(vergleich);

  if (rubrik === "wochenvorschau") {
    const highlight = highlightsImZeitraum(pool, { von, bis }, "highlight");
    let liste = vielfalt(imZeitraum({ von, bis }), MAX_WOCHE);
    if (highlight && !liste.some((e) => e.id === highlight.id)) liste = [highlight, ...liste].slice(0, MAX_WOCHE);
    return { rubrik, von, bis, kandidaten: liste.map((e) => kandidat(e, stufe(e))), highlight: highlight?.id ?? null, top: null };
  }

  const top = highlightsImZeitraum(pool, { von, bis }, "top");
  const gewaehlt: DddEvent[] = top ? [top] : [];
  const je = new Map<string, number>(top ? [[norm(top.ort), 1]] : []);
  for (const w of wochen(von, bis)) {
    let n = 0;
    for (const e of imZeitraum(w)) {
      if (n >= JE_WOCHE_IM_MONAT || gewaehlt.length >= MAX_MONAT) break;
      const ort = norm(e.ort);
      if (gewaehlt.some((x) => x.id === e.id) || (je.get(ort) ?? 0) >= MAX_JE_ORT) continue;
      je.set(ort, (je.get(ort) ?? 0) + 1);
      gewaehlt.push(e);
      n++;
    }
  }
  return { rubrik, von, bis, kandidaten: gewaehlt.map((e) => kandidat(e, stufe(e))), highlight: null, top: top?.id ?? null };
}

/**
 * Header-Schlüssel der Route (T11, Cursor-Prüfung 4 Befund 1): SHA-256 beider Werte (immer 32 Byte), dann
 * timingSafeEqual – nie ein Fehler bei ungleicher Länge. Fehlt der Header oder die Umgebungsvariable → false.
 */
export function schluesselOk(gesendet: string | null | undefined, erwartet: string | undefined = process.env.MAGAZIN_JOB_SCHLUESSEL): boolean {
  if (!gesendet || !erwartet) return false;
  const a = createHash("sha256").update(gesendet).digest();
  const b = createHash("sha256").update(erwartet).digest();
  return timingSafeEqual(a, b);
}
