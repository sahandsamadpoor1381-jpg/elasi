from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.catalog.models import Category, Product, ProductVariant

from .models import InventoryBalance


class InventoryBalanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(
            name="Rings",
            slug="rings",
            sort_order=10,
        )

        product = Product.objects.create(
            name="ELASI Luna Ring",
            slug="elasi-luna-ring",
            category=category,
            status=Product.Status.ACTIVE,
        )

        cls.variant = ProductVariant.objects.create(
            product=product,
            sku="ELA-RNG-LUNA-G18-17",
            material=ProductVariant.Material.GOLD,
            karat=18,
            size="17",
            price_rial=250000000,
        )

    def test_available_is_on_hand_minus_reserved(self):
        inventory = InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=5,
            reserved=2,
        )

        self.assertEqual(
            inventory.available,
            3,
        )

    def test_reserved_cannot_exceed_on_hand(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryBalance.objects.create(
                    variant=self.variant,
                    on_hand=3,
                    reserved=4,
                )

    def test_variant_can_have_only_one_inventory_balance(self):
        InventoryBalance.objects.create(
            variant=self.variant,
            on_hand=5,
            reserved=0,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryBalance.objects.create(
                    variant=self.variant,
                    on_hand=10,
                    reserved=0,
                )