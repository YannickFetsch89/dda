// sitemap.xml: feste Seiten, Tagesansichten der nächsten 14 Tage und alle aktuellen Events.
// Nutzt denselben Event-Pool wie die Seiten (Cache 10 min).
import type { MetadataRoute } from "next";
import { eventPoolLaden } from "@/lib/daten";
import { plusTage } from "@/lib/datum";

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
      ? pool.events.map((e) => ({
          url: `${SITE_URL}/event/${encodeURIComponent(e.id)}`,
          lastModified: e.erstellt_am ? new Date(e.erstellt_am) : jetzt,
          changeFrequency: "weekly",
          priority: 0.5,
        }))
      : [];

  return [...feste, ...tage, ...events];
}
