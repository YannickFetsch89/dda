// Admin-Bereich – „Rückgängig“ im Protokoll (Plan Admin-Dashboard 4.10, Stufe 5a). Nur einfache Feldänderungen:
// event_bearbeiten und ort_bearbeiten (vorher = die geänderten Felder mit altem Wert). Rückgängig geht nur, solange
// niemand die Felder danach noch einmal geändert hat (aktueller Wert = nachher). Rein, getestet in
// web/tests/admin-rest.test.ts; geschrieben wird über dieselben Prüfungen wie beim Bearbeiten.
import { kategorieAusDb } from "../kategorien";

export const RUECKGAENGIG_AKTIONEN = ["event_bearbeiten", "ort_bearbeiten"] as const;

export interface ProtokollEintrag {
  id: string;
  aktion: string;
  tabelle: string | null;
  ziel_id: string | null;
  vorher: unknown;
  nachher: unknown;
}

type Plan =
  | { ok: true; tabelle: "events" | "orte"; id: string; felder: Record<string, unknown>; erwartet: [string, unknown][] }
  | { ok: false; fehler: string };

function gleich(feld: string, a: unknown, b: unknown): boolean {
  const norm = (w: unknown) => {
    if (w === undefined || w === null || w === "") return null;
    if (feld === "uhrzeit" && typeof w === "string") return w.slice(0, 5);
    return typeof w === "object" ? JSON.stringify(w) : w;
  };
  return norm(a) === norm(b);
}

/** Eingabe-Wert wie aus dem Formular (Kategorie als Slug, Uhrzeit HH:MM, null als leerer Text) */
function alsEingabe(feld: string, w: unknown): unknown {
  if (feld === "kategorie" && typeof w === "string") return kategorieAusDb(w);
  if (feld === "uhrzeit" && typeof w === "string") return w.slice(0, 5);
  if (w === null && !["abgesagt", "abgelehnt", "nicht_empfehlen", "aktiv"].includes(feld)) return "";
  return w;
}

/** Plan für „Rückgängig“: Felder aus vorher, nur wenn der aktuelle Stand noch dem nachher entspricht. */
export function rueckgaengigPlan(e: ProtokollEintrag, aktuell: Record<string, unknown> | null): Plan {
  if (!(RUECKGAENGIG_AKTIONEN as readonly string[]).includes(e.aktion)) return { ok: false, fehler: "Diese Aktion lässt sich nicht automatisch rückgängig machen." };
  const vorher = e.vorher && typeof e.vorher === "object" ? (e.vorher as Record<string, unknown>) : null;
  const nachher = e.nachher && typeof e.nachher === "object" ? (e.nachher as Record<string, unknown>) : {};
  if (!vorher || !Object.keys(vorher).length || !e.ziel_id) return { ok: false, fehler: "Im Protokoll fehlen die alten Werte." };
  if (!aktuell) return { ok: false, fehler: "Den Datensatz gibt es nicht mehr." };
  const geaendert = Object.keys(vorher).filter((f) => !gleich(f, aktuell[f], nachher[f]));
  if (geaendert.length) return { ok: false, fehler: `Inzwischen wieder geändert: ${geaendert.join(", ")}. Bitte von Hand anpassen.` };
  const felder = Object.fromEntries(Object.entries(vorher).map(([f, w]) => [f, alsEingabe(f, w)]));
  // Cursor-Prüfung 5a, Befund 4: dieselbe Bedingung noch einmal im UPDATE (kein zweiter Schreibvorgang dazwischen)
  const erwartet: [string, unknown][] = Object.keys(vorher).map((f) => {
    const w = nachher[f];
    if (w === undefined || w === null || w === "") return [f, null];
    return [f, f === "uhrzeit" && typeof w === "string" ? w.slice(0, 5) : w];
  });
  return { ok: true, tabelle: e.aktion === "event_bearbeiten" ? "events" : "orte", id: e.ziel_id, felder, erwartet };
}
