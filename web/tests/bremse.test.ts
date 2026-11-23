// Bremse gegen Massenabrufe der Guides (Ausfall 23.11.2026)
import { describe, expect, it } from "vitest";
import { bremsAdresse, bremseZuruecksetzen, gebremst } from "@/lib/bremse";
import { config as proxyConfig } from "@/proxy";

describe("Bremse", () => {
  it("ab dem 41. Aufruf je Minute und Adresse, danach neues Fenster", () => {
    bremseZuruecksetzen();
    const t0 = 1_000_000;
    for (let i = 0; i < 40; i++) expect(gebremst("1.2.3.4", t0 + i)).toBe(false);
    expect(gebremst("1.2.3.4", t0 + 50)).toBe(true);
    expect(gebremst("5.6.7.8", t0 + 50)).toBe(false); // andere Adresse unberührt
    expect(gebremst("1.2.3.4", t0 + 61_000)).toBe(false); // neues Fenster
  });
  it("Adresse aus X-Real-IP (nginx), sonst letzter X-Forwarded-For-Eintrag", () => {
    expect(bremsAdresse(new Headers({ "x-real-ip": "9.9.9.9", "x-forwarded-for": "1.1.1.1" }))).toBe("9.9.9.9");
    expect(bremsAdresse(new Headers({ "x-forwarded-for": "1.1.1.1, 2.2.2.2" }))).toBe("2.2.2.2");
  });
  it("Proxy läuft für alle Guide-Pfade, auch die Hub-Seiten", () => {
    expect(proxyConfig.matcher).toEqual(expect.arrayContaining(["/guides", "/guides/:path*"]));
  });
});
