
import Link from "next/link";

import { ProductCard } from "@/components/storefront/product-card";

import type { ProductSummary } from "@/types/catalog";


export function ProductGrid({
  products,
}: {
  products: ProductSummary[];
}) {
  return (
    <ul
      className="elasi-product-grid"
      data-density={
        products.length === 1
          ? "single"
          : products.length === 2
            ? "pair"
            : "regular"
      }
    >
      {products.map((product) => (
        <li
          key={product.slug}
          className="elasi-product-card"
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
  action?: {
    href: string;
    label: string;
  };
}) {
  return (
    <div className="rounded-card border border-elasi-green/10 bg-white/60 px-6 py-16 text-center">
      <h2 className="text-lg font-semibold text-elasi-green">
        {title}
      </h2>

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
      className="rounded-card border border-elasi-danger/20 bg-elasi-danger/[0.04] px-6 py-14 text-center"
    >
      <h2 className="text-lg font-semibold text-elasi-green">
        نمایش محصولات ممکن نشد
      </h2>

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
