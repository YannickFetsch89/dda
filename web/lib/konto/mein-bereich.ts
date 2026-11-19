// Nutzerkonten – gemeinsame Bausteine der Routen start, fuer-dich und uebersicht
// (Plan docs/plan-mein-bereich-stufe1-2026-11-18.md, Abschnitte 5 und 6).
import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { stufenKontext, type StufenKontext } from "../ableitungen";
import { eventPoolLaden } from "../daten";
import type { Eingabe, Gemerkt, Interessen, Vorschlag } from "../fuer-dich";
import type { DddEvent } from "../typen";
import { kontoDienstClient } from "./clients";
import { hinweisCookie } from "./cookies";
import { MELDUNG } from "./konfig";
import { merklisteAufteilen } from "./merk-logik";
import { eventsFuerIds } from "./merkliste-events";
import { uuidGueltig } from "./pruefungen";
import { kontoAntwort, type KontoKontext } from "./route";

// ── Sensibel-Menge (E13): nur Dienst-Client, Cache im Prozess, Fehler nie cachen ─────────────────────
const SENSIBEL_MS = 10 * 60 * 1000;
let sensibelCache: { menge: Set<string>; bis: number } | null = null;

/** IDs aus event_sensibel. null bei Fehler (dann rechnen start und fuer-dich nicht, Plan 5). Nie in Antworten. */
export async function sensibelMenge(jetzt = Date.now()): Promise<Set<string> | null> {
  if (sensibelCache && sensibelCache.bis > jetzt) return sensibelCache.menge;
  const dienst = kontoDienstClient();
  if (!dienst) return null;
  const menge = new Set<string>();
  for (let von = 0; ; von += 1000) {
    const { data, error } = await dienst.from("event_sensibel").select("event_id").range(von, von + 999);
    if (error) {
      console.error(`Sensibel-Menge nicht lesbar (${error.code ?? "fehler"})`);
      return null;
    }
    for (const z of data ?? []) menge.add(z.event_id as string);
    if (!data || data.length < 1000) break;
  }
  sensibelCache = { menge, bis: jetzt + SENSIBEL_MS };
  return menge;
}
export const sensibelCacheLeeren = () => {
  sensibelCache = null;
};

// ── Stufen je Pool (teuer: Serien-Erkennung), einmal je geladenem Pool ──────────────────────────────
let stufenCache: { schluessel: string; stufen: StufenKontext } | null = null;
function stufenFuer(events: DddEvent[], heute: string, schluessel: string): StufenKontext {
  if (stufenCache?.schluessel === schluessel) return stufenCache.stufen;
  const stufen = stufenKontext(events, heute);
  stufenCache = { schluessel, stufen };
  return stufen;
}

// ── Merkliste des Kontos mit gemerkt_am (eigene Zeilen über RLS) ────────────────────────────────────
export interface KontoMerkliste {
  zeilen: { event_id: string; gemerkt_am: string }[];
  /** Events zu den IDs; leer, wenn das Laden scheiterte */
  events: DddEvent[];
  heute: string;
  eventsFehler: boolean;
}

export async function kontoMerklisteLaden(db: SupabaseClient): Promise<KontoMerkliste | null> {
  const { data, error } = await db.from("merkliste").select("event_id, gemerkt_am").order("gemerkt_am", { ascending: false }).limit(1000);
  if (error) return null;
  const zeilen = (data ?? []).map((z) => ({ event_id: z.event_id as string, gemerkt_am: z.gemerkt_am as string }));
  try {
    const { heute, events } = await eventsFuerIds(zeilen.map((z) => z.event_id));
    return { zeilen, events, heute, eventsFehler: false };
  } catch (err) {
    console.error(`Mein Bereich: Merkliste-Events nicht geladen (${err instanceof Error ? err.name : "unbekannt"})`);
    return { zeilen, events: [], heute: "", eventsFehler: true };
  }
}

/** Kommende und vergangene Merkungen (merklisteAufteilen) – inklusive eigener sensibler, ohne Kennzeichnung. */
export function merklisteTeilen(m: KontoMerkliste, heute: string) {
  return merklisteAufteilen(m.events, heute);
}

// ── Eingabe für lib/fuer-dich ───────────────────────────────────────────────────────────────────────
export async function eingabeBauen(
  ctx: KontoKontext,
  merkliste: KontoMerkliste | null,
  sensibel: ReadonlySet<string>,
): Promise<Eingabe> {
  const pool = await eventPoolLaden();
  const p = ctx.profil!;
  const zeit = new Map((merkliste?.zeilen ?? []).map((z) => [z.event_id, z.gemerkt_am]));
  const gemerkt: Gemerkt[] = p.personalisierung
    ? (merkliste?.events ?? []).map((event) => ({ event, gemerktAm: zeit.get(event.id) ?? "" }))
    : [];
  // Gemerkte Events auch dann ausschließen, wenn ihre Events nicht geladen werden konnten
  const fehlend = (merkliste?.zeilen ?? []).filter((z) => !gemerkt.some((g) => g.event.id === z.event_id));
  return {
    events: pool.events,
    heute: pool.heute,
    stufen: stufenFuer(pool.events, pool.heute, `${pool.jetzt}|${pool.events.length}`),
    personalisierung: p.personalisierung,
    interessen: (p.praeferenzen ?? {}) as Interessen,
    merkliste: p.personalisierung ? [...gemerkt, ...fehlend.map((z) => ({ event: platzhalter(z.event_id), gemerktAm: z.gemerkt_am }))] : [],
    sensibel,
  };
}

/** Nur zum Ausschluss: ein gemerktes Event ohne geladene Daten darf nicht vorgeschlagen werden, gibt aber keine Punkte. */
function platzhalter(id: string): DddEvent {
  return {
    id, titel: "", datum: "0000-00-00", datum_bis: null, uhrzeit: null, ort: "", adresse: null, kategorie: "sonstiges",
    beschreibung: null, preis: null, quelle_name: null, quelle_url: null, bild_url: null, stadtteil: null,
    erstellt_am: null, tipp_des_tages: false, highlight_der_woche: false, top_event_des_monats: false, slug: null,
    abgesagt: false, reihe: null, uhrzeiten: null,
  };
}

// ── Kleine Helfer der Routen ────────────────────────────────────────────────────────────────────────

/** `ohne`: kommagetrennt, höchstens 24 Einträge, ungültige fallen still weg (Plan 6). */
export function ohneLesen(wert: string | null): Set<string> {
  return new Set((wert ?? "").split(",").slice(0, 24).map((s) => s.trim()).filter(uuidGueltig));
}

/** Öffentliche Event-Felder plus Begründung, keine Punkte, keine Bezüge (Plan 6). */
export const mitBegruendung = (v: Vorschlag) => ({ ...v.event, begruendung: v.begruendung });

/**
 * Verteidigung gegen eine inkonsistente Zeile (Sperre unter 16 und trotzdem Mindestalter gesetzt, Plan 3.0):
 * 403 unter16_gesperrt, nie das Hinweis-Cookie „1“; „0“ nur für den Browser.
 */
export function gesperrtAbwehr(ctx: KontoKontext): Response | null {
  if (!ctx.profil?.unter16_gesperrt_am) return null;
  ctx.ohneHinweis = true;
  if (ctx.sitzung?.quelle === "cookie") ctx.setCookies.push(hinweisCookie("0", ctx.lokal));
  return kontoAntwort(403, { fehler: MELDUNG.unter16, code: "unter16_gesperrt" });
}
