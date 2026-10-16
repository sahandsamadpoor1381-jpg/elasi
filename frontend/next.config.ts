import type { NextConfig } from "next";


/*
 * Browser requests to /api/v1/* and /media/* are proxied to Django by
 * src/proxy.ts, keeping session and CSRF cookies first-party.
 * INTERNAL_API_ORIGIN (server-only, no NEXT_PUBLIC_ prefix) is the
 * Django origin used by that proxy and by server-side data fetching.
 */


const nextConfig: NextConfig = {
  images: {
    dangerouslyAllowLocalIP: true,

    remotePatterns: [
      {
        protocol: "http",
        hostname: "127.0.0.1",
        port: "8000",
        pathname: "/media/**",
      },
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/media/**",
      },
    ],
  },

};


export default nextConfig;
