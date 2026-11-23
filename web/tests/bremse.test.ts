// Bremse gegen Massenabrufe der Guides (Ausfall 23.11.2026)
import { describe, expect, it } from "vitest";
import { bremsAdresse, bremseZuruecksetzen, gebremst, istGuideUebersicht, parameterBereinigen, sammelGebremst, sammelGrenzePruefen } from "@/lib/bremse";
import { config as proxyConfig } from "@/proxy";

describe("Bremse je Adresse", () => {
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

describe("Gemeinsame Grenze der Guide-Übersichten", () => {
  it("ab dem 61. Aufruf je Minute über alle Adressen, nur für /guides/<hub>", () => {
    bremseZuruecksetzen();
    const t0 = 2_000_000;
    for (let i = 0; i < 60; i++) expect(sammelGebremst("/guides/restaurants-cafes", t0 + i)).toBe(false);
    expect(sammelGebremst("/guides/restaurants-cafes", t0 + 70)).toBe(true);
    expect(sammelGebremst("/guides/clubs", t0 + 70)).toBe(false);
    expect(sammelGebremst("/guides/restaurants-cafes", t0 + 61_000)).toBe(false);
    expect(istGuideUebersicht("/guides/restaurants-cafes")).toBe(true);
    expect(istGuideUebersicht("/guides/restaurants-cafes/zum-schiffchen")).toBe(false);
    expect(istGuideUebersicht("/guides")).toBe(false);
  });
});

describe("Saubere Adressen der Guide-Übersichten", () => {
  const p = (s: string) => new URLSearchParams(s);
  it("unbekannte und doppelte Parameter weg, _rsc bleibt, bekannte bleiben", () => {
    expect(parameterBereinigen("/guides/restaurants-cafes", p("stadtteil=bilk&_=123&utm_source=x"))).toBe("stadtteil=bilk");
    expect(parameterBereinigen("/guides/restaurants-cafes", p("kueche=a,b&kueche=c"))).toBe("kueche=a,b");
    expect(parameterBereinigen("/guides/restaurants-cafes", p("stadtteil=bilk&_rsc=abc"))).toBeNull();
    expect(parameterBereinigen("/guides/restaurants-cafes", p(""))).toBeNull();
    expect(parameterBereinigen("/guides/spielplaetze", p("irgendwas=1"))).toBeNull(); // ohne feste Liste: nichts
  });
  it("gemeinsame Grenze: gecachte Übersicht nur mit Filtern, andere immer", () => {
    expect(sammelGrenzePruefen("/guides/restaurants-cafes", p(""))).toBe(false);
    expect(sammelGrenzePruefen("/guides/restaurants-cafes", p("_rsc=x"))).toBe(false);
    expect(sammelGrenzePruefen("/guides/restaurants-cafes", p("stadtteil=bilk"))).toBe(true);
    expect(sammelGrenzePruefen("/guides/kneipen-bars", p(""))).toBe(true);
  });
});
