// Aktiv-Zustand der TabBar angemeldet (Plan Mein Bereich 3.9): kein startsWith("/konto").
import { describe, expect, it } from "vitest";
import { istAktivKonto } from "@/components/client";

const aktiv = (pfad: string) =>
  ["/", "/entdecken", "/konto/fuer-dich", "/merkliste", "/konto"].filter((href) => istAktivKonto(pfad, href));

describe("istAktivKonto", () => {
  it("„Für dich“ nur auf /konto/fuer-dich, dort nicht zugleich „Profil“", () => {
    expect(aktiv("/konto/fuer-dich")).toEqual(["/konto/fuer-dich"]);
  });
  it("„Profil“ auf Übersicht und Unterseiten inkl. Willkommen", () => {
    for (const p of ["/konto", "/konto/einstellungen", "/konto/datenschutz", "/konto/interessen", "/konto/erlebt", "/konto/willkommen"]) {
      expect(aktiv(p)).toEqual(["/konto"]);
    }
  });
  it("öffentliche Konto-Seiten: kein Tab aktiv", () => {
    for (const p of ["/konto/anmelden", "/konto/passwort-neu", "/konto/passwort-vergessen", "/konto/bestaetigen", "/konto/abgemeldet"]) {
      expect(aktiv(p)).toEqual([]);
    }
  });
  it("Start nur bei /, Merkliste nur bei /merkliste, Entdecken mit Unterpfaden", () => {
    expect(aktiv("/")).toEqual(["/"]);
    expect(aktiv("/heute")).toEqual([]);
    expect(aktiv("/merkliste")).toEqual(["/merkliste"]);
    expect(aktiv("/entdecken/musik")).toEqual(["/entdecken"]);
  });
});
