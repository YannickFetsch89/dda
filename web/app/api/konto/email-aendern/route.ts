// Mailadresse im Konto ändern (17.11.2026, Wunsch des Auftraggebers; vorher „schreib uns“, Plan 19 Punkt 4).
// { neu, aktuell }: aktuelles Passwort nötig. Supabase schickt mit „Secure email change“ je eine Bestätigungsmail an
// die alte und die neue Adresse; die neue Adresse gilt erst, wenn beide Links bestätigt sind (/konto/bestaetigen,
// art=email). Je Konto höchstens 5 Fehlversuche beim Passwort in 15 Minuten, höchstens 5 Änderungen pro Stunde.
import { anfragenImFenster, zuVieleAnfragen } from "@/lib/formulare";
import { MELDUNG } from "@/lib/konto/konfig";
import { mailAendern } from "@/lib/konto/passwort";
import { adresseNormal } from "@/lib/konto/pruefungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const FEHL = "konto-email-aendern-fehl";

export const POST = kontoRoute(
  { anmeldung: true, json: true, aendernd: true, limit: { name: "email-aendern", max: 5, fensterMs: ZEIT.STUNDE } },
  async (ctx) => {
    const s = ctx.sitzung!;
    if (anfragenImFenster(FEHL, s.nutzerId) >= 5) return kontoAntwort(429, { fehler: MELDUNG.zuViele, code: "zu_viele" });
    const neu = adresseNormal(ctx.body.neu);
    if (!neu) return kontoAntwort(400, { fehler: "Bitte gib eine gültige Mailadresse ein.", code: "adresse" });
    const aktuell = typeof ctx.body.aktuell === "string" ? ctx.body.aktuell : "";
    if (!aktuell) return kontoAntwort(400, { fehler: "Bitte gib dein aktuelles Passwort ein.", code: "aktuell" });
    if (!s.email) return kontoAntwort(400, { fehler: MELDUNG.ungueltig });
    if (neu === s.email.toLowerCase()) return kontoAntwort(400, { fehler: "Das ist schon deine Mailadresse.", code: "gleich" });

    const r = await mailAendern(s.email, aktuell, neu);
    if (!r.ok) {
      if (r.grund === "aktuell_falsch") {
        zuVieleAnfragen(FEHL, s.nutzerId, Number.MAX_SAFE_INTEGER, ZEIT.VIERTELSTUNDE);
        return kontoAntwort(403, { fehler: "Das aktuelle Passwort stimmt nicht.", code: "aktuell_falsch" });
      }
      if (r.grund === "vorhanden") return kontoAntwort(409, { fehler: MELDUNG.schonRegistriert, code: "vorhanden" });
      return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt." });
    }
    return kontoAntwort(200, { ok: true, meldung: MELDUNG.mailAendernUnterwegs });
  },
);
