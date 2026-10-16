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


  const [
    isLoading,
    setIsLoading,
  ] =
    useState(true);


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  const clearStoredCart =
    useCallback(() => {
      window.localStorage.removeItem(
        CART_TOKEN_STORAGE_KEY,
      );

      setCart(null);
      setError(null);
    }, []);


  const refreshCart =
    useCallback(async () => {
      const token =
        window.localStorage.getItem(
          CART_TOKEN_STORAGE_KEY,
        );


      if (!token) {
        setCart(null);
        setError(null);

        return;
      }


      try {
        const currentCart =
          await getCart(token);

        setCart(
          currentCart,
        );

        setError(null);
      } catch (
        requestError
      ) {
        if (
          requestError instanceof
            CartApiError &&
          requestError.status ===
            404
        ) {
          clearStoredCart();

          return;
        }


        setError(
          requestError instanceof
            Error
            ? requestError.message
            : "خطا در دریافت سبد خرید.",
        );
      }
    }, [
      clearStoredCart,
    ]);


  useEffect(() => {
    let isMounted =
      true;


    async function restoreCart() {
      try {
        await refreshCart();
      } finally {
        if (
          isMounted
        ) {
          setIsLoading(
            false,
          );
        }
      }
    }


    void restoreCart();


    return () => {
      isMounted =
        false;
    };
  }, [
    refreshCart,
  ]);


  const ensureCart =
    useCallback(
      async (): Promise<Cart> => {
        if (cart) {
          return cart;
        }


        const storedToken =
          window.localStorage.getItem(
            CART_TOKEN_STORAGE_KEY,
          );


        if (
          storedToken
        ) {
          try {
            const existingCart =
              await getCart(
                storedToken,
              );


            setCart(
              existingCart,
            );

            setError(
              null,
            );


            return existingCart;
          } catch (
            requestError
          ) {
            if (
              !(
                requestError instanceof
                  CartApiError &&
                requestError.status ===
                  404
              )
            ) {
              throw requestError;
            }


            clearStoredCart();
          }
        }


        const newCart =
          await createCart();


        window.localStorage.setItem(
          CART_TOKEN_STORAGE_KEY,
          newCart.token,
        );


        setCart(
          newCart,
        );

        setError(
          null,
        );


        return newCart;
      },
      [
        cart,
        clearStoredCart,
      ],
    );


  const addItem =
    useCallback(
      async (
        variantSku: string,
        quantity = 1,
      ): Promise<Cart> => {
        setError(null);


        try {
          const activeCart =
            await ensureCart();


          const updatedCart =
            await addCartItem(
              activeCart.token,
              variantSku,
              quantity,
            );


          setCart(
            updatedCart,
          );


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


          setError(
            message,
          );


          throw requestError;
        }
      },
      [
        ensureCart,
      ],
    );


  const updateItemQuantity =
    useCallback(
      async (
        itemId: number,
        quantity: number,
      ): Promise<Cart> => {
        if (!cart) {
          throw new Error(
            "Cart is not available.",
          );
        }


        setError(null);


        try {
          const updatedCart =
            await updateCartItem(
              cart.token,
              itemId,
              quantity,
            );


          setCart(
            updatedCart,
          );


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


          setError(
            message,
          );


          throw requestError;
        }
      },
      [
        cart,
      ],
    );


  const removeItem =
    useCallback(
      async (
        itemId: number,
      ): Promise<void> => {
        if (!cart) {
          return;
        }


        setError(null);


        try {
          await deleteCartItem(
            cart.token,
            itemId,
          );


          await refreshCart();
        } catch (
          requestError
        ) {
          const message =
            requestError instanceof
              Error
              ? requestError.message
              : "حذف محصول از سبد خرید انجام نشد.";


          setError(
            message,
          );


          throw requestError;
        }
      },
      [
        cart,
        refreshCart,
      ],
    );


  const value =
    useMemo<CartContextValue>(
      () => ({
        cart,

        isLoading,

        error,

        addItem,

        updateItemQuantity,

        removeItem,

        refreshCart,

        clearCart:
          clearStoredCart,
      }),
      [
        cart,
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