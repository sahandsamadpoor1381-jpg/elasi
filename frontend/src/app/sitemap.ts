import type { MetadataRoute } from "next";

import { getArticlePage } from "@/lib/blog-api";
import { getProductPage } from "@/lib/catalog-api";
import { siteUrl } from "@/lib/media";


export const dynamic = "force-dynamic";


/**
 * Sitemap for stable, indexable destinations only.
 *
 * Filter combinations and search pages are deliberately excluded (they
 * are marked noindex and are effectively infinite). A catalog or API
 * outage must never break the sitemap, so failures degrade to the
 * static routes.
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const origin = siteUrl();
  const now = new Date();

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: `${origin}/`, lastModified: now, priority: 1 },
    { url: `${origin}/shop`, lastModified: now, priority: 0.9 },
    { url: `${origin}/women`, lastModified: now, priority: 0.8 },
    { url: `${origin}/men`, lastModified: now, priority: 0.8 },
    { url: `${origin}/about`, lastModified: now, priority: 0.5 },
    { url: `${origin}/blog`, lastModified: now, priority: 0.6 },
  ];

  const dynamicRoutes: MetadataRoute.Sitemap = [];

  try {
    const products = await getProductPage({ page_size: 48 });

    for (const product of products.results) {
      dynamicRoutes.push({
        url: `${origin}/products/${product.slug}`,
        lastModified: now,
        priority: 0.7,
      });
    }
  } catch {
    // Catalog unavailable: keep the static routes.
  }

  try {
    const articles = await getArticlePage({ page_size: 36 });

    for (const article of articles.results) {
      dynamicRoutes.push({
        url: `${origin}/blog/${article.slug}`,
        lastModified: new Date(article.published_at),
        priority: 0.5,
      });
    }
  } catch {
    // Journal unavailable: keep the static routes.
  }

  return [...staticRoutes, ...dynamicRoutes];
}
