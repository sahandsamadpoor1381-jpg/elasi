from rest_framework import serializers

from .models import Article


class ArticleListSerializer(serializers.ModelSerializer):
    """Listing payload: enough for a card, no full body."""

    cover_image = serializers.ImageField(
        read_only=True,
    )

    class Meta:
        model = Article
        fields = (
            "title",
            "slug",
            "excerpt",
            "cover_image",
            "published_at",
        )


class ArticleDetailSerializer(serializers.ModelSerializer):
    cover_image = serializers.ImageField(
        read_only=True,
    )

    class Meta:
        model = Article
        fields = (
            "title",
            "slug",
            "excerpt",
            "body",
            "cover_image",
            "published_at",
            "meta_title",
            "meta_description",
        )
