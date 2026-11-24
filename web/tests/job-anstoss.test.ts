// Mail-Jobs anstoßen: höchstens ein Start je 5 Minuten, ein Aufruf in der Sperrzeit wird einmal nachgeholt.
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("@/lib/admin/github", () => ({ workflowStarten: vi.fn() }));

const { ABSTAND_MS, anstossPlanen } = await import("@/lib/job-anstoss");

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
