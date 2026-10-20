import Link from "next/link";

import {
  CATALOG_GENDERS,
  CATALOG_MATERIALS,
  CATALOG_ORDERINGS,
  buildClearCatalogHref,
  type CatalogSearchState,
  type RawSearchParams,
} from "@/lib/catalog-params";
import {
  formatNumber,
  genderLabel,
  materialLabel,
  orderingLabel,
} from "@/lib/format";
import type { CategorySummary } from "@/types/catalog";


type CatalogFilterFormProps = {
  pathname: string;
  searchParams: RawSearchParams;
  categories: CategorySummary[];
  state: CatalogSearchState;
  showGenderFilter: boolean;
  idPrefix: "catalog-desktop" | "catalog-mobile";
  variant: "desktop" | "mobile";
};


const fieldsetClass = "flex flex-col gap-2";
const legendClass = "mb-1 text-sm font-semibold text-elasi-green";
const optionClass =
  "group flex min-h-10 cursor-pointer items-center gap-3 rounded-xl px-3 py-2 text-sm text-elasi-text transition-colors hover:bg-elasi-green/[0.04] focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-elasi-gold-text";
const radioClass =
  "size-4 shrink-0 accent-elasi-green focus-visible:outline-offset-2";


function radioOptionClass(isSelected: boolean): string {
  return `${optionClass} ${isSelected ? "bg-elasi-green/[0.06] font-medium" : ""}`;
}


export function CatalogFilterForm({
  pathname,
  searchParams,
  categories,
  state,
  showGenderFilter,
  idPrefix,
  variant,
}: CatalogFilterFormProps) {
  const isMobile = variant === "mobile";
  const clearHref = buildClearCatalogHref({
    pathname,
    searchParams,
  });

  return (
    <form
      action={pathname}
      method="get"
      className={
        isMobile
          ? "flex min-h-0 flex-1 flex-col"
          : "rounded-card border border-elasi-green/12 bg-white/70 p-4"
      }
    >
      {state.query ? (
        <input type="hidden" name="q" value={state.query} />
      ) : null}

      {state.collection ? (
        <input
          type="hidden"
          name="collection"
          value={state.collection}
        />
      ) : null}

      <div
        className={
          isMobile
            ? "min-h-0 flex-1 space-y-5 overflow-y-auto px-5 py-4"
            : "space-y-5"
        }
      >
        <fieldset className={fieldsetClass}>
          <legend className={legendClass}>دسته‌بندی</legend>

          <label
            htmlFor={`${idPrefix}-category-all`}
            className={radioOptionClass(!state.category)}
          >
            <input
              id={`${idPrefix}-category-all`}
              className={radioClass}
              type="radio"
              name="category"
              value=""
              defaultChecked={!state.category}
            />
            <span className="min-w-0 flex-1">همه‌ی دسته‌ها</span>
          </label>

          {categories.map((category) => (
            <label
              key={category.slug}
              htmlFor={`${idPrefix}-category-${category.slug}`}
              className={radioOptionClass(state.category === category.slug)}
            >
              <input
                id={`${idPrefix}-category-${category.slug}`}
                className={radioClass}
                type="radio"
                name="category"
                value={category.slug}
                defaultChecked={state.category === category.slug}
              />
              <span className="min-w-0 flex-1">{category.name}</span>
              <span className="shrink-0 text-xs tabular-nums text-elasi-muted">
                {formatNumber(category.product_count)}
              </span>
            </label>
          ))}
        </fieldset>

        <fieldset className={fieldsetClass}>
          <legend className={legendClass}>متریال</legend>

          <label
            htmlFor={`${idPrefix}-material-all`}
            className={radioOptionClass(!state.material)}
          >
            <input
              id={`${idPrefix}-material-all`}
              className={radioClass}
              type="radio"
              name="material"
              value=""
              defaultChecked={!state.material}
            />
            <span>همه‌ی متریال‌ها</span>
          </label>

          {CATALOG_MATERIALS.map((material) => (
            <label
              key={material}
              htmlFor={`${idPrefix}-material-${material}`}
              className={radioOptionClass(state.material === material)}
            >
              <input
                id={`${idPrefix}-material-${material}`}
                className={radioClass}
                type="radio"
                name="material"
                value={material}
                defaultChecked={state.material === material}
              />
              <span>{materialLabel(material)}</span>
            </label>
          ))}
        </fieldset>

        {showGenderFilter ? (
          <fieldset className={fieldsetClass}>
            <legend className={legendClass}>مناسب برای</legend>

            <label
              htmlFor={`${idPrefix}-gender-all`}
              className={radioOptionClass(!state.gender)}
            >
              <input
                id={`${idPrefix}-gender-all`}
                className={radioClass}
                type="radio"
                name="gender"
                value=""
                defaultChecked={!state.gender}
              />
              <span>همه</span>
            </label>

            {CATALOG_GENDERS.map((gender) => (
              <label
                key={gender}
                htmlFor={`${idPrefix}-gender-${gender}`}
                className={radioOptionClass(state.gender === gender)}
              >
                <input
                  id={`${idPrefix}-gender-${gender}`}
                  className={radioClass}
                  type="radio"
                  name="gender"
                  value={gender}
                  defaultChecked={state.gender === gender}
                />
                <span>{genderLabel(gender)}</span>
              </label>
            ))}
          </fieldset>
        ) : null}

        <fieldset className={fieldsetClass}>
          <legend className={legendClass}>بازه‌ی قیمت (تومان)</legend>

          <label
            htmlFor={`${idPrefix}-min-price`}
            className="flex flex-col gap-2 text-sm text-elasi-text"
          >
            <span>حداقل قیمت</span>
            <input
              id={`${idPrefix}-min-price`}
              name="min_price_toman"
              type="text"
              inputMode="numeric"
              autoComplete="off"
              pattern="[0-9۰-۹٠-٩,٬ ]*"
              dir="ltr"
              defaultValue={state.minPriceInput ?? ""}
              aria-invalid={state.priceRangeError || undefined}
              aria-describedby={`${idPrefix}-price-help`}
              placeholder="مثلاً ۵۰۰۰۰۰"
              className="min-h-12 w-full rounded-xl border border-elasi-border-strong bg-white px-3 text-end text-elasi-text outline-none transition-colors placeholder:text-elasi-muted/70 hover:border-elasi-green focus-visible:border-elasi-gold-text"
            />
          </label>

          <label
            htmlFor={`${idPrefix}-max-price`}
            className="flex flex-col gap-2 text-sm text-elasi-text"
          >
            <span>حداکثر قیمت</span>
            <input
              id={`${idPrefix}-max-price`}
              name="max_price_toman"
              type="text"
              inputMode="numeric"
              autoComplete="off"
              pattern="[0-9۰-۹٠-٩,٬ ]*"
              dir="ltr"
              defaultValue={state.maxPriceInput ?? ""}
              aria-invalid={state.priceRangeError || undefined}
              aria-describedby={`${idPrefix}-price-help`}
              placeholder="مثلاً ۵۰۰۰۰۰۰"
              className="min-h-12 w-full rounded-xl border border-elasi-border-strong bg-white px-3 text-end text-elasi-text outline-none transition-colors placeholder:text-elasi-muted/70 hover:border-elasi-green focus-visible:border-elasi-gold-text"
            />
          </label>

          <p
            id={`${idPrefix}-price-help`}
            className={
              state.priceRangeError
                ? "text-xs leading-6 text-elasi-danger"
                : "text-xs leading-6 text-elasi-muted"
            }
          >
            {state.priceRangeError
              ? "بازه‌ی قیمت معتبر نیست. عدد صحیح تومان وارد کنید و حداقل را بیشتر از حداکثر نگذارید."
              : "مبلغ را به تومان وارد کنید. قیمت نهایی از اطلاعات ثبت‌شده‌ی محصول می‌آید."}
          </p>
        </fieldset>

        <fieldset className={fieldsetClass}>
          <legend className={legendClass}>موجودی</legend>

          <label
            htmlFor={`${idPrefix}-in-stock`}
            className={optionClass}
          >
            <input
              id={`${idPrefix}-in-stock`}
              className={radioClass}
              type="checkbox"
              name="in_stock"
              value="true"
              defaultChecked={state.inStock}
            />
            <span>فقط محصولات موجود</span>
          </label>
        </fieldset>

        <fieldset className={fieldsetClass}>
          <legend className={legendClass}>مرتب‌سازی</legend>

          {CATALOG_ORDERINGS.map((ordering) => (
            <label
              key={ordering}
              htmlFor={`${idPrefix}-ordering-${ordering}`}
              className={radioOptionClass(state.ordering === ordering)}
            >
              <input
                id={`${idPrefix}-ordering-${ordering}`}
                className={radioClass}
                type="radio"
                name="ordering"
                value={ordering}
                defaultChecked={state.ordering === ordering}
              />
              <span>{orderingLabel(ordering)}</span>
            </label>
          ))}
        </fieldset>
      </div>

      <div
        className={
          isMobile
            ? "flex shrink-0 items-center gap-3 border-t border-elasi-green/10 bg-elasi-ivory px-5 py-4"
            : "mt-5 flex flex-col gap-3 border-t border-elasi-green/10 pt-4"
        }
      >
        <button
          type="submit"
          className="elasi-button elasi-button--primary min-h-12 flex-1"
        >
          اعمال فیلترها
        </button>

        <Link
          href={clearHref}
          className={
            isMobile
              ? "inline-flex min-h-12 shrink-0 items-center justify-center rounded-full border border-elasi-border-strong px-4 text-sm font-medium text-elasi-green transition-colors hover:border-elasi-gold-text hover:bg-white focus-visible:outline-offset-2"
              : "inline-flex min-h-11 items-center justify-center rounded-full px-4 text-sm font-medium text-elasi-muted transition-colors hover:bg-elasi-green/[0.04] hover:text-elasi-green"
          }
        >
          پاک‌کردن
        </Link>
      </div>
    </form>
  );
}
