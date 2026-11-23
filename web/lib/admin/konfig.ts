// Admin-Bereich – feste Werte (Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 3.2 und 3.3).
// Ohne Abhängigkeiten zu Server-Modulen, damit auch proxy.ts und Tests es laden können.
import type { SitzungsCookieArt } from "../konto/cookies";

/** Eigenes Sitzungs-Cookie, nur für admin.diesdas.events (ohne Domain → host-only), getrennt von ddd_sitzung */
export const ADMIN_COOKIE = "ddd_admin";
export const ADMIN_SITZUNG_SEKUNDEN = 12 * 60 * 60;

export const ADMIN_COOKIE_ART: SitzungsCookieArt = {
  name: ADMIN_COOKIE,
  pfad: "/",
  sameSite: "Strict",
  maxAge: ADMIN_SITZUNG_SEKUNDEN,
};

/** Öffentliche Adresse des Admin-Bereichs (Origin-Prüfung). In web/.env.local überschreibbar. */
export function adminUrl(): string {
  return (process.env.ADMIN_URL ?? "https://admin.diesdas.events").replace(/\/+$/, "");
}

/** Kopf, den nginx je Website fest setzt (Plan 3.2): „admin“ auf admin.diesdas.events, „web“ auf diesdas.events */
export const BEREICH_KOPF = "x-ddd-bereich";

/** Größte erlaubte JSON-Anfrage an /api/admin (Bytes) */
export const ADMIN_BODY_MAX_BYTES = 16 * 1024;
