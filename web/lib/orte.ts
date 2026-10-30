// Datenzugriff für Orte (Restaurants, Cafés etc.)
// Analog zu daten.ts – cached per "use cache" und cacheLife.
import { cacheLife } from "next/cache";
import { createClient } from "@supabase/supabase-js";
import type { DddOrt, OrtTyp } from "./typen";

const SPALTEN = [
  "id", "name", "slug", "typ", "untertitel", "beschreibung", "highlight",
  "adresse", "stadtteil", "latitude", "longitude",
  "bild_url", "bild_attribution", "tags", "preis_niveau",
  "oeffnungszeiten", "webseite", "telefon", "instagram",
  "google_place_id", "google_rating", "google_bewertungen_anzahl",
  "qualitaets_score", "extras", "sortierung",
  "erstellt_am", "aktualisiert_am",
].join(", ");

type Zeile = Record<string, unknown>;

function supabaseClient() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!url || !key) return null;
  return createClient(url, key, { auth: { persistSession: false } });
}

function text(wert: unknown): string | null {
  if (typeof wert !== "string") return null;
  const t = wert.trim();
  return t.length ? t : null;
}

function normalisieren(z: Zeile): DddOrt {
  return {
    id: String(z.id),
    name: text(z.name) ?? "Ohne Name",
    slug: text(z.slug) ?? "",
    typ: (text(z.typ) ?? "restaurant") as OrtTyp,
    untertitel: text(z.untertitel),
    beschreibung: text(z.beschreibung),
    highlight: text(z.highlight),
    adresse: text(z.adresse),
    stadtteil: text(z.stadtteil),
    latitude: typeof z.latitude === "number" ? z.latitude : null,
    longitude: typeof z.longitude === "number" ? z.longitude : null,
    bild_url: text(z.bild_url),
    bild_attribution: text(z.bild_attribution),
    tags: Array.isArray(z.tags) ? z.tags.filter((t): t is string => typeof t === "string") : [],
    preis_niveau: text(z.preis_niveau) as DddOrt["preis_niveau"],
    oeffnungszeiten: text(z.oeffnungszeiten),
    webseite: text(z.webseite),
    telefon: text(z.telefon),
    instagram: text(z.instagram),
    google_place_id: text(z.google_place_id),
    google_rating: typeof z.google_rating === "number" ? z.google_rating : null,
    google_bewertungen_anzahl: typeof z.google_bewertungen_anzahl === "number" ? z.google_bewertungen_anzahl : null,
    qualitaets_score: typeof z.qualitaets_score === "number" ? z.qualitaets_score : null,
    extras: (typeof z.extras === "object" && z.extras !== null ? z.extras : {}) as Record<string, unknown>,
    sortierung: typeof z.sortierung === "number" ? z.sortierung : 0,
    erstellt_am: text(z.erstellt_am),
    aktualisiert_am: text(z.aktualisiert_am),
  };
}

/** Alle aktiven Orte eines Typs laden. */
export async function orteLaden(typ: OrtTyp | OrtTyp[]): Promise<DddOrt[]> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 600, expire: 3600 });

  const client = supabaseClient();
  if (!client) return [];

  const typen = Array.isArray(typ) ? typ : [typ];
  const orte: DddOrt[] = [];

  try {
    const { data, error } = await client
      .from("orte")
      .select(SPALTEN)
      .eq("aktiv", true)
      .in("typ", typen)
      .order("sortierung", { ascending: false })
      .order("qualitaets_score", { ascending: false, nullsFirst: false })
      .order("name", { ascending: true });

    if (error) {
      console.error(`Orte konnten nicht geladen werden: ${error.message}`);
      return [];
    }
    if (data) {
      orte.push(...(data as unknown as Zeile[]).map(normalisieren));
    }
  } catch (err) {
    console.error(`Fehler beim Laden der Orte: ${err instanceof Error ? err.message : err}`);
  }
  return orte;
}

/** Einzelnen Ort per Slug laden. */
export async function ortLaden(slug: string): Promise<DddOrt | null> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 600, expire: 3600 });

  const client = supabaseClient();
  if (!client) return null;

  try {
    const { data, error } = await client
      .from("orte")
      .select(SPALTEN)
      .eq("aktiv", true)
      .eq("slug", slug)
      .maybeSingle();

    if (error || !data) return null;
    return normalisieren(data as unknown as Zeile);
  } catch (err) {
    console.error(`Ort '${slug}' konnte nicht geladen werden: ${err instanceof Error ? err.message : err}`);
    return null;
  }
}

/** Alle Stadtteile mit Orte-Anzahl für einen Typ. */
export async function orteNachStadtteil(typ: OrtTyp | OrtTyp[]): Promise<{ stadtteil: string; anzahl: number }[]> {
  const orte = await orteLaden(typ);
  const zaehler = new Map<string, number>();
  for (const o of orte) {
    if (o.stadtteil) {
      zaehler.set(o.stadtteil, (zaehler.get(o.stadtteil) ?? 0) + 1);
    }
  }
  return Array.from(zaehler.entries())
    .map(([stadtteil, anzahl]) => ({ stadtteil, anzahl }))
    .sort((a, b) => b.anzahl - a.anzahl);
}
