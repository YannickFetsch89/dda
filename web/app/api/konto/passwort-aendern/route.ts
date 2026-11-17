// Passwort im Konto ändern (Plan 5.1 Schritt 12): aktuelles Passwort per frischer Anmeldung prüfen, dann setzen,
// andere Sitzungen beenden, frische Sitzung ins Cookie. Je Konto höchstens 5 Fehlversuche in 15 Minuten.
import { anfragenImFenster, zuVieleAnfragen } from "@/lib/formulare";
import { sitzungStarten } from "@/lib/konto/anmeldung";
import { MELDUNG } from "@/lib/konto/konfig";
import { passwortAendern } from "@/lib/konto/passwort";
import { passwortPruefen } from "@/lib/konto/pruefungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const FEHL = "konto-passwort-aendern-fehl";

export const POST = kontoRoute(
  { anmeldung: true, json: true, aendernd: true, ohneMindestalter: true },
  async (ctx) => {
    const s = ctx.sitzung!;
    if (ctx.profil?.unter16_gesperrt_am) return kontoAntwort(403, { fehler: MELDUNG.unter16, code: "unter16_gesperrt" });
    if (anfragenImFenster(FEHL, s.nutzerId) >= 5) return kontoAntwort(429, { fehler: MELDUNG.zuViele, code: "zu_viele" });
    const aktuell = typeof ctx.body.aktuell === "string" ? ctx.body.aktuell : "";
    if (!aktuell) return kontoAntwort(400, { fehler: "Bitte gib dein aktuelles Passwort ein.", code: "aktuell" });
    if (!passwortPruefen(ctx.body.neu)) return kontoAntwort(400, { fehler: MELDUNG.passwortRegel, code: "passwort" });
    if (!s.email) return kontoAntwort(400, { fehler: MELDUNG.ungueltig });

    const ergebnis = await passwortAendern(s.email, aktuell, ctx.body.neu);
    if (!ergebnis.ok) {
      if (ergebnis.grund === "aktuell_falsch") {
        zuVieleAnfragen(FEHL, s.nutzerId, Number.MAX_SAFE_INTEGER, ZEIT.VIERTELSTUNDE);
        return kontoAntwort(403, { fehler: "Das aktuelle Passwort stimmt nicht.", code: "aktuell_falsch" });
      }
      const fehler = ergebnis.grund === "zu_schwach" ? "Bitte wähl ein anderes Passwort." : "Das hat leider nicht geklappt.";
      return kontoAntwort(400, { fehler, code: ergebnis.grund });
    }
    ctx.ohneHinweis = true;
    const { setCookies } = await sitzungStarten(ergebnis.session, ctx.lokal, null);
    ctx.setCookies.push(...setCookies);
    return kontoAntwort(200, { ok: true, meldung: MELDUNG.passwortGeaendert });
  },
);
