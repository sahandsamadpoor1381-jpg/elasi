"use client";

import {
  ArrowLeft,
  Check,
  LockKeyhole,
  MapPin,
  PackageCheck,
} from "lucide-react";

import Link from "next/link";

import {
  useRouter,
} from "next/navigation";

import {
  type ChangeEvent,
  type FormEvent,
  type ReactNode,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useAuth,
} from "@/components/auth/auth-provider";

import {
  AutoGrowTextarea,
} from "@/components/checkout/auto-grow-textarea";

import {
  LocationSelect,
} from "@/components/checkout/location-select";

import {
  useCart,
} from "@/components/cart/cart-provider";

import {
  getIranCitiesByProvince,
  iranProvinces,
} from "@/data/iran";

import {
  CheckoutApiError,
  checkoutCart,
} from "@/lib/checkout-api";

import type {
  CheckoutPayload,
  Order,
} from "@/types/order";


type CheckoutFormState = {
  recipient_name: string;
  phone_number: string;
  province: string;
  city: string;
  postal_code: string;
  address_line: string;
  building_number: string;
  unit_number: string;
  customer_note: string;
};


type CheckoutField =
  keyof CheckoutFormState;


type FieldLabelProps = {
  htmlFor: string;
  children: ReactNode;
  required?: boolean;
};


const initialFormState:
  CheckoutFormState = {
    recipient_name: "",
    phone_number: "",
    province: "",
    city: "",
    postal_code: "",
    address_line: "",
    building_number: "",
    unit_number: "",
    customer_note: "",
  };


function normalizeDigits(
  value: string,
): string {
  const persianDigits =
    "۰۱۲۳۴۵۶۷۸۹";

  const arabicDigits =
    "٠١٢٣٤٥٦٧٨٩";


  return value
    .replace(
      /[۰-۹]/g,
      (digit) =>
        String(
          persianDigits.indexOf(
            digit,
          ),
        ),
    )
    .replace(
      /[٠-٩]/g,
      (digit) =>
        String(
          arabicDigits.indexOf(
            digit,
          ),
        ),
    );
}


function normalizePhoneInput(
  value: string,
): string {
  let normalized =
    normalizeDigits(
      value,
    );


  normalized =
    normalized.replace(
      /[^\d+]/g,
      "",
    );


  normalized =
    normalized.replace(
      /(?!^)\+/g,
      "",
    );


  return normalized.slice(
    0,
    14,
  );
}


function normalizePostalCode(
  value: string,
): string {
  return normalizeDigits(
    value,
  )
    .replace(
      /\D/g,
      "",
    )
    .slice(
      0,
      10,
    );
}


function isValidIranPhone(
  value: string,
): boolean {
  return /^(?:(?:\+98|0098|98|0)?9\d{9})$/.test(
    normalizeDigits(
      value,
    ),
  );
}


function isValidPostalCode(
  value: string,
): boolean {
  return /^\d{10}$/.test(
    normalizeDigits(
      value,
    ),
  );
}


function formatToman(
  rial: number,
): string {
  return new Intl.NumberFormat(
    "fa-IR",
  ).format(
    Math.floor(
      rial / 10,
    ),
  );
}


function formatPersianNumber(
  value:
    | number
    | string,
): string {
  return new Intl.NumberFormat(
    "fa-IR",
  ).format(
    Number(value),
  );
}


function getCheckoutErrorMessage(
  error: unknown,
): string {
  if (
    error instanceof
      CheckoutApiError
  ) {
    switch (
      error.code
    ) {
      case "empty_cart":
        return "سبد خرید شما خالی است.";

      case "cart_not_found":
        return "سبد خرید فعال پیدا نشد. لطفاً به سبد خرید برگردید.";

      case "cart_owner_mismatch":
        return "این سبد خرید متعلق به حساب دیگری است.";

      case "stock_exceeded":
        return error.available !==
          undefined
          ? `موجودی یکی از محصولات کافی نیست. موجودی قابل فروش: ${formatPersianNumber(
              error.available,
            )}`
          : "موجودی یکی از محصولات کافی نیست.";

      case "product_inactive":
      case "variant_inactive":
      case "category_inactive":
        return "یکی از محصولات سبد در حال حاضر قابل سفارش نیست.";

      default:
        break;
    }


    if (
      error.status === 401 ||
      error.status === 403
    ) {
      return "برای ثبت سفارش ابتدا وارد حساب ELASI شوید.";
    }


    if (
      error.message &&
      error.message !==
        "Checkout request failed."
    ) {
      return error.message;
    }
  }


  if (
    error instanceof Error
  ) {
    return error.message;
  }


  return "ثبت سفارش انجام نشد. لطفاً دوباره تلاش کنید.";
}


function FieldLabel({
  htmlFor,
  children,
  required = false,
}: FieldLabelProps) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-2 block text-sm font-medium text-elasi-text"
    >
      {children}

      {required ? (
        <span
          className="mr-1 text-elasi-gold-text"
          aria-hidden="true"
        >
          *
        </span>
      ) : null}
    </label>
  );
}


export function CheckoutClient() {
  const router =
    useRouter();


  const {
    user,
    isLoading:
      isAuthLoading,
  } = useAuth();


  const {
    cart,
    isLoading:
      isCartLoading,
    clearCart,
  } = useCart();


  const [
    form,
    setForm,
  ] =
    useState<CheckoutFormState>(
      initialFormState,
    );


  const [
    hasEditedPhone,
    setHasEditedPhone,
  ] =
    useState(false);


  const [
    fieldErrors,
    setFieldErrors,
  ] =
    useState<
      Partial<
        Record<
          CheckoutField,
          string
        >
      >
    >({});


  const [
    submitError,
    setSubmitError,
  ] =
    useState<
      string | null
    >(null);


  const [
    isSubmitting,
    setIsSubmitting,
  ] =
    useState(false);


  const [
    completedOrder,
    setCompletedOrder,
  ] =
    useState<
      Order | null
    >(null);


  useEffect(() => {
    if (
      isAuthLoading
    ) {
      return;
    }


    if (!user) {
      router.replace(
        "/login?next=/checkout",
      );
    }
  }, [
    isAuthLoading,
    router,
    user,
  ]);


  const isLoading =
    isAuthLoading ||
    isCartLoading;


  const phoneNumberValue =
    hasEditedPhone
      ? form.phone_number
      : (
          user?.phone_number ??
          form.phone_number
        );


  const itemCount =
    cart?.total_quantity ??
    0;


  const subtotal =
    cart?.subtotal_rial ??
    0;


  const availableCities =
    useMemo(
      () =>
        getIranCitiesByProvince(
          form.province,
        ),
      [
        form.province,
      ],
    );


  const provinceOptions =
    useMemo(
      () =>
        iranProvinces.map(
          (
            province,
          ) => ({
            value:
              province.name,

            label:
              province.name,
          }),
        ),
      [],
    );


  const cityOptions =
    useMemo(
      () =>
        availableCities.map(
          (
            city,
          ) => ({
            value:
              city.name,

            label:
              city.name,
          }),
        ),
      [
        availableCities,
      ],
    );


  const orderSummary =
    useMemo(
      () => {
        if (!cart) {
          return [];
        }


        return cart.items.map(
          (
            item,
          ) => ({
            id:
              item.id,

            product_name:
              item.product_name,

            quantity:
              item.quantity,

            line_total_rial:
              item.line_total_rial,
          }),
        );
      },
      [
        cart,
      ],
    );


  const canSubmit =
    Boolean(
      user &&
        cart &&
        cart.items.length >
          0 &&
        !isSubmitting,
    );


  function clearFieldError(
    field:
      CheckoutField,
  ) {
    setFieldErrors(
      (
        current,
      ) => {
        if (
          !current[
            field
          ]
        ) {
          return current;
        }


        const next = {
          ...current,
        };


        delete next[
          field
        ];


        return next;
      },
    );
  }


  function updateField(
    field:
      CheckoutField,
    value: string,
  ) {
    setForm(
      (
        current,
      ) => ({
        ...current,

        [field]:
          value,
      }),
    );


    clearFieldError(
      field,
    );


    setSubmitError(
      null,
    );
  }


  function handleProvinceChange(
    province: string,
  ) {
    setForm(
      (
        current,
      ) => ({
        ...current,

        province,

        city: "",
      }),
    );


    setFieldErrors(
      (
        current,
      ) => {
        const next = {
          ...current,
        };


        delete next.province;
        delete next.city;


        return next;
      },
    );


    setSubmitError(
      null,
    );
  }


  function handleCityChange(
    city: string,
  ) {
    updateField(
      "city",
      city,
    );
  }


  function handleInputChange(
    event:
      ChangeEvent<
        | HTMLInputElement
        | HTMLTextAreaElement
      >,
  ) {
    const {
      name,
      value,
    } =
      event.target;


    const field =
      name as
        CheckoutField;


    if (
      field ===
      "phone_number"
    ) {
      setHasEditedPhone(
        true,
      );


      updateField(
        field,
        normalizePhoneInput(
          value,
        ),
      );


      return;
    }


    if (
      field ===
      "postal_code"
    ) {
      updateField(
        field,
        normalizePostalCode(
          value,
        ),
      );


      return;
    }


    updateField(
      field,
      value,
    );
  }


  function validateForm():
    boolean {
    const errors:
      Partial<
        Record<
          CheckoutField,
          string
        >
      > = {};


    if (
      !form.recipient_name.trim()
    ) {
      errors.recipient_name =
        "نام گیرنده را وارد کنید.";
    }


    if (
      !phoneNumberValue.trim()
    ) {
      errors.phone_number =
        "شماره تماس را وارد کنید.";
    } else if (
      !isValidIranPhone(
        phoneNumberValue,
      )
    ) {
      errors.phone_number =
        "شماره موبایل معتبر نیست.";
    }


    if (
      !form.province
    ) {
      errors.province =
        "استان را انتخاب کنید.";
    }


    if (
      !form.city
    ) {
      errors.city =
        "شهر را انتخاب کنید.";
    }


    if (
      !form.postal_code.trim()
    ) {
      errors.postal_code =
        "کد پستی را وارد کنید.";
    } else if (
      !isValidPostalCode(
        form.postal_code,
      )
    ) {
      errors.postal_code =
        "کد پستی باید ۱۰ رقم باشد.";
    }


    if (
      !form.address_line.trim()
    ) {
      errors.address_line =
        "آدرس کامل را وارد کنید.";
    }


    setFieldErrors(
      errors,
    );


    return (
      Object.keys(
        errors,
      ).length ===
      0
    );
  }


  async function handleSubmit(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();


    if (
      isSubmitting
    ) {
      return;
    }


    setSubmitError(
      null,
    );


    if (!user) {
      router.push(
        "/login?next=/checkout",
      );


      return;
    }


    if (
      !cart ||
      cart.items.length ===
        0
    ) {
      setSubmitError(
        "سبد خرید شما خالی است.",
      );


      return;
    }


    if (
      !validateForm()
    ) {
      return;
    }


    const payload:
      CheckoutPayload = {
      recipient_name:
        form.recipient_name.trim(),

      phone_number:
        normalizeDigits(
          phoneNumberValue,
        ),

      province:
        form.province,

      city:
        form.city,

      postal_code:
        normalizeDigits(
          form.postal_code,
        ),

      address_line:
        form.address_line.trim(),

      building_number:
        normalizeDigits(
          form.building_number.trim(),
        ),

      unit_number:
        normalizeDigits(
          form.unit_number.trim(),
        ),

      customer_note:
        form.customer_note.trim(),
    };


    setIsSubmitting(
      true,
    );


    try {
      const order =
        await checkoutCart(
          cart.token,
          payload,
        );


      setCompletedOrder(
        order,
      );


      clearCart();
    } catch (
      error
    ) {
      setSubmitError(
        getCheckoutErrorMessage(
          error,
        ),
      );
    } finally {
      setIsSubmitting(
        false,
      );
    }
  }


  if (isLoading) {
    return (
      <section className="elasi-section">
        <div className="elasi-container">
          <div className="rounded-[30px] border border-elasi-green/10 bg-white/60 px-6 py-24 text-center">
            <p className="text-label tracking-[0.18em] text-elasi-gold-text">
              SECURE CHECKOUT
            </p>

            <h1 className="mt-4 text-h3 text-elasi-green">
              تکمیل سفارش
            </h1>

            <p className="mt-3 text-body text-elasi-muted">
              در حال آماده‌سازی تکمیل سفارش...
            </p>
          </div>
        </div>
      </section>
    );
  }


  if (!user) {
    return (
      <section className="elasi-section">
        <div className="elasi-container">
          <div className="rounded-[30px] border border-elasi-green/10 bg-white px-6 py-20 text-center">
            <p className="text-body text-elasi-muted">
              در حال انتقال به صفحه ورود...
            </p>
          </div>
        </div>
      </section>
    );
  }


  if (
    completedOrder
  ) {
    return (
      <section className="elasi-section">
        <div className="elasi-container">
          <div className="mx-auto max-w-3xl overflow-hidden rounded-[36px] border border-elasi-green/10 bg-white shadow-[0_24px_70px_rgba(21,42,36,0.06)]">
            <div className="bg-elasi-green px-6 py-10 text-center sm:px-10 sm:py-14">
              <div className="mx-auto flex size-14 items-center justify-center rounded-full border border-elasi-gold/40 bg-white/5 text-elasi-gold">
                <Check
                  size={26}
                  strokeWidth={1.6}
                  aria-hidden="true"
                />
              </div>


              <p className="mt-6 text-label tracking-[0.2em] text-elasi-gold">
                ORDER CREATED
              </p>


              <h1
                className="mt-3"
                style={{
                  color:
                    "var(--elasi-white)",
                }}
              >
                سفارش شما ثبت شد
              </h1>


              <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-white/75">
                سفارش با موفقیت در ELASI ایجاد شده و
                اکنون در وضعیت «در انتظار پرداخت» قرار
                دارد.
              </p>
            </div>


            <div className="px-6 py-8 sm:px-10 sm:py-10">
              <div className="grid gap-5 rounded-[24px] bg-elasi-ivory p-5 sm:grid-cols-2">
                <div>
                  <p className="text-xs text-elasi-muted">
                    شناسه سفارش
                  </p>

                  <p
                    dir="ltr"
                    className="mt-2 break-all text-sm font-medium text-elasi-green"
                  >
                    {
                      completedOrder.public_id
                    }
                  </p>
                </div>


                <div>
                  <p className="text-xs text-elasi-muted">
                    مبلغ سفارش
                  </p>

                  <p className="mt-2 font-semibold text-elasi-green">
                    {formatToman(
                      completedOrder.total_rial,
                    )}{" "}
                    تومان
                  </p>
                </div>
              </div>


              <div
                role="status"
                className="mt-6 rounded-[20px] border border-elasi-gold/30 bg-elasi-gold/5 px-5 py-4 text-sm leading-7 text-elasi-text"
              >
                درگاه پرداخت هنوز به این مرحله متصل نشده است؛
                بنابراین هیچ پرداختی انجام نشده و سفارش فقط
                با وضعیت در انتظار پرداخت ایجاد شده است.
              </div>


              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/"
                  className="elasi-button elasi-button--primary"
                >
                  بازگشت به فروشگاه
                </Link>

                <Link
                  href="/account"
                  className="elasi-button elasi-button--secondary"
                >
                  حساب کاربری
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }


  if (
    !cart ||
    cart.items.length ===
      0
  ) {
    return (
      <section className="elasi-section">
        <div className="elasi-container">
          <div className="mx-auto max-w-2xl rounded-[32px] border border-elasi-green/10 bg-white px-6 py-16 text-center sm:px-10">
            <PackageCheck
              className="mx-auto text-elasi-gold-text"
              size={34}
              strokeWidth={1.5}
              aria-hidden="true"
            />

            <h1 className="mt-5 text-elasi-green">
              سبد خرید شما خالی است
            </h1>

            <p className="mt-4 text-body text-elasi-muted">
              برای تکمیل سفارش ابتدا محصولی را به سبد خرید
              اضافه کنید.
            </p>

            <Link
              href="/#collection"
              className="elasi-button elasi-button--primary mt-8"
            >
              مشاهده محصولات
            </Link>
          </div>
        </div>
      </section>
    );
  }


  return (
    <section className="elasi-section">
      <div className="elasi-container">
        <div className="mb-10 sm:mb-14">
          <div className="flex flex-wrap items-center gap-3 text-sm text-elasi-muted">
            <Link
              href="/cart"
              className="transition-colors hover:text-elasi-gold-text"
            >
              سبد خرید
            </Link>

            <span
              aria-hidden="true"
              className="text-elasi-gold-text/60"
            >
              /
            </span>

            <span className="text-elasi-green">
              تکمیل سفارش
            </span>
          </div>


          <p className="mt-7 text-label tracking-[0.2em] text-elasi-gold-text">
            SECURE CHECKOUT
          </p>

          <h1 className="mt-3 text-elasi-green">
            تکمیل سفارش
          </h1>

          <p className="mt-4 max-w-2xl text-body text-elasi-muted">
            اطلاعات گیرنده و آدرس ارسال را وارد کنید.
            قیمت، موجودی و مبلغ نهایی هنگام ثبت سفارش
            دوباره توسط ELASI بررسی می‌شود.
          </p>
        </div>


        <form
          onSubmit={
            handleSubmit
          }
          noValidate
          className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_390px] xl:items-start xl:gap-12"
        >
          <div className="space-y-6">
            <section className="rounded-[30px] border border-elasi-green/10 bg-white p-5 sm:p-7 lg:p-8">
              <div className="flex items-start gap-4 border-b border-elasi-green/10 pb-6">
                <div className="flex size-11 shrink-0 items-center justify-center rounded-full bg-elasi-green text-elasi-gold">
                  <MapPin
                    size={20}
                    strokeWidth={1.6}
                    aria-hidden="true"
                  />
                </div>

                <div>
                  <p className="text-label tracking-[0.15em] text-elasi-gold-text">
                    DELIVERY DETAILS
                  </p>

                  <h2 className="mt-1 text-2xl text-elasi-green">
                    اطلاعات ارسال
                  </h2>

                  <p className="mt-2 text-sm leading-7 text-elasi-muted">
                    این اطلاعات روی سفارش فعلی ذخیره می‌شود.
                  </p>
                </div>
              </div>


              <div className="mt-7 grid gap-x-5 gap-y-6 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <FieldLabel
                    htmlFor="recipient_name"
                    required
                  >
                    نام و نام خانوادگی گیرنده
                  </FieldLabel>

                  <input
                    id="recipient_name"
                    name="recipient_name"
                    type="text"
                    autoComplete="name"
                    value={
                      form.recipient_name
                    }
                    onChange={
                      handleInputChange
                    }
                    aria-invalid={
                      Boolean(
                        fieldErrors.recipient_name,
                      )
                    }
                    aria-describedby={
                      fieldErrors.recipient_name
                        ? "recipient_name-error"
                        : undefined
                    }
                    className="w-full rounded-[16px] border border-elasi-border-strong bg-elasi-ivory/50 px-4 py-3.5 text-sm text-elasi-text outline-none transition focus:border-elasi-gold-text focus:bg-white"
                  />

                  {fieldErrors.recipient_name ? (
                    <p
                      id="recipient_name-error"
                      className="mt-2 text-xs text-elasi-danger"
                    >
                      {
                        fieldErrors.recipient_name
                      }
                    </p>
                  ) : null}
                </div>


                <div className="sm:col-span-2">
                  <FieldLabel
                    htmlFor="phone_number"
                    required
                  >
                    شماره تماس گیرنده
                  </FieldLabel>

                  <input
                    id="phone_number"
                    name="phone_number"
                    type="tel"
                    inputMode="tel"
                    autoComplete="tel"
                    dir="ltr"
                    maxLength={14}
                    value={
                      phoneNumberValue
                    }
                    onChange={
                      handleInputChange
                    }
                    aria-invalid={
                      Boolean(
                        fieldErrors.phone_number,
                      )
                    }
                    aria-describedby={
                      fieldErrors.phone_number
                        ? "phone_number-error"
                        : undefined
                    }
                    className="w-full rounded-[16px] border border-elasi-border-strong bg-elasi-ivory/50 px-4 py-3.5 text-left text-sm text-elasi-text outline-none transition focus:border-elasi-gold-text focus:bg-white"
                  />

                  <p className="mt-2 text-xs leading-6 text-elasi-muted">
                    شماره حساب شما به‌صورت پیش‌فرض قرار داده
                    شده است و در صورت نیاز می‌توانید شماره
                    گیرنده را تغییر دهید.
                  </p>

                  {fieldErrors.phone_number ? (
                    <p
                      id="phone_number-error"
                      className="mt-2 text-xs text-elasi-danger"
                    >
                      {
                        fieldErrors.phone_number
                      }
                    </p>
                  ) : null}
                </div>


                <LocationSelect
                  id="province"
                  label="استان"
                  value={
                    form.province
                  }
                  options={
                    provinceOptions
                  }
                  placeholder="انتخاب استان"
                  error={
                    fieldErrors.province
                  }
                  onChange={
                    handleProvinceChange
                  }
                />


                <LocationSelect
                  id="city"
                  label="شهر"
                  value={
                    form.city
                  }
                  options={
                    cityOptions
                  }
                  placeholder={
                    form.province
                      ? "انتخاب شهر"
                      : "ابتدا استان را انتخاب کنید"
                  }
                  disabled={
                    !form.province
                  }
                  searchable
                  error={
                    fieldErrors.city
                  }
                  onChange={
                    handleCityChange
                  }
                />


                <div className="sm:col-span-2">
                  <FieldLabel
                    htmlFor="postal_code"
                    required
                  >
                    کد پستی
                  </FieldLabel>

                  <input
                    id="postal_code"
                    name="postal_code"
                    type="text"
                    inputMode="numeric"
                    autoComplete="postal-code"
                    dir="ltr"
                    maxLength={10}
                    value={
                      form.postal_code
                    }
                    onChange={
                      handleInputChange
                    }
                    aria-invalid={
                      Boolean(
                        fieldErrors.postal_code,
                      )
                    }
                    aria-describedby={
                      fieldErrors.postal_code
                        ? "postal_code-error"
                        : undefined
                    }
                    className="w-full rounded-[16px] border border-elasi-border-strong bg-elasi-ivory/50 px-4 py-3.5 text-left text-sm text-elasi-text outline-none transition focus:border-elasi-gold-text focus:bg-white"
                  />

                  {fieldErrors.postal_code ? (
                    <p
                      id="postal_code-error"
                      className="mt-2 text-xs text-elasi-danger"
                    >
                      {
                        fieldErrors.postal_code
                      }
                    </p>
                  ) : null}
                </div>


                <div className="sm:col-span-2">
                  <FieldLabel
                    htmlFor="address_line"
                    required
                  >
                    آدرس کامل
                  </FieldLabel>

                  <AutoGrowTextarea
                    id="address_line"
                    name="address_line"
                    autoComplete="street-address"
                    value={
                      form.address_line
                    }
                    minHeight={128}
                    maxHeight={320}
                    onChange={
                      handleInputChange
                    }
                    aria-invalid={
                      Boolean(
                        fieldErrors.address_line,
                      )
                    }
                    aria-describedby={
                      fieldErrors.address_line
                        ? "address_line-error"
                        : undefined
                    }
                    className="
                      w-full
                      rounded-[16px]
                      border
                      border-elasi-border-strong
                      bg-elasi-ivory/50
                      px-4
                      py-3.5
                      text-sm
                      leading-7
                      text-elasi-text
                      outline-none
                      transition
                      focus:border-elasi-gold-text
                      focus:bg-white
                    "
                  />

                  {fieldErrors.address_line ? (
                    <p
                      id="address_line-error"
                      className="mt-2 text-xs text-elasi-danger"
                    >
                      {
                        fieldErrors.address_line
                      }
                    </p>
                  ) : null}
                </div>


                <div>
                  <FieldLabel htmlFor="building_number">
                    پلاک
                  </FieldLabel>

                  <input
                    id="building_number"
                    name="building_number"
                    type="text"
                    value={
                      form.building_number
                    }
                    onChange={
                      handleInputChange
                    }
                    className="w-full rounded-[16px] border border-elasi-border-strong bg-elasi-ivory/50 px-4 py-3.5 text-sm text-elasi-text outline-none transition focus:border-elasi-gold-text focus:bg-white"
                  />
                </div>


                <div>
                  <FieldLabel htmlFor="unit_number">
                    واحد
                  </FieldLabel>

                  <input
                    id="unit_number"
                    name="unit_number"
                    type="text"
                    value={
                      form.unit_number
                    }
                    onChange={
                      handleInputChange
                    }
                    className="w-full rounded-[16px] border border-elasi-border-strong bg-elasi-ivory/50 px-4 py-3.5 text-sm text-elasi-text outline-none transition focus:border-elasi-gold-text focus:bg-white"
                  />
                </div>


                <div className="sm:col-span-2">
                  <FieldLabel htmlFor="customer_note">
                    توضیحات سفارش
                  </FieldLabel>

                  <AutoGrowTextarea
                    id="customer_note"
                    name="customer_note"
                    value={
                      form.customer_note
                    }
                    minHeight={96}
                    maxHeight={240}
                    onChange={
                      handleInputChange
                    }
                    placeholder="اختیاری"
                    className="
                      w-full
                      rounded-[16px]
                      border
                      border-elasi-border-strong
                      bg-elasi-ivory/50
                      px-4
                      py-3.5
                      text-sm
                      leading-7
                      text-elasi-text
                      outline-none
                      transition
                      placeholder:text-elasi-muted/60
                      focus:border-elasi-gold-text
                      focus:bg-white
                    "
                  />
                </div>
              </div>
            </section>


            <div className="flex items-start gap-3 rounded-[20px] border border-elasi-green/10 bg-white/60 px-5 py-4">
              <LockKeyhole
                size={18}
                strokeWidth={1.6}
                className="mt-1 shrink-0 text-elasi-gold-text"
                aria-hidden="true"
              />

              <p className="text-xs leading-7 text-elasi-muted">
                قیمت و موجودی کالا در لحظه ثبت سفارش دوباره
                روی سرور بررسی می‌شود. ثبت این فرم به معنی
                پرداخت موفق نیست.
              </p>
            </div>
          </div>


          <aside className="rounded-[30px] border border-elasi-green/10 bg-white p-6 xl:sticky xl:top-8">
            <p className="text-label tracking-[0.18em] text-elasi-gold-text">
              ORDER REVIEW
            </p>

            <h2 className="mt-2 text-2xl text-elasi-green">
              مرور سفارش
            </h2>


            <div className="mt-6 space-y-4 border-y border-elasi-green/10 py-5">
              {orderSummary.map(
                (
                  item,
                ) => (
                  <div
                    key={
                      item.id
                    }
                    className="flex items-start justify-between gap-4"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-elasi-text">
                        {
                          item.product_name
                        }
                      </p>

                      <p className="mt-1 text-xs text-elasi-muted">
                        تعداد{" "}
                        {formatPersianNumber(
                          item.quantity,
                        )}
                      </p>
                    </div>

                    <p className="shrink-0 text-sm font-medium text-elasi-green">
                      {formatToman(
                        item.line_total_rial,
                      )}{" "}
                      تومان
                    </p>
                  </div>
                ),
              )}
            </div>


            <dl className="mt-5 space-y-4">
              <div className="flex items-center justify-between gap-4">
                <dt className="text-sm text-elasi-muted">
                  تعداد کالا
                </dt>

                <dd className="text-sm font-medium text-elasi-text">
                  {formatPersianNumber(
                    itemCount,
                  )}
                </dd>
              </div>


              <div className="flex items-center justify-between gap-4">
                <dt className="text-sm text-elasi-muted">
                  جمع محصولات
                </dt>

                <dd className="text-sm font-medium text-elasi-text">
                  {formatToman(
                    subtotal,
                  )}{" "}
                  تومان
                </dd>
              </div>


              <div className="flex items-start justify-between gap-4">
                <dt className="text-sm text-elasi-muted">
                  ارسال
                </dt>

                <dd className="max-w-[190px] text-left text-xs leading-6 text-elasi-muted">
                  هزینه ارسال در نسخه فعلی هنوز نهایی نشده است.
                </dd>
              </div>
            </dl>


            <div className="mt-6 border-t border-elasi-green/10 pt-5">
              <div className="flex items-end justify-between gap-4">
                <p className="font-medium text-elasi-green">
                  مبلغ فعلی سبد
                </p>

                <p className="text-xl font-semibold text-elasi-green">
                  {formatToman(
                    subtotal,
                  )}{" "}
                  تومان
                </p>
              </div>
            </div>


            {submitError ? (
              <div
                role="alert"
                className="mt-5 rounded-[16px] border border-elasi-danger/20 bg-elasi-danger/[0.05] px-4 py-3 text-sm leading-7 text-elasi-danger"
              >
                {
                  submitError
                }
              </div>
            ) : null}


            <button
              type="submit"
              disabled={
                !canSubmit
              }
              className="elasi-button elasi-button--primary mt-6 w-full disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting
                ? "در حال ثبت سفارش..."
                : "ثبت سفارش"}
            </button>


            <Link
              href="/cart"
              className="mt-4 flex min-h-11 items-center justify-center gap-2 text-sm font-medium text-elasi-muted transition-colors hover:text-elasi-gold-text"
            >
              <ArrowLeft
                size={17}
                strokeWidth={1.6}
                aria-hidden="true"
              />

              بازگشت به سبد خرید
            </Link>
          </aside>
        </form>
      </div>
    </section>
  );
}