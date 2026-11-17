// Abmelden (Plan 3.2, 5.6): { ueberall: boolean }. „Dieses Gerät“ = scope local, „Überall“ = scope global.
// Beide Cookies werden in jedem Fall gelöscht, auch wenn Supabase nicht antwortet.
import { authClientAnfrage } from "@/lib/konto/clients";
import { cookiesLoeschen } from "@/lib/konto/cookies";
import { kontoAntwort, kontoRoute } from "@/lib/konto/route";

export const POST = kontoRoute(
  { anmeldung: true, json: true, aendernd: true, resetErlaubt: true, ohneMindestalter: true },
  async (ctx) => {
    const scope = ctx.body.ueberall === true ? "global" : "local";
    const auth = authClientAnfrage();
    if (auth) {
      // admin.signOut(jwt, scope) meldet mit dem Token der Person selbst ab (kein Service-Key nötig)
      const { error } = await auth.auth.admin.signOut(ctx.sitzung!.access, scope);
      if (error) console.warn(`Abmelden: Supabase meldet ${error.code ?? error.status ?? "Fehler"}`);
    }
    ctx.ohneHinweis = true;
    ctx.setCookies.push(...cookiesLoeschen(ctx.lokal));
    return kontoAntwort(200, { ok: true });
  },
);
