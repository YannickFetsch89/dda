// Nutzerkonten – gemeinsamer Rahmen für alle Routen unter /api/konto (Plan 6, 11).
// Reihenfolge je Anfrage: Schalter → Origin/JSON → Größe → Body → Sitzung → Reset-Sperre → Bremslimit →
// Profil → Mindestalter → Aktivität → Route. Jede Antwort: Cache-Control private, no-store.
import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { absenderIp, zuGross, zuVieleAnfragen } from "../formulare";
import { BODY_MAX_BYTES, kontenAktiv, MELDUNG } from "./konfig";
import { hinweisCookie, istLokal } from "./cookies";
import { nutzerClient } from "./clients";
import { istJson, originErlaubt } from "./pruefungen";
import { sitzungAusAnfrage, type Sitzung } from "./sitzung";

/** Spalten aus profiles, die die Routen brauchen (nie rolle nach außen geben) */
export const PROFIL_SPALTEN =
  "id, anzeigename, praeferenzen, onboarding_fertig_am, mindestalter_bestaetigt_am, personalisierung, " +
  "sensible_events_erlaubt, analyse_erlaubt, nutzungsbedingungen_version, geburtstagsmail, geburtsdatum, " +
  "geburtstagsmail_zuletzt, unter16_gesperrt_am, letzte_aktivitaet_am, merkliste_begonnen_am, erstellt_am, rolle, " +
  "vorname, nachname"; // E16: braucht database/konten_stammdaten_2026-11-17.sql

export interface KontoProfil {
  id: string;
  anzeigename: string | null;
  praeferenzen: Record<string, unknown>;
  onboarding_fertig_am: string | null;
  mindestalter_bestaetigt_am: string | null;
  personalisierung: boolean;
  sensible_events_erlaubt: boolean;
  analyse_erlaubt: boolean;
  nutzungsbedingungen_version: string | null;
  geburtstagsmail: boolean;
  geburtsdatum: string | null;
  geburtstagsmail_zuletzt: string | null;
  unter16_gesperrt_am: string | null;
  letzte_aktivitaet_am: string | null;
  merkliste_begonnen_am: string | null;
  erstellt_am: string;
  rolle: "admin" | "user";
  vorname: string | null;
  nachname: string | null;
}

export interface KontoKontext {
  request: Request;
  ip: string;
  lokal: boolean;
  body: Record<string, unknown>;
  /** Nur bei Routen mit Anmeldung gesetzt */
  sitzung: Sitzung | null;
  profil: KontoProfil | null;
  db: SupabaseClient | null;
  /** Zusätzliche Set-Cookie-Zeilen (Anmelden, Abmelden …) */
  setCookies: string[];
  /** Hinweis-Cookie am Ende NICHT setzen (Abmelden, Löschen, Reset-Sitzung) */
  ohneHinweis: boolean;
}

export interface KontoOptionen {
  /** Braucht eine gültige Sitzung */
  anmeldung: boolean;
  /** Erwartet einen JSON-Body (POST/PUT mit Daten) */
  json?: boolean;
  /** Ändernde Methode: Origin-Prüfung bei Cookie (CSRF, 11.2) */
  aendernd?: boolean;
  maxBytes?: number;
  /** Auch ohne Mindestalter erlaubt (Plan 5.3: ich, einstellungen, abmelden, export, loeschen, passwort-*) */
  ohneMindestalter?: boolean;
  /** Auch mit eingeschränkter Reset-Sitzung erlaubt (passwort-setzen, abmelden) */
  resetErlaubt?: boolean;
  /** Bremslimit je Nutzer (mit Anmeldung) bzw. je IP (ohne) */
  limit?: { name: string; max: number; fensterMs: number };
}

const STUNDE = 60 * 60 * 1000;
export const ZEIT = { STUNDE, VIERTELSTUNDE: 15 * 60 * 1000 };

/** JSON-Antwort mit Cache-Control: private, no-store */
export function kontoAntwort(status: number, daten: Record<string, unknown>, setCookies: string[] = []): Response {
  const headers = new Headers({ "Cache-Control": "private, no-store" });
  for (const c of setCookies) headers.append("Set-Cookie", c);
  return new Response(JSON.stringify(daten), {
    status,
    headers: (headers.set("Content-Type", "application/json; charset=utf-8"), headers),
  });
}

// Letzte Aktivität höchstens einmal am Tag je Konto schreiben (Plan 4.1). Merker im Speicher des Prozesses.
const aktivMerker = new Map<string, string>();
export function aktivitaetFaellig(nutzerId: string, heute: string): boolean {
  if (aktivMerker.get(nutzerId) === heute) return false;
  aktivMerker.delete(nutzerId);
  aktivMerker.set(nutzerId, heute);
  if (aktivMerker.size > 20_000) aktivMerker.delete(aktivMerker.keys().next().value!);
  return true;
}
export const aktivitaetZuruecksetzen = () => aktivMerker.clear();

const berlinHeute = () => new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Berlin" }).format(new Date());

async function aktivitaetMerken(db: SupabaseClient, nutzerId: string) {
  const heute = berlinHeute();
  if (!aktivitaetFaellig(nutzerId, heute)) return;
  const { error } = await db
    .from("profiles")
    .update({ letzte_aktivitaet_am: new Date().toISOString() })
    .eq("id", nutzerId)
    .or(`letzte_aktivitaet_am.is.null,letzte_aktivitaet_am.lt.${heute}`);
  if (error) console.error(`Konto: letzte Aktivität nicht gespeichert (${error.code})`);
}

/** Profil der angemeldeten Person über den Nutzer-Client (RLS: nur die eigene Zeile). */
export async function profilLaden(db: SupabaseClient, nutzerId: string): Promise<KontoProfil | null | "fehler"> {
  const { data, error } = await db.from("profiles").select(PROFIL_SPALTEN).eq("id", nutzerId).maybeSingle();
  if (error) {
    // 42P01/42703 = Tabelle/Spalte fehlt (Migration noch nicht gelaufen) → 503
    console.error(`Konto: Profil nicht lesbar (${error.code})`);
    return "fehler";
  }
  return (data as unknown as KontoProfil) ?? null;
}

/** Hinweis-Cookie passend zum Profil: „1“ nur mit Alters-Häkchen (Plan 3.2). */
export const hinweisFuer = (p: KontoProfil | null) => (p?.mindestalter_bestaetigt_am ? "1" : "0") as "0" | "1";

type Handler = (ctx: KontoKontext, routenKontext: { params: Promise<Record<string, string>> }) => Promise<Response>;

/** Baut eine Route mit allen gemeinsamen Prüfungen. */
export function kontoRoute(opt: KontoOptionen, handler: Handler) {
  return async (request: Request, routenKontext: { params: Promise<Record<string, string>> }): Promise<Response> => {
    // Header zuerst lesen: Damit ist die Route nie vorgerendert, auch nicht mit Schalter aus (Cache Components)
    const lokal = istLokal(request.headers);
    const ip = absenderIp(request.headers);
    if (!kontenAktiv()) return kontoAntwort(404, { fehler: "Nicht gefunden." });

    try {
      if ((opt.aendernd || opt.json) && !originErlaubt(request.headers)) {
        return kontoAntwort(403, { fehler: MELDUNG.ungueltig, code: "origin" });
      }
      let body: Record<string, unknown> = {};
      if (opt.json) {
        if (!istJson(request.headers)) return kontoAntwort(415, { fehler: MELDUNG.ungueltig });
        if (zuGross(request, opt.maxBytes ?? BODY_MAX_BYTES)) return kontoAntwort(413, { fehler: MELDUNG.ungueltig });
        try {
          const roh = await request.json();
          if (!roh || typeof roh !== "object" || Array.isArray(roh)) throw new Error("kein Objekt");
          body = roh as Record<string, unknown>;
        } catch {
          return kontoAntwort(400, { fehler: MELDUNG.ungueltig });
        }
      }

      const ctx: KontoKontext = {
        request, ip, lokal, body, sitzung: null, profil: null, db: null, setCookies: [], ohneHinweis: false,
      };

      if (opt.anmeldung) {
        const s = await sitzungAusAnfrage(request);
        if (!s.ok) return kontoAntwort(401, { fehler: "Nicht angemeldet.", code: "abgemeldet" }, s.setCookies);
        ctx.sitzung = s.sitzung;
        ctx.setCookies.push(...s.setCookies);
        if (s.sitzung.nurPasswort && !opt.resetErlaubt) {
          return kontoAntwort(403, { fehler: "Bitte leg zuerst ein neues Passwort fest.", code: "passwort_setzen_noetig" }, ctx.setCookies);
        }
      }

      if (opt.limit) {
        const schluessel = ctx.sitzung ? `nutzer:${ctx.sitzung.nutzerId}` : `ip:${ip}`;
        if (zuVieleAnfragen(`konto-${opt.limit.name}`, schluessel, opt.limit.max, opt.limit.fensterMs)) {
          return kontoAntwort(429, { fehler: MELDUNG.zuViele, code: "zu_viele" }, ctx.setCookies);
        }
      }

      if (ctx.sitzung && !ctx.sitzung.nurPasswort) {
        ctx.db = nutzerClient(ctx.sitzung.access);
        if (!ctx.db) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar }, ctx.setCookies);
        const profil = await profilLaden(ctx.db, ctx.sitzung.nutzerId);
        if (profil === "fehler") return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar }, ctx.setCookies);
        if (!profil) return kontoAntwort(401, { fehler: "Nicht angemeldet.", code: "abgemeldet" }, ctx.setCookies);
        ctx.profil = profil;
        if (!opt.ohneMindestalter && !profil.mindestalter_bestaetigt_am) {
          return kontoAntwort(
            403,
            { fehler: "Bitte bestätige zuerst dein Alter.", code: "mindestalter_fehlt" },
            [...ctx.setCookies, hinweisCookie("0", lokal)],
          );
        }
        await aktivitaetMerken(ctx.db, ctx.sitzung.nutzerId);
      }

      const antwort = await handler(ctx, routenKontext);
      for (const c of ctx.setCookies) antwort.headers.append("Set-Cookie", c);
      if (ctx.profil && !ctx.ohneHinweis) antwort.headers.append("Set-Cookie", hinweisCookie(hinweisFuer(ctx.profil), lokal));
      antwort.headers.set("Cache-Control", "private, no-store");
      return antwort;
    } catch (err) {
      // Nie den Body loggen (Passwörter), nur die Fehlerart
      console.error(`Konto-Route ${new URL(request.url).pathname} fehlgeschlagen: ${err instanceof Error ? err.name : "unbekannt"}`);
      return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt. Bitte versuch es später noch einmal." });
    }
  };
}

/** Supabase-Fehlermeldung aus einer RPC/Trigger-Ausnahme lesen (z. B. „nur_geraet“, „merkliste_voll“). */
export function dbFehlercode(fehler: { message?: string } | null | undefined): string | null {
  const m = fehler?.message?.trim();
  return m && /^[a-z0-9_]+$/.test(m) ? m : null;
}
