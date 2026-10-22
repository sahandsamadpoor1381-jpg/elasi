"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowRight, PackageCheck } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { customerMessage } from "@/lib/api-client";
import { getCustomerOrder } from "@/lib/orders-api";
import { orderDate, orderFulfillmentStep, orderStatusLabel, orderToman } from "@/lib/order-presentation";
import type { Order } from "@/types/order";

export function OrderDetailClient({ publicId }: { publicId: string }) {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [orderOwner, setOrderOwner] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(`/account/orders/${publicId}`)}`);
      return;
    }
    const controller = new AbortController();
    getCustomerOrder(publicId, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setOrder(result);
          setOrderOwner(user.id);
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(customerMessage(cause));
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [user, authLoading, router, publicId, retry]);

  const displayOrder = user && orderOwner === user.id ? order : null;
  const reload = () => {
    setIsLoading(true);
    setError(null);
    setOrder(null);
    setRetry((n) => n + 1);
  };

  return (
    <main className="min-h-[70svh] bg-elasi-ivory py-10 sm:py-16">
      <div className="elasi-container max-w-5xl">
        <Link href="/account/orders" className="inline-flex items-center gap-2 text-sm text-elasi-gold-text hover:underline"><ArrowRight size={16} /> همه سفارش‌ها</Link>
        <header className="mt-7 border-b border-elasi-green/10 pb-8">
          <p dir="ltr" className="text-label tracking-[0.2em] text-elasi-gold-text">ORDER DETAILS</p>
          <h1 className="mt-3 text-h1 text-elasi-green">جزئیات سفارش</h1>
          <p dir="ltr" className="mt-4 break-all text-sm text-elasi-muted">{publicId}</p>
        </header>

        {authLoading || !user || isLoading ? (
          <p role="status" className="py-16 text-center text-elasi-muted">در حال دریافت جزئیات سفارش...</p>
        ) : error ? (
          <section role="alert" className="mt-8 rounded-card border border-elasi-danger/30 bg-white p-8 text-center">
            <p className="text-elasi-danger">{error}</p>
            <button type="button" className="elasi-button elasi-button--secondary mt-5" onClick={reload}>تلاش دوباره</button>
          </section>
        ) : displayOrder ? (
          <div className="mt-8 space-y-6">
            <section className="rounded-card border border-elasi-green/10 bg-white p-6 sm:p-8" aria-label="وضعیت سفارش">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-xs text-elasi-muted">تاریخ ثبت: {orderDate(displayOrder.created_at)}</p>
                  <h2 className="mt-2 text-xl text-elasi-green">{orderStatusLabel(displayOrder.status)}</h2>
                </div>
                <p className="text-xl font-semibold text-elasi-green">{orderToman(displayOrder.total_rial)}</p>
              </div>
              {displayOrder.status === "pending_payment" ? (
                <p role="status" className="mt-5 rounded-xl bg-elasi-ivory p-4 text-sm leading-7 text-elasi-muted">
                  این سفارش هنوز پرداخت نشده است. درگاه آنلاین پس از فعال‌سازی در دسترس قرار می‌گیرد. ثبت سفارش به معنای تأیید پرداخت نیست.
                </p>
              ) : null}
              {orderFulfillmentStep(displayOrder.status) > 0 ? (
                <div className="mt-6 border-t border-elasi-green/10 pt-6" aria-label="مراحل انجام سفارش">
                  <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {["پرداخت تأییدشده", "آماده‌سازی", "ارسال مرسوله", "تحویل به مشتری"].map((label, index) => {
                      const complete = orderFulfillmentStep(displayOrder.status) >= index + 1;
                      return (
                        <li key={label} className={`rounded-xl border p-3 text-center text-xs leading-6 ${complete ? "border-elasi-gold/40 bg-elasi-ivory text-elasi-green" : "border-elasi-green/10 text-elasi-muted"}`}>
                          <span aria-hidden="true" className="mb-1 block text-base">{complete ? "✓" : "○"}</span>
                          {label}
                        </li>
                      );
                    })}
                  </ol>
                </div>
              ) : null}
              {displayOrder.shipment && (displayOrder.shipment.tracking_code || displayOrder.shipment.shipped_at || displayOrder.shipment.delivered_at) ? (
                <div className="mt-5 rounded-xl border border-elasi-green/10 bg-elasi-ivory p-4">
                  <p className="flex items-center gap-2 font-semibold text-elasi-green"><PackageCheck size={18} /> اطلاعات مرسوله</p>
                  <p className="mt-2 text-sm text-elasi-muted">حمل‌کننده: {displayOrder.shipment.carrier || "ثبت نشده"}</p>
                  {displayOrder.shipment.tracking_code ? (
                    <p className="mt-2 break-all text-sm text-elasi-green">کد رهگیری: <bdi dir="ltr">{displayOrder.shipment.tracking_code}</bdi></p>
                  ) : (
                    <p className="mt-2 text-sm text-elasi-muted">کد رهگیری هنوز ثبت نشده است.</p>
                  )}
                  {displayOrder.shipment.shipped_at ? (
                    <p className="mt-2 text-sm text-elasi-muted">تاریخ ارسال: {orderDate(displayOrder.shipment.shipped_at)}</p>
                  ) : null}
                  {displayOrder.shipment.delivered_at ? (
                    <p className="mt-2 text-sm text-elasi-muted">تاریخ تحویل: {orderDate(displayOrder.shipment.delivered_at)}</p>
                  ) : null}
                </div>
              ) : null}
            </section>

            <section className="rounded-card border border-elasi-green/10 bg-white p-6 sm:p-8" aria-label="اقلام سفارش">
              <h2 className="text-xl text-elasi-green">کالاهای سفارش</h2>
              <ul className="mt-5 divide-y divide-elasi-green/10">
                {displayOrder.items.map((item, index) => (
                  <li key={`${item.sku}-${index}`} className="flex flex-wrap items-center justify-between gap-5 py-5">
                    <div>
                      <Link href={`/products/${encodeURIComponent(item.product_slug)}`} className="font-medium text-elasi-green hover:underline">{item.product_name}</Link>
                      <p className="mt-2 text-xs text-elasi-muted">{item.material === "gold" ? "طلا" : "نقره"}{item.size ? ` · سایز ${item.size}` : ""} · تعداد {new Intl.NumberFormat("fa-IR").format(item.quantity)}</p>
                    </div>
                    <span className="font-medium text-elasi-green">{orderToman(item.line_total_rial)}</span>
                  </li>
                ))}
              </ul>
              <dl className="mt-4 space-y-3 border-t border-elasi-green/10 pt-5 text-sm">
                <div className="flex justify-between gap-4"><dt>جمع کالاها</dt><dd>{orderToman(displayOrder.subtotal_rial)}</dd></div>
                <div className="flex justify-between gap-4"><dt>هزینه ارسال</dt><dd>{orderToman(displayOrder.shipping_fee_rial)}</dd></div>
                <div className="flex justify-between gap-4 font-semibold text-elasi-green"><dt>مبلغ نهایی</dt><dd>{orderToman(displayOrder.total_rial)}</dd></div>
              </dl>
            </section>

            <section className="rounded-card border border-elasi-green/10 bg-white p-6 sm:p-8" aria-label="نشانی ارسال">
              <h2 className="text-xl text-elasi-green">نشانی تحویل</h2>
              <p className="mt-4 text-sm leading-8 text-elasi-text">{displayOrder.recipient_name} — {displayOrder.province}، {displayOrder.city}، {displayOrder.address_line}</p>
              <p className="mt-1 text-sm text-elasi-muted">کد پستی: <bdi dir="ltr">{displayOrder.postal_code}</bdi></p>
              {displayOrder.customer_note ? <p className="mt-3 text-sm text-elasi-muted">توضیح سفارش: {displayOrder.customer_note}</p> : null}
            </section>
          </div>
        ) : null}
      </div>
    </main>
  );
}
