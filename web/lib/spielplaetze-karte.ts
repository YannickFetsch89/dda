// Kartenpunkte des Spielplatz-Hubs (Plan 5.2): eigene Punktfunktion – id, Name, Typ, Alter (+ „vermutlich“), Stadtteil,
// Koordinate, URL, Thumb. Keine Bewertung, keine OSM-Tags (ODbL, Score nur intern).
import type { KartenOrt } from "@/components/guide-karte";
import { ortPfad } from "@/components/ort-karten";
import { ortBildUrl } from "./orte";
import { GERAETE, alterInfo, geraetJa, typInfo } from "./spielplaetze";
import { stadtteilName } from "./stadtteile";
import type { DddOrt } from "./typen";

export function spielplatzKartenOrte(orte: DddOrt[]): KartenOrt[] {
  return orte
    .filter((o) => o.latitude != null && o.longitude != null)
    .map((o) => {
      const typ = typInfo(o);
      const alter = alterInfo(o);
      return {
        id: o.id,
        name: o.name,
        typLabel: typ.label,
        icon: typ.icon,
        stadtteil: o.stadtteil ? stadtteilName(o.stadtteil) : null,
        preis: GERAETE.filter((g) => geraetJa(o, g.wert)).slice(0, 3).map((g) => g.label).join(", ") || null,
        rating: null,
        anzahl: null,
        bild: ortBildUrl(o) ?? typ.bild,
        href: ortPfad(o),
        lat: o.latitude!,
        lng: o.longitude!,
        alter: alter?.wert ?? "unbekannt",
        alterLabel: alter ? `${alter.vermutlich ? "vermutlich " : ""}${alter.kurz}` : "Alter unbekannt",
      };
    });
}
