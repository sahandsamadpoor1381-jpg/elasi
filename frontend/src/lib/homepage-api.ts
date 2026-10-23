/** Public, published-only homepage content from Django Admin. */
import { ApiError, apiRequest } from "./api-client";

export type HomePageContent = {
  hero_eyebrow: string;
  hero_heading: string;
  hero_description: string;
  hero_image: string | null;
  hero_image_alt: string;
  hero_primary_label: string;
  hero_secondary_label: string;
  story_heading: string;
  story_description: string;
  closing_heading: string;
  closing_description: string;
};

export async function getHomePageContent(): Promise<HomePageContent | null> {
  try {
    // Django returns 204 when no homepage content is published.
    // Normalize the empty response to null for the static fallback UI.
    return (await apiRequest<HomePageContent | null>("/homepage/", {
      method: "GET",
    })) ?? null;
  } catch (error) {
    // During a staggered rollout, the previous API version lacks this route.
    // Preserve the existing homepage until the Django service is upgraded.
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
