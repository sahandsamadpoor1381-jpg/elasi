export type ArticleSummary = {
  title: string;
  slug: string;
  excerpt: string;
  cover_image: string | null;
  published_at: string;
};

export type Article = ArticleSummary & {
  body: string;
  meta_title: string;
  meta_description: string;
};
