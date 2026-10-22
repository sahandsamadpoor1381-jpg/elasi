import Image from "next/image";
import Link from "next/link";

import { WishlistButton } from "@/components/wishlist/wishlist-button";
import { mediaPath } from "@/lib/media";

import type { ProductSummary } from "@/types/catalog";


type ProductCardProps = {
  product: ProductSummary;
};


function formatToman(priceRial: number): string {
  const priceToman = Math.floor(priceRial / 10);

  return new Intl.NumberFormat("fa-IR").format(priceToman);
}


// Next Image's `sizes` descriptor needs concrete CSS lengths, so these values
// deliberately mirror the responsive breakpoints, page padding and card width.
const PRODUCT_IMAGE_SIZES =
  "(max-width: 640px) calc(100vw - 24px), (max-width: 1024px) 45vw, 360px"; // ds-allow-hardcode: required concrete image source-size values.


function getCategoryLabel(slug: string, fallback: string): string {
  const labels: Record<string, string> = {
    rings: "انگشتر",
    necklaces: "گردنبند",
    bracelets: "دستبند",
    earrings: "گوشواره",
    pendants: "آویز",
    anklets: "پابند",
    sets: "ست و نیم‌ست",
  };

  return labels[slug] ?? fallback;
}


export function ProductCard({ product }: ProductCardProps) {
  const primaryImage =
    product.primary_image ??
    product.images.find((image) => image.is_primary) ??
    product.images[0];

  const isAvailable = product.is_available;

  const priceFrom =
    product.price_from_rial ??
    product.variants[0]?.price_rial ??
    null;

  const priceTo = product.price_to_rial ?? priceFrom;

  const hasPriceRange =
    priceFrom !== null &&
    priceTo !== null &&
    priceTo > priceFrom;

  return (
    <article className="elasi-product-card group relative">
      <div className="absolute start-4 top-4 z-10">
        <WishlistButton
          productSlug={product.slug}
          productName={product.name}
        />
      </div>

      <Link
        href={`/products/${product.slug}`}
        className="block"
      >
        <div className="relative aspect-[4/5] overflow-hidden rounded-card bg-white">
          {primaryImage ? (
            <Image
              src={mediaPath(primaryImage.image) ?? primaryImage.image}
              alt={primaryImage.alt_text || product.name}
              fill
              sizes={PRODUCT_IMAGE_SIZES}
              className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.025]"
            />
          ) : (
            <div className="flex h-full items-center justify-center px-6 text-center text-sm text-elasi-muted">
              تصویر محصول موجود نیست
            </div>
          )}

          {!isAvailable ? (
            <div className="absolute inset-x-4 bottom-4 rounded-full bg-white/90 px-4 py-2 text-center text-xs font-medium text-elasi-text backdrop-blur">
              ناموجود
            </div>
          ) : null}
        </div>

        <div className="px-1 pt-5 text-right">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-caption text-elasi-gold-text">
                {getCategoryLabel(
                  product.category.slug,
                  product.category.name,
                )}
              </p>

              <h3 className="mt-1 text-lg font-semibold text-elasi-text transition-colors group-hover:text-elasi-gold-text">
                {product.name}
              </h3>
            </div>

            <span
              className={`mt-1 size-2 shrink-0 rounded-full ${
                isAvailable
                  ? "bg-elasi-green"
                  : "bg-elasi-muted/40"
              }`}
              aria-label={isAvailable ? "موجود" : "ناموجود"}
            />
          </div>

          {product.short_description ? (
            <p className="mt-2 line-clamp-2 text-sm leading-7 text-elasi-muted">
              {product.short_description}
            </p>
          ) : null}

          <div className="mt-4 flex items-center justify-between gap-4 border-t border-elasi-green/10 pt-4">
            {priceFrom !== null ? (
              <p className="text-price text-elasi-green">
                {hasPriceRange
                  ? `از ${formatToman(priceFrom)} تومان`
                  : `${formatToman(priceFrom)} تومان`}
              </p>
            ) : (
              <p className="text-sm text-elasi-muted">
                قیمت ناموجود
              </p>
            )}

            <span className="text-sm font-medium text-elasi-green transition-colors group-hover:text-elasi-gold-text">
              مشاهده محصول
            </span>
          </div>
        </div>
      </Link>
    </article>
  );
}