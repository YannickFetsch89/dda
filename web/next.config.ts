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
