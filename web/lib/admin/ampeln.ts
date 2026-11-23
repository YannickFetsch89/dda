// Admin-Bereich – Ampeln und „Zu erledigen“ fürs Cockpit (Plan Admin-Dashboard 4.2). Reine Funktionen, getestet in
// web/tests/admin-cockpit.test.ts. Die Daten holt web/lib/admin/cockpit.ts.
import { filtern, tippGilt } from "../ableitungen";
import { plusTage } from "../datum";
import type { DddEvent } from "../typen";
import type { GithubErgebnis } from "./github";
import type { LaufZeile, Warnung } from "./warnregeln";

export type Farbe = "gruen" | "gelb" | "rot" | "grau";

export interface Ampel {
  schluessel: string;
  titel: string;
  farbe: Farbe;
  text: string;
  zeitpunkt: string | null;
  link: string | null;
}

const STUNDE_MS = 60 * 60 * 1000;

function alterStunden(iso: string, jetzt: Date): number {
  return (jetzt.getTime() - new Date(iso).getTime()) / STUNDE_MS;
}

/** Scraper-Ampel aus dem neuesten Lauf und den Warnungen W1–W6 */
export function scraperAmpel(laeufe: LaufZeile[], warnungen: Warnung[], jetzt: Date, laufUrl: string | null): Ampel {
  const neuester = [...laeufe].sort((a, b) => b.gestartet_am.localeCompare(a.gestartet_am))[0];
  const basis = { schluessel: "scraper", titel: "Scraper-Lauf", link: laufUrl };
  if (!neuester) return { ...basis, farbe: "rot", text: "Noch kein Lauf protokolliert.", zeitpunkt: null };
  const rot = warnungen.filter((w) => w.stufe === "rot").length;
  const gelb = warnungen.filter((w) => w.stufe === "gelb").length;
  const alter = alterStunden(neuester.gestartet_am, jetzt);
  let farbe: Farbe = "gruen";
  if (neuester.status === "fehler" || rot > 0 || alter > 7 * 24) farbe = "rot";
  else if (gelb > 0 || alter > 4 * 24) farbe = "gelb";
  const status = { laeuft: "läuft gerade", erfolgreich: "erfolgreich", fehler: "abgebrochen" }[neuester.status];
  const zusatz = rot + gelb > 0 ? ` · ${rot + gelb} Warnung${rot + gelb === 1 ? "" : "en"}` : "";
  return { ...basis, farbe, text: `Letzter Lauf ${status}${zusatz}`, zeitpunkt: neuester.gestartet_am };
}

/**
 * Ampel für einen GitHub-Workflow. `maxStunden`: Ab welchem Alter des letzten Laufs gelb (Wächter alle 15 min,
 * Geburtstag täglich, Magazin stündlich). null = kein Altersgrenzwert (Deploy).
 */
export function workflowAmpel(schluessel: string, titel: string, g: GithubErgebnis, jetzt: Date, maxStunden: number | null): Ampel {
  const basis = { schluessel, titel };
  if (g.art === "kein_token") return { ...basis, farbe: "grau", text: "GitHub nicht verbunden (Token fehlt).", zeitpunkt: null, link: null };
  if (g.art === "fehler") return { ...basis, farbe: "grau", text: `GitHub nicht erreichbar: ${g.meldung}`, zeitpunkt: null, link: null };
  if (!g.lauf) return { ...basis, farbe: "grau", text: "Noch kein Lauf.", zeitpunkt: null, link: null };
  const l = g.lauf;
  let farbe: Farbe = "gruen";
  let text = "erfolgreich";
  if (l.status !== "completed") text = "läuft gerade";
  else if (l.conclusion === "failure" || l.conclusion === "timed_out") {
    farbe = "rot";
    text = "fehlgeschlagen";
  } else if (l.conclusion !== "success" && l.conclusion !== "skipped") {
    farbe = "gelb";
    text = l.conclusion ?? "unbekannt";
  } else if (l.conclusion === "skipped") text = "übersprungen (Schalter aus)";
  if (farbe === "gruen" && maxStunden !== null && alterStunden(l.erstellt_am, jetzt) > maxStunden) {
    farbe = "gelb";
    text = `${text}, aber seit über ${maxStunden} Stunde${maxStunden === 1 ? "" : "n"} kein Lauf`;
  }
  return { ...basis, farbe, text: `Letzter Lauf ${text}`, zeitpunkt: l.erstellt_am, link: l.url };
}

/** Ablauf des GitHub-Tokens: gelb ab 30 Tagen vorher, rot ab 7 Tagen */
export function tokenAmpel(ablauf: string | null, jetzt: Date): Ampel | null {
  if (!ablauf) return null;
  const tage = (new Date(ablauf).getTime() - jetzt.getTime()) / (24 * STUNDE_MS);
  if (!Number.isFinite(tage) || tage > 30) return null;
  return {
    schluessel: "github_token",
    titel: "GitHub-Token",
    farbe: tage <= 7 ? "rot" : "gelb",
    text: tage <= 0 ? "Token ist abgelaufen." : `Token läuft in ${Math.ceil(tage)} Tagen ab.`,
    zeitpunkt: ablauf,
    link: "https://github.com/settings/personal-access-tokens",
  };
}

export interface EventLuecken {
  /** Kommende Tage (heute + 13) ohne Tipp mit Redaktions-Flagge */
  tageOhneTipp: string[];
  /** Nächste 7 Tage: Events ohne Bild / Stadtteil / Adresse */
  ohneBild: number;
  ohneStadtteil: number;
  ohneAdresse: number;
  eventsHeute: number;
  events7Tage: number;
}

/** Lücken und Kennzahlen aus dem Event-Pool der Startseite (gebündelt, ohne abgelehnte) */
export function eventLuecken(events: DddEvent[], heute: string): EventLuecken {
  const aktiv = events.filter((e) => !e.abgesagt);
  const tageOhneTipp: string[] = [];
  for (let i = 0; i < 14; i++) {
    const tag = plusTage(heute, i);
    const kandidaten = filtern(aktiv, { von: tag, bis: tag, mitLanglaeufern: true });
    if (!kandidaten.some((e) => tippGilt(e, tag))) tageOhneTipp.push(tag);
  }
  const woche = filtern(aktiv, { von: heute, bis: plusTage(heute, 6) });
  return {
    tageOhneTipp,
    ohneBild: woche.filter((e) => !e.bild_url).length,
    ohneStadtteil: woche.filter((e) => !e.stadtteil).length,
    ohneAdresse: woche.filter((e) => !e.adresse).length,
    eventsHeute: filtern(aktiv, { von: heute, bis: heute }).length,
    events7Tage: woche.length,
  };
}
