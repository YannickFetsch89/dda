// Kartenpunkte des Club-Hubs: wie die anderen Hubs (kartenOrte), aber mit Club-URL, Club-Unterart,
// Musikrichtung statt Preis und der Empfehlungsstufe A/B/C für die Pin-Farbe.
import type { KartenOrt } from "@/components/guide-karte";
import { kartenOrte } from "@/components/ort-karten";
import { clubArtInfo, clubStufeInfo, hauptGenres } from "./clubs";
import type { DddOrt } from "./typen";

export function clubKartenOrte(orte: DddOrt[]): KartenOrt[] {
  const nachId = new Map(orte.map((o) => [o.id, o]));
  return kartenOrte(orte).map((k) => {
    const o = nachId.get(k.id)!;
    const art = clubArtInfo(o);
    const stufe = clubStufeInfo(o);
    return {
      ...k,
      typLabel: art.label,
      icon: art.icon,
      preis: hauptGenres(o).slice(0, 2).join(" / ") || null,
      href: `/guides/clubs/${encodeURIComponent(o.slug)}`,
      stufe: stufe.wert,
      stufeLabel: stufe.label,
    };
  });
}
