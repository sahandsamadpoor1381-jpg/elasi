# ELASI independent delivery — patch 01

**Base:** `delivery/elasi-v1` at `1b683f136e61a94aca40ba550f7edcae8b4dd9cc`.

**Scope:** merchant admin foundation and catalog empty/sparse states.

## Implemented

- New Django AdminSite and project-level Admin base template installed by `ElasiAdminConfig`, preserving existing model registrations and all inventory/order service protections.
- Persian RTL administration branding and read-only dashboard metrics, backed by actual Order/Product/InventoryBalance/Article records.
- Dashboard data and links only shown to users with corresponding Django `view_*` permissions; recent orders expose no customer contact data.
- Fixed catalog no-match copy distinct from empty-store state.
- Single/two-product listing grids centered without affecting the normal 3+ product grid.
- Django TestCase coverage for administrator, staff without permissions, order-view-only staff and anonymous access.

## Verification performed in the delivery workspace

- `python -m compileall -q backend` — PASS (syntax only).
- `cd frontend && npm run test:catalog` — PASS (9/9).
- `git diff --check` — PASS.

**Not yet executed here:** Django unit/system tests, Next.js TypeScript/build, responsive browser checks. The isolated environment lacks the installed Django and Node package dependencies, and network package installation was unavailable. These checks must run in the local project's configured environment; do not interpret them as PASS.

## Local verification gate

From `backend/` in the configured virtual environment:

```powershell
python manage.py check --settings=config.settings.development
python manage.py makemigrations --check --dry-run --settings=config.settings.development
python manage.py test apps.core.tests_admin_dashboard --settings=config.settings.test
```

From `frontend/`:

```powershell
npm ci
npm run test:catalog
npx tsc --noEmit
npm run lint
npm run build
```

Open `http://127.0.0.1:8000/admin/` with a staff superuser and verify the brand dashboard and existing model admin pages. Recheck `/shop` with one/two products and a no-match filter at desktop and mobile widths. Do not deploy this patch without those gates.

## Unfinished delivery scope

Merchant CMS configuration, robust shipment/payment records, shipping rules, custom-size workflow, real OTP provider, three payment-provider integrations, Render staging/production, backup/restore and final browser acceptance remain pending. External SnappPay and TorobPay merchant onboarding is not active.
