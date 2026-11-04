import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // Der Restaurant-Guide ist von /restaurants nach /guides/restaurants-cafes umgezogen (Design-Handoff v2)
  async redirects() {
    return [
      { source: "/restaurants", destination: "/guides/restaurants-cafes", permanent: true },
      { source: "/restaurants/:slug", destination: "/guides/restaurants-cafes/:slug", permanent: true },
    ];
  },
};

export default nextConfig;
