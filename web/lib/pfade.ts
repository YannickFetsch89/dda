// Kanonische Pfade – ohne React-Abhängigkeiten, damit Server- und Client-Komponenten und proxy.ts sie teilen.
import type { DddEvent } from "./typen";

/** Kanonische Event-URL: /event/<kategorie>/<slug>. Nur Events ohne Slug behalten /event/<uuid>. */
export function eventPfad(e: Pick<DddEvent, "id" | "kategorie" | "slug">): string {
  if (e.slug) return `/event/${encodeURIComponent(e.kategorie)}/${encodeURIComponent(e.slug)}`;
  return `/event/${encodeURIComponent(e.id)}`;
}
