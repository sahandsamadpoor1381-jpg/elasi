import Link from "next/link";

import { ProductCard } from "@/components/storefront/product-card";

import type { ProductSummary } from "@/types/catalog";


export function ProductGrid({
  products,
}: {
  products: ProductSummary[];
}) {
  return (
    <ul className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,240px),1fr))] justify-items-center gap-x-6 gap-y-10 sm:gap-x-8 sm:gap-y-12">
      {products.map((product) => (
        <li
          key={product.slug}
          className="w-full max-w-[360px]"
        >
          <ProductCard product={product} />
        </li>
      ))}
    </ul>
  );
}


export function EmptyCatalogState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: { href: string; label: string };
}) {
  return (
    <div className="rounded-[28px] border border-elasi-green/10 bg-white/60 px-6 py-16 text-center">
      <p className="text-lg font-semibold text-elasi-green">
        {title}
      </p>

      <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-elasi-muted">
        {description}
      </p>

      {action ? (
        <Link
          href={action.href}
          className="elasi-button elasi-button--secondary mt-8"
        >
          {action.label}
        </Link>
      ) : null}
    </div>
  );
}


export function CatalogErrorState({
  retryHref,
}: {
  retryHref: string;
}) {
  return (
    <div
      role="alert"
      className="rounded-[28px] border border-elasi-danger/20 bg-elasi-danger/[0.04] px-6 py-14 text-center"
    >
      <p className="text-lg font-semibold text-elasi-green">
        نمایش محصولات ممکن نشد
      </p>

      <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-elasi-muted">
        ارتباط با سرور فروشگاه برقرار نشد. لطفاً چند لحظه
        دیگر دوباره تلاش کنید.
      </p>

      <Link
        href={retryHref}
        className="elasi-button elasi-button--primary mt-8"
      >
        تلاش دوباره
      </Link>
    </div>
  );
}
