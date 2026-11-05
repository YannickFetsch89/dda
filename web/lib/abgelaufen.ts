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

/** Vergleichsschlüssel für den Ort (null, wenn der Ort zu allgemein ist). */
export function ortSchluessel(ort: string): string | null {
  const s = norm(ort);
  return s.length < 3 || ALLGEMEINE_ORTE.has(s) ? null : s;
}

/**
 * Teile einer Ortsangabe: Scraper schreiben denselben Ort unterschiedlich, z.B. „zakk – Halle“,
 * „zakk – Club“ und „zakk - Zentrum für Aktion, Kultur und Kommunikation“. Geteilt wird an
 * Gedankenstrichen und Klammern; jeder Teil zählt einzeln (allgemeine Teile wie „Düsseldorf“ nicht).
 */
export function ortTeile(ort: string): Set<string> {
  const teile = [ort, ...ort.split(/\s+[–—-]\s+|[()]/)]
    .map((t) => ortSchluessel(t))
    .filter((t): t is string => !!t);
  return new Set(teile);
}

/** Gleicher Ort, wenn die beiden Ortsangaben mindestens einen Teil gemeinsam haben. */
export function gleicherOrt(a: string, b: string): boolean {
  const ta = ortTeile(a);
  for (const t of ortTeile(b)) if (ta.has(t)) return true;
  return false;
}

/** Wie eng ist ein Kandidat mit dem Event verwandt? 3 = Reihe, 2 = Ort, 1 = Kategorie, 0 = nichts. */
export function verwandtschaft(e: DddEvent, x: DddEvent): number {
  if (e.reihe && e.reihe.slug === x.reihe?.slug) return 3;
  const ort = gleicherOrt(e.ort, x.ort);
  // Gleiche Reihe: gleicher bereinigter Titel am gleichen Ort (bis es eine echte Reihen-Zuordnung gibt)
  if (ort && norm(basisTitel(e.titel)) === norm(basisTitel(x.titel))) return 3;
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
