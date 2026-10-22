import type { OrderStatus } from "@/types/order";

const statuses: Record<OrderStatus, string> = {
  pending_payment: "در انتظار پرداخت",
  paid: "پرداخت‌شده",
  processing: "در حال آماده‌سازی",
  shipped: "ارسال‌شده",
  delivered: "تحویل‌شده",
  cancelled: "لغوشده",
  expired: "منقضی‌شده",
};

export function orderStatusLabel(status: OrderStatus): string {
  return statuses[status] ?? "وضعیت نامشخص";
}

export function orderToman(rial: number): string {
  return `${new Intl.NumberFormat("fa-IR").format(rial / 10)} تومان`;
}

export function orderDate(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? "تاریخ نامشخص"
    : new Intl.DateTimeFormat("fa-IR", {
        year: "numeric",
        month: "long",
        day: "numeric",
      }).format(parsed);
}


/** Display progress only for confirmed fulfillment states. */
export function orderFulfillmentStep(status: OrderStatus): number {
  switch (status) {
    case "paid":
      return 1;
    case "processing":
      return 2;
    case "shipped":
      return 3;
    case "delivered":
      return 4;
    default:
      return 0;
  }
}
