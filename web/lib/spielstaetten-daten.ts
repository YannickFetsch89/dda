// Datenzugriff der Ortsseiten /orte (Plan docs/plan-locations-2026-11-18.md, 3.3 Punkt 6, 3.9):
// - eigene Ladefunktion, nicht orteLaden() (kein Qualitäts-Score – sichtbar ist jede aktive Spielstätte)
// - Programm über events.ort_id (Haus plus Kinder), NICHT eventPoolLaden(): alle kommenden Termine, seitenweise,
//   keine Beispieldaten; bei Fehler kurzes Cache-Leben und fehler = true (Seite zeigt „Gerade nicht verfügbar“).
import { cacheLife, cacheTag } from "next/cache";
import { heuteBerlin } from "./datum";
import { indexierbar, profil } from "./spielstaetten";
import { mitSpalten, normalisieren as eventNormalisieren } from "./daten";
import { istSichtbarerClub } from "./clubs";
import { MIN_QUALITAETS_SCORE, normalisieren, SPALTEN_MIT_EXTRAS, type Zeile, ORTE_CACHE_TAG } from "./orte";
import { leseClient } from "./supabase-server";
import { buendeln } from "./termine";
import type { DddEvent, DddOrt } from "./typen";

const KURZ = { stale: 30, revalidate: 60, expire: 120 };
const NORMAL = { stale: 300, revalidate: 600, expire: 3600 };
const SEITE = 1000;

/** Spielstätte mit Haus-Verweis (parent_id) – Säle und Standorte hängen an einem Haus (Spielstätte oder Guide-Zeile). */
export type Spielstaette = DddOrt & { parentId: string | null };

const SPALTEN = `${SPALTEN_MIT_EXTRAS}, parent_id, x_spielstaette:extras->spielstaette`;

function mitEltern(z: Zeile): Spielstaette {
  const o = normalisieren(z);
  if (z.x_spielstaette != null) o.extras.spielstaette = z.x_spielstaette;
  return { ...o, parentId: typeof z.parent_id === "string" ? z.parent_id : null };
}

/** Alle aktiven Spielstätten (seitenweise). `fehler`: Liste unvollständig → nur kurz gecacht. */
export async function spielstaettenLaden(): Promise<{ orte: Spielstaette[]; fehler: boolean }> {
  "use cache";
  cacheTag(ORTE_CACHE_TAG); // Admin-Bereich leert ihn nach Änderungen an Orten (Plan Admin-Dashboard 4.7)
  const client = leseClient();
  if (!client) {
    cacheLife(KURZ);
    return { orte: [], fehler: true };
  }
  const orte: Spielstaette[] = [];
  let fehler = false;
  try {
    for (let s = 0; s < 10; s++) {
      const { data, error } = await client
        .from("orte")
        .select(SPALTEN)
        .eq("aktiv", true)
        .eq("typ", "spielstaette")
        .order("name", { ascending: true })
        .order("id", { ascending: true })
        .range(s * SEITE, (s + 1) * SEITE - 1);
      if (error) {
        console.error(`Spielstätten nicht ladbar: ${error.message}`);
        fehler = true;
        break;
      }
      orte.push(...((data ?? []) as unknown as Zeile[]).map(mitEltern));
      if (!data || data.length < SEITE) break;
    }
  } catch (err) {
    console.error(`Spielstätten nicht ladbar: ${err instanceof Error ? err.message : err}`);
    fehler = true;
  }
  cacheLife(fehler ? KURZ : NORMAL);
  return { orte, fehler };
}

/**
 * Eine Spielstätte per Slug. `fehler`: Abfrage gescheitert (nicht „gibt es nicht“) – die Seite zeigt dann
 * „Gerade nicht verfügbar“, nicht „Ort nicht gefunden“ (Plan 3.10).
 */
export async function spielstaetteLaden(slug: string): Promise<{ ort: Spielstaette | null; fehler: boolean }> {
  "use cache";
  cacheTag(ORTE_CACHE_TAG); // Admin-Bereich leert ihn nach Änderungen an Orten (Plan Admin-Dashboard 4.7)
  const client = leseClient();
  if (!client) {
    cacheLife(KURZ);
    return { ort: null, fehler: true };
  }
  try {
    const { data, error } = await client
      .from("orte").select(SPALTEN).eq("aktiv", true).eq("typ", "spielstaette").eq("slug", slug).maybeSingle();
    if (error) {
      console.error(`Spielstätte '${slug}' nicht ladbar: ${error.message}`);
      cacheLife(KURZ);
      return { ort: null, fehler: true };
    }
    cacheLife(NORMAL);
    return { ort: data ? mitEltern(data as unknown as Zeile) : null, fehler: false };
  } catch (err) {
    console.error(`Spielstätte '${slug}' nicht ladbar: ${err instanceof Error ? err.message : err}`);
    cacheLife(KURZ);
    return { ort: null, fehler: true };
  }
}

/**
 * Beliebige aktive Zeile per ID (Haus eines Saals – auch eine Guide-Zeile wie zakk). `fehler`: Abfrage gescheitert
 * (nicht „gibt es nicht“) – Aufrufer cachen dann nur kurz.
 */
export async function ortZeileAbfragen(id: string): Promise<{ ort: DddOrt | null; fehler: boolean }> {
  "use cache";
  cacheTag(ORTE_CACHE_TAG); // Admin-Bereich leert ihn nach Änderungen an Orten (Plan Admin-Dashboard 4.7)
  const client = leseClient();
  if (!client) {
    cacheLife(KURZ);
    return { ort: null, fehler: true };
  }
  try {
    const { data, error } = await client.from("orte").select(SPALTEN).eq("aktiv", true).eq("id", id).maybeSingle();
    if (error) throw new Error(error.message);
    cacheLife(NORMAL);
    return { ort: data ? mitEltern(data as unknown as Zeile) : null, fehler: false };
  } catch (err) {
    console.error(`Ort ${id} nicht ladbar: ${err instanceof Error ? err.message : err}`);
    cacheLife(KURZ);
    return { ort: null, fehler: true };
  }
}

/** Wie ortZeileAbfragen, nur die Zeile (null = nicht da oder nicht ladbar). */
export async function ortZeileLaden(id: string): Promise<DddOrt | null> {
  return (await ortZeileAbfragen(id)).ort;
}

export interface Programm {
  heute: string;
  /** Gebündelt (mehrere Uhrzeiten eines Tages = ein Eintrag), nach Datum */
  events: DddEvent[];
  fehler: boolean;
}

/**
 * Alle kommenden Events von Haus und Kindern über events.ort_id (Plan 3.9). EINE gecachte Abfrage je Haus;
 * Saalseiten filtern daraus. `ids` = Haus-ID plus Kinder-IDs (sortiert übergeben, damit der Cache-Schlüssel stabil ist).
 */
export async function programmLaden(ids: string[]): Promise<Programm> {
  "use cache";
  cacheTag(ORTE_CACHE_TAG); // Admin-Bereich leert ihn nach Änderungen an Orten (Plan Admin-Dashboard 4.7)
  const heute = heuteBerlin();
  const client = leseClient();
  if (!client || !ids.length) {
    cacheLife(KURZ);
    return { heute, events: [], fehler: !client };
  }
  const alle: DddEvent[] = [];
  try {
    for (let s = 0; s < 20; s++) {
      const { data, error } = await mitSpalten((spalten) =>
        client
          .from("events")
          .select(`${spalten}, ort_id`)
          .eq("abgelehnt", false)
          .in("ort_id", ids)
          .or(`datum.gte.${heute},datum_bis.gte.${heute}`)
          .order("datum", { ascending: true })
          .order("id", { ascending: true })
          .range(s * SEITE, (s + 1) * SEITE - 1),
      );
      if (error) throw new Error(error.message);
      const zeilen = (data ?? []) as unknown as Zeile[];
      alle.push(...zeilen.map((z) => ({ ...eventNormalisieren(z), ort_id: typeof z.ort_id === "string" ? z.ort_id : null })));
      if (zeilen.length < SEITE) break;
    }
  } catch (err) {
    console.error(`Programm nicht ladbar: ${err instanceof Error ? err.message : err}`);
    cacheLife(KURZ);
    return { heute, events: [], fehler: true };
  }
  cacheLife(NORMAL);
  return { heute, events: buendeln(alle), fehler: false };
}

/** Kinder (Säle, Standorte) eines Hauses aus der Spielstätten-Liste – das Haus kann auch eine Guide-Zeile sein. */
export function kinderVon(hausId: string, alle: Spielstaette[]): Spielstaette[] {
  return alle.filter((o) => o.parentId === hausId);
}

/**
 * Ortslink der Eventseite (Plan 3.2): die kanonische, sichtbare Seite des zugeordneten Ortes (Ortsseite oder
 * Guide-Seite nach den Hub-Regeln) – sonst null (dann bleibt der Suchlink „Weitere Events an diesem Ort“).
 */
export async function eventOrtLink(eventId: string): Promise<{ name: string; pfad: string } | null> {
  "use cache";
  cacheTag(ORTE_CACHE_TAG); // Admin-Bereich leert ihn nach Änderungen an Orten (Plan Admin-Dashboard 4.7)
  const client = leseClient();
  if (!client) {
    cacheLife(KURZ);
    return null;
  }
  try {
    const { data: ev, error } = await client.from("events").select("ort_id").eq("id", eventId).maybeSingle();
    const ortId = (ev as { ort_id?: string | null } | null)?.ort_id;
    if (error || !ortId) {
      cacheLife(error ? KURZ : NORMAL);
      return null;
    }
    const { ort, fehler } = await ortZeileAbfragen(ortId);
    // Nur ein erfolgreiches „nicht da“ lange cachen; nach einem Abfragefehler bald neu fragen
    cacheLife(fehler ? KURZ : NORMAL);
    if (!ort) return null;
    const pfad = sichtbarerPfad(ort);
    return pfad ? { name: ort.name, pfad } : null;
  } catch {
    cacheLife(KURZ);
    return null;
  }
}

/** Kanonische, sichtbare Seite einer Zeile – dieselben Regeln wie die Hubs und der Proxy (guideZiel). */
export function sichtbarerPfad(o: DddOrt): string | null {
  const s = encodeURIComponent(o.slug);
  if (o.typ === "spielstaette") return `/orte/${s}`;
  if (o.typ === "spielplatz") return `/guides/spielplaetze/${s}`;
  if (o.typ === "weihnachtsmarkt") return `/guides/weihnachtsmaerkte/${s}`;
  if (o.typ === "ausflug" || o.typ === "wochenendtipp") return null;
  const score = o.qualitaets_score ?? 0;
  if (score >= MIN_QUALITAETS_SCORE && ["restaurant", "imbiss", "cafe"].includes(o.typ)) return `/guides/restaurants-cafes/${s}`;
  if (score >= MIN_QUALITAETS_SCORE && o.typ === "kneipe") return `/guides/kneipen-bars/${s}`;
  return istSichtbarerClub(o) ? `/guides/clubs/${s}` : null;
}

/**
 * Kommende Events je ort_id (für Sitemap und Indexierungsregel, Plan 3.1/3.11). `fehler` → leere Zählung, nur kurz
 * gecacht; die Sitemap lässt Ortsseiten dann weg statt sie falsch zu melden.
 */
export async function kommendeJeOrt(): Promise<{ anzahl: Map<string, number>; fehler: boolean }> {
  "use cache";
  cacheTag(ORTE_CACHE_TAG); // Admin-Bereich leert ihn nach Änderungen an Orten (Plan Admin-Dashboard 4.7)
  const heute = heuteBerlin();
  const client = leseClient();
  const anzahl = new Map<string, number>();
  if (!client) {
    cacheLife(KURZ);
    return { anzahl, fehler: true };
  }
  try {
    for (let s = 0; s < 50; s++) {
      const { data, error } = await client
        .from("events").select("ort_id").eq("abgelehnt", false).not("ort_id", "is", null)
        .or(`datum.gte.${heute},datum_bis.gte.${heute}`).order("id", { ascending: true })
        .range(s * SEITE, (s + 1) * SEITE - 1);
      if (error) throw new Error(error.message);
      for (const z of (data ?? []) as { ort_id: string }[]) anzahl.set(z.ort_id, (anzahl.get(z.ort_id) ?? 0) + 1);
      if (!data || data.length < SEITE) break;
    }
  } catch (err) {
    console.error(`Zählung kommender Events je Ort fehlgeschlagen: ${err instanceof Error ? err.message : err}`);
    cacheLife(KURZ);
    return { anzahl: new Map(), fehler: true };
  }
  cacheLife(NORMAL);
  return { anzahl, fehler: false };
}

/**
 * Indexierbare Ortsseiten (Plan 3.1): Haus zählt eigene plus Kinder-Events; Säle erben die bestätigte Adresse vom
 * Haus (Spielstätte: Flag, Guide-Zeile: vorhandene Adresse). Dieselbe Regel wie generateMetadata der Ortsseite.
 */
export function indexierbareOrte(alle: Spielstaette[], anzahl: Map<string, number>, hausAdresse: Map<string, boolean>): Spielstaette[] {
  const zaehle = (o: Spielstaette) =>
    o.parentId ? anzahl.get(o.id) ?? 0 : (anzahl.get(o.id) ?? 0) + kinderVon(o.id, alle).reduce((n, k) => n + (anzahl.get(k.id) ?? 0), 0);
  return alle.filter((o) => {
    const p = profil(o);
    const adresse = p.adresseBestaetigt || (!!o.parentId && (hausAdresse.get(o.parentId) ?? false));
    return indexierbar({ adresseBestaetigt: adresse, textFreigegeben: p.textFreigegeben, kommende: zaehle(o) });
  });
}

/** Guide-Häuser von Sälen (das Haus ist keine Spielstätte, z. B. der Club zakk) – für die Übersicht /orte. */
export async function guideHaeuserLaden(ids: string[]): Promise<{ orte: DddOrt[]; fehler: boolean }> {
  "use cache";
  cacheTag(ORTE_CACHE_TAG); // Admin-Bereich leert ihn nach Änderungen an Orten (Plan Admin-Dashboard 4.7)
  const client = leseClient();
  if (!client || !ids.length) {
    cacheLife(KURZ);
    return { orte: [], fehler: !client };
  }
  try {
    const { data, error } = await client.from("orte").select(SPALTEN).eq("aktiv", true).in("id", ids);
    if (error) throw new Error(error.message);
    cacheLife(NORMAL);
    return { orte: ((data ?? []) as unknown as Zeile[]).map(mitEltern), fehler: false };
  } catch (err) {
    console.error(`Guide-Häuser der Säle nicht ladbar: ${err instanceof Error ? err.message : err}`);
    cacheLife(KURZ);
    return { orte: [], fehler: true };
  }
}

/** Art eines Guide-Hauses für Symbol und Filter der Übersicht. */
function guideArt(o: DddOrt): string {
  return ["restaurant", "imbiss", "cafe"].includes(o.typ) ? "Café/Restaurant" : "Club/Bar/Kneipe";
}

/**
 * Einträge der Übersicht /orte (rein, testbar): Häuser mit ihren Sälen. Hängt ein Saal an einem Guide-Haus
 * (zakk-Säle am Club), steht das Haus als Eintrag mit Link auf seine kanonische Guide-Seite in der Liste, die Säle
 * darunter. Ist das Haus nicht sichtbar oder nicht ladbar, steht der Saal selbst als Eintrag da – jede Ortsseite
 * ist über die Übersicht erreichbar.
 */
export function uebersichtEintraege(alle: Spielstaette[], guide: DddOrt[]): {
  haeuser: Spielstaette[]; kinder: Map<string, Spielstaette[]>; pfad: Map<string, string>;
} {
  const ids = new Set(alle.map((o) => o.id));
  const pfad = new Map<string, string>();
  const guideHaeuser: Spielstaette[] = [];
  for (const h of guide) {
    const p = sichtbarerPfad(h);
    if (!p || ids.has(h.id)) continue;
    pfad.set(h.id, p);
    guideHaeuser.push({ ...h, parentId: null, extras: { ...h.extras, spielstaette: { art: guideArt(h) } } });
  }
  const hatHaus = (o: Spielstaette) => !!o.parentId && (ids.has(o.parentId) || pfad.has(o.parentId));
  const kinder = new Map<string, Spielstaette[]>();
  for (const o of alle) if (hatHaus(o)) kinder.set(o.parentId!, [...(kinder.get(o.parentId!) ?? []), o]);
  const haeuser = [...alle.filter((o) => !hatHaus(o)), ...guideHaeuser].sort((a, b) => a.name.localeCompare(b.name, "de"));
  return { haeuser, kinder, pfad };
}

/** IDs der Häuser von Sälen, die selbst keine Spielstätte sind (sortiert, stabiler Cache-Schlüssel). */
export function fremdeHausIds(alle: Spielstaette[]): string[] {
  const ids = new Set(alle.map((o) => o.id));
  return [...new Set(alle.filter((o) => o.parentId && !ids.has(o.parentId)).map((o) => o.parentId!))].sort();
}
