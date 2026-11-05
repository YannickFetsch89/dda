// Mehrere Termine desselben Events am selben Tag (gleicher Titel + Ort, verschiedene Uhrzeiten –
// z.B. Führungen um 11 und 14 Uhr oder zwei Vorstellungen) erscheinen in allen Listen nur einmal
// mit „Diverse Uhrzeiten“. Die Detailseite bietet die Uhrzeiten zur Auswahl an; jede Uhrzeit ist
// ein eigenes Event mit eigener Seite und eigenem Ticket-/Quellen-Link.
import type { DddEvent } from "./typen";

// Altdaten: Scraper hängten die Uhrzeit an den Titel („Japanviertel (14:00 Uhr)“)
const ZEIT_IM_TITEL = /\s*[([]\s*\d{1,2}[:.]\d{2}\s*(?:Uhr)?\s*[)\]]\s*$/i;

/** Titel ohne angehängte Uhrzeit. */
export function basisTitel(titel: string): string {
  return titel.replace(ZEIT_IM_TITEL, "").trim() || titel;
}

function norm(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .replace(/\s+/g, " ")
    .trim();
}

/** Gleicher Schlüssel = gleiches Event am gleichen Tag am gleichen Ort. */
export function terminSchluessel(e: Pick<DddEvent, "titel" | "datum" | "ort">): string {
  return `${norm(basisTitel(e.titel))}|${e.datum}|${norm(e.ort)}`;
}

/** Je Uhrzeit ein Termin (bevorzugt nicht abgesagt), sortiert nach Uhrzeit; ohne Uhrzeit zuletzt. */
function proUhrzeit(gruppe: DddEvent[]): DddEvent[] {
  const nachZeit = new Map<string, DddEvent>();
  for (const e of gruppe) {
    const zeit = e.uhrzeit ?? "";
    const bisher = nachZeit.get(zeit);
    if (!bisher || (bisher.abgesagt && !e.abgesagt)) nachZeit.set(zeit, e);
  }
  return [...nachZeit.values()].sort((a, b) => (a.uhrzeit ?? "99").localeCompare(b.uhrzeit ?? "99"));
}

/**
 * Fasst Termine desselben Events am selben Tag zu einem Listeneintrag zusammen.
 * Der Eintrag ist der früheste (nicht abgesagte) Termin mit bereinigtem Titel und `uhrzeiten`;
 * Hervorhebungen (Tipp des Tages usw.) gelten, wenn einer der Termine sie hat.
 */
export function buendeln(events: DddEvent[]): DddEvent[] {
  const gruppen = new Map<string, DddEvent[]>();
  for (const e of events) {
    const k = terminSchluessel(e);
    const g = gruppen.get(k);
    if (g) g.push(e);
    else gruppen.set(k, [e]);
  }
  const ergebnis: DddEvent[] = [];
  for (const gruppe of gruppen.values()) {
    if (gruppe.length === 1) {
      ergebnis.push(gruppe[0]);
      continue;
    }
    const termine = proUhrzeit(gruppe);
    const zeiten = termine.map((e) => e.uhrzeit).filter((z): z is string => !!z);
    const basis = termine.find((e) => !e.abgesagt) ?? termine[0];
    ergebnis.push({
      ...basis,
      titel: basisTitel(basis.titel),
      uhrzeit: zeiten[0] ?? basis.uhrzeit,
      uhrzeiten: zeiten.length > 1 ? zeiten : null,
      abgesagt: termine.every((e) => e.abgesagt),
      tipp_des_tages: gruppe.some((e) => e.tipp_des_tages),
      highlight_der_woche: gruppe.some((e) => e.highlight_der_woche),
      top_event_des_monats: gruppe.some((e) => e.top_event_des_monats),
    });
  }
  // Reihenfolge wie geladen (nach Datum), damit nachfolgende Sortierungen stabil bleiben
  const position = new Map(events.map((e, i) => [e.id, i]));
  return ergebnis.sort((a, b) => (position.get(a.id) ?? 0) - (position.get(b.id) ?? 0));
}

/** Alle Termine (je Uhrzeit einer) zum selben Event am selben Tag – für die Auswahl auf der Detailseite. */
export function termineAmTag(alle: DddEvent[], e: DddEvent): DddEvent[] {
  const k = terminSchluessel(e);
  const termine = proUhrzeit(alle.filter((x) => terminSchluessel(x) === k));
  return termine.filter((x) => x.uhrzeit).length > 1 ? termine : [];
}

/** Uhrzeit für schmale Spalten: „19:30“ oder „div. Zeiten“. */
export function zeitKurz(e: Pick<DddEvent, "uhrzeit" | "uhrzeiten">): string | null {
  return e.uhrzeiten ? "div. Zeiten" : e.uhrzeit;
}

/** Uhrzeit als Text: „19:30 Uhr“ oder „Diverse Uhrzeiten“ (null ohne Uhrzeit). */
export function zeitLang(e: Pick<DddEvent, "uhrzeit" | "uhrzeiten">): string | null {
  if (e.uhrzeiten) return "Diverse Uhrzeiten";
  return e.uhrzeit ? `${e.uhrzeit} Uhr` : null;
}
