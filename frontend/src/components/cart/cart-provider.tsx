"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { customerMessage } from "@/lib/api-client";
import {
  cartSessionIdentity,
  resolveCartForSession,
  shouldDiscardCartToken,
} from "@/lib/cart-session";

import {
  CartApiError,
  addCartItem,
  createCart,
  deleteCartItem,
  getCart,
  updateCartItem,
} from "@/lib/cart-api";

import type {
  Cart,
} from "@/types/cart";


const CART_TOKEN_STORAGE_KEY =
  "elasi_cart_token";


type CartContextValue = {
  cart: Cart | null;

  isLoading: boolean;

  error: string | null;

  addItem: (
    variantSku: string,
    quantity?: number,
  ) => Promise<Cart>;

  updateItemQuantity: (
    itemId: number,
    quantity: number,
  ) => Promise<Cart>;

  removeItem: (
    itemId: number,
  ) => Promise<void>;

  refreshCart:
    () => Promise<void>;

  clearCart:
    () => void;
};


const CartContext =
  createContext<CartContextValue | null>(
    null,
  );


type CartProviderProps = {
  children: ReactNode;
};


export function CartProvider({
  children,
}: CartProviderProps) {
  const [
    cart,
    setCart,
  ] =
    useState<Cart | null>(
      null,
    );


  const { user, isLoading: isAuthLoading } = useAuth();
  const identity = cartSessionIdentity(user?.id ?? null);
  const authenticated = user !== null;

  // Do not expose a previously authenticated cart while a new session loads.
  const [cartIdentity, setCartIdentity] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const previousIdentity = useRef<string | null>(null);
  const loadVersion = useRef(0);
  const pendingCartCreation = useRef<Promise<Cart> | null>(null);

  const sessionCart = cartIdentity === identity && !isAuthLoading
    ? cart
    : null;
  const isLoading = isAuthLoading || cartIdentity !== identity;

  const clearStoredCart = useCallback(() => {
    // Invalidate in-flight responses (for example a late cart read after
    // checkout or logout) so they cannot restore a converted cart.
    loadVersion.current += 1;
    pendingCartCreation.current = null;
    window.localStorage.removeItem(CART_TOKEN_STORAGE_KEY);
    setCart(null);
    setCartIdentity(identity);
    setError(null);
  }, [identity]);

  const loadSessionCart = useCallback(() => {
    return resolveCartForSession(
      window.localStorage.getItem(CART_TOKEN_STORAGE_KEY),
      authenticated,
      {
        getCart,
        createCart,
        isNotFound: (reason) => reason instanceof CartApiError && reason.status === 404,
      },
    );
  }, [authenticated]);

  const refreshCart = useCallback(async () => {
    const version = loadVersion.current;
    try {
      const currentCart = await loadSessionCart();
      if (version !== loadVersion.current) return;

      if (currentCart) {
        window.localStorage.setItem(CART_TOKEN_STORAGE_KEY, currentCart.token);
      } else {
        window.localStorage.removeItem(CART_TOKEN_STORAGE_KEY);
      }
      setCart(currentCart);
      setCartIdentity(identity);
      setError(null);
    } catch (reason) {
      if (version !== loadVersion.current) return;
      setCart(null);
      setCartIdentity(identity);
      setError(customerMessage(reason));
    }
  }, [loadSessionCart, identity]);

  useEffect(() => {
    if (isAuthLoading) return;

    const priorIdentity = previousIdentity.current;
    previousIdentity.current = identity;
    const version = ++loadVersion.current;
    pendingCartCreation.current = null;
    let active = true;

    if (shouldDiscardCartToken(priorIdentity, identity)) {
      window.localStorage.removeItem(CART_TOKEN_STORAGE_KEY);
    }

    async function restoreCart() {
      try {
        const nextCart = await loadSessionCart();
        if (!active || version !== loadVersion.current) return;

        if (nextCart) {
          window.localStorage.setItem(CART_TOKEN_STORAGE_KEY, nextCart.token);
        } else {
          window.localStorage.removeItem(CART_TOKEN_STORAGE_KEY);
        }
        setCart(nextCart);
        setCartIdentity(identity);
        setError(null);
      } catch (reason) {
        if (!active || version !== loadVersion.current) return;
        setCart(null);
        setCartIdentity(identity);
        setError(customerMessage(reason));
      }
    }

    void restoreCart();
    return () => { active = false; };
  }, [identity, isAuthLoading, loadSessionCart]);


  const ensureCart = useCallback(async (): Promise<Cart> => {
    if (isLoading) {
      throw new Error("سبد خرید در حال آماده‌سازی است. دوباره تلاش کنید.");
    }

    if (sessionCart) return sessionCart;
    if (pendingCartCreation.current) return pendingCartCreation.current;

    const version = loadVersion.current;
    const operation = (async () => {
      const currentCart = await loadSessionCart();
      if (version !== loadVersion.current) {
        throw new Error("نشست کاربری تغییر کرده است. دوباره تلاش کنید.");
      }

      // Guests with no stored cart need exactly one new cart even when
      // two product actions start before the first create finishes.
      const nextCart = currentCart ?? await createCart();
      if (version !== loadVersion.current) {
        throw new Error("نشست کاربری تغییر کرده است. دوباره تلاش کنید.");
      }

      window.localStorage.setItem(CART_TOKEN_STORAGE_KEY, nextCart.token);
      setCart(nextCart);
      setCartIdentity(identity);
      setError(null);
      return nextCart;
    })();

    pendingCartCreation.current = operation;
    try {
      return await operation;
    } finally {
      if (pendingCartCreation.current === operation) {
        pendingCartCreation.current = null;
      }
    }
  }, [sessionCart, isLoading, loadSessionCart, identity]);


  const addItem =
    useCallback(
      async (
        variantSku: string,
        quantity = 1,
      ): Promise<Cart> => {
        setError(null);


        const version = loadVersion.current;
        try {
          const activeCart =
            await ensureCart();


          const updatedCart =
            await addCartItem(
              activeCart.token,
              variantSku,
              quantity,
            );


          if (version !== loadVersion.current) {
            throw new Error("نشست کاربری تغییر کرده است. دوباره تلاش کنید.");
          }
          setCart(updatedCart);
          setCartIdentity(identity);

          return updatedCart;
        } catch (
          requestError
        ) {
          const message =
            requestError instanceof
              CartApiError &&
            requestError.code ===
              "stock_exceeded"
              ? `موجودی کافی نیست. موجودی قابل فروش: ${
                  requestError.available ??
                  0
                }`
              : requestError instanceof
                    Error
                ? requestError.message
                : "افزودن محصول به سبد خرید انجام نشد.";


          if (version === loadVersion.current) {
            setError(message);
          }

          throw requestError;
        }
      },
      [
        ensureCart,
        identity,
      ],
    );


  const updateItemQuantity =
    useCallback(
      async (
        itemId: number,
        quantity: number,
      ): Promise<Cart> => {
        if (!sessionCart || isLoading) {
          throw new Error("سبد خرید در دسترس نیست.");
        }

        const version = loadVersion.current;
        setError(null);


        try {
          const updatedCart =
            await updateCartItem(
              sessionCart.token,
              itemId,
              quantity,
            );


          if (version !== loadVersion.current) {
            throw new Error("نشست کاربری تغییر کرده است. دوباره تلاش کنید.");
          }
          setCart(updatedCart);
          setCartIdentity(identity);

          return updatedCart;
        } catch (
          requestError
        ) {
          const message =
            requestError instanceof
              CartApiError &&
            requestError.code ===
              "stock_exceeded"
              ? `موجودی کافی نیست. موجودی قابل فروش: ${
                  requestError.available ??
                  0
                }`
              : requestError instanceof
                    Error
                ? requestError.message
                : "تغییر تعداد محصول انجام نشد.";


          if (version === loadVersion.current) {
            setError(message);
          }

          throw requestError;
        }
      },
      [sessionCart, isLoading, identity],
    );


  const removeItem =
    useCallback(
      async (
        itemId: number,
      ): Promise<void> => {
        if (!sessionCart || isLoading) {
          return;
        }

        const version = loadVersion.current;
        setError(null);


        try {
          await deleteCartItem(
            sessionCart.token,
            itemId,
          );


          if (version !== loadVersion.current) return;
          await refreshCart();
        } catch (
          requestError
        ) {
          const message =
            requestError instanceof
              Error
              ? requestError.message
              : "حذف محصول از سبد خرید انجام نشد.";


          if (version === loadVersion.current) {
            setError(message);
          }

          throw requestError;
        }
      },
      [sessionCart, isLoading, refreshCart],
    );


  const value =
    useMemo<CartContextValue>(
      () => ({
        cart: sessionCart,

        isLoading,

        error: isLoading ? null : error,

        addItem,

        updateItemQuantity,

        removeItem,

        refreshCart,

        clearCart:
          clearStoredCart,
      }),
      [
        sessionCart,
        isLoading,
        error,
        addItem,
        updateItemQuantity,
        removeItem,
        refreshCart,
        clearStoredCart,
      ],
    );


  return (
    <CartContext.Provider
      value={value}
    >
      {children}
    </CartContext.Provider>
  );
}


export function useCart():
  CartContextValue {
  const context =
    useContext(
      CartContext,
    );


  if (!context) {
    throw new Error(
      "useCart must be used inside CartProvider.",
    );
  }


  return context;
}