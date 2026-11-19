// Zahlen für die Übersicht /konto (Plan Mein Bereich 3.1, 6).
// GET → { vorschlaege: number|null, vorschlaege_unbekannt?, kommende, erlebt, interessen }
// Fehlt nur die Sensibel-Menge, bleibt die Antwort 200 (vorschlaege null, vorschlaege_unbekannt true).
import { anzahlVorschlaege } from "@/lib/fuer-dich";
import { MELDUNG } from "@/lib/konto/konfig";
import { eingabeBauen, gesperrtAbwehr, kontoMerklisteLaden, merklisteTeilen, sensibelMenge } from "@/lib/konto/mein-bereich";
import { eventPoolLaden } from "@/lib/daten";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const LISTEN = ["kategorien", "unterkategorien", "stadtteile", "merkmale", "orte"] as const;

export const GET = kontoRoute(
  { anmeldung: true, limit: { name: "uebersicht", max: 120, fensterMs: ZEIT.STUNDE } },
  async (ctx) => {
    const gesperrt = gesperrtAbwehr(ctx);
    if (gesperrt) return gesperrt;
    const p = ctx.profil!;
    const merkliste = await kontoMerklisteLaden(ctx.db!);
    if (!merkliste) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    const pool = await eventPoolLaden();
    const { kommend, vorbei } = merklisteTeilen(merkliste, pool.heute);

    const praeferenzen = (p.praeferenzen ?? {}) as Record<string, unknown>;
    const interessen = LISTEN.reduce((n, k) => n + (Array.isArray(praeferenzen[k]) ? (praeferenzen[k] as unknown[]).length : 0), 0);

    let vorschlaege: number | null = null;
    let unbekannt = false;
    if (p.personalisierung) {
      const sensibel = await sensibelMenge();
      if (sensibel) vorschlaege = anzahlVorschlaege(await eingabeBauen(ctx, merkliste, sensibel));
      else unbekannt = true;
    }
    return kontoAntwort(200, {
      ok: true,
      vorschlaege,
      ...(unbekannt ? { vorschlaege_unbekannt: true } : {}),
      kommende: kommend.length,
      erlebt: vorbei.length,
      interessen,
      merkliste_unvollstaendig: merkliste.eventsFehler || undefined,
    });
  },
);
