"use client";

import Image from "next/image";
import { useState } from "react";

import type { ProductImage } from "@/types/catalog";


type ProductGalleryProps = {
  productName: string;
  images: ProductImage[];
};


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
      <div className="flex aspect-[4/5] items-center justify-center rounded-[32px] border border-elasi-green/10 bg-white px-8 text-center">
        <p className="text-sm text-elasi-muted">
          تصویری برای این محصول ثبت نشده است.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="relative aspect-[4/5] overflow-hidden rounded-[32px] bg-white">
        <Image
          src={selectedImage.image}
          alt={
            selectedImage.alt_text ||
            productName
          }
          fill
          priority
          sizes="(max-width: 1024px) 100vw, 52vw"
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
                  className={`relative aspect-square overflow-hidden rounded-[16px] border bg-white transition ${
                    isSelected
                      ? "border-elasi-gold"
                      : "border-elasi-green/10 hover:border-elasi-green/30"
                  }`}
                >
                  <Image
                    src={image.image}
                    alt=""
                    fill
                    sizes="120px"
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