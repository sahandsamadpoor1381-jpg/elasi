/**
 * ELASI — deterministic storefront browser contract tests.
 *
 * These tests exercise REAL Next.js/React screens and browser navigation,
 * but intercept ONLY the /api/v1 browser calls with Django-shaped fixtures.
 * They do not send OTPs, create orders, or touch real inventory. The Django
 * API journey is separately verified in apps.orders.tests_customer_journey.
 * Do not present this suite as live Django/payment end-to-end acceptance.
 */
import { expect, test, type Page } from "@playwright/test";

const GUEST_TOKEN = "11111111-1111-4111-8111-111111111111";
const ACCOUNT_TOKEN = "22222222-2222-4222-8222-222222222222";
const ORDER_ID = "33333333-3333-4333-8333-333333333333";
const PRODUCT_NAME = "انگشتر آزمایشی ELASI";
const UNIT_PRICE_RIAL = 2_000_000;
const SHIPPING_FEE_RIAL = 150_000;

const customer = {
  id: 18,
  phone_number: "09123456789",
  email: null,
  first_name: "سارا",
  last_name: "تست",
};

function cartFixture(authenticated: boolean) {
  const item = {
    id: 41,
    product_name: PRODUCT_NAME,
    product_slug: "e2e-demo-ring",
    image: null,
    sku: "ELASI-E2E-01",
    material: "gold" as const,
    karat: 18,
    size: "54",
    quantity: 1,
    available: 3,
    unit_price_rial: UNIT_PRICE_RIAL,
    line_total_rial: UNIT_PRICE_RIAL,
  };
  return {
    token: authenticated ? ACCOUNT_TOKEN : GUEST_TOKEN,
    status: "active",
    items: [item],
    item_count: 1,
    total_quantity: 1,
    subtotal_rial: UNIT_PRICE_RIAL,
    created_at: "2026-10-20T10:00:00Z",
    updated_at: "2026-10-20T10:00:00Z",
  };
}

type BrowserScenario = {
  authenticatedInitially?: boolean;
  shippingQuoteFailures?: number;
};

// The mock suite must never be pointed at a real client storefront.
test.beforeAll(() => {
  const baseUrl = new URL(process.env.ELASI_E2E_BASE_URL ?? "http://127.0.0.1:3100");
  if (!["127.0.0.1", "localhost", "::1"].includes(baseUrl.hostname)) {
    throw new Error("Mocked checkout browser tests run only against a local Next.js server.");
  }
});

async function interceptCustomerApi(page: Page, scenario: BrowserScenario = {}) {
  const state = {
    authenticated: scenario.authenticatedInitially ?? false,
    shippingQuoteRequests: 0,
    checkoutRequests: 0,
    cartReads: [] as Array<{ authenticated: boolean; token: string | null }>,
    checkoutPayload: null as Record<string, unknown> | null,
    checkoutCartToken: null as string | null,
  };

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const method = request.method();
    const path = new URL(request.url()).pathname.replace(/\/+$/, "");
    const json = (status: number, data: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });

    if (path === "/api/v1/auth/session" && method === "GET") {
      return state.authenticated
        ? json(200, { authenticated: true, user: customer })
        : json(403, { code: "not_authenticated", detail: "Authentication required." });
    }
    if (path === "/api/v1/auth/csrf" && method === "GET") {
      return json(200, { csrf_token: "test-only-csrf-token" });
    }
    if (path === "/api/v1/auth/otp/request" && method === "POST") {
      const body = request.postDataJSON() as { phone_number: string };
      expect(body.phone_number).toBe(customer.phone_number);
      return json(200, { phone_number: customer.phone_number, expires_in: 120, resend_after: 60 });
    }
    if (path === "/api/v1/auth/otp/verify" && method === "POST") {
      const body = request.postDataJSON() as { code: string; phone_number: string };
      expect(body.code).toBe("123456");
      expect(body.phone_number).toBe(customer.phone_number);
      state.authenticated = true;
      return json(200, { authenticated: true, user: customer });
    }
    if (path === "/api/v1/auth/logout" && method === "POST") {
      state.authenticated = false;
      return route.fulfill({ status: 204 });
    }
    if (path === "/api/v1/cart" && method === "POST") {
      // Account cart get-or-create when no token is stored.
      expect(state.authenticated).toBe(true);
      return json(200, cartFixture(true));
    }
    if (path === "/api/v1/wishlist" && method === "GET") {
      return json(200, { count: 0, next: null, previous: null, results: [] });
    }
    if (path === "/api/v1/cart" && method === "GET") {
      // Authenticated GET claims the guest token and returns the account cart.
      state.cartReads.push({
        authenticated: state.authenticated,
        token: request.headers()["x-cart-token"] ?? null,
      });
      return json(200, cartFixture(state.authenticated));
    }
    if (path === "/api/v1/checkout/shipping-quote" && method === "GET") {
      state.shippingQuoteRequests++;
      if (state.shippingQuoteRequests <= (scenario.shippingQuoteFailures ?? 0)) {
        return json(503, { code: "shipping_fee_unconfigured", detail: "Not configured" });
      }
      return json(200, { shipping_method: "postal", shipping_fee_rial: SHIPPING_FEE_RIAL });
    }
    if (path === "/api/v1/checkout" && method === "POST") {
      state.checkoutRequests++;
      expect(state.authenticated).toBe(true);
      expect(request.headers()["x-csrftoken"]).toBeTruthy();
      state.checkoutCartToken = request.headers()["x-cart-token"] ?? null;
      state.checkoutPayload = request.postDataJSON() as Record<string, unknown>;
      return json(201, {
        public_id: ORDER_ID,
        status: "pending_payment",
        shipping_method: "postal",
        subtotal_rial: UNIT_PRICE_RIAL,
        shipping_fee_rial: SHIPPING_FEE_RIAL,
        total_rial: UNIT_PRICE_RIAL + SHIPPING_FEE_RIAL,
        recipient_name: state.checkoutPayload.recipient_name,
        phone_number: state.checkoutPayload.phone_number,
        province: state.checkoutPayload.province,
        city: state.checkoutPayload.city,
        postal_code: state.checkoutPayload.postal_code,
        address_line: state.checkoutPayload.address_line,
        building_number: "",
        unit_number: "",
        customer_note: "",
        items: [],
        reservation_expires_at: "2026-10-22T15:00:00Z",
        paid_at: null,
        created_at: "2026-10-22T14:30:00Z",
      });
    }
    if (path === `/api/v1/orders/${ORDER_ID}` && method === "GET") {
      return json(200, {
        public_id: ORDER_ID,
        status: "pending_payment",
        shipping_method: "postal",
        subtotal_rial: UNIT_PRICE_RIAL,
        shipping_fee_rial: SHIPPING_FEE_RIAL,
        total_rial: UNIT_PRICE_RIAL + SHIPPING_FEE_RIAL,
        ...state.checkoutPayload,
        shipment: null,
        items: [],
        reservation_expires_at: "2026-10-22T15:00:00Z",
        paid_at: null,
        created_at: "2026-10-22T14:30:00Z",
      });
    }
    // Fail closed: a new API dependency must never silently hit live Django.
    return json(501, { code: "unmocked_endpoint", detail: `${method} ${path}` });
  });

  return state;
}

async function startWithGuestCart(page: Page) {
  await page.goto("/cart");
  await expect(page.getByRole("heading", { name: "سبد خرید شما خالی است" })).toBeVisible();
  await page.evaluate((token) => window.localStorage.setItem("elasi_cart_token", token), GUEST_TOKEN);
  await page.reload();
  await expect(page.getByRole("heading", { name: "سبد خرید" })).toBeVisible();
  await expect(page.getByText(PRODUCT_NAME).first()).toBeVisible();
}

async function fillShippingDetails(page: Page) {
  await page.locator("#recipient_name").fill("سارا آزمون");
  await page.locator("#province").click();
  await page.locator("#province-listbox").getByRole("option", { name: "تهران", exact: true }).click();
  await page.locator("#city").click();
  await page.locator("#city-listbox").getByRole("option", { name: "تهران", exact: true }).click();
  await page.locator("#postal_code").fill("1234567890");
  await page.locator("#address_line").fill("تهران، خیابان آزمایشی، پلاک ۱۰");
}

test("desktop: guest cart survives OTP login and checkout remains unpaid", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const state = await interceptCustomerApi(page);
  await startWithGuestCart(page);
  await page.getByRole("link", { name: "ادامه فرایند خرید" }).click();
  await expect(page).toHaveURL(/\/login\?next=/);

  const loginForm = page.locator("form:visible");
  // Both responsive LoginForm instances are mounted. Labels must resolve
  // to the input inside the *visible* form, not the hidden mobile copy.
  await expect(loginForm.getByLabel("شماره موبایل", { exact: true })).toBeVisible();
  await loginForm.getByLabel("شماره موبایل", { exact: true }).fill(customer.phone_number);
  await loginForm.getByRole("button", { name: "دریافت کد ورود" }).click();
  await expect(loginForm.getByLabel("کد تأیید", { exact: true })).toBeVisible();
  await loginForm.getByLabel("کد تأیید", { exact: true }).fill("123456");
  await loginForm.getByRole("button", { name: "تأیید و ورود" }).click();

  await expect(page).toHaveURL(/\/checkout(?:\?|$)/);
  await expect(page.getByText(PRODUCT_NAME).first()).toBeVisible();
  await expect(page.getByText(/^۱۵[٬,]۰۰۰ تومان$/)).toBeVisible();
  await fillShippingDetails(page);
  await page.getByRole("button", { name: "ثبت سفارش", exact: true }).click();

  await expect(page.getByText(ORDER_ID)).toBeVisible();
  await expect(page.getByText(/در انتظار پرداخت/).first()).toBeVisible();
  expect(state.checkoutRequests).toBe(1);
  expect(state.cartReads).toContainEqual({ authenticated: true, token: GUEST_TOKEN });
  expect(state.checkoutCartToken).toBe(ACCOUNT_TOKEN);
  expect(state.checkoutPayload).toMatchObject({
    recipient_name: "سارا آزمون",
    province: "تهران",
    city: "تهران",
    postal_code: "1234567890",
  });
  expect(state.checkoutPayload).not.toHaveProperty("total_rial");
  expect(state.checkoutPayload).not.toHaveProperty("shipping_fee_rial");
});

test("mobile: an unavailable shipping quote disables checkout until retry succeeds", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const state = await interceptCustomerApi(page, {
    authenticatedInitially: true,
    shippingQuoteFailures: 1,
  });
  await page.goto("/cart");
  // An authenticated user without a local token recovers their account cart.
  await expect(page.getByText(PRODUCT_NAME).first()).toBeVisible();
  await page.getByRole("link", { name: "ادامه فرایند خرید" }).click();
  await expect(page).toHaveURL(/\/checkout(?:\?|$)/);

  await expect(page.getByRole("button", { name: "ثبت سفارش", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "تلاش مجدد برای دریافت هزینه ارسال" })).toBeVisible();
  expect(state.checkoutRequests).toBe(0);
  await page.getByRole("button", { name: "تلاش مجدد برای دریافت هزینه ارسال" }).click();
  await expect(page.getByText(/^۱۵[٬,]۰۰۰ تومان$/)).toBeVisible();
  await fillShippingDetails(page);
  await expect(page.getByRole("button", { name: "ثبت سفارش", exact: true })).toBeEnabled();

  const overflow = await page.evaluate(() =>
    Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) > window.innerWidth,
  );
  expect(overflow).toBe(false);
  expect(state.shippingQuoteRequests).toBe(2);
});
