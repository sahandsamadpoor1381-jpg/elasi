/**
 * Authentication API client (OTP login, session, logout).
 *
 * All requests go through the shared client, which keeps the CSRF token
 * fresh and retries once when Django reports a rotated/rejected token.
 * CSRF enforcement stays on: every unsafe request sends the token and
 * Django validates both the cookie and the header.
 */

import {
  ApiError,
  apiRequest,
  clearCsrfToken,
} from "./api-client";

import type {
  AuthSession,
  OTPRequestResult,
} from "@/types/auth";


export { getCsrfToken } from "./api-client";


export class AuthApiError extends ApiError {
  constructor(
    message: string,
    init: {
      status: number;
      code?: string;
      retryAfter?: number;
      payload?: Record<string, unknown>;
    },
  ) {
    super(message, init);

    this.name = "AuthApiError";
  }
}


export async function requestOTP(
  phoneNumber: string,
): Promise<OTPRequestResult> {
  return apiRequest<OTPRequestResult>(
    "/auth/otp/request/",
    {
      method: "POST",
      body: { phone_number: phoneNumber },
    },
  );
}


export async function verifyOTP(
  phoneNumber: string,
  code: string,
): Promise<AuthSession> {
  const session = await apiRequest<AuthSession>(
    "/auth/otp/verify/",
    {
      method: "POST",
      body: {
        phone_number: phoneNumber,
        code,
      },
    },
  );

  // Django rotates the CSRF secret on login: drop the cached token so
  // the next write fetches the fresh one.
  clearCsrfToken();

  return session;
}


export async function getAuthSession(): Promise<AuthSession | null> {
  try {
    return await apiRequest<AuthSession>(
      "/auth/session/",
      { method: "GET" },
    );
  } catch (error) {
    if (
      error instanceof ApiError &&
      (error.status === 401 || error.status === 403)
    ) {
      return null;
    }

    throw error;
  }
}


export async function logoutSession(): Promise<void> {
  await apiRequest<void>("/auth/logout/", {
    method: "POST",
    body: {},
  });

  clearCsrfToken();
}
