import Link from "next/link";

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

export function MainNavigation() {
  return (
    <nav aria-label="ناوبری اصلی">
      <ul className="flex items-center gap-7">
        {navigationItems.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="text-body-sm font-medium text-elasi-text transition-colors hover:text-elasi-gold"
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}