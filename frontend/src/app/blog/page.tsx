import type { Metadata } from "next";

import Link from "next/link";

import { Pagination } from "@/components/catalog/pagination";
import { getArticlePage, ARTICLES_PAGE_SIZE } from "@/lib/blog-api";
import { ApiError } from "@/lib/api-client";
import { formatNumber } from "@/lib/format";
import { mediaPath } from "@/lib/media";
import type { ArticleSummary } from "@/types/blog";


export const metadata: Metadata = {
  title: "مجله ELASI",
  description:
    "نوشته‌های ELASI درباره‌ی جواهرات، متریال‌ها، نگهداری و انتخاب هوشمندانه.",
  alternates: {
    canonical: "/blog",
  },
};


const faDate = new Intl.DateTimeFormat("fa-IR", {
  year: "numeric",
  month: "long",
  day: "numeric",
});


function ArticleCard({ article }: { article: ArticleSummary }) {
  const cover = mediaPath(article.cover_image);

  return (
    <article className="flex h-full flex-col overflow-hidden rounded-card border border-elasi-green/10 bg-white/60 transition-colors hover:border-elasi-gold/40">
      <Link
        href={`/blog/${article.slug}`}
        className="flex h-full flex-col"
      >
        <div className="relative aspect-[16/9] overflow-hidden bg-elasi-green/[0.05]">
          {cover ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={cover}
              alt=""
              className="size-full object-cover"
            />
          ) : (
            <div className="flex size-full items-center justify-center">
              <span className="text-caption tracking-[0.18em] text-elasi-muted">
                ELASI
              </span>
            </div>
          )}
        </div>

        <div className="flex flex-1 flex-col p-6">
          <p className="text-caption text-elasi-muted">
            {faDate.format(new Date(article.published_at))}
          </p>

          <h2 className="mt-3 text-lg font-semibold leading-8 text-elasi-green transition-colors">
            {article.title}
          </h2>

          {article.excerpt ? (
            <p className="mt-3 line-clamp-3 text-sm leading-7 text-elasi-muted">
              {article.excerpt}
            </p>
          ) : null}

          <span className="mt-5 pt-4 text-sm font-medium text-elasi-gold-text">
            ادامه‌ی مطلب
          </span>
        </div>
      </Link>
    </article>
  );
}


type BlogPageProps = {
  searchParams: Promise<{ page?: string }>;
};


export default async function BlogPage({
  searchParams,
}: BlogPageProps) {
  const params = await searchParams;

  const page = Math.max(
    1,
    Number(params.page ?? "1") || 1,
  );

  let articles: Awaited<
    ReturnType<typeof getArticlePage>
  > | null = null;

  let hasError = false;

  try {
    articles = await getArticlePage({ page });
  } catch (error) {
    if (error instanceof ApiError) {
      hasError = true;
    } else {
      throw error;
    }
  }

  const results = articles?.results ?? [];
  const count = articles?.count ?? 0;

  return (
    <main className="bg-elasi-ivory pb-20">
      <div className="elasi-container pt-10 sm:pt-14">
        <header className="max-w-3xl">
          <p className="text-label font-medium tracking-[0.2em] text-elasi-gold-text">
            JOURNAL
          </p>

          <h1 className="mt-4 text-h2 text-elasi-green">
            مجله ELASI
          </h1>

          <p className="mt-4 text-body text-elasi-muted">
            نوشته‌هایی درباره‌ی جواهرات، انتخاب متریال،
            نگهداری و نکته‌هایی که به تصمیم‌گیری بهتر کمک
            می‌کنند.
          </p>
        </header>

        <div className="mt-12">
          {hasError ? (
            <div
              role="alert"
              className="rounded-card border border-elasi-danger/20 bg-elasi-danger/[0.04] px-6 py-14 text-center"
            >
              <p className="text-lg font-semibold text-elasi-green">
                نمایش مطالب ممکن نشد
              </p>

              <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-elasi-muted">
                ارتباط با سرور فروشگاه برقرار نشد. لطفاً
                چند لحظه دیگر دوباره تلاش کنید.
              </p>

              <Link
                href="/blog"
                className="elasi-button elasi-button--primary mt-8"
              >
                تلاش دوباره
              </Link>
            </div>
          ) : results.length === 0 ? (
            <div className="rounded-card border border-elasi-green/10 bg-white/60 px-6 py-16 text-center">
              <p className="text-lg font-semibold text-elasi-green">
                هنوز مطلبی منتشر نشده است
              </p>

              <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-elasi-muted">
                اولین نوشته‌های مجله ELASI به‌زودی در همین
                صفحه منتشر می‌شود. تا آن زمان می‌توانید
                مجموعه‌ی محصولات را ببینید.
              </p>

              <Link
                href="/shop"
                className="elasi-button elasi-button--secondary mt-8"
              >
                مشاهده محصولات
              </Link>
            </div>
          ) : (
            <>
              <p className="text-sm text-elasi-muted">
                {formatNumber(count)} مطلب
              </p>

              <ul className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {results.map((article) => (
                  <li key={article.slug}>
                    <ArticleCard article={article} />
                  </li>
                ))}
              </ul>

              <Pagination
                currentPage={page}
                totalCount={count}
                pageSize={ARTICLES_PAGE_SIZE}
                buildHref={(targetPage) =>
                  targetPage <= 1
                    ? "/blog"
                    : `/blog?page=${targetPage}`
                }
              />
            </>
          )}
        </div>
      </div>
    </main>
  );
}
