# ELASI storefront browser acceptance

The catalog suite tests responsive layout, URL-backed filters, Toman price
controls, fixed Women/Men scope, keyboard focus and automated accessibility.

## Windows / local environment

1. Run Django in a **separate** PowerShell and keep it open:

   ```powershell
   cd D:\projects\elasi\backend
   .\.venv\Scripts\Activate.ps1
   python manage.py runserver 127.0.0.1:8000
   ```

2. Verify the backend before running browser tests:

   ```powershell
   Test-NetConnection 127.0.0.1 -Port 8000
   ```

   `TcpTestSucceeded` must be `True`. An anonymous `GET /api/v1/auth/session/`
   currently returns `403` by design; the frontend handles it as logged out.
   `GET /api/v1/categories/` and catalog endpoints should return `200`.

3. In a second PowerShell, execute:

   ```powershell
   cd D:\projects\elasi\frontend
   npm ci
   npm run test:e2e:install
   npm run test:e2e
   ```

When `ELASI_E2E_BASE_URL` is absent, Playwright builds Next.js in **production**
mode, starts it on `127.0.0.1:3100`, and runs Chromium with two workers.
It does **not** start Django. The separate port avoids an existing development
server on port 3000, including Fast Refresh reloads that can detach elements
mid-test. You do not need to start Next.js manually. The initial run takes
longer because it runs `next build`.

If the build fails complaining about `NEXT_PUBLIC_API_BASE_URL`, remove the
obsolete variable from `frontend/.env.local` and process environment and use
`INTERNAL_API_ORIGIN=http://127.0.0.1:8000` instead. Do not upload secrets.

Failing tests now save screenshots and Playwright traces under `test-results/`.
You can inspect the report with `npx playwright show-trace <path-to-trace.zip>`.
Do not publish traces from authenticated customer sessions without redaction.

## Already-running staging environment

To target an approved non-production environment, define
`ELASI_E2E_BASE_URL` and ensure its backend is reachable:

```powershell
$env:ELASI_E2E_BASE_URL = "https://<approved-staging-host>"
npm run test:e2e
Remove-Item Env:ELASI_E2E_BASE_URL
```

This skips local build and local server startup. Do not point tests at the
client production domain. The existing catalog tests are read-only and do not
charge customers, create orders, send SMS or modify inventory.

## Limits

The test suite contains 15 checks, but passing it does **not** demonstrate
correct multi-variant filtering against realistic records, complete checkout,
payment security or merchant administration. Those require independent data-
backed and authenticated acceptance suites. Never claim the site is ready to
ship on the strength of these tests alone.

## Delivery 05.7 — browser checkout contract (mocked API)

Run with a local production Next.js server started by Playwright:

```powershell
cd D:\projects\elasi\frontend
npm run test:e2e:checkout
```

This additional suite checks the actual React cart/login/checkout UI, navigation,
OTP form behavior, shipping quote failure/retry, amount presentation and request
payloads at desktop (1440px) and mobile (390px). Only browser `/api/v1/*`
requests are intercepted with deterministic fixtures. It **does not** send real
SMS, call a payment gateway, consume inventory, or create orders in Django.
It does not depend on real catalog products or a running Django service.

It complements `python manage.py test apps.orders.tests_customer_journey
--settings=config.settings.test`, which covers real Django API contracts on an
isolated test database. Both passing is still **not** proof of a full Django-
backed Playwright journey, PostgreSQL concurrency, or production readiness.

Failures retain traces/screenshots. Never replace this suite with live customer
credentials or point it at an actual production checkout.

## Isolated live-Django checkout acceptance (Delivery 05.8)

From `frontend/`, run:

```powershell
npm run test:e2e:live
```

This **does not** use the mocked `/api/v1` routes in
`checkout-browser.spec.ts`. Playwright launches:

- Django `testserver` on `127.0.0.1:8017` with a disposable SQLite test
  database and one synthetic product (`browser_e2e.json`).
- A Next.js production build on `127.0.0.1:3110` configured to use that
  Django origin through the ordinary same-origin proxy.

The OTP provider is test-only and stores the generated code in a private
short-lived OS temporary file consumed by the browser test, **not** an HTTP
endpoint or external SMS. The temporary file is removed after the test.
Django's database is discarded when `testserver` exits. No merchant DB,
real gateway, SMS subscription or payment action is involved.

Preconditions: `backend/.venv` with the project requirements installed,
frontend dependencies + Playwright Chromium installed, and ports `8017`
and `3110` unused. Run the suite only on your own development workstation.
The browser verifies product → guest cart → OTP → shipping quote → order
creation → unpaid order detail. PostgreSQL concurrency, production SMS,
real payments and Render remain separate release gates.
