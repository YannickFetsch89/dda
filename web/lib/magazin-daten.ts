// Magazin: Daten laden (Plan 3.1, T10). Öffentliche Seiten lesen mit dem anon-Schlüssel über die View
// magazin_oeffentlich (nur veröffentlichte Beiträge, nur öffentliche Spalten). Nur die Entwurfs-Vorschau liest mit dem
// Service-Schlüssel (vorschauLaden, ohne Cache).
import { cacheLife } from "next/cache";
import { heuteBerlin } from "./datum";
import { mitSpalten, normalisieren, type Zeile } from "./daten";
import { istRubrik, type MagazinAutor, type MagazinBeitrag, type Rubrik } from "./magazin";
import { ortEntscheidung, type OrtHub, type OrtKopf } from "./pfad-pruefung";
import { SPIELPLAETZE_VERLINKT } from "./schalter";
import { dienstClient, leseClient } from "./supabase-server";
import type { DddEvent } from "./typen";

/** T10: normal bis 5 min nach Veröffentlichung sichtbar, spätestens nach 10 min (auch beim Zurückziehen). */
const MAGAZIN_CACHE = { stale: 60, revalidate: 300, expire: 600 };

const BEITRAG_SPALTEN =
  "id, slug, rubrik, autor_slug, titel, seo_titel, teaser, inhalt_md, kurzfassung, faq, hero_bild, hero_alt, hero_nachweis, " +
  "hero_ki, veroeffentlicht_am, aktualisiert_am, korrektur_hinweis, gueltig_von, gueltig_bis, event_ids, ort_slugs, quellen";

function liste<T>(wert: unknown): T[] {
  return Array.isArray(wert) ? (wert as T[]) : [];
}

/** Zeile der View/Tabelle → Beitrag (fehlende Werte leer, unbekannte Rubrik → null). */
export function beitragAus(z: Zeile): MagazinBeitrag | null {
  const rubrik = String(z.rubrik ?? "");
  if (!istRubrik(rubrik) || typeof z.slug !== "string" || typeof z.titel !== "string") return null;
  const text = (w: unknown) => (typeof w === "string" && w.trim() ? w : null);
  return {
    id: String(z.id),
    slug: z.slug,
    rubrik: rubrik as Rubrik,
    autor_slug: String(z.autor_slug ?? ""),
    titel: z.titel,
    seo_titel: text(z.seo_titel),
    teaser: text(z.teaser),
    inhalt_md: typeof z.inhalt_md === "string" ? z.inhalt_md : "",
    kurzfassung: Array.isArray(z.kurzfassung) ? (z.kurzfassung as unknown[]).map(String) : null,
    faq: Array.isArray(z.faq)
      ? (z.faq as { frage?: unknown; antwort?: unknown }[])
          .filter((f) => typeof f?.frage === "string" && typeof f?.antwort === "string")
          .map((f) => ({ frage: String(f.frage), antwort: String(f.antwort) }))
      : null,
    hero_bild: text(z.hero_bild),
    hero_alt: text(z.hero_alt),
    hero_nachweis: text(z.hero_nachweis),
    hero_ki: z.hero_ki === true,
    veroeffentlicht_am: text(z.veroeffentlicht_am),
    aktualisiert_am: text(z.aktualisiert_am),
    korrektur_hinweis: text(z.korrektur_hinweis),
    gueltig_von: text(z.gueltig_von)?.slice(0, 10) ?? null,
    gueltig_bis: text(z.gueltig_bis)?.slice(0, 10) ?? null,
    event_ids: liste<unknown>(z.event_ids).map(String),
    ort_slugs: liste<unknown>(z.ort_slugs).map(String),
    quellen: liste<{ titel?: unknown; url?: unknown; abgerufen_am?: unknown }>(z.quellen)
      .filter((q) => typeof q?.titel === "string" && typeof q?.url === "string")
      .map((q) => ({ titel: String(q.titel), url: String(q.url), abgerufen_am: typeof q.abgerufen_am === "string" ? q.abgerufen_am : null })),
  };
}

/** Heute (Europe/Berlin) mit demselben Cache wie die Beiträge – für Archiv- und Hinweisregeln (E12). */
export async function magazinHeute(): Promise<string> {
  "use cache";
  cacheLife(MAGAZIN_CACHE);
  return heuteBerlin(new Date());
}

/** Alle veröffentlichten Beiträge, neueste zuerst. Fehler → leer. */
export async function beitraegeLaden(): Promise<MagazinBeitrag[]> {
  "use cache";
  cacheLife(MAGAZIN_CACHE);
  const client = leseClient();
  if (!client) return [];
  const { data, error } = await client
    .from("magazin_oeffentlich")
    .select(BEITRAG_SPALTEN)
    .order("veroeffentlicht_am", { ascending: false })
    .limit(500);
  if (error) {
    console.error(`Magazin: Beiträge konnten nicht geladen werden: ${error.message}`);
    return [];
  }
  return ((data ?? []) as unknown as Zeile[]).map(beitragAus).filter((b): b is MagazinBeitrag => !!b);
}

/** Ein veröffentlichter Beitrag. null = nicht (mehr) sichtbar oder Fehler. */
export async function beitragLaden(slug: string): Promise<MagazinBeitrag | null> {
  "use cache";
  cacheLife(MAGAZIN_CACHE);
  const client = leseClient();
  if (!client) return null;
  const { data, error } = await client.from("magazin_oeffentlich").select(BEITRAG_SPALTEN).eq("slug", slug).maybeSingle();
  if (error) {
    console.error(`Magazin: Beitrag ${slug} konnte nicht geladen werden: ${error.message}`);
    return null;
  }
  return data ? beitragAus(data as unknown as Zeile) : null;
}

/** Aktive Autoren (Pseudonyme). */
export async function autorenLaden(): Promise<MagazinAutor[]> {
  "use cache";
  cacheLife(MAGAZIN_CACHE);
  const client = leseClient();
  if (!client) return [];
  const { data, error } = await client
    .from("magazin_autoren")
    .select("slug, name, kurzbeschreibung, schwerpunkt, rubriken, bild, bild_ki")
    .order("name", { ascending: true });
  if (error) {
    console.error(`Magazin: Autoren konnten nicht geladen werden: ${error.message}`);
    return [];
  }
  return ((data ?? []) as Zeile[]).map((z) => ({
    slug: String(z.slug),
    name: String(z.name),
    kurzbeschreibung: String(z.kurzbeschreibung ?? ""),
    schwerpunkt: String(z.schwerpunkt ?? ""),
    rubriken: liste<unknown>(z.rubriken).map(String).filter(istRubrik),
    bild: typeof z.bild === "string" ? z.bild : null,
    bild_ki: z.bild_ki !== false,
  }));
}

/** Eingebettete Events (live, auch abgesagte – die Karte zeigt das). Reihenfolge wie die IDs. */
export async function eventsFuerIds(ids: string[]): Promise<{ heute: string; events: DddEvent[] }> {
  "use cache";
  cacheLife(MAGAZIN_CACHE);
  const heute = heuteBerlin(new Date());
  const client = leseClient();
  if (!client || !ids.length) return { heute, events: [] };
  const { data, error } = await mitSpalten<Zeile[]>((spalten) =>
    client
      .from("events")
      .select(spalten)
      .in("id", ids.slice(0, 200))
      .eq("abgelehnt", false)
      .then((x) => x as unknown as { data: Zeile[] | null; error: { message: string } | null }),
  );
  if (error) {
    console.error(`Magazin: eingebettete Events konnten nicht geladen werden: ${error.message}`);
    return { heute, events: [] };
  }
  const nachId = new Map((data ?? []).map((z) => [String(z.id), normalisieren(z)]));
  return { heute, events: ids.map((id) => nachId.get(id)).filter((e): e is DddEvent => !!e) };
}

export interface MagazinOrt {
  slug: string;
  name: string;
  typ: string;
  stadtteil: string | null;
  /** Kanonische, sichtbare Ortsseite – sonst null (dann ohne Link). Nie Google-Foto oder -Bewertung (Plan 5.2). */
  pfad: string | null;
}

const TYP_HUB: Record<string, OrtHub> = {
  restaurant: "restaurants-cafes",
  imbiss: "restaurants-cafes",
  cafe: "restaurants-cafes",
  kneipe: "kneipen-bars",
  club: "clubs",
  spielplatz: "spielplaetze",
  weihnachtsmarkt: "weihnachtsmaerkte",
};

/** Ziel-Pfad eines Ortes mit derselben Regel wie proxy.ts (sichtbar → eigene Seite, umgetypt → Weiterleitungsziel). */
export function ortZiel(slug: string, kopf: OrtKopf): string | null {
  const hub = TYP_HUB[kopf.typ];
  if (!hub || (hub === "spielplaetze" && !SPIELPLAETZE_VERLINKT)) return null;
  const e = ortEntscheidung(hub, slug, kopf);
  if (e.art === "weiter") return `/guides/${hub}/${encodeURIComponent(slug)}`;
  return e.art === "umleiten" ? e.ziel : null;
}

/** Eingebettete Orte: Name, Typ, Stadtteil und Link – bewusst ohne Bild und Bewertung. */
export async function orteFuerSlugs(slugs: string[]): Promise<MagazinOrt[]> {
  "use cache";
  cacheLife(MAGAZIN_CACHE);
  const client = leseClient();
  if (!client || !slugs.length) return [];
  const { data, error } = await client
    .from("orte")
    .select(
      "slug, name, typ, aktiv, qualitaets_score, stadtteil, club:extras->club, club_score:extras->club_score, " +
        "club_freigegeben:extras->club_freigegeben, auch_club:extras->auch_club, kein_club:extras->kein_club, " +
        "freigeschaltet_am:extras->spielplatz->>freigeschaltet_am, wm_freigeschaltet_am:extras->weihnachtsmarkt->>freigeschaltet_am",
    )
    .in("slug", slugs.slice(0, 100));
  if (error) {
    console.error(`Magazin: eingebettete Orte konnten nicht geladen werden: ${error.message}`);
    return [];
  }
  return ((data ?? []) as unknown as (OrtKopf & { slug: string; name: string })[]).map((o) => ({
    slug: o.slug,
    name: o.name,
    typ: o.typ,
    stadtteil: o.stadtteil ?? null,
    pfad: ortZiel(o.slug, o),
  }));
}

/** Entwurf für die Vorschau (Plan 5.3): mit Service-Schlüssel, ohne Cache, nur entwurf/in_pruefung. */
export async function vorschauLaden(id: string): Promise<{ beitrag: MagazinBeitrag; hash: string | null; pruefung: Record<string, unknown> } | null> {
  const client = dienstClient();
  if (!client) return null;
  const { data, error } = await client
    .from("magazin_beitraege")
    .select(`${BEITRAG_SPALTEN}, status, vorschau_hash, pruefung`)
    .eq("id", id)
    .in("status", ["entwurf", "in_pruefung"])
    .maybeSingle();
  if (error || !data) return null;
  const z = data as unknown as Zeile;
  const beitrag = beitragAus(z);
  if (!beitrag) return null;
  return {
    beitrag,
    hash: typeof z.vorschau_hash === "string" ? z.vorschau_hash : null,
    pruefung: z.pruefung && typeof z.pruefung === "object" ? (z.pruefung as Record<string, unknown>) : {},
  };
}
