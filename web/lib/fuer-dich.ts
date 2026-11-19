// „Für dich“: persönliche Vorschläge aus Interessen und Merkliste (Plan docs/plan-mein-bereich-stufe1-2026-11-18.md,
// Abschnitt 5; ersetzt Kontenplan Abschnitt 13 „fuer-euch“). Rein und getestet (tests/fuer-dich.test.ts):
// keine Datenbank, keine Uhr. Pool, Profil, Merkliste und die Menge sensibler Event-IDs übergibt die Route.
//
// Grundsätze:
// - Sensible Events (E13, S4) sind weder Eingabe der Punkte noch Vorschlag noch Begründung.
// - Ohne Einwilligung (a) gibt es keine Punkte, keinen Ersatz und die Merkliste wird dafür nicht gelesen.
// - Gleichstand über nachEmpfehlung(stufen) wie beliebtAuswahl, kein zweiter Sortierschlüssel.
import { amFokustag, breite, filtern, fokustag, istKostenlos, istMehrtaegig, istSammelort, nachEmpfehlung, uhrzeitenVon, type StufenKontext } from "./ableitungen";
import { plusTage, wochenende, wochentag } from "./datum";
import { KATEGORIEN } from "./kategorien";
import { stadtteilSlug } from "./landing";
import { stadtteilName } from "./stadtteile";
import { norm } from "./termine";
import type { DddEvent } from "./typen";

// ── Typen ────────────────────────────────────────────────────────────────────

/** Fokustag-Regel je Fenster (Plan 4.2/5): „tag“ = ein Tag, „im-fenster“ = Fokustag irgendwo im Fenster, „kein“ = Zeitraum. */
export type Fokus = "kein" | "tag" | "im-fenster";
export interface Fenster {
  von: string;
  bis: string;
  fokus: Fokus;
}

/** Interessen aus profiles.praeferenzen (Kontenplan 4.2), alles optional. */
export interface Interessen {
  kategorien?: string[];
  unterkategorien?: string[];
  stadtteile?: string[];
  merkmale?: string[];
  orte?: string[];
}

/** Gemerktes Event der Konto-Merkliste; gemerktAm aus der Zeile `merkliste`, nicht vom Event. */
export interface Gemerkt {
  event: DddEvent;
  gemerktAm: string;
}

export interface Eingabe {
  /** pool.events (gebündelt), nicht pool.alle */
  events: DddEvent[];
  heute: string;
  stufen: StufenKontext;
  personalisierung: boolean;
  interessen: Interessen | null;
  /** Konto-Merkliste mit Events. Wird ohne Einwilligung (a) nicht angesehen. */
  merkliste: Gemerkt[];
  /** IDs aus event_sensibel (nur von der Route übergeben, nie nach außen) */
  sensibel: ReadonlySet<string>;
}

export interface Vorschlag {
  event: DddEvent;
  punkte: number;
  begruendung: string;
  /** IDs gemerkter (nicht sensibler) Events mit gleicher Reihe oder gleichem Ort – nur intern (Abschnitt 3 der Seite) */
  bezuege: string[];
}

export type StartErgebnis =
  | { art: "ohne-einwilligung" }
  | { art: "leer" }
  | { art: "persoenlich"; liste: Vorschlag[] }
  | { art: "ersatz"; liste: DddEvent[] };

export interface Abschnitt {
  schluessel: "heute" | "wochenende" | "gemerkt" | "interessen";
  titel: string;
  liste: Vorschlag[];
}

export type SeitenErgebnis = { art: "ohne-einwilligung" } | { art: "abschnitte"; abschnitte: Abschnitt[] };

// ── Konstanten ───────────────────────────────────────────────────────────────

/** Höchstzahlen (Plan 4.2 und 3.3) */
export const START_MAX = 8;
export const ABSCHNITT_MAX = 6;
export const INTERESSEN_MAX = 12;
const MINDESTPUNKTE = 2;

const MERKMAL_TEXT: Record<string, string> = {
  kostenlos: "kostenlos",
  "mit-kindern": "mit Kindern",
  abends: "abends",
  tagsueber: "tagsüber",
  wochenende: "am Wochenende",
};

const UNTER_NAME = new Map<string, string>(KATEGORIEN.flatMap((k) => k.unterkategorien.map((u) => [`${k.slug}/${u.slug}`, u.name] as [string, string])));
const KATEGORIE_NAME = new Map<string, string>(KATEGORIEN.map((k) => [k.slug as string, k.name] as [string, string]));

// ── Fenster ──────────────────────────────────────────────────────────────────

/**
 * Persönliches Fenster der Startseite aus dem öffentlichen Zeitraum (Plan 4.2, Tabelle):
 * „Heute“ → sieben Tage im-fenster; anderer einzelner Tag → tag; Zeitraum → kein.
 */
export function startFenster(von: string, bis: string, heute: string): Fenster {
  if (von === bis && von === heute) return { von: heute, bis: plusTage(heute, 6), fokus: "im-fenster" };
  if (von === bis) return { von, bis, fokus: "tag" };
  return { von, bis, fokus: "kein" };
}

// ── Kandidaten ───────────────────────────────────────────────────────────────

function fokusPasst(e: DddEvent, f: Fenster): boolean {
  if (f.fokus === "tag") return amFokustag(e, f.von);
  if (f.fokus === "im-fenster") {
    if (!istMehrtaegig(e)) return true;
    const t = fokustag(e);
    return t >= f.von && t <= f.bis;
  }
  return true;
}

/**
 * Kandidaten im Fenster (gemeinsam für Punkte und Ersatz, Plan 5): mit Langläufern, nicht abgesagt, kein Stamm,
 * nicht vorbei, nicht gemerkt, nicht sensibel, nicht in `ohne`, Fokustag nach Fenster.
 * Ein vergangener einzelner Tag (`/?datum=` vor heute) hat keine Kandidaten (Plan 4.2), auch wenn ein Mehrtägiges
 * noch läuft und dort seinen Fokustag hat. Damit gibt es weder Vorschläge noch Ersatz.
 */
export function kandidaten(e: Eingabe, f: Fenster, ohne: ReadonlySet<string> = new Set()): DddEvent[] {
  if (f.fokus === "tag" && f.von < e.heute) return [];
  const gemerkt = new Set(e.merkliste.map((g) => g.event.id));
  return filtern(e.events, { von: f.von, bis: f.bis, mitLanglaeufern: true }).filter(
    (ev) =>
      !ev.abgesagt &&
      (breite(ev, e.stufen) ?? 0) >= 1 &&
      (ev.datum_bis ?? ev.datum) >= e.heute &&
      !gemerkt.has(ev.id) &&
      !e.sensibel.has(ev.id) &&
      !ohne.has(ev.id) &&
      fokusPasst(ev, f),
  );
}

// ── Punkte ───────────────────────────────────────────────────────────────────

/** Tage der Laufzeit im Fenster (bei fokus „tag“ nur der Fokustag), höchstens 62 Tage. */
function tageImFenster(ev: DddEvent, f: Fenster): string[] {
  if (f.fokus === "tag") return [f.von];
  const start = ev.datum > f.von ? ev.datum : f.von;
  const ende = (ev.datum_bis ?? ev.datum) < f.bis ? (ev.datum_bis ?? ev.datum) : f.bis;
  const tage: string[] = [];
  for (let t = start, i = 0; t <= ende && i < 62; t = plusTage(t, 1), i++) tage.push(t);
  return tage;
}

interface Treffer {
  gewicht: number;
  text: string;
}

/** Bezug zu einem gemerkten Event: gleiche Reihe oder gleicher Ort (Sammelorte ausgenommen). */
function bezugTrifft(ev: DddEvent, g: DddEvent): boolean {
  if (ev.reihe && g.reihe && ev.reihe.slug === g.reihe.slug) return true;
  if (!ev.ort || istSammelort(ev.ort)) return false;
  return norm(ev.ort) !== "" && norm(ev.ort) === norm(g.ort);
}

/** Punkte und Begründung eines Kandidaten (Plan 5). Ohne Einwilligung nie aufrufen. */
export function bewerten(e: Eingabe, ev: DddEvent, f: Fenster): Vorschlag {
  const i = e.interessen ?? {};
  const kategorien = new Set(i.kategorien ?? []);
  const vonAllem = KATEGORIEN.every((k) => kategorien.has(k.slug));
  const unter = new Set(i.unterkategorien ?? []);
  const stadtteile = new Set(i.stadtteile ?? []);
  const merkmale = new Set(i.merkmale ?? []);
  const treffer: Treffer[] = [];

  const unterSchluessel = ev.unterkategorie && ev.unterkategorie !== "keine" ? `${ev.kategorie}/${ev.unterkategorie}` : null;
  if (unterSchluessel && unter.has(unterSchluessel)) {
    treffer.push({ gewicht: 3, text: UNTER_NAME.get(unterSchluessel) ?? KATEGORIE_NAME.get(ev.kategorie) ?? ev.kategorie });
  }
  if (!vonAllem && kategorien.has(ev.kategorie)) treffer.push({ gewicht: 2, text: KATEGORIE_NAME.get(ev.kategorie) ?? ev.kategorie });
  if (ev.stadtteil && stadtteile.has(stadtteilSlug(ev.stadtteil))) treffer.push({ gewicht: 1, text: stadtteilName(ev.stadtteil) });

  const zeiten = uhrzeitenVon(ev);
  const merkmalTrifft: Record<string, boolean> = {
    kostenlos: istKostenlos(ev),
    "mit-kindern": ev.kategorie === "familie",
    abends: zeiten.some((z) => z >= "17:00"),
    tagsueber: zeiten.some((z) => z < "17:00"),
    wochenende: tageImFenster(ev, f).some((t) => [5, 6, 0].includes(wochentag(t))),
  };
  for (const m of Object.keys(MERKMAL_TEXT)) {
    if (merkmale.has(m) && merkmalTrifft[m]) treffer.push({ gewicht: 1, text: MERKMAL_TEXT[m] });
  }

  // Reihe oder Ort eines gemerkten, nicht sensiblen Events: einmal +1 (nicht je Treffer)
  const bezuege = e.merkliste.filter((g) => !e.sensibel.has(g.event.id) && bezugTrifft(ev, g.event));
  if (bezuege.length) {
    const neuestes = [...bezuege].sort(nachBezugVorrang)[0];
    treffer.push({ gewicht: 1, text: `wie ‚${neuestes.event.titel}‘` });
  }

  const punkte = treffer.reduce((s, t) => s + t.gewicht, 0);
  // Begründung: die höchsten zwei Treffer (stabile Reihenfolge der Prüfung), z. B. „Musik · Flingern“
  const begruendung = [...treffer].sort((a, b) => b.gewicht - a.gewicht).slice(0, 2).map((t) => t.text).join(" · ");
  return { event: ev, punkte, begruendung, bezuege: bezuege.map((g) => g.event.id) };
}

/** Zuletzt gemerkt zuerst, bei gleichem Zeitpunkt die größere event_id. */
function nachBezugVorrang(a: Gemerkt, b: Gemerkt): number {
  return b.gemerktAm.localeCompare(a.gemerktAm) || b.event.id.localeCompare(a.event.id);
}

// ── Liste mit Deckeln ────────────────────────────────────────────────────────

function sortieren(e: Eingabe, vorschlaege: Vorschlag[]): Vorschlag[] {
  const gleichstand = nachEmpfehlung(e.stufen);
  return [...vorschlaege].sort((a, b) => b.punkte - a.punkte || gleichstand(a.event, b.event));
}

/**
 * Füllt bis `max` mit Deckeln (Plan 5): höchstens 2 je Kategorie, 1 je Reihe, 2 je Ort (norm, Sammelorte ohne Deckel).
 * Was ein Deckel auslässt, wird nicht nachgeschoben.
 */
export function mitDeckeln(sortiert: Vorschlag[], max: number): Vorschlag[] {
  const kat = new Map<string, number>();
  const reihe = new Map<string, number>();
  const ort = new Map<string, number>();
  const raus: Vorschlag[] = [];
  for (const v of sortiert) {
    if (raus.length >= max) break;
    const ev = v.event;
    const o = ev.ort && !istSammelort(ev.ort) ? norm(ev.ort) : "";
    if ((kat.get(ev.kategorie) ?? 0) >= 2) continue;
    if (ev.reihe && (reihe.get(ev.reihe.slug) ?? 0) >= 1) continue;
    if (o && (ort.get(o) ?? 0) >= 2) continue;
    raus.push(v);
    kat.set(ev.kategorie, (kat.get(ev.kategorie) ?? 0) + 1);
    if (ev.reihe) reihe.set(ev.reihe.slug, (reihe.get(ev.reihe.slug) ?? 0) + 1);
    if (o) ort.set(o, (ort.get(o) ?? 0) + 1);
  }
  return raus;
}

function bewertetImFenster(e: Eingabe, f: Fenster, ohne?: ReadonlySet<string>): { alle: DddEvent[]; treffer: Vorschlag[] } {
  const alle = kandidaten(e, f, ohne);
  const treffer = alle.map((ev) => bewerten(e, ev, f)).filter((v) => v.punkte >= MINDESTPUNKTE);
  return { alle, treffer: sortieren(e, treffer) };
}

// ── Startseite (Plan 4.2) ────────────────────────────────────────────────────

/**
 * Modul „Für dich empfohlen“: persönliche Liste (bis 8, Deckel); ohne Treffer bei nicht leerer Kandidatenmenge der
 * Ersatz „Beliebt in Düsseldorf“ (gleiche Kandidaten, nachEmpfehlung, bis 8, ohne Deckel); sonst leer.
 */
export function startVorschlaege(e: Eingabe, f: Fenster, ohne: ReadonlySet<string> = new Set()): StartErgebnis {
  if (!e.personalisierung) return { art: "ohne-einwilligung" };
  const { alle, treffer } = bewertetImFenster(e, f, ohne);
  if (!alle.length) return { art: "leer" };
  const liste = mitDeckeln(treffer, START_MAX);
  if (liste.length) return { art: "persoenlich", liste };
  return { art: "ersatz", liste: [...alle].sort(nachEmpfehlung(e.stufen)).slice(0, START_MAX) };
}

/** Zahl für die Kachel auf /konto (Plan 6): persönliche Liste im Fenster „heute + 6 Tage“, ohne Ersatz und ohne `ohne`. */
export function anzahlVorschlaege(e: Eingabe): number | null {
  if (!e.personalisierung) return null;
  const r = startVorschlaege(e, startFenster(e.heute, e.heute, e.heute));
  return r.art === "persoenlich" ? r.liste.length : 0;
}

// ── Seite /konto/fuer-dich (Plan 3.3) ────────────────────────────────────────

/** Vier Abschnitte, jedes Event nur einmal (erster passender Abschnitt), Deckel je Abschnitt, kein Ersatz. */
export function fuerDichSeite(e: Eingabe): SeitenErgebnis {
  if (!e.personalisierung) return { art: "ohne-einwilligung" };
  const benutzt = new Set<string>();
  const abschnitte: Abschnitt[] = [];
  const frei = (vs: Vorschlag[]) => vs.filter((v) => !benutzt.has(v.event.id));
  const merken = (vs: Vorschlag[]) => vs.forEach((v) => benutzt.add(v.event.id));

  // 1. Heute und morgen
  const a1 = mitDeckeln(bewertetImFenster(e, { von: e.heute, bis: plusTage(e.heute, 1), fokus: "im-fenster" }).treffer, ABSCHNITT_MAX);
  merken(a1);
  if (a1.length) abschnitte.push({ schluessel: "heute", titel: "Heute und morgen für dich", liste: a1 });

  // 2. Dein Wochenende: Fr–So aus wochenende(), nicht zeitraumAuflösen (schneidet an Sa/So den Freitag ab)
  const w = wochenende(e.heute);
  const a2 = mitDeckeln(frei(bewertetImFenster(e, { von: w.fr, bis: w.so, fokus: "im-fenster" }).treffer), ABSCHNITT_MAX);
  merken(a2);
  if (a2.length) abschnitte.push({ schluessel: "wochenende", titel: "Dein Wochenende", liste: a2 });

  // 3. und 4. die nächsten 14 Tage
  const vierzehn = frei(bewertetImFenster(e, { von: e.heute, bis: plusTage(e.heute, 13), fokus: "im-fenster" }).treffer);

  // 3. Weil du ‚…‘ gemerkt hast: genau ein Bezugs-Event (meiste Treffer, dann zuletzt gemerkt, dann größere event_id)
  const zaehler = new Map<string, number>();
  for (const v of vierzehn) for (const id of v.bezuege) zaehler.set(id, (zaehler.get(id) ?? 0) + 1);
  const bezug = e.merkliste
    .filter((g) => zaehler.has(g.event.id) && !e.sensibel.has(g.event.id))
    .sort((a, b) => (zaehler.get(b.event.id)! - zaehler.get(a.event.id)!) || nachBezugVorrang(a, b))[0];
  if (bezug) {
    const a3 = mitDeckeln(vierzehn.filter((v) => v.bezuege.includes(bezug.event.id)), ABSCHNITT_MAX);
    merken(a3);
    if (a3.length) abschnitte.push({ schluessel: "gemerkt", titel: `Weil du ‚${bezug.event.titel}‘ gemerkt hast`, liste: a3 });
  }

  // 4. Mehr aus deinen Interessen
  const a4 = mitDeckeln(frei(vierzehn), INTERESSEN_MAX);
  merken(a4);
  if (a4.length) abschnitte.push({ schluessel: "interessen", titel: "Mehr aus deinen Interessen", liste: a4 });

  return { art: "abschnitte", abschnitte };
}
