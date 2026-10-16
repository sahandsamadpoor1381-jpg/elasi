/**
 * Catalog API client.
 *
 * Used from React Server Components (homepage, listing pages, product
 * page) as well as client components; `apiRequest` resolves the correct
 * base URL for each runtime (absolute internal origin on the server,
 * same-origin `/api/v1` in the browser).
 *
 * Every listing is filtered, ordered and paginated **by the server** -
 * the storefront never downloads the catalog to filter it locally.
 */

import { apiRequest } from "./api-client";

import type {
  CategorySummary,
  CollectionSummary,
  Paginated,
  Product,
  ProductMaterial,
  ProductOrdering,
  ProductSummary,
} from "@/types/catalog";


export type ProductListParams = {
  category?: string;
  collection?: string;
  gender?: string;
  material?: ProductMaterial | string;
  min_price?: number | string;
  max_price?: number | string;
  in_stock?: boolean;
  is_featured?: boolean;
  ordering?: ProductOrdering | string;
  q?: string;
  page?: number;
  page_size?: number;
};


export function buildProductQuery(
  params: ProductListParams = {},
): string {
  const search = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }

    search.set(
      key,
      typeof value === "boolean"
        ? value
          ? "true"
          : "false"
        : String(value),
    );
  }

  const query = search.toString();

  return query ? `?${query}` : "";
}


export async function getProductPage(
  params: ProductListParams = {},
): Promise<Paginated<ProductSummary>> {
  return apiRequest<Paginated<ProductSummary>>(
    `/products/${buildProductQuery(params)}`,
    { method: "GET" },
  );
}


/**
 * First page of the listing. Kept for callers that only need a
 * representative set (the homepage showcase).
 */
export async function getProducts(): Promise<ProductSummary[]> {
  const page = await getProductPage({ page_size: 12 });

  return page.results;
}


export async function searchProducts(
  query: string,
  params: ProductListParams = {},
): Promise<Paginated<ProductSummary>> {
  return apiRequest<Paginated<ProductSummary>>(
    `/products/search/${buildProductQuery({ ...params, q: query })}`,
    { method: "GET" },
  );
}


export async function getProduct(
  slug: string,
): Promise<Product | null> {
  try {
    return await apiRequest<Product>(
      `/products/${encodeURIComponent(slug)}/`,
      { method: "GET" },
    );
  } catch (error) {
    if (
      error instanceof Error &&
      "status" in error &&
      (error as { status?: number }).status === 404
    ) {
      return null;
    }

    throw error;
  }
}


export async function getCategories(): Promise<CategorySummary[]> {
  return apiRequest<CategorySummary[]>("/categories/", {
    method: "GET",
  });
}


export async function getCollections(): Promise<CollectionSummary[]> {
  return apiRequest<CollectionSummary[]>("/collections/", {
    method: "GET",
  });
}
