import type { Metadata } from "next";

import Link from "next/link";

import { CatalogErrorState, EmptyCatalogState, ProductGrid } from "@/components/catalog/product-grid";
import { ListingToolbar } from "@/components/catalog/listing-toolbar";
import { Pagination } from "@/components/catalog/pagination";
import { getCategories, getProductPage, searchProducts } from "@/lib/catalog-api";
import {
  PAGE_SIZE,
  buildCatalogHref,
  parseCatalogSearchParams,
  type RawSearchParams,
} from "@/lib/catalog-params";
import { ApiError } from "@/lib/api-client";
import { formatNumber } from "@/lib/format";


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
      "مجموعه‌ی کامل جواهرات طلا و نقره؛ با فیلتر دسته‌بندی، متریال و موجودی.",
    emptyTitle: "هنوز محصولی برای نمایش نیست",
    emptyDescription:
      "به‌محض اضافه‌شدن محصولات، همین صفحه مجموعه‌ی کامل را نشان می‌دهد.",
  },
  women: {
    eyebrow: "WOMEN",
    title: "مجموعه‌ی زنانه",
    description:
      "جواهرات طراحی‌شده برای استایل زنانه؛ به‌همراه طرح‌های مشترک زنانه و مردانه.",
    emptyTitle: "هنوز محصول زنانه‌ای ثبت نشده است",
    emptyDescription:
      "به‌محض اضافه‌شدن محصولات زنانه، همین صفحه آن‌ها را نمایش می‌دهد.",
  },
  men: {
    eyebrow: "MEN",
    title: "مجموعه‌ی مردانه",
    description:
      "جواهرات با فرم‌های ساده و ماندگار برای استایل مردانه؛ به‌همراه طرح‌های مشترک.",
    emptyTitle: "هنوز محصول مردانه‌ای ثبت نشده است",
    emptyDescription:
      "به‌محض اضافه‌شدن محصولات مردانه، همین صفحه آن‌ها را نمایش می‌دهد.",
  },
  search: {
    eyebrow: "SEARCH",
    title: "جست‌وجو در محصولات",
    description:
      "نام محصول، دسته‌بندی یا متریال را جست‌وجو کنید.",
    emptyTitle: "نتیجه‌ای پیدا نشد",
    emptyDescription:
      "برای این جست‌وجو محصولی پیدا نشد. می‌توانید عبارت دیگری را امتحان کنید یا همه‌ی محصولات را ببینید.",
  },
};


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
    // be indexed: they are infinite, low-value and duplicate the
    // canonical listing.
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
      <label
        htmlFor="catalog-search-input"
        className="sr-only"
      >
        جست‌وجوی محصول
      </label>

      <input
        id="catalog-search-input"
        type="search"
        name="q"
        defaultValue={initialQuery}
        autoFocus={autoFocus}
        placeholder="نام محصول، دسته‌بندی یا متریال…"
        className="min-h-12 w-full rounded-full border border-elasi-border-strong bg-white px-5 text-body text-elasi-text outline-none transition-colors placeholder:text-elasi-muted/70 focus:border-elasi-gold focus-visible:ring-2 focus-visible:ring-elasi-gold/40"
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
  const defaults =
    kind === "women"
      ? { gender: "women" }
      : kind === "men"
        ? { gender: "men" }
        : {};

  const state = parseCatalogSearchParams(
    searchParams,
    defaults,
  );

  const copy = PAGE_COPY[kind];

  let categories: Awaited<ReturnType<typeof getCategories>> = [];
  let page = {
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    results: [] as Awaited<
      ReturnType<typeof getProductPage>
    >["results"],
  };
  let hasError = false;

  try {
    const [categoryList, productPage] = await Promise.all([
      getCategories(),
      state.query
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
      searchParams,
      set: { page: targetPage },
      keepPage: true,
    });

  const resultLabel =
    page.count === 0
      ? "بدون نتیجه"
      : `${formatNumber(page.count)} محصول`;

  return (
    <main className="bg-elasi-ivory pb-20">
      <div className="elasi-container pt-10 sm:pt-14">
        <header className="max-w-3xl">
          <p className="text-label font-medium tracking-[0.2em] text-elasi-gold-text">
            {copy.eyebrow}
          </p>

          <h1 className="mt-4 text-h2 text-elasi-green">
            {kind === "search" && state.query
              ? `نتیجه‌ی جست‌وجو برای «${state.query}»`
              : copy.title}
          </h1>

          <p className="mt-4 text-body text-elasi-muted">
            {copy.description}
          </p>
        </header>

        {kind === "search" ? (
          <div className="mt-8 max-w-2xl">
            <CatalogSearchForm
              initialQuery={state.query}
              autoFocus={!state.query}
            />
          </div>
        ) : null}

        <div className="mt-10 rounded-card border border-elasi-green/10 bg-white/60 p-6 sm:p-8">
          <ListingToolbar
            pathname={pathname}
            searchParams={searchParams}
            categories={categories}
            ordering={state.ordering}
            activeCategory={state.category}
            activeMaterial={state.material}
            inStock={state.inStock}
            fixedGender={kind === "women" || kind === "men"}
            hasActiveFilters={state.hasActiveFilters}
          />
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
          <p
            aria-live="polite"
            className="text-sm text-elasi-muted"
          >
            {hasError ? "خطا در دریافت محصولات" : resultLabel}
          </p>

          {state.query ? (
            <Link
              href={pathname}
              className="text-sm font-medium text-elasi-green transition-colors hover:text-elasi-gold-text"
            >
              حذف جست‌وجو
            </Link>
          ) : null}
        </div>

        <div className="mt-8">
          {hasError ? (
            <CatalogErrorState retryHref={pathname} />
          ) : page.results.length === 0 ? (
            <EmptyCatalogState
              title={
                state.query
                  ? copy.emptyTitle
                  : state.hasActiveFilters
                    ? copy.emptyTitle
                    : copy.emptyTitle
              }
              description={
                state.query || state.hasActiveFilters
                  ? copy.emptyDescription
                  : copy.emptyDescription
              }
              action={
                state.hasActiveFilters
                  ? {
                      href: pathname,
                      label: "حذف فیلترها",
                    }
                  : {
                      href: "/",
                      label: "بازگشت به صفحه اصلی",
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
      </div>
    </main>
  );
}
