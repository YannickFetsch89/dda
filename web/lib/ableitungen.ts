// Ableitungen aus dem Event-Pool: Filter, Sortierung, Kennzahlen, kuratierte Listen.
// Felder, die es in der DB (noch) nicht gibt (beliebtheit, tags, redaktion_pick,
// wochenend_slot), werden hier heuristisch berechnet.
import { KATEGORIEN } from "./kategorien";
import { BEZIRKE, OHNE_ZUORDNUNG, bezirkVon } from "./stadtteile";
import { findetStatt, istLanglaeufer, plusTage, uhrzeitMinuten, wochenende } from "./datum";
import type { DddEvent, EventPool, KategorieSlug } from "./typen";

// ---------- Einzel-Eigenschaften ----------

const KOSTENLOS = /(kostenlos|kostenfrei|eintritt frei|freier eintritt|gratis|umsonst|^frei$|^free$|^0([,.]00)? ?€$|^€ ?0$)/i;

export function istKostenlos(e: DddEvent): boolean {
  return !!e.preis && KOSTENLOS.test(e.preis.trim());
}

function hash(text: string): number {
  let h = 0;
  for (let i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) | 0;
  return Math.abs(h);
}

/**
 * Beliebtheits-Score als Platzhalter, bis es eine Spalte `beliebtheit` gibt:
 * Redaktions-Markierungen, Bild, Beschreibung, Uhrzeit. Deterministisch.
 */
export function beliebtheit(e: DddEvent): number {
  let s = 0;
  if (e.top_event_des_monats) s += 40;
  if (e.highlight_der_woche) s += 35;
  if (e.tipp_des_tages) s += 30;
  if (e.bild_url) s += 12;
  if ((e.beschreibung?.length ?? 0) > 80) s += 6;
  if (e.uhrzeit) s += 3;
  if (e.stadtteil) s += 2;
  if (istLanglaeufer(e)) s -= 8;
  return s + (hash(e.id) % 100) / 100;
}

export type Tageszeit = "morgens" | "nachmittags" | "abends" | "nachts";

export const TAGESZEITEN: { key: Tageszeit; name: string; bereich: string; icon: string }[] = [
  { key: "morgens", name: "Morgens", bereich: "6–12 Uhr", icon: "wb_twilight" },
  { key: "nachmittags", name: "Nachmittags", bereich: "12–18 Uhr", icon: "light_mode" },
  { key: "abends", name: "Abends", bereich: "18–23 Uhr", icon: "wb_sunny" },
  { key: "nachts", name: "Nachts", bereich: "ab 23 Uhr", icon: "bedtime" },
];

export function tageszeit(e: DddEvent): Tageszeit | null {
  const m = uhrzeitMinuten(e);
  if (m === null) return null;
  if (m >= 23 * 60 || m < 6 * 60) return "nachts";
  if (m >= 18 * 60) return "abends";
  if (m >= 12 * 60) return "nachmittags";
  return "morgens";
}

// ---------- Sortierung ----------

export function nachZeit(a: DddEvent, b: DddEvent): number {
  return a.datum.localeCompare(b.datum) || (a.uhrzeit ?? "99").localeCompare(b.uhrzeit ?? "99") || a.titel.localeCompare(b.titel);
}

export function nachBeliebtheit(a: DddEvent, b: DddEvent): number {
  return beliebtheit(b) - beliebtheit(a) || nachZeit(a, b);
}

export function nachNeu(a: DddEvent, b: DddEvent): number {
  return (b.erstellt_am ?? "").localeCompare(a.erstellt_am ?? "") || nachZeit(a, b);
}

// ---------- Themen (statt Spalte `tags`) ----------

export const THEMEN: { name: string; muster: RegExp }[] = [
  { name: "Halloween", muster: /halloween|grusel/i },
  { name: "Comedy", muster: /comedy|kabarett|stand-?up/i },
  { name: "Quiz", muster: /quiz/i },
  { name: "Märkte", muster: /markt|märkte/i },
  { name: "Afterwork", muster: /after ?work/i },
  { name: "Brunch", muster: /brunch|frühstück/i },
  { name: "Yoga", muster: /yoga/i },
  { name: "Workshops", muster: /workshop|kurs\b|seminar/i },
  { name: "Lesungen", muster: /lesung|liest|poetry/i },
  { name: "Führungen", muster: /führung|rundgang/i },
  { name: "Kinder", muster: /kinder|kids|familie/i },
  { name: "Jazz", muster: /jazz/i },
  { name: "Techno", muster: /techno|house|rave/i },
  { name: "Ausstellungen", muster: /ausstellung|vernissage/i },
  { name: "Open Air", muster: /open ?air|draußen/i },
  { name: "Kino", muster: /kino|film/i },
  { name: "Little Tokyo", muster: /japan|tokyo|ramen|sushi/i },
  { name: "Flohmärkte", muster: /floh|trödel/i },
];

function themaPasst(e: DddEvent, muster: RegExp): boolean {
  return muster.test(e.titel) || muster.test(e.beschreibung ?? "");
}

export function themenZaehlen(events: DddEvent[]): { name: string; anzahl: number }[] {
  return THEMEN.map((t) => ({ name: t.name, anzahl: events.filter((e) => themaPasst(e, t.muster)).length }))
    .filter((t) => t.anzahl > 0)
    .sort((a, b) => b.anzahl - a.anzahl);
}

// ---------- Filter ----------

export interface Filter {
  von: string;
  bis: string;
  kategorie?: string;
  stadtteil?: string;
  bezirk?: number;
  preis?: "kostenlos" | "bezahlt";
  tageszeit?: Tageszeit;
  suche?: string;
  thema?: string;
  mitLanglaeufern?: boolean;
}

export function filtern(events: DddEvent[], f: Filter): DddEvent[] {
  const suche = f.suche?.trim().toLowerCase();
  const thema = f.thema ? THEMEN.find((t) => t.name === f.thema) : undefined;
  return events.filter((e) => {
    if (!findetStatt(e, f.von, f.bis, f.mitLanglaeufern)) return false;
    if (f.kategorie && e.kategorie !== f.kategorie) return false;
    if (f.stadtteil) {
      if (f.stadtteil === OHNE_ZUORDNUNG ? !!e.stadtteil : e.stadtteil !== f.stadtteil) return false;
    }
    if (f.bezirk && bezirkVon(e.stadtteil)?.nr !== f.bezirk) return false;
    if (f.preis === "kostenlos" && !istKostenlos(e)) return false;
    if (f.preis === "bezahlt" && istKostenlos(e)) return false;
    if (f.tageszeit && tageszeit(e) !== f.tageszeit) return false;
    if (thema && !themaPasst(e, thema.muster)) return false;
    if (suche) {
      const heuhaufen = `${e.titel} ${e.ort} ${e.stadtteil ?? ""} ${e.beschreibung ?? ""}`.toLowerCase();
      if (!heuhaufen.includes(suche)) return false;
    }
    return true;
  });
}

// ---------- Kennzahlen ----------

export function kategorieZaehlen(events: DddEvent[]): Record<KategorieSlug, number> {
  const z = Object.fromEntries([...KATEGORIEN.map((k) => k.slug), "sonstiges"].map((s) => [s, 0])) as Record<KategorieSlug, number>;
  events.forEach((e) => z[e.kategorie]++);
  return z;
}

export function stadtteileZaehlen(events: DddEvent[]): { name: string; anzahl: number }[] {
  const z = new Map<string, number>();
  events.forEach((e) => {
    if (e.stadtteil) z.set(e.stadtteil, (z.get(e.stadtteil) ?? 0) + 1);
  });
  return [...z.entries()].map(([name, anzahl]) => ({ name, anzahl })).sort((a, b) => b.anzahl - a.anzahl);
}

export interface BezirkCluster {
  nr: number;
  name: string;
  x: number;
  y: number;
  anzahl: number;
  stadtteile: { name: string; anzahl: number }[];
  top: DddEvent[];
  kategorien: { slug: KategorieSlug; anzahl: number }[];
}

/** Gruppiert Events nach Stadtbezirk und Stadtteil. */
export function nachBezirken(events: DddEvent[]): { bezirke: BezirkCluster[]; ohneZuordnung: number; umland: { name: string; anzahl: number }[] } {
  const proStadtteil = stadtteileZaehlen(events);
  const bezirke = BEZIRKE.map((b) => {
    const evs = events.filter((e) => bezirkVon(e.stadtteil)?.nr === b.nr);
    const kz = kategorieZaehlen(evs);
    return {
      nr: b.nr,
      name: b.name,
      x: b.x,
      y: b.y,
      anzahl: evs.length,
      stadtteile: proStadtteil.filter((s) => bezirkVon(s.name)?.nr === b.nr),
      top: [...evs].sort(nachBeliebtheit).slice(0, 3),
      kategorien: (Object.entries(kz) as [KategorieSlug, number][])
        .filter(([, n]) => n > 0)
        .sort((a, c) => c[1] - a[1])
        .map(([slug, anzahl]) => ({ slug, anzahl })),
    };
  });
  return {
    bezirke,
    ohneZuordnung: events.filter((e) => !e.stadtteil).length,
    umland: proStadtteil.filter((s) => !bezirkVon(s.name)),
  };
}

// ---------- Kuratierte Auswahl ----------

/** Wählt n Events mit möglichst verschiedenen Kategorien. */
export function vielfaeltig(events: DddEvent[], n: number, ausschliessen = new Set<string>()): DddEvent[] {
  const kandidaten = events.filter((e) => !ausschliessen.has(e.id)).sort(nachBeliebtheit);
  const gewaehlt: DddEvent[] = [];
  const kats = new Set<string>();
  for (const e of kandidaten) {
    if (gewaehlt.length >= n) break;
    if (!kats.has(e.kategorie)) {
      gewaehlt.push(e);
      kats.add(e.kategorie);
    }
  }
  for (const e of kandidaten) {
    if (gewaehlt.length >= n) break;
    if (!gewaehlt.includes(e)) gewaehlt.push(e);
  }
  return gewaehlt;
}

export function neuSeit(events: DddEvent[], jetztIso: string, stunden = 24): DddEvent[] {
  const grenze = new Date(new Date(jetztIso).getTime() - stunden * 3_600_000).toISOString();
  return events.filter((e) => (e.erstellt_am ?? "") >= grenze);
}

export function wochenendProgramm(pool: EventPool, proTag = 3) {
  const w = wochenende(pool.heute);
  const benutzt = new Set<string>();
  return (
    [
      ["Freitag", "Fr", w.fr],
      ["Samstag", "Sa", w.sa],
      ["Sonntag", "So", w.so],
    ] as const
  ).map(([name, kurz, tag]) => {
    const tagesEvents = filtern(pool.events, { von: tag, bis: tag }).filter((e) => e.uhrzeit);
    const auswahl = vielfaeltig(tagesEvents, proTag, benutzt).sort(nachZeit);
    auswahl.forEach((e) => benutzt.add(e.id));
    return { name, kurz, tag, events: auswahl, vergangen: tag < pool.heute };
  });
}

/** Highlight der Woche und Top-Event des Monats (Redaktion, sonst Heuristik). */
export function highlights(pool: EventPool) {
  const woche = filtern(pool.events, { von: pool.heute, bis: plusTage(pool.heute, 6) });
  const monat = filtern(pool.events, { von: pool.heute, bis: plusTage(pool.heute, 29) });
  const highlight = woche.find((e) => e.highlight_der_woche) ?? [...woche].filter((e) => e.bild_url).sort(nachBeliebtheit)[0] ?? woche.sort(nachBeliebtheit)[0] ?? null;
  const top =
    monat.find((e) => e.top_event_des_monats && e.id !== highlight?.id) ??
    [...monat].sort(nachBeliebtheit).find((e) => e.id !== highlight?.id) ??
    null;
  return { highlight, top };
}
