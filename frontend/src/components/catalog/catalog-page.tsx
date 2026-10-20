import type { Metadata } from "next";

import Link from "next/link";

import { CatalogFilterForm } from "@/components/catalog/catalog-filter-form";
import { MobileFilterDialog } from "@/components/catalog/mobile-filter-dialog";
import {
  CatalogErrorState,
  EmptyCatalogState,
  ProductGrid,
} from "@/components/catalog/product-grid";
import { ListingToolbar } from "@/components/catalog/listing-toolbar";
import { Pagination } from "@/components/catalog/pagination";
import {
  getCategories,
  getProductPage,
  searchProducts,
} from "@/lib/catalog-api";
import {
  PAGE_SIZE,
  buildCatalogHref,
  buildClearCatalogHref,
  parseCatalogSearchParams,
  type CatalogSearchState,
  type RawSearchParams,
} from "@/lib/catalog-params";
import { ApiError } from "@/lib/api-client";
import {
  formatNumber,
  genderLabel,
  materialLabel,
} from "@/lib/format";
import type { CategorySummary } from "@/types/catalog";


export type CatalogPageKind = "shop" | "women" | "men" | "search";


type CatalogPageProps = {
  kind: CatalogPageKind;
  pathname: string;
  searchParams: RawSearchParams;
};


const PAGE_COPY: Record<
  CatalogPageKind,
  {
    eyebrow: string;
    title: string;
    description: string;
    emptyTitle: string;
    emptyDescription: string;
  }
> = {
  shop: {
    eyebrow: "SHOP",
    title: "همه‌ی محصولات ELASI",
    description:
      "جواهرات طلا و نقره را بر پایه‌ی دسته‌بندی، متریال، قیمت و موجودی پیدا کنید.",
    emptyTitle: "هنوز محصولی برای نمایش نیست",
    emptyDescription:
      "به‌محض ثبت محصولات، اطلاعات واقعی فروشگاه در این صفحه نمایش داده می‌شود.",
  },
  women: {
    eyebrow: "WOMEN",
    title: "مجموعه‌ی زنانه",
    description:
      "جواهرات طراحی‌شده برای استایل زنانه، به‌همراه طرح‌های مشترک زنانه و مردانه.",
    emptyTitle: "هنوز محصول زنانه‌ای ثبت نشده است",
    emptyDescription:
      "به‌محض ثبت محصولات زنانه، اطلاعات واقعی فروشگاه در این صفحه نمایش داده می‌شود.",
  },
  men: {
    eyebrow: "MEN",
    title: "مجموعه‌ی مردانه",
    description:
      "جواهرات با فرم‌های ساده و ماندگار برای استایل مردانه، به‌همراه طرح‌های مشترک.",
    emptyTitle: "هنوز محصول مردانه‌ای ثبت نشده است",
    emptyDescription:
      "به‌محض ثبت محصولات مردانه، اطلاعات واقعی فروشگاه در این صفحه نمایش داده می‌شود.",
  },
  search: {
    eyebrow: "SEARCH",
    title: "جست‌وجو در محصولات",
    description: "نام محصول، دسته‌بندی یا متریال را جست‌وجو کنید.",
    emptyTitle: "نتیجه‌ای پیدا نشد",
    emptyDescription:
      "برای این جست‌وجو محصولی پیدا نشد. عبارت دیگری را امتحان کنید یا فیلترها را پاک کنید.",
  },
};


type FilterChip = {
  key: string;
  label: string;
  href: string;
};


function activeFilterCount(
  state: CatalogSearchState,
  fixedGender?: "women" | "men",
): number {
  return [
    Boolean(state.category),
    Boolean(state.collection),
    Boolean(state.material),
    Boolean(state.gender && !fixedGender),
    state.inStock,
    state.priceRangeError ||
      state.minPriceToman !== undefined ||
      state.maxPriceToman !== undefined,
  ].filter(Boolean).length;
}


function ActiveFilterChips({
  pathname,
  searchParams,
  categories,
  state,
  fixedGender,
}: {
  pathname: string;
  searchParams: RawSearchParams;
  categories: CategorySummary[];
  state: CatalogSearchState;
  fixedGender?: "women" | "men";
}) {
  const href = (
    set: Record<string, string | number | boolean | null | undefined>,
  ) => buildCatalogHref({ pathname, searchParams, set });

  const chips: FilterChip[] = [];

  if (state.query) {
    chips.push({
      key: "query",
      label: `جست‌وجو: ${state.query}`,
      href: href({ q: null }),
    });
  }

  if (state.category) {
    const categoryName =
      categories.find((category) => category.slug === state.category)?.name ??
      state.category;

    chips.push({
      key: "category",
      label: `دسته‌بندی: ${categoryName}`,
      href: href({ category: null }),
    });
  }

  if (state.collection) {
    chips.push({
      key: "collection",
      label: `مجموعه: ${state.collection}`,
      href: href({ collection: null }),
    });
  }

  if (state.material) {
    chips.push({
      key: "material",
      label: `متریال: ${materialLabel(state.material)}`,
      href: href({ material: null }),
    });
  }

  if (state.gender && !fixedGender) {
    chips.push({
      key: "gender",
      label: `مناسب برای: ${genderLabel(state.gender)}`,
      href: href({ gender: null }),
    });
  }

  if (state.inStock) {
    chips.push({
      key: "stock",
      label: "فقط محصولات موجود",
      href: href({ in_stock: null }),
    });
  }

  if (
    state.priceRangeError ||
    state.minPriceToman !== undefined ||
    state.maxPriceToman !== undefined
  ) {
    const priceLabel = state.priceRangeError
      ? "بازه‌ی قیمت نامعتبر"
      : state.minPriceToman !== undefined &&
          state.maxPriceToman !== undefined
        ? `${formatNumber(state.minPriceToman)} تا ${formatNumber(state.maxPriceToman)} تومان`
        : state.minPriceToman !== undefined
          ? `از ${formatNumber(state.minPriceToman)} تومان`
          : `تا ${formatNumber(state.maxPriceToman ?? 0)} تومان`;

    chips.push({
      key: "price",
      label: priceLabel,
      href: href({
        min_price: null,
        max_price: null,
        min_price_toman: null,
        max_price_toman: null,
      }),
    });
  }

  if (chips.length === 0) {
    return null;
  }

  return (
    <div
      role="group"
      aria-label="فیلترهای فعال"
      className="mt-4 flex flex-wrap items-center gap-2"
    >
      {chips.map((chip) => (
        <Link
          key={chip.key}
          href={chip.href}
          aria-label={`حذف فیلتر ${chip.label}`}
          scroll={false}
          className="inline-flex min-h-10 max-w-full items-center gap-2 rounded-full border border-elasi-border-strong bg-white px-3 text-sm text-elasi-green transition-colors hover:border-elasi-gold-text hover:bg-elasi-green/[0.03] focus-visible:outline-offset-2"
        >
          <span className="min-w-0 truncate">{chip.label}</span>
          <span aria-hidden="true" className="shrink-0 text-elasi-muted">
            ×
          </span>
        </Link>
      ))}
    </div>
  );
}


/** Shared metadata builder so every listing has sane, honest titles. */
export function buildCatalogMetadata(
  kind: CatalogPageKind,
  searchState: { query: string; hasActiveFilters: boolean },
): Metadata {
  const copy = PAGE_COPY[kind];
  const title =
    kind === "search" && searchState.query
      ? `جست‌وجو: ${searchState.query}`
      : copy.title;

  return {
    title,
    description: copy.description,
    alternates: {
      canonical: kind === "search" ? "/search" : undefined,
    },
    // Arbitrary filter combinations and search result pages should not
    // be indexed: they are infinite, low-value and duplicate the listing.
    robots:
      kind === "search" || searchState.hasActiveFilters
        ? { index: false, follow: true }
        : undefined,
  };
}


export function CatalogSearchForm({
  action = "/search",
  initialQuery = "",
  autoFocus = false,
}: {
  action?: string;
  initialQuery?: string;
  autoFocus?: boolean;
}) {
  return (
    <form
      action={action}
      method="get"
      role="search"
      className="flex w-full flex-col gap-3 sm:flex-row"
    >
      <label htmlFor="catalog-search-input" className="sr-only">
        جست‌وجوی محصول
      </label>

      <input
        id="catalog-search-input"
        type="search"
        name="q"
        defaultValue={initialQuery}
        autoFocus={autoFocus}
        placeholder="نام محصول، دسته‌بندی یا متریال…"
        className="min-h-12 w-full rounded-full border border-elasi-border-strong bg-white px-5 text-body text-elasi-text outline-none transition-colors placeholder:text-elasi-muted/70 focus:border-elasi-gold-text"
      />

      <button
        type="submit"
        className="elasi-button elasi-button--primary min-h-12 shrink-0"
      >
        جست‌وجو
      </button>

      {initialQuery ? (
        <Link
          href={action}
          className="flex min-h-12 shrink-0 items-center justify-center rounded-full border border-elasi-border-strong px-5 text-sm font-medium text-elasi-muted transition-colors hover:border-elasi-danger/40 hover:text-elasi-danger"
        >
          پاک‌کردن
        </Link>
      ) : null}
    </form>
  );
}


export async function CatalogPage({
  kind,
  pathname,
  searchParams,
}: CatalogPageProps) {
  const fixedGender =
    kind === "women" ? "women" : kind === "men" ? "men" : undefined;
  const defaults = fixedGender ? { gender: fixedGender } : {};
  const state = parseCatalogSearchParams(searchParams, defaults);
  const copy = PAGE_COPY[kind];

  // Remove route-scoped gender from links and forms. The route itself is
  // authoritative, so /women?gender=men cannot change its catalog scope.
  const effectiveSearchParams: RawSearchParams = { ...searchParams };
  if (fixedGender) {
    delete effectiveSearchParams.gender;
  }

  let categories: CategorySummary[] = [];
  let page = {
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    results: [] as Awaited<ReturnType<typeof getProductPage>>["results"],
  };
  let hasError = false;

  try {
    const [categoryList, productPage] = await Promise.all([
      getCategories(),
      state.priceRangeError
        ? Promise.resolve({ count: 0, next: null, previous: null, results: [] })
        : state.query
          ? searchProducts(state.query, {
              ...state.apiParams,
              q: undefined,
            })
          : getProductPage(state.apiParams),
    ]);

    categories = categoryList;
    page = productPage;
  } catch (error) {
    if (error instanceof ApiError) {
      hasError = true;
    } else {
      throw error;
    }
  }

  const buildHref = (targetPage: number) =>
    buildCatalogHref({
      pathname,
      searchParams: effectiveSearchParams,
      set: { page: targetPage },
      keepPage: true,
    });

  const clearHref = buildClearCatalogHref({
    pathname,
    searchParams: effectiveSearchParams,
  });

  const resultLabel = state.priceRangeError
    ? "بازه‌ی قیمت نامعتبر"
    : page.count === 0
      ? "بدون نتیجه"
      : `${formatNumber(page.count)} محصول`;

  const activeCount = activeFilterCount(state, fixedGender);
  const filterFormProps = {
    pathname,
    searchParams: effectiveSearchParams,
    categories,
    state,
    showGenderFilter: !fixedGender,
  };

  return (
    <main className="bg-elasi-ivory pb-20">
      <div className="elasi-container pt-8 sm:pt-12">
        <header className="max-w-4xl">
          <p className="text-label font-medium tracking-[0.2em] text-elasi-gold-text">
            {copy.eyebrow}
          </p>

          <h1 className="mt-3 text-h1 text-elasi-green">
            {kind === "search" && state.query
              ? `نتیجه‌ی جست‌وجو برای «${state.query}»`
              : copy.title}
          </h1>

          <p className="mt-3 max-w-[65ch] text-body text-elasi-muted">
            {copy.description}
          </p>
        </header>

        {kind === "search" ? (
          <div className="mt-6 max-w-2xl">
            <CatalogSearchForm
              initialQuery={state.query}
              autoFocus={!state.query}
            />
          </div>
        ) : null}

        <div className="mt-8 grid items-start gap-6 lg:grid-cols-[var(--catalog-filter-width)_minmax(0,1fr)] lg:gap-8">
          <aside
            aria-label="فیلترهای محصولات"
            className="hidden lg:block"
          >
            <h2 className="mb-3 text-base font-semibold text-elasi-green">
              فیلترها
            </h2>
            <ListingToolbar
              pathname={pathname}
              searchParams={effectiveSearchParams}
              categories={categories}
              state={state}
              showGenderFilter={!fixedGender}
            />
          </aside>

          <section
            aria-label="نتایج محصولات"
            className="min-w-0"
          >
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-elasi-green/10 pb-4">
              <p
                aria-live="polite"
                className="text-sm font-medium text-elasi-muted"
              >
                {hasError ? "خطا در دریافت محصولات" : resultLabel}
              </p>

              <div className="lg:hidden">
                <MobileFilterDialog activeFilterCount={activeCount}>
                  <CatalogFilterForm
                    {...filterFormProps}
                    idPrefix="catalog-mobile"
                    variant="mobile"
                  />
                </MobileFilterDialog>
              </div>
            </div>

            {state.priceRangeError ? (
              <p
                role="alert"
                className="mt-4 rounded-xl border border-elasi-danger/30 bg-white px-4 py-3 text-sm leading-6 text-elasi-danger"
              >
                بازه‌ی قیمت معتبر نیست. حداقل قیمت باید از حداکثر بیشتر نباشد و هر دو مقدار باید عدد صحیح تومان باشند.
              </p>
            ) : null}

            <ActiveFilterChips
              pathname={pathname}
              searchParams={effectiveSearchParams}
              categories={categories}
              state={state}
              fixedGender={fixedGender}
            />

            <div className="mt-6">
              {hasError ? (
                <CatalogErrorState
                  retryHref={buildCatalogHref({
                    pathname,
                    searchParams: effectiveSearchParams,
                    keepPage: true,
                  })}
                />
              ) : state.priceRangeError ? (
                <EmptyCatalogState
                  title="فیلتر قیمت را اصلاح کنید"
                  description="قیمت‌ها را به تومان وارد کنید و مطمئن شوید حداقل قیمت بیشتر از حداکثر نیست."
                  action={{ href: clearHref, label: "پاک‌کردن فیلترها" }}
                />
              ) : page.results.length === 0 ? (
                <EmptyCatalogState
                  title={
                    state.hasActiveFilters
                      ? "محصولی مطابق انتخاب شما پیدا نشد"
                      : copy.emptyTitle
                  }
                  description={
                    state.hasActiveFilters
                      ? "برای دیدن محصولات بیشتر، فیلترها را تغییر دهید یا پاک کنید."
                      : copy.emptyDescription
                  }
                  action={
                    state.hasActiveFilters
                      ? {
                          href: clearHref,
                          label: "پاک‌کردن فیلترها",
                        }
                      : {
                          href: "/",
                          label: "بازگشت به صفحه‌ی اصلی",
                        }
                  }
                />
              ) : (
                <>
                  <ProductGrid products={page.results} />

                  <Pagination
                    currentPage={state.page}
                    totalCount={page.count}
                    pageSize={PAGE_SIZE}
                    buildHref={buildHref}
                  />
                </>
              )}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
