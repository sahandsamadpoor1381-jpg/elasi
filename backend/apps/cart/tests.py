from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.catalog.models import (
    Category,
    Product,
    ProductVariant,
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