# ELASI v1 task board

- **Updated:** 2026-10-20
- **Branch:** `arena/5630017a-elasi`

| ID | Priority | Work item | Status | Acceptance / next action |
| --- | --- | --- | --- | --- |
| STF-01 | P1 | Rework catalog filters; add customer-facing Toman price bounds; keep API requests in Rial; enforce fixed Women/Men scopes | **Code complete; browser execution BLOCKED** | Install Chromium in an approved runner and run `frontend/e2e/catalog.spec.ts`; verify real catalog results against staging data |
| STF-02 | P1 | Verify catalog search/category/material/gender/in-stock/sort/pagination and product detail on actual data | In progress | Use approved catalog records; capture screenshots at mobile/tablet/desktop widths; do not seed fabricated products |
| STF-03 | P1 | Complete storefront journeys: guest cart, login continuity, wishlist, address, checkout and order views | Not started in this milestone | Run end-to-end regression with an approved non-production account and a non-sending SMS test setup; no charge |
| QA-01 | P1 | Execute Chromium responsive and accessibility checks | **BLOCKED before assertions: Chromium executable absent; 15 tests could not launch** | Run `npm run test:e2e:install` then `npm run test:e2e` in an approved browser-enabled environment; record assertion results, not discovery alone |
| ADM-01 | P1 | Audit and build merchant Admin/CMS workflows with roles and audit trail | Not started | Inventory existing Django admin/API capabilities, then implement and test an approved permission matrix |
| COM-01 | P1 | Internal order/inventory workflow with transaction guarantees and isolated MockProvider | Not started; Stage 3 | Implement after storefront and Admin milestones; mocks must not be described as real payment |
| INT-01 | P0 | Verify payment/SMS provider documents, merchant approvals, sandbox access and credentials | **Blocked** | Resolve exact items in `BLOCKERS.md`; keep real-provider activation and customer charges disabled |
| OPS-01 | P1 | Prepare staging runbook, CI/security, backups, monitoring and rollback | In progress, prerequisites only | Confirm environment owner, target, access, backup/restore and cost approval; do not deploy yet |
| REL-01 | P0 | Final acceptance and handoff | Not started | No GO until all stage gates and live-provider requirements have evidence |

## Completed in this milestone

- Compact desktop filter rail and accessible native mobile filter dialog with Apply and Reset.
- Category, material, gender (where permitted), inventory, ordering, and min/max price controls.
- Price inputs are labeled in Toman; customer-entered Toman is converted once to API Rial. Existing `min_price`/`max_price` Rial links remain compatible.
- Invalid and reversed price ranges are rejected before product API requests.
- `/women` and `/men` route scope cannot be overridden by a query parameter; route defaults no longer appear as active filters.
- URL-backed filter state preserves search/context; pagination and clear-filter links reset or preserve state intentionally.
- Nine executable parser/URL tests and a 15-test Playwright catalog suite were added.
- Gold hover, focus, selection and dark-surface text/icon states were adjusted to meet the measured WCAG AA contrast pairs; wishlist/gallery/variant control borders use a stronger token. Rendered browser verification remains blocked.
