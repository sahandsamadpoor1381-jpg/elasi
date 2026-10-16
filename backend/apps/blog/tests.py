"""
Blog/editorial tests.

The important guarantee: a draft - or a published article with no
publication time - is never exposed to customers, and the constraint is
enforced by the database as well as by the API.
"""

from __future__ import annotations

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Article


def build_article(
    slug: str,
    *,
    status: str = Article.Status.PUBLISHED,
    published_at=None,
    title: str | None = None,
) -> Article:
    return Article.objects.create(
        title=title or f"Article {slug}",
        slug=slug,
        excerpt="خلاصه",
        body="متن کامل مقاله",
        status=status,
        published_at=published_at,
        meta_title="عنوان سئو",
        meta_description="توضیح سئو",
    )


class ArticleModelTests(TestCase):
    def test_publishing_sets_timestamp_automatically(self):
        article = build_article(
            "auto-timestamp",
            published_at=None,
        )

        self.assertIsNotNone(article.published_at)
        self.assertTrue(article.is_published)

    def test_draft_has_no_publication_timestamp(self):
        article = build_article(
            "draft-one",
            status=Article.Status.DRAFT,
        )

        self.assertIsNone(article.published_at)
        self.assertFalse(article.is_published)

    def test_database_rejects_published_without_timestamp(self):
        """Even a direct UPDATE cannot produce an undated published row."""

        article = build_article("constraint-check")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Article.objects.filter(pk=article.pk).update(
                    published_at=None,
                )

    def test_future_publication_is_not_live_yet(self):
        article = build_article(
            "scheduled",
            published_at=timezone.now() + timedelta(days=1),
        )

        self.assertFalse(article.is_published)
        self.assertEqual(
            Article.objects.published().count(),
            0,
        )

    def test_published_queryset_filters_drafts_and_future(self):
        build_article("live")
        build_article(
            "draft",
            status=Article.Status.DRAFT,
        )
        build_article(
            "future",
            published_at=timezone.now() + timedelta(hours=1),
        )

        self.assertEqual(
            list(
                Article.objects.published().values_list(
                    "slug",
                    flat=True,
                ),
            ),
            ["live"],
        )


class ArticleAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.live = build_article(
            "live-article",
            title="مقاله منتشرشده",
        )
        cls.draft = build_article(
            "draft-article",
            status=Article.Status.DRAFT,
        )
        cls.future = build_article(
            "future-article",
            published_at=timezone.now() + timedelta(days=2),
        )

    def test_list_is_public_and_paginated(self):
        response = self.client.get(
            reverse("blog:article-list"),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = response.json()

        self.assertEqual(
            set(payload),
            {"count", "next", "previous", "results"},
        )
        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            payload["results"][0]["slug"],
            "live-article",
        )

    def test_list_never_exposes_drafts_or_scheduled_articles(self):
        response = self.client.get(
            reverse("blog:article-list"),
        )

        slugs = {
            item["slug"]
            for item in response.json()["results"]
        }

        self.assertNotIn("draft-article", slugs)
        self.assertNotIn("future-article", slugs)

    def test_list_omits_the_full_body(self):
        response = self.client.get(
            reverse("blog:article-list"),
        )

        self.assertNotIn(
            "body",
            response.json()["results"][0],
        )

    def test_detail_returns_published_article(self):
        response = self.client.get(
            reverse(
                "blog:article-detail",
                kwargs={"slug": "live-article"},
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = response.json()

        self.assertEqual(payload["title"], "مقاله منتشرشده")
        self.assertEqual(payload["body"], "متن کامل مقاله")
        self.assertIn("published_at", payload)

    def test_detail_hides_draft(self):
        response = self.client.get(
            reverse(
                "blog:article-detail",
                kwargs={"slug": "draft-article"},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_detail_hides_scheduled_article(self):
        response = self.client.get(
            reverse(
                "blog:article-detail",
                kwargs={"slug": "future-article"},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_listing_is_ordered_newest_first(self):
        """Newest publication first, drafts and scheduled items absent."""

        build_article(
            "yesterday-article",
            published_at=timezone.now() - timedelta(days=1),
        )
        build_article(
            "last-week-article",
            published_at=timezone.now() - timedelta(days=7),
        )

        response = self.client.get(
            reverse("blog:article-list"),
        )

        slugs = [
            item["slug"]
            for item in response.json()["results"]
        ]

        # live-article was published "now" in setUpTestData, so it is
        # newer than the two articles created above.
        self.assertEqual(
            slugs,
            [
                "live-article",
                "yesterday-article",
                "last-week-article",
            ],
        )

        published = [
            item["published_at"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            published,
            sorted(published, reverse=True),
        )
