import type { Metadata } from "next";
import { OrdersClient } from "@/components/orders/orders-client";

export const metadata: Metadata = {
  title: "سفارش‌های من",
  description: "مشاهده سفارش‌های ثبت‌شده و وضعیت آن‌ها در ELASI.",
  robots: { index: false, follow: false },
};

export default function CustomerOrdersPage() {
  return <OrdersClient />;
}
