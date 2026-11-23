// Newsletter bestätigen und abmelden (Plan Admin-Dashboard 4.9, Stufe 4) – gemeinsam für die Seiten-Routen und die
// One-Click-Abmeldung (RFC 8058). Schreiben mit dem Service-Schlüssel (schreibClient), nur über ein gültiges Token.
import "server-only";
import { schreibClient } from "./formulare";
import { newsletterTokenPruefen } from "./newsletter";

export type Ergebnis = { status: number; daten: Record<string, unknown> };

const UNGUELTIG: Ergebnis = { status: 400, daten: { fehler: "Dieser Link ist ungültig oder abgelaufen." } };
const NICHT_VERFUEGBAR: Ergebnis = { status: 503, daten: { fehler: "Das geht gerade nicht. Bitte versuch es später noch einmal." } };

/** Bestätigt die Anmeldung (bestaetigt_am, nur beim ersten Mal). Unbekannte ID (gelöscht, abgemeldet) → ungültig. */
export async function bestaetigen(token: unknown): Promise<Ergebnis> {
  const id = newsletterTokenPruefen(token, "bestaetigen");
  if (!id) return UNGUELTIG;
  const db = schreibClient();
  if (!db) return NICHT_VERFUEGBAR;
  const { data, error } = await db.from("newsletter_anmeldungen").select("id, bestaetigt_am").eq("id", id).maybeSingle();
  if (error) {
    console.error(`Newsletter bestätigen: nicht lesbar (${error.code ?? "fehler"})`);
    return NICHT_VERFUEGBAR;
  }
  if (!data) return UNGUELTIG;
  if (!data.bestaetigt_am) {
    const { error: f2 } = await db.from("newsletter_anmeldungen").update({ bestaetigt_am: new Date().toISOString() }).eq("id", id).is("bestaetigt_am", null);
    if (f2) {
      console.error(`Newsletter bestätigen: nicht gespeichert (${f2.code ?? "fehler"})`);
      return NICHT_VERFUEGBAR;
    }
  }
  return { status: 200, daten: { ok: true, meldung: "Danke! Deine Anmeldung ist bestätigt. Du bekommst jetzt unseren Newsletter." } };
}

/** Meldet ab und löscht die Adresse sofort (Datenschutzerklärung Abschnitt 11). Schon gelöscht → ebenfalls Erfolg. */
export async function abmelden(token: unknown): Promise<Ergebnis> {
  const id = newsletterTokenPruefen(token, "abmelden");
  if (!id) return UNGUELTIG;
  const db = schreibClient();
  if (!db) return NICHT_VERFUEGBAR;
  const { error } = await db.from("newsletter_anmeldungen").delete().eq("id", id);
  if (error) {
    console.error(`Newsletter abmelden: nicht gelöscht (${error.code ?? "fehler"})`);
    return NICHT_VERFUEGBAR;
  }
  return { status: 200, daten: { ok: true, meldung: "Erledigt. Deine Adresse ist gelöscht, du bekommst keine Mails mehr von uns." } };
}
