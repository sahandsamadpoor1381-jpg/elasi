/**
 * API URL resolution for the same-origin Django proxy.
 *
 * Browser requests always use the relative `/api/v1` path. `src/proxy.ts`
 * forwards those requests to Django, keeping session and CSRF cookies
 * first-party and preserving Django's CSRF checks. An old absolute
 * `NEXT_PUBLIC_API_BASE_URL` would bypass that proxy, so it is rejected
 * instead of being silently honored.
 *
 * React Server Components and the proxy use `INTERNAL_API_ORIGIN`, a
 * server-only origin (scheme + host + optional port, without `/api/v1`).
 */

const DEFAULT_CLIENT_BASE_URL = "/api/v1";
const DEFAULT_INTERNAL_API_ORIGIN = "http://127.0.0.1:8000";


function trimTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, "");
}


const legacyPublicApiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

if (
  legacyPublicApiBaseUrl &&
  trimTrailingSlashes(legacyPublicApiBaseUrl) !==
    DEFAULT_CLIENT_BASE_URL
) {
  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL no longer supports absolute API URLs. " +
      "Remove it from frontend/.env.local; browser API calls must use " +
      "the same-origin /api/v1 proxy. Configure Django with " +
      "INTERNAL_API_ORIGIN instead.",
  );
}


const legacyInternalApiBaseUrl =
  process.env.INTERNAL_API_BASE_URL?.trim();

if (legacyInternalApiBaseUrl) {
  throw new Error(
    "INTERNAL_API_BASE_URL is deprecated. Rename it to " +
      "INTERNAL_API_ORIGIN and remove its API path (for example /api/v1).",
  );
}


/** Absolute Django origin shared by the proxy and server-side fetches. */
export function internalApiOrigin(): string {
  const configuredOrigin =
    process.env.INTERNAL_API_ORIGIN?.trim() ||
    DEFAULT_INTERNAL_API_ORIGIN;

  let parsedOrigin: URL;

  try {
    parsedOrigin = new URL(configuredOrigin);
  } catch {
    throw new Error(
      "INTERNAL_API_ORIGIN must be an absolute HTTP(S) origin, " +
        "for example http://127.0.0.1:8000.",
    );
  }

  if (
    !["http:", "https:"].includes(parsedOrigin.protocol) ||
    parsedOrigin.pathname !== "/" ||
    parsedOrigin.search !== "" ||
    parsedOrigin.hash !== "" ||
    parsedOrigin.username !== "" ||
    parsedOrigin.password !== ""
  ) {
    throw new Error(
      "INTERNAL_API_ORIGIN must contain only the Django origin " +
        "(scheme, host, and optional port), without credentials, " +
        "a path, query, or fragment.",
    );
  }

  return parsedOrigin.origin;
}


/** Server-only API base URL used by RSC fetches. */
function internalApiBaseUrl(): string {
  return `${internalApiOrigin()}/api/v1`;
}


/**
 * Base URL for the current runtime.
 * - browser: relative, same-origin, and always sent through src/proxy.ts
 * - server: absolute, direct to Django using INTERNAL_API_ORIGIN
 */
export function apiBaseUrl(): string {
  if (typeof window === "undefined") {
    return internalApiBaseUrl();
  }

  return DEFAULT_CLIENT_BASE_URL;
}


/**
 * Build a request URL from a canonical, slash-terminated Django API path
 * (for example `/auth/csrf/`). In proxy mode the browser path is
 * slash-less because Next normalizes slash-terminated URLs before proxy
 * execution; src/proxy.ts restores Django's canonical trailing slash.
 */
export function apiUrl(path: string): string {
  const base = apiBaseUrl();

  const normalized = path.startsWith("/")
    ? path
    : `/${path}`;

  // Separate the pathname from its query string.
  const queryIndex = normalized.indexOf("?");

  const pathname =
    queryIndex === -1
      ? normalized
      : normalized.slice(0, queryIndex);

  const query =
    queryIndex === -1
      ? ""
      : normalized.slice(queryIndex);

  // Django requires the slash before the query string.
  const djangoPath = pathname.endsWith("/")
    ? pathname
    : `${pathname}/`;

  // Browser requests use the Next.js same-origin proxy.
  if (base.startsWith("/")) {
    return `${base}${djangoPath.replace(/\/+$/, "")}${query}`;
  }

  // Server requests go directly to Django.
  return `${base}${djangoPath}${query}`;
}
