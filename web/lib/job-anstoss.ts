// Mail-Jobs auf GitHub direkt anstoßen statt auf den Zeitplan zu warten. GitHub führt „alle 15 Minuten“ oft
// stundenlang nicht aus (24.11.2026: Newsletter-Bestätigung seit dem Einschalten kein einziger geplanter Lauf).
// Öffentliche Formulare dürfen dabei keine Lawine von Läufen auslösen: höchstens ein Start je ABSTAND_MS und Workflow;
// ein Aufruf in der Sperrzeit wird einmal ans Ende der Sperrzeit gelegt (der Lauf nimmt dann alles Offene mit).
import "server-only";
import { workflowStarten, type WorkflowName } from "@/lib/admin/github";

export const ABSTAND_MS = 5 * 60_000;

export type Anstoss = { art: "jetzt" } | { art: "spaeter"; in_ms: number } | { art: "nichts" };

/** Reine Entscheidung (getestet): jetzt starten, einmal später starten oder nichts (schon geplant). */
export function anstossPlanen(letzterStart: number | null, geplant: boolean, jetzt: number, abstand = ABSTAND_MS): Anstoss {
  if (geplant) return { art: "nichts" };
  if (letzterStart === null || jetzt - letzterStart >= abstand) return { art: "jetzt" };
  return { art: "spaeter", in_ms: abstand - (jetzt - letzterStart) };
}

type Stand = { letzterStart: number | null; geplant: boolean };
const g = globalThis as typeof globalThis & { __dddJobAnstoss?: Map<WorkflowName, Stand> };
const staende = (g.__dddJobAnstoss ??= new Map());

async function starten(name: WorkflowName, inputs: Record<string, string>, s: Stand) {
  const ergebnis = await workflowStarten(name, inputs);
  if (!ergebnis.ok) {
    // Cursor-Prüfung 24.11.2026: Ein gescheiterter Start darf die Sperrzeit nicht belegen – der nächste Aufruf
    // (nächste Anmeldung) stößt sofort wieder an; bis dahin bleibt der Zeitplan.
    s.letzterStart = null;
    console.error(`Job-Anstoß ${name} gescheitert (${ergebnis.meldung}) – nächster Aufruf versucht es sofort, sonst der Zeitplan`);
  }
}

/** Stößt den Workflow an (ohne zu warten); Fehler landen nur im Log, nie beim Nutzer. */
export function jobAnstossen(name: WorkflowName, inputs: Record<string, string>): void {
  const s: Stand = staende.get(name) ?? { letzterStart: null, geplant: false };
  staende.set(name, s);
  const plan = anstossPlanen(s.letzterStart, s.geplant, Date.now());
  if (plan.art === "jetzt") {
    s.letzterStart = Date.now();
    void starten(name, inputs, s);
  } else if (plan.art === "spaeter") {
    s.geplant = true;
    setTimeout(() => {
      s.geplant = false;
      s.letzterStart = Date.now();
      void starten(name, inputs, s);
    }, plan.in_ms).unref?.();
  }
}
