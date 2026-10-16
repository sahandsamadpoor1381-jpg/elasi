import type { Metadata } from "next";
import localFont from "next/font/local";

import { AuthProvider } from "@/components/auth/auth-provider";
import { CartProvider } from "@/components/cart/cart-provider";
import { SiteFooter } from "@/components/site-footer/site-footer";
import { SiteHeader } from "@/components/site-header/site-header";
import { WishlistProvider } from "@/components/wishlist/wishlist-provider";

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
            <WishlistProvider>
              <div className="flex min-h-screen flex-col">
                <SiteHeader />

                <div className="flex-1">{children}</div>

                <SiteFooter />
              </div>
            </WishlistProvider>
          </CartProvider>
        </AuthProvider>
      </body>
    </html>
  );
}