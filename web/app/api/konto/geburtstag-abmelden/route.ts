// Geburtstagsmail abbestellen über die Seite /konto/geburtstag-abmelden (Plan Geburtstagsmail G4, Kontenplan 13a).
// POST { token } – erst der Klick auf den Button schickt das (nicht schon der Aufruf, wegen Link-Scannern).
// Ohne Anmeldung, Bremslimit 30 je IP und Stunde, 404 bei ausgeschaltetem KONTEN_AKTIV (kontoRoute).
// Gültiges Token → immer dieselbe Antwort, auch wenn schon abgemeldet oder das Konto gelöscht ist.
import { kontoDienstClient } from "@/lib/konto/clients";
import { geburtstagAbmelden, geburtstagTokenPruefen } from "@/lib/konto/geburtstag";
import { MELDUNG } from "@/lib/konto/konfig";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

const ABGEMELDET = "Du bekommst keine Geburtstagsmails mehr. Ändern kannst du das jederzeit im Konto.";
const UNGUELTIG = "Der Link ist ungültig. Du kannst die Geburtstagsmail auch im Konto unter „Datenschutz“ abschalten.";

export const POST = kontoRoute(
  { anmeldung: false, json: true, aendernd: true, limit: { name: "geburtstag-abmelden", max: 30, fensterMs: ZEIT.STUNDE } },
  async ({ body }) => {
    const nutzerId = geburtstagTokenPruefen(body.token);
    if (!nutzerId) return kontoAntwort(400, { fehler: UNGUELTIG, code: "token" });
    const dienst = kontoDienstClient();
    if (!dienst) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    const r = await geburtstagAbmelden(dienst, nutzerId);
    if (r !== "ok") return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    return kontoAntwort(200, { ok: true, meldung: ABGEMELDET });
  },
);
