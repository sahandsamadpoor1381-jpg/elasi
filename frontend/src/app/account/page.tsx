import type { Metadata } from "next";

import { AccountClient } from "@/components/auth/account-client";


export const metadata: Metadata = {
  title: "حساب کاربری",
  description:
    "مدیریت حساب کاربری ELASI.",
};


export default function AccountPage() {
  return (
    <main className="min-h-[70vh] bg-elasi-ivory">
      <section className="elasi-container py-12 sm:py-16 lg:py-20">
        <AccountClient />
      </section>
    </main>
  );
}