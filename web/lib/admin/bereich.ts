// Admin-Bereich – Trennung von der Website (Plan Admin-Dashboard 3.2).
// Next sieht hinter nginx nur den Host localhost:3847, für diesdas.events und admin.diesdas.events gleich. Deshalb
// setzen beide nginx-Websites den Kopf X-DDD-Bereich fest (proxy_set_header ersetzt einen vom Browser
// mitgeschickten Wert). Fehlt der Kopf, gilt die Anfrage als Website: Der Admin-Bereich ist dann geschlossen.
import { BEREICH_KOPF } from "./konfig";

/**
 * Kommt die Anfrage über admin.diesdas.events? Zum Entwickeln zusätzlich mit ADMIN_LOKAL=1, aber NUR unter `next dev`.
 * Live läuft immer `next start` (NODE_ENV=production), dort greift der Schalter nie. Die Proxy-Köpfe taugen dafür
 * nicht: Live ist der Host ebenfalls localhost:3847, und Next setzt im Proxy selbst X-Forwarded-Köpfe
 * (lokal gemessen 23.11.2026, istLokal war dort auch ohne nginx falsch).
 */
export function istAdminBereich(headers: Headers): boolean {
  if (headers.get(BEREICH_KOPF)?.trim().toLowerCase() === "admin") return true;
  return process.env.NODE_ENV === "development" && process.env.ADMIN_LOKAL === "1";
}

/** Pfade des Admin-Bereichs (Seiten und API) */
export function istAdminPfad(pfad: string): boolean {
  return pfad === "/admin" || pfad.startsWith("/admin/") || pfad === "/api/admin" || pfad.startsWith("/api/admin/");
}

/** Seiten, die ohne Admin-Cookie erreichbar sein müssen */
export const ADMIN_OFFENE_SEITEN = new Set(["/admin/anmelden"]);
