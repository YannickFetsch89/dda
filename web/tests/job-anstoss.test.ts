// Mail-Jobs anstoßen: höchstens ein Start je 5 Minuten, ein Aufruf in der Sperrzeit wird einmal nachgeholt.
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
const starten = vi.hoisted(() => vi.fn());
vi.mock("@/lib/admin/github", () => ({ workflowStarten: starten }));

const { ABSTAND_MS, anstossPlanen, jobAnstossen } = await import("@/lib/job-anstoss");

describe("anstossPlanen", () => {
  it("erster Aufruf startet sofort", () => {
    expect(anstossPlanen(null, false, 1_000)).toEqual({ art: "jetzt" });
  });
  it("nach Ablauf der Sperrzeit wieder sofort", () => {
    expect(anstossPlanen(0, false, ABSTAND_MS)).toEqual({ art: "jetzt" });
  });
  it("in der Sperrzeit einmal ans Ende legen", () => {
    expect(anstossPlanen(0, false, 60_000)).toEqual({ art: "spaeter", in_ms: ABSTAND_MS - 60_000 });
  });
  it("schon geplant → nichts (keine Lawine)", () => {
    expect(anstossPlanen(0, true, 60_000)).toEqual({ art: "nichts" });
    expect(anstossPlanen(null, true, 60_000)).toEqual({ art: "nichts" });
  });
});

describe("jobAnstossen", () => {
  it("gescheiterter Start sperrt nicht: der nächste Aufruf stößt sofort wieder an (Cursor-Prüfung 24.11.2026)", async () => {
    starten.mockReset();
    starten.mockResolvedValueOnce({ ok: false, meldung: "GitHub antwortet mit 403" }).mockResolvedValue({ ok: true });
    const fehler = vi.spyOn(console, "error").mockImplementation(() => {});
    jobAnstossen("meldung-mail", { aufgabe: "senden" });
    await vi.waitFor(() => expect(fehler).toHaveBeenCalled());
    jobAnstossen("meldung-mail", { aufgabe: "senden" });
    expect(starten).toHaveBeenCalledTimes(2);
    fehler.mockRestore();
  });

  it("erfolgreicher Start: weitere Aufrufe in der Sperrzeit starten nicht sofort", async () => {
    starten.mockReset();
    starten.mockResolvedValue({ ok: true });
    vi.useFakeTimers();
    try {
      jobAnstossen("geburtstag", { aufgabe: "senden" });
      jobAnstossen("geburtstag", { aufgabe: "senden" });
      jobAnstossen("geburtstag", { aufgabe: "senden" });
      expect(starten).toHaveBeenCalledTimes(1);
      await vi.advanceTimersByTimeAsync(ABSTAND_MS);
      expect(starten).toHaveBeenCalledTimes(2);
    } finally {
      vi.useRealTimers();
    }
  });
});
