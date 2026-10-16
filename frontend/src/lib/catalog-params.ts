/**
 * Listing URL state.
 *
 * Filters, sorting, search and paging live in the URL, so a filtered
 * listing is always shareable, bookmarkable and server-rendered. These
 * helpers are the single place that reads query params into API params
 * and builds hrefs back to the URL.
 */

import type {
  ProductListParams,
} from "./catalog-api";

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


/** Digits-only integer (Persian/Arabic digits are normalized server-side). */
function toPositiveInt(
  value: string | undefined,
): number | undefined {
  const cleaned = clean(value);

  if (!cleaned) {
    return undefined;
  }

  const digits = cleaned.replace(/[^\d۰-۹٠-٩]/g, "");

  if (!digits) {
    return undefined;
  }

  const ascii = digits.replace(/[۰-۹]/g, (d) =>
    String("۰۱۲۳۴۵۶۷۸۹".indexOf(d)),
  ).replace(/[٠-٩]/g, (d) =>
    String("٠١٢٣٤٥٦٧٨٩".indexOf(d)),
  );

  const parsed = Number(ascii);

  return Number.isFinite(parsed) && parsed > 0
    ? parsed
    : undefined;
}


export type CatalogSearchState = {
  apiParams: ProductListParams;
  query: string;
  ordering: string;
  page: number;
  category?: string;
  material?: string;
  gender?: string;
  inStock: boolean;
  minPrice?: number;
  maxPrice?: number;
  hasActiveFilters: boolean;
};


export function parseCatalogSearchParams(
  searchParams: RawSearchParams,
  defaults: { gender?: string; material?: string } = {},
): CatalogSearchState {
  const category = clean(first(searchParams.category));
  const collection = clean(first(searchParams.collection));
  const query = clean(first(searchParams.q)) ?? "";

  const ordering =
    clean(first(searchParams.ordering)) ?? "newest";

  const material =
    clean(first(searchParams.material)) ?? defaults.material;

  const gender =
    clean(first(searchParams.gender)) ?? defaults.gender;

  const inStock =
    ["1", "true", "yes"].includes(
      (clean(first(searchParams.in_stock)) ?? "").toLowerCase(),
    );

  const minPrice = toPositiveInt(first(searchParams.min_price));
  const maxPrice = toPositiveInt(first(searchParams.max_price));

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

  if (minPrice !== undefined) {
    apiParams.min_price = minPrice;
  }

  if (maxPrice !== undefined) {
    apiParams.max_price = maxPrice;
  }

  if (inStock) {
    apiParams.in_stock = true;
  }

  if (query) {
    apiParams.q = query;
  }

  return {
    apiParams,
    query,
    ordering,
    page,
    category,
    material,
    gender,
    inStock,
    minPrice,
    maxPrice,
    hasActiveFilters: Boolean(
      category ||
        collection ||
        material ||
        gender ||
        inStock ||
        minPrice !== undefined ||
        maxPrice !== undefined ||
        query,
    ),
  };
}


export type BuildHrefOptions = {
  pathname: string;
  searchParams: RawSearchParams;
  /** Params to set; `null`/undefined removes them. `page` resets. */
  set?: Record<string, string | number | boolean | null | undefined>;
  /** Keep the current page number (used by sorting). */
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
