// Ein Event merken (PUT) bzw. entfernen (DELETE) – beides idempotent (Plan 5.5).
// PUT antwortet { gespeichert: 'konto' } oder, für ein Event, das ohne Einwilligung (b) nicht ins Konto darf,
// neutral { gespeichert: 'geraet' } (Plan 5.8). Beides 200, ohne Grund.
import { kontoAntwort, kontoRoute, dbFehlercode, ZEIT } from "@/lib/konto/route";
import { uuidGueltig } from "@/lib/konto/pruefungen";

const OPT = { anmeldung: true, aendernd: true, limit: { name: "merken", max: 300, fensterMs: ZEIT.STUNDE } } as const;

export const PUT = kontoRoute(OPT, async (ctx, { params }) => {
  const { id } = await params;
  if (!uuidGueltig(id)) return kontoAntwort(400, { fehler: "Unbekanntes Event.", code: "event" });
  const { error } = await ctx.db!
    .from("merkliste")
    .upsert({ nutzer_id: ctx.sitzung!.nutzerId, event_id: id.toLowerCase(), quelle: "konto" }, {
      onConflict: "nutzer_id,event_id",
      ignoreDuplicates: true,
    });
  if (!error) return kontoAntwort(200, { ok: true, gespeichert: "konto" });

  const code = dbFehlercode(error);
  if (code === "nur_geraet") return kontoAntwort(200, { ok: true, gespeichert: "geraet" });
  if (code === "merkliste_voll") {
    return kontoAntwort(409, { fehler: "Deine Merkliste ist voll (höchstens 500 Events).", code });
  }
  if (code === "mindestalter_fehlt") return kontoAntwort(403, { fehler: "Bitte bestätige zuerst dein Alter.", code });
  if (error.code === "23503") return kontoAntwort(404, { fehler: "Unbekanntes Event.", code: "event" });
  console.error(`Merken fehlgeschlagen (${error.code})`);
  return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt." });
});

export const DELETE = kontoRoute(OPT, async (ctx, { params }) => {
  const { id } = await params;
  if (!uuidGueltig(id)) return kontoAntwort(400, { fehler: "Unbekanntes Event.", code: "event" });
  const { error } = await ctx.db!
    .from("merkliste")
    .delete()
    .eq("nutzer_id", ctx.sitzung!.nutzerId)
    .eq("event_id", id.toLowerCase());
  if (error) {
    console.error(`Entfernen fehlgeschlagen (${error.code})`);
    return kontoAntwort(500, { fehler: "Das hat leider nicht geklappt." });
  }
  return kontoAntwort(200, { ok: true });
});
