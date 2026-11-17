// „Passwort vergessen“ (Plan 5.1 Schritt 8). Antwort immer gleich. Die Mail enthält nur den Link (Vorlage Reset Password).
import { zuVieleAnfragen } from "@/lib/formulare";
import { authClientAnfrage } from "@/lib/konto/clients";
import { MELDUNG } from "@/lib/konto/konfig";
import { adresseNormal, adressSchluessel } from "@/lib/konto/pruefungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const NEUTRAL = { ok: true, meldung: MELDUNG.resetUnterwegs };

export const POST = kontoRoute(
  { anmeldung: false, json: true, aendernd: true, limit: { name: "passwort-vergessen", max: 10, fensterMs: ZEIT.STUNDE } },
  async ({ body }) => {
    if (typeof body.website === "string" && body.website.trim()) return kontoAntwort(200, NEUTRAL);
    const email = adresseNormal(body.email);
    if (!email) return kontoAntwort(400, { fehler: "Bitte gib eine gültige Mailadresse ein.", code: "adresse" });
    if (zuVieleAnfragen("konto-reset-adresse", adressSchluessel(email), 3, ZEIT.STUNDE)) return kontoAntwort(200, NEUTRAL);

    const auth = authClientAnfrage();
    if (auth) {
      try {
        const { error } = await auth.auth.resetPasswordForEmail(email);
        if (error) console.warn(`Passwort vergessen: Supabase meldet ${error.code ?? error.status ?? "Fehler"}`);
      } catch (err) {
        console.error(`Passwort vergessen fehlgeschlagen: ${err instanceof Error ? err.name : "unbekannt"}`);
      }
    }
    return kontoAntwort(200, NEUTRAL);
  },
);
