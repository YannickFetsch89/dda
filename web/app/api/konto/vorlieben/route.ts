// Interessen im Konto ändern (Plan 5.3, 5.7, 6): { praeferenzen, interessen_ok? }.
// Gilt (a) noch nicht, braucht es interessen_ok: true in derselben Anfrage – dann erst Einwilligung, dann Speichern.
// interessen_ok: false → Widerruf (a), praeferenzen werden geleert und nichts gespeichert.
import { kontoDienstClient } from "@/lib/konto/clients";
import { MELDUNG } from "@/lib/konto/konfig";
import { einwilligungSetzen } from "@/lib/konto/einwilligungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";
import { vorliebenPruefen } from "@/lib/konto/vorlieben";

export const PUT = kontoRoute(
  { anmeldung: true, json: true, aendernd: true, limit: { name: "vorlieben", max: 60, fensterMs: ZEIT.STUNDE } },
  async (ctx) => {
    const p = ctx.profil!;
    const nutzerId = ctx.sitzung!.nutzerId;
    if (p.unter16_gesperrt_am) return kontoAntwort(403, { fehler: MELDUNG.unter16, code: "unter16_gesperrt" });
    const dienst = kontoDienstClient();
    if (!dienst) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });

    if (ctx.body.interessen_ok === false) {
      const r = await einwilligungSetzen(dienst, nutzerId, "personalisierung", false, "interessen_aendern");
      if (!r.ok) return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt." });
      return kontoAntwort(200, { ok: true, personalisierung: false });
    }

    const vorlieben = vorliebenPruefen(ctx.body.praeferenzen);
    if (!vorlieben) return kontoAntwort(400, { fehler: MELDUNG.ungueltig });

    if (!p.personalisierung) {
      if (ctx.body.interessen_ok !== true) {
        return kontoAntwort(409, { fehler: "Bitte willige zuerst ein, dass wir deine Interessen speichern.", code: "einwilligung_fehlt" });
      }
      const r = await einwilligungSetzen(dienst, nutzerId, "personalisierung", true, "interessen_aendern");
      if (!r.ok) return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt." });
    }
    const { error } = await ctx.db!.from("profiles").update({ praeferenzen: vorlieben }).eq("id", nutzerId);
    if (error) return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt.", personalisierung: true });
    return kontoAntwort(200, { ok: true, personalisierung: true, praeferenzen: vorlieben });
  },
);
