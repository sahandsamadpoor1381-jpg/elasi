"""
FIX-01 regression tests: InventoryBalanceAdmin must apply stock
adjustments atomically (row-locked), preserving the latest ``reserved``
written by concurrent order reservations, validating ``on_hand`` and
keeping the StockMovement ledger consistent.
"""

from __future__ import annotations

from unittest import SkipTest

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection, connections
from django.db.models import F
from django.test import RequestFactory, TestCase, TransactionTestCase

from apps.inventory.admin import InventoryBalanceAdmin, InventoryBalanceAdminForm
from apps.inventory.models import InventoryBalance, StockMovement
from apps.orders.tests_fulfillment import build_catalog

User = get_user_model()


def record_initial_stock(variant, on_hand: int) -> None:
    """Seed the ledger so movement sums match the balance exactly."""
    if on_hand:
        StockMovement.objects.create(
            variant=variant,
            reason=StockMovement.Reason.ADJUSTMENT,
            quantity=on_hand,
            on_hand_delta=on_hand,
            reserved_delta=0,
        )


def record_reservation(variant, quantity: int) -> None:
    """Mirror what checkout_cart does to the balance + ledger."""
    InventoryBalance.objects.filter(variant=variant).update(
        reserved=F("reserved") + quantity,
    )
    StockMovement.objects.create(
        variant=variant,
        reason=StockMovement.Reason.RESERVATION,
        quantity=quantity,
        on_hand_delta=0,
        reserved_delta=quantity,
    )


class InventoryAdminAdjustmentBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="inv-admin",
            email="inv-admin@example.com",
            password="test-password",
        )

    def setUp(self):
        self.variant = build_catalog(sku=f"INV-ADJ-{self.id().split('.')[-1][:10]}")
        self.inventory = InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=10,
            reserved=0,
        )
        record_initial_stock(self.variant, 10)
        self.site = AdminSite()
        self.factory = RequestFactory()

    def admin_request(self):
        request = self.factory.post("/admin/inventory/inventorybalance/")
        request.user = self.superuser
        return request

    def make_admin(self):
        return InventoryBalanceAdmin(InventoryBalance, self.site)

    def assert_ledger_consistent(self):
        balance = InventoryBalance.objects.get(variant=self.variant)
        movements = StockMovement.objects.filter(variant=self.variant)
        self.assertEqual(
            sum(m.on_hand_delta for m in movements),
            balance.on_hand,
        )
        self.assertEqual(
            sum(m.reserved_delta for m in movements),
            balance.reserved,
        )
        self.assertLessEqual(balance.reserved, balance.on_hand)
        return balance


class StaleInstanceTests(InventoryAdminAdjustmentBase):
    def test_stale_instance_does_not_clobber_reserved(self):
        stale = InventoryBalance.objects.get(pk=self.inventory.pk)
        # Stale copy loaded by the admin form:
        self.assertEqual(stale.on_hand, 10)

        # A checkout reserves stock AFTER the form was rendered:
        record_reservation(self.variant, 3)

        stale.on_hand = 40
        self.make_admin().save_model(
            self.admin_request(),
            stale,
            form=None,
            change=True,
        )

        balance = self.assert_ledger_consistent()
        self.assertEqual(balance.on_hand, 40)
        self.assertEqual(balance.reserved, 3)

        adjustment = StockMovement.objects.get(
            variant=self.variant,
            reason=StockMovement.Reason.ADJUSTMENT,
            quantity=30,
        )
        self.assertEqual(adjustment.on_hand_delta, 30)
        self.assertEqual(adjustment.reserved_delta, 0)

    def test_adjustment_rejects_on_hand_below_reserved(self):
        record_reservation(self.variant, 8)

        stale = InventoryBalance.objects.get(pk=self.inventory.pk)
        stale.on_hand = 4

        with self.assertRaises(ValidationError):
            self.make_admin().save_model(
                self.admin_request(),
                stale,
                form=None,
                change=True,
            )

        balance = self.assert_ledger_consistent()
        self.assertEqual(balance.on_hand, 10)
        self.assertEqual(
            StockMovement.objects.filter(
                variant=self.variant,
                reason=StockMovement.Reason.ADJUSTMENT,
            ).count(),
            1,
        )

    def test_form_validates_on_hand_below_reserved(self):
        record_reservation(self.variant, 8)

        form = InventoryBalanceAdminForm(
            data={
                "variant": self.variant.pk,
                "on_hand": 4,
            },
            instance=self.inventory,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("on_hand", form.errors)

    def test_no_movement_when_unchanged(self):
        stale = InventoryBalance.objects.get(pk=self.inventory.pk)
        self.make_admin().save_model(
            self.admin_request(),
            stale,
            form=None,
            change=True,
        )
        self.assertEqual(
            StockMovement.objects.filter(
                variant=self.variant,
                reason=StockMovement.Reason.ADJUSTMENT,
            ).count(),
            1,
        )

    def test_add_creates_balance_and_adjustment_movement(self):
        other = build_catalog(sku=f"INV-ADD-{self.id().split('.')[-1][:10]}")
        obj = InventoryBalance(variant=other, on_hand=7)

        self.make_admin().save_model(
            self.admin_request(),
            obj,
            form=None,
            change=False,
        )

        balance = InventoryBalance.objects.get(variant=other)
        self.assertEqual(balance.on_hand, 7)
        self.assertEqual(balance.reserved, 0)
        movement = StockMovement.objects.get(
            variant=other,
            reason=StockMovement.Reason.ADJUSTMENT,
        )
        self.assertEqual(movement.on_hand_delta, 7)

    def test_ledger_consistency_across_adjustment_and_reservation(self):
        stale = InventoryBalance.objects.get(pk=self.inventory.pk)
        stale.on_hand = 25
        self.make_admin().save_model(
            self.admin_request(),
            stale,
            form=None,
            change=True,
        )

        record_reservation(self.variant, 4)

        stale2 = InventoryBalance.objects.get(pk=self.inventory.pk)
        stale2.on_hand = 20
        self.make_admin().save_model(
            self.admin_request(),
            stale2,
            form=None,
            change=True,
        )

        balance = self.assert_ledger_consistent()
        self.assertEqual(balance.on_hand, 20)
        self.assertEqual(balance.reserved, 4)


class InventoryAdminConcurrencyTests(TransactionTestCase):
    """
    True concurrency tests (PostgreSQL only): row locks serialize an
    admin adjustment against a concurrent reservation / another
    adjustment. Skipped on SQLite where select_for_update is a no-op.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not connection.features.has_select_for_update:
            raise SkipTest("Concurrency tests require PostgreSQL.")

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="inv-conc",
            email="inv-conc@example.com",
            password="test-password",
        )
        self.variant = build_catalog(sku=f"INV-CONC-{self.id().split('.')[-1][:10]}")
        self.inventory = InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=10,
            reserved=0,
        )
        record_initial_stock(self.variant, 10)
        self.site = AdminSite()
        self.factory = RequestFactory()

    def tearDown(self):
        connections.close_all()
        super().tearDown()

    def admin_request(self):
        request = self.factory.post("/admin/inventory/inventorybalance/")
        request.user = self.superuser
        return request

    def assert_ledger_consistent(self):
        balance = InventoryBalance.objects.get(variant=self.variant)
        movements = StockMovement.objects.filter(variant=self.variant)
        self.assertEqual(
            sum(m.on_hand_delta for m in movements),
            balance.on_hand,
        )
        self.assertEqual(
            sum(m.reserved_delta for m in movements),
            balance.reserved,
        )
        self.assertLessEqual(balance.reserved, balance.on_hand)
        return balance

    def test_concurrent_reservation_vs_admin_adjustment(self):
        from threading import Barrier, Thread

        from apps.cart.models import Cart, CartItem
        from apps.orders.services import checkout_cart

        cart = Cart.objects.create()
        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=1,
        )

        stale = InventoryBalance.objects.get(pk=self.inventory.pk)
        stale.on_hand = 50

        admin = InventoryBalanceAdmin(InventoryBalance, self.site)

        barrier = Barrier(2)
        results = []

        def reserve():
            try:
                barrier.wait(timeout=5)
                checkout_cart(
                    user=self.superuser,
                    cart_token=cart.token,
                    recipient_name="Concurrency Customer",
                    phone_number="09121234567",
                    province="آذربایجان غربی",
                    city="ارومیه",
                    postal_code="1234567890",
                    address_line="Concurrency address",
                )
                results.append("reserve-ok")
            except Exception as error:  # noqa: BLE001
                results.append(f"reserve-error:{error}")
            finally:
                connection.close()

        def adjust():
            try:
                barrier.wait(timeout=5)
                admin.save_model(
                    self.admin_request(),
                    stale,
                    form=None,
                    change=True,
                )
                results.append("adjust-ok")
            except Exception as error:  # noqa: BLE001
                results.append(f"adjust-error:{error}")
            finally:
                connection.close()

        threads = [
            Thread(target=reserve),
            Thread(target=adjust),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        self.assertEqual(
            sorted(results),
            ["adjust-ok", "reserve-ok"],
        )

        balance = self.assert_ledger_consistent()
        self.assertEqual(balance.on_hand, 50)
        self.assertEqual(balance.reserved, 1)

    def test_two_concurrent_adjustments_keep_ledger_consistent(self):
        from threading import Barrier, Thread

        stale_a = InventoryBalance.objects.get(pk=self.inventory.pk)
        stale_b = InventoryBalance.objects.get(pk=self.inventory.pk)
        stale_a.on_hand = 50
        stale_b.on_hand = 60

        admin_a = InventoryBalanceAdmin(InventoryBalance, self.site)
        admin_b = InventoryBalanceAdmin(InventoryBalance, self.site)

        barrier = Barrier(2)
        results = []

        def run(admin, stale, label):
            try:
                barrier.wait(timeout=5)
                admin.save_model(
                    self.admin_request(),
                    stale,
                    form=None,
                    change=True,
                )
                results.append(f"{label}-ok")
            except Exception as error:  # noqa: BLE001
                results.append(f"{label}-error:{error}")
            finally:
                connection.close()

        threads = [
            Thread(target=run, args=(admin_a, stale_a, "a")),
            Thread(target=run, args=(admin_b, stale_b, "b")),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        self.assertEqual(
            sorted(results),
            ["a-ok", "b-ok"],
        )

        balance = self.assert_ledger_consistent()
        self.assertEqual(balance.on_hand, 60)
