// Aktiv-Zustand der TabBar angemeldet (Plan Mein Bereich 3.9, Tabs seit 27.11.2026: Start · Events · Guides ·
// Merkliste · Profil): kein startsWith("/konto"), Events und Guides umfassen ihre ganze Welt.
import { describe, expect, it } from "vitest";
import { istAktivKonto, istEventSeite, istGuideSeite } from "@/components/client";

const aktiv = (pfad: string) =>
  ["/", "/entdecken", "/guides", "/merkliste", "/konto"].filter((href) => istAktivKonto(pfad, href));

describe("istAktivKonto", () => {
  it("„Profil“ auf Übersicht und Unterseiten inkl. Willkommen und „Für dich“", () => {
    for (const p of ["/konto", "/konto/einstellungen", "/konto/datenschutz", "/konto/interessen", "/konto/erlebt", "/konto/willkommen", "/konto/fuer-dich"]) {
      expect(aktiv(p)).toEqual(["/konto"]);
    }
  });
  it("öffentliche Konto-Seiten: kein Tab aktiv", () => {
    for (const p of ["/konto/anmelden", "/konto/passwort-neu", "/konto/passwort-vergessen", "/konto/bestaetigen", "/konto/abgemeldet"]) {
      expect(aktiv(p)).toEqual([]);
    }
  });
  it("Start nur bei /, Merkliste nur bei /merkliste", () => {
    expect(aktiv("/")).toEqual(["/"]);
    expect(aktiv("/merkliste")).toEqual(["/merkliste"]);
  });
  it("„Events“ auf allen Event-Seiten", () => {
    for (const p of ["/entdecken", "/heute", "/morgen", "/tag/2026-11-28", "/wochenende", "/ausblick", "/kostenlos", "/kategorie/musik", "/event/abc", "/stadtteil/bilk"]) {
      expect(aktiv(p)).toEqual(["/entdecken"]);
    }
  });
  it("„Guides“ auf Hubs, Guide-Seiten und Veranstaltungsorten", () => {
    for (const p of ["/guides", "/guides/clubs", "/guides/restaurants-cafes/x", "/orte", "/orte/zakk"]) {
      expect(aktiv(p)).toEqual(["/guides"]);
    }
  });
  it("Präfixe nur ganze Pfadteile", () => {
    expect(istEventSeite("/tagung")).toBe(false);
    expect(istEventSeite("/eventmelden")).toBe(false);
    expect(istEventSeite("/event-melden")).toBe(false);
    expect(istGuideSeite("/guidesx")).toBe(false);
    expect(aktiv("/magazin")).toEqual([]);
  });
});
