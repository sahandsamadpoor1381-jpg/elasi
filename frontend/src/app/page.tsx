import Image from "next/image";

import { getProducts } from "@/lib/catalog-api";


function formatToman(priceRial: number): string {
  const priceToman = Math.floor(priceRial / 10);

  return new Intl.NumberFormat("fa-IR").format(priceToman);
}


export default async function Home() {
  const products = await getProducts();

  return (
    <main className="min-h-screen bg-elasi-ivory">
      <section className="elasi-section">
        <div className="elasi-container">
          <div className="mx-auto flex min-h-[70vh] max-w-3xl flex-col items-center justify-center text-center">
            <p className="mb-4 text-sm font-medium tracking-[0.24em] text-elasi-gold">
              ELASI
            </p>

            <h1 className="max-w-2xl text-elasi-green">
              زیبایی، در جزئیات ماندگار است.
            </h1>

            <p className="mt-6 max-w-xl text-base leading-8 text-elasi-muted sm:text-lg">
              جواهرات طلا و نقره با طراحی ظریف، مدرن و ماندگار؛ برای انتخاب‌هایی
              که بخشی از استایل شخصی شما می‌شوند.
            </p>

            <div className="mt-8 flex w-full flex-col items-stretch justify-center gap-3 sm:w-auto sm:flex-row sm:items-center">
              <a
                href="#collection"
                className="elasi-button elasi-button--primary"
              >
                مشاهده مجموعه
              </a>

              <a
                href="#about"
                className="elasi-button elasi-button--secondary"
              >
                درباره ELASI
              </a>
            </div>
          </div>
        </div>
      </section>

      <section
        id="collection"
        className="elasi-section"
      >
        <div className="elasi-container">
          <div className="mb-10 text-center">
            <p className="text-sm font-medium tracking-[0.2em] text-elasi-gold">
              COLLECTION
            </p>

            <h2 className="mt-3 text-elasi-green">
              محصولات ELASI
            </h2>
          </div>

          {products.length === 0 ? (
            <p className="text-center text-elasi-muted">
              در حال حاضر محصولی برای نمایش وجود ندارد.
            </p>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {products.map((product) => {
                const primaryImage =
                  product.images.find(
                    (image) => image.is_primary,
                  ) ?? product.images[0];

                const firstVariant =
                  product.variants[0];

                return (
                  <article
                    key={product.slug}
                    className="overflow-hidden rounded-3xl bg-white"
                  >
                    <div className="relative aspect-square overflow-hidden bg-white">
                      {primaryImage ? (
                        <Image
                          src={primaryImage.image}
                          alt={primaryImage.alt_text || product.name}
                          fill
                          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                          className="object-cover"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center text-sm text-elasi-muted">
                          تصویر محصول موجود نیست
                        </div>
                      )}
                    </div>

                    <div className="p-5 text-right">
                      <p className="text-sm text-elasi-muted">
                        {product.category.name}
                      </p>

                      <h3 className="mt-2 text-xl text-elasi-green">
                        {product.name}
                      </h3>

                      {product.short_description ? (
                        <p className="mt-3 line-clamp-2 text-sm leading-7 text-elasi-muted">
                          {product.short_description}
                        </p>
                      ) : null}

                      <div className="mt-5 flex items-end justify-between gap-4">
                        <div>
                          {firstVariant ? (
                            <>
                              <p className="font-medium text-elasi-green">
                                {formatToman(
                                  firstVariant.price_rial,
                                )}{" "}
                                تومان
                              </p>

                              <p className="mt-1 text-xs text-elasi-muted">
                                موجودی قابل فروش:{" "}
                                {firstVariant.available}
                              </p>
                            </>
                          ) : (
                            <p className="text-sm text-elasi-muted">
                              تنوع قابل فروش موجود نیست
                            </p>
                          )}
                        </div>

                        <a
                          href={`/products/${product.slug}`}
                          className="text-sm font-medium text-elasi-green underline-offset-4 hover:underline"
                        >
                          مشاهده محصول
                        </a>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}