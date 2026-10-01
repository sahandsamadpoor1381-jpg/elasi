import { Menu, Search, ShoppingBag } from "lucide-react";
import Link from "next/link";

export function MobileHeader() {
  return (
    <div className="lg:hidden">
      <div className="elasi-container">
        <div className="grid min-h-16 grid-cols-[1fr_auto_1fr] items-center">
          <button
            type="button"
            aria-label="باز کردن منوی اصلی"
            className="flex size-11 justify-self-start items-center justify-center rounded-full text-elasi-green transition-colors hover:bg-elasi-green/5 hover:text-elasi-gold"
          >
            <Menu size={21} strokeWidth={1.7} aria-hidden="true" />
          </button>

          <Link
            href="/"
            aria-label="صفحه اصلی ELASI"
            className="text-lg font-semibold tracking-[0.18em] text-elasi-green"
          >
            ELASI
          </Link>

          <div className="flex justify-self-end items-center gap-1">
            <button
              type="button"
              aria-label="باز کردن جستجو"
              className="flex size-11 items-center justify-center rounded-full text-elasi-green transition-colors hover:bg-elasi-green/5 hover:text-elasi-gold"
            >
              <Search size={20} strokeWidth={1.7} aria-hidden="true" />
            </button>

            <Link
              href="/cart"
              aria-label="سبد خرید"
              className="flex size-11 items-center justify-center rounded-full text-elasi-green transition-colors hover:bg-elasi-green/5 hover:text-elasi-gold"
            >
              <ShoppingBag size={20} strokeWidth={1.7} aria-hidden="true" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}