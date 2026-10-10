import type { Metadata } from "next";

import { LoginForm } from "@/components/auth/login-form";


export const metadata: Metadata = {
  title: "ورود به حساب",
  description:
    "ورود امن به حساب کاربری ELASI با شماره موبایل.",
};


type LoginPageProps = {
  searchParams: Promise<{
    next?: string | string[];
  }>;
};


function getSafeRedirect(
  value: string | string[] | undefined,
): string {
  const redirectValue =
    Array.isArray(value)
      ? value[0]
      : value;

  if (
    !redirectValue ||
    !redirectValue.startsWith("/") ||
    redirectValue.startsWith("//")
  ) {
    return "/account";
  }

  return redirectValue;
}


export default async function LoginPage({
  searchParams,
}: LoginPageProps) {
  const params =
    await searchParams;

  const redirectTo =
    getSafeRedirect(
      params.next,
    );

  return (
    <main className="min-h-[calc(100vh-120px)] bg-elasi-ivory">
      <section className="elasi-container grid min-h-[calc(100vh-120px)] items-stretch lg:grid-cols-[0.9fr_1.1fr]">
        <div className="flex items-center py-14 lg:py-20">
          <div className="mx-auto w-full max-w-md rounded-[2rem] border border-elasi-green/10 bg-white p-6 shadow-[0_24px_70px_rgba(21,42,36,0.06)] sm:p-9">
            <LoginForm
              redirectTo={redirectTo}
            />
          </div>
        </div>

        <div className="relative hidden overflow-hidden border-r border-elasi-green/10 lg:flex lg:min-h-full lg:items-end lg:p-12">
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-[radial-gradient(circle_at_75%_20%,rgba(184,148,90,0.15),transparent_32%),linear-gradient(145deg,#152a24_0%,#1d352e_55%,#10211c_100%)]"
          />

          <div
            aria-hidden="true"
            className="absolute left-12 top-12 size-56 rounded-full border border-white/10"
          />

          <div
            aria-hidden="true"
            className="absolute left-24 top-24 size-32 rounded-full border border-elasi-gold/30"
          />

          <div className="relative z-10 max-w-md pb-6 text-white">
            <p className="mb-5 text-xs font-medium tracking-[0.28em] text-elasi-gold">
              ELASI
            </p>

            <p className="text-3xl font-medium leading-[1.6] text-white">
              حساب شما،
              <br />
              مسیر ساده‌تر خرید در ELASI.
            </p>

            <div
              className="mt-8 h-px w-16 bg-elasi-gold"
              aria-hidden="true"
            />
          </div>
        </div>
      </section>
    </main>
  );
}