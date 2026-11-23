// Admin-Bereich – Zwei-Faktor-Code prüfen. Bei Erfolg neue Tokens mit aal2 ins Cookie, Anmeldung ins Protokoll.
// Bremse: 10 falsche Codes je IP in 15 Minuten.
import { anfragenImFenster, zuVieleAnfragen } from "@/lib/formulare";
import { ADMIN_COOKIE_ART } from "@/lib/admin/konfig";
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { zweiFaktorPruefen } from "@/lib/admin/zwei-faktor";
import { nutzerClient } from "@/lib/konto/clients";
import { sitzungsCookie } from "@/lib/konto/cookies";

const FEHL = "admin-zwei-faktor-fehl";
const FENSTER_MS = 15 * 60 * 1000;
const FALSCH = { fehler: "Der Code stimmt nicht.", code: "falsch" };

export async function POST(request: Request) {
  return adminRoute(request, { zweiFaktor: false }, async ({ admin, body, ip, lokal, setCookies }) => {
    const faktorId = typeof body.faktorId === "string" ? body.faktorId : "";
    const code = typeof body.code === "string" ? body.code.replace(/\s+/g, "") : "";
    if (!/^[0-9a-f-]{36}$/i.test(faktorId) || !/^\d{6}$/.test(code)) return adminAntwort(400, FALSCH, setCookies);
    if (anfragenImFenster(FEHL, ip) >= 10) return adminAntwort(429, FALSCH, setCookies);

    const neu = await zweiFaktorPruefen(admin!.sitzung, faktorId, code);
    if (!neu) {
      zuVieleAnfragen(FEHL, ip, Number.MAX_SAFE_INTEGER, FENSTER_MS);
      return adminAntwort(400, FALSCH, setCookies);
    }
    const db = nutzerClient(neu.access);
    if (db) await protokollieren(db, { aktion: "anmelden" });
    // Das neue Cookie ersetzt ein eventuell oben erneuertes (gleicher Name, später in der Liste)
    return adminAntwort(200, { ok: true, weiter: "/admin" }, [...setCookies, sitzungsCookie(neu, lokal, ADMIN_COOKIE_ART)]);
  });
}
