"""
Editorial content.

An article is only visible to customers once it is PUBLISHED *and* has
a publication timestamp: the model enforces that pairing with a
database constraint, and the public API filters on both. Drafts can
therefore never leak into the storefront.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils import timezone


class ArticleQuerySet(models.QuerySet):
    def published(self) -> "ArticleQuerySet":
        return self.filter(
            status=Article.Status.PUBLISHED,
            published_at__isnull=False,
            published_at__lte=timezone.now(),
        )


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(
        max_length=180,
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
    )

    excerpt = models.CharField(
        max_length=300,
        blank=True,
    )

    body = models.TextField()

    cover_image = models.ImageField(
        upload_to="blog/covers/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    meta_title = models.CharField(
        max_length=70,
        blank=True,
    )

    meta_description = models.CharField(
        max_length=160,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = (
            "-published_at",
            "-created_at",
        )

        constraints = [
            # A published article must carry a publication time: the
            # storefront sorts and filters on it, and "published with no
            # date" would silently disappear from the listing.
            models.CheckConstraint(
                condition=(
                    ~Q(status="published")
                    | Q(published_at__isnull=False)
                ),
                name="blog_published_article_has_timestamp",
            ),
        ]

    def save(self, *args, **kwargs):
        if (
            self.status == self.Status.PUBLISHED
            and self.published_at is None
        ):
            self.published_at = timezone.now()

        update_fields = kwargs.get("update_fields")

        if update_fields is not None:
            kwargs["update_fields"] = list(
                dict.fromkeys(
                    [*update_fields, "published_at"],
                ),
            )

        super().save(*args, **kwargs)

    @property
    def is_published(self) -> bool:
        return (
            self.status == self.Status.PUBLISHED
            and self.published_at is not None
            and self.published_at <= timezone.now()
        )

    def __str__(self) -> str:
        return self.title
