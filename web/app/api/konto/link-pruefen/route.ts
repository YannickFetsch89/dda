// Link aus der Mail bzw. Ersatz-Code prüfen (Plan 5.1 Schritte 3 und 9, 5.2). Läuft nur per POST nach einem Klick,
// damit Mail-Scanner das Einmal-Token nicht verbrauchen.
//   art=neu   → Bestätigung: volle Sitzung, weiter auf /konto/willkommen bzw. Ziel
//   art=reset → eingeschränkte Reset-Sitzung (1 Stunde, nur passwort-setzen), weiter auf /konto/passwort-neu
import type { EmailOtpType } from "@supabase/supabase-js";
import { anfragenImFenster, zuVieleAnfragen } from "@/lib/formulare";
import { resetSitzungCookie, sitzungStarten } from "@/lib/konto/anmeldung";
import { authClientAnfrage } from "@/lib/konto/clients";
import { MELDUNG } from "@/lib/konto/konfig";
import { adresseNormal, adressSchluessel } from "@/lib/konto/pruefungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

/**
 * Typ des Bestätigungslinks (Plan 5.1 Schritt 13): „email“ („signup“ gilt bei Supabase als veraltet).
 * BESTÄTIGT am 17.11.2026: Der Auftraggeber hat lokal gegen das echte Supabase-Projekt registriert, den Link aus der
 * Mail geöffnet und landete angemeldet auf /konto/willkommen; „Passwort vergessen“ (recovery) ebenso.
 * Der Ersatz-Code steht nicht in unserer Bestätigungsmail (docs/konto-mails/1-confirm-signup.html); der Code-Zweig
 * unten bleibt für den Fall, dass er später ergänzt wird.
 */
export const BESTAETIGUNG_TYP: EmailOtpType = "email";

const FEHL = "konto-code-fehl";
const FALSCH = { fehler: MELDUNG.linkFalsch, code: "link" };

export const POST = kontoRoute(
  { anmeldung: false, json: true, aendernd: true, limit: { name: "link-pruefen", max: 30, fensterMs: ZEIT.STUNDE } },
  async ({ body, lokal }) => {
    const art = body.art === "reset" ? "reset" : body.art === "neu" ? "neu" : body.art === "email" ? "email" : null;
    if (!art) return kontoAntwort(400, FALSCH);
    const auth = authClientAnfrage();
    if (!auth) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });

    const tokenHash = typeof body.token_hash === "string" ? body.token_hash.trim() : "";
    const code = typeof body.code === "string" ? body.code.replace(/\s/g, "") : "";
    let ergebnis;

    // Mailadresse ändern (17.11.2026): zwei Links (alte und neue Adresse). Nach dem ersten gibt Supabase keine Sitzung
    // zurück, nach dem zweiten eine mit der neuen Adresse – die kommt dann ins Cookie dieses Browsers.
    if (art === "email") {
      if (!tokenHash || tokenHash.length > 200) return kontoAntwort(400, FALSCH);
      const r = await auth.auth.verifyOtp({ token_hash: tokenHash, type: "email_change" });
      if (r.error) return kontoAntwort(400, FALSCH);
      if (!r.data.session) return kontoAntwort(200, { ok: true, meldung: MELDUNG.mailHalb });
      const { setCookies } = await sitzungStarten(r.data.session, lokal, null);
      return kontoAntwort(200, { ok: true, meldung: MELDUNG.mailFertig }, setCookies);
    }

    if (tokenHash) {
      if (tokenHash.length > 200) return kontoAntwort(400, FALSCH);
      ergebnis = await auth.auth.verifyOtp({ token_hash: tokenHash, type: art === "reset" ? "recovery" : BESTAETIGUNG_TYP });
    } else if (art === "neu" && /^\d{6}$/.test(code)) {
      // Ersatz-Code nur bei der Bestätigung, nie beim Reset (Plan 5.1 Schritt 9)
      const email = adresseNormal(body.email);
      if (!email) return kontoAntwort(400, FALSCH);
      const schluessel = adressSchluessel(email);
      if (anfragenImFenster(FEHL, schluessel) >= 5) return kontoAntwort(400, FALSCH);
      ergebnis = await auth.auth.verifyOtp({ email, token: code, type: "email" });
      if (ergebnis.error || !ergebnis.data.session) zuVieleAnfragen(FEHL, schluessel, Number.MAX_SAFE_INTEGER, ZEIT.VIERTELSTUNDE);
    } else {
      return kontoAntwort(400, FALSCH);
    }

    const session = ergebnis.data.session;
    if (ergebnis.error || !session) return kontoAntwort(400, FALSCH);

    if (art === "reset") {
      return kontoAntwort(200, { ok: true, ziel: "/konto/passwort-neu" }, [resetSitzungCookie(session, lokal)]);
    }
    const { setCookies, ziel } = await sitzungStarten(session, lokal, body.weiter);
    return kontoAntwort(200, { ok: true, ziel }, setCookies);
  },
);
