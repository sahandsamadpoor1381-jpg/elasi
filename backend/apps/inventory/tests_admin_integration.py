"""
FIX-04 regression tests: the InventoryBalance admin must behave like a
normal ModelAdmin through the real admin HTTP interface.

``save_model(change=False)`` used to insert a *separate* ``balance``
instance and leave the ``obj`` handed over by Django Admin without a
primary key. ``log_addition`` then recorded ``object_id=None`` and
``response_add`` crashed on ``quote(obj.pk)`` (options.py:1422), so the
admin's atomic block rolled the insert back and the request returned a
500. These tests drive the real admin URLs with an authenticated client
and assert creation, object identity, redirect, log entry and ledger
behaviour. They also assert that a rejected stock adjustment surfaces as
a normal admin error rather than an HTTP 500.
"""

from __future__ import annotations

from unittest import mock

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.inventory.admin import (
    InventoryBalanceAdmin,
    InventoryBalanceAdminForm,
)
from apps.inventory.models import InventoryBalance, StockMovement
from apps.inventory.tests_admin_adjustment import record_reservation
from apps.orders.tests_fulfillment import build_catalog

User = get_user_model()


def message_text(response) -> str:
    return " ".join(str(m.message) for m in get_messages(response.wsgi_request))


class InventoryAdminAddIntegrationBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="fix04-admin",
            email="fix04-admin@example.com",
            password="test-password",
        )

    def setUp(self):
        self.variant = build_catalog(
            sku=f"FIX04-{self.id().split('.')[-1][-8:]}",
        )
        self.content_type = ContentType.objects.get_for_model(
            InventoryBalance,
        )
        self.add_url = reverse(
            "admin:inventory_inventorybalance_add",
        )
        self.changelist_url = reverse(
            "admin:inventory_inventorybalance_changelist",
        )
        self.client.force_login(self.superuser)
        self.factory = RequestFactory()

    def post_add(self, on_hand, variant=None, **extra):
        return self.client.post(
            self.add_url,
            {
                "variant": str((variant or self.variant).pk),
                "on_hand": str(on_hand),
                **extra,
            },
        )

    def assert_single_initial_movement(self, balance, on_hand):
        movements = StockMovement.objects.filter(
            variant=balance.variant,
        )
        if on_hand:
            self.assertEqual(movements.count(), 1)
            movement = movements.get()
            self.assertEqual(
                movement.reason,
                StockMovement.Reason.ADJUSTMENT,
            )
            self.assertEqual(movement.quantity, on_hand)
            self.assertEqual(movement.on_hand_delta, on_hand)
            self.assertEqual(movement.reserved_delta, 0)
            self.assertIsNone(movement.order_id)
        else:
            self.assertEqual(movements.count(), 0)

        self.assertEqual(
            sum(m.on_hand_delta for m in movements),
            balance.on_hand,
        )
        self.assertEqual(
            sum(m.reserved_delta for m in movements),
            balance.reserved,
        )

    def assert_addition_logged(self, balance):
        return LogEntry.objects.get(
            content_type=self.content_type,
            object_id=str(balance.pk),
            action_flag=ADDITION,
            user_id=self.superuser.pk,
        )


class InventoryBalanceAdminAddTests(InventoryAdminAddIntegrationBase):
    def test_add_form_renders(self):
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 200)

    def test_admin_post_creates_balance_with_populated_identity(self):
        response = self.post_add(25, _continue=1)

        balance = InventoryBalance.objects.get(variant=self.variant)

        # obj.pk was populated: the redirect points at the change form
        # of the row that was actually created (response_add builds this
        # URL from obj.pk, so a None pk raises before redirecting).
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            reverse(
                "admin:inventory_inventorybalance_change",
                args=(balance.pk,),
            ),
        )

        self.assertEqual(balance.on_hand, 25)
        self.assertEqual(balance.reserved, 0)
        self.assert_single_initial_movement(balance, 25)

        entry = self.assert_addition_logged(balance)
        self.assertEqual(entry.object_repr, str(balance))
        self.assertIn(str(balance), message_text(response))

    def test_admin_post_redirects_to_changelist(self):
        response = self.post_add(7)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.changelist_url)

        balance = InventoryBalance.objects.get(variant=self.variant)
        self.assertEqual(balance.on_hand, 7)
        self.assertEqual(balance.reserved, 0)
        self.assert_single_initial_movement(balance, 7)
        self.assert_addition_logged(balance)

    def test_save_model_persists_the_admin_supplied_instance(self):
        model_admin = InventoryBalanceAdmin(
            InventoryBalance,
            AdminSite(),
        )
        request = self.factory.post(self.add_url)
        request.user = self.superuser

        obj = InventoryBalance(
            variant=self.variant,
            on_hand=12,
        )
        self.assertIsNone(obj.pk)

        model_admin.save_model(request, obj, form=None, change=False)

        # The very instance Django Admin passed in is the persisted row.
        self.assertIsNotNone(obj.pk)
        stored = InventoryBalance.objects.get(pk=obj.pk)
        self.assertEqual(stored.variant_id, self.variant.pk)
        self.assertEqual(stored.on_hand, 12)
        self.assertEqual(stored.reserved, 0)
        self.assertEqual(
            InventoryBalance.objects.filter(
                variant=self.variant,
            ).count(),
            1,
        )
        self.assert_single_initial_movement(obj, 12)

    def test_zero_opening_stock_creates_balance_without_movement(self):
        response = self.post_add(0)

        self.assertEqual(response.status_code, 302)
        balance = InventoryBalance.objects.get(variant=self.variant)
        self.assertEqual(balance.on_hand, 0)
        self.assertEqual(balance.reserved, 0)
        self.assert_single_initial_movement(balance, 0)
        self.assert_addition_logged(balance)

    def test_duplicate_variant_balance_is_rejected(self):
        first = self.post_add(5)
        self.assertEqual(first.status_code, 302)

        duplicate = self.post_add(9)

        # Rejected by form validation, never by a database error.
        self.assertEqual(duplicate.status_code, 200)
        self.assertContains(duplicate, "errorlist")
        self.assertEqual(
            InventoryBalance.objects.filter(
                variant=self.variant,
            ).count(),
            1,
        )
        balance = InventoryBalance.objects.get(variant=self.variant)
        self.assertEqual(balance.on_hand, 5)
        self.assertEqual(balance.reserved, 0)
        self.assert_single_initial_movement(balance, 5)


class InventoryBalanceAdminRejectionTests(InventoryAdminAddIntegrationBase):
    """
    Requirement: an invalid stock adjustment must never produce an
    unexpected HTTP 500 in the real admin interface - neither through
    the friendly form check nor through the authoritative row-locked
    re-check in ``save_model`` (the concurrent/raced path).
    """

    def setUp(self):
        super().setUp()
        self.balance = InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=10,
            reserved=0,
        )
        record_reservation(self.variant, 3)
        self.balance.refresh_from_db()
        self.change_url = reverse(
            "admin:inventory_inventorybalance_change",
            args=(self.balance.pk,),
        )

    def test_invalid_adjustment_renders_form_error_not_500(self):
        response = self.client.post(
            self.change_url,
            {"on_hand": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reserved")

        self.balance.refresh_from_db()
        self.assertEqual(self.balance.on_hand, 10)
        self.assertEqual(self.balance.reserved, 3)
        self.assertFalse(
            StockMovement.objects.filter(
                variant=self.variant,
                reason=StockMovement.Reason.ADJUSTMENT,
            ).exists(),
        )

    def test_raced_rejection_returns_admin_error_not_500(self):
        """
        Simulate the race: the form validated while ``reserved`` was
        still low, then a reservation landed before ``save_model`` took
        the row lock. The locked re-check must reject the save and the
        admin must answer with a normal error, not a 500.
        """

        def bypass_clean(form_self):
            return form_self.cleaned_data["on_hand"]

        with mock.patch.object(
            InventoryBalanceAdminForm,
            "clean_on_hand",
            bypass_clean,
        ):
            response = self.client.post(
                self.change_url,
                {"on_hand": "1"},
            )

        self.assertNotEqual(response.status_code, 500)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.changelist_url)

        text = message_text(response)
        self.assertIn("on_hand cannot be lower", text)

        # The rejected save left no trace: rolled back by the admin's
        # atomic block.
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.on_hand, 10)
        self.assertEqual(self.balance.reserved, 3)
        self.assertFalse(
            StockMovement.objects.filter(
                variant=self.variant,
                reason=StockMovement.Reason.ADJUSTMENT,
            ).exists(),
        )
        self.assertFalse(
            LogEntry.objects.filter(
                content_type=self.content_type,
                object_id=str(self.balance.pk),
            ).exists(),
        )

    def test_valid_adjustment_still_succeeds(self):
        response = self.client.post(
            self.change_url,
            {"on_hand": "40"},
        )

        self.assertEqual(response.status_code, 302)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.on_hand, 40)
        self.assertEqual(self.balance.reserved, 3)

        movement = StockMovement.objects.get(
            variant=self.variant,
            reason=StockMovement.Reason.ADJUSTMENT,
        )
        self.assertEqual(movement.on_hand_delta, 30)
        self.assertEqual(movement.reserved_delta, 0)
