/**
 * Checkout API client.
 *
 * Prices and totals stay server-authoritative: this module only sends
 * the customer's shipping details and reads back the order the backend
 * created. Never recompute money on the client.
 */

import {
  ApiError,
  apiRequest,
} from "./api-client";

import type {
  CheckoutApiErrorPayload,
  CheckoutPayload,
  Order,
} from "@/types/order";


export class CheckoutApiError extends ApiError {
  payload: CheckoutApiErrorPayload;

  constructor(
    status: number,
    payload: CheckoutApiErrorPayload,
  ) {
    super(
      typeof payload.detail === "string"
        ? payload.detail
        : `Checkout request failed with status ${status}`,
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
        sku:
          typeof payload.sku === "string"
            ? payload.sku
            : undefined,
        payload,
      },
    );

    this.name = "CheckoutApiError";
    this.payload = payload;
  }
}


export async function checkoutCart(
  cartToken: string,
  payload: CheckoutPayload,
): Promise<Order> {
  try {
    return await apiRequest<Order>("/checkout/", {
      method: "POST",
      body: payload,
      headers: { "X-Cart-Token": cartToken },
    });
  } catch (error) {
    if (error instanceof ApiError) {
      throw new CheckoutApiError(
        error.status,
        error.payload as CheckoutApiErrorPayload,
      );
    }

    throw error;
  }
}
