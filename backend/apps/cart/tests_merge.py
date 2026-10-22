"""Customer cart merge: ownership, quantity conservation and checkout safety."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import InventoryBalance
from apps.orders.models import Order
from apps.orders.services import CheckoutError, checkout_cart

from .models import Cart, CartItem


User = get_user_model()


class CartMergeAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="merge-owner", email="merge-owner@example.com", password="test-only"
        )
        cls.other = User.objects.create_user(
            username="merge-other", email="merge-other@example.com", password="test-only"
        )
        category = Category.objects.create(
            name="Merge rings", slug="merge-rings", sort_order=95
        )
        product = Product.objects.create(
            name="Merge ring", slug="merge-ring", category=category,
            status=Product.Status.ACTIVE,
        )
        cls.ring = ProductVariant.objects.create(
            product=product, sku="MERGE-RING-18", material=ProductVariant.Material.GOLD,
            karat=18, size="18", price_rial=2000000,
        )
        cls.other_ring = ProductVariant.objects.create(
            product=product, sku="MERGE-RING-19", material=ProductVariant.Material.GOLD,
            karat=18, size="19", price_rial=3000000,
        )
        InventoryBalance.objects.create(variant=cls.ring, on_hand=4, reserved=0)
        InventoryBalance.objects.create(variant=cls.other_ring, on_hand=8, reserved=0)

    def make_cart(self, user=None, *, lines=()):
        cart = Cart.objects.create(user=user)
        for variant, quantity in lines:
            CartItem.objects.create(cart=cart, variant=variant, quantity=quantity)
        return cart

    def login_and_get(self, cart):
        self.client.force_authenticate(user=self.owner)
        return self.client.get("/api/v1/cart/", HTTP_X_CART_TOKEN=str(cart.token))

    def test_claim_without_account_cart_keeps_guest_token(self):
        guest = self.make_cart(lines=((self.ring, 2),))
        result = self.login_and_get(guest)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["token"], str(guest.token))
        guest.refresh_from_db()
        self.assertEqual(guest.user, self.owner)
        self.assertEqual(guest.status, Cart.Status.ACTIVE)

    def test_existing_account_cart_and_guest_disjoint_items_are_conserved(self):
        account = self.make_cart(self.owner, lines=((self.ring, 1),))
        guest = self.make_cart(lines=((self.other_ring, 2),))
        result = self.login_and_get(guest)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["token"], str(account.token))
        self.assertEqual(result.data["subtotal_rial"], 8000000)
        self.assertEqual(
            {item["sku"]: item["quantity"] for item in result.data["items"]},
            {self.ring.sku: 1, self.other_ring.sku: 2},
        )
        guest.refresh_from_db()
        self.assertEqual(guest.status, Cart.Status.ABANDONED)
        self.assertEqual(guest.user, self.owner)
        self.assertFalse(CartItem.objects.filter(cart=guest).exists())

    def test_duplicate_sku_quantities_sum_without_duplicate_rows(self):
        account = self.make_cart(self.owner, lines=((self.ring, 1),))
        guest = self.make_cart(lines=((self.ring, 2),))
        result = self.login_and_get(guest)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["token"], str(account.token))
        self.assertEqual(result.data["items"][0]["quantity"], 3)
        self.assertEqual(CartItem.objects.filter(cart=account).count(), 1)

    def test_merge_preserves_quantities_above_current_stock_for_correction(self):
        account = self.make_cart(self.owner, lines=((self.ring, 3),))
        guest = self.make_cart(lines=((self.ring, 2),))
        result = self.login_and_get(guest)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["items"][0]["quantity"], 5)
        self.assertEqual(result.data["items"][0]["available"], 4)
        self.assertFalse(Order.objects.filter(user=self.owner).exists())
        with self.assertRaises(CheckoutError) as captured:
            checkout_cart(
                user=self.owner, cart_token=account.token,
                recipient_name="Test Buyer", phone_number="+989121234567",
                province="تهران", city="تهران", postal_code="1234567890",
                address_line="Test street",
            )
        self.assertEqual(captured.exception.code, "stock_exceeded")
        self.assertFalse(Order.objects.filter(user=self.owner).exists())
        self.assertTrue(Cart.objects.filter(pk=account.pk, status=Cart.Status.ACTIVE).exists())

    def test_merge_keeps_server_prices_authoritative_at_checkout(self):
        account = self.make_cart(self.owner, lines=((self.ring, 1),))
        guest = self.make_cart(lines=((self.ring, 1), (self.other_ring, 1)))
        self.assertEqual(self.login_and_get(guest).status_code, status.HTTP_200_OK)
        order = checkout_cart(
            user=self.owner, cart_token=account.token,
            recipient_name="Test Buyer", phone_number="+989121234567",
            province="تهران", city="تهران", postal_code="1234567890",
            address_line="Test street",
        )
        self.assertEqual(order.subtotal_rial, 7000000)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(Cart.objects.get(pk=account.pk).status, Cart.Status.CONVERTED)

    def test_merged_guest_token_cannot_be_replayed_by_other_users(self):
        account = self.make_cart(self.owner, lines=((self.ring, 1),))
        guest = self.make_cart(lines=((self.other_ring, 1),))
        self.assertEqual(self.login_and_get(guest).status_code, status.HTTP_200_OK)
        other_client = APIClient()
        other_client.force_authenticate(user=self.other)
        self.assertEqual(
            other_client.get("/api/v1/cart/", HTTP_X_CART_TOKEN=str(guest.token)).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        anonymous = APIClient()
        self.assertEqual(
            anonymous.get("/api/v1/cart/", HTTP_X_CART_TOKEN=str(guest.token)).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            CartItem.objects.get(cart=account, variant=self.ring).quantity, 1
        )

    def test_multiple_guest_carts_on_same_account_use_one_canonical_cart(self):
        first = self.make_cart(lines=((self.ring, 1),))
        second = self.make_cart(lines=((self.other_ring, 1),))
        self.assertEqual(self.login_and_get(first).data["token"], str(first.token))
        result = self.login_and_get(second)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["token"], str(first.token))
        self.assertEqual(len(result.data["items"]), 2)
        self.assertEqual(Cart.objects.filter(user=self.owner, status=Cart.Status.ACTIVE).count(), 1)

    def test_account_cart_post_recovers_canonical_after_merge(self):
        account = self.make_cart(self.owner, lines=((self.ring, 1),))
        guest = self.make_cart(lines=((self.other_ring, 1),))
        self.login_and_get(guest)
        response = self.client.post("/api/v1/cart/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], str(account.token))
        self.assertEqual(len(response.data["items"]), 2)

    def test_guest_token_write_uses_canonical_account_cart(self):
        account = self.make_cart(self.owner, lines=((self.ring, 1),))
        guest = self.make_cart(lines=((self.other_ring, 1),))
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            "/api/v1/cart/items/", {"variant_sku": self.ring.sku, "quantity": 1},
            format="json", HTTP_X_CART_TOKEN=str(guest.token),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], str(account.token))
        self.assertEqual(
            {item["sku"]: item["quantity"] for item in response.data["items"]},
            {self.ring.sku: 2, self.other_ring.sku: 1},
        )

    def test_second_checkout_does_not_create_another_order(self):
        account = self.make_cart(self.owner, lines=((self.ring, 1),))
        guest = self.make_cart(lines=((self.other_ring, 1),))
        self.login_and_get(guest)
        address = dict(
            user=self.owner, cart_token=account.token,
            recipient_name="Test Buyer", phone_number="+989121234567",
            province="تهران", city="تهران", postal_code="1234567890",
            address_line="Test street",
        )
        checkout_cart(**address)
        with self.assertRaises(CheckoutError) as captured:
            checkout_cart(**address)
        self.assertEqual(captured.exception.code, "cart_not_found")
        self.assertEqual(Order.objects.filter(user=self.owner).count(), 1)

    def test_archived_product_reports_unavailable_in_cart(self):
        account = self.make_cart(self.owner, lines=((self.ring, 1),))
        self.ring.product.status = Product.Status.ARCHIVED
        self.ring.product.save(update_fields=("status",))
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(
            "/api/v1/cart/", HTTP_X_CART_TOKEN=str(account.token)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"][0]["available"], 0)
        with self.assertRaises(CheckoutError) as captured:
            checkout_cart(
                user=self.owner, cart_token=account.token,
                recipient_name="Test Buyer", phone_number="+989121234567",
                province="تهران", city="تهران", postal_code="1234567890",
                address_line="Test street",
            )
        self.assertEqual(captured.exception.code, "product_inactive")
