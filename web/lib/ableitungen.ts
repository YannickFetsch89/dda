// Ableitungen aus dem Event-Pool: Filter, Sortierung, Kennzahlen, kuratierte Listen.
// Felder, die es in der DB (noch) nicht gibt (beliebtheit, tags, redaktion_pick,
// wochenend_slot), werden hier heuristisch berechnet.
import { KATEGORIEN } from "./kategorien";
import { BEZIRKE, OHNE_ZUORDNUNG, bezirkVon } from "./stadtteile";
import { findetStatt, heuteBerlin, istLanglaeufer, plusTage, tageZwischen, wochenende } from "./datum";
import { basisTitel, norm } from "./termine";
import type { DddEvent, EventPool, KategorieSlug } from "./typen";

// ---------- Einzel-Eigenschaften ----------

const KOSTENLOS = /(kostenlos|kostenfrei|eintritt frei|freier eintritt|gratis|umsonst|^frei$|^free$|^0([,.]00)? ?€$|^€ ?0$)/i;

export function istKostenlos(e: DddEvent): boolean {
  return !!e.preis && KOSTENLOS.test(e.preis.trim());
}

const ONLINE = /\b(online|webinar|livestream|live.?stream|virtuell|digital|zoom|teams)\b/i;

export function istOnline(e: DddEvent): boolean {
  return ONLINE.test(e.ort) || ONLINE.test(e.titel);
}

function hash(text: string): number {
  let h = 0;
  for (let i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) | 0;
  return Math.abs(h);
}

/** Abzug für Events ohne eigenes Bild (auch mit Symbolbild), innerhalb dieser Gruppe. Die Reihenfolge „mit Bild vor ohne Bild“ erzwingt nachBeliebtheit, nicht dieser Abzug: mehrere Markierungen zusammen sind größer als 60. */
export const OHNE_BILD_ABZUG = 60;

/**
 * Beliebtheits-Score als Platzhalter, bis es eine Spalte `beliebtheit` gibt:
 * Redaktions-Markierungen, Bild, Beschreibung, Uhrzeit. Deterministisch.
 * Events ohne eigenes Bild (sie zeigen höchstens ein Symbolbild) gelten als schlecht gepflegt. Dass sie hinter jedem
 * Event mit Bild stehen, stellt nachBeliebtheit sicher (Auftraggeber 12.11.2026).
 */
export function beliebtheit(e: DddEvent): number {
  // Abgesagte Events landen in jeder Beliebtheits-Sortierung ganz hinten
  if (e.abgesagt) return -1000 + (hash(e.id) % 100) / 100;
  let s = beliebtheitOhneFlaggen(e);
  if (e.top_event_des_monats) s += 40;
  if (e.highlight_der_woche) s += 35;
  if (e.tipp_des_tages) s += 30;
  return s + (hash(e.id) % 100) / 100;
}

/**
 * Beliebtheit ohne die Punkte für die drei Flaggen und ohne Hash-Anteil (Sortierschlüssel d, Plan Empfehlungen
 * Abschnitt 9): die Flaggen gehen dort schon in die Stufe ein, der Hash ist der eigene letzte Gleichstand.
 */
export function beliebtheitOhneFlaggen(e: DddEvent): number {
  let s = e.bild_url ? 12 : -OHNE_BILD_ABZUG;
  if ((e.beschreibung?.length ?? 0) > 80) s += 6;
  if (e.uhrzeit) s += 3;
  if (e.stadtteil) s += 2;
  if (istLanglaeufer(e)) s -= 8;
  return s;
}

export type Tageszeit = "morgens" | "nachmittags" | "abends" | "nachts";

export const TAGESZEITEN: { key: Tageszeit; name: string; bereich: string; icon: string }[] = [
  { key: "morgens", name: "Morgens", bereich: "6–12 Uhr", icon: "wb_twilight" },
  { key: "nachmittags", name: "Nachmittags", bereich: "12–18 Uhr", icon: "light_mode" },
  { key: "abends", name: "Abends", bereich: "18–23 Uhr", icon: "wb_sunny" },
  { key: "nachts", name: "Nachts", bereich: "ab 23 Uhr", icon: "bedtime" },
];

function tageszeitVon(uhrzeit: string): Tageszeit {
  const [h, min] = uhrzeit.split(":").map(Number);
  const m = h * 60 + min;
  if (m >= 23 * 60 || m < 6 * 60) return "nachts";
  if (m >= 18 * 60) return "abends";
  if (m >= 12 * 60) return "nachmittags";
  return "morgens";
}

/** Alle Uhrzeiten eines Eintrags (gebündelte Termine haben mehrere, siehe lib/termine.ts). */
export function uhrzeitenVon(e: Pick<DddEvent, "uhrzeit" | "uhrzeiten">): string[] {
  return e.uhrzeiten ?? (e.uhrzeit ? [e.uhrzeit] : []);
}

/** Tageszeit der (ersten) Uhrzeit. */
export function tageszeit(e: DddEvent): Tageszeit | null {
  return e.uhrzeit ? tageszeitVon(e.uhrzeit) : null;
}

/** Alle Tageszeiten, in denen der Eintrag stattfindet (Bündel 11:00/19:00 → morgens + abends). */
export function tageszeiten(e: DddEvent): Tageszeit[] {
  return [...new Set(uhrzeitenVon(e).map(tageszeitVon))];
}

/** Früheste Uhrzeit des Eintrags innerhalb einer Tageszeit (für Sortierung je Abschnitt). */
export function ersteUhrzeitIn(e: DddEvent, t: Tageszeit): string | null {
  return uhrzeitenVon(e).find((z) => tageszeitVon(z) === t) ?? null;
}

// ---------- Sortierung ----------

export function nachZeit(a: DddEvent, b: DddEvent): number {
  return a.datum.localeCompare(b.datum) || (a.uhrzeit ?? "99").localeCompare(b.uhrzeit ?? "99") || a.titel.localeCompare(b.titel);
}

export function nachBeliebtheit(a: DddEvent, b: DddEvent): number {
  // Abgesagte bleiben hinter allen aktiven. Unter den aktiven steht jedes Event mit Bild vor jedem ohne Bild,
  // auch wenn Markierungen, Beschreibung und Uhrzeit den Score darüber heben.
  const abgesagt = Number(!!a.abgesagt) - Number(!!b.abgesagt);
  if (abgesagt) return abgesagt;
  const bild = Number(!!b.bild_url) - Number(!!a.bild_url);
  return bild || beliebtheit(b) - beliebtheit(a) || nachZeit(a, b);
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
  /** Unterkategorie (Slug) – nur zusammen mit kategorie sinnvoll */
  unter?: string;
  mitLanglaeufern?: boolean;
}

export function filtern(events: DddEvent[], f: Filter): DddEvent[] {
  const suche = f.suche?.trim().toLowerCase();
  const thema = f.thema ? THEMEN.find((t) => t.name === f.thema) : undefined;
  return events.filter((e) => {
    if (!findetStatt(e, f.von, f.bis, f.mitLanglaeufern)) return false;
    if (f.kategorie && e.kategorie !== f.kategorie) return false;
    if (f.unter && e.unterkategorie !== f.unter) return false;
    if (f.stadtteil) {
      if (f.stadtteil === OHNE_ZUORDNUNG ? !!e.stadtteil : e.stadtteil !== f.stadtteil) return false;
    }
    if (f.bezirk && bezirkVon(e.stadtteil)?.nr !== f.bezirk) return false;
    if (f.preis === "kostenlos" && !istKostenlos(e)) return false;
    if (f.preis === "bezahlt" && istKostenlos(e)) return false;
    if (f.tageszeit && !tageszeiten(e).includes(f.tageszeit)) return false;
    if (thema && !themaPasst(e, thema.muster)) return false;
    if (suche) {
      const heuhaufen = `${e.titel} ${e.ort} ${e.stadtteil ?? ""} ${e.beschreibung ?? ""}`.toLowerCase();
      if (!heuhaufen.includes(suche)) return false;
    }
    return true;
  });
}

// ---------- Kennzahlen ----------

/** Unterkategorien einer Kategorie mit Treffern, in der festgelegten Reihenfolge (leere fallen weg). */
export function unterkategorienZaehlen(events: DddEvent[], kat: KategorieSlug): { slug: string; name: string; anzahl: number }[] {
  const k = KATEGORIEN.find((x) => x.slug === kat);
  if (!k) return [];
  return k.unterkategorien
    .map((u) => ({ ...u, anzahl: events.filter((e) => e.kategorie === kat && e.unterkategorie === u.slug).length }))
    .filter((u) => u.anzahl > 0);
}

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

/**
 * Wählt n Events mit möglichst verschiedenen Kategorien. Events mit eigenem Bild haben Vorrang vor der Vielfalt:
 * erst verschiedene Kategorien mit Bild, dann weitere mit Bild, erst danach Events ohne Bild (Auftraggeber 12.11.2026).
 */
export function vielfaeltig(
  events: DddEvent[],
  n: number,
  ausschliessen = new Set<string>(),
  vergleich: (a: DddEvent, b: DddEvent) => number = nachBeliebtheit,
): DddEvent[] {
  const kandidaten = events.filter((e) => !e.abgesagt && !ausschliessen.has(e.id)).sort(vergleich);
  const gewaehlt: DddEvent[] = [];
  const kats = new Set<string>();
  const auswaehlen = (liste: DddEvent[]) => {
    for (const e of liste) {
      if (gewaehlt.length >= n) return;
      if (!kats.has(e.kategorie)) {
        gewaehlt.push(e);
        kats.add(e.kategorie);
      }
    }
    for (const e of liste) {
      if (gewaehlt.length >= n) return;
      if (!gewaehlt.includes(e)) gewaehlt.push(e);
    }
  };
  auswaehlen(kandidaten.filter((e) => e.bild_url));
  auswaehlen(kandidaten.filter((e) => !e.bild_url));
  return gewaehlt;
}

export function neuSeit(events: DddEvent[], jetztIso: string, stunden = 24): DddEvent[] {
  const grenze = new Date(new Date(jetztIso).getTime() - stunden * 3_600_000).toISOString();
  return events.filter((e) => (e.erstellt_am ?? "") >= grenze);
}

/** Zehn Tipps fürs Wochenende: Freitag 3, Samstag 4 (der volle Ausgehtag), Sonntag 3. */
export const WOCHENEND_TIPPS = { Fr: 3, Sa: 4, So: 3 } as const;

/**
 * Wochenend-Box: drei Tageslisten (Fr, Sa, So) mit Uhrzeit. Kandidaten mit Langläufern, danach gilt der Fokustag
 * wie in der Tagesansicht; Stamm bleibt draußen; je Tag Sortierschlüssel a)–e) mit Kategorie-Mischung;
 * `benutzt` verhindert dasselbe Event an zwei Tagen (Plan Empfehlungen, Abschnitt 9).
 */
export function wochenendProgramm(pool: EventPool) {
  const w = wochenende(pool.heute);
  const aktiv = pool.events.filter((e) => !e.abgesagt);
  const k = stufenKontext(aktiv, pool.heute);
  const vergleich = nachEmpfehlung(k);
  const benutzt = new Set<string>();
  return (
    [
      ["Freitag", "Fr", w.fr],
      ["Samstag", "Sa", w.sa],
      ["Sonntag", "So", w.so],
    ] as const
  ).map(([name, kurz, tag]) => {
    const tagesEvents = filtern(aktiv, { von: tag, bis: tag, mitLanglaeufern: true }).filter(
      (e) => e.uhrzeit && (breite(e, k) ?? 0) >= 1 && amFokustag(e, tag),
    );
    const auswahl = vielfaeltig(tagesEvents, WOCHENEND_TIPPS[kurz], benutzt, vergleich).sort(nachZeit);
    auswahl.forEach((e) => benutzt.add(e.id));
    return { name, kurz, tag, events: auswahl, vergangen: tag < pool.heute };
  });
}

/**
 * Highlight der Woche und Top-Event des Monats: geltende Flagge mit Bild, sonst das beste Zugpferd (Stufe 3) mit
 * Bild, sonst die beste Stufe 2 mit Bild; ohne Bild erst danach. Zeiträume mit Langläufern, kein Fokustag,
 * Stamm draußen, kein Event auf beiden Plätzen (Plan Empfehlungen, Abschnitt 9).
 */
export function highlights(pool: EventPool) {
  const aktiv = pool.events.filter((e) => !e.abgesagt);
  const k = stufenKontext(aktiv, pool.heute);
  const vergleich = nachEmpfehlung(k);
  const ohneStamm = (liste: DddEvent[]) => liste.filter((e) => (breite(e, k) ?? 0) >= 1);
  const woche = ohneStamm(filtern(aktiv, { von: pool.heute, bis: plusTage(pool.heute, 6), mitLanglaeufern: true }));
  const monat = ohneStamm(filtern(aktiv, { von: pool.heute, bis: plusTage(pool.heute, 29), mitLanglaeufern: true }));
  const waehle = (liste: DddEvent[], flagge: (e: DddEvent) => boolean, ohne?: string): DddEvent | null => {
    const frei = liste.filter((e) => e.id !== ohne);
    const regeln: ((e: DddEvent) => boolean)[] = [
      (e) => flagge(e) && !!e.bild_url,
      (e) => breite(e, k) === 3 && !!e.bild_url,
      (e) => breite(e, k) === 2 && !!e.bild_url,
      (e) => flagge(e),
      () => true,
    ];
    for (const regel of regeln) {
      const treffer = frei.filter(regel);
      if (treffer.length) return treffer.sort(vergleich)[0];
    }
    return null;
  };
  const highlight = waehle(woche, (e) => highlightGilt(e, pool.heute));
  const top = waehle(monat, (e) => topGilt(e, pool.heute), highlight?.id);
  return { highlight, top };
}

// ---------- Empfehlungen: Stufen (Plan docs/plan-empfehlungen-2026-11-13.md) ----------
// Gilt nur für Tipp, Picks, „Beliebt“, Wochenend-Box, Zeitraum-Ansicht und highlights().
// Kalender, Suche, Kategoriezeilen und Stadtteilseiten lesen die Stufe nicht.

/** 0 = Stamm (nie Pick), 1 = Szene/Serie, 2 = normal, 3 = Zugpferd. */
export type Stufe = 0 | 1 | 2 | 3;

/** Häuser, die die Startseite anführen dürfen. Treffer nur, wenn norm(ort) mit dem Eintrag beginnt (Abschnitt 4). */
export const ZUGPFERD_ORTE = [
  "tonhalle",
  "deutsche oper am rhein",
  "opernhaus düsseldorf",
  "düsseldorfer schauspielhaus",
  "schauspielhaus",
  "fft",
  "tanzhaus nrw",
  "kunstpalast",
  "k20",
  "k21",
  "kunstsammlung nrw",
  "kunsthalle düsseldorf",
  "nrw-forum",
  "mitsubishi electric halle",
  "capitol theater",
  "kommödchen",
  "merkur spiel-arena",
  "psd bank dome",
] as const;

/** Erstes Wort hinter einem Zugpferd-Eintrag, das ein anderes Lokal meint („Tonhalle Terrace“, „Capitol Theater - Club Saal“). */
const NEBENORTE = new Set(["terrace", "terrasse", "café", "cafe", "club", "bar", "tiefgarage"]);

/** Titel, die unabhängig vom Ort Zugpferd sind. CSD mit derselben Ausnahme wie lib/symbolbild.ts („Pride and Prejudice“). */
export const ZUGPFERD_TITEL = /rheinkirmes|japan-?tag|nacht der museen|\bcsd\b|\bpride\b(?!\s*(?:and|&)\s+prejudice)|christopher street/i;

/** Orte, die für viele Häuser stehen: keine Serien-Regel 3, keine Ort-Eindeutigkeit in den Plätzen (Abschnitt 6). */
export const SAMMELORTE = new Set(["düsseldorf", "stadtbüchereien düsseldorf"]);

/**
 * Stammformate (Abschnitt 3, Schritt 1). Im Titel immer, in der Beschreibung nur im Satz mit REGELMAESSIG.
 * „Repair Café“ und „Speed Dating“ auch mit Leerzeichen (Nachtrag nach der Cursor-Prüfung der Umsetzung).
 */
export const STAMM =
  /yoga|pilates|meditation|lauftreff|parkrun|repair[-\s]?caf[eé]s?(?![-\s]*t[eé]ria|taria)|spieleabend|brettspiel|sprechstunde|\bmeetup\b|\bspeed[-\s]?dating|sprachcaf[eé]|sprachtreff|sprachtandem|\btandem\b|language exchange|conversation club|stammtisch|(?<!dis)kurse?\b/i;

export const REGELMAESSIG =
  /jeden (montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag|tag|abend|morgen|woche|monat)|wöchentlich|monatlich|regelmäßig|immer (montags|dienstags|mittwochs|donnerstags|freitags|samstags|sonntags)/i;

/** Sprachhinweis: Führung, Kurs oder Treffen in einer anderen Sprache (Abschnitt 5). */
export const SPRACHE =
  /\b(auf|in) (englisch|französisch|spanisch|italienisch|türkisch|niederländisch|polnisch)\b|\bin (englisch|französisch|spanisch|italienisch|türkisch|niederländisch|polnisch)(er|en)? sprache\b|\bin english\b|\b(english|french|spanish) (tour|guided tour)\b|visite guidée|visita guiada/i;
const SPRACHE_AUSNAHME = /deutsch und|und deutsch|zweisprachig|bilingual/i;
const SPRACHE_SATZ_AUSNAHME = /audioguide|untertitel|übersetzung|übersetzt/i;
const SPRACHE_BESCHREIBUNG_TITEL = /führung|kurs|treff|stammtisch/i;
const OMU_OV = /\bomu\b|\bov\b/i;

const SZENE = /jam[- ]?session|\bjam\b|open[- ]?stage|open[- ]?mic|karaoke/i;
/** Formate, die an einem Zugpferd-Ort höchstens Stufe 2 bekommen (Titel oder Ort). */
const KLEINFORMAT = /workshop|atelier|foyer/i;
const HEIMSPIEL = /fortuna|\bdeg\b|düsseldorfer eg|psd bank dome|merkur spiel-?arena/i;
// Linke Wortgrenze per Rückschau (\b kennt keine Umlaute): „Republic Viewing“ und „profan shop“ treffen nicht
// Rechte Grenze bei Viewing und Shop („Fan Shopping“ trifft nicht); „Auswärtsfahrt“ soll treffen, daher dort offen
const KEIN_HEIMSPIEL =
  /(?<![a-zäöüé])auswärts|(?<![a-zäöüé])public[-\s]*viewing(?![a-zäöüé])|(?<![a-zäöüé])fan[-\s]*shop(?![a-zäöüé])/i;

/** Ein Satz endet am nächsten „.“, „!“ oder „?“. */
function saetze(text: string): string[] {
  return text.split(/[.!?]/);
}

/** Ort ist ein Haus aus ZUGPFERD_ORTE: Anfang von norm(ort), danach kein weiteres Ortswort wie „Terrace“ oder „Club“. */
export function istZugpferdOrt(ort: string): boolean {
  const o = norm(ort);
  return ZUGPFERD_ORTE.some((eintrag) => {
    if (!o.startsWith(eintrag)) return false;
    const rest = o.slice(eintrag.length);
    if (rest && !/^[\s-]/.test(rest)) return false; // mitten im Wort („k200“)
    const erstesWort = rest.replace(/^[\s-]+/, "").split(/[\s-]+/)[0];
    return !NEBENORTE.has(erstesWort);
  });
}

export function istSammelort(ort: string): boolean {
  return SAMMELORTE.has(norm(ort));
}

/** Heimspiel von Fortuna oder DEG: Kategorie sport, Titel oder Ort nennt Verein oder Halle; nicht auswärts. */
export function istHeimspiel(e: DddEvent): boolean {
  if (e.kategorie !== "sport") return false;
  if (KEIN_HEIMSPIEL.test(e.titel) || KEIN_HEIMSPIEL.test(e.ort)) return false;
  return HEIMSPIEL.test(e.titel) || HEIMSPIEL.test(e.ort);
}

function sprachtreffer(text: string): boolean {
  if (SPRACHE_AUSNAHME.test(text)) return false;
  return saetze(text).some((satz) => SPRACHE.test(satz) && !SPRACHE_SATZ_AUSNAHME.test(satz));
}

/** Sprachhinweis nach Abschnitt 5: Titel immer, Beschreibung nur bei Führung, Kurs oder Treffen. */
export function hatSprachhinweis(e: DddEvent): boolean {
  if (e.kategorie === "musik" || e.unterkategorie === "film" || OMU_OV.test(e.titel)) return false;
  if (sprachtreffer(e.titel)) return true;
  const beschreibungZaehlt = e.kategorie === "stadtfuehrung" || e.kategorie === "community" || SPRACHE_BESCHREIBUNG_TITEL.test(e.titel);
  return beschreibungZaehlt && !!e.beschreibung && sprachtreffer(e.beschreibung);
}

/** Stammformat oder Sprachhinweis → Stufe 0. */
export function istStamm(e: DddEvent): boolean {
  if (STAMM.test(e.titel)) return true;
  if (e.beschreibung && saetze(e.beschreibung).some((satz) => STAMM.test(satz) && REGELMAESSIG.test(satz))) return true;
  return hatSprachhinweis(e);
}

/**
 * Grundstufe (Abschnitt 3, Schritt 2): Zugpferd 3, Szene 1, sonst 2. Auswärts, Public Viewing und Fanshop heben
 * weder über den Ort noch über das Heimspiel auf 3 („Public Viewing“ in der Merkur Spiel-Arena bleibt 2).
 */
export function grundstufe(e: DddEvent): 1 | 2 | 3 {
  const nebenveranstaltung = KEIN_HEIMSPIEL.test(e.titel) || KEIN_HEIMSPIEL.test(e.ort);
  const ortTreffer = !nebenveranstaltung && istZugpferdOrt(e.ort);
  if (ortTreffer || ZUGPFERD_TITEL.test(e.titel) || istHeimspiel(e)) {
    const kleinformat = e.kategorie === "community" || KLEINFORMAT.test(e.titel) || KLEINFORMAT.test(e.ort);
    return ortTreffer && kleinformat ? 2 : 3;
  }
  return SZENE.test(e.titel) ? 1 : 2;
}

/** Grundstufe ist Szene (Jam-Session, Open Stage, Open Mic, Karaoke) – Kandidat für Platz 4. */
export function istSzene(e: DddEvent): boolean {
  return grundstufe(e) === 1;
}

/** Hat irgendein Fenster von datum bis datum + 14 (Grenzen eingeschlossen) mindestens drei verschiedene Tage? */
function hatSerienFenster(daten: string[]): boolean {
  const tage = [...new Set(daten)].sort();
  for (let i = 0; i + 2 < tage.length; i++) if (tageZwischen(tage[i], tage[i + 2]) <= 14) return true;
  return false;
}

/**
 * Serien nach Abschnitt 6, für die ganze Gruppe: Feld `reihe`, gleicher Titel oder gleicher Ort mit gleicher
 * Kategorie (nicht an Zugpferd- und Sammelorten). Gezählt werden gebündelte Einträge mit verschiedenem `datum`;
 * ein Event mit `datum_bis` ist ein Eintrag. Ergebnis: Event-ID → Serien-Schlüssel (für die Eindeutigkeit).
 */
export function serienErkennen(events: DddEvent[]): Map<string, string[]> {
  const nachTitel = new Map<string, DddEvent[]>();
  const nachOrt = new Map<string, DddEvent[]>();
  const anhaengen = (m: Map<string, DddEvent[]>, schluessel: string, e: DddEvent) => {
    const g = m.get(schluessel);
    if (g) g.push(e);
    else m.set(schluessel, [e]);
  };
  for (const e of events) {
    if (e.abgesagt) continue;
    anhaengen(nachTitel, `titel:${norm(basisTitel(e.titel))}`, e);
    if (!istZugpferdOrt(e.ort) && !istSammelort(e.ort)) anhaengen(nachOrt, `ort:${norm(e.ort)}|${e.kategorie}`, e);
  }
  const serien = new Map<string, string[]>();
  const eintragen = (e: DddEvent, schluessel: string) => serien.set(e.id, [...(serien.get(e.id) ?? []), schluessel]);
  for (const e of events) if (e.reihe && !e.abgesagt) eintragen(e, `reihe:${e.reihe.slug}`);
  for (const gruppen of [nachTitel, nachOrt]) {
    for (const [schluessel, g] of gruppen) {
      if (hatSerienFenster(g.map((e) => e.datum))) g.forEach((e) => eintragen(e, schluessel));
    }
  }
  return serien;
}

export interface StufenKontext {
  /** Heute in Europe/Berlin – Bezug für Highlight- und Top-Flaggen */
  heute: string;
  serien: Map<string, string[]>;
  stufen: Map<string, Stufe | null>;
}

/** Serien und Stufen einmal je Pool rechnen. */
export function stufenKontext(events: DddEvent[], heute: string): StufenKontext {
  return { heute, serien: serienErkennen(events), stufen: new Map() };
}

/** Kalendertag (Europe/Berlin) eines Zeitstempels, null bei ungültigem Wert. */
function setzTag(zeitpunkt: string): string | null {
  const d = new Date(zeitpunkt);
  return Number.isNaN(d.getTime()) ? null : heuteBerlin(d);
}

/** Highlight-Flagge gilt sieben Tage ab dem Setz-Tag (Europe/Berlin); ohne Zeitpunkt nie. */
export function highlightGilt(e: DddEvent, heute: string): boolean {
  if (!e.highlight_der_woche || !e.highlight_gesetzt_am) return false;
  const tag = setzTag(e.highlight_gesetzt_am);
  if (!tag) return false;
  const alter = tageZwischen(tag, heute);
  return alter >= 0 && alter < 7;
}

/** Top-Flagge gilt bis zum Ende des Monats, in dem sie gesetzt wurde (Europe/Berlin); ohne Zeitpunkt nie. */
export function topGilt(e: DddEvent, heute: string): boolean {
  if (!e.top_event_des_monats || !e.top_gesetzt_am) return false;
  const tag = setzTag(e.top_gesetzt_am);
  return !!tag && tag <= heute && tag.slice(0, 7) === heute.slice(0, 7);
}

/** Stufe 0–3 für die Empfehlungen; abgesagte Events haben keine Stufe (null). */
export function breite(e: DddEvent, k: StufenKontext): Stufe | null {
  if (e.abgesagt) return null;
  const gemerkt = k.stufen.get(e.id);
  if (gemerkt !== undefined) return gemerkt;
  const s = stufeRechnen(e, k);
  k.stufen.set(e.id, s);
  return s;
}

function stufeRechnen(e: DddEvent, k: StufenKontext): Stufe {
  // 1. Stamm oder Sprachhinweis → 0, fertig (eine Tipp-Flagge macht daraus nur einen Tipp-Kandidaten)
  if (istStamm(e)) return 0;
  // 2. Grundstufe
  let s: number = grundstufe(e);
  // 3. Serie → höchstens 1
  if (k.serien.has(e.id)) s = Math.min(s, 1);
  // 4. Langläufer → höchstens 2, außer ZUGPFERD_TITEL (Rheinkirmes)
  if (istLanglaeufer(e) && !ZUGPFERD_TITEL.test(e.titel)) s = Math.min(s, 2);
  // 5. Geltende Highlight- oder Top-Flagge → +1, höchstens 3 (die Tipp-Flagge ändert die Stufe nicht)
  if (highlightGilt(e, k.heute) || topGilt(e, k.heute)) s = Math.min(s + 1, 3);
  return s as Stufe;
}

// ---------- Empfehlungen: Fokustag und Tipp-Flagge (Abschnitt 7 und 8) ----------

/** Event mit `datum_bis` nach `datum` (nicht nur Langläufer). */
export function istMehrtaegig(e: DddEvent): boolean {
  return !!e.datum_bis && e.datum_bis > e.datum;
}

/** Fester Fokustag eines mehrtägigen Events: datum + hash(id) % Laufzeit (Tage einschließlich). Sonst `datum`. */
export function fokustag(e: DddEvent): string {
  if (!istMehrtaegig(e)) return e.datum;
  const laufzeit = tageZwischen(e.datum, e.datum_bis!) + 1;
  return plusTage(e.datum, hash(e.id) % laufzeit);
}

/** Eintägig, oder mehrtägig und `tag` ist der Fokustag. */
export function amFokustag(e: DddEvent, tag: string): boolean {
  return !istMehrtaegig(e) || fokustag(e) === tag;
}

/**
 * Gilt die Tipp-Flagge? `tag` = gezeigter Tag (Tagesansicht) oder null (Zeitraum: kein Fokustag).
 * Bis 7 Tage Laufzeit (einschließlich gezählt) an jedem Tag, ab 8 Tagen nur am Fokustag.
 */
export function tippGilt(e: DddEvent, tag: string | null): boolean {
  if (!e.tipp_des_tages || e.abgesagt) return false;
  // Laufzeit einschließlich gezählt (wie beim Fokustag): 1.–7. gilt jeden Tag, 1.–8. nur am Fokustag (Auftraggeber 13.11.2026)
  if (tag === null || !istMehrtaegig(e) || tageZwischen(e.datum, e.datum_bis!) + 1 <= 7) return true;
  return fokustag(e) === tag;
}

// ---------- Empfehlungen: Sortierschlüssel und Plätze (Abschnitt 9) ----------

/**
 * Sortierschlüssel b)–e): mit Bild vor ohne Bild, höhere Stufe, beliebtheit() ohne Flaggen-Punkte, Hash.
 * a) (Stamm draußen) filtern die Aufrufer. Mit `tag` (Tagesansicht, Platz 2 und 3) verliert ein mehrtägiges Event
 * außerhalb seines Fokustags gegen ein Event mit Bild derselben Stufe.
 */
export function nachEmpfehlung(k: StufenKontext, tag: string | null = null) {
  return (a: DddEvent, b: DddEvent): number => {
    const bild = Number(!!b.bild_url) - Number(!!a.bild_url);
    if (bild) return bild;
    const stufe = (breite(b, k) ?? -1) - (breite(a, k) ?? -1);
    if (stufe) return stufe;
    if (tag && a.bild_url && b.bild_url) {
      const fokus = Number(!amFokustag(a, tag)) - Number(!amFokustag(b, tag));
      if (fokus) return fokus;
    }
    return (
      beliebtheitOhneFlaggen(b) - beliebtheitOhneFlaggen(a) ||
      (hash(b.id) % 100) - (hash(a.id) % 100) ||
      nachZeit(a, b) ||
      a.id.localeCompare(b.id)
    );
  };
}

/** Dieselbe Serie oder derselbe norm(ort) (Sammelorte ausgenommen) – dann nur einmal in den fünf Plätzen. */
function gleicheSerieOderOrt(a: DddEvent, b: DddEvent, k: StufenKontext): boolean {
  const sa = k.serien.get(a.id) ?? [];
  const sb = k.serien.get(b.id) ?? [];
  if (sa.some((s) => sb.includes(s))) return true;
  const ort = norm(a.ort);
  return ort === norm(b.ort) && !SAMMELORTE.has(ort);
}

export interface StartPlaetze {
  /** Platz 1, null ohne Kandidaten (dann `startraster--ohne-tipp`) */
  tipp: DddEvent | null;
  /** Plätze 2–5 in dieser Reihenfolge, leere Plätze fallen weg */
  picks: DddEvent[];
  /** Plätze 2–5 mit fester Position (null = leer): groß, groß, Szene, Fund */
  plaetze: [DddEvent | null, DddEvent | null, DddEvent | null, DddEvent | null];
}

/** Klassen des Startrasters: ohne Tipp eine Spalte, sonst bliebe die erste Spalte ab 1200 px leer. */
export function startrasterKlasse(tipp: DddEvent | null): string {
  return tipp ? "sektion startraster" : "sektion startraster startraster--ohne-tipp";
}

/**
 * Die fünf Plätze der Startseite. `kandidaten` kommen aus filtern(..., { mitLanglaeufern: true });
 * `tag` ist der gezeigte Tag (Tagesansicht) oder null (Zeitraum: Fokustag gilt nicht).
 */
export function startPlaetze(kandidaten: DddEvent[], k: StufenKontext, tag: string | null): StartPlaetze {
  const aktiv = kandidaten.filter((e) => !e.abgesagt);
  const vergleich = nachEmpfehlung(k);
  const stufe = (e: DddEvent) => breite(e, k) ?? 0;
  const fokusOk = (e: DddEvent) => tag === null || amFokustag(e, tag);
  const bester = (liste: DddEvent[]) => (liste.length ? [...liste].sort(vergleich)[0] : null);

  // Platz 1: Flagge mit Bild, Heuristik mit Bild; nur wenn überhaupt kein Event ein Bild hat: Flagge, dann Heuristik ohne Bild
  const flaggen = aktiv.filter((e) => tippGilt(e, tag));
  const heuristik = aktiv.filter((e) => stufe(e) >= 1 && fokusOk(e));
  const tipp = aktiv.some((e) => e.bild_url)
    ? (bester(flaggen.filter((e) => e.bild_url)) ?? bester(heuristik.filter((e) => e.bild_url)))
    : (bester(flaggen) ?? bester(heuristik));

  const belegt: DddEvent[] = tipp ? [tipp] : [];
  const frei = (e: DddEvent) => stufe(e) >= 1 && belegt.every((b) => b.id !== e.id && !gleicheSerieOderOrt(b, e, k));
  /** Erster Kandidat nach Regel-Leiter; Bild vor ohne Bild über alle Regeln hinweg (Sortierschlüssel b). */
  const waehle = (regeln: ((e: DddEvent) => boolean)[], vgl = vergleich): DddEvent | null => {
    const basis = aktiv.filter(frei);
    for (const mitBild of [true, false]) {
      for (const regel of regeln) {
        const treffer = basis.filter((e) => !!e.bild_url === mitBild && regel(e));
        if (treffer.length) {
          const e = treffer.sort(vgl)[0];
          belegt.push(e);
          return e;
        }
      }
    }
    return null;
  };
  const gross = (e: DddEvent) => stufe(e) >= 2;
  const eins = (e: DddEvent) => stufe(e) === 1;
  const mitFokus = nachEmpfehlung(k, tag);

  // Platz 2: andere Kategorie als der Tipp (ohne Tipp entfällt die Regel), Stufe 3 oder 2, sonst die nächste Stufe
  const andereKategorie = (e: DddEvent) => !tipp || e.kategorie !== tipp.kategorie;
  const p2 = waehle([(e) => gross(e) && andereKategorie(e), (e) => eins(e) && andereKategorie(e)], mitFokus);
  // Platz 3: anderer Stadtteil als die beiden ersten (ohne Stadtteil nicht wählbar); bleibt er leer, rückt die
  // nächste Stufe (1) ohne die Stadtteil-Regel nach – nicht ein weiteres Event derselben Stufe aus demselben Stadtteil
  const stadtteile = new Set(belegt.map((e) => e.stadtteil).filter((s): s is string => !!s));
  const andererStadtteil = (e: DddEvent) => !!e.stadtteil && !stadtteile.has(e.stadtteil);
  const p3 = waehle([(e) => gross(e) && andererStadtteil(e), eins], mitFokus);
  // Platz 4: genau eine Szene-Karte (auch als Serie); sonst Stufe 2 oder 3 – keine nur über die Serie gedeckelte 1
  const p4 = waehle([istSzene, gross]);
  // Platz 5: Fund – Stufe 2, in der Tagesansicht mehrtägig nur am Fokustag; sonst die nächste Stufe
  const p5 = waehle([(e) => stufe(e) === 2 && fokusOk(e), (e) => stufe(e) === 3 && fokusOk(e), (e) => eins(e) && fokusOk(e)]);

  return { tipp, picks: [p2, p3, p4, p5].filter((e): e is DddEvent => !!e), plaetze: [p2, p3, p4, p5] };
}

/**
 * „Beliebt“: Menge aus dem bisherigen filtern, Stamm draußen, Sortierschlüssel a)–e). In der Tagesansicht steht
 * ein mehrtägiges Event nur an seinem Fokustag – auch beim Auffüllen aus der Woche. Reicht es nicht, wird die Liste kürzer.
 */
export function beliebtAuswahl(menge: DddEvent[], reserve: DddEvent[], k: StufenKontext, tag: string | null, n = 5): DddEvent[] {
  const passt = (e: DddEvent) => (breite(e, k) ?? 0) >= 1 && (tag === null || amFokustag(e, tag));
  const vergleich = nachEmpfehlung(k);
  const primaer = menge.filter(passt).sort(vergleich);
  if (primaer.length >= n) return primaer.slice(0, n);
  const ids = new Set(primaer.map((e) => e.id));
  return [...primaer, ...reserve.filter((e) => passt(e) && !ids.has(e.id)).sort(vergleich)].slice(0, n);
}
