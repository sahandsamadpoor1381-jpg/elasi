from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from io import StringIO

from apps.catalog.models import (
    Category,
    Product,
    ProductVariant,
)
from apps.inventory.models import InventoryBalance

from .models import Order, OrderItem
from .services import get_payment_reservation_duration


User = get_user_model()


class ReconcileOrderReservationsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="reconcile-user",
            email="reconcile@example.com",
            password="test-password",
        )

        category = Category.objects.create(
            name="Reconcile Rings",
            slug="reconcile-rings",
            sort_order=50,
        )

        product = Product.objects.create(
            name="ELASI Reconcile Ring",
            slug="elasi-reconcile-ring",
            category=category,
            status=Product.Status.ACTIVE,
        )

        cls.variant = ProductVariant.objects.create(
            product=product,
            sku="ELA-RECONCILE-G18-17",
            material=ProductVariant.Material.GOLD,
            karat=18,
            size="17",
            weight_grams="3.250",
            price_rial=250000000,
        )

    def setUp(self):
        InventoryBalance.objects.get_or_create(
            variant=self.variant,
            defaults={
                "on_hand": 5,
                "reserved": 0,
            },
        )

    def create_legacy_pending_order(self):
        order = Order.objects.create(
            user=self.user,
            status=Order.Status.PENDING_PAYMENT,
            subtotal_rial=250000000,
            shipping_fee_rial=0,
            total_rial=250000000,
            recipient_name="Reconcile Customer",
            phone_number="+989121234567",
            province="آذربایجان غربی",
            city="ارومیه",
            postal_code="1234567890",
            address_line="Reconcile address",
            reservation_expires_at=None,
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

        return order

    def run_command(self, *args):
        out = StringIO()
        call_command(
            "reconcile_order_reservations",
            *args,
            stdout=out,
        )
        return out.getvalue()

    def test_dry_run_reports_without_changes(self):
        order = self.create_legacy_pending_order()

        output = self.run_command()

        self.assertIn(
            "missing reservation_expires_at: 1",
            output,
        )

        self.assertIn("Dry run", output)

        order.refresh_from_db()

        self.assertIsNone(
            order.reservation_expires_at,
        )

    def test_apply_backfills_deadline(self):
        order = self.create_legacy_pending_order()

        output = self.run_command("--apply")

        self.assertIn(
            "Backfilled reservation_expires_at for 1 order(s).",
            output,
        )

        order.refresh_from_db()

        self.assertIsNotNone(
            order.reservation_expires_at,
        )

        duration = (
            get_payment_reservation_duration()
        )

        self.assertEqual(
            order.reservation_expires_at,
            order.created_at + duration,
        )

    def test_apply_is_idempotent(self):
        order = self.create_legacy_pending_order()

        self.run_command("--apply")

        first_deadline = (
            Order.objects.get(pk=order.pk).reservation_expires_at
        )

        output = self.run_command("--apply")

        self.assertIn(
            "Backfilled reservation_expires_at for 0 order(s).",
            output,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.reservation_expires_at,
            first_deadline,
        )

    def test_paid_orders_are_untouched(self):
        order = self.create_legacy_pending_order()

        Order.objects.filter(pk=order.pk).update(
            status=Order.Status.PAID,
        )

        output = self.run_command("--apply")

        self.assertIn("missing reservation_expires_at: 0", output)

        order.refresh_from_db()

        self.assertIsNone(
            order.reservation_expires_at,
        )
