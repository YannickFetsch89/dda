// Admin-Bereich – Vorschlagsarten (Plan Admin-Dashboard 3.5, Stufen 1d und 3c). Geteilt von Liste und Routen.

export const VORSCHLAG_ARTEN = [
  { wert: "dublette", text: "Dubletten", marke: "Dublette" },
  { wert: "gebiet", text: "außerhalb des Gebiets", marke: "Gebiet" },
  { wert: "ortsname", text: "Ortsnamen", marke: "Ortsname" },
  { wert: "ort_id", text: "Ortszuordnung", marke: "Ortszuordnung" },
  { wert: "adresse", text: "Adressen", marke: "Adresse" },
] as const;

/**
 * Arten, die sich gesammelt entscheiden lassen: Sie setzen nur leere bzw. nicht geschützte Felder (redaktion_felder).
 * Dubletten (Zusammenlegen) und Gebiet (Löschen) bleiben Einzelentscheidungen.
 */
export const SAMMEL_ARTEN: readonly string[] = ["ortsname", "ort_id", "adresse"];
