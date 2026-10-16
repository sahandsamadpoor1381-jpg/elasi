/**
 * Editorial API client.
 *
 * Only published articles are ever returned by these endpoints; the
 * backend filters on status *and* publication time, so drafts cannot
 * leak into the storefront.
 */

import { apiRequest } from "./api-client";

import type {
  Article,
  ArticleSummary,
} from "@/types/blog";
import type { Paginated } from "@/types/catalog";


export const ARTICLES_PAGE_SIZE = 9;


export async function getArticlePage(
  params: { page?: number; page_size?: number } = {},
): Promise<Paginated<ArticleSummary>> {
  const search = new URLSearchParams();

  search.set(
    "page_size",
    String(params.page_size ?? ARTICLES_PAGE_SIZE),
  );

  if (params.page && params.page > 1) {
    search.set("page", String(params.page));
  }

  return apiRequest<Paginated<ArticleSummary>>(
    `/articles/?${search.toString()}`,
    { method: "GET" },
  );
}


export async function getArticle(
  slug: string,
): Promise<Article | null> {
  try {
    return await apiRequest<Article>(
      `/articles/${encodeURIComponent(slug)}/`,
      { method: "GET" },
    );
  } catch (error) {
    if (
      error instanceof Error &&
      "status" in error &&
      (error as { status?: number }).status === 404
    ) {
      return null;
    }

    throw error;
  }
}
