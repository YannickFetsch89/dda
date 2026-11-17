// Merkliste mit Konto – reine Logik ohne Browser (Plan 5.4, 5.5, 5.8, Tests 16.1). Der Browser-Teil steht in
// lib/konto/merk-store.ts und ruft nur diese Funktionen auf.

export type WarteEintrag = { op: "merken" | "entfernen"; id: string; zeit: number };

/** Warteschlange auf eine Liste anwenden (Spiegel im Kontomodus bzw. Geräteliste beim Abmelden/401). */
export function warteschlangeAnwenden(liste: string[], schlange: WarteEintrag[]): string[] {
  let ergebnis = [...liste];
  for (const e of schlange) {
    if (e.op === "merken") {
      if (!ergebnis.includes(e.id)) ergebnis.push(e.id);
    } else {
      ergebnis = ergebnis.filter((x) => x !== e.id);
    }
  }
  return ergebnis;
}

/** IDs, deren letzter Eintrag in der Warteschlange „entfernen“ ist (noch nicht beim Server angekommen). */
export function offeneLoeschungen(schlange: WarteEintrag[]): string[] {
  const letzte = new Map<string, WarteEintrag["op"]>();
  for (const e of schlange) letzte.set(e.id, e.op);
  return [...letzte].filter(([, op]) => op === "entfernen").map(([id]) => id);
}

/** Vereinigung ohne Doppelte, Reihenfolge der ersten Liste zuerst. */
export const vereinigen = (a: string[], b: string[]) => [...a, ...b.filter((x) => !a.includes(x))];

/**
 * Sichtbare Merkliste (Plan 5.5): eine Liste ohne Unterscheidung, auch für Events, die nur auf dem Gerät liegen
 * dürfen (ddd-merkliste-geraet, E13).
 */
export function sichtbareListe(z: {
  kontomodus: boolean;
  geraet: string[];
  spiegel: string[];
  schlange: WarteEintrag[];
  nurGeraet: string[];
}): string[] {
  const basis = z.kontomodus ? warteschlangeAnwenden(z.spiegel, z.schlange) : z.geraet;
  return vereinigen(basis, z.nurGeraet);
}

export interface UebernahmeAntwort {
  konto: string[];
  umgeschrieben: { von: string; nach: string }[];
  ungueltig: string[];
  nicht_uebernommen: string[];
  bleiben_auf_geraet: string[];
  uebernommen: number;
  vollstaendig: boolean;
}

/**
 * Plan 5.4 Schritt 8: Aus der Geräteliste wird NUR entfernt, was im Konto steht, eine aufgelöste Dublette, deren
 * Ziel im Konto steht, was ungültig ist und was auf dem Gerät bleiben muss (wandert nach ddd-merkliste-geraet).
 * Alles andere bleibt, vor allem nicht_uebernommen.
 */
export function geraetelisteNachUebernahme(
  geraet: string[],
  nurGeraet: string[],
  antwort: UebernahmeAntwort,
): { geraet: string[]; nurGeraet: string[] } {
  const konto = new Set(antwort.konto);
  const raus = new Set<string>([...antwort.ungueltig, ...antwort.bleiben_auf_geraet]);
  for (const id of geraet) if (konto.has(id)) raus.add(id);
  for (const u of antwort.umgeschrieben) if (konto.has(u.nach)) raus.add(u.von);
  return {
    geraet: geraet.filter((id) => !raus.has(id)),
    nurGeraet: vereinigen(nurGeraet, antwort.bleiben_auf_geraet),
  };
}

/** Plan 5.4 Schritte 1–3: automatisch übernehmen, nachfragen oder nichts zu tun. */
export function uebernahmeEntscheiden(
  geraet: string[],
  konto: string[],
  merklisteBegonnenAm: string | null,
): { art: "automatisch" | "nachfrage" | "nichts"; nurAufGeraet: string[] } {
  const kontoSet = new Set(konto);
  const nurAufGeraet = geraet.filter((id) => !kontoSet.has(id));
  if (!nurAufGeraet.length) return { art: "nichts", nurAufGeraet };
  return { art: merklisteBegonnenAm ? "nachfrage" : "automatisch", nurAufGeraet };
}

/** Herz im Kontomodus: Spiegel sofort ändern, Eintrag anhängen (Plan 5.5). */
export function herzImKonto(spiegel: string[], schlange: WarteEintrag[], id: string, jetzt: number) {
  const sichtbar = warteschlangeAnwenden(spiegel, schlange).includes(id);
  return { schlange: [...schlange, { op: sichtbar ? "entfernen" : "merken", id, zeit: jetzt } as WarteEintrag] };
}

export type ServerAntwort =
  | { art: "ok"; gespeichert?: "konto" | "geraet" }
  | { art: "abgemeldet" }
  | { art: "mindestalter" }
  | { art: "verwerfen" } // 400/404/409: Eintrag verwerfen, Herz springt zurück
  | { art: "spaeter" }; // Netz oder 5xx: Eintrag bleibt

/** HTTP-Antwort einer Herz-Anfrage einordnen (Plan 5.5 „Fehler“). */
export function herzAntwortEinordnen(status: number | null, code?: string, gespeichert?: string): ServerAntwort {
  if (status === null || status >= 500 || status === 429) return { art: "spaeter" };
  if (status === 401) return { art: "abgemeldet" };
  if (status === 403 && code === "mindestalter_fehlt") return { art: "mindestalter" };
  if (status === 403) return { art: "abgemeldet" };
  if (status >= 400) return { art: "verwerfen" };
  return { art: "ok", gespeichert: gespeichert === "geraet" ? "geraet" : "konto" };
}

/** Vorbei oder kommend? (E9) Mehrtägige Events mit datum_bis ab heute gelten als kommend. */
export function istVorbei(e: { datum: string; datum_bis: string | null }, heute: string): boolean {
  return (e.datum_bis ?? e.datum) < heute;
}

/** Merkliste aufteilen: kommende nach Datum, vergangene getrennt (neueste zuerst). */
export function merklisteAufteilen<T extends { datum: string; datum_bis: string | null }>(events: T[], heute: string) {
  const kommend = events.filter((e) => !istVorbei(e, heute)).sort((a, b) => a.datum.localeCompare(b.datum));
  const vorbei = events.filter((e) => istVorbei(e, heute)).sort((a, b) => b.datum.localeCompare(a.datum));
  return { kommend, vorbei };
}
