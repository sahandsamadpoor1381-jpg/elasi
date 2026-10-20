import { CatalogFilterForm } from "@/components/catalog/catalog-filter-form";
import type { CatalogSearchState, RawSearchParams } from "@/lib/catalog-params";
import type { CategorySummary } from "@/types/catalog";


type ListingToolbarProps = {
  pathname: string;
  searchParams: RawSearchParams;
  categories: CategorySummary[];
  state: CatalogSearchState;
  showGenderFilter: boolean;
};


/** Compact, server-rendered desktop filter rail. */
export function ListingToolbar({
  pathname,
  searchParams,
  categories,
  state,
  showGenderFilter,
}: ListingToolbarProps) {
  return (
    <CatalogFilterForm
      pathname={pathname}
      searchParams={searchParams}
      categories={categories}
      state={state}
      showGenderFilter={showGenderFilter}
      idPrefix="catalog-desktop"
      variant="desktop"
    />
  );
}
