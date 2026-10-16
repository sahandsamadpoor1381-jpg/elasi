import type { Metadata } from "next";

import Link from "next/link";

import { getCategories } from "@/lib/catalog-api";
import { formatNumber } from "@/lib/format";


export const metadata: Metadata = {
  title: "درباره ELASI",
  description:
    "ELASI فروشگاه آنلاین جواهرات طلا و نقره است؛ با تمرکز بر طراحی مدرن، جزئیات دقیق و انتخاب‌های ماندگار.",
  alternates: {
    canonical: "/about",
  },
};


const buyingSteps = [
  {
    title: "انتخاب محصول",
    description:
      "محصولات را بر اساس دسته‌بندی، متریال و موجودی مرور کنید. مشخصات هر محصول شامل متریال، عیار، وزن و اندازه در صفحه‌ی همان محصول آمده است.",
  },
  {
    title: "ورود با شماره موبایل",
    description:
      "برای تکمیل خرید و پیگیری سفارش، با شماره موبایل و رمز یک‌بارمصرف وارد حساب کاربری خود می‌شوید.",
  },
  {
    title: "ثبت اطلاعات ارسال",
    description:
      "نشانی و مشخصات گیرنده در مرحله‌ی نهایی ثبت می‌شود و سفارش شما در حساب کاربری قابل پیگیری است.",
  },
] as const;


export default async function AboutPage() {
  let categories: Awaited<ReturnType<typeof getCategories>> = [];

  try {
    categories = await getCategories();
  } catch {
    categories = [];
  }

  return (
    <main className="bg-elasi-ivory pb-20">
      <div className="elasi-container pt-10 sm:pt-14">
        <header className="max-w-3xl">
          <p className="text-label font-medium tracking-[0.2em] text-elasi-gold">
            ABOUT ELASI
          </p>

          <h1 className="mt-4 text-h2 text-elasi-green">
            جواهراتی برای انتخاب‌های ماندگار
          </h1>

          <p className="mt-6 text-body-lg leading-9 text-elasi-muted">
            ELASI یک فروشگاه آنلاین جواهرات طلا و نقره است.
            تمرکز ما بر طراحی مدرن و ظریف، مشخصات شفاف
            محصول و تجربه‌ای آرام برای انتخاب است؛ بدون
            شلوغی، بدون اغراق.
          </p>
        </header>

        <section className="mt-14 grid gap-6 lg:grid-cols-3">
          <div className="rounded-[28px] border border-elasi-green/10 bg-white/60 p-7">
            <h2 className="text-h3 text-elasi-green">
              مشخصات شفاف
            </h2>

            <p className="mt-4 text-sm leading-7 text-elasi-muted">
              برای هر محصول، متریال (طلا یا نقره)، عیار،
              وزن و اندازه‌های موجود ثبت شده است. قیمت‌ها
              به تومان نمایش داده می‌شوند و بر پایه‌ی
              اطلاعات ثبت‌شده در سامانه‌ی فروشگاه محاسبه
              می‌شوند.
            </p>
          </div>

          <div className="rounded-[28px] border border-elasi-green/10 bg-white/60 p-7">
            <h2 className="text-h3 text-elasi-green">
              موجودی واقعی
            </h2>

            <p className="mt-4 text-sm leading-7 text-elasi-muted">
              موجودی هر محصول به‌صورت زنده از انبار فروشگاه
              خوانده می‌شود؛ بنابراین وضعیت «موجود» یا
              «ناموجود» همان چیزی است که در انبار ثبت شده
              و امکان خرید بیش از موجودی وجود ندارد.
            </p>
          </div>

          <div className="rounded-[28px] border border-elasi-green/10 bg-white/60 p-7">
            <h2 className="text-h3 text-elasi-green">
              اندازه‌ی اختصاصی
            </h2>

            <p className="mt-4 text-sm leading-7 text-elasi-muted">
              برای برخی محصولات امکان سفارش در اندازه‌ی
              اختصاصی وجود دارد. این درخواست‌ها پیش از
              ساخت بررسی و تأیید می‌شوند تا نتیجه دقیقاً
              همان چیزی باشد که انتظار دارید.
            </p>
          </div>
        </section>

        {categories.length > 0 ? (
          <section className="mt-14 rounded-[28px] border border-elasi-green/10 bg-white/60 p-7 sm:p-10">
            <h2 className="text-h3 text-elasi-green">
              دسته‌بندی‌های فعلی فروشگاه
            </h2>

            <p className="mt-4 max-w-2xl text-sm leading-7 text-elasi-muted">
              مجموعه‌ی فعلی ELASI در این دسته‌بندی‌ها ارائه
              می‌شود. تعداد محصولات هر دسته بر اساس
              محصولات فعال فروشگاه محاسبه شده است.
            </p>

            <ul className="mt-7 flex flex-wrap gap-2">
              {categories.map((category) => (
                <li key={category.slug}>
                  <Link
                    href={`/shop?category=${encodeURIComponent(
                      category.slug,
                    )}`}
                    className="flex items-center gap-2 rounded-full border border-elasi-green/15 bg-elasi-ivory px-5 py-2.5 text-sm font-medium text-elasi-green transition-colors hover:border-elasi-gold hover:text-elasi-gold"
                  >
                    {category.name}

                    {category.product_count > 0 ? (
                      <span className="text-xs text-elasi-muted">
                        {formatNumber(category.product_count)}
                      </span>
                    ) : null}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="mt-14">
          <h2 className="text-h3 text-elasi-green">
            خرید از ELASI چطور پیش می‌رود؟
          </h2>

          <ol className="mt-8 grid gap-6 lg:grid-cols-3">
            {buyingSteps.map((step, index) => (
              <li
                key={step.title}
                className="rounded-[28px] border border-elasi-green/10 bg-white/60 p-7"
              >
                <span className="flex size-9 items-center justify-center rounded-full bg-elasi-green text-sm font-semibold text-elasi-ivory">
                  {formatNumber(index + 1)}
                </span>

                <p className="mt-5 text-base font-semibold text-elasi-green">
                  {step.title}
                </p>

                <p className="mt-3 text-sm leading-7 text-elasi-muted">
                  {step.description}
                </p>
              </li>
            ))}
          </ol>
        </section>

        <section className="mt-14 flex flex-col items-start gap-6 rounded-[28px] border border-elasi-green/10 bg-elasi-green/[0.04] p-7 sm:flex-row sm:items-center sm:justify-between sm:p-10">
          <div>
            <h2 className="text-h3 text-elasi-green">
              مجموعه را ببینید
            </h2>

            <p className="mt-3 max-w-xl text-sm leading-7 text-elasi-muted">
              فهرست کامل محصولات، با امکان فیلتر بر اساس
              دسته‌بندی، متریال و موجودی.
            </p>
          </div>

          <Link
            href="/shop"
            className="elasi-button elasi-button--primary shrink-0"
          >
            مشاهده محصولات
          </Link>
        </section>
      </div>
    </main>
  );
}
