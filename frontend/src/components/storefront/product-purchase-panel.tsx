"use client";

import Link from "next/link";
import { useState } from "react";

import { useCart } from "@/components/cart/cart-provider";
import { WishlistButton } from "@/components/wishlist/wishlist-button";
import { formatToman } from "@/lib/format";
import {
  activeProductVariants,
  canBuyProductVariant,
  defaultProductVariant,
  validCompareAtPriceRial,
} from "@/lib/product-variants";
import type {
  Product,
  ProductVariant,
} from "@/types/catalog";


type ProductPurchasePanelProps = {
  product: Product;
};


const categoryLabels: Record<string, string> = {
  rings: "انگشتر",
  necklaces: "گردنبند",
  bracelets: "دستبند",
  earrings: "گوشواره",
  pendants: "آویز",
  anklets: "پابند",
  sets: "ست و نیم‌ست",
};


function getCategoryLabel(
  slug: string,
  fallback: string,
): string {
  return categoryLabels[slug] ?? fallback;
}


function formatPersianNumber(
  value: number | string,
): string {
  const numericValue =
    typeof value === "number"
      ? value
      : Number(value);

  if (Number.isNaN(numericValue)) {
    return String(value);
  }

  return new Intl.NumberFormat(
    "fa-IR",
  ).format(numericValue);
}


function getMaterialLabel(
  material: ProductVariant["material"],
): string {
  const labels: Record<
    ProductVariant["material"],
    string
  > = {
    gold: "طلا",
    silver: "نقره",
  };

  return labels[material];
}


function getVariantTitle(
  variant: ProductVariant,
): string {
  const parts: string[] = [
    getMaterialLabel(variant.material),
  ];

  if (variant.karat) {
    parts.push(
      `${formatPersianNumber(
        variant.karat,
      )} عیار`,
    );
  }

  if (variant.size) {
    parts.push(
      `سایز ${formatPersianNumber(
        variant.size,
      )}`,
    );
  }

  return parts.join(" · ");
}


export function ProductPurchasePanel({
  product,
}: ProductPurchasePanelProps) {
  const {
    addItem,
    isLoading: isCartLoading,
    error: cartError,
  } = useCart();

  const variants = activeProductVariants(product.variants);
  const initialVariant = defaultProductVariant(variants);

  const [
    selectedSku,
    setSelectedSku,
  ] = useState(
    initialVariant?.sku ?? "",
  );

  const [
    isAddingToCart,
    setIsAddingToCart,
  ] = useState(false);

  const [
    addToCartSuccess,
    setAddToCartSuccess,
  ] = useState(false);

  const selectedVariant =
    variants.find((variant) => variant.sku === selectedSku) ?? null;

  const hasMultipleVariants = variants.length > 1;
  const isAvailable = canBuyProductVariant(selectedVariant);
  const compareAtPriceRial = validCompareAtPriceRial(selectedVariant);


  async function handleAddToCart() {
    if (
      !selectedVariant ||
      !isAvailable ||
      isAddingToCart ||
      isCartLoading
    ) {
      return;
    }

    setIsAddingToCart(true);
    setAddToCartSuccess(false);

    try {
      await addItem(
        selectedVariant.sku,
        1,
      );

      setAddToCartSuccess(true);
    } catch {
      setAddToCartSuccess(false);
    } finally {
      setIsAddingToCart(false);
    }
  }


  function handleVariantChange(
    sku: string,
  ) {
    setSelectedSku(sku);
    setAddToCartSuccess(false);
  }


  return (
    <div>
      {/* Product identity */}
      <div>
        <p className="text-caption font-medium tracking-[0.14em] text-elasi-gold-text">
          {getCategoryLabel(
            product.category.slug,
            product.category.name,
          )}
        </p>

        <h1 className="mt-3 text-elasi-green">
          {product.name}
        </h1>

        {product.short_description ? (
          <p className="mt-5 max-w-xl text-body text-elasi-muted">
            {product.short_description}
          </p>
        ) : null}
      </div>

      {/* Price + availability */}
      <div className="mt-8 border-y border-elasi-green/10 py-6">
        {selectedVariant ? (
          <div className="flex flex-wrap items-end justify-between gap-5">
            <div>
              <p className="text-caption text-elasi-muted">
                قیمت
              </p>

              <p className="mt-1 text-xl font-semibold text-elasi-green">
                {formatToman(selectedVariant.price_rial)} تومان
              </p>

              {compareAtPriceRial !== null ? (
                <p className="mt-1 text-sm text-elasi-muted line-through decoration-elasi-muted/60">
                  <span className="sr-only">قیمت پیشین: </span>
                  {formatToman(compareAtPriceRial)} تومان
                </p>
              ) : null}
            </div>

            <div
              className={`rounded-full px-4 py-2 text-sm font-medium ${
                isAvailable
                  ? "bg-elasi-green/10 text-elasi-green"
                  : "bg-black/5 text-elasi-muted"
              }`}
            >
              {isAvailable
                ? "موجود"
                : "ناموجود"}
            </div>
          </div>
        ) : (
          <p className="text-sm text-elasi-muted">
            برای این محصول هنوز مدل قابل
            فروشی ثبت نشده است.
          </p>
        )}
      </div>

      {/* Native radio inputs support keyboard arrows and screen readers. */}
      {hasMultipleVariants ? (
        <fieldset className="mt-9">
          <legend className="text-xl font-semibold text-elasi-green">
            مدل محصول
          </legend>
          <p className="mt-2 text-caption text-elasi-muted">
            {formatPersianNumber(variants.length)} گزینه برای انتخاب
          </p>

          <div className="mt-5 grid gap-3">
            {variants.map((variant) => {
              const isSelected = variant.sku === selectedSku;
              const variantAvailable = canBuyProductVariant(variant);

              return (
                <label
                  key={variant.sku}
                  className={`flex min-h-16 cursor-pointer items-center gap-4 rounded-lg border px-5 py-4 text-right transition focus-within:ring-2 focus-within:ring-elasi-gold-text focus-within:ring-offset-2 ${
                    isSelected
                      ? "border-elasi-gold-text bg-white"
                      : "border-elasi-border-strong bg-white/35 hover:border-elasi-gold-text hover:bg-white/60"
                  } ${isAddingToCart ? "cursor-not-allowed opacity-70" : ""}`}
                >
                  <input
                    type="radio"
                    name={`product-variant-${product.slug}`}
                    value={variant.sku}
                    checked={isSelected}
                    onChange={() => handleVariantChange(variant.sku)}
                    disabled={isAddingToCart}
                    className="peer sr-only"
                  />
                  <span
                    aria-hidden="true"
                    className="size-4 shrink-0 rounded-full border border-elasi-border-strong bg-white peer-checked:border-elasi-gold-text peer-checked:bg-elasi-gold-text"
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-medium text-elasi-text">
                      {getVariantTitle(variant)}
                    </span>
                    <span className="mt-1 block text-xs text-elasi-muted">
                      {variantAvailable ? "آماده سفارش" : "در حال حاضر ناموجود"}
                      {" · "}
                      کد {variant.sku}
                    </span>
                  </span>
                  <span className="shrink-0 text-sm font-medium text-elasi-green">
                    {formatToman(variant.price_rial)} تومان
                  </span>
                </label>
              );
            })}
          </div>
        </fieldset>
      ) : null}

      {/* Custom size */}
      {product.allow_custom_size ? (
        <div className="mt-9 rounded-lg border border-elasi-gold/25 bg-white/40 p-5">
          <div className="flex items-start gap-3">
            <span
              aria-hidden="true"
              className="mt-2 size-1.5 shrink-0 rounded-full bg-elasi-gold"
            />

            <div>
              <p className="font-medium text-elasi-green">
                امکان سفارش سایز سفارشی
              </p>

              <p className="mt-2 text-sm leading-7 text-elasi-muted">
                درخواست سایز اختصاصی نیازمند بررسی و تأیید فروشگاه
                است. ثبت آنلاین این درخواست هنوز فعال نشده است.
              </p>
            </div>
          </div>
        </div>
      ) : null}

      {/* Add to cart */}
      <div className="mt-9">
        <button
          type="button"
          onClick={handleAddToCart}
          disabled={
            !selectedVariant ||
            !isAvailable ||
            isAddingToCart ||
            isCartLoading
          }
          className="elasi-button elasi-button--primary w-full disabled:cursor-not-allowed disabled:opacity-45"
        >
          {isCartLoading
            ? "در حال آماده‌سازی سبد خرید..."
            : isAddingToCart
              ? "در حال افزودن..."
            : isAvailable
              ? "افزودن به سبد خرید"
              : selectedVariant ? "ناموجود" : "مدل قابل خرید ندارد"}
        </button>

        {addToCartSuccess ? (
          <p
            role="status"
            className="mt-3 text-center text-sm font-medium text-elasi-green"
          >
            محصول به سبد خرید اضافه شد.
            {" "}
            <Link href="/cart" className="underline underline-offset-4 hover:text-elasi-gold-text">
              مشاهده سبد خرید
            </Link>
          </p>
        ) : null}

        <WishlistButton
          productSlug={product.slug}
          productName={product.name}
          variant="full"
          className="mt-4"
        />

        {cartError ? (
          <p
            role="alert"
            className="mt-3 text-center text-sm text-elasi-danger"
          >
            {cartError}
          </p>
        ) : null}
      </div>

      {/* Product specifications */}
      {selectedVariant ? (
        <div className="mt-10 border-t border-elasi-green/10 pt-7">
          <p className="text-caption font-medium tracking-[0.12em] text-elasi-gold-text">
            مشخصات محصول
          </p>

          <dl className="mt-5 grid grid-cols-2 gap-x-8 gap-y-6">
            <div>
              <dt className="text-caption text-elasi-muted">
                متریال
              </dt>

              <dd className="mt-1 text-sm font-medium text-elasi-text">
                {getMaterialLabel(
                  selectedVariant.material,
                )}
              </dd>
            </div>

            {selectedVariant.karat ? (
              <div>
                <dt className="text-caption text-elasi-muted">
                  عیار
                </dt>

                <dd className="mt-1 text-sm font-medium text-elasi-text">
                  {formatPersianNumber(
                    selectedVariant.karat,
                  )}
                </dd>
              </div>
            ) : null}

            {selectedVariant.size ? (
              <div>
                <dt className="text-caption text-elasi-muted">
                  سایز
                </dt>

                <dd className="mt-1 text-sm font-medium text-elasi-text">
                  {formatPersianNumber(
                    selectedVariant.size,
                  )}
                </dd>
              </div>
            ) : null}

            {selectedVariant.weight_grams ? (
              <div>
                <dt className="text-caption text-elasi-muted">
                  وزن
                </dt>

                <dd className="mt-1 text-sm font-medium text-elasi-text">
                  {formatPersianNumber(
                    selectedVariant.weight_grams,
                  )}{" "}
                  گرم
                </dd>
              </div>
            ) : null}

            {selectedVariant.purity ? (
              <div>
                <dt className="text-caption text-elasi-muted">
                  خلوص
                </dt>

                <dd className="mt-1 text-sm font-medium text-elasi-text">
                  {
                    selectedVariant.purity
                  }
                </dd>
              </div>
            ) : null}
          </dl>
        </div>
      ) : null}
    </div>
  );
}