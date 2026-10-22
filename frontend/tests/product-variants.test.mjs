import assert from "node:assert/strict";
import test from "node:test";

import { formatToman } from "../src/lib/format.ts";
import {
  activeProductVariants,
  canBuyProductVariant,
  defaultProductVariant,
  validCompareAtPriceRial,
} from "../src/lib/product-variants.ts";

const variant = (overrides = {}) => ({
  sku: "ELASI-001",
  material: "gold",
  karat: 18,
  purity: "",
  size: "",
  weight_grams: "1.25",
  price_rial: 18_000_000,
  compare_at_price_rial: null,
  is_active: true,
  available: 0,
  ...overrides,
});

test("selects the first in-stock active variant, not an out-of-stock or inactive one", () => {
  const inactive = variant({ sku: "inactive", is_active: false, available: 9 });
  const outOfStock = variant({ sku: "out", available: 0 });
  const inStock = variant({ sku: "in", available: 2 });
  assert.deepEqual(activeProductVariants([inactive, outOfStock, inStock]), [outOfStock, inStock]);
  assert.equal(defaultProductVariant([inactive, outOfStock, inStock])?.sku, "in");
});

test("all sold out shows a variant but does not enable buying", () => {
  const outOfStock = variant({ sku: "out" });
  assert.equal(defaultProductVariant([outOfStock])?.sku, "out");
  assert.equal(canBuyProductVariant(outOfStock), false);
  assert.equal(canBuyProductVariant(null), false);
  assert.equal(canBuyProductVariant(variant({ is_active: false, available: 3 })), false);
  assert.equal(canBuyProductVariant(variant({ available: 1 })), true);
});

test("a product without active variants has no purchasable variant", () => {
  assert.equal(defaultProductVariant([]), null);
  assert.equal(defaultProductVariant([variant({ is_active: false, available: 4 })]), null);
});

test("comparison price only appears when greater than the actual server price", () => {
  assert.equal(validCompareAtPriceRial(variant({ compare_at_price_rial: 20_000_000 })), 20_000_000);
  assert.equal(validCompareAtPriceRial(variant({ compare_at_price_rial: 18_000_000 })), null);
  assert.equal(validCompareAtPriceRial(variant({ compare_at_price_rial: 12_000_000 })), null);
  assert.equal(validCompareAtPriceRial(variant({ compare_at_price_rial: null })), null);
  assert.equal(validCompareAtPriceRial(null), null);
});

test("PDP converts server Rial prices into Toman exactly once", () => {
  assert.equal(formatToman(18_000_000), "۱٬۸۰۰٬۰۰۰");
});

test("Django media URLs use the existing same-origin proxy path", async () => {
  const { mediaPath } = await import("../src/lib/media.ts");
  assert.equal(
    mediaPath("http://127.0.0.1:8000/media/products/ring.jpg"),
    "/media/products/ring.jpg",
  );
  assert.equal(
    mediaPath("https://api.example.org/media/products/bracelet.webp?v=2"),
    "/media/products/bracelet.webp?v=2",
  );
  assert.equal(mediaPath("/media/products/pendant.jpg"), "/media/products/pendant.jpg");
  assert.equal(mediaPath(null), null);
});
