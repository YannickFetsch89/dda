// Bestätigungsmail erneut senden (Plan 5.1 Schritt 4). Neutrale Antwort, je Adresse höchstens alle 60 Sekunden.
import { zuVieleAnfragen } from "@/lib/formulare";
import { authClientAnfrage } from "@/lib/konto/clients";
import { MELDUNG } from "@/lib/konto/konfig";
import { adresseNormal, adressSchluessel } from "@/lib/konto/pruefungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const NEUTRAL = { ok: true, meldung: MELDUNG.bestaetigungUnterwegs };

export const POST = kontoRoute(
  { anmeldung: false, json: true, aendernd: true, limit: { name: "bestaetigung", max: 10, fensterMs: ZEIT.STUNDE } },
  async ({ body }) => {
    if (typeof body.website === "string" && body.website.trim()) return kontoAntwort(200, NEUTRAL);
    const email = adresseNormal(body.email);
    if (!email) return kontoAntwort(400, { fehler: "Bitte gib eine gültige Mailadresse ein.", code: "adresse" });
    const schluessel = adressSchluessel(email);
    if (zuVieleAnfragen("konto-bestaetigung-abstand", schluessel, 1, 60_000)) return kontoAntwort(200, NEUTRAL);
    if (zuVieleAnfragen("konto-bestaetigung-adresse", schluessel, 3, ZEIT.STUNDE)) return kontoAntwort(200, NEUTRAL);

    const auth = authClientAnfrage();
    if (auth) {
      try {
        const { error } = await auth.auth.resend({ type: "signup", email });
        if (error) console.warn(`Bestätigung erneut: Supabase meldet ${error.code ?? error.status ?? "Fehler"}`);
      } catch (err) {
        console.error(`Bestätigung erneut fehlgeschlagen: ${err instanceof Error ? err.name : "unbekannt"}`);
      }
    }
    return kontoAntwort(200, NEUTRAL);
  },
);
