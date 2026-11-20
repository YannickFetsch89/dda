// Ortsseiten /orte (Plan docs/plan-locations-2026-11-18.md, Abschnitt 3.8–3.13): reine Hilfen ohne Datenzugriff.
// Eine Spielstätte ist eine `orte`-Zeile mit typ = 'spielstaette'; ihr Profil liegt in extras.spielstaette.
import type { DddOrt } from "./typen";

export const ORTE_BASIS = "/orte";

/** Profil einer Spielstätte aus extras.spielstaette (Plan 3.3 Punkt 5). */
export interface SpielstaettenProfil {
  art: string | null;
  zeileTyp: "haus" | "saal" | "standort" | "filiale";
  eventOrte: string[];
  adresseBestaetigt: boolean;
  textFreigegeben: boolean;
  stadt: string | null;
}

export function profil(o: DddOrt): SpielstaettenProfil {
  const p = (o.extras.spielstaette ?? {}) as Record<string, unknown>;
  const zt = p.zeile_typ;
  return {
    art: typeof p.art === "string" && p.art ? p.art : null,
    zeileTyp: zt === "saal" || zt === "standort" || zt === "filiale" ? zt : "haus",
    eventOrte: Array.isArray(p.event_orte) ? p.event_orte.filter((x): x is string => typeof x === "string") : [],
    adresseBestaetigt: !!p.adresse_bestaetigt,
    textFreigegeben: !!p.text_freigegeben,
    stadt: typeof p.stadt === "string" && p.stadt ? p.stadt : null,
  };
}

/** Art mit Symbol (Ersatzkachel, Filter, Karte). Neue Arten seit 19.11.2026: Laden, Freizeit/Erlebnis, Ausflugsziel. */
export const ARTEN: { wert: string; slug: string; icon: string; schemaTyp: string }[] = [
  { wert: "Oper/Theater/Bühne", slug: "theater", icon: "theater_comedy", schemaTyp: "PerformingArtsTheater" },
  { wert: "Konzert/Halle/Arena", slug: "konzert", icon: "stadium", schemaTyp: "MusicVenue" },
  { wert: "Museum/Ausstellung", slug: "museum", icon: "museum", schemaTyp: "Museum" },
  { wert: "Kino", slug: "kino", icon: "movie", schemaTyp: "MovieTheater" },
  { wert: "Club/Bar/Kneipe", slug: "bar", icon: "local_bar", schemaTyp: "Place" },
  { wert: "Café/Restaurant", slug: "cafe", icon: "local_cafe", schemaTyp: "Place" },
  { wert: "Gastronomie/Eventlocation", slug: "eventlocation", icon: "celebration", schemaTyp: "Place" },
  { wert: "Kultur-/Bürgerzentrum", slug: "kulturzentrum", icon: "diversity_3", schemaTyp: "Place" },
  { wert: "Bibliothek/Bildung", slug: "bildung", icon: "local_library", schemaTyp: "Place" },
  { wert: "Kirche/Gemeinde", slug: "kirche", icon: "church", schemaTyp: "Place" },
  { wert: "Kurs/Studio/Sport", slug: "kurs", icon: "fitness_center", schemaTyp: "Place" },
  { wert: "Laden", slug: "laden", icon: "storefront", schemaTyp: "Place" },
  { wert: "Freizeit/Erlebnis", slug: "freizeit", icon: "attractions", schemaTyp: "Place" },
  { wert: "Ausflugsziel/Sehenswürdigkeit", slug: "ausflugsziel", icon: "landscape", schemaTyp: "Place" },
  { wert: "Öffentliches Gebäude", slug: "oeffentlich", icon: "account_balance", schemaTyp: "Place" },
];
const SONSTIGE = { wert: "Ort", slug: "sonstige", icon: "location_on", schemaTyp: "Place" };

export function artInfo(art: string | null) {
  return ARTEN.find((a) => a.wert === art) ?? SONSTIGE;
}

/** Art eines Saals: eigene, sonst die des Hauses (Plan 3.6 „erbt“). */
export function artVon(o: DddOrt, haus: DddOrt | null): string | null {
  return profil(o).art ?? (haus ? profil(haus).art : null);
}

/** Stadt aus der PLZ (Plan 3.12): Düsseldorf, Neuss, Ratingen – sonst null. */
export function stadtAusPlz(adresse: string | null | undefined): string | null {
  const m = /\b(4\d{4})\b/.exec(adresse ?? "");
  if (!m) return null;
  const n = Number(m[1]);
  if (n >= 40210 && n <= 40629) return "Düsseldorf";
  if (n >= 41460 && n <= 41472) return "Neuss";
  if (n >= 40878 && n <= 40885) return "Ratingen";
  return null;
}

/** Stadt einer Spielstätte: gespeichert, sonst aus der PLZ der Adresse. */
export function stadtVon(o: DddOrt): string | null {
  return profil(o).stadt ?? stadtAusPlz(o.adresse);
}

/**
 * Indexierungsregel (Plan 3.1): (Adresse bestätigt ODER Text freigegeben) UND (kommendes Event ODER Text freigegeben).
 * Dieselbe Regel steht in pipeline/indexnow.py; beide prüfen tests/fixtures/ort_indexierbar.json.
 */
export function indexierbar(f: { adresseBestaetigt: boolean; textFreigegeben: boolean; kommende: number }): boolean {
  return (f.adresseBestaetigt || f.textFreigegeben) && (f.kommende > 0 || f.textFreigegeben);
}

export function ortSeitePfad(slug: string): string {
  return `${ORTE_BASIS}/${encodeURIComponent(slug)}`;
}

/** Entfernung in Metern (Haversine) – für „Orte in der Nähe“. */
export function entfernung(a: { lat: number; lng: number }, b: { lat: number; lng: number }): number {
  const r = 6371000;
  const rad = (x: number) => (x * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat);
  const dLng = rad(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * r * Math.asin(Math.sqrt(h));
}

/** Filter der Übersicht /orte (Plan 3.8): Art, Stadt, Stadtteil, Suche. */
export interface OrteFilter {
  art: string | null;
  stadt: string | null;
  stadtteil: string | null;
  q: string | null;
}

export function filterLesen(sp: Record<string, string | string[] | undefined>): OrteFilter {
  const eins = (k: string) => {
    const v = sp[k];
    const s = (Array.isArray(v) ? v[0] : v)?.trim();
    return s ? s : null;
  };
  return { art: eins("art"), stadt: eins("stadt"), stadtteil: eins("stadtteil"), q: eins("q") };
}

export function filterAktiv(f: OrteFilter): boolean {
  return !!(f.art || f.stadt || f.stadtteil || f.q);
}

function norm(t: string): string {
  return t.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/ß/g, "ss");
}

/** Filtern (nur Häuser – Säle stehen unter ihrem Haus). Stadtteil/Stadt nur bei Zeilen, die die Angabe haben. */
export function orteFiltern<T extends DddOrt>(orte: T[], f: OrteFilter): T[] {
  const q = f.q ? norm(f.q) : null;
  return orte.filter((o) => {
    if (f.art && artInfo(profil(o).art).slug !== f.art) return false;
    if (f.stadt && stadtVon(o) !== f.stadt) return false;
    if (f.stadtteil && norm(o.stadtteil ?? "") !== norm(f.stadtteil)) return false;
    if (q && !norm(`${o.name} ${o.stadtteil ?? ""} ${profil(o).art ?? ""}`).includes(q)) return false;
    return true;
  });
}

/** Buchstabe für die A–Z-Liste („Ä“ → „A“, Ziffern → „#“). */
export function buchstabe(name: string): string {
  const b = norm(name.trim()).charAt(0).toUpperCase();
  return /[A-Z]/.test(b) ? b : "#";
}
