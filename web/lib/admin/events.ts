// Admin-Bereich – Events bearbeiten (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.4, Stufe 1d).
// Reine Funktionen (getestet in web/tests/admin-events.test.ts): Eingaben prüfen, Änderung und Feldschutz bauen.

import { KATEGORIEN } from "../kategorien";
import { istSammelquelle } from "../quellen-rang";

/** Felder, die der Admin-Bereich ändern darf (Whitelist, 4.4) */
export const BEARBEITBAR = [
  "titel",
  "datum",
  "datum_bis",
  "uhrzeit",
  "ort",
  "adresse",
  "stadtteil",
  "kategorie",
  "unterkategorie",
  "preis",
  "beschreibung",
  "bild_url",
  "ort_id",
  "abgesagt",
  "abgelehnt",
  "nicht_empfehlen",
] as const;
export type Feld = (typeof BEARBEITBAR)[number];

/** Änderungen an diesen Feldern setzen beim ersten Mal die abgleich_*-Spalten (Schritt 0 der Pipeline) */
export const ABGLEICH_FELDER = ["titel", "datum", "uhrzeit", "ort"] as const;

/** Website-Slug → DB-Wert (die Website nennt „family“ „familie“) */
export function kategorieInDb(slug: string): string | null {
  if (!KATEGORIEN.some((k) => k.slug === slug)) return null;
  return slug === "familie" ? "family" : slug;
}

const DATUM = /^\d{4}-\d{2}-\d{2}$/;
const UHRZEIT = /^([01]\d|2[0-3]):[0-5]\d$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

type Wert = string | boolean | null;

function text(wert: unknown, max: number, pflicht: boolean): { ok: true; wert: string | null } | { ok: false } {
  if (wert === null || wert === undefined || (typeof wert === "string" && wert.trim() === "")) {
    return pflicht ? { ok: false } : { ok: true, wert: null };
  }
  if (typeof wert !== "string" || wert.trim().length > max) return { ok: false };
  return { ok: true, wert: wert.trim() };
}

/**
 * Prüft die Eingaben einer Bearbeitung. Unbekannte Felder werden abgewiesen (nicht still ignoriert), damit ein
 * Tippfehler im Client nicht unbemerkt bleibt.
 */
export function eingabenPruefen(eingabe: Record<string, unknown>): { ok: true; felder: Partial<Record<Feld, Wert>> } | { ok: false; fehler: string } {
  const felder: Partial<Record<Feld, Wert>> = {};
  for (const [schluessel, wert] of Object.entries(eingabe)) {
    if (!(BEARBEITBAR as readonly string[]).includes(schluessel)) return { ok: false, fehler: `Feld „${schluessel}“ ist nicht bearbeitbar.` };
    const feld = schluessel as Feld;
    switch (feld) {
      case "abgesagt":
      case "abgelehnt":
      case "nicht_empfehlen":
        if (typeof wert !== "boolean") return { ok: false, fehler: `${feld}: ja oder nein erwartet.` };
        felder[feld] = wert;
        break;
      case "datum":
      case "datum_bis": {
        const t = text(wert, 10, feld === "datum");
        if (!t.ok || (t.wert !== null && !DATUM.test(t.wert))) return { ok: false, fehler: `${feld}: Datum als JJJJ-MM-TT.` };
        felder[feld] = t.wert;
        break;
      }
      case "uhrzeit": {
        const t = text(wert, 5, false);
        if (!t.ok || (t.wert !== null && !UHRZEIT.test(t.wert))) return { ok: false, fehler: "uhrzeit: Uhrzeit als HH:MM." };
        felder[feld] = t.wert;
        break;
      }
      case "kategorie": {
        const db = typeof wert === "string" ? kategorieInDb(wert) : null;
        if (!db) return { ok: false, fehler: "kategorie: unbekannte Kategorie." };
        felder[feld] = db;
        break;
      }
      case "ort_id": {
        const t = text(wert, 36, false);
        if (!t.ok || (t.wert !== null && !UUID.test(t.wert))) return { ok: false, fehler: "ort_id: keine gültige ID." };
        felder[feld] = t.wert;
        break;
      }
      case "bild_url": {
        const t = text(wert, 1000, false);
        if (!t.ok || (t.wert !== null && !/^(https:\/\/|\/)/.test(t.wert))) return { ok: false, fehler: "bild_url: https-Adresse oder eigener Pfad." };
        felder[feld] = t.wert;
        break;
      }
      default: {
        const grenzen: Record<string, [number, boolean]> = {
          titel: [300, true],
          ort: [200, true],
          adresse: [300, false],
          stadtteil: [80, false],
          unterkategorie: [60, false],
          preis: [100, false],
          beschreibung: [20000, false],
        };
        const [max, pflicht] = grenzen[feld];
        const t = text(wert, max, pflicht);
        if (!t.ok) return { ok: false, fehler: `${feld}: ${pflicht ? "Pflichtfeld, " : ""}höchstens ${max} Zeichen.` };
        felder[feld] = t.wert;
      }
    }
  }
  if (!Object.keys(felder).length) return { ok: false, fehler: "Keine Änderung." };
  return { ok: true, felder };
}

export interface EventZeile {
  id: string;
  titel: string;
  datum: string;
  uhrzeit: string | null;
  ort: string;
  redaktion_felder: string[] | null;
  abgleich_datum: string | null;
  [feld: string]: unknown;
}

/**
 * Vergleichswert: Uhrzeit aus der DB kommt als HH:MM:SS; Texte ohne Rand-Leerzeichen, leer = null. Sonst gälte ein
 * unberührtes Feld mit Leerzeichen am Ende als geändert und würde ungewollt vor der Pipeline geschützt.
 */
function vergleich(feld: string, wert: unknown): unknown {
  if (typeof wert === "string") {
    const t = feld === "uhrzeit" ? wert.slice(0, 5) : wert.trim();
    return t === "" ? null : t;
  }
  return wert ?? null;
}

/**
 * Baut das Update: nur geänderte Felder, redaktion_felder um diese ergänzt, beim ersten Ändern von Titel, Datum,
 * Uhrzeit oder Ort zusätzlich die bisherigen Werte als abgleich_* (Werte der Quelle für Schritt 0, 4.4 Teil B).
 */
export function updateBauen(bisher: EventZeile, felder: Partial<Record<Feld, Wert>>): { update: Record<string, unknown>; geaendert: Feld[] } {
  const geaendert = (Object.keys(felder) as Feld[]).filter((f) => vergleich(f, felder[f]) !== vergleich(f, bisher[f]));
  const update: Record<string, unknown> = {};
  for (const f of geaendert) update[f] = felder[f];
  if (!geaendert.length) return { update, geaendert };

  update.redaktion_felder = [...new Set([...(bisher.redaktion_felder ?? []), ...geaendert])].sort();
  if (bisher.abgleich_datum === null && geaendert.some((f) => (ABGLEICH_FELDER as readonly string[]).includes(f))) {
    update.abgleich_titel = bisher.titel;
    update.abgleich_datum = bisher.datum;
    update.abgleich_uhrzeit = bisher.uhrzeit;
    update.abgleich_ort = bisher.ort;
  }
  return { update, geaendert };
}

/** Sammel-Quellen wie pipeline/deduplication.ist_aggregator: Rang ≥ 2 (lib/quellen-rang.ts), Uhrzeit dort oft der Einlass */
export function istAggregator(e: { quelle_name?: unknown; quelle_url?: unknown }): boolean {
  return istSammelquelle(e);
}

/**
 * Uhrzeit der Dublette übernehmen? Gleiche Regel wie pipeline/vorschlaege.py: wenn die behaltene keine hat, oder beide
 * abweichen und die behaltene von einer Sammel-Quelle kommt, die Dublette vom Veranstalter (Cursor-Prüfung 1d).
 */
export function uhrzeitUebernehmen(
  behalten: { uhrzeit?: unknown; quelle_name?: unknown; quelle_url?: unknown },
  dublette: { uhrzeit?: unknown; quelle_name?: unknown; quelle_url?: unknown },
): boolean {
  const ub = typeof behalten.uhrzeit === "string" ? behalten.uhrzeit.slice(0, 5) : "";
  const ud = typeof dublette.uhrzeit === "string" ? dublette.uhrzeit.slice(0, 5) : "";
  if (!ud) return false;
  if (!ub) return true;
  return ub !== ud && istAggregator(behalten) && !istAggregator(dublette);
}

/** Filter der Event-Liste (4.4) */
export const LISTEN_FILTER = ["abgelehnt", "abgesagt", "nicht_empfehlen", "ohne_bild", "ohne_stadtteil", "ohne_adresse", "ohne_ort_id", "redaktion"] as const;
export type ListenFilter = (typeof LISTEN_FILTER)[number];
