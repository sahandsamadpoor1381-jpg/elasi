/** Customer-owned order read APIs. Authentication/ownership live in Django. */
import { apiRequest } from "@/lib/api-client";
import type { Order } from "@/types/order";

export type CustomerOrderPage = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Order[];
};

export function getCustomerOrders(page = 1, signal?: AbortSignal) {
  if (!Number.isSafeInteger(page) || page < 1) {
    throw new Error("Invalid order page");
  }
  return apiRequest<CustomerOrderPage>(`/orders/?page=${page}`, { signal });
}

export function getCustomerOrder(publicId: string, signal?: AbortSignal) {
  // Never interpolate unvalidated path segments into the API URL.
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(publicId)) {
    throw new Error("Invalid order reference");
  }
  return apiRequest<Order>(`/orders/${publicId}/`, { signal });
}
