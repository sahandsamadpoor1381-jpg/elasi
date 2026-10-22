export type OrderStatus =
  | "pending_payment"
  | "paid"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled"
  | "expired";


export type ShippingMethod =
  "postal";


export type CheckoutPayload = {
  recipient_name: string;
  phone_number: string;
  province: string;
  city: string;
  postal_code: string;
  address_line: string;
  building_number?: string;
  unit_number?: string;
  customer_note?: string;
};


export type OrderItem = {
  product_name: string;
  product_slug: string;
  sku: string;

  material:
    | "gold"
    | "silver";

  karat: number | null;
  purity: string;
  size: string;

  weight_grams:
    | string
    | null;

  unit_price_rial: number;
  quantity: number;
  line_total_rial: number;
};


export type OrderShipment = {
  carrier: string;
  tracking_code: string;
  shipped_at: string | null;
  delivered_at: string | null;
};

export type Order = {
  shipment?: OrderShipment | null;
  public_id: string;

  status: OrderStatus;

  shipping_method:
    ShippingMethod;

  subtotal_rial: number;
  shipping_fee_rial: number;
  total_rial: number;

  recipient_name: string;
  phone_number: string;

  province: string;
  city: string;
  postal_code: string;

  address_line: string;
  building_number: string;
  unit_number: string;

  customer_note: string;

  items: OrderItem[];

  reservation_expires_at:
    | string
    | null;

  paid_at:
    | string
    | null;

  created_at: string;
};


export type CheckoutApiErrorPayload = {
  code?: string;
  detail?: string;

  available?: number;
  sku?: string;

  [key: string]:
    unknown;
};