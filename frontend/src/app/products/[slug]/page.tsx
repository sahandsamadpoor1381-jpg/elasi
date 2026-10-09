import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ProductGallery } from "@/components/storefront/product-gallery";
import { ProductPurchasePanel } from "@/components/storefront/product-purchase-panel";
import { getProduct } from "@/lib/catalog-api";


type ProductPageProps = {
  params: Promise<{
    slug: string;
  }>;
};


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


export async function generateMetadata({
  params,
}: ProductPageProps): Promise<Metadata> {
  const { slug } = await params;

  const product = await getProduct(
    slug,
  );

  if (!product) {
    return {
      title: "محصول یافت نشد",
    };
  }

  return {
    title: product.name,
    description:
      product.short_description ||
      product.description ||
      `مشاهده ${product.name} در ELASI`,
  };
}


export default async function ProductPage({
  params,
}: ProductPageProps) {
  const { slug } = await params;

  const product = await getProduct(
    slug,
  );

  if (!product) {
    notFound();
  }

  const categoryLabel =
    getCategoryLabel(
      product.category.slug,
      product.category.name,
    );

  return (
    <main className="bg-elasi-ivory">
      {/* Breadcrumb */}
      <div className="elasi-container py-6 sm:py-8">
        <nav
          aria-label="مسیر صفحه"
          className="flex flex-wrap items-center gap-2 text-sm text-elasi-muted"
        >
          <Link
            href="/"
            className="transition-colors hover:text-elasi-gold"
          >
            خانه
          </Link>

          <span
            aria-hidden="true"
            className="text-elasi-muted/50"
          >
            /
          </span>

          <span>
            {categoryLabel}
          </span>

          <span
            aria-hidden="true"
            className="text-elasi-muted/50"
          >
            /
          </span>

          <span
            className="text-elasi-text"
            aria-current="page"
          >
            {product.name}
          </span>
        </nav>
      </div>

      {/* Main Product Area */}
      <section className="pb-16 sm:pb-20 lg:pb-28">
        <div className="elasi-container">
          <div className="grid gap-10 lg:grid-cols-[1.08fr_0.92fr] lg:items-start lg:gap-16">
            <ProductGallery
              productName={product.name}
              images={product.images}
            />

            <div className="lg:sticky lg:top-8">
              <ProductPurchasePanel
                product={product}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Product Story */}
      {product.description ? (
        <section className="border-t border-elasi-green/10 bg-white/40">
          <div className="elasi-container py-16 sm:py-20 lg:py-24">
            <div className="grid gap-8 lg:grid-cols-[0.7fr_1.3fr] lg:gap-16">
              <div>
                <p className="text-label tracking-[0.18em] text-elasi-gold">
                  PRODUCT STORY
                </p>

                <h2 className="mt-3 text-elasi-green">
                  درباره این محصول
                </h2>
              </div>

              <div className="max-w-3xl">
                <p className="text-body-lg text-elasi-muted">
                  {product.description}
                </p>
              </div>
            </div>
          </div>
        </section>
      ) : null}
    </main>
  );
}