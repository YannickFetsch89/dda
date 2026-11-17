// Nutzerkonten – Einwilligungen setzen (Plan 3.4, 4.5). Nur über die Datenbank-Funktionen mit dem
// Dienst-Client, für die Nutzer-ID aus der geprüften Sitzung. textversion kommt immer aus TEXTVERSIONEN.
import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { TEXTVERSIONEN, type EinwilligungArt, type Handlung } from "./konfig";

export type EinwilligungErgebnis = { ok: true; zurueck: string[] } | { ok: false; code: string };

/** einwilligung_setzen(nutzer, art, erteilt, textversion, handlung) – setzt Profilspalte und Nachweis zusammen. */
export async function einwilligungSetzen(
  dienst: SupabaseClient,
  nutzerId: string,
  art: EinwilligungArt,
  erteilt: boolean,
  handlung: Handlung,
): Promise<EinwilligungErgebnis> {
  const { data, error } = await dienst.rpc("einwilligung_setzen", {
    nutzer: nutzerId,
    art,
    erteilt,
    textversion: TEXTVERSIONEN[art],
    handlung,
  });
  if (error) {
    const code = /^[a-z0-9_]+$/.test(error.message ?? "") ? error.message : `db_${error.code ?? "fehler"}`;
    console.error(`Einwilligung ${art} nicht gespeichert (${code})`);
    return { ok: false, code };
  }
  return { ok: true, zurueck: Array.isArray(data) ? (data as string[]) : [] };
}

export interface Stammdaten {
  vorname: string;
  nachname: string;
  geburtsdatum: string;
}

/**
 * stammdaten_setzen(nutzer, vorname, nachname, datum) → „ok“ oder „unter_16“ (E16, Altersprüfung in der Datenbank).
 * Pflichtangaben aus dem Nutzungsvertrag, daher ohne Einwilligungszeile.
 */
export async function stammdatenSetzen(
  dienst: SupabaseClient,
  nutzerId: string,
  s: Stammdaten,
): Promise<{ ok: true; ergebnis: "ok" | "unter_16" } | { ok: false; code: string }> {
  const { data, error } = await dienst.rpc("stammdaten_setzen", {
    nutzer: nutzerId,
    vorname: s.vorname,
    nachname: s.nachname,
    datum: s.geburtsdatum,
  });
  if (error) {
    const code = /^[a-z0-9_]+$/.test(error.message ?? "") ? error.message : `db_${error.code ?? "fehler"}`;
    console.error(`Stammdaten nicht gespeichert (${code})`);
    return { ok: false, code };
  }
  return { ok: true, ergebnis: data === "unter_16" ? "unter_16" : "ok" };
}
