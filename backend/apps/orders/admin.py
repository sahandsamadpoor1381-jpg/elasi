from django.contrib import admin

from apps.orders.services import (
    OrderLifecycleError,
    cancel_pending_order,
    expire_pending_order,
    fulfill_order,
)

from .models import Order, OrderItem


class OrderItemInline(
    admin.TabularInline,
):
    model = OrderItem

    extra = 0

    can_delete = False

    fields = (
        "variant",
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

    readonly_fields = (
        "variant",
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

    def has_add_permission(
        self,
        request,
        obj=None,
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ) -> bool:
        return False

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
    """
    Operational view for orders.

    Payment-sensitive and inventory-sensitive fields (status,
    monetary snapshots, lifecycle timestamps) are read-only:
    they may only change through the validated domain services in
    ``apps.orders.services``. Admin actions expose the safe,
    auditable operations (cancel pending, expire due, fulfill);
    there is deliberately NO "mark as paid" action — marking paid
    requires a verified payment (or a separately approved,
    auditable offline-payment workflow) and must never be a free
    admin edit.
    """

    list_display = (
        "public_id",
        "user",
        "status",
        "total_rial",
        "shipping_method",
        "inventory_released_at",
        "inventory_consumed_at",
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

    fields = (
        "public_id",
        "user",
        "status",
        "shipping_method",
        "subtotal_rial",
        "shipping_fee_rial",
        "total_rial",
        "recipient_name",
        "phone_number",
        "province",
        "city",
        "postal_code",
        "address_line",
        "building_number",
        "unit_number",
        "customer_note",
        "reservation_expires_at",
        "inventory_released_at",
        "inventory_consumed_at",
        "paid_at",
        "cancelled_at",
        "expired_at",
        "created_at",
        "updated_at",
    )

    readonly_fields = (
        "public_id",
        "user",
        "status",
        "subtotal_rial",
        "shipping_fee_rial",
        "total_rial",
        "reservation_expires_at",
        "inventory_released_at",
        "inventory_consumed_at",
        "paid_at",
        "cancelled_at",
        "expired_at",
        "created_at",
        "updated_at",
    )

    inlines = (
        OrderItemInline,
    )

    actions = (
        "cancel_selected_pending_orders",
        "expire_selected_due_orders",
        "fulfill_selected_orders",
    )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ) -> bool:
        # Order rows are financial snapshots; deleting them would
        # destroy the audit trail (items cascade, stock movements
        # are re-pointed). Deletion is intentionally not available
        # through the admin.
        return False

    @admin.action(
        description=(
            "Cancel selected pending-payment orders "
            "(releases inventory reservations)"
        ),
    )
    def cancel_selected_pending_orders(
        self,
        request,
        queryset,
    ):
        cancelled = 0
        skipped = 0

        for order in queryset:
            try:
                cancel_pending_order(
                    order_id=order.pk,
                )
                cancelled += 1
            except OrderLifecycleError:
                skipped += 1

        self.message_user(
            request,
            (
                f"Cancelled {cancelled} order(s); "
                f"skipped {skipped} "
                "(not pending-payment)."
            ),
        )

    @admin.action(
        description=(
            "Expire selected due pending-payment orders "
            "(releases inventory reservations)"
        ),
    )
    def expire_selected_due_orders(
        self,
        request,
        queryset,
    ):
        from django.utils import timezone

        expired = 0
        skipped = 0

        now = timezone.now()

        for order in queryset:
            try:
                expire_pending_order(
                    order_id=order.pk,
                    now=now,
                )
                expired += 1
            except OrderLifecycleError:
                skipped += 1

        self.message_user(
            request,
            (
                f"Expired {expired} order(s); "
                f"skipped {skipped} "
                "(not due or not pending-payment)."
            ),
        )

    @admin.action(
        description=(
            "Fulfill selected paid/processing orders "
            "(consumes inventory reservations)"
        ),
    )
    def fulfill_selected_orders(
        self,
        request,
        queryset,
    ):
        fulfilled = 0
        skipped = 0

        for order in queryset:
            try:
                fulfill_order(
                    order_id=order.pk,
                )
                fulfilled += 1
            except OrderLifecycleError:
                skipped += 1

        self.message_user(
            request,
            (
                f"Fulfilled {fulfilled} order(s); "
                f"skipped {skipped} "
                "(not paid/processing or already fulfilled)."
            ),
        )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Read-only snapshot view. Order items are immutable financial
    records once created by checkout; they can never be added,
    edited or deleted through the admin.
    """

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
        "order",
        "variant",
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

    def has_add_permission(
        self,
        request,
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ) -> bool:
        return False

    def line_total_rial_display(
        self,
        obj: OrderItem,
    ) -> int:
        return obj.line_total_rial

    line_total_rial_display.short_description = (
        "Line total (rial)"
    )
