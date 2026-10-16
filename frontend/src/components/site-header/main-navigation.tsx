"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  isNavigationItemActive,
  navigationItems,
} from "./navigation-items";

export function MainNavigation() {
  const pathname = usePathname();

  return (
    <nav aria-label="ناوبری اصلی">
      <ul className="flex items-center gap-7">
        {navigationItems.map((item) => {
          const isActive = isNavigationItemActive(pathname, item.href);

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`relative py-2 text-body-sm font-medium transition-colors ${
                  isActive
                    ? "text-elasi-gold-text"
                    : "text-elasi-text hover:text-elasi-gold-text"
                }`}
              >
                {item.label}

                <span
                  aria-hidden="true"
                  className={`absolute inset-x-0 -bottom-0.5 mx-auto h-px bg-elasi-gold transition-[width,opacity] duration-200 ${
                    isActive ? "w-full opacity-100" : "w-0 opacity-0"
                  }`}
                />
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}