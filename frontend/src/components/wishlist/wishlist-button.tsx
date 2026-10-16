"use client";

import { Heart, LoaderCircle } from "lucide-react";

import { usePathname, useRouter } from "next/navigation";
import { useState, type MouseEvent } from "react";

import { useWishlist } from "@/components/wishlist/wishlist-provider";


type WishlistButtonProps = {
  productSlug: string;
  productName: string;
  variant?: "icon" | "full";
  className?: string;
};


/**
 * Save/remove a product.
 *
 * Guests are routed to sign-in with a `next` back to the current page:
 * a wishlist belongs to an account, so the button explains itself
 * instead of failing silently. Inside a product-card link, the click is
 * kept from navigating.
 */
export function WishlistButton({
  productSlug,
  productName,
  variant = "icon",
  className = "",
}: WishlistButtonProps) {
  const { isSaved, toggle, pendingSlug, isAuthenticated } =
    useWishlist();

  const router = useRouter();
  const pathname = usePathname();

  const [message, setMessage] = useState<string | null>(null);

  const saved = isSaved(productSlug);
  const isPending = pendingSlug === productSlug;

  const label = saved
    ? `حذف «${productName}» از علاقه‌مندی‌ها`
    : `افزودن «${productName}» به علاقه‌مندی‌ها`;

  async function handleClick(
    event: MouseEvent<HTMLButtonElement>,
  ) {
    event.preventDefault();
    event.stopPropagation();

    setMessage(null);

    const result = await toggle(productSlug);

    if (result === "signin_required") {
      router.push(
        `/login?next=${encodeURIComponent(pathname)}`,
      );

      return;
    }

    if (result === "added") {
      setMessage("به علاقه‌مندی‌ها اضافه شد");
    } else if (result === "removed") {
      setMessage("از علاقه‌مندی‌ها حذف شد");
    } else {
      setMessage("انجام این عملیات ممکن نشد");
    }
  }

  const icon = isPending ? (
    <LoaderCircle
      size={18}
      strokeWidth={1.9}
      aria-hidden="true"
      className="animate-spin"
    />
  ) : (
    <Heart
      size={18}
      strokeWidth={1.9}
      aria-hidden="true"
      fill={saved ? "currentColor" : "none"}
    />
  );

  if (variant === "full") {
    return (
      <div className={className}>
        <button
          type="button"
          onClick={handleClick}
          aria-pressed={saved}
          aria-label={label}
          title={label}
          className={`flex min-h-12 w-full items-center justify-center gap-2 rounded-full border px-6 text-sm font-medium transition-colors ${
            saved
              ? "border-elasi-gold bg-elasi-gold/10 text-elasi-green"
              : "border-elasi-border-strong text-elasi-green hover:border-elasi-gold hover:text-elasi-gold-text"
          }`}
        >
          {icon}

          {saved ? "ذخیره‌شده در علاقه‌مندی‌ها" : "افزودن به علاقه‌مندی‌ها"}
        </button>

        <span
          aria-live="polite"
          className="mt-2 block min-h-5 text-caption text-elasi-muted"
        >
          {message ??
            (isAuthenticated
              ? ""
              : "برای ذخیره‌ی علاقه‌مندی‌ها ابتدا وارد شوید.")}
        </span>
      </div>
    );
  }

  return (
    <div className={className}>
      <button
        type="button"
        onClick={handleClick}
        aria-pressed={saved}
        aria-label={label}
        title={label}
        className={`flex size-10 items-center justify-center rounded-full border backdrop-blur transition-colors ${
          saved
            ? "border-elasi-gold bg-elasi-ivory/90 text-elasi-gold-text"
            : "border-elasi-green/12 bg-elasi-ivory/85 text-elasi-green hover:border-elasi-gold hover:text-elasi-gold-text"
        }`}
      >
        {icon}
      </button>

      <span aria-live="polite" className="sr-only">
        {message ?? ""}
      </span>
    </div>
  );
}
