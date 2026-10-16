from django.contrib import admin
from django.utils import timezone

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Editorial management for the storefront journal."""

    list_display = (
        "title",
        "status",
        "published_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "published_at",
    )

    search_fields = (
        "title",
        "slug",
        "excerpt",
        "body",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "status",
                    "published_at",
                ),
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "excerpt",
                    "body",
                    "cover_image",
                ),
            },
        ),
        (
            "SEO",
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    actions = (
        "publish_articles",
        "unpublish_articles",
    )

    @admin.action(
        description="Publish selected articles",
    )
    def publish_articles(self, request, queryset):
        now = timezone.now()

        updated = queryset.exclude(
            status=Article.Status.PUBLISHED,
        ).update(
            status=Article.Status.PUBLISHED,
            published_at=now,
        )

        # Already-published rows keep their original publication time.
        queryset.filter(
            status=Article.Status.PUBLISHED,
            published_at__isnull=True,
        ).update(published_at=now)

        self.message_user(
            request,
            f"{updated} article(s) published.",
        )

    @admin.action(
        description="Move selected articles back to draft",
    )
    def unpublish_articles(self, request, queryset):
        updated = queryset.update(
            status=Article.Status.DRAFT,
        )

        self.message_user(
            request,
            f"{updated} article(s) moved to draft.",
        )
