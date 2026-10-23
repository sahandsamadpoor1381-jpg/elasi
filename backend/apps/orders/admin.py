from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .admin_dispatch import DispatchOrderForm
from .fulfillment import dispatch_order, confirm_delivery

from apps.orders.services import (
    OrderLifecycleError,
    cancel_pending_order,
    expire_pending_order,
    fulfill_order,
)

from .models import Order, OrderItem, Shipment


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
        "shipment_summary",
        "shipment_actions",
    )

    # Payment, monetary, and lifecycle data are immutable here.
    # Staff can still correct recipient, shipping method and address details.
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
        "shipment_summary",
        "shipment_actions",
    )

    inlines = (
        OrderItemInline,
    )

    actions = (
        "cancel_selected_pending_orders",
        "expire_selected_due_orders",
        "fulfill_selected_orders",
    )

    def get_urls(self):
        extra = [
            path(
                "<path:object_id>/dispatch/",
                self.admin_site.admin_view(self.dispatch_view),
                name="orders_order_dispatch",
            ),
            path(
                "<path:object_id>/confirm-delivery/",
                self.admin_site.admin_view(self.confirm_delivery_view),
                name="orders_order_confirm_delivery",
            ),
        ]
        return extra + super().get_urls()

    def _authorized_order(self, request, object_id):
        order = self.get_object(request, object_id)
        if order is None:
            raise Http404("Order not found.")
        if not self.has_change_permission(request, order):
            raise PermissionDenied
        return order

    @admin.display(description="مرسوله و رهگیری")
    def shipment_summary(self, obj):
        try:
            shipment = obj.shipment
        except Shipment.DoesNotExist:
            return "هنوز مرسوله‌ای ثبت نشده است"
        return format_html(
            "{} — {} — ارسال: {} — تحویل: {}",
            shipment.carrier,
            shipment.tracking_code,
            shipment.shipped_at.strftime("%Y-%m-%d %H:%M"),
            shipment.delivered_at.strftime("%Y-%m-%d %H:%M")
            if shipment.delivered_at else "در انتظار تأیید",
        )

    @admin.display(description="عملیات ارسال")
    def shipment_actions(self, obj):
        if obj.status in (Order.Status.PAID, Order.Status.PROCESSING):
            return format_html(
                '<a href="{}">ثبت ارسال و کد رهگیری</a>',
                reverse("admin:orders_order_dispatch", args=[obj.pk]),
            )
        if obj.status == Order.Status.SHIPPED:
            return format_html(
                '<a href="{}">تأیید تحویل مرسوله</a>',
                reverse("admin:orders_order_confirm_delivery", args=[obj.pk]),
            )
        return "در این وضعیت عملیات ارسال مجاز نیست"

    def _action_context(self, request, order, *, title, form, action_label):
        return {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": order,
            "order": order,
            "title": title,
            "form": form,
            "action_label": action_label,
        }

    def dispatch_view(self, request, object_id):
        order = self._authorized_order(request, object_id)
        form = DispatchOrderForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            try:
                dispatch_order(
                    order_id=order.pk,
                    carrier=form.cleaned_data["carrier"],
                    tracking_code=form.cleaned_data["tracking_code"],
                    recorded_by=request.user,
                )
            except OrderLifecycleError as exc:
                form.add_error(None, exc.detail)
            else:
                self.message_user(request, "ارسال مرسوله ثبت شد.", messages.SUCCESS)
                return HttpResponseRedirect(
                    reverse("admin:orders_order_change", args=[order.pk])
                )
        return TemplateResponse(
            request,
            "admin/orders/fulfillment_action.html",
            self._action_context(
                request, order, title="ثبت مرسوله",
                form=form, action_label="تأیید ارسال",
            ),
        )

    def confirm_delivery_view(self, request, object_id):
        order = self._authorized_order(request, object_id)
        form = forms.Form(request.POST or None)
        if request.method == "POST":
            try:
                confirm_delivery(order_id=order.pk)
            except OrderLifecycleError as exc:
                form.add_error(None, exc.detail)
            else:
                self.message_user(request, "تحویل مرسوله تأیید شد.", messages.SUCCESS)
                return HttpResponseRedirect(
                    reverse("admin:orders_order_change", args=[order.pk])
                )
        return TemplateResponse(
            request,
            "admin/orders/fulfillment_action.html",
            self._action_context(
                request, order, title="تأیید تحویل مرسوله",
                form=form, action_label="تأیید تحویل",
            ),
        )

    def has_add_permission(self, request) -> bool:
        # Orders must originate from authenticated, stock-validating checkout.
        # Django Admin must never manufacture pending/paid orders directly.
        return False

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


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    """Append-only merchant record: dispatch via OrderAdmin, not arbitrary rows."""
    list_display = (
        "order", "carrier", "tracking_code", "shipped_at",
        "delivered_at", "recorded_by",
    )
    search_fields = ("tracking_code", "order__public_id", "carrier")
    list_filter = ("carrier", "shipped_at")
    readonly_fields = (
        "order", "carrier", "tracking_code", "shipped_at",
        "delivered_at", "recorded_by", "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
