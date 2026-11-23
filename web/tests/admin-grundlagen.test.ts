// Tests zum Admin-Bereich, Stufe 1a (Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 6)
import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { istAdminBereich, istAdminPfad } from "@/lib/admin/bereich";
import { ADMIN_COOKIE_ART } from "@/lib/admin/konfig";
import { adminOriginErlaubt } from "@/lib/admin/pruefungen";
import { aalAusToken } from "@/lib/admin/sitzung";
import { adminRoute } from "@/lib/admin/route";
import { sitzungsCookie, sitzungsCookieLoeschen } from "@/lib/konto/cookies";
import { proxy } from "@/proxy";

/** Kopf wie hinter nginx: Host localhost:3847 und X-Forwarded-Proto */
function live(extra: Record<string, string> = {}): Headers {
  return new Headers({ host: "localhost:3847", "x-forwarded-proto": "https", "x-real-ip": "1.2.3.4", ...extra });
}

function anfrage(pfad: string, kopf: Headers): NextRequest {
  return new NextRequest(new URL(pfad, "http://localhost:3847"), { headers: kopf });
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("Bereich (3.2)", () => {
  it("nur mit X-DDD-Bereich: admin", () => {
    expect(istAdminBereich(live({ "x-ddd-bereich": "admin" }))).toBe(true);
    expect(istAdminBereich(live({ "x-ddd-bereich": "web" }))).toBe(false);
    expect(istAdminBereich(live())).toBe(false);
  });

  it("ADMIN_LOKAL wirkt nur unter next dev, nie mit NODE_ENV=production (live)", () => {
    vi.stubEnv("ADMIN_LOKAL", "1");
    vi.stubEnv("NODE_ENV", "production");
    expect(istAdminBereich(new Headers({ host: "localhost:3100" }))).toBe(false);
    expect(istAdminBereich(live())).toBe(false);
    vi.stubEnv("NODE_ENV", "development");
    expect(istAdminBereich(new Headers({ host: "localhost:3100" }))).toBe(true);
  });

  it("Admin-Pfade", () => {
    for (const p of ["/admin", "/admin/anmelden", "/api/admin", "/api/admin/ich"]) expect(istAdminPfad(p)).toBe(true);
    for (const p of ["/", "/administration", "/api/konto/anmelden", "/magazin"]) expect(istAdminPfad(p)).toBe(false);
  });
});

describe("proxy.ts (3.2)", () => {
  it("/admin ohne Admin-Kopf → 404, auch hinter nginx", async () => {
    const r = await proxy(anfrage("/admin", live()));
    expect(r.status).toBe(404);
    const api = await proxy(anfrage("/api/admin/ich", live({ "x-ddd-bereich": "web" })));
    expect(api.status).toBe(404);
  });

  it("/ mit Admin-Kopf → 308 auf /admin (gleicher Ursprung; Next macht die Location beim Ausliefern relativ)", async () => {
    const r = await proxy(anfrage("/", live({ "x-ddd-bereich": "admin" })));
    expect(r.status).toBe(308);
    expect(new URL(r.headers.get("location")!).pathname).toBe("/admin");
    expect(new URL(r.headers.get("location")!).origin).toBe("http://localhost:3847");
  });

  it("/ ohne Admin-Kopf läuft unverändert weiter", async () => {
    const r = await proxy(anfrage("/", live({ "x-ddd-bereich": "web" })));
    expect(r.status).toBe(200);
    expect(r.headers.get("location")).toBeNull();
  });

  it("Admin-Seite ohne Cookie → Anmeldung, Anmeldeseite selbst offen, mit Cookie durch und noindex", async () => {
    const ohne = await proxy(anfrage("/admin", live({ "x-ddd-bereich": "admin" })));
    expect(ohne.status).toBe(307);
    expect(new URL(ohne.headers.get("location")!).pathname).toBe("/admin/anmelden");

    const anmelden = await proxy(anfrage("/admin/anmelden", live({ "x-ddd-bereich": "admin" })));
    expect(anmelden.status).toBe(200);
    expect(anmelden.headers.get("x-robots-tag")).toBe("noindex, nofollow");

    const mit = await proxy(anfrage("/admin", live({ "x-ddd-bereich": "admin", cookie: "ddd_admin=abc" })));
    expect(mit.status).toBe(200);
    expect(mit.headers.get("cache-control")).toBe("private, no-store");
  });

  it("API-Pfade leitet der Proxy nicht zur Anmeldung um (die Route antwortet selbst mit 401)", async () => {
    const r = await proxy(anfrage("/api/admin/ich", live({ "x-ddd-bereich": "admin" })));
    expect(r.status).toBe(200);
  });
});

describe("Cookies (3.3)", () => {
  it("Konto-Cookie unverändert", () => {
    const c = sitzungsCookie({ access: "a", refresh: "r" }, false);
    expect(c).toContain("ddd_sitzung=");
    expect(c).toContain("Path=/api/konto");
    expect(c).toContain("SameSite=Lax");
    expect(c).toContain(`Max-Age=${30 * 24 * 60 * 60}`);
  });

  it("Admin-Cookie: ddd_admin, Path=/, SameSite=Strict, 12 h, HttpOnly, Secure, ohne Domain", () => {
    const c = sitzungsCookie({ access: "a", refresh: "r" }, false, ADMIN_COOKIE_ART);
    expect(c).toMatch(/^ddd_admin=/);
    expect(c).toContain("Path=/;");
    expect(c).toContain("SameSite=Strict");
    expect(c).toContain(`Max-Age=${12 * 60 * 60}`);
    expect(c).toContain("HttpOnly");
    expect(c).toContain("Secure");
    expect(c).not.toContain("Domain");
    expect(sitzungsCookieLoeschen(false, ADMIN_COOKIE_ART)).toMatch(/^ddd_admin=; Path=\/; Max-Age=0/);
  });
});

describe("Origin (3.3)", () => {
  it("live nur der Admin-Ursprung", () => {
    expect(adminOriginErlaubt(live({ origin: "https://admin.diesdas.events" }))).toBe(true);
    expect(adminOriginErlaubt(live({ origin: "https://diesdas.events" }))).toBe(false);
    expect(adminOriginErlaubt(live())).toBe(false);
    expect(adminOriginErlaubt(live({ origin: "http://localhost:3100" }))).toBe(false);
  });
});

describe("Zwei-Faktor-Stufe aus dem Token", () => {
  const token = (nutzlast: object) => `x.${Buffer.from(JSON.stringify(nutzlast)).toString("base64url")}.y`;
  it("aal2 nur, wenn das Token es sagt", () => {
    expect(aalAusToken(token({ aal: "aal2" }))).toBe("aal2");
    expect(aalAusToken(token({ aal: "aal1" }))).toBe("aal1");
    expect(aalAusToken("kaputt")).toBe("aal1");
  });
});

describe("adminRoute (3.3)", () => {
  const ok = async () => new Response("ok");

  it("ohne Admin-Kopf → 404", async () => {
    const r = await adminRoute(new Request("http://localhost:3847/api/admin/ich", { headers: live() }), {}, ok);
    expect(r.status).toBe(404);
  });

  it("ohne Sitzung → 401", async () => {
    const r = await adminRoute(
      new Request("http://localhost:3847/api/admin/ich", { headers: live({ "x-ddd-bereich": "admin" }) }),
      {},
      ok,
    );
    expect(r.status).toBe(401);
  });

  it("POST mit fremdem Ursprung → 403, ohne JSON → 415", async () => {
    const fremd = await adminRoute(
      new Request("http://localhost:3847/api/admin/anmelden", {
        method: "POST",
        headers: live({ "x-ddd-bereich": "admin", origin: "https://diesdas.events", "content-type": "application/json", "content-length": "2" }),
        body: "{}",
      }),
      { anmeldung: false },
      ok,
    );
    expect(fremd.status).toBe(403);
    const text = await adminRoute(
      new Request("http://localhost:3847/api/admin/anmelden", {
        method: "POST",
        headers: live({ "x-ddd-bereich": "admin", origin: "https://admin.diesdas.events", "content-type": "text/plain", "content-length": "2" }),
        body: "{}",
      }),
      { anmeldung: false },
      ok,
    );
    expect(text.status).toBe(415);
  });
});
