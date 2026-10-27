// Liefert Events per ID für die Merkliste (IDs liegen nur im Browser)
import { eventLaden, eventPoolLaden } from "@/lib/daten";

export async function GET(request: Request) {
  const ids = (new URL(request.url).searchParams.get("ids") ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 100);
  try {
    const { heute } = await eventPoolLaden();
    const events = (await Promise.all(ids.map((id) => eventLaden(id)))).filter((e) => e !== null);
    return Response.json({ heute, events });
  } catch (err) {
    console.error(`Merkliste konnte nicht geladen werden: ${err instanceof Error ? err.message : err}`);
    return Response.json({ events: [], fehler: "Events konnten nicht geladen werden." }, { status: 500 });
  }
}
