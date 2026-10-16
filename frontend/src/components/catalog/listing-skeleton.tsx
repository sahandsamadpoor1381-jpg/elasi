export function ListingSkeleton() {
  return (
    <div
      aria-busy="true"
      aria-live="polite"
      className="elasi-container pt-10 pb-20 sm:pt-14"
    >
      <span className="sr-only">در حال بارگذاری محصولات…</span>

      <div className="h-4 w-24 animate-pulse rounded-full bg-elasi-green/10" />
      <div className="mt-5 h-9 w-72 animate-pulse rounded-full bg-elasi-green/10" />
      <div className="mt-4 h-4 w-full max-w-xl animate-pulse rounded-full bg-elasi-green/10" />

      <div className="mt-10 h-40 animate-pulse rounded-[28px] border border-elasi-green/10 bg-white/50" />

      <ul className="mt-10 grid grid-cols-[repeat(auto-fill,minmax(min(100%,240px),1fr))] justify-items-center gap-x-6 gap-y-10 sm:gap-x-8 sm:gap-y-12">
        {Array.from({ length: 6 }).map((_, index) => (
          <li
            key={index}
            className="w-full max-w-[360px]"
          >
            <div className="aspect-[4/5] animate-pulse rounded-[28px] bg-elasi-green/[0.06]" />
            <div className="mt-5 h-3 w-20 animate-pulse rounded-full bg-elasi-green/10" />
            <div className="mt-3 h-5 w-40 animate-pulse rounded-full bg-elasi-green/10" />
            <div className="mt-4 h-3 w-full animate-pulse rounded-full bg-elasi-green/10" />
            <div className="mt-6 h-4 w-24 animate-pulse rounded-full bg-elasi-green/10" />
          </li>
        ))}
      </ul>
    </div>
  );
}
