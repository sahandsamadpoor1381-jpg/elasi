"""
Admin protection tests.

The admin must never bypass order/inventory domain services:
status and monetary snapshots are read-only, order items are
immutable, destructive deletes are denied, there is no
"mark as paid" action, and the exposed actions go through the
validated lifecycle services.
"""

from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    Category,
    Product,
    ProductVariant,
)
from apps.inventory.models import (
    InventoryBalance,
    StockMovement,
)
from apps.inventory.admin import (
    InventoryBalanceAdmin,
    StockMovementAdmin,
)

from .admin import OrderAdmin, OrderItemAdmin, OrderItemInline
from .models import Order, OrderItem
from .services import mark_order_paid


User = get_user_model()


class AdminProtectionBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin-protector",
            email="admin@example.com",
            password="test-password",
        )

        category = Category.objects.create(
            name="Admin Rings",
            slug="admin-rings",
            sort_order=60,
        )

        product = Product.objects.create(
            name="ELASI Admin Ring",
            slug="elasi-admin-ring",
            category=category,
            status=Product.Status.ACTIVE,
        )

        cls.variant = ProductVariant.objects.create(
            product=product,
            sku="ELA-ADMIN-G18-17",
            material=ProductVariant.Material.GOLD,
            karat=18,
            size="17",
            weight_grams="3.250",
            price_rial=250000000,
        )

    def setUp(self):
        self.inventory = InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=5,
            reserved=0,
        )

        self.site = AdminSite()

        self.factory = RequestFactory()

    def build_order(
        self,
        *,
        status=Order.Status.PENDING_PAYMENT,
        expires_at=None,
        reserve: int = 1,
    ) -> Order:
        order = Order.objects.create(
            user=self.superuser,
            status=status,
            subtotal_rial=250000000,
            shipping_fee_rial=0,
            total_rial=250000000,
            recipient_name="Admin Customer",
            phone_number="+989121234567",
            province="آذربایجان غربی",
            city="ارومیه",
            postal_code="1234567890",
            address_line="Admin address",
            reservation_expires_at=expires_at,
        )

        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            product_name=self.variant.product.name,
            product_slug=self.variant.product.slug,
            sku=self.variant.sku,
            material=self.variant.material,
            karat=self.variant.karat,
            purity=self.variant.purity,
            size=self.variant.size,
            weight_grams=self.variant.weight_grams,
            unit_price_rial=self.variant.price_rial,
            quantity=1,
        )

        if reserve:
            self.inventory.refresh_from_db()
            self.inventory.reserved += reserve
            self.inventory.save(
                update_fields=("reserved", "updated_at"),
            )

        return order

    def get_request(self):
        request = self.factory.get("/")
        request.user = self.superuser
        return request


class OrderAdminProtectionTests(AdminProtectionBase):
    def test_payment_sensitive_fields_are_readonly(self):
        request = self.get_request()

        order = self.build_order()

        order_admin = OrderAdmin(Order, self.site)

        form_class = order_admin.get_form(request, order)

        for field in (
            "status",
            "subtotal_rial",
            "shipping_fee_rial",
            "total_rial",
            "user",
            "public_id",
            "paid_at",
            "reservation_expires_at",
            "inventory_released_at",
            "inventory_consumed_at",
        ):
            with self.subTest(field=field):
                self.assertNotIn(
                    field,
                    form_class.base_fields,
                )

                self.assertIn(
                    field,
                    order_admin.get_readonly_fields(
                        request,
                        order,
                    ),
                )

    def test_address_fields_remain_editable(self):
        request = self.get_request()

        order = self.build_order()

        order_admin = OrderAdmin(Order, self.site)

        form_class = order_admin.get_form(request, order)

        for field in (
            "recipient_name",
            "phone_number",
            "province",
            "city",
            "postal_code",
            "address_line",
            "shipping_method",
        ):
            with self.subTest(field=field):
                self.assertIn(
                    field,
                    form_class.base_fields,
                )

    def test_cannot_mark_paid_or_reprice_via_admin_change_view(self):
        order = self.build_order()

        self.client.force_login(self.superuser)

        url = reverse(
            "admin:orders_order_change",
            args=[order.pk],
        )

        response = self.client.post(
            url,
            {
                "shipping_method": (
                    Order.ShippingMethod.POSTAL
                ),
                "recipient_name": "Edited Customer",
                "phone_number": "+989121234567",
                "province": "آذربایجان غربی",
                "city": "ارومیه",
                "postal_code": "1234567890",
                "address_line": "Edited address",
                "building_number": "",
                "unit_number": "",
                "customer_note": "",
                # Tamper attempts — these must be ignored.
                "status": Order.Status.PAID,
                "subtotal_rial": "999",
                "shipping_fee_rial": "999",
                "total_rial": "999",
                "paid_at": "2026-01-01 00:00:00",
                # Inline formset management.
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-id": str(
                    order.items.first().pk
                ),
                "items-0-order": str(order.pk),
                "items-0-variant": str(
                    self.variant.pk
                ),
                "items-0-quantity": "99",
            },
            follow=True,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PENDING_PAYMENT,
        )

        self.assertEqual(
            order.total_rial,
            250000000,
        )

        self.assertEqual(
            order.subtotal_rial,
            250000000,
        )

        self.assertEqual(
            order.shipping_fee_rial,
            0,
        )

        self.assertIsNone(order.paid_at)

        # Address corrections still work.
        self.assertEqual(
            order.recipient_name,
            "Edited Customer",
        )

        # Order item snapshot untouched.
        item = order.items.get()

        self.assertEqual(item.quantity, 1)
        self.assertEqual(
            item.unit_price_rial,
            250000000,
        )

    def test_order_delete_is_denied(self):
        order = self.build_order()

        order_admin = OrderAdmin(Order, self.site)

        request = self.get_request()

        self.assertFalse(
            order_admin.has_delete_permission(
                request,
                order,
            ),
        )

        self.client.force_login(self.superuser)

        url = reverse(
            "admin:orders_order_delete",
            args=[order.pk],
        )

        response = self.client.get(url, follow=True)

        self.assertTrue(
            response.status_code in (403, 404)
            or b"not allowed" in response.content.lower()
            or b"Cannot delete" in response.content
        )

        self.assertTrue(
            Order.objects.filter(pk=order.pk).exists(),
        )

    def test_order_item_inline_is_immutable(self):
        inline = OrderItemInline(Order, self.site)

        request = self.get_request()

        self.assertFalse(
            inline.has_add_permission(request),
        )

        self.assertFalse(
            inline.has_delete_permission(request),
        )

        self.assertTrue(inline.can_delete is False)

        self.assertIn(
            "variant",
            inline.readonly_fields,
        )

        self.assertIn(
            "quantity",
            inline.readonly_fields,
        )

        self.assertIn(
            "unit_price_rial",
            inline.readonly_fields,
        )

    def test_order_item_admin_is_immutable(self):
        item_admin = OrderItemAdmin(OrderItem, self.site)

        request = self.get_request()

        self.assertFalse(
            item_admin.has_add_permission(request),
        )

        self.assertFalse(
            item_admin.has_delete_permission(request),
        )

        for field in (
            "order",
            "variant",
            "quantity",
            "unit_price_rial",
        ):
            with self.subTest(field=field):
                self.assertIn(
                    field,
                    item_admin.readonly_fields,
                )

    def test_no_mark_paid_action_exists(self):
        order_admin = OrderAdmin(Order, self.site)

        request = self.get_request()

        actions = order_admin.get_actions(request)

        action_names = list(actions.keys())

        self.assertNotIn("actions", action_names)

        for name in action_names:
            self.assertNotIn("paid", name.lower())

        self.assertIn(
            "cancel_selected_pending_orders",
            action_names,
        )

        self.assertIn(
            "expire_selected_due_orders",
            action_names,
        )

        self.assertIn(
            "fulfill_selected_orders",
            action_names,
        )

    def test_fulfill_action_consumes_via_service(self):
        order = self.build_order(
            status=Order.Status.PENDING_PAYMENT,
        )

        mark_order_paid(order_id=order.pk)

        self.client.force_login(self.superuser)

        url = reverse(
            "admin:orders_order_changelist",
        )

        response = self.client.post(
            url,
            {
                "action": "fulfill_selected_orders",
                "_selected_action": [str(order.pk)],
            },
            follow=True,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertIsNotNone(
            order.inventory_consumed_at,
        )

        self.assertEqual(self.inventory.on_hand, 4)
        self.assertEqual(self.inventory.reserved, 0)

        self.assertTrue(
            StockMovement.objects.filter(
                order=order,
                reason=StockMovement.Reason.FULFILLMENT,
            ).exists(),
        )

    def test_cancel_action_releases_via_service(self):
        order = self.build_order()

        self.client.force_login(self.superuser)

        url = reverse(
            "admin:orders_order_changelist",
        )

        self.client.post(
            url,
            {
                "action": "cancel_selected_pending_orders",
                "_selected_action": [str(order.pk)],
            },
            follow=True,
        )

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.CANCELLED,
        )

        self.assertIsNotNone(
            order.inventory_released_at,
        )

        self.assertEqual(self.inventory.reserved, 0)

    def test_expire_action_expires_due_orders_via_service(self):
        order = self.build_order(
            expires_at=(
                timezone.now()
                - timedelta(minutes=1)
            ),
        )

        self.client.force_login(self.superuser)

        url = reverse(
            "admin:orders_order_changelist",
        )

        self.client.post(
            url,
            {
                "action": "expire_selected_due_orders",
                "_selected_action": [str(order.pk)],
            },
            follow=True,
        )

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.EXPIRED,
        )

        self.assertIsNotNone(
            order.inventory_released_at,
        )

        self.assertEqual(self.inventory.reserved, 0)

    def test_fulfill_action_skips_pending_orders(self):
        order = self.build_order()

        self.client.force_login(self.superuser)

        url = reverse(
            "admin:orders_order_changelist",
        )

        self.client.post(
            url,
            {
                "action": "fulfill_selected_orders",
                "_selected_action": [str(order.pk)],
            },
            follow=True,
        )

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertIsNone(
            order.inventory_consumed_at,
        )

        self.assertEqual(self.inventory.on_hand, 5)
        self.assertEqual(self.inventory.reserved, 1)


class InventoryAdminProtectionTests(AdminProtectionBase):
    def test_reserved_is_readonly_in_admin(self):
        inventory_admin = InventoryBalanceAdmin(
            InventoryBalance,
            self.site,
        )

        self.assertIn(
            "reserved",
            inventory_admin.readonly_fields,
        )

    def test_stock_movement_admin_is_fully_readonly(self):
        movement_admin = StockMovementAdmin(
            StockMovement,
            self.site,
        )

        request = self.get_request()

        self.assertFalse(
            movement_admin.has_add_permission(request),
        )

        self.assertFalse(
            movement_admin.has_change_permission(request),
        )

        self.assertFalse(
            movement_admin.has_delete_permission(request),
        )

    def test_on_hand_adjustment_is_audited(self):
        inventory_admin = InventoryBalanceAdmin(
            InventoryBalance,
            self.site,
        )

        request = self.get_request()

        self.inventory.on_hand = 8

        inventory_admin.save_model(
            request,
            self.inventory,
            form=None,
            change=True,
        )

        movement = StockMovement.objects.get(
            variant=self.variant,
            reason=StockMovement.Reason.ADJUSTMENT,
        )

        self.assertEqual(movement.on_hand_delta, 3)
        self.assertEqual(movement.reserved_delta, 0)
        self.assertEqual(movement.quantity, 3)
        self.assertIsNone(movement.order)

    def test_no_adjustment_movement_when_unchanged(self):
        inventory_admin = InventoryBalanceAdmin(
            InventoryBalance,
            self.site,
        )

        request = self.get_request()

        inventory_admin.save_model(
            request,
            self.inventory,
            form=None,
            change=True,
        )

        self.assertFalse(
            StockMovement.objects.filter(
                reason=StockMovement.Reason.ADJUSTMENT,
            ).exists(),
        )
