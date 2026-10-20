# ELASI deployment runbook (draft)

- **Status:** Preparation only. No staging or production deployment has been executed or authorized.
- **Last reviewed:** 2026-10-20

## Non-negotiable release controls

- Never deploy to the client live domain, merge to `main`, write production data, run a destructive database operation, activate live credentials, send real customer SMS, initiate a real charge, or incur new service costs without explicit approval.
- Use the active session branch `arena/5630017a-elasi`; this session cannot create or switch to `release/elasi-v1`.
- A successful build, local mock, or payment-provider redirect is not production acceptance.

## Current local verification

From `frontend/`:

```bash
npm ci
npm run test:catalog
npx tsc --noEmit
npm run lint
npm run build
npm run test:e2e:install
npm run test:e2e
```

The last two commands require Chromium. The latest attempt discovered 15 tests, but the current environment has no Playwright Chromium binary; all tests stopped before assertions (**BLOCKED, 0 assertions**). A real staging run also requires an approved Django environment and verified catalog records; no synthetic products/prices/stock are included in the browser suite.

## Required staging inputs before deployment

- Staging owner, URL, access controls, and named test accounts.
- Approved runtime configuration, secret-management path, allowed origins, TLS, storage/media strategy, and service budget.
- Database backup and tested restore evidence, migration owner, monitoring/alert recipients, and rollback procedure.
- Verified SMS and payment provider contracts, sandbox setup, signatures/callbacks and explicit merchant approval. Keep live credentials unavailable until a separately approved release window.
- Approved policies, product data, inventory, pricing, contact details and images.

These values must be supplied by the environment owner and stored through the approved secret channel. Do not add secrets to Git, logs, screenshots, CI output, or this document.

## Release sequence (not yet executed)

1. Complete the storefront, Admin/CMS and internal commerce stages from `RELEASE-PLAN.md`.
2. Run backend tests against SQLite and PostgreSQL; run migrations on a disposable/staging database; confirm migration drift and restore/rollback procedure.
3. Run the full approved Playwright suite against staging at the required widths, including real catalog/API behavior and customer flows. Keep OTP, card and address secrets out of traces and artifacts.
4. Validate callback verification, idempotency, inventory/order reconciliation, alerts and failure/refund workflows using provider sandboxes only.
5. Obtain written release approval and schedule. Confirm backups and rollback operator immediately before release.
6. Deploy only to the approved target, perform read-only health/smoke checks, monitor, and stop/rollback if any gate fails.
7. Complete `FINAL-HANDOFF.md` with exact build/commit, test evidence, remaining risks and owner sign-off.

## Rollback and incident handling

No environment-specific rollback command is documented yet because the target platform and operator are not confirmed. Before release, the deployment owner must add the platform-specific rollback command, database compatibility constraints, backup location, restore rehearsal date and escalation contact. Do not improvise a destructive rollback against production data.
