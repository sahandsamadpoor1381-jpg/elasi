from django.db import (
    IntegrityError,
    transaction,
)
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from apps.catalog.models import (
    Category,
    Product,
    ProductVariant,
)
from apps.inventory.models import (
    InventoryBalance,
)

from .models import Cart, CartItem


class CartModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(
            name="Rings",
            slug="cart-rings",
            sort_order=10,
        )

        product = Product.objects.create(
            name="ELASI Cart Ring",
            slug="elasi-cart-ring",
            category=category,
            status=Product.Status.ACTIVE,
        )

        cls.variant = (
            ProductVariant.objects.create(
                product=product,
                sku="ELA-CART-G18-17",
                material=(
                    ProductVariant.Material.GOLD
                ),
                karat=18,
                size="17",
                price_rial=250000000,
            )
        )

    def test_guest_cart_has_token(self):
        cart = Cart.objects.create()

        self.assertIsNotNone(
            cart.token,
        )

        self.assertIsNone(
            cart.user,
        )

        self.assertEqual(
            cart.status,
            Cart.Status.ACTIVE,
        )

    def test_cart_item_uses_variant_price(
        self,
    ):
        cart = Cart.objects.create()

        item = CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=2,
        )

        self.assertEqual(
            item.unit_price_rial,
            250000000,
        )

        self.assertEqual(
            item.line_total_rial,
            500000000,
        )

    def test_same_variant_cannot_be_duplicated_in_cart(
        self,
    ):
        cart = Cart.objects.create()

        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=1,
        )

        with self.assertRaises(
            IntegrityError,
        ):
            with transaction.atomic():
                CartItem.objects.create(
                    cart=cart,
                    variant=self.variant,
                    quantity=2,
                )

    def test_quantity_cannot_be_zero(
        self,
    ):
        cart = Cart.objects.create()

        with self.assertRaises(
            IntegrityError,
        ):
            with transaction.atomic():
                CartItem.objects.create(
                    cart=cart,
                    variant=self.variant,
                    quantity=0,
                )


class CartAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = (
            Category.objects.create(
                name="API Rings",
                slug="cart-api-rings",
                sort_order=10,
            )
        )

        cls.product = (
            Product.objects.create(
                name="ELASI API Ring",
                slug="elasi-api-ring",
                category=cls.category,
                status=(
                    Product.Status.ACTIVE
                ),
            )
        )

        cls.variant = (
            ProductVariant.objects.create(
                product=cls.product,
                sku="ELA-API-G18-17",
                material=(
                    ProductVariant.Material.GOLD
                ),
                karat=18,
                size="17",
                price_rial=250000000,
            )
        )

        InventoryBalance.objects.create(
            variant=cls.variant,
            on_hand=5,
            reserved=2,
        )

    def create_cart(self) -> str:
        response = self.client.post(
            reverse("cart:cart"),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        return response.json()["token"]

    def cart_headers(
        self,
        token: str,
    ) -> dict[str, str]:
        return {
            "HTTP_X_CART_TOKEN": token,
        }

    def test_create_guest_cart(self):
        response = self.client.post(
            reverse("cart:cart"),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payload = response.json()

        self.assertIn(
            "token",
            payload,
        )

        self.assertEqual(
            payload["items"],
            [],
        )

        self.assertEqual(
            payload["subtotal_rial"],
            0,
        )

    def test_get_cart_requires_token(
        self,
    ):
        response = self.client.get(
            reverse("cart:cart"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_add_item_uses_server_price(
        self,
    ):
        token = self.create_cart()

        response = self.client.post(
            reverse(
                "cart:cart-item-collection",
            ),
            {
                "variant_sku": (
                    self.variant.sku
                ),
                "quantity": 1,
                "price_rial": 1,
            },
            format="json",
            **self.cart_headers(token),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payload = response.json()

        self.assertEqual(
            payload["items"][0][
                "unit_price_rial"
            ],
            250000000,
        )

        self.assertEqual(
            payload["subtotal_rial"],
            250000000,
        )

    def test_add_item_cannot_exceed_available_stock(
        self,
    ):
        token = self.create_cart()

        response = self.client.post(
            reverse(
                "cart:cart-item-collection",
            ),
            {
                "variant_sku": (
                    self.variant.sku
                ),
                "quantity": 4,
            },
            format="json",
            **self.cart_headers(token),
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

    def test_adding_same_variant_increments_quantity(
        self,
    ):
        token = self.create_cart()

        url = reverse(
            "cart:cart-item-collection",
        )

        first_response = (
            self.client.post(
                url,
                {
                    "variant_sku": (
                        self.variant.sku
                    ),
                    "quantity": 1,
                },
                format="json",
                **self.cart_headers(
                    token,
                ),
            )
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = (
            self.client.post(
                url,
                {
                    "variant_sku": (
                        self.variant.sku
                    ),
                    "quantity": 1,
                },
                format="json",
                **self.cart_headers(
                    token,
                ),
            )
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        payload = (
            second_response.json()
        )

        self.assertEqual(
            len(payload["items"]),
            1,
        )

        self.assertEqual(
            payload["items"][0][
                "quantity"
            ],
            2,
        )

        self.assertEqual(
            payload["total_quantity"],
            2,
        )

    def test_patch_item_quantity(
        self,
    ):
        token = self.create_cart()

        add_response = self.client.post(
            reverse(
                "cart:cart-item-collection",
            ),
            {
                "variant_sku": (
                    self.variant.sku
                ),
                "quantity": 1,
            },
            format="json",
            **self.cart_headers(token),
        )

        item_id = (
            add_response.json()[
                "items"
            ][0]["id"]
        )

        response = self.client.patch(
            reverse(
                "cart:cart-item-detail",
                kwargs={
                    "item_id": item_id,
                },
            ),
            {
                "quantity": 3,
            },
            format="json",
            **self.cart_headers(token),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.json()[
                "items"
            ][0]["quantity"],
            3,
        )

    def test_delete_cart_item(self):
        token = self.create_cart()

        add_response = self.client.post(
            reverse(
                "cart:cart-item-collection",
            ),
            {
                "variant_sku": (
                    self.variant.sku
                ),
                "quantity": 1,
            },
            format="json",
            **self.cart_headers(token),
        )

        item_id = (
            add_response.json()[
                "items"
            ][0]["id"]
        )

        response = self.client.delete(
            reverse(
                "cart:cart-item-detail",
                kwargs={
                    "item_id": item_id,
                },
            ),
            **self.cart_headers(token),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            CartItem.objects.filter(
                pk=item_id,
            ).exists(),
        )