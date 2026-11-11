// Datenzugriff für Orte (Restaurants, Cafés etc.)
// Analog zu daten.ts – cached per "use cache" und cacheLife.
import { cacheLife } from "next/cache";
import { leseClient } from "./supabase-server";
import type { DddOrt, OrtTyp } from "./typen";

const SPALTEN = [
  "id", "name", "slug", "typ", "untertitel", "beschreibung", "highlight",
  "adresse", "stadtteil", "latitude", "longitude",
  "bild_url", "bild_attribution", "tags", "preis_niveau",
  "oeffnungszeiten", "webseite", "telefon", "instagram",
  "google_place_id", "google_rating", "google_bewertungen_anzahl",
  "qualitaets_score", "sortierung",
  "erstellt_am", "aktualisiert_am",
].join(", ");

// Aus `extras` nur die Felder laden, die die Website braucht – dort liegen auch Google-Bewertungstexte
// (Material für KI-Beschreibungen), die sonst mehrere MB pro Abfrage ausmachen würden.
const EXTRAS_FELDER = [
  "google_foto", "google_primaertyp", "google_maps_url", "vorab_score",
  "kueche", "highlight_gericht", "reservierung_url", "terrasse",
  // Kneipen & Bars (lib/kneipen.ts) und Hub-Überschneidungen (Brauhäuser in beiden Guides)
  "unterart", "spezialitaeten", "vibes", "happy_hour", "raucher", "auch_restaurant", "auch_kneipe",
  // strukturierte Öffnungszeiten für schema.org (JSON-LD)
  "oeffnungszeiten_perioden",
  // Preis pro Person (scraper/orte/preisspanne.py)
  "preis_pp", "google_preisspanne",
  // Clubs (lib/clubs.ts, scraper/orte/clubs_profil.py) – auch für Orte anderer Hubs mit auch_club
  "club", "club_score", "auch_club", "club_unterart", "club_beschreibung", "club_highlight", "club_freigegeben",
  // umgetypte Orte (früher Restaurant/Kneipe) → alte URL leitet auf die Club-Seite um
  "vorher_typ",
  // Bildausschnitt („unten“/„oben“) und Bildversion (neue URL nach einem Bildtausch → kein alter Browser-Cache)
  "bild_fokus", "foto_version",
];
const SPALTEN_MIT_EXTRAS = `${SPALTEN}, ${EXTRAS_FELDER.map((k) => `x_${k}:extras->${k}`).join(", ")}`;

type Zeile = Record<string, unknown>;

/**
 * Nur Orte ab diesem Qualitäts-Score (1–10) erscheinen auf der Website.
 * In der Datenbank liegen bewusst auch schwächere Kandidaten (für Kuration und spätere Auswertungen).
 */
export const MIN_QUALITAETS_SCORE = 7;
const SEITENGROESSE = 1000;

/** Gemeinsamer Lese-Client (einer pro Prozess, siehe lib/supabase-server.ts). */
function supabaseClient() {
  return leseClient();
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
    extras: Object.fromEntries(
      EXTRAS_FELDER.map((k) => [k, z[`x_${k}`]]).filter(([, v]) => v !== null && v !== undefined),
    ),
    sortierung: typeof z.sortierung === "number" ? z.sortierung : 0,
    erstellt_am: text(z.erstellt_am),
    aktualisiert_am: text(z.aktualisiert_am),
  };
}

/** Google-Foto-Infos aus extras (nur Name und Urheber, nie eine URL mit API-Key). */
interface GoogleFoto {
  name?: string;
  autor?: string | null;
  autor_url?: string | null;
}

function googleFoto(o: DddOrt): GoogleFoto | null {
  const foto = o.extras?.google_foto;
  return foto && typeof foto === "object" && typeof (foto as GoogleFoto).name === "string" ? (foto as GoogleFoto) : null;
}

/**
 * Bild-Adresse eines Ortes: eigenes Bild (bild_url) hat Vorrang,
 * sonst das Google-Foto über die eigene Route /ort-foto/[slug] (Key bleibt auf dem Server).
 */
export function ortBildUrl(o: DddOrt): string | null {
  // Immer über den eigenen Server – auch ein eigenes bild_url kann auf einem fremden Server liegen
  const eigenesBild = !!o.bild_url && !o.bild_url.includes("key=");
  if (!(eigenesBild || googleFoto(o)) || !o.slug) return null;
  const version = o.extras.foto_version;
  return `/ort-foto/${encodeURIComponent(o.slug)}${typeof version === "number" && version > 1 ? `?v=${version}` : ""}`;
}

/** Bildausschnitt eines Ortes für object-position („unten“ → Unterkante bleibt sichtbar). */
export function ortBildFokus(o: DddOrt): string | undefined {
  const f = o.extras.bild_fokus;
  return f === "unten" ? "center bottom" : f === "oben" ? "center top" : undefined;
}

/** Urheber-Link des Google-Fotos (Google verlangt die Nennung beim Foto). */
export function ortBildAutorUrl(o: DddOrt): string | null {
  if (o.bild_url && !o.bild_url.includes("key=")) return null;
  const url = googleFoto(o)?.autor_url;
  return typeof url === "string" && url.startsWith("https://") ? url : null;
}

/**
 * Slug aus der URL sicher dekodieren. Next.js liefert params meist schon dekodiert; ein kaputtes
 * Prozentzeichen ("%", "%ZZ") darf trotzdem keine 500 auslösen → null (= nicht gefunden).
 */
export function slugDekodieren(roh: string): string | null {
  try {
    return decodeURIComponent(roh);
  } catch {
    return null;
  }
}

/** Nur http(s)-Links aus der Datenbank nach außen geben (keine data:-, javascript:- oder //-Adressen). */
export function sichereUrl(wert: unknown): string | null {
  if (typeof wert !== "string") return null;
  try {
    const url = new URL(wert);
    return url.protocol === "https:" || url.protocol === "http:" ? url.toString() : null;
  } catch {
    return null;
  }
}

const KURZ = { stale: 30, revalidate: 60, expire: 120 }; // nach Fehlern: bald neu versuchen
const NORMAL = { stale: 300, revalidate: 600, expire: 3600 };

/** Alle aktiven Orte eines Typs laden (nur Score ≥ MIN_QUALITAETS_SCORE). */
export async function orteLaden(typ: OrtTyp | OrtTyp[]): Promise<DddOrt[]> {
  "use cache";
  const client = supabaseClient();
  if (!client) {
    cacheLife(KURZ);
    return [];
  }

  const typen = Array.isArray(typ) ? typ : [typ];
  const orte: DddOrt[] = [];
  let fehler = false;

  try {
    // Seitenweise laden: Supabase liefert pro Abfrage höchstens 1.000 Zeilen
    for (let seite = 0; seite < 10; seite++) {
      const { data, error } = await client
        .from("orte")
        .select(SPALTEN_MIT_EXTRAS)
        .eq("aktiv", true)
        .gte("qualitaets_score", MIN_QUALITAETS_SCORE)
        .in("typ", typen)
        .order("sortierung", { ascending: false })
        .order("qualitaets_score", { ascending: false, nullsFirst: false })
        .order("name", { ascending: true })
        .order("id", { ascending: true })
        .range(seite * SEITENGROESSE, (seite + 1) * SEITENGROESSE - 1);

      if (error) {
        console.error(`Orte konnten nicht geladen werden (Seite ${seite + 1}): ${error.message}`);
        fehler = true;
        break;
      }
      orte.push(...((data ?? []) as unknown as Zeile[]).map(normalisieren));
      if (!data || data.length < SEITENGROESSE) break;
    }
  } catch (err) {
    console.error(`Fehler beim Laden der Orte: ${err instanceof Error ? err.message : err}`);
    fehler = true;
  }
  // Unvollständige Liste nach einem Fehler nur kurz cachen, damit der nächste Aufruf alles holt
  cacheLife(fehler ? KURZ : NORMAL);
  return orte;
}

/** Einzelnen Ort per Slug laden (nur aktiv und Score ≥ MIN_QUALITAETS_SCORE). */
export async function ortLaden(slug: string): Promise<DddOrt | null> {
  "use cache";
  const client = supabaseClient();
  if (!client) {
    cacheLife(KURZ);
    return null;
  }

  try {
    const { data, error } = await client
      .from("orte")
      .select(SPALTEN_MIT_EXTRAS)
      .eq("aktiv", true)
      .gte("qualitaets_score", MIN_QUALITAETS_SCORE)
      .eq("slug", slug)
      .maybeSingle();

    if (error) {
      console.error(`Ort '${slug}' konnte nicht geladen werden: ${error.message}`);
      cacheLife(KURZ);
      return null;
    }
    cacheLife(NORMAL);
    return data ? normalisieren(data as unknown as Zeile) : null;
  } catch (err) {
    console.error(`Ort '${slug}' konnte nicht geladen werden: ${err instanceof Error ? err.message : err}`);
    cacheLife(KURZ);
    return null;
  }
}

/**
 * Club-Hub: alle aktiven Orte mit typ = club oder extras.auch_club – OHNE die Score-Schwelle der anderen
 * Hubs. Ob ein Ort im Club-Hub erscheint, entscheidet der Club-Score (lib/clubs.ts, istSichtbarerClub).
 */
export async function clubOrteLaden(): Promise<DddOrt[]> {
  "use cache";
  const client = supabaseClient();
  if (!client) {
    cacheLife(KURZ);
    return [];
  }
  try {
    // Seitenweise wie orteLaden – sonst bräche die Liste bei mehr als 1.000 Zeilen still ab
    const orte: DddOrt[] = [];
    for (let seite = 0; seite < 10; seite++) {
      const { data, error } = await client
        .from("orte")
        .select(SPALTEN_MIT_EXTRAS)
        .eq("aktiv", true)
        .or("typ.eq.club,extras->>auch_club.eq.true")
        .order("name", { ascending: true })
        .order("id", { ascending: true })
        .range(seite * SEITENGROESSE, (seite + 1) * SEITENGROESSE - 1);
      if (error) {
        console.error(`Club-Orte konnten nicht geladen werden (Seite ${seite + 1}): ${error.message}`);
        cacheLife(KURZ);
        return [];
      }
      orte.push(...((data ?? []) as unknown as Zeile[]).map(normalisieren));
      if (!data || data.length < SEITENGROESSE) break;
    }
    cacheLife(NORMAL);
    return orte;
  } catch (err) {
    console.error(`Fehler beim Laden der Club-Orte: ${err instanceof Error ? err.message : err}`);
    cacheLife(KURZ);
    return [];
  }
}
