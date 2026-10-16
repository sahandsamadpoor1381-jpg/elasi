"use client";

import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  ArrowLeft,
  Check,
  LoaderCircle,
} from "lucide-react";

import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";


type LoginFormProps = {
  redirectTo?: string;
};


type LoginStep =
  | "phone"
  | "otp";


const PERSIAN_DIGITS =
  "۰۱۲۳۴۵۶۷۸۹";

const ARABIC_DIGITS =
  "٠١٢٣٤٥٦٧٨٩";

const ASCII_DIGITS =
  "0123456789";


function normalizeDigits(
  value: string,
): string {
  const digitMap =
    new Map<string, string>();

  for (
    let index = 0;
    index < ASCII_DIGITS.length;
    index += 1
  ) {
    digitMap.set(
      PERSIAN_DIGITS[index],
      ASCII_DIGITS[index],
    );

    digitMap.set(
      ARABIC_DIGITS[index],
      ASCII_DIGITS[index],
    );
  }

  return [...value]
    .map(
      (character) =>
        digitMap.get(character)
        ?? character,
    )
    .join("");
}


function sanitizeIranPhoneInput(
  value: string,
): string {
  let normalized =
    normalizeDigits(value)
      .replace(
        /[()\s-]/g,
        "",
      )
      .replace(
        /[^\d+]/g,
        "",
      );


  const startsWithPlus =
    normalized.startsWith("+");


  normalized =
    `${startsWithPlus ? "+" : ""}${normalized.replace(/\+/g, "")}`;


  let maxLength = 11;


  if (
    normalized.startsWith("0098")
  ) {
    maxLength = 14;
  } else if (
    normalized.startsWith("+98")
  ) {
    maxLength = 13;
  } else if (
    normalized.startsWith("98")
  ) {
    maxLength = 12;
  }


  return normalized.slice(
    0,
    maxLength,
  );
}


function isValidIranianPhone(
  value: string,
): boolean {
  const normalized =
    normalizeDigits(value)
      .replace(
        /[()\s-]/g,
        "",
      );

  return /^(?:(?:\+98|0098|98|0)?9\d{9})$/.test(
    normalized,
  );
}


function normalizeOtpInput(
  value: string,
): string {
  return normalizeDigits(value)
    .replace(/\D/g, "")
    .slice(0, 6);
}


function formatCountdown(
  seconds: number,
): string {
  return new Intl.NumberFormat(
    "fa-IR",
  ).format(seconds);
}


export function LoginForm({
  redirectTo = "/account",
}: LoginFormProps) {
  const router = useRouter();

  const {
    user,
    isLoading,
    error,
    requestCode,
    verifyCode,
    clearError,
  } = useAuth();


  const [
    step,
    setStep,
  ] = useState<LoginStep>(
    "phone",
  );

  const [
    phoneNumber,
    setPhoneNumber,
  ] = useState("");

  const [
    sentPhoneNumber,
    setSentPhoneNumber,
  ] = useState<string | null>(
    null,
  );

  const [
    code,
    setCode,
  ] = useState("");

  const [
    countdown,
    setCountdown,
  ] = useState(0);

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);

  const [
    localError,
    setLocalError,
  ] = useState<string | null>(
    null,
  );


  const displayedError =
    localError ?? error;


  const canResend =
    step === "otp"
    && countdown <= 0
    && !isSubmitting;


  const verificationPhone =
    sentPhoneNumber
    ?? phoneNumber;


  useEffect(() => {
    if (
      !isLoading
      && user
    ) {
      router.replace(
        redirectTo,
      );
    }
  }, [
    isLoading,
    redirectTo,
    router,
    user,
  ]);


  useEffect(() => {
    if (
      countdown <= 0
    ) {
      return;
    }

    const timer =
      window.setInterval(
        () => {
          setCountdown(
            (current) =>
              Math.max(
                0,
                current - 1,
              ),
          );
        },
        1000,
      );

    return () => {
      window.clearInterval(
        timer,
      );
    };
  }, [
    countdown,
  ]);


  function resetErrors() {
    setLocalError(null);
    clearError();
  }


  async function handlePhoneSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    resetErrors();


    if (
      !isValidIranianPhone(
        phoneNumber,
      )
    ) {
      setLocalError(
        "شماره موبایل را به‌صورت صحیح وارد کنید.",
      );

      return;
    }


    setIsSubmitting(true);

    try {
      const result =
        await requestCode(
          phoneNumber,
        );

      setSentPhoneNumber(
        result.phone_number,
      );

      setCountdown(
        result.resend_after,
      );

      setCode("");

      setStep(
        "otp",
      );
    } catch {
      /*
       * AuthProvider converts API errors
       * into user-facing Persian messages.
       */
    } finally {
      setIsSubmitting(false);
    }
  }


  async function handleOtpSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    resetErrors();


    const normalizedCode =
      normalizeOtpInput(
        code,
      );


    if (
      normalizedCode.length
      !== 6
    ) {
      setLocalError(
        "کد تأیید باید ۶ رقم باشد.",
      );

      return;
    }


    setIsSubmitting(true);

    try {
      await verifyCode(
        verificationPhone,
        normalizedCode,
      );

      router.replace(
        redirectTo,
      );

      router.refresh();
    } catch {
      /*
       * AuthProvider exposes the
       * appropriate error message.
       */
    } finally {
      setIsSubmitting(false);
    }
  }


  async function handleResend() {
    if (
      !canResend
    ) {
      return;
    }

    resetErrors();

    setIsSubmitting(true);

    try {
      const result =
        await requestCode(
          verificationPhone,
        );

      setSentPhoneNumber(
        result.phone_number,
      );

      setCountdown(
        result.resend_after,
      );

      setCode("");
    } catch {
      /*
       * AuthProvider exposes the
       * appropriate error message.
       */
    } finally {
      setIsSubmitting(false);
    }
  }


  function handleChangePhone() {
    resetErrors();

    setStep(
      "phone",
    );

    setCode("");

    setCountdown(0);

    setSentPhoneNumber(
      null,
    );
  }


  if (
    isLoading
  ) {
    return (
      <div className="flex min-h-80 items-center justify-center">
        <LoaderCircle
          size={26}
          strokeWidth={1.5}
          className="animate-spin text-elasi-gold-text"
          aria-hidden="true"
        />

        <span className="sr-only">
          در حال بررسی وضعیت حساب
        </span>
      </div>
    );
  }


  return (
    <div className="w-full">
      <header className="mb-8 sm:mb-10">
        <div
          className="mb-5 h-px w-10 bg-elasi-gold"
          aria-hidden="true"
        />

        <p className="mb-3 text-xs font-medium tracking-[0.2em] text-elasi-gold-text">
          ELASI ACCOUNT
        </p>

        <h1 className="text-h2 text-elasi-green">
          {step === "phone"
            ? "ورود به حساب"
            : "تأیید شماره موبایل"}
        </h1>

        <p className="mt-3 max-w-md text-sm leading-7 text-elasi-muted">
          {step === "phone"
            ? (
              "برای ورود یا ساخت حساب، شماره موبایل خود را وارد کنید."
            )
            : (
              "کد شش‌رقمی ارسال‌شده را وارد کنید."
            )}
        </p>
      </header>


      {displayedError ? (
        <div
          role="alert"
          className="
            mb-6
            rounded-2xl
            border
            border-elasi-danger/20
            bg-elasi-danger/[0.05]
            px-4
            py-3
            text-sm
            leading-7
            text-elasi-danger
          "
        >
          {displayedError}
        </div>
      ) : null}


      {step === "phone" ? (
        <form
          onSubmit={
            handlePhoneSubmit
          }
          noValidate
          className="space-y-6"
        >
          <div>
            <label
              htmlFor="phone-number"
              className="mb-2 block text-sm font-medium text-elasi-text"
            >
              شماره موبایل
            </label>

            <input
              id="phone-number"
              name="phone_number"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              enterKeyHint="send"
              dir="ltr"
              maxLength={14}
              placeholder="09121234567"
              value={
                phoneNumber
              }
              disabled={
                isSubmitting
              }
              onChange={(
                event,
              ) => {
                resetErrors();

                setPhoneNumber(
                  sanitizeIranPhoneInput(
                    event.target.value,
                  ),
                );
              }}
              className="
                h-14
                w-full
                rounded-2xl
                border
                border-elasi-border-strong
                bg-white
                px-4
                text-left
                text-base
                text-elasi-text
                outline-none
                transition
                placeholder:text-elasi-muted/50
                focus:border-elasi-gold
                focus:ring-2
                focus:ring-elasi-gold/10
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            />

            <p className="mt-2 text-xs leading-6 text-elasi-muted">
              شماره را با اعداد فارسی یا انگلیسی می‌توانید وارد کنید.
            </p>
          </div>


          <button
            type="submit"
            disabled={
              isSubmitting
            }
            className="
              elasi-button
              elasi-button--primary
              h-14
              w-full
              rounded-full
              px-6
              text-sm
              text-elasi-white
              disabled:cursor-not-allowed
              disabled:opacity-60
            "
          >
            {isSubmitting ? (
              <>
                <LoaderCircle
                  size={18}
                  strokeWidth={1.7}
                  className="animate-spin"
                  aria-hidden="true"
                />

                <span>
                  در حال ارسال کد
                </span>
              </>
            ) : (
              <>
                <span>
                  دریافت کد ورود
                </span>

                <ArrowLeft
                  size={17}
                  strokeWidth={1.7}
                  aria-hidden="true"
                />
              </>
            )}
          </button>
        </form>
      ) : (
        <form
          onSubmit={
            handleOtpSubmit
          }
          noValidate
          className="space-y-6"
        >
          <div
            className="
              rounded-2xl
              border
              border-elasi-green/10
              bg-elasi-green/[0.025]
              px-4
              py-3
            "
          >
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs text-elasi-muted">
                  شماره موبایل
                </p>

                <p
                  dir="ltr"
                  className="mt-1 text-right text-sm font-medium text-elasi-green"
                >
                  {verificationPhone}
                </p>
              </div>

              <button
                type="button"
                onClick={
                  handleChangePhone
                }
                disabled={
                  isSubmitting
                }
                className="
                  text-xs
                  font-medium
                  text-elasi-gold-text
                  transition
                  hover:text-elasi-green
                  disabled:cursor-not-allowed
                  disabled:opacity-60
                "
              >
                تغییر شماره
              </button>
            </div>
          </div>


          <div>
            <label
              htmlFor="otp-code"
              className="mb-2 block text-sm font-medium text-elasi-text"
            >
              کد تأیید
            </label>

            <input
              id="otp-code"
              name="otp_code"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              enterKeyHint="done"
              dir="ltr"
              maxLength={6}
              placeholder="------"
              value={code}
              disabled={
                isSubmitting
              }
              onChange={(
                event,
              ) => {
                resetErrors();

                setCode(
                  normalizeOtpInput(
                    event.target.value,
                  ),
                );
              }}
              className="
                h-16
                w-full
                rounded-2xl
                border
                border-elasi-border-strong
                bg-white
                px-5
                text-center
                text-2xl
                font-semibold
                tracking-[0.45em]
                text-elasi-green
                outline-none
                transition
                placeholder:text-elasi-muted/35
                focus:border-elasi-gold
                focus:ring-2
                focus:ring-elasi-gold/10
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            />
          </div>


          <button
            type="submit"
            disabled={
              isSubmitting
            }
            className="
              elasi-button
              elasi-button--primary
              h-14
              w-full
              rounded-full
              px-6
              text-sm
              text-elasi-white
              disabled:cursor-not-allowed
              disabled:opacity-60
            "
          >
            {isSubmitting ? (
              <>
                <LoaderCircle
                  size={18}
                  strokeWidth={1.7}
                  className="animate-spin"
                  aria-hidden="true"
                />

                <span>
                  در حال تأیید
                </span>
              </>
            ) : (
              <>
                <span>
                  تأیید و ورود
                </span>

                <Check
                  size={17}
                  strokeWidth={1.7}
                  aria-hidden="true"
                />
              </>
            )}
          </button>


          <div
            className="flex min-h-8 items-center justify-center"
            aria-live="polite"
          >
            {countdown > 0 ? (
              <p className="text-xs text-elasi-muted">
                ارسال مجدد کد تا{" "}
                <span className="font-medium text-elasi-green">
                  {formatCountdown(
                    countdown,
                  )}
                </span>{" "}
                ثانیه دیگر
              </p>
            ) : (
              <button
                type="button"
                onClick={() => {
                  void handleResend();
                }}
                disabled={
                  !canResend
                }
                className="
                  text-xs
                  font-medium
                  text-elasi-gold-text
                  transition
                  hover:text-elasi-green
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                ارسال مجدد کد
              </button>
            )}
          </div>
        </form>
      )}
    </div>
  );
}