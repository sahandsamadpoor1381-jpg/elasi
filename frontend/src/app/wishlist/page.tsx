"use client";

import Link from "next/link";

import { useAuth } from "@/components/auth/auth-provider";
import { WishlistButton } from "@/components/wishlist/wishlist-button";
import { useWishlist } from "@/components/wishlist/wishlist-provider";
import { formatNumber, formatTomanWithUnit } from "@/lib/format";
import { mediaPath } from "@/lib/media";


function WishlistSkeleton() {
  return (
    <ul className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 3 }).map((_, index) => (
        <li
          key={index}
          className="overflow-hidden rounded-[28px] border border-elasi-green/10 bg-white/50"
        >
          <div className="aspect-[4/5] animate-pulse bg-elasi-green/[0.06]" />
          <div className="p-5">
            <div className="h-5 w-3/5 animate-pulse rounded-full bg-elasi-green/10" />
            <div className="mt-4 h-4 w-2/5 animate-pulse rounded-full bg-elasi-green/10" />
          </div>
        </li>
      ))}
    </ul>
  );
}


export default function WishlistPage() {
  const { isLoading: isAuthLoading, isAuthenticated } = useAuth();
  const { items, count, isLoading, error } = useWishlist();

  return (
    <main className="bg-elasi-ivory pb-20">
      <div className="elasi-container pt-10 sm:pt-14">
        <header className="max-w-3xl">
          <p className="text-label font-medium tracking-[0.2em] text-elasi-gold">
            WISHLIST
          </p>

          <h1 className="mt-4 text-h2 text-elasi-green">
            علاقه‌مندی‌های من
          </h1>

          <p className="mt-4 text-body text-elasi-muted">
            محصولاتی که ذخیره کرده‌اید، در حساب کاربری
            خودتان نگه‌داری می‌شوند.
          </p>
        </header>

        <div className="mt-12">
          {isAuthLoading ? (
            <WishlistSkeleton />
          ) : !isAuthenticated ? (
            <div className="rounded-[28px] border border-elasi-green/10 bg-white/60 px-6 py-16 text-center">
              <p className="text-lg font-semibold text-elasi-green">
                برای دیدن علاقه‌مندی‌ها وارد شوید
              </p>

              <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-elasi-muted">
                فهرست علاقه‌مندی‌ها به حساب کاربری شما
                گره خورده است؛ با شماره موبایل وارد شوید تا
                فهرست خودتان را ببینید.
              </p>

              <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Link
                  href="/login?next=/wishlist"
                  className="elasi-button elasi-button--primary"
                >
                  ورود به حساب کاربری
                </Link>

                <Link
                  href="/shop"
                  className="elasi-button elasi-button--secondary"
                >
                  مشاهده محصولات
                </Link>
              </div>
            </div>
          ) : isLoading ? (
            <WishlistSkeleton />
          ) : error ? (
            <div
              role="alert"
              className="rounded-[28px] border border-elasi-danger/20 bg-elasi-danger/[0.04] px-6 py-14 text-center"
            >
              <p className="text-lg font-semibold text-elasi-green">
                نمایش علاقه‌مندی‌ها ممکن نشد
              </p>

              <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-elasi-muted">
                {error}
              </p>
            </div>
          ) : items.length === 0 ? (
            <div className="rounded-[28px] border border-elasi-green/10 bg-white/60 px-6 py-16 text-center">
              <p className="text-lg font-semibold text-elasi-green">
                هنوز محصولی ذخیره نکرده‌اید
              </p>

              <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-elasi-muted">
                با زدن آیکن قلب روی هر محصول، آن را در همین
                صفحه ذخیره می‌کنید تا بعداً راحت‌تر پیدایش
                کنید.
              </p>

              <Link
                href="/shop"
                className="elasi-button elasi-button--primary mt-8"
              >
                مشاهده محصولات
              </Link>
            </div>
          ) : (
            <>
              <p className="text-sm text-elasi-muted">
                {formatNumber(count)} محصول ذخیره‌شده
              </p>

              <ul className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((item) => {
                  const product = item.product;

                  const image =
                    mediaPath(product.primary_image?.image) ??
                    mediaPath(product.images[0]?.image);

                  const price =
                    product.price_from_rial;

                  return (
                    <li
                      key={product.slug}
                      className="overflow-hidden rounded-[28px] border border-elasi-green/10 bg-white/60"
                    >
                      <Link
                        href={`/products/${product.slug}`}
                        className="block"
                      >
                        <div className="relative aspect-[4/5] bg-elasi-green/[0.05]">
                          {image ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={image}
                              alt={product.name}
                              className="size-full object-cover"
                            />
                          ) : (
                            <div className="flex size-full items-center justify-center text-sm text-elasi-muted">
                              تصویر محصول موجود نیست
                            </div>
                          )}

                          {!item.is_purchasable ? (
                            <span className="absolute inset-x-4 bottom-4 rounded-full bg-white/90 px-4 py-2 text-center text-xs font-medium text-elasi-text backdrop-blur">
                              در حال حاضر قابل خرید نیست
                            </span>
                          ) : null}
                        </div>
                      </Link>

                      <div className="p-5 text-right">
                        <Link
                          href={`/products/${product.slug}`}
                          className="text-base font-semibold text-elasi-text transition-colors hover:text-elasi-gold"
                        >
                          {product.name}
                        </Link>

                        <p className="mt-3 text-price text-elasi-green">
                          {price !== null
                            ? formatTomanWithUnit(price)
                            : "قیمت ناموجود"}
                        </p>

                        <WishlistButton
                          productSlug={product.slug}
                          productName={product.name}
                          variant="full"
                          className="mt-4"
                        />
                      </div>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
