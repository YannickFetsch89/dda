// Admin-Bereich – Prüfung eines Magazin-Entwurfs nach der Bearbeitung (Plan Admin-Dashboard 4.6, Stufe 2).
// Dieselben festen Regeln wie pipeline/magazin.py, pruefen() (a)–(i), aber auf dem fertigen Markdown statt auf den
// Abschnitten des KI-Entwurfs. (g) prüft nur der Lauf vor dem Modellaufruf; sie entfällt hier.
// Ergebnis grün → Status in_pruefung (veröffentlichbar), rot → entwurf – wie in der Pipeline.
import { heroErlaubt } from "../magazin-bilder";

export interface PruefEingabe {
  rubrik: string;
  titel: string;
  teaser: string | null;
  kurzfassung: string[] | null;
  faq: { frage?: unknown; antwort?: unknown }[] | null;
  inhalt_md: string;
  hero_bild: string | null;
  hero_alt: string | null;
  gueltig_von: string | null;
  gueltig_bis: string | null;
}

export interface PruefErgebnis {
  ergebnis: "gruen" | "rot";
  punkte: string[];
}

const MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];
// Muster wie pipeline/magazin.py (Zeilen 217–230)
const UHRZEIT = /\b([01]?\d|2[0-3])[:.]([0-5]\d)\b(?!\.)|\bUhr\b/;
const PREIS = /€|\bEuro\b|\bEUR\b|\bkostenlos\b|\beintritt frei\b/i;
const AUSVERKAUFT = /ausverkauft|restlos/i;
const DATUM_MONAT = new RegExp(String.raw`\b(\d{1,2})\.\s*(${MONATE.join("|")})(?![\p{L}])`, "gu");
const DATUM_ZAHL = /\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})?/g;
const CLICKBAIT = /unglaublich|du wirst nicht glauben|ihr werdet nicht glauben|geheimtipp,? den keiner kennt|schockierend|der wahnsinn|muss man gesehen haben/i;
const ICH_FORM = /\b(ich|mich|mir|mein|meine|meinen|meinem|meiner|meines)\b/i;
const GOOGLE = /google|sterne-bewertung|\bbewertet mit\b|\d[,.]\d\s*sterne/i;
const HUB_KOEPFE = ["Weihnachtsmärkte in Düsseldorf", "Clubs in Düsseldorf", "Restaurants & Cafés", "Kneipen & Bars", "Spielplätze in Düsseldorf"];
const LINK = /\[([^\]]+)\]\(([^)\s]*)\)/g;
const INTERNE_PRAEFIXE = ["/heute", "/morgen", "/wochenende", "/entdecken", "/guides", "/kategorie/", "/stadtteil", "/kostenlos", "/magazin", "/reihe/", "/event/"];
const WOERTER: Record<string, [number, number]> = { wochenvorschau: [600, 1800], "monats-tipps": [600, 1800] };
const EINBETTUNG = /^\{\{(event|ort|guide|tag):[^}]+\}\}$/;
const EVENT_EINBETTUNG = /\{\{event:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\}\}/gi;

/** Event-IDs aus den Einbettungen {{event:<uuid>}} in Reihenfolge, ohne Doppelte (wird zu event_ids) */
export function eingebetteteEvents(md: string): string[] {
  return [...new Set([...md.matchAll(EVENT_EINBETTUNG)].map((m) => m[1].toLowerCase()))];
}

/** Überschriften (# …) und Fließtext getrennt; Einbettungszeilen zählen zu keinem von beiden */
export function teilen(md: string): { ueberschriften: string[]; text: string } {
  const ueberschriften: string[] = [];
  const text: string[] = [];
  for (const zeile of md.split(/\r?\n/)) {
    const z = zeile.trim();
    if (!z) continue;
    if (z.startsWith("#")) ueberschriften.push(z.replace(/^#+\s*/, ""));
    else if (!EINBETTUNG.test(z)) text.push(zeile);
  }
  return { ueberschriften, text: text.join("\n") };
}

function datenImText(text: string, jahr: number): string[] {
  const tage: string[] = [];
  const iso = (j: number, m: number, t: number) => {
    const d = new Date(Date.UTC(j, m - 1, t));
    return d.getUTCFullYear() === j && d.getUTCMonth() === m - 1 && d.getUTCDate() === t ? d.toISOString().slice(0, 10) : null;
  };
  for (const m of text.matchAll(DATUM_MONAT)) {
    const t = iso(jahr, MONATE.indexOf(m[2]) + 1, Number(m[1]));
    if (t) tage.push(t);
  }
  for (const m of text.matchAll(DATUM_ZAHL)) {
    let j = m[3] ? Number(m[3]) : jahr;
    if (j < 100) j += 2000;
    const t = iso(j, Number(m[2]), Number(m[1]));
    if (t) tage.push(t);
  }
  return tage;
}

export function linkErlaubt(ziel: string): boolean {
  if (ziel.startsWith("https://") || /^mailto:[A-Za-z0-9._%+-]+@diesdas\.events$/.test(ziel)) return true;
  if (!ziel.startsWith("/") || ziel.startsWith("//") || ziel.includes("..")) return false;
  if (ziel === "/" || /^\/tag\/\d{4}-\d{2}-\d{2}$/.test(ziel)) return true;
  return INTERNE_PRAEFIXE.some((p) => ziel.startsWith(p));
}

/**
 * Prüfung (a)–(i) ohne (g). `eventStatus`: Status der eingebetteten Events (fehlt / abgelehnt / abgesagt), lädt der
 * Aufrufer aus der Datenbank.
 */
export function magazinPruefen(b: PruefEingabe, eventStatus: Map<string, { abgelehnt: boolean; abgesagt: boolean }>): PruefErgebnis {
  const punkte: string[] = [];
  const { ueberschriften, text } = teilen(b.inhalt_md);
  const kurz = b.kurzfassung ?? [];
  const faqText = (b.faq ?? []).map((f) => `${String(f.frage ?? "")}\n${String(f.antwort ?? "")}`).join("\n");
  const fliessMitFaq = [text, faqText].filter(Boolean).join("\n");
  const kopf = [b.titel, b.teaser ?? "", ...kurz, ...ueberschriften].join("\n");
  const alles = [kopf, fliessMitFaq].join("\n");

  // (a) eingebettete Events müssen existieren und dürfen nicht abgesagt sein
  for (const id of eingebetteteEvents(b.inhalt_md)) {
    const s = eventStatus.get(id);
    if (!s || s.abgelehnt) punkte.push(`(a) Event ${id} existiert nicht oder ist ausgeblendet`);
    else if (s.abgesagt) punkte.push(`(a) Event ${id} ist abgesagt`);
  }

  // (b) Uhrzeiten, Preise, „ausverkauft“ nirgends; Daten nur im Kopf und nur im Zeitraum
  for (const [name, muster] of [["Uhrzeit", UHRZEIT], ["Preis", PREIS], ["„ausverkauft“", AUSVERKAUFT]] as const) {
    const t = muster.exec(alles);
    if (t) punkte.push(`(b) ${name} im Text: „${t[0]}“`);
  }
  const jahr = Number((b.gueltig_von ?? new Date().toISOString()).slice(0, 4));
  if (datenImText(fliessMitFaq, jahr).length) punkte.push("(b) Datumsangabe im Fließtext oder in der FAQ (Daten stehen in den Karten)");
  if (b.gueltig_von && b.gueltig_bis) {
    for (const d of datenImText(kopf, jahr)) {
      const naechstes = `${Number(d.slice(0, 4)) + 1}${d.slice(4)}`;
      const drin = (x: string) => x >= b.gueltig_von! && x <= b.gueltig_bis!;
      if (!drin(d) && !drin(naechstes)) punkte.push(`(b) Datum ${d} außerhalb des Zeitraums ${b.gueltig_von}–${b.gueltig_bis}`);
    }
  }

  // (c) Links
  for (const m of fliessMitFaq.matchAll(LINK)) {
    if (!linkErlaubt(m[2])) punkte.push(`(c) Link nicht erlaubt oder unbekannt: ${m[2]}`);
  }

  // (d) Längen
  if (b.titel.length < 1 || b.titel.length > 90) punkte.push(`(d) Titel hat ${b.titel.length} Zeichen (höchstens 90)`);
  const teaserLaenge = (b.teaser ?? "").length;
  if (teaserLaenge < 80 || teaserLaenge > 160) punkte.push(`(d) Teaser hat ${teaserLaenge} Zeichen (80–160)`);
  if (kurz.length < 3 || kurz.length > 5) punkte.push(`(d) Kurzfassung hat ${kurz.length} Punkte (3–5)`);
  const grenzen = WOERTER[b.rubrik];
  if (grenzen) {
    const woerter = text.split(/\s+/).filter(Boolean).length;
    if (woerter < grenzen[0] || woerter > grenzen[1]) punkte.push(`(d) Text hat ${woerter} Wörter (${grenzen[0]}–${grenzen[1]})`);
  }

  // (e) Clickbait; Ich-Form nur in der Stimme des Pseudonyms (FAQ-Fragen sind Leserstimme)
  const cb = CLICKBAIT.exec(alles);
  if (cb) punkte.push(`(e) Clickbait: „${cb[0]}“`);
  const stimme = [kopf, text, ...(b.faq ?? []).map((f) => String(f.antwort ?? ""))].join("\n");
  const ich = ICH_FORM.exec(stimme);
  if (ich) punkte.push(`(e) Ich-Form: „${ich[0]}“`);

  // (f) keine Google-Inhalte
  const g = GOOGLE.exec(alles);
  if (g) punkte.push(`(f) Google-Inhalt: „${g[0]}“`);

  // (h) Titel nicht mit dem Kopfbegriff eines Guides
  if (HUB_KOEPFE.some((k) => b.titel.startsWith(k))) punkte.push("(h) Titel beginnt mit dem Kopfbegriff eines Guides (E5)");

  // (i) Aufmacherbild
  if (!b.hero_bild) punkte.push("(i) Aufmacherbild fehlt");
  else if (!heroErlaubt(b.hero_bild)) punkte.push(`(i) Aufmacherbild nicht erlaubt: ${b.hero_bild}`);
  if (!b.hero_alt?.trim()) punkte.push("(i) Alt-Text des Aufmacherbilds fehlt");

  return { ergebnis: punkte.length ? "rot" : "gruen", punkte };
}
