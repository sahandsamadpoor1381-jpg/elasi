/**
 * Same-origin API proxy.
 *
 * Why this exists (P0 auth fix):
 * Django issues the session and CSRF cookies with `SameSite=Lax`. A
 * browser only attaches them to requests it considers same-site, and
 * `http://localhost:3000` → `http://127.0.0.1:8000` is cross-site even
 * though both are "local". In that topology the CSRF cookie never comes
 * back and every OTP request fails with
 * `403 CSRF Failed: CSRF cookie not set.`
 *
 * Proxying `/api/v1/*` (and Django-served `/media/*`) through the
 * frontend origin makes every browser request same-origin: cookies are
 * first-party, no CORS preflight is needed, and CSRF protection stays
 * fully enforced (Django still validates the cookie *and* the submitted
 * token, and still checks the Origin against CSRF_TRUSTED_ORIGINS).
 *
 * A proxy is used instead of `next.config.ts` rewrites because Next
 * normalizes trailing slashes on rewrite sources: `/api/v1/auth/csrf/`
 * was answered with `308 → /api/v1/auth/csrf`, after which Django's
 * APPEND_SLASH `301` would make a browser re-issue POSTs as GET and
 * break OTP request/verify, cart writes and checkout. Here the exact
 * request path is forwarded untouched.
 */

import {
  NextResponse,
  type NextRequest,
} from "next/server";


const INTERNAL_API_ORIGIN = (
  process.env.INTERNAL_API_ORIGIN ??
    process.env.INTERNAL_API_BASE_URL?.replace(
      /\/api\/v1\/?$/,
      "",
    ) ??
    "http://127.0.0.1:8000"
).replace(/\/+$/, "");


export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  const isApi = pathname.startsWith("/api/v1/");
  const isMedia = pathname.startsWith("/media/");

  if (!isApi && !isMedia) {
    return NextResponse.next();
  }

  /*
   * Next normalizes URLs to have NO trailing slash (308) before the
   * proxy runs, while every Django API route is slash-terminated and
   * would answer a slash-less path with an APPEND_SLASH 301 - a
   * redirect loop that also turns browser POSTs into GETs.
   *
   * So the browser-facing API paths are slash-less and the proxy
   * restores Django's canonical trailing slash here. Media paths keep
   * their exact filename.
   */
  const forwardedPath =
    isApi && !pathname.endsWith("/")
      ? `${pathname}/`
      : pathname;

  const target = new URL(
    `${forwardedPath}${search}`,
    INTERNAL_API_ORIGIN,
  );

  return NextResponse.rewrite(target);
}


export const config = {
  matcher: ["/api/v1/:path*", "/media/:path*"],
};
