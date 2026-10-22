"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PackageOpen, ArrowLeft, RefreshCw } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { customerMessage } from "@/lib/api-client";
import { getCustomerOrders, type CustomerOrderPage } from "@/lib/orders-api";
import { orderDate, orderStatusLabel, orderToman } from "@/lib/order-presentation";

export function OrdersClient() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [page, setPage] = useState(1);
  const [retry, setRetry] = useState(0);
  const [data, setData] = useState<CustomerOrderPage | null>(null);
  const [dataOwner, setDataOwner] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/login?next=/account/orders");
      return;
    }

    const controller = new AbortController();
    getCustomerOrders(page, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setData(result);
          setDataOwner(user.id);
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(customerMessage(cause));
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [user, authLoading, router, page, retry]);

  const displayData = user && dataOwner === user.id ? data : null;
  const reload = () => {
    setIsLoading(true);
    setError(null);
    setData(null);
    setRetry((n) => n + 1);
  };
  const changePage = (target: number) => {
    setIsLoading(true);
    setError(null);
    setData(null);
    setPage(target);
  };

  return (
    <main className="min-h-[70svh] bg-elasi-ivory py-10 sm:py-16">
      <div className="elasi-container max-w-5xl">
        <Link href="/account" className="text-sm text-elasi-gold-text hover:underline">
          بازگشت به حساب کاربری
        </Link>
        <header className="mt-7 border-b border-elasi-green/10 pb-8">
          <p className="text-label tracking-[0.2em] text-elasi-gold-text" dir="ltr">MY ORDERS</p>
          <h1 className="mt-3 text-h1 text-elasi-green">سفارش‌های من</h1>
          <p className="mt-3 text-sm leading-7 text-elasi-muted">
            وضعیت واقعی سفارش‌ها، مبلغ ثبت‌شده و جزئیات ارسال را اینجا دنبال کنید.
          </p>
        </header>

        {authLoading || !user || isLoading ? (
          <p role="status" className="py-16 text-center text-elasi-muted">در حال دریافت سفارش‌ها...</p>
        ) : error ? (
          <section role="alert" className="mt-8 rounded-card border border-elasi-danger/30 bg-white p-8 text-center">
            <p className="text-elasi-danger">{error}</p>
            <button className="elasi-button elasi-button--secondary mt-5" onClick={reload} type="button">
              تلاش دوباره
            </button>
          </section>
        ) : displayData?.results.length === 0 ? (
          <section className="mt-8 rounded-card border border-elasi-green/10 bg-white p-12 text-center">
            <PackageOpen className="mx-auto text-elasi-gold-text" size={34} aria-hidden="true" />
            <h2 className="mt-5 text-xl text-elasi-green">هنوز سفارشی ثبت نکرده‌اید</h2>
            <p className="mt-3 text-sm text-elasi-muted">محصولات منتخب خود را از مجموعه ELASI پیدا کنید.</p>
            <Link href="/shop" className="elasi-button elasi-button--primary mt-7">مشاهده محصولات</Link>
          </section>
        ) : displayData ? (
          <>
            <p className="mt-6 text-sm text-elasi-muted">
              {new Intl.NumberFormat("fa-IR").format(displayData.count)} سفارش
            </p>
            <div className="mt-5 space-y-4">
              {displayData.results.map((order) => (
                <article key={order.public_id} className="rounded-card border border-elasi-green/10 bg-white px-5 py-6 sm:px-8">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <p className="text-xs text-elasi-muted">{orderDate(order.created_at)}</p>
                      <p className="mt-2 text-xs font-medium text-elasi-green" dir="ltr">{order.public_id}</p>
                    </div>
                    <span className="rounded-full border border-elasi-gold/40 bg-elasi-ivory px-4 py-2 text-xs text-elasi-green">
                      {orderStatusLabel(order.status)}
                    </span>
                  </div>
                  <div className="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-elasi-green/10 pt-5">
                    <div>
                      <p className="text-xs text-elasi-muted">مبلغ سفارش</p>
                      <p className="mt-1 font-semibold text-elasi-green">{orderToman(order.total_rial)}</p>
                    </div>
                    <Link href={`/account/orders/${order.public_id}`} className="inline-flex min-h-11 items-center gap-2 rounded-full border border-elasi-border-strong px-5 text-sm text-elasi-green hover:bg-elasi-ivory">
                      مشاهده جزئیات <ArrowLeft size={16} aria-hidden="true" />
                    </Link>
                  </div>
                </article>
              ))}
            </div>
            <div className="mt-8 flex items-center justify-center gap-3">
              <button type="button" className="elasi-button elasi-button--secondary" disabled={!displayData.previous} onClick={() => changePage(Math.max(1, page - 1))}>صفحه قبل</button>
              <span className="text-sm text-elasi-muted">{new Intl.NumberFormat("fa-IR").format(page)}</span>
              <button type="button" className="elasi-button elasi-button--secondary" disabled={!displayData.next} onClick={() => changePage(page + 1)}>صفحه بعد</button>
            </div>
          </>
        ) : (
          <button type="button" className="mt-8 flex items-center gap-2 text-elasi-green" onClick={reload}>
            <RefreshCw size={16} /> دریافت سفارش‌ها
          </button>
        )}
      </div>
    </main>
  );
}
