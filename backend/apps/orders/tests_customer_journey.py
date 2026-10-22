"""Real HTTP API customer journey using an isolated Django test database.

Exercise the same session cookies, CSRF rotation and API URLs as the browser.
The OTP sender is mocked; no SMS, payment or production records are touched.
This is API integration acceptance, not a Playwright/browser acceptance test.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import InventoryBalance, StockMovement
from apps.orders.models import Order


User = get_user_model()


@override_settings(ELASI_POSTAL_SHIPPING_FEE_RIAL=120_000)
class CustomerCheckoutJourneyTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(
            name="Journey Rings", slug="journey-rings", sort_order=98
        )
        product = Product.objects.create(
            name="Journey Gold Ring", slug="journey-gold-ring",
            category=category, status=Product.Status.ACTIVE,
        )
        cls.variant = ProductVariant.objects.create(
            product=product, sku="JOURNEY-GOLD-18",
            material=ProductVariant.Material.GOLD,
            karat=18, size="18", price_rial=23_000_000,
        )
        cls.other_variant = ProductVariant.objects.create(
            product=product, sku="JOURNEY-GOLD-19",
            material=ProductVariant.Material.GOLD,
            karat=18, size="19", price_rial=30_000_000,
        )
        InventoryBalance.objects.create(
            variant=cls.variant, on_hand=5, reserved=0,
        )
        InventoryBalance.objects.create(
            variant=cls.other_variant, on_hand=5, reserved=0,
        )

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf(self):
        response = self.client.get("/api/v1/auth/csrf/")
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["csrf_token"]

    def post(self, url, body, csrf, *, cart_token=None):
        kwargs = {"HTTP_X_CSRFTOKEN": csrf}
        if cart_token is not None:
            kwargs["HTTP_X_CART_TOKEN"] = str(cart_token)
        return self.client.post(url, body, format="json", **kwargs)

    def login_with_otp(self, csrf):
        with (
            patch("apps.accounts.otp.generate_otp_code", return_value="123456"),
            patch("apps.accounts.otp.send_otp_code") as sender,
        ):
            requested = self.post(
                "/api/v1/auth/otp/request/",
                {"phone_number": "09121234567"}, csrf,
            )
            self.assertEqual(requested.status_code, 200, requested.content)
            self.assertNotIn("code", requested.json())
            sender.assert_called_once()
            verified = self.post(
                "/api/v1/auth/otp/verify/",
                {"phone_number": "09121234567", "code": "123456"},
                csrf,
            )
        self.assertEqual(verified.status_code, 200, verified.content)
        self.assertTrue(verified.json()["authenticated"])
        return self.csrf()  # Django rotates CSRF on successful login.

    @staticmethod
    def address():
        return {
            "recipient_name": "Journey Buyer",
            "phone_number": "۰۹۱۲۱۲۳۴۵۶۷",
            "province": "تهران",
            "city": "تهران",
            "postal_code": "۱۲۳۴۵۶۷۸۹۰",
            "address_line": "خیابان آزمایشی پلاک ۱۲",
        }

    def test_guest_cart_otp_checkout_order_history_and_logout(self):
        csrf = self.csrf()
        created = self.post("/api/v1/cart/", {}, csrf)
        self.assertEqual(created.status_code, 201, created.content)
        guest_token = created.json()["token"]

        added = self.post(
            "/api/v1/cart/items/",
            {"variant_sku": self.variant.sku, "quantity": 2},
            csrf, cart_token=guest_token,
        )
        self.assertEqual(added.status_code, 201, added.content)
        self.assertEqual(added.json()["subtotal_rial"], 46_000_000)

        # Guest cannot get a personalized shipping quote or submit checkout.
        anonymous_quote = self.client.get("/api/v1/checkout/shipping-quote/")
        self.assertIn(anonymous_quote.status_code, (401, 403))
        csrf = self.login_with_otp(csrf)

        session = self.client.get("/api/v1/auth/session/")
        self.assertEqual(session.status_code, 200)
        user = User.objects.get(phone_number="+989121234567")
        claimed = self.client.get(
            "/api/v1/cart/", HTTP_X_CART_TOKEN=guest_token
        )
        self.assertEqual(claimed.status_code, 200, claimed.content)
        account_token = claimed.json()["token"]
        self.assertEqual(claimed.json()["total_quantity"], 2)

        quote = self.client.get("/api/v1/checkout/shipping-quote/")
        self.assertEqual(quote.status_code, 200, quote.content)
        self.assertEqual(quote.json()["shipping_fee_rial"], 120_000)

        # Malicious client-side totals are not authoritative.
        payload = self.address() | {
            "subtotal_rial": 1,
            "total_rial": 1,
            "shipping_fee_rial": 0,
        }
        placed = self.post(
            "/api/v1/checkout/", payload, csrf, cart_token=account_token
        )
        self.assertEqual(placed.status_code, 201, placed.content)
        order_data = placed.json()
        self.assertEqual(order_data["status"], "pending_payment")
        self.assertEqual(order_data["subtotal_rial"], 46_000_000)
        self.assertEqual(order_data["shipping_fee_rial"], 120_000)
        self.assertEqual(order_data["total_rial"], 46_120_000)
        self.assertEqual(order_data["postal_code"], "1234567890")
        self.assertEqual(Order.objects.filter(user=user).count(), 1)

        balance = InventoryBalance.objects.get(variant=self.variant)
        self.assertEqual(balance.reserved, 2)
        self.assertEqual(
            StockMovement.objects.filter(order__user=user).count(), 1
        )
        cart = Cart.objects.get(token=account_token)
        self.assertEqual(cart.status, Cart.Status.CONVERTED)

        # Retrying with the same cart must not create another order/reservation.
        repeated = self.post(
            "/api/v1/checkout/", payload, csrf, cart_token=account_token
        )
        self.assertEqual(repeated.status_code, 400, repeated.content)
        self.assertEqual(Order.objects.filter(user=user).count(), 1)
        balance.refresh_from_db()
        self.assertEqual(balance.reserved, 2)

        orders = self.client.get("/api/v1/orders/")
        self.assertEqual(orders.status_code, 200, orders.content)
        self.assertEqual(orders.json()["count"], 1)
        detail_url = f"/api/v1/orders/{order_data['public_id']}/"
        detail = self.client.get(detail_url)
        self.assertEqual(detail.status_code, 200, detail.content)
        self.assertEqual(detail.json()["total_rial"], 46_120_000)

        logout = self.post("/api/v1/auth/logout/", {}, csrf)
        self.assertEqual(logout.status_code, 204, logout.content)
        self.assertIn(self.client.get(detail_url).status_code, (401, 403))
        self.assertEqual(
            self.client.get(
                "/api/v1/cart/", HTTP_X_CART_TOKEN=account_token
            ).status_code,
            404,
        )

    def test_existing_account_cart_merges_with_guest_before_checkout(self):
        existing_user = User.objects.create_user(
            username="+989121234567", phone_number="+989121234567"
        )
        account_cart = Cart.objects.create(user=existing_user)
        CartItem.objects.create(
            cart=account_cart, variant=self.other_variant, quantity=1
        )

        csrf = self.csrf()
        created = self.post("/api/v1/cart/", {}, csrf)
        self.assertEqual(created.status_code, 201)
        guest_token = created.json()["token"]
        added = self.post(
            "/api/v1/cart/items/",
            {"variant_sku": self.variant.sku, "quantity": 2},
            csrf, cart_token=guest_token,
        )
        self.assertEqual(added.status_code, 201, added.content)

        csrf = self.login_with_otp(csrf)
        merged = self.client.get(
            "/api/v1/cart/", HTTP_X_CART_TOKEN=guest_token
        )
        self.assertEqual(merged.status_code, 200, merged.content)
        self.assertEqual(merged.json()["token"], str(account_cart.token))
        self.assertEqual(merged.json()["total_quantity"], 3)
        self.assertEqual(
            {item["sku"]: item["quantity"] for item in merged.json()["items"]},
            {self.variant.sku: 2, self.other_variant.sku: 1},
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/cart/", HTTP_X_CART_TOKEN=guest_token
            ).status_code,
            404,
        )
        guest = Cart.objects.get(token=guest_token)
        self.assertEqual(guest.status, Cart.Status.ABANDONED)

        placed = self.post(
            "/api/v1/checkout/", self.address(), csrf,
            cart_token=account_cart.token,
        )
        self.assertEqual(placed.status_code, 201, placed.content)
        self.assertEqual(placed.json()["subtotal_rial"], 76_000_000)
        self.assertEqual(placed.json()["total_rial"], 76_120_000)
        self.assertEqual(len(placed.json()["items"]), 2)
        self.assertEqual(Order.objects.filter(user=existing_user).count(), 1)

    def test_cross_user_order_access_is_not_authorized(self):
        csrf = self.csrf()
        guest = self.post("/api/v1/cart/", {}, csrf)
        self.assertEqual(guest.status_code, 201)
        token = guest.json()["token"]
        self.assertEqual(
            self.post(
                "/api/v1/cart/items/",
                {"variant_sku": self.variant.sku, "quantity": 1},
                csrf, cart_token=token,
            ).status_code,
            201,
        )
        csrf = self.login_with_otp(csrf)
        order_response = self.post(
            "/api/v1/checkout/", self.address(), csrf,
            cart_token=token,
        )
        self.assertEqual(order_response.status_code, 201, order_response.content)
        public_id = order_response.json()["public_id"]

        other_user = User.objects.create_user(username="another-shopper")
        other = APIClient()
        other.force_authenticate(user=other_user)
        self.assertEqual(
            other.get(f"/api/v1/orders/{public_id}/").status_code,
            404,
        )
        self.assertEqual(other.get("/api/v1/orders/").json()["count"], 0)
