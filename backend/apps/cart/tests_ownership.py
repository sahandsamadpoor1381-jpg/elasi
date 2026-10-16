"""
Cart ownership and authentication-integration tests.

Policy under test:
- guest carts keep capability-token behavior (no regression),
- authenticated users get their account cart bound and preserved
  across the OTP login flow,
- bound carts are never exposed to other users or anonymous
  requests, even with a leaked token,
- authenticated cart writes remain CSRF-protected.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import (
    APIClient,
    APITestCase,
)

from apps.catalog.models import (
    Category,
    Product,
    ProductVariant,
)
from apps.inventory.models import InventoryBalance


User = get_user_model()


class CartOwnershipTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_a = User.objects.create_user(
            username="cart-owner-a",
            email="cart-owner-a@example.com",
            password="test-password",
        )

        cls.user_b = User.objects.create_user(
            username="cart-owner-b",
            email="cart-owner-b@example.com",
            password="test-password",
        )

        category = Category.objects.create(
            name="Ownership Rings",
            slug="ownership-rings",
            sort_order=70,
        )

        product = Product.objects.create(
            name="ELASI Ownership Ring",
            slug="elasi-ownership-ring",
            category=category,
            status=Product.Status.ACTIVE,
        )

        cls.variant = ProductVariant.objects.create(
            product=product,
            sku="ELA-OWNERSHIP-G18-17",
            material=ProductVariant.Material.GOLD,
            karat=18,
            size="17",
            weight_grams="3.250",
            price_rial=250000000,
        )

        InventoryBalance.objects.create(
            variant=cls.variant,
            on_hand=10,
            reserved=0,
        )

    def create_guest_cart_with_item(self):
        response = self.client.post(
            "/api/v1/cart/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        token = response.json()["token"]

        response = self.client.post(
            "/api/v1/cart/items/",
            {
                "variant_sku": self.variant.sku,
                "quantity": 1,
            },
            format="json",
            HTTP_X_CART_TOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        return token

    def test_guest_cart_flow_has_no_regression(self):
        token = self.create_guest_cart_with_item()

        response = self.client.get(
            "/api/v1/cart/",
            HTTP_X_CART_TOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        payload = response.json()

        self.assertEqual(
            len(payload["items"]),
            1,
        )

        self.assertIsNone(
            payload.get("user"),
        )

    def test_authenticated_user_claims_guest_cart_on_access(self):
        token = self.create_guest_cart_with_item()

        self.client.force_authenticate(
            user=self.user_a,
        )

        response = self.client.get(
            "/api/v1/cart/",
            HTTP_X_CART_TOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        payload = response.json()

        self.assertEqual(
            len(payload["items"]),
            1,
        )

        from .models import Cart

        cart = Cart.objects.get(token=token)

        self.assertEqual(
            cart.user,
            self.user_a,
        )

    def test_foreign_user_cart_is_not_exposed(self):
        token = self.create_guest_cart_with_item()

        self.client.force_authenticate(
            user=self.user_a,
        )

        self.client.get(
            "/api/v1/cart/",
            HTTP_X_CART_TOKEN=token,
        )

        self.client.force_authenticate(
            user=self.user_b,
        )

        response = self.client.get(
            "/api/v1/cart/",
            HTTP_X_CART_TOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        response = self.client.post(
            "/api/v1/cart/items/",
            {
                "variant_sku": self.variant.sku,
                "quantity": 1,
            },
            format="json",
            HTTP_X_CART_TOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_bound_cart_is_not_exposed_to_anonymous(self):
        token = self.create_guest_cart_with_item()

        self.client.force_authenticate(
            user=self.user_a,
        )

        self.client.get(
            "/api/v1/cart/",
            HTTP_X_CART_TOKEN=token,
        )

        anonymous = APIClient()

        response = anonymous.get(
            "/api/v1/cart/",
            HTTP_X_CART_TOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_authenticated_create_cart_returns_single_active_cart(self):
        self.client.force_authenticate(
            user=self.user_a,
        )

        first = self.client.post(
            "/api/v1/cart/",
            {},
            format="json",
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )

        second = self.client.post(
            "/api/v1/cart/",
            {},
            format="json",
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            first.json()["token"],
            second.json()["token"],
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_cart_survives_otp_login(
        self,
        send_mock,
        generate_mock,
    ):
        token = self.create_guest_cart_with_item()

        client = APIClient()

        csrf = client.get(
            "/api/v1/auth/csrf/",
        ).json()["csrf_token"]

        response = client.post(
            "/api/v1/auth/otp/request/",
            {"phone_number": "09121234567"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        response = client.post(
            "/api/v1/auth/otp/verify/",
            {
                "phone_number": "09121234567",
                "code": "123456",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        # Same browser, same cart token: the guest cart is now
        # the logged-in user's cart, with its items preserved.
        response = client.get(
            "/api/v1/cart/",
            HTTP_X_CART_TOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        payload = response.json()

        self.assertEqual(
            len(payload["items"]),
            1,
        )

        from .models import Cart

        cart = Cart.objects.get(token=token)

        self.assertEqual(
            cart.user.phone_number,
            "+989121234567",
        )

    def test_authenticated_cart_write_requires_csrf(self):
        token = self.create_guest_cart_with_item()

        strict_client = APIClient(
            enforce_csrf_checks=True,
        )

        # Real session login (force_authenticate would bypass the
        # CSRF enforcement this test exists to verify).
        strict_client.force_login(self.user_a)

        # Claim the cart first (GET is CSRF-exempt).
        response = strict_client.get(
            "/api/v1/cart/",
            HTTP_X_CART_TOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        item_id = response.json()["items"][0]["id"]

        response = strict_client.patch(
            f"/api/v1/cart/items/{item_id}/",
            {"quantity": 2},
            format="json",
            HTTP_X_CART_TOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        # Anonymous writes against an unbound guest cart keep
        # working with the capability token alone — the guest
        # behavior regression check.
        guest_token = self.create_guest_cart_with_item()

        anonymous = APIClient()

        response = anonymous.get(
            "/api/v1/cart/",
            HTTP_X_CART_TOKEN=guest_token,
        )

        guest_item_id = response.json()["items"][0]["id"]

        response = anonymous.patch(
            f"/api/v1/cart/items/{guest_item_id}/",
            {"quantity": 2},
            format="json",
            HTTP_X_CART_TOKEN=guest_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
