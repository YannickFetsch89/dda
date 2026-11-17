// Kartenpunkte des Weihnachtsmarkt-Hubs (Plan 5.2): eigene Punktfunktion – keine Bewertung, kein Score, kein Zustand
// (der Zustand „heute offen“ wird nie fertig gerechnet ausgeliefert, Plan E5). Gruppenzeilen bekommen keinen Pin.
// Pin-Farbe nach Zustand (Stufe 1b) rechnet der Browser aus wmSaisons (components/guide-karte.tsx).
import type { KartenOrt } from "@/components/guide-karte";
import { ortBildFokus, ortBildUrl } from "./orte";
import { stadtteilName } from "./stadtteile";
import type { DddOrt } from "./typen";
import { aktuelleSaison, badges, datumKurz, rolleText, saisonsKompakt, wm, wmPfad } from "./weihnachtsmaerkte";

export function weihnachtsmarktKartenOrte(orte: DddOrt[], alle: DddOrt[] = orte): KartenOrt[] {
  return orte
    .filter((o) => o.latitude != null && o.longitude != null && !wm(o).ist_gruppe)
    .map((o) => {
      const s = aktuelleSaison(wm(o).saisons);
      return {
        id: o.id,
        name: o.name,
        typLabel: rolleText(o),
        icon: wm(o).attraktion ? (wm(o).art.includes("eisbahn") ? "ice_skating" : "attractions") : "wm:markt",
        stadtteil: o.stadtteil ? stadtteilName(o.stadtteil) : null,
        // Zeitraum statt Preis (feste Daten, kein Tageszustand)
        preis: s ? `${datumKurz(s.von)} bis ${datumKurz(s.bis)}` : null,
        rating: null,
        anzahl: null,
        bild: ortBildUrl(o) ?? "/guides/weihnachtsmaerkte.webp",
        fokus: ortBildFokus(o),
        href: wmPfad(o),
        lat: o.latitude!,
        lng: o.longitude!,
        stufeLabel: badges(o, alle).slice(0, 3).map((b) => b.label).join(" · ") || undefined,
        // Nur Zeitraum und Zeiten – den Zustand rechnet der Browser (Pin-Farbe, Stufe 1b)
        wmSaisons: saisonsKompakt(wm(o).saisons),
      };
    });
}
