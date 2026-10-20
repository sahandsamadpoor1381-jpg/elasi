import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";


const viewportWidths = [320, 360, 375, 390, 414, 768, 1024, 1440];
const wcagTags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];


async function openMobileFilters(page: Page) {
  const trigger = page.getByRole("button", { name: /فیلتر و مرتب‌سازی/ });
  await trigger.click();

  const dialog = page.getByRole("dialog", { name: "فیلتر محصولات" });
  await expect(dialog).toBeVisible();

  return { trigger, dialog };
}


test.describe("Catalog responsive layout", () => {
  for (const width of viewportWidths) {
    test(`${width}px viewport has no horizontal overflow`, async ({ page }) => {
      await page.setViewportSize({ width, height: 844 });
      await page.goto("/shop");

      await expect(
        page.getByRole("heading", {
          level: 1,
          name: "همه‌ی محصولات ELASI",
        }),
      ).toBeVisible();

      const hasHorizontalOverflow = await page.evaluate(() => {
        const documentWidth = Math.max(
          document.documentElement.scrollWidth,
          document.body.scrollWidth,
        );

        return documentWidth > window.innerWidth;
      });

      expect(hasHorizontalOverflow).toBe(false);

      if (width < 1024) {
        await expect(
          page.getByRole("button", { name: /فیلتر و مرتب‌سازی/ }),
        ).toBeVisible();
      } else {
        await expect(
          page.getByRole("complementary", { name: "فیلترهای محصولات" }),
        ).toBeVisible();
        await expect(
          page.getByRole("button", { name: /فیلتر و مرتب‌سازی/ }),
        ).toBeHidden();
      }
    });
  }
});


test("mobile filter dialog applies Toman and preserves other filters", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/shop?category=rings&material=gold&in_stock=true");

  const { dialog } = await openMobileFilters(page);
  await dialog.getByLabel("حداقل قیمت").fill("500000");
  await dialog.getByLabel("حداکثر قیمت").fill("900000");
  await dialog.getByRole("button", { name: "اعمال فیلترها" }).click();

  await expect(page).toHaveURL(/min_price_toman=500000/);
  const url = new URL(page.url());
  expect(url.searchParams.get("max_price_toman")).toBe("900000");
  expect(url.searchParams.get("category")).toBe("rings");
  expect(url.searchParams.get("material")).toBe("gold");
  expect(url.searchParams.get("in_stock")).toBe("true");
});


test("invalid and reversed price ranges are explained without querying products", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/shop");

  const { dialog } = await openMobileFilters(page);
  await dialog.getByLabel("حداقل قیمت").fill("900000");
  await dialog.getByLabel("حداکثر قیمت").fill("500000");
  await dialog.getByRole("button", { name: "اعمال فیلترها" }).click();

  await expect(page.getByRole("alert")).toContainText("بازه‌ی قیمت معتبر نیست");
  await expect(page.getByRole("heading", { name: "فیلتر قیمت را اصلاح کنید" })).toBeVisible();
});


test("women catalog remains fixed even when a conflicting gender query is supplied", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/women?gender=men");

  await expect(
    page.getByRole("heading", { level: 1, name: "مجموعه‌ی زنانه" }),
  ).toBeVisible();

  const { dialog } = await openMobileFilters(page);
  await expect(dialog.getByRole("group", { name: "مناسب برای" })).toHaveCount(0);
  await dialog.getByLabel("حداقل قیمت").fill("500000");
  await dialog.getByRole("button", { name: "اعمال فیلترها" }).click();

  await expect(page).toHaveURL(/min_price_toman=500000/);
  expect(new URL(page.url()).searchParams.has("gender")).toBe(false);
});


test("search text survives applying a price filter", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/search?q=%DA%AF%D8%B1%D8%AF%D9%86%D8%A8%D9%86%D8%AF");

  const { dialog } = await openMobileFilters(page);
  await dialog.getByLabel("حداقل قیمت").fill("750000");
  await dialog.getByRole("button", { name: "اعمال فیلترها" }).click();

  await expect(page).toHaveURL(/min_price_toman=750000/);
  expect(new URL(page.url()).searchParams.get("q")).toBe("گردنبند");
});


test("filter dialog closes on Escape and restores focus", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/shop");

  const { trigger, dialog } = await openMobileFilters(page);
  await page.keyboard.press("Escape");

  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
});


test("desktop filter rail meets automated WCAG 2.2 AA checks", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/shop");

  const results = await new AxeBuilder({ page })
    .include('aside[aria-label="فیلترهای محصولات"]')
    .withTags(wcagTags)
    .analyze();

  expect(results.violations).toEqual([]);
});


test("mobile filter dialog meets automated WCAG 2.2 AA checks", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/shop");

  await openMobileFilters(page);

  const results = await new AxeBuilder({ page })
    .include("#catalog-filter-dialog")
    .withTags(wcagTags)
    .analyze();

  expect(results.violations).toEqual([]);
});
