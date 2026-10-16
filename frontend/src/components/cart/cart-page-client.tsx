"use client";

import Image from "next/image";
import Link from "next/link";

import {
  useState,
} from "react";

import {
  CartApiError,
} from "@/lib/cart-api";

import type {
  CartItem,
} from "@/types/cart";

import {
  useCart,
} from "./cart-provider";


function formatToman(
  priceRial: number,
): string {
  return new Intl.NumberFormat(
    "fa-IR",
  ).format(
    Math.floor(
      priceRial / 10,
    ),
  );
}


function formatPersianNumber(
  value:
    | number
    | string,
): string {
  return new Intl.NumberFormat(
    "fa-IR",
  ).format(
    Number(value),
  );
}


function getMaterialLabel(
  material:
    CartItem["material"],
): string {
  const labels: Record<
    CartItem["material"],
    string
  > = {
    gold:
      "طلا",

    silver:
      "نقره",
  };


  return labels[
    material
  ];
}


function getRequestErrorMessage(
  error: unknown,
): string {
  if (
    error instanceof
      CartApiError &&
    error.code ===
      "stock_exceeded"
  ) {
    return `موجودی کافی نیست. موجودی قابل فروش: ${formatPersianNumber(
      error.available ??
        0,
    )}`;
  }


  if (
    error instanceof
      Error
  ) {
    return error.message;
  }


  return "عملیات سبد خرید انجام نشد.";
}


export function CartPageClient() {
  const {
    cart,

    isLoading,

    error:
      providerError,

    updateItemQuantity,

    removeItem,
  } = useCart();


  const [
    pendingItemId,
    setPendingItemId,
  ] =
    useState<
      number | null
    >(null);


  const [
    localError,
    setLocalError,
  ] =
    useState<
      string | null
    >(null);


  async function handleQuantityChange(
    item: CartItem,
    nextQuantity: number,
  ) {
    if (
      nextQuantity < 1 ||
      pendingItemId !==
        null
    ) {
      return;
    }


    setPendingItemId(
      item.id,
    );

    setLocalError(
      null,
    );


    try {
      await updateItemQuantity(
        item.id,
        nextQuantity,
      );
    } catch (
      error
    ) {
      setLocalError(
        getRequestErrorMessage(
          error,
        ),
      );
    } finally {
      setPendingItemId(
        null,
      );
    }
  }


  async function handleRemove(
    itemId: number,
  ) {
    if (
      pendingItemId !==
      null
    ) {
      return;
    }


    setPendingItemId(
      itemId,
    );

    setLocalError(
      null,
    );


    try {
      await removeItem(
        itemId,
      );
    } catch (
      error
    ) {
      setLocalError(
        getRequestErrorMessage(
          error,
        ),
      );
    } finally {
      setPendingItemId(
        null,
      );
    }
  }


  if (isLoading) {
    return (
      <section className="elasi-section">
        <div className="elasi-container">
          <div
            className="
              rounded-card
              border
              border-elasi-green/10
              bg-white/50
              px-6
              py-20
              text-center
            "
          >
            <p className="text-body text-elasi-muted">
              در حال دریافت سبد خرید...
            </p>
          </div>
        </div>
      </section>
    );
  }


  if (
    !cart ||
    cart.items.length ===
      0
  ) {
    return (
      <section className="elasi-section">
        <div className="elasi-container">
          <div
            className="
              mx-auto
              max-w-2xl
              rounded-[32px]
              border
              border-elasi-green/10
              bg-white
              px-6
              py-16
              text-center
              sm:px-10
              sm:py-20
            "
          >
            <p className="text-label tracking-[0.18em] text-elasi-gold-text">
              YOUR CART
            </p>

            <h1 className="mt-4 text-elasi-green">
              سبد خرید شما خالی است
            </h1>

            <p className="mx-auto mt-5 max-w-lg text-body text-elasi-muted">
              هنوز محصولی به سبد خرید اضافه نکرده‌اید.
              مجموعه ELASI را ببینید و انتخاب
              خودتان را پیدا کنید.
            </p>

            <Link
              href="/#collection"
              className="elasi-button elasi-button--primary mt-8"
            >
              مشاهده محصولات
            </Link>
          </div>
        </div>
      </section>
    );
  }


  const visibleError =
    localError ??
    providerError;


  return (
    <section className="elasi-section">
      <div className="elasi-container">
        {/* Page heading */}
        <div className="mb-10 sm:mb-14">
          <p className="text-label tracking-[0.18em] text-elasi-gold-text">
            YOUR CART
          </p>

          <h1 className="mt-3 text-elasi-green">
            سبد خرید
          </h1>

          <p className="mt-3 text-sm text-elasi-muted">
            {formatPersianNumber(
              cart.total_quantity,
            )}{" "}
            کالا در سبد شما
          </p>
        </div>


        {visibleError ? (
          <div
            role="alert"
            className="
              mb-6
              rounded-[18px]
              border
              border-elasi-danger/20
              bg-elasi-danger/[0.05]
              px-5
              py-4
              text-sm
              text-elasi-danger
            "
          >
            {visibleError}
          </div>
        ) : null}


        <div
          className="
            grid
            gap-10
            lg:grid-cols-[1fr_360px]
            lg:items-start
            lg:gap-14
          "
        >
          {/* Cart items */}
          <div className="space-y-4">
            {cart.items.map(
              (item) => {
                const isPending =
                  pendingItemId ===
                  item.id;


                const canIncrease =
                  item.quantity <
                  item.available;


                return (
                  <article
                    key={
                      item.id
                    }
                    className="
                      rounded-[24px]
                      border
                      border-elasi-green/10
                      bg-white
                      p-4
                      sm:p-5
                    "
                  >
                    <div className="flex gap-4 sm:gap-6">
                      {/* Image */}
                      <Link
                        href={`/products/${item.product_slug}`}
                        className="
                          relative
                          size-28
                          shrink-0
                          overflow-hidden
                          rounded-[18px]
                          bg-elasi-ivory
                          sm:size-36
                        "
                      >
                        {item.image ? (
                          <Image
                            src={
                              item.image
                            }
                            alt={
                              item.product_name
                            }
                            fill
                            sizes="144px"
                            className="object-cover"
                          />
                        ) : (
                          <div
                            className="
                              flex
                              h-full
                              items-center
                              justify-center
                              px-3
                              text-center
                              text-xs
                              text-elasi-muted
                            "
                          >
                            بدون تصویر
                          </div>
                        )}
                      </Link>


                      {/* Information */}
                      <div className="min-w-0 flex-1">
                        <div
                          className="
                            flex
                            flex-col
                            gap-3
                            sm:flex-row
                            sm:items-start
                            sm:justify-between
                          "
                        >
                          <div>
                            <Link
                              href={`/products/${item.product_slug}`}
                              className="
                                text-lg
                                font-semibold
                                text-elasi-text
                                transition-colors
                                hover:text-elasi-gold-text
                              "
                            >
                              {
                                item.product_name
                              }
                            </Link>


                            <div
                              className="
                                mt-2
                                flex
                                flex-wrap
                                gap-x-3
                                gap-y-1
                                text-sm
                                text-elasi-muted
                              "
                            >
                              <span>
                                {getMaterialLabel(
                                  item.material,
                                )}
                              </span>


                              {item.karat ? (
                                <span>
                                  {formatPersianNumber(
                                    item.karat,
                                  )}{" "}
                                  عیار
                                </span>
                              ) : null}


                              {item.size ? (
                                <span>
                                  سایز{" "}
                                  {formatPersianNumber(
                                    item.size,
                                  )}
                                </span>
                              ) : null}
                            </div>
                          </div>


                          <div className="sm:text-left">
                            <p className="text-sm font-medium text-elasi-green">
                              {formatToman(
                                item.line_total_rial,
                              )}{" "}
                              تومان
                            </p>


                            {item.quantity >
                            1 ? (
                              <p className="mt-1 text-xs text-elasi-muted">
                                هر عدد{" "}
                                {formatToman(
                                  item.unit_price_rial,
                                )}{" "}
                                تومان
                              </p>
                            ) : null}
                          </div>
                        </div>


                        <div
                          className="
                            mt-5
                            flex
                            flex-wrap
                            items-center
                            justify-between
                            gap-4
                            border-t
                            border-elasi-green/10
                            pt-4
                          "
                        >
                          {/* Quantity */}
                          <div
                            className="
                              inline-flex
                              items-center
                              rounded-full
                              border
                              border-elasi-border-strong
                              bg-elasi-ivory
                            "
                            aria-label="تعداد محصول"
                          >
                            <button
                              type="button"
                              aria-label="کاهش تعداد"
                              disabled={
                                isPending ||
                                item.quantity <=
                                  1
                              }
                              onClick={() =>
                                handleQuantityChange(
                                  item,
                                  item.quantity -
                                    1,
                                )
                              }
                              className="
                                flex
                                size-10
                                items-center
                                justify-center
                                text-lg
                                text-elasi-green
                                transition-colors
                                hover:text-elasi-gold-text
                                disabled:cursor-not-allowed
                                disabled:opacity-30
                              "
                            >
                              −
                            </button>


                            <span className="min-w-10 text-center text-sm font-medium text-elasi-text">
                              {formatPersianNumber(
                                item.quantity,
                              )}
                            </span>


                            <button
                              type="button"
                              aria-label="افزایش تعداد"
                              disabled={
                                isPending ||
                                !canIncrease
                              }
                              onClick={() =>
                                handleQuantityChange(
                                  item,
                                  item.quantity +
                                    1,
                                )
                              }
                              className="
                                flex
                                size-10
                                items-center
                                justify-center
                                text-lg
                                text-elasi-green
                                transition-colors
                                hover:text-elasi-gold-text
                                disabled:cursor-not-allowed
                                disabled:opacity-30
                              "
                            >
                              +
                            </button>
                          </div>


                          <button
                            type="button"
                            disabled={
                              isPending
                            }
                            onClick={() =>
                              handleRemove(
                                item.id,
                              )
                            }
                            className="
                              text-sm
                              text-elasi-muted
                              underline-offset-4
                              transition-colors
                              hover:text-elasi-danger
                              hover:underline
                              disabled:cursor-not-allowed
                              disabled:opacity-40
                            "
                          >
                            {isPending
                              ? "در حال انجام..."
                              : "حذف از سبد"}
                          </button>
                        </div>
                      </div>
                    </div>
                  </article>
                );
              },
            )}
          </div>


          {/* Summary */}
          <aside
            className="
              rounded-card
              border
              border-elasi-green/10
              bg-white
              p-6
              lg:sticky
              lg:top-8
            "
          >
            <p className="text-label tracking-[0.15em] text-elasi-gold-text">
              ORDER SUMMARY
            </p>


            <h2 className="mt-2 text-2xl text-elasi-green">
              خلاصه سبد
            </h2>


            <dl className="mt-7 space-y-4 border-y border-elasi-green/10 py-5">
              <div className="flex items-center justify-between gap-4">
                <dt className="text-sm text-elasi-muted">
                  تعداد کالا
                </dt>

                <dd className="text-sm font-medium text-elasi-text">
                  {formatPersianNumber(
                    cart.total_quantity,
                  )}
                </dd>
              </div>


              <div className="flex items-center justify-between gap-4">
                <dt className="text-sm text-elasi-muted">
                  جمع محصولات
                </dt>

                <dd className="text-sm font-medium text-elasi-text">
                  {formatToman(
                    cart.subtotal_rial,
                  )}{" "}
                  تومان
                </dd>
              </div>
            </dl>


            <div className="mt-6 flex items-end justify-between gap-4">
              <p className="font-medium text-elasi-green">
                مبلغ سبد
              </p>

              <p className="text-xl font-semibold text-elasi-green">
                {formatToman(
                  cart.subtotal_rial,
                )}{" "}
                تومان
              </p>
            </div>


            <Link
              href="/checkout"
              className="
                elasi-button
                elasi-button--primary
                mt-7
                w-full
              "
            >
              ادامه فرایند خرید
            </Link>


            <Link
              href="/#collection"
              className="
                elasi-button
                elasi-button--secondary
                mt-3
                w-full
              "
            >
              ادامه خرید
            </Link>
          </aside>
        </div>
      </div>
    </section>
  );
}