import type { Metadata } from "next";

import { AccountClient } from "@/components/auth/account-client";


export const metadata: Metadata = {
  title: "حساب کاربری",
  description:
    "پروفایل خصوصی و اطلاعات حساب کاربری شما در ELASI.",
};


export default function AccountPage() {
  return (
    <main className="min-h-[calc(100svh-120px)] bg-elasi-ivory">
      <section
        className="
          elasi-container
          py-8
          sm:py-10
          lg:py-14
        "
      >
        <AccountClient />
      </section>
    </main>
  );
}