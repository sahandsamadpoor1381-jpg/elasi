export default function Home() {
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
              <a href="#collection" className="elasi-button elasi-button--primary">
                مشاهده مجموعه
              </a>

              <a href="#about" className="elasi-button elasi-button--secondary">
                درباره ELASI
              </a>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}