from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import InventoryBalance
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
from apps.orders.tests_fulfillment import build_catalog, build_pending_order


class OrderSerializerContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="serializer-user",
            email="serializer@example.com",
            password="test-password",
        )
        cls.variant = build_catalog(sku="SER-1")
        InventoryBalance.objects.get_or_create(
            variant=cls.variant,
            defaults={"on_hand": 5, "reserved": 0},
        )

    def test_serializer_exposes_reservation_deadline_and_paid_at(self):
        deadline = timezone.now() + timedelta(minutes=15)
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
            expires_at=deadline,
        )
        data = OrderSerializer(order).data
        self.assertIn("reservation_expires_at", data)
        self.assertIn("paid_at", data)
        self.assertIsNone(data["paid_at"])

        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paid_at"])
        data = OrderSerializer(order).data
        self.assertIsNotNone(data["paid_at"])
