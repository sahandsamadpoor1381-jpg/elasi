/**
 * Media URL helpers.
 *
 * Django returns absolute media URLs built from the request host. The
 * storefront serves `/media/*` through its own origin (see proxy.ts),
 * so absolute URLs are folded back to a relative path. That keeps
 * next/image working on a single origin no matter which host the API
 * was reached through (localhost, 127.0.0.1 or a preview host).
 */

export function mediaPath(
  url: string | null | undefined,
): string | null {
  if (!url) {
    return null;
  }

  if (url.startsWith("/")) {
    return url;
  }

  try {
    const parsed = new URL(url);

    return `${parsed.pathname}${parsed.search}`;
  } catch {
    return url;
  }
}


/** Public site origin used for metadata and the sitemap. */
export function siteUrl(): string {
  return (
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"
  ).replace(/\/+$/, "");
}
