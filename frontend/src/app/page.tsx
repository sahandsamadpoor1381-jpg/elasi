import Image from "next/image";

import Link from "next/link";

import { ProductCard } from "@/components/storefront/product-card";
import {
  getCategories,
  getProductPage,
} from "@/lib/catalog-api";
import type {
  CategorySummary,
  ProductSummary,
} from "@/types/catalog";


const categoryLabels: Record<string, string> = {
  rings: "انگشتر",
  necklaces: "گردنبند",
  bracelets: "دستبند",
  earrings: "گوشواره",
  pendants: "آویز",
  anklets: "پابند",
  sets: "ست و نیم‌ست",
};


function getCategoryLabel(
  slug: string,
  fallback: string,
): string {
  return categoryLabels[slug] ?? fallback;
}


function getHeroProduct(
  products: ProductSummary[],
): ProductSummary | undefined {
  return (
    products.find(
      (product) =>
        product.is_featured &&
        product.images.length > 0,
    ) ??
    products.find(
      (product) => product.images.length > 0,
    ) ??
    products[0]
  );
}


export default async function Home() {
  const [productPage, categories] = await Promise.all([
    getProductPage({
      page_size: 24,
      ordering: "featured",
    }),
    getCategories(),
  ]);

  const products = productPage.results;

  const heroProduct = getHeroProduct(products);

  const heroImage =
    heroProduct?.images.find(
      (image) => image.is_primary,
    ) ?? heroProduct?.images[0];

  const featuredProducts = products.filter(
    (product) => product.is_featured,
  );

  const showcaseProducts =
    featuredProducts.length > 0
      ? featuredProducts.slice(0, 6)
      : products.slice(0, 6);

  return (
    <main className="overflow-hidden bg-elasi-ivory">
      {/* =====================================================
          HERO
      ====================================================== */}
      <section className="relative">
        <div className="elasi-container py-8 sm:py-10 lg:py-14">
          <div className="grid min-h-[620px] items-stretch gap-8 lg:grid-cols-[0.92fr_1.08fr] lg:gap-12">
            {/* Hero Copy */}
            <div className="order-2 flex flex-col justify-center py-6 text-right lg:order-1 lg:py-12">
              <p className="text-label font-medium tracking-[0.2em] text-elasi-gold">
                ELASI JEWELRY
              </p>

              <h1 className="mt-5 max-w-2xl text-display text-elasi-green">
                زیبایی‌ای که
                <br />
                با شما ماندگار
                <br className="hidden sm:block" />
                می‌شود.
              </h1>

              <p className="mt-7 max-w-xl text-body-lg text-elasi-muted">
                مجموعه‌ای از جواهرات طلا و نقره با نگاهی
                مدرن، ظریف و ماندگار؛ برای انتخاب‌هایی که
                بخشی از استایل شخصی شما می‌شوند.
              </p>

              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/shop"
                  className="elasi-button elasi-button--primary"
                >
                  مشاهده مجموعه
                </Link>

                <Link
                  href="/about"
                  className="elasi-button elasi-button--secondary"
                >
                  داستان ELASI
                </Link>
              </div>

              {/* Hero Meta */}
              <div className="mt-12 grid max-w-xl grid-cols-3 border-y border-elasi-green/10 py-5">
                <div className="border-l border-elasi-green/10 px-3 first:pr-0">
                  <p className="text-caption text-elasi-muted">
                    متریال
                  </p>

                  <p className="mt-1 text-sm font-medium text-elasi-green">
                    طلا و نقره
                  </p>
                </div>

                <div className="border-l border-elasi-green/10 px-3">
                  <p className="text-caption text-elasi-muted">
                    سبک
                  </p>

                  <p className="mt-1 text-sm font-medium text-elasi-green">
                    مدرن و مینیمال
                  </p>
                </div>

                <div className="px-3">
                  <p className="text-caption text-elasi-muted">
                    تجربه
                  </p>

                  <p className="mt-1 text-sm font-medium text-elasi-green">
                    انتخاب شخصی
                  </p>
                </div>
              </div>
            </div>

            {/* Hero Visual */}
            <div className="order-1 lg:order-2">
              <div className="relative min-h-[420px] overflow-hidden rounded-[36px] bg-white sm:min-h-[520px] lg:h-full">
                {heroImage && heroProduct ? (
                  <>
                    <Image
                      src={heroImage.image}
                      alt={
                        heroImage.alt_text ||
                        heroProduct.name
                      }
                      fill
                      priority
                      sizes="(max-width: 1024px) 100vw, 54vw"
                      className="object-cover"
                    />

                    <div className="absolute inset-0 bg-gradient-to-t from-black/25 via-transparent to-transparent" />

                    {/* Hero Product Overlay */}
                    <div className="absolute inset-x-5 bottom-5 rounded-[24px] border border-white/20 bg-white/80 p-5 backdrop-blur-md sm:inset-x-6 sm:bottom-6">
                      <p className="text-caption text-elasi-gold">
                        انتخاب ELASI
                      </p>

                      <div className="mt-1 flex items-end justify-between gap-4">
                        <div>
                          <h2 className="text-xl font-semibold text-elasi-green sm:text-2xl">
                            {heroProduct.name}
                          </h2>

                          <p className="mt-1 text-sm text-elasi-muted">
                            {getCategoryLabel(
                              heroProduct.category.slug,
                              heroProduct.category.name,
                            )}
                          </p>
                        </div>

                        <Link
                          href={`/products/${heroProduct.slug}`}
                          className="shrink-0 text-sm font-medium text-elasi-green transition-colors hover:text-elasi-gold"
                        >
                          مشاهده محصول
                        </Link>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="flex h-full min-h-[420px] items-center justify-center px-8 text-center sm:min-h-[520px]">
                    <div>
                      <p className="text-label tracking-[0.2em] text-elasi-gold">
                        ELASI
                      </p>

                      <p className="mt-4 text-body text-elasi-muted">
                        مجموعه جدید به‌زودی نمایش داده می‌شود.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          CATEGORY DISCOVERY
      ====================================================== */}
      {categories.length > 0 ? (
        <section className="border-y border-elasi-green/10 bg-white/45">
          <div className="elasi-container py-8 sm:py-10">
            <div className="flex flex-col gap-7">
              <div>
                <p className="text-caption font-medium tracking-[0.18em] text-elasi-gold">
                  DISCOVER
                </p>

                <h2 className="mt-2 text-2xl text-elasi-green sm:text-3xl">
                  جواهر مورد علاقه‌ات را پیدا کن
                </h2>
              </div>

              <div className="flex flex-wrap gap-2">
                {categories.map(
                  (category: CategorySummary) => (
                    <Link
                      key={category.slug}
                      href={`/shop?category=${encodeURIComponent(
                        category.slug,
                      )}`}
                      className="rounded-full border border-elasi-green/15 bg-elasi-ivory px-5 py-2.5 text-sm font-medium text-elasi-green transition-colors hover:border-elasi-gold hover:text-elasi-gold"
                    >
                      {getCategoryLabel(
                        category.slug,
                        category.name,
                      )}
                    </Link>
                  ),
                )}
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {/* =====================================================
          FEATURED / SIGNATURE COLLECTION
      ====================================================== */}
      <section
        id="collection"
        className="elasi-section"
      >
        <div className="elasi-container">
          <div className="mb-10 max-w-2xl sm:mb-14">
            <p className="text-label font-medium tracking-[0.18em] text-elasi-gold">
              SIGNATURE COLLECTION
            </p>

            <h2 className="mt-3 text-elasi-green">
              انتخاب‌های ELASI
            </h2>

            <p className="mt-4 text-body text-elasi-muted">
              محصولاتی با طراحی ظریف و هویت ماندگار؛
              انتخاب‌شده برای ساختن مجموعه‌ای شخصی و متفاوت.
            </p>

            <p className="mt-5 text-sm text-elasi-muted">
              {showcaseProducts.length > 0
                ? `${new Intl.NumberFormat("fa-IR").format(
                    showcaseProducts.length,
                  )} محصول`
                : "محصولی موجود نیست"}
            </p>
          </div>

          {showcaseProducts.length === 0 ? (
            <div className="rounded-[28px] border border-elasi-green/10 bg-white/50 px-6 py-16 text-center">
              <p className="text-body text-elasi-muted">
                در حال حاضر محصول فعالی برای نمایش وجود
                ندارد.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,280px),360px))] justify-center gap-x-8 gap-y-12">
              {showcaseProducts.map((product) => (
                <ProductCard
                  key={product.slug}
                  product={product}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* =====================================================
          BRAND STORY
      ====================================================== */}
      <section
        id="brand-story"
        className="bg-elasi-green text-elasi-white"
      >
        <div className="elasi-container py-20 sm:py-24 lg:py-28">
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
            <div>
              <p className="text-label tracking-[0.2em] text-elasi-gold">
                THE ELASI STORY
              </p>

              <h2
                className="mt-4 max-w-lg"
                style={{
                  color: "var(--elasi-white)",
                }}
              >
                جواهر، فقط یک انتخاب نیست؛ بخشی از روایت
                شماست.
              </h2>
            </div>

            <div className="max-w-2xl">
              <p className="text-body-lg text-white/75">
                ELASI با تمرکز بر فرم‌های ظریف، ترکیب‌های
                ماندگار و زیبایی بدون اغراق شکل گرفته است.
                هدف ما ساخت تجربه‌ای است که در آن انتخاب
                جواهر، ساده، شخصی و نزدیک به سبک زندگی شما
                باشد.
              </p>

              <div className="mt-8 h-px w-20 bg-elasi-gold" />

              <p className="mt-7 text-sm leading-7 text-white/60">
                طراحی آرام، جزئیات دقیق و انتخاب آگاهانه؛
                اصولی که هویت بصری و تجربه ELASI را شکل
                می‌دهند.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          CLOSING CTA
      ====================================================== */}
      <section className="elasi-section">
        <div className="elasi-container">
          <div className="relative overflow-hidden rounded-[36px] border border-elasi-green/10 bg-white px-6 py-16 text-center sm:px-10 sm:py-20 lg:px-16">
            <div className="mx-auto max-w-3xl">
              <p className="text-label tracking-[0.2em] text-elasi-gold">
                YOUR STYLE, YOUR STORY
              </p>

              <h2 className="mt-4 text-elasi-green">
                انتخابی که به سبک شما نزدیک‌تر است
              </h2>

              <p className="mx-auto mt-5 max-w-2xl text-body text-elasi-muted">
                مجموعه ELASI را ببینید و میان فرم‌ها،
                متریال‌ها و جزئیات مختلف، انتخاب مناسب خودتان
                را پیدا کنید.
              </p>

              <Link
                href="/shop"
                className="elasi-button elasi-button--primary mt-8"
              >
                مشاهده محصولات
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}