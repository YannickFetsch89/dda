// Admin-Bereich – Meldungen freigeben (Plan Admin-Dashboard 4.10, Stufe 5b; Umzug aus dashboard/meldungen.py).
// Slug-Regel aus pipeline/slug_generator.py nach TypeScript übertragen (Entscheidung bei der Umsetzung: die
// „Alternative“ aus 4.10) – gleiche Ergebnisse prüft tests/fixtures/slugs.json in Python und TypeScript.
// Stadtteil: Vorschlag aus der PLZ (lib/plz-stadtteil.json = PLZ_STADTTEIL aus pipeline/stadtteil_mapper.py), der
// Admin kann ihn ändern. Rein, getestet in web/tests/admin-meldungen.test.ts.
import PLZ_STADTTEIL from "../plz-stadtteil.json";

const UMLAUTE: Record<string, string> = { ä: "ae", ö: "oe", ü: "ue", ß: "ss", Ä: "Ae", Ö: "Oe", Ü: "Ue" };
const MAX_TITEL = 60;
const MAX_ORT = 25;

function slugify(text: string, maxLaenge = 0): string {
  let t = text.replace(/[äöüßÄÖÜ]/g, (z) => UMLAUTE[z]);
  // wie unicodedata.normalize("NFKD") + encode("ascii", "ignore")
  t = t.normalize("NFKD").replace(/[^\x00-\x7F]/g, "");
  t = t.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-{2,}/g, "-").replace(/^-+|-+$/g, "");
  if (maxLaenge && t.length > maxLaenge) t = t.slice(0, maxLaenge).replace(/-+$/, "");
  return t;
}

/** {titel}-{ort}-{YYYY-MM-DD} wie slug_erzeugen in pipeline/slug_generator.py */
export function slugErzeugen(titel: string, ort: string, datum: string): string {
  if (!titel || !datum) return "";
  return [slugify(titel, MAX_TITEL), ort ? slugify(ort, MAX_ORT) : "", datum].filter(Boolean).join("-");
}

/** Erster freier Slug: Basis, dann -b … -z, dann Zahlen (wie slug_mit_suffix) */
export function slugMitSuffix(basis: string, vergeben: Set<string>): string {
  if (!vergeben.has(basis)) return basis;
  for (const b of "bcdefghijklmnopqrstuvwxyz") if (!vergeben.has(`${basis}-${b}`)) return `${basis}-${b}`;
  let z = 26;
  while (vergeben.has(`${basis}-${z}`)) z += 1;
  return `${basis}-${z}`;
}

/** Stadtteil-Vorschlag aus der PLZ in der Adresse (Priorität 3 des Stadtteil-Mappers; Venue-Liste bleibt in Python) */
export function stadtteilAusAdresse(adresse: string | null | undefined): string | null {
  const plz = /\b(40\d{3})\b/.exec(adresse ?? "")?.[1]; // wie _PLZ_REGEX in pipeline/stadtteil_mapper.py
  return plz ? ((PLZ_STADTTEIL as Record<string, string>)[plz] ?? null) : null;
}

/**
 * Höchstlänge der Beschreibung bei der Freigabe = Höchstlänge im Meldeformular (event_meldungen: 20–2.000 Zeichen).
 * Bis 26.11.2026 wurde hier auf 300 Zeichen gekürzt (Altlast aus dem Streamlit-Dashboard); die Grenze in
 * events.beschreibung ist seit 10.11.2026 aufgehoben, die Pipeline schreibt bis etwa 1.200 Zeichen.
 */
export const BESCHREIBUNG_MAX = 2000;

/**
 * Beschreibung aufräumen und nur bei Überlänge kürzen, möglichst am Satzende. Zeilenumbrüche bleiben erhalten:
 * Die Event-Seite zeigt Absätze und Listen (lib/beschreibung.ts beschreibungsBloecke). Mehrfache Leerzeichen und
 * mehr als eine Leerzeile werden zusammengefasst.
 */
export function kuerzen(text: string, laenge = BESCHREIBUNG_MAX): string {
  const t = (text ?? "")
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map((z) => z.replace(/[ \t ]+/g, " ").trim())
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  if (t.length <= laenge) return t;
  const stueck = t.slice(0, laenge - 1);
  const ende = Math.max(...[". ", "! ", "? ", ".\n", "!\n", "?\n"].map((s) => stueck.lastIndexOf(s)));
  if (ende >= Math.floor(laenge / 2)) return stueck.slice(0, ende + 1);
  return stueck.slice(0, Math.max(stueck.lastIndexOf(" "), stueck.lastIndexOf("\n"))).replace(/[\s,;:–-]+$/, "") + "…";
}

export const MELDUNG_KATEGORIEN = ["kultur", "musik", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family", "dating", "sonstiges"] as const;

export interface FreigabeWerte {
  titel: string;
  kategorie: string;
  datum: string;
  datum_bis: string | null;
  uhrzeit: string | null;
  ort: string;
  adresse: string | null;
  stadtteil: string | null;
  preis: string | null;
  link: string | null;
  beschreibung: string;
}

const DATUM = /^\d{4}-\d{2}-\d{2}$/;
const UHRZEIT = /^([01]\d|2[0-3]):[0-5]\d$/;

/** Formularwerte prüfen (Pflichtfelder wie im Dashboard: Titel, Ort, Beschreibung ≥ 20 Zeichen) */
export function freigabePruefen(roh: Record<string, unknown>): { ok: true; werte: FreigabeWerte } | { ok: false; fehler: string } {
  const s = (k: string, max: number) => (typeof roh[k] === "string" ? (roh[k] as string).trim().slice(0, max) : "");
  const titel = s("titel", 150);
  const ort = s("ort", 150);
  const beschreibung = s("beschreibung", 2000);
  const kategorie = s("kategorie", 20);
  const datum = s("datum", 10);
  const datumBis = s("datum_bis", 10);
  const uhrzeit = s("uhrzeit", 5);
  const link = s("link", 500);
  if (titel.length < 3 || !ort || beschreibung.length < 20) return { ok: false, fehler: "Titel, Ort und eine Beschreibung (mind. 20 Zeichen) sind Pflicht." };
  if (!(MELDUNG_KATEGORIEN as readonly string[]).includes(kategorie)) return { ok: false, fehler: "Unbekannte Kategorie." };
  if (!DATUM.test(datum) || (datumBis && (!DATUM.test(datumBis) || datumBis < datum))) return { ok: false, fehler: "Datum als JJJJ-MM-TT, „bis“ nicht vor „von“." };
  if (uhrzeit && !UHRZEIT.test(uhrzeit)) return { ok: false, fehler: "Uhrzeit als HH:MM." };
  if (link && !/^https?:\/\/\S+$/.test(link)) return { ok: false, fehler: "Link muss mit http(s):// beginnen." };
  return {
    ok: true,
    werte: {
      titel,
      kategorie,
      datum,
      datum_bis: datumBis || null,
      uhrzeit: uhrzeit || null,
      ort,
      adresse: s("adresse", 200) || null,
      stadtteil: s("stadtteil", 60) || null,
      preis: s("preis", 80) || null,
      link: link || null,
      beschreibung,
    },
  };
}
