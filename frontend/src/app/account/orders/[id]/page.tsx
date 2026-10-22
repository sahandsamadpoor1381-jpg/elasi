import type { Metadata } from "next";
import { OrderDetailClient } from "@/components/orders/order-detail-client";

export const metadata: Metadata = {
  title: "جزئیات سفارش",
  robots: { index: false, follow: false },
};

export default async function CustomerOrderDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <OrderDetailClient publicId={id} />;
}
