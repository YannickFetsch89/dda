import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // HSTS (SEO-/GEO-Plan, Maßnahme 10): Browser rufen die Domain ein Jahr lang nur noch per HTTPS auf.
  // Hier statt in nginx, weil der verwaltete Server keinen Zugriff auf die nginx-Konfiguration erlaubt.
  // includeSubDomains: alle Subdomains (www, admin) sprechen HTTPS – neue Subdomains brauchen ein Zertifikat.
  // Über http (lokale Entwicklung) ignorieren Browser den Header.
  async headers() {
    return [
      {
        source: "/:pfad*",
        headers: [{ key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" }],
      },
      // Konto-Seiten nie in den Index (Plan Nutzerkonten 12) – zusätzlich zur Metadata; KEIN Disallow in robots.ts,
      // sonst sähe Google das noindex nicht. Zweiter Eintrag im selben Array, damit die HSTS-Regel bleibt.
      {
        source: "/konto/:pfad*",
        headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }],
      },
      // Admin-Bereich (Plan Admin-Dashboard 3.2): nie in den Index, nie zwischenspeichern, keinen Referrer weitergeben.
      // Zusätzlich zu den Köpfen aus proxy.ts (zweite Sicherung).
      {
        source: "/admin/:pfad*",
        headers: [
          { key: "X-Robots-Tag", value: "noindex, nofollow" },
          { key: "Cache-Control", value: "private, no-store" },
          { key: "Referrer-Policy", value: "no-referrer" },
        ],
      },
      {
        source: "/api/admin/:pfad*",
        headers: [
          { key: "X-Robots-Tag", value: "noindex, nofollow" },
          { key: "Cache-Control", value: "private, no-store" },
        ],
      },
      // Eigene Fotos (web/public/ort-bilder): eine Woche cachen statt max-age=0 (Cursor-Prüfung 19.11.2026).
      // Getauschte Weihnachtsmarkt-Fotos bekommen über foto_version eine neue URL (?v=), alte Kopien stören also nicht.
      {
        source: "/ort-bilder/:pfad*",
        headers: [{ key: "Cache-Control", value: "public, max-age=604800, stale-while-revalidate=86400" }],
      },
    ];
  },
  // Der Restaurant-Guide ist von /restaurants nach /guides/restaurants-cafes umgezogen (Design-Handoff v2)
  async redirects() {
    return [
      { source: "/restaurants", destination: "/guides/restaurants-cafes", permanent: true },
      { source: "/restaurants/:slug", destination: "/guides/restaurants-cafes/:slug", permanent: true },
    ];
  },
};

export default nextConfig;
