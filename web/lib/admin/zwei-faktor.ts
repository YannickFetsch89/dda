// Admin-Bereich – Zwei-Faktor (TOTP) über Supabase Auth MFA (Plan Admin-Dashboard 3.3, E2).
// Jeder Aufruf baut einen eigenen Auth-Client ohne Speicher und ohne Timer (Lehre vom 06.11.2026, clients.ts) und
// setzt darin die Sitzung aus dem Cookie.
import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { authClientAnfrage } from "../konto/clients";
import type { Sitzung } from "../konto/sitzung";

const FAKTOR_NAME = "dies.das Admin";

async function clientMitSitzung(sitzung: Sitzung): Promise<SupabaseClient | null> {
  const client = authClientAnfrage();
  if (!client || !sitzung.refresh) return null;
  const { error } = await client.auth.setSession({ access_token: sitzung.access, refresh_token: sitzung.refresh });
  return error ? null : client;
}

export type ZweiFaktorStart =
  | { art: "code"; faktorId: string }
  | { art: "einrichten"; faktorId: string; qr: string; geheimnis: string }
  | { art: "fehler" };

/**
 * Gibt es schon einen bestätigten TOTP-Faktor, wird nur der Code abgefragt. Sonst werden unbestätigte Reste
 * entfernt und ein neuer Faktor angelegt (QR-Code für die Authenticator-App).
 */
export async function zweiFaktorStarten(sitzung: Sitzung): Promise<ZweiFaktorStart> {
  const client = await clientMitSitzung(sitzung);
  if (!client) return { art: "fehler" };
  const { data, error } = await client.auth.mfa.listFactors();
  if (error || !data) return { art: "fehler" };
  const bestaetigt = data.totp?.[0];
  if (bestaetigt) return { art: "code", faktorId: bestaetigt.id };

  for (const f of data.all ?? []) {
    if (f.factor_type === "totp" && f.status !== "verified") {
      await client.auth.mfa.unenroll({ factorId: f.id });
    }
  }
  const neu = await client.auth.mfa.enroll({ factorType: "totp", friendlyName: FAKTOR_NAME });
  if (neu.error || !neu.data) return { art: "fehler" };
  return { art: "einrichten", faktorId: neu.data.id, qr: neu.data.totp.qr_code, geheimnis: neu.data.totp.secret };
}

/** Prüft den Code. Bei Erfolg kommen neue Tokens mit aal2 zurück. */
export async function zweiFaktorPruefen(
  sitzung: Sitzung,
  faktorId: string,
  code: string,
): Promise<{ access: string; refresh: string } | null> {
  const client = await clientMitSitzung(sitzung);
  if (!client) return null;
  const { data, error } = await client.auth.mfa.challengeAndVerify({ factorId: faktorId, code });
  if (error || !data?.access_token || !data.refresh_token) return null;
  return { access: data.access_token, refresh: data.refresh_token };
}

/** Meldet die Sitzung beim Auth-Server ab (nur diese Sitzung). */
export async function adminAbmelden(sitzung: Sitzung): Promise<void> {
  const client = await clientMitSitzung(sitzung);
  if (client) await client.auth.signOut({ scope: "local" });
}
