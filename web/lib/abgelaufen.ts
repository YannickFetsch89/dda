// Abgelaufene Events: Erkennung und Empfehlungen statt Sackgasse.
// Abgelaufene Eventseiten bleiben online (HTTP 200, indexierbar) – sie bekommen nur einen Hinweis
// und verweisen auf kommende Events.
import { nachBeliebtheit } from "./ableitungen";
import { basisTitel, norm } from "./termine";
import type { DddEvent } from "./typen";

/**
 * Abgelaufen = der letzte Event-Tag (datum_bis, sonst datum) liegt vor heute (Europe/Berlin).
 * Ein Event gilt also bis zum Ende seines letzten Tages (23:59 Uhr) als laufend.
 */
export function istAbgelaufen(e: Pick<DddEvent, "datum" | "datum_bis">, heute: string): boolean {
  return (e.datum_bis ?? e.datum) < heute;
}

// Ortsangaben ohne Aussagekraft – darüber werden keine Events als „gleicher Ort“ verknüpft
const ALLGEMEINE_ORTE = new Set(["düsseldorf", "duesseldorf", "online", "diverse orte", "verschiedene orte", "tba", "n/a"]);

/**
 * Vergleichsschlüssel für den Ort: normalisiert, „Düsseldorf“ als Wort entfernt (aus „ZAKK Düsseldorf“
 * wird „zakk“). null, wenn danach nichts Aussagekräftiges übrig bleibt.
 * Gleiche Regeln wie pipeline/reihen_zuordnen.py (_ort_schluessel).
 */
export function ortSchluessel(ort: string): string | null {
  const s = norm(ort.replace(/­/g, "").replace(/-/g, " "))
    .replace(/(^|\s)(düsseldorf|duesseldorf)(?=\s|$)/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return s.length < 3 || ALLGEMEINE_ORTE.has(s) ? null : s;
}

/** Teile einer Ortsangabe, getrennt an Gedankenstrichen, „ / “ und Klammern (Bindestriche im Namen bleiben). */
function ortSegmente(ort: string): string[] {
  return ort
    .split(/\s+[–—\-/]\s+|[()]/)
    .map((t) => ortSchluessel(t))
    .filter((t): t is string => !!t);
}

// Gegenden statt Orte: als erstes Segment („Rheinufer – Tonhallenufer“) taugen sie nicht als Basis
const GEGENDEN = new Set(["rheinufer", "rheinuferpromenade", "hafen", "medienhafen", "altstadt", "carlstadt", "innenstadt", "stadtmitte"]);

/**
 * Der eigentliche Ort = erstes aussagekräftiges Segment („zakk – Halle“ → „zakk“). Ist das eine Gegend
 * („Rheinufer – Tonhallenufer“), zählt das nächste Segment; besteht die Angabe nur aus einer Gegend, diese.
 */
export function ortBasis(ort: string): string | null {
  const segmente = ortSegmente(ort);
  return segmente.find((s) => !GEGENDEN.has(s)) ?? segmente[0] ?? null;
}

/**
 * Gleicher Ort, wenn
 *  - der eigentliche Ort übereinstimmt („zakk – Halle“ / „zakk – Club“, „ZAKK Düsseldorf“ / „ZAKK“), oder
 *  - der ganze Name der einen Angabe ein Segment der anderen ist
 *    („Zentrum für Aktion, Kultur und Kommunikation“ / „zakk - Zentrum für Aktion, …“).
 * Nur nachrangige Teile wie Raum oder Viertel („Brauhaus (Altstadt)“ / „Kneipe – Altstadt“) reichen nicht.
 */
export function gleicherOrt(a: string, b: string): boolean {
  const basisA = ortBasis(a);
  if (basisA && basisA === ortBasis(b)) return true;
  const vollA = ortSchluessel(a);
  const vollB = ortSchluessel(b);
  return (!!vollA && ortSegmente(b).includes(vollA)) || (!!vollB && ortSegmente(a).includes(vollB));
}

/** Titel für den Reihen-Vergleich: ohne Uhrzeit, Bindestriche wie Leerzeichen („Jazz-Schmiede“ = „Jazz Schmiede“). */
function titelSchluessel(titel: string): string {
  return norm(basisTitel(titel).replace(/­/g, "").replace(/-/g, " "));
}

/**
 * Wie eng ist ein Kandidat mit dem Event verwandt?
 * 4 = echte Reihe, 3 = gleicher Titel am gleichen Ort, 2 = gleicher Ort, 1 = gleiche Kategorie, 0 = nichts.
 */
export function verwandtschaft(e: DddEvent, x: DddEvent): number {
  if (e.reihe && e.reihe.slug === x.reihe?.slug) return 4;
  const ort = gleicherOrt(e.ort, x.ort);
  // Gleicher Titel am gleichen Ort – auch ohne (oder vor der) Reihen-Zuordnung durch die Pipeline
  if (ort && titelSchluessel(e.titel) === titelSchluessel(x.titel)) return 3;
  if (ort) return 2;
  if (e.kategorie === x.kategorie) return 1;
  return 0;
}

export const MAX_EMPFEHLUNGEN = 6;

/**
 * Kommende Events für die Seite eines abgelaufenen Events, priorisiert nach
 * gleiche Reihe > gleicher Ort > gleiche Kategorie (innerhalb: nächster Termin zuerst).
 * Reicht das nicht für MAX_EMPFEHLUNGEN, wird mit beliebten kommenden Events aufgefüllt.
 * Nur Events, die heute oder später stattfinden und nicht abgesagt sind.
 */
export function kommendeEmpfehlungen(e: DddEvent, kandidaten: DddEvent[], heute: string): DddEvent[] {
  const kommend = kandidaten.filter((x) => x.id !== e.id && !x.abgesagt && !istAbgelaufen(x, heute));
  const bewertet = kommend.map((x) => ({ x, wert: verwandtschaft(e, x) }));
  const passend = bewertet
    .filter((b) => b.wert > 0)
    .sort((a, b) => b.wert - a.wert || a.x.datum.localeCompare(b.x.datum) || nachBeliebtheit(a.x, b.x))
    .map((b) => b.x);
  const ergebnis = passend.slice(0, MAX_EMPFEHLUNGEN);
  if (ergebnis.length < MAX_EMPFEHLUNGEN) {
    const schon = new Set(ergebnis.map((x) => x.id));
    const auffuellen = kommend.filter((x) => !schon.has(x.id)).sort(nachBeliebtheit);
    ergebnis.push(...auffuellen.slice(0, MAX_EMPFEHLUNGEN - ergebnis.length));
  }
  return ergebnis;
}
