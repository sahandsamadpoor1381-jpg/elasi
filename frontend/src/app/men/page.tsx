import type { Metadata } from "next";

import {
  CatalogPage,
  buildCatalogMetadata,
  type CatalogPageKind,
} from "@/components/catalog/catalog-page";
import {
  parseCatalogSearchParams,
  type RawSearchParams,
} from "@/lib/catalog-params";


const KIND: CatalogPageKind = "men";
const PATHNAME = "/men";


type PageProps = {
  searchParams: Promise<RawSearchParams>;
};


export async function generateMetadata({
  searchParams,
}: PageProps): Promise<Metadata> {
  const raw = await searchParams;

  const state = parseCatalogSearchParams(
    raw,
    { gender: "men" },
  );

  return buildCatalogMetadata(KIND, {
    query: state.query,
    hasActiveFilters: state.hasActiveFilters,
  });
}


export default async function Page({
  searchParams,
}: PageProps) {
  const raw = await searchParams;

  return (
    <CatalogPage
      kind={KIND}
      pathname={PATHNAME}
      searchParams={raw}
    />
  );
}
