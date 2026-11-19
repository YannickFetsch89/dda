// Bildadressen über den eigenen Server (Bild-Proxy) – nutzbar in Server- und Client-Komponenten.
import type { DddEvent } from "./typen";

/**
 * Bild, das auf unserem eigenen Server liegt (web/public/ort-bilder/<hub>/…), z. B. vom Veranstalter geliefert
 * (Auftraggeber 17.11.2026). Nur dieses enge Muster – alles andere läuft weiter über den Bild-Proxy.
 */
// Nicht unter /guides/<hub>/: dort prüft proxy.ts jeden Pfad als Detailseite (Bilder wären live 404, 18.11.2026)
const LOKALES_BILD = /^\/ort-bilder\/[a-z0-9-]+\/[a-z0-9-]+\.(webp|jpg|png)$/;

export function lokalesBild(bildUrl: string | null | undefined): string | null {
  return typeof bildUrl === "string" && LOKALES_BILD.test(bildUrl) ? bildUrl : null;
}


/**
 * Bildadresse eines Events über den eigenen Server (/bild/event/<id>) statt direkt beim Veranstalter –
 * so gehen keine Besucherdaten an fremde Server. Beispieldaten (ohne echte ID) haben keine Bilder.
 */
export function eventBildUrl(e: DddEvent): string | null {
  // Eigenes Foto aus web/public (z. B. Rennbahn-Weihnacht, 19.11.2026): direkt, ohne Umweg über den Proxy
  const lokal = lokalesBild(e.bild_url);
  if (lokal) return lokal;
  if (!e.bild_url || !/^[0-9a-f-]{36}$/i.test(e.id)) return null;
  return `/bild/event/${e.id}`;
}
