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
  | { typ: "ort"; hub: OrtHub; slug: string };

export type OrtHub = "restaurants-cafes" | "kneipen-bars" | "clubs";
const HUBS: OrtHub[] = ["restaurants-cafes", "kneipen-bars", "clubs"];
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
  const [a, b, c, d] = s as string[];
  if (a === "event" && b && !c) return UUID.test(b) ? { typ: "event-uuid", id: b.toLowerCase() } : { typ: "ungueltig" };
  if (a === "event" && b && c && !d) return { typ: "event", kategorie: b, slug: c };
  if (a === "tag" && b && !c) return { typ: "tag", datum: b };
  if (a === "reihe" && b && !c) return { typ: "reihe", slug: b };
  if (a === "guides" && b && c && !d && (HUBS as string[]).includes(b)) return { typ: "ort", hub: b as OrtHub, slug: c };
  return null;
}

/** Echter Kalendertag – dieselbe Regel wie die Tagesseite (lib/datum.ts, istGueltigerTag). */
export const tagGueltig = (datum: string): boolean => istGueltigerTag(datum);

// ---------- Abfragen mit Zwischenspeicher (pro Server-Prozess) ----------

const TREFFER_MS = 10 * 60 * 1000; // wie der Daten-Cache der Seiten
const FEHLT_MS = 2 * 60 * 1000; // neue Events erscheinen schnell
const MAX_EINTRAEGE = 5000;
const speicher = new Map<string, { wert: unknown; bis: number }>();

async function gemerkt<T>(schluessel: string, laden: () => Promise<T | undefined>): Promise<T | undefined> {
  const e = speicher.get(schluessel);
  if (e && e.bis > Date.now()) return e.wert as T;
  const wert = await laden();
  if (wert === undefined) return undefined; // Fehler nicht merken
  if (speicher.size >= MAX_EINTRAEGE) speicher.delete(speicher.keys().next().value as string);
  speicher.set(schluessel, { wert, bis: Date.now() + (wert === null ? FEHLT_MS : TREFFER_MS) });
  return wert;
}

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

type OrtKopf = {
  typ: string; aktiv: boolean; qualitaets_score: number | null;
  club: unknown; club_score: unknown; club_freigegeben: unknown; auch_club: unknown;
};

async function ortLaden(slug: string): Promise<OrtKopf | null | undefined> {
  return gemerkt(`ort:${slug}`, async () => {
    const z = await abfrage<OrtKopf>(
      "orte",
      `select=typ,aktiv,qualitaets_score,club:extras->club,club_score:extras->club_score,` +
        `club_freigegeben:extras->club_freigegeben,auch_club:extras->auch_club&slug=eq.${encodeURIComponent(slug)}&limit=1`,
    );
    return z === undefined ? undefined : (z[0] ?? null);
  });
}

// ---------- Entscheidungen ----------

const MIN_SCORE = 7; // wie MIN_QUALITAETS_SCORE in lib/orte.ts
const HUB_TYPEN: Record<Exclude<OrtHub, "clubs">, string[]> = {
  "restaurants-cafes": ["restaurant", "imbiss", "cafe"],
  "kneipen-bars": ["kneipe"],
};

/** Im Club-Hub sichtbar? Dieselbe Regel wie die Website (lib/clubs.ts). */
export function clubSichtbar(o: OrtKopf): boolean {
  const ort = {
    typ: o.typ,
    extras: { club: o.club, club_score: o.club_score, club_freigegeben: o.club_freigegeben, auch_club: o.auch_club },
  } as unknown as DddOrt;
  return o.aktiv && istSichtbarerClub(ort);
}

/** Entscheidung für einen Ort unter /guides/<hub>/<slug> (rein, testbar). */
export function ortEntscheidung(hub: OrtHub, slug: string, o: OrtKopf | null): Pruefung {
  if (!o) return FEHLT;
  if (hub === "clubs") return clubSichtbar(o) ? WEITER : FEHLT;
  const sichtbar = o.aktiv && HUB_TYPEN[hub].includes(o.typ) && (o.qualitaets_score ?? 0) >= MIN_SCORE;
  if (sichtbar) return WEITER;
  // Zum Club umgetypt (früher hier gelistet): alte URL dauerhaft auf die Club-Seite
  if (o.typ === "club" && clubSichtbar(o)) return { art: "umleiten", ziel: `/guides/clubs/${encodeURIComponent(slug)}` };
  return FEHLT;
}

/** Entscheidung für einen Pfad. Netzwerkfehler → weiter. */
export async function pfadPruefen(pfad: string): Promise<Pruefung> {
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
    case "ort": {
      const o = await ortLaden(route.slug);
      return o === undefined ? WEITER : ortEntscheidung(route.hub, route.slug, o);
    }
  }
}
