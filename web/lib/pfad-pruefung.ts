// Pfadprüfung für proxy.ts (SEO-/GEO-Plan Nov. 2026, Maßnahme 12 „Echte Statuscodes“):
// Entscheidet VOR dem Rendern, ob eine dynamische URL existiert. Mit cacheComponents streamt das Layout,
// bevor die Seite notFound() oder redirect() aufrufen kann – dann bleibt der Status 200 (Soft-404,
// Meta-Weiterleitung). Hier dagegen: echte 308 und echte 404.
//
// Grundsatz: Nur bei einer ERFOLGREICHEN Abfrage ohne Treffer gilt eine URL als fehlend. Fehler, fehlende
// Zugangsdaten oder Zeitüberschreitung → „weiter“ (Seite wird normal ausgeliefert, nie fälschlich 404).
import { istSichtbarerClub } from "./clubs";
import { istGueltigerTag } from "./datum";
import { kategorieAusDb } from "./kategorien";
import {
  guideStadtteilPfad, kanonischerStadtteil, kategorieGueltig, kategoriePfad, stadtteilAusSlug, stadtteilPfad, unterkategorieGueltig,
} from "./landing";
import { istRubrik, RESERVIERT, SLUG_MUSTER } from "./magazin";
import { eventPfad } from "./pfade";
import type { DddOrt, KategorieSlug } from "./typen";

export type Pruefung = { art: "weiter" } | { art: "umleiten"; ziel: string } | { art: "fehlt" };
const WEITER: Pruefung = { art: "weiter" };
const FEHLT: Pruefung = { art: "fehlt" };

// ---------- Routen erkennen (rein, ohne Netz) ----------

export type Route =
  | { typ: "ungueltig" }
  | { typ: "event-uuid"; id: string }
  | { typ: "event"; kategorie: string; slug: string }
  | { typ: "tag"; datum: string }
  | { typ: "reihe"; slug: string }
  | { typ: "ort"; hub: OrtHub; slug: string }
  | { typ: "kategorie"; slug: string }
  | { typ: "unterkategorie"; kategorie: string; unter: string }
  | { typ: "stadtteil"; slug: string }
  | { typ: "guide-stadtteil"; hub: OrtHub; slug: string }
  // Ortsseiten (Plan Locations 3.10)
  | { typ: "spielstaette"; slug: string }
  // Magazin (Plan Redaktion 5.1, T4)
  | { typ: "feed-alt" }
  | { typ: "magazin-fest" }
  | { typ: "magazin-rubrik"; rubrik: string }
  | { typ: "magazin-autor"; slug: string }
  | { typ: "magazin-vorschau"; id: string }
  | { typ: "magazin-beitrag"; slug: string };

export type OrtHub = "restaurants-cafes" | "kneipen-bars" | "clubs" | "spielplaetze" | "weihnachtsmaerkte";
const HUBS: OrtHub[] = ["restaurants-cafes", "kneipen-bars", "clubs", "spielplaetze", "weihnachtsmaerkte"];
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function teil(roh: string): string | null {
  try {
    return decodeURIComponent(roh);
  } catch {
    return null;
  }
}

/** Welche geprüfte Route ist das? null = nicht unsere Sache (normal ausliefern). */
export function routeVon(pfad: string): Route | null {
  const s = pfad.replace(/\/+$/, "").split("/").slice(1).map(teil);
  if (s.some((x) => x === null || x === "")) return null;
  const [a, b, c, d, e] = s as string[];
  if (a === "event" && b && !c) return UUID.test(b) ? { typ: "event-uuid", id: b.toLowerCase() } : { typ: "ungueltig" };
  if (a === "event" && b && c && !d) return { typ: "event", kategorie: b, slug: c };
  if (a === "tag" && b && !c) return { typ: "tag", datum: b };
  if (a === "reihe" && b && !c) return { typ: "reihe", slug: b };
  if (a === "guides" && b && c && !d && (HUBS as string[]).includes(b)) return { typ: "ort", hub: b as OrtHub, slug: c };
  if (a === "guides" && b && c === "stadtteil" && d && !e && (HUBS as string[]).includes(b)) return { typ: "guide-stadtteil", hub: b as OrtHub, slug: d };
  if (a === "kategorie" && b && !c) return { typ: "kategorie", slug: b };
  if (a === "kategorie" && b && c && !d) return { typ: "unterkategorie", kategorie: b, unter: c };
  if (a === "stadtteil" && b && !c) return { typ: "stadtteil", slug: b };
  if (a === "orte" && b && !c) return { typ: "spielstaette", slug: b };
  if (a === "orte" && b && c) return { typ: "ungueltig" };
  if (a === "feed.xml" && !b) return { typ: "feed-alt" };
  if (a === "magazin") return magazinRoute(b, c, d);
  return null;
}

/** Magazin-Pfade (Plan Redaktion 5.1): feste Seiten, Rubrik, Autor, Vorschau, Beitrag; mehr Pfadteile → ungültig. */
function magazinRoute(b?: string, c?: string, d?: string): Route {
  if (d) return { typ: "ungueltig" };
  if (!b) return { typ: "magazin-fest" };
  if (!c) {
    if (b === "feed.xml" || b === "redaktion") return { typ: "magazin-fest" };
    if ((RESERVIERT as readonly string[]).includes(b)) return { typ: "ungueltig" };
    return { typ: "magazin-beitrag", slug: b };
  }
  if (b === "rubrik") return { typ: "magazin-rubrik", rubrik: c };
  if (b === "autor") return { typ: "magazin-autor", slug: c };
  if (b === "vorschau") return { typ: "magazin-vorschau", id: c };
  return { typ: "ungueltig" };
}

/** Echter Kalendertag – dieselbe Regel wie die Tagesseite (lib/datum.ts, istGueltigerTag). */
export const tagGueltig = (datum: string): boolean => istGueltigerTag(datum);

// ---------- Abfragen mit Zwischenspeicher (pro Server-Prozess) ----------

const TREFFER_MS = 10 * 60 * 1000; // wie der Daten-Cache der Seiten
const FEHLT_MS = 2 * 60 * 1000; // neue Events erscheinen schnell
const MAX_EINTRAEGE = 5000;
const speicher = new Map<string, { wert: unknown; bis: number; seit: number }>();

// Stand der Orte (Admin-Bereich, Plan Admin-Dashboard 4.7, Cursor-Prüfung 3a Befund 1): Nach Schließen, Zusammenlegen
// oder Freischalten verwirft die Route alle gemerkten Orte-Einträge (ort:, ort-weiter:, ort-id:). Über globalThis,
// damit es auch gilt, wenn Proxy und Route-Handler getrennt gebündelt sind (gleicher Node-Prozess).
const ORTE_STAND = "__dddOrteStand";

/** Alle gemerkten Orte-Entscheidungen dieses Prozesses ungültig machen. */
export function orteZwischenspeicherVerwerfen(): void {
  (globalThis as Record<string, unknown>)[ORTE_STAND] = Date.now();
}

function orteStand(): number {
  const w = (globalThis as Record<string, unknown>)[ORTE_STAND];
  return typeof w === "number" ? w : 0;
}

async function gemerkt<T>(
  schluessel: string, laden: () => Promise<T | undefined>, zeiten: { treffer: number; fehlt: number } = { treffer: TREFFER_MS, fehlt: FEHLT_MS },
): Promise<T | undefined> {
  const e = speicher.get(schluessel);
  const veraltet = !!e && schluessel.startsWith("ort") && e.seit <= orteStand();
  if (e && e.bis > Date.now() && !veraltet) return e.wert as T;
  const wert = await laden();
  if (wert === undefined) return undefined; // Fehler nicht merken
  if (speicher.size >= MAX_EINTRAEGE) speicher.delete(speicher.keys().next().value as string);
  const jetzt = Date.now();
  speicher.set(schluessel, { wert, bis: jetzt + (wert === null ? zeiten.fehlt : zeiten.treffer), seit: jetzt });
  return wert;
}

/** Nur für Tests: Zwischenspeicher leeren. */
export function speicherLeeren(): void {
  speicher.clear();
}

/** Magazin (Plan Redaktion T10): Treffer 5 min, Fehltreffer 60 s. */
const MAGAZIN_ZEITEN = { treffer: 5 * 60 * 1000, fehlt: 60 * 1000 };

/** REST-Abfrage an Supabase. undefined = Fehler (→ weiter), [] = erfolgreich, aber nichts gefunden. */
async function abfrage<T>(tabelle: string, parameter: string): Promise<T[] | undefined> {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!url || !key) return undefined;
  try {
    const r = await fetch(`${url}/rest/v1/${tabelle}?${parameter}`, {
      headers: { apikey: key, Authorization: `Bearer ${key}` },
      signal: AbortSignal.timeout(3000),
    });
    if (!r.ok) return undefined;
    return (await r.json()) as T[];
  } catch {
    return undefined;
  }
}

/**
 * Wie abfrage(), aber mit dem Service-Schlüssel (Plan Redaktion 3.1, Cursor-Prüfung 2 Befund 2): Nur so sieht der
 * Proxy status, alte_slugs und vorschau_hash. Nur serverseitig; der Proxy gibt nie Inhalt weiter, nur weiter/404/308.
 */
async function dienstAbfrage<T>(tabelle: string, parameter: string): Promise<T[] | undefined> {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_KEY;
  if (!url || !key) return undefined;
  try {
    const r = await fetch(`${url}/rest/v1/${tabelle}?${parameter}`, {
      headers: { apikey: key, Authorization: `Bearer ${key}` },
      signal: AbortSignal.timeout(3000),
    });
    if (!r.ok) return undefined;
    return (await r.json()) as T[];
  } catch {
    return undefined;
  }
}

type EventKopf = { id: string; kategorie: KategorieSlug; slug: string | null };

async function eventLaden(feld: "id" | "slug", wert: string): Promise<EventKopf | null | undefined> {
  return gemerkt(`event:${feld}:${wert}`, async () => {
    const z = await abfrage<{ id: string; kategorie: string | null; slug: string | null }>(
      "events", `select=id,kategorie,slug&abgelehnt=eq.false&${feld}=eq.${encodeURIComponent(wert)}&limit=1`);
    if (z === undefined) return undefined;
    // Wie die Seite (lib/daten.ts): DB-Wert „family“ heißt auf der Website „familie“
    return z[0] ? { ...z[0], kategorie: kategorieAusDb(z[0].kategorie) } : null;
  });
}

async function reiheVorhanden(slug: string): Promise<boolean | undefined> {
  const r = await gemerkt(`reihe:${slug}`, async () => {
    const z = await abfrage<{ slug: string }>("reihen", `select=slug&slug=eq.${encodeURIComponent(slug)}&limit=1`);
    return z === undefined ? undefined : z.length ? true : null;
  });
  return r === undefined ? undefined : r === true;
}

export type OrtKopf = {
  typ: string; aktiv: boolean; qualitaets_score: number | null;
  club: unknown; club_score: unknown; club_freigegeben: unknown; auch_club: unknown; kein_club?: unknown;
  /** Nur Spielplätze: Stadtteil und erster Freischalt-Tag (Weiterleitung abgeschalteter Plätze, Plan 5.5) */
  stadtteil?: string | null; freigeschaltet_am?: string | null;
  /** Nur Weihnachtsmärkte: erster Freischalt-Tag (Plan Weihnachtsmärkte 5.5) */
  wm_freigeschaltet_am?: string | null;
};

async function ortLaden(slug: string): Promise<OrtKopf | null | undefined> {
  return gemerkt(`ort:${slug}`, async () => {
    const z = await abfrage<OrtKopf>(
      "orte",
      `select=typ,aktiv,qualitaets_score,stadtteil,club:extras->club,club_score:extras->club_score,` +
        `club_freigegeben:extras->club_freigegeben,auch_club:extras->auch_club,kein_club:extras->kein_club,` +
        `freigeschaltet_am:extras->spielplatz->>freigeschaltet_am,wm_freigeschaltet_am:extras->weihnachtsmarkt->>freigeschaltet_am&slug=eq.${encodeURIComponent(slug)}&limit=1`,
    );
    return z === undefined ? undefined : (z[0] ?? null);
  });
}

// ---------- Entscheidungen ----------

const MIN_SCORE = 7; // wie MIN_QUALITAETS_SCORE in lib/orte.ts
const HUB_TYPEN: Record<Exclude<OrtHub, "clubs" | "spielplaetze" | "weihnachtsmaerkte">, string[]> = {
  "restaurants-cafes": ["restaurant", "imbiss", "cafe"],
  "kneipen-bars": ["kneipe"],
};

/**
 * Spielplätze (Plan 5.5): sichtbar = aktiv, ohne Score. Nie freigeschaltet → 404. Abgeschaltet (inaktiv mit
 * freigeschaltet_am) → dauerhaft auf die Stadtteilseite (stadtteilSlug, „Hafen“ → medienhafen), ohne gültigen Stadtteil
 * auf den Hub. Eine einmal indexierte URL endet nie in einer 404.
 */
export function spielplatzEntscheidung(o: OrtKopf | null): Pruefung {
  if (!o || o.typ !== "spielplatz") return FEHLT;
  if (o.aktiv) return WEITER;
  if (!o.freigeschaltet_am) return FEHLT;
  const st = kanonischerStadtteil(o.stadtteil);
  return { art: "umleiten", ziel: st ? guideStadtteilPfad("spielplaetze", st) : "/guides/spielplaetze" };
}

/**
 * Weihnachtsmärkte, die mit einem anderen zusammengelegt und danach gelöscht wurden: alter Slug → verbliebener Slug.
 * Schadow-Markt = Märchen-Markt am Schadowplatz (Auftraggeber 18.11.2026).
 */
export const WM_ZUSAMMENGELEGT: Readonly<Record<string, string>> = {
  "schadow-markt-stadtmitte": "maerchen-markt-stadtmitte",
};

/**
 * Weihnachtsmärkte (Plan Weihnachtsmärkte 5.5): sichtbar = aktiv und Typ, ohne Score. Nie freigeschaltet oder unbekannt → 404.
 * Abgeschaltet (inaktiv mit freigeschaltet_am) → dauerhaft auf den Hub (es gibt keine Stadtteilseiten).
 */
export function weihnachtsmarktEntscheidung(o: OrtKopf | null): Pruefung {
  if (!o || o.typ !== "weihnachtsmarkt") return FEHLT;
  if (o.aktiv) return WEITER;
  if (!o.wm_freigeschaltet_am) return FEHLT;
  return { art: "umleiten", ziel: "/guides/weihnachtsmaerkte" };
}

/** Im Club-Hub sichtbar? Dieselbe Regel wie die Website (lib/clubs.ts). */
export function clubSichtbar(o: OrtKopf): boolean {
  const ort = {
    typ: o.typ,
    qualitaets_score: o.qualitaets_score,
    extras: { club: o.club, club_score: o.club_score, club_freigegeben: o.club_freigegeben, auch_club: o.auch_club, kein_club: o.kein_club },
  } as unknown as DddOrt;
  return o.aktiv && istSichtbarerClub(ort);
}

/** Hub, in dem ein Ort (kein Club) seine sichtbare Seite hat – sonst null. */
function sichtbarerHub(o: OrtKopf): Exclude<OrtHub, "clubs" | "spielplaetze" | "weihnachtsmaerkte"> | null {
  if (!o.aktiv || (o.qualitaets_score ?? 0) < MIN_SCORE) return null;
  const hubs = Object.keys(HUB_TYPEN) as Exclude<OrtHub, "clubs" | "spielplaetze" | "weihnachtsmaerkte">[];
  return hubs.find((h) => HUB_TYPEN[h].includes(o.typ)) ?? null;
}

/** Entscheidung für einen Ort unter /guides/<hub>/<slug> (rein, testbar). */
export function ortEntscheidung(hub: OrtHub, slug: string, o: OrtKopf | null): Pruefung {
  if (hub === "spielplaetze") return spielplatzEntscheidung(o);
  // Vor jedem Zugriff auf HUB_TYPEN – der neue Hub steht dort nicht (Plan Weihnachtsmärkte 5.5)
  if (hub === "weihnachtsmaerkte") {
    // Zusammengelegter, aus der Tabelle gelöschter Eintrag → dauerhaft auf den verbliebenen (nie 404 für eine indexierte URL)
    const neu = o ? undefined : WM_ZUSAMMENGELEGT[slug];
    return neu ? { art: "umleiten", ziel: `/guides/weihnachtsmaerkte/${neu}` } : weihnachtsmarktEntscheidung(o);
  }
  if (!o) return FEHLT;
  if (hub === "clubs") {
    if (clubSichtbar(o)) return WEITER;
    // Aus dem Club-Hub genommen, aber im eigenen Hub sichtbar (z. B. Konvex → Bars): dauerhaft dorthin
    const eigener = sichtbarerHub(o);
    return eigener ? { art: "umleiten", ziel: `/guides/${eigener}/${encodeURIComponent(slug)}` } : FEHLT;
  }
  const sichtbar = o.aktiv && HUB_TYPEN[hub].includes(o.typ) && (o.qualitaets_score ?? 0) >= MIN_SCORE;
  if (sichtbar) return WEITER;
  // Zum Club umgetypt (früher hier gelistet) oder nur als Club sichtbar (auch_club, Score hier < 7):
  // diese URL dauerhaft auf die Club-Seite. Orte mit sichtbarer Seite in einem anderen Hub bleiben 404 (eine URL je Ort).
  if (!sichtbarerHub(o) && clubSichtbar(o)) return { art: "umleiten", ziel: `/guides/clubs/${encodeURIComponent(slug)}` };
  return FEHLT;
}

// ---------- Ortsseiten /orte (Plan Locations 3.3 Punkt 4, 3.10) ----------

/**
 * Kanonische Guide-URL einer sichtbaren Guide-Zeile – oder null (unsichtbar, kein Hub, Ausflug/Wochenend-Trip).
 * Dieselben Regeln wie ortEntscheidung: Restaurant/Café/Imbiss/Kneipe über den eigenen Hub (Score ≥ 7), sonst als
 * Club, wenn im Club-Hub sichtbar (auch_club); Spielplatz/Weihnachtsmarkt, wenn aktiv. Nie eine zweite Ansicht.
 */
export function guideZiel(o: OrtKopf, slug: string): string | null {
  const s = encodeURIComponent(slug);
  if (!o.aktiv) return null;
  if (o.typ === "spielplatz") return `/guides/spielplaetze/${s}`;
  if (o.typ === "weihnachtsmarkt") return `/guides/weihnachtsmaerkte/${s}`;
  if (o.typ === "ausflug" || o.typ === "wochenendtipp" || o.typ === "spielstaette") return null;
  const hub = sichtbarerHub(o);
  if (hub) return `/guides/${hub}/${s}`;
  return clubSichtbar(o) ? `/guides/clubs/${s}` : null;
}

/** Zeile hinter einer Weiterleitung (über ziel_ort_id): Slug und die Felder für guideZiel. */
type ZielKopf = OrtKopf & { slug: string };

/**
 * Entscheidung für /orte/<slug> (rein, testbar). `eigen`: Zeile mit diesem Slug (anon: nur aktive),
 * `weiter`: Eintrag in ort_weiterleitungen (undefined = keiner), `ziel`: Zielzeile der Weiterleitung (null = nicht
 * sichtbar/gelöscht/leer). Eine Stufe, keine Ketten; unsichtbares Ziel → /orte (nie ein 308 auf eine 404).
 */
export function spielstaetteEntscheidung(
  slug: string, eigen: OrtKopf | null, weiter: { ziel_ort_id: string | null } | undefined, ziel: ZielKopf | null,
): Pruefung {
  if (eigen) {
    if (eigen.typ === "spielstaette") return eigen.aktiv ? WEITER : FEHLT;
    const g = guideZiel(eigen, slug);
    return g ? { art: "umleiten", ziel: g } : FEHLT;
  }
  const wm = WM_ZUSAMMENGELEGT[slug];
  if (wm) return { art: "umleiten", ziel: `/guides/weihnachtsmaerkte/${wm}` };
  if (!weiter) return FEHLT;
  if (!ziel) return { art: "umleiten", ziel: "/orte" };
  if (ziel.typ === "spielstaette") return { art: "umleiten", ziel: `/orte/${encodeURIComponent(ziel.slug)}` };
  return { art: "umleiten", ziel: guideZiel(ziel, ziel.slug) ?? "/orte" };
}

const ORT_KOPF_SPALTEN =
  "typ,aktiv,qualitaets_score,stadtteil,club:extras->club,club_score:extras->club_score," +
  "club_freigegeben:extras->club_freigegeben,auch_club:extras->auch_club,kein_club:extras->kein_club";

async function weiterleitungLaden(slug: string): Promise<{ ziel_ort_id: string | null } | null | undefined> {
  return gemerkt(`ort-weiter:${slug}`, async () => {
    const z = await abfrage<{ ziel_ort_id: string | null }>(
      "ort_weiterleitungen", `select=ziel_ort_id&alter_slug=eq.${encodeURIComponent(slug)}&limit=1`);
    return z === undefined ? undefined : (z[0] ?? null);
  });
}

async function zielLaden(id: string): Promise<ZielKopf | null | undefined> {
  return gemerkt(`ort-id:${id}`, async () => {
    const z = await abfrage<ZielKopf>("orte", `select=slug,${ORT_KOPF_SPALTEN}&id=eq.${encodeURIComponent(id)}&limit=1`);
    return z === undefined ? undefined : (z[0] ?? null);
  });
}

/** /orte/<slug>: Fehler bei einer der Abfragen → „weiter“ (nie ein falscher 308 auf /orte). */
async function spielstaettePruefen(slug: string): Promise<Pruefung> {
  const eigen = await ortLaden(slug);
  if (eigen === undefined) return WEITER;
  if (eigen) return spielstaetteEntscheidung(slug, eigen, undefined, null);
  if (WM_ZUSAMMENGELEGT[slug]) return spielstaetteEntscheidung(slug, null, undefined, null);
  const weiter = await weiterleitungLaden(slug);
  if (weiter === undefined) return WEITER;
  if (weiter === null) return FEHLT;
  let ziel: ZielKopf | null = null;
  if (weiter.ziel_ort_id) {
    const z = await zielLaden(weiter.ziel_ort_id);
    if (z === undefined) return WEITER;
    ziel = z;
  }
  return spielstaetteEntscheidung(slug, null, weiter, ziel);
}

// ---------- Magazin (Plan Redaktion 5.1) ----------

export type MagazinKopf = { slug: string; status: string; veroeffentlicht_am: string | null };

/** Sichtbar = veröffentlicht und Zeitpunkt erreicht – zur Prüfzeit gerechnet, nicht beim Merken (Cursor-Prüfung 4 Befund 4). */
export function magazinSichtbar(k: MagazinKopf, jetzt: number = Date.now()): boolean {
  if (k.status !== "veroeffentlicht" || !k.veroeffentlicht_am) return false;
  const t = Date.parse(k.veroeffentlicht_am);
  return Number.isFinite(t) && t <= jetzt;
}

/**
 * Entscheidung für /magazin/<slug> (rein, testbar): sichtbarer Beitrag → weiter; alter Slug eines sichtbaren Beitrags →
 * 308 auf den aktuellen; sonst 404 (auch Entwurf, zurückgezogen, Zukunft).
 */
export function magazinBeitragEntscheidung(eigen: MagazinKopf | null, alt: MagazinKopf | null, jetzt: number = Date.now()): Pruefung {
  if (eigen) return magazinSichtbar(eigen, jetzt) ? WEITER : FEHLT;
  if (alt && magazinSichtbar(alt, jetzt)) return { art: "umleiten", ziel: `/magazin/${alt.slug}` };
  return FEHLT;
}

async function magazinKopfLaden(slug: string): Promise<{ eigen: MagazinKopf | null; alt: MagazinKopf | null } | null | undefined> {
  return gemerkt(`magazin:${slug}`, async () => {
    const auswahl = "select=slug,status,veroeffentlicht_am";
    const eigen = await dienstAbfrage<MagazinKopf>("magazin_beitraege", `${auswahl}&slug=eq.${encodeURIComponent(slug)}&limit=1`);
    if (eigen === undefined) return undefined;
    if (eigen[0]) return { eigen: eigen[0], alt: null };
    const alt = await dienstAbfrage<MagazinKopf>("magazin_beitraege", `${auswahl}&alte_slugs=cs.${encodeURIComponent(`{${slug}}`)}&limit=1`);
    if (alt === undefined) return undefined;
    return alt[0] ? { eigen: null, alt: alt[0] } : null;
  }, MAGAZIN_ZEITEN);
}

async function autorAktiv(slug: string): Promise<boolean | undefined> {
  const r = await gemerkt(`magazin-autor:${slug}`, async () => {
    const z = await dienstAbfrage<{ slug: string }>("magazin_autoren", `select=slug&slug=eq.${encodeURIComponent(slug)}&aktiv=is.true&limit=1`);
    return z === undefined ? undefined : z.length ? true : null;
  }, MAGAZIN_ZEITEN);
  return r === undefined ? undefined : r === true;
}

const UUID_FORM = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** SHA-256 als Hex (Web Crypto: läuft im Proxy wie in Node). */
export async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Vergleich zweier gleich langer Hex-Werte ohne frühen Abbruch (zeitkonstant). */
export function gleichZeitkonstant(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let unterschied = 0;
  for (let i = 0; i < a.length; i++) unterschied |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return unterschied === 0;
}

/**
 * Vorschau (Plan 5.3): UUID, Schlüssel gesetzt, SHA-256(Schlüssel) = vorschau_hash, Status entwurf/in_pruefung.
 * Nicht gemerkt. Jeder Fehler → 404: Ein Entwurf darf nie durchrutschen.
 */
export async function vorschauPruefen(id: string, schluessel: string | null): Promise<Pruefung> {
  if (!UUID_FORM.test(id) || !schluessel || schluessel.length > 200) return FEHLT;
  const z = await dienstAbfrage<{ vorschau_hash: string | null }>(
    "magazin_beitraege", `select=vorschau_hash&id=eq.${id.toLowerCase()}&status=in.(entwurf,in_pruefung)&limit=1`);
  const hash = z?.[0]?.vorschau_hash;
  if (!hash || !/^[0-9a-f]{64}$/.test(hash)) return FEHLT;
  return gleichZeitkonstant(await sha256Hex(schluessel), hash) ? WEITER : FEHLT;
}

/** Entscheidung für einen Pfad. Netzwerkfehler → weiter (außer Magazin-Vorschau). `suche` nur für die Vorschau. */
export async function pfadPruefen(pfad: string, suche?: URLSearchParams): Promise<Pruefung> {
  const route = routeVon(pfad);
  if (!route) return WEITER;
  switch (route.typ) {
    case "ungueltig":
      return FEHLT;
    case "tag":
      return tagGueltig(route.datum) ? WEITER : FEHLT;
    case "event-uuid": {
      const e = await eventLaden("id", route.id);
      if (e === undefined) return WEITER;
      if (e === null) return FEHLT;
      return e.slug ? { art: "umleiten", ziel: eventPfad(e) } : WEITER;
    }
    case "event": {
      const e = await eventLaden("slug", route.slug);
      if (e === undefined) return WEITER;
      if (e === null) return FEHLT;
      // Falsche Kategorie im Pfad wäre sonst eine zweite URL für dasselbe Event
      return e.kategorie === route.kategorie ? WEITER : { art: "umleiten", ziel: eventPfad(e) };
    }
    case "reihe": {
      const da = await reiheVorhanden(route.slug);
      return da === undefined || da ? WEITER : FEHLT;
    }
    // Landingpages: rein aus dem Katalog entschieden, ohne Netz
    case "kategorie":
      return kategorieGueltig(route.slug) ? WEITER : FEHLT;
    case "unterkategorie":
      // Die Unterkategorie muss zur Kategorie gehören (/kategorie/musik/theater ist 404), „keine“ ist nie gültig
      return unterkategorieGueltig(route.kategorie, route.unter) ? WEITER : FEHLT;
    case "stadtteil":
      return stadtteilAusSlug(route.slug) ? WEITER : FEHLT;
    case "guide-stadtteil":
      // Weihnachtsmärkte haben keine Stadtteilseiten (Plan E9): immer 404, auch bei gültigem Stadtteil
      if (route.hub === "weihnachtsmaerkte") return FEHLT;
      return stadtteilAusSlug(route.slug, true) ? WEITER : FEHLT;
    case "ort": {
      const o = await ortLaden(route.slug);
      return o === undefined ? WEITER : ortEntscheidung(route.hub, route.slug, o);
    }
    case "spielstaette":
      return spielstaettePruefen(route.slug);
    case "feed-alt":
      return { art: "umleiten", ziel: "/magazin/feed.xml" };
    case "magazin-fest":
      return WEITER;
    case "magazin-rubrik":
      return istRubrik(route.rubrik) ? WEITER : FEHLT;
    case "magazin-autor": {
      if (!SLUG_MUSTER.test(route.slug)) return FEHLT;
      const da = await autorAktiv(route.slug);
      return da === undefined || da ? WEITER : FEHLT;
    }
    case "magazin-vorschau":
      return vorschauPruefen(route.id, suche?.get("s") ?? null);
    case "magazin-beitrag": {
      if (!SLUG_MUSTER.test(route.slug)) return FEHLT;
      const k = await magazinKopfLaden(route.slug);
      if (k === undefined) return WEITER;
      return k === null ? FEHLT : magazinBeitragEntscheidung(k.eigen, k.alt);
    }
  }
}

/**
 * /entdecken mit genau EINEM Filter, der eine Landingpage trifft → Ziel der 301 (SEO-/GEO-Plan, Maßnahme 2).
 * Interne Links tragen immer zusätzlich ein Datum und bleiben deshalb Filteransicht.
 */
export function entdeckenZiel(sp: URLSearchParams): string | null {
  const gesetzt = [...sp.entries()].filter(([, v]) => v !== "");
  if (gesetzt.length !== 1) return null;
  const [schluessel, wert] = gesetzt[0];
  if (schluessel === "kategorie") return kategoriePfad(wert);
  if (schluessel === "stadtteil") return stadtteilPfad(wert);
  // Nur der bekannte Wert – „preis=sonstwas“ bleibt Filteransicht
  if (schluessel === "preis" && wert === "kostenlos") return "/kostenlos";
  return null;
}
