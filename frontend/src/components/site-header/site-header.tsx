import Link from "next/link";

import { AnnouncementBar } from "./announcement-bar";
import { MainNavigation } from "./main-navigation";

export function SiteHeader() {
  return (
    <header className="border-b border-elasi-green/10 bg-elasi-ivory">
      <AnnouncementBar />

      <div className="elasi-container">
        <div className="flex min-h-20 items-center justify-between gap-8">
          <Link
            href="/"
            aria-label="صفحه اصلی ELASI"
            className="text-xl font-semibold tracking-[0.18em] text-elasi-green"
          >
            ELASI
          </Link>

          <MainNavigation />
        </div>
      </div>
    </header>
  );
}