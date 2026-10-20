import assert from "node:assert/strict";
import test from "node:test";

import {
  buildCatalogHref,
  buildClearCatalogHref,
  parseCatalogSearchParams,
} from "../src/lib/catalog-params.ts";


test("converts customer-entered Toman to API Rial exactly once", () => {
  const state = parseCatalogSearchParams({
    min_price_toman: "500000",
    max_price_toman: "1500000",
  });

  assert.equal(state.apiParams.min_price, 5_000_000);
  assert.equal(state.apiParams.max_price, 15_000_000);
  assert.equal(state.minPriceToman, 500_000);
  assert.equal(state.maxPriceToman, 1_500_000);
  assert.equal(state.priceRangeError, false);
});


test("normalizes Persian digits and grouped Toman amounts", () => {
  const state = parseCatalogSearchParams({
    min_price_toman: "۱٬۲۵۰٬۰۰۰",
    max_price_toman: "۲٬۵۰۰٬۰۰۰",
  });

  assert.equal(state.apiParams.min_price, 12_500_000);
  assert.equal(state.apiParams.max_price, 25_000_000);
});


test("keeps legacy min_price/max_price links in Rial", () => {
  const state = parseCatalogSearchParams({
    min_price: "20000000",
    max_price: "45000000",
  });

  assert.equal(state.apiParams.min_price, 20_000_000);
  assert.equal(state.apiParams.max_price, 45_000_000);
  assert.equal(state.minPriceToman, 2_000_000);
  assert.equal(state.maxPriceToman, 4_500_000);
});


test("does not send a reversed range to the catalog API", () => {
  const state = parseCatalogSearchParams({
    min_price_toman: "2000000",
    max_price_toman: "1000000",
  });

  assert.equal(state.priceRangeError, true);
  assert.equal("min_price" in state.apiParams, false);
  assert.equal("max_price" in state.apiParams, false);
});


test("rejects malformed price input instead of silently changing it", () => {
  const state = parseCatalogSearchParams({
    min_price_toman: "12.5",
  });

  assert.equal(state.priceRangeError, true);
  assert.equal("min_price" in state.apiParams, false);
  assert.equal(state.minPriceInput, "12.5");
});


test("keeps women and men routes inside their fixed gender scope", () => {
  const women = parseCatalogSearchParams(
    { gender: "men" },
    { gender: "women" },
  );
  const men = parseCatalogSearchParams(
    { gender: "women" },
    { gender: "men" },
  );

  assert.equal(women.apiParams.gender, "women");
  assert.equal(women.gender, "women");
  assert.equal(women.hasActiveFilters, false);
  assert.equal(men.apiParams.gender, "men");
  assert.equal(men.hasActiveFilters, false);
});


test("ignores unsupported ordering, material, and gender values", () => {
  const state = parseCatalogSearchParams({
    ordering: "untrusted",
    material: "platinum",
    gender: "children",
  });

  assert.equal(state.ordering, "newest");
  assert.equal(state.material, undefined);
  assert.equal(state.gender, undefined);
  assert.equal(state.apiParams.material, undefined);
  assert.equal(state.apiParams.gender, undefined);
});


test("filter links preserve other URL state and reset pagination", () => {
  assert.equal(
    buildCatalogHref({
      pathname: "/shop",
      searchParams: {
        q: "گوشواره",
        category: "earrings",
        page: "4",
      },
      set: { category: null, material: "gold" },
    }),
    "/shop?q=%DA%AF%D9%88%D8%B4%D9%88%D8%A7%D8%B1%D9%87&material=gold",
  );
});


test("clear-filter links remove all customer selections", () => {
  assert.equal(
    buildClearCatalogHref({
      pathname: "/women",
      searchParams: {
        gender: "men",
        category: "rings",
        min_price: "25000000",
        min_price_toman: "3000000",
        q: "انگشتر",
      },
    }),
    "/women",
  );
});
