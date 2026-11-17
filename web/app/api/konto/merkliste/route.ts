// Konto-Merkliste lesen (Plan 5.4 Schritt 1, 5.5): IDs, neueste zuerst; mit ?mit=events auch die Events.
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";
import { eventsFuerIds } from "@/lib/konto/merkliste-events";

export const GET = kontoRoute(
  { anmeldung: true, limit: { name: "merkliste", max: 120, fensterMs: ZEIT.STUNDE } },
  async (ctx) => {
    const { data, error } = await ctx.db!
      .from("merkliste")
      .select("event_id, gemerkt_am")
      .order("gemerkt_am", { ascending: false })
      .limit(1000);
    if (error) return kontoAntwort(503, { fehler: "Die Merkliste ist gerade nicht erreichbar." });
    const ids = (data ?? []).map((z) => z.event_id as string);

    if (new URL(ctx.request.url).searchParams.get("mit") !== "events") return kontoAntwort(200, { ok: true, ids });
    try {
      const { heute, events } = await eventsFuerIds(ids);
      return kontoAntwort(200, { ok: true, ids, heute, events });
    } catch (err) {
      console.error(`Konto-Merkliste: Events nicht geladen (${err instanceof Error ? err.name : "unbekannt"})`);
      return kontoAntwort(200, { ok: true, ids, events: [], fehler: "Events konnten nicht geladen werden." });
    }
  },
);
