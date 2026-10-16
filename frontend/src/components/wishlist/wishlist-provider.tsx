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

import { useAuth } from "@/components/auth/auth-provider";
import { customerMessage } from "@/lib/api-client";
import {
  addToWishlist,
  getWishlistPage,
  removeFromWishlist,
} from "@/lib/wishlist-api";

import type { WishlistItem } from "@/types/wishlist";


type ToggleResult =
  | "added"
  | "removed"
  | "signin_required"
  | "error";


type WishlistContextValue = {
  slugs: Set<string>;
  items: WishlistItem[];
  count: number;
  isLoading: boolean;
  isAuthenticated: boolean;
  pendingSlug: string | null;
  error: string | null;
  isSaved: (productSlug: string) => boolean;
  toggle: (productSlug: string) => Promise<ToggleResult>;
  refresh: () => Promise<void>;
  clearError: () => void;
};


const WishlistContext =
  createContext<WishlistContextValue | null>(null);


const EMPTY_SLUGS = new Set<string>();
const EMPTY_ITEMS: WishlistItem[] = [];


type WishlistSnapshot = {
  slugs: Set<string>;
  items: WishlistItem[];
  count: number;
};


async function fetchWishlistSnapshot(): Promise<WishlistSnapshot> {
  const page = await getWishlistPage({ page_size: 96 });

  return {
    slugs: new Set(
      page.results.map((item) => item.product.slug),
    ),
    items: page.results,
    count: page.count,
  };
}


export function WishlistProvider({
  children,
}: {
  children: ReactNode;
}) {
  const { user, isAuthenticated } = useAuth();

  const [storedSlugs, setStoredSlugs] =
    useState<Set<string>>(EMPTY_SLUGS);
  const [storedItems, setStoredItems] =
    useState<WishlistItem[]>(EMPTY_ITEMS);
  const [storedCount, setStoredCount] = useState(0);

  const [isLoading, setIsLoading] = useState(false);
  const [pendingSlug, setPendingSlug] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const applySnapshot = useCallback(
    (snapshot: WishlistSnapshot) => {
      setStoredSlugs(snapshot.slugs);
      setStoredItems(snapshot.items);
      setStoredCount(snapshot.count);
    },
    [],
  );

  const resetSnapshot = useCallback(() => {
    setStoredSlugs(EMPTY_SLUGS);
    setStoredItems(EMPTY_ITEMS);
    setStoredCount(0);
  }, []);

  /** Manual refresh (after a toggle) — the effect below owns the initial load. */
  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      applySnapshot(await fetchWishlistSnapshot());
    } catch (requestError) {
      resetSnapshot();
      setError(customerMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }, [applySnapshot, resetSnapshot]);

  useEffect(() => {
    if (!isAuthenticated) {
      // A wishlist belongs to an account: nothing is fetched or stored
      // for guests. The exposed values are already empty in that case,
      // so no state has to be reset here.
      return;
    }

    let isActive = true;

    async function initializeWishlist() {
      setIsLoading(true);
      setError(null);

      try {
        const snapshot = await fetchWishlistSnapshot();

        if (!isActive) {
          return;
        }

        applySnapshot(snapshot);
      } catch (requestError) {
        if (!isActive) {
          return;
        }

        resetSnapshot();
        setError(customerMessage(requestError));
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void initializeWishlist();

    return () => {
      isActive = false;
    };
  }, [
    isAuthenticated,
    user?.id,
    applySnapshot,
    resetSnapshot,
  ]);

  /*
   * Guests always see an empty wishlist, derived at render time instead
   * of writing empty state from an effect (which would both fight the
   * optimistic updates and trigger a needless extra render).
   */
  const slugs = isAuthenticated ? storedSlugs : EMPTY_SLUGS;
  const items = isAuthenticated ? storedItems : EMPTY_ITEMS;
  const count = isAuthenticated ? storedCount : 0;

  const isSaved = useCallback(
    (productSlug: string) => slugs.has(productSlug),
    [slugs],
  );

  const toggle = useCallback(
    async (productSlug: string): Promise<ToggleResult> => {
      if (!isAuthenticated) {
        return "signin_required";
      }

      const wasSaved = slugs.has(productSlug);

      setPendingSlug(productSlug);
      setError(null);

      // Optimistic: the heart reacts immediately and is reverted (or
      // refetched) if the server disagrees.
      setStoredSlugs((current) => {
        const next = new Set(current);

        if (wasSaved) {
          next.delete(productSlug);
        } else {
          next.add(productSlug);
        }

        return next;
      });

      if (wasSaved) {
        setStoredItems((current) =>
          current.filter(
            (item) => item.product.slug !== productSlug,
          ),
        );
        setStoredCount((current) => Math.max(0, current - 1));
      }

      try {
        if (wasSaved) {
          await removeFromWishlist(productSlug);
        } else {
          await addToWishlist(productSlug);
        }

        if (!wasSaved) {
          // Pull the authoritative row (price, availability) so the
          // wishlist page shows real data instead of a guess.
          void load();
        }

        return wasSaved ? "removed" : "added";
      } catch (requestError) {
        // Reconcile with the server rather than reverse-guessing.
        void load();

        setError(customerMessage(requestError));

        return "error";
      } finally {
        setPendingSlug(null);
      }
    },
    [isAuthenticated, slugs, load],
  );

  const value = useMemo(
    () => ({
      slugs,
      items,
      count,
      isLoading,
      isAuthenticated,
      pendingSlug,
      error,
      isSaved,
      toggle,
      refresh: load,
      clearError: () => setError(null),
    }),
    [
      slugs,
      items,
      count,
      isLoading,
      isAuthenticated,
      pendingSlug,
      error,
      isSaved,
      toggle,
      load,
    ],
  );

  return (
    <WishlistContext.Provider value={value}>
      {children}
    </WishlistContext.Provider>
  );
}


export function useWishlist(): WishlistContextValue {
  const context = useContext(WishlistContext);

  if (!context) {
    throw new Error(
      "useWishlist must be used inside WishlistProvider.",
    );
  }

  return context;
}
