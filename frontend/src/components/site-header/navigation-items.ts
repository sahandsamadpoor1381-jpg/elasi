export const navigationItems = [
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

export function isNavigationItemActive(
  pathname: string,
  href: string,
): boolean {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}