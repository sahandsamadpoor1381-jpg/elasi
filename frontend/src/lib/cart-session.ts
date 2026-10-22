import type { Cart } from "../types/cart";

/** Identity key is only used to prevent account carts crossing sessions in UI. */
export function cartSessionIdentity(userId: number | null): string {
  return userId === null ? "guest" : `user:${userId}`;
}

export function shouldDiscardCartToken(
  previousIdentity: string | null,
  nextIdentity: string,
): boolean {
  // A guest cart must survive OTP login so it can be claimed by the API.
  // An account-bound token must NEVER remain in this browser after logout
  // or when a different account signs in.
  return previousIdentity !== null &&
    previousIdentity !== "guest" &&
    previousIdentity !== nextIdentity;
}

type CartSessionApi = {
  getCart: (token: string) => Promise<Cart>;
  createCart: () => Promise<Cart>;
  isNotFound: (error: unknown) => boolean;
};

/**
 * Recover a guest cart, claim it on sign-in, or load the account cart.
 * A missing/converted token is recoverable. Other failures must propagate
 * so network errors are never misreported as an empty cart.
 */
export async function resolveCartForSession(
  storedToken: string | null,
  authenticated: boolean,
  api: CartSessionApi,
): Promise<Cart | null> {
  if (storedToken) {
    try {
      return await api.getCart(storedToken);
    } catch (error) {
      if (!api.isNotFound(error)) {
        throw error;
      }
    }
  }

  return authenticated ? api.createCart() : null;
}
