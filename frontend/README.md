# ELASI storefront

Next.js storefront for ELASI. Django remains the source of truth for customer sessions, CSRF validation, catalog data, inventory, cart, and orders.

## Local configuration

Next.js reads frontend environment files from this directory, not from the repository root. The repository-root `.env` is for Django.

```bash
cd frontend
cp .env.example .env.local
```

For local development, keep these values in `frontend/.env.local`:

```dotenv
INTERNAL_API_ORIGIN=http://127.0.0.1:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

`INTERNAL_API_ORIGIN` is server-only and must be just the Django origin (scheme, host, and optional port), without `/api/v1`, `/media`, credentials, or a trailing path. The default is `http://127.0.0.1:8000`.

Run the frontend from this directory:

```bash
npm ci
npm run dev
```

The browser always requests relative `/api/v1` and `/media` paths. `src/proxy.ts` forwards them to `INTERNAL_API_ORIGIN`; React Server Component data requests use the same origin. This keeps session and CSRF cookies first-party. Django's CSRF checks and cookie settings remain enabled; the proxy is not a CSRF bypass. On production deployments, Django must still trust the storefront's actual origin for CSRF Origin validation.

## Migrating an existing `frontend/.env.local`

The previous frontend configuration allowed a public API URL override and an internal API base URL. Replace those settings as follows:

| Previous setting | Required action |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1` (or any absolute Django URL) | **Delete it.** Browser API traffic must not bypass the same-origin proxy. An absolute value now raises a clear configuration error instead of being used. |
| `NEXT_PUBLIC_API_BASE_URL=/api/v1` | It remains same-origin-safe, but is redundant; delete it and let the frontend use the proxy default. |
| `INTERNAL_API_BASE_URL=http://127.0.0.1:8000/api/v1` | Rename it to `INTERNAL_API_ORIGIN=http://127.0.0.1:8000` (remove the `/api/v1` suffix). |
| `INTERNAL_API_BASE_URL` with another path | Rename it to `INTERNAL_API_ORIGIN` and keep only the origin, for example `https://django.example.com`. |

Then:

1. Stop the running Next.js process.
2. Edit **`frontend/.env.local`** (not the root `.env`), remove the old public override, and set the single `INTERNAL_API_ORIGIN` value used by both the proxy and server rendering.
3. Keep `NEXT_PUBLIC_SITE_URL` set to the browser-facing storefront origin; it is for canonical metadata and sitemap URLs, not API routing.
4. Restart Next.js (or rebuild and restart the production server), because Next.js reads environment values at startup/build time.
5. In browser DevTools → Network, verify requests go to the storefront's own `/api/v1/...` path and not directly to the Django host. Do not copy or share cookie values.

The application rejects an absolute `NEXT_PUBLIC_API_BASE_URL` and a legacy `INTERNAL_API_BASE_URL` instead of silently selecting a different API route. Do not weaken `SameSite`, `Secure`, CSRF, or CORS protections to work around a configuration error.

## Quality checks

```bash
npx tsc --noEmit
npm run lint
npm run build
```
