/**
 * Listing URL state.
 *
 * Storefront filters stay in the URL so they are bookmarkable, shareable,
 * server-rendered, and navigable with the browser's Back/Forward controls.
 * Public price fields use Toman; the API and database use Rial.
 */

import type { ProductListParams } from "./catalog-api";

import type {
  ProductMaterial,
  ProductOrdering,
} from "@/types/catalog";


export type RawSearchParams = Record<
  string,
  string | string[] | undefined
>;


export const PAGE_SIZE = 12;

export const CATALOG_ORDERINGS: ProductOrdering[] = [
  "newest",
  "featured",
  "price_asc",
  "price_desc",
  "name",
];

export const CATALOG_MATERIALS: ProductMaterial[] = [
  "gold",
  "silver",
];

export const CATALOG_GENDERS = [
  "women",
  "men",
  "unisex",
] as const;


type ParsedInteger = {
  present: boolean;
  valid: boolean;
  value?: number;
};


function first(
  value: string | string[] | undefined,
): string | undefined {
  if (Array.isArray(value)) {
    return value[0];
  }

  return value ?? undefined;
}


function clean(value: string | undefined): string | undefined {
  const trimmed = value?.trim();

  return trimmed ? trimmed : undefined;
}


function normalizeDigits(value: string): string {
  return value
    .replace(/[۰-۹]/g, (digit) =>
      String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)),
    )
    .replace(/[٠-٩]/g, (digit) =>
      String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)),
    );
}


/**
 * Parse a non-negative integer without silently turning malformed input
 * such as "1.5" or "abc2" into a different price.
 */
function parseNonNegativeInt(value: string | undefined): ParsedInteger {
  const trimmed = value?.trim();

  if (!trimmed) {
    return { present: false, valid: true };
  }

  // Thousands separators are accepted for copy/pasted Persian or Latin
  // amounts. Decimal points, signs, and letters are intentionally rejected.
  const ungrouped = trimmed.replace(/[\s,٬]/g, "");

  if (!/^[0-9۰-۹٠-٩]+$/.test(ungrouped)) {
    return { present: true, valid: false };
  }

  const parsed = Number(normalizeDigits(ungrouped));

  if (!Number.isSafeInteger(parsed) || parsed < 0) {
    return { present: true, valid: false };
  }

  return { present: true, valid: true, value: parsed };
}


/** Digits-only positive integer, used for pages rather than money. */
function toPositiveInt(value: string | undefined): number | undefined {
  const parsed = parseNonNegativeInt(value);

  return parsed.valid && parsed.value !== undefined && parsed.value > 0
    ? parsed.value
    : undefined;
}


type ParsedPriceBound = {
  rial?: number;
  toman?: number;
  input?: string;
  present: boolean;
  invalid: boolean;
};


function parsePriceBound(
  searchParams: RawSearchParams,
  bound: "min" | "max",
): ParsedPriceBound {
  const tomanKey = `${bound}_price_toman`;
  const rialKey = `${bound}_price`;
  const tomanRaw = first(searchParams[tomanKey]);

  // New storefront URLs are unambiguous and customer-facing in Toman.
  if (tomanRaw !== undefined) {
    const parsed = parseNonNegativeInt(tomanRaw);

    if (!parsed.valid) {
      return {
        input: tomanRaw,
        present: true,
        invalid: true,
      };
    }

    if (!parsed.present || parsed.value === undefined) {
      return { present: false, invalid: false };
    }

    const rial = parsed.value * 10;

    if (!Number.isSafeInteger(rial)) {
      return {
        input: tomanRaw,
        present: true,
        invalid: true,
      };
    }

    return {
      rial,
      toman: parsed.value,
      input: tomanRaw.trim(),
      present: true,
      invalid: false,
    };
  }

  // Backwards compatibility: existing min_price/max_price links were Rial.
  const rialRaw = first(searchParams[rialKey]);

  if (rialRaw === undefined) {
    return { present: false, invalid: false };
  }

  const parsed = parseNonNegativeInt(rialRaw);

  if (!parsed.valid) {
    return {
      input: rialRaw,
      present: true,
      invalid: true,
    };
  }

  if (!parsed.present || parsed.value === undefined) {
    return { present: false, invalid: false };
  }

  const toman =
    bound === "min"
      ? Math.ceil(parsed.value / 10)
      : Math.floor(parsed.value / 10);

  return {
    rial: parsed.value,
    toman,
    input: String(toman),
    present: true,
    invalid: false,
  };
}


export type CatalogSearchState = {
  apiParams: ProductListParams;
  query: string;
  collection?: string;
  ordering: ProductOrdering;
  page: number;
  category?: string;
  material?: ProductMaterial;
  gender?: (typeof CATALOG_GENDERS)[number];
  inStock: boolean;
  minPriceToman?: number;
  maxPriceToman?: number;
  minPriceInput?: string;
  maxPriceInput?: string;
  minPriceRial?: number;
  maxPriceRial?: number;
  priceRangeError: boolean;
  hasActiveFilters: boolean;
};


export function parseCatalogSearchParams(
  searchParams: RawSearchParams,
  defaults: { gender?: string; material?: string } = {},
): CatalogSearchState {
  const category = clean(first(searchParams.category));
  const collection = clean(first(searchParams.collection));
  const query = clean(first(searchParams.q)) ?? "";

  const requestedOrdering = clean(first(searchParams.ordering));
  const ordering = CATALOG_ORDERINGS.includes(
    requestedOrdering as ProductOrdering,
  )
    ? (requestedOrdering as ProductOrdering)
    : "newest";

  const requestedMaterial = clean(first(searchParams.material));
  const material = defaults.material
    ? (defaults.material as ProductMaterial)
    : CATALOG_MATERIALS.includes(requestedMaterial as ProductMaterial)
      ? (requestedMaterial as ProductMaterial)
      : undefined;

  // Gender-specific pages are a hard scope, not a user-overridable default.
  // /women?gender=men must never request men's products.
  const requestedGender = clean(first(searchParams.gender));
  const gender = defaults.gender
    ? (defaults.gender as (typeof CATALOG_GENDERS)[number])
    : CATALOG_GENDERS.includes(
          requestedGender as (typeof CATALOG_GENDERS)[number],
        )
      ? (requestedGender as (typeof CATALOG_GENDERS)[number])
      : undefined;

  const inStock = ["1", "true", "yes"].includes(
    (clean(first(searchParams.in_stock)) ?? "").toLowerCase(),
  );

  const minPrice = parsePriceBound(searchParams, "min");
  const maxPrice = parsePriceBound(searchParams, "max");
  const invalidOrReversedPriceRange =
    minPrice.invalid ||
    maxPrice.invalid ||
    (minPrice.rial !== undefined &&
      maxPrice.rial !== undefined &&
      minPrice.rial > maxPrice.rial);

  const page = toPositiveInt(first(searchParams.page)) ?? 1;

  const apiParams: ProductListParams = {
    page,
    page_size: PAGE_SIZE,
    ordering,
  };

  if (category) {
    apiParams.category = category;
  }

  if (collection) {
    apiParams.collection = collection;
  }

  if (gender) {
    apiParams.gender = gender;
  }

  if (material) {
    apiParams.material = material;
  }

  // The API accepts Rial only. Toman from the storefront is converted once,
  // at this boundary. Invalid/reversed ranges never reach the API.
  if (!invalidOrReversedPriceRange && minPrice.rial !== undefined) {
    apiParams.min_price = minPrice.rial;
  }

  if (!invalidOrReversedPriceRange && maxPrice.rial !== undefined) {
    apiParams.max_price = maxPrice.rial;
  }

  if (inStock) {
    apiParams.in_stock = true;
  }

  if (query) {
    apiParams.q = query;
  }

  const hasPriceBound = minPrice.present || maxPrice.present;
  const hasNonDefaultGender = Boolean(gender && !defaults.gender);
  const hasNonDefaultMaterial = Boolean(
    material && material !== defaults.material,
  );

  return {
    apiParams,
    query,
    collection,
    ordering,
    page,
    category,
    material,
    gender,
    inStock,
    minPriceToman: minPrice.toman,
    maxPriceToman: maxPrice.toman,
    minPriceInput: minPrice.input,
    maxPriceInput: maxPrice.input,
    minPriceRial: minPrice.rial,
    maxPriceRial: maxPrice.rial,
    priceRangeError: invalidOrReversedPriceRange,
    // Route scope (for example, the fixed Women's collection) is not an
    // active user filter and must not show a false "clear filters" state.
    hasActiveFilters: Boolean(
      category ||
        collection ||
        hasNonDefaultMaterial ||
        hasNonDefaultGender ||
        inStock ||
        hasPriceBound ||
        query,
    ),
  };
}


export type BuildHrefOptions = {
  pathname: string;
  searchParams: RawSearchParams;
  /** Params to set; `null`/undefined removes them. `page` resets. */
  set?: Record<string, string | number | boolean | null | undefined>;
  /** Keep the current page number (used by pagination). */
  keepPage?: boolean;
};


export function buildCatalogHref({
  pathname,
  searchParams,
  set = {},
  keepPage = false,
}: BuildHrefOptions): string {
  const params = new URLSearchParams();

  for (const [key, rawValue] of Object.entries(searchParams)) {
    const value = first(rawValue);

    if (value === undefined || value === "") {
      continue;
    }

    params.set(key, value);
  }

  for (const [key, value] of Object.entries(set)) {
    if (value === null || value === undefined || value === false) {
      params.delete(key);
      continue;
    }

    params.set(key, value === true ? "true" : String(value));
  }

  if (!keepPage) {
    params.delete("page");
  }

  const query = params.toString();

  return query ? `${pathname}?${query}` : pathname;
}


/** Clear customer-selected search and filter state while preserving a fixed route scope. */
export function buildClearCatalogHref({
  pathname,
  searchParams,
}: {
  pathname: string;
  searchParams: RawSearchParams;
}): string {
  return buildCatalogHref({
    pathname,
    searchParams,
    set: {
      q: null,
      category: null,
      collection: null,
      material: null,
      gender: null,
      in_stock: null,
      min_price: null,
      max_price: null,
      min_price_toman: null,
      max_price_toman: null,
      ordering: null,
    },
  });
}
