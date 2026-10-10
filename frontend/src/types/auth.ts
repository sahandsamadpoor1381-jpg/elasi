export type AuthUser = {
  id: number;
  phone_number: string;
  email: string | null;
  first_name: string;
  last_name: string;
};

export type AuthSession = {
  authenticated: true;
  user: AuthUser;
};

export type OTPRequestResult = {
  phone_number: string;
  expires_in: number;
  resend_after: number;
};

export type AuthApiErrorPayload = {
  code?: string;
  detail?: string;
  retry_after?: number;
};