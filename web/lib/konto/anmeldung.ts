// Nutzerkonten – gemeinsamer Abschluss nach Anmeldung, Bestätigung und Passwortwechsel (Plan 3.2, 5.1).
import "server-only";
import { hinweisCookie, sitzungsCookie } from "./cookies";
import { nutzerClient } from "./clients";
import { zielNachAnmeldung } from "./pruefungen";
import { hinweisFuer, profilLaden, type KontoProfil } from "./route";

export interface NeueSitzung {
  access_token: string;
  refresh_token: string;
  user?: { id: string } | null;
}

/**
 * Setzt Sitzungs- und Hinweis-Cookie und bestimmt das Ziel. Das Profil wird mit dem neuen Token über RLS gelesen.
 * Ohne lesbares Profil gilt das Konto als „Alter fehlt“ (ddd_konto=0, Ziel /konto/willkommen).
 */
export async function sitzungStarten(
  session: NeueSitzung,
  lokal: boolean,
  weiter: unknown,
): Promise<{ setCookies: string[]; ziel: string; profil: KontoProfil | null }> {
  const setCookies = [sitzungsCookie({ access: session.access_token, refresh: session.refresh_token }, lokal)];
  let profil: KontoProfil | null = null;
  const db = nutzerClient(session.access_token);
  const id = session.user?.id;
  if (db && id) {
    const p = await profilLaden(db, id);
    profil = p === "fehler" ? null : p;
  }
  setCookies.push(hinweisCookie(hinweisFuer(profil), lokal));
  return { setCookies, ziel: zielNachAnmeldung(profil, weiter), profil };
}

/** Eingeschränkte Reset-Sitzung (Plan 5.1 Schritt 9): 1 Stunde, nur_passwort, KEIN Hinweis-Cookie. */
export function resetSitzungCookie(session: NeueSitzung, lokal: boolean): string {
  return sitzungsCookie({ access: session.access_token, refresh: session.refresh_token, nur_passwort: true }, lokal);
}
