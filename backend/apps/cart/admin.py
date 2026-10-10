from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = (
        "unit_price_rial_display",
        "line_total_rial_display",
        "created_at",
        "updated_at",
    )

    def unit_price_rial_display(
        self,
        obj: CartItem,
    ) -> int:
        return obj.unit_price_rial

    unit_price_rial_display.short_description = (
        "Unit price (rial)"
    )

    def line_total_rial_display(
        self,
        obj: CartItem,
    ) -> int:
        return obj.line_total_rial

    line_total_rial_display.short_description = (
        "Line total (rial)"
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "token",
        "user",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "token",
        "user__email",
        "user__phone_number",
    )

    readonly_fields = (
        "token",
        "created_at",
        "updated_at",
    )

    inlines = (
        CartItemInline,
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "cart",
        "variant",
        "quantity",
        "unit_price_rial_display",
        "line_total_rial_display",
        "updated_at",
    )

    search_fields = (
        "cart__token",
        "variant__sku",
        "variant__product__name",
    )

    autocomplete_fields = (
        "cart",
        "variant",
    )

    readonly_fields = (
        "unit_price_rial_display",
        "line_total_rial_display",
        "created_at",
        "updated_at",
    )

    def unit_price_rial_display(
        self,
        obj: CartItem,
    ) -> int:
        return obj.unit_price_rial

    unit_price_rial_display.short_description = (
        "Unit price (rial)"
    )

    def line_total_rial_display(
        self,
        obj: CartItem,
    ) -> int:
        return obj.line_total_rial

    line_total_rial_display.short_description = (
        "Line total (rial)"
    )