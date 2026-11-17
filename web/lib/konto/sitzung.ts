// Nutzerkonten – Sitzung aus der Anfrage lesen, prüfen und bei Bedarf erneuern (Plan 3.2, 3.3).
import "server-only";
import { SITZUNG_COOKIE } from "./konfig";
import { cookieLesen, cookiesLoeschen, istLokal, sitzungDekodieren, sitzungsCookie, type SitzungsWert } from "./cookies";
import { authClientAnfrage, tokenPruefen } from "./clients";
import { tokenLaeuftAb } from "./pruefungen";

export interface Sitzung {
  access: string;
  /** null bei Bearer (spätere App): Erneuern macht dann die App selbst */
  refresh: string | null;
  nutzerId: string;
  email: string | null;
  nurPasswort: boolean;
  quelle: "cookie" | "bearer";
}

export type SitzungsErgebnis =
  | { ok: true; sitzung: Sitzung; setCookies: string[] }
  | { ok: false; setCookies: string[] };

/**
 * Liest die Sitzung aus dem Cookie ddd_sitzung oder aus Authorization: Bearer (Plan 3.3).
 * Läuft das Access-Token in weniger als 60 s ab, erneuert ein anfragebezogener Client es (ohne Timer) und das
 * Cookie wird neu gesetzt. Widerrufene Token-Familie, kaputtes Cookie oder ungültige Signatur → abgemeldet,
 * beide Cookies werden gelöscht (Antwort 401).
 */
export async function sitzungAusAnfrage(request: Request, jetztMs = Date.now()): Promise<SitzungsErgebnis> {
  const lokal = istLokal(request.headers);
  const bearer = /^Bearer\s+(\S+)$/i.exec(request.headers.get("authorization") ?? "")?.[1];
  const roh = cookieLesen(request.headers, SITZUNG_COOKIE);

  if (!roh && bearer) {
    const id = await tokenPruefen(bearer);
    if (!id) return { ok: false, setCookies: [] };
    return {
      ok: true,
      sitzung: { access: bearer, refresh: null, nutzerId: id.sub, email: id.email, nurPasswort: false, quelle: "bearer" },
      setCookies: [],
    };
  }

  if (!roh) return { ok: false, setCookies: [] };
  let wert: SitzungsWert | null = sitzungDekodieren(roh);
  if (!wert) return { ok: false, setCookies: cookiesLoeschen(lokal) };

  const setCookies: string[] = [];
  const zustand = tokenLaeuftAb(wert.access, jetztMs);
  if (zustand === "kaputt") return { ok: false, setCookies: cookiesLoeschen(lokal) };
  if (zustand === "erneuern") {
    const client = authClientAnfrage();
    if (!client) return { ok: false, setCookies: [] };
    const { data, error } = await client.auth.refreshSession({ refresh_token: wert.refresh });
    if (error || !data.session) {
      // z. B. Refresh-Token schon eingelöst (Token-Familie widerrufen, Plan 3.2) → lokal abmelden
      return { ok: false, setCookies: cookiesLoeschen(lokal) };
    }
    wert = {
      access: data.session.access_token,
      refresh: data.session.refresh_token,
      ...(wert.nur_passwort ? { nur_passwort: true as const } : {}),
    };
    setCookies.push(sitzungsCookie(wert, lokal));
  }

  const id = await tokenPruefen(wert.access);
  if (!id) return { ok: false, setCookies: cookiesLoeschen(lokal) };
  return {
    ok: true,
    sitzung: {
      access: wert.access,
      refresh: wert.refresh,
      nutzerId: id.sub,
      email: id.email,
      nurPasswort: wert.nur_passwort === true,
      quelle: "cookie",
    },
    setCookies,
  };
}
