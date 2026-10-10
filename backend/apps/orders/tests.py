from django.contrib.auth import (
    get_user_model,
)
from django.db import (
    IntegrityError,
    transaction,
)
from django.test import TestCase

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