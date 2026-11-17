// Status der angemeldeten Person (Plan 6): Profil, Schalter, Onboarding. Auch ohne Alters-Häkchen erlaubt.
// Gibt nie rolle, nie eine Kennzeichnung sensibler Events aus.
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

export const GET = kontoRoute(
  { anmeldung: true, ohneMindestalter: true, limit: { name: "ich", max: 120, fensterMs: ZEIT.STUNDE } },
  async ({ sitzung, profil }) => {
    const p = profil!;
    return kontoAntwort(200, {
      ok: true,
      email: sitzung!.email,
      angelegt: p.erstellt_am,
      onboarding_fertig_am: p.onboarding_fertig_am,
      mindestalter_bestaetigt: !!p.mindestalter_bestaetigt_am,
      gesperrt: !!p.unter16_gesperrt_am,
      personalisierung: p.personalisierung,
      sensible_events_erlaubt: p.sensible_events_erlaubt,
      widerspruch_zaehlung: !p.analyse_erlaubt && !!p.onboarding_fertig_am,
      geburtstagsmail: p.geburtstagsmail,
      geburtsdatum: p.unter16_gesperrt_am ? null : p.geburtsdatum,
      vorname: p.vorname,
      nachname: p.nachname,
      praeferenzen: p.praeferenzen ?? {},
      merkliste_begonnen_am: p.merkliste_begonnen_am,
    });
  },
);
