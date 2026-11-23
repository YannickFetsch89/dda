// Admin-Bereich – Bilder und Guide-Pflege (Plan Admin-Dashboard 4.7, Stufe 3b). Reine Funktionen, getestet in
// web/tests/admin-guides.test.ts. Geschrieben wird über die Funktionen in database/admin_guides_2026-11-23.sql;
// die Regeln hier spiegeln sie für die Anzeige (Button an/aus, Hinweise) und für lesbare Fehlermeldungen.

/** Google-Foto, wie es in extras.google_foto steht (nie eine URL mit Key) */
export interface GoogleFoto {
  name: string;
  breite: number | null;
  hoehe: number | null;
  autor: string | null;
  autor_url: string | null;
}

export const FOTO_NAME = /^places\/[A-Za-z0-9_-]+\/photos\/[A-Za-z0-9_-]+$/;
export const PLACE_ID = /^[A-Za-z0-9_-]{10,300}$/;

/** Kandidaten aus der Antwort der Places API (photos mit authorAttributions), höchstens 10 */
export function googleKandidaten(antwort: unknown): GoogleFoto[] {
  const fotos = (antwort as { photos?: unknown })?.photos;
  if (!Array.isArray(fotos)) return [];
  const aus: GoogleFoto[] = [];
  for (const f of fotos) {
    const x = f as { name?: unknown; widthPx?: unknown; heightPx?: unknown; authorAttributions?: { displayName?: unknown; uri?: unknown }[] };
    if (typeof x.name !== "string" || !FOTO_NAME.test(x.name)) continue;
    const autor = Array.isArray(x.authorAttributions) ? x.authorAttributions[0] : undefined;
    const uri = typeof autor?.uri === "string" && autor.uri.startsWith("https://") ? autor.uri : null;
    aus.push({
      name: x.name,
      breite: typeof x.widthPx === "number" ? x.widthPx : null,
      hoehe: typeof x.heightPx === "number" ? x.heightPx : null,
      autor: typeof autor?.displayName === "string" ? autor.displayName.slice(0, 200) : null,
      autor_url: uri,
    });
    if (aus.length >= 10) break;
  }
  return aus;
}

/** Eigene Bilddatei unter /ort-bilder/ (wie die SQL-Prüfung in admin_ort_bild_setzen) */
export function eigenesBildErlaubt(pfad: string): boolean {
  return /^\/ort-bilder\/[a-z0-9][a-z0-9/_-]*\.(webp|jpg|jpeg|png)$/.test(pfad) && !pfad.includes("..");
}

/** Klick ins Bild → senkrechte Lage in Prozent (0 % oben), gerundet auf 5 % */
export function fokusAusKlick(y: number, hoehe: number): string {
  if (!(hoehe > 0)) return "50%";
  const p = Math.min(100, Math.max(0, Math.round(((y / hoehe) * 100) / 5) * 5));
  return `${p}%`;
}

// ---------- Spielplätze (wie scraper/spielplaetze/score.py und database/spielplaetze_freischalten.sql) ----------

export const SPERRT_IMMER = ["name_unklar", "kein_stadtteil"] as const;
export const SPERRT_OHNE_BESTAETIGUNG = ["access_private", "gruppe_gemischt"] as const;

export const PRUEF_CODE_TEXT: Record<string, string> = {
  name_unklar: "Name unklar (Stadtdaten)",
  kein_stadtteil: "kein Stadtteil",
  access_private: "laut OSM nicht öffentlich",
  gruppe_gemischt: "gemischte Gruppe (Kinder- und Bolzplatz o. Ä.)",
  bezirk_abweichend: "Bezirk weicht ab",
  zuordnung_mehrdeutig: "OSM-Zuordnung mehrdeutig",
};

export interface SpielplatzStand {
  pruefung?: string[] | null;
  bestaetigt?: string[] | null;
  ausgeschlossen?: string | null;
  freigeschaltet_am?: string | null;
}

/** Codes, die eine Freischaltung gerade sperren */
export function spielplatzSperren(sp: SpielplatzStand | null | undefined): string[] {
  const pruefung = new Set(sp?.pruefung ?? []);
  const bestaetigt = new Set(sp?.bestaetigt ?? []);
  return [
    ...SPERRT_IMMER.filter((c) => pruefung.has(c)),
    ...SPERRT_OHNE_BESTAETIGUNG.filter((c) => pruefung.has(c) && !bestaetigt.has(c)),
  ];
}

export function spielplatzFreischaltbar(aktiv: boolean, sp: SpielplatzStand | null | undefined): boolean {
  return !aktiv && !sp?.ausgeschlossen && spielplatzSperren(sp).length === 0;
}

/** Bestätigen lassen sich alle Codes außer den immer sperrenden */
export function codeBestaetigbar(code: string): boolean {
  return !(SPERRT_IMMER as readonly string[]).includes(code);
}

// ---------- Weihnachtsmärkte (wie database/weihnachtsmaerkte_freischalten.sql) ----------

export interface WmStand {
  top5_rang?: number | null;
  ausgeschlossen?: string | null;
  freigeschaltet_am?: string | null;
  saisons?: Record<string, { von?: string | null; bis?: string | null; zeiten?: unknown }> | null;
}

export function wmHatSaison(wm: WmStand | null | undefined): boolean {
  return Object.values(wm?.saisons ?? {}).some((s) => !!s?.von && !!s?.bis && Array.isArray(s.zeiten) && s.zeiten.length > 0);
}

export function wmFreischaltbar(aktiv: boolean, wm: WmStand | null | undefined): boolean {
  return !aktiv && !wm?.ausgeschlossen && wmHatSaison(wm);
}

// ---------- Clubs ----------

/** Typen, bei denen der Club-Abschnitt erscheint (wie admin_club_setzen) */
export const CLUB_TYPEN = ["club", "kneipe", "restaurant", "cafe", "imbiss"];

export interface ClubStand {
  typ: string;
  club: unknown;
  club_score: unknown;
  club_freigegeben: unknown;
  auch_club: unknown;
  kein_club: unknown;
}

/** Kurzbeschreibung des Club-Stands für die Anzeige */
export function clubStand(o: ClubStand): { imHub: boolean; profil: boolean; score: number | null; freigegeben: boolean } {
  const score = (o.club_score as { gesamt?: unknown } | null)?.gesamt;
  const profil = !!o.club && typeof o.club === "object";
  const imHub = !o.kein_club && (o.typ === "club" || o.auch_club === true);
  return { imHub, profil, score: typeof score === "number" ? score : null, freigegeben: typeof o.club_freigegeben === "string" };
}
