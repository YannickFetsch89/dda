// Tests zu Stufe 4 (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.9): Newsletter-Tokens und Anmelde-Regeln
import { describe, expect, it } from "vitest";
import { anmeldungPlanen, MAX_MAILS, newsletterToken, newsletterTokenPruefen } from "@/lib/newsletter";

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

describe("Anmeldung planen", () => {
  const jetzt = Date.parse("2026-11-23T12:00:00Z");
  const b = (x: Partial<{ bestaetigt_am: string | null; bestaetigung_gesendet_am: string | null; mails_gesendet: number }>) => ({
    id: ID,
    bestaetigt_am: null,
    bestaetigung_gesendet_am: null,
    mails_gesendet: 0,
    ...x,
  });
  it("neu, bestätigt, ausstehend", () => {
    expect(anmeldungPlanen(null, jetzt)).toBe("anlegen");
    expect(anmeldungPlanen(b({ bestaetigt_am: "2026-11-01T00:00:00Z" }), jetzt)).toBe("nichts");
    expect(anmeldungPlanen(b({}), jetzt)).toBe("nichts");
  });
  it("erneut nur nach 24 Stunden und höchstens dreimal", () => {
    expect(anmeldungPlanen(b({ bestaetigung_gesendet_am: "2026-11-23T01:00:00Z", mails_gesendet: 1 }), jetzt)).toBe("nichts");
    expect(anmeldungPlanen(b({ bestaetigung_gesendet_am: "2026-11-22T01:00:00Z", mails_gesendet: 1 }), jetzt)).toBe("erneut_senden");
    expect(anmeldungPlanen(b({ bestaetigung_gesendet_am: "2026-11-01T01:00:00Z", mails_gesendet: MAX_MAILS }), jetzt)).toBe("nichts");
  });
});
