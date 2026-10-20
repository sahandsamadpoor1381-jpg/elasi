"use client";

import Image from "next/image";
import { useState } from "react";

import type { ProductImage } from "@/types/catalog";


type ProductGalleryProps = {
  productName: string;
  images: ProductImage[];
};


const PRODUCT_GALLERY_SIZES =
  "(max-width: 1024px) 100vw, 52vw"; // ds-allow-hardcode: Next Image sizes descriptors require concrete CSS source sizes.
const PRODUCT_THUMBNAIL_SIZES =
  "120px"; // ds-allow-hardcode: fixed thumbnail source-size hint for Next Image.


export function ProductGallery({
  productName,
  images,
}: ProductGalleryProps) {
  const sortedImages = [...images].sort(
    (firstImage, secondImage) => {
      if (
        firstImage.is_primary !==
        secondImage.is_primary
      ) {
        return firstImage.is_primary ? -1 : 1;
      }

      return (
        firstImage.sort_order -
        secondImage.sort_order
      );
    },
  );

  const [selectedIndex, setSelectedIndex] =
    useState(0);

  const selectedImage =
    sortedImages[selectedIndex];

  if (!selectedImage) {
    return (
      <div className="flex aspect-[4/5] items-center justify-center rounded-card border border-elasi-green/10 bg-white px-8 text-center">
        <p className="text-sm text-elasi-muted">
          تصویری برای این محصول ثبت نشده است.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="relative aspect-[4/5] overflow-hidden rounded-card bg-white">
        <Image
          src={selectedImage.image}
          alt={
            selectedImage.alt_text ||
            productName
          }
          fill
          priority
          sizes={PRODUCT_GALLERY_SIZES}
          className="object-cover"
        />
      </div>

      {sortedImages.length > 1 ? (
        <div
          className="mt-4 grid grid-cols-4 gap-3 sm:grid-cols-5"
          aria-label="تصاویر محصول"
        >
          {sortedImages.map(
            (image, index) => {
              const isSelected =
                index === selectedIndex;

              return (
                <button
                  key={`${image.image}-${index}`}
                  type="button"
                  onClick={() =>
                    setSelectedIndex(index)
                  }
                  aria-label={`نمایش تصویر ${
                    index + 1
                  } از ${productName}`}
                  aria-pressed={isSelected}
                  className={`relative aspect-square overflow-hidden rounded-md border bg-white transition ${
                    isSelected
                      ? "border-elasi-gold-text"
                      : "border-elasi-border-strong hover:border-elasi-gold-text"
                  }`}
                >
                  <Image
                    src={image.image}
                    alt=""
                    fill
                    sizes={PRODUCT_THUMBNAIL_SIZES}
                    className="object-cover"
                  />
                </button>
              );
            },
          )}
        </div>
      ) : null}
    </div>
  );
}