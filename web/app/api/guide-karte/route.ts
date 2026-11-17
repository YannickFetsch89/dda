// Kartenpunkte der Guide-Hubs für die Kartenansicht – gefiltert wie die Hub-Seite.
// Die Seite schickt der Karte nur ihre Filter-URL; die Punkte (bei Restaurants über 600) kommen hier
// nach, statt die erste HTML-Antwort aufzublähen. Daten über orteLaden ("use cache"), Antwort im
// Browser/Proxy kurz zwischengespeichert.
//   /api/guide-karte?hub=restaurants&typ=restaurant,cafe&stadtteil=bilk
//   /api/guide-karte?hub=kneipen&art=bar&stadtteil=altstadt
//   /api/guide-karte?hub=clubs&stufe=a,c&genre=techno
import type { KartenOrt } from "@/components/guide-karte";
import { kartenOrte } from "@/components/ort-karten";
import { clubFilterLesen, clubsFiltern, clubsSortieren, clubStufe } from "@/lib/clubs";
import { clubKartenOrte } from "@/lib/clubs-karte";
import { clubsLaden } from "@/lib/clubs-daten";
import { filterLesen, filtern, sortieren } from "@/lib/guide-filter";
import { brauhaeuserFuerRestaurants, kneipenLaden } from "@/lib/kneipen-daten";
import { filterLesen as kneipenFilterLesen, filtern as kneipenFiltern } from "@/lib/kneipen";
import { orteLaden } from "@/lib/orte";
import {
  filterLesen as spielplatzFilterLesen, filtern as spielplaetzeFiltern, ortStadtteilSlug, sortieren as spielplaetzeSortieren,
} from "@/lib/spielplaetze";
import { spielplaetzeLaden } from "@/lib/spielplaetze-daten";
import { spielplatzKartenOrte } from "@/lib/spielplaetze-karte";
import { istGueltigerTag } from "@/lib/datum";
import { wmFilterAktiv, wmFilterLesen, wmFiltern, wmSortieren } from "@/lib/weihnachtsmaerkte";
import { heuteKurz, weihnachtsmaerkteLaden } from "@/lib/weihnachtsmaerkte-daten";
import { weihnachtsmarktKartenOrte } from "@/lib/weihnachtsmaerkte-karte";

const CACHE = "public, max-age=300, stale-while-revalidate=3600";

/** JSON-Antwort, gzip-gepackt wenn der Browser es kann (Next packt Route-Antworten nicht selbst; ~200 KB → ~30 KB). */
function antwort(request: Request, daten: unknown): Response {
  const text = JSON.stringify(daten);
  const kopf: Record<string, string> = { "Content-Type": "application/json; charset=utf-8", "Cache-Control": CACHE, Vary: "Accept-Encoding" };
  if (!/\bgzip\b/.test(request.headers.get("accept-encoding") ?? "")) return new Response(text, { headers: kopf });
  const gepackt = new Blob([text]).stream().pipeThrough(new CompressionStream("gzip"));
  return new Response(gepackt, { headers: { ...kopf, "Content-Encoding": "gzip" } });
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const sp = Object.fromEntries(url.searchParams.entries());
  try {
    if (sp.hub === "kneipen") {
      const f = kneipenFilterLesen(sp);
      const orte = sortieren(kneipenFiltern(await kneipenLaden(), f), f.sort);
      return antwort(request, kartenOrte(orte));
    }
    if (sp.hub === "clubs") {
      const f = clubFilterLesen(sp);
      // Liste neben der Karte: erst Top-Empfehlungen, dann B, dann C – innerhalb nach gewählter Sortierung
      const sortiert = clubsSortieren(clubsFiltern(await clubsLaden(), f), f.sort);
      const orte = ["a", "b", "c"].flatMap((s) => sortiert.filter((o) => clubStufe(o) === s));
      return antwort(request, clubKartenOrte(orte));
    }
    if (sp.hub === "spielplaetze") {
      const f = spielplatzFilterLesen(sp);
      const orte = spielplaetzeSortieren(spielplaetzeFiltern(await spielplaetzeLaden(), f, ortStadtteilSlug), f.sort);
      return antwort(request, spielplatzKartenOrte(orte));
    }
    if (sp.hub === "weihnachtsmaerkte") {
      // Nur Zeiten/Stammdaten, nie ein fertig gerechneter Zustand „offen/zu“ (Antwort ist public und bis 1 h alt, Plan E5)
      const alle = await weihnachtsmaerkteLaden();
      // Gleiche Filter wie der Hub (Stufe 1b); Bezugstag = ?tag= oder heute (höchstens 5 Minuten alt)
      const f = wmFilterLesen(sp);
      const bezugTag = istGueltigerTag(sp.tag) ? sp.tag : await heuteKurz();
      const orte = wmFilterAktiv(f) ? wmSortieren(wmFiltern(alle, alle, f, bezugTag), f.sort) : alle;
      return antwort(request, weihnachtsmarktKartenOrte(orte, alle));
    }
    if (sp.hub === "restaurants") {
      const f = filterLesen(sp);
      const [eigene, brauhaeuser] = await Promise.all([orteLaden(["restaurant", "imbiss", "cafe"]), brauhaeuserFuerRestaurants()]);
      const orte = sortieren(filtern([...eigene, ...brauhaeuser], f), f.sort);
      // Pin-Farbe nach Art: Restaurant/Imbiss, Café, Brauhaus (Brauhäuser kommen als Kneipen mit Unterart)
      const art = new Map(orte.map((o) => [o.id, o.typ === "kneipe" ? "brauhaus" : o.typ] as const));
      return antwort(request, kartenOrte(orte).map((k) => ({ ...k, art: art.get(k.id) as KartenOrt["art"] })));
    }
    return Response.json({ fehler: "Unbekannter Hub" }, { status: 400 });
  } catch (err) {
    console.error(`Kartenpunkte konnten nicht geladen werden: ${err instanceof Error ? err.message : err}`);
    return Response.json({ fehler: "Kartenpunkte konnten nicht geladen werden." }, { status: 500 });
  }
}
