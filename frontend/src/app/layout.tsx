import type { Metadata } from "next";
import localFont from "next/font/local";

import { AuthProvider } from "@/components/auth/auth-provider";
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
    "فروشگاه آنلاین جواهرات طلا و نقره ELASI.",
};


type RootLayoutProps = Readonly<{
  children: React.ReactNode;
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
        <AuthProvider>
          <CartProvider>
            <SiteHeader />

            {children}
          </CartProvider>
        </AuthProvider>
      </body>
    </html>
  );
}