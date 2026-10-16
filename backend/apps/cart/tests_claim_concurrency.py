"""
FIX-03 regression tests: claiming an unbound guest cart must be
transactional and concurrency-safe. Two different users racing for
the same unclaimed token must never both claim it or overwrite each
other's ownership. Guest (anonymous) behavior and CSRF protections
are unchanged and covered by the existing tests_ownership.py suite.
"""

from __future__ import annotations

from unittest import SkipTest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import connection, connections
from django.test import TestCase, TransactionTestCase
from rest_framework.exceptions import NotFound
from rest_framework.test import APIRequestFactory

from apps.cart.models import Cart
from apps.cart.views import get_request_cart

User = get_user_model()


def build_request(user, token):
    request = APIRequestFactory().get(
        "/api/v1/cart/",
        HTTP_X_CART_TOKEN=str(token),
    )
    request.user = user
    return request


class GuestClaimSemanticsTests(TestCase):
    def setUp(self):
        self.cart = Cart.objects.create()
        self.user_a = User.objects.create_user(
            username="claim-a",
            email="claim-a@example.com",
            password="test-password",
        )
        self.user_b = User.objects.create_user(
            username="claim-b",
            email="claim-b@example.com",
            password="test-password",
        )

    def test_guest_flow_is_unchanged(self):
        for _ in range(2):
            cart = get_request_cart(
                build_request(AnonymousUser(), self.cart.token),
            )
            self.assertEqual(cart.pk, self.cart.pk)

        self.cart.refresh_from_db()
        self.assertIsNone(self.cart.user_id)

    def test_first_authenticated_user_claims(self):
        cart = get_request_cart(
            build_request(self.user_a, self.cart.token),
        )
        self.assertEqual(cart.user_id, self.user_a.pk)

        # The owner keeps full access afterwards.
        again = get_request_cart(
            build_request(self.user_a, self.cart.token),
        )
        self.assertEqual(again.pk, self.cart.pk)

    def test_second_user_cannot_claim_or_steal(self):
        get_request_cart(
            build_request(self.user_a, self.cart.token),
        )

        with self.assertRaises(NotFound):
            get_request_cart(
                build_request(self.user_b, self.cart.token),
            )

        self.cart.refresh_from_db()
        self.assertEqual(self.cart.user_id, self.user_a.pk)

    def test_anonymous_cannot_touch_claimed_cart(self):
        get_request_cart(
            build_request(self.user_a, self.cart.token),
        )

        with self.assertRaises(NotFound):
            get_request_cart(
                build_request(AnonymousUser(), self.cart.token),
            )


class GuestClaimConcurrencyTests(TransactionTestCase):
    """
    True concurrency test (PostgreSQL only): two authenticated users
    hit the same unclaimed token at the same instant. Row locking must
    produce exactly one claim. Skipped on SQLite where select_for_update
    is a no-op.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not connection.features.has_select_for_update:
            raise SkipTest("Concurrency tests require PostgreSQL.")

    def setUp(self):
        self.cart = Cart.objects.create()
        self.user_a = User.objects.create_user(
            username="race-a",
            email="race-a@example.com",
            password="test-password",
        )
        self.user_b = User.objects.create_user(
            username="race-b",
            email="race-b@example.com",
            password="test-password",
        )

    def tearDown(self):
        connections.close_all()
        super().tearDown()

    def test_concurrent_claim_has_exactly_one_winner(self):
        from threading import Barrier, Thread

        barrier = Barrier(2)
        results = []

        def run(label, user):
            try:
                barrier.wait(timeout=5)
                cart = get_request_cart(
                    build_request(user, self.cart.token),
                )
                results.append((label, "ok", cart.pk))
            except NotFound:
                results.append((label, "not_found", None))
            except Exception as error:  # noqa: BLE001
                results.append((label, f"error:{error}", None))
            finally:
                connection.close()

        threads = [
            Thread(target=run, args=("a", self.user_a)),
            Thread(target=run, args=("b", self.user_b)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        outcomes = sorted(outcome for _, outcome, _ in results)
        self.assertEqual(outcomes, ["not_found", "ok"])

        self.cart.refresh_from_db()
        winner = [
            label for label, outcome, _ in results if outcome == "ok"
        ][0]
        expected = self.user_a.pk if winner == "a" else self.user_b.pk
        self.assertEqual(self.cart.user_id, expected)
