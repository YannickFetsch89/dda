// Tests zum Cockpit, Stufe 1b (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.2 und 4.3)
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";
import { workflowStarten } from "@/lib/admin/github";
import { eventLuecken, scraperAmpel, tokenAmpel, workflowAmpel } from "@/lib/admin/ampeln";
import { warnungenBerechnen, type ErgebnisZeile, type LaufZeile } from "@/lib/admin/warnregeln";
import { ev } from "./hilfen";

interface Fall {
  name: string;
  jetzt: string;
  laeufe: LaufZeile[];
  ergebnisse: ErgebnisZeile[];
  erwartet: { regel: string; quelle: string | null }[];
}

const FIXTURE = JSON.parse(
  readFileSync(fileURLToPath(new URL("../../tests/fixtures/lauf_warnungen.json", import.meta.url)), "utf8"),
) as { faelle: Fall[] };

const schluessel = (w: { regel: string; quelle: string | null }) => `${w.regel}|${w.quelle ?? ""}`;

describe("Warnregeln W1–W6 (gemeinsame Fixture mit Python)", () => {
  for (const fall of FIXTURE.faelle) {
    it(fall.name, () => {
      const ist = warnungenBerechnen(fall.laeufe, fall.ergebnisse, new Date(fall.jetzt)).map(schluessel).sort();
      expect(ist).toEqual(fall.erwartet.map(schluessel).sort());
    });
  }
});

describe("Ampeln", () => {
  const jetzt = new Date("2026-11-23T12:00:00Z");
  const lauf = (alterStunden: number, conclusion: string | null, status = "completed") => ({
    art: "ok" as const,
    tokenAblauf: null,
    lauf: { status, conclusion, erstellt_am: new Date(jetzt.getTime() - alterStunden * 3600_000).toISOString(), url: "u", titel: "t" },
  });

  it("Workflow: Erfolg grün, Fehler rot, zu alt gelb, ohne Token grau", () => {
    expect(workflowAmpel("w", "W", lauf(0.2, "success"), jetzt, 1).farbe).toBe("gruen");
    expect(workflowAmpel("w", "W", lauf(0.2, "failure"), jetzt, 1).farbe).toBe("rot");
    expect(workflowAmpel("w", "W", lauf(3, "success"), jetzt, 1).farbe).toBe("gelb");
    expect(workflowAmpel("w", "W", lauf(300, "success"), jetzt, null).farbe).toBe("gruen");
    expect(workflowAmpel("w", "W", { art: "kein_token" }, jetzt, 1).farbe).toBe("grau");
  });

  it("Token-Ablauf: erst ab 30 Tagen sichtbar, ab 7 Tagen rot", () => {
    expect(tokenAmpel(null, jetzt)).toBeNull();
    expect(tokenAmpel("2027-06-01 00:00:00 UTC", jetzt)).toBeNull();
    expect(tokenAmpel("2026-12-10T00:00:00Z", jetzt)?.farbe).toBe("gelb");
    expect(tokenAmpel("2026-11-25T00:00:00Z", jetzt)?.farbe).toBe("rot");
  });

  it("Scraper: rote Warnung macht die Ampel rot, sonst Alter", () => {
    const laeufe: LaufZeile[] = [{ id: "a", gestartet_am: "2026-11-23T05:00:00Z", beendet_am: "2026-11-23T06:00:00Z", status: "erfolgreich", speicher_fehler: 0 }];
    expect(scraperAmpel(laeufe, [], jetzt, null).farbe).toBe("gruen");
    expect(scraperAmpel(laeufe, [{ regel: "W1", stufe: "rot", quelle: "zakk", text: "" }], jetzt, null).farbe).toBe("rot");
    expect(scraperAmpel(laeufe, [{ regel: "W3", stufe: "gelb", quelle: "zakk", text: "" }], jetzt, null).farbe).toBe("gelb");
    expect(scraperAmpel([], [], jetzt, null).farbe).toBe("rot");
  });
});

describe("Lücken aus dem Event-Pool", () => {
  it("Tage ohne Redaktions-Tipp, Events ohne Bild/Stadtteil/Adresse", () => {
    const heute = "2026-11-23";
    const events = [
      ev({ id: "t", datum: heute, tipp_des_tages: true, bild_url: "b", stadtteil: "Bilk", adresse: "x" }),
      ev({ id: "o", datum: "2026-11-24" }),
    ];
    const l = eventLuecken(events, heute);
    expect(l.tageOhneTipp).toHaveLength(13);
    expect(l.tageOhneTipp).not.toContain(heute);
    expect(l.ohneBild).toBe(1);
    expect(l.ohneStadtteil).toBe(1);
    expect(l.ohneAdresse).toBe(1);
    expect(l.eventsHeute).toBe(1);
    expect(l.events7Tage).toBe(2);
  });
});

describe("Lauf starten über GitHub (Stufe 1c)", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("ohne Token kein Start", async () => {
    vi.stubEnv("ADMIN_GITHUB_TOKEN", "");
    const r = await workflowStarten("scrape");
    expect(r.ok).toBe(false);
  });

  it("startet scrape.yml auf dem Arbeitszweig, 204 = ok", async () => {
    vi.stubEnv("ADMIN_GITHUB_TOKEN", "github_pat_test");
    const abruf = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", abruf);
    expect(await workflowStarten("scrape")).toEqual({ ok: true });
    const [url, init] = abruf.mock.calls[0];
    expect(String(url)).toMatch(/\/actions\/workflows\/scrape\.yml\/dispatches$/);
    expect(JSON.parse(init.body)).toEqual({ ref: "claude/setup-project-structure-5QNOf" });
    expect(init.headers.Authorization).toBe("Bearer github_pat_test");
  });

  it("GitHub-Fehler wird gemeldet", async () => {
    vi.stubEnv("ADMIN_GITHUB_TOKEN", "github_pat_test");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 403 })));
    expect(await workflowStarten("scrape")).toEqual({ ok: false, meldung: "GitHub antwortet mit 403" });
  });
});
