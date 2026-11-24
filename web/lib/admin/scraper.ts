// Admin-Bereich – Daten der Scraper-Seite (Plan Admin-Dashboard 4.3, Stufe 1c): Läufe, Quellen mit Verlauf, Warnungen.
import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { letzterLauf, type GithubErgebnis } from "./github";
import { warnungenBerechnen, type ErgebnisZeile, type LaufZeile, type Warnung } from "./warnregeln";

export interface LaufAnzeige extends LaufZeile {
  ausloeser: string | null;
  github_run_url: string | null;
  events_gesammelt: number | null;
  neu_gespeichert: number | null;
  duplikate: number | null;
  fehlermeldung: string | null;
  /** Quellen-Kennzahlen (Plan Quellen-Ausbau 4.3, database/quellen_spalte_2026-11-24.sql) */
  kuenftige_events: number | null;
  nur_rausgegangen: number | null;
}

export interface QuelleAnzeige {
  quelle: string;
  /** Neueste zuerst, höchstens 10 beendete Läufe; null = in diesem Lauf nicht dabei */
  verlauf: ({ status: ErgebnisZeile["status"]; anzahl: number } | null)[];
  letzterErfolg: string | null;
  letzteMeldung: string | null;
  warnungen: Warnung[];
}

export interface ScraperDaten {
  jetzt: string;
  laeufe: LaufAnzeige[];
  quellen: QuelleAnzeige[];
  laufWarnungen: Warnung[];
  github: GithubErgebnis;
}

const LAEUFE = 20;
const VERLAUF = 10;

export async function scraperDatenLaden(db: SupabaseClient): Promise<ScraperDaten> {
  const jetzt = new Date();
  const basis = "id, gestartet_am, beendet_am, status, speicher_fehler, ausloeser, github_run_url, events_gesammelt, neu_gespeichert, duplikate, fehlermeldung";
  const abfrage = (spalten: string) =>
    db.from("scraper_laeufe").select(spalten).order("gestartet_am", { ascending: false }).limit(LAEUFE);
  let { data: laeufe, error } = await abfrage(`${basis}, kuenftige_events, nur_rausgegangen, luecken`);
  // Fehlen die Kennzahl-Spalten (SQL quellen_spalte_2026-11-24 noch nicht ausgeführt), Seite ohne sie zeigen
  if (error && /does not exist|42703|PGRST204/.test(`${error.code ?? ""} ${error.message}`)) {
    ({ data: laeufe, error } = await abfrage(basis));
  }
  if (error) throw new Error(error.message);
  const alle = (laeufe ?? []) as unknown as LaufAnzeige[];
  const beendet = alle.filter((l) => l.status !== "laeuft").slice(0, VERLAUF);
  const ids = beendet.map((l) => l.id);

  let ergebnisse: ErgebnisZeile[] = [];
  if (ids.length) {
    const { data, error: f2 } = await db.from("scraper_ergebnisse").select("lauf_id, quelle, status, anzahl, meldung").in("lauf_id", ids).limit(4000);
    if (f2) throw new Error(f2.message);
    ergebnisse = (data ?? []) as ErgebnisZeile[];
  }

  const warnungen = warnungenBerechnen(alle, ergebnisse, jetzt);
  const position = new Map(beendet.map((l, i) => [l.id, i]));
  const jeQuelle = new Map<string, ErgebnisZeile[]>();
  for (const e of ergebnisse) jeQuelle.set(e.quelle, [...(jeQuelle.get(e.quelle) ?? []), e]);

  const quellen: QuelleAnzeige[] = [...jeQuelle].map(([quelle, liste]) => {
    const verlauf: QuelleAnzeige["verlauf"] = beendet.map(() => null);
    for (const e of liste) verlauf[position.get(e.lauf_id)!] = { status: e.status, anzahl: e.anzahl };
    const sortiert = [...liste].sort((a, b) => position.get(a.lauf_id)! - position.get(b.lauf_id)!);
    const erfolg = sortiert.find((e) => e.status === "ok");
    const meldung = sortiert.find((e) => e.meldung);
    return {
      quelle,
      verlauf,
      letzterErfolg: erfolg ? beendet[position.get(erfolg.lauf_id)!].gestartet_am : null,
      letzteMeldung: meldung?.meldung ?? null,
      warnungen: warnungen.filter((w) => w.quelle === quelle),
    };
  });
  // Quellen mit Warnungen zuerst (rot vor gelb), dann alphabetisch
  const gewicht = (q: QuelleAnzeige) => (q.warnungen.some((w) => w.stufe === "rot") ? 0 : q.warnungen.length ? 1 : 2);
  quellen.sort((a, b) => gewicht(a) - gewicht(b) || a.quelle.localeCompare(b.quelle, "de"));

  return {
    jetzt: jetzt.toISOString(),
    laeufe: alle,
    quellen,
    laufWarnungen: warnungen.filter((w) => w.quelle === null),
    github: await letzterLauf("scrape"),
  };
}
