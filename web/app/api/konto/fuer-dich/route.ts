// Seite /konto/fuer-dich (Plan Mein Bereich 3.3, 6): vier Abschnitte, jedes Event nur einmal, kein Ersatz.
// GET → { personalisierung, heute, abschnitte: [{ schluessel, titel, events: [Event + begruendung] }] }
import { fuerDichSeite } from "@/lib/fuer-dich";
import { MELDUNG } from "@/lib/konto/konfig";
import { eingabeBauen, gesperrtAbwehr, kontoMerklisteLaden, mitBegruendung, sensibelMenge } from "@/lib/konto/mein-bereich";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

export const GET = kontoRoute(
  { anmeldung: true, limit: { name: "fuer-dich", max: 60, fensterMs: ZEIT.STUNDE } },
  async (ctx) => {
    const gesperrt = gesperrtAbwehr(ctx);
    if (gesperrt) return gesperrt;
    // Ohne Einwilligung (a): nicht rechnen, Merkliste nicht lesen
    if (!ctx.profil!.personalisierung) return kontoAntwort(200, { ok: true, personalisierung: false, abschnitte: [] });

    const sensibel = await sensibelMenge();
    if (!sensibel) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    const merkliste = await kontoMerklisteLaden(ctx.db!);
    if (!merkliste) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });

    const eingabe = await eingabeBauen(ctx, merkliste, sensibel);
    const r = fuerDichSeite(eingabe);
    const abschnitte = r.art === "abschnitte"
      ? r.abschnitte.map((a) => ({ schluessel: a.schluessel, titel: a.titel, events: a.liste.map(mitBegruendung) }))
      : [];
    // heute: nur für die Datumszeile der Karten (metaZeile), nicht persönlich
    return kontoAntwort(200, { ok: true, personalisierung: true, heute: eingabe.heute, abschnitte });
  },
);
