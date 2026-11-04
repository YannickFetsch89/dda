// Bildadressen über den eigenen Server (Bild-Proxy) – nutzbar in Server- und Client-Komponenten.
import type { DddEvent } from "./typen";

/**
 * Bildadresse eines Events über den eigenen Server (/bild/event/<id>) statt direkt beim Veranstalter –
 * so gehen keine Besucherdaten an fremde Server. Beispieldaten (ohne echte ID) haben keine Bilder.
 */
export function eventBildUrl(e: DddEvent): string | null {
  if (!e.bild_url || !/^[0-9a-f-]{36}$/i.test(e.id)) return null;
  return `/bild/event/${e.id}`;
}
