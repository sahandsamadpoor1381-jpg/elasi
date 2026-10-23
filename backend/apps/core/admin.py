"""Simple, permission-controlled homepage editing in Django Admin."""

from django.contrib import admin

from .models import HomePageContent


@admin.register(HomePageContent)
class HomePageContentAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_published", "updated_at")
    readonly_fields = ("updated_at",)
    fieldsets = (
        ("انتشار", {"fields": ("is_published",)}),
        (
            "Hero",
            {"fields": (
                "hero_eyebrow", "hero_heading", "hero_description", "hero_image",
                "hero_image_alt", "hero_primary_label", "hero_secondary_label",
            )},
        ),
        ("داستان برند", {"fields": ("story_heading", "story_description")}),
        ("بخش پایانی", {"fields": ("closing_heading", "closing_description")}),
        ("زمان ویرایش", {"fields": ("updated_at",)}),
    )

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not HomePageContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
