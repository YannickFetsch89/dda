// Ziel nach der Anmeldung prüfen (Plan 5.1 Schritt 14). Eigene Datei ohne Node-Abhängigkeiten: auch im Browser nutzbar.

const STANDARD_ZIEL = "/merkliste";

/**
 * Prüft das Ziel nach der Anmeldung (`weiter`, Plan 5.1 Schritt 14). Gegen offene Redirects:
 * höchstens zweimal dekodieren, dann muss der ganze Wert ein Pfad auf dieser Website sein.
 */
export function weiterPruefen(wert: unknown): string {
  if (typeof wert !== "string" || !wert) return STANDARD_ZIEL;
  // Kodierte Schrägstriche bzw. ein kodiertes % sind auf keiner Stufe erlaubt, auch nicht im Rohwert
  if (/%2f|%5c|%25/i.test(wert)) return STANDARD_ZIEL;
  let pfad = wert;
  for (let i = 0; i < 2; i++) {
    let neu: string;
    try {
      neu = decodeURIComponent(pfad);
    } catch {
      return STANDARD_ZIEL;
    }
    if (neu === pfad) break;
    pfad = neu;
  }
  if (pfad.length > 200) return STANDARD_ZIEL;
  if (!pfad.startsWith("/") || pfad.startsWith("//")) return STANDARD_ZIEL;
  if (pfad.includes("//") || pfad.includes("\\")) return STANDARD_ZIEL;
  if (/%2f|%5c|%25/i.test(pfad)) return STANDARD_ZIEL;
  if (/[\u0000-\u001F\u007F\s]/.test(pfad)) return STANDARD_ZIEL;
  return pfad;
}
