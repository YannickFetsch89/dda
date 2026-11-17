// Anmelden mit Mail und Passwort (Plan 5.1 Schritte 5–7, 6).
// Bremse je Paar aus IP und Adresse: nach 5 Fehlversuchen in 15 Minuten wird dieses Paar ohne Aufruf von Supabase
// mit derselben Meldung abgewiesen – auch mit richtigem Passwort. Andere IPs (die echte Person) sind nicht betroffen.
import { anfragenImFenster, zuVieleAnfragen } from "@/lib/formulare";
import { sitzungStarten } from "@/lib/konto/anmeldung";
import { authClientAnfrage } from "@/lib/konto/clients";
import { MELDUNG } from "@/lib/konto/konfig";
import { adresseNormal, adressSchluessel } from "@/lib/konto/pruefungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const FEHL = "konto-anmelden-fehl";
const FALSCH = { fehler: MELDUNG.anmeldenFalsch, code: "falsch" };

export const POST = kontoRoute(
  { anmeldung: false, json: true, aendernd: true, limit: { name: "anmelden", max: 30, fensterMs: ZEIT.STUNDE } },
  async ({ body, ip, lokal }) => {
    const email = adresseNormal(body.email);
    const passwort = typeof body.passwort === "string" ? body.passwort : "";
    if (!email || !passwort) return kontoAntwort(400, FALSCH);

    const paar = `${ip}|${adressSchluessel(email)}`;
    if (anfragenImFenster(FEHL, paar) >= 5) return kontoAntwort(400, FALSCH);

    const auth = authClientAnfrage();
    if (!auth) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    const { data, error } = await auth.auth.signInWithPassword({ email, password: passwort });
    if (error || !data.session) {
      if (error?.code === "email_not_confirmed") {
        // Laut Vorversuch (Plan 5.1 Schritt 13) nur bei richtigem Passwort – sonst Abbildung auf FALSCH umstellen
        return kontoAntwort(400, { fehler: MELDUNG.nichtBestaetigt, code: "nicht_bestaetigt" });
      }
      zuVieleAnfragen(FEHL, paar, Number.MAX_SAFE_INTEGER, ZEIT.VIERTELSTUNDE); // Fehlversuch zählen
      return kontoAntwort(400, FALSCH);
    }

    const { setCookies, ziel } = await sitzungStarten(data.session, lokal, body.weiter);
    return kontoAntwort(200, { ok: true, ziel }, setCookies);
  },
);
