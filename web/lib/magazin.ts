// Magazin (Plan docs/plan-redaktion-2026-11-19.md): Typen und reine Regeln – ohne Netz, testbar.
// Daten laden lib/magazin-daten.ts, Bilder lib/magazin-bilder.ts, Text lib/magazin-markdown.ts.
import { plusTage } from "./datum";

// Nachtleben, Genuss und Familie seit 19.11.2026 als eigene Rubriken (Entscheidung Auftraggeber, Plan-Nachtrag);
// Stadtleben nimmt alles auf, was nicht eindeutig zuzuordnen ist. Werte = URL-Segment = CHECK in der Datenbank.
export const RUBRIKEN = ["wochenvorschau", "monats-tipps", "saison", "nachtleben", "genuss", "familie", "stadtleben"] as const;
export type Rubrik = (typeof RUBRIKEN)[number];

export const RUBRIK_NAME: Record<Rubrik, string> = {
  wochenvorschau: "Wochenvorschau",
  "monats-tipps": "Monats-Tipps",
  saison: "Saison",
  nachtleben: "Nachtleben",
  genuss: "Genuss",
  familie: "Familie",
  stadtleben: "Stadtleben",
};

export const RUBRIK_TEXT: Record<Rubrik, string> = {
  wochenvorschau: "Was in der kommenden Woche in Düsseldorf los ist – jeden Sonntag neu.",
  "monats-tipps": "Unsere Auswahl der stärksten Events des Monats.",
  saison: "Weihnachtsmärkte, Karneval, Sommer am Rhein: was die Saison in Düsseldorf bringt.",
  nachtleben: "Konzerte, Clubnächte und Partys: wo in Düsseldorf abends die Musik spielt.",
  genuss: "Restaurants, Cafés, Foodmärkte und Tastings in Düsseldorf.",
  familie: "Kinderprogramm, Spielplätze und Ausflüge: Düsseldorf mit Kindern.",
  stadtleben: "Stadtteile, Alltag und Geschichten aus Düsseldorf abseits des Kalenders.",
};

export function istRubrik(wert: string): wert is Rubrik {
  return (RUBRIKEN as readonly string[]).includes(wert);
}

/** Slug-Form wie im CHECK der Datenbank (database/magazin_2026-11-19.sql). */
export const SLUG_MUSTER = /^[a-z0-9]+(-[a-z0-9]+)*$/;
/** Feste Pfade unter /magazin, nie Beitrags-Slugs (Plan 3.1). */
export const RESERVIERT = ["rubrik", "autor", "vorschau", "seite", "redaktion"] as const;

export const REDAKTION_NAME = "Redaktion dies.das.düsseldorf";
export const VERANTWORTLICH = "Yannick Fetsch";
export const FEED_TITEL = "dies.das.düsseldorf – Magazin";
export const FEED_PFAD = "/magazin/feed.xml";

/** Öffentliche Spalten (View magazin_oeffentlich). */
export interface MagazinBeitrag {
  id: string;
  slug: string;
  rubrik: Rubrik;
  autor_slug: string;
  titel: string;
  seo_titel: string | null;
  teaser: string | null;
  inhalt_md: string;
  kurzfassung: string[] | null;
  faq: { frage: string; antwort: string }[] | null;
  hero_bild: string | null;
  hero_alt: string | null;
  hero_nachweis: string | null;
  hero_ki: boolean;
  veroeffentlicht_am: string | null;
  aktualisiert_am: string | null;
  korrektur_hinweis: string | null;
  gueltig_von: string | null;
  gueltig_bis: string | null;
  event_ids: string[];
  ort_slugs: string[];
  quellen: { titel: string; url: string; abgerufen_am?: string | null }[];
}

export interface MagazinAutor {
  slug: string;
  name: string;
  kurzbeschreibung: string;
  schwerpunkt: string;
  rubriken: Rubrik[];
  bild: string | null;
  bild_ki: boolean;
}

export const beitragPfad = (b: Pick<MagazinBeitrag, "slug">) => `/magazin/${b.slug}`;
export const autorPfad = (a: Pick<MagazinAutor, "slug">) => `/magazin/autor/${a.slug}`;
export const rubrikPfad = (r: Rubrik) => `/magazin/rubrik/${r}`;

/** Laufende Rubriken mit Zeitraum: nach dem Ende Hinweisbox, 30 Tage danach noindex (E12, Plan 5.12). */
const LAUFENDE: Rubrik[] = ["wochenvorschau", "monats-tipps"];
export const ARCHIV_TAGE = 30;

/** Ausgabe vorbei (Hinweisbox „Diese Vorschau ist vorbei“)? Nur Wochenvorschau und Monats-Tipps. */
export function istVorbei(b: Pick<MagazinBeitrag, "rubrik" | "gueltig_bis">, heute: string): boolean {
  return LAUFENDE.includes(b.rubrik) && !!b.gueltig_bis && b.gueltig_bis < heute;
}

/** Archiviert (E12): 30 Tage nach gueltig_bis → noindex,follow, raus aus Sitemap und Feed. Seite bleibt. */
export function istArchiviert(b: Pick<MagazinBeitrag, "rubrik" | "gueltig_bis">, heute: string): boolean {
  return LAUFENDE.includes(b.rubrik) && !!b.gueltig_bis && plusTage(b.gueltig_bis, ARCHIV_TAGE) < heute;
}

/** Saison vorbei (Hinweisbox „Saison vorbei“, bleibt indexiert, Plan 5.12). */
export function saisonVorbei(b: Pick<MagazinBeitrag, "rubrik" | "gueltig_bis">, heute: string): boolean {
  return b.rubrik === "saison" && !!b.gueltig_bis && b.gueltig_bis < heute;
}

/** Hinweis am Ende (E4/E4a): Datenart aus den Einbettungen. */
export function entstehungsHinweis(b: Pick<MagazinBeitrag, "event_ids" | "ort_slugs">): string {
  const events = b.event_ids.length > 0;
  const orte = b.ort_slugs.length > 0;
  const art = events && !orte ? "Eventdaten" : orte && !events ? "Ortsdaten" : "Event- und Ortsdaten";
  return `Mit KI-Unterstützung aus unseren ${art} erstellt, von der Redaktion geprüft und freigegeben. Redaktionell verantwortlich: ${VERANTWORTLICH}.`;
}

/** Lesezeit in Minuten (200 Wörter je Minute, mindestens 1). */
export function lesezeit(text: string): number {
  const woerter = text.replace(/\{\{[^}]*\}\}/g, " ").split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(woerter / 200));
}

/** Kalendertag (Europe/Berlin) eines Zeitstempels, z. B. für „Veröffentlicht am“. */
export function berlinTag(zeitpunkt: string): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit" }).format(
    new Date(zeitpunkt),
  );
}

/** ISO-Zeitpunkt mit Berliner Versatz (JSON-LD, Plan 5.4: dateModified mit Zeitzone). */
export function berlinIso(zeitpunkt: string): string {
  const d = new Date(zeitpunkt);
  const teile = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
      second: "2-digit", hourCycle: "h23", timeZoneName: "longOffset",
    })
      .formatToParts(d)
      .map((t) => [t.type, t.value]),
  ) as Record<string, string>;
  const versatz = (teile.timeZoneName ?? "GMT+01:00").replace("GMT", "") || "+00:00";
  return `${teile.year}-${teile.month}-${teile.day}T${teile.hour}:${teile.minute}:${teile.second}${versatz}`;
}

/** Guides, die ein Beitrag einbetten darf ({{guide:slug}}), mit kurzem Text. Spielplätze nur, wenn verlinkt. */
export const GUIDE_KAESTEN: Record<string, { label: string; text: string }> = {
  weihnachtsmaerkte: { label: "Weihnachtsmärkte", text: "Welche Märkte heute offen haben – mit Sonderzeiten an den Feiertagen" },
  "restaurants-cafes": { label: "Restaurants & Cafés", text: "Die besten Adressen zum Essen und Kaffeetrinken" },
  "kneipen-bars": { label: "Kneipen & Bars", text: "Altbier, Cocktails und gemütliche Ecken" },
  clubs: { label: "Clubs", text: "Düsseldorfs Nachtleben von Techno bis Hip-Hop" },
  spielplaetze: { label: "Spielplätze", text: "Der perfekte Spielplatz für jedes Alter" },
};
