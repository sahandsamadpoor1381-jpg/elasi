"use client";

import { useState } from "react";

import { useCart } from "@/components/cart/cart-provider";
import { WishlistButton } from "@/components/wishlist/wishlist-button";
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


function formatToman(
  priceRial: number,
): string {
  const toman = Math.floor(
    priceRial / 10,
  );

  return new Intl.NumberFormat(
    "fa-IR",
  ).format(toman);
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
    error: cartError,
  } = useCart();

  const initialVariant =
    product.variants.find(
      (variant) => variant.available > 0,
    ) ?? product.variants[0];

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
    product.variants.find(
      (variant) =>
        variant.sku === selectedSku,
    ) ?? initialVariant;

  const hasMultipleVariants =
    product.variants.length > 1;

  const isAvailable =
    Boolean(
      selectedVariant &&
        selectedVariant.available > 0,
    );


  async function handleAddToCart() {
    if (
      !selectedVariant ||
      !isAvailable ||
      isAddingToCart
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
                {formatToman(
                  selectedVariant.price_rial,
                )}{" "}
                تومان
              </p>
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

      {/* Variant selector */}
      {hasMultipleVariants ? (
        <div className="mt-9">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-caption text-elasi-muted">
                انتخاب
              </p>

              <h2 className="mt-1 text-xl font-semibold text-elasi-green">
                مدل محصول
              </h2>
            </div>

            <span className="text-caption text-elasi-muted">
              {formatPersianNumber(
                product.variants.length,
              )}{" "}
              گزینه
            </span>
          </div>

          <div
            className="mt-5 grid gap-3"
            role="radiogroup"
            aria-label="انتخاب مدل محصول"
          >
            {product.variants.map(
              (variant) => {
                const isSelected =
                  variant.sku ===
                  selectedVariant?.sku;

                const variantAvailable =
                  variant.available > 0;

                return (
                  <button
                    key={variant.sku}
                    type="button"
                    role="radio"
                    aria-checked={
                      isSelected
                    }
                    onClick={() =>
                      handleVariantChange(
                        variant.sku,
                      )
                    }
                    className={`flex min-h-16 items-center justify-between gap-5 rounded-[18px] border px-5 py-4 text-right transition ${
                      isSelected
                        ? "border-elasi-gold bg-white"
                        : "border-elasi-green/10 bg-white/35 hover:border-elasi-green/25 hover:bg-white/60"
                    }`}
                  >
                    <div>
                      <p className="text-sm font-medium text-elasi-text">
                        {getVariantTitle(
                          variant,
                        )}
                      </p>

                      <p className="mt-1 text-xs text-elasi-muted">
                        {variantAvailable
                          ? "آماده سفارش"
                          : "در حال حاضر ناموجود"}
                      </p>
                    </div>

                    <p className="shrink-0 text-sm font-medium text-elasi-green">
                      {formatToman(
                        variant.price_rial,
                      )}{" "}
                      تومان
                    </p>
                  </button>
                );
              },
            )}
          </div>
        </div>
      ) : null}

      {/* Custom size */}
      {product.allow_custom_size ? (
        <div className="mt-9 rounded-[20px] border border-elasi-gold/25 bg-white/40 p-5">
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
                برای این محصول امکان ثبت
                درخواست سایز اختصاصی وجود
                دارد.
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
            isAddingToCart
          }
          className="elasi-button elasi-button--primary w-full disabled:cursor-not-allowed disabled:opacity-45"
        >
          {isAddingToCart
            ? "در حال افزودن..."
            : isAvailable
              ? "افزودن به سبد خرید"
              : "ناموجود"}
        </button>

        {addToCartSuccess ? (
          <p
            role="status"
            className="mt-3 text-center text-sm font-medium text-elasi-green"
          >
            محصول به سبد خرید اضافه شد.
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