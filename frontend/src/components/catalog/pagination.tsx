import Link from "next/link";

import { formatNumber } from "@/lib/format";


type PaginationProps = {
  currentPage: number;
  totalCount: number;
  pageSize: number;
  buildHref: (page: number) => string;
};


/**
 * Link-based pagination: works without JavaScript, keeps every other
 * filter in the URL, and is keyboard/screen-reader friendly.
 */
export function Pagination({
  currentPage,
  totalCount,
  pageSize,
  buildHref,
}: PaginationProps) {
  const totalPages = Math.max(
    1,
    Math.ceil(totalCount / pageSize),
  );

  if (totalPages <= 1) {
    return null;
  }

  const windowStart = Math.max(
    1,
    Math.min(
      currentPage - 2,
      totalPages - 4,
    ),
  );

  const windowEnd = Math.min(
    totalPages,
    windowStart + 4,
  );

  const pages: number[] = [];

  for (let page = windowStart; page <= windowEnd; page += 1) {
    pages.push(page);
  }

  const linkClasses =
    "flex min-w-11 items-center justify-center rounded-full border px-4 py-2 text-sm font-medium transition-colors";

  return (
    <nav
      aria-label="صفحه‌بندی نتایج"
      className="mt-14 flex flex-wrap items-center justify-center gap-2"
    >
      {currentPage > 1 ? (
        <Link
          href={buildHref(currentPage - 1)}
          rel="prev"
          className={`${linkClasses} border-elasi-green/15 text-elasi-green hover:border-elasi-gold hover:text-elasi-gold`}
        >
          قبلی
        </Link>
      ) : null}

      {pages.map((page) => {
        const isCurrent = page === currentPage;

        return (
          <Link
            key={page}
            href={buildHref(page)}
            aria-current={isCurrent ? "page" : undefined}
            aria-label={`صفحه ${formatNumber(page)}`}
            className={`${linkClasses} ${
              isCurrent
                ? "border-elasi-green bg-elasi-green text-elasi-ivory"
                : "border-elasi-green/15 text-elasi-green hover:border-elasi-gold hover:text-elasi-gold"
            }`}
          >
            {formatNumber(page)}
          </Link>
        );
      })}

      {currentPage < totalPages ? (
        <Link
          href={buildHref(currentPage + 1)}
          rel="next"
          className={`${linkClasses} border-elasi-green/15 text-elasi-green hover:border-elasi-gold hover:text-elasi-gold`}
        >
          بعدی
        </Link>
      ) : null}
    </nav>
  );
}
