// Gemeinsame Typen für das Website-Frontend

export type KategorieSlug =
  | "kultur"
  | "musik"
  | "food"
  | "sport"
  | "outdoor"
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
  erstellt_am: string | null;
  tipp_des_tages: boolean;
  highlight_der_woche: boolean;
  top_event_des_monats: boolean;
  slug: string | null;
  /** Bleibt im Kalender sichtbar (markiert), fällt aber aus allen Hervorhebungen und der Startseite */
  abgesagt: boolean;
}

/** Typ eines Ortes in der `orte`-Tabelle. */
export type OrtTyp = "restaurant" | "cafe" | "kneipe" | "club" | "spielplatz" | "ausflug" | "wochenendtipp";

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
  events: DddEvent[];
  quelle: "supabase" | "beispiel";
  fehler: string | null;
}
