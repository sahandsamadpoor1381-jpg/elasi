"use client";

import { ShoppingBag } from "lucide-react";
import Link from "next/link";

import { useCart } from "./cart-provider";


type CartLinkProps = {
  className?: string;
};


export function CartLink({
  className = "",
}: CartLinkProps) {
  const {
    cart,
    isLoading,
  } = useCart();

  const quantity =
    cart?.total_quantity ?? 0;

  const label =
    quantity > 0
      ? `سبد خرید، ${new Intl.NumberFormat(
          "fa-IR",
        ).format(quantity)} کالا`
      : "سبد خرید";

  return (
    <Link
      href="/cart"
      aria-label={label}
      className={`relative flex size-10 items-center justify-center rounded-full text-elasi-green transition-colors hover:bg-elasi-green/5 hover:text-elasi-gold ${className}`}
    >
      <ShoppingBag
        size={20}
        strokeWidth={1.7}
        aria-hidden="true"
      />

      {!isLoading && quantity > 0 ? (
        <span className="absolute -left-1 -top-1 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-elasi-gold px-1 text-[10px] font-semibold leading-none text-white">
          {new Intl.NumberFormat(
            "fa-IR",
          ).format(quantity)}
        </span>
      ) : null}
    </Link>
  );
}