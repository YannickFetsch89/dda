// Konto anlegen (Plan 5.1 Schritte 1–2). Antwortet gleich (200, gleicher Text), ob die Adresse neu, unbestätigt oder
// Supabase gerade nicht erreichbar ist. AUSNAHME seit 17.11.2026 (Entscheidung des Auftraggebers): Gibt es zur Adresse
// schon ein BESTÄTIGTES Konto, sagt die Route das (409 „vorhanden“) und die Seite schickt zur Anmeldung – sonst wartet
// die Person vergeblich auf eine Mail (Supabase schickt in dem Fall keine). Damit lässt sich prüfen, ob eine Adresse
// ein Konto hat; das Bremslimit (10/Std je IP, 3/Std je Adresse) bleibt die Grenze dafür.
import type { SupabaseClient } from "@supabase/supabase-js";
import { zuVieleAnfragen } from "@/lib/formulare";
import { authClientAnfrage, kontoDienstClient } from "@/lib/konto/clients";
import { MELDUNG } from "@/lib/konto/konfig";
import { einwilligungSetzen } from "@/lib/konto/einwilligungen";
import { adresseNormal, adressSchluessel, nachweisImZeitfenster, passwortPruefen } from "@/lib/konto/pruefungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const NEUTRAL = { ok: true, meldung: MELDUNG.registriert };
const VORHANDEN = { fehler: MELDUNG.schonRegistriert, code: "vorhanden" };

export const POST = kontoRoute(
  { anmeldung: false, json: true, aendernd: true, limit: { name: "registrieren", max: 10, fensterMs: ZEIT.STUNDE } },
  async ({ body }) => {
    // Honeypot: still „erfolgreich“
    if (typeof body.website === "string" && body.website.trim()) return kontoAntwort(200, NEUTRAL);

    const email = adresseNormal(body.email);
    if (!email) return kontoAntwort(400, { fehler: "Bitte gib eine gültige Mailadresse ein.", code: "adresse" });
    if (!passwortPruefen(body.passwort)) return kontoAntwort(400, { fehler: MELDUNG.passwortRegel, code: "passwort" });
    if (body.alter_ok !== true) {
      return kontoAntwort(400, { fehler: "Bitte bestätige, dass du mindestens 16 Jahre alt bist.", code: "alter" });
    }
    if (zuVieleAnfragen("konto-registrieren-adresse", adressSchluessel(email), 3, ZEIT.STUNDE)) {
      return kontoAntwort(200, NEUTRAL); // gleiche Antwort, keine weitere Mail
    }

    const auth = authClientAnfrage();
    if (!auth) {
      console.error("Registrieren: SUPABASE_URL / SUPABASE_KEY fehlen");
      return kontoAntwort(200, NEUTRAL);
    }
    // Ohne Service-Key entstünde ein Konto ohne Alters-Nachweis, das sich auch auf /konto/willkommen nicht
    // abschließen ließe (Abschluss braucht denselben Key). Daher vorher abbrechen – die Antwort hängt nicht von
    // der Adresse ab, verrät also nichts (lokaler Test 17.11.2026: Key fehlte in web/.env.local).
    const dienst = kontoDienstClient();
    if (!dienst) {
      console.error("Registrieren: SUPABASE_SERVICE_KEY fehlt – kein Konto angelegt");
      return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    }
    try {
      // Bewusst OHNE Metadaten: raw_user_meta_data kann jeder mit dem anon-Key setzen, daraus wird nie ein Nachweis
      const { data, error } = await auth.auth.signUp({ email, password: body.passwort as string });
      const eingang = Date.now();
      if (error) {
        if (error.code === "user_already_exists" || error.code === "email_exists") return kontoAntwort(409, VORHANDEN);
        console.warn(`Registrieren: Supabase meldet ${error.code ?? error.status ?? "Fehler"}`);
        return kontoAntwort(200, NEUTRAL);
      }
      const user = data.user;
      // Leere identities = bestätigtes Konto mit dieser Adresse (Supabase schickt keine Mail) → zur Anmeldung
      if (user && (user.identities?.length ?? 0) === 0) return kontoAntwort(409, VORHANDEN);
      // Nachweis nur für ein Konto, das durch genau diese Anfrage entstanden ist (Plan 5.1 Schritt 2)
      if (user && (user.identities?.length ?? 0) > 0) {
        if (nachweisImZeitfenster(user.created_at, eingang)) {
          await nachweisSetzen(dienst, user.id);
        } else {
          console.warn("Registrieren: Konto-Zeitpunkt außerhalb des Zeitfensters – Alter wird auf /konto/willkommen abgefragt");
        }
      }
    } catch (err) {
      console.error(`Registrieren fehlgeschlagen: ${err instanceof Error ? err.name : "unbekannt"}`);
    }
    return kontoAntwort(200, NEUTRAL);
  },
);

/** Alter und Nutzungsbedingungen per Dienst-Client, nur wenn beide im Profil noch leer sind. */
async function nachweisSetzen(dienst: SupabaseClient, nutzerId: string) {
  const { data, error } = await dienst
    .from("profiles")
    .select("mindestalter_bestaetigt_am, nutzungsbedingungen_version")
    .eq("id", nutzerId)
    .maybeSingle();
  if (error || !data) {
    console.warn(`Registrieren: Profil nicht lesbar (${error?.code ?? "fehlt"}) – Alter wird auf /konto/willkommen abgefragt`);
    return;
  }
  if (data.mindestalter_bestaetigt_am || data.nutzungsbedingungen_version) return;
  // Scheitert ein Aufruf, fragt /konto/willkommen das Alter nach der Bestätigung ab (Plan 5.1 Schritt 7)
  await einwilligungSetzen(dienst, nutzerId, "mindestalter", true, "registrierung");
  await einwilligungSetzen(dienst, nutzerId, "nutzungsbedingungen", true, "registrierung");
}
