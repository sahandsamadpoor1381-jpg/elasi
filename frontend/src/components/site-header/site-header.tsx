import { AnnouncementBar } from "./announcement-bar";
import { DesktopHeader } from "./desktop-header";

export function SiteHeader() {
  return (
    <header className="border-b border-elasi-green/10 bg-elasi-ivory">
      <AnnouncementBar />
      <DesktopHeader />
    </header>
  );
}