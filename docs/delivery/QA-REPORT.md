# ELASI storefront QA report

- **Date:** 2026-10-20
- **Milestone:** Stage 1, catalog discovery and filtering
- **Branch:** `arena/5630017a-elasi`
- **Baseline commit:** `18425e6cc54fac4f1491057240f8c0f9434bbac1` (HEAD before this catalog milestone)
- **Implementation commit:** `a28f92a4bf84c998ab963fd8f5cb858e9bd0ade0` on the active branch
- **Status:** Catalog implementation and QA evidence are committed; rendered acceptance is not claimed.
- **Visual evidence:** No screenshots were present. Findings below are from source inspection and automated non-browser checks; they are not pixel-level or browser acceptance.

## Redesign Skill workflow

### SCAN

- Framework: Next.js App Router, React, TypeScript, Tailwind CSS v4.
- Rendering: server-rendered catalog/search pages; client component only for native mobile filter dialog.
- Theme: Persian RTL, Peyda, ELASI deep green / antique-gold / ivory tokens in `frontend/src/app/globals.css`.
- Preserved: `/shop`, `/women`, `/men`, `/search`, server-side product filtering, URL state, API Rial contract, existing product data, pagination and current routes.
- Browser/source limitation: no browser binary and no supplied screenshots. The E2E command was attempted, but Chromium could not launch; none of the browser assertions ran.

### DIAGNOSE

| # | Severity | Location | Source finding | Status |
| --- | --- | --- | --- | --- |
| 1 | Major | Catalog filter state and toolbar | The parser accepted min/max API parameters, but the customer UI had no price fields or visible Toman unit | Fixed: min/max controls now accept Toman and convert once to Rial at the API boundary |
| 2 | Major | `/women` and `/men` catalog routes | A query-string gender could override a gender-specific route; the fixed route default was also counted as an active filter | Fixed: route scope is authoritative, omitted from user filters/links, and does not trigger a false active-filter state |
| 3 | Major | Listing layout on desktop/mobile | All filter/sort chips were placed in one full-width block; mobile had no draft-and-apply filter experience or clear reset action | Fixed in source: compact desktop rail and native modal dialog with Apply/Reset, focus return and Escape support |
| 4 | Major | Gender filter states | Gender options were rendered with `isActive={false}`, so selected gender state was not reflected | Fixed by stateful radio options and URL-backed selection |
| 5 | Critical | Interactive and dark-surface contrast states | White over bright gold measured 2.83:1; dark gold-text over deep green measured 2.59:1; several focused/selected and image-overlay control borders were too faint | Fixed in source: primary hover uses green on gold (5.34:1), dark-green accents use bright gold (5.34:1), and light-surface hover/focus/selected states use contrast-safe gold-text/strong borders |
| 6 | Minor | Product-card wishlist placement | `left-4` was a physical inset inside an RTL catalog card | Fixed with logical `start-4` |
| 7 | P1 | Browser and real-data acceptance | Responsive, keyboard, rendered contrast and API-backed filter behavior cannot be confirmed without Chromium and an approved staging catalog | Open; see blockers and Playwright instructions |

### DIRECT

- Direction: High-End Agency archetype adapted to ELASI's existing **quiet-luxury editorial** identity.
- Palette, Peyda typography, RTL direction, and approved brand tokens were retained. Generic black/white/Oswald/blue library palettes were not substituted for the established ELASI brand.
- Layout: asymmetric desktop filter rail beside a product grid; mobile filter dialog; no full-bleed hero; real product records only.
- Motion: no decorative animation added. Native dialog behavior is keyboard-operable and existing `prefers-reduced-motion` foundation remains active.

### APPLY

- Added a compact server-rendered desktop filter rail and accessible mobile filter dialog with Apply, Reset, Escape dismissal and trigger focus restoration.
- Corrected shared hover/focus contrast: primary buttons use green text on the gold hover fill; secondary/link text, focused control borders, selected product/location states and interactive card borders use the contrast-safe gold-text token. Wishlist, gallery-thumbnail and variant-selector baseline borders now use the strong control-border token. Dark-green login/profile/checkout/story accents use bright brand gold instead of the low-contrast dark-gold text token.
- Added category, material, gender where route permits, in-stock, ordering, and min/max Toman controls.
- Added strict integer parsing (ASCII/Persian/Arabic digits and grouping separators), invalid/reversed range handling, old Rial URL compatibility, search preservation and explicit active-filter removal links.
- Aligned loading skeleton with the new sidebar/grid composition and switched the wishlist overlay to a flow-relative `start` inset for RTL.
- Added only layout tokens for filter width and dialog max-height; no new color palette or fake product data.

## Implemented files

- Catalog behavior/UI: `frontend/src/lib/catalog-params.ts`; `frontend/src/components/catalog/catalog-page.tsx`, `catalog-filter-form.tsx`, `mobile-filter-dialog.tsx`, `listing-toolbar.tsx`, `pagination.tsx`, and `listing-skeleton.tsx`.
- RTL and interaction contrast states: `frontend/src/app/globals.css`; `frontend/src/components/storefront/product-card.tsx`, `product-gallery.tsx`, `product-purchase-panel.tsx`; `frontend/src/components/wishlist/wishlist-button.tsx`; `frontend/src/components/auth/account-client.tsx`, `login-form.tsx`; `frontend/src/components/checkout/checkout-client.tsx`, `location-select.tsx`; and `frontend/src/app/page.tsx`, `about/page.tsx`, `blog/page.tsx`, `login/page.tsx`.
- Tests/setup: `frontend/tests/catalog-params.test.mjs`, `frontend/e2e/catalog.spec.ts`, `frontend/e2e/README.md`, `frontend/playwright.config.ts`, `frontend/package.json`, `frontend/package-lock.json`, and `.gitignore`.
- Delivery evidence: all six files in `docs/delivery/` (`RELEASE-PLAN.md`, `TASK-BOARD.md`, `BLOCKERS.md`, `QA-REPORT.md`, `DEPLOYMENT-RUNBOOK.md`, `FINAL-HANDOFF.md`).

### VERIFY

| Check | Result | Evidence / note |
| --- | --- | --- |
| Catalog URL/parser unit tests | **PASS** | `npm run test:catalog`: 9 passed, 0 failed |
| TypeScript | **PASS** | `npx tsc --noEmit` |
| ESLint | **PASS** | `npm run lint` |
| Playwright test discovery | **PASS** | `npx playwright test --list`: 15 tests discovered |
| Playwright Chromium execution | **BLOCKED (0 assertions)** | Latest `npm run test:e2e` attempted all 15 tests; each stopped at launch because `/home/user/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell` is absent. These are environment launch failures, not assertion results; install Chromium and rerun in an approved browser-enabled environment. |
| Eight required viewport widths | **NOT TESTED** | 320, 360, 375, 390, 414, 768, 1024, 1440 are encoded in the suite |
| Axe/WCAG browser scan | **BLOCKED** | Desktop rail and mobile dialog scans are encoded; Chromium launch failure prevented execution |
| Dark mode | **NOT APPLICABLE** | Current storefront explicitly uses a light-only theme; no dark-mode switch exists |
| Reduced motion | **SOURCE REVIEW PASS** | Existing global `prefers-reduced-motion` rule retained; no new motion was added |
| Redesign hardcode lint | **PASS** | `lint_hardcodes.py` scanned 12 catalog/product-card/gallery/variant/wishlist/global-style candidate files; no violations. Card width and control radii use shared tokens; Next Image `sizes` descriptors are documented explicit-value exceptions. |
| Patch whitespace check | **PASS** | `git diff --check` |
| Contrast | **PASS for measured pairs** | See measured ratios below; rendered-state contrast still requires browser execution |
| Production build | **PASS** | `npm run build` with Next.js 16.4.2/Turbopack; all routes compiled and optimized |
| Dependency audit | **PASS production / OPEN dev tooling** | `npm audit --omit=dev --audit-level=high`: 0 production vulnerabilities. Full audit reports 5 high-severity paths to `braces` through `eslint-config-next`/`fast-glob`; the suggested force fix downgrades to `eslint-config-next@14.2.35`, so no forced/breaking fix was applied |
| Full customer journey / staging data | **NOT TESTED** | No approved staging URL/account or live catalog record supplied |
| Payment/SMS | **BLOCKED / NOT TESTED** | No gateway activation, SMS, order mutation or charge was attempted |

### Contrast measurements

Measured with the Redesign Skill contrast utility using current project token values:

| Foreground | Background | Ratio | Requirement | Result |
| --- | --- | ---: | ---: | --- |
| `#171717` | ELASI ivory `#f8f4ec` | 16.34:1 | 4.5:1 normal text | Pass |
| `#6e6a62` | ELASI ivory `#f8f4ec` | 4.91:1 | 4.5:1 normal text | Pass |
| `#7e6029` | ELASI ivory `#f8f4ec` | 5.33:1 | 4.5:1 normal text | Pass |
| `#152a24` | ELASI ivory `#f8f4ec` | 13.79:1 | 4.5:1 normal text | Pass |
| `#ffffff` | ELASI green `#152a24` | 15.12:1 | 4.5:1 normal text | Pass |
| ELASI green `#152a24` | ELASI gold `#b8945a` | 5.34:1 | 4.5:1 normal text | Pass; primary button hover |
| ELASI gold `#b8945a` | Deep green `#152a24` | 5.34:1 | 4.5:1 normal text / 3:1 icon | Pass; login/profile/checkout/story accents |
| Gold-text `#7e6029` | ELASI ivory `#f8f4ec` | 5.33:1 | 3:1 UI component / 4.5:1 text | Pass; secondary hover and focused borders |
| Gold-text `#7e6029` | Selected gold tint over ivory `#f2eadd` | 4.90:1 | 4.5:1 normal text | Pass; selected location check indicator |
| Composited strong border `#7b857e` | ELASI ivory `#f8f4ec` | 3.48:1 | 3:1 UI component | Pass |

The generic kit contrast validator expects DTCG `tokens/colors.json`; ELASI's source of truth is CSS custom properties. The project values were mapped temporarily for the validator rather than introducing a second, drift-prone palette file. All required light-mode pairs passed. The validator reported the existing 1.25:1 default border pair as an advisory warning; that border is decorative only, not used to identify an operable control. The suite currently has no dark palette to validate.

### Provisional design-review score

This is a **source-review estimate only**, not a rendered screenshot score or release sign-off.

| Dimension | Score / 10 | Basis |
| --- | ---: | --- |
| Visual hierarchy | 7.5 | Catalog hierarchy and sidebar/grid composition are explicit in source; no browser rendering inspected |
| Consistency | 8.5 | Existing ELASI tokens and shared filter form pattern retained |
| Accessibility | 8.0 | Native labels/radios/dialog, Escape and focus-return coverage added; axe execution blocked |
| Usability | 8.0 | Apply/Reset, Toman labels, URL state and errors implemented; API-backed results not verified |
| Responsiveness | 7.0 | Mobile/desktop layouts and eight viewport tests authored; none executed in Chromium |
| Performance | 7.0 | Server components preserved; one small client dialog; no rendered performance measurement |
| **Weighted overall** | **7.8 / 10** | Provisional only; browser and real-data acceptance remain open |

## Defects still open

- Execute the Chromium suite at all listed widths and fix any actual browser findings.
- Validate filters/sorting/pagination against approved real catalog data and confirm backend result counts/prices.
- Complete customer journeys and Admin/CMS/commerce/provider/release stages in the order in `RELEASE-PLAN.md`.

## Next executable milestone

Continue Stage 1 with **STF-03 storefront journey hardening** across cart, login continuity, wishlist, saved addresses and checkout UX. Keep checkout non-paying; do not activate a gateway, send SMS, or create production orders. Run browser assertions only after Chromium is installed, and use approved non-production account/catalog data for API-backed acceptance. The immediate environment action is `npm run test:e2e:install` followed by `npm run test:e2e` in a browser-enabled runner.

## GO verdict

**NO-GO for staging/production release.** The catalog code milestone may proceed to browser verification; the full storefront, merchant, commerce, provider and handoff gates are not complete. No live domain deployment, payment activation, real SMS or charge was attempted.
