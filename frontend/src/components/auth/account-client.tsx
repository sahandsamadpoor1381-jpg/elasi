"use client";

import {
  Check,
  LoaderCircle,
  LogOut,
  Mail,
  Package,
  Phone,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import { useRouter } from "next/navigation";
import Link from "next/link";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { useAuth } from "@/components/auth/auth-provider";


function getValue(
  value: string | null | undefined,
): string {
  const normalized =
    value?.trim();

  return normalized
    ? normalized
    : "ثبت نشده";
}


function getInitials(
  firstName?: string | null,
  lastName?: string | null,
): string {
  const first =
    firstName?.trim().charAt(0);

  const last =
    lastName?.trim().charAt(0);

  const value =
    `${first ?? ""}${last ?? ""}`;

  return value || "E";
}


export function AccountClient() {
  const router = useRouter();

  const {
    user,
    isLoading,
    error,
    logout,
  } = useAuth();

  const [
    isLoggingOut,
    setIsLoggingOut,
  ] = useState(false);


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


  const fullName =
    useMemo(
      () => {
        if (!user) {
          return "";
        }

        return [
          user.first_name,
          user.last_name,
        ]
          .filter(Boolean)
          .join(" ")
          .trim();
      },
      [user],
    );


  const initials =
    useMemo(
      () =>
        getInitials(
          user?.first_name,
          user?.last_name,
        ),
      [
        user?.first_name,
        user?.last_name,
      ],
    );


  async function handleLogout() {
    if (isLoggingOut) {
      return;
    }

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
      <div className="flex min-h-[55vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div
            className="
              flex
              size-14
              items-center
              justify-center
              rounded-full
              border
              border-elasi-gold/30
            "
          >
            <LoaderCircle
              size={21}
              strokeWidth={1.5}
              className="animate-spin text-elasi-gold-text"
              aria-hidden="true"
            />
          </div>

          <p className="text-xs tracking-[0.08em] text-elasi-muted">
            در حال آماده‌سازی حساب
          </p>
        </div>
      </div>
    );
  }


  return (
    <div className="mx-auto w-full max-w-[1180px]">

      {/* =====================================================
          PAGE INTRO
         ===================================================== */}

      <header className="mb-8 lg:mb-10">
        <div className="max-w-2xl">
          <div className="mb-5 flex items-center gap-3">
            <span
              aria-hidden="true"
              className="h-px w-11 bg-elasi-gold"
            />

            <p
              dir="ltr"
              className="
                text-[10px]
                font-medium
                tracking-[0.28em]
                text-elasi-gold-text
              "
            >
              ELASI PRIVATE PROFILE
            </p>
          </div>

          <h1 className="text-h1 text-elasi-text">
            حساب شما
          </h1>

          <p className="mt-3 max-w-lg text-sm leading-7 text-elasi-muted">
            هویت و اطلاعات حساب شما در فضای خصوصی ELASI.
          </p>


          <div
            className="
              mt-5
              flex
              w-fit
              items-center
              gap-3
              rounded-full
              border
              border-elasi-green/10
              bg-white/70
              px-4
              py-2.5
            "
          >
            <span
              className="
                flex
                size-7
                items-center
                justify-center
                rounded-full
                bg-elasi-green
                text-elasi-white
              "
            >
              <Check
                size={13}
                strokeWidth={2}
                aria-hidden="true"
              />
            </span>

            <div>
              <p className="text-[9px] leading-none text-elasi-muted">
                وضعیت حساب
              </p>

              <p className="mt-1 text-xs font-medium text-elasi-green">
                ورود تأیید شده
              </p>
            </div>
          </div>
        </div>
      </header>


      {error ? (
        <div
          role="alert"
          className="
            mb-6
            rounded-[1.25rem]
            border
            border-elasi-danger/20
            bg-elasi-danger/[0.05]
            px-5
            py-4
            text-sm
            leading-7
            text-elasi-danger
          "
        >
          {error}
        </div>
      ) : null}


      {/* =====================================================
          PRIVATE PROFILE
         ===================================================== */}

      <section
        aria-label="پروفایل خصوصی ELASI"
        className="
          overflow-hidden
          rounded-[2rem]
          border
          border-elasi-green/10
          bg-white
          shadow-[0_26px_80px_rgba(21,42,36,0.085)]
          lg:grid
          lg:grid-cols-[0.9fr_1.1fr]
        "
      >

        {/* ===================================================
            IDENTITY PANEL
           =================================================== */}

        <div
          className="
            relative
            min-h-[340px]
            overflow-hidden
            bg-elasi-green
            px-6
            py-7
            text-elasi-white
            sm:min-h-[390px]
            sm:px-9
            sm:py-9
            lg:min-h-[570px]
            lg:px-10
            lg:py-10
          "
        >
          {/* Orbits */}

          <div
            aria-hidden="true"
            className="
              absolute
              -left-[90px]
              -top-[90px]
              size-[270px]
              rounded-full
              border
              border-elasi-white/10
              sm:-left-[70px]
              sm:-top-[90px]
              sm:size-[330px]
              lg:-left-[80px]
              lg:-top-[70px]
              lg:size-[390px]
            "
          />

          <div
            aria-hidden="true"
            className="
              absolute
              -left-[22px]
              -top-[22px]
              size-[135px]
              rounded-full
              border
              border-elasi-gold/35
              sm:left-[5px]
              sm:top-[5px]
              sm:size-[175px]
              lg:left-[30px]
              lg:top-[45px]
              lg:size-[205px]
            "
          />

          <div
            aria-hidden="true"
            className="
              absolute
              left-[31px]
              top-[31px]
              size-7
              rounded-full
              border
              border-elasi-gold/50
              sm:left-[73px]
              sm:top-[73px]
              sm:size-9
              lg:left-[113px]
              lg:top-[113px]
              lg:size-11
            "
          />


          <div
            aria-hidden="true"
            className="
              absolute
              bottom-0
              left-[38%]
              top-0
              w-px
              bg-gradient-to-b
              from-transparent
              via-elasi-white/[0.055]
              to-transparent
            "
          />


          <div
            className="
              relative
              z-10
              flex
              h-full
              min-h-[286px]
              flex-col
              justify-between
              sm:min-h-[318px]
              lg:min-h-[490px]
            "
          >
            <div
              dir="ltr"
              className="flex items-start justify-between"
            >
              <div>
                <p className="text-[10px] font-medium tracking-[0.32em] text-elasi-gold">
                  ELASI
                </p>

                <p className="mt-1.5 text-[8px] tracking-[0.25em] text-elasi-white/40">
                  PRIVATE IDENTITY
                </p>
              </div>

              <span className="text-[8px] tracking-[0.25em] text-elasi-white/35">
                01 / PROFILE
              </span>
            </div>


            <div className="mt-14 sm:mt-18 lg:mt-auto lg:pb-2">

              <div
                className="
                  flex
                  size-[74px]
                  items-center
                  justify-center
                  rounded-full
                  border
                  border-elasi-gold/50
                  sm:size-[86px]
                  lg:size-[100px]
                "
              >
                <div
                  className="
                    flex
                    size-[62px]
                    items-center
                    justify-center
                    rounded-full
                    border
                    border-elasi-white/10
                    sm:size-[72px]
                    lg:size-[84px]
                  "
                >
                  <span
                    className="
                      text-2xl
                      font-medium
                      tracking-[0.08em]
                      text-elasi-white
                      sm:text-3xl
                      lg:text-4xl
                    "
                  >
                    {initials}
                  </span>
                </div>
              </div>


              <div className="mt-7">
                <p
                  dir="ltr"
                  className="
                    text-[9px]
                    font-medium
                    tracking-[0.26em]
                    text-elasi-gold
                  "
                >
                  PROFILE HOLDER
                </p>

                <h2
                  style={{
                    color:
                      "var(--elasi-white)",
                  }}
                  className="
                    mt-2
                    text-[1.65rem]
                    font-semibold
                    leading-[1.5]
                    sm:text-[1.95rem]
                    lg:text-[2.2rem]
                  "
                >
                  {fullName
                    ? fullName
                    : "حساب ELASI"}
                </h2>

                <p className="mt-2 text-xs leading-6 text-elasi-white/50">
                  حساب خصوصی شما برای دسترسی به ELASI
                </p>
              </div>


              <div
                aria-hidden="true"
                className="
                  my-6
                  h-px
                  w-full
                  bg-gradient-to-l
                  from-elasi-gold/75
                  via-elasi-white/10
                  to-transparent
                "
              />


              <div className="flex items-end justify-between gap-4">
                <div>
                  <p
                    dir="ltr"
                    className="
                      text-[8px]
                      tracking-[0.24em]
                      text-elasi-white/35
                    "
                  >
                    MOBILE ID
                  </p>

                  <p
                    dir="ltr"
                    className="
                      mt-1.5
                      text-left
                      text-sm
                      font-medium
                      tracking-[0.04em]
                      text-elasi-white
                      sm:text-base
                    "
                  >
                    {user.phone_number}
                  </p>
                </div>

                <ShieldCheck
                  size={23}
                  strokeWidth={1.3}
                  className="text-elasi-gold"
                  aria-hidden="true"
                />
              </div>
            </div>
          </div>
        </div>


        {/* ===================================================
            ACCOUNT RECORD
           =================================================== */}

        <div
          className="
            relative
            flex
            flex-col
            p-6
            sm:p-9
            lg:p-10
            xl:p-12
          "
        >
          <div className="mb-7 sm:mb-9">
            <div className="flex items-center gap-3">
              <span
                aria-hidden="true"
                className="h-px w-9 bg-elasi-gold"
              />

              <p
                dir="ltr"
                className="
                  text-[9px]
                  font-medium
                  tracking-[0.26em]
                  text-elasi-gold-text
                "
              >
                ACCOUNT RECORD
              </p>
            </div>

            <h2 className="mt-4 text-h3 text-elasi-text">
              اطلاعات حساب
            </h2>

            <p className="mt-2 max-w-md text-sm leading-7 text-elasi-muted">
              اطلاعات واقعی ثبت‌شده برای حساب شما.
            </p>
          </div>


          <div className="border-t border-elasi-green/10">

            {/* NAME */}

            <div
              className="
                group
                grid
                grid-cols-[48px_1fr]
                gap-x-4
                gap-y-1
                border-b
                border-elasi-green/10
                py-5
                sm:grid-cols-[52px_150px_1fr]
                sm:items-center
              "
            >
              <div
                className="
                  row-span-2
                  flex
                  size-11
                  items-center
                  justify-center
                  rounded-full
                  border
                  border-elasi-green/10
                  bg-elasi-ivory
                  text-elasi-green
                  transition-all
                  duration-300
                  group-hover:border-elasi-gold-text
                  group-hover:text-elasi-gold-text
                  sm:row-span-1
                "
              >
                <UserRound
                  size={18}
                  strokeWidth={1.5}
                  aria-hidden="true"
                />
              </div>

              <p className="self-center text-xs text-elasi-muted">
                نام و نام خانوادگی
              </p>

              <div className="col-start-2 sm:col-start-auto">
                <p className="text-sm font-medium text-elasi-text sm:text-base">
                  {getValue(
                    fullName,
                  )}
                </p>

                {!fullName ? (
                  <p className="mt-1 text-[10px] leading-5 text-elasi-muted/65">
                    هنوز برای این حساب ثبت نشده است.
                  </p>
                ) : null}
              </div>
            </div>


            {/* PHONE */}

            <div
              className="
                group
                grid
                grid-cols-[48px_1fr]
                gap-x-4
                gap-y-1
                border-b
                border-elasi-green/10
                py-5
                sm:grid-cols-[52px_150px_1fr]
                sm:items-center
              "
            >
              <div
                className="
                  row-span-2
                  flex
                  size-11
                  items-center
                  justify-center
                  rounded-full
                  border
                  border-elasi-green/10
                  bg-elasi-ivory
                  text-elasi-green
                  transition-all
                  duration-300
                  group-hover:border-elasi-gold-text
                  group-hover:text-elasi-gold-text
                  sm:row-span-1
                "
              >
                <Phone
                  size={18}
                  strokeWidth={1.5}
                  aria-hidden="true"
                />
              </div>

              <p className="self-center text-xs text-elasi-muted">
                شماره موبایل
              </p>

              <div
                className="
                  col-start-2
                  flex
                  flex-wrap
                  items-center
                  gap-2
                  sm:col-start-auto
                "
              >
                <p
                  dir="ltr"
                  className="
                    text-left
                    text-sm
                    font-medium
                    text-elasi-text
                    sm:text-base
                  "
                >
                  {user.phone_number}
                </p>

                <span
                  className="
                    inline-flex
                    items-center
                    gap-1
                    rounded-full
                    bg-elasi-green/[0.055]
                    px-2.5
                    py-1
                    text-[9px]
                    font-medium
                    text-elasi-green
                  "
                >
                  <Check
                    size={10}
                    strokeWidth={2}
                    aria-hidden="true"
                  />

                  تأیید شده
                </span>
              </div>
            </div>


            {/* EMAIL */}

            <div
              className="
                group
                grid
                grid-cols-[48px_1fr]
                gap-x-4
                gap-y-1
                py-5
                sm:grid-cols-[52px_150px_1fr]
                sm:items-center
              "
            >
              <div
                className="
                  row-span-2
                  flex
                  size-11
                  items-center
                  justify-center
                  rounded-full
                  border
                  border-elasi-green/10
                  bg-elasi-ivory
                  text-elasi-green
                  transition-all
                  duration-300
                  group-hover:border-elasi-gold-text
                  group-hover:text-elasi-gold-text
                  sm:row-span-1
                "
              >
                <Mail
                  size={18}
                  strokeWidth={1.5}
                  aria-hidden="true"
                />
              </div>

              <p className="self-center text-xs text-elasi-muted">
                ایمیل
              </p>

              <div className="col-start-2 sm:col-start-auto">
                <p className="break-all text-sm font-medium text-elasi-text sm:text-base">
                  {getValue(
                    user.email,
                  )}
                </p>

                {!user.email ? (
                  <p className="mt-1 text-[10px] leading-5 text-elasi-muted/65">
                    هنوز ایمیلی برای این حساب ثبت نشده است.
                  </p>
                ) : null}
              </div>
            </div>
          </div>


          {/* =================================================
              VERIFIED ACCESS
             ================================================= */}

          <div
            className="
              mt-7
              rounded-[1.4rem]
              border
              border-elasi-green/10
              bg-elasi-ivory/55
              p-4
              sm:p-5
            "
          >
            <div className="flex items-start gap-4">
              <div
                className="
                  flex
                  size-10
                  shrink-0
                  items-center
                  justify-center
                  rounded-full
                  bg-elasi-green
                  text-elasi-white
                "
              >
                <ShieldCheck
                  size={18}
                  strokeWidth={1.5}
                  aria-hidden="true"
                />
              </div>

              <div>
                <p className="text-sm font-medium text-elasi-green">
                  دسترسی تأیید شده
                </p>

                <p className="mt-1 text-xs leading-6 text-elasi-muted">
                  این حساب با کد یک‌بارمصرف شماره موبایل وارد شده است.
                </p>
              </div>
            </div>
          </div>


          <Link
            href="/account/orders"
            className="mt-6 flex min-h-14 items-center justify-between gap-4 rounded-[1.4rem] border border-elasi-border-strong bg-elasi-ivory px-5 text-sm font-medium text-elasi-green transition-colors hover:border-elasi-gold-text hover:bg-white"
          >
            <span>سفارش‌ها و رهگیری من</span>
            <Package size={20} strokeWidth={1.5} aria-hidden="true" />
          </Link>

          {/* =================================================
              LOGOUT
             ================================================= */}

          <div className="mt-auto pt-7 lg:pt-9">
            <div className="mb-5 flex items-center gap-3">
              <div
                aria-hidden="true"
                className="h-px flex-1 bg-elasi-green/10"
              />

              <span
                dir="ltr"
                className="
                  text-[8px]
                  tracking-[0.28em]
                  text-elasi-muted/45
                "
              >
                ELASI
              </span>

              <div
                aria-hidden="true"
                className="h-px flex-1 bg-elasi-green/10"
              />
            </div>


            <button
              type="button"
              disabled={isLoggingOut}
              onClick={() => {
                void handleLogout();
              }}
              className="
                group
                flex
                min-h-[52px]
                w-full
                items-center
                justify-between
                rounded-full
                border
                border-elasi-border-strong
                bg-transparent
                px-5
                transition-all
                duration-300
                hover:border-elasi-green
                hover:bg-elasi-green
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              <span
                className="
                  text-sm
                  font-medium
                  text-elasi-green
                  transition-colors
                  duration-300
                  group-hover:text-elasi-white
                "
              >
                {isLoggingOut
                  ? "در حال خروج..."
                  : "خروج از حساب"}
              </span>

              <span
                className="
                  flex
                  size-8
                  items-center
                  justify-center
                  rounded-full
                  bg-elasi-green/[0.055]
                  text-elasi-green
                  transition-all
                  duration-300
                  group-hover:bg-elasi-white/10
                  group-hover:text-elasi-white
                "
              >
                {isLoggingOut ? (
                  <LoaderCircle
                    size={16}
                    strokeWidth={1.5}
                    className="animate-spin"
                    aria-hidden="true"
                  />
                ) : (
                  <LogOut
                    size={16}
                    strokeWidth={1.5}
                    aria-hidden="true"
                  />
                )}
              </span>
            </button>
          </div>
        </div>
      </section>


      <footer
        className="
          mt-4
          flex
          items-center
          justify-between
          gap-6
          px-1
          text-[8px]
          tracking-[0.12em]
          text-elasi-muted/40
          sm:mt-5
        "
      >
        <span>
          فضای خصوصی شما
        </span>

        <span
          dir="ltr"
          className="tracking-[0.24em]"
        >
          ELASI / PRIVATE PROFILE
        </span>
      </footer>
    </div>
  );
}