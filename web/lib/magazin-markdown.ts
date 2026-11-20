// Eingeschränktes Markdown für Magazin-Beiträge (Plan T2). Eigener kleiner Parser, keine Bibliothek, kein HTML aus der
// Datenbank: Das Ergebnis ist ein Baum aus reinen Daten, den components/magazin-text.tsx mit React (Escaping) ausgibt.
//
// Erlaubt: ## / ### Überschriften, Absätze, Listen (- oder 1.), **fett**, Links [Text](Ziel), Einbettungen
// {{event:<uuid>}}, {{ort:<slug>}}, {{guide:<slug>}}, {{tag:YYYY-MM-DD}} als eigene Zeile. Alles andere ist Text.
import { istGueltigerTag } from "./datum";

export type Inline =
  | { art: "text"; text: string }
  | { art: "fett"; kinder: Inline[] }
  | { art: "link"; href: string; extern: boolean; kinder: Inline[] };

export type EinbettungsArt = "event" | "ort" | "guide" | "tag";

export type Block =
  | { art: "h2"; id: string; text: string }
  | { art: "h3"; text: string }
  | { art: "absatz"; inhalt: Inline[] }
  | { art: "liste"; nummeriert: boolean; punkte: Inline[][] }
  | { art: "einbettung"; typ: EinbettungsArt; id: string };

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

/** Einbettung prüfen: Art aus der Liste, ID im passenden Format. Sonst null (die Einbettung entfällt). */
export function einbettungPruefen(typ: string, id: string): { typ: EinbettungsArt; id: string } | null {
  switch (typ) {
    case "event":
      return UUID.test(id) ? { typ, id: id.toLowerCase() } : null;
    case "ort":
    case "guide":
      return SLUG.test(id) ? { typ, id } : null;
    case "tag":
      return istGueltigerTag(id) ? { typ, id } : null;
    default:
      return null;
  }
}

/**
 * Linkziel prüfen (Plan T2, Cursor-Prüfung 2 Befund 6): erst einmal dekodieren, dann die Regeln anwenden.
 * Intern nur „/…“ ohne zweiten Schrägstrich am Anfang, ohne Backslash und ohne „..“-Segment; extern nur https://.
 * Dazu mailto: auf Adressen von diesdas.events (z. B. hallo@diesdas.events), ohne Zusätze wie ?subject= (20.11.2026).
 * Gibt das Ziel unverändert zurück (oder null = als Text ausgeben).
 */
export function linkZiel(roh: string): { href: string; extern: boolean } | null {
  const ziel = roh.trim();
  let dekodiert: string;
  try {
    dekodiert = decodeURIComponent(ziel);
  } catch {
    return null;
  }
  // Leerraum nur kodiert (%20), Steuerzeichen nie – auch nicht kodiert
  if (/\s/.test(ziel) || /[\u0000-\u001f\u007f]/.test(dekodiert)) return null;
  if (/^mailto:[a-z0-9._%+-]+@diesdas\.events$/i.test(ziel)) return { href: ziel, extern: false };
  if (/^\/(?![/\\])/.test(dekodiert)) {
    if (dekodiert.includes("\\")) return null;
    const pfad = dekodiert.split(/[?#]/)[0];
    if (pfad.split("/").some((s) => s === ".." || s === ".")) return null;
    return { href: ziel, extern: false };
  }
  if (/^https:\/\//.test(dekodiert) && /^https:\/\//.test(ziel)) {
    try {
      const u = new URL(ziel);
      return u.protocol === "https:" && u.hostname ? { href: u.toString(), extern: true } : null;
    } catch {
      return null;
    }
  }
  return null;
}

/** Inline-Text: **fett** und [Text](Ziel). Unpassende Muster bleiben Text. */
export function inline(text: string): Inline[] {
  const teile: Inline[] = [];
  const muster = /\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)\s]*)\)/g;
  let pos = 0;
  for (const m of text.matchAll(muster)) {
    const start = m.index ?? 0;
    if (start > pos) teile.push({ art: "text", text: text.slice(pos, start) });
    if (m[1] !== undefined) {
      teile.push({ art: "fett", kinder: inline(m[1]) });
    } else {
      const ziel = linkZiel(m[3]);
      if (ziel) teile.push({ art: "link", href: ziel.href, extern: ziel.extern, kinder: inline(m[2]) });
      else teile.push({ art: "text", text: m[0] });
    }
    pos = start + m[0].length;
  }
  if (pos < text.length) teile.push({ art: "text", text: text.slice(pos) });
  return teile;
}

/** Anker-ID aus einer Überschrift: Kleinbuchstaben, Umlaute ausgeschrieben, sonst Bindestriche. */
export function ankerId(text: string): string {
  const s = text
    .toLowerCase()
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .normalize("NFKD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return s || "abschnitt";
}

/** Reiner Text eines Inline-Baums (Überschriften, Inhaltsverzeichnis). */
export function nurText(teile: Inline[]): string {
  return teile.map((t) => (t.art === "text" ? t.text : nurText(t.kinder))).join("");
}

const EINBETTUNG = /^\{\{\s*([a-z]+)\s*:\s*([^}\s]*)\s*\}\}$/;

/** Markdown → Blöcke. */
export function parsen(md: string): Block[] {
  const bloecke: Block[] = [];
  const ids = new Map<string, number>();
  const zeilen = md.replace(/\r\n?/g, "\n").split("\n");
  let absatz: string[] = [];
  let liste: { nummeriert: boolean; punkte: string[] } | null = null;

  const absatzSchliessen = () => {
    if (absatz.length) bloecke.push({ art: "absatz", inhalt: inline(absatz.join(" ")) });
    absatz = [];
  };
  const listeSchliessen = () => {
    if (liste) bloecke.push({ art: "liste", nummeriert: liste.nummeriert, punkte: liste.punkte.map(inline) });
    liste = null;
  };

  for (const roh of zeilen) {
    const zeile = roh.trim();
    if (!zeile) {
      absatzSchliessen();
      listeSchliessen();
      continue;
    }
    const einbettung = zeile.match(EINBETTUNG);
    if (einbettung) {
      absatzSchliessen();
      listeSchliessen();
      const e = einbettungPruefen(einbettung[1], einbettung[2]);
      if (e) bloecke.push({ art: "einbettung", ...e });
      continue;
    }
    const ueberschrift = zeile.match(/^(#{2,3})\s+(.+)$/);
    if (ueberschrift) {
      absatzSchliessen();
      listeSchliessen();
      const text = nurText(inline(ueberschrift[2].trim()));
      if (ueberschrift[1] === "##") {
        const basis = ankerId(text);
        const n = (ids.get(basis) ?? 0) + 1;
        ids.set(basis, n);
        bloecke.push({ art: "h2", id: n === 1 ? basis : `${basis}-${n}`, text });
      } else {
        bloecke.push({ art: "h3", text });
      }
      continue;
    }
    const punkt = zeile.match(/^(?:([-*])|(\d{1,2})\.)\s+(.+)$/);
    if (punkt) {
      absatzSchliessen();
      const nummeriert = punkt[2] !== undefined;
      if (!liste || liste.nummeriert !== nummeriert) {
        listeSchliessen();
        liste = { nummeriert, punkte: [] };
      }
      liste.punkte.push(punkt[3]);
      continue;
    }
    listeSchliessen();
    absatz.push(zeile);
  }
  absatzSchliessen();
  listeSchliessen();
  return bloecke;
}

/** Inhaltsverzeichnis: erst ab drei ##-Überschriften (Plan 5.2 Punkt 6). */
export function inhaltsverzeichnis(bloecke: Block[]): { id: string; text: string }[] {
  const h2 = bloecke.filter((b): b is Extract<Block, { art: "h2" }> => b.art === "h2").map((b) => ({ id: b.id, text: b.text }));
  return h2.length >= 3 ? h2 : [];
}
