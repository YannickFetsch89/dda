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
}

/** Alle Events eines Ladevorgangs plus Zeitbezug (in Europe/Berlin). */
export interface EventPool {
  heute: string;
  jetzt: string; // ISO-Zeitstempel des Ladezeitpunkts
  events: DddEvent[];
  quelle: "supabase" | "beispiel";
  fehler: string | null;
}
