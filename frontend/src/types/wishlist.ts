import type { ProductSummary } from "./catalog";


export type WishlistItem = {
  created_at: string;
  is_purchasable: boolean;
  product: ProductSummary;
};
