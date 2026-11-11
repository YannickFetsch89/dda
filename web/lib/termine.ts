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

// ---------- Anzeige-Titel (SEO-/GEO-Plan, Maßnahme 9) ----------
// Nur für H1, <title>, JSON-LD und Listen. Der Originaltitel im Datensatz und der Bündelungs-Schlüssel
// (terminSchluessel nutzt basisTitel) bleiben unverändert.

const EMOJI_RAND = /^[\p{Extended_Pictographic}\uFE0F\u200D\s]+|[\p{Extended_Pictographic}\uFE0F\u200D\s]+$/gu;
// „… in Düsseldorf“, „… | Düsseldorf“, „… /// Düsseldorf“ am Ende (nur am Ende – „Düsseldorf – Christmas Walk“ bleibt)
const STADT_ENDE = /(?:\s*[-–—|•·/,:]+\s*|\s+in\s+)D(?:ü|ue)sseldorf\s*[-–—|•·/]*\s*$/i;
// Ein einzelnes Datum am Ende („Morgenandacht 15.11.2026“, „• 14.11.26 Düsseldorf“) – steht ohnehin auf der Seite.
// Mindestens ein Leerzeichen davor, damit Zeiträume wie „13.11.-15.11.2026“ unangetastet bleiben.
const DATUM_ENDE = /\s+(?:[-–—|•·/,]+\s*)?(?:am\s+)?(?:(?:Mo|Di|Mi|Do|Fr|Sa|So)\.?,?\s+)?\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2})?(?:\s+D(?:ü|ue)sseldorf)?\s*$/i;
// Trenner, hinter denen ein Ortsanhang stehen kann („DISCOTECA - The Paradise Now“)
const ORT_TRENNER = /\s+(?:[-–—|@]|\/{2,})\s+/g;
const RAND_TRENNER = /^[\s\-–—|•·/:,]+|[\s\-–—|•·/:,]+$/g;

function ohneOrtsAnhang(titel: string, ort: string): string {
  const o = norm(ort);
  if (o.length < 4) return titel;
  let letzter = -1;
  let laenge = 0;
  for (const m of titel.matchAll(ORT_TRENNER)) {
    letzter = m.index ?? -1;
    laenge = m[0].length;
  }
  if (letzter <= 0) return titel;
  const anhang = norm(titel.slice(letzter + laenge));
  const passt = anhang.length >= 4 && (o.includes(anhang) || anhang.includes(o));
  return passt ? titel.slice(0, letzter) : titel;
}

/**
 * Titel für die Anzeige: ohne angehängte Uhrzeit, ohne „in Düsseldorf“ / „| Düsseldorf“ am Ende, ohne einzelnes
 * Datum am Ende, ohne Ortsanhang („… - Black Box im Filmmuseum Düsseldorf“), ohne Emojis am Rand und ohne
 * doppelte Trenner. Bleibt zu wenig übrig, gilt der Originaltitel.
 */
export function anzeigeTitel(titel: string, ort?: string | null): string {
  let t = basisTitel(titel).replace(EMOJI_RAND, "");
  t = t.replace(DATUM_ENDE, "").replace(STADT_ENDE, "");
  if (ort) t = ohneOrtsAnhang(t, ort).replace(STADT_ENDE, "");
  t = t
    .replace(/(\s[-–—]\s*){2,}/g, " - ") // „NIRVANA - - SUNDAY“
    .replace(/\s{2,}/g, " ")
    .replace(RAND_TRENNER, "")
    .trim();
  return t.length >= 3 ? t : basisTitel(titel);
}

/** Text für Vergleiche vereinheitlichen (Kleinschreibung, ohne Satzzeichen, einfache Leerzeichen). */
export function norm(s: string): string {
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
