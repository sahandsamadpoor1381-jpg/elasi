"""ELASI fulfillment guarantees: shipping, customer visibility, admin workflow."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.inventory.models import InventoryBalance, StockMovement

from .fulfillment import confirm_delivery, dispatch_order
from .models import Order, Shipment
from .services import OrderLifecycleError, mark_order_paid
from .tests_fulfillment import build_catalog, build_pending_order


User = get_user_model()


class ShipmentLifecycleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(
            username="delivery-customer", email="delivery-customer@example.com",
            password="test-pass-123"
        )
        cls.other_customer = User.objects.create_user(
            username="other-delivery-customer",
            email="other-delivery-customer@example.com", password="test-pass-123"
        )
        cls.staff = User.objects.create_superuser(
            username="delivery-admin", email="delivery-admin@example.com",
            password="test-pass-123",
        )
        cls.variant = build_catalog(sku="ELA-DLV-G18-17")

    def setUp(self):
        self.inventory = InventoryBalance.objects.create(
            variant=self.variant, on_hand=5, reserved=0,
        )

    def make_order(self, *, paid=True, quantity=2):
        order = build_pending_order(
            user=self.customer, variant=self.variant, quantity=quantity,
        )
        if paid:
            mark_order_paid(order_id=order.pk)
        return order

    def test_dispatch_consumes_stock_once_records_tracking_and_actor(self):
        order = self.make_order()
        dispatch_order(
            order_id=order.pk, carrier="پست", tracking_code=" 123456 ",
            recorded_by=self.staff,
        )
        order.refresh_from_db()
        self.inventory.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertIsNotNone(order.inventory_consumed_at)
        self.assertEqual((self.inventory.on_hand, self.inventory.reserved), (3, 0))
        self.assertEqual(order.shipment.tracking_code, "123456")
        self.assertEqual(order.shipment.recorded_by_id, self.staff.pk)
        self.assertEqual(StockMovement.objects.filter(
            order=order, reason=StockMovement.Reason.FULFILLMENT,
        ).count(), 1)

    def test_duplicate_dispatch_is_idempotent(self):
        order = self.make_order()
        for _ in range(2):
            dispatch_order(order_id=order.pk, carrier="پست", tracking_code="T123")
        self.inventory.refresh_from_db()
        self.assertEqual((self.inventory.on_hand, self.inventory.reserved), (3, 0))
        self.assertEqual(Shipment.objects.filter(order=order).count(), 1)
        self.assertEqual(StockMovement.objects.filter(
            order=order, reason=StockMovement.Reason.FULFILLMENT,
        ).count(), 1)

    def test_cannot_change_shipment_by_repeating_dispatch(self):
        order = self.make_order()
        dispatch_order(order_id=order.pk, carrier="پست", tracking_code="T123")
        with self.assertRaises(OrderLifecycleError) as error:
            dispatch_order(order_id=order.pk, carrier="پست", tracking_code="T456")
        self.assertEqual(error.exception.code, "shipment_already_recorded")
        self.assertEqual(order.shipment.tracking_code, "T123")

    def test_pending_order_cannot_ship_and_stock_remains_reserved(self):
        order = self.make_order(paid=False)
        with self.assertRaises(OrderLifecycleError) as error:
            dispatch_order(order_id=order.pk, carrier="پست", tracking_code="T123")
        self.assertEqual(error.exception.code, "invalid_order_state")
        self.inventory.refresh_from_db()
        self.assertEqual((self.inventory.on_hand, self.inventory.reserved), (5, 2))
        self.assertFalse(Shipment.objects.filter(order=order).exists())

    def test_rejects_empty_and_control_character_tracking(self):
        order = self.make_order()
        for value in ("", "\n", "a\nb", "t" * 121):
            with self.subTest(value=repr(value)), self.assertRaises(OrderLifecycleError):
                dispatch_order(order_id=order.pk, carrier="پست", tracking_code=value)
        self.assertFalse(Shipment.objects.filter(order=order).exists())

    def test_delivery_requires_shipping_and_is_idempotent(self):
        order = self.make_order()
        with self.assertRaises(OrderLifecycleError):
            confirm_delivery(order_id=order.pk)
        dispatch_order(order_id=order.pk, carrier="پست", tracking_code="T123")
        confirm_delivery(order_id=order.pk)
        confirm_delivery(order_id=order.pk)
        order.refresh_from_db()
        self.inventory.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)
        self.assertIsNotNone(order.shipment.delivered_at)
        self.assertEqual((self.inventory.on_hand, self.inventory.reserved), (3, 0))
        self.assertEqual(StockMovement.objects.filter(
            order=order, reason=StockMovement.Reason.FULFILLMENT,
        ).count(), 1)

    def test_customer_order_list_and_detail_never_expose_other_orders(self):
        mine = self.make_order()
        other = build_pending_order(user=self.other_customer, variant=self.variant,
                                    quantity=1, with_reservation=False)
        self.client.force_login(self.customer)
        response = self.client.get(reverse("orders:customer-order-list"))
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["public_id"], str(mine.public_id))
        self.assertIsNone(results[0]["shipment"])
        detail = self.client.get(reverse(
            "orders:customer-order-detail", kwargs={"public_id": mine.public_id}
        ))
        self.assertEqual(detail.status_code, 200)
        forbidden = self.client.get(reverse(
            "orders:customer-order-detail", kwargs={"public_id": other.public_id}
        ))
        self.assertEqual(forbidden.status_code, 404)

    def test_customer_can_view_own_tracking_after_dispatch(self):
        order = self.make_order()
        dispatch_order(order_id=order.pk, carrier="پست", tracking_code="T-123")
        self.client.force_login(self.customer)
        response = self.client.get(reverse(
            "orders:customer-order-detail", kwargs={"public_id": order.public_id}
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["shipment"]["tracking_code"], "T-123")

    def test_anonymous_customer_cannot_read_order_list(self):
        response = self.client.get(reverse("orders:customer-order-list"))
        self.assertIn(response.status_code, (401, 403))

    def test_admin_dispatch_and_delivery_are_post_only_for_mutations(self):
        order = self.make_order()
        self.client.force_login(self.staff)
        dispatch_url = reverse("admin:orders_order_dispatch", args=[order.pk])
        confirm_url = reverse("admin:orders_order_confirm_delivery", args=[order.pk])
        response = self.client.get(dispatch_url)
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        response = self.client.post(dispatch_url, {
            "carrier": "پست", "tracking_code": "123456",
        })
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertEqual(order.shipment.recorded_by_id, self.staff.pk)
        self.assertEqual(self.client.get(confirm_url).status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertEqual(self.client.post(confirm_url, {}).status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)

    def test_staff_without_order_change_permission_cannot_dispatch(self):
        order = self.make_order()
        unprivileged = User.objects.create_user(
            username="ship-view-only", email="ship-view-only@example.com",
            password="test-pass-123", is_staff=True
        )
        self.client.force_login(unprivileged)
        response = self.client.post(
            reverse("admin:orders_order_dispatch", args=[order.pk]),
            {"carrier": "پست", "tracking_code": "T123"},
        )
        self.assertIn(response.status_code, (302, 403))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertFalse(Shipment.objects.filter(order=order).exists())

    def test_shipment_cannot_be_added_or_edited_in_standard_admin(self):
        self.client.force_login(self.staff)
        shipment_admin = admin.site._registry[Shipment]
        request = type("Request", (), {"user": self.staff})()
        self.assertFalse(shipment_admin.has_add_permission(request))
        self.assertFalse(shipment_admin.has_change_permission(request))
        self.assertFalse(shipment_admin.has_delete_permission(request))
