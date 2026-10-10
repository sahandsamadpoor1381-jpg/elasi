import type { Metadata } from "next";

import { CartPageClient } from "@/components/cart/cart-page-client";


export const metadata: Metadata = {
  title: "سبد خرید",

  description:
    "محصولات انتخاب‌شده شما در سبد خرید ELASI.",
};


export default function CartPage() {
  return (
    <main className="min-h-screen bg-elasi-ivory">
      <CartPageClient />
    </main>
  );
}