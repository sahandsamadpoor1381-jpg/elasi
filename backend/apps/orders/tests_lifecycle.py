from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import (
    Category,
    Product,
    ProductVariant,
)
from apps.inventory.models import InventoryBalance

from .models import Order, OrderItem
from .services import (
    OrderLifecycleError,
    cancel_pending_order,
    expire_pending_order,
    expire_stale_pending_orders,
    mark_order_paid,
)


User = get_user_model()


class OrderLifecycleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = (
            User.objects.create_user(
                username=(
                    "lifecycle-user"
                ),
                email=(
                    "lifecycle@example.com"
                ),
                password=(
                    "test-password"
                ),
            )
        )

        category = (
            Category.objects.create(
                name=(
                    "Lifecycle Rings"
                ),
                slug=(
                    "lifecycle-rings"
                ),
                sort_order=20,
            )
        )

        product = (
            Product.objects.create(
                name=(
                    "ELASI Lifecycle Ring"
                ),
                slug=(
                    "elasi-lifecycle-ring"
                ),
                category=category,
                status=(
                    Product.Status.ACTIVE
                ),
            )
        )

        cls.variant = (
            ProductVariant.objects.create(
                product=product,
                sku=(
                    "ELA-LIFECYCLE-G18-17"
                ),
                material=(
                    ProductVariant.Material.GOLD
                ),
                karat=18,
                size="17",
                weight_grams="3.250",
                price_rial=250000000,
            )
        )

    def setUp(self):
        InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=5,
            reserved=3,
        )

    def create_pending_order(
        self,
        *,
        expires_at=None,
    ) -> Order:
        if expires_at is None:
            expires_at = (
                timezone.now()
                + timedelta(
                    minutes=15,
                )
            )

        order = (
            Order.objects.create(
                user=self.user,
                status=(
                    Order.Status.PENDING_PAYMENT
                ),
                subtotal_rial=(
                    250000000
                ),
                shipping_fee_rial=0,
                total_rial=(
                    250000000
                ),
                recipient_name=(
                    "Lifecycle Customer"
                ),
                phone_number=(
                    "09120000000"
                ),
                province=(
                    "West Azerbaijan"
                ),
                city="Urmia",
                postal_code=(
                    "1234567890"
                ),
                address_line=(
                    "Lifecycle address"
                ),
                reservation_expires_at=(
                    expires_at
                ),
            )
        )

        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            product_name=(
                self.variant.product.name
            ),
            product_slug=(
                self.variant.product.slug
            ),
            sku=self.variant.sku,
            material=(
                self.variant.material
            ),
            karat=(
                self.variant.karat
            ),
            purity=(
                self.variant.purity
            ),
            size=(
                self.variant.size
            ),
            weight_grams=(
                self.variant.weight_grams
            ),
            unit_price_rial=(
                self.variant.price_rial
            ),
            quantity=1,
        )

        return order

    def test_cancel_releases_inventory(
        self,
    ):
        order = (
            self.create_pending_order()
        )

        cancel_pending_order(
            order_id=order.pk,
        )

        order.refresh_from_db()

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        self.assertEqual(
            order.status,
            Order.Status.CANCELLED,
        )

        self.assertIsNotNone(
            order.cancelled_at,
        )

        self.assertIsNotNone(
            order.inventory_released_at,
        )

        self.assertEqual(
            inventory.reserved,
            2,
        )

    def test_cancel_is_idempotent(
        self,
    ):
        order = (
            self.create_pending_order()
        )

        cancel_pending_order(
            order_id=order.pk,
        )

        cancel_pending_order(
            order_id=order.pk,
        )

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        self.assertEqual(
            inventory.reserved,
            2,
        )

    def test_expired_order_releases_inventory(
        self,
    ):
        now = timezone.now()

        order = (
            self.create_pending_order(
                expires_at=(
                    now
                    - timedelta(
                        minutes=1,
                    )
                ),
            )
        )

        expire_pending_order(
            order_id=order.pk,
            now=now,
        )

        order.refresh_from_db()

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        self.assertEqual(
            order.status,
            Order.Status.EXPIRED,
        )

        self.assertIsNotNone(
            order.expired_at,
        )

        self.assertIsNotNone(
            order.inventory_released_at,
        )

        self.assertEqual(
            inventory.reserved,
            2,
        )

    def test_expire_is_idempotent(
        self,
    ):
        now = timezone.now()

        order = (
            self.create_pending_order(
                expires_at=(
                    now
                    - timedelta(
                        minutes=1,
                    )
                ),
            )
        )

        expire_pending_order(
            order_id=order.pk,
            now=now,
        )

        expire_pending_order(
            order_id=order.pk,
            now=now,
        )

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        self.assertEqual(
            inventory.reserved,
            2,
        )

    def test_order_cannot_expire_early(
        self,
    ):
        order = (
            self.create_pending_order()
        )

        with self.assertRaises(
            OrderLifecycleError,
        ) as context:
            expire_pending_order(
                order_id=order.pk,
            )

        self.assertEqual(
            context.exception.code,
            "reservation_not_expired",
        )

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        self.assertEqual(
            inventory.reserved,
            3,
        )

    def test_paid_order_keeps_inventory_reserved(
        self,
    ):
        order = (
            self.create_pending_order()
        )

        mark_order_paid(
            order_id=order.pk,
        )

        order.refresh_from_db()

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        self.assertEqual(
            order.status,
            Order.Status.PAID,
        )

        self.assertIsNotNone(
            order.paid_at,
        )

        self.assertIsNone(
            order.inventory_released_at,
        )

        self.assertEqual(
            inventory.reserved,
            3,
        )

    def test_mark_paid_is_idempotent(
        self,
    ):
        order = (
            self.create_pending_order()
        )

        mark_order_paid(
            order_id=order.pk,
        )

        mark_order_paid(
            order_id=order.pk,
        )

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        self.assertEqual(
            inventory.reserved,
            3,
        )

    def test_late_payment_expires_order(
        self,
    ):
        now = timezone.now()

        order = (
            self.create_pending_order(
                expires_at=(
                    now
                    - timedelta(
                        seconds=1,
                    )
                ),
            )
        )

        with self.assertRaises(
            OrderLifecycleError,
        ) as context:
            mark_order_paid(
                order_id=order.pk,
                paid_at=now,
            )

        self.assertEqual(
            context.exception.code,
            "reservation_expired",
        )

        order.refresh_from_db()

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        self.assertEqual(
            order.status,
            Order.Status.EXPIRED,
        )

        self.assertIsNotNone(
            order.inventory_released_at,
        )

        self.assertEqual(
            inventory.reserved,
            2,
        )

    def test_expire_stale_pending_orders(
        self,
    ):
        now = timezone.now()

        first_order = (
            self.create_pending_order(
                expires_at=(
                    now
                    - timedelta(
                        minutes=5,
                    )
                ),
            )
        )

        second_order = (
            self.create_pending_order(
                expires_at=(
                    now
                    - timedelta(
                        minutes=2,
                    )
                ),
            )
        )

        future_order = (
            self.create_pending_order(
                expires_at=(
                    now
                    + timedelta(
                        minutes=10,
                    )
                ),
            )
        )

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        inventory.reserved = 5

        inventory.save(
            update_fields=(
                "reserved",
                "updated_at",
            ),
        )

        expired_count = (
            expire_stale_pending_orders(
                now=now,
            )
        )

        self.assertEqual(
            expired_count,
            2,
        )

        first_order.refresh_from_db()
        second_order.refresh_from_db()
        future_order.refresh_from_db()
        inventory.refresh_from_db()

        self.assertEqual(
            first_order.status,
            Order.Status.EXPIRED,
        )

        self.assertEqual(
            second_order.status,
            Order.Status.EXPIRED,
        )

        self.assertEqual(
            future_order.status,
            Order.Status.PENDING_PAYMENT,
        )

        self.assertEqual(
            inventory.reserved,
            3,
        )