export type CartItem = {
  id: number;
  product_name: string;
  product_slug: string;
  image: string | null;
  sku: string;
  material: "gold" | "silver";
  karat: number | null;
  size: string;
  quantity: number;
  available: number;
  unit_price_rial: number;
  line_total_rial: number;
};

export type Cart = {
  token: string;
  status: "active" | "converted" | "abandoned";
  items: CartItem[];
  item_count: number;
  total_quantity: number;
  subtotal_rial: number;
  created_at: string;
  updated_at: string;
};

export type CartApiErrorPayload = {
  code?: string;
  detail?: string;
  available?: number;
};