import {
  getCsrfToken,
} from "@/lib/auth-api";

import type {
  Cart,
  CartApiErrorPayload,
} from "@/types/cart";


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL;


function getApiBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URL is not configured.",
    );
  }

  return API_BASE_URL;
}


export class CartApiError extends Error {
  status: number;
  code?: string;
  available?: number;

  constructor(
    status: number,
    payload: CartApiErrorPayload,
  ) {
    super(
      payload.detail ||
        "Cart request failed.",
    );

    this.name = "CartApiError";
    this.status = status;
    this.code = payload.code;
    this.available = payload.available;
  }
}


async function parseErrorResponse(
  response: Response,
): Promise<CartApiErrorPayload> {
  try {
    return await response.json();
  } catch {
    return {
      detail: `Cart request failed: ${response.status}`,
    };
  }
}


async function assertCartResponse(
  response: Response,
): Promise<Cart> {
  if (!response.ok) {
    const payload =
      await parseErrorResponse(response);

    throw new CartApiError(
      response.status,
      payload,
    );
  }

  return response.json();
}


export async function createCart(): Promise<Cart> {
  /*
   * credentials: "include" is required so the session cookie
   * reaches the API and authenticated users get their account
   * cart (get-or-create) instead of an anonymous one.
   *
   * Authenticated POSTs are CSRF-protected (Django Session
   * Authentication), so always send the CSRF token header.
   */
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `${getApiBaseUrl()}/cart/`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({}),
    },
  );

  return assertCartResponse(response);
}


export async function getCart(
  token: string,
): Promise<Cart> {
  const response = await fetch(
    `${getApiBaseUrl()}/cart/`,
    {
      method: "GET",
      credentials: "include",
      headers: {
        "X-Cart-Token": token,
      },
      cache: "no-store",
    },
  );

  return assertCartResponse(response);
}


export async function addCartItem(
  token: string,
  variantSku: string,
  quantity = 1,
): Promise<Cart> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `${getApiBaseUrl()}/cart/items/`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
        "X-Cart-Token": token,
      },
      body: JSON.stringify({
        variant_sku: variantSku,
        quantity,
      }),
    },
  );

  return assertCartResponse(response);
}


export async function updateCartItem(
  token: string,
  itemId: number,
  quantity: number,
): Promise<Cart> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `${getApiBaseUrl()}/cart/items/${itemId}/`,
    {
      method: "PATCH",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
        "X-Cart-Token": token,
      },
      body: JSON.stringify({
        quantity,
      }),
    },
  );

  return assertCartResponse(response);
}


export async function deleteCartItem(
  token: string,
  itemId: number,
): Promise<void> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `${getApiBaseUrl()}/cart/items/${itemId}/`,
    {
      method: "DELETE",
      credentials: "include",
      headers: {
        "X-CSRFToken": csrfToken,
        "X-Cart-Token": token,
      },
    },
  );

  if (!response.ok) {
    const payload =
      await parseErrorResponse(response);

    throw new CartApiError(
      response.status,
      payload,
    );
  }
}
