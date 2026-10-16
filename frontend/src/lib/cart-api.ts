/**
 * Cart API client.
 *
 * Uses the shared client so the CSRF token is attached to every unsafe
 * request and refreshed automatically when Django rotates it. The guest
 * cart token keeps travelling in `X-Cart-Token` exactly as before, so
 * the Phase 01 ownership rules are untouched.
 */

import {
  ApiError,
  apiRequest,
} from "./api-client";

import type {
  Cart,
  CartApiErrorPayload,
} from "@/types/cart";


export class CartApiError extends ApiError {
  payload: CartApiErrorPayload;

  constructor(
    status: number,
    payload: CartApiErrorPayload,
  ) {
    super(
      typeof payload.detail === "string"
        ? payload.detail
        : `Cart request failed with status ${status}`,
      {
        status,
        code:
          typeof payload.code === "string"
            ? payload.code
            : undefined,
        available:
          typeof payload.available === "number"
            ? payload.available
            : undefined,
        payload,
      },
    );

    this.name = "CartApiError";
    this.payload = payload;
  }
}


async function request<T>(
  path: string,
  init: {
    method?: string;
    body?: unknown;
    token?: string;
  },
): Promise<T> {
  try {
    return await apiRequest<T>(path, {
      method: init.method,
      body: init.body,
      headers: init.token
        ? { "X-Cart-Token": init.token }
        : undefined,
    });
  } catch (error) {
    if (error instanceof ApiError) {
      throw new CartApiError(
        error.status,
        error.payload as CartApiErrorPayload,
      );
    }

    throw error;
  }
}


export async function createCart(): Promise<Cart> {
  /*
   * credentials: "include" is required so the session cookie reaches
   * the API and authenticated users get their account cart
   * (get-or-create) instead of an anonymous one.
   */
  return request<Cart>("/cart/", {
    method: "POST",
    body: {},
  });
}


export async function getCart(token: string): Promise<Cart> {
  return request<Cart>("/cart/", {
    method: "GET",
    token,
  });
}


export async function addCartItem(
  token: string,
  variantSku: string,
  quantity = 1,
): Promise<Cart> {
  return request<Cart>("/cart/items/", {
    method: "POST",
    token,
    body: {
      variant_sku: variantSku,
      quantity,
    },
  });
}


export async function updateCartItem(
  token: string,
  itemId: number,
  quantity: number,
): Promise<Cart> {
  return request<Cart>(`/cart/items/${itemId}/`, {
    method: "PATCH",
    token,
    body: { quantity },
  });
}


export async function deleteCartItem(
  token: string,
  itemId: number,
): Promise<void> {
  await request<void>(`/cart/items/${itemId}/`, {
    method: "DELETE",
    token,
  });
}
