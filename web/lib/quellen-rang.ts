// Rangfolge der Quellen (Plan docs/plan-quellen-ausbau-2026-11-23.md, 4.1, Schritt R1) – TypeScript-Gegenstück zu
// pipeline/quellen_rang.py für gespeicherte Zeilen (Admin-Bereich). Kleiner Rang = bessere Quelle:
// 1 Haus · 2 Ticketverkauf · 3 Portale · 4 Aggregatoren · 5 Rausgegangen. Beide prüfen gegen tests/fixtures/quellen_rang.json.

/** Gespeicherter quelle_name → Rang (wie RANG_GESPEICHERT in pipeline/quellen_rang.py) */
export const RANG_GESPEICHERT: Readonly<Record<string, number>> = {
  "Ticketmaster": 2,
  "Kulturportal Düsseldorf": 3,
  "VisitDüsseldorf": 3,
  "VisitDüsseldorf Führungen": 3,
  "Meetup.com": 3,
  "Resident Advisor": 3,
  "PRINZ.de Düsseldorf": 4,
  "Songkick": 4,
  "AllEvents.in Düsseldorf": 4,
  "Rausgegangen": 5,
  "Tonhalle Düsseldorf": 1,
  "zakk": 1,
  "Deutsche Oper am Rhein": 1,
  "Düsseldorfer Schauspielhaus": 1,
  "d-live": 1,
  "Kunstpalast Düsseldorf": 1,
  "Kunstsammlung NRW (K20/K21)": 1,
  "NRW-Forum Düsseldorf": 1,
  "FFT Düsseldorf": 1,
  "Stahlwerk Düsseldorf": 1,
  "Rudas Studios Düsseldorf": 1,
  "Mitsubishi Electric HALLE": 1,
  "Kulturschlachthof R25": 1,
  "Salon des Amateurs": 1,
  "Pitcher Rock HQ": 1,
  "Kunsthalle Düsseldorf": 1,
  "Filmmuseum Düsseldorf": 1,
  "Stadtbüchereien Düsseldorf": 1,
  "Tanzhaus NRW": 1,
  "Jazz-Schmiede Düsseldorf": 1,
  "Capitol Theater Düsseldorf": 1,
  "Kom(m)ödchen Düsseldorf": 1,
  "STARTPLATZ Düsseldorf": 1,
  "Parkrun Volksgarten Düsseldorf": 1,
  "Sport im Park Düsseldorf": 1,
  "Fortuna Düsseldorf": 1,
  "DEG Eishockey Düsseldorf": 1,
  "Messe Düsseldorf": 1,
  "EKŌ-Haus der Japanischen Kultur": 1,
  "Classic Remise Düsseldorf": 1,
  "Stadtstrand Düsseldorf": 1,
  "IHK Düsseldorf": 1,
  "StartupDorf Meetup": 1,
  "Street Food Thursday": 1,
  "Kasematten Düsseldorf": 1,
  "Auf ins Viertel": 1,
  "Kleine Weihnachtsmärkte": 1,
  "Classic Remise": 1,
  "Street Food Thursday Düsseldorf": 1,
  "Kleine Weihnachtsmärkte (Redaktion)": 1,
  "Event-Meldung": 1,
  "Eventbrite": 4,
  "eventfinder.de": 4,
  "meinestadt.de": 4,
  "Bandsintown": 4,
  "Spontacts Düsseldorf": 4,
};

/** Unbekannter gespeicherter Name (z. B. CSV-Namen der kleinen Weihnachtsmärkte): neutral zwischen Haus und Aggregator */
export const UNBEKANNT_GESPEICHERT = 3;
export const HAUS = 1;
export const RAUSGEGANGEN = 5;

const text = (wert: unknown) => (typeof wert === "string" ? wert : "");

/** Rang einer gespeicherten Zeile; Rausgegangen auch an der URL. Andere Domains in quelle_url zählen nicht. */
export function rangGespeichert(e: { quelle_name?: unknown; quelle_url?: unknown }): number {
  const name = text(e.quelle_name).trim();
  if (name.toLowerCase().includes("rausgegangen") || text(e.quelle_url).toLowerCase().includes("rausgegangen.de")) return RAUSGEGANGEN;
  return RANG_GESPEICHERT[name] ?? UNBEKANNT_GESPEICHERT;
}

/** Gibt die Quelle Termine nur weiter (Rang ≥ 2)? Dort ist die Uhrzeit oft der Einlass. */
export function istSammelquelle(e: { quelle_name?: unknown; quelle_url?: unknown }): boolean {
  return rangGespeichert(e) > HAUS;
}
