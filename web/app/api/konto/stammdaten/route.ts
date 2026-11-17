// Name und Geburtsdatum im Konto ändern (Plan 5.7, E16): { vorname, nachname, geburtsdatum }, alle Pflicht.
// Gleiche Altersprüfung wie beim Abschluss: Ein Datum unter 16 sperrt das Konto (Löschung beim nächsten Job-Lauf).
import { hinweisCookie } from "@/lib/konto/cookies";
import { kontoDienstClient } from "@/lib/konto/clients";
import { MELDUNG } from "@/lib/konto/konfig";
import { stammdatenSetzen } from "@/lib/konto/einwilligungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";
import { stammdatenAusBody } from "@/lib/konto/stammdaten";

export const PUT = kontoRoute(
  { anmeldung: true, json: true, aendernd: true, limit: { name: "stammdaten", max: 20, fensterMs: ZEIT.STUNDE } },
  async (ctx) => {
    const p = ctx.profil!;
    const stamm = stammdatenAusBody(ctx.body);
    if (stamm.fehler) return stamm.fehler;
    const s = stamm.daten;
    if (p.vorname === s.vorname && p.nachname === s.nachname && p.geburtsdatum === s.geburtsdatum) {
      return kontoAntwort(200, { ok: true });
    }
    const dienst = kontoDienstClient();
    if (!dienst) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });

    const r = await stammdatenSetzen(dienst, ctx.sitzung!.nutzerId, s);
    if (!r.ok) {
      if (r.code === "unter16_gesperrt") return kontoAntwort(403, { fehler: MELDUNG.unter16, code: r.code });
      return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt." });
    }
    if (r.ergebnis === "unter_16") {
      ctx.ohneHinweis = true;
      ctx.setCookies.push(hinweisCookie("0", ctx.lokal));
      return kontoAntwort(200, { ok: false, gesperrt: true, meldung: MELDUNG.unter16 });
    }
    return kontoAntwort(200, { ok: true });
  },
);
