// Liefert Events per ID für die Merkliste (IDs liegen nur im Browser)
import { eventLaden, eventPoolLaden } from "@/lib/daten";
import { basisTitel, termineAmTag } from "@/lib/termine";

export async function GET(request: Request) {
  const ids = (new URL(request.url).searchParams.get("ids") ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 100);
  try {
    const pool = await eventPoolLaden();
    const { heute } = pool;
    // Gemerkt ist ein einzelner Termin; gibt es am Tag weitere Uhrzeiten, wie in den Listen „Diverse Uhrzeiten“ zeigen
    const events = (await Promise.all(ids.map((id) => eventLaden(id))))
      .filter((e) => e !== null)
      .map((e) => {
        const zeiten = termineAmTag(pool.alle, e).map((t) => t.uhrzeit).filter((z): z is string => !!z);
        return zeiten.length > 1 ? { ...e, titel: basisTitel(e.titel), uhrzeiten: zeiten } : e;
      });
    return Response.json({ heute, events });
  } catch (err) {
    console.error(`Merkliste konnte nicht geladen werden: ${err instanceof Error ? err.message : err}`);
    return Response.json({ events: [], fehler: "Events konnten nicht geladen werden." }, { status: 500 });
  }
}
