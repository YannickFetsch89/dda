// Gemeinsame Supabase-Clients für den Server – je EINER pro Prozess.
//
// Wichtig (Absturz 06.11.2026, „JavaScript heap out of memory“ nach ~14 h): supabase-js startet in Node
// pro Client einen Dauer-Timer für das Token-Auffrischen (autoRefreshToken, Standard: an). Der Timer
// hält den Client für immer im Speicher. Wurde pro Anfrage ein neuer Client erzeugt (Event-Bilder,
// Eventseiten außerhalb des Pools), wuchs der Speicher bis zum Absturz. Deshalb: ein Client pro Prozess,
// ohne Auffrischen und ohne Sitzung (wir melden uns auf der Website nie an).
import "server-only"; // enthält den Service-Key-Client – darf nie in ein Browser-Bundle
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const OPTIONEN = { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } };

let lesend: SupabaseClient | null | undefined;
let schreibend: SupabaseClient | null | undefined;

/** Lese-Client mit dem anon-Key (öffentliche Daten). null, wenn die Umgebungsvariablen fehlen. */
export function leseClient(): SupabaseClient | null {
  if (lesend === undefined) {
    const url = process.env.SUPABASE_URL;
    const key = process.env.SUPABASE_KEY;
    lesend = url && key ? createClient(url, key, OPTIONEN) : null;
  }
  return lesend;
}

/** Schreib-Client mit dem Service-Key – NUR serverseitig (Formulare). null, wenn der Key fehlt. */
export function dienstClient(): SupabaseClient | null {
  if (schreibend === undefined) {
    const url = process.env.SUPABASE_URL;
    const key = process.env.SUPABASE_SERVICE_KEY;
    schreibend = url && key ? createClient(url, key, OPTIONEN) : null;
  }
  return schreibend;
}
