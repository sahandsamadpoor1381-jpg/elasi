from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(
    admin.TabularInline,
):
    model = OrderItem

    extra = 0

    readonly_fields = (
        "product_name",
        "product_slug",
        "sku",
        "material",
        "karat",
        "purity",
        "size",
        "weight_grams",
        "unit_price_rial",
        "quantity",
        "line_total_rial_display",
        "created_at",
    )

    def line_total_rial_display(
        self,
        obj: OrderItem,
    ) -> int:
        return obj.line_total_rial

    line_total_rial_display.short_description = (
        "Line total (rial)"
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "user",
        "status",
        "total_rial",
        "shipping_method",
        "created_at",
    )

    list_filter = (
        "status",
        "shipping_method",
        "created_at",
    )

    search_fields = (
        "public_id",
        "user__email",
        "user__phone_number",
        "recipient_name",
        "phone_number",
        "postal_code",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    inlines = (
        OrderItemInline,
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product_name",
        "sku",
        "quantity",
        "unit_price_rial",
        "line_total_rial_display",
    )

    search_fields = (
        "order__public_id",
        "product_name",
        "sku",
    )

    readonly_fields = (
        "line_total_rial_display",
        "created_at",
    )

    autocomplete_fields = (
        "order",
        "variant",
    )

    def line_total_rial_display(
        self,
        obj: OrderItem,
    ) -> int:
        return obj.line_total_rial

    line_total_rial_display.short_description = (
        "Line total (rial)"
    )