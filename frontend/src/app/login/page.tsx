import type { Metadata } from "next";

import { LoginForm } from "@/components/auth/login-form";


export const metadata: Metadata = {
  title: "ورود به حساب",
  description:
    "ورود یا ساخت حساب کاربری ELASI با شماره موبایل.",
};


type LoginPageProps = {
  searchParams: Promise<{
    next?: string | string[];
  }>;
};


function getSafeRedirect(
  value: string | string[] | undefined,
): string {
  const requestedPath =
    Array.isArray(value)
      ? value[0]
      : value;

  if (
    !requestedPath ||
    !requestedPath.startsWith("/") ||
    requestedPath.startsWith("//")
  ) {
    return "/account";
  }

  return requestedPath;
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
    <main className="overflow-hidden bg-elasi-ivory">
      <section className="mx-auto w-full max-w-[1440px]">

        {/* =====================================================
            MOBILE + TABLET
           ===================================================== */}

        <div className="lg:hidden">

          {/* Brand stage */}

          <div
            className="
              relative
              h-[290px]
              overflow-hidden
              bg-elasi-green
              px-5
              pt-7
              text-elasi-white
              sm:h-[320px]
              sm:px-8
              sm:pt-9
            "
          >
            {/* Decorative jewelry orbit */}

            <div
              aria-hidden="true"
              className="
                absolute
                -left-[76px]
                -top-[76px]
                size-[220px]
                rounded-full
                border
                border-elasi-white/10
                sm:-left-[60px]
                sm:-top-[100px]
                sm:size-[300px]
              "
            />

            <div
              aria-hidden="true"
              className="
                absolute
                -left-[30px]
                -top-[30px]
                size-[130px]
                rounded-full
                border
                border-elasi-gold/40
                sm:left-[10px]
                sm:-top-[40px]
                sm:size-[180px]
              "
            />

            <div
              aria-hidden="true"
              className="
                absolute
                left-[21px]
                top-[21px]
                size-7
                rounded-full
                border
                border-elasi-gold/55
                sm:left-[81px]
                sm:top-[31px]
                sm:size-10
              "
            />


            {/* Fine editorial guide */}

            <div
              aria-hidden="true"
              className="
                absolute
                left-[38%]
                top-0
                h-full
                w-px
                bg-gradient-to-b
                from-transparent
                via-elasi-white/[0.055]
                to-transparent
              "
            />


            {/* Metadata */}

            <div
              dir="ltr"
              className="
                relative
                z-10
                mx-auto
                flex
                max-w-[720px]
                items-start
                justify-between
              "
            >
              <div>
                <p className="text-[10px] font-medium tracking-[0.3em] text-elasi-gold">
                  ELASI
                </p>

                <p className="mt-1.5 text-[8px] tracking-[0.24em] text-elasi-white/45">
                  PRIVATE ACCESS
                </p>
              </div>

              <p className="text-[8px] tracking-[0.25em] text-elasi-white/35">
                01 / ACCOUNT
              </p>
            </div>


            {/* Statement */}

            <div
              className="
                absolute
                bottom-[70px]
                right-5
                z-10
                max-w-[310px]
                sm:bottom-[80px]
                sm:right-8
                sm:max-w-[430px]
              "
            >
              <p className="text-[10px] font-medium tracking-[0.16em] text-elasi-gold">
                فضای شخصی ELASI
              </p>

              <h2
                style={{
                  color: "var(--elasi-white)",
                }}
                className="
                  mt-2
                  text-[1.45rem]
                  font-semibold
                  leading-[1.55]
                  sm:text-[1.85rem]
                "
              >
                ورود، آغاز تجربه شخصی شماست.
              </h2>

              <div className="mt-4 flex items-center gap-2">
                <span
                  aria-hidden="true"
                  className="h-px w-11 bg-elasi-gold"
                />

                <span
                  aria-hidden="true"
                  className="size-1 rounded-full bg-elasi-gold"
                />
              </div>
            </div>
          </div>


          {/* Floating form */}

          <div
            className="
              relative
              z-20
              -mt-14
              px-3
              pb-4
              sm:-mt-16
              sm:px-6
              sm:pb-6
            "
          >
            <div
              className="
                mx-auto
                w-full
                max-w-[660px]
                overflow-hidden
                rounded-[1.75rem]
                border
                border-elasi-green/10
                bg-white
                shadow-[0_24px_70px_rgba(21,42,36,0.10)]
                sm:rounded-[2rem]
              "
            >
              <div className="p-6 sm:p-9">
                <LoginForm
                  redirectTo={
                    redirectTo
                  }
                headingLevel="h2"
                />
              </div>
            </div>


            <div
              dir="ltr"
              className="
                mx-auto
                mt-3
                flex
                max-w-[660px]
                items-center
                justify-between
                px-2
              "
            >
              <span className="text-[8px] tracking-[0.22em] text-elasi-muted/40">
                ELASI / ACCOUNT
              </span>

              <span className="text-[8px] tracking-[0.12em] text-elasi-muted/35">
                PRIVATE EXPERIENCE
              </span>
            </div>
          </div>
        </div>


        {/* =====================================================
            DESKTOP
           ===================================================== */}

        <div
          dir="ltr"
          className="
            hidden
            min-h-[calc(100svh-132px)]
            grid-cols-[1.03fr_0.97fr]
            lg:grid
          "
        >
          {/* ===================================================
              GREEN EDITORIAL PANEL
             =================================================== */}

          <div
            dir="rtl"
            className="
              relative
              overflow-hidden
              bg-elasi-green
              px-12
              py-12
              text-elasi-white
              xl:px-16
              xl:py-14
            "
          >
            {/* Orbit system */}

            <div
              aria-hidden="true"
              className="
                absolute
                left-[70px]
                top-[70px]
                size-[280px]
                rounded-full
                border
                border-elasi-white/10
                xl:left-[90px]
                xl:top-[82px]
                xl:size-[330px]
              "
            />

            <div
              aria-hidden="true"
              className="
                absolute
                left-[125px]
                top-[125px]
                size-[170px]
                rounded-full
                border
                border-elasi-gold/30
                xl:left-[158px]
                xl:top-[150px]
                xl:size-[195px]
              "
            />

            <div
              aria-hidden="true"
              className="
                absolute
                left-[184px]
                top-[184px]
                size-[52px]
                rounded-full
                border
                border-elasi-gold/45
                xl:left-[225px]
                xl:top-[218px]
                xl:size-[60px]
              "
            />


            {/* Editorial guide */}

            <div
              aria-hidden="true"
              className="
                absolute
                bottom-0
                left-[51%]
                top-0
                w-px
                bg-gradient-to-b
                from-transparent
                via-elasi-white/[0.05]
                to-transparent
              "
            />


            <div className="relative z-10 flex h-full min-h-[610px] flex-col justify-between">

              {/* Panel metadata */}

              <div
                dir="ltr"
                className="flex items-start justify-between"
              >
                <div>
                  <p className="text-[10px] font-medium tracking-[0.32em] text-elasi-gold">
                    ELASI
                  </p>

                  <p className="mt-2 text-[8px] tracking-[0.25em] text-elasi-white/40">
                    PRIVATE ACCESS
                  </p>
                </div>

                <span className="text-[8px] tracking-[0.25em] text-elasi-white/35">
                  01 / ACCOUNT
                </span>
              </div>


              {/* Statement */}

              <div className="max-w-[560px] pb-16 xl:pb-20">
                <p className="text-[11px] font-medium tracking-[0.18em] text-elasi-gold">
                  حساب شما،
                </p>

                <h2
                  style={{
                    color: "var(--elasi-white)",
                  }}
                  className="
                    mt-3
                    text-[2.4rem]
                    font-semibold
                    leading-[1.55]
                    xl:text-[2.75rem]
                  "
                >
                  مسیر ساده‌تر خرید
                  <br />
                  در ELASI.
                </h2>

                <p className="mt-4 max-w-[430px] text-sm leading-8 text-elasi-white/60">
                  فضای شخصی شما برای تجربه‌ای دقیق‌تر،
                  سریع‌تر و متناسب با شما.
                </p>

                <div className="mt-8 flex items-center gap-3">
                  <span
                    aria-hidden="true"
                    className="h-px w-16 bg-elasi-gold"
                  />

                  <span
                    aria-hidden="true"
                    className="size-1 rounded-full bg-elasi-gold"
                  />
                </div>
              </div>
            </div>
          </div>


          {/* ===================================================
              FORM SIDE
             =================================================== */}

          <div
            dir="rtl"
            className="
              relative
              flex
              items-center
              justify-center
              bg-elasi-ivory
              px-8
              py-12
              xl:px-14
            "
          >
            <div
              className="
                relative
                w-full
                max-w-[500px]
                -translate-x-4
                overflow-hidden
                rounded-[2rem]
                border
                border-elasi-green/10
                bg-white
                p-9
                shadow-[0_22px_65px_rgba(21,42,36,0.075)]
                xl:-translate-x-6
                xl:p-11
              "
            >
              <LoginForm
                redirectTo={
                  redirectTo
                }
              />
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}