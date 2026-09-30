import Link from "next/link";

import { AnnouncementBar } from "./announcement-bar";
import { HeaderActions } from "./header-actions";
import { MainNavigation } from "./main-navigation";

export function SiteHeader() {
  return (
    <header className="border-b border-elasi-green/10 bg-elasi-ivory">
      <AnnouncementBar />

      <div className="elasi-container">
        <div className="flex min-h-20 items-center gap-8">
          <Link
            href="/"
            aria-label="صفحه اصلی ELASI"
            className="shrink-0 text-xl font-semibold tracking-[0.18em] text-elasi-green"
          >
            ELASI
          </Link>

          <div className="flex flex-1 items-center justify-center">
            <MainNavigation />
          </div>

          <HeaderActions />
        </div>
      </div>
    </header>
  );
}