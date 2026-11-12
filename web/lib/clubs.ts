// Guide-Hub „Clubs“: Club-Profil und Club-Score aus extras (scraper/orte/clubs_profil.py, nur belegte
// Angaben) sowie Filter und URL-Parameter. Plan: docs/plan-clubs-2026-11-11.md.
// Orte aus anderen Hubs (Pitcher, Konvex …, extras.auch_club) behalten dort ihre Texte – hier gelten
// club_beschreibung/club_highlight und der Club-Score statt qualitaets_score.
import { slugify } from "./kueche";
import type { DddOrt } from "./typen";

/**
 * Ab diesem Club-Score (und mit Freigabe nach Sichtprüfung) ist ein Ort eine Top-Empfehlung (Stufe A, Entscheidung C2).
 * Seit 12.11.2026 zeigt der Hub ALLE Clubs mit passendem Profil, gestuft nach A/B/C (siehe clubStufe).
 */
export const MIN_CLUB_SCORE = 7;
/** Ab diesem Club-Score: „Weitere Empfehlungen“ (Stufe B); darunter „Sonstige Clubs“ (Stufe C). */
export const MIN_CLUB_SCORE_B = 5;
/** Ab diesem qualitaets_score ist die Haupt-Seite eines Orts aus einem anderen Hub sichtbar (wie MIN_QUALITAETS_SCORE). */
const MIN_SCORE_HAUPT_HUB = 7;
const HAUPT_HUB_TYPEN = ["restaurant", "imbiss", "cafe", "kneipe"];

export type ClubStufe = "a" | "b" | "c";
export const CLUB_STUFEN: { wert: ClubStufe; label: string; titel: string }[] = [
  { wert: "a", label: "Top-Empfehlung", titel: "Top-Empfehlungen" },
  { wert: "b", label: "Weitere Empfehlung", titel: "Weitere Empfehlungen" },
  { wert: "c", label: "Sonstiger Club", titel: "Sonstige Clubs" },
];

export type ClubArt = "club" | "kulturhaus" | "partylocation";
export const CLUB_ARTEN: { wert: ClubArt; label: string; mehrzahl: string; icon: string }[] = [
  { wert: "club", label: "Club", mehrzahl: "Clubs", icon: "nightlife" },
  { wert: "kulturhaus", label: "Kulturhaus", mehrzahl: "Kulturhäuser", icon: "theater_comedy" },
  { wert: "partylocation", label: "Partylocation", mehrzahl: "Partylocations", icon: "celebration" },
];

/** Feste Genre-Liste (wie im Profil-Schritt) mit Icon für die großen Genre-Chips. */
export const GENRES: { name: string; icon: string }[] = [
  { name: "Techno", icon: "graphic_eq" },
  { name: "House", icon: "album" },
  { name: "Elektro/Experimental", icon: "electric_bolt" },
  { name: "Drum & Bass", icon: "speaker" },
  { name: "Hip-Hop", icon: "mic" },
  { name: "R&B", icon: "headphones" },
  { name: "Afrobeats", icon: "public" },
  { name: "Reggaeton/Latin", icon: "music_note" },
  { name: "Pop/Charts", icon: "trending_up" },
  { name: "80er/90er/2000er", icon: "history" },
  { name: "Schlager", icon: "celebration" },
  { name: "Rock/Indie", icon: "radio" }, // „electric_guitar“ fehlt in der lokalen Icon-Schrift
  { name: "Metal/Punk", icon: "bolt" },
  { name: "Disco/Funk/Soul", icon: "album" },
  { name: "Jazz", icon: "piano" },
  { name: "Gemischt", icon: "queue_music" },
];
const GENRE_NAMEN = GENRES.map((g) => g.name);
export const genreIcon = (name: string) => GENRES.find((g) => g.name === name)?.icon ?? "music_note";

export const EINTRITT_STUFEN = [
  { wert: "frei", label: "Eintritt frei" },
  { wert: "bis10", label: "bis 10 €" },
  { wert: "bis20", label: "bis 20 €" },
  { wert: "ueber20", label: "20 € +" },
] as const;
export type EintrittStufe = (typeof EINTRITT_STUFEN)[number]["wert"];

export const FAKT_LABEL: Record<string, string> = {
  oeffnung: "Geöffnet",
  eintritt: "Eintritt",
  tuer: "Tür",
  alter: "Alter",
  kapazitaet: "Kapazität",
  floors: "Floors",
};
const DRESSCODE_TEXT: Record<string, string> = { casual: "Casual", schick: "Schick", egal: "Egal" };

export interface ClubGenre { wert: string; anteil: "haupt" | "neben" }
export interface ClubFormat { name: string; rhythmus: string; musik: string }
export interface ClubZusatz { art: string; beispiel: string }
export interface ClubProfil {
  passt: boolean;
  unterart: ClubArt | null;
  genres: ClubGenre[];
  formate: ClubFormat[];
  zusatz: ClubZusatz[];
  fakten: Record<string, string>;
  eintritt: { min: number | null; max: number | null } | null;
  dresscode: string | null;
  publikum: string[];
  ausstattung: string[];
  instagram: string | null;
  residentAdvisor: string | null;
  eventOrte: string[];
  datum: string | null;
}
export interface ClubScore { gesamt: number; programm: number; szene: number; profil: number; beliebtheit: number }

const obj = (v: unknown): Record<string, unknown> => (v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {});
const arr = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const str = (v: unknown): string | null => (typeof v === "string" && v.trim() ? v.trim() : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const httpsLink = (v: unknown, muster: RegExp) => {
  const s = str(v);
  return s && muster.test(s) ? s : null;
};

/** Club-Profil aus extras.club (nur feste Werte; unbekannte werden verworfen). */
export function clubProfil(o: DddOrt): ClubProfil | null {
  const p = obj(o.extras.club);
  if (!Object.keys(p).length) return null;
  const art = str(p.unterart);
  const fakten: Record<string, string> = {};
  for (const [k, v] of Object.entries(obj(p.fakten))) {
    const t = str(obj(v).text);
    if (t && k in FAKT_LABEL) fakten[k] = t;
  }
  // Preis-Badge und Filter nur mit Beleg von Website/Presse – einzelne Google-Bewertungen („lag schon bei 35 €“)
  // sind kein typischer Eintritt (der Text bleibt im Info-Panel)
  const eintrittQuelle = str(obj(obj(p.fakten).eintritt).quelle) ?? "";
  const eintritt = /^google/i.test(eintrittQuelle) ? {} : obj(p.eintritt);
  return {
    passt: p.passt === true,
    unterart: CLUB_ARTEN.some((a) => a.wert === art) ? (art as ClubArt) : null,
    genres: arr(p.genres)
      .map((g) => ({ wert: str(obj(g).wert) ?? "", anteil: obj(g).anteil === "haupt" ? "haupt" : "neben" }) as ClubGenre)
      .filter((g) => GENRE_NAMEN.includes(g.wert)),
    formate: arr(p.formate)
      .map((f) => ({ name: str(obj(f).name) ?? "", rhythmus: str(obj(f).rhythmus) ?? "", musik: str(obj(f).musik) ?? "" }))
      .filter((f) => f.name),
    zusatz: arr(p.zusatz_events)
      .map((z) => ({ art: str(obj(z).art) ?? "", beispiel: str(obj(z).beispiel) ?? "" }))
      .filter((z) => z.art),
    fakten,
    eintritt: Object.keys(eintritt).length ? { min: num(eintritt.min), max: num(eintritt.max) } : null,
    dresscode: DRESSCODE_TEXT[str(p.dresscode) ?? ""] ?? null,
    publikum: arr(p.publikum).filter((x): x is string => typeof x === "string"),
    ausstattung: arr(p.ausstattung).filter((x): x is string => typeof x === "string"),
    // Nur exakte Profil-URLs ohne Query/Fragment (wie im Profil-Schritt geprüft)
    instagram: httpsLink(p.instagram, /^https:\/\/(www\.)?instagram\.com\/[A-Za-z0-9_.]{1,30}\/?$/),
    residentAdvisor: httpsLink(p.resident_advisor, /^https:\/\/(www\.)?ra\.co\/clubs\/\d{1,8}\/?$/),
    eventOrte: arr(p.event_orte).filter((x): x is string => typeof x === "string"),
    datum: str(p.datum),
  };
}

export function clubScore(o: DddOrt): ClubScore | null {
  const s = obj(o.extras.club_score);
  const gesamt = num(s.gesamt);
  if (gesamt == null) return null;
  return { gesamt, programm: num(s.programm) ?? 0, szene: num(s.szene) ?? 0, profil: num(s.profil) ?? 0, beliebtheit: num(s.beliebtheit) ?? 0 };
}

/** Nach der Sichtprüfung freigegeben? („passt“ der KI ist nur ein Vorschlag) */
export const istFreigegeben = (o: DddOrt) => typeof o.extras.club_freigegeben === "string";

/** Vom Auftraggeber aus dem Club-Hub genommen (z. B. Konvex: Bar mit DJ-Nächten, kein Club). */
export const istKeinClub = (o: DddOrt) => typeof o.extras.kein_club === "string";

/**
 * Gehört der Ort sichtbar in den Club-Hub? Seit 12.11.2026 alle Clubs mit passendem Profil und Club-Score –
 * die Empfehlung zeigt die Stufe (clubStufe). Typ = club oder Ort eines anderen Hubs mit auch_club.
 */
export function istSichtbarerClub(o: DddOrt): boolean {
  const p = clubProfil(o);
  return !!p?.passt && !!clubScore(o) && !istKeinClub(o) && (o.typ === "club" || o.extras.auch_club === true);
}

/** A = Top-Empfehlung (Freigabe + Score ≥ 7), B = Score ≥ 5, C = alle übrigen. */
export function clubStufe(o: DddOrt): ClubStufe {
  const gesamt = clubScore(o)?.gesamt ?? 0;
  if (istFreigegeben(o) && gesamt >= MIN_CLUB_SCORE) return "a";
  return gesamt >= MIN_CLUB_SCORE_B ? "b" : "c";
}
export const clubStufeInfo = (o: DddOrt) => CLUB_STUFEN.find((s) => s.wert === clubStufe(o))!;

/** Club-Detailseite im Index? Nur A und B – C ist nicht geprüft und meist dünn (noindex, nicht in der Sitemap). */
export const clubIndexierbar = (o: DddOrt) => clubStufe(o) !== "c";

/**
 * Hat ein Ort aus einem anderen Hub dort eine sichtbare Seite? Nur dann ist die Club-Ansicht ein Zusatz mit Canonical
 * auf die Haupt-URL. Sonst (z. B. Giselle Bar, Bar-Score < 7) ist die Club-Seite die einzige – und damit kanonisch.
 */
export const hauptSeiteSichtbar = (o: DddOrt) =>
  o.typ !== "club" && HAUPT_HUB_TYPEN.includes(o.typ) && (o.qualitaets_score ?? 0) >= MIN_SCORE_HAUPT_HUB;
export const eigeneClubSeite = (o: DddOrt) => !hauptSeiteSichtbar(o);

export function clubArt(o: DddOrt): ClubArt {
  const roh = o.typ === "club" ? o.extras.unterart : o.extras.club_unterart;
  const art = (typeof roh === "string" ? roh : null) ?? clubProfil(o)?.unterart;
  return CLUB_ARTEN.some((a) => a.wert === art) ? (art as ClubArt) : "club";
}
export const clubArtInfo = (o: DddOrt) => CLUB_ARTEN.find((a) => a.wert === clubArt(o))!;

/** Texte für den Club-Hub (bei auch_club die eigenen Club-Texte statt der des Haupt-Hubs). */
export function clubBeschreibung(o: DddOrt): string | null {
  return o.typ === "club" ? o.beschreibung : str(o.extras.club_beschreibung) ?? o.beschreibung;
}
export function clubHighlight(o: DddOrt): string | null {
  return o.typ === "club" ? o.highlight : str(o.extras.club_highlight) ?? o.highlight;
}

/** Hauptgenres, sonst die gelegentlichen (für Badge und Zeile auf der Card). */
export function hauptGenres(o: DddOrt): string[] {
  const g = clubProfil(o)?.genres ?? [];
  const haupt = g.filter((x) => x.anteil === "haupt").map((x) => x.wert);
  return haupt.length ? haupt : g.map((x) => x.wert);
}
export const alleGenres = (o: DddOrt): string[] => (clubProfil(o)?.genres ?? []).map((g) => g.wert);

/** Typischer Eintritt als Stufe (Untergrenze zählt; nur belegte Preise). */
export function eintrittStufe(o: DddOrt): EintrittStufe | null {
  const e = clubProfil(o)?.eintritt;
  const wert = e?.min ?? e?.max ?? null;
  if (wert == null) return null;
  if (wert === 0) return "frei";
  if (wert <= 10) return "bis10";
  if (wert <= 20) return "bis20";
  return "ueber20";
}

/** Kurzer Eintritts-Text für das Badge („ab 10 €“, „Eintritt frei“). */
export function eintrittKurz(o: DddOrt): string | null {
  const e = clubProfil(o)?.eintritt;
  if (!e) return null;
  const euro = (n: number) => `${Number.isInteger(n) ? n : n.toFixed(2).replace(".", ",")} €`;
  if (e.min === 0 && (e.max == null || e.max === 0)) return "Eintritt frei";
  if (e.min != null && e.max != null && e.max > e.min) return `${euro(e.min)}–${euro(e.max)}`;
  if (e.min != null) return e.min === 0 ? "Eintritt frei" : `ab ${euro(e.min)}`;
  return e.max != null ? (e.max === 0 ? "Eintritt frei" : `bis ${euro(e.max)}`) : null;
}

// ── Filter ──────────────────────────────────────────────────────────────────

export type ClubSort = "empfohlen" | "bewertung" | "neu";
export const CLUB_SORTIERUNGEN: { wert: ClubSort; label: string }[] = [
  { wert: "empfohlen", label: "Empfohlen" },
  { wert: "bewertung", label: "Google-Bewertung" },
  { wert: "neu", label: "Neu im Guide" },
];

export type ClubAnsicht = "grid" | "karte";

export interface ClubFilter {
  stufen: ClubStufe[]; // leer = alle (A/B/C)
  arten: ClubArt[]; // leer = alle
  genres: string[]; // Slugs (ODER)
  stadtteile: string[]; // Slugs (ODER)
  eintritt: EintrittStufe | null;
  sort: ClubSort;
  ansicht: ClubAnsicht; // Grid ist Standard, Karte optional
}

type SP = Record<string, string | string[] | undefined>;
const eins = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) || undefined;
const mehrere = (v: string | string[] | undefined) => (eins(v) ?? "").split(",").map((s) => s.trim()).filter(Boolean);
const GENRE_SLUGS = new Map(GENRE_NAMEN.map((g) => [slugify(g), g]));
export const genreSlug = (name: string) => slugify(name);
export const genreName = (slug: string) => GENRE_SLUGS.get(slug) ?? slug;

export const CLUB_STANDARD: ClubFilter = { stufen: [], arten: [], genres: [], stadtteile: [], eintritt: null, sort: "empfohlen", ansicht: "grid" };

export function clubFilterLesen(sp: SP): ClubFilter {
  const sort = eins(sp.sort);
  const eintritt = eins(sp.eintritt);
  return {
    stufen: CLUB_STUFEN.map((x) => x.wert).filter((w) => mehrere(sp.stufe).includes(w)),
    arten: CLUB_ARTEN.map((a) => a.wert).filter((w) => mehrere(sp.art).includes(w)),
    genres: [...new Set(mehrere(sp.genre))].filter((g) => GENRE_SLUGS.has(g)),
    stadtteile: [...new Set(mehrere(sp.stadtteil))],
    eintritt: EINTRITT_STUFEN.some((s) => s.wert === eintritt) ? (eintritt as EintrittStufe) : null,
    sort: CLUB_SORTIERUNGEN.some((s) => s.wert === sort) ? (sort as ClubSort) : "empfohlen",
    ansicht: eins(sp.ansicht) === "karte" ? "karte" : "grid",
  };
}

/** Hat die URL einen Filter- oder Sortier-Parameter? (→ noindex) */
export function clubHatParameter(sp: SP): boolean {
  return ["stufe", "art", "genre", "stadtteil", "eintritt", "sort", "ansicht"].some((k) => eins(sp[k]) !== undefined);
}

export function clubFilterHref(basis: string, f: ClubFilter, aenderung: Partial<ClubFilter>): string {
  const n = { ...f, ...aenderung };
  const p = new URLSearchParams();
  if (n.stufen.length) p.set("stufe", CLUB_STUFEN.map((s) => s.wert).filter((w) => n.stufen.includes(w)).join(","));
  if (n.arten.length) p.set("art", CLUB_ARTEN.map((a) => a.wert).filter((w) => n.arten.includes(w)).join(","));
  if (n.genres.length) p.set("genre", n.genres.join(","));
  if (n.stadtteile.length) p.set("stadtteil", n.stadtteile.join(","));
  if (n.eintritt) p.set("eintritt", n.eintritt);
  if (n.sort !== "empfohlen") p.set("sort", n.sort);
  if (n.ansicht === "karte") p.set("ansicht", "karte");
  const qs = p.toString().replace(/%2C/g, ",");
  return qs ? `${basis}?${qs}` : basis;
}

/** Filtern; `ohne` lässt einzelne Filter weg (für die Zählwerte an den Chips). Genres: ODER. */
export function clubsFiltern(orte: DddOrt[], f: ClubFilter, ohne: (keyof ClubFilter)[] = []): DddOrt[] {
  const mit = (k: keyof ClubFilter) => !ohne.includes(k);
  return orte.filter((o) => {
    if (mit("stufen") && f.stufen.length && !f.stufen.includes(clubStufe(o))) return false;
    if (mit("arten") && f.arten.length && !f.arten.includes(clubArt(o))) return false;
    if (mit("genres") && f.genres.length && !alleGenres(o).some((g) => f.genres.includes(slugify(g)))) return false;
    if (mit("stadtteile") && f.stadtteile.length && !f.stadtteile.includes(slugify(o.stadtteil ?? ""))) return false;
    if (mit("eintritt") && f.eintritt) {
      // „bis 20 €“ schließt günstigere ein; „20 € +“ nur teure
      const reihenfolge = EINTRITT_STUFEN.map((s) => s.wert);
      const eigene = eintrittStufe(o);
      if (!eigene) return false;
      if (f.eintritt === "ueber20" ? eigene !== "ueber20" : reihenfolge.indexOf(eigene) > reihenfolge.indexOf(f.eintritt)) return false;
    }
    return true;
  });
}

/** Sortierung: Empfohlen = Club-Score, dann Programm, dann Google-Bewertungen. */
export function clubsSortieren(orte: DddOrt[], sort: ClubSort): DddOrt[] {
  const kopie = [...orte];
  const s = (o: DddOrt) => clubScore(o);
  if (sort === "bewertung") {
    kopie.sort((a, b) => (b.google_rating ?? 0) - (a.google_rating ?? 0) || (b.google_bewertungen_anzahl ?? 0) - (a.google_bewertungen_anzahl ?? 0));
  } else if (sort === "neu") {
    kopie.sort((a, b) => (b.erstellt_am ?? "").localeCompare(a.erstellt_am ?? ""));
  } else {
    kopie.sort((a, b) =>
      (s(b)?.gesamt ?? 0) - (s(a)?.gesamt ?? 0) ||
      (s(b)?.programm ?? 0) - (s(a)?.programm ?? 0) ||
      (b.google_bewertungen_anzahl ?? 0) - (a.google_bewertungen_anzahl ?? 0) ||
      a.name.localeCompare(b.name, "de"));
  }
  return kopie;
}

/** Nach Stufe gruppiert (A, B, C), Reihenfolge innerhalb der Stufe bleibt erhalten; leere Stufen fallen weg. */
export function nachStufen(orte: DddOrt[]): { stufe: (typeof CLUB_STUFEN)[number]; orte: DddOrt[] }[] {
  return CLUB_STUFEN.map((stufe) => ({ stufe, orte: orte.filter((o) => clubStufe(o) === stufe.wert) })).filter((g) => g.orte.length);
}

/** Anzahl je Genre (für die Genre-Chips). */
export function genresZaehlen(orte: DddOrt[]): { name: string; slug: string; icon: string; anzahl: number }[] {
  return GENRES.map((g) => ({ ...g, slug: slugify(g.name), anzahl: orte.filter((o) => alleGenres(o).includes(g.name)).length }));
}
