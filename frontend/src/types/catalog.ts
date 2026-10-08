export type Category = {
  name: string;
  slug: string;
};

export type Collection = {
  name: string;
  slug: string;
};

export type ProductImage = {
  image: string;
  alt_text: string;
  sort_order: number;
  is_primary: boolean;
};

export type ProductVariant = {
  sku: string;
  material: "gold" | "silver";
  karat: number | null;
  purity: string;
  size: string;
  weight_grams: string | null;
  price_rial: number;
  compare_at_price_rial: number | null;
  available: number;
};

export type Product = {
  name: string;
  slug: string;
  category: Category;
  collections: Collection[];
  short_description: string;
  description: string;
  gender: "women" | "men" | "unisex";
  allow_custom_size: boolean;
  is_featured: boolean;
  images: ProductImage[];
  variants: ProductVariant[];
};