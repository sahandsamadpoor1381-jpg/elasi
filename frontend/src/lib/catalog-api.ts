import type { Product } from "@/types/catalog";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

function getApiBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URL is not configured.",
    );
  }

  return API_BASE_URL;
}

export async function getProducts(): Promise<Product[]> {
  const response = await fetch(
    `${getApiBaseUrl()}/products/`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch products: ${response.status}`,
    );
  }

  return response.json();
}