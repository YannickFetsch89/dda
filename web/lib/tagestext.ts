// Sätze aus echten Daten für /heute, /tag/… und /wochenende (SEO-/GEO-Plan Nov. 2026, Maßnahmen 4 und 15).
// Kein Marketingtext: Zahl und Kategorien kommen aus der Liste, die auf der Seite steht (gebündelte Termine
// zählen einmal, wie die Zeilen der Liste). Ändert sich der Pool, ändert sich der Satz.
import { MONATE } from "./datum";
import { kategorie } from "./kategorien";
import type { DddEvent } from "./typen";

/** „11. November 2026“ */
export function datumText(tag: string): string {
  const [j, m, t] = tag.split("-").map(Number);
  return `${t}. ${MONATE[m - 1]} ${j}`;
}

/** Die häufigsten Kategorien (Anzeigenamen), bei Gleichstand alphabetisch. */
export function topKategorien(events: Pick<DddEvent, "kategorie">[], anzahl = 3): string[] {
  const zaehler = new Map<string, number>();
  for (const e of events) zaehler.set(e.kategorie, (zaehler.get(e.kategorie) ?? 0) + 1);
  return [...zaehler.entries()]
    .map(([slug, n]) => ({ name: kategorie(slug).name, n }))
    .sort((a, b) => b.n - a.n || a.name.localeCompare(b.name, "de"))
    .slice(0, anzahl)
    .map((k) => k.name);
}

/** „Musik, Kultur und Nightlife“ */
export function aufzaehlung(namen: string[]): string {
  if (namen.length <= 1) return namen[0] ?? "";
  return `${namen.slice(0, -1).join(", ")} und ${namen[namen.length - 1]}`;
}

/** „Am 11. November 2026 stehen in Düsseldorf 86 Events an, die meisten aus Musik, Kultur und Nightlife.“ */
export function tagesSatz(tag: string, events: Pick<DddEvent, "kategorie">[]): string {
  const datum = datumText(tag);
  const n = events.length;
  if (n === 0) return `Für den ${datum} sind in Düsseldorf noch keine Events eingetragen.`;
  if (n === 1) return `Am ${datum} steht in Düsseldorf ein Event an.`;
  const top = n >= 3 ? topKategorien(events) : [];
  return `Am ${datum} stehen in Düsseldorf ${n} Events an${top.length ? `, die meisten aus ${aufzaehlung(top)}` : ""}.`;
}

/** „Vom 13. bis 15. November 2026 stehen in Düsseldorf 214 Events an, die meisten aus …; neun davon empfehlen wir.“ */
export function wochenendSatz(fr: string, so: string, events: Pick<DddEvent, "kategorie">[], tipps: number): string {
  const [, mf, tf] = fr.split("-").map(Number);
  const [, ms] = so.split("-").map(Number);
  const von = mf === ms ? `${tf}.` : `${tf}. ${MONATE[mf - 1]}`;
  const n = events.length;
  const top = n >= 3 ? topKategorien(events) : [];
  const zahlwort = ["keine", "einen", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn"][tipps] ?? String(tipps);
  const basis = n === 0
    ? `Vom ${von} bis ${datumText(so)} sind in Düsseldorf noch keine Events eingetragen.`
    : `Vom ${von} bis ${datumText(so)} stehen in Düsseldorf ${n} Events an${top.length ? `, die meisten aus ${aufzaehlung(top)}` : ""}.`;
  return tipps > 0 && n > 0 ? `${basis.slice(0, -1)}; ${zahlwort} davon empfehlen wir.` : basis;
}

/** „Stand: 11.11.2026, 14:05 Uhr“ – Zeitpunkt, zu dem der Event-Pool in den Cache geschrieben wurde (Berliner Zeit). */
export function standText(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const teile = new Intl.DateTimeFormat("de-DE", {
    timeZone: "Europe/Berlin", day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  }).formatToParts(d);
  const w = (typ: string) => teile.find((t) => t.type === typ)?.value ?? "";
  return `Stand: ${w("day")}.${w("month")}.${w("year")}, ${w("hour")}:${w("minute")} Uhr`;
}
