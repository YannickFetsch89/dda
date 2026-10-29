// Datums-Hilfen. Alle Kalendertage sind Strings im Format YYYY-MM-DD in Europe/Berlin.
import type { DddEvent } from "./typen";

const TZ = "Europe/Berlin";

export const WT_KURZ = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
export const WT_LANG = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];
export const MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];

export function heuteBerlin(jetzt: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" }).format(jetzt);
}

/** Minuten seit Mitternacht in Berlin. */
export function minutenBerlin(jetzt: Date = new Date()): number {
  const teile = new Intl.DateTimeFormat("de-DE", { timeZone: TZ, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(jetzt);
  const h = Number(teile.find((t) => t.type === "hour")?.value ?? 0);
  const m = Number(teile.find((t) => t.type === "minute")?.value ?? 0);
  return h * 60 + m;
}

function alsUtc(tag: string): Date {
  const [j, m, t] = tag.split("-").map(Number);
  return new Date(Date.UTC(j, m - 1, t));
}

export function plusTage(tag: string, n: number): string {
  const d = alsUtc(tag);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export function tageZwischen(von: string, bis: string): number {
  return Math.round((alsUtc(bis).getTime() - alsUtc(von).getTime()) / 86_400_000);
}

export function wochentag(tag: string): number {
  return alsUtc(tag).getUTCDay();
}

export function istGueltigerTag(wert: string | undefined | null): wert is string {
  return !!wert && /^\d{4}-\d{2}-\d{2}$/.test(wert) && !Number.isNaN(alsUtc(wert).getTime());
}

/** "30.10." */
export function kurzDatum(tag: string): string {
  const [, m, t] = tag.split("-");
  return `${t}.${m}.`;
}

/** "Fr 30.10." */
export function tagKurz(tag: string): string {
  return `${WT_KURZ[wochentag(tag)]} ${kurzDatum(tag)}`;
}

/** "Dienstag, 27. Oktober 2026" */
export function tagLang(tag: string, mitJahr = true): string {
  const [j, m, t] = tag.split("-").map(Number);
  return `${WT_LANG[wochentag(tag)]}, ${t}. ${MONATE[m - 1]}${mitJahr ? ` ${j}` : ""}`;
}

/** "27. Oktober" */
export function tagMonat(tag: string): string {
  const [, m, t] = tag.split("-").map(Number);
  return `${t}. ${MONATE[m - 1]}`;
}

/** Laufende Events länger als eine Woche (Ausstellungen etc.) */
export function istLanglaeufer(e: DddEvent): boolean {
  return !!e.datum_bis && tageZwischen(e.datum, e.datum_bis) > 7;
}

/** Meta-Zeile der Cards, z.B. "Fr 30.10. · 20:00" oder "bis 12.01." bei laufenden Events. */
export function metaZeile(e: DddEvent, heute: string): string {
  if (e.datum_bis && e.datum < heute) return `läuft bis ${kurzDatum(e.datum_bis)}`;
  const tag = e.datum === heute ? "Heute" : e.datum === plusTage(heute, 1) ? "Morgen" : tagKurz(e.datum);
  return e.uhrzeit ? `${tag} · ${e.uhrzeit}` : tag;
}

export function uhrzeitMinuten(e: DddEvent): number | null {
  if (!e.uhrzeit) return null;
  const [h, m] = e.uhrzeit.split(":").map(Number);
  return h * 60 + m;
}

export interface Zeitraum {
  key: string;
  label: string;
  von: string;
  bis: string;
}

export const ZEITRAUM_OPTIONEN = [
  { key: "heute", label: "Heute" },
  { key: "morgen", label: "Morgen" },
  { key: "wochenende", label: "Dieses Wochenende" },
  { key: "woche", label: "Diese Woche" },
  { key: "monat", label: "Nächste 30 Tage" },
  { key: "alle", label: "60 Tage" },
];

/** Nächstes (bzw. laufendes) Wochenende Fr–So. */
export function wochenende(heute: string): { fr: string; sa: string; so: string } {
  const wt = wochentag(heute);
  // Sa/So: laufendes Wochenende, sonst kommender Freitag
  const fr = wt === 6 ? plusTage(heute, -1) : wt === 0 ? plusTage(heute, -2) : plusTage(heute, (5 - wt + 7) % 7);
  return { fr, sa: plusTage(fr, 1), so: plusTage(fr, 2) };
}

export function zeitraumAuflösen(eingabe: string | undefined, heute: string): Zeitraum {
  const key: string = eingabe ?? "heute";
  if (istGueltigerTag(key)) return { key, label: tagKurz(key), von: key, bis: key };
  switch (key) {
    case "morgen":
      return { key, label: "Morgen", von: plusTage(heute, 1), bis: plusTage(heute, 1) };
    case "wochenende": {
      const w = wochenende(heute);
      return { key, label: "Dieses Wochenende", von: w.fr < heute ? heute : w.fr, bis: w.so };
    }
    case "woche":
      return { key, label: "Diese Woche", von: heute, bis: plusTage(heute, 6) };
    case "monat":
      return { key, label: "Nächste 30 Tage", von: heute, bis: plusTage(heute, 29) };
    case "alle":
      return { key, label: "60 Tage", von: heute, bis: plusTage(heute, 59) };
    default:
      return { key: "heute", label: "Heute", von: heute, bis: heute };
  }
}

/**
 * Findet das Event im Zeitraum statt? Langläufer (> 7 Tage) zählen in Tagesansichten
 * nur am Starttag, sonst würden Ausstellungen jede Tagesliste füllen.
 */
export function findetStatt(e: DddEvent, von: string, bis: string, mitLanglaeufern = false): boolean {
  if (istLanglaeufer(e) && !mitLanglaeufern) return e.datum >= von && e.datum <= bis;
  const ende = e.datum_bis ?? e.datum;
  return e.datum <= bis && ende >= von;
}
