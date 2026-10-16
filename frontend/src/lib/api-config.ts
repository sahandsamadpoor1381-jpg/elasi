/**
 * API base URL resolution.
 *
 * Cookie topology (the reason this module exists):
 *
 * Django issues the session and CSRF cookies with `SameSite=Lax` and
 * no `Secure` flag, which is correct for a same-site storefront. A
 * browser only attaches those cookies when it considers the request
 * "same site" - and `http://localhost:3000` vs `http://127.0.0.1:8000`
 * are *cross-site* even though both are "local". In that topology the
 * CSRF cookie is never sent back and Django answers every OTP request
 * with `403 CSRF Failed: CSRF cookie not set.`
 *
 * So in the browser we default to a **relative** base (`/api/v1`) that
 * Next.js proxies to Django (`next.config.ts` rewrites). Every request
 * is then same-origin, first-party cookies always travel, no CORS
 * negotiation is needed, and CSRF protection stays fully enforced.
 *
 * Server-side rendering (RSC / route handlers) cannot use a relative
 * URL, so it talks to Django directly through `INTERNAL_API_BASE_URL`
 * (never exposed to the browser bundle).
 */

const DEFAULT_CLIENT_BASE_URL = "/api/v1";

const DEFAULT_INTERNAL_BASE_URL = "http://127.0.0.1:8000/api/v1";


function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}


/**
 * Set `NEXT_PUBLIC_API_BASE_URL` only when the API must be reached on
 * another origin (and then make sure the hostnames match the site, and
 * that CORS_ALLOWED_ORIGINS / CSRF_TRUSTED_ORIGINS cover the site
 * origin). Leaving it unset is the recommended, cookie-safe default.
 */
const PUBLIC_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL
    ? trimTrailingSlash(
        process.env.NEXT_PUBLIC_API_BASE_URL,
      )
    : null;


/** Server-only: used by RSC fetches and by the Next.js rewrite target. */
const INTERNAL_API_BASE_URL = trimTrailingSlash(
  process.env.INTERNAL_API_BASE_URL ??
    DEFAULT_INTERNAL_BASE_URL,
);


/** Absolute origin of the Django server (used for /media and rewrites). */
export function internalApiOrigin(): string {
  return INTERNAL_API_BASE_URL.replace(/\/api\/v1$/, "");
}


/**
 * Base URL for the current runtime.
 * - browser  → relative, same-origin (proxied by Next.js)
 * - server   → absolute, direct to Django
 */
export function apiBaseUrl(): string {
  if (typeof window === "undefined") {
    return INTERNAL_API_BASE_URL;
  }

  return PUBLIC_API_BASE_URL ?? DEFAULT_CLIENT_BASE_URL;
}


/**
 * Build a request URL from a canonical, slash-terminated API path
 * (the shape Django's URLconf uses, e.g. `/auth/csrf/`).
 *
 * - same-origin proxy mode (default): the trailing slash is dropped,
 *   because Next normalizes slash-less URLs and `src/proxy.ts` restores
 *   the slash when forwarding to Django. Requesting the slash form from
 *   the browser would be answered with a 308 and, for POSTs, could end
 *   up downgraded to a GET by Django's APPEND_SLASH 301.
 * - absolute override mode: the browser talks to Django directly, so
 *   the canonical slash-terminated path is required.
 */
export function apiUrl(path: string): string {
  const base = apiBaseUrl();

  const normalized = path.startsWith("/")
    ? path
    : `/${path}`;

  if (base.startsWith("/")) {
    return `${base}${normalized.replace(/\/+$/, "")}`;
  }

  return `${base}${
    normalized.endsWith("/")
      ? normalized
      : `${normalized}/`
  }`;
}
