import type { Metadata } from "next";

import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError } from "@/lib/api-client";
import { getArticle } from "@/lib/blog-api";
import { mediaPath, siteUrl } from "@/lib/media";


type ArticlePageProps = {
  params: Promise<{ slug: string }>;
};


const faDate = new Intl.DateTimeFormat("fa-IR", {
  year: "numeric",
  month: "long",
  day: "numeric",
});


export async function generateMetadata({
  params,
}: ArticlePageProps): Promise<Metadata> {
  const { slug } = await params;

  let article = null;

  try {
    article = await getArticle(slug);
  } catch (error) {
    if (!(error instanceof ApiError)) {
      throw error;
    }
  }

  if (!article) {
    return {
      title: "مطلب یافت نشد",
      robots: { index: false, follow: true },
    };
  }

  const description =
    article.meta_description || article.excerpt;

  return {
    title: article.meta_title || article.title,
    description: description || undefined,
    alternates: {
      canonical: `/blog/${article.slug}`,
    },
    openGraph: {
      type: "article",
      title: article.meta_title || article.title,
      description: description || undefined,
      publishedTime: article.published_at,
      url: `${siteUrl()}/blog/${article.slug}`,
      images: article.cover_image
        ? [mediaPath(article.cover_image) ?? article.cover_image]
        : undefined,
    },
  };
}


export default async function ArticlePage({
  params,
}: ArticlePageProps) {
  const { slug } = await params;

  let article = null;

  try {
    article = await getArticle(slug);
  } catch (error) {
    if (!(error instanceof ApiError)) {
      throw error;
    }
  }

  if (!article) {
    notFound();
  }

  const cover = mediaPath(article.cover_image);

  const paragraphs = article.body
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  return (
    <main className="bg-elasi-ivory pb-20">
      <article className="elasi-container pt-10 sm:pt-14">
        <nav aria-label="مسیر صفحه" className="text-sm text-elasi-muted">
          <ol className="flex flex-wrap items-center gap-2">
            <li>
              <Link
                href="/"
                className="transition-colors hover:text-elasi-gold-text"
              >
                خانه
              </Link>
            </li>

            <li aria-hidden="true">/</li>

            <li>
              <Link
                href="/blog"
                className="transition-colors hover:text-elasi-gold-text"
              >
                مجله
              </Link>
            </li>

            <li aria-hidden="true">/</li>

            <li className="text-elasi-text">{article.title}</li>
          </ol>
        </nav>

        <header className="mt-8 max-w-3xl">
          <p className="text-caption text-elasi-muted">
            {faDate.format(new Date(article.published_at))}
          </p>

          <h1 className="mt-4 text-h2 text-elasi-green">
            {article.title}
          </h1>

          {article.excerpt ? (
            <p className="mt-5 text-body-lg leading-9 text-elasi-muted">
              {article.excerpt}
            </p>
          ) : null}
        </header>

        {cover ? (
          <div className="mt-10 overflow-hidden rounded-card border border-elasi-green/10 bg-white/60">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={cover}
              alt={article.title}
              className="h-auto w-full object-cover"
            />
          </div>
        ) : null}

        <div className="mt-12 max-w-3xl">
          {paragraphs.map((paragraph, index) => (
            <p
              key={index}
              className="mb-6 text-body leading-9 text-elasi-text"
            >
              {paragraph}
            </p>
          ))}
        </div>

        <div className="mt-14 flex flex-col items-start gap-5 rounded-card border border-elasi-green/10 bg-white/60 p-7 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm leading-7 text-elasi-muted">
            مجموعه‌ی محصولات ELASI را ببینید یا مطلب دیگری
            از مجله بخوانید.
          </p>

          <div className="flex shrink-0 gap-3">
            <Link
              href="/blog"
              className="elasi-button elasi-button--secondary"
            >
              همه‌ی مطالب
            </Link>

            <Link
              href="/shop"
              className="elasi-button elasi-button--primary"
            >
              مشاهده محصولات
            </Link>
          </div>
        </div>
      </article>
    </main>
  );
}
