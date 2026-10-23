"""Public projection: the admin's draft settings are never included."""

from rest_framework import serializers

from .models import HomePageContent


class HomePageContentSerializer(serializers.ModelSerializer):
    hero_image = serializers.SerializerMethodField()

    class Meta:
        model = HomePageContent
        fields = (
            "hero_eyebrow", "hero_heading", "hero_description", "hero_image",
            "hero_image_alt", "hero_primary_label", "hero_secondary_label",
            "story_heading", "story_description", "closing_heading", "closing_description",
        )
        read_only_fields = fields

    def get_hero_image(self, obj: HomePageContent):
        return obj.hero_image.url if obj.hero_image else None
