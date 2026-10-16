from __future__ import annotations

from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import InventoryBalance, StockMovement
from apps.orders.models import Order
from apps.orders.tests_fulfillment import build_catalog, build_pending_order


class ExpirePendingOrdersCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="expire-user",
            email="expire@example.com",
            password="test-password",
        )
        cls.variant = build_catalog(sku="EXP-CMD-1")
        InventoryBalance.objects.get_or_create(
            variant=cls.variant,
            defaults={"on_hand": 10, "reserved": 0},
        )

    def test_expires_due_pending_and_releases_exactly_once(self):
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        call_command("expire_pending_orders")
        order.refresh_from_db()
        balance = InventoryBalance.objects.get(variant=self.variant)
        self.assertEqual(order.status, Order.Status.EXPIRED)
        self.assertEqual(balance.reserved, 0)
        self.assertEqual(
            StockMovement.objects.filter(
                variant=self.variant, reason=StockMovement.Reason.RELEASE
            ).count(),
            1,
        )
        call_command("expire_pending_orders")
        balance.refresh_from_db()
        self.assertEqual(balance.reserved, 0)

    def test_skips_future_pending_and_paid_orders(self):
        future = build_pending_order(
            user=self.user,
            variant=self.variant,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        paid = build_pending_order(
            user=self.user,
            variant=self.variant,
            expires_at=timezone.now() - timedelta(minutes=5),
        )
        paid.status = Order.Status.PAID
        paid.save(update_fields=["status"])
        call_command("expire_pending_orders")
        future.refresh_from_db()
        paid.refresh_from_db()
        self.assertEqual(future.status, Order.Status.PENDING_PAYMENT)
        self.assertEqual(paid.status, Order.Status.PAID)

    def test_legacy_null_deadline_uses_created_at_fallback(self):
        order = build_pending_order(user=self.user, variant=self.variant, expires_at=None)
        Order.objects.filter(pk=order.pk).update(
            created_at=timezone.now() - timedelta(minutes=30),
        )
        call_command("expire_pending_orders")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.EXPIRED)
