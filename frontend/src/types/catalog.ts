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
  is_active: boolean;
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

/**
 * Listing shape returned by /products/ and /products/search/: the
 * product plus server-computed price and availability aggregates, so a
 * listing never has to derive them per row.
 */
export type ProductSummary = Product & {
  price_from_rial: number | null;
  price_to_rial: number | null;
  is_available: boolean;
  materials: ("gold" | "silver")[];
  primary_image: ProductImage | null;
};

/** DRF page-number pagination envelope. */
export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type CategorySummary = Category & {
  product_count: number;
};

export type CollectionSummary = Collection & {
  description: string;
  product_count: number;
};

export type ProductGender = "women" | "men" | "unisex";

export type ProductMaterial = "gold" | "silver";

export type ProductOrdering =
  | "newest"
  | "price_asc"
  | "price_desc"
  | "name"
  | "featured";
