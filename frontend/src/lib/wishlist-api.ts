/**
 * Wishlist API client.
 *
 * Requires an authenticated session: the backend answers guests with
 * 401/403 and a stable `not_authenticated` code, which the storefront
 * turns into a clear sign-in path rather than a silent failure.
 */

import { apiRequest } from "./api-client";

import type { Paginated } from "@/types/catalog";
import type { WishlistItem } from "@/types/wishlist";


export const WISHLIST_PAGE_SIZE = 24;


export async function getWishlistPage(
  params: { page?: number; page_size?: number } = {},
): Promise<Paginated<WishlistItem>> {
  const search = new URLSearchParams();

  search.set(
    "page_size",
    String(params.page_size ?? WISHLIST_PAGE_SIZE),
  );

  if (params.page && params.page > 1) {
    search.set("page", String(params.page));
  }

  return apiRequest<Paginated<WishlistItem>>(
    `/wishlist/?${search.toString()}`,
    { method: "GET" },
  );
}


export async function addToWishlist(
  productSlug: string,
): Promise<WishlistItem> {
  return apiRequest<WishlistItem>("/wishlist/", {
    method: "POST",
    body: { product: productSlug },
  });
}


export async function removeFromWishlist(
  productSlug: string,
): Promise<void> {
  await apiRequest<void>(
    `/wishlist/items/${encodeURIComponent(productSlug)}/`,
    { method: "DELETE" },
  );
}
