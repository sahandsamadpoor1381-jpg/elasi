import type { Metadata } from "next";
import localFont from "next/font/local";
import type { ReactNode } from "react";

import { CartProvider } from "@/components/cart/cart-provider";
import { SiteHeader } from "@/components/site-header/site-header";

import "./globals.css";


const peyda = localFont({
  src: [
    {
      path: "../assets/fonts/peyda/Peyda-Regular.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "../assets/fonts/peyda/Peyda-Medium.ttf",
      weight: "500",
      style: "normal",
    },
    {
      path: "../assets/fonts/peyda/Peyda-SemiBold.ttf",
      weight: "600",
      style: "normal",
    },
    {
      path: "../assets/fonts/peyda/Peyda-Bold.ttf",
      weight: "700",
      style: "normal",
    },
  ],
  variable: "--font-peyda",
  display: "swap",
});


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


export default function RootLayout({
  children,
}: RootLayoutProps) {
  return (
    <html
      lang="fa"
      dir="rtl"
      className={peyda.variable}
    >
      <body>
        <CartProvider>
          <SiteHeader />

          {children}
        </CartProvider>
      </body>
    </html>
  );
}