from django.db.models.deletion import ProtectedError
from django.test import TestCase

from .models import Category, Collection, Product, ProductVariant


class CatalogModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Rings",
            slug="rings",
            sort_order=10,
        )

        cls.collection = Collection.objects.create(
            name="Signature",
            slug="signature",
        )

        cls.product = Product.objects.create(
            name="ELASI Luna Ring",
            slug="elasi-luna-ring",
            category=cls.category,
            gender=Product.Gender.WOMEN,
            status=Product.Status.ACTIVE,
            allow_custom_size=True,
            is_featured=True,
        )

        cls.product.collections.add(cls.collection)

        cls.variant = ProductVariant.objects.create(
            product=cls.product,
            sku="ELA-RNG-LUNA-G18-17",
            material=ProductVariant.Material.GOLD,
            karat=18,
            size="17",
            weight_grams="3.250",
            price_rial=250000000,
        )

    def test_product_relationships(self):
        self.assertEqual(
            self.product.category,
            self.category,
        )

        self.assertIn(
            self.collection,
            self.product.collections.all(),
        )

        self.assertIn(
            self.variant,
            self.product.variants.all(),
        )

    def test_variant_belongs_to_product(self):
        self.assertEqual(
            self.variant.product,
            self.product,
        )

        self.assertEqual(
            self.variant.sku,
            "ELA-RNG-LUNA-G18-17",
        )

    def test_category_with_products_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()