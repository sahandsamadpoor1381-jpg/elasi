"use client";

import { Heart, UserRound, X } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

type MobileNavigationDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
};

const navigationItems = [
  {
    label: "خانه",
    href: "/",
  },
  {
    label: "فروشگاه",
    href: "/shop",
  },
  {
    label: "زنانه",
    href: "/women",
  },
  {
    label: "مردانه",
    href: "/men",
  },
  {
    label: "مجله",
    href: "/blog",
  },
  {
    label: "درباره ما",
    href: "/about",
  },
] as const;

export function MobileNavigationDrawer({
  isOpen,
  onClose,
}: MobileNavigationDrawerProps) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  const drawerState = isOpen ? "open" : "closed";

  return (
    <div
      aria-hidden={!isOpen}
      inert={!isOpen}
      className={`fixed inset-0 z-50 lg:hidden ${
        isOpen ? "pointer-events-auto" : "pointer-events-none"
      }`}
    >
      <button
        type="button"
        aria-label="بستن منوی اصلی"
        onClick={onClose}
        data-state={drawerState}
        className="elasi-mobile-drawer-overlay absolute inset-0 bg-black/30"
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-label="منوی اصلی موبایل"
        data-state={drawerState}
        className="elasi-mobile-drawer-panel absolute inset-y-0 right-0 w-[min(88vw,360px)] bg-elasi-ivory shadow-2xl"
      >
        <div
          data-state={drawerState}
          className="elasi-mobile-drawer-content flex h-full flex-col"
        >
          <div className="flex min-h-16 items-center justify-between border-b border-elasi-green/10 px-5">
            <Link
              href="/"
              onClick={onClose}
              className="text-lg font-semibold tracking-[0.18em] text-elasi-green"
            >
              ELASI
            </Link>

            <button
              type="button"
              aria-label="بستن منو"
              onClick={onClose}
              className="flex size-11 items-center justify-center rounded-full text-elasi-green transition-colors hover:bg-elasi-green/5 hover:text-elasi-gold"
            >
              <X size={21} strokeWidth={1.7} aria-hidden="true" />
            </button>
          </div>

          <nav
            aria-label="ناوبری موبایل"
            className="flex-1 overflow-y-auto px-5 py-6"
          >
            <ul className="flex flex-col">
              {navigationItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={onClose}
                    className="flex min-h-12 items-center border-b border-elasi-green/8 text-base font-medium text-elasi-text transition-colors hover:text-elasi-gold"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>

            <div className="mt-8 border-t border-elasi-green/10 pt-5">
              <Link
                href="/account"
                onClick={onClose}
                className="flex min-h-12 items-center gap-3 text-sm font-medium text-elasi-text transition-colors hover:text-elasi-gold"
              >
                <UserRound
                  size={19}
                  strokeWidth={1.7}
                  aria-hidden="true"
                />

                حساب کاربری
              </Link>

              <Link
                href="/wishlist"
                onClick={onClose}
                className="flex min-h-12 items-center gap-3 text-sm font-medium text-elasi-text transition-colors hover:text-elasi-gold"
              >
                <Heart
                  size={19}
                  strokeWidth={1.7}
                  aria-hidden="true"
                />

                علاقه‌مندی‌ها
              </Link>
            </div>
          </nav>
        </div>
      </aside>
    </div>
  );
}