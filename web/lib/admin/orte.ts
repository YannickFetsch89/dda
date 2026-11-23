// Admin-Bereich – Orte (Plan Admin-Dashboard 4.7, Stufe 3a): Filter, Stammdaten-Eingaben, Texte, Seitenpfad.
// Reine Funktionen, getestet in web/tests/admin-orte.test.ts. Schreiben: Stammdaten per UPDATE (Policy
// orte_admin_aendern), alles mit Weiterleitung oder extras über die Funktionen in database/admin_orte_2026-11-23.sql.
import { guideZiel, type OrtKopf } from "../pfad-pruefung";
import { BEZIRKE } from "../stadtteile";
import type { OrtTyp } from "../typen";

export const ORT_TYPEN: { wert: OrtTyp; text: string }[] = [
  { wert: "spielstaette", text: "Spielstätte" },
  { wert: "club", text: "Club" },
  { wert: "kneipe", text: "Kneipe/Bar" },
  { wert: "restaurant", text: "Restaurant" },
  { wert: "cafe", text: "Café" },
  { wert: "imbiss", text: "Imbiss" },
  { wert: "spielplatz", text: "Spielplatz" },
  { wert: "weihnachtsmarkt", text: "Weihnachtsmarkt" },
  { wert: "ausflug", text: "Ausflug" },
  { wert: "wochenendtipp", text: "Wochenendtipp" },
];

export function istOrtTyp(w: unknown): w is OrtTyp {
  return typeof w === "string" && ORT_TYPEN.some((t) => t.wert === w);
}

export const ORT_FILTER = ["inaktiv", "ohne_text", "ohne_bild", "ohne_geo", "ohne_adresse", "text_entwurf"] as const;
export type OrtFilter = (typeof ORT_FILTER)[number];

/** Alle Stadtteile der Bezirke (Vorschlagsliste im Formular; Neuss/Ratingen u. a. bleiben als freier Text möglich) */
export const STADTTEILE = BEZIRKE.flatMap((b) => b.stadtteile).sort((a, b) => a.localeCompare(b, "de"));

/** Spalten, die das Stammdaten-Formular ändern darf (UPDATE mit dem Admin-Token) */
export const STAMMDATEN_FELDER = [
  "name",
  "untertitel",
  "beschreibung",
  "highlight",
  "adresse",
  "stadtteil",
  "latitude",
  "longitude",
  "webseite",
  "telefon",
  "instagram",
  "oeffnungszeiten",
  "preis_niveau",
  "sortierung",
  "aktiv",
] as const;

const LAENGEN: Record<string, number> = {
  name: 120,
  untertitel: 200,
  beschreibung: 4000,
  highlight: 300,
  adresse: 200,
  stadtteil: 60,
  webseite: 300,
  telefon: 40,
  instagram: 100,
  oeffnungszeiten: 1500,
};

// Grober Rahmen um Düsseldorf mit Neuss und Ratingen (E3 des Orte-Plans) – fängt vertauschte Koordinaten ab
const BREITE: [number, number] = [51.05, 51.45];
const LAENGE: [number, number] = [6.55, 7.05];

export type Eingabe = { ok: true; felder: Record<string, unknown> } | { ok: false; fehler: string };

/**
 * Spalten, die ein Import bei jedem Lauf aus seiner CSV neu schreibt – im Dashboard geändert, wären sie beim nächsten
 * Lauf wieder weg (Stufe 3b, Q6). Weihnachtsmärkte: scraper/weihnachtsmaerkte/import_maerkte.py (maerkte.csv);
 * Spielplätze: scraper/spielplaetze/stadt_import.py und abenteuer_import.py (Stadtdaten, korrekturen.csv, abenteuer.csv).
 */
export const CSV_FELDER: Record<string, { felder: string[]; quelle: string }> = {
  weihnachtsmarkt: {
    felder: ["name", "stadtteil", "adresse", "latitude", "longitude", "webseite", "beschreibung"],
    quelle: "data/weihnachtsmaerkte/maerkte.csv",
  },
  spielplatz: {
    felder: ["name", "stadtteil", "adresse", "latitude", "longitude", "oeffnungszeiten"],
    quelle: "data/spielplaetze/korrekturen.csv bzw. abenteuer.csv",
  },
};

/**
 * Prüft die Stammdaten aus dem Formular. Leere Texte werden NULL. `aktiv` nur true (Abschalten läuft über
 * „Schließen“ mit Weiterleitung). Bei Spielstätten ist die Beschreibung gesperrt: Sie ändert sich nur über die
 * Text-Freigabe (mit Quellen).
 */
export function stammdatenPruefen(eingabe: Record<string, unknown>, typ: string): Eingabe {
  const felder: Record<string, unknown> = {};
  for (const [k, w] of Object.entries(eingabe)) {
    if (!(STAMMDATEN_FELDER as readonly string[]).includes(k)) return { ok: false, fehler: `Feld „${k}“ ist hier nicht bearbeitbar.` };
    const csv = CSV_FELDER[typ];
    if (csv?.felder.includes(k)) return { ok: false, fehler: `„${k}“ kommt aus ${csv.quelle} – der Import würde die Änderung überschreiben.` };
    if (k === "aktiv") {
      if (w !== true) return { ok: false, fehler: "Abschalten bitte über „Schließen“ (mit Weiterleitung)." };
      // Spielplätze und Weihnachtsmärkte brauchen beim Freischalten freigeschaltet_am, sonst endet die Guide-URL nach
      // einem späteren Schließen als 404 (Cursor-Prüfung 3a, Befund 2). Das pflegt erst die Guide-Pflege (3b).
      if (typ === "spielplatz" || typ === "weihnachtsmarkt") return { ok: false, fehler: "Spielplätze und Weihnachtsmärkte werden mit der Guide-Pflege freigeschaltet (Stufe 3b)." };
      felder.aktiv = true;
    } else if (k === "latitude" || k === "longitude") {
      if (w === null || w === "") {
        felder[k] = null;
        continue;
      }
      const z = typeof w === "number" ? w : Number(String(w).replace(",", "."));
      const [min, max] = k === "latitude" ? BREITE : LAENGE;
      if (!Number.isFinite(z) || z < min || z > max) return { ok: false, fehler: `${k === "latitude" ? "Breite" : "Länge"} muss zwischen ${min} und ${max} liegen.` };
      felder[k] = Math.round(z * 1e6) / 1e6;
    } else if (k === "sortierung") {
      const z = Number(w);
      if (!Number.isInteger(z) || z < -1000 || z > 1000) return { ok: false, fehler: "Sortierung: ganze Zahl von -1000 bis 1000." };
      felder[k] = z;
    } else if (k === "preis_niveau") {
      const s = typeof w === "string" ? w.trim() : "";
      if (s && !["€", "€€", "€€€"].includes(s)) return { ok: false, fehler: "Preisniveau: €, €€ oder €€€." };
      felder[k] = s || null;
    } else {
      if (k === "beschreibung" && typ === "spielstaette") return { ok: false, fehler: "Den Text einer Spielstätte bitte über „Text“ ändern und freigeben." };
      const s = typeof w === "string" ? w.trim() : "";
      if (k === "name" && !s) return { ok: false, fehler: "Name darf nicht leer sein." };
      if (s.length > LAENGEN[k]) return { ok: false, fehler: `${k}: höchstens ${LAENGEN[k]} Zeichen.` };
      if (k === "webseite" && s && !/^https?:\/\/[^\s]+$/.test(s)) return { ok: false, fehler: "Website muss mit http(s):// beginnen." };
      felder[k] = s || null;
    }
  }
  if (("latitude" in felder) !== ("longitude" in felder)) return { ok: false, fehler: "Breite und Länge nur zusammen ändern." };
  if ((felder.latitude === null) !== (felder.longitude === null)) return { ok: false, fehler: "Breite und Länge beide setzen oder beide leeren." };
  return { ok: true, felder };
}

/** Nur die Felder, die sich wirklich ändern (für Update und Protokoll) */
export function aenderungen(bisher: Record<string, unknown>, felder: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(felder).filter(([k, w]) => (bisher[k] ?? null) !== (w ?? null)));
}

/** Eingaben für Text-Entwurf und -Freigabe (gleiche Grenzen wie admin_ort_text_speichern) */
export function textPruefen(text: unknown, quellen: unknown, freigeben: boolean): { ok: true; text: string; quellen: string[] } | { ok: false; fehler: string } {
  const t = typeof text === "string" ? text.trim() : "";
  if (t.length < 200 || t.length > 4000) return { ok: false, fehler: `Text: 200 bis 4000 Zeichen (jetzt ${t.length}).` };
  const liste = (Array.isArray(quellen) ? quellen : typeof quellen === "string" ? quellen.split(/\r?\n/) : [])
    .map((q) => String(q).trim())
    .filter(Boolean);
  const falsch = liste.find((q) => !/^https:\/\/\S+$/.test(q));
  if (falsch) return { ok: false, fehler: `Quelle muss mit https:// beginnen: ${falsch}` };
  if (freigeben && !liste.length) return { ok: false, fehler: "Zur Freigabe mindestens eine Quelle angeben." };
  return { ok: true, text: t, quellen: liste };
}

/** Kopf-Felder für guideZiel aus einer Admin-Zeile (extras-Teile wie in pfad-pruefung.ts) */
export function ortKopf(z: { typ: string; aktiv: boolean | null; qualitaets_score: number | null; stadtteil?: string | null; extras_kopf?: Record<string, unknown> | null }): OrtKopf {
  const x = z.extras_kopf ?? {};
  return {
    typ: z.typ,
    aktiv: !!z.aktiv,
    qualitaets_score: z.qualitaets_score,
    club: x.club ?? null,
    club_score: x.club_score ?? null,
    club_freigegeben: x.club_freigegeben ?? null,
    auch_club: x.auch_club ?? null,
    kein_club: x.kein_club ?? null,
    stadtteil: z.stadtteil ?? null,
  };
}

/** Öffentliche Seite eines Ortes oder null (nicht sichtbar) – dieselben Regeln wie der Proxy */
export function oeffentlicherPfad(slug: string, kopf: OrtKopf): string | null {
  if (kopf.typ === "spielstaette") return kopf.aktiv ? `/orte/${encodeURIComponent(slug)}` : null;
  return guideZiel(kopf, slug);
}
