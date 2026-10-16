import Link from "next/link";

import { navigationItems } from "@/components/site-header/navigation-items";


const serviceLinks = [
  { href: "/search", label: "جست‌وجو در محصولات" },
  { href: "/about", label: "درباره ELASI" },
  { href: "/blog", label: "مجله" },
] as const;


const accountLinks = [
  { href: "/account", label: "حساب کاربری" },
  { href: "/wishlist", label: "علاقه‌مندی‌ها" },
  { href: "/cart", label: "سبد خرید" },
] as const;


/**
 * Site footer.
 *
 * Only destinations that actually exist are listed: a footer link that
 * 404s is worse than no link. Policy, terms and contact pages are
 * deliberately absent until the merchant supplies approved content.
 */
export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-elasi-green/10 bg-white/50">
      <div className="elasi-container py-14">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-lg font-semibold tracking-[0.18em] text-elasi-green">
              ELASI
            </p>

            <p className="mt-4 max-w-xs text-sm leading-7 text-elasi-muted">
              جواهرات طلا و نقره با طراحی مدرن و ظریف؛
              انتخاب‌شده برای ماندگاری.
            </p>
          </div>

          <nav aria-label="فروشگاه">
            <p className="text-caption font-medium tracking-[0.18em] text-elasi-gold-text">
              فروشگاه
            </p>

            <ul className="mt-4 flex flex-col gap-3">
              {navigationItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-elasi-text transition-colors hover:text-elasi-gold-text"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <nav aria-label="خدمات">
            <p className="text-caption font-medium tracking-[0.18em] text-elasi-gold-text">
              خدمات
            </p>

            <ul className="mt-4 flex flex-col gap-3">
              {serviceLinks.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-elasi-text transition-colors hover:text-elasi-gold-text"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <nav aria-label="حساب کاربری">
            <p className="text-caption font-medium tracking-[0.18em] text-elasi-gold-text">
              حساب کاربری
            </p>

            <ul className="mt-4 flex flex-col gap-3">
              {accountLinks.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-elasi-text transition-colors hover:text-elasi-gold-text"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="mt-12 flex flex-col gap-4 border-t border-elasi-green/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-caption text-elasi-muted">
            © ELASI
          </p>

          <p className="text-caption text-elasi-muted">
            قیمت‌ها به تومان نمایش داده می‌شوند.
          </p>
        </div>
      </div>
    </footer>
  );
}
