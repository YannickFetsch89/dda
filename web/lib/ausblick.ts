// Ausblick (Plan docs/plan-quellen-ausbau-2026-11-23.md, 6.1/6.4, Schritt W2): große Events von Tag 61 bis 365.
// Seite /ausblick und Startseiten-Box. Aus dem Fernpool nur Quellen mit Rang 1–2 (Haus, Ticketverkauf), nur Orte mit
// eigener Ortsseite und nur große Events (Grundstufe 3 der Startseite: Zugpferd-Häuser, Zugpferd-Titel, Heimspiele;
// ohne Stammformate). Gleicher Titel am gleichen Ort wird ein Eintrag („6 Termine bis 14.03.“). Eingegrenzt nach der
// Browser-Prüfung vom 25.11.2026: der breite Filter ließ 1.085 Karten durch, darunter Kurse und Kindertheater.
// Die Suche auf /entdecken und die Ortsseiten nutzen den Fernpool ohne diesen Filter.
import { grundstufe, istStamm, nachBeliebtheit } from "./ableitungen";
import { fernPoolLaden } from "./daten";
import { kurzDatum } from "./datum";
import { rangGespeichert, TICKETVERKAUF } from "./quellen-rang";
import { spielstaettenLaden } from "./spielstaetten-daten";
import { basisTitel, norm } from "./termine";
import type { DddEvent } from "./typen";

/** Einträge der Startseiten-Box (Q10) */
export const AUSBLICK_BOX = 6;

/** Ein Eintrag im Ausblick: erster Termin (Karte, Link) und Zahl der Termine dieses Titels am selben Ort. */
export interface AusblickEintrag {
  e: DddEvent;
  termine: number;
  /** Datum des letzten Termins (gleich e.datum bei einem Termin) */
  bis: string;
}

function nachDatum(a: DddEvent, b: DddEvent): number {
  return a.datum.localeCompare(b.datum) || (a.uhrzeit ?? "").localeCompare(b.uhrzeit ?? "") || a.titel.localeCompare(b.titel);
}

/** Auswahl für den Ausblick: nicht abgesagt, Rang ≤ 2, Ort mit Ortsseite, Grundstufe 3 ohne Stammformat; nach Datum. */
export function ausblickAuswahl(events: DddEvent[], ortIds: ReadonlySet<string>): DddEvent[] {
  return events
    .filter((e) => !e.abgesagt && rangGespeichert(e) <= TICKETVERKAUF && !!e.ort_id && ortIds.has(e.ort_id))
    .filter((e) => grundstufe(e) === 3 && !istStamm(e))
    .sort(nachDatum);
}

/** Gleicher Titel (ohne Uhrzeit im Titel, normalisiert) am gleichen Ort → ein Eintrag mit dem ersten Termin. */
export function ausblickBuendeln(events: DddEvent[]): AusblickEintrag[] {
  const gruppen = new Map<string, AusblickEintrag>();
  for (const e of [...events].sort(nachDatum)) {
    const schluessel = `${e.ort_id ?? norm(e.ort)}|${norm(basisTitel(e.titel))}`;
    const g = gruppen.get(schluessel);
    if (!g) gruppen.set(schluessel, { e, termine: 1, bis: e.datum });
    else {
      g.termine += 1;
      if (e.datum > g.bis) g.bis = e.datum;
    }
  }
  return [...gruppen.values()];
}

/** Hinweis unter der Karte bei mehreren Terminen, sonst null. */
export function termineHinweis(x: AusblickEintrag): string | null {
  if (x.termine < 2) return null;
  return x.bis === x.e.datum ? `${x.termine} Termine an diesem Tag` : `${x.termine} Termine bis ${kurzDatum(x.bis)}`;
}

/**
 * Startseiten-Box: höchstens ein Eintrag je Haus, über die Monate verteilt (reihum, je Monat der beliebteste
 * noch freie Eintrag; Events mit eigenem Bild zuerst, über nachBeliebtheit), danach nach Datum.
 */
export function ausblickBox(eintraege: AusblickEintrag[], anzahl = AUSBLICK_BOX): AusblickEintrag[] {
  const monate = new Map<string, AusblickEintrag[]>();
  for (const x of eintraege) {
    const m = x.e.datum.slice(0, 7);
    const liste = monate.get(m);
    if (liste) liste.push(x);
    else monate.set(m, [x]);
  }
  const reihen = [...monate.keys()].sort().map((m) => monate.get(m)!.sort((a, b) => nachBeliebtheit(a.e, b.e)));
  const haeuser = new Set<string>();
  const auswahl: AusblickEintrag[] = [];
  let weiter = true;
  while (auswahl.length < anzahl && weiter) {
    weiter = false;
    for (const reihe of reihen) {
      if (auswahl.length >= anzahl) break;
      const i = reihe.findIndex((x) => !haeuser.has(x.e.ort_id ?? norm(x.e.ort)));
      if (i < 0) continue;
      const [x] = reihe.splice(i, 1);
      haeuser.add(x.e.ort_id ?? norm(x.e.ort));
      auswahl.push(x);
      weiter = true;
    }
  }
  return auswahl.sort((a, b) => nachDatum(a.e, b.e));
}

/** Kategorien, die im Ausblick vorkommen (für die Filter-Chips), in der Reihenfolge der Häufigkeit. */
export function ausblickKategorien(eintraege: AusblickEintrag[]): { slug: string; anzahl: number }[] {
  const zaehler = new Map<string, number>();
  for (const { e } of eintraege) zaehler.set(e.kategorie, (zaehler.get(e.kategorie) ?? 0) + 1);
  return [...zaehler].map(([slug, anzahl]) => ({ slug, anzahl })).sort((a, b) => b.anzahl - a.anzahl || a.slug.localeCompare(b.slug));
}

/**
 * Lädt den Ausblick: Fernpool (eigener Cache, bei Fehler leer – nie Beispieldaten) und die aktiven Spielstätten
 * (Orte mit Seite unter /orte). `heute` für Monats-Labels, `letzter` für den Seitentitel („bis <Monat Jahr>“).
 */
export async function ausblickLaden(): Promise<{ heute: string; eintraege: AusblickEintrag[]; letzter: string | null }> {
  const [fern, { orte }] = await Promise.all([fernPoolLaden(), spielstaettenLaden()]);
  const events = ausblickAuswahl(fern.events, new Set(orte.map((o) => o.id)));
  return { heute: fern.heute, eintraege: ausblickBuendeln(events), letzter: events.length ? events[events.length - 1].datum : null };
}
