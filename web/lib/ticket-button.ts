// Ticket-Button und Ortswebsite auf der Eventseite (Plan docs/plan-quellen-ausbau-2026-11-23.md, 5.5.3, 6.3, 4.4,
// Schritt W2). Reine Funktionen (getestet in tests/ticket-button.test.ts) und ein schlanker Loader für die
// Quellenliste eines Events.
import { cacheLife, cacheTag } from "next/cache";
import { EVENTS_CACHE_TAG } from "./daten";
import { sichereUrl } from "./orte";
import { RAUSGEGANGEN, TICKETVERKAUF, rangGespeichert } from "./quellen-rang";
import { leseClient } from "./supabase-server";

export interface QuellenEintrag {
  name: string;
  url: string | null;
  rang: number | null;
}

type EventTeil = { quelle_name?: string | null; quelle_url?: string | null; ticket_url?: string | null };

/**
 * Ziel des zweiten Buttons „Tickets“ (5.5.3): zuerst der Ticket-Link, den das Haus selbst nennt (`ticket_url`), sonst
 * der Link einer Ticketverkaufs-Quelle (Rang 2) aus der Quellenliste. Kein zweiter Button, wenn die Hauptquelle selbst
 * ein Ticketanbieter ist (dann ist der Haupt-Button schon der Ticket-Link) oder das Ziel gleich dem Haupt-Button wäre.
 * Auswahl nach Offiziellkeit, nicht nach Provision.
 */
export function ticketZiel(e: EventTeil, quellen: QuellenEintrag[] = []): string | null {
  if (rangGespeichert(e) === TICKETVERKAUF) return null;
  const haupt = e.quelle_url ?? null;
  const eigen = sichereUrl(e.ticket_url);
  if (eigen && eigen !== haupt && eigen !== sichereUrl(haupt)) return eigen;
  if (eigen) return null; // Ticket-Link des Hauses ist schon der Haupt-Button (z. B. Webshop der Tonhalle)
  for (const q of quellen) {
    const url = sichereUrl(q.url);
    if (q.rang === TICKETVERKAUF && url && url !== haupt) return url;
  }
  return null;
}

/**
 * „Website von <Ort>“ (4.4): nur bei Events, die nur Rausgegangen kennt (Hauptquelle Rang 5), und nur, wenn der über
 * `ort_id` zugeordnete Ort eine Website hat. Der Haupt-Button bleibt die Rausgegangen-Seite.
 */
export function ortWebsite(e: EventTeil, ort: { name: string; webseite: string | null } | null): { name: string; url: string } | null {
  if (!ort || rangGespeichert(e) !== RAUSGEGANGEN) return null;
  const url = sichereUrl(ort.webseite);
  return url ? { name: ort.name, url } : null;
}

/** Quellenliste aus der Spalte `quellen` (jsonb) lesen; Unlesbares wird übergangen. */
export function quellenLesen(wert: unknown): QuellenEintrag[] {
  if (!Array.isArray(wert)) return [];
  return wert.flatMap((q) => {
    if (!q || typeof q !== "object") return [];
    const { name, url, rang } = q as Record<string, unknown>;
    if (typeof name !== "string") return [];
    return [{ name, url: typeof url === "string" ? url : null, rang: typeof rang === "number" ? rang : null }];
  });
}

/** Quellenliste eines Events (Spalte `quellen`, Plan 4.3). Fehler oder fehlende Spalte → leere Liste. */
export async function eventQuellenLaden(eventId: string): Promise<QuellenEintrag[]> {
  "use cache";
  cacheTag(EVENTS_CACHE_TAG);
  const client = leseClient();
  if (!client) {
    cacheLife({ stale: 30, revalidate: 60, expire: 120 });
    return [];
  }
  try {
    const { data, error } = await client.from("events").select("quellen").eq("id", eventId).maybeSingle();
    if (error) throw new Error(error.message);
    cacheLife({ stale: 300, revalidate: 600, expire: 3600 });
    return quellenLesen((data as { quellen?: unknown } | null)?.quellen);
  } catch (err) {
    console.warn(`Quellen für Event ${eventId} nicht ladbar: ${err instanceof Error ? err.message : err}`);
    cacheLife({ stale: 30, revalidate: 60, expire: 120 });
    return [];
  }
}
