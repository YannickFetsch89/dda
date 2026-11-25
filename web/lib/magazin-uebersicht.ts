// Magazin-Übersicht nach dem Vorbild eines Ratgeber-Hubs (Auftraggeber, 25.11.2026): Themenwelten mit Anzahl,
// Titelgeschichte, „Frisch aus der Redaktion“ mit Rubrik-Filter. Hier nur reine Auswahl- und Datenlogik (getestet),
// die Darstellung steht in components/magazin-uebersicht.tsx und components/magazin-filter.tsx.
import { tagLang } from "./datum";
import { berlinTag, beitragPfad, istVorbei, lesezeit, RUBRIKEN, RUBRIK_NAME, saisonVorbei, type MagazinBeitrag, type Rubrik } from "./magazin";
import { heroFuer } from "./magazin-bilder";

/** Material-Symbol je Rubrik (Themenwelten, Filter, Rubrik-Seite). */
export const RUBRIK_ICON: Record<Rubrik, string> = {
  wochenvorschau: "date_range",
  "monats-tipps": "calendar_month",
  saison: "celebration",
  nachtleben: "nightlife",
  genuss: "restaurant",
  familie: "family_restroom",
  stadtleben: "location_city",
};

/** Laufende Ausgaben (Wochenvorschau, Monats-Tipps) – als Titelgeschichte nur, wenn nichts anderes da ist. */
const LAUFEND: Rubrik[] = ["wochenvorschau", "monats-tipps"];

/** Noch aktuell: laufende Ausgabe nicht abgelaufen, Saison nicht vorbei. */
export function istAktuell(b: MagazinBeitrag, heute: string): boolean {
  return !istVorbei(b, heute) && !saisonVorbei(b, heute);
}

/** Anzahl veröffentlichter Beiträge je Rubrik (alle Rubriken, auch mit 0). */
export function themenZaehlen(beitraege: MagazinBeitrag[]): Record<Rubrik, number> {
  const zahl = Object.fromEntries(RUBRIKEN.map((r) => [r, 0])) as Record<Rubrik, number>;
  for (const b of beitraege) zahl[b.rubrik] += 1;
  return zahl;
}

/**
 * Titelgeschichte: der neueste aktuelle Beitrag außerhalb der laufenden Rubriken (Saison, Stadtleben, Genuss …) –
 * das sind die längeren, länger gültigen Stücke. Gibt es keinen, der neueste aktuelle überhaupt, sonst der neueste.
 * beitraege kommt neueste zuerst (beitraegeLaden).
 */
export function titelgeschichte(beitraege: MagazinBeitrag[], heute: string): MagazinBeitrag | null {
  const aktuell = beitraege.filter((b) => istAktuell(b, heute));
  return aktuell.find((b) => !LAUFEND.includes(b.rubrik)) ?? aktuell[0] ?? beitraege[0] ?? null;
}

/** Was eine Karte in „Frisch aus der Redaktion“ braucht – serialisierbar für die Client-Komponente mit dem Filter. */
export interface KarteDaten {
  id: string;
  href: string;
  titel: string;
  teaser: string | null;
  rubrik: Rubrik;
  rubrikName: string;
  datum: string | null;
  lesezeit: number;
  bild: string;
  /** KI-Symbolbild → kleine Kennzeichnung auf dem Bild (E7) */
  bildKi: boolean;
}

export function karteDaten(b: MagazinBeitrag): KarteDaten {
  return {
    id: b.id,
    href: beitragPfad(b),
    titel: b.titel,
    teaser: b.teaser,
    rubrik: b.rubrik,
    rubrikName: RUBRIK_NAME[b.rubrik],
    datum: b.veroeffentlicht_am ? tagLang(berlinTag(b.veroeffentlicht_am)) : null,
    lesezeit: lesezeit(b.inhalt_md),
    bild: heroFuer(b).pfad,
    bildKi: heroFuer(b).ki,
  };
}

/** Rubriken, für die es in der Liste mindestens einen Beitrag gibt – in der festen Reihenfolge der Rubriken. */
export function filterRubriken(karten: Pick<KarteDaten, "rubrik">[]): Rubrik[] {
  const da = new Set(karten.map((k) => k.rubrik));
  return RUBRIKEN.filter((r) => da.has(r));
}
