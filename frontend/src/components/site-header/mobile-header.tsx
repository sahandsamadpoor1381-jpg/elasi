"use client";

import {
  Menu,
  Search,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { CartLink } from "@/components/cart/cart-link";

import { MobileNavigationDrawer } from "./mobile-navigation-drawer";


export function MobileHeader() {
  const [
    isMenuOpen,
    setIsMenuOpen,
  ] = useState(false);

  return (
    <>
      <div className="lg:hidden">
        <div className="elasi-container">
          <div className="grid min-h-16 grid-cols-[1fr_auto_1fr] items-center">
            <button
              type="button"
              aria-label="باز کردن منوی اصلی"
              aria-expanded={
                isMenuOpen
              }
              onClick={() =>
                setIsMenuOpen(true)
              }
              className="flex size-11 justify-self-start items-center justify-center rounded-full text-elasi-green transition-colors hover:bg-elasi-green/5 hover:text-elasi-gold-text"
            >
              <Menu
                size={21}
                strokeWidth={1.7}
                aria-hidden="true"
              />
            </button>

            <Link
              href="/"
              aria-label="صفحه اصلی ELASI"
              className="text-lg font-semibold tracking-[0.18em] text-elasi-green"
            >
              ELASI
            </Link>

            <div className="flex items-center justify-self-end gap-1">
              <Link
                href="/search"
                aria-label="جست‌وجو در محصولات"
                title="جست‌وجو در محصولات"
                className="flex size-11 items-center justify-center rounded-full text-elasi-green transition-colors hover:bg-elasi-green/5 hover:text-elasi-gold-text"
              >
                <Search
                  size={20}
                  strokeWidth={1.7}
                  aria-hidden="true"
                />
              </Link>

              <CartLink className="size-11" />
            </div>
          </div>
        </div>
      </div>

      <MobileNavigationDrawer
        isOpen={isMenuOpen}
        onClose={() =>
          setIsMenuOpen(false)
        }
      />
    </>
  );
}