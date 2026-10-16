import {
  getCsrfToken,
} from "@/lib/auth-api";

import type {
  CheckoutApiErrorPayload,
  CheckoutPayload,
  Order,
} from "@/types/order";


const API_BASE_URL =
  process.env
    .NEXT_PUBLIC_API_BASE_URL;


function getApiBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URL is not configured.",
    );
  }

  return API_BASE_URL;
}


export class CheckoutApiError
  extends Error {
  status: number;

  code?: string;
  available?: number;
  sku?: string;

  payload:
    CheckoutApiErrorPayload;


  constructor(
    status: number,
    payload:
      CheckoutApiErrorPayload,
  ) {
    super(
      payload.detail ||
        "Checkout request failed.",
    );

    this.name =
      "CheckoutApiError";

    this.status = status;
    this.code = payload.code;
    this.available =
      payload.available;
    this.sku = payload.sku;

    this.payload = payload;
  }
}


async function parseErrorResponse(
  response: Response,
): Promise<CheckoutApiErrorPayload> {
  try {
    const payload =
      await response.json();

    if (
      payload &&
      typeof payload ===
        "object"
    ) {
      return payload;
    }
  } catch {
    // Fall through.
  }

  return {
    detail:
      `Checkout request failed: ${response.status}`,
  };
}


export async function checkoutCart(
  cartToken: string,
  payload: CheckoutPayload,
): Promise<Order> {
  const csrfToken =
    await getCsrfToken();

  const response =
    await fetch(
      `${getApiBaseUrl()}/checkout/`,
      {
        method: "POST",

        credentials:
          "include",

        headers: {
          "Content-Type":
            "application/json",

          "X-CSRFToken":
            csrfToken,

          "X-Cart-Token":
            cartToken,
        },

        body:
          JSON.stringify(
            payload,
          ),
      },
    );


  if (!response.ok) {
    const errorPayload =
      await parseErrorResponse(
        response,
      );

    throw new CheckoutApiError(
      response.status,
      errorPayload,
    );
  }


  return response.json();
}