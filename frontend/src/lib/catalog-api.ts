/**
 * Catalog API client.
 *
 * Used from React Server Components (homepage, product page) as well as
 * client components; `apiRequest` resolves the correct base URL for
 * each runtime (absolute internal origin on the server, same-origin
 * `/api/v1` in the browser).
 */

import { apiRequest } from "./api-client";

import type { Product } from "@/types/catalog";


export async function getProducts(): Promise<Product[]> {
  return apiRequest<Product[]>("/products/", {
    method: "GET",
  });
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
