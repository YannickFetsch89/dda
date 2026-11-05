// Test-Hilfe: Event mit sinnvollen Standardwerten bauen
import type { DddEvent } from "@/lib/typen";

export function ev(teil: Partial<DddEvent> & { id: string }): DddEvent {
  return {
    titel: "Testevent",
    datum: "2026-11-10",
    datum_bis: null,
    uhrzeit: null,
    ort: "zakk",
    adresse: null,
    kategorie: "musik",
    beschreibung: null,
    preis: null,
    quelle_name: null,
    quelle_url: null,
    bild_url: null,
    stadtteil: null,
    erstellt_am: null,
    tipp_des_tages: false,
    highlight_der_woche: false,
    top_event_des_monats: false,
    slug: `slug-${teil.id}`,
    abgesagt: false,
    reihe: null,
    uhrzeiten: null,
    ...teil,
  };
}
