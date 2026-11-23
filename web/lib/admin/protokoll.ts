// Admin-Bereich – Protokoll jeder schreibenden Aktion (Plan Admin-Dashboard 3.3, Tabelle admin_protokoll aus
// database/admin_grundlagen_2026-11-23.sql). Geschrieben mit dem Token des Admins; admin_id setzt die Datenbank.
import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";

export interface ProtokollEintrag {
  aktion: string;
  tabelle?: string;
  ziel_id?: string;
  vorher?: unknown;
  nachher?: unknown;
}

/** Schreibt einen Eintrag. Fehler werden gemeldet, aber nicht geworfen: Das Protokoll blockiert keine Anmeldung. */
export async function protokollieren(db: SupabaseClient, eintrag: ProtokollEintrag): Promise<boolean> {
  try {
    const { error } = await db.from("admin_protokoll").insert({
      aktion: eintrag.aktion.slice(0, 80),
      tabelle: eintrag.tabelle ?? null,
      ziel_id: eintrag.ziel_id ?? null,
      vorher: eintrag.vorher ?? null,
      nachher: eintrag.nachher ?? null,
    });
    if (error) {
      console.error("Admin-Protokoll konnte nicht geschrieben werden:", error.message);
      return false;
    }
    return true;
  } catch (e) {
    console.error("Admin-Protokoll konnte nicht geschrieben werden:", e);
    return false;
  }
}
