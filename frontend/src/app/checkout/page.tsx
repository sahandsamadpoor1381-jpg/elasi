import type {
  Metadata,
} from "next";

import {
  CheckoutClient,
} from "@/components/checkout/checkout-client";


export const metadata: Metadata = {
  title: "تکمیل سفارش",

  description:
    "تکمیل اطلاعات ارسال و ثبت سفارش ELASI.",
};


export default function CheckoutPage() {
  return (
    <main className="min-h-screen bg-elasi-ivory">
      <CheckoutClient />
    </main>
  );
}