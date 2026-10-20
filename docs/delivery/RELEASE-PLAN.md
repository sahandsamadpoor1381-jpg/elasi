# ELASI v1 delivery plan

- **Status:** In progress, not a release approval
- **Hard deadline:** 2026-10-27
- **Current work branch:** `arena/5630017a-elasi`
- **Production deployment / live charging:** Not authorized

## Approved delivery order

| Stage | Scope | Current status | Exit gate |
| --- | --- | --- | --- |
| 1. Storefront | Catalog, customer discovery, product detail, cart, account, wishlist, checkout UX | **In progress.** Catalog filters and URL state implemented; Chromium execution is blocked before assertions | Product/catalog data verified; search/filter/sort, product, cart, auth continuity, wishlist, addresses, checkout and responsive journeys pass on approved staging; defects recorded |
| 2. Admin/CMS | Merchant catalog/content management and staff permissions | Not started | Role/access matrix approved; product, variant, inventory and content workflows tested without changing production data |
| 3. Internal commerce | Order lifecycle, inventory reservation, auditability, isolated MockProvider | Not started | Transaction, idempotency, state-machine, authorization, inventory and mock-isolation tests pass; mock results are clearly non-payment |
| 4. Real integrations | SMS and selected payment/shipping providers | **Blocked on verified provider documentation, merchant acceptance, credentials and explicit approval** | Provider contracts, sandbox credentials, callbacks/signatures, reconciliation, retries/refunds and failure handling independently verified; no live charge before approval |
| 5. Authorized release | Staging/production, final acceptance, handoff | Not started | Written deployment approval, verified backups/rollback/monitoring, approved content and end-to-end sign-off |

## Parallel preparation

- Keep deployment, security, provider and external-content prerequisites visible in `BLOCKERS.md` while storefront work continues.
- Do not activate credentials, send real SMS, run destructive migrations, write production data, deploy the live domain, or incur new service charges without explicit approval.
- Do not treat mocks or a successful build as live-provider or release acceptance.

## Branch constraint

The session is restricted to `arena/5630017a-elasi`. The requested `release/elasi-v1` branch cannot be created or checked out in this session. Work and any push must remain on the active Arena branch; no merge to `main` is authorized.
