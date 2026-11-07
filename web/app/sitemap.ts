// sitemap.xml: feste Seiten, Tagesansichten der nächsten 14 Tage und alle aktuellen Events.
// Nutzt denselben Event-Pool wie die Seiten (Cache 10 min).
import type { MetadataRoute } from "next";
import { istAbgelaufen } from "@/lib/abgelaufen";
import { eventPoolLaden } from "@/lib/daten";
import { plusTage } from "@/lib/datum";
import { kneipenLaden } from "@/lib/kneipen-daten";
import { orteLaden } from "@/lib/orte";
import { ortPfad } from "@/components/ort-karten";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pool = await eventPoolLaden();
  const jetzt = new Date();

  const feste: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, lastModified: jetzt, changeFrequency: "hourly", priority: 1 },
    { url: `${SITE_URL}/heute`, lastModified: jetzt, changeFrequency: "hourly", priority: 0.9 },
    { url: `${SITE_URL}/entdecken`, lastModified: jetzt, changeFrequency: "hourly", priority: 0.9 },
    { url: `${SITE_URL}/wochenende`, lastModified: jetzt, changeFrequency: "daily", priority: 0.8 },
    { url: `${SITE_URL}/stadtteile`, lastModified: jetzt, changeFrequency: "daily", priority: 0.7 },
    { url: `${SITE_URL}/event-melden`, lastModified: jetzt, changeFrequency: "monthly", priority: 0.4 },
  ];

  const tage: MetadataRoute.Sitemap = Array.from({ length: 14 }, (_, i) => ({
    url: `${SITE_URL}/tag/${plusTage(pool.heute, i)}`,
    lastModified: jetzt,
    changeFrequency: "daily",
    priority: 0.6,
  }));

  // Beispiel-Events (Fallback ohne Supabase) gehören nicht in die Sitemap
  const events: MetadataRoute.Sitemap =
    pool.quelle === "supabase"
      ? pool.alle // jede Uhrzeit hat eine eigene Seite (Listen zeigen sie gebündelt)
          // Abgelaufene Events raus (ihre Seiten bleiben online, gehören aber nicht mehr in die Sitemap)
          .filter((e) => e.slug && !istAbgelaufen(e, pool.heute))
          .map((e) => ({
            url: `${SITE_URL}/event/${encodeURIComponent(e.kategorie)}/${encodeURIComponent(e.slug!)}`,
            lastModified: e.erstellt_am ? new Date(e.erstellt_am) : jetzt,
            changeFrequency: "weekly",
            priority: 0.5,
          }))
      : [];

  // Guides: Restaurants & Cafés (nur freigeschaltete Orte ab Mindest-Score, wie auf der Website)
  // Jeder Ort genau einmal (URL nach typ über ortPfad) – auch Brauhäuser, die in zwei Hubs erscheinen
  const [orte, kneipen] = await Promise.all([orteLaden(["restaurant", "imbiss", "cafe", "kneipe"]), kneipenLaden()]);
  // Hub-URL, sobald der Kneipen-Hub etwas zeigt – auch wenn es nur Restaurants mit auch_kneipe sind
  const hatKneipen = kneipen.length > 0;
  const guides: MetadataRoute.Sitemap = orte.length
    ? [
        { url: `${SITE_URL}/guides`, lastModified: jetzt, changeFrequency: "weekly", priority: 0.7 },
        { url: `${SITE_URL}/guides/restaurants-cafes`, lastModified: jetzt, changeFrequency: "weekly", priority: 0.7 },
        ...(hatKneipen ? [{ url: `${SITE_URL}/guides/kneipen-bars`, lastModified: jetzt, changeFrequency: "weekly" as const, priority: 0.7 }] : []),
        ...orte.map((o) => ({
          url: `${SITE_URL}${ortPfad(o)}`,
          lastModified: o.aktualisiert_am ? new Date(o.aktualisiert_am) : jetzt,
          changeFrequency: "monthly" as const,
          priority: 0.4,
        })),
      ]
    : [];

  // Reihen mit mindestens einem kommenden Termin. Reihenseiten ohne Termin bleiben erreichbar (HTTP 200,
  // z.B. als 301-Ziel), sind aber dünn und gehören deshalb nicht in die Sitemap.
  const reihenSlugs = new Set(
    pool.alle.filter((e) => e.reihe && !istAbgelaufen(e, pool.heute)).map((e) => e.reihe!.slug),
  );
  const reihen: MetadataRoute.Sitemap =
    pool.quelle === "supabase"
      ? [...reihenSlugs].sort().map((slug) => ({
          url: `${SITE_URL}/reihe/${encodeURIComponent(slug)}`,
          lastModified: jetzt,
          changeFrequency: "weekly" as const,
          priority: 0.6,
        }))
      : [];

  return [...feste, ...tage, ...events, ...reihen, ...guides];
}
