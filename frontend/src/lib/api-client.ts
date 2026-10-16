/**
 * Shared storefront API client.
 *
 * Responsibilities:
 *  1. Resolve the API base URL for the current runtime (see api-config).
 *  2. Keep the CSRF token fresh and attach it to unsafe requests.
 *     Django rotates the CSRF secret on login, so a cached token can go
 *     stale: a `csrf_failed` rejection triggers exactly one transparent
 *     refresh-and-retry. CSRF protection itself is never bypassed - the
 *     token is always sent and Django always validates cookie + header.
 *  3. Turn every failure into an `ApiError` carrying a stable `code`,
 *     and map it to customer-facing Persian copy. Raw technical text
 *     from the framework (for example "CSRF Failed: CSRF cookie not
 *     set.") is never shown to a customer.
 */

import { apiUrl } from "./api-config";


export type ApiErrorPayload = {
  detail?: string;
  code?: string;
  retry_after?: number;
  available?: number;
  sku?: string;
  [key: string]: unknown;
};


export type ApiErrorInit = {
  status: number;
  code?: string;
  retryAfter?: number;
  available?: number;
  sku?: string;
  payload?: ApiErrorPayload;
  isNetworkError?: boolean;
};


export class ApiError extends Error {
  status: number;
  code?: string;
  retryAfter?: number;
  available?: number;
  sku?: string;
  payload: ApiErrorPayload;
  isNetworkError: boolean;

  constructor(
    message: string,
    {
      status,
      code,
      retryAfter,
      available,
      sku,
      payload = {},
      isNetworkError = false,
    }: ApiErrorInit,
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.retryAfter = retryAfter;
    this.available = available;
    this.sku = sku;
    this.payload = payload;
    this.isNetworkError = isNetworkError;
  }
}


/* ---------------------------------------------------------
   Persian customer-facing copy
   --------------------------------------------------------- */

const CUSTOMER_MESSAGES: Record<string, string> = {
  // Session / security layer
  csrf_failed:
    "نشست امنیتی شما به‌روز شد. لطفاً یک بار دیگر تلاش کنید.",
  not_authenticated:
    "برای ادامه ابتدا وارد حساب کاربری خود شوید.",
  permission_denied:
    "شما اجازه‌ی انجام این عملیات را ندارید.",
  session_expired:
    "نشست شما به پایان رسیده است. لطفاً دوباره وارد شوید.",

  // Authentication / OTP
  invalid_phone_number:
    "شماره موبایل واردشده معتبر نیست. نمونه: ۰۹۱۲۱۲۳۴۵۶۷",
  resend_too_soon:
    "برای ارسال مجدد کد، کمی صبر کنید.",
  request_rate_limited:
    "تعداد درخواست‌ها بیش از حد مجاز است. لطفاً بعداً تلاش کنید.",
  invalid_otp:
    "کد تأیید واردشده صحیح نیست.",
  otp_expired:
    "کد تأیید منقضی شده است. لطفاً کد جدید دریافت کنید.",
  otp_locked:
    "به‌دلیل تلاش‌های ناموفق متعدد، ورود موقتاً محدود شده است. لطفاً بعداً تلاش کنید.",
  account_disabled:
    "این حساب کاربری غیرفعال است. لطفاً با پشتیبانی تماس بگیرید.",

  // Cart
  invalid_quantity:
    "تعداد واردشده معتبر نیست.",
  item_not_found:
    "این کالا دیگر در سبد خرید شما نیست.",
  variant_not_found:
    "این محصول یافت نشد.",
  stock_exceeded:
    "تعداد درخواستی بیشتر از موجودی انبار است.",
  product_inactive:
    "این محصول در حال حاضر قابل خرید نیست.",
  variant_inactive:
    "این گزینه‌ی محصول در حال حاضر قابل خرید نیست.",
  category_inactive:
    "این دسته‌بندی در حال حاضر فعال نیست.",
  cart_not_found:
    "سبد خرید شما یافت نشد. لطفاً دوباره تلاش کنید.",
  cart_owner_mismatch:
    "این سبد خرید به حساب کاربری شما تعلق ندارد.",

  // Checkout
  empty_cart:
    "سبد خرید شما خالی است.",
  order_not_found:
    "سفارش موردنظر یافت نشد.",
  order_has_no_items:
    "این سفارش هیچ کالایی ندارد.",
  invalid_order_state:
    "وضعیت سفارش اجازه‌ی این عملیات را نمی‌دهد.",

  // Transport / server
  network_error:
    "اتصال به سرور برقرار نشد. اتصال اینترنت خود را بررسی کنید و دوباره تلاش کنید.",
  timeout_error:
    "پاسخ سرور به‌طول انجامید. لطفاً دوباره تلاش کنید.",
  server_error:
    "مشکل غیرمنتظره‌ای پیش آمد. لطفاً لحظاتی دیگر دوباره تلاش کنید.",
  not_found:
    "مورد درخواستی یافت نشد.",
  parse_error:
    "اطلاعات دریافتی از سرور قابل پردازش نیست. لطفاً دوباره تلاش کنید.",
  validation_error:
    "لطفاً اطلاعات خواسته‌شده را بررسی و کامل کنید.",
};


export function customerMessageFor(
  code?: string,
): string | null {
  if (!code) {
    return null;
  }

  return CUSTOMER_MESSAGES[code] ?? null;
}


export const GENERIC_CUSTOMER_MESSAGE =
  "انجام این عملیات ناموفق بود. لطفاً دوباره تلاش کنید.";


/**
 * Technical strings that must never reach a customer. Django/DRF
 * rejections are English prose and can leak implementation details.
 */
const TECHNICAL_DETAIL_PATTERN =
  /csrf|traceback|exception|django|rest framework|sql|integrity|operational|internal server|bad request|unprocessable|<[a-z/][^>]*>/i;


export function isSafeCustomerDetail(
  detail?: string,
): boolean {
  if (!detail) {
    return false;
  }

  if (TECHNICAL_DETAIL_PATTERN.test(detail)) {
    return false;
  }

  // Customer copy for this project is Persian; anything purely ASCII
  // is treated as framework prose and replaced.
  return /[^\x00-\x7F]/.test(detail);
}


/** Single entry point for "what do we show the customer?". */
export function customerMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const mapped = customerMessageFor(error.code);

    if (mapped) {
      return mapped;
    }

    if (error.status >= 500) {
      return CUSTOMER_MESSAGES.server_error;
    }

    const detail =
      typeof error.payload.detail === "string"
        ? error.payload.detail
        : undefined;

    if (isSafeCustomerDetail(detail)) {
      return detail as string;
    }

    return GENERIC_CUSTOMER_MESSAGE;
  }

  if (error instanceof Error) {
    if (isSafeCustomerDetail(error.message)) {
      return error.message;
    }

    return GENERIC_CUSTOMER_MESSAGE;
  }

  return GENERIC_CUSTOMER_MESSAGE;
}


/* ---------------------------------------------------------
   CSRF token handling
   --------------------------------------------------------- */

let cachedCsrfToken: string | null = null;


export function clearCsrfToken(): void {
  cachedCsrfToken = null;
}


/**
 * Fetch (and cache) the CSRF token. Django sets the `csrftoken` cookie
 * on this response; because the browser talks to a single origin the
 * cookie is first-party and is attached to every later request.
 */
export async function getCsrfToken(
  options: { force?: boolean } = {},
): Promise<string> {
  if (!options.force && cachedCsrfToken) {
    return cachedCsrfToken;
  }

  let response: Response;

  try {
    response = await fetch(apiUrl("/auth/csrf/"), {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      CUSTOMER_MESSAGES.network_error,
      {
        status: 0,
        code: "network_error",
        isNetworkError: true,
      },
    );
  }

  if (!response.ok) {
    throw new ApiError(
      CUSTOMER_MESSAGES.server_error,
      {
        status: response.status,
        code: "server_error",
      },
    );
  }

  const payload = (await response.json()) as {
    csrf_token?: string;
  };

  if (!payload.csrf_token) {
    throw new ApiError(
      CUSTOMER_MESSAGES.csrf_failed,
      {
        status: response.status,
        code: "csrf_failed",
      },
    );
  }

  cachedCsrfToken = payload.csrf_token;

  return cachedCsrfToken;
}


/* ---------------------------------------------------------
   Request plumbing
   --------------------------------------------------------- */

const UNSAFE_METHODS = new Set([
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
]);


export type ApiRequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  cache?: RequestCache;
  signal?: AbortSignal;

  /**
   * Attach a CSRF token. Defaults to true for unsafe methods, which is
   * what Django requires for session-authenticated and login writes.
   */
  csrf?: boolean;

};


async function parsePayload(
  response: Response,
): Promise<ApiErrorPayload | null> {
  try {
    const payload = (await response.json()) as unknown;

    if (payload && typeof payload === "object") {
      return payload as ApiErrorPayload;
    }
  } catch {
    // Non-JSON error body (proxy or framework error page).
  }

  return null;
}


function buildApiError(
  response: Response,
  payload: ApiErrorPayload | null,
): ApiError {
  const detail =
    payload && typeof payload.detail === "string"
      ? payload.detail
      : undefined;

  const code =
    payload && typeof payload.code === "string"
      ? payload.code
      : response.status === 404
        ? "not_found"
        : response.status >= 500
          ? "server_error"
          : undefined;

  return new ApiError(
    detail ?? `Request failed with status ${response.status}`,
    {
      status: response.status,
      code,
      retryAfter:
        payload && typeof payload.retry_after === "number"
          ? payload.retry_after
          : undefined,
      available:
        payload && typeof payload.available === "number"
          ? payload.available
          : undefined,
      sku:
        payload && typeof payload.sku === "string"
          ? payload.sku
          : undefined,
      payload: payload ?? {},
    },
  );
}


/**
 * Perform an API request. Unsafe methods carry the CSRF token, and a
 * single transparent retry happens when Django reports that the token
 * was rejected (typical right after login rotates the secret).
 */
export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const needsCsrf =
    options.csrf ?? UNSAFE_METHODS.has(method);

  let csrfToken: string | null = null;

  if (needsCsrf) {
    csrfToken = await getCsrfToken();
  }

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.headers ?? {}),
  };

  if (options.body !== undefined) {
    headers["Content-Type"] ??= "application/json";
  }

  if (csrfToken) {
    headers["X-CSRFToken"] = csrfToken;
  }

  const init: RequestInit = {
    method,
    // Browser only: send the session/CSRF cookies. On the server the
    // request goes straight to Django and carries no cookies.
    ...(typeof window === "undefined"
      ? {}
      : { credentials: "include" as RequestCredentials }),
    headers,
    cache: options.cache ?? "no-store",
    signal: options.signal,
  };

  if (options.body !== undefined) {
    init.body = JSON.stringify(options.body);
  }

  let response: Response;

  try {
    response = await fetch(apiUrl(path), init);
  } catch (error) {
    /*
     * Only genuine transport failures (fetch rejects with TypeError)
     * become a customer-facing network error. Everything else must
     * propagate untouched - notably AbortError and framework signals
     * such as Next.js' DynamicServerUsageError, which the build uses
     * to mark a route dynamic. Wrapping those would turn a normal
     * "this page is dynamic" signal into a prerender failure.
     */
    if (!(error instanceof TypeError)) {
      throw error;
    }

    throw new ApiError(
      CUSTOMER_MESSAGES.network_error,
      {
        status: 0,
        code: "network_error",
        isNetworkError: true,
      },
    );
  }

  if (!response.ok) {
    const payload = await parsePayload(response);

    // Django rotated the CSRF secret (login/logout) or the browser had
    // no usable token: refresh once and retry, still fully protected.
    if (
      response.status === 403 &&
      payload?.code === "csrf_failed" &&
      needsCsrf
    ) {
      clearCsrfToken();

      const freshToken = await getCsrfToken({
        force: true,
      });

      const retryResponse = await fetch(apiUrl(path), {
        ...init,
        headers: {
          ...headers,
          "X-CSRFToken": freshToken,
        },
      });

      if (retryResponse.ok) {
        return readBody<T>(retryResponse);
      }

      throw buildApiError(
        retryResponse,
        await parsePayload(retryResponse),
      );
    }

    throw buildApiError(response, payload);
  }

  return readBody<T>(response);
}


async function readBody<T>(
  response: Response,
): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();

  if (!text) {
    return undefined as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError(
      CUSTOMER_MESSAGES.parse_error,
      {
        status: response.status,
        code: "parse_error",
      },
    );
  }
}
