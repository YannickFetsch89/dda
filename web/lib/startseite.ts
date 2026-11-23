// Auswahl der Startseite: Tipp, Picks, „Beliebt“ und Wochenend-Tipps (Plan docs/plan-empfehlungen-2026-11-13.md,
// Abschnitt 9). Aus web/app/page.tsx herausgezogen, damit Startseite und Admin-Tagesvorschau
// (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.5) dieselbe Rechnung nutzen.
// Rechnet nur, lädt nichts und hat kein "use cache": Das Laden (eventPoolLaden, vergangeneWochenendEvents) bleibt beim
// Aufrufer, das Caching der Startseite ändert sich nicht.
import { beliebtAuswahl, filtern, startPlaetze, stufenKontext, tippGilt, wochenendProgramm, type StufenKontext } from "./ableitungen";
import { plusTage, zeitraumAuflösen } from "./datum";
import type { DddEvent, EventPool } from "./typen";

export interface StartseitenAuswahl {
  /** Pool ohne abgesagte Events (wie auf der Startseite) */
  pool: EventPool;
  z: ReturnType<typeof zeitraumAuflösen>;
  /** Gewählter Tag in der Tagesansicht, null im Zeitraum */
  fokusTag: string | null;
  stufen: StufenKontext;
  imZeitraum: DddEvent[];
  woche: DddEvent[];
  tipp: DddEvent | null;
  picks: DddEvent[];
  /** Der gezeigte Tipp trägt die Tipp-Flagge, und sie gilt an diesem Tag („Von der Redaktion“) */
  vonRedaktion: boolean;
  beliebt: DddEvent[];
  /** Hängt an pool.heute, nicht am gewählten Tag */
  wochenende: ReturnType<typeof wochenendProgramm>;
}

/**
 * `geladen`: Pool aus eventPoolLaden (gebündelt, ohne abgelehnte). `vergangene`: vergangeneWochenendEvents(geladen.heute).
 * `datumParam`: der Parameter ?datum= der Startseite (Tag, Zeitraum oder leer).
 */
export function startseitenAuswahl(geladen: EventPool, vergangene: DddEvent[], datumParam: string | undefined): StartseitenAuswahl {
  // Abgesagte Events erscheinen nicht auf der Startseite (in Kalender/Entdecken bleiben sie markiert sichtbar)
  const pool = { ...geladen, events: geladen.events.filter((e) => !e.abgesagt) };
  const z = zeitraumAuflösen(datumParam, pool.heute);
  const imZeitraum = filtern(pool.events, { von: z.von, bis: z.bis });
  const woche = filtern(pool.events, { von: z.von, bis: plusTage(z.von, 6) });

  // Tipp + Picks: fünf Plätze nach Stufe und Sortierschlüssel. Kandidaten mit Langläufern; in der Tagesansicht gilt
  // der Fokustag, im Zeitraum nicht.
  const fokusTag = z.von === z.bis ? z.von : null;
  const stufen = stufenKontext(pool.events, pool.heute);
  const { tipp, picks } = startPlaetze(filtern(pool.events, { von: z.von, bis: z.bis, mitLanglaeufern: true }), stufen, fokusTag);
  const vonRedaktion = !!tipp && tippGilt(tipp, fokusTag);
  // „Beliebt“: Stamm draußen, mehrtägige Events in der Tagesansicht nur am Fokustag; ohne die Events aus Tipp und Picks
  const schonGezeigt = new Set([tipp, ...picks].filter((e): e is DddEvent => !!e).map((e) => e.id));
  const beliebt = beliebtAuswahl(imZeitraum, woche, stufen, fokusTag, 5, schonGezeigt);
  // Bis einschließlich Sonntag auch die schon vergangenen Tage des Wochenendes (Fr/Sa)
  const wochenende = wochenendProgramm(pool, vergangene);

  return { pool, z, fokusTag, stufen, imZeitraum, woche, tipp, picks, vonRedaktion, beliebt, wochenende };
}
