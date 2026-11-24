// Tests zu Stufe 4 (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.9): Newsletter-Tokens und Anmelde-Regeln
import { describe, expect, it } from "vitest";
import { anmeldungPlanen, istOneClick, MAX_MAILS, newsletterToken, newsletterTokenPruefen } from "@/lib/newsletter";

const ID = "11111111-1111-4111-8111-111111111111";
const S = "testschluessel";
// Gleiche Werte wie tests/test_newsletter_bestaetigung.py (Python erzeugt die Tokens im Job)
const PY_BESTAETIGEN = `${ID}.fsGeRv_rV1jKlVNHfzGT4pIANAPYL-BZMiTKbOt0FL0`;
const PY_ABMELDEN = `${ID}.FRdGhX1Ca8LeXmS471jk01xpskKmgV_dcIU8J4lzkNs`;

describe("Tokens", () => {
  it("gleich wie im Python-Job", () => {
    expect(newsletterToken(ID, "bestaetigen", S)).toBe(PY_BESTAETIGEN);
    expect(newsletterToken(ID, "abmelden", S)).toBe(PY_ABMELDEN);
  });
  it("gilt nur für seinen Zweck und Schlüssel", () => {
    expect(newsletterTokenPruefen(PY_BESTAETIGEN, "bestaetigen", S)).toBe(ID);
    expect(newsletterTokenPruefen(PY_BESTAETIGEN, "abmelden", S)).toBeNull();
    expect(newsletterTokenPruefen(PY_ABMELDEN, "abmelden", "anderer")).toBeNull();
    expect(newsletterTokenPruefen(PY_ABMELDEN, "abmelden", undefined)).toBeNull();
    expect(newsletterTokenPruefen(`${ID}.kaputt`, "abmelden", S)).toBeNull();
    expect(newsletterTokenPruefen("keine-id.x", "abmelden", S)).toBeNull();
    expect(newsletterTokenPruefen(42, "abmelden", S)).toBeNull();
  });
});

describe("Schlüssel mit Zeilenumbruch (Livetest 24.11.2026)", () => {
  it("Secret roh mit Umbruch prüft dieselben Links wie der Mail-Job", () => {
    expect(newsletterTokenPruefen(PY_BESTAETIGEN, "bestaetigen", `${S}\n`)).toBe(ID);
    expect(newsletterTokenPruefen(PY_BESTAETIGEN, "bestaetigen", ` test\r\nschluessel\t`)).toBe(ID);
    expect(newsletterToken(ID, "bestaetigen", `${S}\r\n`)).toBe(PY_BESTAETIGEN);
  });
  it("nur Leerraum gilt als fehlender Schlüssel", () => {
    expect(newsletterTokenPruefen(PY_BESTAETIGEN, "bestaetigen", " \n")).toBeNull();
  });
});

describe("Anmeldung planen", () => {
  const jetzt = Date.parse("2026-11-23T12:00:00Z");
  const b = (x: Partial<{ bestaetigt_am: string | null; bestaetigung_zugestellt_am: string | null; mails_gesendet: number }>) => ({
    id: ID,
    bestaetigt_am: null,
    bestaetigung_gesendet_am: null,
    bestaetigung_zugestellt_am: null,
    mails_gesendet: 0,
    ...x,
  });
  it("neu, bestätigt, ausstehend", () => {
    expect(anmeldungPlanen(null, jetzt)).toBe("anlegen");
    expect(anmeldungPlanen(b({ bestaetigt_am: "2026-11-01T00:00:00Z" }), jetzt)).toBe("nichts");
    expect(anmeldungPlanen(b({}), jetzt)).toBe("nichts");
  });
  it("erneut nur nach 24 Stunden und höchstens dreimal", () => {
    expect(anmeldungPlanen(b({ bestaetigung_zugestellt_am: "2026-11-23T01:00:00Z", mails_gesendet: 1 }), jetzt)).toBe("nichts");
    expect(anmeldungPlanen(b({ bestaetigung_zugestellt_am: "2026-11-22T01:00:00Z", mails_gesendet: 1 }), jetzt)).toBe("erneut_senden");
    expect(anmeldungPlanen(b({ bestaetigung_zugestellt_am: "2026-11-01T01:00:00Z", mails_gesendet: MAX_MAILS }), jetzt)).toBe("nichts");
  });
});

describe("Nachträge Cursor-Prüfung Stufe 4", () => {
  it("One-Click nur mit Formular-Body „List-Unsubscribe=One-Click“ (RFC 8058, Befund 1)", () => {
    const form = "application/x-www-form-urlencoded";
    expect(istOneClick(form, "List-Unsubscribe=One-Click")).toBe(true);
    expect(istOneClick(`${form}; charset=utf-8`, "List-Unsubscribe=One-Click\r\n")).toBe(true);
    expect(istOneClick(form, "")).toBe(false);
    expect(istOneClick(form, "List-Unsubscribe=One-Click&x=1")).toBe(false);
    expect(istOneClick("application/json", "List-Unsubscribe=One-Click")).toBe(false);
    expect(istOneClick(null, "List-Unsubscribe=One-Click")).toBe(false);
  });
});
