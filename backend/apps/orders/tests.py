from rest_framework import status
from rest_framework.test import APITestCase

from apps.cart.models import Cart, CartItem
from apps.inventory.models import InventoryBalance

from django.contrib.auth import (
    get_user_model,
)
from django.db import (
    IntegrityError,
    transaction,
)
from django.test import TestCase, override_settings

from apps.catalog.models import (
    Category,
    Product,
    ProductVariant,
)

from .models import Order, OrderItem


User = get_user_model()


class OrderModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="order-user",
            email="order@example.com",
            password="test-password",
        )

        category = Category.objects.create(
            name="Rings",
            slug="order-rings",
            sort_order=10,
        )

        product = Product.objects.create(
            name="ELASI Order Ring",
            slug="elasi-order-ring",
            category=category,
            status=Product.Status.ACTIVE,
        )

        cls.variant = (
            ProductVariant.objects.create(
                product=product,
                sku="ELA-ORDER-G18-17",
                material=(
                    ProductVariant.Material.GOLD
                ),
                karat=18,
                size="17",
                weight_grams="3.250",
                price_rial=250000000,
            )
        )

    def create_order(
        self,
    ) -> Order:
        return Order.objects.create(
            user=self.user,
            subtotal_rial=250000000,
            shipping_fee_rial=0,
            total_rial=250000000,
            recipient_name="Test Customer",
            phone_number="09120000000",
            province="West Azerbaijan",
            city="Urmia",
            postal_code="1234567890",
            address_line="Test address",
        )

    def create_order_item(
        self,
        order: Order,
        *,
        quantity: int = 1,
    ) -> OrderItem:
        return OrderItem.objects.create(
            order=order,
            variant=self.variant,
            product_name=(
                self.variant.product.name
            ),
            product_slug=(
                self.variant.product.slug
            ),
            sku=self.variant.sku,
            material=self.variant.material,
            karat=self.variant.karat,
            purity=self.variant.purity,
            size=self.variant.size,
            weight_grams=(
                self.variant.weight_grams
            ),
            unit_price_rial=(
                self.variant.price_rial
            ),
            quantity=quantity,
        )

    def test_order_has_public_id_and_default_status(
        self,
    ):
        order = self.create_order()

        self.assertIsNotNone(
            order.public_id,
        )

        self.assertEqual(
            order.status,
            Order.Status.PENDING_PAYMENT,
        )

    def test_order_item_calculates_line_total(
        self,
    ):
        order = self.create_order()

        item = self.create_order_item(
            order,
            quantity=2,
        )

        self.assertEqual(
            item.line_total_rial,
            500000000,
        )

    def test_order_item_price_is_snapshot(
        self,
    ):
        order = self.create_order()

        item = self.create_order_item(
            order,
        )

        self.variant.price_rial = (
            320000000
        )

        self.variant.save(
            update_fields=(
                "price_rial",
            ),
        )

        item.refresh_from_db()

        self.assertEqual(
            item.unit_price_rial,
            250000000,
        )

    def test_order_item_quantity_cannot_be_zero(
        self,
    ):
        order = self.create_order()

        with self.assertRaises(
            IntegrityError,
        ):
            with transaction.atomic():
                self.create_order_item(
                    order,
                    quantity=0,
                )

    def test_same_variant_cannot_appear_twice_in_order(
        self,
    ):
        order = self.create_order()

        self.create_order_item(
            order,
        )

        with self.assertRaises(
            IntegrityError,
        ):
            with transaction.atomic():
                self.create_order_item(
                    order,
                )

class CheckoutAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="checkout-user",
            email="checkout@example.com",
            password="test-password",
        )

        category = Category.objects.create(
            name="Checkout Rings",
            slug="checkout-rings",
            sort_order=10,
        )

        product = Product.objects.create(
            name="ELASI Checkout Ring",
            slug="elasi-checkout-ring",
            category=category,
            status=Product.Status.ACTIVE,
        )

        cls.variant = (
            ProductVariant.objects.create(
                product=product,
                sku="ELA-CHECKOUT-G18-17",
                material=(
                    ProductVariant.Material.GOLD
                ),
                karat=18,
                size="17",
                weight_grams="3.250",
                price_rial=250000000,
            )
        )

        InventoryBalance.objects.create(
            variant=cls.variant,
            on_hand=5,
            reserved=2,
        )

    def create_cart(
        self,
        *,
        quantity: int = 1,
    ) -> Cart:
        cart = Cart.objects.create()

        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=quantity,
        )

        return cart

    def checkout_payload(self):
        return {
            "recipient_name": (
                "Test Customer"
            ),
            "phone_number": (
                "09120000000"
            ),
            "province": (
                "آذربایجان غربی"
            ),
            "city": "ارومیه",
            "postal_code": (
                "1234567890"
            ),
            "address_line": (
                "Test checkout address"
            ),
        }

    def test_shipping_quote_requires_authentication(self):
        response = self.client.get("/api/v1/checkout/shipping-quote/")
        self.assertIn(response.status_code, (401, 403))

    @override_settings(ELASI_POSTAL_SHIPPING_FEE_RIAL=-1)
    def test_missing_shipping_fee_blocks_checkout_without_reserving_stock(self):
        cart = self.create_cart()
        self.client.force_authenticate(user=self.user)
        quote = self.client.get("/api/v1/checkout/shipping-quote/")
        self.assertEqual(quote.status_code, 503)
        self.assertEqual(quote.json()["code"], "shipping_fee_unconfigured")

        response = self.client.post(
            "/api/v1/checkout/", self.checkout_payload(),
            format="json", HTTP_X_CART_TOKEN=str(cart.token),
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "shipping_fee_unconfigured")
        self.assertFalse(Order.objects.exists())
        cart.refresh_from_db()
        self.assertEqual(cart.status, Cart.Status.ACTIVE)
        balance = InventoryBalance.objects.get(variant=self.variant)
        self.assertEqual(balance.reserved, 2)

    @override_settings(ELASI_POSTAL_SHIPPING_FEE_RIAL=150_000)
    def test_approved_postal_shipping_fee_is_quoted_and_charged_by_server(self):
        cart = self.create_cart()
        self.client.force_authenticate(user=self.user)
        quote = self.client.get("/api/v1/checkout/shipping-quote/")
        self.assertEqual(quote.status_code, 200)
        self.assertEqual(quote.json(), {
            "shipping_method": "postal", "shipping_fee_rial": 150_000,
        })
        payload = self.checkout_payload()
        payload["shipping_fee_rial"] = 0  # never trust client value
        response = self.client.post(
            "/api/v1/checkout/", payload,
            format="json", HTTP_X_CART_TOKEN=str(cart.token),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["shipping_fee_rial"], 150_000)
        self.assertEqual(response.json()["total_rial"], 250_150_000)

    @override_settings(ELASI_POSTAL_SHIPPING_FEE_RIAL=150_005)
    def test_shipping_quote_rejects_fractional_toman_fee(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/checkout/shipping-quote/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "shipping_fee_unconfigured")

    @override_settings(ELASI_POSTAL_SHIPPING_FEE_RIAL=0)
    def test_free_shipping_requires_explicit_zero(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/checkout/shipping-quote/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["shipping_fee_rial"], 0)

    def test_checkout_requires_authentication(
        self,
    ):
        cart = self.create_cart()

        response = self.client.post(
            "/api/v1/checkout/",
            self.checkout_payload(),
            format="json",
            HTTP_X_CART_TOKEN=str(
                cart.token,
            ),
        )

        self.assertIn(
            response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

    def test_checkout_creates_order_and_reserves_inventory(
        self,
    ):
        cart = self.create_cart(
            quantity=2,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            "/api/v1/checkout/",
            self.checkout_payload(),
            format="json",
            HTTP_X_CART_TOKEN=str(
                cart.token,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payload = response.json()

        self.assertEqual(
            payload["subtotal_rial"],
            500000000,
        )

        self.assertEqual(
            payload["total_rial"],
            500000000,
        )

        self.assertEqual(
            len(payload["items"]),
            1,
        )

        inventory = (
            InventoryBalance.objects.get(
                variant=self.variant,
            )
        )

        self.assertEqual(
            inventory.reserved,
            4,
        )

        cart.refresh_from_db()

        self.assertEqual(
            cart.status,
            Cart.Status.CONVERTED,
        )

        self.assertEqual(
            cart.user,
            self.user,
        )

    def test_checkout_uses_server_price(
        self,
    ):
        cart = self.create_cart()

        self.client.force_authenticate(
            user=self.user,
        )

        payload = (
            self.checkout_payload()
        )

        payload["total_rial"] = 1
        payload["subtotal_rial"] = 1

        response = self.client.post(
            "/api/v1/checkout/",
            payload,
            format="json",
            HTTP_X_CART_TOKEN=str(
                cart.token,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.json()[
                "total_rial"
            ],
            250000000,
        )

    def test_checkout_rejects_insufficient_stock(
        self,
    ):
        cart = self.create_cart(
            quantity=4,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            "/api/v1/checkout/",
            self.checkout_payload(),
            format="json",
            HTTP_X_CART_TOKEN=str(
                cart.token,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        payload = response.json()

        self.assertEqual(
            payload["code"],
            "stock_exceeded",
        )

        self.assertEqual(
            payload["available"],
            3,
        )

        self.assertFalse(
            Order.objects.exists(),
        )

    def test_converted_cart_cannot_checkout_twice(
        self,
    ):
        cart = self.create_cart()

        self.client.force_authenticate(
            user=self.user,
        )

        first_response = (
            self.client.post(
                "/api/v1/checkout/",
                self.checkout_payload(),
                format="json",
                HTTP_X_CART_TOKEN=str(
                    cart.token,
                ),
            )
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = (
            self.client.post(
                "/api/v1/checkout/",
                self.checkout_payload(),
                format="json",
                HTTP_X_CART_TOKEN=str(
                    cart.token,
                ),
            )
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Order.objects.count(),
            1,
        )