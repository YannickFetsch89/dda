// Übernahme der lokalen Merkliste ins Konto (Plan 5.4 Schritte 4–7). Die Prüfung der IDs ist eine reine
// Funktion mit eingereichten Nachschlage-Daten, damit sie ohne Datenbank testbar ist.
import { UEBERNAHME_MAX_IDS } from "./konfig";
import { uuidGueltig } from "./pruefungen";

export interface EventStand {
  /** existiert in events (auch abgelehnt) */
  vorhanden: boolean;
  abgelehnt: boolean;
  /** bei abgelehnter Dublette mit Weiterleitung: Ziel-Event-ID, falls sich der Pfad auflösen lässt */
  weiterleitungAuf: string | null;
}

export interface Vorbereitung {
  /** IDs in Reihenfolge der Geräteliste, Dubletten schon umgeschrieben, ohne Doppelte */
  kandidaten: string[];
  umgeschrieben: { von: string; nach: string }[];
  ungueltig: string[];
}

/** Zu viele IDs? Dann 413 ohne Schreiben (Plan 5.4 Schritt 4). */
export const zuVieleIds = (ids: unknown[]) => ids.length > UEBERNAHME_MAX_IDS;

/**
 * Schritt 5: UUID-Format, Doppelte raus, beispiel-* und unbekannte IDs → ungueltig. Abgelehnte Dublette mit
 * auflösbarer Weiterleitung → auf das behaltene Event umschreiben; sonst Ursprungs-ID unverändert übernehmen.
 */
export function uebernahmeVorbereiten(ids: unknown[], stand: ReadonlyMap<string, EventStand>): Vorbereitung {
  const kandidaten: string[] = [];
  const umgeschrieben: { von: string; nach: string }[] = [];
  const ungueltig: string[] = [];
  const gesehen = new Set<string>();

  for (const roh of ids) {
    if (typeof roh !== "string") continue;
    const id = roh.trim();
    if (gesehen.has(id)) continue;
    gesehen.add(id);
    if (!uuidGueltig(id)) {
      ungueltig.push(id);
      continue;
    }
    const s = stand.get(id.toLowerCase());
    if (!s?.vorhanden) {
      ungueltig.push(id);
      continue;
    }
    if (s.abgelehnt && s.weiterleitungAuf && s.weiterleitungAuf !== id) {
      umgeschrieben.push({ von: id, nach: s.weiterleitungAuf });
      if (!kandidaten.includes(s.weiterleitungAuf)) kandidaten.push(s.weiterleitungAuf);
      continue;
    }
    if (!kandidaten.includes(id)) kandidaten.push(id);
  }
  return { kandidaten, umgeschrieben, ungueltig };
}

/** Pfad /event/<kategorie>/<slug> → slug (für die Auflösung von Weiterleitungszielen). */
export function slugAusEventPfad(ziel: string | null | undefined): string | null {
  const m = /^\/event\/[a-z0-9-]+\/([a-z0-9-]+)\/?$/i.exec(ziel ?? "");
  return m ? m[1] : null;
}
