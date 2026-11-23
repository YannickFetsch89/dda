// Admin-Bereich – Anmelden mit Mail und Passwort (Plan Admin-Dashboard 3.3). Danach folgt immer der Zwei-Faktor-Code
// (/api/admin/zwei-faktor/*); ohne aal2 liefert keine Daten-Route etwas.
// Bremse: 10 Fehlversuche je IP in 15 Minuten, danach dieselbe Meldung ohne Aufruf von Supabase.
import { anfragenImFenster, zuVieleAnfragen } from "@/lib/formulare";
import { ADMIN_COOKIE_ART } from "@/lib/admin/konfig";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { istAdminKonto } from "@/lib/admin/sitzung";
import { authClientAnfrage, nutzerClient } from "@/lib/konto/clients";
import { sitzungsCookie } from "@/lib/konto/cookies";

const FEHL = "admin-anmelden-fehl";
const FENSTER_MS = 15 * 60 * 1000;
const FALSCH = { fehler: "Mailadresse oder Passwort stimmen nicht, oder das Konto hat keinen Admin-Zugang.", code: "falsch" };

export async function POST(request: Request) {
  return adminRoute(request, { anmeldung: false }, async ({ body, ip, lokal }) => {
    const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
    const passwort = typeof body.passwort === "string" ? body.passwort : "";
    if (!email || !passwort || email.length > 254 || passwort.length > 200) return adminAntwort(400, FALSCH);
    if (anfragenImFenster(FEHL, ip) >= 10) return adminAntwort(429, FALSCH);

    const auth = authClientAnfrage();
    if (!auth) return adminAntwort(503, { fehler: "Dienst nicht erreichbar.", code: "dienst" });
    const { data, error } = await auth.auth.signInWithPassword({ email, password: passwort });
    if (error || !data.session) {
      zuVieleAnfragen(FEHL, ip, Number.MAX_SAFE_INTEGER, FENSTER_MS); // Fehlversuch zählen
      return adminAntwort(400, FALSCH);
    }

    // Nur Admins: sonst die eben entstandene Sitzung sofort wieder abmelden, gleiche Meldung wie bei falschem Passwort
    const db = nutzerClient(data.session.access_token);
    if (!db || !(await istAdminKonto(db, data.session.user.id))) {
      await auth.auth.signOut({ scope: "local" });
      zuVieleAnfragen(FEHL, ip, Number.MAX_SAFE_INTEGER, FENSTER_MS);
      return adminAntwort(400, FALSCH);
    }

    const cookie = sitzungsCookie({ access: data.session.access_token, refresh: data.session.refresh_token }, lokal, ADMIN_COOKIE_ART);
    return adminAntwort(200, { ok: true, weiter: "/admin/zwei-faktor" }, [cookie]);
  });
}
