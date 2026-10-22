/** True browser + Django smoke acceptance. No page.route() mocks.
 *
 * The testserver starts with an isolated SQLite test database containing
 * ONE synthetic product. OTP is captured through a local temporary file,
 * without SMS. A pending-payment order is created only in that database.
 */
import { expect, test } from "@playwright/test";
import { readFileSync, rmSync } from "node:fs";

const productName = "انگشتر آزمایشی ELASI";
const expectedShippingFee = 15000; // Toman, synthetic test-only tariff
const phone = "09123456789";

function readTestOtp(): string {
  const otpPath = process.env.ELASI_E2E_OTP_FILE;
  if (!otpPath) throw new Error("Isolated test OTP file is not configured.");
  const value = JSON.parse(readFileSync(otpPath, "utf8")) as {
    phone_number: string;
    code: string;
  };
  expect(value.phone_number).toBe("+989123456789");
  expect(value.code).toMatch(/^\d{6}$/);
  return value.code;
}

test.afterAll(() => {
  const otpPath = process.env.ELASI_E2E_OTP_FILE;
  if (otpPath) rmSync(otpPath, { force: true });
});

test("real Django: product → guest cart → OTP → checkout → unpaid order", async ({ page }) => {
  // Catch a Django/Next integration regression; do not intercept the API.
  const apiFailures: string[] = [];
  page.on("response", (response) => {
    if (new URL(response.url()).pathname.startsWith("/api/v1/") && response.status() >= 500) {
      apiFailures.push(`${response.status()} ${response.url()}`);
    }
  });

  await page.goto("/products/e2e-checkout-ring");
  await expect(page.getByRole("heading", { name: productName })).toBeVisible();
  await page.getByRole("button", { name: "افزودن به سبد خرید" }).click();
  await expect(page.getByText("محصول به سبد خرید اضافه شد.")).toBeVisible();
  await page.getByRole("link", { name: "مشاهده سبد خرید" }).click();
  await expect(page.getByText(productName).first()).toBeVisible();
  await page.getByRole("link", { name: "ادامه فرایند خرید" }).click();
  await expect(page).toHaveURL(/\/login\?next=/);

  const login = page.locator("form:visible");
  await login.getByLabel("شماره موبایل", { exact: true }).fill(phone);
  await login.getByRole("button", { name: "دریافت کد ورود" }).click();
  await expect(login.getByLabel("کد تأیید", { exact: true })).toBeVisible();
  await login.getByLabel("کد تأیید", { exact: true }).fill(readTestOtp());
  await login.getByRole("button", { name: "تأیید و ورود" }).click();

  await expect(page).toHaveURL(/\/checkout(?:\?|$)/);
  await expect(page.getByText(productName).first()).toBeVisible();
  await expect(page.getByText(new RegExp(`^${new Intl.NumberFormat("fa-IR").format(expectedShippingFee)} تومان$`))).toBeVisible();
  await page.locator("#recipient_name").fill("سارا آزمون");
  await page.locator("#province").click();
  await page.locator("#province-listbox").getByRole("option", { name: "تهران", exact: true }).click();
  await page.locator("#city").click();
  await page.locator("#city-listbox").getByRole("option", { name: "تهران", exact: true }).click();
  await page.locator("#postal_code").fill("1234567890");
  await page.locator("#address_line").fill("خیابان آزمایشی، پلاک ۱۰");
  await page.getByRole("button", { name: "ثبت سفارش", exact: true }).click();

  await expect(page.getByText(/در انتظار پرداخت/).first()).toBeVisible();
  await page.getByRole("link", { name: "مشاهده جزئیات سفارش" }).click();
  await expect(page.getByRole("heading", { name: "جزئیات سفارش" })).toBeVisible();
  await expect(page.getByText("این سفارش هنوز پرداخت نشده است.", { exact: false })).toBeVisible();
  expect(apiFailures).toEqual([]);
});
