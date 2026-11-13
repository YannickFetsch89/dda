// Gemeinsame Typen für das Website-Frontend

export type KategorieSlug =
  | "kultur"
  | "musik"
  | "food"
  | "sport"
  | "outdoor"
  | "stadtfuehrung"
  | "community"
  | "nightlife"
  | "familie"
  | "dating"
  | "sonstiges";

/** Event, wie es aus der Supabase-Tabelle `events` gelesen und normalisiert wird. */
export interface DddEvent {
  id: string;
  titel: string;
  datum: string; // YYYY-MM-DD
  datum_bis: string | null;
  uhrzeit: string | null; // HH:MM
  ort: string;
  adresse: string | null;
  kategorie: KategorieSlug;
  beschreibung: string | null;
  preis: string | null;
  quelle_name: string | null;
  quelle_url: string | null;
  bild_url: string | null;
  stadtteil: string | null;
  /** Feinfilter innerhalb der Kategorie (Slug aus lib/unterkategorien.json, „keine“ = geprüft, nichts passt) */
  unterkategorie?: string | null;
  erstellt_am: string | null;
  tipp_des_tages: boolean;
  highlight_der_woche: boolean;
  top_event_des_monats: boolean;
  /** Zeitpunkt, zu dem die Highlight-Flagge gesetzt wurde; ohne ihn gilt die Flagge nicht (Plan Empfehlungen, Abschnitt 8) */
  highlight_gesetzt_am?: string | null;
  /** Zeitpunkt, zu dem die Top-Flagge gesetzt wurde; ohne ihn gilt die Flagge nicht */
  top_gesetzt_am?: string | null;
  slug: string | null;
  /** Bleibt im Kalender sichtbar (markiert), fällt aber aus allen Hervorhebungen und der Startseite */
  abgesagt: boolean;
  /** Reihe (wiederkehrendes Event) mit dauerhafter Seite /reihe/<slug>, sonst null */
  reihe: { slug: string; titel: string } | null;
  /** Nur bei gebündelten Listeneinträgen (lib/termine.ts): alle Uhrzeiten des Tages, sonst null */
  uhrzeiten: string[] | null;
}

/** Typ eines Ortes in der `orte`-Tabelle. */
export type OrtTyp = "restaurant" | "imbiss" | "cafe" | "kneipe" | "club" | "spielplatz" | "ausflug" | "wochenendtipp";

/** Preisniveau eines Ortes. */
export type PreisNiveau = "€" | "€€" | "€€€";

/** Ort, wie er aus der Supabase-Tabelle `orte` gelesen wird. */
export interface DddOrt {
  id: string;
  name: string;
  slug: string;
  typ: OrtTyp;
  untertitel: string | null;
  beschreibung: string | null;
  highlight: string | null;
  adresse: string | null;
  stadtteil: string | null;
  latitude: number | null;
  longitude: number | null;
  bild_url: string | null;
  bild_attribution: string | null;
  tags: string[];
  preis_niveau: PreisNiveau | null;
  oeffnungszeiten: string | null;
  webseite: string | null;
  telefon: string | null;
  instagram: string | null;
  google_place_id: string | null;
  google_rating: number | null;
  google_bewertungen_anzahl: number | null;
  qualitaets_score: number | null;
  extras: Record<string, unknown>;
  sortierung: number;
  erstellt_am: string | null;
  aktualisiert_am: string | null;
}

/** Alle Events eines Ladevorgangs plus Zeitbezug (in Europe/Berlin). */
export interface EventPool {
  heute: string;
  jetzt: string; // ISO-Zeitstempel des Ladezeitpunkts
  /** Für alle Listen: mehrere Uhrzeiten desselben Events am selben Tag zu einem Eintrag gebündelt */
  events: DddEvent[];
  /** Alle Termine einzeln (Detailseiten, Uhrzeit-Auswahl) */
  alle: DddEvent[];
  quelle: "supabase" | "beispiel";
  fehler: string | null;
}
