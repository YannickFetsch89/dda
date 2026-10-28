// robots.txt: Die öffentliche Website darf vollständig gecrawlt werden, nur die API nicht.
// (admin.diesdas.events wird separat per nginx gesperrt.)
import type { MetadataRoute } from "next";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: "/api/" },
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
