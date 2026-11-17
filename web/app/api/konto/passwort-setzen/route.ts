// Neues Passwort nach „Passwort vergessen“ (Plan 5.1 Schritt 10). Erlaubt auch mit der eingeschränkten Reset-Sitzung.
// Danach: andere Sitzungen beendet, normale Sitzung (30 Tage) ohne nur_passwort.
import { sitzungStarten } from "@/lib/konto/anmeldung";
import { MELDUNG } from "@/lib/konto/konfig";
import { passwortSetzen } from "@/lib/konto/passwort";
import { passwortPruefen } from "@/lib/konto/pruefungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

export const POST = kontoRoute(
  {
    anmeldung: true, json: true, aendernd: true, resetErlaubt: true, ohneMindestalter: true,
    limit: { name: "passwort-setzen", max: 10, fensterMs: ZEIT.STUNDE },
  },
  async (ctx) => {
    const s = ctx.sitzung!;
    if (!passwortPruefen(ctx.body.passwort)) return kontoAntwort(400, { fehler: MELDUNG.passwortRegel, code: "passwort" });
    if (!s.refresh) return kontoAntwort(400, { fehler: MELDUNG.ungueltig });

    const ergebnis = await passwortSetzen(s.access, s.refresh, ctx.body.passwort);
    if (!ergebnis.ok) {
      const fehler = ergebnis.grund === "zu_schwach" ? "Bitte wähl ein anderes Passwort." : "Das hat leider nicht geklappt.";
      return kontoAntwort(400, { fehler, code: ergebnis.grund });
    }
    ctx.ohneHinweis = true; // sitzungStarten setzt den Hinweis selbst passend zum Profil
    const { setCookies, ziel } = await sitzungStarten(ergebnis.session, ctx.lokal, ctx.body.weiter);
    ctx.setCookies.push(...setCookies);
    return kontoAntwort(200, { ok: true, meldung: MELDUNG.passwortGeaendert, ziel });
  },
);
