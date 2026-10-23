"""Read-only merchant visibility into customer-owned cart state.

All cart mutations must use the cart API/services. Editing these rows in
Django Admin bypasses ownership checks and cart lifecycle rules.
"""

from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    can_delete = False
    fields = (
        "variant", "quantity", "unit_price_rial_display",
        "line_total_rial_display", "created_at", "updated_at",
    )
    readonly_fields = fields

    @admin.display(description="قیمت واحد (ریال)")
    def unit_price_rial_display(self, obj):
        return obj.unit_price_rial if obj.pk else "—"

    @admin.display(description="جمع ردیف (ریال)")
    def line_total_rial_display(self, obj):
        return obj.line_total_rial if obj.pk else "—"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Inspect customer carts; never create or alter them manually."""

    list_display = ("token", "user", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("token", "user__email", "user__phone_number")
    readonly_fields = ("token", "user", "status", "created_at", "updated_at")
    inlines = (CartItemInline,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Cart lines are customer-owned and are managed only by cart services."""

    list_display = (
        "cart", "variant", "quantity", "unit_price_rial_display",
        "line_total_rial_display", "updated_at",
    )
    search_fields = ("cart__token", "variant__sku", "variant__product__name")
    readonly_fields = (
        "cart", "variant", "quantity", "unit_price_rial_display",
        "line_total_rial_display", "created_at", "updated_at",
    )

    @admin.display(description="قیمت واحد (ریال)")
    def unit_price_rial_display(self, obj):
        return obj.unit_price_rial

    @admin.display(description="جمع ردیف (ریال)")
    def line_total_rial_display(self, obj):
        return obj.line_total_rial

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
