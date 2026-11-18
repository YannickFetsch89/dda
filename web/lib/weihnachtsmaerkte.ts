// Logik des Weihnachtsmarkt-Guides (Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, 4.3, 4.7, 5.1–5.4).
// Reine Funktionen ohne Netz und ohne Uhr: das Datum kommt immer von außen (Browser oder dynamischer Seitenteil).
// Gleiche Öffnungsregeln wie scraper/weihnachtsmaerkte/zeiten.py – beide gegen tests/fixtures/weihnachtsmaerkte_oeffnung.json.
import { istGueltigerTag } from "./datum";
import type { DddOrt } from "./typen";

export const WM_BASIS = "/guides/weihnachtsmaerkte";
/** Saisonjahr, solange noch keine Daten geladen sind (Rückfall ohne Uhr). */
export const SAISON_STANDARD = "2026";
export const wmPfad = (o: DddOrt) => `${WM_BASIS}/${encodeURIComponent(o.slug)}`;

// ---------- Datenmodell (extras.weihnachtsmarkt, Plan 3.1) ----------

export type Tag = "mo" | "di" | "mi" | "do" | "fr" | "sa" | "so";
export const TAGE: Tag[] = ["mo", "di", "mi", "do", "fr", "sa", "so"];
const TAG_KURZ: Record<Tag, string> = { mo: "Mo", di: "Di", mi: "Mi", do: "Do", fr: "Fr", sa: "Sa", so: "So" };

export interface WmZeit { tage: Tag[]; von: string; bis: string }
export interface WmSonder { datum: string; geschlossen?: boolean; von?: string; bis?: string }
export interface WmSaison {
  von?: string | null;
  bis?: string | null;
  zeiten?: WmZeit[];
  sonder?: WmSonder[];
  geerbt?: string[];
  geerbt_von?: string;
  quelle?: string;
  beleg?: string;
  url?: string;
  stand?: string;
}
export type Saisons = Record<string, WmSaison>;
export interface WmMerkmal { wert: "ja" | "nein" | "teilweise"; notiz?: string; quelle?: string; beleg?: string; url?: string; stand?: string }
export interface WmDaten {
  schluessel: string;
  gruppe: string | null;
  ist_gruppe: boolean;
  attraktion: boolean;
  immer_im_guide: boolean;
  art: string[];
  veranstalter: string | null;
  quelle_url: string | null;
  toubiz_url: string | null;
  eintritt: { wert: "frei" | "kostenpflichtig"; beleg?: string } | null;
  anfahrt: { haltestellen: { name: string; linien?: string }[]; parken?: string; beleg?: string } | null;
  staende: { anzahl: number; beleg?: string } | null;
  merkmale: Record<string, WmMerkmal>;
  saisons: Saisons;
  event_muster: string[];
  top5_rang: number | null;
  score: { wert?: number; manuell?: number } | null;
}

const text = (v: unknown): string | null => (typeof v === "string" && v.trim() ? v.trim() : null);
const obj = (v: unknown): Record<string, unknown> => (v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {});

/** extras.weihnachtsmarkt nur aus bekannten Feldern lesen (Plan 5.1). */
export function wm(o: DddOrt): WmDaten {
  const x = obj(o.extras?.weihnachtsmarkt);
  const eintritt = obj(x.eintritt);
  const anfahrt = obj(x.anfahrt);
  const staende = obj(x.staende);
  const score = obj(x.score);
  return {
    schluessel: text(x.schluessel) ?? o.slug,
    gruppe: text(x.gruppe),
    ist_gruppe: x.ist_gruppe === true,
    attraktion: x.attraktion === true,
    immer_im_guide: x.immer_im_guide === true,
    art: Array.isArray(x.art) ? x.art.filter((a): a is string => typeof a === "string") : [],
    veranstalter: text(x.veranstalter),
    quelle_url: text(x.quelle_url),
    toubiz_url: text(x.toubiz_url),
    eintritt: eintritt.wert === "frei" || eintritt.wert === "kostenpflichtig" ? { wert: eintritt.wert, beleg: text(eintritt.beleg) ?? undefined } : null,
    anfahrt: Array.isArray(anfahrt.haltestellen)
      ? { haltestellen: (anfahrt.haltestellen as unknown[]).map(obj).filter((h) => text(h.name)).map((h) => ({ name: text(h.name)!, linien: text(h.linien) ?? undefined })), parken: text(anfahrt.parken) ?? undefined }
      : null,
    staende: typeof staende.anzahl === "number" ? { anzahl: staende.anzahl, beleg: text(staende.beleg) ?? undefined } : null,
    merkmale: Object.fromEntries(
      Object.entries(obj(x.merkmale)).map(([k, v]) => [k, obj(v) as unknown as WmMerkmal]).filter(([, v]) => ["ja", "nein", "teilweise"].includes((v as WmMerkmal).wert)),
    ),
    saisons: Object.fromEntries(Object.entries(obj(x.saisons)).map(([k, v]) => [k, obj(v) as WmSaison])),
    event_muster: Array.isArray(x.event_muster) ? x.event_muster.filter((m): m is string => typeof m === "string") : [],
    top5_rang: typeof x.top5_rang === "number" && x.top5_rang >= 1 && x.top5_rang <= 5 ? x.top5_rang : null,
    score: Object.keys(score).length ? { wert: typeof score.wert === "number" ? score.wert : undefined, manuell: typeof score.manuell === "number" ? score.manuell : undefined } : null,
  };
}

// ---------- Feiertage und Öffnung (Plan 4.3) ----------

function utc(datum: string): Date {
  const [j, m, t] = datum.split("-").map(Number);
  return new Date(Date.UTC(j, m - 1, t));
}
const iso = (d: Date) => d.toISOString().slice(0, 10);
/** Wochentag als Tag-Kürzel (Montag = mo). */
export const wochentag = (datum: string): Tag => TAGE[(utc(datum).getUTCDay() + 6) % 7];

/** Totensonntag = Sonntag vor dem 1. Advent = 4. Advent − 4 Wochen (2026: 22.11., 2027: 21.11.). */
export function totensonntag(jahr: number): string {
  const weihnachten = new Date(Date.UTC(jahr, 11, 25));
  const zurueck = (weihnachten.getUTCDay() + 7) % 7 || 7; // Sonntag = 0 → eine Woche zurück
  const vierter = new Date(weihnachten.getTime() - zurueck * 86_400_000);
  return iso(new Date(vierter.getTime() - 28 * 86_400_000));
}

export function feiertag(datum: string): string | null {
  const jahr = Number(datum.slice(0, 4));
  if (datum === totensonntag(jahr)) return "Totensonntag";
  return ({ "12-24": "Heiligabend", "12-25": "1. Weihnachtstag", "12-26": "2. Weihnachtstag", "12-31": "Silvester", "01-01": "Neujahr" } as Record<string, string>)[datum.slice(5)] ?? null;
}

const mitZeitraum = (saisons: Saisons) => Object.entries(saisons).filter(([, s]) => s.von && s.bis) as [string, WmSaison & { von: string; bis: string }][];

/** Saison für ein Datum (4.3 Schritt 1): die mit von ≤ datum ≤ bis – nicht der Schlüssel des Kalenderjahrs. */
export function saisonFuer(saisons: Saisons, datum: string): { schluessel: string | null; lage: "in" | "vor" | "nach" | "unbekannt" } {
  const alle = mitZeitraum(saisons);
  if (!alle.length) return { schluessel: null, lage: "unbekannt" };
  const drin = alle.find(([, s]) => s.von <= datum && datum <= s.bis);
  if (drin) return { schluessel: drin[0], lage: "in" };
  const spaeter = alle.filter(([, s]) => s.von > datum).sort((a, b) => a[1].von.localeCompare(b[1].von));
  if (spaeter.length) return { schluessel: spaeter[0][0], lage: "vor" };
  const letzte = [...alle].sort((a, b) => b[1].bis.localeCompare(a[1].bis))[0];
  return { schluessel: letzte[0], lage: "nach" };
}

export type Zustand = "vor_saison" | "nach_saison" | "zu" | "offen" | "unbekannt";
/** saison = Schlüssel der gewählten Saison (z. B. "2026" auch für Tage im Januar 2027). */
export interface Oeffnung { zustand: Zustand; von?: string; bis?: string; grund?: string | null; ab?: string; ende?: string; saison?: string }

export function oeffnungAm(saisons: Saisons, datum: string): Oeffnung {
  const { schluessel, lage } = saisonFuer(saisons, datum);
  if (!schluessel) return { zustand: "unbekannt" };
  const s = saisons[schluessel];
  if (lage === "vor") return { zustand: "vor_saison", ab: s.von!, saison: schluessel };
  if (lage === "nach") return { zustand: "nach_saison", ende: s.bis!, saison: schluessel };
  if (!s.zeiten?.length) return { zustand: "unbekannt" };
  const grund = feiertag(datum);
  const sonder = (s.sonder ?? []).find((x) => x.datum === datum);
  if (sonder) return sonder.geschlossen ? { zustand: "zu", grund } : { zustand: "offen", von: sonder.von, bis: sonder.bis, grund };
  // Feiertag ohne Sonderzeile: weder Beleg für „zu“ noch für „offen“ (4.3 Schritt 4)
  if (grund) return { zustand: "unbekannt", grund };
  const z = s.zeiten.find((x) => x.tage.includes(wochentag(datum)));
  return z ? { zustand: "offen", von: z.von, bis: z.bis } : { zustand: "zu" };
}

/** Saison mit dem spätesten bis, die Zeitraum UND Wochenzeiten hat (ein leerer neuer Schlüssel ändert nichts). */
export function aktuelleSaison(saisons: Saisons): (WmSaison & { von: string; bis: string; jahr: string }) | null {
  const kandidaten = mitZeitraum(saisons).filter(([, s]) => s.zeiten?.length).sort((a, b) => b[1].bis.localeCompare(a[1].bis));
  return kandidaten.length ? { ...kandidaten[0][1], jahr: kandidaten[0][0] } : null;
}

// ---------- Texte ----------

const WT = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
/** „Fr, 20.11.“ */
export function datumKurz(datum: string): string {
  const d = utc(datum);
  return `${WT[d.getUTCDay()]}, ${datum.slice(8, 10)}.${datum.slice(5, 7)}.`;
}
/** „20.11.2026“ */
export const datumLang = (datum: string) => `${datum.slice(8, 10)}.${datum.slice(5, 7)}.${datum.slice(0, 4)}`;
/** „11–21 Uhr“, „11:30–20:30 Uhr“ */
export function zeitText(von?: string, bis?: string): string {
  const k = (t?: string) => (t ? (t.endsWith(":00") ? String(Number(t.slice(0, 2))) : `${Number(t.slice(0, 2))}:${t.slice(3)}`) : "?");
  return `${k(von)}–${k(bis)} Uhr`;
}
/** „Mo–Do“, „Mo–Do, So“ */
export function tageText(tage: Tag[]): string {
  const idx = [...tage].map((t) => TAGE.indexOf(t)).sort((a, b) => a - b);
  const gruppen: number[][] = [];
  for (const i of idx) {
    const g = gruppen.at(-1);
    if (g && i === g.at(-1)! + 1) g.push(i);
    else gruppen.push([i]);
  }
  if (idx.length === 7) return "täglich";
  return gruppen.map((g) => (g.length === 1 ? TAG_KURZ[TAGE[g[0]]] : `${TAG_KURZ[TAGE[g[0]]]}–${TAG_KURZ[TAGE[g.at(-1)!]]}`)).join(", ");
}

/** Tageszustand als Text (ohne Uhrzeit). */
export function oeffnungText(o: Oeffnung, bezug: "heute" | "tag" = "heute"): string {
  const vorne = bezug === "heute" ? "Heute" : "An diesem Tag";
  switch (o.zustand) {
    case "offen": return `${vorne} ${zeitText(o.von, o.bis)}${o.grund ? ` (${o.grund})` : ""}`;
    case "zu": return `${vorne} geschlossen${o.grund ? ` (${o.grund})` : ""}`;
    case "vor_saison": return `Öffnet am ${datumKurz(o.ab!)}`;
    // Jahr aus dem Saisonschlüssel, nicht aus dem Enddatum (Kö on Ice: Saison 2026 endet am 10.01.2027)
    case "nach_saison": return `Saison ${o.saison ?? o.ende!.slice(0, 4)} beendet`;
    default: return o.grund ? `${o.grund}: nicht veröffentlicht` : "Öffnungszeiten noch nicht veröffentlicht";
  }
}

const minuten = (t: string) => Number(t.slice(0, 2)) * 60 + Number(t.slice(3, 5));
/** Mit Uhrzeit (4.3 Schritt 6): „Jetzt geöffnet bis 21 Uhr“, „Öffnet heute um 11 Uhr“, „Heute schon geschlossen“. */
export function jetztText(o: Oeffnung, minutenJetzt: number): string {
  if (o.zustand !== "offen" || !o.von || !o.bis) return oeffnungText(o);
  if (minutenJetzt < minuten(o.von)) return `Öffnet heute um ${zeitText(o.von, o.bis).split("–")[0]} Uhr`;
  if (minutenJetzt < minuten(o.bis)) return `Jetzt geöffnet bis ${zeitText(o.von, o.bis).split("–")[1]}`;
  return "Heute schon geschlossen";
}

// ---------- Zeitentabelle und Sonderzeiten (5.2, 5.3) ----------

export function wochenZeilen(s: WmSaison): { tage: string; zeit: string }[] {
  return [...(s.zeiten ?? [])]
    .sort((a, b) => TAGE.indexOf(a.tage[0]) - TAGE.indexOf(b.tage[0]))
    .map((z) => ({ tage: tageText(z.tage), zeit: zeitText(z.von, z.bis) }));
}

export function sonderZeilen(s: WmSaison): { datum: string; name: string | null; text: string }[] {
  return [...(s.sonder ?? [])]
    .sort((a, b) => a.datum.localeCompare(b.datum))
    .map((x) => ({ datum: x.datum, name: feiertag(x.datum), text: x.geschlossen ? "geschlossen" : zeitText(x.von, x.bis) }));
}

/** Die sechs festen Tage der Sonderzeiten-Tabelle (Totensonntag … Neujahr) für ein Saisonjahr. */
export function sonderTage(jahr: number): { datum: string; name: string }[] {
  return [
    { datum: totensonntag(jahr), name: "Totensonntag" },
    { datum: `${jahr}-12-24`, name: "Heiligabend" },
    { datum: `${jahr}-12-25`, name: "1. Weihnachtstag" },
    { datum: `${jahr}-12-26`, name: "2. Weihnachtstag" },
    { datum: `${jahr}-12-31`, name: "Silvester" },
    { datum: `${jahr + 1}-01-01`, name: "Neujahr" },
  ];
}

/** Zelle der Sonderzeiten-Tabelle: „–“ außerhalb des Zeitraums, sonst Zeit, „geschlossen“ oder „nicht veröffentlicht“. */
export function sonderZelle(saisons: Saisons, datum: string): string {
  const o = oeffnungAm(saisons, datum);
  if (o.zustand === "vor_saison" || o.zustand === "nach_saison") return "–";
  if (o.zustand === "offen") return zeitText(o.von, o.bis);
  if (o.zustand === "zu") return "geschlossen";
  return "nicht veröffentlicht";
}

// ---------- Rollen, Zahlen, Badges, Sortierung ----------

export const istMarkt = (o: DddOrt) => !wm(o).ist_gruppe && !wm(o).attraktion;

/** Jahr im Hub-Titel nur während der Saison (bis zum spätesten bis aller Einträge), danach ohne Jahr (5.8). */
export function hubJahr(alle: DddOrt[], heute: string): string | null {
  const s = alle.map((o) => aktuelleSaison(wm(o).saisons)).filter((x): x is NonNullable<typeof x> => !!x);
  if (!s.length) return null;
  const letztes = s.map((x) => x.bis).sort().at(-1)!;
  return heute <= letztes ? s.map((x) => x.jahr).sort().at(-1)! : null;
}

/** Hero (5.2): Märkte ohne Gruppenzeile und ohne Attraktionen, Zeitraum nur aus diesen. */
export function heroZahlen(alle: DddOrt[]): { anzahl: number; von: string | null; bis: string | null; jahr: string | null } {
  const maerkte = alle.filter(istMarkt);
  const saisons = maerkte.map((o) => aktuelleSaison(wm(o).saisons)).filter((s): s is NonNullable<typeof s> => !!s);
  const von = saisons.map((s) => s.von).sort()[0] ?? null;
  const bis = saisons.map((s) => s.bis).sort().at(-1) ?? null;
  const jahr = saisons.map((s) => s.jahr).sort().at(-1) ?? null;
  return { anzahl: maerkte.length, von, bis, jahr };
}

export interface Badge { wert: string; label: string; icon: string }
export const BADGES: Badge[] = [
  { wert: "familien", label: "Für Familien", icon: "child_care" },
  { wert: "eisbahn", label: "Mit Eisbahn", icon: "ice_skating" },
  { wert: "riesenrad", label: "Mit Riesenrad", icon: "attractions" },
  { wert: "kindereisenbahn", label: "Mit Kindereisenbahn", icon: "train" },
  { wert: "kunsthandwerk", label: "Kunsthandwerk", icon: "palette" },
  { wert: "schloss", label: "Schlosskulisse", icon: "castle" },
  { wert: "lange", label: "Lange offen", icon: "nightlight" },
  { wert: "wochenende", label: "Nur am Wochenende", icon: "event" },
];

const ja = (d: WmDaten, m: string) => d.merkmale[m]?.wert === "ja";

/** Merkmale einer Gruppe enthalten Eisbahn/Riesenrad ihrer Attraktionen (4.7). */
function gruppenMerkmale(o: DddOrt, alle: DddOrt[]): Set<string> {
  const d = wm(o);
  const m = new Set(Object.entries(d.merkmale).filter(([, v]) => v.wert === "ja").map(([k]) => k));
  if (d.ist_gruppe) {
    for (const t of alle) {
      const td = wm(t);
      if (td.gruppe === d.schluessel && td.attraktion) {
        if (ja(td, "eisbahn")) m.add("eisbahn");
        if (ja(td, "riesenrad")) m.add("riesenrad");
      }
    }
  }
  return m;
}

/** Badges eines Eintrags in fester Reihenfolge (4.7), nur aus belegten Daten. Ohne „Unser Tipp“ (Auftraggeber 18.11.2026). */
export function badges(o: DddOrt, alle: DddOrt[]): Badge[] {
  const d = wm(o);
  const m = gruppenMerkmale(o, alle);
  const s = aktuelleSaison(d.saisons);
  const tage = new Set((s?.zeiten ?? []).flatMap((z) => z.tage));
  const treffer: Record<string, boolean> = {
    familien: ["kinderprogramm", "karussell", "kindereisenbahn", "puppenbuehne"].some((x) => m.has(x)),
    eisbahn: m.has("eisbahn"),
    riesenrad: m.has("riesenrad"),
    kindereisenbahn: m.has("kindereisenbahn"),
    kunsthandwerk: m.has("kunsthandwerk") || d.art.includes("kunsthandwerk"),
    schloss: d.art.includes("schloss"),
    lange: (s?.zeiten ?? []).some((z) => z.bis >= "22:00"),
    wochenende: tage.size > 0 && [...tage].every((t) => t === "fr" || t === "sa" || t === "so"),
  };
  return BADGES.filter((b) => treffer[b.wert]);
}

const scoreWert = (d: WmDaten) => d.score?.manuell ?? d.score?.wert ?? null;

/** Sortierung „Empfohlen“ (5.1): Top-5-Rang, dann Score (manuell vor gerechnet), dann Name. */
export function sortieren(orte: DddOrt[]): DddOrt[] {
  return [...orte].sort((a, b) => {
    const da = wm(a), db = wm(b);
    const ra = da.top5_rang ?? 99, rb = db.top5_rang ?? 99;
    if (ra !== rb) return ra - rb;
    const sa = scoreWert(da) ?? -1, sb = scoreWert(db) ?? -1;
    if (sa !== sb) return sb - sa;
    return a.name.localeCompare(b.name, "de");
  });
}

/** Top 5 an einem Tag (5.5/5.8): nur vom 01.10. bis 30.12. und nur mit genau fünf Rängen; ohne Tag (Fallback ohne Uhr) nie. */
export function topFuenfAm(alle: DddOrt[], heute: string | null): DddOrt[] {
  if (!heute) return [];
  const md = heute.slice(5);
  return md >= "10-01" && md <= "12-30" ? topFuenf(alle) : [];
}

/** Pin-Zustand heute (nur im Browser aufgerufen, Plan E5): offen | zu | saison (vor/nach) | unbekannt. */
export function pinZustand(saisons: Saisons, heute: string): "offen" | "zu" | "saison" | "unbekannt" {
  const z = oeffnungAm(saisons, heute).zustand;
  return z === "offen" || z === "zu" || z === "unbekannt" ? z : "saison";
}

/** Top 5 (4.6): genau fünf Ränge nötig, sonst kein Block. Das Datumsfenster prüft topFuenfAm. */
export function topFuenf(alle: DddOrt[]): DddOrt[] {
  const top = alle.filter((o) => wm(o).top5_rang != null).sort((a, b) => wm(a).top5_rang! - wm(b).top5_rang!);
  return top.length === 5 ? top : [];
}

/** Listenreihenfolge im Hub: Gruppe mit ihren Teilen zuerst (Märkte, dann Attraktionen), danach die übrigen Märkte. */
export function listenReihenfolge(alle: DddOrt[]): { gruppe: DddOrt; teile: DddOrt[] }[] {
  const gruppen = sortieren(alle.filter((o) => wm(o).ist_gruppe));
  const inGruppe = new Set<string>();
  const ergebnis = gruppen.map((g) => {
    const teile = sortieren(alle.filter((o) => wm(o).gruppe === wm(g).schluessel && !wm(o).ist_gruppe));
    teile.sort((a, b) => Number(wm(a).attraktion) - Number(wm(b).attraktion));
    teile.forEach((t) => inGruppe.add(t.id));
    return { gruppe: g, teile };
  });
  const rest = sortieren(alle.filter((o) => !wm(o).ist_gruppe && !inGruppe.has(o.id)));
  return [...ergebnis, ...rest.map((o) => ({ gruppe: o, teile: [] }))];
}

/** Indexierbar (5.4): irgendeine Saison mit Zeitraum und Wochenzeiten und eine Beschreibung. */
export function istIndexierbar(o: DddOrt): boolean {
  return !!o.beschreibung && !!aktuelleSaison(wm(o).saisons);
}

/** Rolle als Text für Karten und Listen. */
export function rolleText(o: DddOrt): string {
  const d = wm(o);
  if (d.ist_gruppe) return "Weihnachtsmarkt (mehrere Märkte)";
  if (d.attraktion) return d.art.includes("eisbahn") ? "Eisbahn" : d.art.includes("riesenrad") ? "Riesenrad" : "Attraktion";
  return "Weihnachtsmarkt";
}

// ---------- Filter und Sortierung (Stufe 1b, Plan 4.7 und 5.1) ----------

export const FILTER_BADGES = ["familien", "eisbahn", "riesenrad", "kindereisenbahn", "kunsthandwerk", "lange"] as const;
/** Badges, die eine konkrete Suchfrage beantworten, erscheinen schon ab einem Treffer (4.7). */
const SCHWELLE_EINS = new Set(["eisbahn", "riesenrad", "kindereisenbahn"]);
export const GEBIETE = [
  { wert: "innenstadt", label: "Innenstadt" },
  { wert: "stadtteile", label: "Düsseldorfer Stadtteile" },
  { wert: "neuss", label: "Neuss" },
  { wert: "ratingen", label: "Ratingen" },
] as const;
export const SORTIERUNGEN = [
  { wert: "empfohlen", label: "Empfohlen" },
  { wert: "name", label: "Name" },
] as const;
export type Gebiet = (typeof GEBIETE)[number]["wert"];

export interface WmFilter { badges: string[]; gebiet: Gebiet | null; offen: boolean; sort: "empfohlen" | "name" }
export const WM_STANDARD: WmFilter = { badges: [], gebiet: null, offen: false, sort: "empfohlen" };

type Roh = Record<string, string | string[] | undefined>;
const ersterWert = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) ?? "";

/** URL-Parameter lesen: badge=familien,eisbahn · gebiet=innenstadt · offen=1 · sort=name (unbekannte Werte fallen weg). */
export function wmFilterLesen(sp: Roh): WmFilter {
  const badgesRoh = ersterWert(sp.badge).split(",").map((b) => b.trim()).filter(Boolean);
  const gebiet = GEBIETE.find((g) => g.wert === ersterWert(sp.gebiet))?.wert ?? null;
  return {
    badges: [...new Set(badgesRoh.filter((b) => (FILTER_BADGES as readonly string[]).includes(b)))],
    gebiet,
    offen: ersterWert(sp.offen) === "1",
    sort: ersterWert(sp.sort) === "name" ? "name" : "empfohlen",
  };
}

export const wmFilterAktiv = (f: WmFilter) => f.badges.length > 0 || !!f.gebiet || f.offen || f.sort !== "empfohlen";

/** Filter-URL mit Änderung a (leere Werte fallen weg; Reihenfolge fest, damit gleiche Filter gleiche URLs haben). */
export function wmFilterHref(f: WmFilter, a: Partial<WmFilter> = {}, tag: string | null = null): string {
  const n = { ...f, ...a };
  const p = new URLSearchParams();
  if (tag) p.set("tag", tag);
  if (n.badges.length) p.set("badge", [...n.badges].sort().join(","));
  if (n.gebiet) p.set("gebiet", n.gebiet);
  if (n.offen) p.set("offen", "1");
  if (n.sort !== "empfohlen") p.set("sort", n.sort);
  const q = p.toString();
  return q ? `${WM_BASIS}?${q}` : WM_BASIS;
}

export function gebietVon(o: DddOrt): Gebiet {
  if (o.stadtteil === "Neuss") return "neuss";
  if (o.stadtteil === "Ratingen") return "ratingen";
  const d = wm(o);
  return d.ist_gruppe || d.gruppe === "innenstadt" || d.schluessel === "innenstadt" ? "innenstadt" : "stadtteile";
}

/** Filtern (UND über Badges, Gebiet, „an diesem Tag geöffnet“). tag = gewählter oder heutiger Tag. */
export function wmFiltern(orte: DddOrt[], alle: DddOrt[], f: WmFilter, tag: string, ohne: (keyof WmFilter)[] = []): DddOrt[] {
  return orte.filter((o) => {
    if (!ohne.includes("badges") && f.badges.length) {
      const b = new Set(badges(o, alle).map((x) => x.wert));
      if (!f.badges.every((x) => b.has(x))) return false;
    }
    if (!ohne.includes("gebiet") && f.gebiet && gebietVon(o) !== f.gebiet) return false;
    if (!ohne.includes("offen") && f.offen && oeffnungAm(wm(o).saisons, tag).zustand !== "offen") return false;
    return true;
  });
}

export function wmSortieren(orte: DddOrt[], sort: WmFilter["sort"]): DddOrt[] {
  return sort === "name" ? [...orte].sort((a, b) => a.name.localeCompare(b.name, "de")) : sortieren(orte);
}

/** Chips mit Anzahl; Schwelle 2, für Eisbahn/Riesenrad/Kindereisenbahn 1 (4.7). Aktive Chips bleiben immer sichtbar. */
export function badgeChips(orte: DddOrt[], alle: DddOrt[], aktiv: string[]): { wert: string; label: string; icon: string; anzahl: number }[] {
  return BADGES.filter((b) => (FILTER_BADGES as readonly string[]).includes(b.wert))
    .map((b) => ({ ...b, anzahl: orte.filter((o) => badges(o, alle).some((x) => x.wert === b.wert)).length }))
    .filter((b) => aktiv.includes(b.wert) || b.anzahl >= (SCHWELLE_EINS.has(b.wert) ? 1 : 2));
}

// ---------- Events: Zuordnung zu Einträgen (3.3) und Kurz-Markt-Liste (4.5), Stufe 1b ----------

/**
 * Cache-Header der Weihnachtsmarkt-Karte je Anfrage: „heute geöffnet“ (offen=1) ohne gültigen ?tag= ist eine fertige
 * Tagesmenge und darf nicht über Mitternacht hinaus aus geteilten Caches kommen (Cursor-Check Stufe 1b).
 */
export function wmKartenCache(sp: Record<string, string | undefined>, oeffentlich: string): string {
  // gleiche Prüfung wie der Bezugstag in der Route (ungültiger Tag → heute → Tagesmenge)
  return sp.offen === "1" && !istGueltigerTag(sp.tag) ? "private, no-store" : oeffentlich;
}

/** Spiegel von data/weihnachtsmaerkte/event_ausschluss.csv (ein Test prüft, dass beide gleich sind). */
export const EVENT_AUSSCHLUSS = new Set<string>([
  "https://prinz.de/events/leipziger-weihnachtsmarkt/2026-12-12/",
]);
/** Titel-Muster für kleine Märkte (4.5). */
export const KURZ_MUSTER = /weihnachtsmarkt|adventsmarkt|wintermarkt|christkindl|weihnachtsbasar|adventsbasar|veihnachtsmarkt|nikolausmarkt|lichterzauber/i;
/**
 * Veranstaltungsorte außerhalb, die in Düsseldorfer Quellen regelmäßig ohne Adresse auftauchen (Event-Ort enthält das Muster).
 * Seit Märkte ohne Adresse durchgelassen werden (18.11.2026) nötig – wiederkehrende Orte hier, Einzelfälle in event_ausschluss.csv.
 */
export const ORTE_AUSSERHALB = /gertrudenhof/i; // Erlebnisbauernhof Gertrudenhof, Hürth
/** Postleitzahlen Düsseldorf, Neuss, Ratingen (4.5). */
const PLZ_ERLAUBT = (plz: number) => (plz >= 40210 && plz <= 40629) || (plz >= 41460 && plz <= 41472) || (plz >= 40878 && plz <= 40885);

type EventLike = { id: string; titel: string; datum: string; datum_bis: string | null; ort: string; adresse: string | null; stadtteil: string | null;
  quelle_name: string | null; quelle_url: string | null; abgesagt: boolean; slug: string | null; kategorie: string };

function musterTreffer(muster: string, text: string): boolean {
  try {
    return new RegExp(muster, "i").test(text);
  } catch {
    return false; // ungültiges Muster prüft schon der Import; hier nie werfen
  }
}

/** Guide-Eintrag, den ein Event meint (über event_muster, Titel und Ort). */
export function eintragFuerEvent(e: Pick<EventLike, "titel" | "ort">, eintraege: DddOrt[]): DddOrt | null {
  const text = `${e.titel} ${e.ort ?? ""}`;
  return eintraege.find((o) => wm(o).event_muster.some((m) => musterTreffer(m, text))) ?? null;
}

/** Gleicher Ort trotz anderer Schreibweise: identisch, oder der kürzere (≥ 3 Zeichen) ist der Anfang des längeren („fft“ ↔ „fft düsseldorf …“). */
export function gleicherOrt(a: string, b: string): boolean {
  if (a === b) return true;
  const [kurz, lang] = a.length <= b.length ? [a, b] : [b, a];
  return kurz.length >= 3 && lang.startsWith(`${kurz} `);
}

/** Kleine Weihnachtsmärkte aus der Eventtabelle (4.5): höchstens 12, nach Datum, ohne Rauschen und ohne Guide-Einträge. */
export function kurzMaerkte<E extends EventLike>(events: E[], eintraege: DddOrt[], heute: string, katalog: (st: string | null) => string | null): E[] {
  const jahrEnde = `${heute.slice(0, 4)}-12-31`;
  const gesehen: { titel: string; datum: string; ort: string }[] = [];
  const norm = (t: string) => t.toLowerCase().replace(/\s+\d{4}\b/g, "").replace(/\s+in\s+düsseldorf\b/g, "").replace(/[^a-zäöüß0-9]+/g, " ").trim();
  return events
    .filter((e) => KURZ_MUSTER.test(e.titel))
    .filter((e) => (e.datum_bis ?? e.datum) >= heute && e.datum <= jahrEnde)
    .filter((e) => !e.abgesagt && e.quelle_name !== "Meetup.com" && !EVENT_AUSSCHLUSS.has(e.quelle_url ?? ""))
    .filter((e) => {
      if (katalog(e.stadtteil)) return true;
      const plz = (e.adresse ?? "").match(/\b(\d{5})\b/);
      if (plz) return PLZ_ERLAUBT(Number(plz[1]));
      // Weder PLZ noch Stadtteil bekannt: durchlassen – die Quellen sind auf Düsseldorf ausgerichtet (Auftraggeber 18.11.2026).
      // Märkte anderer Städte ohne Adresse kommen in data/weihnachtsmaerkte/event_ausschluss.csv (EVENT_AUSSCHLUSS).
      return !e.stadtteil && !ORTE_AUSSERHALB.test(`${e.ort ?? ""} ${e.titel}`);
    })
    .filter((e) => !eintragFuerEvent(e, eintraege))
    // bei Dubletten gewinnt der kürzere Titel (meist das Original, „… in Düsseldorf“ ist oft ein Sammelportal)
    .sort((a, b) => a.datum.localeCompare(b.datum) || a.titel.length - b.titel.length)
    .filter((e) => {
      // Titel, Datum und Ort (wie terminSchluessel) – zwei gleichnamige Märkte an verschiedenen Orten bleiben getrennt,
      // „FFT“ und „FFT Düsseldorf – Forum Freies Theater“ gelten als derselbe Ort (gleicherOrt)
      const k = { titel: norm(e.titel), datum: e.datum, ort: norm(e.ort ?? "") };
      if (gesehen.some((g) => g.titel === k.titel && g.datum === k.datum && gleicherOrt(g.ort, k.ort))) return false;
      gesehen.push(k);
      return true;
    })
    .slice(0, 12);
}

// ---------- FAQ-Antworten aus den Daten (Plan 6.2: feste Satzmuster, Namen und Zeiten aus den Daten) ----------

const link = (o: DddOrt) => `[${o.name}](${wmPfad(o)})`;
function aufzaehlen(teile: string[]): string {
  if (teile.length <= 1) return teile.join("");
  return `${teile.slice(0, -1).join(", ")} und ${teile.at(-1)}`;
}

/** Werte für die Platzhalter der FAQ ({saison}, {faq_start} …). familienHref: in Stufe 1a der Hub ohne Parameter. */
export function faqWerte(alle: DddOrt[], familienHref: string = WM_BASIS): Record<string, string> {
  const hero = heroZahlen(alle);
  // Ohne Daten: Saisonjahr des Guides (keine Uhr – die Seite wird vorgerendert, Plan E5)
  const jahr = Number(hero.jahr ?? SAISON_STANDARD);
  const maerkte = sortieren(alle.filter(istMarkt));
  const ohneAttr = sortieren(alle.filter((o) => !wm(o).attraktion));

  // 1) Start
  const nachStart = new Map<string, DddOrt[]>();
  for (const o of maerkte) {
    const s = aktuelleSaison(wm(o).saisons);
    if (s) nachStart.set(s.von, [...(nachStart.get(s.von) ?? []), o]);
  }
  const starts = [...nachStart.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  const faqStart = starts.length
    ? starts.slice(0, 3).map(([d, os], i) => `${i === 0 ? "Los geht es am" : "Am"} ${datumKurz(d)} mit ${aufzaehlen(os.slice(0, 6).map(link))}${os.length > 6 ? " und weiteren" : ""}.`).join(" ") +
      (hero.bis ? ` Die letzten Märkte schließen am ${datumKurz(hero.bis)}.` : "")
    : "Die Termine für diese Saison stehen noch nicht fest – wir tragen sie ein, sobald die Veranstalter sie veröffentlichen.";

  // 2) Totensonntag
  const ts = totensonntag(jahr);
  const amTs = ohneAttr.concat(alle.filter((o) => wm(o).attraktion)).map((o) => ({ o, x: oeffnungAm(wm(o).saisons, ts) }))
    .filter(({ x }) => x.zustand !== "vor_saison" && x.zustand !== "nach_saison");
  const zu = amTs.filter(({ x }) => x.zustand === "zu").map(({ o }) => link(o));
  const offen = amTs.filter(({ x }) => x.zustand === "offen").map(({ o, x }) => `${link(o)} (${zeitText(x.von, x.bis)})`);
  const unklar = amTs.filter(({ x }) => x.zustand === "unbekannt").map(({ o }) => link(o));
  const faqTs = [
    `Der Totensonntag ist ein stiller Feiertag und fällt ${jahr} auf den ${datumLang(ts)}.`,
    zu.length ? `Geschlossen sind ${aufzaehlen(zu)}.` : "",
    offen.length ? `Geöffnet sind ${aufzaehlen(offen)}.` : "",
    unklar.length ? `Für ${aufzaehlen(unklar)} hat der Veranstalter nichts veröffentlicht.` : "",
  ].filter(Boolean).join(" ");

  // 3) Feiertage
  const tage = sonderTage(jahr).slice(1); // ohne Totensonntag
  const saetze = tage.map(({ datum, name }) => {
    const auf = alle.map((o) => ({ o, x: oeffnungAm(wm(o).saisons, datum) })).filter(({ x }) => x.zustand === "offen")
      .map(({ o, x }) => `${link(o)} ${zeitText(x.von, x.bis)}`);
    return auf.length ? `${name}: ${aufzaehlen(auf)}.` : `${name}: kein Markt mit veröffentlichter Öffnungszeit.`;
  });
  const faqFeiertage = `${saetze.join(" ")} Alle Sonderzeiten stehen in der Tabelle [„Sonderzeiten auf einen Blick“](${WM_BASIS}).`;

  // 4) Eisbahn/Riesenrad
  const mit = (m: string) => alle.filter((o) => wm(o).merkmale[m]?.wert === "ja").map(link);
  const eis = mit("eisbahn"), rad = mit("riesenrad");
  const faqEis = [
    eis.length ? `Eine Eisbahn gibt es bei ${aufzaehlen(eis)}.` : "Für diese Saison ist keine Eisbahn eingetragen.",
    rad.length ? `Ein Riesenrad steht bei ${aufzaehlen(rad)}.` : "",
    "Beide haben eigene Öffnungszeiten und laufen oft länger als die Märkte.",
  ].filter(Boolean).join(" ");

  // 5) Familien
  const fam = ohneAttr.filter((o) => badges(o, alle).some((b) => b.wert === "familien")).map(link);
  const faqFam = fam.length
    ? `Belegtes Programm für Kinder – Karussell, Kindereisenbahn, Puppenbühne oder Mitmachaktionen – gibt es bei ${aufzaehlen(fam)}. Alle Märkte für Familien zeigt die [Übersicht](${familienHref}).`
    : `Sobald ein Veranstalter ein Kinderprogramm veröffentlicht, steht es auf der Seite des Markts; alle Märkte zeigt die [Übersicht](${familienHref}).`;

  return { saison: hero.jahr ?? "", faq_start: faqStart, faq_totensonntag: faqTs, faq_feiertage: faqFeiertage, faq_eisbahn: faqEis, faq_familien: faqFam };
}

/** Kompakte Saisondaten für Browser-Inseln (nur Zeitraum und Zeiten, keine Belege). */
export function saisonsKompakt(saisons: Saisons): Saisons {
  return Object.fromEntries(
    Object.entries(saisons).filter(([, s]) => s.von && s.bis).map(([k, s]) => [k, { von: s.von, bis: s.bis, zeiten: s.zeiten ?? [], sonder: s.sonder ?? [] }]),
  );
}
