// Konto löschen (Plan 4.6, 5.7): nur mit aktuellem Passwort und „LÖSCHEN“. Admin-Konten nur im Supabase-Dashboard.
// Reihenfolge: Anmeldeprotokoll (konto_protokoll_loeschen) → deleteUser (Fremdschlüssel räumen profiles,
// merkliste, einwilligungen ab) → Cookies weg.
import { kontoDienstClient } from "@/lib/konto/clients";
import { cookiesLoeschen } from "@/lib/konto/cookies";
import { MELDUNG } from "@/lib/konto/konfig";
import { passwortStimmt } from "@/lib/konto/passwort";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

export const POST = kontoRoute(
  {
    anmeldung: true, json: true, aendernd: true, ohneMindestalter: true,
    limit: { name: "loeschen", max: 3, fensterMs: ZEIT.STUNDE },
  },
  async (ctx) => {
    const s = ctx.sitzung!;
    if (ctx.profil!.rolle === "admin") {
      return kontoAntwort(403, { fehler: "Admin-Konten bitte im Supabase-Dashboard löschen.", code: "admin" });
    }
    if (ctx.body.bestaetigung !== "LÖSCHEN") {
      return kontoAntwort(400, { fehler: "Bitte tippe LÖSCHEN zur Bestätigung.", code: "bestaetigung" });
    }
    const passwort = typeof ctx.body.passwort === "string" ? ctx.body.passwort : "";
    if (!passwort || !s.email || !(await passwortStimmt(s.email, passwort))) {
      return kontoAntwort(403, { fehler: "Das Passwort stimmt nicht.", code: "passwort" });
    }
    const dienst = kontoDienstClient();
    if (!dienst) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });

    const protokoll = await dienst.rpc("konto_protokoll_loeschen", { nutzer: s.nutzerId });
    if (protokoll.error) {
      console.error(`Konto löschen: Protokoll nicht gelöscht (${protokoll.error.code})`);
      return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt. Bitte versuch es später noch einmal." });
    }
    const { error } = await dienst.auth.admin.deleteUser(s.nutzerId);
    if (error) {
      console.error(`Konto löschen: deleteUser fehlgeschlagen (${error.code ?? error.status})`);
      return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt. Bitte versuch es später noch einmal." });
    }
    ctx.ohneHinweis = true;
    ctx.setCookies.push(...cookiesLoeschen(ctx.lokal));
    return kontoAntwort(200, { ok: true, meldung: MELDUNG.geloescht });
  },
);
