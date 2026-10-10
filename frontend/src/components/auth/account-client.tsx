"use client";

import {
  LogOut,
  Mail,
  Phone,
  UserRound,
  LoaderCircle,
} from "lucide-react";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useState,
} from "react";

import { useAuth } from "@/components/auth/auth-provider";


function displayValue(
  value: string | null | undefined,
): string {
  if (!value?.trim()) {
    return "ثبت نشده";
  }

  return value;
}


export function AccountClient() {
  const router = useRouter();

  const {
    user,
    isLoading,
    error,
    logout,
  } = useAuth();

  const [isLoggingOut, setIsLoggingOut] =
    useState(false);


  useEffect(() => {
    if (
      !isLoading &&
      !user
    ) {
      router.replace(
        "/login?next=/account",
      );
    }
  }, [
    isLoading,
    router,
    user,
  ]);


  async function handleLogout() {
    setIsLoggingOut(true);

    try {
      await logout();

      router.replace("/");
      router.refresh();
    } catch {
      setIsLoggingOut(false);
    }
  }


  if (
    isLoading ||
    !user
  ) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoaderCircle
          size={28}
          strokeWidth={1.5}
          className="animate-spin text-elasi-gold"
          aria-hidden="true"
        />

        <span className="sr-only">
          در حال بارگذاری حساب
        </span>
      </div>
    );
  }


  const fullName = [
    user.first_name,
    user.last_name,
  ]
    .filter(Boolean)
    .join(" ")
    .trim();


  return (
    <div className="mx-auto w-full max-w-4xl">
      <div className="mb-10">
        <div
          className="mb-5 h-px w-10 bg-elasi-gold"
          aria-hidden="true"
        />

        <p className="mb-3 text-xs font-medium tracking-[0.2em] text-elasi-gold">
          ELASI ACCOUNT
        </p>

        <h1 className="text-h2 text-elasi-green">
          حساب کاربری
        </h1>

        <p className="mt-3 text-sm leading-7 text-elasi-muted">
          اطلاعات حساب و دسترسی‌های شما در ELASI.
        </p>
      </div>


      {error ? (
        <div
          role="alert"
          className="mb-6 rounded-2xl border border-red-900/10 bg-red-950/[0.035] px-4 py-3 text-sm text-red-900"
        >
          {error}
        </div>
      ) : null}


      <div className="grid gap-5 md:grid-cols-2">
        <article className="rounded-[1.75rem] border border-elasi-green/10 bg-white p-6">
          <div className="mb-6 flex size-11 items-center justify-center rounded-full bg-elasi-green/[0.055] text-elasi-green">
            <UserRound
              size={20}
              strokeWidth={1.6}
              aria-hidden="true"
            />
          </div>

          <p className="text-xs text-elasi-muted">
            نام و نام خانوادگی
          </p>

          <p className="mt-2 text-base font-medium text-elasi-text">
            {displayValue(
              fullName,
            )}
          </p>
        </article>


        <article className="rounded-[1.75rem] border border-elasi-green/10 bg-white p-6">
          <div className="mb-6 flex size-11 items-center justify-center rounded-full bg-elasi-green/[0.055] text-elasi-green">
            <Phone
              size={20}
              strokeWidth={1.6}
              aria-hidden="true"
            />
          </div>

          <p className="text-xs text-elasi-muted">
            شماره موبایل
          </p>

          <p
            dir="ltr"
            className="mt-2 text-right text-base font-medium text-elasi-text"
          >
            {user.phone_number}
          </p>
        </article>


        <article className="rounded-[1.75rem] border border-elasi-green/10 bg-white p-6 md:col-span-2">
          <div className="mb-6 flex size-11 items-center justify-center rounded-full bg-elasi-green/[0.055] text-elasi-green">
            <Mail
              size={20}
              strokeWidth={1.6}
              aria-hidden="true"
            />
          </div>

          <p className="text-xs text-elasi-muted">
            ایمیل
          </p>

          <p className="mt-2 text-base font-medium text-elasi-text">
            {displayValue(
              user.email,
            )}
          </p>
        </article>
      </div>


      <div className="mt-8 border-t border-elasi-green/10 pt-8">
        <button
          type="button"
          onClick={() => {
            void handleLogout();
          }}
          disabled={isLoggingOut}
          className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-elasi-green/15 bg-transparent px-6 text-sm font-medium text-elasi-green transition hover:border-elasi-gold hover:text-elasi-gold disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoggingOut ? (
            <LoaderCircle
              size={17}
              strokeWidth={1.6}
              className="animate-spin"
              aria-hidden="true"
            />
          ) : (
            <LogOut
              size={17}
              strokeWidth={1.6}
              aria-hidden="true"
            />
          )}

          {isLoggingOut
            ? "در حال خروج"
            : "خروج از حساب"}
        </button>
      </div>
    </div>
  );
}