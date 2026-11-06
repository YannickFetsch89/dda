// Datenzugriff: lädt alle relevanten Events einmal aus Supabase und cached sie 10 Minuten.
// Alle Ansichten leiten ihre Listen aus diesem Pool ab (siehe lib/ableitungen.ts).
import { cacheLife } from "next/cache";
import { leseClient } from "./supabase-server";
import beispiel from "./beispiel-events.json";
import { kategorieAusDb } from "./kategorien";
import { heuteBerlin, plusTage, tageZwischen } from "./datum";
import { buendeln } from "./termine";
import type { DddEvent, EventPool } from "./typen";

const SPALTEN_BASIS =
  "id, titel, datum, datum_bis, uhrzeit, ort, adresse, kategorie, beschreibung, preis, quelle_name, quelle_url, bild_url, stadtteil, slug, erstellt_am, tipp_des_tages, highlight_der_woche, top_event_des_monats";
// Neuere Spalten zuerst; fehlen sie in der DB noch, wird mit der nächsten Variante geladen (siehe spaltenFehlt)
const SPALTEN_VARIANTEN = [
  `${SPALTEN_BASIS}, abgesagt, reihe:reihen(slug, titel)`,
  `${SPALTEN_BASIS}, abgesagt`,
  SPALTEN_BASIS,
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
    preis: text(z.preis),
    quelle_name: text(z.quelle_name),
    quelle_url: text(z.quelle_url),
    bild_url: text(z.bild_url),
    stadtteil: text(z.stadtteil),
    slug: text(z.slug),
    erstellt_am: text(z.erstellt_am),
    tipp_des_tages: z.tipp_des_tages === true,
    highlight_der_woche: z.highlight_der_woche === true,
    top_event_des_monats: z.top_event_des_monats === true,
    abgesagt: z.abgesagt === true || ABSAGE.test(titel) || (ortUngueltig && ABSAGE.test(ortRoh ?? "")),
    reihe: reiheAus(z.reihe),
    uhrzeiten: null,
  };
}

function reiheAus(wert: unknown): DddEvent["reihe"] {
  const r = (Array.isArray(wert) ? wert[0] : wert) as { slug?: unknown; titel?: unknown } | null | undefined;
  return r && typeof r.slug === "string" && typeof r.titel === "string" ? { slug: r.slug, titel: r.titel } : null;
}

/** Supabase meldet eine unbekannte Spalte/Beziehung (Migration noch nicht ausgeführt). */
function spaltenFehlt(meldung: string | undefined): boolean {
  return !!meldung && /abgesagt|reihe/.test(meldung);
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

async function ausSupabaseLaden(heute: string): Promise<DddEvent[]> {
  const client = supabaseClient();
  if (!client) throw new Error("SUPABASE_URL / SUPABASE_KEY fehlen in .env.local");

  const bis = plusTage(heute, TAGE_VORAUS);
  const events: DddEvent[] = [];
  let variante = 0;
  for (let seite = 0; seite < 20; seite++) {
    const { data, error } = await client
      .from("events")
      .select(SPALTEN_VARIANTEN[variante])
      .eq("abgelehnt", false)
      .or(`datum.gte.${heute},datum_bis.gte.${heute}`)
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
      top_event_des_monats: id === "e13",
    };
  });
}

export async function eventPoolLaden(): Promise<EventPool> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 600, expire: 3600 });

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

/** Einzelnes Event per Slug laden (Fallback: UUID für Altlinks). */
export async function eventLaden(kennung: string): Promise<DddEvent | null> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 600, expire: 3600 });

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
