# Storefront browser acceptance

The catalog suite uses Chromium and checks the listing at the required viewport widths, URL-backed filter application, Toman input handling, fixed Women/Men route scope, keyboard dismissal of the mobile dialog, and axe checks scoped to the filter controls.

## Local setup

From `frontend/`:

```bash
npm ci
npm run test:e2e:install
npm run test:e2e
```

When `ELASI_E2E_BASE_URL` is unset, Playwright starts the local Next.js development server on `127.0.0.1:3000`. A local Django API may also be started on `127.0.0.1:8000` for API-backed result verification. The catalog shell and URL-state checks can run without catalog records; no products, prices, or inventory are seeded by this suite.

To target an approved non-production environment that is already running:

```bash
ELASI_E2E_BASE_URL=https://<approved-staging-host> npm run test:e2e
```

Do not point this suite at the client production domain. The current catalog tests are read-only and do not create accounts, send SMS, modify inventory, create orders, or initiate payments.

## Browser availability

The package and test code are present on the active branch, but the current coding environment has no installed Chromium binary. The latest `npm run test:e2e` attempt discovered 15 tests; all stopped at browser launch before assertions. Browser execution is **BLOCKED (0 assertions)**, not a pass or assertion failure. Install Chromium with `npm run test:e2e:install` in an approved browser-enabled environment, then rerun the suite. A passing TypeScript build or unit test is not a substitute.
