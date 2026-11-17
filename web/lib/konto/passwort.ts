// Nutzerkonten – Passwort setzen bzw. ändern mit einem anfragebezogenen Auth-Client (Plan 5.1 Schritte 10 und 12).
// Danach werden alle ANDEREN Sitzungen beendet (signOut scope „others“); ins Cookie kommt die Sitzung
// NACH updateUser (getSession desselben Clients).
import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { authClientAnfrage } from "./clients";

export type PasswortErgebnis =
  | { ok: true; session: { access_token: string; refresh_token: string; user: { id: string } } }
  | { ok: false; grund: "aktuell_falsch" | "fehler" | "zu_schwach" };

async function setzenMitClient(client: SupabaseClient, neu: string): Promise<PasswortErgebnis> {
  const { error } = await client.auth.updateUser({ password: neu });
  if (error) {
    // weak_password / same_password usw. → für Nutzer „zu schwach/ungeeignet“, ohne Fehlertext von Supabase
    const schwach = error.code === "weak_password" || error.code === "same_password";
    console.warn(`Passwort setzen: Supabase meldet ${error.code ?? error.status ?? "Fehler"}`);
    return { ok: false, grund: schwach ? "zu_schwach" : "fehler" };
  }
  const { error: abmeldeFehler } = await client.auth.signOut({ scope: "others" });
  if (abmeldeFehler) console.warn(`Andere Sitzungen nicht beendet (${abmeldeFehler.code ?? abmeldeFehler.status})`);
  const { data } = await client.auth.getSession();
  if (!data.session) return { ok: false, grund: "fehler" };
  return { ok: true, session: data.session };
}

/** Nach Reset (Plan 5.1 Schritt 10): mit der bestehenden (Reset-)Sitzung das neue Passwort setzen. */
export async function passwortSetzen(access: string, refresh: string, neu: string): Promise<PasswortErgebnis> {
  const client = authClientAnfrage();
  if (!client) return { ok: false, grund: "fehler" };
  const { error } = await client.auth.setSession({ access_token: access, refresh_token: refresh });
  if (error) return { ok: false, grund: "fehler" };
  return setzenMitClient(client, neu);
}

/** Im Konto (Plan 5.1 Schritt 12): erst das aktuelle Passwort per frischer Anmeldung prüfen, dann setzen. */
export async function passwortAendern(email: string, aktuell: string, neu: string): Promise<PasswortErgebnis> {
  const client = authClientAnfrage();
  if (!client) return { ok: false, grund: "fehler" };
  const { data, error } = await client.auth.signInWithPassword({ email, password: aktuell });
  if (error || !data.session) return { ok: false, grund: "aktuell_falsch" };
  return setzenMitClient(client, neu);
}

/** Aktuelles Passwort prüfen, ohne etwas zu ändern (Konto löschen, Plan 5.7). */
export async function passwortStimmt(email: string, passwort: string): Promise<boolean> {
  const client = authClientAnfrage();
  if (!client) return false;
  const { data, error } = await client.auth.signInWithPassword({ email, password: passwort });
  if (error || !data.session) return false;
  // Die frische Prüf-Sitzung gleich wieder beenden (nur diese, scope „local“)
  await client.auth.signOut({ scope: "local" }).catch(() => undefined);
  return true;
}
