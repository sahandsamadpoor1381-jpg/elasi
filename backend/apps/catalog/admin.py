from decimal import Decimal

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
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


def _variant_inventory_link(variant):
    """Navigation only: stock changes must go through audited Inventory Admin."""
    if not variant.pk:
        return "ابتدا مدل و محصول را ذخیره کنید"

    try:
        balance = variant.inventory
    except ObjectDoesNotExist:
        url = reverse("admin:inventory_inventorybalance_add")
        return format_html(
            '<a href="{}?variant={}">ثبت موجودی</a>', url, variant.pk,
        )

    url = reverse(
        "admin:inventory_inventorybalance_change", args=(balance.pk,),
    )
    return format_html(
        '<a href="{}">{} قابل فروش / {} رزرو</a>',
        url, balance.available, balance.reserved,
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


class ProductVariantInline(admin.StackedInline):
    model = ProductVariant
    form = ProductVariantAdminForm
    extra = 1
    verbose_name = "مشخصات و قیمت یک مدل محصول"
    verbose_name_plural = "مدل‌ها، سایزها و قیمت‌ها (Variant)"

    # Present one variant per readable card; a 10-column tabular inline
    # is unusable in RTL and hides the inventory shortcut off-screen.
    fieldsets = ((None, {"fields": (
        ("sku", "material", "karat"),
        ("purity", "size", "weight_grams"),
        ("price_toman", "compare_at_price_toman"),
        ("is_active", "inventory_shortcut"),
    )}),)
    readonly_fields = ("inventory_shortcut",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("inventory")

    @admin.display(description="موجودی و رزرو")
    def inventory_shortcut(self, obj):
        return _variant_inventory_link(obj)


class ProductImageInline(admin.StackedInline):
    model = ProductImage
    formset = ProductImageInlineFormSet
    extra = 3
    verbose_name = "تصویر محصول"
    verbose_name_plural = "گالری تصاویر (فقط یک تصویر اصلی)"

    fieldsets = ((None, {"fields": (
        ("image", "preview"),
        ("alt_text", "sort_order", "is_primary"),
    )}),)
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
        "stock_summary",
        "gender",
        "status",
        "is_featured",
        "allow_custom_size",
        "updated_at",
    )

    list_select_related = ("category",)

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

    # The old two-pane filter_horizontal widget consumed half the page in
    # RTL; searchable multi-select uses the existing CollectionAdmin lookup.
    autocomplete_fields = ("collections",)

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
        return super().get_queryset(request).prefetch_related(
            "images", "variants__inventory",
        )

    @admin.display(description="مدل / موجودی قابل فروش")
    def stock_summary(self, obj):
        variants = list(obj.variants.all())
        available = 0
        for variant in variants:
            if not variant.is_active:
                continue
            try:
                available += max(0, variant.inventory.available)
            except ObjectDoesNotExist:
                pass
        return f"{len(variants)} مدل | {available} موجود"

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
        "inventory_shortcut",
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "inventory")

    @admin.display(description="موجودی و رزرو")
    def inventory_shortcut(self, obj):
        return _variant_inventory_link(obj)

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