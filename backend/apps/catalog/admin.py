from django.contrib import admin

from .models import Category, Collection, Product, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
        "sort_order",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0

    fields = (
        "sku",
        "material",
        "karat",
        "purity",
        "size",
        "weight_grams",
        "price_rial",
        "compare_at_price_rial",
        "is_active",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "gender",
        "status",
        "is_featured",
        "allow_custom_size",
        "updated_at",
    )

    list_filter = (
        "status",
        "gender",
        "category",
        "is_featured",
        "allow_custom_size",
    )

    search_fields = (
        "name",
        "slug",
        "short_description",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    filter_horizontal = (
        "collections",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = (
        ProductVariantInline,
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "product",
        "material",
        "karat",
        "size",
        "price_rial",
        "is_active",
    )

    list_filter = (
        "material",
        "karat",
        "is_active",
    )

    search_fields = (
        "sku",
        "product__name",
        "product__slug",
    )

    autocomplete_fields = (
        "product",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )