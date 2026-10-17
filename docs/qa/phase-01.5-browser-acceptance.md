# Phase 01.5 — Final browser acceptance checklist

## Execution status for this stabilization pass

**BLOCKED — not executed in a real browser.** The runner has no Chrome/Chromium/Firefox binary or configured browser automation runtime. No OTP, wishlist, cart, navigation, or viewport behavior is being reported as browser-verified. Complete this checklist in an approved browser/staging environment before release.

## Before testing

- Run Django and the Next.js storefront with `frontend/.env.local` migrated to `INTERNAL_API_ORIGIN`; use one storefront origin throughout the test (for example `http://localhost:3000`).
- Use an approved test account and a functioning test SMS sink/provider. Do not use a real customer's phone number, expose OTPs in screenshots/logs, or add OTPs to test notes.
- Use staging-only catalog fixtures, never invented products in production. Include at least:
  - one product with an available gold variant priced at 25,000,000 Rial and a sold-out silver variant priced at 4,000,000 Rial;
  - one product with sold-out gold at 40,000,000 Rial and available silver at 5,000,000 Rial;
  - one product with available gold at 80,000,000 Rial and available silver at 8,000,000 Rial.
- Record only pass/fail, route, viewport, and sanitized observations. Never record cookie values, OTPs, or credentials.

## Acceptance steps

### 1. OTP login and session persistence

1. At the storefront origin, open `/login` and enter the authorized test account's mobile number.
2. Request an OTP, retrieve it only from the approved test SMS sink, enter it, and verify.
3. In DevTools → Network, confirm the browser requests `/api/v1/auth/csrf`, `/api/v1/auth/otp/request`, and `/api/v1/auth/otp/verify` on the **storefront origin**; there must be no browser request directly to the Django host.
4. In DevTools → Application/Storage, confirm session and CSRF cookies exist for the storefront origin. Confirm the session cookie is HttpOnly and note cookie names/attributes only; do not copy values.
5. Refresh the page and open the account page. Confirm the user remains authenticated, then confirm a protected action succeeds with CSRF protection still enabled.

### 2. Product search and combined filters

1. Open `/search`, search for a known staging product/category term, and confirm the matching database-backed product appears. Try a term with no match and confirm the empty state is usable.
2. Open `/shop`; apply a category, the **طلا** material filter, and **فقط موجود** together. Confirm the URL keeps the combined state and the results satisfy all selected filters.
3. For the regression case with price bounds, open this storefront URL (bounds are in Rial):

   `/shop?material=gold&min_price=20000000&max_price=30000000&in_stock=true&ordering=price_asc`

   Confirm only products with one gold variant that is simultaneously in the 20,000,000–30,000,000 Rial range and available are returned. A cheap silver option must not make a gold product qualify. Confirm displayed price and price order reflect matching gold variants, not another material's cheaper option.
4. Clear the filters and confirm the broader listing returns; use browser Back/Forward to verify URL state restores correctly.

### 3. Wishlist add/remove

1. While authenticated, open a product listing and activate the heart control for a product.
2. Confirm its pressed/selected state changes and `/wishlist` shows that product after navigation and refresh.
3. Remove it from the wishlist and confirm the item disappears after refresh. Confirm a guest is prompted to sign in rather than seeing another account's wishlist.

### 4. Cart continuity after authentication

1. In a clean browser profile, add an available product variant to the cart as a guest. Record the visible item, quantity, and server-returned total (not any cookies/tokens).
2. Sign in through OTP without clearing site data.
3. Open `/cart`; confirm the same item and quantity remain, the cart is associated with the signed-in account, and the server-provided total is consistent.
4. Refresh `/cart` and confirm the item remains. Do not continue into payment or submit an order as part of this phase.

### 5. Navigation and responsive behavior

Repeat at **1440 px, 768 px, 390 px, and 320 px** viewport widths:

- Visit `/`, `/shop`, `/women`, `/men`, `/search`, `/about`, `/blog`, `/wishlist`, `/cart`, and `/login`; confirm visible navigation links resolve without a 404.
- At 1440 px, inspect the desktop header, search/account/cart/wishlist actions, footer links, active navigation, product cards, filters, and pagination.
- At 768/390/320 px, open and close the mobile navigation, follow a link, use the search form, and operate product-card and wishlist controls. Confirm the drawer can close with its close control and Escape, and focus returns sensibly.
- Check for clipped text, inaccessible controls, overlapping elements, horizontal page scrolling, and buttons/inputs too narrow to operate. Verify the login, search, catalog, wishlist, and cart layouts remain usable at 320 px.
- Do not enter payment or checkout submission flows.

## Sign-off record

For each step, record `PASS`, `FAIL`, or `BLOCKED`, browser/version, viewport, and a sanitized note. Any failure or missing approved test fixture/provider remains a release blocker; no browser acceptance is implied by the automated backend/frontend checks.
