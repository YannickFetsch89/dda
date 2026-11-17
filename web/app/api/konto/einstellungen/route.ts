// Einzelner Schalter (Plan 5.3, 5.7, 6): { art, erteilt }.
//   mindestalter     – nur erteilt: true (Häkchen auf /konto/willkommen), abgelehnt bei gesperrtem Konto
//   personalisierung – Widerruf leert praeferenzen
//   sensible_events  – Widerruf: Antwort zurueck_aufs_geraet (IDs, die das Gerät lokal behält, Plan 5.8)
//   analyse          – erteilt = mitzählen; 409 solange onboarding_fertig_am leer (Hinweis Art. 21 kommt zuerst, E4)
//   geburtstagsmail  – nur der Schalter; erteilt braucht ein gespeichertes Geburtsdatum (E16, Pflichtangabe),
//                      der Widerruf lässt das Datum stehen. Name und Datum ändert /api/konto/stammdaten.
// Auch ohne Alters-Häkchen erreichbar, dann aber nur für „mindestalter“.
import { kontoDienstClient } from "@/lib/konto/clients";
import { MELDUNG, TEXTVERSIONEN, type EinwilligungArt } from "@/lib/konto/konfig";
import { einwilligungSetzen } from "@/lib/konto/einwilligungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const ARTEN = new Set(Object.keys(TEXTVERSIONEN).filter((a) => a !== "nutzungsbedingungen"));

export const PUT = kontoRoute(
  {
    anmeldung: true, json: true, aendernd: true, ohneMindestalter: true,
    limit: { name: "einstellungen", max: 60, fensterMs: ZEIT.STUNDE },
  },
  async (ctx) => {
    const p = ctx.profil!;
    const nutzerId = ctx.sitzung!.nutzerId;
    const art = ctx.body.art;
    const erteilt = ctx.body.erteilt;
    if (typeof art !== "string" || !ARTEN.has(art) || typeof erteilt !== "boolean") {
      return kontoAntwort(400, { fehler: MELDUNG.ungueltig });
    }
    if (p.unter16_gesperrt_am) return kontoAntwort(403, { fehler: MELDUNG.unter16, code: "unter16_gesperrt" });
    if (art !== "mindestalter" && !p.mindestalter_bestaetigt_am) {
      return kontoAntwort(403, { fehler: "Bitte bestätige zuerst dein Alter.", code: "mindestalter_fehlt" });
    }
    if (art === "mindestalter" && !erteilt) return kontoAntwort(400, { fehler: MELDUNG.ungueltig });
    if (art === "analyse" && !p.onboarding_fertig_am) {
      return kontoAntwort(409, { fehler: "Bitte schließ zuerst dein Profil ab.", code: "onboarding_fehlt" });
    }
    const dienst = kontoDienstClient();
    if (!dienst) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });

    const handlung = art === "mindestalter" ? "abschlussseite" : "konto_schalter";
    const r = await einwilligungSetzen(dienst, nutzerId, art as EinwilligungArt, erteilt, handlung);
    if (!r.ok) {
      if (r.code === "unter16_gesperrt") return kontoAntwort(403, { fehler: MELDUNG.unter16, code: r.code });
      if (r.code === "geburtsdatum_fehlt") {
        return kontoAntwort(400, { fehler: "Bitte trag zuerst dein Geburtsdatum ein.", code: "geburtsdatum" });
      }
      return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt." });
    }
    if (art === "mindestalter") {
      // Hinweis-Cookie springt auf „1“: ab jetzt Kontomodus, die Übernahme startet (Plan 5.3)
      ctx.profil = { ...p, mindestalter_bestaetigt_am: new Date().toISOString() };
    }
    if (art === "sensible_events" && !erteilt) return kontoAntwort(200, { ok: true, zurueck_aufs_geraet: r.zurueck });
    return kontoAntwort(200, { ok: true });
  },
);
