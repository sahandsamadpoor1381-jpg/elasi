"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  AuthApiError,
  getAuthSession,
  logoutSession,
  requestOTP,
  verifyOTP,
} from "@/lib/auth-api";

import type {
  AuthUser,
  OTPRequestResult,
} from "@/types/auth";


type AuthContextValue = {
  user: AuthUser | null;

  isLoading: boolean;
  isAuthenticated: boolean;

  error: string | null;

  requestCode: (
    phoneNumber: string,
  ) => Promise<OTPRequestResult>;

  verifyCode: (
    phoneNumber: string,
    code: string,
  ) => Promise<AuthUser>;

  logout: () => Promise<void>;

  refreshSession: () => Promise<void>;

  clearError: () => void;
};


const AuthContext =
  createContext<AuthContextValue | null>(
    null,
  );


function getAuthErrorMessage(
  error: unknown,
): string {
  if (error instanceof AuthApiError) {
    switch (error.code) {
      case "invalid_phone_number":
        return "شماره موبایل واردشده معتبر نیست.";

      case "resend_too_soon":
        return "برای ارسال مجدد کد کمی صبر کنید.";

      case "request_rate_limited":
        return "تعداد درخواست‌ها بیش از حد مجاز است. کمی بعد دوباره تلاش کنید.";

      case "invalid_otp":
        return "کد واردشده صحیح نیست.";

      case "otp_expired":
        return "کد تأیید منقضی شده است. کد جدید دریافت کنید.";

      case "otp_locked":
        return "به‌دلیل تلاش‌های ناموفق متعدد، ورود موقتاً محدود شده است.";

      case "account_disabled":
        return "این حساب کاربری غیرفعال است.";

      default:
        return error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "در ارتباط با حساب کاربری مشکلی پیش آمد.";
}


export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [user, setUser] =
    useState<AuthUser | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);


  const refreshSession =
    useCallback(async () => {
      try {
        setError(null);

        const session =
          await getAuthSession();

        setUser(
          session?.user ?? null,
        );
      } catch (requestError) {
        setUser(null);

        setError(
          getAuthErrorMessage(
            requestError,
          ),
        );
      }
    }, []);


  useEffect(() => {
    let isMounted = true;

    async function initializeAuth() {
      try {
        const session =
          await getAuthSession();

        if (!isMounted) {
          return;
        }

        setUser(
          session?.user ?? null,
        );
      } catch (requestError) {
        if (!isMounted) {
          return;
        }

        setUser(null);

        setError(
          getAuthErrorMessage(
            requestError,
          ),
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void initializeAuth();

    return () => {
      isMounted = false;
    };
  }, []);


  const requestCode =
    useCallback(
      async (
        phoneNumber: string,
      ) => {
        setError(null);

        try {
          return await requestOTP(
            phoneNumber,
          );
        } catch (requestError) {
          const message =
            getAuthErrorMessage(
              requestError,
            );

          setError(message);

          throw requestError;
        }
      },
      [],
    );


  const verifyCode =
    useCallback(
      async (
        phoneNumber: string,
        code: string,
      ) => {
        setError(null);

        try {
          const session =
            await verifyOTP(
              phoneNumber,
              code,
            );

          setUser(session.user);

          return session.user;
        } catch (requestError) {
          const message =
            getAuthErrorMessage(
              requestError,
            );

          setError(message);

          throw requestError;
        }
      },
      [],
    );


  const logout =
    useCallback(async () => {
      setError(null);

      try {
        await logoutSession();

        setUser(null);
      } catch (requestError) {
        const message =
          getAuthErrorMessage(
            requestError,
          );

        setError(message);

        throw requestError;
      }
    }, []);


  const clearError =
    useCallback(() => {
      setError(null);
    }, []);


  const value = useMemo(
    () => ({
      user,

      isLoading,

      isAuthenticated:
        user !== null,

      error,

      requestCode,
      verifyCode,
      logout,
      refreshSession,
      clearError,
    }),
    [
      user,
      isLoading,
      error,
      requestCode,
      verifyCode,
      logout,
      refreshSession,
      clearError,
    ],
  );


  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}


export function useAuth(): AuthContextValue {
  const context =
    useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}