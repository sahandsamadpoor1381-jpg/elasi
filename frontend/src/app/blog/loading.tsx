export default function Loading() {
  return (
    <div
      aria-busy="true"
      className="elasi-container pt-10 pb-20 sm:pt-14"
    >
      <span className="sr-only">در حال بارگذاری مطالب…</span>

      <div className="h-4 w-24 animate-pulse rounded-full bg-elasi-green/10" />
      <div className="mt-5 h-9 w-56 animate-pulse rounded-full bg-elasi-green/10" />

      <ul className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <li
            key={index}
            className="overflow-hidden rounded-[28px] border border-elasi-green/10 bg-white/50"
          >
            <div className="aspect-[16/9] animate-pulse bg-elasi-green/[0.06]" />
            <div className="p-6">
              <div className="h-3 w-24 animate-pulse rounded-full bg-elasi-green/10" />
              <div className="mt-4 h-5 w-4/5 animate-pulse rounded-full bg-elasi-green/10" />
              <div className="mt-4 h-3 w-full animate-pulse rounded-full bg-elasi-green/10" />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
