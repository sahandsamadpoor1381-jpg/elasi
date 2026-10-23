from decimal import Decimal

from django.contrib import admin
from django.utils.html import format_html

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
    extra = 1
    verbose_name = "مشخصات و قیمت یک مدل محصول"
    verbose_name_plural = "مدل‌ها، سایزها و قیمت‌ها (Variant)"

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
    extra = 3
    verbose_name = "تصویر محصول"
    verbose_name_plural = "گالری تصاویر (فقط یک تصویر اصلی)"

    fields = (
        "image",
        "alt_text",
        "sort_order",
        "is_primary",
        "preview",
    )
    readonly_fields = ("preview",)

    @admin.display(description="پیش‌نمایش")
    def preview(self, obj):
        if not obj.pk or not obj.image:
            return "پس از ذخیره تصویر نمایش داده می‌شود"
        return format_html(
            '<img src="{}" alt="" style="height:64px;width:64px;object-fit:cover;border-radius:8px">',
            obj.image.url,
        )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail",
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

    fieldsets = (
        ("اطلاعات محصول", {"fields": (
            "name", "slug", "category", "collections", "gender",
            "short_description", "description",
        )}),
        ("نمایش در فروشگاه", {"fields": (
            "status", "is_featured", "allow_custom_size",
        ), "description": "ابتدا پیش‌نویس بسازید؛ پس از ثبت مدل، تصویر و موجودی واقعی، محصول را فعال کنید."}),
        ("زمان ثبت", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    inlines = (
        ProductVariantInline,
        ProductImageInline,
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("images")

    @admin.display(description="تصویر اصلی")
    def thumbnail(self, obj):
        images = list(obj.images.all())
        image = next((item for item in images if item.is_primary), None)
        if image is None and images:
            image = images[0]
        if image is None or not image.image:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="height:46px;width:46px;object-fit:cover;border-radius:8px">',
            image.image.url,
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