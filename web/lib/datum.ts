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

/** Tagesleiste der Startseite: 60 Tage, bei einem ferneren Tag 14 Tage darüber hinaus, höchstens ein Jahr. */
export function tagesleistenLaenge(heute: string, von: string): number {
  return Math.min(366, Math.max(60, tageZwischen(heute, von) + 15));
}

export function wochentag(tag: string): number {
  return alsUtc(tag).getUTCDay();
}

/**
 * Echter Kalendertag im sinnvollen Bereich (2020–2100): „2099-99-99“ oder „2026-02-30“ rechnet Date.UTC sonst
 * einfach weiter. Gilt für die Tagesseite und für proxy.ts (lib/pfad-pruefung.ts) gleich.
 */
export function istGueltigerTag(wert: string | undefined | null): wert is string {
  if (!wert || !/^\d{4}-\d{2}-\d{2}$/.test(wert)) return false;
  const jahr = Number(wert.slice(0, 4));
  const d = alsUtc(wert);
  return jahr >= 2020 && jahr <= 2100 && !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === wert;
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

/** Party und Food laufen an jedem Tag der Spanne (Kasematten-Oktoberfest). Ausstellungen nicht: die würden jede Tagesliste füllen. */
const LAEUFT_JEDEN_TAG = new Set<DddEvent["kategorie"]>(["nightlife", "food"]);

/** Laufende Events länger als eine Woche, die in Tageslisten nur am Starttag zählen. */
export function istLanglaeufer(e: DddEvent): boolean {
  return !!e.datum_bis && tageZwischen(e.datum, e.datum_bis) > 7 && !LAEUFT_JEDEN_TAG.has(e.kategorie);
}

/** Meta-Zeile der Cards, z.B. "Fr 30.10. · 20:00" oder "bis 12.01." bei laufenden Events. */
export function metaZeile(e: DddEvent, heute: string): string {
  if (e.datum_bis && e.datum < heute) return `läuft bis ${kurzDatum(e.datum_bis)}`;
  const tag = e.datum === heute ? "Heute" : e.datum === plusTage(heute, 1) ? "Morgen" : tagKurz(e.datum);
  if (e.uhrzeiten) return `${tag} · Diverse Uhrzeiten`;
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

/** Eigener Zeitraum aus dem Kalender: „2026-11-18_2026-11-22“ (Start und Ende, beide einschließlich). */
const EIGENER_ZEITRAUM = /^(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})$/;
/** Längster wählbarer Zeitraum – so weit wie Tagesleiste und Kalender reichen. */
export const MAX_ZEITRAUM_TAGE = 60;

export const zeitraumKey = (von: string, bis: string) => (von === bis ? von : `${von}_${bis}`);

/** Ist der Key ein eigener Zeitraum (nicht „heute“, „woche“ …)? Dann bleibt das Label groß („Mi 18.11. – So 22.11.“). */
export const istEigenerZeitraum = (key: string) => EIGENER_ZEITRAUM.test(key);

/** Label klein beginnend für Sätze („diese Woche“), eigene Zeiträume unverändert („Mi 18.11. – So 22.11.“). */
export function zeitraumImSatz(z: Zeitraum): string {
  return istEigenerZeitraum(z.key) ? z.label : z.label.charAt(0).toLowerCase() + z.label.slice(1);
}

export function zeitraumAuflösen(eingabe: string | undefined, heute: string): Zeitraum {
  const key: string = eingabe ?? "heute";
  // Vor istGueltigerTag lesen: der Typ-Guard verengt key danach
  const eigen = key.match(EIGENER_ZEITRAUM);
  if (istGueltigerTag(key)) return { key, label: tagKurz(key), von: key, bis: key };
  // Eigener Zeitraum aus dem Kalender: gültige Tage, Start ≤ Ende; Vergangenes beginnt heute, höchstens 60 Tage
  if (eigen && istGueltigerTag(eigen[1]) && istGueltigerTag(eigen[2]) && eigen[1] <= eigen[2] && eigen[2] >= heute) {
    const von = eigen[1] < heute ? heute : eigen[1];
    const grenze = plusTage(von, MAX_ZEITRAUM_TAGE - 1);
    const bis = eigen[2] > grenze ? grenze : eigen[2];
    if (von === bis) return { key: von, label: tagKurz(von), von, bis };
    const k = zeitraumKey(von, bis);
    return { key: k, label: `${tagKurz(von)} – ${tagKurz(bis)}`, von, bis };
  }
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

/** Kennzahl unter der Event-Zahl: „kostenlos heute“, „kostenlos Do 03.12.“, „kostenlos dieses Wochenende“. */
export function kostenlosKennzahl(z: Zeitraum, heute: string): string {
  if (z.von === heute && z.bis === heute) return "kostenlos heute";
  if (z.von === z.bis) return `kostenlos ${tagKurz(z.von)}`; // „kostenlos Sa 21.11.“ (ohne „am“, Auftraggeber 16.11.2026)
  if (z.key === "monat") return "kostenlos in den nächsten 30 Tagen";
  if (z.key === "alle") return "kostenlos in 60 Tagen";
  return `kostenlos ${zeitraumImSatz(z)}`;
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
