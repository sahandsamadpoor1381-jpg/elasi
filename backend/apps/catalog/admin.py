from decimal import Decimal

from django.contrib import admin

from .admin_forms import (
    ProductImageAdminForm,
    ProductImageInlineFormSet,
    ProductVariantAdminForm,
)

from .models import (
    Category,
    Collection,
    Product,
    ProductImage,
    ProductVariant,
)


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
    form = ProductVariantAdminForm
    extra = 0

    fields = (
        "sku",
        "material",
        "karat",
        "purity",
        "size",
        "weight_grams",
        "price_toman",
        "compare_at_price_toman",
        "is_active",
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    formset = ProductImageInlineFormSet
    extra = 0

    fields = (
        "image",
        "alt_text",
        "sort_order",
        "is_primary",
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
        ProductImageInline,
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    form = ProductVariantAdminForm

    fields = (
        "product", "sku", "material", "karat", "purity", "size",
        "weight_grams", "price_toman", "compare_at_price_toman",
        "is_active", "created_at", "updated_at",
    )

    list_display = (
        "sku",
        "product",
        "material",
        "karat",
        "size",
        "price_toman_display",
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

    @admin.display(description="قیمت (تومان)")
    def price_toman_display(self, obj):
        price = obj.price_rial
        if price % 10 == 0:
            return f"{price // 10:,}"
        return f"{Decimal(price) / Decimal(10):,.1f}"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    form = ProductImageAdminForm

    list_display = (
        "product",
        "image",
        "sort_order",
        "is_primary",
        "created_at",
    )

    list_filter = (
        "is_primary",
    )

    search_fields = (
        "product__name",
        "product__slug",
        "alt_text",
    )

    autocomplete_fields = (
        "product",
    )

    readonly_fields = (
        "created_at",
    )