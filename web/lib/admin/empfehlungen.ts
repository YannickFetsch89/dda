// Admin-Bereich – Empfehlungen: Tagesvorschau, Kandidaten mit „Warum“, Kalender (Plan Admin-Dashboard 4.5, Stufe 1e).
// Rechnet mit genau denselben Funktionen wie die Startseite (web/lib/startseite.ts) auf demselben Pool.
import "server-only";
import { amFokustag, filtern, highlightGilt, highlights, istMehrtaegig, nachEmpfehlung, startPlaetze, stufeErklaeren, tippGilt, topGilt, type StufenKontext } from "../ableitungen";
import { eventPoolLaden, vergangeneWochenendEvents } from "../daten";
import { plusTage } from "../datum";
import { kategorieAusDb } from "../kategorien";
import { eventPfad } from "../pfade";
import { startseitenAuswahl } from "../startseite";
import type { DddEvent } from "../typen";

export interface EventKurz {
  id: string;
  titel: string;
  ort: string;
  datum: string;
  datum_bis: string | null;
  uhrzeit: string | null;
  kategorie: string;
  bild: boolean;
  pfad: string;
  stufe: number | null;
  gruende: string[];
  flaggen: { tipp: boolean; tippGilt: boolean; highlight: boolean; top: boolean; nichtEmpfehlen: boolean };
  /** Mehrtägig und der gezeigte Tag ist nicht sein Fokustag (zählt dann weniger) */
  ausserhalbFokus: boolean;
}

export interface KalenderTag {
  tag: string;
  tipp: { id: string; titel: string; bild: boolean } | null;
  redaktion: boolean;
}

export interface EmpfehlungsDaten {
  heute: string;
  tag: string;
  bisTag: string;
  quelle: "supabase" | "beispiel";
  tipp: EventKurz | null;
  vonRedaktion: boolean;
  picks: EventKurz[];
  beliebt: EventKurz[];
  wochenende: { name: string; tag: string; vergangen: boolean; events: EventKurz[] }[];
  highlight: EventKurz | null;
  top: EventKurz | null;
  kandidaten: EventKurz[];
  kalender: KalenderTag[];
}

const TAGE_VORAUS = 59; // Pool reicht 60 Tage ab heute (daten.ts, TAGE_VORAUS)

function kurz(e: DddEvent, k: StufenKontext, tag: string | null): EventKurz {
  const erklaerung = stufeErklaeren(e, k);
  return {
    id: e.id,
    titel: e.titel,
    ort: e.ort,
    datum: e.datum,
    datum_bis: e.datum_bis,
    uhrzeit: e.uhrzeit,
    kategorie: e.kategorie,
    bild: !!e.bild_url,
    pfad: eventPfad({ id: e.id, slug: e.slug, kategorie: kategorieAusDb(e.kategorie) }),
    stufe: erklaerung.stufe,
    gruende: erklaerung.gruende,
    flaggen: {
      tipp: e.tipp_des_tages,
      tippGilt: tippGilt(e, tag),
      highlight: highlightGilt(e, k.heute),
      top: topGilt(e, k.heute),
      nichtEmpfehlen: !!e.nicht_empfehlen,
    },
    ausserhalbFokus: !!tag && istMehrtaegig(e) && !amFokustag(e, tag),
  };
}

/** `tagWunsch`: YYYY-MM-DD; wird auf heute … heute + 59 begrenzt (so weit reicht der Pool der Startseite). */
export async function empfehlungenLaden(tagWunsch: string | null): Promise<EmpfehlungsDaten> {
  const geladen = await eventPoolLaden();
  const heute = geladen.heute;
  const bisTag = plusTage(heute, TAGE_VORAUS);
  const tag = tagWunsch && /^\d{4}-\d{2}-\d{2}$/.test(tagWunsch) && tagWunsch >= heute && tagWunsch <= bisTag ? tagWunsch : heute;

  const a = startseitenAuswahl(geladen, await vergangeneWochenendEvents(heute), tag);
  const k = a.stufen;
  const h = highlights(a.pool);

  // Kandidaten des Tages: alles, was an dem Tag stattfindet, nach dem Sortierschlüssel der Startseite
  const kandidaten = filtern(a.pool.events, { von: tag, bis: tag, mitLanglaeufern: true })
    .sort(nachEmpfehlung(k, tag))
    .slice(0, 80)
    .map((e) => kurz(e, k, tag));

  // Kalender: je Tag der Tipp, den die Startseite zeigen würde
  const kalender: KalenderTag[] = Array.from({ length: 30 }, (_, i) => {
    const t = plusTage(heute, i);
    const { tipp } = startPlaetze(filtern(a.pool.events, { von: t, bis: t, mitLanglaeufern: true }), k, t);
    return { tag: t, tipp: tipp ? { id: tipp.id, titel: tipp.titel, bild: !!tipp.bild_url } : null, redaktion: !!tipp && tippGilt(tipp, t) };
  });

  return {
    heute,
    tag,
    bisTag,
    quelle: geladen.quelle,
    tipp: a.tipp ? kurz(a.tipp, k, tag) : null,
    vonRedaktion: a.vonRedaktion,
    picks: a.picks.map((e) => kurz(e, k, tag)),
    beliebt: a.beliebt.map((e) => kurz(e, k, tag)),
    wochenende: a.wochenende.map((w) => ({ name: w.name, tag: w.tag, vergangen: w.vergangen, events: w.events.map((e) => kurz(e, k, w.tag)) })),
    highlight: h.highlight ? kurz(h.highlight, k, null) : null,
    top: h.top ? kurz(h.top, k, null) : null,
    kandidaten,
    kalender,
  };
}

/** Flaggen, die die Empfehlungs-Seite setzen darf, mit den Spalten, die sie ändern (wie flagge_setzen im alten Dashboard) */
export const FLAGGEN = ["tipp", "highlight", "top", "nicht_empfehlen"] as const;
export type Flagge = (typeof FLAGGEN)[number];

export function flaggenUpdate(flagge: Flagge, wert: boolean, jetzt = new Date()): Record<string, unknown> {
  const zeit = wert ? jetzt.toISOString() : null;
  switch (flagge) {
    case "tipp":
      return { tipp_des_tages: wert };
    case "highlight":
      return { highlight_der_woche: wert, highlight_gesetzt_am: zeit };
    case "top":
      return { top_event_des_monats: wert, top_gesetzt_am: zeit };
    case "nicht_empfehlen":
      return { nicht_empfehlen: wert };
  }
}

