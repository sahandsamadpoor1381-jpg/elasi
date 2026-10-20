export function ListingSkeleton() {
  return (
    <main
      aria-busy="true"
      aria-live="polite"
      className="bg-elasi-ivory pb-20"
    >
      <div className="elasi-container pt-8 sm:pt-12">
        <span className="sr-only">در حال بارگذاری محصولات…</span>

        <div className="h-4 w-24 animate-pulse rounded-full bg-elasi-green/10" />
        <div className="mt-4 h-10 w-full max-w-xl animate-pulse rounded-full bg-elasi-green/10" />
        <div className="mt-4 h-4 w-full max-w-2xl animate-pulse rounded-full bg-elasi-green/10" />

        <div className="mt-8 grid items-start gap-6 lg:grid-cols-[var(--catalog-filter-width)_minmax(0,1fr)] lg:gap-8">
          <aside className="hidden lg:block">
            <div className="mb-3 h-5 w-20 animate-pulse rounded-full bg-elasi-green/10" />
            <div className="space-y-5 rounded-card border border-elasi-green/10 bg-white/60 p-4">
              {Array.from({ length: 5 }).map((_, groupIndex) => (
                <div
                  key={groupIndex}
                  className="space-y-3 border-b border-elasi-green/10 pb-4 last:border-b-0"
                >
                  <div className="h-4 w-24 animate-pulse rounded-full bg-elasi-green/10" />
                  {Array.from({ length: 3 }).map((_, itemIndex) => (
                    <div
                      key={itemIndex}
                      className="h-4 w-full animate-pulse rounded-full bg-elasi-green/[0.06]"
                    />
                  ))}
                </div>
              ))}
            </div>
          </aside>

          <section aria-label="در حال بارگذاری نتایج محصولات">
            <div className="flex items-center justify-between gap-3 border-b border-elasi-green/10 pb-4">
              <div className="h-4 w-28 animate-pulse rounded-full bg-elasi-green/10" />
              <div className="h-12 w-40 animate-pulse rounded-full border border-elasi-green/10 bg-white/60 lg:hidden" />
            </div>

            <ul className="elasi-product-grid mt-6">
              {Array.from({ length: 6 }).map((_, index) => (
                <li key={index} className="elasi-product-card">
                  <div className="aspect-[4/5] animate-pulse rounded-card bg-elasi-green/[0.06]" />
                  <div className="mt-5 h-3 w-20 animate-pulse rounded-full bg-elasi-green/10" />
                  <div className="mt-3 h-5 w-40 animate-pulse rounded-full bg-elasi-green/10" />
                  <div className="mt-4 h-3 w-full animate-pulse rounded-full bg-elasi-green/10" />
                  <div className="mt-6 h-4 w-24 animate-pulse rounded-full bg-elasi-green/10" />
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </main>
  );
}
