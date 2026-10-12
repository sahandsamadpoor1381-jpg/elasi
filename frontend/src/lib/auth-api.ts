import type {
  AuthApiErrorPayload,
  AuthSession,
  OTPRequestResult,
} from "@/types/auth";


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL;


if (!API_BASE_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL is not configured.",
  );
}


export class AuthApiError extends Error {
  status: number;
  code?: string;
  retryAfter?: number;

  constructor(
    message: string,
    {
      status,
      code,
      retryAfter,
    }: {
      status: number;
      code?: string;
      retryAfter?: number;
    },
  ) {
    super(message);

    this.name = "AuthApiError";
    this.status = status;
    this.code = code;
    this.retryAfter = retryAfter;
  }
}


async function parseError(
  response: Response,
): Promise<AuthApiError> {
  let payload: AuthApiErrorPayload = {};

  try {
    payload =
      (await response.json()) as AuthApiErrorPayload;
  } catch {
    // Response may not contain JSON.
  }

  return new AuthApiError(
    payload.detail ??
      "در ارتباط با حساب کاربری مشکلی پیش آمد.",
    {
      status: response.status,
      code: payload.code,
      retryAfter: payload.retry_after,
    },
  );
}


export async function getCsrfToken(): Promise<string> {
  const response = await fetch(
    `${API_BASE_URL}/auth/csrf/`,
    {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw await parseError(response);
  }

  const payload = (await response.json()) as {
    csrf_token: string;
  };

  return payload.csrf_token;
}


export async function requestOTP(
  phoneNumber: string,
): Promise<OTPRequestResult> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `${API_BASE_URL}/auth/otp/request/`,
    {
      method: "POST",
      credentials: "include",

      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },

      body: JSON.stringify({
        phone_number: phoneNumber,
      }),
    },
  );

  if (!response.ok) {
    throw await parseError(response);
  }

  return (await response.json()) as OTPRequestResult;
}


export async function verifyOTP(
  phoneNumber: string,
  code: string,
): Promise<AuthSession> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `${API_BASE_URL}/auth/otp/verify/`,
    {
      method: "POST",
      credentials: "include",

      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },

      body: JSON.stringify({
        phone_number: phoneNumber,
        code,
      }),
    },
  );

  if (!response.ok) {
    throw await parseError(response);
  }

  return (await response.json()) as AuthSession;
}


export async function getAuthSession(): Promise<AuthSession | null> {
  const response = await fetch(
    `${API_BASE_URL}/auth/session/`,
    {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    },
  );

  if (
    response.status === 401 ||
    response.status === 403
  ) {
    return null;
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  return (await response.json()) as AuthSession;
}


export async function logoutSession(): Promise<void> {
  /*
   * Django rotates the CSRF token after login.
   * Therefore always obtain the current token
   * immediately before logout.
   */
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `${API_BASE_URL}/auth/logout/`,
    {
      method: "POST",
      credentials: "include",

      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },

      body: JSON.stringify({}),
    },
  );

  if (!response.ok) {
    throw await parseError(response);
  }
}