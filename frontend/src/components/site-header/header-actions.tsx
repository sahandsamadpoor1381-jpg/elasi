import {
  Heart,
  Search,
} from "lucide-react";

import Link from "next/link";

import { AccountLink } from "@/components/auth/account-link";
import { CartLink } from "@/components/cart/cart-link";


export function HeaderActions() {
  return (
    <div
      className="flex items-center gap-1"
      aria-label="عملیات حساب و خرید"
    >
      <Link
        href="/search"
        aria-label="جست‌وجو در محصولات"
        title="جست‌وجو در محصولات"
        className="
          flex
          size-10
          items-center
          justify-center
          rounded-full
          text-elasi-green
          transition-colors
          hover:bg-elasi-green/5
          hover:text-elasi-gold
        "
      >
        <Search
          size={20}
          strokeWidth={1.7}
          aria-hidden="true"
        />
      </Link>


      <AccountLink />


      <Link
        href="/wishlist"
        aria-label="علاقه‌مندی‌ها"
        className="
          flex
          size-10
          items-center
          justify-center
          rounded-full
          text-elasi-green
          transition-colors
          hover:bg-elasi-green/5
          hover:text-elasi-gold
        "
      >
        <Heart
          size={20}
          strokeWidth={1.7}
          aria-hidden="true"
        />
      </Link>


      <CartLink />
    </div>
  );
}