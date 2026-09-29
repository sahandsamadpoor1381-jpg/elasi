import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "ELASI | جواهرات طلا و نقره",
    template: "%s | ELASI",
  },
  description:
    "ELASI؛ فروشگاه آنلاین جواهرات طلا و نقره با تمرکز بر طراحی ظریف، انتخاب ماندگار و تجربه خرید حرفه‌ای.",
};

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}