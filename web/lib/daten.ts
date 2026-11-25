// Datenzugriff: lädt alle relevanten Events einmal aus Supabase und cached sie 10 Minuten.
// Alle Ansichten leiten ihre Listen aus diesem Pool ab (siehe lib/ableitungen.ts).
import { cacheLife, cacheTag } from "next/cache";
import { leseClient } from "./supabase-server";
import beispiel from "./beispiel-events.json";
import { kategorieAusDb } from "./kategorien";
import { heuteBerlin, plusTage, tageZwischen, wochenende } from "./datum";
import { buendeln } from "./termine";
import type { DddEvent, EventPool } from "./typen";

/** Cache-Tag aller Event-Loader (Plan Admin-Dashboard 4.4) */
export const EVENTS_CACHE_TAG = "events";

const SPALTEN_OHNE_ORT =
  "id, titel, datum, datum_bis, uhrzeit, ort, adresse, kategorie, beschreibung, preis, quelle_name, quelle_url, bild_url, stadtteil, slug, erstellt_am, tipp_des_tages, highlight_der_woche, top_event_des_monats";
// ort_id (Ausblick nur an Orten mit Ortsseite, Plan Quellen-Ausbau W2); fehlt sie, lädt die letzte Variante ohne sie
const SPALTEN_BASIS = `${SPALTEN_OHNE_ORT}, ort_id`;
// Neuere Spalten zuerst; fehlen sie in der DB noch, wird mit der nächsten Variante geladen (siehe spaltenFehlt)
const SPALTEN_VARIANTEN = [
  // Ticket-Link des Hauses (database/ticket_url_2026-11-24.sql, Plan Quellen-Ausbau 5.5.2, P1; Button erst mit W2)
  `${SPALTEN_BASIS}, abgesagt, unterkategorie, highlight_gesetzt_am, top_gesetzt_am, nicht_empfehlen, ticket_url, reihe:reihen(slug, titel)`,
  // Redaktions-Schalter „nicht empfehlen“ (database/nicht_empfehlen_2026-11-23.sql)
  `${SPALTEN_BASIS}, abgesagt, unterkategorie, highlight_gesetzt_am, top_gesetzt_am, nicht_empfehlen, reihe:reihen(slug, titel)`,
  // Zeitpunkte der Highlight-/Top-Flaggen (database/flaggen_zeitpunkt_2026-11-13.sql); ohne sie gelten die Flaggen nicht
  `${SPALTEN_BASIS}, abgesagt, unterkategorie, highlight_gesetzt_am, top_gesetzt_am, reihe:reihen(slug, titel)`,
  `${SPALTEN_BASIS}, abgesagt, unterkategorie, reihe:reihen(slug, titel)`,
  `${SPALTEN_BASIS}, abgesagt, reihe:reihen(slug, titel)`,
  `${SPALTEN_BASIS}, abgesagt`,
  SPALTEN_BASIS,
  SPALTEN_OHNE_ORT,
];

// Absage im Text erkennen (auch für Altdaten, z.B. PRINZ-Ort "© EventimAbgesagt")
const ABSAGE = /abgesagt|entfällt|fällt aus|cancell?ed/i;
// Bildnachweise, die ein Scraper fälschlich als Ort gespeichert hat
const KEIN_ORT = /^(©|quelle:)/i;

// Wie weit in die Zukunft geladen wird
const TAGE_VORAUS = 60;
const SEITENGROESSE = 1000;

export type Zeile = Record<string, unknown>;

function text(wert: unknown): string | null {
  if (typeof wert !== "string") return null;
  const t = wert.trim();
  return t.length ? t : null;
}

// Einheitliche Schreibweise für freien Eintritt (wie preis_normalisieren in pipeline/deduplication.py):
// nur exakte Varianten – „kostenlos oder auf Anfrage“ bleibt, wie es ist
const FREI_GENAU = /^(?:eintritt[: ]*frei|freier eintritt|kostenlos|kostenfrei|gratis|umsonst|frei|free|0(?:[,.]0{1,2})? ?€|€ ?0)$/i;

export function preisText(wert: unknown): string | null {
  const t = text(wert);
  return t && FREI_GENAU.test(t) ? "kostenlos" : t;
}

export function normalisieren(z: Zeile): DddEvent {
  const titel = text(z.titel) ?? "Ohne Titel";
  const ortRoh = text(z.ort);
  const ortUngueltig = !!ortRoh && KEIN_ORT.test(ortRoh);
  return {
    id: String(z.id),
    titel,
    datum: String(z.datum).slice(0, 10),
    datum_bis: text(z.datum_bis)?.slice(0, 10) ?? null,
    uhrzeit: text(z.uhrzeit)?.slice(0, 5) ?? null,
    ort: (!ortUngueltig && ortRoh) || "Düsseldorf",
    adresse: text(z.adresse),
    kategorie: kategorieAusDb(text(z.kategorie)),
    beschreibung: text(z.beschreibung),
    preis: preisText(z.preis),
    quelle_name: text(z.quelle_name),
    quelle_url: text(z.quelle_url),
    ticket_url: text(z.ticket_url),
    ort_id: text(z.ort_id),
    bild_url: text(z.bild_url),
    stadtteil: text(z.stadtteil),
    slug: text(z.slug),
    erstellt_am: text(z.erstellt_am),
    tipp_des_tages: z.tipp_des_tages === true,
    highlight_der_woche: z.highlight_der_woche === true,
    top_event_des_monats: z.top_event_des_monats === true,
    highlight_gesetzt_am: text(z.highlight_gesetzt_am),
    top_gesetzt_am: text(z.top_gesetzt_am),
    nicht_empfehlen: z.nicht_empfehlen === true,
    abgesagt: z.abgesagt === true || ABSAGE.test(titel) || (ortUngueltig && ABSAGE.test(ortRoh ?? "")),
    reihe: reiheAus(z.reihe),
    unterkategorie: typeof z.unterkategorie === "string" ? z.unterkategorie : null,
    uhrzeiten: null,
  };
}

function reiheAus(wert: unknown): DddEvent["reihe"] {
  const r = (Array.isArray(wert) ? wert[0] : wert) as { slug?: unknown; titel?: unknown } | null | undefined;
  return r && typeof r.slug === "string" && typeof r.titel === "string" ? { slug: r.slug, titel: r.titel } : null;
}

/** Supabase meldet eine unbekannte Spalte/Beziehung (Migration noch nicht ausgeführt). */
function spaltenFehlt(meldung: string | undefined): boolean {
  return !!meldung && /abgesagt|reihe|unterkategorie|gesetzt_am|nicht_empfehlen|ticket_url|ort_id/.test(meldung);
}

/** Events laden mit der neuesten Spaltenvariante, die die DB schon kennt. */
export async function mitSpalten<T>(
  laden: (spalten: string) => PromiseLike<{ data: T | null; error: { message: string } | null }>,
): Promise<{ data: T | null; error: { message: string } | null }> {
  let ergebnis = await laden(SPALTEN_VARIANTEN[0]);
  for (let i = 1; i < SPALTEN_VARIANTEN.length && ergebnis.error && spaltenFehlt(ergebnis.error.message); i++) {
    ergebnis = await laden(SPALTEN_VARIANTEN[i]);
  }
  return ergebnis;
}

/** Gemeinsamer Lese-Client (einer pro Prozess, siehe lib/supabase-server.ts). */
export function supabaseClient() {
  return leseClient();
}

/**
 * Zeitraum der Pool-Abfrage: ab `von` (laufende Events mit datum_bis ≥ von eingeschlossen) bis `ende`, Standard
 * `von` + TAGE_VORAUS. eventPoolLaden() ruft ohne Ende (Startseite unverändert), magazinPoolLaden() mit
 * max(bis, von + 60 Tage) (Plan Redaktion 4.2, Cursor-Prüfung 5 Befund 2).
 */
export function poolGrenzen(von: string, ende?: string): { von: string; bis: string } {
  const standard = plusTage(von, TAGE_VORAUS);
  return { von, bis: ende && ende > standard ? ende : standard };
}

async function ausSupabaseLaden(heute: string, ende?: string, fern = false): Promise<DddEvent[]> {
  const client = supabaseClient();
  if (!client) throw new Error("SUPABASE_URL / SUPABASE_KEY fehlen in .env.local");

  const { bis } = fern ? { bis: ende ?? heute } : poolGrenzen(heute, ende);
  const events: DddEvent[] = [];
  let variante = 0;
  for (let seite = 0; seite < 20; seite++) {
    const basis = client.from("events").select(SPALTEN_VARIANTEN[variante]).eq("abgelehnt", false);
    // Fernpool: nur Termine, die an `heute` (= erster Ferntag) beginnen, und nur fertig kategorisierte (Plan 6.1, 5.3)
    const abfrage = fern
      ? basis.gte("datum", heute).not("kategorie", "is", null)
      : basis.or(`datum.gte.${heute},datum_bis.gte.${heute}`);
    const { data, error } = await abfrage
      .lte("datum", bis)
      .order("datum", { ascending: true })
      .order("id", { ascending: true })
      .range(seite * SEITENGROESSE, (seite + 1) * SEITENGROESSE - 1);
    if (error && variante < SPALTEN_VARIANTEN.length - 1 && spaltenFehlt(error.message)) {
      console.warn(`Neue Spalte fehlt in Supabase (${error.message}) – lade ohne sie (SQL in database/ ausführen)`);
      variante += 1;
      seite -= 1;
      continue;
    }
    if (error) throw new Error(`Supabase-Fehler: ${error.message}`);
    events.push(...(data as unknown as Zeile[]).map(normalisieren));
    if (!data || data.length < SEITENGROESSE) break;
  }
  return events;
}

/**
 * Events der schon vergangenen Tage des laufenden Wochenendes (Fr/Sa, Stand Sa oder So), nur für die Wochenend-Box
 * der Startseite: Sie zeigt bis einschließlich Sonntag alle drei Tage (Auftraggeber 16.11.2026). Der Pool selbst
 * beginnt bei heute und bleibt so. An Mo–Fr leer. Fehler → leer (die Box zeigt dann „Noch keine Tipps“ wie bisher).
 */
export async function vergangeneWochenendEvents(heute: string): Promise<DddEvent[]> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 600, expire: 3600 });
  // Admin-Bereich leert diesen Tag nach jeder Event-Änderung (Plan Admin-Dashboard 4.4, revalidateTag mit expire: 0)
  cacheTag(EVENTS_CACHE_TAG);

  const { fr } = wochenende(heute);
  if (fr >= heute) return [];
  const client = supabaseClient();
  if (!client) return [];
  const events: DddEvent[] = [];
  let variante = 0;
  try {
    for (let seite = 0; seite < 5; seite++) {
      const { data, error } = await client
        .from("events")
        .select(SPALTEN_VARIANTEN[variante])
        .eq("abgelehnt", false)
        .gte("datum", fr)
        .lt("datum", heute)
        .order("datum", { ascending: true })
        .order("id", { ascending: true })
        .range(seite * SEITENGROESSE, (seite + 1) * SEITENGROESSE - 1);
      if (error && variante < SPALTEN_VARIANTEN.length - 1 && spaltenFehlt(error.message)) {
        variante += 1;
        seite -= 1;
        continue;
      }
      if (error) throw new Error(`Supabase-Fehler: ${error.message}`);
      events.push(...(data as unknown as Zeile[]).map(normalisieren));
      if (!data || data.length < SEITENGROESSE) break;
    }
  } catch (err) {
    console.warn(`Vergangene Wochenendtage konnten nicht geladen werden: ${err instanceof Error ? err.message : err}`);
    return [];
  }
  return buendeln(events);
}

// Ort → Stadtteil für die Beispiel-Events aus dem Design-Handoff
const BEISPIEL_STADTTEIL: Record<string, string> = {
  Medienhafen: "Hafen",
  Immermannstraße: "Stadtmitte",
  Rheinuferpromenade: "Altstadt",
  Rheinkniebrücke: "Unterbilk",
  Hofgarten: "Pempelfort",
  "Aachener Platz": "Bilk",
  "Kö-Bogen": "Stadtmitte",
  Carlsplatz: "Carlstadt",
};
const FRISCH = new Set(["e24", "e25", "e27", "e28", "e29", "e30", "e17", "e19"]);

/** Beispiel-Events aus dem Handoff, relativ zu heute verschoben. */
function beispielEvents(heute: string, jetzt: Date): DddEvent[] {
  const versatz = tageZwischen("2026-10-27", heute);
  return (beispiel as Zeile[]).map((z) => {
    const e = normalisieren(z);
    const id = e.id;
    const datum = plusTage(e.datum, versatz);
    return {
      ...e,
      id: `beispiel-${id}`,
      datum,
      slug: `beispiel-${id}-${datum}`,
      stadtteil: BEISPIEL_STADTTEIL[e.ort] ?? e.ort,
      quelle_name: "Beispieldaten",
      erstellt_am: new Date(jetzt.getTime() - (FRISCH.has(id) ? 10 : 72) * 3_600_000).toISOString(),
      tipp_des_tages: id === "e1",
      highlight_der_woche: id === "e5",
      highlight_gesetzt_am: id === "e5" ? jetzt.toISOString() : null,
      top_event_des_monats: id === "e13",
      top_gesetzt_am: id === "e13" ? jetzt.toISOString() : null,
    };
  });
}

export async function eventPoolLaden(): Promise<EventPool> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 600, expire: 3600 });
  // Admin-Bereich leert diesen Tag nach jeder Event-Änderung (Plan Admin-Dashboard 4.4, revalidateTag mit expire: 0)
  cacheTag(EVENTS_CACHE_TAG);

  const jetzt = new Date();
  const heute = heuteBerlin(jetzt);
  try {
    const alle = await ausSupabaseLaden(heute);
    return { heute, jetzt: jetzt.toISOString(), events: buendeln(alle), alle, quelle: "supabase", fehler: null };
  } catch (err) {
    const fehler = err instanceof Error ? err.message : String(err);
    console.warn(`Events konnten nicht geladen werden, nutze Beispieldaten: ${fehler}`);
    const alle = beispielEvents(heute, jetzt);
    return { heute, jetzt: jetzt.toISOString(), events: buendeln(alle), alle, quelle: "beispiel", fehler };
  }
}

/** Erster und letzter Tag des Fernpools (Plan Quellen-Ausbau 6.1): Tag 61 bis 365 ab heute. */
export const FERN_AB_TAG = TAGE_VORAUS + 1;
export const FERN_BIS_TAG = 365;

/** Liegt ein Tag hinter dem 60-Tage-Pool (also im Fernpool)? */
export function istFern(datum: string, heute: string): boolean {
  return datum >= plusTage(heute, FERN_AB_TAG);
}

/**
 * Zweiter, schlanker Pool für Tag 61–365 (Plan docs/plan-quellen-ausbau-2026-11-23.md, 6.1, Schritt W1): Suche und
 * eigener Zeitraum auf /entdecken, ferne Tagesseiten, Nachbarn ferner Eventseiten, Sitemap. Gleiche Spalten und
 * normalisieren() wie eventPoolLaden(), nur kategorisierte Events. Hängt am selben Cache-Tag (der Admin-Bereich leert
 * beide). Bei einem Fehler: leere Liste – nie Beispieldaten (Ausblick und Sitemap dürfen sie nicht zeigen).
 */
export async function fernPoolLaden(): Promise<EventPool> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 900, expire: 3600 });
  cacheTag(EVENTS_CACHE_TAG);

  const jetzt = new Date();
  const heute = heuteBerlin(jetzt);
  try {
    const alle = await ausSupabaseLaden(plusTage(heute, FERN_AB_TAG), plusTage(heute, FERN_BIS_TAG), true);
    return { heute, jetzt: jetzt.toISOString(), events: buendeln(alle), alle, quelle: "supabase", fehler: null };
  } catch (err) {
    const fehler = err instanceof Error ? err.message : String(err);
    console.warn(`Fernpool konnte nicht geladen werden (leer): ${fehler}`);
    return { heute, jetzt: jetzt.toISOString(), events: [], alle: [], quelle: "supabase", fehler };
  }
}

/**
 * Event-Pool für einen Magazin-Zeitraum (Plan Redaktion 4.2, Cursor-Prüfungen 5 und 6): dieselbe Abfrage, Schleife,
 * Spaltenvarianten, normalisieren und buendeln wie eventPoolLaden(), aber ab `von` statt heute und bis
 * max(bis, von + 60 Tage). So sieht der Pool aus wie der der Startseite am `von`. Kein "use cache" (seltene Läufe,
 * Route no-store). Fehler → WIRFT: Beispieldaten dürfen nie in einen Entwurf gelangen.
 */
export async function magazinPoolLaden(von: string, bis: string): Promise<EventPool> {
  const alle = await ausSupabaseLaden(von, bis);
  return { heute: von, jetzt: new Date().toISOString(), events: buendeln(alle), alle, quelle: "supabase", fehler: null };
}

/** Einzelnes Event per Slug laden (Fallback: UUID für Altlinks). */
export async function eventLaden(kennung: string): Promise<DddEvent | null> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 600, expire: 3600 });
  // Admin-Bereich leert diesen Tag nach jeder Event-Änderung (Plan Admin-Dashboard 4.4, revalidateTag mit expire: 0)
  cacheTag(EVENTS_CACHE_TAG);

  const pool = await eventPoolLaden();
  const istUuid = /^[0-9a-f-]{36}$/i.test(kennung);
  const treffer = pool.alle.find((e) => istUuid ? e.id === kennung : e.slug === kennung);
  if (treffer || pool.quelle === "beispiel") return treffer ?? null;

  const client = supabaseClient();
  if (!client) return null;
  try {
    const laden = (spalten: string) => {
      const query = client.from("events").select(spalten).eq("abgelehnt", false);
      return istUuid ? query.eq("id", kennung).maybeSingle() : query.eq("slug", kennung).maybeSingle();
    };
    const { data, error } = await mitSpalten(laden);
    if (error || !data) return null;
    return normalisieren(data as unknown as Zeile);
  } catch (err) {
    console.error(`Event ${kennung} konnte nicht geladen werden: ${err instanceof Error ? err.message : err}`);
    return null;
  }
}
