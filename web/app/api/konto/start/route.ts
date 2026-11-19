// Startseiten-Insel (Plan Mein Bereich 4.2, 6): „Für dich empfohlen“ und „Deine nächsten Events“ in einem Abruf.
// GET ?datum=…&ohne=id,id → { personalisierung, heute, ersatz, fuer_dich, naechste, vorname? }
// Ohne Einwilligung (a) keine Punkte, kein Ersatz; „naechste“ kommt trotzdem (Merkliste = Vertrag).
import { startFenster, startVorschlaege } from "@/lib/fuer-dich";
import { zeitraumAuflösen } from "@/lib/datum";
import { MELDUNG, NAMEN_ANREDE } from "@/lib/konto/konfig";
import {
  eingabeBauen, gesperrtAbwehr, kontoMerklisteLaden, merklisteTeilen, mitBegruendung, ohneLesen, sensibelMenge,
} from "@/lib/konto/mein-bereich";
import { eventPoolLaden } from "@/lib/daten";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const NAECHSTE_MAX = 4;

export const GET = kontoRoute(
  { anmeldung: true, limit: { name: "start", max: 120, fensterMs: ZEIT.STUNDE } },
  async (ctx) => {
    const gesperrt = gesperrtAbwehr(ctx);
    if (gesperrt) return gesperrt;
    const p = ctx.profil!;
    const url = new URL(ctx.request.url);

    const merkliste = await kontoMerklisteLaden(ctx.db!);
    const pool = await eventPoolLaden();
    const naechste = merkliste ? merklisteTeilen(merkliste, pool.heute).kommend.slice(0, NAECHSTE_MAX) : [];
    const basis = {
      ok: true,
      personalisierung: p.personalisierung,
      // heute: nur für die Datumszeile der Karten (metaZeile), nicht persönlich
      heute: pool.heute,
      naechste,
      ...(NAMEN_ANREDE && p.vorname ? { vorname: p.vorname } : {}),
    };

    if (!p.personalisierung) return kontoAntwort(200, { ...basis, ersatz: false, fuer_dich: [] });

    // Ohne lesbare Merkliste ließen sich gemerkte Events nicht ausschließen → nicht rechnen
    if (!merkliste) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    const sensibel = await sensibelMenge();
    if (!sensibel) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });

    const z = zeitraumAuflösen(url.searchParams.get("datum") ?? undefined, pool.heute);
    const eingabe = await eingabeBauen(ctx, merkliste, sensibel);
    const r = startVorschlaege(eingabe, startFenster(z.von, z.bis, pool.heute), ohneLesen(url.searchParams.get("ohne")));
    if (r.art === "persoenlich") return kontoAntwort(200, { ...basis, ersatz: false, fuer_dich: r.liste.map(mitBegruendung) });
    if (r.art === "ersatz") return kontoAntwort(200, { ...basis, ersatz: true, fuer_dich: r.liste });
    return kontoAntwort(200, { ...basis, ersatz: false, fuer_dich: [] });
  },
);
