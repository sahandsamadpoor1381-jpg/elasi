import type { MetadataRoute } from "next";

import { siteUrl } from "@/lib/media";


export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          // Authenticated/customer-specific areas.
          "/account",
          "/cart",
          "/checkout",
          "/login",
          // Infinite, low-value URL space (also marked noindex).
          "/search",
        ],
      },
    ],
    sitemap: `${siteUrl()}/sitemap.xml`,
  };
}
