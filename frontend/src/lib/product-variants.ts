/**
 * PDP variant rules. The API is authoritative for prices and inventory;
 * this module only decides what the customer can select and display.
 */
import type { ProductVariant } from "@/types/catalog";

export function activeProductVariants(
  variants: ProductVariant[],
): ProductVariant[] {
  return variants.filter((variant) => variant.is_active);
}

export function defaultProductVariant(
  variants: ProductVariant[],
): ProductVariant | null {
  return (
    variants.find(
      (variant) => variant.is_active && variant.available > 0,
    ) ??
    variants.find((variant) => variant.is_active) ??
    null
  );
}

export function canBuyProductVariant(
  variant: ProductVariant | null,
): boolean {
  return Boolean(
    variant && variant.is_active && variant.available > 0,
  );
}

/** Do not display an invalid or non-discounted comparison price. */
export function validCompareAtPriceRial(
  variant: ProductVariant | null,
): number | null {
  if (!variant) {
    return null;
  }

  const comparison = variant.compare_at_price_rial;
  return comparison !== null &&
    Number.isSafeInteger(comparison) &&
    comparison > variant.price_rial
    ? comparison
    : null;
}
