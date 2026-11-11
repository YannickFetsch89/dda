// sitemap.xml: feste Seiten, Tagesansichten der nächsten 14 Tage und alle aktuellen Events.
// Nutzt denselben Event-Pool wie die Seiten (Cache 10 min).
import type { MetadataRoute } from "next";
import { istAbgelaufen } from "@/lib/abgelaufen";
import { eventPoolLaden } from "@/lib/daten";
import { findetStatt, plusTage, zeitraumAuflösen } from "@/lib/datum";
import { kneipenLaden } from "@/lib/kneipen-daten";
import { clubsLaden } from "@/lib/clubs-daten";
import { orteLaden } from "@/lib/orte";
import { ortPfad } from "@/components/ort-karten";
import { KATEGORIEN } from "@/lib/kategorien";
import { BEZIRKE } from "@/lib/stadtteile";
import { hubOrte, orteImStadtteil, stadtteileMitOrten } from "@/lib/guide-stadtteile";
import { GUIDE_HUBS, LANDING_TAGE, MIN_EINTRAEGE, guideStadtteilPfad, stadtteilPfad, type GuideHub } from "@/lib/landing";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

/** Jüngstes erstellt_am einer Event-Menge (Inhaltsdatum), sonst undefined – nie die Uhrzeit des Abrufs. */
export function juengstes(events: { erstellt_am: string | null }[]): Date | undefined {
  let max = "";
  for (const e of events) if (e.erstellt_am && e.erstellt_am > max) max = e.erstellt_am;
  const d = max ? new Date(max) : undefined;
  return d && !Number.isNaN(d.getTime()) ? d : undefined;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pool = await eventPoolLaden();
  // lastModified = Inhaltsdatum (SEO-/GEO-Plan, Maßnahme 12): wann zuletzt ein Event dazukam, das auf
  // DIESER Seite steht (Standardansicht der Seite, nicht der ganze Pool)
  const zwischen = (von: string, bis: string) => pool.alle.filter((e) => findetStatt(e, von, bis, true));
  const amTag = (tag: string) => zwischen(tag, tag);
  const imZeitraum = (key?: string) => {
    const z = zeitraumAuflösen(key, pool.heute);
    return zwischen(z.von, z.bis);
  };
  const mit = (d: Date | undefined) => (d ? { lastModified: d } : {});

  const feste: MetadataRoute.Sitemap = [
    // Start zeigt standardmäßig „heute“, Entdecken und Stadtteile „diese Woche“
    { url: `${SITE_URL}/`, ...mit(juengstes(imZeitraum(undefined))), changeFrequency: "hourly", priority: 1 },
    { url: `${SITE_URL}/heute`, ...mit(juengstes(amTag(pool.heute))), changeFrequency: "hourly", priority: 0.9 },
    { url: `${SITE_URL}/morgen`, ...mit(juengstes(amTag(plusTage(pool.heute, 1)))), changeFrequency: "hourly", priority: 0.8 },
    { url: `${SITE_URL}/entdecken`, ...mit(juengstes(imZeitraum("woche"))), changeFrequency: "hourly", priority: 0.9 },
    { url: `${SITE_URL}/wochenende`, ...mit(juengstes(imZeitraum("wochenende"))), changeFrequency: "daily", priority: 0.8 },
    { url: `${SITE_URL}/stadtteile`, ...mit(juengstes(imZeitraum("woche"))), changeFrequency: "daily", priority: 0.7 },
    { url: `${SITE_URL}/event-melden`, changeFrequency: "monthly", priority: 0.4 },
    { url: `${SITE_URL}/ueber`, changeFrequency: "monthly", priority: 0.4 },
  ];

  const tage: MetadataRoute.Sitemap = Array.from({ length: 14 }, (_, i) => {
    const tag = plusTage(pool.heute, i);
    return { url: `${SITE_URL}/tag/${tag}`, ...mit(juengstes(amTag(tag))), changeFrequency: "daily" as const, priority: 0.6 };
  });

  // Beispiel-Events (Fallback ohne Supabase) gehören nicht in die Sitemap
  const events: MetadataRoute.Sitemap =
    pool.quelle === "supabase"
      ? pool.alle // jede Uhrzeit hat eine eigene Seite (Listen zeigen sie gebündelt)
          // Abgelaufene Events raus (ihre Seiten bleiben online, gehören aber nicht mehr in die Sitemap)
          .filter((e) => e.slug && !istAbgelaufen(e, pool.heute))
          .map((e) => ({
            url: `${SITE_URL}/event/${encodeURIComponent(e.kategorie)}/${encodeURIComponent(e.slug!)}`,
            ...mit(juengstes([e])),
            changeFrequency: "weekly",
            priority: 0.5,
          }))
      : [];

  // Guides: Restaurants & Cafés (nur freigeschaltete Orte ab Mindest-Score, wie auf der Website)
  // Jeder Ort genau einmal (URL nach typ über ortPfad) – auch Brauhäuser, die in zwei Hubs erscheinen
  const [orte, kneipen, clubsAlle] = await Promise.all([orteLaden(["restaurant", "imbiss", "cafe", "kneipe"]), kneipenLaden(), clubsLaden()]);
  // Club-Hub: nur Orte mit typ = club bekommen hier ihre URL (auch_club-Orte haben noindex und ihre Haupt-URL)
  const clubs = clubsAlle.filter((o) => o.typ === "club");
  // Hub-URL, sobald der Kneipen-Hub etwas zeigt – auch wenn es nur Restaurants mit auch_kneipe sind
  const hatKneipen = kneipen.length > 0;
  // Hub-Datum = jüngste Änderung eines seiner Orte
  const geaendert = (liste: { aktualisiert_am: string | null }[]) => juengstes(liste.map((o) => ({ erstellt_am: o.aktualisiert_am })));
  const restaurants = orte.filter((o) => o.typ !== "kneipe");
  const guides: MetadataRoute.Sitemap = orte.length
    ? [
        { url: `${SITE_URL}/guides`, ...mit(geaendert([...orte, ...clubsAlle])), changeFrequency: "weekly", priority: 0.7 },
        { url: `${SITE_URL}/guides/restaurants-cafes`, ...mit(geaendert(restaurants)), changeFrequency: "weekly", priority: 0.7 },
        ...(hatKneipen ? [{ url: `${SITE_URL}/guides/kneipen-bars`, ...mit(geaendert(kneipen)), changeFrequency: "weekly" as const, priority: 0.7 }] : []),
        ...(clubsAlle.length ? [{ url: `${SITE_URL}/guides/clubs`, ...mit(geaendert(clubsAlle)), changeFrequency: "weekly" as const, priority: 0.7 }] : []),
        ...[...orte, ...clubs].map((o) => ({
          url: `${SITE_URL}${ortPfad(o)}`,
          ...mit(geaendert([o])),
          changeFrequency: "monthly" as const,
          priority: 0.4,
        })),
      ]
    : [];

  // Reihen mit mindestens einem kommenden Termin. Reihenseiten ohne Termin bleiben erreichbar (HTTP 200,
  // z.B. als 301-Ziel), sind aber dünn und gehören deshalb nicht in die Sitemap.
  const reihenEvents = new Map<string, typeof pool.alle>();
  for (const e of pool.alle) {
    if (!e.reihe || istAbgelaufen(e, pool.heute)) continue;
    reihenEvents.set(e.reihe.slug, [...(reihenEvents.get(e.reihe.slug) ?? []), e]);
  }
  const reihen: MetadataRoute.Sitemap =
    pool.quelle === "supabase"
      ? [...reihenEvents.keys()].sort().map((slug) => ({
          url: `${SITE_URL}/reihe/${encodeURIComponent(slug)}`,
          ...mit(juengstes(reihenEvents.get(slug)!)),
          changeFrequency: "weekly" as const,
          priority: 0.6,
        }))
      : [];

  // Landingpages (Phase B): nur ab MIN_EINTRAEGE kommenden Einträgen – dünnere Seiten sind noindex und fehlen hier.
  // Dieselbe Liste wie auf den Seiten (die nächsten LANDING_TAGE Tage, ohne Langläufer).
  const bis = plusTage(pool.heute, LANDING_TAGE - 1);
  const landing = (filter: (e: (typeof pool.events)[number]) => boolean) => pool.events.filter((e) => findetStatt(e, pool.heute, bis) && filter(e));
  const kategorien: MetadataRoute.Sitemap =
    pool.quelle === "supabase"
      ? KATEGORIEN.flatMap((k) => {
          const ev = landing((e) => e.kategorie === k.slug);
          return ev.length >= MIN_EINTRAEGE ? [{ url: `${SITE_URL}/kategorie/${k.slug}`, ...mit(juengstes(ev)), changeFrequency: "daily" as const, priority: 0.7 }] : [];
        })
      : [];
  const stadtteile: MetadataRoute.Sitemap =
    pool.quelle === "supabase"
      ? BEZIRKE.flatMap((b) => b.stadtteile).flatMap((st) => {
          const ev = landing((e) => e.stadtteil === st);
          return ev.length >= MIN_EINTRAEGE ? [{ url: `${SITE_URL}${stadtteilPfad(st)}`, ...mit(juengstes(ev)), changeFrequency: "daily" as const, priority: 0.6 }] : [];
        })
      : [];
  const hubs = Object.keys(GUIDE_HUBS) as GuideHub[];
  const hubListen = await Promise.all(hubs.map((h) => hubOrte(h)));
  const guideStadtteile: MetadataRoute.Sitemap = hubs.flatMap((h, i) =>
    stadtteileMitOrten(hubListen[i]).map((x) => ({
      url: `${SITE_URL}${guideStadtteilPfad(h, x.stadtteil)}`,
      ...mit(geaendert(orteImStadtteil(hubListen[i], x.stadtteil))),
      changeFrequency: "weekly" as const,
      priority: 0.6,
    })),
  );

  return [...feste, ...tage, ...kategorien, ...stadtteile, ...events, ...reihen, ...guides, ...guideStadtteile];
}
