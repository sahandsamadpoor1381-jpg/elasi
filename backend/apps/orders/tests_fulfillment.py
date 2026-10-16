"""
Inventory fulfillment and order-lifecycle integrity tests.

Covers the fulfillment consumption service (exactly-once,
state guards, audit ledger), legacy reservation-deadline
handling, and — on PostgreSQL — concurrent oversell and
duplicate-fulfillment protection.
"""

from datetime import timedelta
from unittest import SkipTest

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.catalog.models import (
    Category,
    Product,
    ProductVariant,
)
from apps.inventory.models import (
    InventoryBalance,
    StockMovement,
)

from .models import Order, OrderItem
from .services import (
    CheckoutError,
    OrderLifecycleError,
    cancel_pending_order,
    checkout_cart,
    expire_pending_order,
    expire_stale_pending_orders,
    fulfill_order,
    mark_order_paid,
)


User = get_user_model()


def build_catalog(sku: str):
    category, _ = Category.objects.get_or_create(
        name="Fulfillment Rings",
        defaults={
            "slug": "fulfillment-rings",
            "sort_order": 40,
        },
    )

    product, _ = Product.objects.get_or_create(
        slug="elasi-fulfillment-ring",
        defaults={
            "name": "ELASI Fulfillment Ring",
            "category": category,
            "status": Product.Status.ACTIVE,
        },
    )

    variant = ProductVariant.objects.create(
        product=product,
        sku=sku,
        material=ProductVariant.Material.GOLD,
        karat=18,
        size="17",
        weight_grams="3.250",
        price_rial=250000000,
    )

    return variant


def build_pending_order(
    *,
    user,
    variant,
    quantity: int = 1,
    expires_at=None,
    with_reservation: bool = True,
) -> Order:
    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDING_PAYMENT,
        subtotal_rial=250000000 * quantity,
        shipping_fee_rial=0,
        total_rial=250000000 * quantity,
        recipient_name="Fulfillment Customer",
        phone_number="+989121234567",
        province="آذربایجان غربی",
        city="ارومیه",
        postal_code="1234567890",
        address_line="Fulfillment address",
        reservation_expires_at=expires_at,
    )

    OrderItem.objects.create(
        order=order,
        variant=variant,
        product_name=variant.product.name,
        product_slug=variant.product.slug,
        sku=variant.sku,
        material=variant.material,
        karat=variant.karat,
        purity=variant.purity,
        size=variant.size,
        weight_grams=variant.weight_grams,
        unit_price_rial=variant.price_rial,
        quantity=quantity,
    )

    if with_reservation:
        balance = InventoryBalance.objects.get(
            variant=variant,
        )

        balance.reserved += quantity

        balance.save(
            update_fields=(
                "reserved",
                "updated_at",
            ),
        )

    return order


class FulfillOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="fulfillment-user",
            email="fulfillment@example.com",
            password="test-password",
        )

    def setUp(self):
        self.variant = build_catalog(
            sku=f"ELA-FULFILL-G18-{self.id().split('.')[-1][:8]}",
        )

        self.inventory = InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=5,
            reserved=0,
        )

    def create_paid_order(
        self,
        *,
        quantity: int = 1,
    ) -> Order:
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
            quantity=quantity,
        )

        return mark_order_paid(
            order_id=order.pk,
        )

    def test_fulfill_consumes_inventory(self):
        order = self.create_paid_order(
            quantity=2,
        )

        fulfill_order(order_id=order.pk)

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PAID,
        )

        self.assertIsNotNone(
            order.inventory_consumed_at,
        )

        self.assertEqual(
            self.inventory.on_hand,
            3,
        )

        self.assertEqual(
            self.inventory.reserved,
            0,
        )

        movements = StockMovement.objects.filter(
            order=order,
            reason=StockMovement.Reason.FULFILLMENT,
        )

        self.assertEqual(movements.count(), 1)

        movement = movements.get()

        self.assertEqual(movement.quantity, 2)
        self.assertEqual(movement.on_hand_delta, -2)
        self.assertEqual(movement.reserved_delta, -2)

    def test_fulfill_is_idempotent(self):
        order = self.create_paid_order(
            quantity=2,
        )

        fulfill_order(order_id=order.pk)
        fulfill_order(order_id=order.pk)

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.on_hand,
            3,
        )

        self.assertEqual(
            self.inventory.reserved,
            0,
        )

        self.assertEqual(
            StockMovement.objects.filter(
                order=order,
                reason=StockMovement.Reason.FULFILLMENT,
            ).count(),
            1,
        )

    def test_fulfill_rejects_pending_order(self):
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
        )

        with self.assertRaises(
            OrderLifecycleError,
        ) as raised:
            fulfill_order(order_id=order.pk)

        self.assertEqual(
            raised.exception.code,
            "invalid_order_state",
        )

    def test_fulfill_rejects_cancelled_order(self):
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
        )

        InventoryBalance.objects.filter(
            pk=self.inventory.pk,
        ).update(reserved=1)

        cancel_pending_order(
            order_id=order.pk,
        )

        with self.assertRaises(
            OrderLifecycleError,
        ) as raised:
            fulfill_order(order_id=order.pk)

        self.assertEqual(
            raised.exception.code,
            "invalid_order_state",
        )

    def test_fulfill_rejects_expired_order(self):
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
            expires_at=(
                timezone.now()
                - timedelta(minutes=1)
            ),
        )

        InventoryBalance.objects.filter(
            pk=self.inventory.pk,
        ).update(reserved=1)

        expire_pending_order(
            order_id=order.pk,
        )

        with self.assertRaises(
            OrderLifecycleError,
        ) as raised:
            fulfill_order(order_id=order.pk)

        self.assertEqual(
            raised.exception.code,
            "invalid_order_state",
        )

    def test_fulfill_rejects_late_paid_order(self):
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
            expires_at=(
                timezone.now()
                - timedelta(minutes=1)
            ),
        )

        InventoryBalance.objects.filter(
            pk=self.inventory.pk,
        ).update(reserved=1)

        with self.assertRaises(
            OrderLifecycleError,
        ) as raised:
            mark_order_paid(
                order_id=order.pk,
            )

        self.assertEqual(
            raised.exception.code,
            "reservation_expired",
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.EXPIRED,
        )

        with self.assertRaises(
            OrderLifecycleError,
        ) as raised:
            fulfill_order(order_id=order.pk)

        self.assertEqual(
            raised.exception.code,
            "invalid_order_state",
        )

    def test_fulfill_detects_inconsistent_reservation(self):
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
            quantity=2,
            with_reservation=False,
        )

        order.status = Order.Status.PAID
        order.save(update_fields=("status",))

        # Reserved (0) is lower than the ordered quantity (2).
        with self.assertRaises(
            OrderLifecycleError,
        ) as raised:
            fulfill_order(order_id=order.pk)

        self.assertEqual(
            raised.exception.code,
            "inventory_reservation_inconsistent",
        )

    def test_fulfill_detects_missing_inventory(self):
        order = self.create_paid_order()

        InventoryBalance.objects.filter(
            variant=self.variant,
        ).delete()

        with self.assertRaises(
            OrderLifecycleError,
        ) as raised:
            fulfill_order(order_id=order.pk)

        self.assertEqual(
            raised.exception.code,
            "inventory_missing",
        )

    def test_fulfill_unknown_order(self):
        with self.assertRaises(
            OrderLifecycleError,
        ) as raised:
            fulfill_order(order_id=999999)

        self.assertEqual(
            raised.exception.code,
            "order_not_found",
        )

    def test_reservation_and_release_movements_are_recorded(self):
        cart = Cart.objects.create()

        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=1,
        )

        order = checkout_cart(
            user=self.user,
            cart_token=cart.token,
            recipient_name="Fulfillment Customer",
            phone_number="09121234567",
            province="آذربایجان غربی",
            city="ارومیه",
            postal_code="1234567890",
            address_line="Fulfillment address",
        )

        cancel_pending_order(
            order_id=order.pk,
        )

        reasons = list(
            StockMovement.objects.filter(
                order=order,
            )
            .order_by("reason")
            .values_list("reason", flat=True)
        )

        self.assertEqual(
            sorted(reasons),
            [
                StockMovement.Reason.RELEASE,
                StockMovement.Reason.RESERVATION,
            ],
        )

    def test_fulfill_after_cancel_keeps_release_exactly_once(self):
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
        )

        InventoryBalance.objects.filter(
            pk=self.inventory.pk,
        ).update(reserved=1)

        cancel_pending_order(order_id=order.pk)
        cancel_pending_order(order_id=order.pk)

        self.inventory.refresh_from_db()

        self.assertEqual(self.inventory.reserved, 0)

        self.assertEqual(
            StockMovement.objects.filter(
                order=order,
                reason=StockMovement.Reason.RELEASE,
            ).count(),
            1,
        )


class LegacyReservationDeadlineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="legacy-user",
            email="legacy@example.com",
            password="test-password",
        )

    def setUp(self):
        self.variant = build_catalog(
            sku=f"ELA-LEGACY-G18-{self.id().split('.')[-1][:8]}",
        )

        self.inventory = InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=5,
            reserved=0,
        )

    def make_legacy_order(self, age_minutes: int) -> Order:
        order = build_pending_order(
            user=self.user,
            variant=self.variant,
            expires_at=None,
            with_reservation=False,
        )

        InventoryBalance.objects.filter(
            pk=self.inventory.pk,
        ).update(reserved=1)

        Order.objects.filter(pk=order.pk).update(
            created_at=(
                timezone.now()
                - timedelta(minutes=age_minutes)
            ),
        )

        order.refresh_from_db()
        return order

    def test_expire_handles_missing_deadline(self):
        order = self.make_legacy_order(
            age_minutes=20,
        )

        expire_pending_order(
            order_id=order.pk,
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

        self.assertEqual(
            self.inventory.reserved,
            0,
        )

    def test_mark_paid_handles_recent_missing_deadline(self):
        order = self.make_legacy_order(
            age_minutes=0,
        )

        mark_order_paid(order_id=order.pk)

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PAID,
        )

        self.assertEqual(
            self.inventory.reserved,
            1,
        )

    def test_mark_paid_expires_legacy_old_order(self):
        order = self.make_legacy_order(
            age_minutes=20,
        )

        with self.assertRaises(
            OrderLifecycleError,
        ) as raised:
            mark_order_paid(order_id=order.pk)

        self.assertEqual(
            raised.exception.code,
            "reservation_expired",
        )

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.EXPIRED,
        )

        self.assertEqual(
            self.inventory.reserved,
            0,
        )

    def test_expire_stale_includes_legacy_null_deadline(self):
        self.make_legacy_order(age_minutes=20)

        expired_count = (
            expire_stale_pending_orders()
        )

        self.assertEqual(expired_count, 1)

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved,
            0,
        )

    def test_expire_stale_ignores_recent_null_deadline(self):
        self.make_legacy_order(age_minutes=0)

        expired_count = (
            expire_stale_pending_orders()
        )

        self.assertEqual(expired_count, 0)

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.reserved,
            1,
        )


class FulfillmentConcurrencyTests(TransactionTestCase):
    """
    True concurrency tests. They require a database backend with
    real row locks (PostgreSQL); on SQLite they are skipped because
    ``select_for_update`` is a no-op there.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        if not connection.features.has_select_for_update:
            raise SkipTest(
                "Concurrency tests require PostgreSQL.",
            )

    def setUp(self):
        self.user = User.objects.create_user(
            username="concurrency-user",
            email="concurrency@example.com",
            password="test-password",
        )

        self.variant = build_catalog(
            sku="ELA-CONCURRENCY-G18-17",
        )

        self.inventory = InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=1,
            reserved=0,
        )

    def tearDown(self):
        connections.close_all()
        super().tearDown()

    def test_concurrent_checkout_cannot_oversell(self):
        from threading import Barrier, Thread

        payload = {
            "recipient_name": "Concurrency Customer",
            "phone_number": "09121234567",
            "province": "آذربایجان غربی",
            "city": "ارومیه",
            "postal_code": "1234567890",
            "address_line": "Concurrency address",
        }

        carts = []

        for _ in range(2):
            cart = Cart.objects.create()
            CartItem.objects.create(
                cart=cart,
                variant=self.variant,
                quantity=1,
            )
            carts.append(cart)

        barrier = Barrier(2)
        results = []

        def run(cart):
            try:
                barrier.wait(timeout=5)

                checkout_cart(
                    user=self.user,
                    cart_token=cart.token,
                    **payload,
                )

                results.append("ok")
            except CheckoutError as error:
                results.append(error.code)
            finally:
                connection.close()

        threads = [
            Thread(target=run, args=(cart,))
            for cart in carts
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=10)

        self.assertEqual(
            sorted(results),
            ["ok", "stock_exceeded"],
        )

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.on_hand,
            1,
        )

        self.assertEqual(
            self.inventory.reserved,
            1,
        )

    def test_concurrent_fulfill_runs_exactly_once(self):
        from threading import Barrier, Thread

        order = Order.objects.create(
            user=self.user,
            status=Order.Status.PENDING_PAYMENT,
            subtotal_rial=250000000,
            shipping_fee_rial=0,
            total_rial=250000000,
            recipient_name="Concurrency Customer",
            phone_number="+989121234567",
            province="آذربایجان غربی",
            city="ارومیه",
            postal_code="1234567890",
            address_line="Concurrency address",
            reservation_expires_at=(
                timezone.now()
                + timedelta(minutes=15)
            ),
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

        self.inventory.reserved = 1
        self.inventory.save(update_fields=("reserved",))

        mark_order_paid(order_id=order.pk)

        barrier = Barrier(2)
        results = []

        def run():
            try:
                barrier.wait(timeout=5)

                fulfill_order(
                    order_id=order.pk,
                )

                results.append("ok")
            except Exception as error:  # noqa: BLE001
                results.append(
                    type(error).__name__
                )
            finally:
                connection.close()

        threads = [
            Thread(target=run)
            for _ in range(2)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=10)

        self.assertEqual(
            sorted(results),
            ["ok", "ok"],
        )

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.on_hand,
            0,
        )

        self.assertEqual(
            self.inventory.reserved,
            0,
        )

        self.assertEqual(
            StockMovement.objects.filter(
                order=order,
                reason=StockMovement.Reason.FULFILLMENT,
            ).count(),
            1,
        )
