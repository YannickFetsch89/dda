// robots.txt: Die öffentliche Website darf gecrawlt werden, außer der API und den Filter-Adressen.
// (admin.diesdas.events wird separat per nginx gesperrt.)
//
// Filter-Adressen (Search Console 19.11.2026): Jede Filterseite verlinkt rund 70 weitere Kombinationen, Google rief so
// Zehntausende Varianten ab (am 06.11. während des Ausfalls als 5xx gemeldet). Alle sind noindex oder haben ein Canonical
// auf die Seite ohne Parameter, sollen also nicht in die Suche. Google empfiehlt für Filternavigation robots.txt.
// Gesperrt werden nur Seitenpfade MIT Parametern; die Seiten ohne Parameter, Event-, Reihen-, Kategorie-, Stadtteil- und
// Guide-Detailseiten bleiben frei. Bilder mit Parametern (/ort-foto/…?v=, /icon.svg?…) liegen unter anderen Pfaden.
import type { MetadataRoute } from "next";
import { ROBOTS_GESPERRT } from "@/lib/seo";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ROBOTS_GESPERRT },
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
