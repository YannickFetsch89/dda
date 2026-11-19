// RSS-Feed des Magazins (Plan 5.6). Schalter aus → echte 404 (T9); die IndexNow-Meldung der Pipeline folgt diesem Status (T6).
import { autorenLaden, beitraegeLaden, magazinHeute } from "@/lib/magazin-daten";
import { feedXml } from "@/lib/magazin-feed";
import { MAGAZIN_VERLINKT } from "@/lib/schalter";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

export async function GET() {
  if (!MAGAZIN_VERLINKT) {
    return new Response("Nicht gefunden", { status: 404, headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" } });
  }
  const [beitraege, autoren, heute] = await Promise.all([beitraegeLaden(), autorenLaden(), magazinHeute()]);
  return new Response(feedXml(SITE_URL, beitraege, autoren, heute), {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8", "Cache-Control": "public, max-age=300" },
  });
}
