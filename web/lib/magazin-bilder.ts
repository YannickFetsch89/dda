// Magazin-Bilder (Plan 3.1 und 5.11): erlaubte Aufmacherbilder, Rubrik-Ersatzbild, Zuschnitte.
import type { MagazinBeitrag, Rubrik } from "./magazin";

/**
 * KI-Symbolbilder aus public/fallback/ mit mindestens 1200×675 px (16:9 ohne Hochskalieren). Einmalig mit sharp
 * erzeugt (19.11.2026, 84 von 151); der Test in tests/magazin.test.ts vergleicht die Liste mit den Dateien.
 */
export const ERLAUBTE_FALLBACK_HEROS: readonly string[] = [
  "advent-weihnachtsmarkt-1", "advent-weihnachtsmarkt-2", "advent-weihnachtsmarkt-3", "advent-weihnachtsmarkt-4",
  "advent-weihnachtsmarkt-5", "csd-pride-1", "csd-pride-2", "csd-pride-3", "csd-pride-4", "csd-pride-5", "japan-tag-1",
  "japan-tag-2", "japan-tag-3", "japan-tag-4", "japan-tag-5", "karneval-1", "karneval-3", "karneval-5", "nacht-der-museen-1",
  "nacht-der-museen-2", "nacht-der-museen-3", "nacht-der-museen-4", "nacht-der-museen-5", "nikolaus-1", "nikolaus-2",
  "nikolaus-3", "nikolaus-4", "oktoberfest-1", "oktoberfest-2", "oktoberfest-3", "oktoberfest-4", "oktoberfest-5",
  "oktoberfest-6", "oktoberfest-7", "ostern-1", "ostern-2", "ostern-3", "ostern-4", "ostern-5", "rheinkirmes-1",
  "rheinkirmes-2", "rheinkirmes-3", "rheinkirmes-4", "rheinkirmes-5", "silvester-1", "silvester-2", "silvester-3",
  "silvester-4", "silvester-5", "silvester-6", "sommer-openair-1", "sommer-openair-2", "sommer-openair-3",
  "sommer-openair-4", "sommer-openair-5", "sprachcafe-1", "sprachcafe-3", "sprachcafe-4", "sprachcafe-6",
  "tanz-in-den-mai-1", "tanz-in-den-mai-2", "tanz-in-den-mai-3", "tanz-in-den-mai-4", "tanz-in-den-mai-5", "theater-1",
  "theater-2", "theater-3", "theater-4", "theater-5", "theater-6", "theater-7", "theater-8", "valentinstag-1",
  "valentinstag-2", "valentinstag-3", "valentinstag-4", "valentinstag-5", "weihnachten-1", "weihnachten-2",
  "weihnachten-3", "weihnachten-4", "weihnachten-5", "weihnachten-6", "weihnachten-7",
].map((name) => `/fallback/${name}.webp`);

/**
 * Rubrik-Ersatzbilder (Plan 3.1, Vorschlag; Auftraggeber kann tauschen). Alle in der Liste oben (≥ 1200×675).
 * Für die neuen Rubriken (19.11.2026) Motive ohne erkennbare Gesichter: Lichtinstallation, Café-Fassade, Picknick.
 */
export const RUBRIK_ERSATZ: Record<Rubrik, string> = {
  wochenvorschau: "/fallback/theater-1.webp",
  "monats-tipps": "/fallback/theater-2.webp",
  saison: "/fallback/theater-3.webp",
  nachtleben: "/fallback/nacht-der-museen-2.webp",
  genuss: "/fallback/sprachcafe-3.webp",
  familie: "/fallback/ostern-3.webp",
  stadtleben: "/fallback/sprachcafe-1.webp",
};

/** Muster wie der CHECK magazin_hero_pfad in der Datenbank (Fremdfoto koe-on-ice als eigenes Verbot). */
const HERO_PFAD = /^\/(magazin-bilder\/[a-z0-9-]+|fallback|ort-bilder\/weihnachtsmaerkte)\/[a-z0-9-]+\.(webp|jpg|png)$/;
const FREMDFOTO = "/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp";

/** Darf dieses Bild Aufmacher sein? Pfad-Muster, kein Fremdfoto, Fallback nur aus der Liste (≥ 675 px). */
export function heroErlaubt(pfad: string | null | undefined): pfad is string {
  if (!pfad || !HERO_PFAD.test(pfad) || pfad === FREMDFOTO) return false;
  return !pfad.startsWith("/fallback/") || ERLAUBTE_FALLBACK_HEROS.includes(pfad);
}

export interface Hero {
  pfad: string;
  alt: string;
  /** Bildnachweis – leer bei eigenen Fotos (Regel des Auftraggebers vom 20.11.2026: Nachweis nur bei fremden Bildern) */
  nachweis: string;
  /** „Symbolbild (KI-generiert)“ anzeigen */
  ki: boolean;
  /** Rubrik-Ersatzbild statt des gespeicherten Bilds */
  ersatz: boolean;
}

/**
 * Eigenes Foto? hero_nachweis ist beim Veröffentlichen Pflicht (Trigger); für eigene Fotos steht dort
 * „dies.das.düsseldorf“ (auch „Foto: dies.das.düsseldorf“). Angezeigt wird ein Nachweis nur bei fremden Bildern.
 */
export function eigenesFoto(nachweis: string | null | undefined): boolean {
  const n = (nachweis ?? "").trim().toLowerCase();
  return n === "" || /^(foto:\s*)?dies\.das\.düsseldorf$/.test(n);
}

/**
 * Das Aufmacherbild, das überall gilt: <img>, og:image, JSON-LD, Feed und Sitemap (Plan 3.1, Cursor-Prüfungen 3 und 4).
 * Ein nicht erlaubtes oder fehlendes Bild wird durch das Rubrik-Ersatzbild ersetzt.
 */
export function heroFuer(b: Pick<MagazinBeitrag, "rubrik" | "titel" | "hero_bild" | "hero_alt" | "hero_nachweis" | "hero_ki">): Hero {
  if (heroErlaubt(b.hero_bild)) {
    const fallback = b.hero_bild.startsWith("/fallback/");
    return {
      pfad: b.hero_bild,
      alt: b.hero_alt?.trim() || b.titel,
      nachweis: fallback ? b.hero_nachweis?.trim() || "Symbolbild" : eigenesFoto(b.hero_nachweis) ? "" : b.hero_nachweis!.trim(),
      ki: fallback || b.hero_ki,
      ersatz: false,
    };
  }
  return { pfad: RUBRIK_ERSATZ[b.rubrik], alt: b.titel, nachweis: "Symbolbild", ki: true, ersatz: true };
}

export const ZUSCHNITTE = ["16x9", "4x3", "1x1"] as const;
export type Zuschnitt = (typeof ZUSCHNITTE)[number];

/** Zuschnitt-URL (Route app/magazin-bild/[...pfad]): /magazin-bild/16x9/fallback/theater-1.webp */
export function zuschnittUrl(pfad: string, z: Zuschnitt): string {
  return `/magazin-bild/${z}${pfad}`;
}

/** Breite × Höhe je Zuschnitt (Ausgabe der Route; ≥ 50 000 Pixel, Plan 5.4). */
export const ZUSCHNITT_MASSE: Record<Zuschnitt, { breite: number; hoehe: number }> = {
  "16x9": { breite: 1200, hoehe: 675 },
  "4x3": { breite: 1200, hoehe: 900 },
  "1x1": { breite: 1200, hoehe: 1200 },
};

/** Erlaubte Ordner der Zuschnitt-Route (relativ zu public/). */
export const ZUSCHNITT_ORDNER = ["fallback", "magazin-bilder", "ort-bilder/weihnachtsmaerkte"] as const;

/**
 * Pfadteile der Zuschnitt-Route prüfen (Plan 5.11, Cursor-Prüfung 1 Befund 8): Seitenverhältnis aus der Liste, jedes
 * Segment dekodiert gegen ^[a-z0-9-]+$ (letztes mit Endung), Ordner aus der Liste. Ergebnis: Pfad relativ zu public/
 * oder null. Die Route prüft danach zusätzlich mit path.resolve, dass die Datei im Ordner liegt.
 */
export function zuschnittPruefen(teile: string[]): { zuschnitt: Zuschnitt; relativ: string } | null {
  if (teile.length < 3 || teile.length > 4) return null;
  let dekodiert: string[];
  try {
    dekodiert = teile.map((t) => decodeURIComponent(t));
  } catch {
    return null;
  }
  const [z, ...rest] = dekodiert;
  if (!(ZUSCHNITTE as readonly string[]).includes(z)) return null;
  const datei = rest[rest.length - 1];
  const ordner = rest.slice(0, -1);
  if (!/^[a-z0-9-]+\.(webp|jpg|png)$/.test(datei) || !ordner.every((s) => /^[a-z0-9-]+$/.test(s))) return null;
  const ordnerPfad = ordner.join("/");
  const erlaubt =
    ordnerPfad === "fallback" ||
    ordnerPfad === "ort-bilder/weihnachtsmaerkte" ||
    (ordner.length === 2 && ordner[0] === "magazin-bilder");
  if (!erlaubt) return null;
  const relativ = `${ordnerPfad}/${datei}`;
  if (`/${relativ}` === FREMDFOTO) return null;
  return { zuschnitt: z as Zuschnitt, relativ };
}
