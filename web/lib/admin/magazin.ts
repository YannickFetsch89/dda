// Admin-Bereich – Magazin (Plan Admin-Dashboard 4.6, Stufe 2): Redaktionsplan, Eingaben prüfen.
// Reine Funktionen, getestet in web/tests/admin-magazin.test.ts. Die Daten kommen aus den SECURITY-DEFINER-Funktionen
// in database/admin_magazin_2026-11-23.sql.
import { plusTage } from "../datum";
import { RUBRIKEN } from "../magazin";
import { eingebetteteEvents } from "./magazin-pruefung";

export interface ListenBeitrag {
  id: string;
  slug: string;
  rubrik: string;
  autor_slug: string;
  titel: string;
  status: "entwurf" | "in_pruefung" | "veroeffentlicht" | "zurueckgezogen";
  gueltig_von: string | null;
  gueltig_bis: string | null;
  veroeffentlicht_am: string | null;
  erstellt_am: string;
  pruefung_ergebnis: string | null;
}

export interface PlanTermin {
  rubrik: "wochenvorschau" | "monats-tipps";
  /** erster Tag der Ausgabe */
  von: string;
  /** Tag, an dem der Job den Entwurf schreibt (Fr vorher bzw. 28. des Vormonats) */
  entwurfAm: string;
  beitrag: ListenBeitrag | null;
  farbe: "gruen" | "gelb" | "rot" | "grau";
  text: string;
}

function wochentag(iso: string): number {
  return new Date(`${iso}T12:00:00Z`).getUTCDay();
}

/**
 * Feste Termine der laufenden Rubriken: die nächsten 6 Wochenvorschauen (Ausgabe ab Montag, Entwurf am Freitag davor)
 * und die nächsten 2 Monats-Tipps (Ausgabe ab dem 1., Entwurf am 28. des Vormonats). Ampel: veröffentlicht grün,
 * Entwurf grün geprüft gelb, sonst rot, sobald der Entwurfstag vorbei ist; vorher grau.
 */
export function redaktionsplan(liste: ListenBeitrag[], heute: string): PlanTermin[] {
  const termine: PlanTermin[] = [];
  const bisMontag = (8 - wochentag(heute)) % 7 || 7;
  // Diese Woche zählt mit, wenn heute Mo–So der laufenden Ausgabe ist: Start beim Montag dieser Woche
  let montag = plusTage(heute, bisMontag - 7);
  for (let i = 0; i < 6; i++, montag = plusTage(montag, 7)) {
    termine.push(termin("wochenvorschau", montag, plusTage(montag, -3), liste, heute));
  }
  // Laufender und nächster Monat (Cursor-Prüfung Stufe 2: auch ein fehlender Entwurf für den laufenden Monat ist rot)
  const [j, m] = [Number(heute.slice(0, 4)), Number(heute.slice(5, 7))];
  for (let i = 0; i < 2; i++) {
    const erster = new Date(Date.UTC(j, m - 1 + i, 1)).toISOString().slice(0, 10);
    const entwurf = new Date(Date.UTC(j, m - 2 + i, 28)).toISOString().slice(0, 10);
    termine.push(termin("monats-tipps", erster, entwurf, liste, heute));
  }
  return termine;
}

function termin(rubrik: PlanTermin["rubrik"], von: string, entwurfAm: string, liste: ListenBeitrag[], heute: string): PlanTermin {
  const passend = liste
    .filter((b) => b.rubrik === rubrik && b.gueltig_von === von && b.status !== "zurueckgezogen")
    .sort((a, b) => ["veroeffentlicht", "in_pruefung", "entwurf"].indexOf(a.status) - ["veroeffentlicht", "in_pruefung", "entwurf"].indexOf(b.status));
  const beitrag = passend[0] ?? null;
  if (beitrag?.status === "veroeffentlicht") return { rubrik, von, entwurfAm, beitrag, farbe: "gruen", text: "veröffentlicht" };
  if (beitrag?.status === "in_pruefung") return { rubrik, von, entwurfAm, beitrag, farbe: "gelb", text: "Entwurf geprüft, wartet auf Freigabe" };
  if (beitrag) return { rubrik, von, entwurfAm, beitrag, farbe: "rot", text: "Entwurf mit Prüfbefund" };
  if (entwurfAm < heute) return { rubrik, von, entwurfAm, beitrag, farbe: "rot", text: "kein Entwurf" };
  return { rubrik, von, entwurfAm, beitrag, farbe: "grau", text: `Entwurf kommt am ${entwurfAm.slice(8, 10)}.${entwurfAm.slice(5, 7)}.` };
}

/** Felder, die das Bearbeiten-Formular schickt (Whitelist wie admin_magazin_speichern, ohne event_ids: die folgen aus dem Text) */
export const MAGAZIN_FELDER = [
  "titel",
  "seo_titel",
  "teaser",
  "inhalt_md",
  "kurzfassung",
  "faq",
  "hero_bild",
  "hero_alt",
  "hero_nachweis",
  "gueltig_von",
  "gueltig_bis",
  "naechste_pruefung",
  "autor_slug",
] as const;

const DATUM = /^\d{4}-\d{2}-\d{2}$/;

/**
 * Prüft die Eingaben gegen die CHECKs der Tabelle (magazin_laengen u. a.), damit der Admin eine lesbare Meldung
 * bekommt statt eines Datenbankfehlers. Ändert sich inhalt_md, werden event_ids aus den Einbettungen neu gesetzt
 * („Events tauschen“ = Einbettungszeile im Text ändern).
 */
export function magazinEingabe(eingabe: Record<string, unknown>): { ok: true; felder: Record<string, unknown> } | { ok: false; fehler: string } {
  const felder: Record<string, unknown> = {};
  for (const [k, w] of Object.entries(eingabe)) {
    if (!(MAGAZIN_FELDER as readonly string[]).includes(k)) return { ok: false, fehler: `Feld „${k}“ ist nicht bearbeitbar.` };
    if (k === "kurzfassung") {
      const liste = Array.isArray(w) ? w.map((x) => String(x).trim()).filter(Boolean) : [];
      if (liste.length && (liste.length < 3 || liste.length > 5)) return { ok: false, fehler: "Auf einen Blick: 3 bis 5 Punkte." };
      felder[k] = liste;
    } else if (k === "faq") {
      const liste = Array.isArray(w) ? (w as { frage?: unknown; antwort?: unknown }[]).filter((f) => String(f.frage ?? "").trim() && String(f.antwort ?? "").trim()) : [];
      felder[k] = liste.length ? liste.map((f) => ({ frage: String(f.frage).trim(), antwort: String(f.antwort).trim() })) : null;
    } else if (k === "gueltig_von" || k === "gueltig_bis" || k === "naechste_pruefung") {
      const s = typeof w === "string" ? w.trim() : "";
      if (s && !DATUM.test(s)) return { ok: false, fehler: `${k}: Datum als JJJJ-MM-TT.` };
      felder[k] = s;
    } else {
      const s = typeof w === "string" ? (k === "inhalt_md" ? w : w.trim()) : "";
      if (k === "titel" && (s.length < 1 || s.length > 90)) return { ok: false, fehler: "Titel: 1 bis 90 Zeichen." };
      if (k === "seo_titel" && s.length > 60) return { ok: false, fehler: "SEO-Titel: höchstens 60 Zeichen." };
      if (k === "teaser" && s && (s.length < 80 || s.length > 160)) return { ok: false, fehler: `Teaser: 80 bis 160 Zeichen (jetzt ${s.length}).` };
      if (k === "inhalt_md" && s.length > 60000) return { ok: false, fehler: "Text zu lang." };
      felder[k] = s;
    }
  }
  if (typeof felder.gueltig_von === "string" && typeof felder.gueltig_bis === "string" && felder.gueltig_von && felder.gueltig_bis && felder.gueltig_von > felder.gueltig_bis) {
    return { ok: false, fehler: "Zeitraum: „von“ liegt nach „bis“." };
  }
  if (typeof felder.inhalt_md === "string") felder.event_ids = eingebetteteEvents(felder.inhalt_md);
  return { ok: true, felder };
}

export function istRubrikWert(w: unknown): boolean {
  return typeof w === "string" && (RUBRIKEN as readonly string[]).includes(w);
}
