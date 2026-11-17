// Nutzerkonten – Pflichtangaben Vorname, Nachname, Geburtsdatum aus dem Body prüfen (E16).
// Gemeinsam für /api/konto/abschluss und /api/konto/stammdaten.
import "server-only";
import type { Stammdaten } from "./einwilligungen";
import { geburtsdatumGueltig, nameNormal } from "./pruefungen";
import { kontoAntwort } from "./route";

export function stammdatenAusBody(b: Record<string, unknown>): { daten: Stammdaten; fehler?: undefined } | { fehler: Response } {
  const vorname = nameNormal(b.vorname);
  if (!vorname) return { fehler: kontoAntwort(400, { fehler: "Bitte gib deinen Vornamen ein.", code: "vorname" }) };
  const nachname = nameNormal(b.nachname);
  if (!nachname) return { fehler: kontoAntwort(400, { fehler: "Bitte gib deinen Nachnamen ein.", code: "nachname" }) };
  if (!geburtsdatumGueltig(b.geburtsdatum)) {
    return { fehler: kontoAntwort(400, { fehler: "Bitte gib ein gültiges Geburtsdatum ein.", code: "geburtsdatum" }) };
  }
  return { daten: { vorname, nachname, geburtsdatum: b.geburtsdatum } };
}
