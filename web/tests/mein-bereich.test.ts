// Tests der Routen start, fuer-dich und uebersicht sowie der Wrapper-Änderung (Plan Mein Bereich 6 und 10).
// Supabase, Event-Pool und Merkliste-Events sind Attrappen – kein Netz.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DddEvent, EventPool } from "@/lib/typen";

type Ergebnis = { data?: unknown; error?: { message?: string; code?: string } | null };

const zustand = vi.hoisted(() => ({
  aufrufe: [] as { tabelle: string; op: string; args: unknown[] }[],
  antworten: {} as Record<string, (args: unknown[]) => unknown>,
  pool: null as unknown as EventPool,
  eventsFehler: false,
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
    rpc: () => Promise.resolve({ data: [], error: null }),
    auth: new Proxy({}, { get: () => () => Promise.resolve({ data: {}, error: null }) }),
  };
}

vi.mock("@/lib/konto/clients", () => ({
  ANFRAGE_OPTIONEN: {},
  authClientAnfrage: () => db(),
  nutzerClient: () => db(),
  kontoDienstClient: () => db(),
  tokenPruefen: async () => zustand.token,
}));
vi.mock("@/lib/daten", () => ({ eventPoolLaden: async () => zustand.pool }));
vi.mock("@/lib/konto/merkliste-events", () => ({
  eventsFuerIds: async (ids: string[]) => {
    if (zustand.eventsFehler) throw new Error("kaputt");
    const karte = new Map(zustand.pool.alle.map((e) => [e.id, e]));
    return { heute: zustand.pool.heute, events: ids.map((id) => karte.get(id)).filter(Boolean) };
  },
}));

import { bremslimitZuruecksetzen } from "@/lib/formulare";
import { sitzungKodieren } from "@/lib/konto/cookies";
import { sensibelCacheLeeren } from "@/lib/konto/mein-bereich";
import { aktivitaetZuruecksetzen } from "@/lib/konto/route";
import { ev } from "./hilfen";

const A = "11111111-1111-4111-8111-111111111111";
const HEUTE = "2026-11-19";
const id = (n: number) => `aaaaaaaa-0000-4000-8000-${String(n).padStart(12, "0")}`;
let zaehler = 0;

function poolAus(events: DddEvent[]): EventPool {
  return { heute: HEUTE, jetzt: `2026-11-19T10:00:${String(zaehler++).padStart(2, "0")}Z`, events, alle: events, quelle: "supabase", fehler: null };
}
function profil(teil: Record<string, unknown> = {}) {
  return {
    id: A, anzeigename: null, praeferenzen: {}, onboarding_fertig_am: "2026-11-16T10:00:00Z", mindestalter_bestaetigt_am: "2026-11-16T10:00:00Z",
    personalisierung: false, sensible_events_erlaubt: false, analyse_erlaubt: true, nutzungsbedingungen_version: "x",
    geburtstagsmail: false, geburtsdatum: "2000-01-01", geburtstagsmail_zuletzt: null, unter16_gesperrt_am: null,
    letzte_aktivitaet_am: null, merkliste_begonnen_am: null, erstellt_am: "2026-11-16T10:00:00Z", rolle: "user",
    vorname: "Erika", nachname: "Muster", ...teil,
  };
}
function jwt(): string {
  const b = (o: object) => Buffer.from(JSON.stringify(o)).toString("base64url");
  return `${b({ alg: "ES256" })}.${b({ sub: A, exp: Math.floor(Date.now() / 1000) + 3600, email: "a@example.org" })}.sig`;
}
function anfrage(pfad: string, art: "cookie" | "bearer" | "keine" = "cookie"): Request {
  const headers: Record<string, string> = {};
  if (art === "cookie") headers.cookie = `ddd_sitzung=${sitzungKodieren({ access: jwt(), refresh: "r1" })}`;
  if (art === "bearer") headers.authorization = `Bearer ${jwt()}`;
  return new Request(`https://diesdas.events${pfad}`, { method: "GET", headers });
}
const ctx = () => ({ params: Promise.resolve({}) });
const setCookie = (r: Response) => r.headers.get("set-cookie") ?? "";

// Events: zwei Musik-Events (Interesse), ein gemerktes, ein sensibles, ein kommendes gemerktes
const musik1 = ev({ id: id(1), datum: HEUTE, ort: "zakk", kategorie: "musik" });
const musik2 = ev({ id: id(2), datum: "2026-11-21", ort: "Tonhalle", kategorie: "musik" });
const sensibel = ev({ id: id(3), datum: HEUTE, ort: "Gemeindesaal", kategorie: "musik" });
const gemerkt = ev({ id: id(4), datum: "2026-11-22", ort: "Capitol", kategorie: "musik" });
const kultur = ev({ id: id(5), datum: HEUTE, ort: "Kunsthalle", kategorie: "kultur" });

async function start(pfad = "/api/konto/start", art: "cookie" | "bearer" = "cookie") {
  const { GET } = await import("@/app/api/konto/start/route");
  return GET(anfrage(pfad, art), ctx());
}

beforeEach(() => {
  zustand.aufrufe = [];
  zustand.eventsFehler = false;
  zustand.token = { sub: A, email: "a@example.org" };
  zustand.pool = poolAus([musik1, musik2, sensibel, gemerkt, kultur]);
  zustand.antworten = {
    "profiles.select": () => ({ data: profil({ personalisierung: true, praeferenzen: { version: 1, kategorien: ["musik"] } }), error: null }),
    "merkliste.select": () => ({ data: [{ event_id: gemerkt.id, gemerkt_am: "2026-11-10T10:00:00Z" }], error: null }),
    "event_sensibel.select": () => ({ data: [{ event_id: sensibel.id }], error: null }),
  };
  process.env.KONTEN_AKTIV = "1";
  bremslimitZuruecksetzen();
  aktivitaetZuruecksetzen();
  sensibelCacheLeeren();
});
afterEach(() => {
  delete process.env.KONTEN_AKTIV;
});

describe("GET /api/konto/start", () => {
  it("persönliche Vorschläge mit Begründung, ohne gemerkte und sensible Events, ohne interne Felder", async () => {
    const res = await start();
    expect(res.status).toBe(200);
    const text = await res.clone().text();
    const d = await res.json();
    expect(d.personalisierung).toBe(true);
    expect(d.heute).toMatch(/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/);
    expect(d.ersatz).toBe(false);
    expect(d.fuer_dich.map((e: DddEvent) => e.id).sort()).toEqual([musik1.id, musik2.id].sort());
    expect(d.fuer_dich[0].begruendung).toBe("Musik");
    expect(text).not.toMatch(/sensibel|punkte|bezuege|nutzer_id/);
    expect(d.naechste.map((e: DddEvent) => e.id)).toEqual([gemerkt.id]);
    // NAMEN_ANREDE seit 19.11.2026 an (Schritt 5)
    expect(d.vorname).toBe("Erika");
    expect(res.headers.get("cache-control")).toBe("private, no-store");
  });
  it("ohne: ausgeschlossen, höchstens 24, ungültige still weg", async () => {
    const viele = [musik1.id, ...Array.from({ length: 30 }, (_, n) => id(100 + n)), "kaputt"].join(",");
    const d = await (await start(`/api/konto/start?ohne=${viele}`)).json();
    expect(d.fuer_dich.map((e: DddEvent) => e.id)).toEqual([musik2.id]);
    const d2 = await (await start(`/api/konto/start?ohne=${[...Array.from({ length: 24 }, (_, n) => id(200 + n)), musik1.id].join(",")}`)).json();
    // musik1 steht an Stelle 25 und fällt mit dem Deckel weg → bleibt Vorschlag
    expect(d2.fuer_dich.map((e: DddEvent) => e.id)).toContain(musik1.id);
  });
  it("Ersatz „Beliebt“ ohne Treffer, ohne sensible IDs", async () => {
    zustand.antworten["profiles.select"] = () => ({ data: profil({ personalisierung: true, praeferenzen: { version: 1, kategorien: ["sport"] } }), error: null });
    const d = await (await start()).json();
    expect(d.ersatz).toBe(true);
    expect(d.fuer_dich.map((e: DddEvent) => e.id)).not.toContain(sensibel.id);
    expect(d.fuer_dich.map((e: DddEvent) => e.id)).not.toContain(gemerkt.id);
  });
  it("ohne Einwilligung: keine Rechnung, Sensibel-Tabelle nicht gelesen, naechste trotzdem", async () => {
    zustand.antworten["profiles.select"] = () => ({ data: profil({ personalisierung: false }), error: null });
    const d = await (await start()).json();
    expect(d).toMatchObject({ personalisierung: false, ersatz: false, fuer_dich: [] });
    expect(d.naechste.map((e: DddEvent) => e.id)).toEqual([gemerkt.id]);
    expect(zustand.aufrufe.some((a) => a.tabelle === "event_sensibel")).toBe(false);
  });
  it("Sensibel-Menge nicht lesbar: 503, ohne Cache des Fehlers", async () => {
    zustand.antworten["event_sensibel.select"] = () => ({ data: null, error: { code: "x" } });
    expect((await start()).status).toBe(503);
    zustand.antworten["event_sensibel.select"] = () => ({ data: [{ event_id: sensibel.id }], error: null });
    expect((await start()).status).toBe(200);
  });
  it("Events der Merkliste nicht ladbar: naechste leer, fuer_dich trotzdem, gemerktes Event trotzdem ausgeschlossen", async () => {
    zustand.eventsFehler = true;
    const d = await (await start()).json();
    expect(d.naechste).toEqual([]);
    expect(d.fuer_dich.length).toBeGreaterThan(0);
    expect(d.fuer_dich.map((e: DddEvent) => e.id)).not.toContain(gemerkt.id);
  });
  it("datum: anderer Tag nur dieser Tag; ungültig wird zu heute", async () => {
    const d = await (await start("/api/konto/start?datum=2026-11-21")).json();
    expect(d.fuer_dich.map((e: DddEvent) => e.id)).toEqual([musik2.id]);
    const d2 = await (await start("/api/konto/start?datum=quatsch")).json();
    expect(d2.fuer_dich.map((e: DddEvent) => e.id).sort()).toEqual([musik1.id, musik2.id].sort());
  });
  it("Schalter aus → 404; ohne Sitzung → 401", async () => {
    const { GET } = await import("@/app/api/konto/start/route");
    expect((await GET(anfrage("/api/konto/start", "keine"), ctx())).status).toBe(401);
    process.env.KONTEN_AKTIV = "0";
    expect((await GET(anfrage("/api/konto/start"), ctx())).status).toBe(404);
  });
});

describe("Hinweis-Cookie nur bei Cookie-Sitzung (Wrapper, Plan 6)", () => {
  it("Cookie: 200 setzt ddd_konto=1; Bearer: kein ddd_konto", async () => {
    expect(setCookie(await start())).toContain("ddd_konto=1");
    const bearer = await start("/api/konto/start", "bearer");
    expect(bearer.status).toBe(200);
    expect(setCookie(bearer)).not.toContain("ddd_konto");
  });
  it("403 mindestalter_fehlt: Cookie bekommt ddd_konto=0, Bearer nicht (auch bei gesetzter Sperre der Live-Pfad)", async () => {
    zustand.antworten["profiles.select"] = () => ({ data: profil({ mindestalter_bestaetigt_am: null, unter16_gesperrt_am: "2026-11-18T10:00:00Z" }), error: null });
    const c = await start();
    expect(c.status).toBe(403);
    expect((await c.json()).code).toBe("mindestalter_fehlt");
    expect(setCookie(c)).toContain("ddd_konto=0");
    const b = await start("/api/konto/start", "bearer");
    expect(b.status).toBe(403);
    expect(setCookie(b)).not.toContain("ddd_konto");
  });
  it("Verteidigung: Sperre bei gesetztem Mindestalter → 403 unter16_gesperrt, nie ddd_konto=1", async () => {
    zustand.antworten["profiles.select"] = () => ({ data: profil({ unter16_gesperrt_am: "2026-11-18T10:00:00Z" }), error: null });
    const c = await start();
    expect(c.status).toBe(403);
    expect((await c.json()).code).toBe("unter16_gesperrt");
    expect(setCookie(c)).toContain("ddd_konto=0");
    expect(setCookie(c)).not.toContain("ddd_konto=1");
    const b = await start("/api/konto/start", "bearer");
    expect(setCookie(b)).not.toContain("ddd_konto");
  });
});

describe("GET /api/konto/fuer-dich", () => {
  it("Abschnitte ohne interne Felder; ohne Einwilligung leer und ohne Merkliste-Abruf", async () => {
    const { GET } = await import("@/app/api/konto/fuer-dich/route");
    const res = await GET(anfrage("/api/konto/fuer-dich"), ctx());
    const text = await res.clone().text();
    const d = await res.json();
    expect(d.personalisierung).toBe(true);
    // heute für die Datumszeile der Karten (Schritt 3)
    expect(d.heute).toMatch(/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/);
    expect(d.abschnitte.length).toBeGreaterThan(0);
    expect(text).not.toMatch(/sensibel|punkte|bezuege/);
    zustand.aufrufe = [];
    zustand.antworten["profiles.select"] = () => ({ data: profil({ personalisierung: false }), error: null });
    const d2 = await (await GET(anfrage("/api/konto/fuer-dich"), ctx())).json();
    expect(d2).toMatchObject({ personalisierung: false, abschnitte: [] });
    expect(zustand.aufrufe.some((a) => a.tabelle === "merkliste" || a.tabelle === "event_sensibel")).toBe(false);
  });
  it("Sensibel-Menge nicht lesbar: 503", async () => {
    zustand.antworten["event_sensibel.select"] = () => ({ data: null, error: { code: "x" } });
    const { GET } = await import("@/app/api/konto/fuer-dich/route");
    expect((await GET(anfrage("/api/konto/fuer-dich"), ctx())).status).toBe(503);
  });
});

describe("GET /api/konto/uebersicht", () => {
  it("Zahlen; vorschlaege null ohne Einwilligung; fehlende Sensibel-Menge → 200 mit vorschlaege_unbekannt", async () => {
    zustand.antworten["profiles.select"] = () => ({
      data: profil({ personalisierung: true, praeferenzen: { version: 1, kategorien: ["musik"], stadtteile: ["flingern-nord"] } }),
      error: null,
    });
    const { GET } = await import("@/app/api/konto/uebersicht/route");
    const d = await (await GET(anfrage("/api/konto/uebersicht"), ctx())).json();
    expect(d).toMatchObject({ vorschlaege: 2, kommende: 1, erlebt: 0, interessen: 2 });

    zustand.antworten["event_sensibel.select"] = () => ({ data: null, error: { code: "x" } });
    sensibelCacheLeeren();
    const r2 = await GET(anfrage("/api/konto/uebersicht"), ctx());
    expect(r2.status).toBe(200);
    expect(await r2.json()).toMatchObject({ vorschlaege: null, vorschlaege_unbekannt: true, kommende: 1 });

    zustand.antworten["profiles.select"] = () => ({ data: profil({ personalisierung: false }), error: null });
    expect(await (await GET(anfrage("/api/konto/uebersicht"), ctx())).json()).toMatchObject({ vorschlaege: null });
  });
  it("Merkliste-Events nicht geladen: Flag merkliste_unvollstaendig, damit die Kacheln keine 0 zeigen (Cursor-Befund 3)", async () => {
    zustand.eventsFehler = true;
    const { GET } = await import("@/app/api/konto/uebersicht/route");
    const res = await GET(anfrage("/api/konto/uebersicht"), ctx());
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ merkliste_unvollstaendig: true });
  });
});

describe("Reset-Sitzung an den neuen Routen (Plan 3.0, 6)", () => {
  it("start, fuer-dich und uebersicht → 403 passwort_setzen_noetig, ohne Daten", async () => {
    const reset = sitzungKodieren({ access: jwt(), refresh: "r1", nur_passwort: true });
    const routen = {
      start: (await import("@/app/api/konto/start/route")).GET,
      "fuer-dich": (await import("@/app/api/konto/fuer-dich/route")).GET,
      uebersicht: (await import("@/app/api/konto/uebersicht/route")).GET,
    };
    for (const [pfad, GET] of Object.entries(routen)) {
      const res: Response = await GET(
        new Request(`https://diesdas.events/api/konto/${pfad}`, { method: "GET", headers: { cookie: `ddd_sitzung=${reset}` } }),
        ctx(),
      );
      expect(res.status, pfad).toBe(403);
      const d = await res.json();
      expect(d.code, pfad).toBe("passwort_setzen_noetig");
      expect(d).not.toHaveProperty("fuer_dich");
      expect(d).not.toHaveProperty("abschnitte");
      expect(d).not.toHaveProperty("kommende");
    }
  });
});
