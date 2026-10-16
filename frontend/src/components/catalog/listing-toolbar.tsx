import Link from "next/link";

import {
  CATALOG_ORDERINGS,
  buildCatalogHref,
  type RawSearchParams,
} from "@/lib/catalog-params";
import { orderingLabel } from "@/lib/format";

import type { CategorySummary } from "@/types/catalog";


type ListingToolbarProps = {
  pathname: string;
  searchParams: RawSearchParams;
  categories: CategorySummary[];
  ordering: string;
  activeCategory?: string;
  activeMaterial?: string;
  inStock: boolean;
  /** Hide the gender chips on the gender-specific listings. */
  fixedGender?: boolean;
  hasActiveFilters: boolean;
};


const chipBase =
  "rounded-full border px-4 py-2 text-sm font-medium transition-colors";

const chipIdle =
  "border-elasi-green/15 bg-elasi-ivory text-elasi-green hover:border-elasi-gold hover:text-elasi-gold";

const chipActive =
  "border-elasi-gold bg-elasi-gold/12 text-elasi-green";


function Chip({
  href,
  label,
  isActive,
  count,
}: {
  href: string;
  label: string;
  isActive: boolean;
  count?: number;
}) {
  return (
    <Link
      href={href}
      aria-current={isActive ? "true" : undefined}
      scroll={false}
      className={`${chipBase} ${
        isActive ? chipActive : chipIdle
      }`}
    >
      {label}
      {typeof count === "number" && count > 0 ? (
        <span className="mr-2 text-xs text-elasi-muted">
          {count.toLocaleString("fa-IR")}
        </span>
      ) : null}
    </Link>
  );
}


/**
 * Filter and sort controls.
 *
 * Everything is a link (or a plain GET form), so filtering works with
 * JavaScript disabled, every state is shareable, and nothing depends on
 * client-side data fetching.
 */
export function ListingToolbar({
  pathname,
  searchParams,
  categories,
  ordering,
  activeCategory,
  activeMaterial,
  inStock,
  fixedGender = false,
  hasActiveFilters,
}: ListingToolbarProps) {
  const href = (
    set: Record<string, string | boolean | null | undefined>,
    keepPage = false,
  ) =>
    buildCatalogHref({
      pathname,
      searchParams,
      set,
      keepPage,
    });

  const genderOptions: {
    value: string;
    label: string;
  }[] = fixedGender
    ? []
    : [
        { value: "women", label: "زنانه" },
        { value: "men", label: "مردانه" },
        { value: "unisex", label: "زنانه و مردانه" },
      ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3">
        <p className="text-caption font-medium tracking-[0.18em] text-elasi-gold">
          دسته‌بندی
        </p>

        <div className="flex flex-wrap gap-2">
          <Chip
            href={href({ category: null })}
            label="همه"
            isActive={!activeCategory}
          />

          {categories.map((category) => (
            <Chip
              key={category.slug}
              href={href({ category: category.slug })}
              label={category.name}
              isActive={activeCategory === category.slug}
              count={category.product_count}
            />
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <p className="text-caption font-medium tracking-[0.18em] text-elasi-gold">
          متریال
        </p>

        <div className="flex flex-wrap gap-2">
          <Chip
            href={href({ material: null })}
            label="همه"
            isActive={!activeMaterial}
          />

          <Chip
            href={href({ material: "gold" })}
            label="طلا"
            isActive={activeMaterial === "gold"}
          />

          <Chip
            href={href({ material: "silver" })}
            label="نقره"
            isActive={activeMaterial === "silver"}
          />
        </div>
      </div>

      {genderOptions.length > 0 ? (
        <div className="flex flex-col gap-3">
          <p className="text-caption font-medium tracking-[0.18em] text-elasi-gold">
            مناسب برای
          </p>

          <div className="flex flex-wrap gap-2">
            {genderOptions.map((option) => (
              <Chip
                key={option.value}
                href={href({ gender: option.value })}
                label={option.label}
                isActive={false}
              />
            ))}
          </div>
        </div>
      ) : null}

      <div className="flex flex-col gap-3 border-t border-elasi-green/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-caption text-elasi-muted">
            مرتب‌سازی:
          </span>

          {CATALOG_ORDERINGS.map((option) => (
            <Chip
              key={option}
              href={href({ ordering: option })}
              label={orderingLabel(option)}
              isActive={ordering === option}
            />
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Chip
            href={href({ in_stock: inStock ? null : true })}
            label="فقط موجود"
            isActive={inStock}
          />

          {hasActiveFilters ? (
            <Link
              href={pathname}
              scroll={false}
              className="text-sm font-medium text-elasi-muted underline-offset-4 transition-colors hover:text-elasi-danger hover:underline"
            >
              حذف همه فیلترها
            </Link>
          ) : null}
        </div>
      </div>
    </div>
  );
}
