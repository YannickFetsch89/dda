// Geburtstagsmail (Plan docs/plan-geburtstagsmail-2026-11-20.md, Abschnitt 5): Token, Abmelde-Routen, interne Tipps-Route.
// Supabase, Event-Pool und Merkliste-Events sind Attrappen – kein Netz.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { EventPool } from "@/lib/typen";

const zustand = vi.hoisted(() => ({
  profil: { geburtstagsmail: true } as Record<string, unknown> | null,
  profile: [] as Record<string, unknown>[],
  merkliste: [] as Record<string, unknown>[],
  sensibel: [] as { event_id: string }[],
  sensibelFehler: false,
  merklisteFehler: false,
  rpc: [] as { name: string; args: Record<string, unknown> }[],
  pool: null as unknown as EventPool,
}));

/** Abfrage-Kette mit `.eq(spalte, wert)` als Filter auf Zeilen; alle anderen Methoden geben die Kette zurück. */
function kette(ergebnis: { data: unknown; error: unknown }): unknown {
  const filter: [string, unknown][] = [];
  const aufloesen = () => {
    if (!Array.isArray(ergebnis.data) || !filter.length) return ergebnis;
    const zeilen = (ergebnis.data as Record<string, unknown>[]).filter((z) => filter.every(([s, w]) => !(s in z) || z[s] === w));
    return { ...ergebnis, data: zeilen };
  };
  const p: unknown = new Proxy(function () {}, {
    get(_z, prop) {
      if (prop === "then") return (ok: (v: unknown) => unknown, f: (e: unknown) => unknown) => Promise.resolve(aufloesen()).then(ok, f);
      if (prop === "maybeSingle") return () => Promise.resolve({ data: zustand.profil, error: null });
      if (prop === "eq") return (spalte: string, wert: unknown) => { filter.push([spalte, wert]); return p; };
      return () => p;
    },
  });
  return p;
}
function db() {
  return {
    from(tabelle: string) {
      const daten =
        tabelle === "profiles" ? { data: zustand.profile, error: null }
        : tabelle === "merkliste" ? (zustand.merklisteFehler ? { data: null, error: { code: "x" } } : { data: zustand.merkliste, error: null })
        : tabelle === "event_sensibel" ? (zustand.sensibelFehler ? { data: null, error: { code: "x" } } : { data: zustand.sensibel, error: null })
        : { data: [], error: null };
      return { select: () => kette(daten) };
    },
    rpc: (name: string, args: Record<string, unknown>) => {
      zustand.rpc.push({ name, args });
      return Promise.resolve({ data: [], error: null });
    },
  };
}

vi.mock("@/lib/konto/clients", () => ({
  ANFRAGE_OPTIONEN: {},
  authClientAnfrage: () => db(),
  nutzerClient: () => db(),
  kontoDienstClient: () => db(),
  tokenPruefen: async () => null,
}));
vi.mock("@/lib/daten", () => ({ eventPoolLaden: async () => zustand.pool }));
vi.mock("@/lib/konto/merkliste-events", () => ({
  eventsFuerIds: async (ids: string[]) => {
    const karte = new Map(zustand.pool.alle.map((e) => [e.id, e]));
    return { heute: zustand.pool.heute, events: ids.map((id) => karte.get(id)).filter(Boolean) };
  },
}));

import { bremslimitZuruecksetzen } from "@/lib/formulare";
import { geburtstagToken, geburtstagTokenPruefen } from "@/lib/konto/geburtstag";
import { TEXTVERSIONEN } from "@/lib/konto/konfig";
import { sensibelCacheLeeren } from "@/lib/konto/mein-bereich";
import { ev } from "./hilfen";

const ID = "11111111-1111-4111-8111-111111111111";
const B = "22222222-2222-4222-8222-222222222222";
// Derselbe Vektor steht in tests/test_geburtstag_mails.py (Python erzeugt, TypeScript prüft)
const VEKTOR = "11111111-1111-4111-8111-111111111111.BRfJlKb2M3AvQu-zT11zVD367NArUYwl-_3hz0aCAEc";
const HEUTE = "2026-11-20";
const ctx = (params: Record<string, string> = {}) => ({ params: Promise.resolve(params) });

const musik = ev({ id: "aaaaaaaa-0000-4000-8000-000000000001", titel: "Jazz im Keller", datum: HEUTE, ort: "zakk", kategorie: "musik", uhrzeit: "20:00" });
const kultur = ev({ id: "aaaaaaaa-0000-4000-8000-000000000002", titel: "Vernissage", datum: HEUTE, ort: "Kunsthalle", kategorie: "kultur", uhrzeit: "18:00" });
const sensibel = ev({ id: "aaaaaaaa-0000-4000-8000-000000000003", titel: "Gottesdienst mit Chor", datum: HEUTE, ort: "Gemeindesaal", kategorie: "musik", uhrzeit: "19:00" });
const morgen = ev({ id: "aaaaaaaa-0000-4000-8000-000000000004", titel: "Konzert morgen", datum: "2026-11-21", ort: "Tonhalle", kategorie: "musik" });

beforeEach(() => {
  process.env.KONTEN_AKTIV = "1";
  process.env.GEBURTSTAG_TOKEN_SCHLUESSEL = "testschluessel";
  process.env.GEBURTSTAG_JOB_SCHLUESSEL = "jobschluessel";
  zustand.profil = { geburtstagsmail: true };
  zustand.profile = [];
  zustand.merkliste = [];
  zustand.sensibel = [{ event_id: sensibel.id }];
  zustand.sensibelFehler = false;
  zustand.merklisteFehler = false;
  zustand.rpc = [];
  const events = [musik, kultur, sensibel, morgen];
  zustand.pool = { heute: HEUTE, jetzt: `${HEUTE}T08:00:00Z`, events, alle: events, quelle: "supabase", fehler: null };
  bremslimitZuruecksetzen();
  sensibelCacheLeeren();
});
afterEach(() => {
  delete process.env.KONTEN_AKTIV;
  delete process.env.GEBURTSTAG_TOKEN_SCHLUESSEL;
  delete process.env.GEBURTSTAG_JOB_SCHLUESSEL;
});

describe("Abmelde-Token (G4)", () => {
  it("gleicher Vektor wie der Python-Job", () => {
    expect(geburtstagToken(ID, "testschluessel")).toBe(VEKTOR);
    expect(geburtstagTokenPruefen(VEKTOR, "testschluessel")).toBe(ID);
  });
  it("fälschungssicher", () => {
    const [, mac] = VEKTOR.split(".");
    expect(geburtstagTokenPruefen(VEKTOR, "anderer")).toBeNull();
    expect(geburtstagTokenPruefen(`${B}.${mac}`, "testschluessel")).toBeNull();
    expect(geburtstagTokenPruefen(`${ID}.${mac.slice(0, -1)}A`, "testschluessel")).toBeNull();
    for (const kaputt of ["", "x", ID, `${ID}.`, `nicht-uuid.${mac}`, 7, null, "a".repeat(300)]) {
      expect(geburtstagTokenPruefen(kaputt, "testschluessel")).toBeNull();
    }
    // Ohne gesetzten Schlüssel ist jedes Token ungültig
    delete process.env.GEBURTSTAG_TOKEN_SCHLUESSEL;
    expect(geburtstagTokenPruefen(VEKTOR)).toBeNull();
  });
});

function post(pfad: string, body?: unknown, kopf: Record<string, string> = {}): Request {
  const text = body === undefined ? undefined : JSON.stringify(body);
  return new Request(`https://diesdas.events${pfad}`, {
    method: "POST",
    headers: { ...(text === undefined ? {} : { "content-type": "application/json", "content-length": String(Buffer.byteLength(text)) }), ...kopf },
    body: text,
  });
}

describe("POST /api/konto/geburtstag-abmelden (Seite)", () => {
  const ORIGIN = { origin: "https://diesdas.events" };
  it("gültiges Token → Widerruf mit abmeldelink und aktueller Textversion, Datum bleibt (kein stammdaten-Aufruf)", async () => {
    const { POST } = await import("@/app/api/konto/geburtstag-abmelden/route");
    const res = await POST(post("/api/konto/geburtstag-abmelden", { token: VEKTOR }, ORIGIN), ctx());
    expect(res.status).toBe(200);
    expect(zustand.rpc).toEqual([{
      name: "einwilligung_setzen",
      args: { nutzer: ID, art: "geburtstagsmail", erteilt: false, textversion: TEXTVERSIONEN.geburtstagsmail, handlung: "abmeldelink" },
    }]);
  });
  it("schon abgemeldet oder Konto weg → gleiche Antwort, keine neue Nachweiszeile", async () => {
    const { POST } = await import("@/app/api/konto/geburtstag-abmelden/route");
    zustand.profil = { geburtstagsmail: false };
    const a = await (await POST(post("/api/konto/geburtstag-abmelden", { token: VEKTOR }, ORIGIN), ctx())).json();
    zustand.profil = null;
    const b = await (await POST(post("/api/konto/geburtstag-abmelden", { token: VEKTOR }, ORIGIN), ctx())).json();
    expect(a).toEqual(b);
    expect(zustand.rpc).toEqual([]);
  });
  it("ungültiges Token → 400, fremder Origin → 403, Schalter aus → 404", async () => {
    const { POST } = await import("@/app/api/konto/geburtstag-abmelden/route");
    expect((await POST(post("/api/konto/geburtstag-abmelden", { token: "x" }, ORIGIN), ctx())).status).toBe(400);
    expect((await POST(post("/api/konto/geburtstag-abmelden", { token: VEKTOR }, { origin: "https://evil.example" }), ctx())).status).toBe(403);
    process.env.KONTEN_AKTIV = "0";
    expect((await POST(post("/api/konto/geburtstag-abmelden", { token: VEKTOR }, ORIGIN), ctx())).status).toBe(404);
    expect(zustand.rpc).toEqual([]);
  });
  it("Bremslimit 30 je IP und Stunde", async () => {
    const { POST } = await import("@/app/api/konto/geburtstag-abmelden/route");
    let letzte = 0;
    for (let i = 0; i < 31; i++) letzte = (await POST(post("/api/konto/geburtstag-abmelden", { token: "x" }, { ...ORIGIN, "x-real-ip": "203.0.113.9" }), ctx())).status;
    expect(letzte).toBe(429);
  });
});

describe("One-Click /api/konto/geburtstag-abmelden/[token] (RFC 8058)", () => {
  it("POST ohne Origin (vom Mailserver) → 200 und Widerruf", async () => {
    const { POST } = await import("@/app/api/konto/geburtstag-abmelden/[token]/route");
    const req = new Request(`https://diesdas.events/api/konto/geburtstag-abmelden/${VEKTOR}`, {
      method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: "List-Unsubscribe=One-Click",
    });
    const res = await POST(req, ctx({ token: VEKTOR }));
    expect(res.status).toBe(200);
    expect(zustand.rpc.map((r) => r.args.handlung)).toEqual(["abmeldelink"]);
  });
  it("Schalter KONTEN_AKTIV aus → POST und GET 404", async () => {
    const { GET, POST } = await import("@/app/api/konto/geburtstag-abmelden/[token]/route");
    process.env.KONTEN_AKTIV = "0";
    const url = `https://diesdas.events/api/konto/geburtstag-abmelden/${VEKTOR}`;
    expect((await POST(new Request(url, { method: "POST" }), ctx({ token: VEKTOR }))).status).toBe(404);
    expect((await GET(new Request(url))).status).toBe(404);
    expect(zustand.rpc).toEqual([]);
  });
  it("Fehler-Log maskiert das Token im Pfad (Cursor-Hinweis)", async () => {
    const { pfadFuerLog } = await import("@/lib/konto/route");
    expect(pfadFuerLog(`/api/konto/geburtstag-abmelden/${VEKTOR}`)).toBe("/api/konto/geburtstag-abmelden/…");
    expect(pfadFuerLog(`/api/konto/merkliste/${ID}`)).toBe(`/api/konto/merkliste/${ID}`);
  });
  it("GET ändert nichts (405), ungültiges Token 400", async () => {
    const { GET, POST } = await import("@/app/api/konto/geburtstag-abmelden/[token]/route");
    const g = await GET(new Request(`https://diesdas.events/api/konto/geburtstag-abmelden/${VEKTOR}`));
    expect(g.status).toBe(405);
    expect(g.headers.get("allow")).toBe("POST");
    expect((await POST(new Request("https://diesdas.events/api/konto/geburtstag-abmelden/x", { method: "POST" }), ctx({ token: "x" }))).status).toBe(400);
    expect((await POST(new Request("https://diesdas.events/api/konto/geburtstag-abmelden/%E0", { method: "POST" }), ctx({ token: "%E0" }))).status).toBe(400);
    expect(zustand.rpc).toEqual([]);
  });
});

describe("POST /api/intern/geburtstag-tipps (G2)", () => {
  const anfrage = (body: unknown, schluessel = "jobschluessel") =>
    new Request("https://diesdas.events/api/intern/geburtstag-tipps", {
      method: "POST", headers: { "content-type": "application/json", "x-geburtstag-schluessel": schluessel }, body: JSON.stringify(body),
    }) as unknown as import("next/server").NextRequest;

  it("ohne oder mit falschem Schlüssel 404", async () => {
    const { POST } = await import("@/app/api/intern/geburtstag-tipps/route");
    expect((await POST(anfrage({ nutzer: [] }, "falsch"))).status).toBe(404);
    delete process.env.GEBURTSTAG_JOB_SCHLUESSEL;
    expect((await POST(anfrage({ nutzer: [] }))).status).toBe(404);
  });
  it("persönlich (a) und allgemein, höchstens drei, nie sensibel, nie gemerkt, nie morgen", async () => {
    const { POST } = await import("@/app/api/intern/geburtstag-tipps/route");
    zustand.profile = [
      { id: ID, personalisierung: true, praeferenzen: { kategorien: ["musik"], merkmale: ["abends"] } },
      { id: B, personalisierung: false, praeferenzen: {} },
    ];
    zustand.merkliste = [{ nutzer_id: B, event_id: kultur.id, gemerkt_am: "2026-11-01T10:00:00Z" }];
    const res = await POST(anfrage({ nutzer: [ID, B, "kaputt"] }));
    expect(res.status).toBe(200);
    const text = await res.clone().text();
    const d = await res.json();
    expect(d.datum).toBe(HEUTE);
    expect(Object.keys(d.tipps).sort()).toEqual([ID, B].sort());
    const titel = (liste: { titel: string }[]) => liste.map((t) => t.titel);
    // Musik-Interesse → das Musik-Event von heute ist dabei
    expect(titel(d.tipps[ID])).toContain(musik.titel);
    for (const liste of [d.allgemein, d.tipps[ID], d.tipps[B]]) {
      expect(liste.length).toBeLessThanOrEqual(3);
      expect(titel(liste)).not.toContain(sensibel.titel);
      expect(titel(liste)).not.toContain(morgen.titel);
    }
    // Gemerktes Event von B nicht in Bs Tipps
    expect(titel(d.tipps[B])).not.toContain(kultur.titel);
    // Keine Interessen, Begründungen, Punkte oder Adressen in der Antwort
    expect(text).not.toMatch(/begruendung|punkte|praeferenzen|sensibel|@/);
    expect(d.tipps[ID][0]).toEqual({ titel: expect.any(String), ort: "zakk", uhrzeit: "20:00", pfad: expect.stringMatching(/^\/event\//) });
  });
  it("Sensibel-Menge nicht lesbar → 503", async () => {
    const { POST } = await import("@/app/api/intern/geburtstag-tipps/route");
    zustand.sensibelFehler = true;
    expect((await POST(anfrage({ nutzer: [ID] }))).status).toBe(503);
  });
  it("mehr als 200 Nutzer → 400", async () => {
    const { POST } = await import("@/app/api/intern/geburtstag-tipps/route");
    expect((await POST(anfrage({ nutzer: Array.from({ length: 201 }, () => ID) }))).status).toBe(400);
  });
  it("Beispielpool nach Ladefehler → 503, keine Beispiel-Events als Tipps (Cursor-Befund hoch)", async () => {
    const { POST } = await import("@/app/api/intern/geburtstag-tipps/route");
    zustand.pool = { ...zustand.pool, quelle: "beispiel", fehler: "kaputt" };
    expect((await POST(anfrage({ nutzer: [ID] }))).status).toBe(503);
  });
  it("Schalter KONTEN_AKTIV aus → 404", async () => {
    const { POST } = await import("@/app/api/intern/geburtstag-tipps/route");
    process.env.KONTEN_AKTIV = "0";
    expect((await POST(anfrage({ nutzer: [] }))).status).toBe(404);
  });
  it("mit Einwilligung (a): gemerktes Event fällt raus, auch wenn es am besten passt; Merkliste je Person", async () => {
    const { POST } = await import("@/app/api/intern/geburtstag-tipps/route");
    zustand.profile = [{ id: ID, personalisierung: true, praeferenzen: { kategorien: ["musik"] } }];
    zustand.merkliste = [
      { nutzer_id: ID, event_id: musik.id, gemerkt_am: "2026-11-01T10:00:00Z" },
      // Zeile einer anderen Person darf ID nicht beeinflussen
      { nutzer_id: B, event_id: kultur.id, gemerkt_am: "2026-11-01T10:00:00Z" },
    ];
    const d = await (await POST(anfrage({ nutzer: [ID] }))).json();
    const titel = d.tipps[ID].map((t: { titel: string }) => t.titel);
    expect(titel).not.toContain(musik.titel);
    expect(titel).not.toContain(sensibel.titel);
  });
  it("Merkliste nicht lesbar oder verdächtig voll → 503 statt unvollständiger Tipps (Cursor-Befund gering)", async () => {
    const { POST } = await import("@/app/api/intern/geburtstag-tipps/route");
    zustand.profile = [{ id: ID, personalisierung: false, praeferenzen: {} }];
    zustand.merklisteFehler = true;
    expect((await POST(anfrage({ nutzer: [ID] }))).status).toBe(503);
    zustand.merklisteFehler = false;
    zustand.merkliste = Array.from({ length: 1000 }, (_, i) => ({ nutzer_id: ID, event_id: `x${i}`, gemerkt_am: "2026-11-01T10:00:00Z" }));
    expect((await POST(anfrage({ nutzer: [ID] }))).status).toBe(503);
  });
});
