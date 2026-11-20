// Tests Nutzerkonten, Server-Teil (Plan 16.1). Supabase ist überall eine Attrappe – kein Netz.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ── Attrappen ────────────────────────────────────────────────────────────────
type Ergebnis = { data?: unknown; error?: { message?: string; code?: string } | null };

const zustand = vi.hoisted(() => ({
  aufrufe: [] as { tabelle: string; op: string; args: unknown[] }[],
  rpc: [] as { name: string; args: Record<string, unknown> }[],
  antworten: {} as Record<string, (args: unknown[]) => unknown>,
  rpcAntwort: (() => ({ data: [], error: null })) as (name: string, args: Record<string, unknown>) => unknown,
  auth: {} as Record<string, (...a: unknown[]) => unknown>,
  authOptionen: [] as unknown[],
  token: { sub: "11111111-1111-4111-8111-111111111111", email: "a@example.org" } as { sub: string; email: string | null } | null,
}));

function kette(ergebnis: Ergebnis): unknown {
  const p: unknown = new Proxy(function () {}, {
    get(_z, prop) {
      if (prop === "then") return (ok: (v: unknown) => unknown, fehler: (e: unknown) => unknown) => Promise.resolve(ergebnis).then(ok, fehler);
      return () => p;
    },
  });
  return p;
}

function db() {
  return {
    from(tabelle: string) {
      const op = (name: string) => (...args: unknown[]) => {
        zustand.aufrufe.push({ tabelle, op: name, args });
        const f = zustand.antworten[`${tabelle}.${name}`];
        return kette((f ? f(args) : { data: [], error: null }) as Ergebnis);
      };
      return { select: op("select"), update: op("update"), upsert: op("upsert"), insert: op("insert"), delete: op("delete") };
    },
    rpc(name: string, args: Record<string, unknown>) {
      zustand.rpc.push({ name, args });
      return Promise.resolve(zustand.rpcAntwort(name, args));
    },
    auth: new Proxy({}, { get: (_z, prop: string) => zustand.auth[prop] ?? (() => Promise.resolve({ data: {}, error: null })) }),
  };
}

vi.mock("@/lib/konto/clients", () => ({
  ANFRAGE_OPTIONEN: { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } },
  authClientAnfrage: () => db(),
  nutzerClient: () => db(),
  kontoDienstClient: () => db(),
  tokenPruefen: async () => zustand.token,
}));
vi.mock("@/lib/konto/merkliste-events", () => ({ eventsFuerIds: async () => ({ heute: "2026-11-16", events: [] }) }));

import { anfragenImFenster, bremslimitSchluessel, bremslimitZuruecksetzen, zuVieleAnfragen } from "@/lib/formulare";
import { cookiesLoeschen, hinweisCookie, istLokal, sitzungKodieren, sitzungsCookie } from "@/lib/konto/cookies";
import { TEXTVERSIONEN } from "@/lib/konto/konfig";
import {
  adressSchluessel, erlaubteUrspruenge, nachweisImZeitfenster, originErlaubt, passwortPruefen, tokenLaeuftAb, weiterPruefen,
  zielNachAnmeldung,
} from "@/lib/konto/pruefungen";
import { aktivitaetFaellig, aktivitaetZuruecksetzen } from "@/lib/konto/route";
import { uebernahmeVorbereiten, zuVieleIds, type EventStand } from "@/lib/konto/uebernahme";
import { vorliebenPruefen } from "@/lib/konto/vorlieben";

// ── Hilfen ───────────────────────────────────────────────────────────────────
const A = "11111111-1111-4111-8111-111111111111";
const E1 = "aaaaaaaa-0000-4000-8000-000000000001";
const E2 = "aaaaaaaa-0000-4000-8000-000000000002";
const E3 = "aaaaaaaa-0000-4000-8000-000000000003";

function jwt(expSek: number, sub = A): string {
  const b = (o: object) => Buffer.from(JSON.stringify(o)).toString("base64url");
  return `${b({ alg: "ES256", kid: "x" })}.${b({ sub, exp: expSek, email: "a@example.org" })}.sig`;
}
const gueltig = () => jwt(Math.floor(Date.now() / 1000) + 3600);

function profil(teil: Record<string, unknown> = {}) {
  return {
    id: A, anzeigename: null, praeferenzen: {}, onboarding_fertig_am: null, mindestalter_bestaetigt_am: "2026-11-16T10:00:00Z",
    personalisierung: false, sensible_events_erlaubt: false, analyse_erlaubt: false, nutzungsbedingungen_version: "x",
    geburtstagsmail: false, geburtsdatum: null, geburtstagsmail_zuletzt: null, unter16_gesperrt_am: null,
    letzte_aktivitaet_am: null, merkliste_begonnen_am: null, erstellt_am: "2026-11-16T10:00:00Z", rolle: "user",
    vorname: null, nachname: null, ...teil,
  };
}

function anfrage(pfad: string, methode = "POST", body?: unknown, mitSitzung: string | null = null, extra: Record<string, string> = {}): Request {
  const text = body === undefined ? undefined : JSON.stringify(body);
  const headers: Record<string, string> = { origin: "https://diesdas.events", ...extra };
  if (text !== undefined) {
    headers["content-type"] = "application/json";
    headers["content-length"] = String(Buffer.byteLength(text));
  }
  if (mitSitzung) headers.cookie = `ddd_sitzung=${mitSitzung}`;
  return new Request(`https://diesdas.events${pfad}`, { method: methode, headers, body: text });
}
const ctx = (params: Record<string, string> = {}) => ({ params: Promise.resolve(params) });
const sitzung = (nurPasswort = false) =>
  sitzungKodieren({ access: gueltig(), refresh: "r1", ...(nurPasswort ? { nur_passwort: true as const } : {}) });

beforeEach(() => {
  zustand.aufrufe = [];
  zustand.rpc = [];
  zustand.antworten = { "profiles.select": () => ({ data: profil(), error: null }) };
  zustand.rpcAntwort = () => ({ data: [], error: null });
  zustand.auth = {};
  zustand.token = { sub: A, email: "a@example.org" };
  process.env.KONTEN_AKTIV = "1";
  bremslimitZuruecksetzen();
  aktivitaetZuruecksetzen();
});
afterEach(() => {
  delete process.env.KONTEN_AKTIV;
});

// ── Reine Funktionen ─────────────────────────────────────────────────────────
describe("weiterPruefen", () => {
  it("lässt eigene Pfade durch", () => {
    expect(weiterPruefen("/merkliste")).toBe("/merkliste");
    expect(weiterPruefen("/event/kultur/abc?x=1")).toBe("/event/kultur/abc?x=1");
  });
  it.each([
    "//evil.example", "https://evil.example", "/\\evil", "javascript:alert(1)", "/a\u0000b", "%2F%2Fevil.example",
    "%252F%252Fevil.example", "/%5Cevil", "/%255Cevil", "/a//b", "/a%2Fb", "%0d%0a", "%E0%A4%A", "", 7, "/" + "x".repeat(200),
  ])("weist %s ab", (wert) => {
    expect(weiterPruefen(wert)).toBe("/konto");
  });
});

describe("passwortPruefen", () => {
  it("prüft nur die Länge", () => {
    expect(passwortPruefen("123456789")).toBe(false);
    expect(passwortPruefen("1234567890")).toBe(true);
    expect(passwortPruefen("a".repeat(72))).toBe(true);
    expect(passwortPruefen("a".repeat(73))).toBe(false);
    expect(passwortPruefen(" ".repeat(12))).toBe(false);
    expect(passwortPruefen("nurkleinbuchstaben")).toBe(true);
  });
});

describe("Zeitfenster bei der Registrierung", () => {
  const eingang = Date.parse("2026-11-16T12:00:00Z");
  const iso = (ms: number) => new Date(eingang + ms).toISOString();
  it("setzt den Nachweis nur im Fenster −60 s … +5 s", () => {
    expect(nachweisImZeitfenster(iso(-61_000), eingang)).toBe(false);
    expect(nachweisImZeitfenster(iso(-30_000), eingang)).toBe(true);
    expect(nachweisImZeitfenster(iso(4_000), eingang)).toBe(true);
    expect(nachweisImZeitfenster(iso(6_000), eingang)).toBe(false);
    expect(nachweisImZeitfenster(undefined, eingang)).toBe(false);
  });
});

describe("tokenLaeuftAb", () => {
  const jetzt = Date.now();
  it("erneuert 60 s vor Ablauf und erkennt kaputte Tokens", () => {
    expect(tokenLaeuftAb(jwt(Math.floor(jetzt / 1000) + 3600), jetzt)).toBe("gueltig");
    expect(tokenLaeuftAb(jwt(Math.floor(jetzt / 1000) + 30), jetzt)).toBe("erneuern");
    expect(tokenLaeuftAb(jwt(Math.floor(jetzt / 1000) - 10), jetzt)).toBe("erneuern");
    expect(tokenLaeuftAb("kaputt", jetzt)).toBe("kaputt");
  });
});

describe("originErlaubt", () => {
  const h = (o: Record<string, string>) => new Headers(o);
  it("gleicher Ursprung ja, fremder nein, Bearer ohne Cookie ja", () => {
    expect(originErlaubt(h({ origin: "https://diesdas.events", cookie: "ddd_sitzung=x" }))).toBe(true);
    expect(originErlaubt(h({ origin: "https://evil.example", cookie: "ddd_sitzung=x" }))).toBe(false);
    expect(originErlaubt(h({ cookie: "ddd_sitzung=x" }))).toBe(false);
    expect(originErlaubt(h({ authorization: "Bearer abc" }))).toBe(true);
    expect(originErlaubt(h({ authorization: "Bearer abc", cookie: "ddd_sitzung=x", origin: "https://evil.example" }))).toBe(false);
  });
  it("localhost nur, wenn die Anfrage selbst an localhost geht", () => {
    expect(originErlaubt(h({ origin: "http://localhost:3200", host: "localhost:3200" }))).toBe(true);
    expect(originErlaubt(h({ origin: "http://localhost:3200", host: "diesdas.events" }))).toBe(false);
  });
});

describe("Bremslimit-Schlüssel", () => {
  it("nutzt nur den Hash, unabhängig von Groß- und Kleinschreibung", () => {
    expect(adressSchluessel("A@Example.org")).toBe(adressSchluessel("a@example.org"));
    expect(adressSchluessel("a@example.org")).not.toContain("@");
  });
});

describe("Cookies", () => {
  it("Sitzungs-Cookie: HttpOnly, Lax, Pfad /api/konto, 30 Tage, Secure außer lokal", () => {
    const c = sitzungsCookie({ access: "a", refresh: "r" }, false);
    expect(c).toMatch(/^ddd_sitzung=/);
    expect(c).toContain("HttpOnly");
    expect(c).toContain("SameSite=Lax");
    expect(c).toContain("Path=/api/konto");
    expect(c).toContain(`Max-Age=${30 * 24 * 3600}`);
    expect(c).toContain("Secure");
    expect(sitzungsCookie({ access: "a", refresh: "r" }, true)).not.toContain("Secure");
  });
  it("Hinter nginx (Host localhost:3847 mit X-Forwarded-*) gilt die Anfrage nicht als lokal", () => {
    expect(istLokal(new Headers({ host: "localhost:3200" }))).toBe(true);
    const live = new Headers({ host: "localhost:3847", "x-forwarded-proto": "https", "x-real-ip": "203.0.113.5" });
    expect(istLokal(live)).toBe(false);
    expect(istLokal(new Headers({ host: "localhost:3847", "x-forwarded-for": "203.0.113.5" }))).toBe(false);
    expect(istLokal(new Headers({ host: "diesdas.events" }))).toBe(false);
    expect(erlaubteUrspruenge(live)).toEqual(["https://diesdas.events"]);
    expect(erlaubteUrspruenge(new Headers({ host: "localhost:3200" }))).toContain("http://localhost:3200");
  });
  it("Reset-Sitzung: 1 Stunde mit nur_passwort", () => {
    const c = sitzungsCookie({ access: "a", refresh: "r", nur_passwort: true }, false);
    expect(c).toContain("Max-Age=3600");
    const wert = c.split(";")[0].split("=")[1];
    expect(JSON.parse(Buffer.from(wert, "base64url").toString()).nur_passwort).toBe(true);
  });
  it("Hinweis-Cookie: nicht HttpOnly, Pfad /, nur 0 oder 1", () => {
    const c = hinweisCookie("0", false);
    expect(c).toMatch(/^ddd_konto=0;/);
    expect(c).toContain("Path=/;");
    expect(c).not.toContain("HttpOnly");
    expect(hinweisCookie("1", false)).toMatch(/^ddd_konto=1;/);
  });
  it("Löschen setzt beide auf Max-Age=0", () => {
    const [a, b] = cookiesLoeschen(false);
    expect(a).toMatch(/^ddd_sitzung=;.*Max-Age=0/);
    expect(b).toMatch(/^ddd_konto=;.*Max-Age=0/);
  });
});

describe("vorliebenPruefen", () => {
  it("filtert gegen die Whitelists", () => {
    const v = vorliebenPruefen({
      kategorien: ["musik", "sonstiges", "erfunden"],
      unterkategorien: ["kultur/theater", "kultur/erfunden"],
      stadtteile: ["bilk", "medienhafen", "neuss", "atlantis"],
      merkmale: ["kostenlos", "nachts"],
      orte: ["clubs", "zoo"],
    })!;
    expect(v.version).toBe(1);
    expect(v.kategorien).toEqual(["musik"]);
    expect(v.unterkategorien).toEqual(["kultur/theater"]);
    expect(v.stadtteile).toEqual(["bilk", "medienhafen", "neuss"]);
    expect(v.merkmale).toEqual(["kostenlos"]);
    expect(v.orte).toEqual(["clubs"]);
  });
  it("kappt auf 60 Einträge, lehnt Nicht-Objekte ab", () => {
    const viele = vorliebenPruefen({ stadtteile: Array.from({ length: 200 }, (_, i) => (i % 2 ? "bilk" : "flingern-nord")) })!;
    expect(viele.stadtteile.length).toBeLessThanOrEqual(60);
    expect(vorliebenPruefen(null)).toBeNull();
    expect(vorliebenPruefen([1])).toBeNull();
  });
});

describe("uebernahmeVorbereiten", () => {
  const stand = new Map<string, EventStand>([
    [E1, { vorhanden: true, abgelehnt: false, weiterleitungAuf: null }],
    [E2, { vorhanden: true, abgelehnt: true, weiterleitungAuf: E3 }],
    [E3, { vorhanden: true, abgelehnt: false, weiterleitungAuf: null }],
  ]);
  it("filtert, entfernt Doppelte und schreibt Dubletten um", () => {
    const unbekannt = "bbbbbbbb-0000-4000-8000-000000000009";
    const v = uebernahmeVorbereiten([E1, "beispiel-e1", E1, unbekannt, E2], stand);
    expect(v.kandidaten).toEqual([E1, E3]);
    expect(v.ungueltig).toEqual(["beispiel-e1", unbekannt]);
    expect(v.umgeschrieben).toEqual([{ von: E2, nach: E3 }]);
  });
  it("Dublette ohne auflösbares Ziel bleibt unverändert", () => {
    const s = new Map(stand);
    s.set(E2, { vorhanden: true, abgelehnt: true, weiterleitungAuf: null });
    const v = uebernahmeVorbereiten([E2], s);
    expect(v.kandidaten).toEqual([E2]);
    expect(v.umgeschrieben).toEqual([]);
  });
  it("mehr als 1.000 IDs sind zu viele", () => {
    expect(zuVieleIds(Array(1001).fill(E1))).toBe(true);
    expect(zuVieleIds(Array(1000).fill(E1))).toBe(false);
  });
});

describe("zielNachAnmeldung", () => {
  it("Sperre vor allem, dann Alter und Profil, sonst weiter", () => {
    const p = { unter16_gesperrt_am: null, mindestalter_bestaetigt_am: "x", onboarding_fertig_am: "x" };
    expect(zielNachAnmeldung({ ...p, unter16_gesperrt_am: "x" }, "/heute")).toBe("/konto");
    expect(zielNachAnmeldung({ ...p, mindestalter_bestaetigt_am: null }, "/heute")).toBe("/konto/willkommen");
    expect(zielNachAnmeldung({ ...p, onboarding_fertig_am: null }, "/heute")).toBe("/konto/willkommen");
    expect(zielNachAnmeldung(p, "/heute")).toBe("/heute");
    expect(zielNachAnmeldung(p, "//evil")).toBe("/konto");
    // Ohne weiter: Übersicht (20.11.2026)
    expect(zielNachAnmeldung(p, undefined)).toBe("/konto");
  });
});

describe("zuVieleAnfragen mit eigenem Fenster je Schlüssel", () => {
  it("ein 15-Minuten-Aufruf löscht keinen Stundenzähler mehr", () => {
    vi.useFakeTimers();
    try {
      vi.setSystemTime(Date.parse("2026-11-16T10:00:00Z"));
      zuVieleAnfragen("x", "a", 10, 60 * 60_000);
      vi.setSystemTime(Date.parse("2026-11-16T10:30:00Z"));
      zuVieleAnfragen("y", "b", 10, 15 * 60_000); // Bereinigung läuft (mehr als 1 Minute seit der letzten)
      expect(anfragenImFenster("x", "a")).toBe(1);
      vi.setSystemTime(Date.parse("2026-11-16T11:01:00Z"));
      zuVieleAnfragen("y", "b", 10, 15 * 60_000);
      expect(anfragenImFenster("x", "a")).toBe(0);
    } finally {
      vi.useRealTimers();
    }
  });
  it("hält die Zahl der Schlüssel begrenzt", () => {
    for (let i = 0; i < 10_050; i++) zuVieleAnfragen("massen", String(i), 5, 60 * 60_000);
    expect(bremslimitSchluessel()).toBeLessThanOrEqual(10_000);
    expect(anfragenImFenster("massen", "10049")).toBe(1); // zuletzt genutzt bleibt
  });
  it("verhält sich für Newsletter wie bisher", () => {
    for (let i = 0; i < 5; i++) expect(zuVieleAnfragen("newsletter", "1.2.3.4", 5, 60 * 60_000)).toBe(false);
    expect(zuVieleAnfragen("newsletter", "1.2.3.4", 5, 60 * 60_000)).toBe(true);
  });
});

describe("letzte Aktivität", () => {
  it("schreibt höchstens einmal am Tag", () => {
    expect(aktivitaetFaellig(A, "2026-11-16")).toBe(true);
    expect(aktivitaetFaellig(A, "2026-11-16")).toBe(false);
    expect(aktivitaetFaellig(A, "2026-11-17")).toBe(true);
  });
});

describe("Textversionen", () => {
  it("haben die im Plan genannten Kennungen und passen in einwilligungstexte.version (≤ 40)", () => {
    expect(TEXTVERSIONEN.personalisierung).toBe("interessen-2026-11-2");
    // -2: Widerrufssatz per du (19.11.2026)
    expect(TEXTVERSIONEN.sensible_events).toBe("sensible-events-2026-11-2");
    expect(TEXTVERSIONEN.analyse).toBe("analyse-hinweis-2026-11");
    for (const v of Object.values(TEXTVERSIONEN)) expect(v.length).toBeLessThanOrEqual(40);
  });
});

// ── Routen mit Attrappe ──────────────────────────────────────────────────────
type Modul = Record<string, (r: Request, c: unknown) => Promise<Response>>;
const ROUTEN: [string, string, () => Promise<unknown>][] = [
  ["registrieren", "POST", () => import("@/app/api/konto/registrieren/route")],
  ["bestaetigung-erneut", "POST", () => import("@/app/api/konto/bestaetigung-erneut/route")],
  ["anmelden", "POST", () => import("@/app/api/konto/anmelden/route")],
  ["passwort-vergessen", "POST", () => import("@/app/api/konto/passwort-vergessen/route")],
  ["link-pruefen", "POST", () => import("@/app/api/konto/link-pruefen/route")],
  ["passwort-setzen", "POST", () => import("@/app/api/konto/passwort-setzen/route")],
  ["passwort-aendern", "POST", () => import("@/app/api/konto/passwort-aendern/route")],
  ["ich", "GET", () => import("@/app/api/konto/ich/route")],
  ["abmelden", "POST", () => import("@/app/api/konto/abmelden/route")],
  ["abschluss", "POST", () => import("@/app/api/konto/abschluss/route")],
  ["vorlieben", "PUT", () => import("@/app/api/konto/vorlieben/route")],
  ["einstellungen", "PUT", () => import("@/app/api/konto/einstellungen/route")],
  ["merkliste", "GET", () => import("@/app/api/konto/merkliste/route")],
  ["merkliste/uebernehmen", "POST", () => import("@/app/api/konto/merkliste/uebernehmen/route")],
  ["export", "GET", () => import("@/app/api/konto/export/route")],
  ["loeschen", "POST", () => import("@/app/api/konto/loeschen/route")],
  ["stammdaten", "PUT", () => import("@/app/api/konto/stammdaten/route")],
  ["email-aendern", "POST", () => import("@/app/api/konto/email-aendern/route")],
];

describe("Schalter aus", () => {
  it.each(ROUTEN)("/api/konto/%s antwortet 404", async (pfad, methode, laden) => {
    process.env.KONTEN_AKTIV = "0";
    const mod = (await laden()) as Modul;
    const res = await mod[methode](anfrage(`/api/konto/${pfad}`, methode, methode === "GET" ? undefined : {}), ctx());
    expect(res.status).toBe(404);
    expect(zustand.aufrufe).toHaveLength(0);
  });
  it("auch merkliste/[id]", async () => {
    process.env.KONTEN_AKTIV = "0";
    const mod = await import("@/app/api/konto/merkliste/[id]/route");
    expect((await mod.PUT(anfrage(`/api/konto/merkliste/${E1}`, "PUT"), ctx({ id: E1 }))).status).toBe(404);
  });
});

describe("registrieren: neutral, nur ein bestätigtes Konto wird genannt (Entscheidung 17.11.2026)", () => {
  const faelle: [string, () => unknown][] = [
    ["neu", () => ({ data: { user: { id: A, identities: [{}], created_at: new Date().toISOString() }, session: null }, error: null })],
    ["unbestätigt, anderes Passwort", () => ({ data: { user: { id: A, identities: [{}], created_at: "2026-01-01T00:00:00Z" }, session: null }, error: null })],
    ["Supabase nicht erreichbar", () => Promise.reject(new Error("fetch failed"))],
  ];
  const vorhanden: [string, () => unknown][] = [
    ["bestätigt, verschleiert", () => ({ data: { user: { id: A, identities: [], created_at: "2026-01-01T00:00:00Z" }, session: null }, error: null })],
    ["bestätigt, Fehler", () => ({ data: { user: null, session: null }, error: { code: "user_already_exists", message: "User already registered" } })],
  ];
  it.each(vorhanden)("%s → 409 vorhanden, ohne Supabase-Details und ohne Nachweis", async (_name, signUp) => {
    zustand.auth.signUp = signUp as () => unknown;
    const { POST } = await import("@/app/api/konto/registrieren/route");
    const res = await POST(anfrage("/api/konto/registrieren", "POST", { email: "x@example.org", passwort: "langespasswort", alter_ok: true }), ctx());
    expect(res.status).toBe(409);
    const body = await res.json();
    expect(body.code).toBe("vorhanden");
    expect(JSON.stringify(body)).not.toMatch(/user|error|identit/i);
    expect(zustand.rpc).toHaveLength(0);
  });
  it.each(faelle)("%s → 200, gleicher Body", async (_name, signUp) => {
    zustand.auth.signUp = signUp as () => unknown;
    zustand.antworten["profiles.select"] = () => ({ data: { mindestalter_bestaetigt_am: null, nutzungsbedingungen_version: null }, error: null });
    const { POST } = await import("@/app/api/konto/registrieren/route");
    const res = await POST(anfrage("/api/konto/registrieren", "POST", { email: "x@example.org", passwort: "langespasswort", alter_ok: true }), ctx());
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toEqual({ ok: true, meldung: expect.stringContaining("Fast geschafft") });
    expect(JSON.stringify(body)).not.toMatch(/user|error/);
  });
  it("setzt den Nachweis nur bei frischem Konto, über einwilligung_setzen", async () => {
    zustand.auth.signUp = faelle[0][1] as () => unknown;
    zustand.antworten["profiles.select"] = () => ({ data: { mindestalter_bestaetigt_am: null, nutzungsbedingungen_version: null }, error: null });
    const { POST } = await import("@/app/api/konto/registrieren/route");
    await POST(anfrage("/api/konto/registrieren", "POST", { email: "x@example.org", passwort: "langespasswort", alter_ok: true }), ctx());
    expect(zustand.rpc.map((r) => [r.args.art, r.args.handlung, r.args.textversion])).toEqual([
      ["mindestalter", "registrierung", TEXTVERSIONEN.mindestalter],
      ["nutzungsbedingungen", "registrierung", TEXTVERSIONEN.nutzungsbedingungen],
    ]);
    zustand.rpc = [];
    zustand.auth.signUp = faelle[1][1] as () => unknown;
    await POST(anfrage("/api/konto/registrieren", "POST", { email: "y@example.org", passwort: "langespasswort", alter_ok: true }), ctx());
    expect(zustand.rpc).toHaveLength(0);
  });
  it("ohne Alters-Häkchen 400", async () => {
    const { POST } = await import("@/app/api/konto/registrieren/route");
    const res = await POST(anfrage("/api/konto/registrieren", "POST", { email: "x@example.org", passwort: "langespasswort" }), ctx());
    expect(res.status).toBe(400);
  });
});

describe("Bremse beim Anmelden", () => {
  it("nach 5 Fehlversuchen von IP A ohne Supabase-Aufruf abgewiesen, IP B kommt durch", async () => {
    let aufrufe = 0;
    let richtig = false;
    zustand.auth.signInWithPassword = async () => {
      aufrufe++;
      return richtig
        ? { data: { session: { access_token: gueltig(), refresh_token: "r", user: { id: A } } }, error: null }
        : { data: { session: null }, error: { code: "invalid_credentials" } };
    };
    const { POST } = await import("@/app/api/konto/anmelden/route");
    const versuch = (ip: string) =>
      POST(anfrage("/api/konto/anmelden", "POST", { email: "x@example.org", passwort: "falschfalsch" }, null, { "x-real-ip": ip }), ctx());
    for (let i = 0; i < 5; i++) expect((await versuch("1.1.1.1")).status).toBe(400);
    richtig = true;
    const sechster = await versuch("1.1.1.1");
    expect(sechster.status).toBe(400);
    expect((await sechster.json()).fehler).toBe("Mailadresse oder Passwort stimmen nicht.");
    expect(aufrufe).toBe(5);
    const andereIp = await versuch("2.2.2.2");
    expect(andereIp.status).toBe(200);
    expect(andereIp.headers.get("set-cookie")).toContain("ddd_sitzung=");
  });
  it("bildet jeden Fehler außer email_not_confirmed auf dieselbe Meldung ab", async () => {
    zustand.auth.signInWithPassword = async () => ({ data: { session: null }, error: { code: "user_banned", message: "geheim" } });
    const { POST } = await import("@/app/api/konto/anmelden/route");
    const res = await POST(anfrage("/api/konto/anmelden", "POST", { email: "x@example.org", passwort: "falschfalsch" }), ctx());
    const body = await res.json();
    expect(body.fehler).toBe("Mailadresse oder Passwort stimmen nicht.");
    expect(JSON.stringify(body)).not.toContain("geheim");
  });
});

describe("angemeldete Routen", () => {
  it("ohne Sitzung 401", async () => {
    const { GET } = await import("@/app/api/konto/ich/route");
    expect((await GET(anfrage("/api/konto/ich", "GET"), ctx())).status).toBe(401);
  });
  it("Reset-Sitzung: alles außer passwort-setzen und abmelden → 403 passwort_setzen_noetig", async () => {
    const { GET } = await import("@/app/api/konto/ich/route");
    const res = await GET(anfrage("/api/konto/ich", "GET", undefined, sitzung(true)), ctx());
    expect(res.status).toBe(403);
    expect((await res.json()).code).toBe("passwort_setzen_noetig");
  });
  it("fremder Origin mit Cookie → 403", async () => {
    const { POST } = await import("@/app/api/konto/abschluss/route");
    const res = await POST(anfrage("/api/konto/abschluss", "POST", {}, sitzung(), { origin: "https://evil.example" }), ctx());
    expect(res.status).toBe(403);
  });
  it("ohne Mindestalter: merkliste 403 mindestalter_fehlt mit ddd_konto=0, ich erlaubt", async () => {
    zustand.antworten["profiles.select"] = () => ({ data: profil({ mindestalter_bestaetigt_am: null }), error: null });
    const merk = await import("@/app/api/konto/merkliste/route");
    const res = await merk.GET(anfrage("/api/konto/merkliste", "GET", undefined, sitzung()), ctx());
    expect(res.status).toBe(403);
    expect((await res.json()).code).toBe("mindestalter_fehlt");
    expect(res.headers.get("set-cookie")).toContain("ddd_konto=0");
    const ich = await import("@/app/api/konto/ich/route");
    const r2 = await ich.GET(anfrage("/api/konto/ich", "GET", undefined, sitzung()), ctx());
    expect(r2.status).toBe(200);
    expect(r2.headers.get("cache-control")).toBe("private, no-store");
  });
  it("Erneuern: widerrufenes Refresh-Token → 401 und beide Cookies gelöscht", async () => {
    zustand.auth.refreshSession = async () => ({ data: { session: null }, error: { code: "refresh_token_already_used" } });
    const ablauf = sitzungKodieren({ access: jwt(Math.floor(Date.now() / 1000) + 10), refresh: "alt" });
    const { GET } = await import("@/app/api/konto/ich/route");
    const res = await GET(anfrage("/api/konto/ich", "GET", undefined, ablauf), ctx());
    expect(res.status).toBe(401);
    const cookies = res.headers.get("set-cookie") ?? "";
    expect(cookies).toContain("ddd_sitzung=;");
    expect(cookies).toContain("ddd_konto=;");
  });
  it("ich gibt weder rolle noch Kennzeichnungen aus", async () => {
    const { GET } = await import("@/app/api/konto/ich/route");
    const text = await (await GET(anfrage("/api/konto/ich", "GET", undefined, sitzung()), ctx())).text();
    expect(text).not.toMatch(/rolle|sensibel|"grund"|event_sensibel/);
  });
});

// Pflichtangaben (E16), bei jedem Abschluss dabei
const STAMM = { vorname: "Erika", nachname: "Muster", geburtsdatum: "2000-01-01" };

describe("abschluss", () => {
  const ohneAbschluss = () => {
    zustand.antworten["einwilligungen.select"] = () => ({ data: [], error: null });
  };
  it("(a) nein: keine praeferenzen, aber Nachweise für alle Angaben, Version aus Konstanten", async () => {
    ohneAbschluss();
    const { POST } = await import("@/app/api/konto/abschluss/route");
    const res = await POST(
      anfrage("/api/konto/abschluss", "POST", {
        praeferenzen: { kategorien: ["musik"] }, interessen_ok: false, sensibel_ok: false, widerspruch: false,
        geburtstagsmail_ok: false, ...STAMM, textversion: "gefaelscht",
      }, sitzung()),
      ctx(),
    );
    expect(res.status).toBe(200);
    expect(zustand.rpc[0]).toMatchObject({ name: "stammdaten_setzen", args: { vorname: "Erika", nachname: "Muster", datum: "2000-01-01" } });
    expect(zustand.rpc.slice(1).map((r) => [r.args.art, r.args.erteilt, r.args.handlung])).toEqual([
      ["geburtstagsmail", false, "abschlussseite"],
      ["personalisierung", false, "abschlussseite"],
      ["sensible_events", false, "abschlussseite"],
      ["analyse", true, "abschlussseite"],
    ]);
    expect(zustand.rpc.every((r) => r.args.textversion !== "gefaelscht")).toBe(true);
    const updates = zustand.aufrufe.filter((a) => a.tabelle === "profiles" && a.op === "update").map((a) => a.args[0]);
    expect(updates.some((u) => (u as Record<string, unknown>).praeferenzen)).toBe(false);
    expect(updates.some((u) => (u as Record<string, unknown>).onboarding_fertig_am)).toBe(true);
  });
  it("(a) ja: Einwilligung vor dem Speichern der praeferenzen", async () => {
    ohneAbschluss();
    const reihenfolge: string[] = [];
    zustand.rpcAntwort = (_n, a) => (reihenfolge.push(`rpc:${a.art}`), { data: [], error: null });
    zustand.antworten["profiles.update"] = (args) => {
      if ((args[0] as Record<string, unknown>).praeferenzen) reihenfolge.push("praeferenzen");
      return { error: null };
    };
    const { POST } = await import("@/app/api/konto/abschluss/route");
    await POST(anfrage("/api/konto/abschluss", "POST", { praeferenzen: { kategorien: ["musik"] }, interessen_ok: true, ...STAMM }, sitzung()), ctx());
    expect(reihenfolge.indexOf("rpc:personalisierung")).toBeLessThan(reihenfolge.indexOf("praeferenzen"));
  });
  it("Widerspruch → analyse_erlaubt bleibt false", async () => {
    ohneAbschluss();
    const { POST } = await import("@/app/api/konto/abschluss/route");
    await POST(anfrage("/api/konto/abschluss", "POST", { widerspruch: true, ...STAMM }, sitzung()), ctx());
    expect(zustand.rpc.find((r) => r.args.art === "analyse")?.args.erteilt).toBe(false);
  });
  it("Stammdaten unter 16 → Abbruch vor allen anderen Angaben", async () => {
    ohneAbschluss();
    zustand.rpcAntwort = (name) => ({ data: name === "stammdaten_setzen" ? "unter_16" : [], error: null });
    const { POST } = await import("@/app/api/konto/abschluss/route");
    const res = await POST(
      anfrage("/api/konto/abschluss", "POST", { interessen_ok: true, geburtstagsmail_ok: true, ...STAMM, geburtsdatum: "2015-01-01" }, sitzung()),
      ctx(),
    );
    const body = await res.json();
    expect(body.gesperrt).toBe(true);
    expect(zustand.rpc.map((r) => r.name)).toEqual(["stammdaten_setzen"]);
    expect(res.headers.get("set-cookie")).toContain("ddd_konto=0");
  });
  it("Wiederholung: (a) nicht erneut gesetzt, praeferenzen erneut geschrieben", async () => {
    zustand.antworten["einwilligungen.select"] = () => ({
      data: [{ art: "personalisierung" }, { art: "sensible_events" }, { art: "analyse" }, { art: "geburtstagsmail" }],
      error: null,
    });
    zustand.antworten["profiles.select"] = () => ({
      data: profil({ personalisierung: true, analyse_erlaubt: true, vorname: "Erika", nachname: "Muster", geburtsdatum: "2000-01-01" }),
      error: null,
    });
    const { POST } = await import("@/app/api/konto/abschluss/route");
    await POST(anfrage("/api/konto/abschluss", "POST", { praeferenzen: { kategorien: ["musik"] }, interessen_ok: true, ...STAMM }, sitzung()), ctx());
    expect(zustand.rpc).toHaveLength(0);
    expect(zustand.aufrufe.some((a) => a.op === "update" && (a.args[0] as Record<string, unknown>).praeferenzen)).toBe(true);
  });
  it.each([
    [{ ...STAMM, vorname: "  " }, "vorname"],
    [{ ...STAMM, nachname: undefined }, "nachname"],
    [{ ...STAMM, vorname: "<script>" }, "vorname"],
    [{ ...STAMM, geburtsdatum: "2000-02-30" }, "geburtsdatum"],
    [{ vorname: "Erika", nachname: "Muster" }, "geburtsdatum"],
  ])("Pflichtangabe fehlt oder ungültig → 400 ohne Speichern (%o)", async (stamm, code) => {
    ohneAbschluss();
    const { POST } = await import("@/app/api/konto/abschluss/route");
    const res = await POST(anfrage("/api/konto/abschluss", "POST", { interessen_ok: false, ...stamm }, sitzung()), ctx());
    expect(res.status).toBe(400);
    expect((await res.json()).code).toBe(code);
    expect(zustand.rpc).toHaveLength(0);
  });
  it("Namen werden normalisiert (Leerraum)", async () => {
    ohneAbschluss();
    const { POST } = await import("@/app/api/konto/abschluss/route");
    await POST(anfrage("/api/konto/abschluss", "POST", { ...STAMM, vorname: "  Anna   Lena ", nachname: "O’Brien-Müller" }, sitzung()), ctx());
    expect(zustand.rpc[0].args).toMatchObject({ vorname: "Anna Lena", nachname: "O’Brien-Müller" });
  });
});

describe("Mailadresse ändern (17.11.2026)", () => {
  const sitzungsAntwort = { data: { session: { access_token: gueltig(), refresh_token: "r2", user: { id: A } } }, error: null };
  it("prüft das aktuelle Passwort und ruft updateUser mit der neuen Adresse", async () => {
    const aufrufe: unknown[] = [];
    zustand.auth.signInWithPassword = async () => sitzungsAntwort;
    zustand.auth.updateUser = async (a: unknown) => (aufrufe.push(a), { data: {}, error: null });
    const { POST } = await import("@/app/api/konto/email-aendern/route");
    const res = await POST(anfrage("/api/konto/email-aendern", "POST", { neu: " Neu@Example.org ", aktuell: "altespasswort" }, sitzung()), ctx());
    expect(res.status).toBe(200);
    expect(aufrufe).toEqual([{ email: "neu@example.org" }]);
  });
  it("falsches Passwort → 403, keine Änderung", async () => {
    let geaendert = false;
    zustand.auth.signInWithPassword = async () => ({ data: { session: null }, error: { code: "invalid_credentials" } });
    zustand.auth.updateUser = async () => ((geaendert = true), { data: {}, error: null });
    const { POST } = await import("@/app/api/konto/email-aendern/route");
    const res = await POST(anfrage("/api/konto/email-aendern", "POST", { neu: "neu@example.org", aktuell: "falsch" }, sitzung()), ctx());
    expect(res.status).toBe(403);
    expect(geaendert).toBe(false);
  });
  it("gleiche Adresse → 400, vergebene Adresse → 409", async () => {
    const { POST } = await import("@/app/api/konto/email-aendern/route");
    const gleich = await POST(anfrage("/api/konto/email-aendern", "POST", { neu: "a@example.org", aktuell: "x" }, sitzung()), ctx());
    expect(gleich.status).toBe(400);
    zustand.auth.signInWithPassword = async () => sitzungsAntwort;
    zustand.auth.updateUser = async () => ({ data: {}, error: { code: "email_exists" } });
    const vergeben = await POST(anfrage("/api/konto/email-aendern", "POST", { neu: "b@example.org", aktuell: "x" }, sitzung()), ctx());
    expect(vergeben.status).toBe(409);
  });
  it("Link art=email: erster Link ohne Sitzung → Meldung, zweiter mit Sitzung → Cookie", async () => {
    const { POST } = await import("@/app/api/konto/link-pruefen/route");
    const typen: unknown[] = [];
    zustand.auth.verifyOtp = async (a: unknown) => (typen.push((a as { type: string }).type), { data: { session: null, user: null }, error: null });
    const halb = await POST(anfrage("/api/konto/link-pruefen", "POST", { token_hash: "abc", art: "email" }), ctx());
    expect(halb.status).toBe(200);
    expect((await halb.json()).meldung).toContain("andere Adresse");
    expect(halb.headers.get("set-cookie") ?? "").not.toContain("ddd_sitzung=");
    zustand.auth.verifyOtp = async (a: unknown) => (typen.push((a as { type: string }).type), sitzungsAntwort);
    const fertig = await POST(anfrage("/api/konto/link-pruefen", "POST", { token_hash: "abc", art: "email" }), ctx());
    expect((await fertig.json()).meldung).toContain("neue Mailadresse");
    expect(fertig.headers.get("set-cookie")).toContain("ddd_sitzung=");
    expect(typen).toEqual(["email_change", "email_change"]);
  });
});

describe("Export als Auskunft nach Art. 15", () => {
  it("enthält die Angaben nach Art. 15 und keine Kennzeichnung sensibel", async () => {
    zustand.auth.admin = { getUserById: async () => ({ data: { user: null }, error: null }) } as unknown as () => unknown;
    const { GET } = await import("@/app/api/konto/export/route");
    const res = await GET(anfrage("/api/konto/export", "GET", undefined, sitzung()), ctx());
    expect(res.status).toBe(200);
    const text = await res.text();
    const daten = JSON.parse(text);
    expect(Object.keys(daten.auskunft_art_15)).toEqual(expect.arrayContaining([
      "zwecke_und_rechtsgrundlagen", "empfaenger", "drittland", "speicherdauer", "herkunft", "deine_rechte",
    ]));
    expect(text).not.toMatch(/sensibel/i);
    expect(res.headers.get("content-disposition")).toContain("diesdas-auskunft.json");
  });
});

describe("stammdaten", () => {
  it("ändert Name und Datum über stammdaten_setzen", async () => {
    zustand.antworten["profiles.select"] = () => ({
      data: profil({ onboarding_fertig_am: "2026-11-17T10:00:00Z", vorname: "Erika", nachname: "Muster", geburtsdatum: "2000-01-01" }),
      error: null,
    });
    const { PUT } = await import("@/app/api/konto/stammdaten/route");
    const res = await PUT(anfrage("/api/konto/stammdaten", "PUT", { ...STAMM, nachname: "Neu" }, sitzung()), ctx());
    expect(res.status).toBe(200);
    expect(zustand.rpc.map((r) => [r.name, r.args.nachname])).toEqual([["stammdaten_setzen", "Neu"]]);
  });
  it("unverändert → kein Datenbankaufruf", async () => {
    zustand.antworten["profiles.select"] = () => ({
      data: profil({ vorname: "Erika", nachname: "Muster", geburtsdatum: "2000-01-01" }),
      error: null,
    });
    const { PUT } = await import("@/app/api/konto/stammdaten/route");
    const res = await PUT(anfrage("/api/konto/stammdaten", "PUT", STAMM, sitzung()), ctx());
    expect(res.status).toBe(200);
    expect(zustand.rpc).toHaveLength(0);
  });
  it("Datum unter 16 → gesperrt, ddd_konto=0", async () => {
    zustand.rpcAntwort = () => ({ data: "unter_16", error: null });
    const { PUT } = await import("@/app/api/konto/stammdaten/route");
    const res = await PUT(anfrage("/api/konto/stammdaten", "PUT", { ...STAMM, geburtsdatum: "2015-01-01" }, sitzung()), ctx());
    expect((await res.json()).gesperrt).toBe(true);
    expect(res.headers.get("set-cookie")).toContain("ddd_konto=0");
  });
});

describe("einstellungen", () => {
  it("analyse vor onboarding_fertig_am → 409", async () => {
    const { PUT } = await import("@/app/api/konto/einstellungen/route");
    const res = await PUT(anfrage("/api/konto/einstellungen", "PUT", { art: "analyse", erteilt: false }, sitzung()), ctx());
    expect(res.status).toBe(409);
  });
  it("Geburtstagsmail ohne gespeichertes Datum → 400", async () => {
    zustand.rpcAntwort = () => ({ data: null, error: { message: "geburtsdatum_fehlt" } });
    const { PUT } = await import("@/app/api/konto/einstellungen/route");
    const res = await PUT(anfrage("/api/konto/einstellungen", "PUT", { art: "geburtstagsmail", erteilt: true }, sitzung()), ctx());
    expect(res.status).toBe(400);
  });
  it("Widerruf (b) gibt zurueck_aufs_geraet", async () => {
    zustand.rpcAntwort = () => ({ data: [E1], error: null });
    const { PUT } = await import("@/app/api/konto/einstellungen/route");
    const res = await PUT(anfrage("/api/konto/einstellungen", "PUT", { art: "sensible_events", erteilt: false }, sitzung()), ctx());
    expect((await res.json()).zurueck_aufs_geraet).toEqual([E1]);
  });
  it("Mindestalter gesetzt → ddd_konto=1", async () => {
    zustand.antworten["profiles.select"] = () => ({ data: profil({ mindestalter_bestaetigt_am: null }), error: null });
    const { PUT } = await import("@/app/api/konto/einstellungen/route");
    const res = await PUT(anfrage("/api/konto/einstellungen", "PUT", { art: "mindestalter", erteilt: true }, sitzung()), ctx());
    expect(res.status).toBe(200);
    expect(res.headers.get("set-cookie")).toContain("ddd_konto=1");
  });
});

describe("merkliste/[id]", () => {
  it("sensibles Event ohne Einwilligung → 200 gespeichert: geraet, ohne Grund", async () => {
    zustand.antworten["merkliste.upsert"] = () => ({ error: { message: "nur_geraet", code: "P0001" } });
    const { PUT } = await import("@/app/api/konto/merkliste/[id]/route");
    const res = await PUT(anfrage(`/api/konto/merkliste/${E1}`, "PUT", undefined, sitzung()), ctx({ id: E1 }));
    expect(res.status).toBe(200);
    const text = await res.text();
    expect(JSON.parse(text)).toEqual({ ok: true, gespeichert: "geraet" });
    expect(text).not.toMatch(/sensibel|grund/);
  });
  it("keine UUID → 400", async () => {
    const { PUT } = await import("@/app/api/konto/merkliste/[id]/route");
    expect((await PUT(anfrage("/api/konto/merkliste/beispiel-e1", "PUT", undefined, sitzung()), ctx({ id: "beispiel-e1" }))).status).toBe(400);
  });
});

describe("Übernahme", () => {
  it("413 bei mehr als 1.000 IDs, ohne zu schreiben", async () => {
    const { POST } = await import("@/app/api/konto/merkliste/uebernehmen/route");
    const ids = Array.from({ length: 1001 }, (_, i) => `aaaaaaaa-0000-4000-8000-${String(i).padStart(12, "0")}`);
    const res = await POST(anfrage("/api/konto/merkliste/uebernehmen", "POST", { ids }, sitzung()), ctx());
    expect(res.status).toBe(413);
    expect(zustand.aufrufe.some((a) => a.tabelle === "merkliste" && a.op === "upsert")).toBe(false);
  });
  it("sensible Events ohne (b) → bleiben_auf_geraet, nicht eingefügt", async () => {
    zustand.antworten["events.select"] = () => ({ data: [{ id: E1, abgelehnt: false }, { id: E2, abgelehnt: false }], error: null });
    zustand.antworten["event_sensibel.select"] = () => ({ data: [{ event_id: E2 }], error: null });
    let eingefuegt: unknown[] = [];
    zustand.antworten["merkliste.upsert"] = (args) => ((eingefuegt = args[0] as unknown[]), { error: null });
    const { POST } = await import("@/app/api/konto/merkliste/uebernehmen/route");
    const res = await POST(anfrage("/api/konto/merkliste/uebernehmen", "POST", { ids: [E1, E2] }, sitzung()), ctx());
    const body = await res.json();
    expect(body.bleiben_auf_geraet).toEqual([E2]);
    expect(eingefuegt.map((z) => (z as { event_id: string }).event_id)).toEqual([E1]);
    expect(JSON.stringify(body)).not.toMatch(/sensibel|grund/);
  });
});

describe("Keine Passwörter in Logs", () => {
  it("ein Fehler beim Anmelden schreibt weder Passwort noch Body in die Konsole", async () => {
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    zustand.auth.signInWithPassword = async () => {
      throw new Error("kaputt geheimes-passwort-123");
    };
    const { POST } = await import("@/app/api/konto/anmelden/route");
    const res = await POST(anfrage("/api/konto/anmelden", "POST", { email: "x@example.org", passwort: "geheimes-passwort-123" }), ctx());
    expect(res.status).toBe(500);
    const alles = [...log.mock.calls, ...warn.mock.calls].flat().join(" ");
    expect(alles).not.toContain("geheimes-passwort-123");
    log.mockRestore();
    warn.mockRestore();
  });
});
