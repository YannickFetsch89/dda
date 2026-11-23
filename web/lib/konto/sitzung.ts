// Nutzerkonten – Sitzung aus der Anfrage lesen, prüfen und bei Bedarf erneuern (Plan 3.2, 3.3).
import "server-only";
import {
  cookieLesen,
  cookiesLoeschen,
  istLokal,
  KONTO_COOKIE_ART,
  sitzungDekodieren,
  sitzungsCookie,
  sitzungsCookieLoeschen,
  type SitzungsCookieArt,
  type SitzungsWert,
} from "./cookies";
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
export async function sitzungAusAnfrage(
  request: Request,
  jetztMs = Date.now(),
  art: SitzungsCookieArt = KONTO_COOKIE_ART,
): Promise<SitzungsErgebnis> {
  const lokal = istLokal(request.headers);
  // Bearer (spätere App) nur für die Konto-Sitzung; der Admin-Bereich kennt nur sein Cookie (Plan Admin-Dashboard 3.3)
  const konto = art === KONTO_COOKIE_ART;
  const loeschen = () => (konto ? cookiesLoeschen(lokal) : [sitzungsCookieLoeschen(lokal, art)]);
  const bearer = konto ? /^Bearer\s+(\S+)$/i.exec(request.headers.get("authorization") ?? "")?.[1] : undefined;
  const roh = cookieLesen(request.headers, art.name);

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
  if (!wert) return { ok: false, setCookies: loeschen() };

  const setCookies: string[] = [];
  const zustand = tokenLaeuftAb(wert.access, jetztMs);
  if (zustand === "kaputt") return { ok: false, setCookies: loeschen() };
  if (zustand === "erneuern") {
    const client = authClientAnfrage();
    if (!client) return { ok: false, setCookies: [] };
    const { data, error } = await client.auth.refreshSession({ refresh_token: wert.refresh });
    if (error || !data.session) {
      // z. B. Refresh-Token schon eingelöst (Token-Familie widerrufen, Plan 3.2) → lokal abmelden
      return { ok: false, setCookies: loeschen() };
    }
    wert = {
      access: data.session.access_token,
      refresh: data.session.refresh_token,
      ...(wert.nur_passwort ? { nur_passwort: true as const } : {}),
    };
    setCookies.push(sitzungsCookie(wert, lokal, art));
  }

  const id = await tokenPruefen(wert.access);
  if (!id) return { ok: false, setCookies: loeschen() };
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
