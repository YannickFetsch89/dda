// Admin-Bereich – Origin-Prüfung (Plan Admin-Dashboard 3.3, Cursor-Prüfung 1, Befund 8).
// Eigene Prüfung statt originErlaubt aus web/lib/konto/pruefungen.ts: Die Konto-Prüfung erlaubt nur SITE_URL und
// kennt nur ddd_sitzung. Hier gilt nur der Ursprung des Admin-Bereichs, und jede schreibende Anfrage braucht ihn.
import { istLokal } from "../konto/cookies";
import { adminUrl } from "./konfig";

export function adminUrspruenge(headers: Headers): string[] {
  const admin = adminUrl();
  if (!istLokal(headers)) return [admin];
  const host = (headers.get("host") ?? "").toLowerCase();
  return [admin, "http://localhost:3100", "http://localhost:3200", `http://${host}`];
}

/** Schreibende Admin-Anfragen nur mit Origin des Admin-Bereichs (CSRF-Schutz zusätzlich zu SameSite=Strict). */
export function adminOriginErlaubt(headers: Headers): boolean {
  const origin = headers.get("origin");
  return !!origin && adminUrspruenge(headers).includes(origin.replace(/\/+$/, ""));
}
