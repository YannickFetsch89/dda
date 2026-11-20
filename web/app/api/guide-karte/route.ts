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
import { lokalesBild, orteLaden } from "@/lib/orte";
import {
  artInfo, entfernung, filterLesen as orteFilterLesen, orteFiltern, ortSeitePfad, profil, stadtVon,
} from "@/lib/spielstaetten";
import { fremdeHausIds, guideHaeuserLaden, spielstaettenLaden, uebersichtEintraege } from "@/lib/spielstaetten-daten";
import {
  filterLesen as spielplatzFilterLesen, filtern as spielplaetzeFiltern, ortStadtteilSlug, sortieren as spielplaetzeSortieren,
} from "@/lib/spielplaetze";
import { spielplaetzeLaden } from "@/lib/spielplaetze-daten";
import { spielplatzKartenOrte } from "@/lib/spielplaetze-karte";
import { istGueltigerTag } from "@/lib/datum";
import { wmFilterAktiv, wmFilterLesen, wmFiltern, wmKartenCache, wmSortieren } from "@/lib/weihnachtsmaerkte";
import { heuteKurz, weihnachtsmaerkteLaden } from "@/lib/weihnachtsmaerkte-daten";
import { weihnachtsmarktKartenOrte } from "@/lib/weihnachtsmaerkte-karte";

const CACHE = "public, max-age=300, stale-while-revalidate=3600";

/**
 * JSON-Antwort, ungepackt: Seit Next.js 16.4.6 packt der Server Route-Antworten selbst. Das frühere eigene gzip wurde
 * dadurch doppelt gepackt (ein Content-Encoding-Kopf, zwei gzip-Schichten) – der Browser konnte die Kartenpunkte
 * nicht mehr lesen, alle Guide-Karten zeigten „konnten nicht geladen werden“ (17./18.11.2026).
 */
function antwort(daten: unknown, cache: string = CACHE): Response {
  return new Response(JSON.stringify(daten), {
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": cache, Vary: "Accept-Encoding" },
  });
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const sp = Object.fromEntries(url.searchParams.entries());
  try {
    if (sp.hub === "kneipen") {
      const f = kneipenFilterLesen(sp);
      const orte = sortieren(kneipenFiltern(await kneipenLaden(), f), f.sort);
      return antwort(kartenOrte(orte));
    }
    if (sp.hub === "clubs") {
      const f = clubFilterLesen(sp);
      // Liste neben der Karte: erst Top-Empfehlungen, dann B, dann C – innerhalb nach gewählter Sortierung
      const sortiert = clubsSortieren(clubsFiltern(await clubsLaden(), f), f.sort);
      const orte = ["a", "b", "c"].flatMap((s) => sortiert.filter((o) => clubStufe(o) === s));
      return antwort(clubKartenOrte(orte));
    }
    if (sp.hub === "spielplaetze") {
      const f = spielplatzFilterLesen(sp);
      const orte = spielplaetzeSortieren(spielplaetzeFiltern(await spielplaetzeLaden(), f, ortStadtteilSlug), f.sort);
      return antwort(spielplatzKartenOrte(orte));
    }
    if (sp.hub === "weihnachtsmaerkte") {
      // Nur Zeiten/Stammdaten, nie ein fertig gerechneter Zustand „offen/zu“ (Antwort ist public und bis 1 h alt, Plan E5)
      const alle = await weihnachtsmaerkteLaden();
      // Gleiche Filter wie der Hub (Stufe 1b); Bezugstag = ?tag= oder heute (höchstens 5 Minuten alt)
      const f = wmFilterLesen(sp);
      const bezugTag = istGueltigerTag(sp.tag) ? sp.tag : await heuteKurz();
      const orte = wmFilterAktiv(f) ? wmSortieren(wmFiltern(alle, alle, f, bezugTag), f.sort) : alle;
      // „heute geöffnet“ ohne festen Tag ist eine fertige Tagesmenge → nicht aus geteilten Caches (Cursor-Check Stufe 1b)
      return antwort(weihnachtsmarktKartenOrte(orte, alle), wmKartenCache(sp, CACHE));
    }
    if (sp.hub === "restaurants") {
      const f = filterLesen(sp);
      const [eigene, brauhaeuser] = await Promise.all([orteLaden(["restaurant", "imbiss", "cafe"]), brauhaeuserFuerRestaurants()]);
      const orte = sortieren(filtern([...eigene, ...brauhaeuser], f), f.sort);
      // Pin-Farbe nach Art: Restaurant/Imbiss, Café, Brauhaus (Brauhäuser kommen als Kneipen mit Unterart)
      const art = new Map(orte.map((o) => [o.id, o.typ === "kneipe" ? "brauhaus" : o.typ] as const));
      return antwort(kartenOrte(orte).map((k) => ({ ...k, art: art.get(k.id) as KartenOrt["art"] })));
    }
    if (sp.hub === "orte") {
      // Ortsseiten (Plan Locations 3.8): alle Häuser mit Koordinaten, gefiltert wie /orte; nahe=<slug> → dieser Ort
      // und die 12 nächsten. Nur lokale Bilder, nie ein Google-Foto (Plan 3.13).
      const { orte: alle } = await spielstaettenLaden();
      // Dieselben Einträge wie die Liste: auch Guide-Häuser von Sälen (zakk) mit Link auf ihre Guide-Seite
      const { orte: guide } = await guideHaeuserLaden(fremdeHausIds(alle));
      const eintraege = uebersichtEintraege(alle, guide);
      const haeuser = eintraege.haeuser.filter((o) => o.latitude != null && o.longitude != null);
      let auswahl = orteFiltern(haeuser, orteFilterLesen(sp));
      const mitte = sp.nahe ? alle.find((o) => o.slug === sp.nahe) : undefined;
      if (sp.nahe) {
        // Mittelpunkt: eigene Koordinaten; ein Saal ohne eigene nimmt die der Seite (= die des Hauses, lat/lng),
        // nur im Raum Düsseldorf/Neuss/Ratingen – sonst keine Punkte.
        const zahl = (v: string | undefined) => (v != null && v !== "" && Number.isFinite(Number(v)) ? Number(v) : null);
        const pLat = zahl(sp.lat);
        const pLng = zahl(sp.lng);
        const imRaum = pLat != null && pLng != null && pLat > 50.9 && pLat < 51.5 && pLng > 6.4 && pLng < 7.2;
        const m = mitte?.latitude != null && mitte.longitude != null
          ? { lat: mitte.latitude, lng: mitte.longitude }
          : mitte && imRaum ? { lat: pLat!, lng: pLng! } : null;
        auswahl = m
          ? [...haeuser].sort((a, b) => entfernung(m, { lat: a.latitude!, lng: a.longitude! }) - entfernung(m, { lat: b.latitude!, lng: b.longitude! })).slice(0, 13)
          : [];
        // Der Saal selbst als eigener Punkt, wenn er nicht schon (als Haus) dabei ist
        if (m && mitte && !auswahl.some((o) => o.id === mitte.id)) auswahl = [{ ...mitte, latitude: m.lat, longitude: m.lng }, ...auswahl.slice(0, 12)];
      }
      return antwort(auswahl.map((o): KartenOrt => {
        const info = artInfo(profil(o).art);
        return {
          id: o.id, name: o.name, typLabel: info.wert, icon: info.icon, stadtteil: o.stadtteil ?? stadtVon(o),
          preis: null, rating: null, anzahl: null, bild: lokalesBild(o.bild_url), href: eintraege.pfad.get(o.id) ?? ortSeitePfad(o.slug),
          lat: o.latitude!, lng: o.longitude!,
        };
      }));
    }
    return Response.json({ fehler: "Unbekannter Hub" }, { status: 400 });
  } catch (err) {
    console.error(`Kartenpunkte konnten nicht geladen werden: ${err instanceof Error ? err.message : err}`);
    return Response.json({ fehler: "Kartenpunkte konnten nicht geladen werden." }, { status: 500 });
  }
}
